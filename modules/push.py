import time
from config import *

def push_block(robot, vision, read_gray, read_photo):

    cl, cr = 0, 0
    start_time = time.time()
    lost_count = 0
    last_print_time = 0

    l0, r0 = read_photo(robot)

    print(f"[PUSH] Entering push mode, initial photo sensors: L={l0}, R={r0}")

    target_ids = [0]
    if PUSH_ID_1:
        target_ids.append(1)
    if PUSH_ID_2:
        target_ids.append(2)

    def ramp(c, t):
        if c < t:
            return min(c + RAMP_STEP, t)
        return max(c - RAMP_STEP, t)

    while True:

        # ⏱ 超时保护
        if time.time() - start_time > PUSH_TIMEOUT:
            break

        tag = vision.get()

        # ================= 目标锁定 =================
        if tag and tag["id"] in target_ids:

            lost_count = 0

            err = tag["cx"]
            dist = tag["distance"]

            # 每 0.2 秒打印一次距离信息
            if time.time() - last_print_time > 0.2:
                print(f"[PUSH] Tag ID: {tag['id']}, Distance: {dist:.3f}m, Center X: {err:.3f}")
                last_print_time = time.time()

            # 距离速度映射（降低速度，避免冲太快）
            if dist < 0.15:
                base = 700  # 近距离保持推进
            elif dist < 0.30:
                base = 800  # 中距离加速推进
            else:
                base = max(400, min(900, int(KP_DIST * dist * 100)))

            # 只在距离较远时进行转向对准，近距离直接推进
            if dist > 0.25:
                turn = KP_ANGLE * err * 400
            else:
                turn = 0  # 近距离不转向，直接推进

        else:
            lost_count += 1

            # 丢失目标时继续前进，不退出
            if lost_count > LOST_TOLERANCE:
                # 继续前进寻找目标
                base = 500
                turn = 0
            else:
                turn = 0
                base = 400

        # ================= 灰度防掉台 =================
        try:
            norm, _ = read_gray(robot)
        except Exception as e:
            print(f"ERROR: read_gray failed in push: {e}")
            robot.set_speed(0, 0)
            break

        # 安全检查：传感器异常时停止
        if all(v == 0 for v in norm) or any(v < 0 or v > 1.1 for v in norm):
            print("WARN: abnormal sensor readings in push, stopping:", norm)
            robot.set_speed(0, 0)
            break

        if max(norm) > 0.7:
            base = min(base, 400)

        # 极限保护（防自杀）- 这是唯一允许退出的灰度情况
        if max(norm) > 0.85:
            robot.set_speed(-800, -800)
            time.sleep(0.25)
            robot.set_speed(0, 0)
            print("WARN: Edge detected, emergency retreat from push mode")
            break

        # ================= 电机输出 =================
        lt = base - turn
        rt = base + turn

        cl = ramp(cl, lt)
        cr = ramp(cr, rt)

        robot.set_speed(cl, cr)

        # ================= 推出判定 =================
        l, r = read_photo(robot)

        # 推出判定需要同时满足两个条件：
        # 1. 光电传感器：两个都变成1（铲子悬空，方块推下去了）
        # 2. 灰度传感器：检测到台边（灰度值变高，方块推到边缘了）
        photo_pushed = (l == 1 and r == 1) and (l0 == 0 or r0 == 0)
        gray_edge = max(norm) > 0.7  # 灰度检测到台边

        if photo_pushed and gray_edge:
            time.sleep(PUSH_CONFIRM_DELAY)

            l2, r2 = read_photo(robot)
            norm2, _ = read_gray(robot)

            # 二次确认：光电都还是1，并且灰度还是高
            if l2 == 1 and r2 == 1 and max(norm2) > 0.7:

                # ================= 收尾 =================

                # 冲一下（确保掉）
                robot.set_speed(400, 400)
                time.sleep(0.1)

                # 后退脱离，回到台中心
                robot.set_speed(-800, -800)
                time.sleep(0.5)

                # 回正
                robot.set_speed(500, -500)
                time.sleep(0.2)

                robot.set_speed(0, 0)
                print("[PUSH] Block pushed successfully (photo + gray confirmed), returning to patrol")
                return  # 退出push函数，继续巡台

        time.sleep(0.01)

    robot.set_speed(0, 0)
    print("[PUSH] Exiting push mode (timeout or edge detected)")

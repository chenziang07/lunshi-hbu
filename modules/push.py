import time
from config import *

def push_block(robot, vision, read_gray, read_photo):

    cl, cr = 0, 0
    start_time = time.time()
    lost_count = 0
    last_print_time = 0

    l0, r0 = read_photo(robot)

    pushed_once = False   # 是否已经触发一次推出

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

            # 距离速度映射（确保最小速度400）
            if dist < 0.25:
                base = MAX_SPEED
            else:
                base = max(400, min(MAX_SPEED, int(KP_DIST * dist * 100)))

            turn = KP_ANGLE * err * 400

        else:
            lost_count += 1

            if lost_count > LOST_TOLERANCE:
                break

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

        # 极限保护（防自杀）
        if max(norm) > 0.85:
            robot.set_speed(-800, -800)
            time.sleep(0.25)
            break

        # ================= 电机输出 =================
        lt = base - turn
        rt = base + turn

        cl = ramp(cl, lt)
        cr = ramp(cr, rt)

        robot.set_speed(cl, cr)

        # ================= 推出判定 =================
        l, r = read_photo(robot)

        # 光电传感器：0=有东西（未推下去），1=悬空（推下去了）
        # 判断：至少有一个变成1才算推下去
        pushed = (l == 1 or r == 1)

        if pushed:
            time.sleep(PUSH_CONFIRM_DELAY)

            l2, r2 = read_photo(robot)

            # 二次确认：至少有一个还是1
            if l2 == 1 or r2 == 1:

                # ================= 收尾 =================

                # 冲一下（确保掉）
                robot.set_speed(600, 600)
                time.sleep(0.15)

                # 后退脱离，回到台中心
                robot.set_speed(-800, -800)
                time.sleep(0.5)

                # 回正
                robot.set_speed(500, -500)
                time.sleep(0.2)

                robot.set_speed(0, 0)
                return  # 退出push函数，继续巡台

        time.sleep(0.01)

    robot.set_speed(0, 0)

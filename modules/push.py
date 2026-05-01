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

    # ================= 推块前方向修正 =================
    print("[PUSH] Aligning direction before pushing...")
    align_start = time.time()
    aligned = False

    while time.time() - align_start < 3.0:  # 最多修正3秒
        tag = vision.get()

        if tag and tag["id"] in target_ids:
            err = tag["cx"]

            # 方向已对齐（误差小于阈值）
            if abs(err) < 0.05:
                aligned = True
                robot.set_speed(0, 0)
                print(f"[PUSH] Direction aligned (error: {err:.3f}), ready to push")
                time.sleep(0.1)
                break

            # 原地转向修正
            turn_speed = int(KP_ANGLE * err * 500)
            robot.set_speed(-turn_speed, turn_speed)
            time.sleep(0.01)
        else:
            # 未检测到目标，停止修正
            robot.set_speed(0, 0)
            break

    robot.set_speed(0, 0)

    if not aligned:
        print("[PUSH] Warning: Direction alignment incomplete, proceeding anyway")

    time.sleep(0.1)  # 稳定后再开始推进

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

            # 距离速度映射（根据摄像头偏差修正：0.22m实际识别为0.12m）
            # 原阈值 * (0.12/0.22) ≈ 原阈值 * 0.55
            if dist < 0.03:  # 实际约5cm，极近距离，降低速度避免冲太快
                base = 500  # 极近距离慢速推进
            elif dist < 0.08:  # 实际约0.15m
                base = 700  # 近距离保持推进
            elif dist < 0.16:  # 实际约0.30m
                base = 800  # 中距离加速推进
            else:
                base = max(400, min(900, int(KP_DIST * dist * 100)))

            # 全程进行方向修正，确保块在画面中心
            # 近距离时降低转向增益，避免过度摆动
            if dist < 0.08:  # 实际约0.15m
                turn = KP_ANGLE * err * 200  # 近距离降低转向力度
            elif dist < 0.16:  # 实际约0.30m
                turn = KP_ANGLE * err * 300  # 中距离适中转向
            else:
                turn = KP_ANGLE * err * 400  # 远距离正常转向

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

        # 极限保护（防自杀）- 提高阈值，只在真正危险时才退出
        # 推块过程中灰度会升高，但只要光电未触发就应该继续推
        if max(norm) > 0.95:
            robot.set_speed(-800, -800)
            time.sleep(0.25)
            robot.set_speed(0, 0)
            print("WARN: Extreme edge detected, emergency retreat from push mode")
            break

        # ================= 电机输出 =================
        lt = base - turn
        rt = base + turn

        cl = ramp(cl, lt)
        cr = ramp(cr, rt)

        robot.set_speed(cl, cr)

        # ================= 推出判定（光电+灰度双重确认）=================
        l, r = read_photo(robot)

        # 检测光电数值：至少一个变成1（铲子开始悬空，方块推下去了）
        # 同时灰度必须在0.92以上（确实到了台边）
        photo_pushed = (l == 1 or r == 1) and (l0 == 0 or r0 == 0)
        gray_edge = max(norm) > 0.92  # 提高灰度阈值，确保真的推到位了

        if photo_pushed and gray_edge:
            print(f"[PUSH] Photo sensor triggered (L={l}, R={r}), gray={max(norm):.2f}, retreating to safe zone")

            # 立即停止
            robot.set_speed(0, 0)
            time.sleep(0.05)

            # 后退到安全区域
            robot.set_speed(-800, -800)
            time.sleep(0.5)

            # 回正
            robot.set_speed(500, -500)
            time.sleep(0.2)

            robot.set_speed(0, 0)
            print("[PUSH] Block pushed successfully, returned to safe zone")
            return  # 退出push函数，继续巡台

        time.sleep(0.01)

    robot.set_speed(0, 0)
    print("[PUSH] Exiting push mode (timeout or edge detected)")

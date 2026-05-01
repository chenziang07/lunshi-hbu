import time
from config import *
from config import PATROL_SAFE_ZONE_THRESHOLD

def push_block(robot, vision, read_gray, read_photo):

    cl, cr = 0, 0
    lost_count = 0
    last_print_time = 0
    lost_start_time = None  # 记录开始丢失目标的时间
    last_known_cx = 0  # 记录最后一次看到目标时的水平偏移量

    l0, r0 = read_photo(robot)

    print(f"[PUSH] Entering push mode, initial photo sensors: L={l0}, R={r0}")

    # 显示初始前两个灰度传感器的归一化值
    try:
        norm_init, _ = read_gray(robot)
        print(f"[PUSH] Initial front two gray sensors: [{norm_init[0]:.2f}, {norm_init[1]:.2f}]")
    except Exception as e:
        print(f"[PUSH] Warning: Could not read initial gray sensors: {e}")

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

    while time.time() - align_start < PUSH_ALIGN_TIMEOUT:
        tag = vision.get()

        if tag and tag["id"] in target_ids:
            err = tag["cx"]

            # 方向已对齐（误差小于阈值）
            if abs(err) < PUSH_ALIGN_THRESHOLD:
                aligned = True
                robot.set_speed(0, 0)
                print(f"[PUSH] Direction aligned (error: {err:.3f}), ready to push")
                time.sleep(0.1)
                break

            # 原地转向修正
            turn_speed = int(KP_ANGLE * err * PUSH_ALIGN_TURN_GAIN)
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

        tag = vision.get()

        # ================= 目标锁定 =================
        if tag and tag["id"] in target_ids:

            lost_count = 0
            lost_start_time = None  # 重置丢失计时

            err = tag["cx"]
            dist = tag["distance"]
            last_known_cx = err  # 记录最后一次看到的水平偏移量

            # 每 0.2 秒打印一次距离信息
            if time.time() - last_print_time > 0.2:
                print(f"[PUSH] Tag ID: {tag['id']}, Distance: {dist:.3f}m, Center X: {err:.3f}")
                last_print_time = time.time()

            # 距离速度映射（根据摄像头偏差修正：0.22m实际识别为0.12m）
            # 原阈值 * (0.12/0.22) ≈ 原阈值 * 0.55
            if dist < 0.03:  # 实际约5cm，极近距离，降低速度避免冲太快
                base = PUSH_SPEED_VERY_CLOSE
            elif dist < 0.08:  # 实际约0.15m
                base = PUSH_SPEED_CLOSE
            elif dist < 0.16:  # 实际约0.30m
                base = PUSH_SPEED_MEDIUM
            else:
                base = max(MIN_SPEED, min(900, int(KP_DIST * dist * 100)))

            # 全程进行方向修正，确保块在画面中心
            # 近距离时降低转向增益，避免过度摆动
            if dist < 0.08:  # 实际约0.15m
                turn = KP_ANGLE * err * PUSH_TURN_GAIN_CLOSE
            elif dist < 0.16:  # 实际约0.30m
                turn = KP_ANGLE * err * PUSH_TURN_GAIN_MEDIUM
            else:
                turn = KP_ANGLE * err * PUSH_TURN_GAIN_FAR

        else:
            # 目标丢失处理
            if lost_start_time is None:
                lost_start_time = time.time()
                print(f"[PUSH] Target lost, last known cx={last_known_cx:.3f}, starting recovery...")

            lost_duration = time.time() - lost_start_time

            # 丢失时间超过容忍时间，尝试恢复
            if lost_duration > LOST_TOLERANCE:
                print(f"[PUSH] Target lost for {lost_duration:.1f}s, attempting recovery...")

                # 1. 低速后退0.2秒
                robot.set_speed(-400, -400)
                time.sleep(0.2)
                robot.set_speed(0, 0)
                time.sleep(0.1)

                # 2. 读取灰度值，判断是否朝向安全区域
                try:
                    norm, _ = read_gray(robot)
                except Exception as e:
                    print(f"ERROR: read_gray failed during recovery: {e}")
                    robot.set_speed(0, 0)
                    return

                max_danger = max(norm)
                print(f"[PUSH] After retreat, danger values: {norm}, max={max_danger:.2f}")

                # 3. 如果不在安全区域（危险值 >= PATROL_SAFE_ZONE_THRESHOLD），分析灰度并转向安全方向
                if max_danger >= PATROL_SAFE_ZONE_THRESHOLD:
                    print("[PUSH] Not facing safe zone, analyzing gray values to turn towards center...")

                    # 分析前后灰度值，找到最安全的方向
                    # norm[0]=左前, norm[1]=右前, norm[2]=左后, norm[3]=右后
                    front_avg = (norm[0] + norm[1]) / 2
                    back_avg = (norm[2] + norm[3]) / 2
                    left_avg = (norm[0] + norm[2]) / 2
                    right_avg = (norm[1] + norm[3]) / 2

                    print(f"[PUSH] Direction analysis: front={front_avg:.2f}, back={back_avg:.2f}, left={left_avg:.2f}, right={right_avg:.2f}")

                    # 找到最安全的方向（灰度值最小）
                    directions = {
                        'front': front_avg,
                        'back': back_avg,
                        'left': left_avg,
                        'right': right_avg
                    }
                    safest_direction = min(directions, key=directions.get)
                    print(f"[PUSH] Safest direction: {safest_direction}")

                    # 根据最安全方向转向
                    if safest_direction == 'back':
                        # 后方最安全，转180度
                        print("[PUSH] Turning 180° towards back (safest)")
                        robot.set_speed(500, -500)
                        time.sleep(0.6)
                    elif safest_direction == 'left':
                        # 左侧最安全，左转90度
                        print("[PUSH] Turning left 90° (safest)")
                        robot.set_speed(-500, 500)
                        time.sleep(0.3)
                    elif safest_direction == 'right':
                        # 右侧最安全，右转90度
                        print("[PUSH] Turning right 90° (safest)")
                        robot.set_speed(500, -500)
                        time.sleep(0.3)
                    else:
                        # 前方最安全，不转向
                        print("[PUSH] Front is safest, no turn needed")

                    robot.set_speed(0, 0)
                    time.sleep(0.1)

                    # 4. 转向后继续后退到安全区域
                    print("[PUSH] Retreating to safe zone after reorientation...")
                    while True:
                        try:
                            norm, _ = read_gray(robot)
                        except Exception as e:
                            print(f"ERROR: read_gray failed: {e}")
                            break

                        max_danger = max(norm)
                        if max_danger < PATROL_SAFE_ZONE_THRESHOLD:
                            print(f"[PUSH] Reached safe zone (danger={max_danger:.2f})")
                            break

                        robot.set_speed(-500, -500)
                        time.sleep(0.1)

                    robot.set_speed(0, 0)
                    time.sleep(0.1)

                # 5. 检查是否找回目标
                recovery_tag = vision.get()
                if recovery_tag and recovery_tag["id"] in target_ids:
                    print("[PUSH] Target recovered! Continuing push...")
                    lost_start_time = None
                    continue

                # 恢复失败，确保在安全区域后退出推块模式
                print("[PUSH] Recovery failed, ensuring safe zone before exiting...")
                try:
                    norm, _ = read_gray(robot)
                    max_danger = max(norm)
                    if max_danger >= PATROL_SAFE_ZONE_THRESHOLD:
                        print(f"[PUSH] Still not safe (danger={max_danger:.2f}), final retreat...")
                        robot.set_speed(-600, -600)
                        time.sleep(0.3)
                except Exception:
                    pass

                robot.set_speed(0, 0)
                print("[PUSH] Exiting push mode to patrol")
                return

            # 丢失时间未超过容忍时间，继续前进寻找
            base = PUSH_LOST_SPEED_CONTINUE
            turn = 0

        # ================= 灰度减速控制 =================
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

        # 根据前两个灰度传感器逐渐减速，但最多只能减到500
        front_two_max = max(norm[0], norm[1])
        if front_two_max > PUSH_GRAY_SLOWDOWN_THRESHOLD:
            # 灰度越高，速度越低，但不低于PUSH_GRAY_MIN_SPEED
            # PUSH_GRAY_SLOWDOWN_THRESHOLD -> 不减速, 1.0 -> 减到PUSH_GRAY_MIN_SPEED
            speed_factor = max(0.5, 1.0 - (front_two_max - PUSH_GRAY_SLOWDOWN_THRESHOLD) / (1.0 - PUSH_GRAY_SLOWDOWN_THRESHOLD) * 0.5)
            base = max(int(base * speed_factor), PUSH_GRAY_MIN_SPEED)

        # ================= 电机输出 =================
        lt = base - turn
        rt = base + turn

        cl = ramp(cl, lt)
        cr = ramp(cr, rt)

        robot.set_speed(cl, cr)

        # ================= 推出判定（仅光电触发）=================
        l, r = read_photo(robot)

        # 检测光电数值：至少一个变成1（铲子开始悬空，方块推下去了）
        photo_pushed = (l == 1 or r == 1) and (l0 == 0 or r0 == 0)

        if photo_pushed:
            print(f"[PUSH] Photo sensor triggered (L={l}, R={r}), front gray=[{norm[0]:.2f}, {norm[1]:.2f}], retreating to safe zone")

            # 立即停止
            robot.set_speed(0, 0)
            time.sleep(0.05)

            # 后退到安全区域
            print("[PUSH] Retreating to safe zone...")
            while True:
                try:
                    norm, _ = read_gray(robot)
                except Exception as e:
                    print(f"ERROR: read_gray failed during retreat: {e}")
                    break

                max_danger = max(norm)

                # 已到达安全区域（危险值 < PATROL_SAFE_ZONE_THRESHOLD）
                if max_danger < PATROL_SAFE_ZONE_THRESHOLD:
                    print(f"[PUSH] Reached safe zone (danger={max_danger:.2f})")
                    break

                # 继续后退
                robot.set_speed(-PUSH_SUCCESS_RETREAT_SPEED, -PUSH_SUCCESS_RETREAT_SPEED)
                time.sleep(0.1)

            robot.set_speed(0, 0)
            time.sleep(0.1)

            # 回正
            robot.set_speed(PUSH_SUCCESS_TURN_SPEED, -PUSH_SUCCESS_TURN_SPEED)
            time.sleep(PUSH_SUCCESS_TURN_TIME)

            robot.set_speed(0, 0)
            print("[PUSH] Block pushed successfully, returned to safe zone")
            return  # 退出push函数，继续巡台

        time.sleep(0.01)

    robot.set_speed(0, 0)
    print("[PUSH] Exiting push mode (edge detected or sensor error)")

import time
from config import *

def push_block(robot, vision, read_gray, read_photo):

    cl, cr = 0, 0
    start_time = time.time()
    lost_count = 0

    l0, r0 = read_photo(robot)

    pushed_once = False   # 是否已经触发一次推出

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
        if tag and tag["id"] in [0, 1]:

            lost_count = 0

            err = tag["cx"]
            dist = tag["distance"]

            # 近距离冲刺
            if dist < 0.25:
                base = MAX_SPEED
            else:
                base = max(MIN_SPEED, min(MAX_SPEED, KP_DIST * dist))

            turn = KP_ANGLE * err * 400

        else:
            lost_count += 1

            if lost_count > LOST_TOLERANCE:
                break

            turn = 0
            base = MIN_SPEED

        # ================= 灰度防掉台 =================
        norm, _ = read_gray(robot)

        if max(norm) > 0.7:
            base = min(base, 200)

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

        if PUSH_REQUIRE_BOTH:
            pushed = (l == PHOTO_EMPTY_VALUE and r == PHOTO_EMPTY_VALUE)
        else:
            pushed = (l == PHOTO_EMPTY_VALUE or r == PHOTO_EMPTY_VALUE)

        if PUSH_USE_TRANSITION:
            pushed = pushed and (l0 == PHOTO_BLOCK_VALUE or r0 == PHOTO_BLOCK_VALUE)

        if pushed:
            time.sleep(PUSH_CONFIRM_DELAY)

            l2, r2 = read_photo(robot)

            if l2 == PHOTO_EMPTY_VALUE and r2 == PHOTO_EMPTY_VALUE:

                #  新增：二次补推
                if not pushed_once:
                    pushed_once = True
                    robot.set_speed(MAX_SPEED, MAX_SPEED)
                    time.sleep(0.2)
                    continue   # 再检测一次

                # ================= 收尾 =================

                # 冲一下（确保掉）
                robot.set_speed(600, 600)
                time.sleep(0.15)

                # 后退脱离
                robot.set_speed(-800, -800)
                time.sleep(0.35)

                # 回正
                robot.set_speed(500, -500)
                time.sleep(0.2)

                break

        time.sleep(0.01)

    robot.set_speed(0, 0)
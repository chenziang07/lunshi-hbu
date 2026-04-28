# modules/patrol.py

import time
from config import *
from modules.sensors import read_gray

class Patrol:

    def __init__(self, robot):
        self.robot = robot
        self.l = 0
        self.r = 0

        # 状态机
        self.STATE_NORMAL = 0
        self.STATE_ESCAPE = 1
        self.state = self.STATE_NORMAL
        self.escape_start = 0

    # ================== 线性加速 ==================
    def ramp(self, cur, target):
        if cur < target:
            return min(cur + ACC_STEP, target)
        return max(cur - ACC_STEP, target)

    # ================== 主逻辑 ==================
    def step(self):

        norm, _ = read_gray(self.robot)

        front = (norm[0] + norm[1]) / 2
        back  = (norm[2] + norm[3]) / 2
        left  = (norm[0] + norm[2]) / 2
        right = (norm[1] + norm[3]) / 2

        max_val = max(norm)

        # ==================  极限掉台保护 ==================
        if all(v > 0.85 for v in norm):
            self.state = self.STATE_ESCAPE
            self.escape_start = time.time()

        # ================== 状态机：强制脱离 ==================
        if self.state == self.STATE_ESCAPE:

            # 后退 + 偏转
            l = -800
            r = -800

            if left > right:
                l -= 200
            else:
                r -= 200

            # 脱离后恢复
            if time.time() - self.escape_start > 0.4:
                self.state = self.STATE_NORMAL

        # ================== 正常巡航 ==================
        else:

            # ==================  连续控制 ==================
            error = norm[0] - norm[1]

            base_speed = 600

            # ==================  提前掉台预测 ==================
            if max_val > DANGER_THRESHOLD:

                # 减速
                base_speed = 250

                # 转向（远离危险侧）
                if left > right:
                    error += 0.5
                else:
                    error -= 0.5

            # ================== 动态转向 ==================
            l = base_speed - STEER_GAIN * error
            r = base_speed + STEER_GAIN * error

            # ==================  后方危险补偿 ==================
            if back > 0.7:
                l += 100
                r += 100

        # ================== 线性加速 ==================
        self.l = self.ramp(self.l, l)
        self.r = self.ramp(self.r, r)

        # ================== 输出 ==================
        self.robot.set_speed(self.l, self.r)
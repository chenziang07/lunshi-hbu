# modules/patrol.py

import time

from config import DEBUG
from modules.sensors import read_gray


class Patrol:
    def __init__(self, robot):
        self.robot = robot

        self.STATE_FORWARD = 0
        self.STATE_RETREAT = 1
        self.STATE_TURN = 2

        self.state = self.STATE_FORWARD
        self.turn_start = 0
        self.forward_start = 0  # 记录前进开始时间

        self.turn_duration = 0.2  # 转向时间（缩短以减小巡台范围）
        self.forward_duration = 0.25  # 前进时间（缩短以便更频繁扫描）
        self.center_threshold = 0.35
        self.last_left = 0
        self.last_right = 0
        self.last_print = 0

        self.current_speed = 0
        self.target_speed = 700  # 提高巡台速度，更快找到块

    def smooth(self, left, right):
        left = int(0.7 * self.last_left + 0.3 * left)
        right = int(0.7 * self.last_right + 0.3 * right)
        self.last_left = left
        self.last_right = right
        return left, right

    def is_center_safe(self, norm):
        return all(v < self.center_threshold for v in norm)

    def ramp_speed(self, target):
        from config import ACC_STEP
        if self.current_speed < target:
            self.current_speed = min(self.current_speed + ACC_STEP, target)
        elif self.current_speed > target:
            self.current_speed = max(self.current_speed - ACC_STEP, target)
        return self.current_speed

    def step(self):
        try:
            norm, _ = read_gray(self.robot)
        except Exception as e:
            print(f"ERROR: read_gray failed in patrol: {e}")
            self.robot.set_speed(0, 0)
            return

        # 安全检查：如果所有传感器读数都是0或异常，停止电机
        if all(v == 0 for v in norm) or any(v < 0 or v > 1.1 for v in norm):
            if DEBUG:
                print("WARN: abnormal sensor readings, stopping:", norm)
            self.robot.set_speed(0, 0)
            self.current_speed = 0
            return

        max_val = max(norm)

        if all(v > 0.85 for v in norm):
            front_avg = (norm[0] + norm[1]) / 2
            left = 800 if front_avg < 0.5 else 400
            right = 800 if front_avg < 0.5 else -400
            self.state = self.STATE_FORWARD
            left, right = self.smooth(left, right)
            self.robot.set_speed(left, right)
            return

        if self.state == self.STATE_FORWARD:
            speed = self.ramp_speed(self.target_speed)
            left = speed
            right = speed

            # 检测到边缘时后退
            if max_val > 0.5:
                self.state = self.STATE_RETREAT
                self.current_speed = 0

        elif self.state == self.STATE_RETREAT:
            left = -700
            right = -700
            self.current_speed = 0
            if self.is_center_safe(norm):
                self.state = self.STATE_TURN
                self.turn_start = time.time()

        else:  # STATE_TURN
            # 转向时保持低速前进，缩小转向幅度以减小巡台范围
            left = 500   # 提高左轮速度，减小转向半径
            right = -500  # 提高右轮速度，减小转向半径
            if time.time() - self.turn_start > self.turn_duration:
                self.state = self.STATE_FORWARD
                self.forward_start = time.time()  # 记录前进开始时间

        left, right = self.smooth(left, right)
        if DEBUG and time.time() - self.last_print > 0.2:
            print("patrol:", self.state, "gray:", norm, "cmd:", left, right)
            self.last_print = time.time()
        self.robot.set_speed(left, right)

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

        self.turn_duration = 0.3
        self.center_threshold = 0.25
        self.last_left = 0
        self.last_right = 0
        self.last_print = 0

    def smooth(self, left, right):
        left = int(0.7 * self.last_left + 0.3 * left)
        right = int(0.7 * self.last_right + 0.3 * right)
        self.last_left = left
        self.last_right = right
        return left, right

    def is_center_safe(self, norm):
        return all(v < self.center_threshold for v in norm)

    def step(self):
        norm, _ = read_gray(self.robot)
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
            left = 600
            right = 600
            if max_val > 0.5:
                self.state = self.STATE_RETREAT

        elif self.state == self.STATE_RETREAT:
            left = -700
            right = -700
            if self.is_center_safe(norm):
                self.state = self.STATE_TURN
                self.turn_start = time.time()

        else:
            left = 500
            right = -500
            if time.time() - self.turn_start > self.turn_duration:
                self.state = self.STATE_FORWARD

        left, right = self.smooth(left, right)
        if DEBUG and time.time() - self.last_print > 0.2:
            print("patrol:", self.state, "gray:", norm, "cmd:", left, right)
            self.last_print = time.time()
        self.robot.set_speed(left, right)

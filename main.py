import time
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DRIVERS_DIR = os.path.join(BASE_DIR, "drivers")
if DRIVERS_DIR not in sys.path:
    sys.path.insert(0, DRIVERS_DIR)

import uptech
from modules.vision import Vision
from modules.patrol import Patrol
from modules.push import push_block
from modules.sensors import load_gray, read_gray, read_photo
from config import (
    PUSH_ID_1,
    PUSH_ID_2,
    LOCK_FRAMES,
    MOTOR_LEFT_ID,
    MOTOR_RIGHT_ID,
    MOTOR_LEFT_SIGN,
    MOTOR_RIGHT_SIGN,
    DEBUG,
)


class Robot:
    def __init__(self):
        self.up = uptech.UpTech()
        self.up.ADC_IO_Open()
        self.up.CDS_Open()
        time.sleep(0.01)
        self.up.CDS_SetMode(MOTOR_LEFT_ID, 1)
        self.up.CDS_SetMode(MOTOR_RIGHT_ID, 1)
        self.last_print = 0

    def set_speed(self, left_speed, right_speed):
        left = MOTOR_LEFT_SIGN * int(left_speed)
        right = MOTOR_RIGHT_SIGN * int(right_speed)
        if DEBUG and time.time() - self.last_print > 0.2:
            print("speed:", left, right)
            self.last_print = time.time()
        self.up.CDS_SetSpeed(MOTOR_LEFT_ID, left)
        self.up.CDS_SetSpeed(MOTOR_RIGHT_ID, right)

    def read_adc(self):
        return self.up.ADC_Get_All_Channle()

    def read_io(self):
        io_all_input = self.up.ADC_IO_GetAllInputLevel()
        if io_all_input < 0:
            return [1] * 8

        io_array = "{:08b}".format(io_all_input)
        io_data = []
        for value in io_array:
            io_data.insert(0, int(value))
        return io_data

    def stop(self):
        self.set_speed(0, 0)
        self.up.CDS_Close()


def select_target(tag):
    """根据策略选择目标"""
    if not tag:
        return None

    tid = tag["id"]

    if tid == 0:
        return 0
    elif tid == 1 and PUSH_ID_1:
        return 1
    elif tid == 2 and PUSH_ID_2:
        return 2

    return None


def main():

    # ===== 初始化 =====
    robot = Robot()
    load_gray()

    vision = Vision()
    vision.start()

    patrol = Patrol(robot)

    MODE_PATROL = 0
    MODE_PUSH = 1

    mode = MODE_PATROL

    # ===== 防抖计数 =====
    lock_count = 0
    target_id = None

    try:
        # ===== 主循环 =====
        while True:

            tag = vision.get()
            target = select_target(tag)

            # ===== 防抖逻辑 =====
            if target is not None:
                lock_count += 1
            else:
                lock_count = 0

            # ===== 模式切换 =====
            if lock_count >= LOCK_FRAMES:
                mode = MODE_PUSH
                target_id = target
            else:
                mode = MODE_PATROL

            # ===== 执行 =====
            if mode == MODE_PATROL:
                patrol.step()

            elif mode == MODE_PUSH:
                push_block(robot, vision, read_gray, read_photo)
                lock_count = 0
                mode = MODE_PATROL

            time.sleep(0.02)

    except KeyboardInterrupt:
        print("exit")

    finally:
        robot.stop()
        vision.stop()


if __name__ == "__main__":
    main()

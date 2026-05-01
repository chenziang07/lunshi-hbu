import time
import os
import sys
import signal
import atexit

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
        self._stopped = False

    def set_speed(self, left_speed, right_speed):
        if self._stopped:
            return
        left = MOTOR_LEFT_SIGN * int(left_speed)
        right = MOTOR_RIGHT_SIGN * int(right_speed)
        if DEBUG and time.time() - self.last_print > 0.2:
            print("speed:", left, right)
            self.last_print = time.time()
        try:
            self.up.CDS_SetSpeed(MOTOR_LEFT_ID, left)
            self.up.CDS_SetSpeed(MOTOR_RIGHT_ID, right)
        except Exception as e:
            print(f"ERROR: set_speed failed: {e}")
            self.stop()

    def read_adc(self):
        try:
            return self.up.ADC_Get_All_Channle()
        except Exception as e:
            print(f"ERROR: read_adc failed: {e}")
            self.stop()
            return [0] * 8

    def read_io(self):
        try:
            io_all_input = self.up.ADC_IO_GetAllInputLevel()
            if io_all_input < 0:
                return [1] * 8

            io_array = "{:08b}".format(io_all_input)
            io_data = []
            for value in io_array:
                io_data.insert(0, int(value))
            return io_data
        except Exception as e:
            print(f"ERROR: read_io failed: {e}")
            self.stop()
            return [1] * 8

    def stop(self):
        if self._stopped:
            return
        self._stopped = True
        try:
            self.up.CDS_SetSpeed(MOTOR_LEFT_ID, 0)
            self.up.CDS_SetSpeed(MOTOR_RIGHT_ID, 0)
            time.sleep(0.05)
            self.up.CDS_Close()
            print("INFO: Robot stopped")
        except Exception as e:
            print(f"ERROR: stop failed: {e}")


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
    elif tid == 2 and not PUSH_ID_2:
        return -2  # 特殊标记：需要避让的ID=2

    return None


def avoid_obstacle(robot):
    """避让障碍物（ID=2）"""
    print("[AVOID] Detected ID=2, retreating and avoiding...")

    # 后退
    robot.set_speed(-700, -700)
    time.sleep(0.5)

    # 停顿
    robot.set_speed(0, 0)
    time.sleep(0.1)

    # 转向避让（右转）
    robot.set_speed(500, -500)
    time.sleep(0.4)

    # 停止
    robot.set_speed(0, 0)
    print("[AVOID] Avoidance complete, resuming patrol")


def main():

    # ===== 初始化 =====
    robot = Robot()
    vision = None

    def cleanup(signum=None, frame=None):
        """清理资源"""
        print("\nINFO: Cleaning up resources...")
        if robot:
            robot.stop()
        if vision:
            vision.stop()
        if signum == signal.SIGTSTP:
            print("WARN: Ctrl+Z detected - resources cleaned, process will suspend")
        sys.exit(0)

    # 注册信号处理器
    signal.signal(signal.SIGINT, cleanup)   # Ctrl+C
    if hasattr(signal, 'SIGTSTP'):
        signal.signal(signal.SIGTSTP, cleanup)  # Ctrl+Z (Unix only)

    # 注册退出处理器（备用）
    atexit.register(lambda: cleanup())

    try:
        load_gray()

        vision = Vision(robot=robot)
        vision.start()

        patrol = Patrol(robot)

        MODE_PATROL = 0
        MODE_PUSH = 1
        MODE_AVOID = 2

        mode = MODE_PATROL

        # ===== 防抖计数 =====
        lock_count = 0
        target_id = None

        # ===== 避让计数（避免重复避让同一个障碍）=====
        avoided_ids = set()  # 记录已避让过的ID=2

        # ===== 主循环 =====
        while True:

            tag = vision.get()
            target = select_target(tag)

            # ===== 防抖逻辑 =====
            if target == -2:  # 需要避让的ID=2
                # 检查是否已经避让过这个位置的ID=2
                if -2 not in avoided_ids:
                    lock_count += 1
                else:
                    lock_count = 0
            elif target is not None:
                lock_count += 1
            else:
                lock_count = 0

            # ===== 模式切换 =====
            if lock_count >= LOCK_FRAMES:
                if target == -2:
                    mode = MODE_AVOID
                else:
                    mode = MODE_PUSH
                target_id = target
            else:
                mode = MODE_PATROL

            # ===== 执行 =====
            if mode == MODE_PATROL:
                patrol.step()

            elif mode == MODE_PUSH:
                push_block(robot, vision, read_gray, read_photo)
                print(f"[MAIN] Block ID {target_id} push attempt completed")
                lock_count = 0
                mode = MODE_PATROL

            elif mode == MODE_AVOID:
                avoid_obstacle(robot)
                avoided_ids.add(-2)  # 记录已避让
                print(f"[MAIN] Obstacle avoided, total avoided: {len(avoided_ids)}")
                lock_count = 0
                mode = MODE_PATROL

            time.sleep(0.02)

    except KeyboardInterrupt:
        print("\nINFO: KeyboardInterrupt received")

    except Exception as e:
        print(f"\nERROR: Unexpected error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        cleanup()


if __name__ == "__main__":
    main()

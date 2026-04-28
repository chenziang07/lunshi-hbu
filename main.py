import time

from drivers.up_controller import Robot
from modules.vision import Vision
from modules.patrol import Patrol
from modules.push import push_block
from modules.sensors import load_gray, read_gray, read_photo
from config import PUSH_ID_1, PUSH_ID_2, LOCK_FRAMES


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


if __name__ == "__main__":
    main()
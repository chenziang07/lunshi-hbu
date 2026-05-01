#!/usr/bin/env python3
"""
线性加速冲台测试脚本
用于测试机器人的线性加速功能，从0加速到最大速度1023
带灰度传感器保护：至少2个传感器归一化值 < 1 时停止
使用闭环速度控制
"""

import time
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DRIVERS_DIR = os.path.join(BASE_DIR, "drivers")
if DRIVERS_DIR not in sys.path:
    sys.path.insert(0, DRIVERS_DIR)

# 导入drivers目录下的模块
import sys
sys.path.insert(0, os.path.join(BASE_DIR, "drivers"))
from up_controller import UpController

# 导入其他模块
from modules.sensors import load_gray, read_gray
from config import MOTOR_LEFT_ID, MOTOR_RIGHT_ID, MOTOR_LEFT_SIGN, MOTOR_RIGHT_SIGN

# 加速参数
MAX_SPEED = 1023
ACC_STEP = 80  # 每次加速步长
UPDATE_INTERVAL = 0.02  # 20ms更新一次

def rush_forward(controller, robot_wrapper, duration=3.0):
    """
    线性加速冲台（带灰度传感器保护）

    Args:
        controller: UpController对象（闭环控制）
        robot_wrapper: 用于读取传感器的包装对象
        duration: 冲台持续时间（秒）
    """
    print("=" * 50)
    print("线性加速冲台测试（闭环控制 + 灰度保护）")
    print("=" * 50)
    print(f"最大速度: {MAX_SPEED}")
    print(f"加速步长: {ACC_STEP}")
    print(f"持续时间: {duration}秒")
    print(f"灰度保护: 至少2个传感器 < 1.0 时停止")
    print()

    current_speed = 0
    start_time = time.time()
    last_update = start_time
    last_print = start_time

    print("开始加速...")

    try:
        while time.time() - start_time < duration:
            now = time.time()

            # ================= 灰度传感器检测 =================
            try:
                norm, raw = read_gray(robot_wrapper)

                # 统计有多少个传感器值 < 1.0（检测到台边）
                edge_count = sum(1 for v in norm if v < 1.0)

                # 至少2个传感器检测到台边时停止
                if edge_count >= 2:
                    print(f"\n⚠️ 灰度保护触发！检测到 {edge_count} 个传感器 < 1.0")
                    print(f"   归一化值: {norm}")
                    print(f"   原始值: {raw}")
                    break

            except Exception as e:
                print(f"\n❌ 读取灰度传感器失败: {e}")
                break

            # ================= 线性加速控制 =================
            # 每20ms更新一次速度
            if now - last_update >= UPDATE_INTERVAL:
                # 线性加速
                if current_speed < MAX_SPEED:
                    current_speed = min(current_speed + ACC_STEP, MAX_SPEED)

                # 使用闭环控制设置电机速度
                left = MOTOR_LEFT_SIGN * current_speed
                right = MOTOR_RIGHT_SIGN * current_speed
                controller.move_cmd(left, right)
                last_update = now

            # 每0.2秒打印一次状态
            if now - last_print >= 0.2:
                elapsed = now - start_time
                print(f"[{elapsed:.1f}s] 速度: {current_speed}, 灰度: {norm}")
                last_print = now

            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n用户中断")

    finally:
        # 停止电机
        print("\n减速停止...")
        controller.move_cmd(0, 0)
        print("✅ 测试完成")

class RobotWrapper:
    """包装类，用于兼容 read_gray 函数"""
    def __init__(self, controller):
        self.controller = controller

    def read_adc(self):
        return self.controller.adc_data

def main():
    print("初始化机器人...")

    try:
        # 加载灰度传感器标定数据
        print("加载灰度传感器标定...")
        load_gray()

        # 初始化 UpController（闭环控制）
        controller = UpController()
        controller.set_chassis_mode(controller.CHASSIS_MODE_CONTROLLER)

        # 设置电机为电机模式
        controller.up.CDS_SetMode(MOTOR_LEFT_ID, 1)
        controller.up.CDS_SetMode(MOTOR_RIGHT_ID, 1)

        # 创建包装对象用于读取传感器
        robot_wrapper = RobotWrapper(controller)

        print("✅ 机器人初始化成功")
        print()

        # 倒计时
        for i in range(3, 0, -1):
            print(f"倒计时: {i}秒...")
            time.sleep(1)
        print()

        # 执行冲台测试
        rush_forward(controller, robot_wrapper, duration=3.0)

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\n关闭机器人连接...")
        try:
            controller.move_cmd(0, 0)
            time.sleep(0.05)
            controller.up.CDS_Close()
        except:
            pass
        print("✅ 程序结束")

if __name__ == "__main__":
    main()

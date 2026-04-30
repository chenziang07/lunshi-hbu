#!/usr/bin/env python3
"""
简易焦距标定工具
使用 AprilTag 和已知距离快速标定相机焦距

使用方法：
1. 打印一个 AprilTag（记录其实际尺寸，单位：米）
2. 用尺子测量 AprilTag 到相机的距离
3. 运行此脚本，输入实际距离
4. 程序自动计算焦距并更新 config.py
"""

import cv2
import numpy as np
import apriltag
import platform
import os
import sys

# 导入配置
from config import CAMERA_WIDTH, CAMERA_HEIGHT, APRILTAG_SIZE


def detect_camera():
    """自动检测可用的摄像头"""
    system = platform.system()
    if system == "Linux":
        if os.path.exists("/dev/video0"):
            return "/dev/video0"
        elif os.path.exists("/dev/video1"):
            return "/dev/video1"
        return 0
    else:
        return 0


def calculate_focal_length(tag_size_m, distance_m, tag_width_px):
    """
    根据 AprilTag 实际尺寸、实际距离和图像中的像素宽度计算焦距

    公式：f = (tag_width_px * distance_m) / tag_size_m

    参数：
        tag_size_m: AprilTag 实际尺寸（米）
        distance_m: AprilTag 到相机的实际距离（米）
        tag_width_px: AprilTag 在图像中的宽度（像素）

    返回：
        焦距（像素）
    """
    focal_length = (tag_width_px * distance_m) / tag_size_m
    return focal_length


def main():
    print("=" * 60)
    print("简易焦距标定工具")
    print("=" * 60)
    print()
    print(f"当前配置：")
    print(f"  - 相机分辨率: {CAMERA_WIDTH}x{CAMERA_HEIGHT}")
    print(f"  - AprilTag 尺寸: {APRILTAG_SIZE}m ({APRILTAG_SIZE*100}cm)")
    print()
    print("准备工作：")
    print("  1. 确保 AprilTag 已打印（尺寸正确）")
    print("  2. 用尺子测量 AprilTag 到相机镜头的距离")
    print("  3. 将 AprilTag 放在该距离处，正面朝向相机")
    print()
    print("操作说明：")
    print("  - 按 [空格] 采集当前帧并输入实际距离")
    print("  - 按 [q] 退出")
    print("=" * 60)
    print()

    # 打开摄像头
    camera_device = detect_camera()
    cap = cv2.VideoCapture(camera_device)

    if not cap.isOpened():
        print(f"错误：无法打开摄像头 {camera_device}")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    # 初始化 AprilTag 检测器
    detector = apriltag.Detector(apriltag.DetectorOptions(families='tag36h11 tag25h9'))

    # 存储多次测量结果
    measurements = []

    print("摄像头已打开，等待检测 AprilTag...")
    print()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("警告：无法读取摄像头画面")
            continue

        # 旋转图像（根据你的设置）
        frame = cv2.rotate(frame, cv2.ROTATE_180)

        # 转换为灰度图
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 检测 AprilTag
        tags = detector.detect(gray)

        # 显示画面
        display_frame = frame.copy()

        if len(tags) > 0:
            tag = tags[0]

            # 绘制角点
            for corner in tag.corners:
                cv2.circle(display_frame, tuple(corner.astype(int)), 5, (0, 255, 0), -1)

            # 绘制中心点
            center = tuple(tag.center.astype(int))
            cv2.circle(display_frame, center, 8, (0, 0, 255), -1)

            # 计算 AprilTag 宽度（像素）
            tag_width_px = np.linalg.norm(tag.corners[0] - tag.corners[1])

            # 显示信息
            cv2.putText(display_frame, f"Tag ID: {tag.tag_id}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(display_frame, f"Width: {tag_width_px:.1f} px", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(display_frame, "Press [SPACE] to calibrate", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # 绘制边框
            pts = tag.corners.astype(int).reshape((-1, 1, 2))
            cv2.polylines(display_frame, [pts], True, (0, 255, 0), 2)

        else:
            cv2.putText(display_frame, "No AprilTag detected", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(display_frame, "Adjust position and angle", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # 显示已采集的测量次数
        if measurements:
            cv2.putText(display_frame, f"Measurements: {len(measurements)}", (10, CAMERA_HEIGHT - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        cv2.imshow("Focal Length Calibration", display_frame)

        key = cv2.waitKey(1) & 0xFF

        # 按空格键采集
        if key == ord(' '):
            if len(tags) == 0:
                print("错误：未检测到 AprilTag，请调整位置")
                continue

            tag = tags[0]
            tag_width_px = np.linalg.norm(tag.corners[0] - tag.corners[1])

            print()
            print("-" * 60)
            print(f"检测到 AprilTag ID: {tag.tag_id}")
            print(f"图像中宽度: {tag_width_px:.2f} 像素")
            print()

            # 输入实际距离
            while True:
                try:
                    distance_input = input("请输入 AprilTag 到相机镜头的实际距离（单位：厘米）: ").strip()
                    distance_cm = float(distance_input)
                    if distance_cm <= 0:
                        print("错误：距离必须大于 0")
                        continue
                    distance_m = distance_cm / 100.0
                    break
                except ValueError:
                    print("错误：请输入有效的数字")

            # 计算焦距
            focal_length = calculate_focal_length(APRILTAG_SIZE, distance_m, tag_width_px)

            measurements.append({
                'distance_m': distance_m,
                'tag_width_px': tag_width_px,
                'focal_length': focal_length
            })

            print()
            print(f"✓ 测量 #{len(measurements)}")
            print(f"  实际距离: {distance_cm} cm ({distance_m:.3f} m)")
            print(f"  计算焦距: {focal_length:.2f} 像素")
            print()
            print("提示：建议在不同距离（如 20cm, 30cm, 50cm）测量 3-5 次取平均值")
            print("按 [空格] 继续测量，按 [q] 完成标定")
            print("-" * 60)

        # 按 q 退出
        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    # 计算结果
    if len(measurements) == 0:
        print()
        print("未进行任何测量，退出")
        return

    print()
    print("=" * 60)
    print("标定结果")
    print("=" * 60)
    print()

    # 显示所有测量
    print("测量记录：")
    for i, m in enumerate(measurements, 1):
        print(f"  #{i}: 距离 {m['distance_m']*100:.1f}cm, "
              f"像素宽度 {m['tag_width_px']:.1f}px, "
              f"焦距 {m['focal_length']:.2f}px")

    print()

    # 计算平均焦距
    focal_lengths = [m['focal_length'] for m in measurements]
    avg_focal_length = np.mean(focal_lengths)
    std_focal_length = np.std(focal_lengths)

    print(f"平均焦距: {avg_focal_length:.2f} 像素")
    print(f"标准差: {std_focal_length:.2f} 像素")

    if len(measurements) > 1:
        print(f"变异系数: {(std_focal_length/avg_focal_length)*100:.1f}%")
        if std_focal_length / avg_focal_length > 0.05:
            print("⚠ 警告：测量结果波动较大，建议重新测量")

    print()
    print("=" * 60)
    print("请将以下参数更新到 config.py 中：")
    print("=" * 60)
    print()
    print(f"CAMERA_FX = {avg_focal_length:.2f}")
    print(f"CAMERA_FY = {avg_focal_length:.2f}")
    print(f"CAMERA_CX = {CAMERA_WIDTH / 2:.2f}")
    print(f"CAMERA_CY = {CAMERA_HEIGHT / 2:.2f}")
    print()
    print("=" * 60)
    print()

    # 询问是否自动更新
    update = input("是否自动更新 config.py？(y/n): ").strip().lower()
    if update == 'y':
        update_config(avg_focal_length)


def update_config(focal_length):
    """自动更新 config.py 中的焦距参数"""
    try:
        with open('config.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()

        updated = False
        new_lines = []

        for line in lines:
            if line.strip().startswith('CAMERA_FX'):
                new_lines.append(f'CAMERA_FX = {focal_length:.2f}\n')
                updated = True
            elif line.strip().startswith('CAMERA_FY'):
                new_lines.append(f'CAMERA_FY = {focal_length:.2f}\n')
            elif line.strip().startswith('CAMERA_CX'):
                new_lines.append(f'CAMERA_CX = {CAMERA_WIDTH / 2:.2f}\n')
            elif line.strip().startswith('CAMERA_CY'):
                new_lines.append(f'CAMERA_CY = {CAMERA_HEIGHT / 2:.2f}\n')
            else:
                new_lines.append(line)

        if updated:
            with open('config.py', 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print()
            print("✓ config.py 已更新！")
        else:
            print()
            print("⚠ 警告：未找到 CAMERA_FX 参数，请手动更新")

    except Exception as e:
        print()
        print(f"错误：无法更新 config.py: {e}")
        print("请手动复制上述参数到 config.py")


if __name__ == '__main__':
    main()

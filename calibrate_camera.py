#!/usr/bin/env python3
"""
相机标定工具
使用棋盘格标定板进行相机内参标定
"""

import cv2
import numpy as np
import os
import platform

# 棋盘格参数（内角点数量）
CHECKERBOARD = (9, 6)  # 列数 x 行数（内角点）
SQUARE_SIZE = 0.025    # 棋盘格方块边长（米），默认 2.5cm

# 相机分辨率（与实际使用时一致）
CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240

# 采集图片数量
MIN_IMAGES = 15


def detect_camera():
    """自动检测相机设备"""
    system = platform.system()
    if system == "Linux":
        if os.path.exists("/dev/video0"):
            return "/dev/video0"
        elif os.path.exists("/dev/video1"):
            return "/dev/video1"
        return 0
    else:
        return 0


def calibrate_camera():
    """执行相机标定"""

    # 准备棋盘格的 3D 点（世界坐标系）
    objp = np.zeros((CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)
    objp *= SQUARE_SIZE

    # 存储所有图像的角点
    objpoints = []  # 3D 点
    imgpoints = []  # 2D 点

    # 打开相机
    camera_device = detect_camera()
    cap = cv2.VideoCapture(camera_device)

    if not cap.isOpened():
        print(f"错误：无法打开相机 {camera_device}")
        return None

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    print("=" * 60)
    print("相机标定工具")
    print("=" * 60)
    print(f"棋盘格配置: {CHECKERBOARD[0]}x{CHECKERBOARD[1]} 内角点")
    print(f"方块尺寸: {SQUARE_SIZE * 100}cm")
    print(f"需要采集: {MIN_IMAGES} 张图片")
    print()
    print("操作说明:")
    print("  - 按 [空格] 采集当前图像")
    print("  - 按 [q] 退出")
    print("  - 采集足够图片后会自动开始标定")
    print()
    print("提示:")
    print("  - 从不同角度、距离拍摄棋盘格")
    print("  - 确保棋盘格完全在画面内")
    print("  - 避免模糊和反光")
    print("=" * 60)

    captured_count = 0
    gray_shape = None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("警告：无法读取相机画面")
            continue

        # 旋转 180 度（与实际使用一致）
        frame = cv2.rotate(frame, cv2.ROTATE_180)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_shape = gray.shape[::-1]

        # 查找棋盘格角点
        ret, corners = cv2.findChessboardCorners(
            gray,
            CHECKERBOARD,
            cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_FAST_CHECK + cv2.CALIB_CB_NORMALIZE_IMAGE
        )

        # 显示画面
        display = frame.copy()

        if ret:
            # 找到角点，绘制
            cv2.drawChessboardCorners(display, CHECKERBOARD, corners, ret)
            cv2.putText(display, "Found! Press SPACE to capture", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        else:
            cv2.putText(display, "Searching for checkerboard...", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        cv2.putText(display, f"Captured: {captured_count}/{MIN_IMAGES}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        cv2.imshow("Camera Calibration", display)

        key = cv2.waitKey(1) & 0xFF

        # 按空格采集
        if key == ord(' ') and ret:
            # 亚像素精度优化
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)

            objpoints.append(objp)
            imgpoints.append(corners2)
            captured_count += 1

            print(f"✓ 已采集 {captured_count}/{MIN_IMAGES} 张图片")

            # 采集足够后开始标定
            if captured_count >= MIN_IMAGES:
                print()
                print("正在标定相机，请稍候...")
                break

        # 按 q 退出
        elif key == ord('q'):
            print("用户取消标定")
            cap.release()
            cv2.destroyAllWindows()
            return None

    cap.release()
    cv2.destroyAllWindows()

    # 执行标定
    ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
        objpoints, imgpoints, gray_shape, None, None
    )

    if not ret:
        print("错误：标定失败")
        return None

    # 计算重投影误差
    mean_error = 0
    for i in range(len(objpoints)):
        imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i],
                                          camera_matrix, dist_coeffs)
        error = cv2.norm(imgpoints[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
        mean_error += error
    mean_error /= len(objpoints)

    print()
    print("=" * 60)
    print("标定完成！")
    print("=" * 60)
    print()
    print("相机内参矩阵:")
    print(camera_matrix)
    print()
    print("畸变系数:")
    print(dist_coeffs)
    print()
    print(f"重投影误差: {mean_error:.4f} 像素")
    print()
    print("=" * 60)
    print("请将以下参数复制到 config.py 中:")
    print("=" * 60)
    print()
    print(f"CAMERA_FX = {camera_matrix[0, 0]:.2f}")
    print(f"CAMERA_FY = {camera_matrix[1, 1]:.2f}")
    print(f"CAMERA_CX = {camera_matrix[0, 2]:.2f}")
    print(f"CAMERA_CY = {camera_matrix[1, 2]:.2f}")
    print()
    print("=" * 60)

    # 保存标定结果
    np.savez('camera_calibration.npz',
             camera_matrix=camera_matrix,
             dist_coeffs=dist_coeffs,
             mean_error=mean_error)
    print("标定结果已保存到: camera_calibration.npz")
    print()

    return camera_matrix, dist_coeffs, mean_error


if __name__ == "__main__":
    try:
        calibrate_camera()
    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

"""
相机标定工具
使用 10×7 黑白方格棋盘进行标定
每个格子大小：2.5cm × 2.5cm
"""

import cv2
import numpy as np
import time
import platform
import os


def calibrate_camera(
    pattern_size=(9, 6),   # 内角点数量 (列-1, 行-1) = (10-1, 7-1)
    square_size=0.025,     # 格子大小 2.5cm = 0.025m
    num_images=20,         # 采集图像数量
    camera_device=None,
    save_path="camera_params.txt"
):
    """
    相机标定函数

    参数:
        pattern_size: 棋盘内角点数量 (列数-1, 行数-1)
        square_size: 每个格子的实际大小（米）
        num_images: 需要采集的图像数量
        camera_device: 相机设备号或路径
        save_path: 标定结果保存路径

    返回:
        camera_matrix: 相机内参矩阵
        dist_coeffs: 畸变系数
        rvecs: 旋转向量
        tvecs: 平移向量
    """

    # 检测相机设备
    if camera_device is None:
        system = platform.system()
        if system == "Linux":
            if os.path.exists("/dev/video0"):
                camera_device = "/dev/video0"
            elif os.path.exists("/dev/video1"):
                camera_device = "/dev/video1"
            else:
                camera_device = 0
        else:
            camera_device = 0

    # 打开相机
    cap = cv2.VideoCapture(camera_device)
    if not cap.isOpened():
        print(f"ERROR: Cannot open camera {camera_device}")
        return None, None, None, None

    # 设置相机分辨率
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print(f"Camera opened: {camera_device}")
    print(f"Pattern size: {pattern_size[0]}×{pattern_size[1]} inner corners")
    print(f"Square size: {square_size*100}cm")
    print(f"Target images: {num_images}")
    print("\n=== Instructions ===")
    print("1. 将棋盘放在不同位置和角度")
    print("2. 按 SPACE 键采集图像")
    print("3. 按 Q 键退出")
    print("4. 采集足够图像后会自动开始标定\n")

    # 准备物体点（棋盘的3D坐标）
    objp = np.zeros((pattern_size[0] * pattern_size[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:pattern_size[0], 0:pattern_size[1]].T.reshape(-1, 2)
    objp *= square_size

    # 存储所有图像的物体点和图像点
    objpoints = []  # 3D 点
    imgpoints = []  # 2D 点

    collected_images = 0

    while collected_images < num_images:
        ret, frame = cap.read()
        if not ret:
            print("ERROR: Failed to read frame")
            break

        # 旋转图像180度（与实际使用时保持一致）
        frame = cv2.rotate(frame, cv2.ROTATE_180)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 查找棋盘角点
        ret_corners, corners = cv2.findChessboardCorners(
            gray,
            pattern_size,
            cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE
        )

        # 显示图像
        display = frame.copy()

        if ret_corners:
            # 亚像素精度优化
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)

            # 绘制角点
            cv2.drawChessboardCorners(display, pattern_size, corners_refined, ret_corners)

            # 显示提示
            cv2.putText(display, "Pattern detected! Press SPACE to capture",
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            cv2.putText(display, "No pattern detected",
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.putText(display, f"Collected: {collected_images}/{num_images}",
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow('Camera Calibration', display)

        key = cv2.waitKey(1) & 0xFF

        if key == ord(' ') and ret_corners:  # 空格键采集
            objpoints.append(objp)
            imgpoints.append(corners_refined)
            collected_images += 1
            print(f"✓ Image {collected_images}/{num_images} captured")
            time.sleep(0.3)  # 防止重复采集

        elif key == ord('q'):  # Q键退出
            print("Calibration cancelled")
            break

    cap.release()
    cv2.destroyAllWindows()

    if collected_images < 5:
        print(f"ERROR: Not enough images collected ({collected_images}), need at least 5")
        return None, None, None, None

    print(f"\n=== Starting calibration with {collected_images} images ===")

    # 执行标定
    ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
        objpoints, imgpoints, gray.shape[::-1], None, None
    )

    if not ret:
        print("ERROR: Calibration failed")
        return None, None, None, None

    # 计算重投影误差
    total_error = 0
    for i in range(len(objpoints)):
        imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i],
                                          camera_matrix, dist_coeffs)
        error = cv2.norm(imgpoints[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
        total_error += error

    mean_error = total_error / len(objpoints)

    print("\n=== Calibration Results ===")
    print(f"RMS re-projection error: {mean_error:.4f} pixels")
    print(f"\nCamera Matrix (fx, fy, cx, cy):")
    print(camera_matrix)
    print(f"\nDistortion Coefficients:")
    print(dist_coeffs)

    # 提取参数
    fx = camera_matrix[0, 0]
    fy = camera_matrix[1, 1]
    cx = camera_matrix[0, 2]
    cy = camera_matrix[1, 2]

    print(f"\n=== Config.py Parameters ===")
    print(f"CAMERA_FX = {fx:.2f}")
    print(f"CAMERA_FY = {fy:.2f}")
    print(f"CAMERA_CX = {cx:.2f}")
    print(f"CAMERA_CY = {cy:.2f}")

    # 保存结果
    with open(save_path, 'w') as f:
        f.write("=== Camera Calibration Results ===\n\n")
        f.write(f"RMS re-projection error: {mean_error:.4f} pixels\n\n")
        f.write("Camera Matrix:\n")
        f.write(f"{camera_matrix}\n\n")
        f.write("Distortion Coefficients:\n")
        f.write(f"{dist_coeffs}\n\n")
        f.write("=== Config.py Parameters ===\n")
        f.write(f"CAMERA_FX = {fx:.2f}\n")
        f.write(f"CAMERA_FY = {fy:.2f}\n")
        f.write(f"CAMERA_CX = {cx:.2f}\n")
        f.write(f"CAMERA_CY = {cy:.2f}\n")

    print(f"\nResults saved to: {save_path}")

    return camera_matrix, dist_coeffs, rvecs, tvecs


def test_calibration(camera_matrix, dist_coeffs, camera_device=None):
    """
    测试标定结果
    显示原始图像和去畸变后的图像对比
    """
    if camera_matrix is None or dist_coeffs is None:
        print("ERROR: Invalid calibration parameters")
        return

    if camera_device is None:
        system = platform.system()
        if system == "Linux":
            camera_device = "/dev/video0" if os.path.exists("/dev/video0") else 0
        else:
            camera_device = 0

    cap = cv2.VideoCapture(camera_device)
    if not cap.isOpened():
        print(f"ERROR: Cannot open camera {camera_device}")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("\n=== Testing Calibration ===")
    print("Press Q to quit")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.rotate(frame, cv2.ROTATE_180)

        # 去畸变
        h, w = frame.shape[:2]
        new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(
            camera_matrix, dist_coeffs, (w, h), 1, (w, h)
        )
        undistorted = cv2.undistort(frame, camera_matrix, dist_coeffs,
                                    None, new_camera_matrix)

        # 并排显示
        combined = np.hstack([frame, undistorted])
        cv2.putText(combined, "Original", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(combined, "Undistorted", (w + 10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow('Calibration Test', combined)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    print("=== Camera Calibration Tool ===\n")

    # 执行标定
    camera_matrix, dist_coeffs, rvecs, tvecs = calibrate_camera(
        pattern_size=(9, 6),   # 10-1=9 列, 7-1=6 行
        square_size=0.025,     # 2.5cm
        num_images=20,
        save_path="camera_params.txt"
    )

    # 测试标定结果
    if camera_matrix is not None:
        print("\nWould you like to test the calibration? (y/n)")
        choice = input().strip().lower()
        if choice == 'y':
            test_calibration(camera_matrix, dist_coeffs)

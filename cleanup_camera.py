#!/usr/bin/env python3
"""
清理摄像头资源的辅助脚本
当程序被 Ctrl+Z 挂起后，运行此脚本释放摄像头
"""

import cv2
import sys
import platform

def cleanup_camera():
    """尝试打开并立即释放摄像头，清理残留资源"""
    print("正在清理摄像头资源...")

    # 尝试多个可能的摄像头索引
    camera_indices = [0, 1, 2]

    if platform.system() == "Linux":
        camera_indices = ["/dev/video0", "/dev/video1", 0, 1]

    for idx in camera_indices:
        try:
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                print(f"  - 找到摄像头: {idx}")
                cap.release()
                print(f"  - 已释放摄像头: {idx}")
            else:
                print(f"  - 摄像头 {idx} 未打开")
        except Exception as e:
            print(f"  - 处理摄像头 {idx} 时出错: {e}")

    # 销毁所有 OpenCV 窗口
    cv2.destroyAllWindows()
    cv2.waitKey(1)

    print("清理完成！")

if __name__ == "__main__":
    cleanup_camera()

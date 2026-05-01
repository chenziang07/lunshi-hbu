import threading
import time
import cv2
import platform
import os
import numpy as np
from perception.apriltag_detect import ApriltagDetect
from config import (CAMERA_WIDTH, CAMERA_HEIGHT, APRILTAG_SIZE,
                    CAMERA_FX, CAMERA_FY, CAMERA_CX, CAMERA_CY,
                    CAMERA_DIST_COEFFS,
                    DETECT_FALLEN_BLOCK, FALLEN_GRAY_THRESHOLD,
                    FALLEN_DISTANCE_THRESHOLD, FALLEN_GRAY_LEFT_FRONT,
                    FALLEN_GRAY_RIGHT_FRONT, FALLEN_DISTANCE_CHANNEL)


class Vision:

    def __init__(self, camera_device=None, robot=None):
        # 构建相机内参矩阵
        camera_matrix = np.array([
            [CAMERA_FX, 0, CAMERA_CX],
            [0, CAMERA_FY, CAMERA_CY],
            [0, 0, 1]
        ], dtype=np.float32)

        # 畸变系数
        dist_coeffs = np.array(CAMERA_DIST_COEFFS, dtype=np.float32)

        self.detector = ApriltagDetect(
            tag_size=APRILTAG_SIZE,
            camera_matrix=camera_matrix,
            dist_coeffs=dist_coeffs
        )
        self.lock = threading.Lock()
        self.running = False
        self.thread = None

        self.tag = None
        self.robot = robot  # 保存 robot 实例用于读取传感器
        self._camera_ok = False
        self._reconnect_event = threading.Event()

        self._cap = None
        self._camera_device = self._detect_camera(camera_device)

        self._open_camera()

    def _detect_camera(self, camera_device):
        if camera_device is not None:
            return camera_device

        system = platform.system()
        if system == "Linux":
            if os.path.exists("/dev/video0"):
                return "/dev/video0"
            elif os.path.exists("/dev/video1"):
                return "/dev/video1"
            return 0
        elif system == "Windows":
            return 0
        else:
            return 0

    def _open_camera(self):
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None

        self._cap = cv2.VideoCapture(self._camera_device)
        if isinstance(self._camera_device, int):
            device_str = f"camera index {self._camera_device}"
        else:
            device_str = self._camera_device

        if self._cap.isOpened():
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
            self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self._camera_ok = True
            print(f"INFO: camera {device_str} opened successfully")
            return True
        else:
            self._camera_ok = False
            print(f"WARN: camera {device_str} failed to open")
            return False

    def _close_camera(self):
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None
        self._camera_ok = False

    def start(self):
        if self.running:
            return
        self.running = True
        self._reconnect_event.clear()
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        reconnect_delay = 0.5
        max_reconnect_delay = 5.0
        consecutive_failures = 0

        while self.running:
            if not self._camera_ok:
                self._reconnect_event.wait(timeout=reconnect_delay)
                reconnect_delay = min(reconnect_delay * 1.5, max_reconnect_delay)
                if self._open_camera():
                    reconnect_delay = 0.5
                    consecutive_failures = 0
                continue

            try:
                ret, frame = self._cap.read()
            except Exception as e:
                print(f"ERROR: camera read exception: {e}")
                ret = False

            if not ret or frame is None:
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    print(f"WARN: camera read failed {consecutive_failures} times, attempting reconnect")
                    self._close_camera()
                    consecutive_failures = 0
                time.sleep(0.1)
                continue

            consecutive_failures = 0
            reconnect_delay = 0.5

            try:
                frame = cv2.rotate(frame, cv2.ROTATE_180)
                self.detector.update_frame(frame)
                result = self.detector.get_target_info()

                # ================= 台下块检测 =================
                if DETECT_FALLEN_BLOCK and self.robot is not None:
                    result = self._check_fallen_block(result)

                with self.lock:
                    self.tag = result
            except Exception as e:
                print(f"ERROR: frame processing error: {e}")

            time.sleep(0.03)

        self._close_camera()

    def _check_fallen_block(self, result):
        """检测台下的块（已推下去的块）"""
        try:
            from modules.sensors import read_gray

            # 读取灰度传感器
            norm, _ = read_gray(self.robot)

            # 读取测距传感器 ADC3
            adc_values = self.robot.read_adc()
            distance_value = adc_values[FALLEN_DISTANCE_CHANNEL]

            # 判断条件：左前和右前灰度 > 0.98，且 ADC3 < 600
            left_front_gray = norm[FALLEN_GRAY_LEFT_FRONT]
            right_front_gray = norm[FALLEN_GRAY_RIGHT_FRONT]

            is_at_edge = (left_front_gray > FALLEN_GRAY_THRESHOLD and
                         right_front_gray > FALLEN_GRAY_THRESHOLD)
            has_fallen_block = distance_value < FALLEN_DISTANCE_THRESHOLD

            # 调试输出（每秒最多输出一次）
            if not hasattr(self, '_last_debug_time'):
                self._last_debug_time = 0

            if time.time() - self._last_debug_time > 1.0:
                print(f"[FALLEN_DEBUG] Gray L={left_front_gray:.2f}, R={right_front_gray:.2f}, ADC3={distance_value}, at_edge={is_at_edge}, has_block={has_fallen_block}")
                self._last_debug_time = time.time()

            if is_at_edge and has_fallen_block:
                print(f"[VISION] Fallen block detected! Gray L={left_front_gray:.2f}, R={right_front_gray:.2f}, ADC3={distance_value}")

                # 如果没有检测到台上的块，创建一个特殊的标记表示台下有块
                if result is None:
                    return {
                        "id": -1,  # 特殊 ID 表示台下块
                        "cx": 0.0,
                        "cy": 0.0,
                        "distance": 0.0,
                        "fallen": True  # 标记为台下块
                    }
                else:
                    # 如果同时检测到台上的块，给结果添加台下块标记
                    result["fallen_block_detected"] = True

        except Exception as e:
            print(f"ERROR: fallen block detection failed: {e}")

        return result

    def get(self):
        with self.lock:
            return self.tag

    def is_camera_ok(self):
        return self._camera_ok

    def stop(self):
        self.running = False
        self._reconnect_event.set()
        if self.thread:
            self.thread.join(timeout=2.0)
        cv2.destroyAllWindows()
        cv2.waitKey(1)

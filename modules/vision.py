import threading
import time
import cv2
import platform
import os
from perception.apriltag_detect import ApriltagDetect


class Vision:

    def __init__(self, camera_device=None):
        self.detector = ApriltagDetect()
        self.lock = threading.Lock()
        self.running = False
        self.thread = None

        self.tag = None
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
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
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

                with self.lock:
                    self.tag = result
            except Exception as e:
                print(f"ERROR: frame processing error: {e}")

            time.sleep(0.03)

        self._close_camera()

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

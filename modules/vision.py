import threading, time, cv2
from perception.apriltag_detect import ApriltagDetect

class Vision:

    def __init__(self):
        self.detector = ApriltagDetect()
        self.cap = cv2.VideoCapture(0)
        self.tag = None
        self.lock = threading.Lock()

    def start(self):
        threading.Thread(target=self.loop, daemon=True).start()

    def loop(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                continue

            frame = cv2.rotate(frame, cv2.ROTATE_180)
            self.detector.update_frame(frame)
            result = self.detector.get_target_info()

            with self.lock:
                self.tag = result

            time.sleep(0.03)

    def get(self):
        with self.lock:
            return self.tag
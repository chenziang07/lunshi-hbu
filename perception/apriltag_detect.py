import cv2
import apriltag
import numpy as np
import time


class ApriltagDetect:
    def __init__(self):
        # minimal state so Vision can query latest detection
        self.target = None
        self.at_detector = apriltag.Detector(apriltag.DetectorOptions(families='tag36h11 tag25h9'))

    def update_frame(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        tags = self.at_detector.detect(gray)

        # reset target each frame by default
        self.target = None

        if len(tags) == 0:
            return

        # use the first detected tag as target
        tag = tags[0]

        # draw corners for debug/visualization
        for c in tag.corners:
            cv2.circle(frame, tuple(c.astype(int)), 4, (255, 0, 0), 2)

        # compute normalized center x (-1..1) relative to image center
        h, w = frame.shape[:2]
        cx = tag.center[0]
        norm_cx = (cx - w/2) / (w/2)

        # approximate distance from tag size (larger tag -> closer)
        tag_width_px = abs(tag.corners[0][0] - tag.corners[1][0])
        # normalize by image width to get rough distance metric
        distance_approx = 1.0 - (tag_width_px / float(w))

        self.target = {
            "id": int(tag.tag_id),
            "cx": float(norm_cx),
            "distance": float(max(0.0, min(1.0, distance_approx)))
        }

    def get_target_info(self):
        return self.target

if __name__ == '__main__':
    cap = cv2.VideoCapture(0)
    cap.set(3,640)
    cap.set(4,480)
    ad = ApriltagDetect()
    while True:
        ret, frame = cap.read()
        frame = cv2.rotate(frame, cv2.ROTATE_180)
        ad.update_frame(frame)
        cv2.imshow("img", frame)
        if cv2.waitKey(100) & 0xff == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()


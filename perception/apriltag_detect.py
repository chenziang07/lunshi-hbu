import cv2
import apriltag
import numpy as np
import time


class ApriltagDetect:
    def __init__(self, tag_size=0.05, camera_matrix=None, dist_coeffs=None):
        # minimal state so Vision can query latest detection
        self.target = None
        self.at_detector = apriltag.Detector(apriltag.DetectorOptions(families='tag36h11 tag25h9'))

        # AprilTag 实际尺寸（米）
        self.tag_size = tag_size

        # 相机内参矩阵
        if camera_matrix is None:
            # 默认参数（320x240分辨率的估算值）
            fx = fy = 200.0  # 焦距
            cx, cy = 160.0, 120.0  # 光心
            self.camera_matrix = np.array([
                [fx, 0, cx],
                [0, fy, cy],
                [0, 0, 1]
            ], dtype=np.float32)
        else:
            self.camera_matrix = camera_matrix

        # 畸变系数（假设无畸变）
        self.dist_coeffs = dist_coeffs if dist_coeffs is not None else np.zeros(5, dtype=np.float32)

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

        # 使用 PnP 算法计算精确距离
        distance_m = self._calculate_distance_pnp(tag)

        # 如果 PnP 失败，使用近似方法
        if distance_m is None:
            tag_width_px = abs(tag.corners[0][0] - tag.corners[1][0])
            distance_approx = 1.0 - (tag_width_px / float(w))
            distance_m = float(max(0.0, min(1.0, distance_approx)))

        self.target = {
            "id": int(tag.tag_id),
            "cx": float(norm_cx),
            "distance": float(distance_m)
        }

    def _calculate_distance_pnp(self, tag):
        """使用 PnP 算法计算 AprilTag 到相机的距离（米）"""
        try:
            # AprilTag 的 3D 坐标（以 tag 中心为原点）
            half_size = self.tag_size / 2.0
            object_points = np.array([
                [-half_size, -half_size, 0],  # 左上
                [ half_size, -half_size, 0],  # 右上
                [ half_size,  half_size, 0],  # 右下
                [-half_size,  half_size, 0]   # 左下
            ], dtype=np.float32)

            # AprilTag 检测到的 2D 角点
            image_points = tag.corners.astype(np.float32)

            # 使用 solvePnP 计算位姿
            success, rvec, tvec = cv2.solvePnP(
                object_points,
                image_points,
                self.camera_matrix,
                self.dist_coeffs,
                flags=cv2.SOLVEPNP_IPPE_SQUARE
            )

            if success:
                # tvec[2] 是 Z 轴距离（深度）
                distance = float(tvec[2][0])
                return distance if distance > 0 else None
            else:
                return None

        except Exception as e:
            print(f"PnP calculation error: {e}")
            return None

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


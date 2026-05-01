# modules/patrol.py

import time
from collections import deque

from config import (
    DEBUG,
    DANGER_THRESHOLD,
    PATROL_SPEED,
    PATROL_RETREAT_SPEED,
    PATROL_TURN_SPEED,
    PATROL_CENTER_THRESHOLD,
    PATROL_EMERGENCY_THRESHOLD,
    PATROL_EMERGENCY_RETREAT_SPEED,
    PATROL_EMERGENCY_RETREAT_TIME,
    PATROL_CIRCLE_SMALL_RADIUS,
    PATROL_CIRCLE_MEDIUM_RADIUS,
    PATROL_CIRCLE_LARGE_RADIUS,
    PATROL_CIRCLE_SMALL_LAPS,
    PATROL_CIRCLE_MEDIUM_LAPS,
    PATROL_CIRCLE_LARGE_LAPS,
    PATROL_GRADIENT_THRESHOLD,
    PATROL_GRADIENT_HISTORY,
    PHOTOELECTRIC_EMPTY,
)
from modules.sensors import read_gray, read_photoelectric_edge


class Patrol:
    def __init__(self, robot):
        self.robot = robot

        # 状态定义
        self.STATE_CIRCLE_SMALL = 0
        self.STATE_CIRCLE_MEDIUM = 1
        self.STATE_CIRCLE_LARGE = 2
        self.STATE_RETREAT = 3

        self.state = self.STATE_CIRCLE_SMALL
        self.current_lap = 0
        self.lap_start_time = 0

        self.last_left = 0
        self.last_right = 0
        self.last_print = 0

        self.current_speed = 0

        # 灰度梯度历史记录
        self.gray_history = deque(maxlen=PATROL_GRADIENT_HISTORY)

    def smooth(self, left, right):
        left = int(0.7 * self.last_left + 0.3 * left)
        right = int(0.7 * self.last_right + 0.3 * right)
        self.last_left = left
        self.last_right = right
        return left, right

    def is_center_safe(self, norm):
        """检查是否在中心安全区域（危险值 < 0.3）"""
        return all(v < PATROL_CENTER_THRESHOLD for v in norm)

    def calculate_gradient(self, norm):
        """计算灰度梯度（当前帧与上一帧的最大变化）"""
        if len(self.gray_history) == 0:
            return 0.0

        last_norm = self.gray_history[-1]
        max_change = max(abs(norm[i] - last_norm[i]) for i in range(4))
        return max_change

    def check_photoelectric_edge(self):
        """检查光电传感器是否检测到台边
        返回: (触发数量, 是否紧急)
        """
        try:
            lf, rf, lb, rb = read_photoelectric_edge(self.robot)
            triggered = [lf, rf, lb, rb].count(PHOTOELECTRIC_EMPTY)
            emergency = triggered >= 2  # 两个或以上光电触发为紧急情况
            return triggered, emergency
        except Exception as e:
            if DEBUG:
                print(f"WARN: read_photoelectric_edge failed: {e}")
            return 0, False

    def get_circle_params(self):
        """根据当前状态返回圆周运动参数 (左轮速度, 右轮速度, 最大圈数)"""
        if self.state == self.STATE_CIRCLE_SMALL:
            # 小圆：左轮慢，右轮快
            return 350, 500, PATROL_CIRCLE_SMALL_LAPS
        elif self.state == self.STATE_CIRCLE_MEDIUM:
            # 中圆：速度差适中
            return 400, 550, PATROL_CIRCLE_MEDIUM_LAPS
        elif self.state == self.STATE_CIRCLE_LARGE:
            # 大圆：速度差较小
            return 420, 550, PATROL_CIRCLE_LARGE_LAPS
        else:
            return 0, 0, 0

    def step(self):
        try:
            norm, _ = read_gray(self.robot)
        except Exception as e:
            print(f"ERROR: read_gray failed in patrol: {e}")
            self.robot.set_speed(0, 0)
            return

        # 安全检查：如果所有传感器读数都是0或异常，停止电机
        if all(v == 0 for v in norm) or any(v < 0 or v > 1.1 for v in norm):
            if DEBUG:
                print("WARN: abnormal sensor readings, stopping:", norm)
            self.robot.set_speed(0, 0)
            self.current_speed = 0
            return

        # 记录灰度历史
        self.gray_history.append(norm)

        # 计算灰度梯度
        gradient = self.calculate_gradient(norm)

        # 检查光电传感器
        photo_triggered, photo_emergency = self.check_photoelectric_edge()

        max_val = max(norm)

        # ===== 紧急情况处理 =====

        # 1. 四个灰度都>=1.0，紧急后退
        if all(v >= PATROL_EMERGENCY_THRESHOLD for v in norm):
            print("[PATROL] All sensors at edge (all>=1.0), emergency retreat!")
            self.robot.set_speed(-PATROL_EMERGENCY_RETREAT_SPEED, -PATROL_EMERGENCY_RETREAT_SPEED)
            time.sleep(PATROL_EMERGENCY_RETREAT_TIME)
            self.robot.set_speed(0, 0)
            self.state = self.STATE_CIRCLE_SMALL
            self.current_lap = 0
            self.current_speed = 0
            return

        # 2. 光电传感器紧急触发（>=2个）
        if photo_emergency:
            print(f"[PATROL] Photoelectric emergency ({photo_triggered} sensors triggered), retreating!")
            self.robot.set_speed(-PATROL_EMERGENCY_RETREAT_SPEED, -PATROL_EMERGENCY_RETREAT_SPEED)
            time.sleep(PATROL_EMERGENCY_RETREAT_TIME)
            self.robot.set_speed(0, 0)
            self.state = self.STATE_CIRCLE_SMALL
            self.current_lap = 0
            self.current_speed = 0
            return

        # 3. 灰度梯度过大 + 灰度值高（突然变黑）
        if gradient > PATROL_GRADIENT_THRESHOLD and max_val > DANGER_THRESHOLD:
            print(f"[PATROL] High gradient detected ({gradient:.2f}), max gray={max_val:.2f}, retreating!")
            self.robot.set_speed(-PATROL_RETREAT_SPEED, -PATROL_RETREAT_SPEED)
            time.sleep(0.3)
            self.robot.set_speed(0, 0)
            self.state = self.STATE_CIRCLE_SMALL
            self.current_lap = 0
            self.current_speed = 0
            return

        # ===== 正常巡台逻辑 =====

        if self.state == self.STATE_RETREAT:
            # 后退到安全区域
            left = -PATROL_RETREAT_SPEED
            right = -PATROL_RETREAT_SPEED
            self.current_speed = 0

            if self.is_center_safe(norm):
                # 返回安全区域，重新开始小圆巡台
                self.state = self.STATE_CIRCLE_SMALL
                self.current_lap = 0
                self.lap_start_time = time.time()
                print("[PATROL] Returned to safe zone, starting small circle patrol")

        else:
            # 圆周运动
            left_speed, right_speed, max_laps = self.get_circle_params()

            # 检查是否需要切换到下一个圆或后退
            if max_val > DANGER_THRESHOLD or photo_triggered > 0:
                # 检测到边缘或光电触发，后退
                self.state = self.STATE_RETREAT
                if DEBUG:
                    print(f"[PATROL] Edge detected (gray={max_val:.2f}, photo={photo_triggered}), retreating")
                return

            # 检查是否完成当前圆的圈数（简单时间估算）
            # 假设一圈大约需要8秒（根据实际调整）
            lap_duration = 8.0
            if self.lap_start_time == 0:
                self.lap_start_time = time.time()

            elapsed = time.time() - self.lap_start_time
            completed_laps = int(elapsed / lap_duration)

            if completed_laps >= max_laps:
                # 完成当前圆，切换到下一个圆
                if self.state == self.STATE_CIRCLE_SMALL:
                    self.state = self.STATE_CIRCLE_MEDIUM
                    self.current_lap = 0
                    self.lap_start_time = time.time()
                    if DEBUG:
                        print("[PATROL] Switching to medium circle")
                elif self.state == self.STATE_CIRCLE_MEDIUM:
                    self.state = self.STATE_CIRCLE_LARGE
                    self.current_lap = 0
                    self.lap_start_time = time.time()
                    if DEBUG:
                        print("[PATROL] Switching to large circle")
                elif self.state == self.STATE_CIRCLE_LARGE:
                    # 完成大圆，回到小圆重新开始
                    self.state = self.STATE_CIRCLE_SMALL
                    self.current_lap = 0
                    self.lap_start_time = time.time()
                    if DEBUG:
                        print("[PATROL] Completed all circles, restarting from small circle")

            left = left_speed
            right = right_speed

        left, right = self.smooth(left, right)

        if DEBUG and time.time() - self.last_print > 0.5:
            print(f"[PATROL] State={self.state}, Gray={norm}, Gradient={gradient:.2f}, Photo={photo_triggered}, Cmd=({left},{right})")
            self.last_print = time.time()

        self.robot.set_speed(left, right)

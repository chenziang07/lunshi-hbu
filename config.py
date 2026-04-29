# config.py

MAX_SPEED = 1023
DEBUG = False

# ==================== 电机方向 ====================
MOTOR_LEFT_ID = 1
MOTOR_RIGHT_ID = 2
MOTOR_LEFT_SIGN = 1
MOTOR_RIGHT_SIGN = 1

# ==================== 巡台 ====================
DANGER_THRESHOLD = 0.65   # 越小越保守
STEER_GAIN = 200          # 越大转向越猛
ACC_STEP = 80             # 越大越激进


# ==================== 推块核心 ====================

# 转向强度（对准目标）
KP_ANGLE = 0.8

# 前进速度（根据距离）
KP_DIST = 20

# 加速快慢
RAMP_STEP = 80

# 最低推进速度
MIN_SPEED = 150


# ==================== 灰度 ====================
GRAY_CHANNELS = [5, 8, 6, 7]


# ==================== 推块目标策略 ====================

PUSH_ID_1 = True
PUSH_ID_2 = False

PRIORITY_MODE = True

# 防抖（进入推块）
LOCK_FRAMES = 3


# ====================  光电传感器（铲子） ====================

PHOTO_LEFT_IO  = 5
PHOTO_RIGHT_IO = 4

# 电平定义（你当前假设）
PHOTO_BLOCK_VALUE = 0   # 有东西
PHOTO_EMPTY_VALUE = 1   # 悬空


# ==================== 推出判定策略 ====================

# 是否必须两个都触发
PUSH_REQUIRE_BOTH = True

# 是否要求“从有到无”的变化
PUSH_USE_TRANSITION = True

# 二次确认延时
PUSH_CONFIRM_DELAY = 0.05


# ==================== 目标锁定 ====================

LOST_TOLERANCE = 5
PUSH_TIMEOUT = 3.0

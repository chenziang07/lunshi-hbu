# config.py

MAX_SPEED = 1023
DEBUG = False

# ==================== 视觉配置 ====================
CAMERA_WIDTH = 320   # 树莓派建议 320，性能好的设备可用 640
CAMERA_HEIGHT = 240  # 树莓派建议 240，性能好的设备可用 480

# AprilTag 实际尺寸（米）
APRILTAG_SIZE = 0.12  # 12cm

# 相机内参（根据实际相机标定结果修改）
# 默认值是 320x240 分辨率的估算值
CAMERA_FX = 200.0  # 焦距 x
CAMERA_FY = 200.0  # 焦距 y
CAMERA_CX = 160.0  # 光心 x
CAMERA_CY = 120.0  # 光心 y

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

# 最低推进速度（电机最少需要400才能转动）
MIN_SPEED = 400


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

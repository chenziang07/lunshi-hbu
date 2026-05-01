# config.py

MAX_SPEED = 1023
DEBUG = False

# ==================== 视觉配置 ====================
CAMERA_WIDTH = 320   # 树莓派建议 320，性能好的设备可用 640
CAMERA_HEIGHT = 240  # 树莓派建议 240，性能好的设备可用 480

# AprilTag 实际尺寸（米）
APRILTAG_SIZE = 0.12  # 12cm

# 相机内参（根据实际相机标定结果修改）
CAMERA_FX = 463.38  # 焦距 x
CAMERA_FY = 461.28  # 焦距 y
CAMERA_CX = 329.90  # 光心 x
CAMERA_CY = 236.95  # 光心 y

# 畸变系数（根据相机标定结果）
CAMERA_DIST_COEFFS = [-0.00991687, 0.09554795, -0.01163809, 0.00175394, -0.10636701]

# ==================== 电机方向 ====================
MOTOR_LEFT_ID = 1
MOTOR_RIGHT_ID = 2
MOTOR_LEFT_SIGN = 1
MOTOR_RIGHT_SIGN = 1

# ==================== 巡台 ====================
DANGER_THRESHOLD = 0.4   # 边缘检测阈值，越小越保守
PATROL_SPEED = 433       # 巡台前进速度
PATROL_RETREAT_SPEED = 700  # 巡台后退速度
PATROL_TURN_SPEED = 500     # 巡台转向速度
PATROL_TURN_DURATION = 0.2  # 转向持续时间（秒）
PATROL_CENTER_THRESHOLD = 0.35  # 中心安全阈值
PATROL_EMERGENCY_THRESHOLD = 1.0  # 紧急后退阈值（四个灰度都达到此值）
PATROL_EMERGENCY_RETREAT_SPEED = 800  # 紧急后退速度
PATROL_EMERGENCY_RETREAT_TIME = 0.3   # 紧急后退时间（秒）
PATROL_EDGE_HIGH_THRESHOLD = 0.85  # 高边缘阈值（特殊处理）
STEER_GAIN = 200          # 越大转向越猛
ACC_STEP = 80             # 越大越激进


# ==================== 推块核心 ====================

# 转向强度（对准目标）
KP_ANGLE = 0.9

# 前进速度（根据距离）
KP_DIST = 20

# 加速快慢
RAMP_STEP = 80

# 最低推进速度（电机最少需要400才能转动）
MIN_SPEED = 400

# 推块时的对齐误差阈值（画面中心偏移容忍度）
PUSH_ALIGN_THRESHOLD = 0.05  # 越小要求越精确

# 推块前对齐超时时间（秒）
PUSH_ALIGN_TIMEOUT = 3.0

# 推块时各距离段的速度
PUSH_SPEED_VERY_CLOSE = 500  # dist < 0.03m 极近距离
PUSH_SPEED_CLOSE = 700       # dist < 0.08m 近距离
PUSH_SPEED_MEDIUM = 800      # dist < 0.16m 中距离

# 推块时各距离段的转向增益倍数
PUSH_TURN_GAIN_CLOSE = 200   # dist < 0.08m 近距离转向力度
PUSH_TURN_GAIN_MEDIUM = 300  # dist < 0.16m 中距离转向力度
PUSH_TURN_GAIN_FAR = 400     # dist >= 0.16m 远距离转向力度

# 推块前对齐时的转向增益倍数
PUSH_ALIGN_TURN_GAIN = 500

# 推块时灰度减速参数
PUSH_GRAY_SLOWDOWN_THRESHOLD = 0.6  # 前两个灰度超过此值开始减速
PUSH_GRAY_MIN_SPEED = 500           # 灰度减速时的最低速度

# 推块丢失目标时的速度
PUSH_LOST_SPEED_TOLERANT = 400  # 刚丢失时的速度
PUSH_LOST_SPEED_CONTINUE = 500  # 丢失超过容忍次数后的速度

# 推块成功后的后退参数
PUSH_SUCCESS_RETREAT_SPEED = 800  # 后退速度
PUSH_SUCCESS_RETREAT_TIME = 0.5   # 后退时间（秒）
PUSH_SUCCESS_TURN_SPEED = 500     # 回正转向速度
PUSH_SUCCESS_TURN_TIME = 0.2      # 回正转向时间（秒）


# ==================== 灰度 ====================
GRAY_CHANNELS = [5, 8, 6, 7]


# ==================== 推块目标策略 ====================

PUSH_ID_1 = True  # 推 ID=1 的块
PUSH_ID_2 = False  # 不推 ID=2 的块
# 注意：ID=0 总是会被推

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

LOST_TOLERANCE = 3.0  # 目标丢失容忍时间（秒），超过此时间尝试恢复
LOST_RETREAT_TIME = 0.5  # 丢失目标后后退时间（秒）
LOST_RETREAT_SPEED = 600  # 丢失目标后后退速度


# ==================== 台下块检测 ====================

# 启用台下块检测
DETECT_FALLEN_BLOCK = True

# 灰度阈值（左前和右前都要大于此值）
FALLEN_GRAY_THRESHOLD = 0.98

# 测距传感器阈值（ADC3 小于此值表示检测到台下物体）
FALLEN_DISTANCE_THRESHOLD = 600

# 灰度传感器索引（左前、右前）
FALLEN_GRAY_LEFT_FRONT = 0   # 对应 GRAY_CHANNELS[0]
FALLEN_GRAY_RIGHT_FRONT = 1  # 对应 GRAY_CHANNELS[1]

# 测距传感器通道
FALLEN_DISTANCE_CHANNEL = 3  # ADC3

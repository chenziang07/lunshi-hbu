# 🤖 lunshi4.30 - 自主巡台推块机器人系统

基于视觉识别的自主巡台推块机器人，使用 AprilTag 进行目标识别，灰度传感器防掉台，光电传感器判断推块成功。

## ✨ 主要特性

- 🎯 **AprilTag 视觉识别**：基于 PnP 算法的精确距离测量（米级精度）
- 🚀 **线性加速控制**：平滑的运动控制，避免电机冲击
- 🛡️ **多重安全保护**：灰度传感器防掉台 + 超时保护
- 📏 **实时距离显示**：控制台实时打印目标距离和偏移
- 🔧 **完善的标定工具**：提供简易和完整两种相机标定方案
- 🔄 **自动返回巡台**：推块完成后自动返回台中心继续巡逻

## 📋 系统要求

### 硬件
- UpTech 主控板
- USB 摄像头（支持 320x240 或 640x480 分辨率）
- 灰度传感器阵列（4 路）
- 光电传感器（2 路）
- 舵机电机（2 个）

### 软件
- Python 3.7+
- OpenCV (`opencv-python`)
- NumPy
- apriltag (Python 绑定)

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install opencv-python numpy apriltag
```

### 2. 相机标定（首次使用）

#### 方法一：简易焦距标定 ⭐ 推荐（5 分钟）
```bash
python calibrate_focal_length.py
```
- 只需要 AprilTag 和尺子
- 在不同距离测量 3-5 次
- 自动更新配置文件

#### 方法二：完整相机标定（15-20 分钟）
```bash
python calibrate_camera.py
```
- 需要打印 9x6 棋盘格标定板
- 采集 15 张不同角度的图片
- 获得最高精度和畸变校正

详细说明请查看 [CAMERA_CALIBRATION.md](CAMERA_CALIBRATION.md)

### 3. 配置参数

编辑 `config.py`，根据实际情况修改：

```python
# AprilTag 实际尺寸（米）
APRILTAG_SIZE = 0.12  # 12cm，根据实际测量修改

# 相机内参（标定后更新）
CAMERA_FX = 200.0  # 焦距 x
CAMERA_FY = 200.0  # 焦距 y
CAMERA_CX = 160.0  # 光心 x
CAMERA_CY = 120.0  # 光心 y

# 推块目标选择
PUSH_ID_1 = True   # 是否推 ID=1 的块
PUSH_ID_2 = False  # 是否推 ID=2 的块
```

### 4. 运行主程序

```bash
python main.py
```

控制台会显示实时距离信息：
```
[PUSH] Tag ID: 0, Distance: 0.350m, Center X: -0.123
[PUSH] Tag ID: 0, Distance: 0.280m, Center X: -0.056
[PUSH] Tag ID: 0, Distance: 0.210m, Center X: 0.012
```

## 📁 项目结构

```
lunshi4.30/
├── main.py                      # 主程序入口
├── config.py                    # 全局配置文件
├── README.md                    # 项目说明
├── CAMERA_CALIBRATION.md        # 相机标定指南
├── TROUBLESHOOTING.md           # 故障排查文档
│
├── drivers/                     # 硬件驱动层
│   ├── uptech.py               # UpTech 主控板驱动
│   ├── closed_loop_controller.py
│   ├── serial_helper.py
│   └── up_controller.py
│
├── modules/                     # 功能模块
│   ├── patrol.py               # 巡台模块（线性加速）
│   ├── push.py                 # 推块模块（精确距离控制）
│   ├── vision.py               # 视觉系统（AprilTag 检测）
│   └── sensors.py              # 传感器读取（灰度、光电）
│
├── perception/                  # 视觉感知
│   └── apriltag_detect.py      # AprilTag 检测（PnP 距离测量）
│
├── tools/                       # 工具脚本
│   └── biaoding.py             # 标定工具
│
└── 标定工具/
    ├── calibrate_camera.py      # 完整相机标定
    ├── calibrate_focal_length.py # 简易焦距标定
    └── cleanup_camera.py        # 相机清理工具
```

## 🎯 工作流程

```
启动
  ↓
初始化（机器人 + 视觉 + 传感器）
  ↓
┌─────────────────────────────────┐
│      主循环（20ms 周期）         │
├─────────────────────────────────┤
│ 1. 获取 AprilTag 检测结果       │
│ 2. 目标选择（ID 0/1/2）         │
│ 3. 防抖计数（LOCK_FRAMES=3）    │
│                                 │
│ ┌─────────────┐  ┌───────────┐ │
│ │  巡台模式   │  │ 推块模式  │ │
│ ├─────────────┤  ├───────────┤ │
│ │ • 线性加速  │  │ • 距离控制│ │
│ │ • 灰度避障  │  │ • 角度对准│ │
│ │ • 状态机    │  │ • 光电判断│ │
│ │   - 前进    │  │ • 后退脱离│ │
│ │   - 后退    │  │ • 返回巡台│ │
│ │   - 转向    │  └───────────┘ │
│ └─────────────┘                │
└─────────────────────────────────┘
```

## 🔧 核心功能说明

### 1. 巡台模块 (`modules/patrol.py`)
- **线性加速**：使用 `ACC_STEP=80` 实现平滑加速，避免电机冲击
- **状态机控制**：前进 → 后退 → 转向 → 前进
- **灰度避障**：实时检测台边，自动后退和转向

### 2. 推块模块 (`modules/push.py`)
- **精确距离控制**：基于 PnP 算法测量真实距离（米）
- **速度映射**：根据距离动态调整速度（最小 400，最大 1023）
- **角度对准**：PID 控制，自动对准目标中心
- **光电判断**：至少一个传感器悬空（值=1）判定推下成功
- **自动返回**：推块完成后后退 0.5 秒，回到台中心继续巡台

### 3. 视觉系统 (`perception/apriltag_detect.py`)
- **AprilTag 检测**：支持 tag36h11 和 tag25h9 家族
- **PnP 距离测量**：使用相机内参和 tag 实际尺寸计算真实距离
- **实时处理**：30ms 刷新率，低延迟

## 📊 关键参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `APRILTAG_SIZE` | 0.12m | AprilTag 实际尺寸（12cm） |
| `MIN_SPEED` | 400 | 电机最小转动速度 |
| `MAX_SPEED` | 1023 | 电机最大速度 |
| `ACC_STEP` | 80 | 加速步长 |
| `KP_ANGLE` | 0.8 | 角度控制增益 |
| `KP_DIST` | 20 | 距离控制增益 |
| `LOCK_FRAMES` | 3 | 防抖帧数 |
| `PUSH_TIMEOUT` | 3.0s | 推块超时 |
| `LOST_TOLERANCE` | 5 | 丢失目标容忍帧数 |

## 🛠️ 故障排查

### 问题 1：识别到 AprilTag 但不前进
**可能原因**：
- 电机最小速度不足（需要至少 400）
- 距离计算错误

**解决方法**：
- 检查 `config.py` 中 `MIN_SPEED = 400`
- 运行相机标定，更新焦距参数

### 问题 2：推块后不返回巡台
**可能原因**：
- 光电传感器判断逻辑错误
- 后退时间不足

**解决方法**：
- 检查光电传感器接线（IO4, IO5）
- 确认 `PHOTO_EMPTY_VALUE = 1`（悬空时的电平）

### 问题 3：距离测量不准确
**可能原因**：
- 相机未标定或标定参数错误
- AprilTag 尺寸设置错误

**解决方法**：
- 运行 `python calibrate_focal_length.py` 重新标定
- 用尺子测量 AprilTag 黑色方块边长，更新 `APRILTAG_SIZE`

更多问题请查看 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## 📝 更新日志

### v4.30 (2026-05-01)

#### 🎉 新增功能
- ✅ **精确距离测量**：基于 PnP 算法，返回真实物理距离（米）
- ✅ **线性加速控制**：巡台时平滑加速，避免电机冲击
- ✅ **实时距离显示**：推块时每 0.2 秒打印距离和偏移
- ✅ **简易焦距标定工具**：5 分钟快速标定，自动更新配置
- ✅ **完整相机标定工具**：支持棋盘格标定，获得最高精度

#### 🔧 优化改进
- ✅ 修复推块速度过低导致电机不转的问题（最小速度 150 → 400）
- ✅ 简化光电传感器判断逻辑（至少一个悬空即判定成功）
- ✅ 优化推块后返回逻辑（后退时间 0.35s → 0.5s，确保回到台中心）
- ✅ 提升灰度保护限速（200 → 400），保证推进力度
- ✅ 改进距离速度映射公式，避免速度过小

#### 📚 文档完善
- ✅ 新增 `README.md` 项目说明
- ✅ 新增 `CAMERA_CALIBRATION.md` 相机标定指南
- ✅ 优化代码注释和配置说明

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 👥 作者

- 项目维护：chenziang07
- AI 辅助优化：Claude (Anthropic)

## 🙏 致谢

- [AprilTag](https://april.eecs.umich.edu/software/apriltag) - 视觉标记库
- [OpenCV](https://opencv.org/) - 计算机视觉库
- [UpTech](http://www.up-tech.com/) - 机器人主控板

---

**⭐ 如果这个项目对你有帮助，请给个 Star！**

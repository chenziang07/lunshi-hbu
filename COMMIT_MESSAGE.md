# GitHub 仓库更新指南

## 📦 本次更新内容

### v4.30 - 重大功能升级 (2026-05-01)

---

## 🎯 核心改进

### 1. 精确距离测量系统 ✨
**问题**：原有距离测量使用简单的像素宽度归一化，精度低且不是真实物理距离

**解决方案**：
- 实现基于 PnP 算法的精确距离测量
- 使用相机内参 + AprilTag 实际尺寸计算真实距离
- 返回米（m）为单位的物理距离

**影响文件**：
- `perception/apriltag_detect.py` - 新增 `_calculate_distance_pnp()` 方法
- `modules/vision.py` - 传递相机内参到检测器
- `config.py` - 新增相机内参和 AprilTag 尺寸配置

---

### 2. 线性加速控制 🚀
**问题**：巡台时速度从 0 直接跳到 600，电机冲击大，运动不平滑

**解决方案**：
- 实现线性加速算法，使用 `ACC_STEP=80` 逐步加速
- 新增 `ramp_speed()` 方法控制加速过程
- 状态切换时重置速度为 0

**影响文件**：
- `modules/patrol.py` - 新增加速控制逻辑

---

### 3. 推块逻辑优化 🎯
**问题**：
- 识别到 AprilTag 后不前进（速度过低，电机转不动）
- 推块完成后不返回巡台
- 光电传感器判断逻辑复杂

**解决方案**：
- 最小速度从 150 提升到 400（电机最小转动速度）
- 优化距离速度映射公式
- 简化光电传感器判断：至少一个悬空（值=1）即判定成功
- 后退时间延长到 0.5 秒，确保回到台中心
- 使用 `return` 退出函数，自动返回巡台模式

**影响文件**：
- `modules/push.py` - 重构推块逻辑
- `config.py` - 更新 `MIN_SPEED = 400`

---

### 4. 实时调试信息 📊
**新增功能**：
- 推块时每 0.2 秒打印距离和偏移信息
- 格式：`[PUSH] Tag ID: X, Distance: X.XXXm, Center X: X.XXX`

**影响文件**：
- `modules/push.py` - 新增距离打印逻辑

---

### 5. 相机标定工具 🔧
**新增功能**：
- **简易焦距标定**（推荐）：5 分钟快速标定，只需 AprilTag 和尺子
- **完整相机标定**：15-20 分钟，使用棋盘格，获得最高精度

**新增文件**：
- `calibrate_focal_length.py` - 简易焦距标定脚本
- `calibrate_camera.py` - 完整相机标定脚本
- `CAMERA_CALIBRATION.md` - 详细标定指南

---

## 📝 文档完善

### 新增文档
- ✅ `README.md` - 完整的项目说明文档
- ✅ `CAMERA_CALIBRATION.md` - 相机标定详细指南
- ✅ `COMMIT_MESSAGE.md` - 本次更新说明

### 优化内容
- ✅ 代码注释优化
- ✅ 配置参数说明
- ✅ 故障排查指南

---

## 🔄 Git 提交建议

### 提交信息模板

```bash
git add .
git commit -m "feat: v4.30 重大功能升级 - 精确距离测量与线性加速控制

🎉 新增功能：
- 基于 PnP 算法的精确距离测量（米级精度）
- 线性加速控制，平滑运动
- 实时距离显示
- 简易焦距标定工具（5分钟）
- 完整相机标定工具

🔧 优化改进：
- 修复推块速度过低问题（最小速度 150→400）
- 简化光电传感器判断逻辑
- 优化推块后返回逻辑（后退 0.35s→0.5s）
- 提升灰度保护限速（200→400）

📚 文档完善：
- 新增 README.md 项目说明
- 新增 CAMERA_CALIBRATION.md 标定指南
- 优化代码注释

影响文件：
- perception/apriltag_detect.py
- modules/patrol.py
- modules/push.py
- modules/vision.py
- config.py
- calibrate_focal_length.py (新增)
- calibrate_camera.py (新增)
- README.md (新增)
- CAMERA_CALIBRATION.md (新增)
"
```

---

## 📋 推送前检查清单

- [ ] 确认所有修改的文件已添加到暂存区
- [ ] 检查 `config.py` 中的敏感信息（如有）
- [ ] 确认 `.gitignore` 包含以下内容：
  ```
  __pycache__/
  *.pyc
  *.pyo
  *.npz
  camera_calibration.npz
  .vscode/
  .idea/
  ```
- [ ] 测试主程序能正常运行
- [ ] 检查 README.md 中的链接是否有效

---

## 🚀 推送命令

```bash
# 1. 查看修改状态
git status

# 2. 添加所有修改
git add .

# 3. 提交（使用上面的提交信息）
git commit -m "feat: v4.30 重大功能升级 - 精确距离测量与线性加速控制"

# 4. 推送到远程仓库
git push origin main
# 或者如果你的主分支是 master
git push origin master

# 5. 创建标签（可选）
git tag -a v4.30 -m "v4.30 - 精确距离测量与线性加速控制"
git push origin v4.30
```

---

## 📊 更新统计

### 修改文件
- `perception/apriltag_detect.py` - 新增 PnP 距离计算（+70 行）
- `modules/patrol.py` - 新增线性加速（+15 行）
- `modules/push.py` - 重构推块逻辑（+10 行，-20 行）
- `modules/vision.py` - 传递相机参数（+10 行）
- `config.py` - 新增配置参数（+10 行）

### 新增文件
- `calibrate_focal_length.py` - 简易焦距标定（300 行）
- `calibrate_camera.py` - 完整相机标定（300 行）
- `README.md` - 项目说明（400 行）
- `CAMERA_CALIBRATION.md` - 标定指南（280 行）
- `COMMIT_MESSAGE.md` - 更新说明（本文件）

### 总计
- **新增代码**：~1,400 行
- **修改代码**：~100 行
- **新增文档**：~700 行

---

## 🎯 后续计划

### 短期（v4.31）
- [ ] 添加多目标优先级选择
- [ ] 优化转向算法
- [ ] 添加性能监控

### 中期（v4.4）
- [ ] 支持多相机
- [ ] 添加 Web 控制界面
- [ ] 实现路径规划

### 长期（v5.0）
- [ ] 深度学习目标检测
- [ ] SLAM 建图与定位
- [ ] 多机器人协作

---

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- GitHub Issues: https://github.com/chenziang07/lunshi4.30/issues
- Email: [你的邮箱]

---

**感谢使用本项目！如果对你有帮助，请给个 ⭐ Star！**

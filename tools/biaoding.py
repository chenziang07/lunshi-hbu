#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
灰度传感器逐一标定 + 车头朝向六状态判断 + 标定值保存（纯终端）
传感器布局：前左(AD5)、前右(AD8)、后左(AD6)、后右(AD7)
操作：← → 选择传感器，W 标白，B 标黑，ESC 退出
"""

import time
import curses
import json
import os
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRIVERS_DIR = os.path.join(PROJECT_DIR, "drivers")
if DRIVERS_DIR not in sys.path:
    sys.path.insert(0, DRIVERS_DIR)

import uptech

# ==================== 配置 ====================
# AD5:左上(前左)  AD8:右上(前右)  AD6:左下(后左)  AD7:右下(后右)
GRAY_CHANNELS = [5, 8, 6, 7]               # 前左, 前右, 后左, 后右
SENSOR_NAMES = ['前左(AD5)', '前右(AD8)', '后左(AD6)', '后右(AD7)']
CALIB_FILE = os.path.join(PROJECT_DIR, "gray_calibration.json")
DATA_CALIB_FILE = os.path.join(PROJECT_DIR, "data", "gray_calibration.json")

WHITE = [0, 0, 0, 0]
BLACK = [0, 0, 0, 0]

# ==================== 标定文件操作 ====================
def save_calibration():
    data = {"white": WHITE, "black": BLACK, "channels": GRAY_CHANNELS}
    try:
        os.makedirs(os.path.dirname(DATA_CALIB_FILE), exist_ok=True)
        with open(CALIB_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        with open(DATA_CALIB_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def load_calibration():
    calib_file = CALIB_FILE if os.path.exists(CALIB_FILE) else DATA_CALIB_FILE
    if not os.path.exists(calib_file):
        return False
    try:
        with open(calib_file, 'r') as f:
            data = json.load(f)
        if data.get("channels") == GRAY_CHANNELS:
            for i in range(4):
                WHITE[i] = data["white"][i]
                BLACK[i] = data["black"][i]
            return True
    except Exception:
        pass
    return False

# ==================== 硬件读取 ====================
def read_gray(up):
    raw = up.ADC_Get_All_Channle()
    values = [raw[ch] for ch in GRAY_CHANNELS]
    norm = []
    for i in range(4):
        w = WHITE[i]
        b = BLACK[i]
        if w == 0 or b == 0:
            norm.append(0.0)
        else:
            v = (values[i] - w) / (b - w)
            v = max(0.0, min(1.0, v))
            norm.append(round(v, 3))
    return norm, values

# ==================== 朝向判断（六状态） ====================
def judge_direction(norm):
    fl, fr, rl, rr = norm
    front_avg = (fl + fr) / 2
    rear_avg  = (rl + rr) / 2
    left_avg  = (fl + rl) / 2
    right_avg = (fr + rr) / 2

    if front_avg < 0.35 and rear_avg < 0.35:
        direction = "正中心"
    elif front_avg < 0.35 and rear_avg > 0.45:
        if abs(left_avg - right_avg) < 0.12:
            direction = "正中心"
        elif left_avg > right_avg:
            direction = "朝向中心偏左"
        else:
            direction = "朝向中心偏右"
    elif front_avg > 0.45 and rear_avg < 0.35:
        if abs(left_avg - right_avg) < 0.12:
            direction = "朝外边中点"
        elif left_avg > right_avg:
            direction = "朝外偏左"
        else:
            direction = "朝外偏右"
    else:
        if front_avg < rear_avg:
            if abs(left_avg - right_avg) < 0.12:
                direction = "正中心"
            elif left_avg > right_avg:
                direction = "朝向中心偏左"
            else:
                direction = "朝向中心偏右"
        else:
            if abs(left_avg - right_avg) < 0.12:
                direction = "朝外边中点"
            elif left_avg > right_avg:
                direction = "朝外偏左"
            else:
                direction = "朝外偏右"

    max_val = max(norm)
    if max_val > 0.75:
        danger = "【紧急】已压边界"
    elif max_val > 0.5:
        danger = "接近边界"
    else:
        danger = "安全"
    return f"{direction} | {danger}"

# ==================== 主程序 ====================
def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.keypad(1)

    up = uptech.UpTech()
    up.CDS_Open()
    time.sleep(0.01)
    up.ADC_IO_Open()

    use_existing = False

    if load_calibration():
        stdscr.clear()
        stdscr.addstr(0, 0, "检测到上次的标定值，是否沿用？")
        stdscr.addstr(1, 0, "按 Y = 沿用，按 N = 重新标定")
        stdscr.addstr(3, 0, f"白区: {WHITE}")
        stdscr.addstr(4, 0, f"黑区: {BLACK}")
        stdscr.refresh()
        while True:
            ch = stdscr.getch()
            if ch == ord('y') or ch == ord('Y'):
                use_existing = True
                break
            elif ch == ord('n') or ch == ord('N'):
                for i in range(4):
                    WHITE[i] = 0
                    BLACK[i] = 0
                break
            time.sleep(0.05)

    selected = 0

    stdscr.clear()
    stdscr.addstr(0, 0, "灰度传感器逐一标定 + 车头朝向六状态判断")
    stdscr.addstr(1, 0, "按键：← → 选择传感器  W=标定白区  B=标定黑区  ESC=退出")
    stdscr.refresh()

    try:
        while True:
            ch = stdscr.getch()
            if ch == 27:
                break
            elif ch == curses.KEY_LEFT:
                selected = (selected - 1) % 4
            elif ch == curses.KEY_RIGHT:
                selected = (selected + 1) % 4
            elif ord('1') <= ch <= ord('4'):
                selected = ch - ord('1')

            norm, raw = read_gray(up)

            save_needed = False
            if ch == ord('w') or ch == ord('W'):
                WHITE[selected] = raw[selected]
                save_needed = True
            elif ch == ord('b') or ch == ord('B'):
                BLACK[selected] = raw[selected]
                save_needed = True

            if save_needed:
                save_calibration()

            stdscr.clear()
            status = "沿用旧值" if use_existing else "手动标定"
            stdscr.addstr(0, 0, f"状态: {status} | 当前选中: {SENSOR_NAMES[selected]}")
            stdscr.addstr(1, 0, "← → 或1~4选择   W=标白   B=标黑   ESC=退出")
            stdscr.addstr(3, 0, "传感器       原始值   白区标定  黑区标定  归一化")
            for i in range(4):
                marker = ">>" if i == selected else "  "
                line = f"{marker}{SENSOR_NAMES[i]:8s}  {raw[i]:5d}   {WHITE[i]:5d}    {BLACK[i]:5d}    {norm[i]:.3f}"
                stdscr.addstr(4+i, 0, line)
            direction = judge_direction(norm)
            stdscr.addstr(9, 0, "朝向判断: " + direction)
            stdscr.refresh()

            time.sleep(0.05)
    finally:
        save_calibration()
        up.CDS_Close()
        curses.endwin()

if __name__ == "__main__":
    curses.wrapper(main)

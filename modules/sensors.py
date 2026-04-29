import json
import os

from config import GRAY_CHANNELS, PHOTO_LEFT_IO, PHOTO_RIGHT_IO

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

WHITE = [0]*4
BLACK = [0]*4

def load_gray():
    calib_file = os.path.join(PROJECT_DIR, "data", "gray_calibration.json")
    if not os.path.exists(calib_file):
        calib_file = os.path.join(PROJECT_DIR, "gray_calibration.json")

    with open(calib_file) as f:
        data = json.load(f)

    if data.get("channels") != GRAY_CHANNELS:
        raise RuntimeError("gray calibration channels do not match GRAY_CHANNELS")

    for i in range(4):
        WHITE[i] = data["white"][i]
        BLACK[i] = data["black"][i]

def read_gray(robot):
    raw = robot.read_adc()
    vals = [raw[ch] for ch in GRAY_CHANNELS]

    norm = []
    for i in range(4):
        w,b = WHITE[i], BLACK[i]
        v = (vals[i]-w)/(b-w) if w and b and b!=w else 0
        norm.append(round(max(0,min(1,v)), 3))

    return norm, vals

def read_photo(robot):
    io = robot.read_io()
    return io[PHOTO_LEFT_IO], io[PHOTO_RIGHT_IO]

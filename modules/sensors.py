import json
from config import GRAY_CHANNELS

WHITE = [0]*4
BLACK = [0]*4

def load_gray():
    with open("data/gray_calibration.json") as f:
        data = json.load(f)
    for i in range(4):
        WHITE[i] = data["white"][i]
        BLACK[i] = data["black"][i]

def read_gray(robot):
    raw = robot.read_adc()
    vals = [raw[ch] for ch in GRAY_CHANNELS]

    norm = []
    for i in range(4):
        w,b = WHITE[i], BLACK[i]
        v = (vals[i]-w)/(b-w) if b!=w else 0
        norm.append(max(0,min(1,v)))

    return norm, vals

def read_photo(robot):
    io = robot.read_io()
    return io[0], io[1]
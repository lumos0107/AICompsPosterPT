"""면 없는 후보와 R13이 교량 면에서 얼마나 떨어져 있는지 잰다. 면 안 규칙에 여유 거리를 주면 잡히는지 보기 위함."""
import csv
import os
import sys

import numpy as np

HERE = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\새그래프_1110"
sys.path.insert(0, r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\데이터진단_1109\수집계획용\에이전트검토")
from lib_shp import read_shp

sys.stdout.reconfigure(encoding="utf-8")
RAW = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵\연속수치지도_제주_20261109\풀기"
a, b = [], []
for base in ("N3A_A0070000", "N3A_A0063321"):
    for _, rings in read_shp(os.path.join(RAW, base, base)):
        for r in rings:
            a.append(r[:-1])
            b.append(r[1:])
a, b = np.vstack(a), np.vstack(b)
v = b - a
vv = np.maximum((v * v).sum(1), 1e-9)


def dist(p):
    t = np.clip(((p - a) * v).sum(1) / vv, 0, 1)
    return float(np.hypot(*(a + t[:, None] * v - p).T).min())


named = {"R13": (911902, 1497204), "N01": (913596, 1498454), "N08": (927013, 1480631), "N19": (894141, 1485995)}
for k, p in named.items():
    print(k, "교량·육교 면 경계까지", round(dist(np.array(p, float)), 1), "m")
rows = list(csv.DictReader(open(os.path.join(HERE, "입체후보2.csv"), encoding="utf-8-sig")))
none = [r for r in rows if not r["속한 면"]]
d = np.array([dist(np.array([float(r["x"]), float(r["y"])])) for r in none])
for th in (5, 10, 15, 20, 30, 50):
    print(f"면 없는 후보 {len(none)}개 중 교량·육교 면 {th}m 안: {int((d <= th).sum())}개")

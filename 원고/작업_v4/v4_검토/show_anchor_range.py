"""사용자 설명용(원고용 아님): 출발점마다 16방향 안내점 중 실험 범위(1:1,000 도엽 114칸) 안에 든 방향과 빠진 방향을 그린다.
로컬 자료만 읽는다. 실행: py -I v4_검토/show_anchor_range.py → 안내점_범위.png"""
import csv
import math
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.patches import Rectangle
import numpy as np
import pymysql
from pyproj import Transformer

sys.stdout.reconfigure(encoding="utf-8")
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False
HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), "실험")   # HERE = 원고/작업_v4/v4_검토
fw = Transformer.from_crs(4326, 5179, always_xy=True)
START = {"탑동": (33.515, 126.522, 3000), "도심": (33.499, 126.531, 5000), "연동": (33.489, 126.490, 3000), "이도": (33.499, 126.541, 4000)}
NAME = {"탑동": "탑동 (3 km)", "도심": "시청 (5 km)", "연동": "연동 (3 km)", "이도": "이도동 (4 km)"}

tiles = [tuple(map(int, l.split(","))) for l in open(os.path.join(EXP, "도심실험_1110", "실험범위_114칸.txt"), encoding="utf-8") if l[0].isdigit()]
anch = {}
for r in csv.DictReader(open(os.path.join(EXP, "코드수정_1110", "본실험_안내점.csv"), encoding="utf-8-sig")):
    anch.setdefault(r["출발점"], {})[int(r["방향(16분할)"])] = (float(r["위도"]), float(r["경도"]))

pw = re.search(r'password="([^"]*)"', open(r"C:\Users\seungjun\Documents\claude_code\논문\데이터사이언스학회\04_실험\새그래프_만들기\build_v2b_graph.py", encoding="utf-8").read()).group(1)
con = pymysql.connect(host="localhost", user="root", password=pw, db="gildongmu_v3")
cur = con.cursor()
cur.execute("SELECT point_id, latitude, longitude FROM jeju_road_points")
P = {int(a): fw.transform(float(c), float(b)) for a, b, c in cur.fetchall()}
cur.execute("SELECT from_point_id, to_point_id FROM jeju_road_edges WHERE from_point_id < to_point_id")
SEG = np.array([(P[int(a)], P[int(b)]) for a, b in cur.fetchall()])
con.close()


def to_xy(lat, lon):
    return fw.transform(lon, lat)


def dest(lat, lon, bearing_deg, dist_m):
    """출발점에서 방위(북 0°, 시계 방향)와 거리로 간 점(구면 근사)."""
    R = 6371000.0
    p1, l1, b = math.radians(lat), math.radians(lon), math.radians(bearing_deg)
    d = dist_m / R
    p2 = math.asin(math.sin(p1) * math.cos(d) + math.cos(p1) * math.sin(d) * math.cos(b))
    l2 = l1 + math.atan2(math.sin(b) * math.sin(d) * math.cos(p1), math.cos(d) - math.sin(p1) * math.sin(p2))
    return math.degrees(p2), math.degrees(l2)


xs = [x for x, _ in P.values()]; ys = [y for _, y in P.values()]
x0, x1, y0, y1 = min(xs) - 1300, max(xs) + 1300, min(ys) - 1300, max(ys) + 1300
fig, axs = plt.subplots(2, 2, figsize=(12, 9.6), dpi=110)
for ax, (st, (lat, lon, T)) in zip(axs.flat, START.items()):
    for gx, gy in tiles:   # 실험 범위 = 1:1,000 도엽 칸
        (a, b_), (c, d) = to_xy(gy * 0.005, gx * 0.005), to_xy((gy + 1) * 0.005, (gx + 1) * 0.005)
        ax.add_patch(Rectangle((a, b_), c - a, d - b_, fc="#eef3f8", ec="#d2deea", lw=0.4, zorder=0))
    ax.add_collection(LineCollection(SEG, colors="#c9c8c3", linewidths=0.25, zorder=1))
    sx, sy = to_xy(lat, lon)
    used = anch.get(st, {})
    for i in range(16):
        if i in used:
            ax_, ay_ = to_xy(*used[i])
            ax.plot([sx, ax_], [sy, ay_], color="#2a78d6", lw=0.8, zorder=2)
            ax.scatter([ax_], [ay_], marker="^", s=30, color="#2a78d6", zorder=4)
        else:
            ax_, ay_ = to_xy(*dest(lat, lon, 22.5 * i, 0.38 * T))
            ax.plot([sx, ax_], [sy, ay_], color="#e34948", lw=0.8, ls=(0, (3, 2)), zorder=2)
            ax.scatter([ax_], [ay_], marker="x", s=36, color="#e34948", lw=1.2, zorder=4)
    ax.scatter([sx], [sy], marker="s", s=40, color="black", zorder=5)
    ax.set_title(f"{NAME[st]}: 16방향 중 {len(used)}개 사용, {16 - len(used)}개 빠짐", fontsize=12, loc="left")
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
fig.text(0.01, 0.005, "연한 파랑 칸 = 실험 범위(1:1,000 지도가 있는 114칸), ▲ 파랑 = 범위 안이라 쓴 안내점, ✕ 빨강 = 범위 밖이라 뺀 방향(출발점에서 0.38T)",
         fontsize=11)
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig(os.path.join(HERE, "안내점_범위.png"), facecolor="white")
print({st: len(v) for st, v in anch.items()}, sum(len(v) for v in anch.values()))

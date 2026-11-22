"""실험 자료 그림(시안, 2026-11-11 사용자 요청): 실험 도로망 위에 선호 항목 8가지의 노드 속성을 칸마다 그린다.
자료는 로컬 DB gildongmu_v3(노드·간선·고도)와 ../../실험/동선개선_1110/노드속성_v3c.csv만 읽는다. 외부로 보내지 않는다.
실행: py -I 원고/그림_v4/make_fig_data.py → 그림_자료.png
"""
import csv
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np
import pymysql
from pyproj import Transformer

sys.stdout.reconfigure(encoding="utf-8")
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False
HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), "실험")   # HERE = 원고/작업_v4/그림_v4
INK, ROAD, BLUE = "#1f1f1f", "#d6d5d0", "#2a78d6"
MM = 1 / 25.4
fw = Transformer.from_crs(4326, 5179, always_xy=True)
START = {"탑동": (33.515, 126.522), "시청": (33.499, 126.531), "연동": (33.489, 126.490), "이도동": (33.499, 126.541)}

pw = re.search(r'password="([^"]*)"', open(r"C:\Users\seungjun\Documents\claude_code\논문\데이터사이언스학회\04_실험\새그래프_만들기\build_v2b_graph.py", encoding="utf-8").read()).group(1)
con = pymysql.connect(host="localhost", user="root", password=pw, db="gildongmu_v3")
cur = con.cursor()
cur.execute("SELECT point_id, latitude, longitude, elevation_meters FROM jeju_road_points")
rows = cur.fetchall()
cur.execute("SELECT from_point_id, to_point_id, distance_meters FROM jeju_road_edges WHERE from_point_id < to_point_id")
edges = cur.fetchall()
con.close()

ids = np.array([int(r[0]) for r in rows])
X, Y = fw.transform([float(r[2]) for r in rows], [float(r[1]) for r in rows])
XY = np.c_[X, Y]
idx = {int(i): k for k, i in enumerate(ids)}
elev = np.array([float(r[3]) if r[3] is not None else np.nan for r in rows])
E = np.array([(idx[int(a)], idx[int(b)], float(d)) for a, b, d in edges])
ea, eb, el = E[:, 0].astype(int), E[:, 1].astype(int), E[:, 2]
SEG = np.stack([XY[ea], XY[eb]], axis=1)
grade = np.abs(elev[eb] - elev[ea]) / np.maximum(el, 0.5) * 100
fs = np.clip((grade - 2) / 20, 0, 1)
fs[np.isnan(fs)] = 0

A = {int(r["point_id"]): r for r in csv.DictReader(open(os.path.join(EXP, "동선개선_1110", "노드속성_v3c.csv"), encoding="utf-8"))}
col = lambda key, f: np.array([f(A[int(i)][key]) for i in ids])
sig = col("signal", lambda v: v == "1")
fac = col("facility_m", float)
lit = col("lit", lambda v: v == "1")
wat = col("water_m", lambda v: float(v) <= 50)
side = col("sidewalk", lambda v: v == "1")
green = col("green", lambda v: v == "1")
big = col("quiet", lambda v: v != "1")
n = len(ids)
print(f"노드 {n:,}, 간선 {len(edges):,}, 경사>2% 간선 길이 비율 {el[grade > 2].sum() / el.sum():.2f}")
for nm, m in (("신호", sig), ("조명", lit), ("물가", wat), ("보도", side), ("녹지", green), ("큰길", big)):
    print(nm, int(m.sum()), f"{m.mean() * 100:.0f}%")
print("시설 500 m 안", f"{(fac < 500).mean() * 100:.0f}%", "중앙값", f"{np.median(fac):.0f} m")

x0, y0 = XY.min(0) - 150
x1, y1 = XY.max(0) + 150
print(f"범위 {(x1 - x0) / 1000:.1f} x {(y1 - y0) / 1000:.1f} km")
SX = {k: fw.transform(v[1], v[0]) for k, v in START.items()}


def base(ax, title):
    ax.add_collection(LineCollection(SEG, colors=ROAD, linewidths=0.2, zorder=1))
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_color("#b9b8b3"); sp.set_linewidth(0.4)
    ax.set_title(title, fontsize=6.2, pad=2)


def starts(ax, names=False):
    for k, (sx, sy) in SX.items():
        ax.scatter([sx], [sy], marker="s", s=6, color=INK, lw=0, zorder=8)
        if names:
            ax.text(sx + 120, sy + 90, k, fontsize=5, color=INK, zorder=9,
                    bbox=dict(fc="white", ec="none", alpha=0.8, pad=0.4))


def dots(ax, m, s=0.35, color=BLUE):
    ax.scatter(XY[m, 0], XY[m, 1], s=s, color=color, lw=0, zorder=3)


def draw(rows, cols, width_mm, fname):
    """8칸을 rows x cols로 그린다. 한 단 폭(4x2, 80 mm)과 전체 폭(2x4, 150 mm) 둘 다 이 함수로 만든다."""
    asp = (y1 - y0) / (x1 - x0)
    pw_ = (width_mm - 2) / cols
    fig, axs = plt.subplots(rows, cols, figsize=(width_mm * MM, rows * (pw_ * asp + 5.5) * MM), dpi=300)
    A_ = axs.flat
    # 회색 선 = 실험 도로망(모든 칸 공통), 파랑 = 그 항목, ■ = 출발점(이름은 (a)에만)
    ax = A_[0]
    base(ax, "(a) 경사 2% 초과 (진할수록 급함)")
    m = fs > 0
    ax.add_collection(LineCollection(SEG[m], colors=plt.cm.Blues(0.35 + 0.65 * fs[m]), linewidths=0.6, zorder=3))
    starts(ax, names=True)
    ax.plot([x1 - 1150, x1 - 150], [y0 + 180, y0 + 180], color=INK, lw=0.7)
    ax.text(x1 - 650, y0 + 260, "1 km", ha="center", fontsize=5)
    ax = A_[1]
    base(ax, f"(b) 신호 교차로 {int(sig.sum())}곳")
    dots(ax, sig, s=1.6)
    ax = A_[2]
    base(ax, "(c) 편의시설 (진할수록 가까움)")
    o = np.argsort(-fac)
    ax.scatter(XY[o, 0], XY[o, 1], s=0.3, c=1 - np.minimum(fac[o], 500) / 500, cmap="Blues", vmin=-0.15, vmax=1, lw=0, zorder=3)
    for ax, (t, m) in zip(list(A_)[3:], [(f"(d) 조명 25 m 안 ({lit.mean() * 100:.0f}%)", lit),
                                         (f"(e) 해안·하천 50 m 안 ({wat.mean() * 100:.0f}%)", wat),
                                         (f"(f) 인도 20 m 안 ({side.mean() * 100:.0f}%)", side),
                                         (f"(g) 도시공원 안 ({green.mean() * 100:.0f}%)", green),
                                         (f"(h) 폭 20 m 이상 큰길 ({big.mean() * 100:.0f}%)", big)]):
        base(ax, t)
        dots(ax, m)
    for ax in list(A_)[1:]:
        starts(ax)
    fig.subplots_adjust(left=0.005, right=0.995, top=1 - 4.5 / (rows * (pw_ * asp + 5.5)), bottom=0.005,
                        wspace=0.03, hspace=5.5 / (pw_ * asp))
    fig.savefig(os.path.join(HERE, fname), dpi=300, facecolor="white")
    plt.close(fig)


draw(4, 2, 80, "그림_자료.png")             # 원고용: 한 단 폭(사용자 11/11, 표·그림 양식 맞춤)
draw(2, 4, 150, "그림_자료_전체폭.png")      # 되돌릴 때 쓸 전체 폭 판
print("끝")

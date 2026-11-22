"""정보기술학회 버전(LOOP_V2 + 선호 비용) 경로 보기: 출발점 4곳, 안내점 0번, 기준 설정 (0,0,0)에서 서버가 돌려준 고유 경로(최대 3개).
자료: 본실험.json(새로 돌리지 않음). 색: 파랑·주황·초록(선 모양도 다르게), 점은 신호 교차로 노드.
결과: 본실험_반환경로.png   실행: py -I plot_returned_routes.py
"""
import csv
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(EXP, "데이터진단_1109", "수집계획용", "에이전트검토"))
from lib_shp import read_shp

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False
ROAD = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵\연속수치지도_제주_20261109\풀기\N3L_A0020000\N3L_A0020000"
g = np.load(os.path.join(EXP, "도심실험_1110", "그래프_도심_114칸.npz"))
gl, ga, gb, main = g["line"], g["a"], g["b"], g["main"]
lines = [p for r, parts in read_shp(ROAD, clip=False) for p in parts]
segs = [lines[gl[e]][ga[e]:gb[e] + 1] for e in np.where(main)[0].tolist()]
sig = np.array([(float(r["x5179"]), float(r["y5179"])) for r in csv.DictReader(open(os.path.join(EXP, "도심실험_1110", "신호노드_114칸.csv"), encoding="utf-8-sig"))])
R = json.load(open(os.path.join(HERE, "본실험.json"), encoding="utf-8"))
fw = Transformer.from_crs(4326, 5179, always_xy=True)
STY = [("#2a78d6", "-", 2.6), ("#eb6834", "--", 2.2), ("#1baf7a", ":", 2.6)]

fig, axs = plt.subplots(2, 2, figsize=(13, 15.5), facecolor="#fcfcfb")
for ax, (name, T) in zip(axs.flat, [("탑동", 3000), ("도심", 5000), ("연동", 3000), ("이도", 4000)]):
    ms = sorted([m for m in R if m["start"] == name and m["anchor_id"] == 0 and m["setting"] == "기준"], key=lambda m: m["route"])
    xy = []
    for m in ms:
        ll = np.array(m["coords"])
        X, Y = fw.transform(ll[:, 1], ll[:, 0])
        xy.append(np.c_[X, Y])
    an = fw.transform(ms[0]["anchor"][1], ms[0]["anchor"][0])
    P = np.vstack(xy + [np.array([an])])
    x0, y0 = P.min(0) - 200
    x1, y1 = P.max(0) + 200
    span = max(x1 - x0, y1 - y0)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    x0, x1, y0, y1 = cx - span / 2, cx + span / 2, cy - span / 2, cy + span / 2
    for p in segs:
        if p[:, 0].max() < x0 or p[:, 0].min() > x1 or p[:, 1].max() < y0 or p[:, 1].min() > y1:
            continue
        ax.plot(p[:, 0], p[:, 1], color="#d6d5d0", lw=0.6, zorder=1)
    inb = (sig[:, 0] > x0) & (sig[:, 0] < x1) & (sig[:, 1] > y0) & (sig[:, 1] < y1)
    ax.scatter(sig[inb, 0], sig[inb, 1], s=12, facecolors="none", edgecolors="#52514e", linewidths=0.7, zorder=2, label="신호 교차로 노드")
    for k, (m, q) in enumerate(zip(ms, xy)):
        c, ls, lw = STY[k]
        ax.plot(q[:, 0], q[:, 1], color=c, ls=ls, lw=lw, zorder=3 + k, solid_capstyle="round",
                label=f"경로 {k + 1}: {m['length'] / 1000:.2f} km (오차 {m['err'] * 100:.1f}%), 경사 {m['slope']:.1f}%, 신호 {m['signals']}회, 시설 {m['facility_m']:.0f} m")
    sx, sy = xy[0][0]
    ax.scatter([sx], [sy], marker="s", s=90, color="#0b0b0b", zorder=8)
    ax.annotate("출발", (sx, sy), xytext=(8, 8), textcoords="offset points", fontsize=11)
    ax.scatter([an[0]], [an[1]], marker="^", s=90, color="#0b0b0b", zorder=8)
    ax.annotate("안내점", an, xytext=(8, -14), textcoords="offset points", fontsize=11)
    ax.plot([x1 - 600, x1 - 100], [y0 + 120, y0 + 120], color="#52514e", lw=2)
    ax.text(x1 - 350, y0 + 160, "500 m", ha="center", fontsize=10, color="#52514e")
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_color("#d6d5d0")
    ax.set_title(f"{name} {T / 1000:.0f} km: 경로 {len(ms)}개", fontsize=14, loc="left")
    ax.legend(loc="upper left", bbox_to_anchor=(0, -0.01), fontsize=9, frameon=False)
fig.suptitle("정보기술학회 버전 경로 예: 기준 설정 (0,0,0), 안내점 0번에서 돌려준 경로", fontsize=15, x=0.02, ha="left")
fig.subplots_adjust(left=0.03, right=0.98, top=0.94, bottom=0.07, hspace=0.30, wspace=0.06)
fig.savefig(os.path.join(HERE, "본실험_반환경로.png"), dpi=110, facecolor="#fcfcfb")
print("끝")

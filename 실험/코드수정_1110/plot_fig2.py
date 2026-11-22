"""원고 그림 2 (한 단 폭 71 mm): 같은 출발점·안내점에서 기준 설정과 신호 회피 α=10의 첫 경로, 신호 교차로 노드 표시.
예 고르는 규칙: 47개 요청 중 '신호 회피 α=10 첫 경로 − 기준 첫 경로'의 km당 신호 수 차이가 중앙값에 가장 가까운 요청
(가장 극적인 예를 고르지 않음). 결과: 탑동 안내점 5.
색: 기준 #52514e 실선, 신호 회피 #eb6834 점선(dataviz 검증한 팔레트). 경로가 지나는 신호는 경로 색으로 채움.
결과: 그림2_본실험.png   실행: py -I plot_fig2.py
"""
import collections
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
SRCJ = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "본실험.json")   # 인자: [결과 json] [출력 접미사]
SUF = sys.argv[2] if len(sys.argv) > 2 else ""
EXP = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(EXP, "데이터진단_1109", "수집계획용", "에이전트검토"))
from lib_shp import read_shp

sys.stdout.reconfigure(encoding="utf-8")
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False
R = json.load(open(SRCJ, encoding="utf-8"))
g = collections.defaultdict(list)
for m in R:
    g[(m["start"], m["anchor_id"], m["setting"])].append(m)
first = lambda k, s: min(g[(k[0], k[1], s)], key=lambda m: m["route"])
keys = sorted({(m["start"], m["anchor_id"]) for m in R})
diff = {k: first(k, "신호회피10")["signals_per_km"] - first(k, "기준")["signals_per_km"] for k in keys}
med = float(np.median(list(diff.values())))
ORDER = ["탑동", "도심", "연동", "이도"]
pick = min(keys, key=lambda k: (abs(diff[k] - med), ORDER.index(k[0]), k[1]))
print("중앙값", round(med, 3), "고른 요청", pick, round(diff[pick], 3))

ROAD = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵\연속수치지도_제주_20261109\풀기\N3L_A0020000\N3L_A0020000"
gr = np.load(os.path.join(EXP, "도심실험_1110", "그래프_도심_114칸.npz"))
gl, ga, gb, main = gr["line"], gr["a"], gr["b"], gr["main"]
lines = [p for r, parts in read_shp(ROAD, clip=False) for p in parts]
segs = [lines[gl[e]][ga[e]:gb[e] + 1] for e in np.where(main)[0].tolist()]
sig = np.array([(float(r["x5179"]), float(r["y5179"])) for r in csv.DictReader(open(os.path.join(EXP, "도심실험_1110", "신호노드_114칸.csv"), encoding="utf-8-sig"))])
fw = Transformer.from_crs(4326, 5179, always_xy=True)

R0, R1 = first(pick, "기준"), first(pick, "신호회피10")
xy = {}
for nm, m in (("기준", R0), ("신호", R1)):
    ll = np.array(m["coords"])
    X, Y = fw.transform(ll[:, 1], ll[:, 0])
    xy[nm] = np.c_[X, Y]
P = np.vstack(list(xy.values()) + [np.array([fw.transform(R0["anchor"][1], R0["anchor"][0])])])
x0, y0 = P.min(0) - 120
x1, y1 = P.max(0) + 120
span = max(x1 - x0, y1 - y0)
cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
x0, x1, y0, y1 = cx - span / 2, cx + span / 2, cy - span / 2, cy + span / 2

fig = plt.figure(figsize=(2.8, 3.07), dpi=300, facecolor="white")
ax = fig.add_axes([0.01, 0.145, 0.98, 0.845])
for p in segs:
    if p[:, 0].max() < x0 or p[:, 0].min() > x1 or p[:, 1].max() < y0 or p[:, 1].min() > y1:
        continue
    ax.plot(p[:, 0], p[:, 1], color="#d6d5d0", lw=0.4, zorder=1)
inb = (sig[:, 0] > x0) & (sig[:, 0] < x1) & (sig[:, 1] > y0) & (sig[:, 1] < y1)
ax.scatter(sig[inb, 0], sig[inb, 1], s=9, facecolors="white", edgecolors="#0b0b0b", linewidths=0.6, zorder=5)
ts = cKDTree = None
from scipy.spatial import cKDTree
tsig = cKDTree(sig)
STY = {"기준": ("#52514e", "-", 1.8), "신호": ("#eb6834", (0, (3, 1.5)), 1.3)}
for nm, m in (("기준", R0), ("신호", R1)):
    c, ls, lw = STY[nm]
    ax.plot(xy[nm][:, 0], xy[nm][:, 1], color=c, ls=ls, lw=lw, zorder=3 if nm == "기준" else 4, solid_capstyle="round")
    d, i = tsig.query(xy[nm][1:-1])
    hit = np.unique(i[d < 1.0])
    ax.scatter(sig[hit, 0], sig[hit, 1], s=13, color=c, edgecolors="#0b0b0b", linewidths=0.5, zorder=6)
sx, sy = xy["기준"][0]
ax.scatter([sx], [sy], marker="s", s=22, color="#0b0b0b", zorder=7)
ax.annotate("출발", (sx, sy), xytext=(4, -9), textcoords="offset points", fontsize=7)
ax_, ay_ = fw.transform(R0["anchor"][1], R0["anchor"][0])
ax.scatter([ax_], [ay_], marker="^", s=24, color="#0b0b0b", zorder=7)
ax.annotate("안내점", (ax_, ay_), xytext=(4, 3), textcoords="offset points", fontsize=7)
ax.plot([x1 - 560, x1 - 60], [y0 + 70, y0 + 70], color="#52514e", lw=1.2)
ax.text(x1 - 310, y0 + 100, "500 m", ha="center", fontsize=6.5, color="#52514e")
ax.set_xlim(x0, x1)
ax.set_ylim(y0, y1)
ax.set_aspect("equal")
ax.set_xticks([])
ax.set_yticks([])
for sp in ax.spines.values():
    sp.set_color("#a3a29d")
    sp.set_linewidth(0.5)
from matplotlib.lines import Line2D
hd = [Line2D([], [], color="#52514e", lw=1.8, label=f"기준 (0, 0, 0): {R0['length'] / 1000:.2f} km, 신호 통과 {R0['signals']}회"),
      Line2D([], [], color="#eb6834", lw=1.3, ls=(0, (3, 1.5)), label=f"신호 회피 $\\alpha_c$=10: {R1['length'] / 1000:.2f} km, 신호 통과 {R1['signals']}회")]
# 원(신호 교차로 노드)과 채운 원(경로가 지나는 곳)의 뜻은 원고 그림 설명에 적는다(범례 2줄로 높이를 줄임).
fig.legend(handles=hd, loc="lower left", bbox_to_anchor=(0.01, 0.0), fontsize=6.5, frameon=False, handlelength=2.2)
fig.savefig(os.path.join(HERE, f"그림2_본실험{SUF}.png"), dpi=300, facecolor="white")
print("기준", R0["signals"], round(R0["length"]), "신호회피10", R1["signals"], round(R1["length"]))

"""시험 결과 그림: 출발점 4곳(예비 안내점 0번), 왼쪽 '없음'(지금 방식), 오른쪽 고른 설정. 경로는 응답의 고유 경로 전부.
결과: 시험_비교.png   실행: py -I plot_dev.py [설정이름=근접100x3+회전60]
"""
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
PICK = sys.argv[1] if len(sys.argv) > 1 else "근접100x3+회전60"
ROAD = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵\연속수치지도_제주_20261109\풀기\N3L_A0020000\N3L_A0020000"
g = np.load(os.path.join(EXP, "도심실험_1110", "그래프_도심_114칸.npz"))
gl, ga, gb, main = g["line"], g["a"], g["b"], g["main"]
lines = [p for r, parts in read_shp(ROAD, clip=False) for p in parts]
segs = [lines[gl[e]][ga[e]:gb[e] + 1] for e in np.where(main)[0].tolist()]
R = json.load(open(os.path.join(HERE, "시험결과.json"), encoding="utf-8"))
fw = Transformer.from_crs(4326, 5179, always_xy=True)
COL = [("#2a78d6", "-", 2.4), ("#eb6834", "--", 2.0), ("#1baf7a", ":", 2.4)]
STARTS = ["탑동", "도심", "연동", "이도"]
fig, axs = plt.subplots(4, 2, figsize=(11, 22), facecolor="#fcfcfb")
for row, st in enumerate(STARTS):
    recs = {x["set"]: x for x in R if x["start"] == st and x["anchor_id"] == 0}
    allp = []
    for nm in ("없음", PICK):
        for m in recs[nm]["routes"]:
            ll = np.array(m["coords"])
            X, Y = fw.transform(ll[:, 1], ll[:, 0])
            allp.append(np.c_[X, Y])
    P = np.vstack(allp)
    x0, y0 = P.min(0) - 150
    x1, y1 = P.max(0) + 150
    span = max(x1 - x0, y1 - y0)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    x0, x1, y0, y1 = cx - span / 2, cx + span / 2, cy - span / 2, cy + span / 2
    for col, nm in enumerate(("없음", PICK)):
        ax = axs[row, col]
        for p in segs:
            if p[:, 0].max() < x0 or p[:, 0].min() > x1 or p[:, 1].max() < y0 or p[:, 1].min() > y1:
                continue
            ax.plot(p[:, 0], p[:, 1], color="#d6d5d0", lw=0.5, zorder=1)
        for k, m in enumerate(recs[nm]["routes"]):
            ll = np.array(m["coords"])
            X, Y = fw.transform(ll[:, 1], ll[:, 0])
            c, ls, lw = COL[k % 3]
            ax.plot(X, Y, color=c, ls=ls, lw=lw, zorder=3 + k,
                    label=f"{m['length'] / 1000:.2f} km, 둥근 {m['comp']:.2f}, 회전 {m['turns_km']:.1f}/km")
        sx, sy = fw.transform(recs[nm]["routes"][0]["coords"][0][1], recs[nm]["routes"][0]["coords"][0][0])
        ax.scatter([sx], [sy], marker="s", s=60, color="#0b0b0b", zorder=8)
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_color("#d6d5d0")
        ax.set_title(f"{st}: {'지금 방식' if nm == '없음' else nm}", loc="left", fontsize=12)
        ax.legend(loc="upper left", bbox_to_anchor=(0, -0.005), fontsize=8.5, frameon=False)
fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.04, hspace=0.32, wspace=0.05)
fig.savefig(os.path.join(HERE, "시험_비교.png"), dpi=100, facecolor="#fcfcfb")
print("끝")

"""본 실험 경로 그림(plot_prelim.py에서 설정 이름만 바꿈, α=10): 출발점마다 안내점 0번, 네 설정의 첫 경로를 한 판에 그린다. 배경은 실험 그래프(회색), 점은 신호 교차로.
색: 기준 회색 실선, 평지 파랑, 신호 회피 주황, 시설 청록(dataviz 검증 통과, 청록 대비 경고 → 선 모양·범례로 보완).
결과: 본실험_경로그림.png   실행: py -I plot_prelim.py
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
xy, main, gl, ga, gb = g["xy"], g["main"], g["line"], g["a"], g["b"]
lines = [p for r, parts in read_shp(ROAD, clip=False) for p in parts]
segs = [lines[gl[e]][ga[e]:gb[e] + 1] for e in np.where(main)[0].tolist()]
sig = np.array([(float(r["x5179"]), float(r["y5179"])) for r in csv.DictReader(open(os.path.join(EXP, "도심실험_1110", "신호노드_114칸.csv"), encoding="utf-8-sig"))])
R = json.load(open(os.path.join(HERE, "본실험.json"), encoding="utf-8"))
fw = Transformer.from_crs(4326, 5179, always_xy=True)
STYLE = {"기준": ("#52514e", "-", 3.2, "기준 (0,0,0)"), "평지10": ("#2a78d6", "-", 2.0, "평지 α=10"),
         "신호회피10": ("#eb6834", "--", 2.0, "신호 회피 α=10"), "시설10": ("#1baf7a", ":", 2.4, "시설 근접 α=10")}
fig, axs = plt.subplots(2, 2, figsize=(13, 16.5), facecolor="#fcfcfb")
for ax, (name, T) in zip(axs.flat, [("탑동", 3000), ("도심", 5000), ("연동", 3000), ("이도", 4000)]):
    ms = {m["setting"]: m for m in R if m["start"] == name and m["anchor_id"] == 0 and m["route"] == min(x["route"] for x in R if x["start"] == name and x["anchor_id"] == 0 and x["setting"] == m["setting"])}
    allp = []
    for s, m in ms.items():
        ll = np.array(m["coords"])
        X, Y = fw.transform(ll[:, 1], ll[:, 0])
        allp.append(np.c_[X, Y])
    P = np.vstack(allp)
    x0, y0 = P.min(0) - 250
    x1, y1 = P.max(0) + 250
    span = max(x1 - x0, y1 - y0)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    x0, x1, y0, y1 = cx - span / 2, cx + span / 2, cy - span / 2, cy + span / 2
    for p in segs:
        if p[:, 0].max() < x0 or p[:, 0].min() > x1 or p[:, 1].max() < y0 or p[:, 1].min() > y1:
            continue
        ax.plot(p[:, 0], p[:, 1], color="#d6d5d0", lw=0.6, zorder=1)
    m_s = (sig[:, 0] > x0) & (sig[:, 0] < x1) & (sig[:, 1] > y0) & (sig[:, 1] < y1)
    ax.scatter(sig[m_s, 0], sig[m_s, 1], s=14, facecolors="none", edgecolors="#0b0b0b", linewidths=0.8, zorder=5, label="신호 교차로 노드")
    for s in ["기준", "평지10", "신호회피10", "시설10"]:
        if s not in ms:
            continue
        m = ms[s]
        ll = np.array(m["coords"])
        X, Y = fw.transform(ll[:, 1], ll[:, 0])
        c, ls, lw, lab = STYLE[s]
        ax.plot(X, Y, color=c, ls=ls, lw=lw, zorder=3 if s == "기준" else 4, solid_capstyle="round",
                label=f"{lab}: {m['length'] / 1000:.2f} km, 경사 {m['slope']:.1f}%, 신호 {m['signals']}개, 시설 {m['facility_m']:.0f} m")
    sx, sy = fw.transform(ms["기준"]["coords"][0][1], ms["기준"]["coords"][0][0])
    ax.scatter([sx], [sy], marker="s", s=90, color="#0b0b0b", zorder=6)
    ax.annotate("출발", (sx, sy), xytext=(8, 8), textcoords="offset points", fontsize=11, color="#0b0b0b", zorder=7)
    an = ms["기준"]["anchor"]
    ax_, ay_ = fw.transform(an[1], an[0])
    ax.scatter([ax_], [ay_], marker="^", s=90, color="#0b0b0b", zorder=6)
    ax.annotate("안내점", (ax_, ay_), xytext=(8, -14), textcoords="offset points", fontsize=11, color="#0b0b0b", zorder=7)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_color("#d6d5d0")
    ax.set_title(f"{name} {T / 1000:.0f} km (안내점 0번)", fontsize=14, color="#0b0b0b", loc="left")
    ax.plot([x1 - 600, x1 - 100], [y0 + 120, y0 + 120], color="#52514e", lw=2)
    ax.text(x1 - 350, y0 + 160, "500 m", ha="center", fontsize=10, color="#52514e")
    ax.legend(loc="upper left", bbox_to_anchor=(0, -0.01), fontsize=9, frameon=False)
fig.suptitle("본 실험 예: 같은 출발점·안내점에서 선호 설정만 바꾼 경로 (α=10, τ=2%, κ=100 m, λp=1)", fontsize=15, x=0.02, ha="left", color="#0b0b0b")
fig.subplots_adjust(left=0.03, right=0.98, top=0.93, bottom=0.08, hspace=0.30, wspace=0.06)
fig.savefig(os.path.join(HERE, "본실험_경로그림.png"), dpi=130, facecolor="#fcfcfb")
print("끝")

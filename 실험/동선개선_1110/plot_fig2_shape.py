"""원고 그림 2 (한 단 폭): 같은 출발점·안내점에서 (a) 모양 벌점 전(1차 본실험 기준 설정) (b) 러닝 동선 모양 반영(본실험2 기준 설정)의 첫 경로.
예 고르는 규칙: 47개 요청 중 첫 경로 둥근 정도의 개선폭(b − a)이 중앙값에 가장 가까운 요청(극적인 예를 고르지 않음).
결과: 그림2_모양.png   실행: py -I plot_fig2_shape.py
"""
import json
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
OLD = os.path.join(EXP, "코드수정_1110")
sys.path.insert(0, os.path.join(EXP, "데이터진단_1109", "수집계획용", "에이전트검토"))
from lib_shp import read_shp

sys.stdout.reconfigure(encoding="utf-8")
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False
fw = Transformer.from_crs(4326, 5179, always_xy=True)


def first_base(path):
    d = {}
    for m in json.load(open(path, encoding="utf-8")):
        if m["setting"] != "기준":
            continue
        k = (m["start"], m["anchor_id"])
        if k not in d or m["route"] < d[k]["route"]:
            d[k] = m
    return d


def xy(m):
    ll = np.array(m["coords"])
    X, Y = fw.transform(ll[:, 1], ll[:, 0])
    return np.c_[X, Y]


def comp(m):
    P = xy(m)
    area = 0.5 * abs(np.dot(P[:-1, 0], P[1:, 1]) - np.dot(P[1:, 0], P[:-1, 1]))
    return 4 * math.pi * area / (m["length"] ** 2)


A = first_base(os.path.join(OLD, "본실험.json"))
B = first_base(os.path.join(HERE, "본실험2.json"))
keys = sorted(set(A) & set(B))
gain = {k: comp(B[k]) - comp(A[k]) for k in keys}
med = float(np.median(list(gain.values())))
ORDER = ["탑동", "도심", "연동", "이도"]
pick = min(keys, key=lambda k: (abs(gain[k] - med), ORDER.index(k[0]), k[1]))
print("둥근 정도 개선폭 중앙값", round(med, 3), "고른 요청", pick, "전", round(comp(A[pick]), 2), "후", round(comp(B[pick]), 2))

ROAD = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵\연속수치지도_제주_20261109\풀기\N3L_A0020000\N3L_A0020000"
g = np.load(os.path.join(EXP, "도심실험_1110", "그래프_도심_114칸.npz"))
gl, ga, gb, main = g["line"], g["a"], g["b"], g["main"]
lines = [p for r, parts in read_shp(ROAD, clip=False) for p in parts]
segs = [lines[gl[e]][ga[e]:gb[e] + 1] for e in np.where(main)[0].tolist()]
Pa, Pb = xy(A[pick]), xy(B[pick])
an = np.array(fw.transform(A[pick]["anchor"][1], A[pick]["anchor"][0]))
P = np.vstack([Pa, Pb, an[None]])
x0, y0 = P.min(0) - 100
x1, y1 = P.max(0) + 100
span = max(x1 - x0, y1 - y0)
cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
x0, x1, y0, y1 = cx - span / 2, cx + span / 2, cy - span / 2, cy + span / 2

fig, axs = plt.subplots(1, 2, figsize=(2.8, 1.72), dpi=300, facecolor="white")
for ax, (lab, m, Q, c) in zip(axs, [("(a) 모양 벌점 전", A[pick], Pa, "#52514e"), ("(b) 러닝 동선 반영", B[pick], Pb, "#2a78d6")]):
    for p in segs:
        if p[:, 0].max() < x0 or p[:, 0].min() > x1 or p[:, 1].max() < y0 or p[:, 1].min() > y1:
            continue
        ax.plot(p[:, 0], p[:, 1], color="#dcdbd6", lw=0.3, zorder=1)
    ax.plot(Q[:, 0], Q[:, 1], color=c, lw=1.4, zorder=3, solid_capstyle="round")
    ax.scatter([Q[0, 0]], [Q[0, 1]], marker="s", s=10, color="#0b0b0b", zorder=5)
    ax.scatter([an[0]], [an[1]], marker="^", s=11, color="#0b0b0b", zorder=5)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_color("#a3a29d")
        sp.set_linewidth(0.4)
    ax.set_title(lab, fontsize=6.5, pad=2)
    ax.text(0.03, -0.04, f"{m['length'] / 1000:.2f} km, 둥근 정도 {comp(m):.2f}", transform=ax.transAxes, fontsize=5.6, va="top")
axs[1].plot([x1 - 560, x1 - 60], [y0 + 60, y0 + 60], color="#52514e", lw=0.8)
axs[1].text(x1 - 310, y0 + 90, "500 m", ha="center", fontsize=5.2, color="#52514e")
fig.subplots_adjust(left=0.01, right=0.99, top=0.9, bottom=0.12, wspace=0.05)
fig.savefig(os.path.join(HERE, "그림2_모양.png"), dpi=300, facecolor="white")
print("끝", pick)

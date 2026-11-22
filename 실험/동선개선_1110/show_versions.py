"""사용자에게 보여 주는 그림(원고용 아님, 2026-11-11): 알고리즘 단계별 동선 비교.
열: (1) 데이터사이언스 방식 = 빔 귀환(../코드수정_1110/표2.json '빔 귀환', 같은 v3 그래프·같은 안내점)
    (2) 최단 비용 귀환 γ=5 (1차 본실험 기준 설정) (3) + 러닝 모양 (본실험2 기준) (4) + 신호 회피 α=10 (본실험2)
행: 출발점 네 곳. 요청은 show_overview.py와 같은 규칙(출발점마다 (2)→(3) 둥근 정도 개선폭이 중앙값에 가까운 요청).
각 칸은 그 설정의 첫 경로. 결과: 보기_버전비교.png   실행: py -I show_versions.py
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
INK = "#2b2b2b"
START = {"탑동": (33.515, 126.522, 3000), "도심": (33.499, 126.531, 5000), "연동": (33.489, 126.490, 3000), "이도": (33.499, 126.541, 4000)}


def first(R, setting):
    d = {}
    for m in R:
        if m["setting"] != setting:
            continue
        k = (m["start"], m["anchor_id"])
        if k not in d or m["route"] < d[k]["route"]:
            d[k] = m
    return d


def xy(coords):
    ll = np.array(coords)
    X, Y = fw.transform(ll[:, 1], ll[:, 0])
    return np.c_[X, Y]


def comp(P, L):
    area = 0.5 * abs(np.dot(P[:-1, 0], P[1:, 1]) - np.dot(P[1:, 0], P[:-1, 1]))
    return 4 * math.pi * area / (L ** 2)


def retrace(P):
    seen, rt, tot = set(), 0.0, 0.0
    for a, b in zip(P[:-1], P[1:]):
        s = float(np.hypot(*(b - a)))
        tot += s
        k = tuple(sorted((tuple(np.round(a, 0)), tuple(np.round(b, 0)))))
        if k in seen:
            rt += s
        seen.add(k)
    return rt / tot if tot else 0.0


R1 = json.load(open(os.path.join(OLD, "본실험.json"), encoding="utf-8"))
R2 = json.load(open(os.path.join(HERE, "본실험2.json"), encoding="utf-8"))
T2 = json.load(open(os.path.join(OLD, "표2.json"), encoding="utf-8"))
beam = {(r["start"], r["anchor_id"]): r for r in T2 if r["conf"] == "빔 귀환"}
A, B, C = first(R1, "기준"), first(R2, "기준"), first(R2, "신호회피10")
keys = sorted(set(A) & set(B) & set(C) & set(beam))

ROAD = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵\연속수치지도_제주_20261109\풀기\N3L_A0020000\N3L_A0020000"
g = np.load(os.path.join(EXP, "도심실험_1110", "그래프_도심_114칸.npz"))
lines = [p for r, parts in read_shp(ROAD, clip=False) for p in parts]
segs = [lines[g["line"][e]][g["a"][e]:g["b"][e] + 1] for e in np.where(g["main"])[0].tolist()]

COLS = [("① 데이터사이언스 방식\n(빔으로 돌아오기)", "#8a8984"), ("② 최단 비용으로 돌아오기\n(되밟기 벌점 γ=5)", "#e8893a"),
        ("③ + 러닝 모양 벌점\n(정보기술 기준 설정)", "#2a78d6"), ("④ + 신호 회피 α=10\n(선호 반영 예)", "#1f5fae")]
fig, axs = plt.subplots(4, 4, figsize=(13, 13.6), dpi=120, facecolor="white")
for i, st in enumerate(["탑동", "도심", "연동", "이도"]):
    ks = [k for k in keys if k[0] == st]
    gain = {k: comp(xy(B[k]["coords"]), B[k]["length"]) - comp(xy(A[k]["coords"]), A[k]["length"]) for k in ks}
    med = float(np.median(list(gain.values())))
    k = min(ks, key=lambda k: (abs(gain[k] - med), k[1]))
    T = START[st][2]
    b0 = beam[k]["routes"][0] if beam[k]["routes"] else None
    items = [(b0["coords"], b0["length"]) if b0 else None, (A[k]["coords"], A[k]["length"]), (B[k]["coords"], B[k]["length"]), (C[k]["coords"], C[k]["length"])]
    Ps = [xy(c) for c, _ in [x for x in items if x]]
    an = np.array(fw.transform(B[k]["anchor"][1], B[k]["anchor"][0]))
    P = np.vstack(Ps + [an[None]])
    x0, y0 = P.min(0) - 150
    x1, y1 = P.max(0) + 150
    s = max(x1 - x0, y1 - y0)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    x0, x1, y0, y1 = cx - s / 2, cx + s / 2, cy - s / 2, cy + s / 2
    for j, ((lab, col), it) in enumerate(zip(COLS, items)):
        ax = axs[i, j]
        for p in segs:
            if p[:, 0].max() < x0 or p[:, 0].min() > x1 or p[:, 1].max() < y0 or p[:, 1].min() > y1:
                continue
            ax.plot(p[:, 0], p[:, 1], color="#dcdbd6", lw=0.4, zorder=1)
        if it is None:
            ax.text(0.5, 0.5, "경로 없음", transform=ax.transAxes, ha="center")
        else:
            Q = xy(it[0])
            L = it[1]
            ax.plot(Q[:, 0], Q[:, 1], color=col, lw=2.2, zorder=3, solid_capstyle="round")
            ax.scatter([Q[0, 0]], [Q[0, 1]], marker="s", s=22, color=INK, zorder=6)
            err = abs(L - T) / T
            rt = retrace(Q)
            txt = f"오차 {err * 100:.0f}%  되밟기 {rt * 100:.0f}%  둥근 정도 {comp(Q, L):.2f}"
            ax.text(0.02, 0.02, txt, transform=ax.transAxes, fontsize=7.6, color="#b3261e" if err > 0.1 or rt >= 0.4 else INK,
                    bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.5), zorder=7)
        ax.scatter([an[0]], [an[1]], marker="^", s=24, color=INK, zorder=6)
        ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal")
        ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_color("#c8c7c2"); sp.set_linewidth(0.5)
        if i == 0:
            ax.set_title(lab, fontsize=10.5, pad=6)
        if j == 0:
            ax.set_ylabel(f"{st} {T // 1000} km", fontsize=10.5)
    axs[i, 3].plot([x1 - 560, x1 - 60], [y0 + 70, y0 + 70], color=INK, lw=1)
    axs[i, 3].text(x1 - 310, y0 + 110, "500 m", ha="center", fontsize=7, color=INK)
    print(st, k)
fig.suptitle("같은 요청에서 알고리즘이 바뀌며 동선이 어떻게 달라졌나 · ■ 출발점 ▲ 안내점 · 각 칸은 첫 번째 경로 · 빨간 글씨 = 오차 10% 초과 또는 되밟기 40% 이상", fontsize=11)
fig.subplots_adjust(left=0.03, right=0.99, top=0.93, bottom=0.01, wspace=0.03, hspace=0.06)
fig.savefig(os.path.join(HERE, "보기_버전비교.png"), facecolor="white")
print("끝")

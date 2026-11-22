"""영어판 그림 4(구성 요소별 경로)·그림 5(선호별 경로), 포스터 전체 폭 (2026-11-13).

요청 고르는 규칙, 지표 계산(오차·되밟기·둥근 정도), 자료(본실험 json, 도로중심선, 노드속성, 로컬 DB gildongmu_v3)는
원고 그림 스크립트(원고/작업_v5/그림_v4/make_figs_v4.py)와 같다. 원고 스크립트는 고치지 않는다.
실행: python make_en_maps.py → 그림/compare_en.png, 그림/prefs_en.png
"""
import collections
import csv
import json
import math
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pymysql
from pyproj import Transformer

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.join(os.path.dirname(os.path.dirname(HERE)), "실험")
NEW = os.path.join(EXP, "동선개선_1110")
OLD = os.path.join(EXP, "코드수정_1110")
sys.path.insert(0, os.path.join(EXP, "데이터진단_1109", "수집계획용", "에이전트검토"))
from lib_shp import read_shp

plt.rcParams["font.family"] = "Arial"
plt.rcParams["axes.unicode_minus"] = False
fw = Transformer.from_crs(4326, 5179, always_xy=True)
INK, GRAY, BLUE, ORANGE = "#1f1f1f", "#8a8984", "#2a78d6", "#e8893a"
FS_T, FS_V = 8.0, 7.0   # 칸 제목, 칸 안 수치 글자 크기(pt)

ROAD = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵\연속수치지도_제주_20261109\풀기\N3L_A0020000\N3L_A0020000"
g = np.load(os.path.join(EXP, "도심실험_1110", "그래프_도심_114칸.npz"))
lines = [p for r, parts in read_shp(ROAD, clip=False) for p in parts]
segs = [lines[g["line"][e]][g["a"][e]:g["b"][e] + 1] for e in np.where(g["main"])[0].tolist()]


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


def first(R, setting):
    d = {}
    for m in R:
        if m["setting"] != setting:
            continue
        k = (m["start"], m["anchor_id"])
        if k not in d or m["route"] < d[k]["route"]:
            d[k] = m
    return d


def square(Ps, pad=120):
    P = np.vstack(Ps)
    x0, y0 = P.min(0) - pad
    x1, y1 = P.max(0) + pad
    s = max(x1 - x0, y1 - y0)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return cx - s / 2, cx + s / 2, cy - s / 2, cy + s / 2


def base_axes(ax, b):
    x0, x1, y0, y1 = b
    for p in segs:
        if p[:, 0].max() < x0 or p[:, 0].min() > x1 or p[:, 1].max() < y0 or p[:, 1].min() > y1:
            continue
        ax.plot(p[:, 0], p[:, 1], color="#d9d8d3", lw=0.3, zorder=1)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_color("#b9b8b3"); sp.set_linewidth(0.5)


def marks(ax, start_xy, anchor_xy):
    ax.scatter([start_xy[0]], [start_xy[1]], marker="s", s=14, color=INK, zorder=6, lw=0)
    ax.scatter([anchor_xy[0]], [anchor_xy[1]], marker="^", s=16, color=INK, zorder=6, lw=0)


def scalebar(ax, b, top=False):
    x0, x1, y0, y1 = b
    yb = y1 - 200 if top else y0 + 80
    ax.plot([x1 - 560, x1 - 60], [yb, yb], color=INK, lw=0.8)
    ax.text(x1 - 310, yb + 45, "500 m", ha="center", fontsize=FS_V, color=INK)


def note(ax, s):
    ax.text(0.03, 0.03, s, transform=ax.transAxes, fontsize=FS_V, linespacing=1.2,
            bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.2), zorder=7)


# ---------- 그림 4: 구성 요소별 경로 (연동) ----------
R1 = json.load(open(os.path.join(OLD, "본실험.json"), encoding="utf-8"))
R2 = json.load(open(os.path.join(NEW, "본실험2.json"), encoding="utf-8"))
T2 = json.load(open(os.path.join(OLD, "표2.json"), encoding="utf-8"))
beam = {(r["start"], r["anchor_id"]): r for r in T2 if r["conf"] == "빔 귀환"}
A, B = first(R1, "기준"), first(R2, "기준")
C = first(R2, "신호회피10")
keys = sorted(set(A) & set(B) & set(C) & set(beam))
ks = [k for k in keys if k[0] == "연동"]
gain = {k: comp(xy(B[k]["coords"]), B[k]["length"]) - comp(xy(A[k]["coords"]), A[k]["length"]) for k in ks}
med = float(np.median(list(gain.values())))
k2 = min(ks, key=lambda k: (abs(gain[k] - med), k[1]))
print("그림 4 요청", k2)
T = 3000
items = [("(a) Beam-search return", beam[k2]["routes"][0]["coords"], beam[k2]["routes"][0]["length"], GRAY),
         ("(b) Least-cost return (γ = 5)", A[k2]["coords"], A[k2]["length"], ORANGE),
         ("(c) (b) + shape terms (ours)", B[k2]["coords"], B[k2]["length"], BLUE)]
an = np.array(fw.transform(B[k2]["anchor"][1], B[k2]["anchor"][0]))
b = square([xy(c) for _, c, _, _ in items] + [an[None]])
fig, axs = plt.subplots(1, 3, figsize=(5.9, 2.2), dpi=300)
for ax, (lab, c, L, col) in zip(axs, items):
    base_axes(ax, b)
    Q = xy(c)
    ax.plot(Q[:, 0], Q[:, 1], color=col, lw=1.7, zorder=3, solid_capstyle="round")
    marks(ax, Q[0], an)
    ax.set_title(lab, fontsize=FS_T, pad=2.5)
    note(ax, f"error {abs(L - T) / T * 100:.0f}%, reuse {retrace(Q) * 100:.0f}%, roundness {comp(Q, L):.2f}")
    print(lab, f"오차 {abs(L - T) / T * 100:.0f}%, 되밟기 {retrace(Q) * 100:.0f}%, 둥근 정도 {comp(Q, L):.2f}")
scalebar(axs[2], b, top=True)
fig.subplots_adjust(left=0.004, right=0.996, top=0.92, bottom=0.005, wspace=0.03)
fig.savefig(os.path.join(HERE, "그림", "compare_en.png"), dpi=300, facecolor="white")
plt.close(fig)

# ---------- 그림 5: 선호별 경로 (이도동) ----------
R3 = json.load(open(os.path.join(NEW, "본실험3.json"), encoding="utf-8"))
share = {"조명": "lit_share", "물가": "water_share", "보도": "sidewalk_share", "녹지": "green_share", "조용": "quiet_share"}
F = {s: first(R3, s) for s in ["기준"] + [f"{p}10" for p in share]}
ok = [k for k in F["기준"] if all(k in F[f"{p}10"] and F[f"{p}10"][k]["err"] <= 0.1 for p in share) and F["기준"][k]["err"] <= 0.1]
rank = collections.Counter()
for p, key in share.items():
    d = {k: F[f"{p}10"][k][key] - F["기준"][k][key] for k in ok}
    m_ = float(np.median(list(d.values())))
    for r_, k in enumerate(sorted(ok, key=lambda k: abs(d[k] - m_))):
        rank[k] += r_
k3 = min(ok, key=lambda k: (rank[k], k))
print("그림 5 요청", k3)
pw = re.search(r'password="([^"]*)"', open(r"C:\Users\seungjun\Documents\claude_code\논문\데이터사이언스학회\04_실험\새그래프_만들기\build_v2b_graph.py", encoding="utf-8").read()).group(1)
con = pymysql.connect(host="localhost", user="root", password=pw, db="gildongmu_v3")
cur = con.cursor()
cur.execute("SELECT point_id, latitude, longitude FROM jeju_road_points")
pts = {int(a): (float(c), float(bb)) for a, bb, c in cur.fetchall()}
con.close()
attr = {int(r["point_id"]): r for r in csv.DictReader(open(os.path.join(NEW, "노드속성_v3c.csv"), encoding="utf-8"))}
has = {"조명": lambda r: r["lit"] != "1", "물가": lambda r: float(r["water_m"]) <= 50, "조용": lambda r: r["quiet"] != "1"}
DOT = {"조명": "#6b6a66", "물가": ORANGE, "조용": "#6b6a66"}
NAME = {"조명": "Lighting α = 10", "물가": "Waterside α = 10", "조용": "Quiet streets α = 10"}
LAB = {"조명": "lit", "물가": "waterside 50 m", "조용": "quiet"}
base = F["기준"][k3]
show = ["조명", "물가", "조용"]
b = square([xy(base["coords"])] + [xy(F[f"{p}10"][k3]["coords"]) for p in show], pad=260)
ids = np.array(list(pts))
XY = np.array(fw.transform([pts[i][0] for i in ids], [pts[i][1] for i in ids])).T
inb = (XY[:, 0] > b[0]) & (XY[:, 0] < b[1]) & (XY[:, 1] > b[2]) & (XY[:, 1] < b[3])
an = np.array(fw.transform(base["anchor"][1], base["anchor"][0]))
fig, axs = plt.subplots(1, 4, figsize=(5.9, 1.78), dpi=300)
Pb = xy(base["coords"])
for j, ax in enumerate(axs):
    base_axes(ax, b)
    if j == 0:
        ax.plot(Pb[:, 0], Pb[:, 1], color=INK, lw=1.5, zorder=3)
        ax.set_title("(a) Baseline (no preference)", fontsize=FS_T, pad=2.5)
        note(ax, f"{base['length'] / 1000:.1f} km, signals {base['signals_per_km']:.1f}/km")
        marks(ax, Pb[0], an)
        continue
    p = show[j - 1]
    sel = inb & np.array([has[p](attr[int(i)]) for i in ids])
    ax.scatter(XY[sel, 0], XY[sel, 1], s=0.35, color=DOT[p], alpha=0.6, lw=0, zorder=2)
    m = F[f"{p}10"][k3]
    ax.plot(Pb[:, 0], Pb[:, 1], color=GRAY, lw=0.9, ls=(0, (3, 2)), zorder=3)
    Q = xy(m["coords"])
    ax.plot(Q[:, 0], Q[:, 1], color=BLUE, lw=1.5, zorder=4)
    marks(ax, Q[0], an)
    ax.set_title(f"({'bcd'[j - 1]}) {NAME[p]}", fontsize=FS_T, pad=2.5)
    note(ax, f"{m['length'] / 1000:.1f} km, signals {m['signals_per_km']:.1f}/km\n{LAB[p]} {base[share[p]]:.2f}→{m[share[p]]:.2f}")
scalebar(axs[0], b)
fig.subplots_adjust(left=0.004, right=0.996, top=0.9, bottom=0.005, wspace=0.03)
fig.savefig(os.path.join(HERE, "그림", "prefs_en.png"), dpi=300, facecolor="white")
print("끝")

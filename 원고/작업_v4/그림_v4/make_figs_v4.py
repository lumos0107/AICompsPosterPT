"""원고 v4 그림(6월 원고처럼 그림 중심, 2026-11-11).
그림1_구조.png : 제안 방법의 흐름(한 단 폭)
그림2_비교.png : 같은 요청(연동 3 km)에서 ① 빔 귀환(데이터사이언스 방식) ② 최소 비용 귀환 γ=5 ③ +모양 (전체 폭)
                 요청 규칙: ../../실험/동선개선_1110/show_versions.py와 같음(출발점마다 ②→③ 둥근 정도 개선폭이 중앙값에 가까운 요청)
그림3_새선호.png : 같은 요청에서 기준·조명·물가·조용한 길 α=10 (전체 폭)
                 요청 규칙: show_overview.py와 같음(다섯 선호 α=10이 모두 성공한 요청 중 해당 비율 변화가 중앙값에 가장 가까운 요청)
실행: py -I 원고/그림_v4/make_figs_v4.py
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
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pymysql
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), "실험")   # HERE = 원고/작업_v4/그림_v4
NEW = os.path.join(EXP, "동선개선_1110")
OLD = os.path.join(EXP, "코드수정_1110")
sys.path.insert(0, os.path.join(EXP, "데이터진단_1109", "수집계획용", "에이전트검토"))
from lib_shp import read_shp

sys.stdout.reconfigure(encoding="utf-8")
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False
fw = Transformer.from_crs(4326, 5179, always_xy=True)
INK, GRAY, BLUE, ORANGE = "#1f1f1f", "#8a8984", "#2a78d6", "#e8893a"
MM = 1 / 25.4

# ---------- 그림 1: 흐름도 (흑백, 논문용) ----------
from matplotlib.patches import Rectangle


def box(ax, x0, y0, w, h, title, sub=None, fill="white", lw=0.6, ls="-"):
    ax.add_patch(Rectangle((x0, y0), w, h, fc=fill, ec=INK, lw=lw, ls=ls))
    if sub:
        ax.text(x0 + w / 2, y0 + h * 0.64, title, fontsize=6.1, ha="center", va="center", color=INK)
        ax.text(x0 + w / 2, y0 + h * 0.28, sub, fontsize=5.2, ha="center", va="center", color="#333333")
    else:
        ax.text(x0 + w / 2, y0 + h / 2, title, fontsize=6.1, ha="center", va="center", color=INK)


def arrow(ax, p, q):
    ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle="-|>", lw=0.55, color=INK, mutation_scale=5, shrinkA=0, shrinkB=0))


fig, (ax0, ax) = plt.subplots(2, 1, figsize=(75 * MM, 100 * MM), dpi=300, gridspec_kw=dict(height_ratios=[28, 72], hspace=0.02))
# (a) 순환 경로의 구성 (개념도)
def smooth(pts, n=60):
    P = np.array(pts, float)
    out = []
    for k in range(len(P) - 1):
        p0 = P[k - 1] if k > 0 else P[k]
        p1, p2 = P[k], P[k + 1]
        p3 = P[k + 2] if k + 2 < len(P) else P[k + 1]
        for t_ in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t_ * t_, t_ * t_ * t_
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t_ + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-1])
    return np.array(out)


def mid_arrow(axx, C, frac, **kw):
    j = int(len(C) * frac)
    axx.annotate("", xy=C[j + 1], xytext=C[j - 1], arrowprops=dict(arrowstyle="-|>", lw=0, mutation_scale=7, color=kw.get("color", INK)))


ax0.set_xlim(0, 100); ax0.set_ylim(0, 42); ax0.axis("off")
# 흑백(사용자 11/11): 검정 실선 = 진출 구간, 검정 점선 = 반환 구간, 회색 점선 = 버린 부분
S0, TP, END, ANC = (9, 9), (60, 31), (79, 33.5), (93, 36.5)
ax0.plot([S0[0], ANC[0] - 2.2], [S0[1], ANC[1] - 0.7], color="#c4c4c4", lw=0.5, ls=(0, (2, 1.5)), zorder=1)   # 안내점 방향
OUT = smooth([S0, (19, 22), (37, 29.5), TP])
EXT = smooth([TP, (70, 33), END])
RET = smooth([TP, (68, 24), (65, 14), (51, 6.5), (31, 3.5), (16, 4.5), S0])
ax0.plot(OUT[:, 0], OUT[:, 1], color=INK, lw=1.4, solid_capstyle="round", zorder=3)
ax0.plot(EXT[:, 0], EXT[:, 1], color="#9a9a9a", lw=1.0, ls=(0, (1.5, 1.5)), zorder=2)
ax0.plot(RET[:, 0], RET[:, 1], color=INK, lw=1.4, ls=(0, (4, 1.8)), zorder=3)
mid_arrow(ax0, OUT, 0.55); mid_arrow(ax0, RET, 0.55)
ax0.scatter([S0[0]], [S0[1]], marker="s", s=16, color=INK, zorder=5)
ax0.scatter([TP[0]], [TP[1]], marker="o", s=20, color=INK, zorder=5)
ax0.scatter([END[0]], [END[1]], marker="x", s=12, color="#9a9a9a", lw=0.8, zorder=5)
ax0.scatter([ANC[0]], [ANC[1]], marker="^", s=16, color=INK, zorder=5)
ax0.text(S0[0] + 1.5, S0[1] - 4.6, "출발점", fontsize=6, ha="center", va="center")
ax0.text(TP[0] - 1, TP[1] + 4.3, "반환점", fontsize=6, ha="center", va="center")
ax0.text(END[0], END[1] + 4.3, "빔이 멈춘 곳 (버림)", fontsize=5.2, ha="center", va="center", color="#666666")
ax0.text(ANC[0], ANC[1] - 4.6, "안내점", fontsize=6, ha="center", va="center")
ax0.text(42, 11, "안내점 방향 (직선 $0.38T$)", fontsize=5.2, ha="center", va="center", color="#666666")
ax0.text(23, 31, "진출 구간 (②)", fontsize=6, ha="center", va="center")
ax0.text(80, 14, "반환 구간 (④)", fontsize=6, ha="center", va="center")
ax0.text(1, 40.5, "(a) 순환 경로의 구성", fontsize=6.1, ha="left", va="center")
ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
ax.text(1, 99.5, "(b) 처리 흐름", fontsize=6.1, ha="left", va="center")
X, W, BH = 3, 60, 8.2          # 주 흐름 상자의 x, 폭, 높이
cx = X + W / 2
rows = {"in": 87.5, "g": 75, "out2": 59.5, "turn": 47.5, "ret": 35.5, "sel": 19.5, "res": 5.5}
box(ax, X, rows["in"], W, BH, "입력: 출발점 $s$, 목표 거리 $T$, 가중치 $\\alpha$")
box(ax, X, rows["g"], W, BH, "① 안내점 선택", "출발점에서 직선 $0.38T$, 16방향")
ax.add_patch(Rectangle((X - 1.8, rows["ret"] - 2.2), W + 3.6, rows["out2"] + BH + 6.2 - rows["ret"], fc="none", ec=INK, lw=0.5, ls=(0, (3, 2))))
ax.text(X - 0.8, rows["out2"] + BH + 1.7, "빔 $b=1,\\dots,9$마다 반복", fontsize=5.2, ha="left", va="center", color=INK)
box(ax, X, rows["out2"], W, BH, "② 진출 구간 탐색", "다양성 빔 탐색, 식 (2)")
box(ax, X, rows["turn"], W, BH, "③ 반환점 후보 선정", "전체 길이가 $T$에 가까운 노드 5개")
box(ax, X, rows["ret"], W, BH, "④ 반환 구간 탐색", "최소 비용 탐색, 식 (3)")
box(ax, X, rows["sel"], W, BH, "⑤ 경로 선택", "오차 ±10% 이내, 최대 3개")
box(ax, X, rows["res"], W, BH, "출력: 순환 경로")
for a_, b_ in (("in", "g"), ("g", "out2"), ("out2", "turn"), ("turn", "ret"), ("ret", "sel"), ("sel", "res")):
    arrow(ax, (cx, rows[a_]), (cx, rows[b_] + BH))
SX, SW = 71, 27
box(ax, SX, 66, SW, 12, "도로망·노드 속성", "표 1")
box(ax, SX, 44, SW, 12, "선호 비용 $p$", "식 (1)", fill="#e6e6e6")
arrow(ax, (SX + SW / 2, 66), (SX + SW / 2, 56))
arrow(ax, (SX, 52), (X + W, rows["out2"] + BH / 2))
arrow(ax, (SX, 48), (X + W, rows["ret"] + BH / 2))
fig.subplots_adjust(0, 0, 1, 0.98)
fig.savefig(os.path.join(HERE, "그림1_구조.png"), dpi=300, facecolor="white")
plt.close(fig)
if "fig1" in sys.argv:
    sys.exit(0)
# ---------- 공통 ----------
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
        ax.plot(p[:, 0], p[:, 1], color="#d9d8d3", lw=0.25, zorder=1)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_color("#b9b8b3"); sp.set_linewidth(0.4)


def marks(ax, start_xy, anchor_xy):
    ax.scatter([start_xy[0]], [start_xy[1]], marker="s", s=7, color=INK, zorder=6, lw=0)
    ax.scatter([anchor_xy[0]], [anchor_xy[1]], marker="^", s=8, color=INK, zorder=6, lw=0)


def scalebar(ax, b):
    x0, x1, y0, y1 = b
    ax.plot([x1 - 560, x1 - 60], [y0 + 80, y0 + 80], color=INK, lw=0.6)
    ax.text(x1 - 310, y0 + 120, "500 m", ha="center", fontsize=4.8, color=INK)


# ---------- 그림 2: 알고리즘 단계 비교 (연동) ----------
R1 = json.load(open(os.path.join(OLD, "본실험.json"), encoding="utf-8"))
R2 = json.load(open(os.path.join(NEW, "본실험2.json"), encoding="utf-8"))
T2 = json.load(open(os.path.join(OLD, "표2.json"), encoding="utf-8"))
beam = {(r["start"], r["anchor_id"]): r for r in T2 if r["conf"] == "빔 귀환"}
A, B = first(R1, "기준"), first(R2, "기준")
C = first(R2, "신호회피10")
keys = sorted(set(A) & set(B) & set(C) & set(beam))
st = "연동"
ks = [k for k in keys if k[0] == st]
gain = {k: comp(xy(B[k]["coords"]), B[k]["length"]) - comp(xy(A[k]["coords"]), A[k]["length"]) for k in ks}
med = float(np.median(list(gain.values())))
k2 = min(ks, key=lambda k: (abs(gain[k] - med), k[1]))
print("그림2 요청", k2)
T = 3000
items = [("(a) 빔 탐색 반환", beam[k2]["routes"][0]["coords"], beam[k2]["routes"][0]["length"], GRAY),
         ("(b) 최소 비용 반환 (γ=5)", A[k2]["coords"], A[k2]["length"], ORANGE),
         ("(c) (b) + 모양 항 (제안)", B[k2]["coords"], B[k2]["length"], BLUE)]
an = np.array(fw.transform(B[k2]["anchor"][1], B[k2]["anchor"][0]))
b = square([xy(c) for _, c, _, _ in items] + [an[None]])
# 한 단 폭(사용자 11/11): 2x2, 지도 3칸 + 수치 표 1칸. 전체 폭 판은 그림2_비교_전체폭.png로 남김
fig, axs = plt.subplots(2, 2, figsize=(80 * MM, 86 * MM), dpi=300)
stats = []
for ax, (lab, c, L, col) in zip(axs.flat[:3], items):
    base_axes(ax, b)
    Q = xy(c)
    ax.plot(Q[:, 0], Q[:, 1], color=col, lw=1.2, zorder=3, solid_capstyle="round")
    marks(ax, Q[0], an)
    ax.set_title(lab, fontsize=6.0, pad=2)
    stats.append((lab[:3], f"{abs(L - T) / T * 100:.0f}%", f"{retrace(Q) * 100:.0f}%", f"{comp(Q, L):.2f}", col))
scalebar(axs.flat[2], b)
ax = axs[1, 1]
ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
ax.set_title("이 요청의 값", fontsize=6.0, pad=2)
XS = [0.10, 0.36, 0.59, 0.82]
for x_, h_ in zip(XS, ["", "오차", "되밟기", "둥근 정도"]):
    ax.text(x_, 0.80, h_, fontsize=5.6, ha="center", va="center", color=INK)
ax.plot([0.02, 0.98], [0.72, 0.72], color=INK, lw=0.4)
for k, (nm, e, r_, cp, col) in enumerate(stats):
    y_ = 0.60 - k * 0.15
    ax.plot([0.03, 0.08], [y_, y_], color=col, lw=1.6)
    ax.text(0.13, y_, nm, fontsize=5.6, ha="left", va="center")
    for x_, v in zip(XS[1:], (e, r_, cp)):
        ax.text(x_, y_, v, fontsize=5.6, ha="center", va="center")
fig.subplots_adjust(left=0.005, right=0.995, top=0.955, bottom=0.005, wspace=0.03, hspace=0.09)
fig.savefig(os.path.join(HERE, "그림2_비교.png"), dpi=300, facecolor="white")
plt.close(fig)

# ---------- 그림 3: 새 선호 예 ----------
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
print("그림3 요청", k3)
pw = re.search(r'password="([^"]*)"', open(r"C:\Users\seungjun\Documents\claude_code\논문\데이터사이언스학회\04_실험\새그래프_만들기\build_v2b_graph.py", encoding="utf-8").read()).group(1)
con = pymysql.connect(host="localhost", user="root", password=pw, db="gildongmu_v3")
cur = con.cursor()
cur.execute("SELECT point_id, latitude, longitude FROM jeju_road_points")
pts = {int(a): (float(c), float(bb)) for a, bb, c in cur.fetchall()}
con.close()
attr = {int(r["point_id"]): r for r in csv.DictReader(open(os.path.join(NEW, "노드속성_v3c.csv"), encoding="utf-8"))}
has = {"조명": lambda r: r["lit"] != "1", "물가": lambda r: float(r["water_m"]) <= 50, "조용": lambda r: r["quiet"] != "1"}
DOT = {"조명": "#6b6a66", "물가": ORANGE, "조용": "#6b6a66"}
NAME = {"조명": "조명 α=10", "물가": "물가 α=10", "조용": "조용한 길 α=10"}
LAB = {"조명": "밝은 길", "물가": "물가 50 m", "조용": "조용한 길"}
base = F["기준"][k3]
show = ["조명", "물가", "조용"]
b = square([xy(base["coords"])] + [xy(F[f"{p}10"][k3]["coords"]) for p in show], pad=260)
ids = np.array(list(pts))
XY = np.array(fw.transform([pts[i][0] for i in ids], [pts[i][1] for i in ids])).T
inb = (XY[:, 0] > b[0]) & (XY[:, 0] < b[1]) & (XY[:, 1] > b[2]) & (XY[:, 1] < b[3])
an = np.array(fw.transform(base["anchor"][1], base["anchor"][0]))
# 한 단 폭(사용자 11/11): 2x2. 전체 폭 판은 그림3_새선호_전체폭.png로 남김
fig, axs = plt.subplots(2, 2, figsize=(80 * MM, 86 * MM), dpi=300)
axs = axs.flat
Pb = xy(base["coords"])
for j, ax in enumerate(axs):
    base_axes(ax, b)
    if j == 0:
        ax.plot(Pb[:, 0], Pb[:, 1], color=INK, lw=1.1, zorder=3)
        ax.set_title("(a) 기준 (선호 없음)", fontsize=6.0, pad=2)
        ax.text(0.03, 0.03, f"{base['length'] / 1000:.1f} km, 신호 {base['signals_per_km']:.1f}/km", transform=ax.transAxes, fontsize=5,
                bbox=dict(fc="white", ec="none", alpha=0.85, pad=1), zorder=7)
        marks(ax, Pb[0], an)
        continue
    p = show[j - 1]
    sel = inb & np.array([has[p](attr[int(i)]) for i in ids])
    ax.scatter(XY[sel, 0], XY[sel, 1], s=0.25, color=DOT[p], alpha=0.6, lw=0, zorder=2)
    m = F[f"{p}10"][k3]
    ax.plot(Pb[:, 0], Pb[:, 1], color=GRAY, lw=0.7, ls=(0, (3, 2)), zorder=3)
    Q = xy(m["coords"])
    ax.plot(Q[:, 0], Q[:, 1], color=BLUE, lw=1.1, zorder=4)
    marks(ax, Q[0], an)
    ax.set_title(f"({'bcd'[j - 1]}) {NAME[p]}", fontsize=6.0, pad=2)
    ax.text(0.03, 0.03, f"{m['length'] / 1000:.1f} km, 신호 {m['signals_per_km']:.1f}/km\n{LAB[p]} {base[share[p]]:.2f}→{m[share[p]]:.2f}",
            transform=ax.transAxes, fontsize=5, linespacing=1.25, bbox=dict(fc="white", ec="none", alpha=0.85, pad=1), zorder=7)
scalebar(axs[0], b)
fig.subplots_adjust(left=0.005, right=0.995, top=0.955, bottom=0.005, wspace=0.03, hspace=0.09)
fig.savefig(os.path.join(HERE, "그림3_새선호.png"), dpi=300, facecolor="white")
print("끝")

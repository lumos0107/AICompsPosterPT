"""사용자에게 실험을 눈으로 보여 주는 그림 세 장(원고용 아님, 2026-11-11).
1) 보기_모양.png: 출발점 네 곳에서 모양 벌점 전(1차 본실험 기준)과 후(본실험2 기준)의 첫 경로. 출발점마다 둥근 정도 개선폭이 그 출발점 중앙값에 가까운 요청.
2) 보기_새선호.png: 한 요청에서 기준 경로(회색 점선)와 새 선호 α=10 경로(파랑). 주황 점은 그 성질이 있는 노드.
   요청 고르는 규칙: 다섯 선호 α=10이 모두 성공(첫 경로 오차 ≤0.1)한 요청 중, 다섯 선호의 해당 비율 변화가 각 선호 중앙값에 가장 가까운(순위 합이 가장 작은) 요청.
3) 보기_효과.png: 선호 8개 × α 1·3·10의 평균 변화와 목표 거리 성공 요청 수.
실행: py -I show_overview.py
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

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
OLD = os.path.join(EXP, "코드수정_1110")
sys.path.insert(0, os.path.join(EXP, "데이터진단_1109", "수집계획용", "에이전트검토"))
from lib_shp import read_shp

sys.stdout.reconfigure(encoding="utf-8")
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False
fw = Transformer.from_crs(4326, 5179, always_xy=True)
GRAY, BLUE, ORANGE, INK = "#8a8984", "#2a78d6", "#e8893a", "#2b2b2b"

R1 = json.load(open(os.path.join(OLD, "본실험.json"), encoding="utf-8"))
R2 = json.load(open(os.path.join(HERE, "본실험2.json"), encoding="utf-8"))
R3 = json.load(open(os.path.join(HERE, "본실험3.json"), encoding="utf-8"))


def first(R, setting):
    d = {}
    for m in R:
        if m["setting"] != setting:
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


ROAD = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵\연속수치지도_제주_20261109\풀기\N3L_A0020000\N3L_A0020000"
g = np.load(os.path.join(EXP, "도심실험_1110", "그래프_도심_114칸.npz"))
lines = [p for r, parts in read_shp(ROAD, clip=False) for p in parts]
segs = [lines[g["line"][e]][g["a"][e]:g["b"][e] + 1] for e in np.where(g["main"])[0].tolist()]


def box(*Ps, pad=120):
    P = np.vstack(Ps)
    x0, y0 = P.min(0) - pad
    x1, y1 = P.max(0) + pad
    s = max(x1 - x0, y1 - y0)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return cx - s / 2, cx + s / 2, cy - s / 2, cy + s / 2


def roads(ax, b):
    x0, x1, y0, y1 = b
    for p in segs:
        if p[:, 0].max() < x0 or p[:, 0].min() > x1 or p[:, 1].max() < y0 or p[:, 1].min() > y1:
            continue
        ax.plot(p[:, 0], p[:, 1], color="#dcdbd6", lw=0.4, zorder=1)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_color("#c8c7c2"); sp.set_linewidth(0.5)


def marks(ax, m):
    P = xy(m)
    an = fw.transform(m["anchor"][1], m["anchor"][0])
    ax.scatter([P[0, 0]], [P[0, 1]], marker="s", s=22, color=INK, zorder=6)
    ax.scatter([an[0]], [an[1]], marker="^", s=24, color=INK, zorder=6)


def scalebar(ax, b):
    x0, x1, y0, y1 = b
    ax.plot([x1 - 560, x1 - 60], [y0 + 70, y0 + 70], color=INK, lw=1)
    ax.text(x1 - 310, y0 + 110, "500 m", ha="center", fontsize=7, color=INK)


# 1) 모양 전후
A, B = first(R1, "기준"), first(R2, "기준")
keys = sorted(set(A) & set(B))
fig, axs = plt.subplots(2, 4, figsize=(12, 6.6), dpi=130, facecolor="white")
for j, st in enumerate(["탑동", "도심", "연동", "이도"]):
    ks = [k for k in keys if k[0] == st]
    gain = {k: comp(B[k]) - comp(A[k]) for k in ks}
    med = float(np.median(list(gain.values())))
    k = min(ks, key=lambda k: (abs(gain[k] - med), k[1]))
    b = box(xy(A[k]), xy(B[k]))
    for i, (lab, m, c) in enumerate([("전", A[k], GRAY), ("후", B[k], BLUE)]):
        ax = axs[i, j]
        roads(ax, b)
        P = xy(m)
        ax.plot(P[:, 0], P[:, 1], color=c, lw=2.2, zorder=3, solid_capstyle="round")
        marks(ax, m)
        ax.set_title(f"{st} {m['target'] // 1000} km · 모양 반영 {lab}", fontsize=9.5, pad=3)
        ax.text(0.02, 0.02, f"둥근 정도 {comp(m):.2f}  길이 {m['length'] / 1000:.2f} km", transform=ax.transAxes, fontsize=8,
                bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.5), zorder=7)
        if j == 3:
            scalebar(ax, b)
fig.suptitle("러닝 동선 모양 반영 전(회색)과 후(파랑) · ■ 출발점 ▲ 안내점 · 출발점마다 개선폭이 중앙값인 요청", fontsize=11)
fig.subplots_adjust(left=0.01, right=0.99, top=0.9, bottom=0.01, wspace=0.04, hspace=0.12)
fig.savefig(os.path.join(HERE, "보기_모양.png"), facecolor="white")
plt.close(fig)

# 2) 새 선호 α=10
pw = re.search(r'password="([^"]*)"', open(r"C:\Users\seungjun\Documents\claude_code\논문\데이터사이언스학회\04_실험\새그래프_만들기\build_v2b_graph.py", encoding="utf-8").read()).group(1)
con = pymysql.connect(host="localhost", user="root", password=pw, db="gildongmu_v3")
cur = con.cursor()
cur.execute("SELECT point_id, latitude, longitude FROM jeju_road_points")
pts = {int(a): (float(c), float(b)) for a, b, c in cur.fetchall()}
con.close()
attr = {int(r["point_id"]): r for r in csv.DictReader(open(os.path.join(HERE, "노드속성_v3c.csv"), encoding="utf-8"))}
has = {"조명": lambda r: r["lit"] == "1", "물가": lambda r: float(r["water_m"]) <= 50, "보도": lambda r: r["sidewalk"] == "1",
       "녹지": lambda r: r["green"] == "1", "조용": lambda r: r["quiet"] == "1"}
share = {"조명": "lit_share", "물가": "water_share", "보도": "sidewalk_share", "녹지": "green_share", "조용": "quiet_share"}
NAME = {"조명": "조명(밝은 길)", "물가": "물가 50 m", "보도": "보도", "녹지": "녹지(공원)", "조용": "조용한 길"}
F = {s: first(R3, s) for s in ["기준"] + [f"{p}10" for p in share]}
ok = [k for k in F["기준"] if all(k in F[f"{p}10"] and F[f"{p}10"][k]["err"] <= 0.1 for p in share) and F["기준"][k]["err"] <= 0.1]
rank = collections.Counter()
for p, key in share.items():
    d = {k: F[f"{p}10"][k][key] - F["기준"][k][key] for k in ok}
    med = float(np.median(list(d.values())))
    for r_, k in enumerate(sorted(ok, key=lambda k: abs(d[k] - med))):
        rank[k] += r_
k = min(ok, key=lambda k: (rank[k], k))
print("새 선호 예 요청", k, "후보", len(ok))
base = F["기준"][k]
b = box(xy(base), *[xy(F[f"{p}10"][k]) for p in share], pad=150)
ids = np.array(list(pts))
XY = np.array(fw.transform([pts[i][0] for i in ids], [pts[i][1] for i in ids])).T
inb = (XY[:, 0] > b[0]) & (XY[:, 0] < b[1]) & (XY[:, 1] > b[2]) & (XY[:, 1] < b[3])
fig, axs = plt.subplots(2, 3, figsize=(12, 8.4), dpi=130, facecolor="white")
for ax, p in zip(axs.flat, ["기준"] + list(share)):
    roads(ax, b)
    Pb = xy(base)
    if p == "기준":
        ax.plot(Pb[:, 0], Pb[:, 1], color=INK, lw=2.2, zorder=3)
        ax.set_title(f"기준 (선호 없음) · {base['start']} {base['target'] // 1000} km", fontsize=10, pad=3)
        txt = "  ".join(f"{NAME[q].split('(')[0]} {base[share[q]]:.2f}" for q in share)
        ax.text(0.02, 0.02, "길이 비율: " + txt, transform=ax.transAxes, fontsize=7.2, bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.5), zorder=7)
        marks(ax, base)
        continue
    sel = inb & np.array([has[p](attr[int(i)]) for i in ids])
    ax.scatter(XY[sel, 0], XY[sel, 1], s=1.2, color=ORANGE, alpha=0.55, lw=0, zorder=2)
    m = F[f"{p}10"][k]
    ax.plot(Pb[:, 0], Pb[:, 1], color=GRAY, lw=1.3, ls=(0, (3, 2)), zorder=3)
    P = xy(m)
    ax.plot(P[:, 0], P[:, 1], color=BLUE, lw=2.2, zorder=4)
    marks(ax, m)
    ax.set_title(f"{NAME[p]} 선호 α=10", fontsize=10, pad=3)
    ax.text(0.02, 0.02, f"{NAME[p]} 길이 비율 {base[share[p]]:.2f} → {m[share[p]]:.2f} · 신호 {base['signals_per_km']:.1f} → {m['signals_per_km']:.1f}개/km · 오차 {m['err']:.2f}",
            transform=ax.transAxes, fontsize=7.2, bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.5), zorder=7)
scalebar(axs[1, 2], b)
fig.suptitle("같은 요청에서 새 선호를 켰을 때 · 회색 점선 = 기준 경로, 파랑 = 선호 경로, 주황 점 = 그 성질이 있는 도로 지점", fontsize=11)
fig.subplots_adjust(left=0.01, right=0.99, top=0.93, bottom=0.01, wspace=0.03, hspace=0.08)
fig.savefig(os.path.join(HERE, "보기_새선호.png"), facecolor="white")
plt.close(fig)


# 3) 효과 크기
def req_mean(R, setting, key):
    d = collections.defaultdict(list)
    for m in R:
        if m["setting"] == setting:
            d[(m["start"], m["anchor_id"])].append(m[key])
    return {k: float(np.mean(v)) for k, v in d.items()}


def success(R, setting):
    d = collections.defaultdict(bool)
    for m in R:
        if m["setting"] == setting:
            d[(m["start"], m["anchor_id"])] |= m["err"] <= 0.1
    return sum(d.values())


DOWN = [("평지", "경사", "slope", R2), ("신호회피", "신호\n교차로", "signals_per_km", R2), ("시설", "시설까지\n거리", "facility_m", R2)]
UP = [(p, NAME[p].replace("(", "\n(").replace(" 50 m", "\n50 m"), share[p], R3) for p in share]
fig, axs = plt.subplots(1, 3, figsize=(13, 4.6), dpi=130, facecolor="white", gridspec_kw=dict(width_ratios=[3, 5, 8]))
SHADES = ["#a9cdf2", "#5a9ee6", "#1f5fae"]
for ax, group, unit in [(axs[0], DOWN, "줄어든 비율 (%)"), (axs[1], UP, "늘어난 길이 비율 (%p)")]:
    for i, (p, lab, key, R) in enumerate(group):
        b0 = req_mean(R, "기준", key)
        for j, a in enumerate((1, 3, 10)):
            s = req_mean(R, f"{p}{a}", key)
            ks = sorted(set(b0) & set(s))
            d = np.mean([s[k] - b0[k] for k in ks])
            v = -d / np.mean([b0[k] for k in ks]) * 100 if group is DOWN else d * 100
            ax.bar(i + (j - 1) * 0.27, v, 0.25, color=SHADES[j], label=f"α={a}" if i == 0 else None)
            ax.text(i + (j - 1) * 0.27, v + 0.6, f"{v:.0f}", ha="center", fontsize=7.5, color=INK)
            print(p, a, round(v, 2))
    ax.set_xticks(range(len(group)))
    ax.set_xticklabels([x[1] for x in group], fontsize=8.5)
    ax.set_title(unit, fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="y", labelsize=8)
    ax.grid(axis="y", color="#eeeeea", lw=0.6)
    ax.set_axisbelow(True)
axs[0].legend(fontsize=8, frameon=False, loc="upper left")
ax = axs[2]
ALL = [("평지", "평지", R2), ("신호회피", "신호 회피", R2), ("시설", "시설", R2)] + [(p, NAME[p].split("(")[0].replace(" 50 m", ""), R3) for p in share]
for i, (p, lab, R) in enumerate(ALL):
    for j, a in enumerate((1, 3, 10)):
        n = success(R, f"{p}{a}")
        ax.bar(i + (j - 1) * 0.27, n, 0.25, color=SHADES[j] if n == 47 else ORANGE)
        if n < 47:
            ax.text(i + (j - 1) * 0.27, n + 0.5, str(n), ha="center", fontsize=7.5, color=INK)
ax.axhline(47, color=GRAY, lw=0.8, ls=":")
ax.set_ylim(0, 50)
ax.set_xticks(range(len(ALL)))
ax.set_xticklabels([x[1] for x in ALL], fontsize=8.5)
ax.set_title("목표 거리 ±10% 성공 요청 (47개 중, 주황 = 47 미만)", fontsize=10)
ax.spines[["top", "right"]].set_visible(False)
ax.tick_params(axis="y", labelsize=8)
fig.suptitle("선호 크기(α)를 키울수록 · 같은 47개 요청에서 기준 대비", fontsize=11)
fig.subplots_adjust(left=0.04, right=0.99, top=0.84, bottom=0.1, wspace=0.18)
fig.savefig(os.path.join(HERE, "보기_효과.png"), facecolor="white")
print("끝")

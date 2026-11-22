"""자동 생성: make_en_figs12.py가 make_fig_beam.py에서 라벨만 영어로 바꾼 사본. 직접 고치지 말 것."""
"""포스터 그림: 진출 구간의 다양성 빔 탐색 개념도 (2026-11-13).

원고 v4 3.3절(수식 (2))을 그림으로 옮긴 것이다. 실제 계산 결과가 아니라 개념도다.
(a) 빔 9개가 안내점 방향 기준 –45°~+45°로 서로 다른 방위를 받는다.
(b) 한 단계에서 현재 노드 u의 이웃 후보마다 점수 = 안내점 쪽 진행 – 선호 비용 – 방위 차이 – 다른 빔과 겹침을 매겨 고른다.
포스터에 원래 크기(폭 6.36인치)로 놓으므로 글자 크기가 곧 포스터 글자 크기다.
실행: python make_fig_beam.py → 그림/진출구간_빔.png
"""
import math
import os
import sys

import matplotlib
import numpy as np
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge

sys.stdout.reconfigure(encoding="utf-8")
plt.rcParams["font.family"] = ["Arial", "Malgun Gothic"]
plt.rcParams["axes.unicode_minus"] = False
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "그림", "진출구간_빔_en.png")
INK, MID, LIGHT, BLUE, ORANGE = "#1f1f1f", "#9a9a9a", "#e4e4e4", "#2a78d6", "#e8893a"
FS = 9.5


K1 = 0.75  # 그림 1(a)를 줄인 비율(같은 장면으로 보이게 출발점·안내점·진출 구간 모양을 그대로 쓴다)


def qbez(p0, c, p1, n=80):
    t = np.linspace(0, 1, n)[:, None]
    p0, c, p1 = map(np.array, (p0, c, p1))
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * c + t ** 2 * p1


def arc_len(pts):
    return float(np.sum(np.hypot(*np.diff(pts, axis=0).T)))


def steer_path(theta0, goal, length, step=0.01, turn=0.9):
    """방위 theta0(도)로 출발해 안내점(goal) 쪽으로 서서히 휘며 length만큼 나아가는 길(그림용)."""
    x, y, h = 0.0, 0.0, math.radians(theta0)
    pts = [(0.0, 0.0)]
    for i in range(int(length / step)):
        g = math.atan2(goal[1] - y, goal[0] - x)
        w = min(1.0, i * step / length * turn)
        d = (g - h + math.pi) % (2 * math.pi) - math.pi
        hh = h + w * d
        x, y = x + step * math.cos(hh), y + step * math.sin(hh)
        pts.append((x, y))
    return np.array(pts)


def bez_chain(pts, n=60):
    """2차 베지어 조각을 이은 곡선(그림 1과 같은 함수). pts = [p0, c1, p1, c2, p2, ...]."""
    out = []
    for i in range(0, len(pts) - 2, 2):
        out.append(qbez(pts[i], pts[i + 1], pts[i + 2], n))
    return np.vstack(out)


def panel_a(ax):
    ax.set_title("(a) Fig. 1 outbound = 1 of 9 beams", fontsize=FS + 1, loc="left", color=INK)
    # 그림 1(a)와 같은 배치: 출발점·반환점·안내점이 한 가로줄, 진출 구간은 위쪽 호
    S = np.array([0.0, 0.0])
    R = np.array([2.75, 0.0]) * K1           # 반환점
    G = np.array([3.85, 0.0]) * K1           # 안내점
    out = bez_chain([S, np.array([0.45, 0.4]) * K1, np.array([1.375, 0.4]) * K1, np.array([2.6, 0.4]) * K1, R])
    L_out = arc_len(out)
    X = R + np.array([0.4, -0.12]) * K1      # 빔이 반환점 뒤로 더 나아갔다가 멈춘 곳(버림)
    L_beam = L_out + float(np.hypot(*(X - R)))  # 모든 빔은 같은 누적 거리(0.51T)에서 멈춤
    # 빔 방위의 범위(안내점 방향 기준 ±45°)
    r_w = 1.1
    ax.add_patch(Wedge(tuple(S), r_w, -45, 45, fc="#e3eefb", ec="none", zorder=0))
    for d, lab in ((-45, "–45°"), (45, "+45°")):
        t = math.radians(d)
        ax.plot([0, r_w * math.cos(t)], [0, r_w * math.sin(t)], color=BLUE, lw=0.7, ls=(0, (2, 2)), zorder=1)
        ax.text((r_w + 0.1) * math.cos(t), (r_w + 0.1) * math.sin(t), lab, fontsize=FS - 1, color=BLUE, ha="center", va="center")
    # 안내점 방향
    ax.plot([0, G[0]], [0, G[1]], ls=(0, (2, 2)), color=MID, lw=0.8, zorder=1)
    # 다른 빔 둘(–22.5°, –45°): 안내점 쪽으로 휘며 같은 거리에서 멈춤
    for th in (-22.5, -45):
        b = steer_path(th, G, L_beam)
        ax.plot(b[:, 0], b[:, 1], color=BLUE, lw=1.6, zorder=2, solid_capstyle="round")
        ax.plot(*b[-1], marker="o", ms=5, mfc=BLUE, mec="white", mew=0.7, zorder=4)
    # 그림 1의 진출 구간이 된 빔(검정): 반환점 뒤 부분은 버림
    ax.plot(out[:, 0], out[:, 1], color=INK, lw=2.2, zorder=3, solid_capstyle="round")
    ax.plot([R[0], X[0]], [R[1], X[1]], ls=(0, (1.5, 1.5)), color=MID, lw=1.6, zorder=2)
    ax.plot(*X, marker="x", color=MID, ms=5.5, mew=1.3, zorder=4)
    ax.plot(*R, marker="o", color=INK, ms=6.5, zorder=5)
    ax.text(1.3, 0.36, "② Outbound", fontsize=FS - 0.5, color=INK, ha="center", va="bottom", fontweight="bold")
    ax.text(R[0] - 0.02, R[1] + 0.07, "③ Turnaround", fontsize=FS - 1, color=INK, ha="left", va="bottom")
    ax.plot(*G, marker="^", color=INK, ms=7, zorder=5)
    ax.text(G[0] + 0.08, G[1], "① Guide point", fontsize=FS - 1, color=INK, ha="left", va="center")
    ax.plot(0, 0, marker="s", color=INK, ms=7, zorder=5)
    ax.text(-0.14, 0, "Start", fontsize=FS - 0.5, color=INK, ha="right", va="center")
    ax.text(1.95, 0.66, "● ×  stop at 0.51T traveled", fontsize=FS - 1.5, color=MID, ha="left", va="center")
    ax.set_xlim(-0.62, 3.65)
    ax.set_ylim(-0.98, 0.86)


def panel_b(ax):
    ax.set_title("(b) One step: best-scoring neighbor", fontsize=FS + 1, loc="left", color=INK)
    roads = [[(0, -1.0), (0, 1.35)], [(-1.35, 0), (1.45, 0)], [(0, 0), (1.3, 1.3)], [(1.75, 0.55), (0.8, 0.8), (0.55, 1.45)]]
    for r in roads:
        ax.plot(*zip(*r), color=LIGHT, lw=5, solid_capstyle="round", zorder=1)
    # 다른 빔이 이미 지난 길
    ax.plot([1.75, 0.8, 0.55], [0.55, 0.8, 1.45], color=MID, lw=2.4, zorder=2)
    ax.text(1.82, 0.53, "other beam", fontsize=FS - 1, color=MID, ha="left", va="center")
    # 이 빔이 지나온 길과 방위
    ax.plot([0, 0], [-1.0, 0], color=BLUE, lw=2.4, zorder=3)
    ax.annotate("", xy=(0.62, 0.62), xytext=(0, 0), arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=1, ls="--", mutation_scale=8), zorder=4)
    ax.text(0.5, 0.2, "this beam's heading", fontsize=FS - 1, color=BLUE, ha="left", va="center")
    # 선택한 후보
    ax.annotate("", xy=(0.95, 0), xytext=(0.06, 0), arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=2.4, mutation_scale=11), zorder=4)
    cands = {"N": (0, 1.0), "NE": (0.8, 0.8), "E": (1.0, 0), "W": (-1.0, 0)}
    for name, (x, y) in cands.items():
        ax.plot(x, y, marker="o", ms=7, mfc="white", mec=INK, mew=1.2, zorder=5)
    ax.plot(0, 1.0, marker="o", ms=7, mfc=ORANGE, mec=INK, mew=1.2, zorder=6)
    ax.plot(0, 0, marker="o", ms=8, mfc=INK, mec=INK, zorder=6)
    ax.text(-0.1, -0.22, "u (current node)", fontsize=FS - 0.5, color=INK, ha="right", va="top")
    ax.text(-0.1, 1.0, "traffic signal\n– preference cost", fontsize=FS - 0.5, color=ORANGE, ha="right", va="center")
    ax.text(0.98, 0.98, "– overlap", fontsize=FS - 0.5, color=INK, ha="left", va="bottom")
    ax.text(-1.0, 0.1, "against heading\n– heading gap", fontsize=FS - 0.5, color=INK, ha="center", va="bottom")
    ax.text(1.08, -0.1, "best score → next node", fontsize=FS - 0.5, color=BLUE, ha="left", va="top", fontweight="bold")
    ax.set_xlim(-1.45, 2.55)
    ax.set_ylim(-0.75, 1.65)


def main():
    fig = plt.figure(figsize=(6.36, 1.72))
    a = fig.add_axes([0.0, 0.18, 0.47, 0.67])
    b = fig.add_axes([0.47, 0.18, 0.53, 0.67])
    for ax in (a, b):
        ax.set_aspect("equal")
        ax.axis("off")
    panel_a(a)
    panel_b(b)
    fig.text(0.5, 0.06, "Score = progress to guide point – preference cost – heading gap – overlap",
             fontsize=FS + 0.5, color=INK, ha="center", va="center",
             bbox=dict(fc="#e3eefb", ec="none", boxstyle="square,pad=0.35"))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.savefig(OUT, dpi=300, facecolor="white")
    print("저장:", OUT)


if __name__ == "__main__":
    main()

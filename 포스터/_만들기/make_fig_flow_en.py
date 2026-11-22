"""자동 생성: make_en_figs12.py가 make_fig_flow.py에서 라벨만 영어로 바꾼 사본. 직접 고치지 말 것."""
"""포스터 그림 1: (a) 순환 경로의 구성 + (b) 처리 흐름(가로) (2026-11-13).

원고 그림 1(원고/작업_v5/그림_v4/make_figs_v4.py)과 같은 내용을 포스터 한 단 폭(6.36인치)에 맞게 다시 그린다.
(a)의 ①~④ 라벨이 (b) 흐름의 단계 번호와 그림 2·3, 식 (2)를 가리키게 해 서로 이어 읽게 한다.
식 번호는 포스터 기준이다: 선호 비용 = 식 (1), 반환 구간 비용 = 식 (2)(원고 식 (3)), 진출 구간 빔 점수는 그림 2로 보인다.
포스터에 원래 크기로 놓으므로 글자 크기가 곧 포스터 글자 크기다.
실행: python make_fig_flow.py → 그림/그림1_구조_포스터.png
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

sys.stdout.reconfigure(encoding="utf-8")
plt.rcParams["font.family"] = ["Arial", "Malgun Gothic"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["mathtext.fontset"] = "stix"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "그림", "그림1_구조_포스터_en.png")
INK, MID, BLUE, PALEB, GRAY = "#1f1f1f", "#6b6a64", "#2a78d6", "#e3eefb", "#e4e4e4"
W, HB, HA = 6.36, 1.78, 1.18   # 폭, (b) 높이, (a) 높이
H = HB + HA
FS_T, FS_S = 8.2, 7.4        # 상자 제목, 설명 글자 크기(pt)
FS_A = 8.4                   # (a) 라벨

MAIN = [
    ("입력", "출발점 $s$\n목표 거리 $T$\n가중치 $\\alpha$", 0.64, "io"),
    ("① 안내점 선택", "출발점에서\n직선 0.38$T$, 16방향", 0.92, ""),
    ("② 진출 구간 탐색", "다양성 빔 탐색\n(그림 2)", 0.92, "p"),
    ("③ 반환점 후보", "전체 길이가 $T$에\n가까운 노드 5개", 0.88, ""),
    ("④ 반환 구간 탐색", "최소 비용 탐색\n식 (2)", 0.92, "p"),
    ("⑤ 경로 선택", "오차 ±10% 안\n최대 3개", 0.8, ""),
    ("출력", "순환\n경로", 0.5, "io"),
]
GAP = (W - 0.04 - sum(m[2] for m in MAIN)) / (len(MAIN) - 1)
BH, YT = 0.6, 0.8            # 위 줄 상자 높이, 아래 끝 y
BH2, YB = 0.4, 0.02          # 아래 줄 상자 높이, 아래 끝 y


def box(ax, x, y, w, h, title, sub, kind):
    fc, ec = {"p": (PALEB, BLUE), "io": ("white", MID), "": ("white", INK), "g": (GRAY, INK)}[kind]
    ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec=ec, lw=0.9, zorder=2))
    if sub:
        ax.text(x + w / 2, y + h - 0.06, title, fontsize=FS_T, color=INK, ha="center", va="top", fontweight="bold", zorder=3)
        ax.text(x + w / 2, y + h - 0.23, sub, fontsize=FS_S, color=INK, ha="center", va="top", linespacing=1.15, zorder=3)
    else:
        ax.text(x + w / 2, y + h / 2, title, fontsize=FS_T, color=INK, ha="center", va="center", fontweight="bold", zorder=3)


def arrow(ax, a, b, color=INK, ms=7, lw=0.9):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=ms, lw=lw, color=color, shrinkA=0, shrinkB=0, zorder=4))


def bezier(pts, n=60):
    """2차 베지어 조각들을 이은 매끈한 곡선. pts = [p0, c1, p1, c2, p2, ...]."""
    out = []
    for i in range(0, len(pts) - 2, 2):
        p0, c, p1 = map(np.array, pts[i:i + 3])
        t = np.linspace(0, 1, n)[:, None]
        out.append((1 - t) ** 2 * p0 + 2 * (1 - t) * t * c + t ** 2 * p1)
    return np.vstack(out)


def panel_a(ax, y0):
    """(a) 순환 경로의 구성. y0: 이 칸의 아래 끝.
    출발점·반환점·안내점을 한 가로줄에 두고, 진출 구간은 위쪽 호, 반환 구간은 아래쪽 호로 그린다(점선이 경로와 엇갈리지 않게)."""
    ax.text(0.02, y0 + HA - 0.02, "(a) Loop route", fontsize=FS_T + 0.5, color=INK, ha="left", va="top")
    yc = y0 + 0.5
    S = np.array([1.0, yc])                 # 출발점
    R = np.array([3.75, yc])                # 반환점
    G = np.array([5.05, yc])                # 안내점
    # 안내점 방향(직선 0.38T): 출발점에서 고리 안을 지나 반환점 너머 안내점까지
    ax.plot([S[0], G[0]], [S[1], G[1]], ls=(0, (2, 2.5)), color=MID, lw=0.8, zorder=1)
    # ② 진출 구간(위쪽 호, 실선)
    out = bezier([S, (1.45, yc + 0.4), (2.375, yc + 0.4), (3.6, yc + 0.4), R])
    ax.plot(out[:, 0], out[:, 1], color=INK, lw=2.4, zorder=3, solid_capstyle="round")
    k = len(out) // 2
    arrow(ax, out[k - 2], out[k + 2], ms=17, lw=0)
    ax.text(2.33, yc + 0.47, "② Outbound part", fontsize=FS_A, color=INK, ha="right", va="bottom", fontweight="bold")
    ax.text(2.38, yc + 0.47, "beam search (Fig. 2)", fontsize=FS_S, color=BLUE, ha="left", va="bottom")
    # ④ 반환 구간(아래쪽 호, 점선)
    back = bezier([R, (3.6, yc - 0.4), (2.375, yc - 0.4), (1.45, yc - 0.4), S])
    ax.plot(back[:, 0], back[:, 1], color=INK, lw=2.4, ls=(0, (4, 2.5)), zorder=3)
    k = len(back) // 2
    arrow(ax, back[k - 2], back[k + 2], ms=17, lw=0)
    ax.text(3.45, yc - 0.42, "④ Return part", fontsize=FS_A, color=INK, ha="left", va="center", fontweight="bold")
    ax.text(4.42, yc - 0.42, "least-cost search (Eq. (2))", fontsize=FS_S, color=BLUE, ha="left", va="center")
    # 고리 안: 전체 길이
    ax.text(2.375, yc - 0.17, "Outbound + return = $T$ (±10%)", fontsize=FS_S + 0.3, color=INK, ha="center", va="center")
    # ③ 반환점, ① 안내점, 출발점
    ax.plot(*R, marker="o", color=INK, ms=9, zorder=5)
    ax.text(R[0] + 0.1, R[1] + 0.08, "③ Turnaround", fontsize=FS_A, color=INK, ha="left", va="bottom", fontweight="bold")
    ax.text(R[0] + 0.12, R[1] - 0.07, "(Fig. 3)", fontsize=FS_S, color=BLUE, ha="left", va="top")
    ax.plot(*G, marker="^", color=INK, ms=9, zorder=5)
    ax.text(G[0] + 0.12, G[1] + 0.06, "① Guide point", fontsize=FS_A, color=INK, ha="left", va="bottom", fontweight="bold")
    ax.text(G[0] + 0.12, G[1] - 0.04, "sets direction only\n(straight 0.38$T$)", fontsize=FS_S, color=MID, ha="left", va="top")
    ax.plot(*S, marker="s", color=INK, ms=9, zorder=5)
    ax.text(S[0] - 0.12, S[1], "Start", fontsize=FS_A, color=INK, ha="right", va="center", fontweight="bold")


CARDS = [  # (머리, 설명 줄들, 선호 비용 p를 쓰는지)
    ("① Guide point", ["0.38$T$ straight", "from the start", "(1 of 16 directions)"], False),
    ("② Outbound", ["Diverse beam", "search (Fig. 2)"], True),
    ("③ Turnaround", ["5 candidates with", "total length near $T$"], False),
    ("④ Return", ["Least-cost search", "(Eq. (2))"], True),
    ("⑤ Select", ["Error within ±10%,", "up to 3 routes"], False),
]
FS_H, FS_B = 9.0, 7.8        # 카드 머리, 설명 글자 크기(pt)
PALE = "#eeeee9"


def pill(ax, cx, cy, w, h, text, fc, tc, bold=False, fs=FS_B):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h, boxstyle=f"round,pad=0,rounding_size={h / 2}",
                                fc=fc, ec="none", zorder=5))
    ax.text(cx, cy, text, fontsize=fs, color=tc, ha="center", va="center", fontweight="bold" if bold else "normal", zorder=6)


def panel_b(ax):
    """(b) 처리 흐름: 카드 5장. 입력·출력은 회색 알약, 선호 비용 p는 ②·④ 카드의 파랑 태그, 반복은 ④→② 되돌이 화살표."""
    ax.text(0.02, HB - 0.02, "(b) Processing flow", fontsize=FS_T + 0.5, color=INK, ha="left", va="top")
    n, gap = len(CARDS), 0.17
    cw = (W - 0.04 - gap * (n - 1)) / n
    ch, hh, yb = 0.86, 0.26, 0.36              # 카드 높이, 머리 높이, 카드 아래 끝
    xs = [0.02 + i * (cw + gap) for i in range(n)]
    for x, (head, lines, usep) in zip(xs, CARDS):
        col = BLUE if usep else "#5f5e59"
        ax.add_patch(FancyBboxPatch((x, yb), cw, ch, boxstyle="round,pad=0,rounding_size=0.05",
                                    fc=PALEB if usep else "white", ec=col, lw=1.1, zorder=2))
        ax.add_patch(FancyBboxPatch((x, yb + ch - hh), cw, hh, boxstyle="round,pad=0,rounding_size=0.05",
                                    fc=col, ec=col, lw=1.1, zorder=3))
        ax.add_patch(Rectangle((x, yb + ch - hh), cw, hh / 2, fc=col, ec="none", zorder=3))  # 머리 아래 모서리는 각지게
        ax.text(x + cw / 2, yb + ch - hh / 2, head, fontsize=FS_H, color="white", ha="center", va="center", fontweight="bold", zorder=4)
        body_top, body_bot = yb + ch - hh, yb + (0.24 if usep else 0.0)
        ax.text(x + cw / 2, (body_top + body_bot) / 2, "\n".join(lines), fontsize=FS_B, color=INK, ha="center", va="center",
                linespacing=1.2, zorder=4)
        if usep:
            pill(ax, x + cw / 2, yb + 0.14, cw - 0.22, 0.17, "uses cost $p$", BLUE, "white", bold=True, fs=FS_B - 0.4)
    yc = yb + (ch - hh) / 2
    for i in range(n - 1):
        arrow(ax, (xs[i] + cw + 0.015, yc), (xs[i + 1] - 0.015, yc), ms=11, lw=1.3)
    # 입력: 회색 알약에서 ①로
    iw = 3.2
    pill(ax, 0.02 + iw / 2, yb + ch + 0.22, iw, 0.22, "Input: start $s$, target distance $T$, weights $\\alpha$", PALE, INK, fs=FS_B + 0.2)
    arrow(ax, (xs[0] + cw / 2, yb + ch + 0.11), (xs[0] + cw / 2, yb + ch + 0.01), ms=9, lw=1.2)
    # 반복: ④ 아래에서 ② 아래로 되돌아감
    x2, x4, yl = xs[1] + cw / 2, xs[3] + cw / 2, 0.15
    ax.plot([x4, x4, x2], [yb - 0.01, yl, yl], color="#5f5e59", lw=1.1, zorder=1)
    arrow(ax, (x2, yl), (x2, yb - 0.02), color="#5f5e59", ms=9, lw=1.1)
    ax.text((x2 + x4) / 2, yl, "Repeat for each of the 9 beams", fontsize=FS_B, color=INK, ha="center", va="center", zorder=5,
            bbox=dict(fc="white", ec="none", pad=1.0))
    # 출력: ⑤에서 회색 알약으로
    x5, ow = xs[4] + cw / 2, 1.45
    arrow(ax, (x5, yb - 0.01), (x5, yl + 0.12), ms=9, lw=1.2)
    pill(ax, min(x5, W - 0.03 - ow / 2), yl + 0.01, ow, 0.22, "Output: loop routes", PALE, INK, bold=True, fs=FS_B + 0.2)


def main():
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")
    panel_a(ax, HB)
    panel_b(ax)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.savefig(OUT, dpi=300, facecolor="white")
    print("저장:", OUT, f"(상자 사이 {GAP:.2f}인치)")


if __name__ == "__main__":
    main()

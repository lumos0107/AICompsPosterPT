"""원고 v4 그림 2(반환점 선택, 한 단 폭, 2026-11-11).
가상 바둑판 도로(칸 100 m, 강 위 다리 2곳)에서 3.4절 반환점 선택 두 단계를 실제로 계산해 그린다.
비용은 수식 (3)처럼 지나온 간선 x(1+5), 진출 구간 근처 간선 x(1+3)이고, 회전·선호는 생략한다.
계산은 ../v4_검토/explain_turnaround.py와 같다.
실행: py -I 원고/그림_v4/make_fig_turn.py → 그림2_반환점.png
"""
import heapq
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.stdout.reconfigure(encoding="utf-8")
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False
HERE = os.path.dirname(os.path.abspath(__file__))
INK, MID, LIGHT, BLUE, ORANGE = "#1f1f1f", "#9a9a9a", "#e4e4e4", "#2a78d6", "#e8893a"
MM = 1 / 25.4

W, H, D, T, CT = 10, 8, 100, 2600, 60
S = (1, 1)
# 예시는 ../v4_검토/find_toy.py로 고른 것(반환점이 멈춘 곳이 아니고, 1단계 값과 2단계 값이 다른 후보가 있는 깔끔한 예)
OUT = [(1, 1), (1, 2), (2, 2), (3, 2), (3, 3), (3, 4), (3, 5), (4, 5), (5, 5), (6, 5), (6, 6), (6, 7), (7, 7), (8, 7)]
BRIDGES = {3, 7}   # y=2와 y=3 사이가 강, x=3과 x=7에만 다리


def nbrs(n):
    x, y = n
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if 0 <= x + dx < W and 0 <= y + dy < H:
            if dy and {y, y + dy} == {2, 3} and x not in BRIDGES:
                continue
            yield (x + dx, y + dy)


def ek(a, b):
    return tuple(sorted((a, b)))


def search(k):
    """출발점에서 간선 상태 다익스트라(꺾일 때마다 CT). 벌점 대상은 OUT[0..k]까지의 진출 구간.
    돌려주는 함수 path(n)은 n → ... → 출발점 경로."""
    pre = OUT[:k + 1]
    out_e = {ek(pre[i], pre[i + 1]) for i in range(len(pre) - 1)}
    near_n = set(pre) | {m for p in pre for m in nbrs(p)}
    START = (None, S)
    dist, prev, best = {START: 0.0}, {}, {S: START}
    pq = [(0.0, START)]
    while pq:
        d, st = heapq.heappop(pq)
        if d > dist[st]:
            continue
        pu, u = st
        for v in nbrs(u):
            if v == pu:
                continue
            e = ek(u, v)
            c = D * (1 + (5 if e in out_e else 0) + (3 if (u in near_n and v in near_n and e not in out_e) else 0))
            if pu is not None and (u[0] - pu[0], u[1] - pu[1]) != (v[0] - u[0], v[1] - u[1]):
                c += CT
            ns = (u, v)
            if d + c < dist.get(ns, 1e18):
                dist[ns], prev[ns] = d + c, st
                heapq.heappush(pq, (d + c, ns))
                if v not in best or d + c < dist[best[v]]:
                    best[v] = ns

    def path(n):
        st, p = best[n], []
        while st != START:
            p.append(st[1]); st = prev[st]
        return p + [S]
    return path, out_e


path1, _ = search(len(OUT) - 1)
rows = []
for i, n in enumerate(OUT[1:], 1):
    rp = path1(n)
    rows.append(dict(i=i, n=n, go=i * D, back=(len(rp) - 1) * D, ret=rp))
for r in rows:
    r["sum"] = r["go"] + r["back"]
top5 = sorted(rows, key=lambda r: abs(r["sum"] - T))[:5]
ref = []
for r in top5:
    p2, oute = search(r["i"])
    rp = p2(r["n"])
    back = (len(rp) - 1) * D
    retr = sum(D for a, b in zip(rp[:-1], rp[1:]) if ek(a, b) in oute)
    ref.append(dict(i=r["i"], n=r["n"], go=r["go"], back=back, sum=r["go"] + back, retr=retr, ret=rp, rough=r["sum"]))
ok = [r for r in ref if abs(r["sum"] - T) <= 0.1 * T]
best = min(ok or ref, key=lambda r: (r["retr"], abs(r["sum"] - T)))
for r in sorted(ref, key=lambda r: r["i"]):
    print(f"P{r['i']}: 1단계 {r['rough']} → 2단계 {r['sum']} (되밟기 {r['retr']})")
print("반환점 P", best["i"])


def base(ax, title):
    ax.fill_between([-0.4, W - 0.6], 2.28, 2.72, color="#dfe8f1", lw=0, zorder=0)
    ax.text(W - 0.55, 2.5, "강", fontsize=5.2, color="#5a7a99", va="center", ha="right")
    for x in range(W):
        ax.plot([x, x], [0, 2], color=LIGHT, lw=0.45, zorder=0)
        ax.plot([x, x], [3, H - 1], color=LIGHT, lw=0.45, zorder=0)
        if x in BRIDGES:
            ax.plot([x, x], [2, 3], color=MID, lw=1.0, zorder=1)
    for y in range(H):
        ax.plot([0, W - 1], [y, y], color=LIGHT, lw=0.45, zorder=0)
    ax.scatter(*S, marker="s", s=12, color=INK, zorder=8)
    ax.text(S[0] - 0.4, S[1], "출발점", fontsize=5.4, ha="right", va="center",
            bbox=dict(fc="white", ec="none", pad=0.3))
    ax.set_xlim(-1.4, W - 0.5); ax.set_ylim(-1.3, H + 0.1); ax.set_aspect("equal"); ax.axis("off")
    ax.text(-1.4, H + 0.15, title, fontsize=6.1, ha="left", va="bottom")


def line(ax, pts, **kw):
    ax.plot([p[0] for p in pts], [p[1] for p in pts], solid_capstyle="round", **kw)


# 기본은 검정·회색, 후보 P1~P5(진출 경로 순서)만 서로 다른 색(사용자 11/11). 색은 dataviz 기본 범주 색 1~5번.
CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
OFF = [-0.16, -0.08, 0.0, 0.08, 0.16]   # 겹치는 길이 보이도록 후보마다 조금씩 비켜 그림
cands = sorted(top5, key=lambda r: r["i"])
COL = {r["i"]: CAT[j] for j, r in enumerate(cands)}
NAME = {r["i"]: f"P{j + 1}" for j, r in enumerate(cands)}
SHIFT = {r["i"]: OFF[j] for j, r in enumerate(cands)}
REF = {r["i"]: r for r in ref}
LBL = {1: (0, 0.38, "center", "bottom"), 2: (-0.32, 0, "right", "center"), 3: (0, 0.38, "center", "bottom"),
       4: (0, 0.38, "center", "bottom"), 5: (0, 0.38, "center", "bottom")}


def shifted(pts, o):
    return [(x + o, y + o) for x, y in pts]


def cand_marks(ax, chosen=None):
    for j, r in enumerate(cands, 1):
        big = chosen is not None and r["i"] == chosen
        ax.scatter(*r["n"], s=22 if big else 13, color=COL[r["i"]], edgecolor=INK if big else "white",
                   lw=0.7 if big else 0.5, zorder=9)
        dx, dy, ha, va = LBL[j]
        ax.text(r["n"][0] + dx, r["n"][1] + dy, NAME[r["i"]], fontsize=5.0, ha=ha, va=va, zorder=10)


fig, (a, b) = plt.subplots(1, 2, figsize=(75 * MM, 38 * MM), dpi=300)
# (a) 1단계: 검정 = 빔이 나아간 길, 색 점선 = 후보마다 한 번의 탐색에서 얻은 돌아오는 길
base(a, "(a) 한 번 탐색해 후보 5개")
line(a, OUT, color=INK, lw=1.1, zorder=3)
for r in cands:
    line(a, shifted(r["ret"], SHIFT[r["i"]]), color=COL[r["i"]], lw=0.75, ls=(0, (2.4, 1.2)), zorder=4)
a.scatter(*OUT[-1], marker="x", s=9, color=INK, lw=0.6, zorder=11)
a.text(OUT[-1][0] + 0.3, OUT[-1][1] - 0.3, "$0.51T$", fontsize=5.0, ha="left", va="top")
cand_marks(a)
a.text(-1.4, -1.25, "색 점선: 한 번의 탐색으로 얻은 돌아오는 길", fontsize=5.0, color="#555555", ha="left", va="bottom")
# (b) 2단계: 검정 실선 = 진출 구간, 검정 점선 = 반환 구간, 회색 점선 = 버린 부분, 색 점선 = 후보별로 다시 잰 길
k = best["i"]
base(b, "(b) 후보마다 다시 탐색해 선택")
line(b, OUT[:k + 1], color=INK, lw=1.1, zorder=3)
line(b, OUT[k:], color=MID, lw=0.8, ls=(0, (1, 1.2)), zorder=3)
for r in cands:
    if r["i"] != k:
        line(b, shifted(REF[r["i"]]["ret"], SHIFT[r["i"]]), color=COL[r["i"]], lw=0.6, ls=(0, (2.4, 1.2)), alpha=0.9, zorder=4)
line(b, best["ret"], color=INK, lw=1.2, ls=(0, (3, 1.4)), zorder=5)
b.scatter(*OUT[-1], marker="x", s=9, color=MID, lw=0.6, zorder=11)
cand_marks(b, chosen=k)
# 1단계 대략값과 다시 잰 값이 다른 후보에 두 값을 적는다
for r in cands:
    f = REF[r["i"]]
    if f["rough"] != f["sum"]:
        b.text(f["n"][0] - 0.35, f["n"][1], f"{f['rough']:,} → {f['sum']:,} m", fontsize=4.8, color="#555555", ha="right", va="center")
b.text(-1.4, -1.25, f"반환점 {NAME[k]}: 전체 {best['sum']:,} m, 되밟기 {best['retr']} m",
       fontsize=5.0, color="#555555", ha="left", va="bottom")
fig.subplots_adjust(0.01, 0.0, 0.99, 0.97, wspace=0.06)
fig.savefig(os.path.join(HERE, "그림2_반환점.png"), dpi=300, facecolor="white")

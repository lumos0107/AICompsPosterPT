"""사용자 설명용 그림(원고용 아님): 바둑판 가상 도로(칸 100 m)에서 반환점 고르기를 실제로 계산해 단계별로 그린다.
비용은 식 (3)과 같은 방식(지나온 길 x6, 근처 길 x4, 회전과 선호는 생략). 실행: py -I v4_검토/explain_turnaround.py → 반환점_설명.png"""
import heapq
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False
HERE = os.path.dirname(os.path.abspath(__file__))
W, H, D = 10, 8, 100
T = 2600
S = (1, 1)
OUT = [(1, 1), (1, 2), (2, 2), (2, 3), (3, 3), (3, 4), (4, 4), (5, 4), (5, 5), (6, 5), (7, 5), (7, 6), (8, 6), (8, 7)]  # 빔이 0.51T까지 나아간 경로(13칸 = 1,300 m)
nodes = [(x, y) for x in range(W) for y in range(H)]


BRIDGES = {2, 8}   # y=2와 y=3 사이에 강이 있고, x=2와 x=8에만 다리가 있다


def nbrs(n):
    x, y = n
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if 0 <= x + dx < W and 0 <= y + dy < H:
            if dy and {y, y + dy} == {2, 3} and x not in BRIDGES:
                continue
            yield (x + dx, y + dy)


def ek(a, b):
    return tuple(sorted((a, b)))


def search(prefix_len):
    """반환점 후보가 OUT[prefix_len]일 때(1단계는 전체) 지나온 길 x6, 근처 길 x4로 출발점에서 다익스트라."""
    pre = OUT[:prefix_len + 1]
    out_e = {ek(pre[i], pre[i + 1]) for i in range(len(pre) - 1)}
    near_n = set(pre) | {m for p in pre for m in nbrs(p)}
    dist, prev = {S: 0.0}, {}
    pq = [(0.0, S)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        for v in nbrs(u):
            e = ek(u, v)
            mult = 1 + (5 if e in out_e else 0) + (3 if (u in near_n and v in near_n and e not in out_e) else 0)
            nd = d + D * mult
            if nd < dist.get(v, 1e18):
                dist[v], prev[v] = nd, u
                heapq.heappush(pq, (nd, v))
    return dist, prev, out_e


def path_to(prev, n):
    p = [n]
    while p[-1] != S:
        p.append(prev[p[-1]])
    return p   # n → ... → S


# 1단계: 전체를 벌점 대상으로 한 번
dist1, prev1, out1 = search(len(OUT) - 1)
rows = []
for i, n in enumerate(OUT[1:], 1):
    rp = path_to(prev1, n)
    back = (len(rp) - 1) * D
    rows.append((i, n, i * D, back, i * D + back, rp))
top5 = sorted(rows, key=lambda r: abs(r[4] - T))[:5]
# 2단계: 후보마다 앞부분만 벌점 대상으로 다시
refined = []
for i, n, go, _, _, _ in top5:
    d2, p2, oute = search(i)
    rp = path_to(p2, n)
    back = (len(rp) - 1) * D
    retr = sum(D for a, b in zip(rp[:-1], rp[1:]) if ek(a, b) in oute)
    refined.append((i, n, go, back, go + back, retr, rp))
ok = [r for r in refined if abs(r[4] - T) <= 0.1 * T]
best = min(ok or refined, key=lambda r: (r[5], abs(r[4] - T)))
for r in rows:
    print("1단계", r[0], r[2], r[3], r[4])
for r in refined:
    print("2단계", r[0], r[2], r[3], r[4], "되밟기", r[5])
print("반환점", best[0])


def base(ax, title):
    ax.fill_between([-0.5, W - 0.5], 2.25, 2.75, color="#cfe3f7", zorder=0)
    ax.text(W - 0.6, 2.5, "강", fontsize=9, color="#2a78d6", va="center", ha="right")
    for x in range(W):
        ax.plot([x, x], [0, 2], color="#e2e2e2", lw=0.8, zorder=0)
        ax.plot([x, x], [3, H - 1], color="#e2e2e2", lw=0.8, zorder=0)
        if x in BRIDGES:
            ax.plot([x, x], [2, 3], color="#8c8c8c", lw=2.2, zorder=1)
    for y in range(H):
        ax.plot([0, W - 1], [y, y], color="#e2e2e2", lw=0.8, zorder=0)
    ax.scatter(*S, marker="s", s=70, color="black", zorder=6)
    ax.text(S[0] - 0.35, S[1] - 0.45, "출발점", fontsize=9)
    ax.set_xlim(-0.6, W - 0.4); ax.set_ylim(-0.8, H - 0.3); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(title, fontsize=11, loc="left")


def line(ax, pts, **kw):
    ax.plot([p[0] for p in pts], [p[1] for p in pts], **kw)


fig, axs = plt.subplots(2, 2, figsize=(13, 11.5), dpi=110)
# ①
ax = axs[0, 0]
base(ax, "① 빔이 목표의 약 절반(0.51T)까지 나아가고 멈춘다")
line(ax, OUT, color="black", lw=3, zorder=3)
ax.scatter(*OUT[-1], marker="x", s=90, color="black", zorder=6)
ax.text(OUT[-1][0] + 0.15, OUT[-1][1] + 0.15, "멈춘 곳", fontsize=9)
ax.text(0, -0.75, f"목표 T = {T:,} m, 바둑판 한 칸 = 100 m, 나아간 길 1,300 m", fontsize=9)
# ②
ax = axs[0, 1]
base(ax, "② 출발점에서 다익스트라 한 번 → 모든 지점의 '돌아오는 길'")
line(ax, OUT, color="black", lw=3, zorder=3)
samples = [rows[3], rows[8], rows[-1]]
cols = ["#2a78d6", "#e8893a", "#7a4fc9"]
for r, c in zip(samples, cols):
    line(ax, r[5], color=c, lw=2, ls=(0, (4, 2)), zorder=4)
    ax.scatter(*r[1], s=60, color=c, zorder=7)
    ax.text(r[1][0] + 0.15, r[1][1] - 0.4, f"P{r[0]}: 돌아오는 길 {r[3]:,} m", fontsize=9, color=c)
ax.text(0, -0.75, "지나온 길(검정)은 통행료 6배, 바로 옆 길은 4배 → 돌아오는 길은 다른 길로 돈다", fontsize=9)
# ③
ax = axs[1, 0]
base(ax, "③ 지점마다 '나아간 길이 + 돌아오는 길이'를 더해 목표에 가까운 5곳")
line(ax, OUT, color="black", lw=3, zorder=3)
for r in rows:
    on = r in top5
    ax.scatter(*r[1], s=70 if on else 18, color="#e8893a" if on else "#9a9a9a", zorder=7)
    if on:
        ax.text(r[1][0] - 0.2, r[1][1] + 0.25, f"P{r[0]}", fontsize=9, color="#c4630f")
tbl = "지점  나아간+돌아오는 = 합\n" + "\n".join(f"P{r[0]:<3} {r[2]:>5,} + {r[3]:>5,} = {r[4]:>5,}" for r in sorted(top5, key=lambda r: r[0]))
ax.text(4.6, 0.2, tbl, fontsize=9, family="Malgun Gothic", va="bottom", bbox=dict(fc="white", ec="#cccccc"))
ax.text(0, -0.75, "1단계는 '멈춘 곳까지 전부 지나온 길'로 보고 잰 대략값이다", fontsize=9)
# ④
ax = axs[1, 1]
i_b = best[0]
base(ax, f"④ 5곳만 다시 정확히 재서 반환점 선택 → P{i_b}")
line(ax, OUT[:i_b + 1], color="black", lw=3, zorder=3)
line(ax, OUT[i_b:], color="#9a9a9a", lw=2.5, ls=(0, (1.5, 1.5)), zorder=3)
line(ax, best[6], color="#2a78d6", lw=3, ls=(0, (4, 2)), zorder=4)
ax.scatter(*OUT[i_b], s=110, color="black", zorder=7)
ax.text(OUT[i_b][0] - 0.9, OUT[i_b][1] + 0.3, "반환점", fontsize=10)
ax.text(OUT[-1][0] - 0.2, OUT[-1][1] + 0.25, "버림", fontsize=9, color="#666666")
ax.text(0, -0.75, f"진출 {best[2]:,} m + 반환 {best[3]:,} m = {best[4]:,} m (목표 {T:,} m), 되밟기 {best[5]} m", fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(HERE, "반환점_설명.png"), facecolor="white")

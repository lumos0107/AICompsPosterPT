"""20m에서 큰 교차로가 빠져 반경을 다시 묻기 위한 비교 값. 자른 그래프(그래프_도심.npz) 기준.

안 A: 반경 r 안의 차수 3+ 노드 전부를 신호 노드로 (r = 20, 25, 30).
안 B: 20m 안 노드 전부 + 20m에 하나도 안 붙은 묶음은 30m 안에서 묶음 점에 가장 가까운 노드 하나만 추가.
무작위 비교: 같은 묶음 모양을 무작위 도로 점으로 옮겨 같은 규칙을 적용(시드 20261110, 묶음당 20회).
결과: 반경안.out
"""
import csv
import os
import sys

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
G = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\새그래프_1110"
sys.path.insert(0, r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\데이터진단_1109\수집계획용\에이전트검토")
from lib_shp import read_shp, dbf_columns

sys.stdout.reconfigure(encoding="utf-8")
GPATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "그래프_도심.npz")
TAG = sys.argv[2] if len(sys.argv) > 2 else ""
EXTRA = sys.argv[3] if len(sys.argv) > 3 else None
out = open(os.path.join(HERE, f"반경안{TAG and '_' + TAG}.out"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out.write(s + "\n")


ROAD = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵\연속수치지도_제주_20261109\풀기\N3L_A0020000\N3L_A0020000"
g = np.load(GPATH)
xy, A, B, L, main, deg, rec = g["xy"], g["A"], g["B"], g["L"], g["main"], g["deg_full"], g["rec"]
wid = np.array([float(x or 0) for x in dbf_columns(ROAD, ["RVWD"])["RVWD"]])
nodes = np.unique(np.r_[A[main], B[main]])
jn = nodes[deg[nodes] >= 3]
tj = cKDTree(xy[jn])
# 노드에 붙은 가장 넓은 도로 폭과 두 번째 폭
w1 = np.zeros(len(xy))
w2 = np.zeros(len(xy))
for e in np.where(main)[0].tolist():
    for n in (A[e], B[e]):
        w = wid[rec[e]]
        if w > w1[n]:
            w1[n], w2[n] = w, w1[n]
        elif w > w2[n]:
            w2[n] = w
big = (w2[jn] >= 20)  # 20m 이상 도로 둘 이상이 만나는 노드
sig = [r for r in csv.DictReader(open(os.path.join(G, "신호1000.csv"), encoding="utf-8-sig")) if r["지역"] == "제주 도심"]
if EXTRA:
    sig += list(csv.DictReader(open(EXTRA, encoding="utf-8-sig")))
Q = np.array([(float(r["x5179"]), float(r["y5179"])) for r in sig])
pr = cKDTree(Q).query_pairs(30.0, output_type="ndarray")
nC, cl = connected_components(coo_matrix((np.ones(len(pr)), (pr[:, 0], pr[:, 1])), shape=(len(Q), len(Q))), directed=False)


def mark(P, lab, n, rule, r):
    near = tj.query_ball_point(P, r if rule == "A" else 20.0)
    m = set(i for lst in near for i in lst)
    att = np.zeros(n, bool)
    for k, lst in zip(lab.tolist(), near):
        if lst:
            att[k] = True
    if rule == "B":
        d, i = tj.query(P)
        for k in np.where(~att)[0].tolist():
            sel = np.where(lab == k)[0]
            j = sel[np.argmin(d[sel])]
            if d[j] <= 30:
                m.add(int(i[j]))
                att[k] = True
    return m, att


# 무작위 이동 묶음
rng = np.random.default_rng(20261110)
# 도로 길이에 비례한 무작위 점 (간선을 길이 비율로 고르고 양 끝 사이 직선 위 균등 위치; 중점만 쓰면 교차로 근처 짧은 간선이 과다 추출됨)
lines = [p for r_, parts in read_shp(ROAD, clip=False) for p in parts]
road = []
gl_, ga_, gb_ = g["line"], g["a"], g["b"]
for e in np.where(main)[0].tolist():
    p = lines[gl_[e]][ga_[e]:gb_[e] + 1]
    c = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]
    if c[-1] <= 0:
        continue
    k = max(int(round(c[-1] / 5.0)), 1)
    t_ = (np.arange(k) + 0.5) * c[-1] / k
    road.append(np.c_[np.interp(t_, c, p[:, 0]), np.interp(t_, c, p[:, 1])])
road = np.vstack(road)  # cut_jeju.py와 같은 방식(간선을 약 5m 구간으로 나눈 중앙 점)
Cxy = np.c_[np.bincount(cl, weights=Q[:, 0]) / np.bincount(cl), np.bincount(cl, weights=Q[:, 1]) / np.bincount(cl)]
RP, RL = [], []
t = 0
for k in range(nC):
    pts = Q[cl == k] - Cxy[k]
    for b0 in road[rng.choice(len(road), 20, replace=False)]:
        RP.append(pts + b0)
        RL += [t] * len(pts)
        t += 1
RP, RL = np.vstack(RP), np.array(RL)

log(f"차수 3+ 노드 {len(jn):,}, 그중 폭 20m 이상 도로 둘 이상이 만나는 노드 {int(big.sum())}")
log("안 | 묶음 부착 | 무작위 이동 묶음 부착 | 신호 노드 수 | 부착 묶음당 노드 | 큰 교차로 노드 중 신호 노드 | 신호 노드 중 큰 교차로")
for rule, r in (("A", 20), ("A", 25), ("A", 30), ("B", 30)):
    m, att = mark(Q, cl, nC, rule, r)
    _, att_r = mark(RP, RL, t, rule, r)
    mm = np.array(sorted(m))
    bm = big[mm].sum() if len(mm) else 0
    name = f"반경 {r}m" if rule == "A" else "20m + 안 붙은 묶음만 30m 안 가장 가까운 노드 하나"
    log(f"{name} | {att.sum()}/{nC} ({att.mean():.1%}) | {att_r.mean():.1%} | {len(m)} | {len(m) / max(att.sum(), 1):.2f} | {bm}/{int(big.sum())} ({bm / big.sum():.1%}) | {bm / max(len(m), 1):.1%}")
# 큰 교차로 노드 중 1:1,000 점이 30m 안에 있는데 20m 안에는 없는 것
dq = tj.query_ball_point(Q, 30.0)
m30 = set(i for lst in dq for i in lst)
m20 = set(i for lst in tj.query_ball_point(Q, 20.0) for i in lst)
bb = [i for i in np.where(big)[0].tolist()]
log(f"큰 교차로 노드 {len(bb)}개: 20m 신호 노드 {sum(i in m20 for i in bb)}, 30m에서만 {sum((i in m30) and (i not in m20) for i in bb)}, 30m에도 없음 {sum(i not in m30 for i in bb)}")
dn = cKDTree(Q).query(xy[jn[big]])[0]
log("큰 교차로 노드에서 가장 가까운 1:1,000 점까지: " + ", ".join(f"{a}m 안 {(dn <= a).mean():.1%}" for a in (10, 15, 20, 25, 30, 40)) + f", 중앙값 {np.median(dn):.1f}m")
dn_all = cKDTree(Q).query(xy[jn])[0]
log("참고: 모든 차수 3+ 노드: " + ", ".join(f"{a}m 안 {(dn_all <= a).mean():.1%}" for a in (10, 20, 25, 30)))
log("끝")

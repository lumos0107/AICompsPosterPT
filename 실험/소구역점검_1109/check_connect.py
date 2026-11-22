"""수집계획 3장 가 '연결' 점검. 5월 사본 도로중심선, 읽기 전용.

그래프 규칙은 에이전트검토/s4_graph.py와 같다(1cm 공유 꼭짓점 + 막다른 노드 1m 보정).
재현 확인값: 연결요소 1,463, 주 요소 길이비율 95.80%, 총 14,424km, 시험구역 1,045.4km.
"""
import collections
import os
import sys
import time

import numpy as np
from pyproj import Transformer
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

HERE = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\소구역점검_1109"
sys.path.insert(0, r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\데이터진단_1109\수집계획용\에이전트검토")
from lib_shp import FILES, dbf_columns, read_shp

sys.stdout.reconfigure(encoding="utf-8")
out = open(os.path.join(HERE, "연결점검.out"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out.write(s + "\n")
    out.flush()


T0 = time.time()
to5179 = Transformer.from_crs(4326, 5179, always_xy=True)
to4326 = Transformer.from_crs(5179, 4326, always_xy=True)
REGIONS = {"제주시 시험구역": (33.46, 33.54, 126.46, 126.58), "서귀포시내": (33.24, 33.27, 126.53, 126.60)}
BOXES = {}
for name, (la0, la1, lo0, lo1) in REGIONS.items():
    x0, y0 = to5179.transform(lo0, la0)
    x1, y1 = to5179.transform(lo1, la1)
    BOXES[name] = (x0, y0, x1, y1)

lines = [(rec, p) for rec, parts in read_shp(FILES["road"], clip=False) for p in parts]
log("선", len(lines))

# 1) 꼭짓점 -> 노드 (1cm)
allv = np.vstack([p for _, p in lines])
lid = np.concatenate([np.full(len(p), i) for i, (_, p) in enumerate(lines)])
uk, vid = np.unique(np.round(allv / 0.01).astype(np.int64), axis=0, return_inverse=True)
vid = vid.ravel()
nline = np.bincount(np.unique(np.c_[vid, lid], axis=0)[:, 0], minlength=len(uk))
xy = uk * 0.01

# 2) 분기점에서 자름
off = np.cumsum([0] + [len(p) for _, p in lines])
edges = []
for i, (_, p) in enumerate(lines):
    ids = vid[off[i]:off[i + 1]]
    cut = [0] + [j for j in range(1, len(p) - 1) if nline[ids[j]] >= 2] + [len(p) - 1]
    for a, b in zip(cut[:-1], cut[1:]):
        edges.append((int(ids[a]), int(ids[b]), float(np.hypot(*np.diff(p[a:b + 1], axis=0).T).sum()), i, a, b))
u = np.array([e[0] for e in edges])
v = np.array([e[1] for e in edges])
elen = np.array([e[2] for e in edges])

# 3) 막다른 노드 1m 보정
deg = np.bincount(u, minlength=len(uk)) + np.bincount(v, minlength=len(uk))
dead = np.where(deg == 1)[0]
used = np.unique(np.r_[u, v])
adj = collections.defaultdict(set)
for a, b in zip(u.tolist(), v.tolist()):
    adj[a].add(b)
    adj[b].add(a)
snap = []
for dn, g in zip(dead.tolist(), cKDTree(xy[used]).query_ball_point(xy[dead], 1.0, workers=-1)):
    cand = [int(used[j]) for j in g if int(used[j]) != dn and int(used[j]) not in adj[dn]]
    if cand:
        snap.append((dn, min(cand, key=lambda w: float(np.hypot(*(xy[w] - xy[dn]))))))
parent = list(range(len(uk)))


def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


for a, b in snap:
    parent[find(a)] = find(b)
root = np.array([find(i) for i in range(len(uk))])
uu, vv = root[u], root[v]
keep = uu != vv
nodes = np.unique(np.r_[uu, vv])
remap = -np.ones(len(uk), int)
remap[nodes] = np.arange(len(nodes))
A, B, L = remap[uu[keep]], remap[vv[keep]], elen[keep]
kept = [e for e, k in zip(edges, keep) if k]
N = len(nodes)
xyN = xy[nodes]
nc, lab = connected_components(coo_matrix((np.ones(len(A)), (A, B)), shape=(N, N)), directed=False)
Lcc = np.bincount(lab[A], weights=L, minlength=nc)
main = int(Lcc.argmax())
log(f"[재현] 1m 보정 대상 {len(snap)}, 노드 {N:,}, 간선 {len(A):,}, 연결요소 {nc:,}, 주 요소 길이비율 {Lcc[main]/Lcc.sum():.2%}, 총 {Lcc.sum()/1000:,.0f}km")

# 4) 주 요소가 아닌 조각의 위치와 주 요소까지 거리 (주 요소 선을 2m로 조밀화)
m_pts = []
for e, c in zip(kept, lab[A].tolist()):
    if c != main:
        continue
    p = lines[e[3]][1][e[4]:e[5] + 1]
    cum = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]
    t = np.r_[np.arange(0, cum[-1], 2.0), cum[-1]]
    m_pts.append(np.c_[np.interp(t, cum, p[:, 0]), np.interp(t, cum, p[:, 1])])
tm = cKDTree(np.vstack(m_pts))
del m_pts
o_pts, o_lab = [], []
for e, c in zip(kept, lab[A].tolist()):
    if c != main:
        p = lines[e[3]][1][e[4]:e[5] + 1]
        o_pts.append(p)
        o_lab.append(np.full(len(p), c))
o_pts, o_lab = np.vstack(o_pts), np.concatenate(o_lab)
d_all, _ = tm.query(o_pts, workers=-1)
dmin = np.full(nc, np.inf)
np.minimum.at(dmin, o_lab, d_all)
cx = np.bincount(o_lab, weights=o_pts[:, 0], minlength=nc) / np.maximum(np.bincount(o_lab, minlength=nc), 1)
cy = np.bincount(o_lab, weights=o_pts[:, 1], minlength=nc) / np.maximum(np.bincount(o_lab, minlength=nc), 1)

others = [c for c in range(nc) if c != main and Lcc[c] > 0]
log(f"\n[주 요소 밖 조각] {len(others):,}개, {sum(Lcc[c] for c in others)/1000:,.1f}km")
for lo, hi, nm in [(0, 2, "2m 이하"), (2, 5, "2~5m"), (5, 10, "5~10m"), (10, 30, "10~30m"), (30, 100, "30~100m"), (100, 1e12, "100m 초과")]:
    s = [c for c in others if lo < dmin[c] <= hi or (lo == 0 and dmin[c] == 0)]
    log(f"  주 요소까지 {nm}: {len(s):,}개 {sum(Lcc[c] for c in s)/1000:,.1f}km")
for lo, hi, nm in [(0, 100, "100m 미만"), (100, 500, "100~500m"), (500, 1000, "500m~1km"), (1000, 5000, "1~5km"), (5000, 1e12, "5km 이상")]:
    s = [c for c in others if lo <= Lcc[c] < hi]
    log(f"  조각 길이 {nm}: {len(s):,}개 {sum(Lcc[c] for c in s)/1000:,.1f}km")
log("\n[길이 상위 조각 15개] km, 주 요소까지 m, 위도, 경도")
for c in sorted(others, key=lambda c: -Lcc[c])[:15]:
    lo, la = to4326.transform(cx[c], cy[c])
    log(f"  {Lcc[c]/1000:7.1f}km  {dmin[c]:9.1f}m  {la:.4f}, {lo:.4f}")

# 5) 소구역별
mid = (xyN[A] + xyN[B]) / 2
for name, (x0, y0, x1, y1) in BOXES.items():
    ib = (mid[:, 0] >= x0) & (mid[:, 0] <= x1) & (mid[:, 1] >= y0) & (mid[:, 1] <= y1)
    in_main = lab[A] == main
    log(f"\n[{name}] 상자 EPSG:5179 {x0:.0f} {y0:.0f} {x1:.0f} {y1:.0f}")
    log(f"  도로 {L[ib].sum()/1000:,.1f}km, 간선 {ib.sum():,}")
    log(f"  전체 그래프의 주 요소에 속함 {L[ib & in_main].sum()/1000:,.1f}km ({L[ib & in_main].sum()/L[ib].sum():.2%}), 밖 {L[ib & ~in_main].sum()/1000:,.2f}km")
    cs = sorted(set(lab[A[ib & ~in_main]].tolist()), key=lambda c: -Lcc[c])
    log(f"  상자 안에 걸친 주 요소 밖 조각 {len(cs)}개, 2m 안 {sum(1 for c in cs if dmin[c] <= 2)}개, 5m 안 {sum(1 for c in cs if dmin[c] <= 5)}개, 30m 안 {sum(1 for c in cs if dmin[c] <= 30)}개")
    for c in cs[:8]:
        lo, la = to4326.transform(cx[c], cy[c])
        log(f"    {Lcc[c]/1000:6.2f}km  주 요소까지 {dmin[c]:8.1f}m  {la:.5f}, {lo:.5f}")
    # 상자 안 간선만으로 만든 부분 그래프
    Ab, Bb, Lb = A[ib], B[ib], L[ib]
    nb, lb = connected_components(coo_matrix((np.ones(len(Ab)), (Ab, Bb)), shape=(N, N)), directed=False)
    Lc = np.bincount(lb[Ab], weights=Lb, minlength=nb)
    log(f"  상자 안 간선만의 부분 그래프: 요소 {int((Lc > 0).sum()):,}개, 최대 요소 길이비율 {Lc.max()/Lc.sum():.2%}, 1km 미만 요소 {int(((Lc > 0) & (Lc < 1000)).sum()):,}개 {Lc[(Lc > 0) & (Lc < 1000)].sum()/1000:,.1f}km")

# 6) 폭 3m 미만 구간을 뺐을 때 (영상 표본에서 길이 안 보이는 경우가 여기에 몰림)
wid = np.array([float(x or 0) for x in dbf_columns(FILES["road"], ["RVWD"])["RVWD"]])
ew = wid[[lines[e[3]][0] for e in kept]]
narrow = ew < 3
ISLANDS = {"우도": (33.50, 126.95), "추자도": (33.95, 126.31), "가파도": (33.17, 126.27), "비양도": (33.41, 126.23), "마라도": (33.12, 126.27)}
isl = []
for c in others:
    lo, la = to4326.transform(cx[c], cy[c])
    if Lcc[c] > 5000 and dmin[c] > 500 and any(abs(la - a) < 0.03 and abs(lo - b) < 0.03 for a, b in ISLANDS.values()):
        isl.append(c)
isl_km = sum(Lcc[c] for c in isl) / 1000
log(f"\n[섬] {len(isl)}개 {isl_km:.1f}km, 섬 뺀 본섬 기준 주 요소 길이비율 {Lcc[main]/(Lcc.sum()-sum(Lcc[c] for c in isl)):.2%}")
log(f"[폭 3m 미만] 전체 {L[narrow].sum()/1000:,.1f}km / {L.sum()/1000:,.1f}km = {L[narrow].sum()/L.sum():.1%}")
A2, B2, L2 = A[~narrow], B[~narrow], L[~narrow]
n2, lab2 = connected_components(coo_matrix((np.ones(len(A2)), (A2, B2)), shape=(N, N)), directed=False)
Lc2 = np.bincount(lab2[A2], weights=L2, minlength=n2)
m2 = int(Lc2.argmax())
log(f"  빼면 도로 {L2.sum()/1000:,.1f}km, 요소 {int((Lc2 > 0).sum()):,}개, 주 요소 길이비율 {Lc2[m2]/L2.sum():.2%}")
for name, (x0, y0, x1, y1) in BOXES.items():
    ib = (mid[:, 0] >= x0) & (mid[:, 0] <= x1) & (mid[:, 1] >= y0) & (mid[:, 1] <= y1)
    in2 = (~narrow) & (lab2[A] == m2)
    log(f"  {name}: 폭 3m 미만 {L[ib & narrow].sum()/1000:,.1f}km / {L[ib].sum()/1000:,.1f}km = {L[ib & narrow].sum()/L[ib].sum():.1%}, 뺀 뒤 주 요소에 남는 도로 {L[ib & in2].sum()/1000:,.1f}km (남은 도로의 {L[ib & in2].sum()/L[ib & ~narrow].sum():.2%})")
log("\n끝", round(time.time() - T0, 1), "초")

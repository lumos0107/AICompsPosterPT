"""도로중심선만으로 그래프 재구성, 품질 기준 계산 가능성 측정."""
import collections
import csv
import glob
import io
import math
import os
import pickle
import struct
import sys
import time
import zipfile
import numpy as np
from pyproj import Transformer
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

sys.path.insert(0, r"C:\Users\seungjun\AppData\Local\Temp\plan_review_Br6p2s")
from lib_shp import *

sys.stdout.reconfigure(encoding="utf-8")
TMP = r"C:\Users\seungjun\AppData\Local\Temp\plan_review_Br6p2s"
T0 = time.time()
to5179 = Transformer.from_crs(4326, 5179, always_xy=True)
BOX = (33.46, 33.54, 126.46, 126.58)
bx0, by0 = to5179.transform(BOX[2], BOX[0])
bx1, by1 = to5179.transform(BOX[3], BOX[1])
print("시험구역 EPSG:5179", round(bx0), round(by0), round(bx1), round(by1))

recs = read_shp(FILES["road"], clip=False)
attr = dbf_columns(FILES["road"], ["RDDV", "PVQT", "DVYN", "RDLN", "RVWD", "ONSD"])
lines = []  # (record, pts)
for idx, parts in recs:
    for p in parts:
        lines.append((idx, p))
print("lines", len(lines), time.time() - T0)

# 1) 꼭짓점 -> 노드 (1cm 격자)
allv = np.vstack([p for _, p in lines])
lid = np.concatenate([np.full(len(p), i) for i, (_, p) in enumerate(lines)])
key = np.round(allv / 0.01).astype(np.int64)
uk, vid, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True)
vid = vid.ravel()
print("고유 꼭짓점", len(uk))
# 서로 다른 선이 쓰는 수
pairs = np.unique(np.c_[vid, lid], axis=0)
nline = np.bincount(pairs[:, 0], minlength=len(uk))
print("2개 이상의 선이 공유하는 꼭짓점", int((nline >= 2).sum()))

# 2) 선을 분기점(끝점, 공유 꼭짓점)에서 자름
off = np.cumsum([0] + [len(p) for _, p in lines])
edges = []  # (u, v, length, line index)
for i, (rec, p) in enumerate(lines):
    ids = vid[off[i]:off[i + 1]]
    cut = [0] + [j for j in range(1, len(p) - 1) if nline[ids[j]] >= 2] + [len(p) - 1]
    for a, b in zip(cut[:-1], cut[1:]):
        L = float(np.hypot(*np.diff(p[a:b + 1], axis=0).T).sum())
        edges.append((int(ids[a]), int(ids[b]), L, i, a, b))
print("기본 간선(분기점 기준)", len(edges), "자기루프", sum(1 for e in edges if e[0] == e[1]))
E = np.array([(e[0], e[1], e[2]) for e in edges])
u, v = E[:, 0].astype(int), E[:, 1].astype(int)
V_used = np.unique(np.r_[u, v])
print("사용 노드", len(V_used))
xy = uk * 0.01

# 3) 1m 끝점 보정
deg = np.bincount(u, minlength=len(uk)) + np.bincount(v, minlength=len(uk))
dead = np.where(deg == 1)[0]
tall = cKDTree(xy[V_used])
gs = tall.query_ball_point(xy[dead], 1.0, workers=-1)
snap = []
adj = collections.defaultdict(set)
for a, b in zip(u, v):
    adj[int(a)].add(int(b)); adj[int(b)].add(int(a))
for dn, g in zip(dead, gs):
    best = None; bd = 9
    for j in g:
        w = int(V_used[j])
        if w == int(dn) or w in adj[int(dn)]:
            continue
        d = float(np.hypot(*(xy[w] - xy[dn])))
        if d < bd:
            bd = d; best = w
    if best is not None:
        snap.append((int(dn), best, bd))
pk = set((min(a, b), max(a, b)) for a, b, _ in snap)
print(f"막다른 노드 {len(dead):,}개 중 1m 안에 다른 (비인접) 노드 있는 것 {len(snap):,}, 고유 쌍 {len(pk):,}")

# 합집합 후 연결요소
parent = list(range(len(uk)))
def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x
for a, b, _ in snap:
    parent[find(a)] = find(b)
root = np.array([find(i) for i in range(len(uk))])
uu, vv = root[u], root[v]
keep = uu != vv
all_nodes = np.unique(np.r_[uu, vv])
remap = -np.ones(len(uk), int); remap[all_nodes] = np.arange(len(all_nodes))
A, B = remap[uu[keep]], remap[vv[keep]]
N = len(all_nodes)
n_c, lab = connected_components(coo_matrix((np.ones(len(A)), (A, B)), shape=(N, N)), directed=False)
cc = np.bincount(lab)
Lkeep = E[keep, 2]
Lcc = np.bincount(lab[A], weights=Lkeep, minlength=n_c)
print(f"분기점 그래프: 노드 {N:,} 간선 {len(A):,} 연결요소 {n_c:,}  최대 요소 노드비율 {cc.max()/N:.2%}, 길이비율 {Lcc.max()/Lcc.sum():.2%}  (총 {Lcc.sum()/1000:,.0f} km)")
srt = np.sort(Lcc)[::-1]
print("  상위 요소 길이(km)", (srt[:6] / 1000).round(1), " 1km 미만 요소", int((Lcc < 1000).sum()), " 그 길이 합 km", round(Lcc[Lcc < 1000].sum() / 1000, 1))
gdeg = np.bincount(A, minlength=N) + np.bincount(B, minlength=N)
print("  차수 분포", dict(sorted(collections.Counter(gdeg.tolist()).items())[:10]))
print("  차수 2 비율(가짜 노드)", f"{np.mean(gdeg == 2):.1%}")

# 4) 15m 재표집 계산: 차수2 체인 병합
adjm = collections.defaultdict(list)
for ei, (a, b) in enumerate(zip(A, B)):
    adjm[int(a)].append((int(b), ei)); adjm[int(b)].append((int(a), ei))
used = np.zeros(len(A), bool)
chains = []
for s in range(N):
    if gdeg[s] == 2:
        continue
    for t, ei in adjm[s]:
        if used[ei]:
            continue
        used[ei] = True
        L = Lkeep[ei]
        cur, prev, seq = t, s, [ei]
        while gdeg[cur] == 2:
            nb = adjm[cur]
            nx = None
            for w, ej in nb:
                if not used[ej]:
                    nx = (w, ej); break
            if nx is None:
                break
            w, ej = nx
            used[ej] = True; L += Lkeep[ej]; seq.append(ej); prev, cur = cur, w
        chains.append((s, cur, L, seq))
cyc = int((~used).sum())
L_ch = np.array([c[2] for c in chains])
print(f"체인 {len(chains):,} (순환 잔여 간선 {cyc})  체인 길이 중앙값 {np.median(L_ch):.1f}m  평균 {L_ch.mean():.1f}m  15m 미만 {np.mean(L_ch<15):.1%}")
nJ = int((gdeg != 2).sum())
for name, f in [("round", lambda l: np.maximum(1, np.round(l / 15))), ("floor", lambda l: np.maximum(1, np.floor(l / 15))), ("ceil", lambda l: np.ceil(l / 15))]:
    ne = int(f(L_ch).sum())
    print(f"15m 재표집({name}): 간선 {ne:,}, 노드(분기 {nJ:,} + 내부 {ne - len(L_ch):,}) = {nJ + ne - len(L_ch):,}")

# 5) 시험구역 안
xyN = xy[all_nodes]
pickle.dump(dict(xy=xyN, A=A, B=B, L=Lkeep, deg=gdeg, lab=lab), open(os.path.join(TMP, "graph.pkl"), "wb"))
in_box = lambda P: (P[:, 0] >= bx0) & (P[:, 0] <= bx1) & (P[:, 1] >= by0) & (P[:, 1] <= by1)
mid = (xyN[A] + xyN[B]) / 2
ib = in_box(mid)
print(f"시험구역 도로 길이 {Lkeep[ib].sum()/1000:,.1f} km, 노드 {int(in_box(xyN).sum()):,}, 차수3+ 노드 {int(in_box(xyN[gdeg >= 3]).sum()):,}")
# 시험구역 속성(선 단위, 길이 가중)
rec_of = np.array([lines[e[3]][0] for e in edges])[keep]
pv = np.array(attr["PVQT"])[rec_of]; rd = np.array(attr["RDDV"])[rec_of]; ln = np.array(attr["RDLN"])[rec_of].astype(float); wd = np.array([float(x) for x in attr["RVWD"]])[rec_of]
for label, mask in [("전체", np.ones(len(A), bool)), ("시험구역", ib)]:
    t = Lkeep[mask].sum()
    print(label, "비포장 길이비", round(Lkeep[mask & (pv == "RDQ005")].sum() / t, 3), "미분류", round(Lkeep[mask & (rd == "RDD000")].sum() / t, 3), "소로", round(Lkeep[mask & (rd == "RDD009")].sum() / t, 3), "면리간", round(Lkeep[mask & (rd == "RDD008")].sum() / t, 3), "지방도", round(Lkeep[mask & (rd == "RDD003")].sum() / t, 3))
print("RDDV x RDLN/RVWD (길이가중)")
all_w = np.array([float(x) for x in attr["RVWD"]])
all_l = np.array(attr["RDLN"]).astype(float)
all_r = np.array(attr["RDDV"])
llen = np.load(os.path.join(TMP, "road_len.npy"))
for r in ["RDD000", "RDD003", "RDD008", "RDD009"]:
    m = all_r == r
    print(r, "선", int(m.sum()), "km", round(llen[m].sum() / 1000), "RDLN 값", collections.Counter(all_l[m].tolist()).most_common(5), "RVWD 분위", np.percentile(all_w[m], [5, 25, 50, 75, 95]).round(1), "RVWD 상위", collections.Counter(np.round(all_w[m], 1).tolist()).most_common(5))

# 6) 겹친 길 지표 재계산 (audit.py와 같은 정의) - 15m 내외 간선으로 분할
def resample_edges(lines_, step=15.0):
    pts = []; seg = []
    return

Ax, Ay = xyN[A].T; Bx, By = xyN[B].T
def densify():
    # 분기점 간선을 실제 형상으로 15m 분할
    F, T, X = [], [], []
    node_count = 0
    out = []
    for e, ok in zip(edges, keep):
        if not ok:
            continue
        li = e[3]; a0, b0 = e[4], e[5]
        p = lines[li][1][a0:b0 + 1]
        out.append(p)
    return out
polys = densify()

def split(p, step):
    seg = np.hypot(*np.diff(p, axis=0).T); cum = np.r_[0, np.cumsum(seg)]
    if cum[-1] <= 0:
        return np.empty((0, 2)), np.empty((0, 2))
    n = max(1, int(round(cum[-1] / step)))
    t = np.linspace(0, cum[-1], n + 1)
    q = np.c_[np.interp(t, cum, p[:, 0]), np.interp(t, cum, p[:, 1])]
    return q[:-1], q[1:]

for step in (15.0,):
    a_, b_, F_, T_ = [], [], [], []
    pos = 0
    nid = 0
    for i, p in enumerate(polys):
        qa, qb = split(p, step)
        if len(qa) == 0:
            continue
        a_.append(qa); b_.append(qb)
        F_.append(np.arange(nid, nid + len(qa)))
        T_.append(np.arange(nid + 1, nid + len(qa) + 1))
        nid += len(qa) + 1
    a_ = np.vstack(a_); b_ = np.vstack(b_); F_ = np.concatenate(F_); T_ = np.concatenate(T_)
    # 공유 노드는 좌표가 같으면 같은 노드로 친다(반올림 1cm)
    def nid_of(P):
        return np.unique(np.round(P / 0.01).astype(np.int64), axis=0, return_inverse=True)[1].ravel()
    fi = nid_of(a_); ti = nid_of(b_)
    # a_,b_ 합쳐 노드 공유 판정
    both = np.r_[a_, b_]
    ids = np.unique(np.round(both / 0.01).astype(np.int64), axis=0, return_inverse=True)[1].ravel()
    fi, ti = ids[:len(a_)], ids[len(a_):]
    mid2 = (a_ + b_) / 2
    L2 = np.hypot(*(b_ - a_).T)
    ib2 = in_box(mid2) & (L2 >= 3)
    idx = np.where(ib2)[0]
    mx, my = mid2[idx].T
    dx, dy = (b_ - a_)[idx].T
    LL = np.hypot(dx, dy) + 1e-9
    ang = np.degrees(np.arctan2(dy, dx)) % 180
    ux, uy = dx / LL, dy / LL
    Fk, Tk = fi[idx], ti[idx]
    tr = cKDTree(np.c_[mx, my])
    for radius, latmax in [(14, 12), (32, 30)]:
        pr = tr.query_pairs(radius, output_type="ndarray")
        i, j = pr[:, 0], pr[:, 1]
        diff = np.abs(ang[i] - ang[j]); diff = np.minimum(diff, 180 - diff)
        vx, vy = mx[j] - mx[i], my[j] - my[i]
        lat = np.abs(vx * uy[i] - vy * ux[i]); al = np.abs(vx * ux[i] + vy * uy[i])
        share = (Fk[i] == Fk[j]) | (Fk[i] == Tk[j]) | (Tk[i] == Fk[j]) | (Tk[i] == Tk[j])
        near = (diff < 12) & (lat >= 1.0) & (lat <= latmax) & (al <= (LL[i] + LL[j]) / 2) & (~share)
        fl = np.zeros(len(idx), bool); fl[i[near]] = True; fl[j[near]] = True
        print(f"겹친 길(옆 {latmax}m까지, audit 방식): {LL[fl].sum()/1000:,.1f} km / {LL.sum()/1000:,.1f} km = {LL[fl].sum()/LL.sum():.2%}")

# 7) 분리대 도로의 평행 쌍
divy = np.array(attr["DVYN"]) == "CSU001"
print("분리대 유 도로 km", round(llen[divy].sum() / 1000, 1), "/ 시험구역 안 선 필요시 별도")
print("끝", time.time() - T0)

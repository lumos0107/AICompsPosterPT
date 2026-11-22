"""신호 노드를 확정 규칙으로 만들고, 신호 위치의 근거로 신호기현황 변환 위치 대조를 잰다.

신호 노드 규칙 (2026-11-10 사용자 결정, 20~30m 묶음 영상 확인 뒤에 정함):
  1:1,000 점 20m 안의 차수 3+ 노드 전부 + 20m에 하나도 안 붙은 묶음은 30m 안에서 묶음 점에 가장 가까운 노드 하나.
신호 위치 근거: 도엽 안 신호기현황 변환 위치(성공)에서 가장 가까운 1:1,000 장비까지 거리. 비교는 실험 그래프 위에서
  길이에 비례해 고르게 뽑은 무작위 도로 점(간선을 약 5m 구간으로 나눈 중앙 점, 시드 20261110).
입력: 그래프 npz(main, deg_full), 칸 목록 파일. 실행: py -I signal_nodes.py <그래프.npz> <칸목록.txt> <접미사>
결과: 신호노드_<접미사>.csv, 신호근거_<접미사>.out
"""
import collections
import csv
import os
import sys

import numpy as np
from pyproj import Transformer
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
G = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\새그래프_1110"
sys.path.insert(0, r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\데이터진단_1109\수집계획용\에이전트검토")
from lib_shp import read_shp

sys.stdout.reconfigure(encoding="utf-8")
gpath, cpath, tag = sys.argv[1], sys.argv[2], sys.argv[3]
out = open(os.path.join(HERE, f"신호근거_{tag}.out"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out.write(s + "\n")


ROAD = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵\연속수치지도_제주_20261109\풀기\N3L_A0020000\N3L_A0020000"
STEP = 0.005
to_wgs = Transformer.from_crs(5179, 4326, always_xy=True)
cells = set()
for line in open(cpath, encoding="utf-8"):
    t = line.strip()
    if t and not t.startswith("#"):
        i, j = t.split(",")
        cells.add((int(i), int(j)))


def inside(P):
    P = np.atleast_2d(P)
    lo, la = to_wgs.transform(P[:, 0], P[:, 1])
    ii, jj = np.floor(np.asarray(lo) / STEP).astype(int), np.floor(np.asarray(la) / STEP).astype(int)
    return np.array([(a, b) in cells for a, b in zip(ii.tolist(), jj.tolist())])


g = np.load(gpath)
xy, A, B, main, deg, gl, ga, gb = g["xy"], g["A"], g["B"], g["main"], g["deg_full"], g["line"], g["a"], g["b"]
nodes = np.unique(np.r_[A[main], B[main]])
jn = nodes[deg[nodes] >= 3]
tj = cKDTree(xy[jn])
log(f"칸 {len(cells)}개, 실험 그래프 주 요소 노드 {len(nodes):,}, 차수 3+ {len(jn):,}")

# 1:1,000 점 (칸 안)
sig = list(csv.DictReader(open(os.path.join(G, "신호1000.csv"), encoding="utf-8-sig")))
extra = sys.argv[4] if len(sys.argv) > 4 else os.path.join(HERE, f"신호1000_{tag}.csv")  # 확장 도엽의 추가 점(있으면 함께 쓴다)
if os.path.exists(extra):
    sig += list(csv.DictReader(open(extra, encoding="utf-8-sig")))
Q = np.array([(float(r["x5179"]), float(r["y5179"])) for r in sig])
keep = inside(Q)
Q = Q[keep]
log(f"1:1,000 신호등·제어기 칸 안 {len(Q)}개")
pr = cKDTree(Q).query_pairs(30.0, output_type="ndarray")
nC, cl = connected_components(coo_matrix((np.ones(len(pr)), (pr[:, 0], pr[:, 1])), shape=(len(Q), len(Q))), directed=False)

# 신호 노드 (확정 규칙)
near20 = tj.query_ball_point(Q, 20.0)
marked = set(i for lst in near20 for i in lst)
att = np.zeros(nC, bool)
for k, lst in zip(cl.tolist(), near20):
    if lst:
        att[k] = True
d1, i1 = tj.query(Q)
added = []
for k in np.where(~att)[0].tolist():
    sel = np.where(cl == k)[0]
    j = sel[np.argmin(d1[sel])]
    if d1[j] <= 30:
        added.append((k, int(i1[j]), float(d1[j]), i1[j] in marked))
        marked.add(int(i1[j]))
        att[k] = True
log(f"30m 묶음 {nC}곳, 20m 부착 {nC - len(added) - int((~att).sum())}곳, 30m 가장 가까운 노드로 추가 부착 {len(added)}곳, 끝내 안 붙음 {int((~att).sum())}곳")
log(f"묶음 부착 {int(att.sum())}/{nC} ({att.mean():.1%}), 신호 노드 {len(marked)}개, 부착 묶음당 {len(marked) / att.sum():.2f}")
Cxy = np.c_[np.bincount(cl, weights=Q[:, 0]) / np.bincount(cl), np.bincount(cl, weights=Q[:, 1]) / np.bincount(cl)]
log("추가 부착 묶음 (중심 위경도, 최소 거리, 이미 다른 점으로 표시된 노드인지):")
for k, n, d, already in added:
    lo, la = to_wgs.transform(*Cxy[k])
    log(f"  묶음 중심 {la:.6f},{lo:.6f} 점 {int((cl == k).sum())}개 거리 {d:.1f}m 노드 {int(jn[n])} 이미표시 {bool(already)}")
with open(os.path.join(HERE, f"신호노드_{tag}.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["노드", "x5179", "y5179", "차수"])
    for i in sorted(marked):
        n = int(jn[i])
        w.writerow([n, round(float(xy[n, 0]), 2), round(float(xy[n, 1]), 2), int(deg[n])])

# 무작위 도로 점 (고른 추출)
lines = [p for r, parts in read_shp(ROAD, clip=False) for p in parts]
road = []
for e in np.where(main)[0].tolist():
    p = lines[gl[e]][ga[e]:gb[e] + 1]
    c = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]
    if c[-1] <= 0:
        continue
    k = max(int(round(c[-1] / 5.0)), 1)
    t = (np.arange(k) + 0.5) * c[-1] / k
    road.append(np.c_[np.interp(t, c, p[:, 0]), np.interp(t, c, p[:, 1])])
road = np.vstack(road)
rng = np.random.default_rng(20261110)
rnd = road[rng.choice(len(road), 5000, replace=False)]

# 신호기현황 대조
reg = list(csv.DictReader(open(os.path.join(G, "신호위치.csv"), encoding="utf-8-sig")))
S = np.array([(float(r["x"]), float(r["y"])) if r["x"] else (np.nan, np.nan) for r in reg])
st = np.array([r["상태"] for r in reg])
has = np.isfinite(S[:, 0])
inS = np.zeros(len(S), bool)
inS[has] = inside(S[has])
tq = cKDTree(Q)
BINS = [(0, 10), (10, 20), (20, 30), (30, 50), (50, 100), (100, 1e12)]


def row(name, d):
    cells_ = []
    for a, b in BINS:
        k = int(((d > a) & (d <= b)).sum()) + (int((d == 0).sum()) if a == 0 else 0)
        cells_.append(f"{k / len(d):.1%}")
    log(f"{name} | n={len(d)} | " + " | ".join(cells_) + f" | 30m 안 {(d <= 30).mean():.1%} | 50m 안 {(d <= 50).mean():.1%} | 중앙값 {np.median(d):.1f}m")


log("\n[신호 위치 근거] 가장 가까운 1:1,000 신호등·제어기까지 | 10m 이하 | 10~20 | 20~30 | 30~50 | 50~100 | 100 초과")
row("신호기현황 변환 위치(성공, 칸 안)", tq.query(S[inS & (st == "성공")])[0])
if (inS & (st == "모호")).any():
    row("신호기현황 변환 위치(모호, 칸 안)", tq.query(S[inS & (st == "모호")])[0])
row("고른 무작위 도로 점", tq.query(rnd)[0])
log("\n[참고] 묶음 부착과 같은 규칙을 무작위 도로 점 하나에 적용: 20m 안 차수 3+ 노드 " + f"{(tj.query(rnd)[0] <= 20).mean():.1%}, 30m 안 {(tj.query(rnd)[0] <= 30).mean():.1%}")
log("끝")

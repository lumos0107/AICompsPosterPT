"""제주 도심 1:1,000 도엽 95장 범위로 실험 그래프를 자르고 신호 부착·출발점·신호기현황 점검 값을 잰다. 원본은 읽기만 한다.

사용자 결정 2026-11-10: 1:1,000을 신호 위치 자료로, 실험은 제주 도심 95장 안에서만, 반경 20m.
도엽 범위: 각 도엽은 경위도 0.005도 칸(도엽 외곽 상자로 확인). 간선은 모든 꼭짓점이 도엽 칸 안일 때만 남긴다.
차수: 자르기 전 최종 그래프(keep)의 차수. 범위 경계에서 바깥 간선이 잘려도 실제 교차로는 교차로로 본다.
신호 묶음: 1:1,000 신호등·신호등제어기를 30m로 이은 묶음(신호검증과 같음).
묶음 부착(반경 r): 묶음의 점 하나라도 r 안에 자른 그래프 주 요소의 차수 3+ 노드가 있으면 부착.
신호 노드(반경 r): 1:1,000 점 r 안의 차수 3+ 노드.

실행: py -I cut_jeju.py
결과: 도심실험.out, 그래프_도심.npz, 신호노드_20m.csv, 묶음_20과30사이.json, 신호기현황_점검.csv
"""
import collections
import csv
import json
import os
import sys

import numpy as np
from pyproj import Transformer
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
G = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\새그래프_1110"
sys.path.insert(0, r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\데이터진단_1109\수집계획용\에이전트검토")
from lib_shp import read_shp, dbf_columns

sys.stdout.reconfigure(encoding="utf-8")
out = open(os.path.join(HERE, "도심실험.out"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out.write(s + "\n")
    out.flush()


ROOT = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵\수치지형도_1000_표본\제주도심_95장\풀기"
ROAD = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵\연속수치지도_제주_20261109\풀기\N3L_A0020000\N3L_A0020000"
to_wgs = Transformer.from_crs(5179, 4326, always_xy=True)
from_wgs = Transformer.from_crs(4326, 5179, always_xy=True)
S5186 = Transformer.from_crs(5186, 4326, always_xy=True)
STEP = 0.005

# ---- 도엽 칸
import glob
import struct

cells = set()
for sd in sorted(glob.glob(os.path.join(ROOT, "*"))):
    if not os.path.isdir(sd):
        continue
    b = [np.inf, np.inf, -np.inf, -np.inf]
    for shp in glob.glob(os.path.join(sd, "*.shp")):
        d = open(shp, "rb").read(100)
        x0, y0, x1, y1 = struct.unpack("<4d", d[36:68])
        if x1 > x0 or y1 > y0:
            b = [min(b[0], x0), min(b[1], y0), max(b[2], x1), max(b[3], y1)]
    lo, la = S5186.transform((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
    cells.add((int(np.floor(lo / STEP)), int(np.floor(la / STEP))))
ci = np.array(sorted(cells))
log(f"도엽 {len(cells)}칸, 경도 칸 {ci[:, 0].min()}~{ci[:, 0].max()} ({np.ptp(ci[:, 0]) + 1}), 위도 칸 {ci[:, 1].min()}~{ci[:, 1].max()} ({np.ptp(ci[:, 1]) + 1})")
log(f"바깥 사각형 칸 {(np.ptp(ci[:, 0]) + 1) * (np.ptp(ci[:, 1]) + 1)}개 중 빈 칸 {(np.ptp(ci[:, 0]) + 1) * (np.ptp(ci[:, 1]) + 1) - len(cells)}개")
grid = ["".join("#" if (i, j) in cells else "." for i in range(ci[:, 0].min(), ci[:, 0].max() + 1)) for j in range(ci[:, 1].max(), ci[:, 1].min() - 1, -1)]
log("도엽 배치 (위가 북쪽, #=도엽):")
for g_ in grid:
    log("  " + g_)
log(f"경위도 범위: 경도 {ci[:, 0].min() * STEP:.3f}~{(ci[:, 0].max() + 1) * STEP:.3f}, 위도 {ci[:, 1].min() * STEP:.3f}~{(ci[:, 1].max() + 1) * STEP:.3f}")


def inside(P):
    P = np.atleast_2d(P)
    lo, la = to_wgs.transform(P[:, 0], P[:, 1])
    ii, jj = np.floor(np.asarray(lo) / STEP).astype(int), np.floor(np.asarray(la) / STEP).astype(int)
    return np.array([(i, j) in cells for i, j in zip(ii.tolist(), jj.tolist())])


def dist_to_outside(P):
    """점에서 도엽 밖(칸 경계)까지 최단 거리(m)를 경위도 칸 경계 샘플로 근사."""
    edges = []
    for (i, j) in cells:
        for (di, dj, side) in ((-1, 0, "W"), (1, 0, "E"), (0, -1, "S"), (0, 1, "N")):
            if (i + di, j + dj) in cells:
                continue
            t = np.linspace(0, 1, 50)
            if side in ("W", "E"):
                lo = np.full(50, (i + (side == "E")) * STEP)
                la = (j + t) * STEP
            else:
                la = np.full(50, (j + (side == "N")) * STEP)
                lo = (i + t) * STEP
            x, y = from_wgs.transform(lo, la)
            edges.append(np.c_[x, y])
    return cKDTree(np.vstack(edges)).query(np.atleast_2d(P))[0]


# ---- 그래프
g = np.load(os.path.join(G, "그래프_최종.npz"))
xy, A, B, L, keep, line, ga, gb, rec = g["xy"], g["A"], g["B"], g["L"], g["keep"], g["line"], g["a"], g["b"], g["rec"]
N = len(xy)
lines = [p for r, parts in read_shp(ROAD, clip=False) for p in parts]
wid = np.array([float(x or 0) for x in dbf_columns(ROAD, ["RVWD"])["RVWD"]])
deg_full = np.bincount(A[keep], minlength=N) + np.bincount(B[keep], minlength=N)

cand = np.where(keep)[0]
mid = (xy[A[cand]] + xy[B[cand]]) / 2
pre = inside(mid) | inside(xy[A[cand]]) | inside(xy[B[cand]])
inn = np.zeros(len(A), bool)
part = np.zeros(len(A), bool)
for e in cand[pre].tolist():
    p = lines[line[e]][ga[e]:gb[e] + 1]
    m = inside(p)
    if m.all():
        inn[e] = True
    elif m.any():
        part[e] = True
log(f"\n최종 그래프(둘 다 제외, 입체 10곳 끊음, 계단 제외) 중 도엽 안 간선 {int(inn.sum()):,}개 {L[inn].sum() / 1000:.1f}km, 경계에 걸쳐 버린 간선 {int(part.sum()):,}개 {L[part].sum() / 1000:.1f}km")


def comps(m):
    n, lab = connected_components(coo_matrix((np.ones(int(m.sum())), (A[m], B[m])), shape=(N, N)), directed=False)
    Lc = np.bincount(lab[A[m]], weights=L[m], minlength=n)
    return lab, Lc


lab, Lc = comps(inn)
mc = int(Lc.argmax())
cmain = inn & (lab[A] == mc)
nz = Lc[Lc > 0]
log(f"자른 그래프: 도로 {L[inn].sum() / 1000:.1f}km, 요소 {len(nz)}, 주 요소 {Lc.max() / 1000:.1f}km, 주 요소 비율 {Lc.max() / L[inn].sum():.2%}")
small = np.sort(nz)[::-1][1:]
log(f"  주 요소 밖 조각 {len(small)}개 {small.sum() / 1000:.2f}km, 가장 긴 것 {small[:5].round(0).tolist()} m")
# 원인: 전체 그래프에서는 주 요소였는가
lab0, Lc0 = comps(keep)
mc0 = int(Lc0.argmax())
off = inn & ~cmain
was_main = off & (lab0[A] == mc0)
log(f"  주 요소 밖 간선 중 자르기 전에는 주 요소였던 길이 {L[was_main].sum() / 1000:.2f}km (경계에서 잘려 떨어진 것), 원래도 떨어져 있던 길이 {L[off & ~was_main].sum() / 1000:.2f}km")
nodes_main = np.unique(np.r_[A[cmain], B[cmain]])
log(f"  주 요소 간선 {int(cmain.sum()):,}, 노드 {len(nodes_main):,}")
deg_cut = np.bincount(A[cmain], minlength=N) + np.bincount(B[cmain], minlength=N)
jn = nodes_main[deg_full[nodes_main] >= 3]
log(f"  차수 3+ 노드(자르기 전 차수 기준) {len(jn):,}, 그중 자른 뒤 차수가 줄어든 노드 {int((deg_cut[jn] < deg_full[jn]).sum())}")
np.savez_compressed(os.path.join(HERE, "그래프_도심.npz"), xy=xy, A=A, B=B, L=L, rec=rec, line=line, a=ga, b=gb, main=cmain, deg_full=deg_full)

# ---- 1:1,000 묶음
sig = list(csv.DictReader(open(os.path.join(G, "신호1000.csv"), encoding="utf-8-sig")))
sig = [r for r in sig if r["지역"] == "제주 도심"]
Q = np.array([(float(r["x5179"]), float(r["y5179"])) for r in sig])
typ = np.array([r["종류"] for r in sig])
use = np.array([r["용도"] for r in sig])
log(f"\n1:1,000 제주 도심 점 {len(Q)} ({collections.Counter(typ.tolist()).most_common()}), 도엽 칸 밖 {int((~inside(Q)).sum())}")
log(f"  신호등 용도: {collections.Counter(use[typ == '신호등'].tolist()).most_common()}")
nC, cl = connected_components(coo_matrix((np.ones(len(pr := cKDTree(Q).query_pairs(30.0, output_type='ndarray'))), (pr[:, 0], pr[:, 1])), shape=(len(Q), len(Q))), directed=False)
Cxy = np.c_[np.bincount(cl, weights=Q[:, 0]) / np.bincount(cl), np.bincount(cl, weights=Q[:, 1]) / np.bincount(cl)]
log(f"30m 묶음 {nC}곳")
tj = cKDTree(xy[jn])
dq = tj.query(Q)[0]
dmin = np.full(nC, np.inf)
np.minimum.at(dmin, cl, dq)
dcen = tj.query(Cxy)[0]

# 무작위 도로 점 (자른 그래프 주 요소, 5m 간격)
road = []
for e in np.where(cmain)[0].tolist():
    p = lines[line[e]][ga[e]:gb[e] + 1]
    c = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]
    if c[-1] <= 0:
        continue
    # 5m 간격 점에 끝점을 더하면 짧은 간선(교차로 근처)이 과다 추출되므로, 구간 중앙 점만 쓴다(점 하나가 길이 약 5m를 대표).
    k = max(int(round(c[-1] / 5.0)), 1)
    t = (np.arange(k) + 0.5) * c[-1] / k
    road.append(np.c_[np.interp(t, c, p[:, 0]), np.interp(t, c, p[:, 1])])
road = np.vstack(road)
rng = np.random.default_rng(20261110)
rnd = road[rng.choice(len(road), 3000, replace=False)]
drnd = tj.query(rnd)[0]
# 묶음과 같은 조건의 무작위 비교: 실제 묶음 모양(점 배치)을 무작위 도로 점으로 평행 이동
rmin = []
for k in range(nC):
    pts = Q[cl == k] - Cxy[k]
    base = road[rng.choice(len(road), 20, replace=False)]
    for b0 in base:
        rmin.append(tj.query(pts + b0)[0].min())
rmin = np.array(rmin)
log("\n[8장 기준] 신호 묶음 부착 (합격선 80%, 자른 그래프)")
log("반경 | 묶음 부착(점 하나라도 r 안) | 묶음 중심 r 안 | 무작위 도로 점 r 안 | 무작위 이동 묶음(같은 모양) r 안")
for r in (10, 20, 30):
    log(f"{r}m | {int((dmin <= r).sum())}/{nC} ({(dmin <= r).mean():.1%}) | {(dcen <= r).mean():.1%} | {(drnd <= r).mean():.1%} | {(rmin <= r).mean():.1%}")
# 신호 노드
for r in (20, 30):
    near = tj.query_ball_point(Q, r)
    marked = sorted(set(i for lst in near for i in lst))
    log(f"반경 {r}m 신호 노드 {len(marked)}개 (차수 3+ 노드 {len(jn):,}개 중 {len(marked) / len(jn):.1%}), 부착 묶음당 {len(marked) / max(int((dmin <= r).sum()), 1):.2f}")
near20 = tj.query_ball_point(Q, 20.0)
m20 = sorted(set(i for lst in near20 for i in lst))
with open(os.path.join(HERE, "신호노드_20m.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["노드", "x5179", "y5179", "차수"])
    for i in m20:
        n = int(jn[i])
        w.writerow([n, round(float(xy[n, 0]), 2), round(float(xy[n, 1]), 2), int(deg_full[n])])

# ---- 20m 안 붙고 30m에서만 붙는 묶음
mid_e = (xy[A] + xy[B]) / 2
te = cKDTree(mid_e[keep])
ke = np.where(keep)[0]
gap = np.where((dmin > 20) & (dmin <= 30))[0]
items = []
for k in gap.tolist():
    m = cl == k
    i_q = np.where(m)[0][np.argmin(dq[m])]
    dd, ii = tj.query(Q[i_q])
    n = int(jn[ii])
    es = np.where(keep & ((A == n) | (B == n)))[0]
    ws = sorted({float(wid[rec[e]]) for e in es}, reverse=True)
    lo, la = to_wgs.transform(*Cxy[k])
    items.append(dict(id=f"S{k:03d}", x=round(float(Cxy[k, 0])), y=round(float(Cxy[k, 1])), z=12, lon=round(lo, 6), lat=round(la, 6),
                      n_light=int((typ[m] == "신호등").sum()), n_ctrl=int((typ[m] == "제어기").sum()), uses=collections.Counter(use[m].tolist()).most_common(),
                      dmin=round(float(dmin[k]), 1), node=n, node_xy=[round(float(xy[n, 0]), 1), round(float(xy[n, 1]), 1)], deg=int(deg_full[n]), widths=ws))
log(f"\n20m 밖 30m 안 묶음 {len(gap)}곳 (영상 확인 대상)")
for it in items:
    log(f"  {it['id']} 중심 {it['lat']},{it['lon']} 신호등 {it['n_light']} 제어기 {it['n_ctrl']} 최소거리 {it['dmin']}m 노드차수 {it['deg']} 붙은도로폭 {it['widths']} 용도 {it['uses']}")
json.dump(items, open(os.path.join(HERE, "묶음_20과30사이.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
far = np.where(dmin > 30)[0]
log(f"30m 밖 묶음 {len(far)}곳: 신호등 수 합 {int(sum((typ[cl == k] == '신호등').sum() for k in far))}, 제어기 수 합 {int(sum((typ[cl == k] == '제어기').sum() for k in far))}")

# ---- 신호기현황 변환 위치 점검 (합격선 없음)
reg = list(csv.DictReader(open(os.path.join(G, "신호위치.csv"), encoding="utf-8-sig")))
S = np.array([(float(r["x"]), float(r["y"])) if r["x"] else (np.nan, np.nan) for r in reg])
st = np.array([r["상태"] for r in reg])
has = np.isfinite(S[:, 0])
inS = np.zeros(len(S), bool)
inS[has] = inside(S[has])
tq = cKDTree(Q)
log("\n[점검] 신호기현황 변환 위치(단일로 제외) 중 도엽 칸 안 -> 가장 가까운 1:1,000 신호등·제어기 (합격선 없음)")
BINS = [(0, 10), (10, 20), (20, 30), (30, 50), (50, 100), (100, 1e12)]
rows = []
for nm, m in (("성공", inS & (st == "성공")), ("모호", inS & (st == "모호"))):
    d = tq.query(S[m])[0]
    cells_ = []
    for a, b in BINS:
        k = int(((d > a) & (d <= b)).sum()) + (int((d == 0).sum()) if a == 0 else 0)
        cells_.append(f"{k} ({k / max(len(d), 1):.1%})")
    log(f"{nm} n={len(d)} | " + " | ".join(cells_) + f" | 중앙값 {np.median(d):.1f}m" if len(d) else f"{nm} 없음")
    for i, dd in zip(np.where(m)[0].tolist(), d.tolist()):
        rows.append(dict(연번=reg[i]["연번"], 주소=reg[i]["주소"], 상태=nm, 기하구조=reg[i]["기하구조"], x=reg[i]["x"], y=reg[i]["y"], 가장가까운_1000m=round(dd, 1)))
rows.sort(key=lambda r: -r["가장가까운_1000m"])
with open(os.path.join(HERE, "신호기현황_점검.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
log("50m 넘는 것: " + "; ".join(f"{r['연번']} {r['주소']} {r['기하구조']} {r['가장가까운_1000m']}m ({r['상태']})" for r in rows if r["가장가까운_1000m"] > 50))
log(f"참고: 신호기현황(단일로 제외) 830건 중 주소 변환 실패·좌표 없음 {int((~has).sum())}건은 위치를 몰라 도엽 안 여부를 판단하지 못함")
dS = cKDTree(S[has & np.isin(st, ['성공', '모호'])]).query(Cxy)[0]
log(f"역방향(참고): 1:1,000 묶음 {nC}곳 중 변환 위치 50m 안 {(dS <= 50).mean():.1%}, 100m 안 {(dS <= 100).mean():.1%} (단일로·보행 신호는 830건에 없으므로 낮게 나옴)")

# ---- 출발점
log("\n[출발점] 초안 4곳 (탐색 범위 직선 0.7T, 안내점 0.38T)")
SCN = [("탑동", 33.515, 126.522, 3000), ("도심", 33.499, 126.531, 5000), ("연동", 33.489, 126.490, 3000), ("이도", 33.499, 126.541, 4000)]
tn = cKDTree(xy[nodes_main])
Wm = coo_matrix((L[cmain], (A[cmain], B[cmain])), shape=(N, N))
Wm = Wm + Wm.T
for nm, la, lo, T in SCN:
    x, y = from_wgs.transform(lo, la)
    p = np.array([[x, y]])
    ins = bool(inside(p)[0])
    dn, inode = tn.query(p[0])
    s = int(nodes_main[inode])
    db = float(dist_to_outside(p)[0])
    # 0.38T 거리 16방향 안내점이 도엽 안 주 요소 노드로 있는지 (각 방향 200m 안 노드)
    ok = 0
    for ang in np.arange(16) * 22.5:
        t = p[0] + 0.38 * T * np.array([np.sin(np.radians(ang)), np.cos(np.radians(ang))])
        if tn.query(t)[0] <= 200 and bool(inside(t)[0]):
            ok += 1
    # 0.7T 원 안 도로 중 도엽 안 비율 (자르기 전 최종 그래프 기준)
    mk = keep & (np.hypot(*(mid_e - p[0]).T) <= 0.7 * T)
    frac = L[mk & cmain].sum() / max(L[mk].sum(), 1)
    dd = dijkstra(Wm, indices=s, limit=0.5 * T * 1.2)
    reach = np.isfinite(dd)
    log(f"{nm} ({la}, {lo}, {T / 1000:.0f}km): 도엽 안 {ins}, 가장 가까운 주 요소 노드 {dn:.1f}m, 도엽 경계까지 {db:.0f}m, 0.38T 16방향 중 안내점 가능 {ok}, 0.7T 원 안 도로 중 실험 그래프 비율 {frac:.1%}, 도로 거리 0.6T 안 노드 {int(reach.sum()):,}")
log("끝")

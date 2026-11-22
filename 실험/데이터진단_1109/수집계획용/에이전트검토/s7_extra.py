"""남은 측정: 신호 상한, 입력 자료 신뢰성, 겹침 지표 민감도, 입체 후보, 도로 사이 이동."""
import collections
import csv
import glob
import io
import os
import pickle
import sys
import time
import numpy as np
from pyproj import Transformer
from scipy.sparse import coo_matrix, csr_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.spatial import cKDTree

sys.path.insert(0, r"C:\Users\seungjun\AppData\Local\Temp\plan_review_Br6p2s")
from lib_shp import *

sys.stdout.reconfigure(encoding="utf-8")
TMP = r"C:\Users\seungjun\AppData\Local\Temp\plan_review_Br6p2s"
ROOT = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\공공데이터포털"
T0 = time.time()
tf = Transformer.from_crs(4326, 5179, always_xy=True)
bx0, by0 = tf.transform(126.46, 33.46); bx1, by1 = tf.transform(126.58, 33.54)


def load(label):
    p = glob.glob(os.path.join(ROOT, label, "*.csv"))[0]
    raw = open(p, "rb").read()
    for enc in ("utf-8-sig", "cp949"):
        try:
            return list(csv.DictReader(io.StringIO(raw.decode(enc))))
        except UnicodeDecodeError:
            continue


def P(rows):
    x = []; i_ = []
    for i, r in enumerate(rows):
        try:
            la, lo = float(r["위도"]), float(r["경도"])
        except Exception:
            continue
        a, b = tf.transform(lo, la); x.append((a, b)); i_.append(i)
    return np.array(x), i_


def clusters(a, d):
    pr = cKDTree(a).query_pairs(d, output_type="ndarray")
    g = coo_matrix((np.ones(len(pr)), (pr[:, 0], pr[:, 1])), shape=(len(a), len(a)))
    return connected_components(g, directed=False)

print("=== a. 신호기현황 시×기하구조")
st = load("제주_신호기현황")
print(collections.Counter((r["주소"].split(" ")[1], r["기하구조"]) for r in st).most_common())
std = load("횡단보도표준_제주특별자치도_서귀포시_횡단보도")
A_std, idx = P(std)
yn = np.array([std[i]["보행자신호등유무"] == "Y" for i in idx])
Ped = A_std[yn]
for R in (50,):
    n, lab = clusters(Ped, R)
    sz = np.sort(np.bincount(lab))[::-1]
    for k, name in [(385, "서귀포 전체 385"), (385 - sum(1 for r in st if "서귀포" in r["주소"] and r["기하구조"] == "단일로"), "단일로 제외")]:
        print(f"  50m 묶음 {n}개 (크기순 상위 {k}개가 지점을 모두 덮는다고 가정한 상한: 844 중 {sz[:k].sum()}개 = {sz[:k].sum()/844:.1%}) [{name}]")

print("\n=== b. 어린이 횡단보도의 보행신호 유무와 표준 대조 (서귀포)")
cx = load("제주_어린이보호구역_횡단보도")
Ac, ix = P(cx)
sw = np.array(["서귀포" in cx[i]["시군구명"] for i in ix])
Ac_s = Ac[sw]
d, j = cKDTree(A_std).query(Ac_s)
print(f"어린이 서귀포 {len(Ac_s)}개 모두 있음. 표준 최근접 30m 안: {np.mean(d<=30):.1%}. 그중 표준이 Y {np.mean(yn[j[d<=30]]):.1%}")
print("어린이 제주시 있음/없음", collections.Counter(cx[i]["보행자신호등유무"] for i, s in zip(ix, sw) if not s))

print("\n=== c. KIND x BYYN / SWK002와 SWK001 거리")
sa = dbf_columns(FILES["sidewalk"], ["KIND", "BYYN", "WIDT"])
recs = read_shp(FILES["sidewalk"], clip=True)
ids = [r for r, _ in recs]
print(collections.Counter((sa["KIND"][i], sa["BYYN"][i]) for i in ids).most_common())
ps = {"SWK001": [], "SWK002": []}
for rec, parts in recs:
    for p in parts:
        ps[sa["KIND"][rec]].append(p)
def dens(ls, step):
    out = []
    for p in ls:
        s = np.hypot(*np.diff(p, axis=0).T); c = np.r_[0, np.cumsum(s)]
        t = np.r_[np.arange(0, c[-1], step), c[-1]] if c[-1] > 0 else np.array([0.0])
        out.append(np.c_[np.interp(t, c, p[:, 0]), np.interp(t, c, p[:, 1])])
    return np.vstack(out)
A1 = dens(ps["SWK001"], 5.0); A2 = dens(ps["SWK002"], 5.0)
print(f"km: 인도 {sum(np.hypot(*np.diff(p,axis=0).T).sum() for p in ps['SWK001'])/1000:,.0f}, 자전거 {sum(np.hypot(*np.diff(p,axis=0).T).sum() for p in ps['SWK002'])/1000:,.0f}")
d, _ = cKDTree(A1).query(A2, workers=-1)
print(f"자전거 표본 -> 인도(SWK001) 2m 안 {np.mean(d<=2):.1%}, 5m {np.mean(d<=5):.1%}, 12m {np.mean(d<=12):.1%}, 중앙값 {np.median(d):.1f}")

print("\n=== d. 도로명주소 도로구간 속성")
seg = dbf_columns(FILES["seg"], ["ROA_CLS_SE", "ROAD_BT", "WDR_RD_CD"])
print("ROA_CLS_SE", collections.Counter(seg["ROA_CLS_SE"]).most_common(8))
print("ROAD_BT", collections.Counter(seg["ROAD_BT"]).most_common(6))
v = np.array([float(x) if x else np.nan for x in seg["ROAD_BT"]])
print("ROAD_BT 양수", np.mean(v > 0), "분위", np.nanpercentile(v[v > 0], [10, 50, 90]))
print("WDR_RD_CD", collections.Counter(seg["WDR_RD_CD"]).most_common(6))

print("\n=== f. 겹침 지표 민감도 및 12~30m 구성")
g = pickle.load(open(os.path.join(TMP, "graph.pkl"), "rb"))
xyN = g["xy"]; A = g["A"]; B = g["B"]; L = g["L"]; deg = g["deg"]
print("연결요소 노드 수", g["lab"].max() + 1)
in_box = lambda p: (p[:, 0] >= bx0) & (p[:, 0] <= bx1) & (p[:, 1] >= by0) & (p[:, 1] <= by1)
recs_r = read_shp(FILES["road"], clip=False)
ra = dbf_columns(FILES["road"], ["RVWD", "RDLN", "DVYN", "PVQT"])
rw = np.array([float(x) for x in ra["RVWD"]]); rn = np.array([float(x) for x in ra["RDLN"]]); dv = np.array(ra["DVYN"])
lines = []
for rec, parts in recs_r:
    for p in parts:
        lines.append((rec, p))
print("라인", len(lines), time.time() - T0)


def split(p, step):
    s = np.hypot(*np.diff(p, axis=0).T); c = np.r_[0, np.cumsum(s)]
    if c[-1] <= 0:
        return None
    n = max(1, int(round(c[-1] / step)))
    t = np.linspace(0, c[-1], n + 1)
    q = np.c_[np.interp(t, c, p[:, 0]), np.interp(t, c, p[:, 1])]
    return q[:-1], q[1:]


def build(step):
    a_, b_, rec_ = [], [], []
    for rec, p in lines:
        r = split(p, step)
        if r is None:
            continue
        a_.append(r[0]); b_.append(r[1]); rec_.append(np.full(len(r[0]), rec))
    return np.vstack(a_), np.vstack(b_), np.concatenate(rec_)


for step in (10.0, 15.0, 20.0, 30.0):
    a_, b_, rec_ = build(step)
    both = np.r_[a_, b_]
    ids = np.unique(np.round(both / 0.01).astype(np.int64), axis=0, return_inverse=True)[1].ravel()
    fi, ti = ids[:len(a_)], ids[len(a_):]
    mid = (a_ + b_) / 2
    LL = np.hypot(*(b_ - a_).T)
    idx = np.where(in_box(mid) & (LL >= 3))[0]
    mx, my = mid[idx].T
    dx, dy = (b_ - a_)[idx].T
    Lx = np.hypot(dx, dy) + 1e-9
    ang = np.degrees(np.arctan2(dy, dx)) % 180
    ux, uy = dx / Lx, dy / Lx
    Fk, Tk = fi[idx], ti[idx]
    tr = cKDTree(np.c_[mx, my])
    res = {}
    for latmax in (12, 30):
        pr = tr.query_pairs(latmax + 2 if latmax == 12 else 32, output_type="ndarray")
        i, j = pr[:, 0], pr[:, 1]
        diff = np.abs(ang[i] - ang[j]); diff = np.minimum(diff, 180 - diff)
        vx, vy = mx[j] - mx[i], my[j] - my[i]
        lat = np.abs(vx * uy[i] - vy * ux[i]); al = np.abs(vx * ux[i] + vy * uy[i])
        share = (Fk[i] == Fk[j]) | (Fk[i] == Tk[j]) | (Tk[i] == Fk[j]) | (Tk[i] == Tk[j])
        near = (diff < 12) & (lat >= 1.0) & (lat <= latmax) & (al <= (Lx[i] + Lx[j]) / 2) & (~share)
        fl = np.zeros(len(idx), bool); fl[i[near]] = True; fl[j[near]] = True
        res[latmax] = fl
        if latmax == 30:
            R = rec_[idx]
            two = (dv[R] == "CSU001")
            wide = (rw[R] >= 15) | (rn[R] >= 4)
            print(f"  step {step:.0f}m  30m까지 {Lx[fl].sum()/1000:,.1f} km ({Lx[fl].sum()/Lx.sum():.2%}) 중 분리대 유 도로 {Lx[fl & two].sum()/Lx[fl].sum():.1%}, 폭>=15 또는 차로>=4 {Lx[fl & wide].sum()/Lx[fl].sum():.1%}")
    print(f"  step {step:.0f}m  12m 겹침 {Lx[res[12]].sum()/Lx.sum():.2%}  (총 {Lx.sum()/1000:,.0f} km)")

print("\n=== g. 공유 꼭짓점 없이 기하학적으로 교차하는 선 (입체 후보)")
a = np.vstack([p[:-1] for _, p in lines]); b = np.vstack([p[1:] for _, p in lines])
own = np.concatenate([np.full(len(p) - 1, i) for i, (_, p) in enumerate(lines)])
cs = 100.0
cell = collections.defaultdict(list)
for i in range(len(a)):
    cx0, cy0 = int(min(a[i, 0], b[i, 0]) // cs), int(min(a[i, 1], b[i, 1]) // cs)
    cx1, cy1 = int(max(a[i, 0], b[i, 0]) // cs), int(max(a[i, 1], b[i, 1]) // cs)
    for cx in range(cx0, cx1 + 1):
        for cy in range(cy0, cy1 + 1):
            cell[(cx, cy)].append(i)
print("격자", time.time() - T0, flush=True)
key = np.unique(np.round(np.r_[a, b] / 0.01).astype(np.int64), axis=0, return_inverse=True)[1].ravel()
ka, kb = key[:len(a)], key[len(a):]
seen = set(); hits = []
for c, lst in cell.items():
    if len(lst) < 2:
        continue
    lst = np.array(lst)
    A_ = a[lst]; D_ = b[lst] - a[lst]
    n = len(lst)
    I, J = np.triu_indices(n, 1)
    # 교차 판정 (벡터화)
    denom = D_[I, 0] * D_[J, 1] - D_[I, 1] * D_[J, 0]
    ok = np.abs(denom) > 1e-9
    I, J = I[ok], J[ok]; denom = denom[ok]
    wx = A_[J, 0] - A_[I, 0]; wy = A_[J, 1] - A_[I, 1]
    t = (wx * D_[J, 1] - wy * D_[J, 0]) / denom
    u = (wx * D_[I, 1] - wy * D_[I, 0]) / denom
    good = (t > 0.0) & (t < 1.0) & (u > 0.0) & (u < 1.0)
    for ii, jj, tt in zip(lst[I[good]], lst[J[good]], t[good]):
        if own[ii] == own[jj]:
            continue
        if ka[ii] in (ka[jj], kb[jj]) or kb[ii] in (ka[jj], kb[jj]):
            continue
        k = (min(ii, jj), max(ii, jj))
        if k in seen:
            continue
        seen.add(k)
        hits.append((a[ii] + tt * (b[ii] - a[ii])).tolist())
hits = np.array(hits) if hits else np.empty((0, 2))
print(f"공유 꼭짓점 없이 내부에서 교차하는 선분 쌍 {len(hits):,}  (t={time.time()-T0:.0f}s)")
if len(hits):
    print("  시험구역 안", int(in_box(hits).sum()))
    # 공유 꼭짓점에서 평면으로 연결된 4지 교차(입체 후보 확인 불가) 안내만
    tj = cKDTree(xyN[deg >= 3])
    d_, _ = tj.query(hits)
    print(f"  교차점이 차수3+ 노드 5m 안 {np.mean(d_<=5):.1%}, 20m 안 {np.mean(d_<=20):.1%}")

print("\n=== i. 인도 파일 bbox 안 제주 밖 여부")
Rs = np.vstack([p for _, p in lines])
Rs = Rs[::3]
tree = cKDTree(Rs)
Sall = dens(ps["SWK001"] + ps["SWK002"], 20.0)
d, _ = tree.query(Sall, workers=-1)
print(f"인도 표본 {len(Sall):,}: 도로 1km 초과 {np.mean(d>1000):.2%}  ({(d>1000).sum()*20/1000:.1f} km), 5km 초과 {(d>5000).sum()*20/1000:.1f} km")

print("\n=== j. 1m 보정 정의별 수")
ep = np.vstack([p[[0, -1]] for _, p in lines]); own_e = np.repeat(np.arange(len(lines)), 2)
all_v = np.vstack([p for _, p in lines]); ov = np.concatenate([np.full(len(p), i) for i, (_, p) in enumerate(lines)])
tv = cKDTree(all_v)
te = cKDTree(ep)
same = te.query_ball_point(ep, 0.01, workers=-1)
unm = np.array([not any(own_e[j] != own_e[i] for j in g_) for i, g_ in enumerate(same)])
idx_un = np.where(unm)[0]
gs = tv.query_ball_point(ep[idx_un], 1.0, workers=-1)
ct_v = sum(1 for ii, g_ in zip(idx_un, gs) if any(ov[j] != own_e[ii] for j in g_))
print("안 만나는 끝점 중 다른 선 꼭짓점 1m 안:", ct_v)
gs2 = te.query_ball_point(ep[idx_un], 1.0, workers=-1)
ct_e = sum(1 for ii, g_ in zip(idx_un, gs2) if any(own_e[j] != own_e[ii] for j in g_))
print("안 만나는 끝점 중 다른 선 끝점 1m 안:", ct_e)
print("끝", time.time() - T0)

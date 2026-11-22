"""마지막 측정: 입체 판정 검증, 844 기준 현실성, 부착 규칙 비교, 도로 사이 이동."""
import collections
import csv
import glob
import heapq
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


def xy(rows):
    x = []; i_ = []
    for i, r in enumerate(rows):
        try:
            la, lo = float(r["위도"]), float(r["경도"])
        except Exception:
            continue
        a, b = tf.transform(lo, la); x.append((a, b)); i_.append(i)
    return np.array(x), i_


print("=== 1. 교차 판정 함수 시험 (합성 자료)")
def crossing_test(a, b):
    D = b - a
    I, J = np.triu_indices(len(a), 1)
    den = D[I, 0] * D[J, 1] - D[I, 1] * D[J, 0]
    ok = np.abs(den) > 1e-9
    I, J, den = I[ok], J[ok], den[ok]
    w = a[J] - a[I]
    t = (w[:, 0] * D[J, 1] - w[:, 1] * D[J, 0]) / den
    u = (w[:, 0] * D[I, 1] - w[:, 1] * D[I, 0]) / den
    g = (t > 0) & (t < 1) & (u > 0) & (u < 1)
    return list(zip(I[g], J[g]))
a = np.array([[0.0, 0], [10, 0], [5, 5], [20, 0]]); b = np.array([[10.0, 10], [0, 10], [5, 8], [30, 0]])
print("  X자 교차 (0,1)만 나와야 함:", crossing_test(a, b))

print("\n=== 2. 신호기현황 관리부서와 횡단보도 종류")
st = load("제주_신호기현황")
print("관리부서", collections.Counter(r["관리부서"] for r in st))
std = load("횡단보도표준_제주특별자치도_서귀포시_횡단보도")
A_std, idx = xy(std)
yn = np.array([std[i]["보행자신호등유무"] == "Y" for i in idx])
print("횡단보도종류(전체)", collections.Counter(r["횡단보도종류"] for r in std).most_common(8))
print("횡단보도종류(Y)", collections.Counter(std[i]["횡단보도종류"] for i, f in zip(idx, yn) if f).most_common(8))
Ped = A_std[yn]
print("\n=== 3. 신호기 수만큼 놓았을 때 844의 50m 포함 상한(탐욕 근사, 후보=844점 자신)")
t = cKDTree(Ped)
cover = t.query_ball_point(Ped, 50.0)
cover = [set(c) for c in cover]
n = len(Ped)
for K in (385, 385 - sum(1 for r in st if "서귀포" in r["주소"] and r["기하구조"] == "단일로")):
    covered = set(); chosen = 0
    heap = [(-len(c), i) for i, c in enumerate(cover)]
    heapq.heapify(heap)
    while chosen < K and heap:
        gain, i = heapq.heappop(heap)
        g = len(cover[i] - covered)
        if not heap or -heap[0][0] <= g:
            covered |= cover[i]; chosen += 1
        else:
            heapq.heappush(heap, (-g, i))
    print(f"  {K}개 배치 시 844 중 {len(covered)}개 포함 = {len(covered)/n:.1%}")

print("\n=== 4. 인도 부착 규칙 비교")
def densify(p, step):
    seg = np.hypot(*np.diff(p, axis=0).T); cum = np.r_[0, np.cumsum(seg)]
    if cum[-1] <= 0:
        return None
    tt = np.r_[np.arange(0, cum[-1], step), cum[-1]]
    i = np.clip(np.searchsorted(cum, tt, side="right") - 1, 0, len(seg) - 1)
    q = np.c_[np.interp(tt, cum, p[:, 0]), np.interp(tt, cum, p[:, 1])]
    d = (p[i + 1] - p[i]) / np.maximum(seg[i], 1e-9)[:, None]
    return q, d, float(cum[-1])

def load_lines(key, step):
    P_, D_, R_, Li, Ln = [], [], [], [], []
    for rec, parts in read_shp(FILES[key], clip=True):
        for p in parts:
            r = densify(p, step)
            if r is None:
                continue
            q, d, l = r
            P_.append(q); D_.append(d); R_.append(np.full(len(q), rec)); Li.append(np.full(len(q), len(Ln))); Ln.append(l)
    return np.vstack(P_), np.vstack(D_), np.concatenate(R_), np.concatenate(Li), np.array(Ln)

Rp, Rd, Rr, _, _ = load_lines("road", 3.0)
Sp, Sd, Sr, Sl, SL = load_lines("sidewalk", 10.0)
ra = dbf_columns(FILES["road"], ["RVWD", "RDLN", "DVYN", "PVQT", "RDDV"])
sa = dbf_columns(FILES["sidewalk"], ["KIND", "BYYN", "WIDT"])
rw = np.array([float(x) for x in ra["RVWD"]])
kind = np.array(sa["KIND"])[Sr]
tr = cKDTree(Rp)
dd, ii = tr.query(Sp, k=80, distance_upper_bound=40, workers=-1)
valid = np.isfinite(dd); i2 = np.where(valid, ii, 0)
cosv = np.abs((Rd[i2] * Sd[:, None, :]).sum(2))
par = valid & (cosv > np.cos(np.radians(20)))
ddp = np.where(par, dd, np.inf)
jp = ddp.argmin(1); rows = np.arange(len(Sp)); dp = ddp[rows, jp]; ip = i2[rows, jp]
wm = rw[Rr[ip]]
inw = np.where(np.isfinite(dp), dp <= np.maximum(12, wm / 2 + 8), False)
for nm, m in [("SWK001 인도", kind == "SWK001"), ("전체", np.ones(len(Sp), bool))]:
    print(f"{nm}: 고정 12m(거리만) {np.mean((dd.min(1)<=12)[m]):.1%}, 12m+평행 {np.mean((dp<=12)[m]):.1%}, 폭반영 W+평행 {np.mean(inw[m]):.1%}, 평행 없음/멂 {np.mean(~inw[m]):.1%}")

print("\n=== 5. '도로에서 떨어진 인도' 3,362 구성 (전체/시험구역)")
off = np.load(os.path.join(TMP, "off.npz")); off_rec = set(off["idx"].tolist())
is_off = np.array([r in off_rec for r in Sr])
d1 = dd.min(1)
groups = collections.defaultdict(list)
for i in np.where(is_off)[0]:
    groups[Sl[i]].append(i)
line_cat = {}
for sl, ids in groups.items():
    ids = np.array(ids)
    frac30 = np.mean(dp[ids] <= 30)
    wmed = np.median(wm[ids][np.isfinite(dp[ids]) & (dp[ids] <= 30)]) if (dp[ids] <= 30).any() else 0
    md = np.median(np.minimum(d1[ids], 1e9))
    if frac30 >= 0.8 and wmed >= 15:
        c = "A"
    elif frac30 >= 0.8:
        c = "B"
    elif np.isfinite(md) and md > 50:
        c = "D"
    elif md > 30:
        c = "C"
    else:
        c = "E"
    line_cat[sl] = c
pts_all = {sl: Sp[np.array(ids)] for sl, ids in groups.items()}
inb = lambda P: (P[:, 0] >= bx0) & (P[:, 0] <= bx1) & (P[:, 1] >= by0) & (P[:, 1] <= by1)
tot = collections.Counter(); box = collections.Counter(); nbox = collections.Counter()
for sl, c in line_cat.items():
    l = SL[sl]
    tot[c] += l
    if inb(pts_all[sl]).mean() > 0.5:
        box[c] += l; nbox[c] += 1
print("  유형: A 넓은 도로 옆 B 평행(폭<15) C 30~50 D 50m 밖 E 기타")
print("  전체 km", {k: round(v / 1000, 1) for k, v in sorted(tot.items())})
print("  시험구역 km", {k: round(v / 1000, 1) for k, v in sorted(box.items())}, "개수", dict(nbox))
print("  시험구역 인도 표본 km", round(inb(Sp).sum() * 10 / 1000, 1))

print("\n=== 6. 진짜 떨어진 선이 도로 사이 지름길인가")
g = pickle.load(open(os.path.join(TMP, "graph.pkl"), "rb"))
xyN, A, B, L = g["xy"], g["A"], g["B"], g["L"]
N = len(xyN)
G = csr_matrix((np.r_[L, L], (np.r_[A, B], np.r_[B, A])), shape=(N, N))
tn = cKDTree(xyN)
# 진짜 떨어진 선(C,D,E)의 원형 끝점 + 그룹
recs = read_shp(FILES["sidewalk"], clip=True)
real_lines = []
for rec, parts in recs:
    if rec in off_rec:
        for p in parts:
            real_lines.append((rec, p))
# line_cat의 키는 부분선 인덱스(Sl), 위와 순서 다를 수 있어 표본 분류를 레코드 단위로 근사
rec_cat = {}
for sl, c in line_cat.items():
    rec_cat[int(Sr[np.array(groups[sl])][0])] = c
real = [(rec, p) for rec, p in real_lines if rec_cat.get(rec) in ("C", "D", "E")]
print("  진짜 떨어진 선", len(real), "km", round(sum(np.hypot(*np.diff(p, axis=0).T).sum() for _, p in real) / 1000, 1))
ep = np.vstack([p[[0, -1]] for _, p in real]); ow = np.repeat(np.arange(len(real)), 2)
te = cKDTree(ep)
pr = te.query_pairs(1.0, output_type="ndarray")
n_ = len(real)
gg = coo_matrix((np.ones(len(pr) * 1), (ow[pr[:, 0]], ow[pr[:, 1]])), shape=(n_, n_)) if len(pr) else coo_matrix((n_, n_))
nc, lab = connected_components(gg, directed=False)
Ld = np.bincount(lab, weights=[np.hypot(*np.diff(p, axis=0).T).sum() for _, p in real], minlength=nc)
print(f"  연결 묶음 {nc}개, 길이 상위(km) {np.sort(Ld)[::-1][:8].round(2)/1000}")
dep, _ = tr.query(ep, workers=-1)
touch_groups = collections.defaultdict(list)
for i, (d_, e_) in enumerate(zip(dep, ep)):
    if d_ <= 15:
        touch_groups[lab[ow[i]]].append(i)
print(f"  도로 15m 안 끝점을 2개 이상 가진 묶음 {sum(1 for v in touch_groups.values() if len(v) >= 2)}, 1개 {sum(1 for v in touch_groups.values() if len(v) == 1)}, 없음 {nc - len(touch_groups)}")
rat = []; kms = []
for gid, v in touch_groups.items():
    if len(v) < 2:
        continue
    P = ep[v]
    dm = np.hypot(P[:, None, 0] - P[None, :, 0], P[:, None, 1] - P[None, :, 1])
    a_, b_ = np.unravel_index(dm.argmax(), dm.shape)
    if dm[a_, b_] < 100:
        continue
    s = tn.query(P[a_])[1]; t_ = tn.query(P[b_])[1]
    dist = dijkstra(G, indices=int(s), directed=False, limit=20000)[t_]
    rat.append(dist / dm[a_, b_]); kms.append(Ld[gid])
rat = np.array(rat); kms = np.array(kms)
print(f"  두 끝 사이 100m 이상 떨어진 묶음 {len(rat)}개, 길이 합 {kms.sum()/1000:.1f} km")
if len(rat):
    print(f"  도로 우회/직선 비: 중앙값 {np.median(rat[np.isfinite(rat)]):.2f}, >2배 {np.mean(rat>2):.1%} (길이 {kms[rat>2].sum()/1000:.1f} km), >3배 {np.mean(rat>3):.1%}, 연결 안 됨(20km 내 없음) {np.mean(~np.isfinite(rat)):.1%}")

print("끝", time.time() - T0)

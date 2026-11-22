"""CSV 건수, 8장 품질 기준 계산 가능성, DEM 격자 크기."""
import collections
import csv
import glob
import io
import os
import pickle
import re
import struct
import sys
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
ROOT = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\공공데이터포털"
to5179 = Transformer.from_crs(4326, 5179, always_xy=True)


def load(label):
    p = glob.glob(os.path.join(ROOT, label, "*.csv"))[0]
    raw = open(p, "rb").read()
    for enc in ("utf-8-sig", "cp949"):
        try:
            return list(csv.DictReader(io.StringIO(raw.decode(enc)))), enc
        except UnicodeDecodeError:
            continue


def pts(rows):
    out = []; idx = []
    bad = 0
    for i, r in enumerate(rows):
        try:
            la, lo = float(r["위도"]), float(r["경도"])
        except (KeyError, TypeError, ValueError):
            bad += 1; continue
        if not (33.0 < la < 34.1 and 126.0 < lo < 127.2):
            bad += 1; continue
        x, y = to5179.transform(lo, la)
        out.append((x, y)); idx.append(i)
    return np.array(out), idx, bad


def clusters(a, d):
    pr = cKDTree(a).query_pairs(d, output_type="ndarray")
    n = len(a)
    g = coo_matrix((np.ones(len(pr)), (pr[:, 0], pr[:, 1])), shape=(n, n))
    return connected_components(g, directed=False)


print("===== 건수와 항목")
D_ = {}
for p in sorted(os.listdir(ROOT)):
    rows, enc = load(p)
    D_[p] = rows
    a, idx, bad = pts(rows) if "위도" in rows[0] else (np.empty((0, 2)), [], len(rows))
    print(f"[{p}] 행 {len(rows):,} 인코딩 {enc} 좌표 정상 {len(a):,} 이상/누락 {bad:,}")
    print("   항목:", list(rows[0].keys())[:40])
    for k in rows[0]:
        if "기준일" in k:
            print("   기준일 값", collections.Counter(r[k] for r in rows).most_common(4))
    for k in ("시군구명", "시군구"):
        if k in rows[0]:
            print("   시군구", collections.Counter(r[k] for r in rows).most_common(6))

st = D_["제주_신호기현황"]
print("\n===== 신호기현황")
print("기하구조", collections.Counter(r.get("기하구조", "") for r in st).most_common(15))
print("주소 앞 2토큰", collections.Counter(" ".join(r["주소"].split(" ")[:2]) for r in st).most_common(6))
print("시", collections.Counter(r["주소"].split(" ")[1] for r in st).most_common(5))
print("주소 있음", sum(1 for r in st if r["주소"].strip()), "번지로 끝남(마지막 토큰 숫자 시작)", sum(1 for r in st if r["주소"].split(" ")[-1][:1].isdigit()))
print("주소 형식: 도로명 포함(로/길 토큰)", sum(1 for r in st if re.search(r"(로|길)(\s|\d|$)", r["주소"])))
print("중복 주소 수", len(st) - len(set(r["주소"] for r in st)))
print("지번 주소 표본", [r["주소"] for r in st[:6]])
print("모든 항목 첫 행", st[0])
for k in st[0]:
    v = collections.Counter(r[k] for r in st)
    if 1 < len(v) < 30 and k != "주소":
        print(f"  {k}", v.most_common(12))

print("\n===== 서귀포 표준 횡단보도")
std = D_["횡단보도표준_제주특별자치도_서귀포시_횡단보도"]
print("보행자신호등유무", collections.Counter(r["보행자신호등유무"] for r in std))
A_std, idx_std, bad = pts(std)
sig_flag = np.array([std[i]["보행자신호등유무"].strip().upper() in ("Y", "있음") for i in idx_std])
Ped = A_std[sig_flag]
print("좌표 정상", len(A_std), "보행신호", sig_flag.sum(), "좌표 x범위", A_std[:, 0].min().round(), A_std[:, 0].max().round(), "y", A_std[:, 1].min().round(), A_std[:, 1].max().round())
# 서귀포시 범위 벗어난 점(북쪽)
print("한라산 북쪽(위도>33.43 가량 y>1490000)", int((A_std[:, 1] > 1490000).sum()))
for d in (15, 30, 50, 100):
    print(f"  보행신호 844의 {d}m 묶음 수 {clusters(Ped, d)[0]}")

print("\n===== 어린이보호구역")
sg = D_["제주_어린이보호구역_신호등"]
A_sg, idx, bad = pts(sg)
print("신호등 건수", len(sg), "좌표", len(A_sg), "구분", collections.Counter(r["신호등구분"] for r in sg).most_common(), "시군구", collections.Counter(r["시군구명"] for r in sg).most_common())
print("  30m 묶음", clusters(A_sg, 30)[0], " 50m 묶음", clusters(A_sg, 50)[0])
cx = D_["제주_어린이보호구역_횡단보도"]
A_cx, idx_cx, bad = pts(cx)
print("횡단보도", len(cx), "시군구", collections.Counter(r["시군구명"] for r in cx).most_common(), "보행신호등", collections.Counter((r["시군구명"], r.get("보행자신호등유무")) for r in cx).most_common())
sw = np.array(["서귀포" in cx[i]["시군구명"] for i in idx_cx])
Ac = A_cx[sw]
d, _ = cKDTree(A_std).query(Ac)
print(f"  서귀포 어린이 횡단보도 {len(Ac)} -> 표준 30m {np.mean(d<=30):.1%} 20m {np.mean(d<=20):.1%} 50m {np.mean(d<=50):.1%} 중앙값 {np.median(d):.1f}")
kx = D_["제주_어린이보호구역_교차로"]
A_kx, idx_kx, bad = pts(kx)
print("교차로", len(kx), "시군구", collections.Counter(r["시군구명"] for r in kx).most_common())
for k in kx[0]:
    v = collections.Counter(r[k] for r in kx)
    if 1 < len(v) < 10:
        print(f"  {k}", v.most_common(8))

# 도로 그래프
g = pickle.load(open(os.path.join(TMP, "graph.pkl"), "rb"))
xy = g["xy"]; deg = g["deg"]; A = g["A"]; B = g["B"]; L = g["L"]
J = xy[deg >= 3]
tj = cKDTree(J)
print("\n===== 8장 기준: 도로 교차로(차수>=3) 근접")
print("차수>=3 노드", len(J))


def summ(name, P):
    d, _ = tj.query(P)
    print(f"  {name} n={len(P)}: 교차로 5m {np.mean(d<=5):.1%} 10m {np.mean(d<=10):.1%} 15m {np.mean(d<=15):.1%} 20m {np.mean(d<=20):.1%} 30m {np.mean(d<=30):.1%} 50m {np.mean(d<=50):.1%}  중앙값 {np.median(d):.1f}")
    return d


# 무작위 도로 위 점 (시험구역 안 + 서귀포시내)
rng = np.random.default_rng(0)
recs = read_shp(FILES["road"], clip=False)
sel = []
tf = Transformer.from_crs(4326, 5179, always_xy=True)
bx0, by0 = tf.transform(126.46, 33.46); bx1, by1 = tf.transform(126.58, 33.54)
sx0, sy0 = tf.transform(126.53, 33.24); sx1, sy1 = tf.transform(126.60, 33.27)
Pall = []
for rec, parts in recs:
    for p in parts:
        Pall.append(p)
Pall_mid = np.array([(p[len(p) // 2]) for p in Pall])
lens = np.array([np.hypot(*np.diff(p, axis=0).T).sum() for p in Pall])
for name, box in [("제주시 시험구역 도로 무작위점", (bx0, by0, bx1, by1)), ("서귀포시내 도로 무작위점", (sx0, sy0, sx1, sy1))]:
    m = (Pall_mid[:, 0] >= box[0]) & (Pall_mid[:, 0] <= box[2]) & (Pall_mid[:, 1] >= box[1]) & (Pall_mid[:, 1] <= box[3])
    ids = np.where(m)[0]
    prob = lens[ids] / lens[ids].sum()
    pick = rng.choice(ids, size=min(5000, len(ids)), p=prob, replace=True)
    Q = []
    for i in pick:
        p = Pall[i]
        s = np.hypot(*np.diff(p, axis=0).T); c = np.r_[0, np.cumsum(s)]
        t = rng.uniform(0, c[-1])
        Q.append([np.interp(t, c, p[:, 0]), np.interp(t, c, p[:, 1])])
    Q = np.array(Q)
    summ(name, Q)
print("  (무작위 도로 위 점도 위처럼 교차로에 붙음 = 기준의 판별력 지표)")
d844 = summ("서귀포 보행신호 횡단보도", Ped)
summ("어린이 교차로", A_kx)
print("표준 전체", len(A_std)); summ("서귀포 표준 전체", A_std)

# 신호기 복수 노드
print("\n== 한 지점 주변의 차수>=3 노드 수")
for name, P in [("서귀포 보행신호", Ped), ("어린이 교차로", A_kx)]:
    for r in (20, 30, 50):
        c = np.array([len(x) for x in tj.query_ball_point(P, r)])
        print(f"  {name}: 반경 {r}m 노드 수 중앙값 {np.median(c):.0f}, 평균 {c.mean():.2f}, 0개 {np.mean(c==0):.1%}, 2개이상 {np.mean(c>=2):.1%}, 4개이상 {np.mean(c>=4):.1%}")

# 체인 기준 '진짜 교차로' (세 가지 이상 가지가 20m 이상)
adj = collections.defaultdict(list)
for i, (a, b) in enumerate(zip(A, B)):
    adj[int(a)].append((int(b), i)); adj[int(b)].append((int(a), i))
N = len(xy)
chain_leg = {}
def walk(s, ei):
    prev, ej = s, ei
    a_, b_ = A[ej], B[ej]
    cur = int(b_ if a_ == prev else a_)
    length = L[ej]
    steps = 0
    while deg[cur] == 2 and steps < 500:
        nxt = [(w, k) for w, k in adj[cur] if k != ej]
        if not nxt:
            break
        w, k = nxt[0]
        prev, cur, ej = cur, w, k
        length += L[k]
        steps += 1
    return length, cur
real = []
for s in np.where(deg >= 3)[0]:
    lens_ = [walk(int(s), k)[0] for w, k in adj[int(s)]]
    real.append(sum(1 for x in lens_ if x >= 20) >= 3)
real = np.array(real)
Jr = J[real]
print("차수>=3 중 20m 이상 가지 3개 이상", len(Jr), f"/ {len(J)} = {len(Jr)/len(J):.1%}")
tr = cKDTree(Jr)
for name, P in [("서귀포 보행신호 844", Ped), ("어린이 교차로 127", A_kx)]:
    d, _ = tr.query(P)
    print(f"  {name}: 5m {np.mean(d<=5):.1%} 10m {np.mean(d<=10):.1%} 20m {np.mean(d<=20):.1%} 30m {np.mean(d<=30):.1%} 50m {np.mean(d<=50):.1%}")

# 844의 위치(시내/외곽)
print("\n== 844 보행신호 지점이 도로 위인가")
Rp = []
for p in Pall:
    Rp.append(p)
samples = []
for p in Pall:
    s = np.hypot(*np.diff(p, axis=0).T); c = np.r_[0, np.cumsum(s)]
    if c[-1] <= 0:
        continue
    t = np.r_[np.arange(0, c[-1], 3.0), c[-1]]
    samples.append(np.c_[np.interp(t, c, p[:, 0]), np.interp(t, c, p[:, 1])])
samples = np.vstack(samples)
tR = cKDTree(samples)
dr, _ = tR.query(Ped)
print(f"844 -> 도로중심선: 5m {np.mean(dr<=5):.1%} 10m {np.mean(dr<=10):.1%} 20m {np.mean(dr<=20):.1%} 중앙값 {np.median(dr):.1f}")

print("\n===== 공개 DEM 격자")
p = os.path.join(D, "(B080)공개DEM_33607_img_2025.zip")
b = zipfile.ZipFile(p).read("33607/33607.img")
hp = struct.unpack("<I", b[16:20])[0]
root = struct.unpack("<I", b[hp + 8:hp + 12])[0]
out = []
def walk_hfa(ptr):
    while ptr:
        nxt, _, _, child, data, size = struct.unpack("<6I", b[ptr:ptr + 24])
        name = b[ptr + 24:ptr + 88].split(b"\0")[0].decode("latin1")
        typ = b[ptr + 88:ptr + 120].split(b"\0")[0].decode("latin1")
        if typ == "Eimg_Layer":
            w, h = struct.unpack("<II", b[data:data + 8])
            print("layer", name, w, h)
        if typ == "Eprj_MapInfo":
            n = struct.unpack("<I", b[data:data + 4])[0]
            q = data + 8 + n
            ul = struct.unpack("<2d", b[q + 8:q + 24]); q += 24
            lr = struct.unpack("<2d", b[q + 8:q + 24]); q += 24
            ps = struct.unpack("<2d", b[q + 8:q + 24])
            print("mapinfo ul", ul, "lr", lr, "pixel", ps)
        if child:
            walk_hfa(child)
        ptr = nxt
walk_hfa(root)

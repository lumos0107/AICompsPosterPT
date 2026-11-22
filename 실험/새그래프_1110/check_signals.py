"""신호기현황 변환 위치를 1:1,000 신호등제어기·신호등으로 독립 검증하고 신호 판정 반경 10·20·30m를 비교한다. 원본은 읽기만 한다.

1:1,000은 위치 자료로 쓰지 않는다(사용자 결정 2026-11-10). 비교는 도엽이 있는 곳 안에서만 한다.
도엽 범위: 도곽선이 없으면 도엽 안 모든 층의 외곽 상자.
진실 교차로(T): 최종 그래프의 차수 3 이상 노드 중 1:1,000 신호등·신호등제어기가 30m 안에 있는 노드. 20m도 민감도로 본다.
표시 노드(M_r): 변환 위치에서 r m 안의 차수 3 이상 노드 중 가장 가까운 하나 (교차로 단위 한 번만 셈).

실행: py -I check_signals.py
결과: 신호검증.out, 신호1000.csv
"""
import collections
import csv
import glob
import os
import re
import struct
import sys

import numpy as np
from pyproj import Transformer
from scipy.spatial import cKDTree

HERE = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\새그래프_1110"
sys.path.insert(0, r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\데이터진단_1109\수집계획용\에이전트검토")
from lib_shp import read_shp

sys.stdout.reconfigure(encoding="utf-8")
out = open(os.path.join(HERE, "신호검증.out"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out.write(s + "\n")
    out.flush()


ROOT = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵\수치지형도_1000_표본"
ROAD = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵\연속수치지도_제주_20261109\풀기\N3L_A0020000\N3L_A0020000"
to5179 = Transformer.from_crs(5186, 5179, always_xy=True)
wgs = Transformer.from_crs(4326, 5179, always_xy=True)
pts = []  # area, sheet, source, type, use, x5186, y5186
sheets = collections.defaultdict(lambda: [np.inf, np.inf, -np.inf, -np.inf])


def dbf_read(path):
    raw = open(path, "rb").read()
    n = struct.unpack("<I", raw[4:8])[0]
    hlen, rlen = struct.unpack("<2H", raw[8:12])
    off, pos, f = 1, 32, []
    while raw[pos] != 13:
        c = raw[pos:pos + 32]
        f.append((c[:11].split(b"\0")[0].decode("cp949", "replace"), off, c[16]))
        off += c[16]
        pos += 32
    rows = []
    for i in range(n):
        r = raw[hlen + i * rlen:hlen + (i + 1) * rlen]
        rows.append({k: r[o:o + l].decode("cp949", "replace").strip() for k, o, l in f})
    return rows


def shp_points(path):
    d = open(path, "rb").read()
    pos, o = 100, []
    while pos < len(d):
        _, clen = struct.unpack(">2i", d[pos:pos + 8])
        s = pos + 8
        if struct.unpack("<i", d[s:s + 4])[0] != 0:
            o.append(struct.unpack("<2d", d[s + 4:s + 20]))
        else:
            o.append(None)
        pos = s + clen * 2
    return o


# SHP 도엽
for area, folder in (("제주 도심", "제주도심_95장"), ("서귀포시내", "서귀포시내_86장")):
    for sd in sorted(glob.glob(os.path.join(ROOT, folder, "풀기", "*"))):
        if not os.path.isdir(sd):
            continue
        sh = os.path.basename(sd)
        for shp in glob.glob(os.path.join(sd, "*.shp")):
            d = open(shp, "rb").read(100)
            if len(d) >= 100:
                x0, y0, x1, y1 = struct.unpack("<4d", d[36:68])
                if x1 > x0 or y1 > y0:
                    b = sheets[(area, sh, "SHP")]
                    b[0], b[1], b[2], b[3] = min(b[0], x0), min(b[1], y0), max(b[2], x1), max(b[3], y1)
        for base, kind in (("N1P_C0493376", "신호등"), ("N1P_C0503375", "차단기")):
            p = os.path.join(sd, base)
            if not os.path.exists(p + ".shp"):
                continue
            xy = shp_points(p + ".shp")
            at = dbf_read(p + ".dbf")
            for q, r in zip(xy, at):
                if q is None:
                    continue
                use = r.get("용도") if kind == "신호등" else r.get("구분")
                if kind == "차단기" and not (use or "").startswith(("신호등제어기", "IUD002")):
                    continue
                pts.append((area, sh, "SHP", "신호등" if kind == "신호등" else "제어기", use, q[0], q[1]))
log(f"SHP 도엽 {len(sheets)}장, 점 {len(pts):,}")

# NGI 도엽 (서귀포시내)
ngi_n = 0
for f in sorted(glob.glob(os.path.join(ROOT, "서귀포시내_86장", "ngi", "*.ngi"))):
    t = open(f, "rb").read().decode("cp949", "replace")
    n = open(f[:-4] + ".nda", "rb").read().decode("cp949", "replace")
    sh = re.search(r"수치지도_(\d+)_", os.path.basename(f)).group(1)
    ngi_n += 1
    for bd in re.findall(r"BOUND\(([-\d.]+),\s*([-\d.]+),\s*([-\d.]+),\s*([-\d.]+)\)", t):
        x0, y0, x1, y1 = map(float, bd)
        b = sheets[("서귀포시내", sh, "NGI")]
        b[0], b[1], b[2], b[3] = min(b[0], x0), min(b[1], y0), max(b[2], x1), max(b[3], y1)

    def blocks(text):
        o = {}
        for p in re.split(r"<LAYER_START>", text)[1:]:
            m = re.search(r'\$LAYER_NAME\s*"([^"]+)"', p)
            if m:
                o[m.group(1)] = p
        return o

    gb, ab = blocks(t), blocks(n)
    for layer, kind, field in (("C0493376", "신호등", "용도"), ("C0503375", "차단기", "구분")):
        if layer not in gb or layer not in ab:
            continue
        geo = dict((int(i), (float(x), float(y))) for i, x, y in re.findall(r"\$RECORD\s+(\d+)\s+POINT\s+([-\d.]+)\s+([-\d.]+)", gb[layer]))
        fields = re.findall(r'ATTRIB\("([^"]+)"', ab[layer])
        ix = fields.index(field)
        for i, row in re.findall(r"\$RECORD\s+(\d+)\s*\r?\n([^\r\n]+)", ab[layer].split("<DATA>")[1]):
            vals = next(csv.reader([row], skipinitialspace=True))
            use = vals[ix]
            if kind == "차단기" and use != "신호등제어기":
                continue
            if int(i) in geo:
                x, y = geo[int(i)]
                pts.append(("서귀포시내", sh, "NGI", "신호등" if kind == "신호등" else "제어기", use, x, y))
log(f"NGI 도엽 {ngi_n}장, 누적 점 {len(pts):,}")
log("종류별:", collections.Counter((p[0], p[2], p[3]) for p in pts).most_common())
log("용도:", collections.Counter(p[4] for p in pts).most_common())

P = np.array([(p[5], p[6]) for p in pts])
X, Y = to5179.transform(P[:, 0], P[:, 1])
Q = np.c_[X, Y]
area = np.array([p[0] for p in pts])
source = np.array([p[2] for p in pts])
ptype = np.array([p[3] for p in pts])

# 도엽 범위 (5179)
sh_box = []
for k, b in sheets.items():
    xx, yy = to5179.transform([b[0], b[2], b[2], b[0]], [b[1], b[1], b[3], b[3]])
    sh_box.append((k, min(xx), min(yy), max(xx), max(yy)))
boxes = np.array([b[1:] for b in sh_box])


def covered(p):
    p = np.atleast_2d(p)
    c = np.zeros(len(p), bool)
    a = np.empty(len(p), dtype=object)
    for (k, x0, y0, x1, y1) in sh_box:
        m = (p[:, 0] >= x0) & (p[:, 0] <= x1) & (p[:, 1] >= y0) & (p[:, 1] <= y1)
        c |= m
        a[m] = k[0]
    return c, a


# 그래프
g = np.load(os.path.join(HERE, "그래프_최종.npz"))
xy, A, B, L, main, gline, ga, gb_ = g["xy"], g["A"], g["B"], g["L"], g["main"], g["line"], g["a"], g["b"]
N = len(xy)
deg = np.bincount(A[main], minlength=N) + np.bincount(B[main], minlength=N)
jn = np.where(deg >= 3)[0]
tj = cKDTree(xy[jn])
lines = [p for r, parts in read_shp(ROAD, clip=False) for p in parts]
road_pts = []
for ei in np.where(main)[0].tolist():
    p = lines[gline[ei]][ga[ei]:gb_[ei] + 1]
    c = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]
    if c[-1] <= 0:
        continue
    t = np.r_[np.arange(0, c[-1], 5.0), c[-1]]
    road_pts.append(np.c_[np.interp(t, c, p[:, 0]), np.interp(t, c, p[:, 1])])
road_pts = np.vstack(road_pts)
tr = cKDTree(road_pts)

# 좌표계 확인: NGI와 SHP의 도로까지 거리
d_r = tr.query(Q)[0]
log("\n[좌표계 확인] 1:1,000 점에서 1:5,000 도로중심선까지 거리 (변환 뒤)")
for nm, m in (("제주 도심 SHP", (area == "제주 도심") & (source == "SHP")), ("서귀포시내 SHP", (area == "서귀포시내") & (source == "SHP")), ("서귀포시내 NGI", source == "NGI")):
    if m.any():
        log(f"  {nm}: {int(m.sum()):,}개, 중앙값 {np.median(d_r[m]):.1f}m, 90% {np.percentile(d_r[m], 90):.1f}m, 최대 {d_r[m].max():.1f}m")

# 중복 (도엽 경계)
keep = np.ones(len(Q), bool)
for tp in ("신호등", "제어기"):
    idx = np.where(ptype == tp)[0]
    pr = cKDTree(Q[idx]).query_pairs(1.0, output_type="ndarray")
    sh_id = np.array([pts[i][1] for i in idx])
    diff = sh_id[pr[:, 0]] != sh_id[pr[:, 1]]
    log(f"[중복] {tp}: 1m 안 쌍 {len(pr)}, 그중 서로 다른 도엽 {int(diff.sum())}")
    keep[idx[np.unique(pr[diff].max(1))]] = False
Qk, area_k, ptype_k = Q[keep], area[keep], ptype[keep]
log(f"중복 제거 뒤 점 {len(Qk):,} (제거 {int((~keep).sum())})")
log("지역·종류:", collections.Counter(zip(area_k.tolist(), ptype_k.tolist())).most_common())
with open(os.path.join(HERE, "신호1000.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["지역", "도엽", "형식", "종류", "용도", "x5179", "y5179"])
    for i, (a_, sh, src, tp, use, _, _) in enumerate(pts):
        if keep[i]:
            w.writerow([a_, sh, src, tp, use, round(float(Q[i, 0]), 2), round(float(Q[i, 1]), 2)])

# 변환 위치
sig = list(csv.DictReader(open(os.path.join(HERE, "신호위치.csv"), encoding="utf-8-sig")))
S = np.array([(float(r["x"]), float(r["y"])) if r["x"] else (np.nan, np.nan) for r in sig])
state = np.array([r["상태"] for r in sig])
city = np.array([r["시"] for r in sig])
has = np.isfinite(S[:, 0])
cov, cov_a = covered(np.nan_to_num(S))
cov &= has
log(f"\n변환 위치 {int(has.sum())}건, 도엽 안 {int(cov.sum())}건 ({collections.Counter(cov_a[cov].tolist()).most_common()})")
log(f"도엽 안 상태: {collections.Counter(state[cov].tolist()).most_common()}")

BINS = [(0, 10), (10, 20), (20, 30), (30, 50), (50, 100), (100, 1e12)]
LBL = ["10m 이하", "10~20m", "20~30m", "30~50m", "50~100m", "100m 초과"]


def table(name, d):
    n = len(d)
    if n == 0:
        log(f"{name}: 대상 없음")
        return
    cells = []
    for a, b in BINS:
        k = int(((d > a) & (d <= b)).sum()) + (int((d == 0).sum()) if a == 0 else 0)
        cells.append(f"{k} ({k / n:.1%})")
    log(f"{name} | n={n} | {' | '.join(cells)} | 중앙값 {np.median(d):.1f}m")


tl_all = cKDTree(Qk)
tl_c = cKDTree(Qk[ptype_k == "제어기"])
tl_s = cKDTree(Qk[ptype_k == "신호등"])
log("\n[표 A] 변환 위치 -> 가장 가까운 1:1,000 (도엽 안)")
log("구분 | 대상 | " + " | ".join(LBL) + " | 중앙값")
success = cov & (state == "성공")
ambig = cov & (state == "모호")
for nm, tree in (("제어기", tl_c), ("신호등", tl_s), ("제어기+신호등", tl_all)):
    table(f"성공 전체 -> {nm}", tree.query(S[success])[0])
    for ar in ("제주 도심", "서귀포시내"):
        m = success & (cov_a == ar)
        table(f"  성공 {ar} -> {nm}", tree.query(S[m])[0])
table("모호 -> 제어기+신호등", tl_all.query(S[ambig])[0])

# 기준점: 도엽 안 무작위 도로 점
rc, ra = covered(road_pts)
rng = np.random.default_rng(20261110)
cand = np.where(rc)[0]
rand = road_pts[rng.choice(cand, size=min(3000, len(cand)), replace=False)]
log("\n[비교 기준] 도엽 안 도로 위 무작위 3,000점 -> 제어기+신호등")
table("무작위 도로 점", tl_all.query(rand)[0])
table("무작위 도로 점 -> 차수 3 이상 노드", tj.query(rand)[0])

# 역방향: 1:1,000 묶음 -> 변환 위치
cl_n = np.arange(len(Qk))
pr = tl_all.query_pairs(30.0, output_type="ndarray")
parent = list(range(len(Qk)))


def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


for a_, b_ in pr.tolist():
    parent[find(a_)] = find(b_)
root = np.array([find(i) for i in range(len(Qk))])
ur, cl = np.unique(root, return_inverse=True)
Cxy = np.c_[np.bincount(cl, weights=Qk[:, 0]) / np.bincount(cl), np.bincount(cl, weights=Qk[:, 1]) / np.bincount(cl)]
log(f"\n1:1,000 점을 30m로 묶은 곳 {len(Cxy):,}곳")
ts = cKDTree(S[has])
log("[표 B] 1:1,000 묶음 중심 -> 가장 가까운 변환 위치 (변환 830건 전부 사용)")
table("1:1,000 묶음", ts.query(Cxy)[0])

# 반경 비교
log("\n[표 C] 반경별 비교 (도엽 안, 차수 3 이상 노드, 성공만)")
jc, _ = covered(xy[jn])
nodes_cov = jn[jc]
dT30 = tl_all.query(xy[nodes_cov])[0]
for truth_r in (30.0, 20.0):
    T = set(nodes_cov[dT30 <= truth_r].tolist())
    log(f"\n진실 교차로: 도엽 안 차수 3+ 노드 {len(nodes_cov):,}개 중 1:1,000 {truth_r:.0f}m 안 {len(T):,}개")
    log("반경 | 노드가 r 안에 있는 변환 비율 | 무작위 도로 점의 같은 비율 | 표시 노드 수 | 정밀도 | 재현율")
    sp = S[success]
    dj, ij = tj.query(sp)
    dj_rand = tj.query(rand)[0]
    for r in (10.0, 20.0, 30.0):
        m = dj <= r
        marked = set(jn[ij[m]].tolist()) & set(nodes_cov.tolist())
        tp = len(marked & T)
        log(f"{int(r)}m | {m.mean():.1%} | {(dj_rand <= r).mean():.1%} | {len(marked):,} | {tp / max(len(marked), 1):.1%} | {tp / max(len(T), 1):.1%}")

# 8장 기준 (제주 전체)
log("\n[표 D] 8장 기준 값 (제주 전체, 단일로 제외, 변환 성공)")
ok = has & (state == "성공")
d_all = tj.query(S[ok])[0]
for r in (10, 20, 30):
    log(f"차수 3 이상 노드가 {r}m 안: {(d_all <= r).mean():.1%} (성공 {int(ok.sum())}건)")
for nm in ("제주시", "서귀포시"):
    m = ok & (city == nm)
    log(f"  {nm} 30m 안: {(tj.query(S[m])[0] <= 30).mean():.1%} ({int(m.sum())}건)")
ok2 = has & np.isin(state, ["성공", "모호"])
log(f"모호 포함 30m 안: {(tj.query(S[ok2])[0] <= 30).mean():.1%} ({int(ok2.sum())}건)")
allroad = tj.query(road_pts[rng.choice(len(road_pts), 5000, replace=False)])[0]
log(f"참고: 제주 전체 도로 위 무작위 점의 30m 안 비율 {(allroad <= 30).mean():.1%}")

# 서귀포시 보행신호 횡단보도
import io
raw = open(r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\공공데이터포털\횡단보도표준_제주특별자치도_서귀포시_횡단보도\횡단보도표준_제주특별자치도_서귀포시_횡단보도.csv", "rb").read().decode("utf-8-sig")
cw = list(csv.DictReader(io.StringIO(raw)))
sg_col = [c for c in cw[0] if "보행자신호등" in c or "보행신호" in c][0]
la, lo = [c for c in cw[0] if "위도" in c][0], [c for c in cw[0] if "경도" in c][0]
ped = [r for r in cw if r[sg_col].strip().upper() in ("Y", "있음", "1")]
log(f"\n[표 E] 서귀포시 횡단보도 {len(cw):,}, 보행신호 있음 {len(ped)} (항목 '{sg_col}')")
cx, cy = wgs.transform(np.array([float(r[lo]) for r in ped]), np.array([float(r[la]) for r in ped]))
C = np.c_[cx, cy]
sg = has & (city == "서귀포시") & (state == "성공")
tsg = cKDTree(S[sg])
d50 = tsg.query(C)[0]
near_j = tj.query(C)[0]
for nm, m in (("전체 보행신호 횡단보도", np.ones(len(C), bool)), ("교차로 부근(차수 3+ 노드 30m 안)", near_j <= 30), ("교차로 부근(50m 안)", near_j <= 50)):
    log(f"{nm}: {int(m.sum())}개, 변환 위치 50m 안 {(d50[m] <= 50).mean():.1%}, 30m 안 {(d50[m] <= 30).mean():.1%}, 100m 안 {(d50[m] <= 100).mean():.1%}")
log("끝")

# ---- 기준 미달 시 판단 자료 (사용자 지시 2026-11-10: 혼자 바꾸지 말고 1:1,000 위치 자료 안을 같이 가져올 것)
log("\n[표 F] 변환 위치의 넓은 반경 참고 (도엽 안, 성공만, 채택 아님)")
log("반경 | 노드가 r 안 비율 | 무작위 도로 점 | 표시 노드 수 | 정밀도(진실 30m) | 재현율")
T = set(nodes_cov[dT30 <= 30].tolist())
for r in (30.0, 40.0, 50.0, 60.0):
    m = dj <= r
    marked = set(jn[ij[m]].tolist()) & set(nodes_cov.tolist())
    tp = len(marked & T)
    log(f"{int(r)}m | {m.mean():.1%} | {(dj_rand <= r).mean():.1%} | {len(marked):,} | {tp / max(len(marked), 1):.1%} | {tp / max(len(T), 1):.1%}")
sp_all = S[has & (state == "성공")]
log("제주 전체 성공 807건: " + ", ".join(f"{r}m 안 {(tj.query(sp_all)[0] <= r).mean():.1%}" for r in (30, 40, 50, 60)))

log("\n[표 G] 대안: 1:1,000을 위치 자료로 쓰고 실험 범위를 도엽이 있는 곳으로 좁힐 때")
mid = (xy[A] + xy[B]) / 2
for ar in ("제주 도심", "서귀포시내"):
    bb = [b for b in sh_box if b[0][0] == ar]
    area_km2 = sum((b[3] - b[1]) * (b[4] - b[2]) for b in bb) / 1e6
    mk = np.zeros(len(mid), bool)
    nk = np.zeros(len(jn), bool)
    for (_, x0, y0, x1, y1) in bb:
        mk |= (mid[:, 0] >= x0) & (mid[:, 0] <= x1) & (mid[:, 1] >= y0) & (mid[:, 1] <= y1)
        nk |= (xy[jn, 0] >= x0) & (xy[jn, 0] <= x1) & (xy[jn, 1] >= y0) & (xy[jn, 1] <= y1)
    in_a = area_k == ar
    roots = np.unique(cl[in_a])
    cc = Cxy[roots]
    d_c = tj.query(cc)[0]
    ext = (min(b[1] for b in bb), min(b[2] for b in bb), max(b[3] for b in bb), max(b[4] for b in bb))
    log(f"{ar}: 도엽 {len(bb)}장, 도엽 합계 {area_km2:.1f}km2, 바깥 사각형 {(ext[2] - ext[0]) / 1000:.1f} x {(ext[3] - ext[1]) / 1000:.1f}km, 최종 도로 {L[main & mk].sum() / 1000:.1f}km, 차수 3+ 노드 {int(nk.sum()):,}, 1:1,000 묶음 {len(cc)}곳")
    log(f"  묶음 중심에서 차수 3+ 노드: 10m 안 {(d_c <= 10).mean():.1%}, 20m 안 {(d_c <= 20).mean():.1%}, 30m 안 {(d_c <= 30).mean():.1%}, 중앙값 {np.median(d_c):.1f}m")
    tq = cKDTree(Qk[in_a])
    jc_a = jn[nk]
    dn = tq.query(xy[jc_a])[0]
    cl_a = cl[in_a]
    for r in (10.0, 20.0, 30.0):
        mk_n = dn <= r
        hit = set(cl_a[tq.query(xy[jc_a[mk_n]])[1]].tolist())
        log(f"  반경 {int(r)}m: 표시 노드 {int(mk_n.sum()):,} ({mk_n.mean():.1%}), 노드가 붙은 묶음 {len(hit)}/{len(cc)} ({len(hit) / len(cc):.1%}), 묶음당 노드 {mk_n.sum() / max(len(hit), 1):.1f}")
    road_rand = road_pts[(road_pts[:, 0] >= ext[0]) & (road_pts[:, 0] <= ext[2]) & (road_pts[:, 1] >= ext[1]) & (road_pts[:, 1] <= ext[3])]
    log(f"  서로 비교: 이 지역 변환 위치 대비 묶음 재현 {(cKDTree(S[has]).query(cc)[0] <= 50).mean():.1%} (50m 안)")
log("도엽 연도: 제주 도심 95장 전부 2024 촬영·2025 제작, 서귀포시내 86장은 2025년 15장·2017년 25장·2013년 46장 (11/10 기록)")
log("끝2")

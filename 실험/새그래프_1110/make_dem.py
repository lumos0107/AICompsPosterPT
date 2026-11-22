"""등고선(5m 간격)과 표고점으로 고도를 보간한다. 원본은 읽기만 한다.
1) 표고점 이상값 확인 (표고점만 뺀 등고선 보간과 비교)
2) 2km 구역 단위로 표고점 20%를 빼서 검증 (시드 20261110, 8장 기준: 오차 중앙값 2m 이하)
3) 전체 점으로 10m 격자와 최종 그래프 노드 고도 계산 (고도 누락 1% 이하 기준)
보간은 들로네 삼각망 선형 보간이다. 등고선 꼭짓점은 선을 따라 10m 간격으로 솎는다.
실행: py -I make_dem.py
결과: 고도점검.out, 고도격자_10m.npy, 고도격자_10m.json, 노드고도.npy
"""
import json
import os
import sys
import time

import numpy as np
from scipy.interpolate import LinearNDInterpolator
from scipy.spatial import Delaunay

HERE = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\새그래프_1110"
sys.path.insert(0, r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\데이터진단_1109\수집계획용\에이전트검토")
from lib_shp import dbf_columns

sys.stdout.reconfigure(encoding="utf-8")
out = open(os.path.join(HERE, "고도점검.out"), "w", encoding="utf-8")
T0 = time.time()


def log(*a):
    s = " ".join(str(x) for x in a) + f"  [{time.time() - T0:.0f}초]"
    print(s, flush=True)
    out.write(s + "\n")
    out.flush()


N3 = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵\연속수치지도_제주_20261109\풀기"
CONT = os.path.join(N3, "N3L_F0010000", "N3L_F0010000")
SPOT = os.path.join(N3, "N3P_F0020000", "N3P_F0020000")
import struct

# 등고선
zc = np.array([float(x) for x in dbf_columns(CONT, ["CONT"])["CONT"]])
log(f"등고선 {len(zc):,}개, 값 범위 {zc.min()} ~ {zc.max()}, 5m 배수 아님 {int((np.abs(zc / 5 - np.round(zc / 5)) > 1e-6).sum())}개")
d = open(CONT + ".shp", "rb").read()
P, Z = [], []
pos, i, raw = 100, 0, 0
while pos < len(d):
    _, clen = struct.unpack(">2i", d[pos:pos + 8])
    s = pos + 8
    if struct.unpack("<i", d[s:s + 4])[0] != 0:
        np_, npts = struct.unpack("<2i", d[s + 36:s + 44])
        parts = list(np.frombuffer(d, "<i4", np_, s + 44)) + [npts]
        pts = np.frombuffer(d, "<f8", npts * 2, s + 44 + 4 * np_).reshape(-1, 2)
        raw += npts
        for a, b in zip(parts[:-1], parts[1:]):
            q = pts[a:b]
            if len(q) < 2:
                continue
            c = np.r_[0, np.cumsum(np.hypot(*np.diff(q, axis=0).T))]
            n = max(2, int(c[-1] // 10) + 1)
            t = np.linspace(0, c[-1], n)
            P.append(np.c_[np.interp(t, c, q[:, 0]), np.interp(t, c, q[:, 1])])
            Z.append(np.full(n, zc[i]))
    pos = s + clen * 2
    i += 1
Pc, Zc = np.vstack(P), np.concatenate(Z)
log(f"등고선 꼭짓점 원본 {raw:,}, 10m 솎은 뒤 {len(Pc):,}")

# 표고점
d = open(SPOT + ".shp", "rb").read()
sxy = []
pos = 100
while pos < len(d):
    _, clen = struct.unpack(">2i", d[pos:pos + 8])
    s = pos + 8
    sxy.append(struct.unpack("<2d", d[s + 4:s + 20]))
    pos = s + clen * 2
sxy = np.array(sxy)
sz = np.array([float(x) for x in dbf_columns(SPOT, ["NUME"])["NUME"]])
log(f"표고점 {len(sz):,}개, 범위 {sz.min():.2f} ~ {sz.max():.2f}, 0 이하 {int((sz <= 0).sum())}개, 0 {int((sz == 0).sum())}개")

# 1) 이상값: 등고선만의 보간과 비교
tc = Delaunay(Pc)
log("등고선 삼각망 끝")
fc = LinearNDInterpolator(tc, Zc)
z0 = fc(sxy)
ok0 = np.isfinite(z0)
diff = sz - z0
log(f"등고선 보간 범위 안 표고점 {int(ok0.sum()):,}개, 표고점-등고선 차 분위(5,50,95) {np.nanpercentile(diff, [5, 50, 95]).round(2).tolist()}")
for th in (5, 10, 20, 50):
    log(f"  차 절댓값 {th}m 초과: {int((np.abs(diff[ok0]) > th).sum()):,}개")
low = sz <= 0
log(f"0 이하 표고점 {int(low.sum())}개: 등고선 범위 안 {int((low & ok0).sum())}, 차 절댓값 5m 초과 {int((low & ok0 & (np.abs(diff) > 5)).sum())}, 최솟값 지점의 등고선 보간 {z0[int(np.argmin(sz))]:.2f}")
bad = ok0 & (np.abs(diff) > 20)
outside = ~ok0
log(f"이상값으로 뺀 표고점: 차 절댓값 20m 초과 {int(bad.sum())}개. 등고선 범위 밖 표고점 {int(outside.sum())}개는 유지")
use = ~bad

# 2) 구역 단위 검증
rng = np.random.default_rng(20261110)
bx = np.floor(sxy[:, 0] / 2000).astype(np.int64)
by = np.floor(sxy[:, 1] / 2000).astype(np.int64)
key = bx * 100000 + by
blocks = np.unique(key[use])
hold_b = rng.choice(blocks, size=int(round(len(blocks) * 0.2)), replace=False)
hold = np.isin(key, hold_b) & use
train = use & ~hold
log(f"구역 {len(blocks):,}개 중 검증 {len(hold_b):,}개, 검증 표고점 {int(hold.sum()):,}개, 학습 표고점 {int(train.sum()):,}개")
Pv = np.vstack([Pc, sxy[train]])
Zv = np.r_[Zc, sz[train]]
Pv, ui = np.unique(np.round(Pv, 2), axis=0, return_index=True)
Zv = Zv[ui]
fv = LinearNDInterpolator(Pv, Zv)
log("검증용 삼각망 끝")
zh = fv(sxy[hold])
e = zh - sz[hold]
ev = e[np.isfinite(e)]
log(f"[표고점 검증] 평가 {len(ev):,}개, 절대오차 중앙값 {np.median(np.abs(ev)):.2f}m, 평균 {np.abs(ev).mean():.2f}m, 90% {np.percentile(np.abs(ev), 90):.2f}m, 편향 중앙값 {np.median(ev):.2f}m, 범위 밖 {int((~np.isfinite(e)).sum())}개")

# 3) 전체 점
Pa = np.vstack([Pc, sxy[use]])
Za = np.r_[Zc, sz[use]]
Pa, ui = np.unique(np.round(Pa, 2), axis=0, return_index=True)
Za = Za[ui]
fa = LinearNDInterpolator(Pa, Za)
log(f"전체 삼각망 끝, 점 {len(Pa):,}개")

g = np.load(os.path.join(HERE, "그래프_최종.npz"))
xy, main, A, B = g["xy"], g["main"], g["A"], g["B"]
zn = fa(xy).astype(np.float32)
np.save(os.path.join(HERE, "노드고도.npy"), zn)
nm = np.unique(np.r_[A[main], B[main]])
log(f"[노드 고도] 주 요소 노드 {len(nm):,}개, 누락 {int(np.isnan(zn[nm]).sum())}개 ({np.isnan(zn[nm]).mean():.3%}), 범위 {np.nanmin(zn[nm]):.1f} ~ {np.nanmax(zn[nm]):.1f}m")
if np.isnan(zn[nm]).any():
    miss = nm[np.isnan(zn[nm])]
    log("  누락 노드 예:", xy[miss[:5]].round().tolist())

X0, Y0, X1, Y1 = 873000, 1458000, 952000, 1559000
RES = 10.0
xs = np.arange(X0 + RES / 2, X1, RES)
ys = np.arange(Y0 + RES / 2, Y1, RES)
grid = np.empty((len(ys), len(xs)), np.float32)
for j in range(0, len(ys), 500):
    yy = ys[j:j + 500]
    XX, YY = np.meshgrid(xs, yy)
    grid[j:j + 500] = fa(np.c_[XX.ravel(), YY.ravel()]).reshape(XX.shape).astype(np.float32)
    if j % 2500 == 0:
        log(f"  격자 {j}/{len(ys)}")
np.save(os.path.join(HERE, "고도격자_10m.npy"), grid)
json.dump(dict(crs="EPSG:5179", res=RES, x0=X0, y0=Y0, nx=len(xs), ny=len(ys), 주의="행은 y가 작은 쪽부터, 값은 셀 중심, 범위 밖은 NaN"), open(os.path.join(HERE, "고도격자_10m.json"), "w", encoding="utf-8"), ensure_ascii=False)
log(f"[격자] {grid.shape}, 값 있음 {np.isfinite(grid).mean():.1%}")
log("끝")

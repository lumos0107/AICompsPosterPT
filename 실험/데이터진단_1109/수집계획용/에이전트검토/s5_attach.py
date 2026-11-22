"""인도를 도로 속성으로만 붙이는 처리가 가능한지 측정."""
import collections
import os
import pickle
import sys
import time
import numpy as np
from pyproj import Transformer
from scipy.spatial import cKDTree

sys.path.insert(0, r"C:\Users\seungjun\AppData\Local\Temp\plan_review_Br6p2s")
from lib_shp import *

sys.stdout.reconfigure(encoding="utf-8")
TMP = r"C:\Users\seungjun\AppData\Local\Temp\plan_review_Br6p2s"
T0 = time.time()
to5179 = Transformer.from_crs(4326, 5179, always_xy=True)
bx0, by0 = to5179.transform(126.46, 33.46); bx1, by1 = to5179.transform(126.58, 33.54)


def densify(p, step):
    seg = np.hypot(*np.diff(p, axis=0).T); cum = np.r_[0, np.cumsum(seg)]
    if cum[-1] <= 0:
        return None
    t = np.r_[np.arange(0, cum[-1], step), cum[-1]]
    i = np.clip(np.searchsorted(cum, t, side="right") - 1, 0, len(seg) - 1)
    q = np.c_[np.interp(t, cum, p[:, 0]), np.interp(t, cum, p[:, 1])]
    d = (p[i + 1] - p[i]) / np.maximum(seg[i], 1e-9)[:, None]
    return q, d, float(cum[-1])


def load(key, step):
    recs = read_shp(FILES[key], clip=True)
    P, D, R, Li, Ln = [], [], [], [], []
    for rec, parts in recs:
        for p in parts:
            r = densify(p, step)
            if r is None:
                continue
            q, d, l = r
            P.append(q); D.append(d); R.append(np.full(len(q), rec)); Li.append(np.full(len(q), len(Ln))); Ln.append(l)
    return np.vstack(P), np.vstack(D), np.concatenate(R), np.concatenate(Li), np.array(Ln)


Rp, Rd, Rr, Rl, RL = load("road", 3.0)
Sp, Sd, Sr, Sl, SL = load("sidewalk", 10.0)
print("road samples", len(Rp), "sidewalk samples", len(Sp), time.time() - T0, flush=True)
ra = dbf_columns(FILES["road"], ["RVWD", "RDLN", "DVYN", "RDDV"])
sa = dbf_columns(FILES["sidewalk"], ["KIND", "BYYN", "WIDT"])
rw = np.array([float(x) for x in ra["RVWD"]])
rn = np.array([float(x) for x in ra["RDLN"]])
rdv = np.array(ra["DVYN"])
kind = np.array(sa["KIND"])[Sr]
widt = np.array([float(x) if x else np.nan for x in sa["WIDT"]])[Sr]
weights = np.ones(len(Sp)) * 10.0
tr = cKDTree(Rp)
# 1) 가장 가까운 도로 분류
d1, i1 = tr.query(Sp, workers=-1)
ang = np.degrees(np.arccos(np.clip(np.abs((Sd * Rd[i1]).sum(1)), 0, 1)))
print("\n== 인도 표본 분류 (가장 가까운 도로 기준, 표본 비율)")
for nm, m in [("인도+자전거 전체", np.ones(len(Sp), bool)), ("SWK001 인도", kind == "SWK001"), ("SWK002 자전거", kind == "SWK002")]:
    S = (d1 <= 12) & (ang < 20); T = (d1 <= 12) & (ang >= 20); U = (d1 > 12) & (d1 <= 30) & (ang < 20); V = (d1 > 12) & (d1 <= 30) & (ang >= 20); W = d1 > 30
    print(f"{nm}: <=12평행 {np.mean(S[m]):.1%} <=12비평행 {np.mean(T[m]):.1%} 12~30평행 {np.mean(U[m]):.1%} 12~30비평행 {np.mean(V[m]):.1%} >30 {np.mean(W[m]):.1%}  n={m.sum():,}")

# 2) 30m 안의 평행 도로
K = 80
dd, ii = tr.query(Sp, k=K, distance_upper_bound=35, workers=-1)
print("이웃 질의", time.time() - T0, flush=True)
valid = np.isfinite(dd)
ii2 = np.where(valid, ii, 0)
cosv = np.abs((Rd[ii2] * Sd[:, None, :]).sum(2))
par = valid & (cosv > np.cos(np.radians(20)))
# 가장 가까운 평행 도로
ddp = np.where(par, dd, np.inf)
jp = ddp.argmin(1)
rows = np.arange(len(Sp))
dp = ddp[rows, jp]
ip = ii2[rows, jp]
has30 = dp <= 30
has12 = dp <= 12
print(f"\n== 평행 도로 (20도 이내) 가장 가까운 거리: 12m 안 {has12.mean():.1%}, 30m 안 {has30.mean():.1%}, 35m 초과 {np.mean(dp>35):.1%}")
vals = Rr[ip]
wmatch = rw[vals]
print("가장 가까운 평행 도로의 RVWD 분포 (평행 도로 있는 표본)", np.percentile(wmatch[has30], [10, 25, 50, 75, 90]).round(1))
# 도로폭 구간별 거리
print("도로폭 구간별 인도-중심선 거리 (평행 도로 30m 안 표본)")
for a, b in [(0, 4), (4, 8), (8, 12), (12, 16), (16, 20), (20, 25), (25, 30), (30, 100)]:
    m = has30 & (wmatch >= a) & (wmatch < b)
    if m.sum():
        print(f"  폭 {a:>2}~{b:<3}: 표본 {m.sum():>7,}  거리 분위 p25 {np.percentile(dp[m],25):5.1f} p50 {np.median(dp[m]):5.1f} p75 {np.percentile(dp[m],75):5.1f}  >12m {np.mean(dp[m]>12):.1%}")
# 12~30m 표본의 원인
m = (dp > 12) & (dp <= 30)
print(f"12~30m에 평행 도로가 있는 표본 {m.mean():.1%}. 그 도로의 폭>=15m {np.mean(wmatch[m]>=15):.1%}, >=20m {np.mean(wmatch[m]>=20):.1%}, 폭/2+6>=거리 {np.mean(wmatch[m]/2+6>=dp[m]):.1%}")
# 후보 도로 중의성: 12m 안 평행 도로 선 수
d12 = par & (dd <= 12)
nline = []
for r, v in zip(ii2[has12][:, :], d12[has12]):
    nline.append(len(set(Rr[r[v]].tolist())))
nline = np.array(nline)
print(f"12m 안 평행 도로가 있는 표본 {has12.sum():,}: 후보 선(레코드) 수 1개 {np.mean(nline==1):.1%}, 2개 {np.mean(nline==2):.1%}, 3개+ {np.mean(nline>=3):.1%}")

# 3) 도로 쪽에서 본 좌우 인도 유무
print("\n== 도로 쪽에서 본 인도 유무 (15m 간격 도로 표본, 임계 W = max(12, 폭/2+8))")
Sp5, Sd5, Sr5, _, _ = load("sidewalk", 5.0)
keep_mask = np.array(sa["KIND"])[Sr5] == "SWK001"
Sp5, Sd5 = Sp5[keep_mask], Sd5[keep_mask]
ts = cKDTree(Sp5)
sel = np.arange(0, len(Rp), 5)
d0, _ = ts.query(Rp[sel], workers=-1, distance_upper_bound=40)
near = sel[np.isfinite(d0)]
print("도로 표본", len(sel), "40m 안 인도 표본 있는 도로 표본", len(near), time.time() - T0, flush=True)
dq, iq = ts.query(Rp[near], k=40, distance_upper_bound=40, workers=-1)
valid = np.isfinite(dq)
iq2 = np.where(valid, iq, 0)
cos2 = np.abs((Sd5[iq2] * Rd[near][:, None, :]).sum(2))
par2 = valid & (cos2 > np.cos(np.radians(20)))
W = np.maximum(12, rw[Rr[near]] / 2 + 8)
inw = par2 & (dq <= W[:, None])
nx, ny = -Rd[near, 1], Rd[near, 0]
dx = Sp5[iq2, 0] - Rp[near, 0][:, None]; dy = Sp5[iq2, 1] - Rp[near, 1][:, None]
side = dx * nx[:, None] + dy * ny[:, None]
left = (inw & (side > 0)).any(1); right = (inw & (side < 0)).any(1)
tot_len = len(sel) * 15.0 / 1000
print(f"도로 총 표본 길이 {tot_len:,.0f} km 중 인도(한쪽 이상) 있는 길이 {(left|right).sum()*15/1000:,.0f} km ({(left|right).sum()/len(sel):.1%}), 양쪽 {(left&right).sum()*15/1000:,.0f} km, 한쪽 {(left^right).sum()*15/1000:,.0f} km")
Rw = rw[Rr[near]]
sample_w = rw[Rr[sel]]
for a, b in [(0, 4), (4, 8), (8, 12), (12, 16), (16, 20), (20, 25), (25, 100)]:
    m = (Rw >= a) & (Rw < b)
    tot = ((sample_w >= a) & (sample_w < b)).sum()
    if tot:
        print(f"  폭 {a:>2}~{b:<3}: 도로 {tot*15/1000:7,.0f} km  인도 있음 {(left|right)[m].sum()/tot:.1%}  양쪽 {(left&right)[m].sum()/tot:.1%}  한쪽 {(left^right)[m].sum()/tot:.1%}")
# 시험구역 안
inb = (Rp[near, 0] >= bx0) & (Rp[near, 0] <= bx1) & (Rp[near, 1] >= by0) & (Rp[near, 1] <= by1)
inb_all = (Rp[sel, 0] >= bx0) & (Rp[sel, 0] <= bx1) & (Rp[sel, 1] >= by0) & (Rp[sel, 1] <= by1)
print(f"시험구역 도로 {inb_all.sum()*15/1000:,.0f} km 중 인도 있음 {(left|right)[inb].sum()/inb_all.sum():.1%}, 양쪽 {(left&right)[inb].sum()/inb_all.sum():.1%}, 한쪽 {(left^right)[inb].sum()/inb_all.sum():.1%}")

# 인도가 12m 고정 임계에서 놓치는 길이
print("\n== 도로에서 떨어진 인도 분석")
off = np.load(os.path.join(TMP, "off.npz"))
off_rec = set(off["idx"].tolist())
is_off = np.array([r in off_rec for r in Sr])
# 위 off 정의는 파트 단위로 저장되었으나 레코드와 파트 대부분 1:1
print("off 표본", is_off.sum(), "표본 x10m km", is_off.sum() * 10 / 1000)
med_d = collections.defaultdict(list)
for sl, dv, dpv, w in zip(Sl[is_off], d1[is_off], dp[is_off], wmatch[is_off]):
    med_d[sl].append((dv, dpv, w))
cat = collections.Counter(); km = collections.Counter()
for sl, v in med_d.items():
    a = np.array(v)
    md = np.median(a[:, 0]); mp = np.median(a[:, 1])
    wm = np.median(a[:, 2][np.isfinite(a[:, 1]) & (a[:, 1] <= 30)]) if (a[:, 1] <= 30).any() else 0
    frac30 = np.mean(a[:, 1] <= 30)
    if frac30 >= 0.8 and wm >= 15:
        c = "A 넓은도로(폭>=15) 평행 30m안"
    elif frac30 >= 0.8:
        c = "B 평행 30m안(폭<15)"
    elif md > 50:
        c = "D 도로 50m 밖(중앙값)"
    elif md > 30:
        c = "C 30~50m"
    else:
        c = "E 기타(비평행 30m안 등)"
    cat[c] += 1; km[c] += SL[sl]
for c in sorted(cat):
    print(f"  {c}: {cat[c]:,}개 {km[c]/1000:,.1f} km")
print("총", sum(cat.values()), round(sum(km.values()) / 1000, 1))

# 시험구역 안 분포
ib = (Sp[:, 0] >= bx0) & (Sp[:, 0] <= bx1) & (Sp[:, 1] >= by0) & (Sp[:, 1] <= by1)
print(f"시험구역 안 인도 표본 {ib.sum()*10/1000:,.0f} km, off 표본 {(ib & is_off).sum()*10/1000:,.1f} km")
# off 격자 500m 상위
g = np.floor(Sp[is_off] / 500).astype(int)
cnt = collections.Counter(map(tuple, g.tolist()))
tf = Transformer.from_crs(5179, 4326, always_xy=True)
print("off 표본 500m 격자 상위")
for (a, b), n in cnt.most_common(12):
    lo, la = tf.transform((a + .5) * 500, (b + .5) * 500)
    print(f"  ({la:.4f},{lo:.4f}) {n*10/1000:.1f} km")

# 인도끼리 연결
print("\n== off 선 끝점의 연결 (1m)")
recs = read_shp(FILES["sidewalk"], clip=True)
ep = []; own = []; isoff = []
for rec, parts in recs:
    for p in parts:
        ep.append(p[0]); ep.append(p[-1]); own += [len(own) // 2, len(own) // 2]; isoff += [rec in off_rec, rec in off_rec]
ep = np.array(ep); own = np.array(own); isoff = np.array(isoff)
t = cKDTree(ep)
gs = t.query_ball_point(ep[isoff], 1.0, workers=-1)
n_to_any = sum(1 for g, o in zip(gs, own[isoff]) if any(own[j] != o for j in g))
n_to_off = sum(1 for g, o in zip(gs, own[isoff]) if any(own[j] != o and isoff[j] for j in g))
print(f"off 끝점 {isoff.sum():,}: 다른 인도 끝점 1m 안 {n_to_any/isoff.sum():.1%}, 다른 off 끝점 1m 안 {n_to_off/isoff.sum():.1%}")
# 도로 쪽 근접
d_road_end, _ = tr.query(ep[isoff], workers=-1)
print(f"off 끝점 도로까지 <=5m {np.mean(d_road_end<=5):.1%} <=15 {np.mean(d_road_end<=15):.1%} <=30 {np.mean(d_road_end<=30):.1%}")
print("끝", time.time() - T0)

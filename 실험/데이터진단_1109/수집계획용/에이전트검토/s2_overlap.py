"""계획서 겹침 수치 재현. 임시 폴더에서 실행, 원본은 읽기만."""
import collections
import sys
import time
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, r"C:\Users\seungjun\AppData\Local\Temp\plan_review_Br6p2s")
from lib_shp import *

sys.stdout.reconfigure(encoding="utf-8")
T0 = time.time()


def sample(pts, step):
    seg = np.hypot(*np.diff(pts, axis=0).T)
    cum = np.r_[0, np.cumsum(seg)]
    if cum[-1] <= 0:
        return pts[:1].copy(), 0.0
    t = np.r_[np.arange(0, cum[-1], step), cum[-1]]
    return np.c_[np.interp(t, cum, pts[:, 0]), np.interp(t, cum, pts[:, 1])], float(cum[-1])


L = {}
for k, base in FILES.items():
    recs = read_shp(base, clip=True)
    per = []
    for idx, parts in recs:
        for p in parts:
            s, l = sample(p, 3.0 if k == "road" else 10.0)
            per.append((idx, s, p[[0, -1]], l, p))
    L[k] = dict(per=per, pts=np.vstack([x[1] for x in per]), km=sum(x[3] for x in per) / 1000, n=len(per), base=base,
                ids=set(x[0] for x in per))
    print(f"{k}: bbox lines {len(per):,}  km {L[k]['km']:,.1f}  samples {len(L[k]['pts']):,}  t={time.time()-T0:.0f}s", flush=True)

road = cKDTree(L["road"]["pts"])
print("\n== 표본점 비율: 도로중심선까지 거리")
for k in ["sidewalk", "foot", "bike", "seg"]:
    d, _ = road.query(L[k]["pts"], workers=-1)
    L[k]["d"] = d
    print(f"{k}: <=2m {np.mean(d<=2):.2%}  <=12m {np.mean(d<=12):.2%}  12~30 {np.mean((d>12)&(d<=30)):.2%}  30~50 {np.mean((d>30)&(d<=50)):.2%}  >50 {np.mean(d>50):.2%}  median {np.median(d):.2f}")

print("\n== 길이 가중(선별 표본 평균 x 길이)")
for k in ["sidewalk", "foot", "bike", "seg"]:
    tot = 0.0; t2 = 0.0; t12 = 0.0
    pos = 0
    for idx, s, ep, l, p in L[k]["per"]:
        d = L[k]["d"][pos:pos+len(s)]
        pos += len(s)
        tot += l; t2 += l*np.mean(d<=2); t12 += l*np.mean(d<=12)
    print(f"{k}: 길이가중 <=2m {t2/tot:.2%} <=12m {t12/tot:.2%}  총 {tot/1000:,.0f} km")

print("\n== 도로에서 떨어진 인도 (표본 80% 이상 12m 초과)")
pos = 0
off = []
for idx, s, ep, l, p in L["sidewalk"]["per"]:
    d = L["sidewalk"]["d"][pos:pos+len(s)]
    pos += len(s)
    if np.mean(d > 12) >= 0.8:
        off.append((idx, ep, l, p))
de, _ = road.query(np.vstack([x[1] for x in off]), workers=-1)
print(f"off-road lines {len(off):,}  km {sum(x[2] for x in off)/1000:,.1f}  ends<=5m {np.mean(de<=5):.2%}  <=15m {np.mean(de<=15):.2%}")
np.savez(r"C:\Users\seungjun\AppData\Local\Temp\plan_review_Br6p2s\off.npz", idx=np.array([x[0] for x in off]), l=np.array([x[2] for x in off]))

print("\n== 꼭짓점 일치")
def verts(k):
    return np.vstack([x[4] for x in L[k]["per"]])
vs = verts("sidewalk")
vk = verts("bike"); vf = verts("foot")
print("sidewalk verts", len(vs), "bike verts", len(vk), "foot verts", len(vf))
t_vs = cKDTree(vs)
for name, v in [("bike", vk), ("foot", vf)]:
    d, _ = t_vs.query(v, workers=-1)
    print(f"{name}: 인도 꼭짓점과 거리 <=1cm {np.mean(d<=0.01):.2%}  <=0.5m {np.mean(d<=0.5):.2%}  (반올림 격자 대신 거리)")
    r = 0.01
    s = set(map(tuple, np.round(vs / r).astype(np.int64)))
    hit = np.mean([tuple(x) in s for x in np.round(v / r).astype(np.int64)])
    print(f"   1cm 반올림 격자 일치 {hit:.2%}")
t_s = cKDTree(L["sidewalk"]["pts"])
for name in ("foot", "bike"):
    d, _ = t_s.query(L[name]["pts"], workers=-1)
    print(f"{name} -> 인도 표본 12m 안 {np.mean(d<=12):.2%}, 2m 안 {np.mean(d<=2):.2%}, 중앙값 {np.median(d):.2f}")
d, _ = cKDTree(L["foot"]["pts"]).query(L["sidewalk"]["pts"], workers=-1)
print(f"sidewalk -> 보도중심선 12m 안 {np.mean(d<=12):.2%}")

print("\n== 도로 끝점 일치")
rp = L["road"]["per"]
ep = np.vstack([x[2] for x in rp])
owner = np.repeat(np.arange(len(rp)), 2)
print("끝점", len(ep))
t = cKDTree(ep)
gs = t.query_ball_point(ep, 0.01, workers=-1)
n_pass = 0; n_excl_self = 0
unm = np.zeros(len(ep), bool)
for i, g in enumerate(gs):
    if len(g) > 1:
        n_pass += 1
    if any(owner[j] != owner[i] for j in g):
        n_excl_self += 1
    else:
        unm[i] = True
print(f"1cm 안 다른 끝점 있는 비율(원 코드) {n_pass/len(ep):.2%}  안 만나는 {len(ep)-n_pass:,}")
print(f"자기 선 끝점 제외 {n_excl_self/len(ep):.2%}  안 만나는 {unm.sum():,}")

# 다른 선의 중간 꼭짓점 일치
all_v = []; owner_v = []; is_end = []
for j, x in enumerate(rp):
    p = x[4]
    all_v.append(p); owner_v.append(np.full(len(p), j))
    e = np.zeros(len(p), bool); e[0] = True; e[-1] = True; is_end.append(e)
all_v = np.vstack(all_v); owner_v = np.concatenate(owner_v); is_end = np.concatenate(is_end)
print("road verts", len(all_v))
tv = cKDTree(all_v)
idx_un = np.where(unm)[0]
gs2 = tv.query_ball_point(ep[idx_un], 0.01, workers=-1)
mid = 0
for ii, g in zip(idx_un, gs2):
    if any(owner_v[j] != owner[ii] and not is_end[j] for j in g):
        mid += 1
print(f"안 만나는 끝점 중 다른 선 중간 꼭짓점 1cm 안 {mid}")

# 다른 선까지 거리: 세그먼트 기반
segs_a = []; segs_b = []; seg_own = []
for j, x in enumerate(rp):
    p = x[4]
    segs_a.append(p[:-1]); segs_b.append(p[1:]); seg_own.append(np.full(len(p)-1, j))
segs_a = np.vstack(segs_a); segs_b = np.vstack(segs_b); seg_own = np.concatenate(seg_own)
print("segments", len(segs_a))
# 격자 색인(50m)
cs = 50.0
cell = collections.defaultdict(list)
for i, (a, b) in enumerate(zip(segs_a, segs_b)):
    l = np.hypot(*(b - a))
    k = max(1, int(l / (cs / 2)))
    seen = set()
    for t_ in np.linspace(0, 1, k + 1):
        c = (int((a[0] + t_ * (b[0] - a[0])) // cs), int((a[1] + t_ * (b[1] - a[1])) // cs))
        if c not in seen:
            seen.add(c); cell[c].append(i)
print("격자 끝", time.time()-T0, flush=True)

def dist_other(pt, own):
    cx, cy = int(pt[0] // cs), int(pt[1] // cs)
    cand = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            cand.extend(cell.get((cx + dx, cy + dy), []))
    if not cand:
        return np.inf
    cand = np.array(list(set(cand)))
    cand = cand[seg_own[cand] != own]
    if len(cand) == 0:
        return np.inf
    a = segs_a[cand]; b = segs_b[cand]
    ab = b - a
    t = np.clip(((pt - a) * ab).sum(1) / np.maximum((ab * ab).sum(1), 1e-12), 0, 1)
    return float(np.min(np.hypot(*(a + (ab.T * t).T - pt).T)))

dist = np.array([dist_other(ep[ii], owner[ii]) for ii in idx_un])
print(f"안 만나는 끝점 -> 다른 선까지: 1m 안 {np.mean(dist<=1):.2%} ({(dist<=1).sum()})  2m {np.mean(dist<=2):.2%} ({(dist<=2).sum()})  5m {np.mean(dist<=5):.2%} ({(dist<=5).sum()})  10m {np.mean(dist<=10):.2%}  20m {np.mean(dist<=20):.2%}")
# 다른 끝점까지
gs3 = t.query(ep[idx_un], k=2, workers=-1)[0][:, 1]
print(f"안 만나는 끝점 -> 다른 끝점: 1m 안 {(gs3<=1).sum()}  2m {(gs3<=2).sum()}")

print("\n== 도로 속성")
n = dbf_columns(FILES["road"], ["RDDV", "DVYN", "RDLN", "RVWD", "ONSD", "PVQT", "NAME", "RDNU", "REST", "SCLS", "RDNM"])
lens = np.zeros(394562)
for x in rp:
    lens[x[0]] += x[3]
np.save(r"C:\Users\seungjun\AppData\Local\Temp\plan_review_Br6p2s\road_len.npy", lens)
for k in ["RDDV", "DVYN", "ONSD", "PVQT", "SCLS", "REST"]:
    c = collections.Counter(n[k])
    w = collections.defaultdict(float)
    for v, l in zip(n[k], lens):
        w[v] += l
    print(k, "건수 상위", [(a, b, f"{b/len(n[k]):.1%}") for a, b in c.most_common(8)])
    print("   길이 상위", [(a, f"{b/1000:,.0f}km", f"{b/lens.sum():.1%}") for a, b in sorted(w.items(), key=lambda z: -z[1])[:8]])
for k in ["RDLN", "RVWD"]:
    v = np.array([float(x) if x not in ("", None) else np.nan for x in n[k]])
    print(k, f"NaN {np.isnan(v).mean():.1%}  0이하 {(v<=0).mean():.2%}  양수 {(v>0).mean():.2%}  길이 가중 양수 {lens[v>0].sum()/lens.sum():.2%}", "분위(양수)", np.percentile(v[v>0], [5, 25, 50, 75, 95, 99]).round(2) if (v>0).any() else "")
    print("   값 상위", collections.Counter(n[k]).most_common(10))
print("NAME 채움", np.mean([bool(x) for x in n["NAME"]]), "RDNU 채움", np.mean([bool(x) for x in n["RDNU"]]), "RDNM 채움", np.mean([bool(x) for x in n["RDNM"]]))

for key, base, cols in [("sidewalk", FILES["sidewalk"], ["KIND", "QUAL", "BYYN", "SCLS", "WIDT"]), ("foot", FILES["foot"], ["PMTR_SE", "MESRMTH_SE"]), ("bike", FILES["bike"], ["BCYKND_SE", "PMTR_SE"])]:
    m = dbf_columns(base, cols)
    ids = sorted(L[key]["ids"])
    print(key, "대상 레코드", len(ids))
    for c in cols:
        if c == "WIDT":
            v = np.array([float(m[c][i]) if m[c][i] else np.nan for i in ids])
            print("  WIDT 양수비", np.mean(v > 0), "NaN", np.isnan(v).mean(), "분위", np.nanpercentile(v, [5, 25, 50, 75, 95]))
        else:
            print(" ", c, collections.Counter(m[c][i] for i in ids).most_common(10))

print("끝", time.time()-T0)

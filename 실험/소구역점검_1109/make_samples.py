"""수집계획 3장 가 영상 확인용 표본. 5월 사본, 읽기 전용.

독립 보행로: spot_check2.py의 정의로 3,362개 506.4km와 나머지 286.4km 1,398묶음을 재현한 뒤,
나머지 길이 위에서 균등하게 40점을 뽑는다(길이 비례).
도로: 두 소구역 안에서 포장 여부 x 도로 폭으로 나눠 칸마다 3점을 뽑는다(칸 안에서는 길이 비례).
"""
import collections
import json
import os
import sys

import numpy as np
from pyproj import Transformer
from scipy.spatial import cKDTree

HERE = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\소구역점검_1109"
sys.path.insert(0, r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\데이터진단_1109\수집계획용\에이전트검토")
from lib_shp import FILES, dbf_columns, read_shp

sys.stdout.reconfigure(encoding="utf-8")
out = open(os.path.join(HERE, "표본추출.out"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out.write(s + "\n")
    out.flush()


SEED = 20261109
rng = np.random.default_rng(SEED)
to5179 = Transformer.from_crs(4326, 5179, always_xy=True)
to4326 = Transformer.from_crs(5179, 4326, always_xy=True)
BOXES = {}
for name, (la0, la1, lo0, lo1) in {"제주시": (33.46, 33.54, 126.46, 126.58), "서귀포시": (33.24, 33.27, 126.53, 126.60)}.items():
    x0, y0 = to5179.transform(lo0, la0)
    x1, y1 = to5179.transform(lo1, la1)
    BOXES[name] = (x0, y0, x1, y1)


def region_of(x, y):
    for name, (x0, y0, x1, y1) in BOXES.items():
        if x0 <= x <= x1 and y0 <= y <= y1:
            return name
    return "그 외"


def sample(pts, step):
    cum = np.r_[0, np.cumsum(np.hypot(*np.diff(pts, axis=0).T))]
    if cum[-1] <= 0:
        return pts[:1], 0.0
    t = np.r_[np.arange(0, cum[-1], step), cum[-1]]
    return np.c_[np.interp(t, cum, pts[:, 0]), np.interp(t, cum, pts[:, 1])], float(cum[-1])


def near_part(pts, c, radius=350.0):
    """표시용: 점 c에서 radius 안에 있는 꼭짓점 구간만 남긴다."""
    keep = np.hypot(*(pts - c).T) <= radius
    return pts[keep].round(2).tolist() if keep.sum() >= 2 else pts.round(2).tolist()


def lonlat(x, y):
    lo, la = to4326.transform(float(x), float(y))
    return round(lo, 6), round(la, 6)


# 도로
ra = dbf_columns(FILES["road"], ["RVWD", "PVQT", "RDDV", "RDLN"])
wid = np.array([float(v or 0) for v in ra["RVWD"]])
pv = np.array(ra["PVQT"])
S3, W3, R3, road_parts = [], [], [], {}
for rec, parts in read_shp(FILES["road"], clip=True):
    for p in parts:
        s, _ = sample(p, 3.0)
        S3.append(s)
        W3.append(np.full(len(s), wid[rec]))
        R3.append(np.full(len(s), rec))
        road_parts.setdefault(rec, []).append(p)
S3, W3, R3 = np.vstack(S3), np.concatenate(W3), np.concatenate(R3)
tr3 = cKDTree(S3)
log("도로 3m 표본", len(S3))
log("포장 코드(선 수)", collections.Counter(pv.tolist()).most_common())

# 독립 보행로
sa = dbf_columns(FILES["sidewalk"], ["KIND"])
ind = []
for rec, parts in read_shp(FILES["sidewalk"], clip=True):
    for p in parts:
        s, L = sample(p, 10.0)
        d, _ = tr3.query(s)
        if np.mean(d > 12) >= 0.8:
            ind.append((rec, p, s, L))
log(f"[재현] 도로에서 떨어진 인도 {len(ind):,}개 {sum(x[3] for x in ind)/1000:.1f}km (기대 3,362, 506.4)")
wide_km, rest = 0.0, []
for x in ind:
    near = tr3.query_ball_point(x[2], 30)
    if np.mean([bool(g) and W3[g].max() >= 15 for g in near]) >= 0.8:
        wide_km += x[3] / 1000
    else:
        rest.append(x)
rest_km = sum(x[3] for x in rest) / 1000
log(f"[재현] 폭 15m 이상 도로 30m 안 {wide_km:.1f}km, 나머지 {len(rest):,}개 {rest_km:.1f}km (기대 220.0, 286.4)")
ends = np.vstack([x[1][[0, -1]] for x in rest])
parent = list(range(len(rest)))


def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a


for i, j in cKDTree(ends).query_pairs(2.0):
    parent[find(i // 2)] = find(j // 2)
groups = collections.defaultdict(list)
for i in range(len(rest)):
    groups[find(i)].append(i)
glen = {g: sum(rest[i][3] for i in m) for g, m in groups.items()}
log(f"[재현] 묶음 {len(groups):,}개 (기대 1,398)")
for lo, hi, nm in [(0, 100, "100m 미만"), (100, 300, "100~300m"), (300, 500, "300~500m"), (500, 1000, "500m~1km"), (1000, 1e12, "1km 이상")]:
    s = [g for g, v in glen.items() if lo <= v < hi]
    log(f"  묶음 길이 {nm}: {len(s):,}개 {sum(glen[g] for g in s)/1000:.1f}km ({sum(glen[g] for g in s)/1000/rest_km:.1%})")
kind_km = collections.Counter()
reg_km = collections.Counter()
for x in rest:
    kind_km[sa["KIND"][x[0]]] += x[3] / 1000
    mid = x[1][len(x[1]) // 2]
    reg_km[region_of(*mid)] += x[3] / 1000
closed = [x for x in rest if np.hypot(*(x[1][0] - x[1][-1])) <= 1.0]
log(f"  닫힌 선(시작·끝 1m 안) {len(closed):,}개 {sum(x[3] for x in closed)/1000:.1f}km ({sum(x[3] for x in closed)/1000/rest_km:.1%})")
log("  KIND별 km", {k: round(v, 1) for k, v in kind_km.most_common()})
log("  지역별 km", {k: round(v, 1) for k, v in reg_km.most_common()})

P = np.vstack([x[2] for x in rest])
O = np.concatenate([np.full(len(x[2]), i) for i, x in enumerate(rest)])
samples = []
for n, k in enumerate(rng.choice(len(P), 40, replace=False)):
    i = int(O[k])
    g = find(i)
    c = P[k]
    lo, la = lonlat(*c)
    d, _ = tr3.query(c)
    samples.append({
        "id": f"W{n + 1:02d}", "type": "보행로", "region": region_of(*c), "lon": lo, "lat": la, "x": round(float(c[0]), 2), "y": round(float(c[1]), 2),
        "kind": sa["KIND"][rest[i][0]], "group_km": round(glen[g] / 1000, 3), "road_dist_m": round(float(d), 1),
        "lines": [near_part(rest[m][1], c) for m in groups[g] if (np.hypot(*(rest[m][1] - c).T) <= 350).any()],
    })

# 도로
WB = [(0, 3, "폭 3m 미만"), (3, 6, "폭 3~6m"), (6, 15, "폭 6~15m"), (15, 1e9, "폭 15m 이상")]
PAVE = [("비포장", lambda r: r == "RDQ005"), ("포장", lambda r: r != "RDQ005")]
for name, (x0, y0, x1, y1) in BOXES.items():
    ib = np.where((S3[:, 0] >= x0) & (S3[:, 0] <= x1) & (S3[:, 1] >= y0) & (S3[:, 1] <= y1))[0]
    log(f"\n[{name}] 도로 표본 칸별 길이")
    for pn, pf in PAVE:
        pm = np.array([pf(r) for r in pv[R3[ib]]])
        for lo, hi, wn in WB:
            cell = ib[pm & (W3[ib] >= lo) & (W3[ib] < hi)]
            km = len(cell) * 3 / 1000
            if km < 1.0:
                log(f"  {pn} {wn}: {km:.1f}km  (1km 미만, 뽑지 않음)")
                continue
            log(f"  {pn} {wn}: {km:.1f}km")
            taken, tries = [], 0
            while len(taken) < 3 and tries < 500:
                tries += 1
                k = int(rng.choice(cell))
                if int(R3[k]) not in [int(R3[t]) for t in taken]:
                    taken.append(k)
            for k in taken:
                c = S3[k]
                rec = int(R3[k])
                lo_, la_ = lonlat(*c)
                samples.append({
                    "id": f"R{sum(1 for s in samples if s['type'] == '도로') + 1:02d}", "type": "도로", "region": name, "lon": lo_, "lat": la_, "x": round(float(c[0]), 2), "y": round(float(c[1]), 2),
                    "stratum": f"{pn} {wn}", "pvqt": str(pv[rec]), "width_m": float(wid[rec]), "rddv": ra["RDDV"][rec], "lanes": ra["RDLN"][rec],
                    "lines": [near_part(p, c) for p in road_parts[rec]],
                })
json.dump({"seed": SEED, "samples": samples}, open(os.path.join(HERE, "samples.json"), "w", encoding="utf-8"), ensure_ascii=False)

# 1km 이상 묶음은 표본이 아니라 전수로 본다
long_groups = []
for g, m in sorted(((g, m) for g, m in groups.items() if glen[g] >= 1000), key=lambda t: -glen[t[0]]):
    pts = np.vstack([rest[i][1] for i in m])
    closed_km = sum(rest[i][3] for i in m if np.hypot(*(rest[i][1][0] - rest[i][1][-1])) <= 1.0) / 1000
    c = pts.mean(0)
    lo, la = lonlat(*c)
    long_groups.append({
        "id": f"L{len(long_groups) + 1:02d}", "km": round(glen[g] / 1000, 2), "closed_km": round(closed_km, 2), "n_lines": len(m), "lon": lo, "lat": la,
        "region": region_of(*c), "kind": sorted({sa["KIND"][rest[i][0]] for i in m}),
        "lines": [[[round(float(a)), round(float(b))] for a, b in np.vstack([rest[i][1][::10], rest[i][1][-1:]])] for i in m],
    })
json.dump(long_groups, open(os.path.join(HERE, "long_groups.json"), "w", encoding="utf-8"), ensure_ascii=False)
log("1km 이상 묶음", len(long_groups), "개", round(sum(x["km"] for x in long_groups), 1), "km, 닫힌 선", round(sum(x["closed_km"] for x in long_groups), 1), "km")
log("\n표본", collections.Counter(s["type"] for s in samples))

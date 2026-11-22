"""면 자료가 없는 입체 교차(R13 같은 경우)를 찾는 전수 검사. 원본은 읽기만 한다.
차수 4 이상 노드에서 간선을 직진 쌍으로 묶어, 두 직진 축이 교차하고 그중 한 축이 넓은 도로(폭 15m 이상 또는 분리대 있음)인 노드를 후보로 본다.
실행: py -I check_grade2.py
결과: 입체점검2.out, 입체후보2.csv, 입체위치2.json
"""
import collections
import csv
import json
import os
import random
import sys

import numpy as np
from pyproj import Transformer

HERE = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\새그래프_1110"
sys.path.insert(0, r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\데이터진단_1109\수집계획용\에이전트검토")
from lib_shp import dbf_columns, read_shp

sys.stdout.reconfigure(encoding="utf-8")
out = open(os.path.join(HERE, "입체점검2.out"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out.write(s + "\n")
    out.flush()


RAW = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본"
N3 = os.path.join(RAW, "국토정보맵", "연속수치지도_제주_20261109", "풀기")
ROAD = os.path.join(N3, "N3L_A0020000", "N3L_A0020000")
to4326 = Transformer.from_crs(5179, 4326, always_xy=True)
d = np.load(os.path.join(HERE, "그래프_새자료.npz"))
xy, A, B, narrow, island, rec, line, ea, eb = d["xy"], d["A"], d["B"], d["narrow"], d["island"], d["rec"], d["line"], d["a"], d["b"]
N = len(xy)
final = ~narrow & ~island
lines = [p for r, parts in read_shp(ROAD, clip=False) for p in parts]
at = dbf_columns(ROAD, ["RVWD", "DVYN"])
wid = np.array([float(x or 0) for x in at["RVWD"]])
dv = np.array(at["DVYN"])
wide = (wid[rec] >= 15) | (dv[rec] == "CSU001")
log("DVYN 분포", collections.Counter(at["DVYN"]).most_common())

inc = collections.defaultdict(list)
for ei in np.where(final)[0].tolist():
    inc[int(A[ei])].append((ei, 0))
    inc[int(B[ei])].append((ei, 1))


def direction(ei, end):
    p = lines[line[ei]][ea[ei]:eb[ei] + 1]
    if end == 1:
        p = p[::-1]
    c = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]
    t = min(15.0, c[-1])
    q = np.array([np.interp(t, c, p[:, 0]), np.interp(t, c, p[:, 1])]) - p[0]
    return np.degrees(np.arctan2(q[1], q[0])) % 360


cands = []
for n, es in inc.items():
    if len(es) != 4:
        continue
    ang = [direction(e, s) for e, s in es]
    pairs = [((0, 1), (2, 3)), ((0, 2), (1, 3)), ((0, 3), (1, 2))]
    best = None
    for (a, b), (c, e) in pairs:
        dev1 = abs(((ang[a] - ang[b]) % 360) - 180)
        dev2 = abs(((ang[c] - ang[e]) % 360) - 180)
        if best is None or dev1 + dev2 < best[0]:
            best = (dev1 + dev2, dev1, dev2, (a, b), (c, e))
    _, dev1, dev2, p1, p2 = best
    if dev1 > 25 or dev2 > 25:
        continue
    axis = abs(((ang[p1[0]] - ang[p2[0]]) % 180))
    axis = min(axis, 180 - axis)
    if axis < 30:
        continue
    w1 = all(wide[es[i][0]] for i in p1)
    w2 = all(wide[es[i][0]] for i in p2)
    if not (w1 or w2):
        continue
    cands.append(dict(n=n, both=w1 and w2, wmin=[float(min(wid[rec[es[i][0]]] for i in p)) for p in (p1, p2)]))
log(f"차수 4 직진 교차 + 넓은 도로 축 후보 {len(cands):,}개, 두 축 모두 넓음 {sum(c['both'] for c in cands):,}개")


def inside(pt, rings):
    x, y = pt
    c = False
    for r in rings:
        for x0, y0, x1, y1 in zip(r[:-1, 0], r[:-1, 1], r[1:, 0], r[1:, 1]):
            if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
                c = not c
    return c


polys = []
kinds = dbf_columns(os.path.join(N3, "N3A_A0080000", "N3A_A0080000"), ["KIND"])["KIND"]
for rc, rings in read_shp(os.path.join(N3, "N3A_A0080000", "N3A_A0080000")):
    polys.append(("평면교차점" if kinds[rc] == "CRK001" else "입체교차점", rings))
for nm, base in [("교량", os.path.join(N3, "N3A_A0070000", "N3A_A0070000")), ("인터체인지", os.path.join(N3, "N3A_A0100000", "N3A_A0100000")), ("입체교차부", os.path.join(RAW, "브이월드", "입체교차부_30223", "풀기", "N3A_A0090000"))]:
    for rc, rings in read_shp(base):
        polys.append((nm, rings))
boxes = np.array([[np.vstack(r)[:, 0].min(), np.vstack(r)[:, 1].min(), np.vstack(r)[:, 0].max(), np.vstack(r)[:, 1].max()] for _, r in polys])
for c in cands:
    x, y = xy[c["n"]]
    hit = np.where((boxes[:, 0] <= x) & (boxes[:, 2] >= x) & (boxes[:, 1] <= y) & (boxes[:, 3] >= y))[0]
    c["in"] = sorted({polys[i][0] for i in hit.tolist() if inside((x, y), polys[i][1])})
cnt = collections.Counter(";".join(c["in"]) or "면 없음" for c in cands)
log("후보가 속한 면:", cnt.most_common())
none = [c for c in cands if not c["in"]]
log(f"면 없는 후보 {len(none)}개")

R13 = (911896, 1497196)
dist = sorted((float(np.hypot(*(xy[c['n']] - R13))), c["in"], c["wmin"], round(float(xy[c['n']][0])), round(float(xy[c['n']][1]))) for c in cands)[:1]
log("R13 표본에 가장 가까운 후보(거리 m, 속한 면, 축별 최소 폭, x, y):", dist)

with open(os.path.join(HERE, "입체후보2.csv"), "w", encoding="utf-8-sig", newline="") as f:
    wr = csv.writer(f)
    wr.writerow(["노드", "x", "y", "위도", "경도", "속한 면", "두 축 모두 넓음", "축1 최소폭", "축2 최소폭"])
    for c in cands:
        x, y = xy[c["n"]]
        lo, la = to4326.transform(x, y)
        wr.writerow([c["n"], round(float(x), 1), round(float(y), 1), round(la, 5), round(lo, 5), ";".join(c["in"]), int(c["both"]), c["wmin"][0], c["wmin"][1]])

random.seed(20261110)
pick = random.sample(none, min(20, len(none)))
items = [dict(id=f"N{i + 1:02d}", x=round(float(xy[c['n']][0])), y=round(float(xy[c['n']][1])), z=13, name=f"축 최소폭 {c['wmin'][0]:.0f}/{c['wmin'][1]:.0f}", kind="면 없음") for i, c in enumerate(pick)]
json.dump(items, open(os.path.join(HERE, "입체위치2.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(json.dumps([[i["id"], i["x"], i["y"], i["z"]] for i in items], separators=(",", ":")))
log("끝")

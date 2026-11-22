"""입체 구간 점검(계획서 3장 나)과 폭 제외 뒤 작은 요소 원인 확인. 원본은 읽기만 한다.
입체교차부·입체교차점·인터체인지·육교·교량 면 안의 분기 노드를 찾아 표본 목록을 만든다.
실행: py -I check_grade.py  (build_graph.py 뒤)
결과: 입체점검.out, 입체후보.csv
"""
import collections
import csv
import os
import sys

import numpy as np
from pyproj import Transformer
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

HERE = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\새그래프_1110"
sys.path.insert(0, r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\데이터진단_1109\수집계획용\에이전트검토")
from lib_shp import FILES, dbf_columns, dbf_fields, read_shp

sys.stdout.reconfigure(encoding="utf-8")
out = open(os.path.join(HERE, "입체점검.out"), "w", encoding="utf-8")


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
xy, A, B, L, rec, narrow, island, stair = d["xy"], d["A"], d["B"], d["L"], d["rec"], d["narrow"], d["island"], d["stair_len"]
N = len(xy)
final = ~narrow & ~island


def deg_of(mask):
    return np.bincount(A[mask], minlength=N) + np.bincount(B[mask], minlength=N)


deg_all, deg_final = deg_of(np.ones(len(A), bool)), deg_of(final)

# 1) 폭 제외 뒤 요소 수가 왜 늘었나: 5월과 새 자료의 폭 분포, 작은 요소
log("=== 폭 제외 뒤 작은 요소")
for nm, base in (("5월 사본", FILES["road"]), ("새 자료", ROAD)):
    w = np.array([float(x or 0) for x in dbf_columns(base, ["RVWD"])["RVWD"]])
    log(f"{nm}: 선 {len(w):,}, 폭 3m 미만 {(w < 3).sum():,} ({(w < 3).mean():.1%}), 분위(5,25,50,75,95) {np.percentile(w, [5, 25, 50, 75, 95]).round(1).tolist()}")
n, lab = connected_components(coo_matrix((np.ones(int(final.sum())), (A[final], B[final])), shape=(N, N)), directed=False)
Lc = np.bincount(lab[A[final]], weights=L[final], minlength=n)
m = int(Lc.argmax())
others = [c for c in np.where(Lc > 0)[0].tolist() if c != m]
log(f"새 자료 둘 다 제외: 주 요소 밖 조각 {len(others)}개 {sum(Lc[c] for c in others) / 1000:.1f}km")
for lo, hi, nm in [(0, 50, "50m 미만"), (50, 200, "50~200m"), (200, 1000, "200m~1km"), (1000, 5000, "1~5km"), (5000, 1e12, "5km 이상")]:
    s = [c for c in others if lo <= Lc[c] < hi]
    log(f"  {nm}: {len(s)}개 {sum(Lc[c] for c in s) / 1000:.1f}km")


def inside(pts, rings):
    x, y = pts[:, 0], pts[:, 1]
    c = np.zeros(len(pts), bool)
    for r in rings:
        for x0, y0, x1, y1 in zip(r[:-1, 0], r[:-1, 1], r[1:, 0], r[1:, 1]):
            if y0 != y1:
                c ^= ((y0 > y) != (y1 > y)) & (x < (x1 - x0) * (y - y0) / (y1 - y0) + x0)
    return c


def bdist(p, rings):
    """점 하나에서 면 경계까지의 거리."""
    best = np.inf
    for r in rings:
        a, b = r[:-1], r[1:]
        v = b - a
        t = np.clip(((p - a) * v).sum(1) / np.maximum((v * v).sum(1), 1e-9), 0, 1)
        best = min(best, float(np.hypot(*(a + t[:, None] * v - p).T).min()))
    return best


# 2) 면 자료
layers = [
    ("입체교차부", os.path.join(RAW, "브이월드", "입체교차부_30223", "풀기", "N3A_A0090000")),
    ("교차로", os.path.join(N3, "N3A_A0080000", "N3A_A0080000")),
    ("인터체인지", os.path.join(N3, "N3A_A0100000", "N3A_A0100000")),
    ("육교", os.path.join(N3, "N3A_A0063321", "N3A_A0063321")),
    ("교량", os.path.join(N3, "N3A_A0070000", "N3A_A0070000")),
]
order = np.argsort(xy[:, 0])
xs = xy[order, 0]
rows = []
for name, base in layers:
    n_, _, _, fields = dbf_fields(base)
    names = [f[0] for f in fields]
    log(f"\n=== {name} 항목 {names}")
    cols = [c for c in ("NAME", "KIND", "STRU", "SDWK", "SCLS", "ROAD", "BRDK", "CRKD") if c in names]
    at = dbf_columns(base, cols) if cols else {}
    for c in cols:
        if c != "NAME":
            log(f"  {c} 분포 {collections.Counter(at[c]).most_common(8)}")
    tot, hit = 0, 0
    for rc, rings in read_shp(base):
        allr = np.vstack(rings)
        x0, y0, x1, y1 = allr[:, 0].min(), allr[:, 1].min(), allr[:, 0].max(), allr[:, 1].max()
        ids = order[np.searchsorted(xs, x0):np.searchsorted(xs, x1, side="right")]
        ids = ids[(xy[ids, 1] >= y0) & (xy[ids, 1] <= y1)]
        tot += 1
        if len(ids) == 0:
            continue
        ins = ids[inside(xy[ids], rings)]
        ins = ins[deg_all[ins] > 0]
        if len(ins) == 0:
            continue
        j = ins[deg_all[ins] >= 3]
        deep = [int(v) for v in j.tolist() if bdist(xy[v], rings) >= 3]
        cx, cy = allr[:, 0].mean(), allr[:, 1].mean()
        lo, la = to4326.transform(cx, cy)
        tag = {c: at[c][rc] for c in cols}
        if j.size:
            hit += 1
        rows.append(dict(종류=name, 레코드=rc, 위도=round(la, 5), 경도=round(lo, 5), 면속성=";".join(f"{k}={v}" for k, v in tag.items() if v),
                         면안노드=len(ins), 분기노드=len(j), 경계3m안쪽분기=len(deep), 최대차수=int(deg_all[ins].max()),
                         폭제외뒤분기=int((deg_final[ins] >= 3).sum()), 가로세로m=f"{x1 - x0:.0f}x{y1 - y0:.0f}"))
    log(f"  면 {tot:,}개, 도로 노드가 안에 있는 면 {sum(1 for r in rows if r['종류'] == name):,}개, 분기 노드(차수 3 이상)가 있는 면 {hit:,}개")

with open(os.path.join(HERE, "입체후보.csv"), "w", encoding="utf-8-sig", newline="") as f:
    wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    wr.writeheader()
    wr.writerows(rows)
log(f"\n입체후보.csv {len(rows):,}행")
for r in rows:
    if r["종류"] in ("입체교차부", "인터체인지", "육교") or "CRK002" in r["면속성"]:
        log(r)
br = [r for r in rows if r["종류"] == "교량"]
log(f"\n교량 {len(br):,}개 중 경계 3m 안쪽 분기 있음 {sum(1 for r in br if r['경계3m안쪽분기'] > 0):,}개, 폭 제외 뒤에도 분기 {sum(1 for r in br if r['폭제외뒤분기'] > 0):,}개")
log("끝")

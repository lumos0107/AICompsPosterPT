"""계단 제외 효과와 소구역 안 입체 확인 대상 수를 잰다."""
import csv
import os
import sys

import numpy as np
from pyproj import Transformer
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

HERE = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\새그래프_1110"
sys.path.insert(0, r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\데이터진단_1109\수집계획용\에이전트검토")
from lib_shp import dbf_columns

sys.stdout.reconfigure(encoding="utf-8")
ROAD = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵\연속수치지도_제주_20261109\풀기\N3L_A0020000\N3L_A0020000"
d = np.load(os.path.join(HERE, "그래프_새자료.npz"))
xy, A, B, L, narrow, island, stair, rec = d["xy"], d["A"], d["B"], d["L"], d["narrow"], d["island"], d["stair_len"], d["rec"]
N = len(xy)
base = ~narrow & ~island
for name, m in [("둘 다 제외", base), ("+ 계단 면 안 1m 이상 간선 제외", base & (stair < 1)), ("+ 계단 면 안 5m 이상 간선 제외", base & (stair < 5))]:
    n, lab = connected_components(coo_matrix((np.ones(int(m.sum())), (A[m], B[m])), shape=(N, N)), directed=False)
    Lc = np.bincount(lab[A[m]], weights=L[m], minlength=n)
    print(f"{name}: 도로 {L[m].sum() / 1000:,.1f}km, 요소 {int((Lc > 0).sum())}, 주 요소 비율 {Lc.max() / L[m].sum():.2%}, 뺀 간선 {int((base & ~m).sum())}개 {L[base & ~m].sum() / 1000:.2f}km")

to5179 = Transformer.from_crs(4326, 5179, always_xy=True)
REG = {"제주시 시험구역": (33.46, 33.54, 126.46, 126.58), "서귀포시내": (33.24, 33.27, 126.53, 126.60)}
at = dbf_columns(ROAD, ["RVWD", "DVYN"])
wid = np.array([float(x or 0) for x in at["RVWD"]])
dv = np.array(at["DVYN"])
wide = (wid[rec] >= 15) | (dv[rec] == "CSU001")
deg = np.bincount(A[base], minlength=N) + np.bincount(B[base], minlength=N)
wdeg = np.bincount(A[base & wide], minlength=N) + np.bincount(B[base & wide], minlength=N)
rows = list(csv.DictReader(open(os.path.join(HERE, "입체후보2.csv"), encoding="utf-8-sig")))
rx = np.array([float(r["x"]) for r in rows])
ry = np.array([float(r["y"]) for r in rows])
for nm, (la0, la1, lo0, lo1) in REG.items():
    x0, y0 = to5179.transform(lo0, la0)
    x1, y1 = to5179.transform(lo1, la1)
    ib = (xy[:, 0] >= x0) & (xy[:, 0] <= x1) & (xy[:, 1] >= y0) & (xy[:, 1] <= y1)
    strict = (rx >= x0) & (rx <= x1) & (ry >= y0) & (ry <= y1)
    print(f"{nm}: 직진 교차 후보 {int(strict.sum())}개, 차수 4 이상이고 넓은 도로 간선 2개 이상인 노드(R13도 포함되는 넓은 조건) {int((ib & (deg >= 4) & (wdeg >= 2)).sum())}개")
P = np.array([911902, 1497204])
n = int(np.argmin(np.hypot(*(xy - P).T)))
print("R13 노드 넓은 조건 포함:", bool(deg[n] >= 4 and wdeg[n] >= 2))

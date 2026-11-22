"""잘못된 평면 연결로 판정한 곳의 노드와 붙은 간선을 출력한다. 끊는 방법을 곳마다 정하기 위한 자료."""
import os
import sys

import numpy as np

HERE = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\새그래프_1110"
sys.path.insert(0, r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\데이터진단_1109\수집계획용\에이전트검토")
from lib_shp import dbf_columns, read_shp

sys.stdout.reconfigure(encoding="utf-8")
RAW = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본"
N3 = os.path.join(RAW, "국토정보맵", "연속수치지도_제주_20261109", "풀기")
ROAD = os.path.join(N3, "N3L_A0020000", "N3L_A0020000")
d = np.load(os.path.join(HERE, "그래프_새자료.npz"))
xy, A, B, L, narrow, island, rec, line, ea, eb = d["xy"], d["A"], d["B"], d["L"], d["narrow"], d["island"], d["rec"], d["line"], d["a"], d["b"]
lines = [p for r, parts in read_shp(ROAD, clip=False) for p in parts]
at = dbf_columns(ROAD, ["RVWD", "DVYN", "NAME", "RDNM"])
deg = np.bincount(A, minlength=len(xy)) + np.bincount(B, minlength=len(xy))
BR = os.path.join(N3, "N3A_A0070000", "N3A_A0070000")
GD = os.path.join(RAW, "브이월드", "입체교차부_30223", "풀기", "N3A_A0090000")
bridges = {r: g for r, g in read_shp(BR)}
gd = {r: g for r, g in read_shp(GD)}
SITES = [("G0428 공항지하차도", gd[428]), ("B0056 제2태흥교", bridges[56]), ("B0074 동명교", bridges[74]), ("B0170 제6광령교", bridges[170]), ("B0190 제4광령교", bridges[190]),
         ("B0309 해안육교", bridges[309]), ("B0471 죽성육교", bridges[471]), ("B1231 우남육교", bridges[1231]), ("B1275 색달육교", bridges[1275]), ("B1295 이름 없음", bridges[1295])]


def inside(pts, rings):
    x, y = pts[:, 0], pts[:, 1]
    c = np.zeros(len(pts), bool)
    for r in rings:
        for x0, y0, x1, y1 in zip(r[:-1, 0], r[:-1, 1], r[1:, 0], r[1:, 1]):
            if y0 != y1:
                c ^= ((y0 > y) != (y1 > y)) & (x < (x1 - x0) * (y - y0) / (y1 - y0) + x0)
    return c


def show(name, n):
    print(f"\n{name} 노드 {n} ({xy[n][0]:.1f}, {xy[n][1]:.1f}) 차수 {int(deg[n])}")
    for ei in np.where((A == n) | (B == n))[0].tolist():
        p = lines[line[ei]][ea[ei]:eb[ei] + 1]
        if B[ei] == n:
            p = p[::-1]
        c = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]
        t = min(15.0, c[-1])
        q = np.array([np.interp(t, c, p[:, 0]), np.interp(t, c, p[:, 1])]) - p[0]
        r = rec[ei]
        print(f"  간선 {ei}: 방위 {np.degrees(np.arctan2(q[1], q[0])) % 360:5.0f}, 길이 {c[-1]:6.1f}m, 폭 {at['RVWD'][r]}, 분리대 {at['DVYN'][r]}, 폭미달 {int(narrow[ei])}, 이름 {at['NAME'][r] or '-'} / {at['RDNM'][r] or '-'}")


for name, rings in SITES:
    allr = np.vstack(rings)
    ids = np.where((xy[:, 0] >= allr[:, 0].min()) & (xy[:, 0] <= allr[:, 0].max()) & (xy[:, 1] >= allr[:, 1].min()) & (xy[:, 1] <= allr[:, 1].max()))[0]
    ins = ids[inside(xy[ids], rings)]
    for n in ins[deg[ins] >= 3].tolist():
        show(name, int(n))
show("R0013 애조로", int(np.argmin(np.hypot(*(xy - np.array([911902, 1497204])).T))))

"""check_signals.py의 무작위 도로 점은 간선마다 끝점을 더해 교차로 쪽으로 치우쳤다. 치우침 없는 추출로 제주 전체·도엽 안 값을 다시 잰다(비교용)."""
import os, sys, csv
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\데이터진단_1109\수집계획용\에이전트검토")
from lib_shp import read_shp
sys.stdout.reconfigure(encoding="utf-8")
G = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\새그래프_1110"
ROAD = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵\연속수치지도_제주_20261109\풀기\N3L_A0020000\N3L_A0020000"
g = np.load(os.path.join(G, "그래프_최종.npz"))
xy, A, B, main, line, a, b = g["xy"], g["A"], g["B"], g["main"], g["line"], g["a"], g["b"]
N = len(xy)
deg = np.bincount(A[main], minlength=N) + np.bincount(B[main], minlength=N)
tj = cKDTree(xy[deg >= 3])
lines = [p for r, parts in read_shp(ROAD, clip=False) for p in parts]
old, new = [], []
for e in np.where(main)[0].tolist():
    p = lines[line[e]][a[e]:b[e] + 1]
    c = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]
    if c[-1] <= 0: continue
    t0 = np.r_[np.arange(0, c[-1], 5.0), c[-1]]
    k = max(int(round(c[-1] / 5.0)), 1); t1 = (np.arange(k) + 0.5) * c[-1] / k
    old.append(np.c_[np.interp(t0, c, p[:, 0]), np.interp(t0, c, p[:, 1])])
    new.append(np.c_[np.interp(t1, c, p[:, 0]), np.interp(t1, c, p[:, 1])])
old, new = np.vstack(old), np.vstack(new)
rng = np.random.default_rng(20261110)
for nm, P in (("이전 방식", old), ("치우침 없음", new)):
    d = tj.query(P[rng.choice(len(P), 20000, replace=False)])[0]
    print(f"제주 전체 {nm}: " + ", ".join(f"{r}m 안 {(d <= r).mean():.1%}" for r in (10, 20, 30, 50)))
# 도엽 안(두 지역 상자): 신호1000 점의 도엽 범위 대신 지역별 점 외곽 상자로 근사
q = list(csv.DictReader(open(os.path.join(G, "신호1000.csv"), encoding="utf-8-sig")))
for ar in ("제주 도심", "서귀포시내"):
    Q = np.array([(float(r["x5179"]), float(r["y5179"])) for r in q if r["지역"] == ar])
    x0, y0 = Q.min(0); x1, y1 = Q.max(0)
    for nm, P in (("이전 방식", old), ("치우침 없음", new)):
        m = (P[:, 0] >= x0) & (P[:, 0] <= x1) & (P[:, 1] >= y0) & (P[:, 1] <= y1)
        d = tj.query(P[m][rng.choice(int(m.sum()), 5000, replace=False)])[0]
        print(f"{ar} 신호 점 외곽 상자 {nm}: " + ", ".join(f"{r}m 안 {(d <= r).mean():.1%}" for r in (10, 20, 30, 50)))

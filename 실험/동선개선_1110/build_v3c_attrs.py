"""노드 속성 2차 확장(2026-11-10 밤): 노드속성_v3b.csv(신호, 시설, 조명, 물가)에 보도·녹지·조용한 길을 더한다.
- 보도 sidewalk: 연속수치지도 인도 선(N3L_A0033320)을 5 m 간격 점으로 바꿔, 노드 20 m 안에 있으면 1.
  (인도의 75%가 도로 중심선 12 m 안, 폭 30 m 이상 도로는 중앙값 15 m라 20 m로 둠)
- 녹지 green: 도시공원 표준데이터(제주시) 중심에서 '같은 면적의 원 반지름 + 20 m' 안이면 1(공원 모양은 모름, 어림).
- 조용한 길 quiet: 노드가 놓인 도로(가장 가까운 실험 그래프 간선, 10 m 안)의 폭이 20 m 미만이면 1(20 m 이상 = 4차로 이상 큰길).
결과: 노드속성_v3c.csv(point_id, signal, facility_m, lit, water_m, sidewalk, green, quiet), 노드속성_v3c.out
실행: py -I build_v3c_attrs.py
"""
import csv
import math
import os
import re
import sys

import numpy as np
import pymysql
from pyproj import Transformer
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(EXP, "데이터진단_1109", "수집계획용", "에이전트검토"))
from lib_shp import read_shp, dbf_columns

sys.stdout.reconfigure(encoding="utf-8")
out = open(os.path.join(HERE, "노드속성_v3c.out"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    out.write(s + "\n")


RAW = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본"
fw = Transformer.from_crs(4326, 5179, always_xy=True)

pw = re.search(r'password="([^"]*)"', open(r"C:\Users\seungjun\Documents\claude_code\논문\데이터사이언스학회\04_실험\새그래프_만들기\build_v2b_graph.py", encoding="utf-8").read()).group(1)
con = pymysql.connect(host="localhost", user="root", password=pw, db="gildongmu_v3")
cur = con.cursor()
cur.execute("SELECT point_id, latitude, longitude FROM jeju_road_points")
P = np.array([(int(a), float(b), float(c)) for a, b, c in cur.fetchall()])
con.close()
X, Y = fw.transform(P[:, 2], P[:, 1])
N = np.c_[X, Y]
x0, y0 = N.min(0) - 500
x1, y1 = N.max(0) + 500

# 보도
S = []
base = os.path.join(RAW, "국토정보맵", "연속수치지도_제주_20261109", "풀기", "N3L_A0033320", "N3L_A0033320")
for r, parts in read_shp(base, clip=False):
    for p in parts:
        if p[:, 0].max() < x0 or p[:, 0].min() > x1 or p[:, 1].max() < y0 or p[:, 1].min() > y1:
            continue
        for a, b in zip(p[:-1], p[1:]):
            k = max(1, int(np.hypot(*(b - a)) // 5))
            for t in np.linspace(0, 1, k + 1):
                S.append(a + (b - a) * t)
S = np.array(S)
ds, _ = cKDTree(S).query(N)
sidewalk = (ds <= 20).astype(int)
log(f"보도 점 {len(S)}(범위 안), 노드 20 m 안 보도 {sidewalk.mean():.3f}")

# 녹지(공원)
pk = os.path.join(RAW, "공공데이터포털", "도시공원표준_제주특별자치도_제주시_도시공원정보", "도시공원표준_제주특별자치도_제주시_도시공원정보.csv")
rows = None
for enc in ("utf-8-sig", "cp949"):
    try:
        rows = list(csv.DictReader(open(pk, encoding=enc)))
        break
    except UnicodeDecodeError:
        continue
parks = []
for r in rows:
    try:
        la, lo, ar = float(r["위도"]), float(r["경도"]), float(r["공원면적"] or 0)
    except ValueError:
        continue
    px, py = fw.transform(lo, la)
    if x0 <= px <= x1 and y0 <= py <= y1:
        parks.append((px, py, math.sqrt(max(ar, 0) / math.pi) + 20.0))
parks = np.array(parks)
green = np.zeros(len(N), int)
tp = cKDTree(N)
for px, py, rad in parks:
    for i in tp.query_ball_point((px, py), rad):
        green[i] = 1
log(f"공원 {len(parks)}곳(범위 안), 노드 공원 범위 안 {green.mean():.3f}")

# 조용한 길(도로 폭)
ROAD = os.path.join(RAW, "국토정보맵", "연속수치지도_제주_20261109", "풀기", "N3L_A0020000", "N3L_A0020000")
g = np.load(os.path.join(EXP, "도심실험_1110", "그래프_도심_114칸.npz"))
main, rec, gl, ga, gb = g["main"], g["rec"], g["line"], g["a"], g["b"]
wid = np.array([float(x or 0) for x in dbf_columns(ROAD, ["RVWD"])["RVWD"]])
lines = [p for r, parts in read_shp(ROAD, clip=False) for p in parts]
pts, pw_ = [], []
for e in np.where(main)[0].tolist():   # 간선을 실제 선 모양대로 5 m 간격 점으로(중점만 쓰면 긴 간선 위 노드를 놓침)
    p = lines[gl[e]][ga[e]:gb[e] + 1]
    for a, b in zip(p[:-1], p[1:]):
        k = max(1, int(np.hypot(*(b - a)) // 5))
        for t in np.linspace(0, 1, k + 1):
            pts.append(a + (b - a) * t)
            pw_.append(wid[rec[e]])
de, ie = cKDTree(np.array(pts)).query(N)
w_node = np.array(pw_)[ie]
quiet = ((w_node < 20) | (de > 10)).astype(int)
log(f"노드 도로 폭 20 m 미만(조용한 길) {quiet.mean():.3f}, 가장 가까운 간선 10 m 넘는 노드 {(de > 10).mean():.3f}")

old = {int(r["point_id"]): r for r in csv.DictReader(open(os.path.join(HERE, "노드속성_v3b.csv"), encoding="utf-8"))}
with open(os.path.join(HERE, "노드속성_v3c.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["point_id", "signal", "facility_m", "lit", "water_m", "sidewalk", "green", "quiet"])
    for pid, s_, gr, q in zip(P[:, 0].astype(int), sidewalk, green, quiet):
        o = old[pid]
        w.writerow([pid, o["signal"], o["facility_m"], o["lit"], o["water_m"], s_, gr, q])
log("끝")

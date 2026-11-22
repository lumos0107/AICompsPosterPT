"""노드 속성 확장(2026-11-10 밤): 기존 노드속성_v3.csv(신호, 시설 거리)에 조명·물가 두 항목을 더한다.
- 조명: 1:1,000 수치지형도 조명(N1P_C0220000, 가로등·방범등 등) 점. 실험 범위 114칸 = 제주도심_95장 + 제주도심_북쪽19장.
  좌표 EPSG:5186 → 5179, 1 m 안 중복(도엽 경계) 하나로. lit = 노드 25 m 안에 조명 점이 있으면 1.
- 물가: 연속수치지도 해안선(N3L_E0080000)과 하천 중심선(N3L_E0020000), 5 m 간격 점으로 바꿔 노드까지 거리(m, 500 상한).
결과: 노드속성_v3b.csv(point_id, signal, facility_m, lit, water_m), 노드속성_v3b.out
실행: py -I build_v3b_attrs.py
"""
import csv
import glob
import math
import os
import re
import struct
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
out = open(os.path.join(HERE, "노드속성_v3b.out"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    out.write(s + "\n")


RAW = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵"
LIT_R, WATER_CAP = 25.0, 500.0


def shp_points(path):
    d = open(path, "rb").read()
    pos, o = 100, []
    while pos < len(d):
        _, clen = struct.unpack(">2i", d[pos:pos + 8])
        s = pos + 8
        o.append(struct.unpack("<2d", d[s + 4:s + 20]) if struct.unpack("<i", d[s:s + 4])[0] != 0 else None)
        pos = s + clen * 2
    return o


t5186 = Transformer.from_crs(5186, 5179, always_xy=True)
L, kinds = [], {}
dirs = sorted(glob.glob(os.path.join(RAW, "수치지형도_1000_표본", "제주도심_95장", "풀기", "*"))) + \
       sorted(glob.glob(os.path.join(RAW, "수치지형도_1000_표본", "제주도심_북쪽19장", "풀기", "*")))
nd = 0
for sd in dirs:
    base = os.path.join(sd, "N1P_C0220000")
    if not os.path.exists(base + ".shp"):
        continue
    nd += 1
    try:
        kind = dbf_columns(base, ["구분"])["구분"]
    except Exception:
        kind = [""] * len(shp_points(base + ".shp"))
    for q, k in zip(shp_points(base + ".shp"), kind):
        if q is None:
            continue
        x, y = t5186.transform(q[0], q[1])
        L.append((x, y))
        kinds[k] = kinds.get(k, 0) + 1
L = np.array(L)
keep = np.ones(len(L), bool)
for i, j in cKDTree(L).query_pairs(1.0):
    keep[max(i, j)] = False
L = L[keep]
log(f"조명 도엽 {nd}/{len(dirs)}, 조명 점 {len(L)} (1 m 중복 {int((~keep).sum())} 뺌), 구분 {kinds}")

W = []
for code in ("N3L_E0080000", "N3L_E0020000"):
    base = os.path.join(RAW, "연속수치지도_제주_20261109_추가", "풀기", code, code)
    n = 0
    for r, parts in read_shp(base, clip=False):
        for p in parts:
            seg = np.hypot(*np.diff(p, axis=0).T)
            for (a, b), l in zip(zip(p[:-1], p[1:]), seg):
                k = max(1, int(l // 5))
                for t in np.linspace(0, 1, k + 1):
                    W.append(a + (b - a) * t)
            n += 1
    log(f"{code}: 선 조각 {n}")
W = np.array(W)

pw = re.search(r'password="([^"]*)"', open(r"C:\Users\seungjun\Documents\claude_code\논문\데이터사이언스학회\04_실험\새그래프_만들기\build_v2b_graph.py", encoding="utf-8").read()).group(1)
con = pymysql.connect(host="localhost", user="root", password=pw, db="gildongmu_v3")
cur = con.cursor()
cur.execute("SELECT point_id, latitude, longitude FROM jeju_road_points")
P = np.array([(int(a), float(b), float(c)) for a, b, c in cur.fetchall()])
con.close()
fw = Transformer.from_crs(4326, 5179, always_xy=True)
X, Y = fw.transform(P[:, 2], P[:, 1])
N = np.c_[X, Y]
dl, _ = cKDTree(L).query(N)
dw, _ = cKDTree(W).query(N)
lit = (dl <= LIT_R).astype(int)
water = np.minimum(dw, WATER_CAP)

old = {int(r["point_id"]): r for r in csv.DictReader(open(os.path.join(EXP, "코드수정_1110", "노드속성_v3.csv"), encoding="utf-8"))}
with open(os.path.join(HERE, "노드속성_v3b.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["point_id", "signal", "facility_m", "lit", "water_m"])
    for pid, l_, wm in zip(P[:, 0].astype(int), lit, water):
        o = old[pid]
        w.writerow([pid, o["signal"], o["facility_m"], l_, round(float(wm), 1)])
log(f"노드 {len(N)}: 조명 25 m 안 {lit.mean():.3f}, 물가 50 m 안 {(water <= 50).mean():.3f}, 100 m 안 {(water <= 100).mean():.3f}, 물가 거리 중앙값 {np.median(water):.0f} m")

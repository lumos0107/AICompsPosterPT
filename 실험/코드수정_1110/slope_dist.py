"""τ 근거 자료: gildongmu_v3 그래프 간선의 경사 분포(길이 가중). τ를 정한 뒤에 잰 서술 자료이며 τ를 고르는 데 쓰지 않았다.
결과: 경사분포_v3.out   실행: py -I slope_dist.py
"""
import os
import re
import sys

import numpy as np
import pymysql

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
pw = re.search(r'password="([^"]*)"', open(r"C:\Users\seungjun\Documents\claude_code\논문\데이터사이언스학회\04_실험\새그래프_만들기\build_v2b_graph.py", encoding="utf-8").read()).group(1)
con = pymysql.connect(host="localhost", user="root", password=pw, db="gildongmu_v3")
cur = con.cursor()
cur.execute("SELECT e.distance_meters, ABS(a.elevation_meters - b.elevation_meters) FROM jeju_road_edges e JOIN jeju_road_points a ON a.point_id = e.from_point_id JOIN jeju_road_points b ON b.point_id = e.to_point_id WHERE e.from_point_id < e.to_point_id")
R = np.array(cur.fetchall(), dtype=float)
con.close()
L, dz = R[:, 0], R[:, 1]
ok = L > 0.5
g = dz[ok] / L[ok] * 100
w = L[ok]
out = open(os.path.join(HERE, "경사분포_v3.out"), "w", encoding="utf-8")
def log(s):
    print(s); out.write(s + "\n")
log(f"간선 {ok.sum()}개, 길이 {w.sum() / 1000:.1f} km")
order = np.argsort(g); cw = np.cumsum(w[order]) / w.sum()
for q in (0.25, 0.5, 0.75, 0.9):
    log(f"길이 가중 {int(q * 100)}% 분위 경사: {g[order][np.searchsorted(cw, q)]:.2f}%")
for t in (2, 3, 5, 8):
    log(f"경사 {t}% 초과 길이 비율: {w[g > t].sum() / w.sum():.3f}")

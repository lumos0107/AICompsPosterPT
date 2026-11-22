"""본 실험 다시 (2026-11-10 밤): 러닝 동선 모양 설정을 넣고 1차 본 실험과 같은 조건으로 돌린다.
- 안내점: 1차 본 실험과 같은 47개(../코드수정_1110/본실험_안내점.csv), 설정 10개(기준 + 세 선호 x α 1·3·10), 요청 470회.
- 모양 설정(예비 안내점 12개 시험에서 미리 정한 규칙으로 고름, dev_shape.py → dev_shape_b.py):
  귀환 근접 100 m x 3, 회전 60 m(45°), 나가는 구간 지그재그 배율 0.25, 측면 분리 0.
- 지표 계산은 main_routes.py와 같다(마지막 점은 첫 노드로 닫음, 한 응답 안 같은 경로는 하나로 셈).
실행: py -I main_routes2.py   결과: 본실험2.json, 본실험2.out
"""
import csv
import json
import math
import os
import re
import sys
import time
import urllib.request

import numpy as np
import pymysql
from scipy.spatial import cKDTree

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
OLD = os.path.join(os.path.dirname(HERE), "코드수정_1110")
API = "http://localhost:8080/api/routes/recommend"
OUT = open(os.path.join(HERE, "본실험2.out"), "w", encoding="utf-8")
SHAPE = dict(shapeProxRadius=100, shapeProxGamma=3, shapeTurnCost=60, shapeTurnAngle=45, shapeZigzagScale=0.25, shapeLateral=0)


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    OUT.write(s + "\n")
    OUT.flush()


START = {"탑동": (33.515, 126.522, 3000), "도심": (33.499, 126.531, 5000), "연동": (33.489, 126.490, 3000), "이도": (33.499, 126.541, 4000)}
SETS = [("기준", (0, 0, 0))] + [(f"{nm}{a}", tuple(a if j == k else 0 for j in range(3))) for k, nm in enumerate(["평지", "신호회피", "시설"]) for a in (1, 3, 10)]
TAU, KAPPA, CAP = 2.0, 100.0, 500.0
ANCH = [(r[0], int(r[1]), int(r[2]), float(r[5]), float(r[6])) for r in list(csv.reader(open(os.path.join(OLD, "본실험_안내점.csv"), encoding="utf-8-sig")))[1:]]

pw = re.search(r'password="([^"]*)"', open(r"C:\Users\seungjun\Documents\claude_code\논문\데이터사이언스학회\04_실험\새그래프_만들기\build_v2b_graph.py", encoding="utf-8").read()).group(1)
con = pymysql.connect(host="localhost", user="root", password=pw, db="gildongmu_v3")
cur = con.cursor()
cur.execute("SELECT point_id, latitude, longitude, elevation_meters FROM jeju_road_points")
P = np.array([(int(a), float(b), float(c), float(d)) for a, b, c, d in cur.fetchall()])
con.close()
ids = P[:, 0].astype(int)
coslat = math.cos(math.radians(33.5))
tree = cKDTree(np.c_[P[:, 1] * 111320, P[:, 2] * 111320 * coslat])
elev_of = dict(zip(ids.tolist(), P[:, 3].tolist()))
attr = {int(r["point_id"]): (r["signal"] == "1", float(r["facility_m"])) for r in csv.DictReader(open(os.path.join(OLD, "노드속성_v3.csv"), encoding="utf-8"))}


def hav(a, b):
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    x = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(b[1] - a[1]) / 2) ** 2
    return 2 * 6371000 * math.asin(min(1, math.sqrt(x)))


def metrics(pts, target):
    ll = [(p["latitude"], p["longitude"]) for p in pts]
    if len(ll) > 2 and hav(ll[-1], ll[0]) > 0.5:
        ll = ll[:-1] + [ll[0]]
    d, i = tree.query(np.array([(a * 111320, b * 111320 * coslat) for a, b in ll]))
    nodes = ids[i].tolist()
    seg = [hav(ll[k - 1], ll[k]) for k in range(1, len(ll))]
    L = sum(seg)
    el = [elev_of[n] for n in nodes]
    sl = [abs(el[k] - el[k - 1]) / s * 100 for k, s in enumerate(seg, 1) if s > 0.5]
    w = [s for s in seg if s > 0.5]
    mean_slope = sum(a * b for a, b in zip(sl, w)) / sum(w)
    cum = np.r_[0, np.cumsum(seg)]
    seg_slope = {}
    for step in (50, 100, 200):
        t = np.arange(0, cum[-1] + 1e-9, step)
        if len(t) < 2:
            continue
        e = np.interp(t, cum, el)
        seg_slope[step] = float(np.mean(np.abs(np.diff(e)) / step * 100))
    inner = nodes[1:-1]
    sig = sum(1 for n in inner if attr[n][0])
    fac = sum(s * (min(attr[nodes[k - 1]][1], CAP) + min(attr[nodes[k]][1], CAP)) / 2 for k, s in enumerate(seg, 1)) / L
    fs = sum(s * min(1, max(0, (abs(el[k] - el[k - 1]) / s * 100) - TAU) / 20) for k, s in enumerate(seg, 1) if s > 0.5)
    ff = sum(s * (min(attr[nodes[k - 1]][1], CAP) + min(attr[nodes[k]][1], CAP)) / 2 / CAP for k, s in enumerate(seg, 1))
    keys = [tuple(sorted((nodes[k - 1], nodes[k]))) for k in range(1, len(nodes))]
    seen, rt = set(), 0.0
    for k, s in zip(keys, seg):
        if k in seen:
            rt += s
        seen.add(k)
    return dict(length=L, err=abs(L - target) / target, slope=mean_slope, seg_slope=seg_slope, signals=sig, signals_per_km=sig / L * 1000,
                facility_m=fac, retrace=rt / L, cost_slope_per_km=fs / L * 1000, cost_fac_per_km=ff / L * 1000,
                cost_sig_per_km=sig * KAPPA / L * 1000, nodes=nodes, seg=seg, snap_max=float(d.max()), coords=ll)


def recommend(body):
    req = urllib.request.Request(API, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.loads(r.read().decode())


results, fails = [], []
t_all = time.time()
for st, ai, dr, la_a, lo_a in ANCH:
    la, lo, T = START[st]
    for sname, (a_s, a_c, a_f) in SETS:
        body = dict(latitude=la, longitude=lo, targetDistance=T, difficulty="normal", timeOfDay="day", algorithm="LOOP_V2",
                    alphaS=a_s, alphaC=a_c, alphaF=a_f, waypointLat=la_a, waypointLng=lo_a, **SHAPE)
        t0 = time.time()
        try:
            res = recommend(body)
        except Exception as e:
            log(f"{st} 안내점{ai} {sname}: 요청 실패 {e}")
            fails.append((st, ai, sname))
            continue
        sec = time.time() - t0
        seen = set()
        for ri, r in enumerate(res["routes"]):
            key = tuple((round(p["latitude"], 6), round(p["longitude"], 6)) for p in r["points"])
            if key in seen:
                continue
            seen.add(key)
            m = metrics(r["points"], T)
            m.update(start=st, target=T, setting=sname, alpha=[a_s, a_c, a_f], anchor_id=ai, anchor=[la_a, lo_a], anchor_dir=dr,
                     route=ri, n_routes=len(res["routes"]), sec=sec)
            results.append(m)
    log(f"  {st} 안내점{ai} 끝, 누적 경로 {len(results)}, 경과 {time.time() - t_all:.0f}초")
json.dump(results, open(os.path.join(HERE, "본실험2.json"), "w", encoding="utf-8"), ensure_ascii=False)
log(f"끝: 경로 {len(results)}, 요청 실패 {len(fails)}, 총 {time.time() - t_all:.0f}초")

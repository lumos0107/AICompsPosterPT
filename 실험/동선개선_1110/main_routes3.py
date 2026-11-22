"""새 선호 실험 (2026-11-10 밤): 본실험2와 같은 조건(안내점 47개, 러닝 동선 모양 설정)에서 새 선호 다섯 개를 각각 1·3·10으로 돌린다.
- 설정 16개: 기준 + 조명 α_l(alphaL), 물가 α_w(alphaW), 보도·녹지·조용한 길(alphaFlags: sidewalk, green, quiet) × 1·3·10. 요청 752회.
- 기준 설정도 다시 돌려 본실험2 기준 설정과 같은지 확인한다(summary_new.py).
- 서버는 노드 속성 노드속성_v3c.csv(lit, water_m, sidewalk, green, quiet 열 추가)로 띄운다(../코드수정_1110/server/start_server_v3c.sh).
- 지표 계산은 main_routes2.py와 같고, 밝은 길·물가 50 m·보도·공원·조용한 길 길이 비율(두 끝이 모두 그 성질인 구간)을 더한다.
실행: py -I main_routes3.py   결과: 본실험3.json, 본실험3.out
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
OUT = open(os.path.join(HERE, "본실험3.out"), "w", encoding="utf-8")
SHAPE = dict(shapeProxRadius=100, shapeProxGamma=3, shapeTurnCost=60, shapeTurnAngle=45, shapeZigzagScale=0.25, shapeLateral=0)


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    OUT.write(s + "\n")
    OUT.flush()


START = {"탑동": (33.515, 126.522, 3000), "도심": (33.499, 126.531, 5000), "연동": (33.489, 126.490, 3000), "이도": (33.499, 126.541, 4000)}
SETS = [("기준", {})] + [(f"{nm}{a}", {key: a}) for nm, key in (("조명", "alphaL"), ("물가", "alphaW")) for a in (1, 3, 10)] + \
    [(f"{nm}{a}", {"alphaFlags": {flag: a}}) for nm, flag in (("보도", "sidewalk"), ("녹지", "green"), ("조용", "quiet")) for a in (1, 3, 10)]
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
attr = {int(r["point_id"]): (r["signal"] == "1", float(r["facility_m"]), r["lit"] == "1", float(r["water_m"]), r["sidewalk"] == "1", r["green"] == "1", r["quiet"] == "1") for r in csv.DictReader(open(os.path.join(HERE, "노드속성_v3c.csv"), encoding="utf-8"))}


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
    lit_share = sum(s for k, s in enumerate(seg, 1) if attr[nodes[k - 1]][2] and attr[nodes[k]][2]) / L
    water_share = sum(s for k, s in enumerate(seg, 1) if attr[nodes[k - 1]][3] <= 50 and attr[nodes[k]][3] <= 50) / L
    both = lambda j: sum(s for k, s in enumerate(seg, 1) if attr[nodes[k - 1]][j] and attr[nodes[k]][j]) / L
    return dict(lit_share=lit_share, water_share=water_share, sidewalk_share=both(4), green_share=both(5), quiet_share=both(6), length=L, err=abs(L - target) / target, slope=mean_slope, seg_slope=seg_slope, signals=sig, signals_per_km=sig / L * 1000,
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
    for sname, extra in SETS:
        body = dict(latitude=la, longitude=lo, targetDistance=T, difficulty="normal", timeOfDay="day", algorithm="LOOP_V2",
                    alphaS=0, alphaC=0, alphaF=0, waypointLat=la_a, waypointLng=lo_a, **SHAPE, **extra)
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
            m.update(start=st, target=T, setting=sname, alpha=extra, anchor_id=ai, anchor=[la_a, lo_a], anchor_dir=dr,
                     route=ri, n_routes=len(res["routes"]), sec=sec)
            results.append(m)
    log(f"  {st} 안내점{ai} 끝, 누적 경로 {len(results)}, 경과 {time.time() - t_all:.0f}초")
json.dump(results, open(os.path.join(HERE, "본실험3.json"), "w", encoding="utf-8"), ensure_ascii=False)
log(f"끝: 경로 {len(results)}, 요청 실패 {len(fails)}, 총 {time.time() - t_all:.0f}초")

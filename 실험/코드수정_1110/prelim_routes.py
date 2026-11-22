"""예비 경로 (2026-11-10): 출발점 4곳 × 선호 설정 4가지, LOOP_V2 + 선호 비용, 서버는 gildongmu_v3.

- 안내점: 서버 generateAnchorPoint와 같은 규칙(0.38T, 16방향 중 실험 범위 안, 스냅 대상 노드 중 출발점에서 0.85~1.15배 거리,
  방향점 600 m 안)으로 이 스크립트가 시드 20261110으로 출발점마다 3개 고르고, 네 설정 모두 같은 안내점을 waypoint로 넘긴다.
  (응답의 anchorLatitude는 LOOP_V2에서 출발점이라 안내점으로 쓸 수 없음, 11/10 확인)
- 경로 마지막 점은 요청한 출발 좌표(노드 아님)라 지표에서 뺀다. 한 응답 안의 같은 경로는 하나로 센다.
- 경로 점 좌표를 DB 점과 맞춰 노드 번호를 찾는다(0.5 m 안).
- 지표: 거리 오차, 거리 가중 평균 경사(노드 사이), 50·100·200 m 구간 경사, 신호 교차로 경유 수(/km),
  가장 가까운 시설까지 평균 거리(길이 가중, 500 m 상한), 되밟기 비율, 각 선호 항의 크기(경로 1 km당 m).
실행: py -I prelim_routes.py   결과: 예비경로.json, 예비경로_요약.csv, 예비경로.out
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
EXP_DIR = os.path.dirname(HERE)
API = "http://localhost:8080/api/routes/recommend"
OUT = open(os.path.join(HERE, "예비경로.out"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    OUT.write(s + "\n")
    OUT.flush()


SCN = [("탑동", 33.515, 126.522, 3000), ("도심", 33.499, 126.531, 5000), ("연동", 33.489, 126.490, 3000), ("이도", 33.499, 126.541, 4000)]
SETS = [("기준", (0, 0, 0)), ("평지", (1, 0, 0)), ("신호회피", (0, 1, 0)), ("시설", (0, 0, 1))]
TAU, KAPPA, CAP = 2.0, 100.0, 500.0   # Preference.java 잠정값과 같게

pw = re.search(r'password="([^"]*)"', open(r"C:\Users\seungjun\Documents\claude_code\논문\데이터사이언스학회\04_실험\새그래프_만들기\build_v2b_graph.py", encoding="utf-8").read()).group(1)
con = pymysql.connect(host="localhost", user="root", password=pw, db="gildongmu_v3")
cur = con.cursor()
cur.execute("SELECT point_id, latitude, longitude, elevation_meters, osm_node_id IS NOT NULL FROM jeju_road_points")
P = np.array([(int(a), float(b), float(c), float(d), int(e)) for a, b, c, d, e in cur.fetchall()])
con.close()
ids = P[:, 0].astype(int)
coslat = math.cos(math.radians(33.5))
tree = cKDTree(np.c_[P[:, 1] * 111320, P[:, 2] * 111320 * coslat])
elev_of = dict(zip(ids.tolist(), P[:, 3].tolist()))
attr = {int(r["point_id"]): (r["signal"] == "1", float(r["facility_m"])) for r in csv.DictReader(open(os.path.join(HERE, "노드속성_v3.csv"), encoding="utf-8"))}


def hav(a, b):
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    x = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(b[1] - a[1]) / 2) ** 2
    return 2 * 6371000 * math.asin(min(1, math.sqrt(x)))


CELLS = {tuple(int(v) for v in l.split(",")) for l in open(os.path.join(EXP_DIR, "도심실험_1110", "실험범위_114칸.txt"), encoding="utf-8") if l.strip() and not l.startswith("#")}
SNAP = P[P[:, 4] == 1]
rng = np.random.default_rng(20261110)


def inside(la, lo):
    return (math.floor(lo / 0.005), math.floor(la / 0.005)) in CELLS


def pick_anchors(la, lo, T, n):
    ad = 0.38 * T
    out = []
    dirs = []
    for i in range(16):
        r = math.radians(360 / 16 * i)
        dla, dlo = la + ad / 111000 * math.cos(r), lo + ad / (111000 * math.cos(math.radians(la))) * math.sin(r)
        if inside(dla, dlo):
            dirs.append((i, dla, dlo))
    cands = {}
    for i, dla, dlo in dirs:
        for q in SNAP:
            if hav((dla, dlo), (q[1], q[2])) <= 600 and 0.85 * ad <= hav((la, lo), (q[1], q[2])) <= 1.15 * ad:
                cands[int(q[0])] = (i, float(q[1]), float(q[2]))
    keys = sorted(cands)
    for k in rng.choice(len(keys), size=min(n, len(keys)), replace=False):
        out.append(cands[keys[k]])
    return out, len(dirs), len(keys)


def recommend(body):
    req = urllib.request.Request(API, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read().decode())


def metrics(pts, target):
    ll = [(p["latitude"], p["longitude"]) for p in pts]
    if len(ll) > 2 and hav(ll[-1], ll[0]) > 0.5:
        ll = ll[:-1] + [ll[0]]   # 마지막 점(요청 출발 좌표) 대신 첫 노드로 닫는다
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
                cost_sig_per_km=sig * KAPPA / L * 1000, nodes=nodes, snap_max=float(d.max()), coords=ll)


results = []
for name, la, lo, T in SCN:
    anchors, ndir, ncand = pick_anchors(la, lo, T, 3)
    log(f"{name}: 범위 안 방향 {ndir}/16, 안내점 후보 {ncand}, 고른 안내점 {[(a[0], round(a[1], 5), round(a[2], 5)) for a in anchors]}")
    for ai, anchor in enumerate(anchors):
        for sname, (a_s, a_c, a_f) in SETS:
            body = dict(latitude=la, longitude=lo, targetDistance=T, difficulty="normal", timeOfDay="day", algorithm="LOOP_V2",
                        alphaS=a_s, alphaC=a_c, alphaF=a_f, waypointLat=anchor[1], waypointLng=anchor[2])
            t0 = time.time()
            try:
                res = recommend(body)
            except Exception as e:
                log(f"{name} 안내점{ai} {sname}: 실패 {e}")
                continue
            sec = time.time() - t0
            seen = set()
            for ri, r in enumerate(res["routes"]):
                key = tuple((round(p["latitude"], 6), round(p["longitude"], 6)) for p in r["points"])
                if key in seen:
                    continue
                seen.add(key)
                m = metrics(r["points"], T)
                m.update(start=name, target=T, setting=sname, alpha=[a_s, a_c, a_f], anchor_id=ai, anchor=anchor[1:], anchor_dir=anchor[0],
                         route=ri, n_routes=len(res["routes"]), sec=sec)
                results.append(m)
                log(f"{name} 안내점{ai} {sname} 경로{ri}: {m['length']:.0f}m 오차 {m['err']:.3f} 경사 {m['slope']:.2f}% 신호 {m['signals']}개({m['signals_per_km']:.2f}/km) "
                    f"시설 {m['facility_m']:.0f}m 되밟기 {m['retrace']:.2f} 비용/km 경사 {m['cost_slope_per_km']:.1f} 시설 {m['cost_fac_per_km']:.0f} 신호 {m['cost_sig_per_km']:.0f} "
                    f"구간경사 {', '.join(f'{k}m {v:.2f}' for k, v in m['seg_slope'].items())} 매칭최대 {m['snap_max']:.2f}m")
json.dump(results, open(os.path.join(HERE, "예비경로.json"), "w", encoding="utf-8"), ensure_ascii=False)
with open(os.path.join(HERE, "예비경로_요약.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["출발점", "안내점", "설정", "경로", "길이m", "오차", "경사%", "경사50", "경사100", "경사200", "신호수", "신호/km", "시설거리m", "되밟기", "경사비용/km", "시설비용/km", "신호비용/km", "초"])
    for m in results:
        ss = m["seg_slope"]
        w.writerow([m["start"], m["anchor_id"], m["setting"], m["route"], round(m["length"]), round(m["err"], 3), round(m["slope"], 2), *(round(ss.get(k, float("nan")), 2) for k in (50, 100, 200)),
                    m["signals"], round(m["signals_per_km"], 2), round(m["facility_m"]), round(m["retrace"], 3), round(m["cost_slope_per_km"], 1), round(m["cost_fac_per_km"]), round(m["cost_sig_per_km"]), round(m["sec"])])
log("끝", len(results))

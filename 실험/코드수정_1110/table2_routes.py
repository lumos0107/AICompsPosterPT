"""표 2 재측정 (2026-11-11, 사용자 지시): gildongmu_v3, 본 실험과 같은 안내점 47개(본실험_안내점.csv), 기준 설정.
구성 3가지:
  빔 귀환       : algorithm 생략(기존 DIRECTION). 선호 비용을 지원하지 않아 기존 점수(normal: 경사 가중치 0.5, 임계 8%)를 그대로 쓴다.
                  장애물·시설 표는 v3에서 비어 있어 그 항은 0이다.
  제안 귀환 γ=0 : LOOP_V2, α=(0,0,0), returnGamma=0
  제안 귀환 γ=5 : LOOP_V2, α=(0,0,0), returnGamma=5 (본 실험 '기준'과 같은 요청)
나가는 구간 종료는 세 구성 모두 코드 기본값(본 실험과 같음).
열(원고 표 2와 같음): 경로 수, 거리 오차, 성공 요청, 왕복형 경로, 경로 간 겹침, 응답 시간.
  경로 수 = 한 응답 안 고유 경로 수. 거리 오차 = 요청 안 경로 평균의 요청 간 평균±표준편차.
  왕복형 = 같은 간선을 두 번째 지나는 길이 비율 0.4 이상인 경로 / 전체 경로.
  경로 간 겹침 = 소수 넷째 자리 좌표 집합의 겹침(작은 쪽 기준)을 경로 쌍별로 평균한 요청 값의 평균±표준편차(경로 2개 이상인 요청만).
실행: py -I table2_routes.py   결과: 표2.json, 표2.out
"""
import csv
import json
import math
import os
import re
import statistics
import sys
import time
import urllib.request

import numpy as np
import pymysql
from scipy.spatial import cKDTree

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
API = "http://localhost:8080/api/routes/recommend"
OUT = open(os.path.join(HERE, "표2.out"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    OUT.write(s + "\n")
    OUT.flush()


START = {"탑동": (33.515, 126.522, 3000), "도심": (33.499, 126.531, 5000), "연동": (33.489, 126.490, 3000), "이도": (33.499, 126.541, 4000)}
ANCH = [(r[0], int(r[1]), float(r[5]), float(r[6])) for r in list(csv.reader(open(os.path.join(HERE, "본실험_안내점.csv"), encoding="utf-8-sig")))[1:]]
CONF = [("빔 귀환", dict()),
        ("제안 귀환 γ=0", dict(algorithm="LOOP_V2", alphaS=0, alphaC=0, alphaF=0, returnGamma=0)),
        ("제안 귀환 γ=5", dict(algorithm="LOOP_V2", alphaS=0, alphaC=0, alphaF=0, returnGamma=5))]
ONLY = sys.argv[1:]   # 구성 이름 일부만 돌릴 때

pw = re.search(r'password="([^"]*)"', open(r"C:\Users\seungjun\Documents\claude_code\논문\데이터사이언스학회\04_실험\새그래프_만들기\build_v2b_graph.py", encoding="utf-8").read()).group(1)
con = pymysql.connect(host="localhost", user="root", password=pw, db="gildongmu_v3")
cur = con.cursor()
cur.execute("SELECT point_id, latitude, longitude FROM jeju_road_points")
P = np.array([(int(a), float(b), float(c)) for a, b, c in cur.fetchall()])
con.close()
ids = P[:, 0].astype(int)
coslat = math.cos(math.radians(33.5))
tree = cKDTree(np.c_[P[:, 1] * 111320, P[:, 2] * 111320 * coslat])


def hav(a, b):
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    x = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(b[1] - a[1]) / 2) ** 2
    return 2 * 6371000 * math.asin(min(1, math.sqrt(x)))


def recommend(body):
    req = urllib.request.Request(API, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.loads(r.read().decode())


def route_metrics(pts, T):
    ll = [(p["latitude"], p["longitude"]) for p in pts]
    if len(ll) > 2 and hav(ll[-1], ll[0]) > 0.5:
        ll = ll[:-1] + [ll[0]]   # 마지막 점이 요청 출발 좌표면 첫 노드로 닫는다(본 실험과 같음)
    d, i = tree.query(np.array([(a * 111320, b * 111320 * coslat) for a, b in ll]))
    nodes = ids[i].tolist()
    seg = [hav(ll[k - 1], ll[k]) for k in range(1, len(ll))]
    L = sum(seg)
    seen, rt = set(), 0.0
    for k in range(1, len(nodes)):
        key = tuple(sorted((nodes[k - 1], nodes[k])))
        if key in seen:
            rt += seg[k - 1]
        seen.add(key)
    return dict(length=L, err=abs(L - T) / T, retrace=rt / L if L else 0.0, cells=sorted({f"{a:.4f},{b:.4f}" for a, b in ll}),
                snap_max=float(d.max()), coords=ll)


def overlap(routes):
    v = []
    for a in range(len(routes)):
        for b in range(a + 1, len(routes)):
            s1, s2 = set(routes[a]["cells"]), set(routes[b]["cells"])
            v.append(len(s1 & s2) / min(len(s1), len(s2)))
    return statistics.mean(v) if v else None


res = json.load(open(os.path.join(HERE, "표2.json"), encoding="utf-8")) if ONLY and os.path.exists(os.path.join(HERE, "표2.json")) else []
for cname, extra in CONF:
    if ONLY and not any(o in cname for o in ONLY):
        continue
    res = [r for r in res if r["conf"] != cname]
    t_all = time.time()
    for k, (st, ai, la_a, lo_a) in enumerate(ANCH):
        la, lo, T = START[st]
        body = dict(latitude=la, longitude=lo, targetDistance=T, difficulty="normal", timeOfDay="day", waypointLat=la_a, waypointLng=lo_a, **extra)
        t0 = time.time()
        try:
            resp = recommend(body)
            ok = True
        except Exception as e:
            log(f"{cname} {st}-{ai}: 요청 실패 {type(e).__name__} {e}")
            resp, ok = {"routes": []}, False
        sec = time.time() - t0
        seen, rts = set(), []
        for r in resp["routes"]:
            key = tuple((round(p["latitude"], 6), round(p["longitude"], 6)) for p in r["points"])
            if key in seen or len(r["points"]) < 2:
                continue
            seen.add(key)
            rts.append(route_metrics(r["points"], T))
        res.append(dict(conf=cname, start=st, anchor_id=ai, ok=ok, sec=sec, n=len(rts), routes=rts))
        log(f"{cname} {st}-{ai}: 경로 {len(rts)}, 오차 {[round(m['err'], 3) for m in rts]}, 되밟기 {[round(m['retrace'], 2) for m in rts]}, {sec:.1f}초 (누적 {time.time() - t_all:.0f}초)")
    json.dump(res, open(os.path.join(HERE, "표2.json"), "w", encoding="utf-8"), ensure_ascii=False)


def ms(xs, f="{:.2f}"):
    xs = [x for x in xs if x is not None]
    return (f + "±" + f).format(statistics.mean(xs), statistics.stdev(xs)) if len(xs) > 1 else "-"


log("\n| 구성 | 경로 수 | 거리 오차 | 성공 요청 | 왕복형 경로 | 경로 간 겹침 | 응답 시간(s) | 요청 실패 | 되밟기 평균 |")
log("|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
for cname, _ in CONF:
    q = [r for r in res if r["conf"] == cname]
    if not q:
        continue
    allr = [m for r in q for m in r["routes"]]
    log(f"| {cname} | {ms([r['n'] for r in q])} | {ms([statistics.mean([m['err'] for m in r['routes']]) if r['routes'] else None for r in q])} | "
        f"{sum(any(m['err'] <= 0.1 for m in r['routes']) for r in q)}/{len(q)} | {sum(m['retrace'] >= 0.4 for m in allr)}/{len(allr)} | "
        f"{ms([overlap(r['routes']) for r in q])} | {ms([r['sec'] for r in q], '{:.1f}')} | {sum(not r['ok'] for r in q)} | {statistics.mean(m['retrace'] for m in allr):.3f} |")

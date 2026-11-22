"""러닝 동선 모양 벌점 값 시험 (2026-11-10 밤). 본 실험 안내점(47개)이 아니라 예비 안내점 12개(시드 20261110)로만 시험한다.

설정(결과를 보기 전에 정함): 기준 선호 α=(0,0,0)에서
  없음 / 근접 r∈{100,200} m × γ_p∈{1,3} / 회전 c_t∈{30,60} m(45°) / 근접 r∈{100,200}, γ_p=3 + 회전 c_t∈{30,60}
고르는 규칙(결과 보기 전에 정함): 성공 요청 12/12, 경로 평균 거리 오차 ≤ 0.05인 설정 중 둥근 정도 중앙값이 가장 큰 것,
  같으면(소수 둘째 자리) km당 회전 수가 적은 것.
지표(러닝규칙_측정과 같은 정의): 둥근 정도 4πA/P², 10 m 단순화 뒤 45° 넘는 회전/km, 곧은 구간 중앙값, 되밟기(같은 무방향 간선
  두 번째 길이 비율, 좌표 6자리로 간선 식별), 왕복형(되밟기 ≥ 0.4), 오차, 성공(오차 ≤ 10% 경로 1개 이상), 경로 수, 응답 시간.
실행: py -I dev_shape.py   결과: 시험결과.json, 시험결과.out
"""
import collections
import json
import math
import os
import statistics
import sys
import time
import urllib.request

import numpy as np
from pyproj import Transformer

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
PRE = os.path.join(os.path.dirname(HERE), "코드수정_1110", "예비경로.json")
API = "http://localhost:8080/api/routes/recommend"
OUT = open(os.path.join(HERE, "시험결과.out"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    OUT.write(s + "\n")
    OUT.flush()


START = {"탑동": (33.515, 126.522, 3000), "도심": (33.499, 126.531, 5000), "연동": (33.489, 126.490, 3000), "이도": (33.499, 126.541, 4000)}
anch = {}
for m in json.load(open(PRE, encoding="utf-8")):
    anch[(m["start"], m["anchor_id"])] = m["anchor"]
ANCH = sorted(anch.items(), key=lambda kv: (list(START).index(kv[0][0]), kv[0][1]))
SETS = [("없음", 0, 0, 0)]
SETS += [(f"근접{r}x{g}", r, g, 0) for r in (100, 200) for g in (1, 3)]
SETS += [(f"회전{c}", 0, 0, c) for c in (30, 60)]
SETS += [(f"근접{r}x3+회전{c}", r, 3, c) for r in (100, 200) for c in (30, 60)]
fw = Transformer.from_crs(4326, 5179, always_xy=True)


def hav(a, b):
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    x = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(b[1] - a[1]) / 2) ** 2
    return 2 * 6371000 * math.asin(min(1, math.sqrt(x)))


def dp(P, eps):
    if len(P) < 3:
        return P
    a, b = P[0], P[-1]
    ab = b - a
    n = np.hypot(*ab)
    d = np.abs(ab[0] * (P[:, 1] - a[1]) - ab[1] * (P[:, 0] - a[0])) / n if n > 0 else np.hypot(*(P - a).T)
    i = int(np.argmax(d))
    if d[i] > eps:
        return np.vstack([dp(P[:i + 1], eps)[:-1], dp(P[i:], eps)])
    return np.array([a, b])


def route_metrics(pts, T):
    ll = [(p["latitude"], p["longitude"]) for p in pts]
    if len(ll) > 2 and hav(ll[-1], ll[0]) > 0.5:
        ll = ll[:-1] + [ll[0]]
    seg = [hav(ll[k - 1], ll[k]) for k in range(1, len(ll))]
    L = sum(seg)
    X, Y = fw.transform([b for a, b in ll], [a for a, b in ll])
    P = np.c_[X, Y]
    S = dp(P, 10.0)
    v = np.diff(S, axis=0)
    h = np.degrees(np.arctan2(v[:, 1], v[:, 0]))
    dh = np.abs((np.diff(h) + 180) % 360 - 180)
    turns = set(np.where(dh > 45)[0].tolist())
    runs, cur = [], 0.0
    for k, s in enumerate(np.hypot(*v.T)):
        cur += s
        if k in turns:
            runs.append(cur)
            cur = 0.0
    runs.append(cur)
    area = 0.5 * abs(np.dot(P[:-1, 0], P[1:, 1]) - np.dot(P[1:, 0], P[:-1, 1]))
    keys = [tuple(sorted(((round(ll[k - 1][0], 6), round(ll[k - 1][1], 6)), (round(ll[k][0], 6), round(ll[k][1], 6))))) for k in range(1, len(ll))]
    seen, rt = set(), 0.0
    for kk, s in zip(keys, seg):
        if kk in seen:
            rt += s
        seen.add(kk)
    return dict(length=L, err=abs(L - T) / T, comp=4 * math.pi * area / (L * L), turns_km=len(turns) / L * 1000,
                run_med=float(np.median(runs)), retrace=rt / L, coords=ll)


def recommend(body):
    req = urllib.request.Request(API, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.loads(r.read().decode())


res = []
for name, r, g, c in SETS:
    for (st, ai), an in ANCH:
        la, lo, T = START[st]
        body = dict(latitude=la, longitude=lo, targetDistance=T, difficulty="normal", timeOfDay="day", algorithm="LOOP_V2",
                    alphaS=0, alphaC=0, alphaF=0, waypointLat=an[0], waypointLng=an[1],
                    shapeProxRadius=r, shapeProxGamma=g, shapeTurnCost=c)
        t0 = time.time()
        try:
            resp = recommend(body)
        except Exception as e:
            log(f"{name} {st}-{ai}: 실패 {e}")
            res.append(dict(set=name, start=st, anchor_id=ai, ok=False, sec=time.time() - t0, routes=[]))
            continue
        sec = time.time() - t0
        seen, rts = set(), []
        for rr in resp["routes"]:
            key = tuple((round(p["latitude"], 6), round(p["longitude"], 6)) for p in rr["points"])
            if key in seen:
                continue
            seen.add(key)
            rts.append(route_metrics(rr["points"], T))
        res.append(dict(set=name, start=st, anchor_id=ai, ok=True, sec=sec, routes=rts))
    log(f"{name} 끝")
json.dump(res, open(os.path.join(HERE, "시험결과.json"), "w", encoding="utf-8"), ensure_ascii=False)

log("\n설정 | 성공 | 경로/요청 | 평균 오차 | 오차≤5% 경로 | 둥근 정도 중앙 | 회전/km 중앙 | 곧은 구간 중앙 m | 되밟기 평균 | 왕복형 | 응답 초 중앙")
summary = []
for name, *_ in SETS:
    q = [x for x in res if x["set"] == name]
    R = [m for x in q for m in x["routes"]]
    succ = sum(any(m["err"] <= 0.1 for m in x["routes"]) for x in q)
    s = dict(name=name, succ=succ, n=len(q), err=statistics.mean(m["err"] for m in R), comp=statistics.median(m["comp"] for m in R),
             turns=statistics.median(m["turns_km"] for m in R))
    summary.append(s)
    log(f"{name} | {succ}/{len(q)} | {len(R) / len(q):.2f} | {s['err']:.3f} | {sum(m['err'] <= 0.05 for m in R)}/{len(R)} | {s['comp']:.2f} | {s['turns']:.2f} | "
        f"{statistics.median(m['run_med'] for m in R):.0f} | {statistics.mean(m['retrace'] for m in R):.3f} | {sum(m['retrace'] >= 0.4 for m in R)}/{len(R)} | {statistics.median(x['sec'] for x in q):.1f}")
ok = [s for s in summary if s["succ"] == s["n"] and s["err"] <= 0.05]
pick = sorted(ok, key=lambda s: (-round(s["comp"], 2), s["turns"]))[0] if ok else None
log(f"\n고르는 규칙에 따른 설정: {pick['name'] if pick else '조건을 만족하는 설정 없음'}")

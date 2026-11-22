"""표 2 (모양 반영 행 추가): 빔 귀환 / 제안 귀환 γ=0 / γ=5 (../코드수정_1110/표2.json) + γ=5 + 러닝 동선 모양(본실험2.json 기준 설정).
네 행 모두 gildongmu_v3, 같은 안내점 47개, 기준 선호 (0,0,0). 기존 열에 둥근 정도(4πA/P²)와 km당 회전(10 m 단순화 뒤 45° 초과)을 더한다.
경로 수 = 한 응답 안 고유 경로 수, 오차·겹침은 요청 평균의 평균±표준편차, 둥근 정도·회전은 경로 중앙값.
실행: py -I table2_shape.py   결과: 표2_모양.out
"""
import json
import math
import os
import statistics
import sys

import numpy as np
from pyproj import Transformer

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
OLD = os.path.join(os.path.dirname(HERE), "코드수정_1110")
out = open(os.path.join(HERE, "표2_모양.out"), "w", encoding="utf-8")
fw = Transformer.from_crs(4326, 5179, always_xy=True)


def log(s):
    print(s)
    out.write(s + "\n")


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


def shape(coords, L):
    ll = np.array(coords)
    X, Y = fw.transform(ll[:, 1], ll[:, 0])
    P = np.c_[X, Y]
    area = 0.5 * abs(np.dot(P[:-1, 0], P[1:, 1]) - np.dot(P[1:, 0], P[:-1, 1]))
    S = dp(P, 10.0)
    v = np.diff(S, axis=0)
    h = np.degrees(np.arctan2(v[:, 1], v[:, 0]))
    dh = np.abs((np.diff(h) + 180) % 360 - 180)
    return 4 * math.pi * area / (L * L), int((dh > 45).sum()) / L * 1000


def cells(coords):
    return set(f"{a:.4f},{b:.4f}" for a, b in coords)


def overlap(rs):
    v = []
    for i in range(len(rs)):
        for j in range(i + 1, len(rs)):
            s1, s2 = cells(rs[i]["coords"]), cells(rs[j]["coords"])
            v.append(len(s1 & s2) / min(len(s1), len(s2)))
    return statistics.mean(v) if v else None


reqs = {}
for r in json.load(open(os.path.join(OLD, "표2.json"), encoding="utf-8")):
    reqs.setdefault(r["conf"], []).append(dict(sec=r["sec"], routes=r["routes"]))
m2 = [m for m in json.load(open(os.path.join(HERE, "본실험2.json"), encoding="utf-8")) if m["setting"] == "기준"]
grp = {}
for m in m2:
    grp.setdefault((m["start"], m["anchor_id"]), []).append(m)
reqs["제안 귀환 γ=5 + 모양"] = [dict(sec=v[0]["sec"], routes=v) for v in grp.values()]


def ms(xs, f="{:.2f}"):
    xs = [x for x in xs if x is not None]
    return (f + "±" + f).format(statistics.mean(xs), statistics.stdev(xs)) if len(xs) > 1 else "-"


log("| 구성 | 경로 수 | 거리 오차 | 성공 요청 | 왕복형 경로 | 경로 간 겹침 | 둥근 정도 | 회전/km | 응답 시간(s) |")
log("|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
for name in ["빔 귀환", "제안 귀환 γ=0", "제안 귀환 γ=5", "제안 귀환 γ=5 + 모양"]:
    q = reqs[name]
    R = [m for r in q for m in r["routes"]]
    sh = [shape(m["coords"], m["length"]) for m in R]
    log(f"| {name} | {ms([len(r['routes']) for r in q])} | {ms([statistics.mean(m['err'] for m in r['routes']) if r['routes'] else None for r in q])} | "
        f"{sum(any(m['err'] <= 0.1 for m in r['routes']) for r in q)}/{len(q)} | {sum(m['retrace'] >= 0.4 for m in R)}/{len(R)} | "
        f"{ms([overlap(r['routes']) for r in q])} | {statistics.median(c for c, t in sh):.2f} | {statistics.median(t for c, t in sh):.2f} | {ms([r['sec'] for r in q], '{:.1f}')} |")

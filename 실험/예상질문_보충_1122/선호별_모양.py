"""선호를 켰을 때 거리 오차·둥근 정도·꺾임 수 (2026-11-22, 예상 질문 답 보충).

질문: 표 2(논문)는 기준 설정에서만 잰 값인데, 선호를 켜도 경로 모양이 유지되나?
측정 방식은 ../코드수정_1110/running_rules_measure.py와 같다.
- 둥근 정도: 4πA/L², A는 경로 좌표(EPSG 5179)로 잰 넓이(신발끈 공식), L은 경로 길이
- 꺾임 수: 10 m 허용 오차로 단순화(Douglas–Peucker)한 뒤 45°보다 크게 꺾인 횟수 / km
- 둥근 정도·꺾임 수는 경로 중앙값, 거리 오차는 요청 평균(그 요청 경로들의 평균)의 평균
- 성공 요청: 오차 10% 이하이고 되밟기 비율 0.4 미만인 경로가 1개 이상
자료: ../동선개선_1110/본실험2.json(기준·경사·신호·편의시설), 본실험3.json(조명·물가·보도·녹지·조용한 길)
실행: python -I 선호별_모양.py  → 선호별_모양.out
"""
import collections
import json
import math
import os

import numpy as np
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "동선개선_1110")
fw = Transformer.from_crs(4326, 5179, always_xy=True)


def dp(P, eps):
    if len(P) < 3:
        return P
    a, b = P[0], P[-1]
    ab = b - a
    n = np.hypot(*ab)
    d = np.abs(np.cross(ab, P - a)) / n if n > 0 else np.hypot(*(P - a).T)
    i = int(np.argmax(d))
    if d[i] > eps:
        return np.vstack([dp(P[:i + 1], eps)[:-1], dp(P[i:], eps)])
    return np.array([a, b])


def shape(m):
    ll = np.array(m["coords"])
    X, Y = fw.transform(ll[:, 1], ll[:, 0])
    P = np.c_[X, Y]
    L = m["length"]
    S = dp(P, 10.0)
    v = np.diff(S, axis=0)
    h = np.degrees(np.arctan2(v[:, 1], v[:, 0]))
    dh = np.abs((np.diff(h) + 180) % 360 - 180)
    area = 0.5 * abs(np.dot(P[:-1, 0], P[1:, 1]) - np.dot(P[1:, 0], P[:-1, 1]))
    return 4 * math.pi * area / (L * L), int((dh > 45).sum()) / L * 1000


rows = []
for fn, keep_base in (("본실험2.json", True), ("본실험3.json", False)):
    for m in json.load(open(os.path.join(SRC, fn), encoding="utf-8")):
        if m["setting"] == "기준" and not keep_base:
            continue
        rows.append(m)

order, by = [], collections.defaultdict(list)
for m in rows:
    if m["setting"] not in by:
        order.append(m["setting"])
    by[m["setting"]].append(m)

out = ["| 설정 | 경로 수 | 성공 요청 | 거리 오차(요청 평균) | 둥근 정도(중앙값) | 꺾임 수/km(중앙값) |", "|---|---:|---:|---:|---:|---:|"]
for s in order:
    ms = by[s]
    req = collections.defaultdict(list)
    for m in ms:
        req[(m["start"], m["anchor_id"])].append(m)
    ok = sum(any(r["err"] <= 0.10 and r["retrace"] < 0.4 for r in v) for v in req.values())
    err = np.mean([np.mean([r["err"] for r in v]) for v in req.values()])
    sh = [shape(m) for m in ms]
    out.append(f"| {s} | {len(ms)} | {ok}/{len(req)} | {err * 100:.1f}% | {np.median([a for a, _ in sh]):.2f} | {np.median([t for _, t in sh]):.2f} |")

text = "\n".join(out)
print(text)
open(os.path.join(HERE, "선호별_모양.out"), "w", encoding="utf-8").write(text + "\n")

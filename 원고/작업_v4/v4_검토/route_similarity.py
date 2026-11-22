"""사용자 질문용: 한 요청에서 나온 경로(최대 3개)가 얼마나 비슷한가. 본실험3.json 기준 설정만.
겹침 = 두 경로가 함께 지난 간선 길이 / 짧은 쪽 경로 길이(좌표 6자리로 간선 식별).
방향 차이 = 출발점에서 각 경로의 가장 먼 점을 본 방위의 차이.
실행: py -I v4_검토/route_similarity.py"""
import collections
import itertools
import json
import math
import os
import statistics
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, "..", "..", "..", "실험", "동선개선_1110", "본실험3.json"), encoding="utf-8"))
req = collections.defaultdict(list)
for m in R:
    if m["setting"] == "기준":
        req[(m["start"], m["anchor_id"])].append(m)


def hav(a, b):
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    x = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(b[1] - a[1]) / 2) ** 2
    return 2 * 6371000 * math.asin(min(1, math.sqrt(x)))


def edges(c):
    out = {}
    for a, b in zip(c[:-1], c[1:]):
        k = tuple(sorted(((round(a[0], 6), round(a[1], 6)), (round(b[0], 6), round(b[1], 6)))))
        out[k] = hav(a, b)
    return out


def far_bearing(c):
    s = c[0]
    f = max(c, key=lambda p: hav(s, p))
    dy = f[0] - s[0]
    dx = (f[1] - s[1]) * math.cos(math.radians(s[0]))
    return math.degrees(math.atan2(dx, dy)) % 360


cnt = collections.Counter(len(v) for v in req.values())
ov, ang = [], []
for k, v in req.items():
    for a, b in itertools.combinations(v, 2):
        ea, eb = edges(a["coords"]), edges(b["coords"])
        shared = sum(ea[e] for e in ea.keys() & eb.keys())
        ov.append(shared / min(sum(ea.values()), sum(eb.values())))
        d = abs(far_bearing(a["coords"]) - far_bearing(b["coords"])) % 360
        ang.append(min(d, 360 - d))
q = lambda xs, p: sorted(xs)[int(p * (len(xs) - 1))]
print("요청 수", len(req), "요청당 경로 수 분포", dict(sorted(cnt.items())))
print(f"경로 쌍 {len(ov)}개")
print(f"겹치는 길 비율: 중앙값 {statistics.median(ov):.2f}, 사분위 {q(ov, .25):.2f}~{q(ov, .75):.2f}, 최대 {max(ov):.2f}")
print(f"가장 먼 점 방향 차이(°): 중앙값 {statistics.median(ang):.0f}, 사분위 {q(ang, .25):.0f}~{q(ang, .75):.0f}, 최대 {max(ang):.0f}")
print("겹침 0.5 이상 쌍 비율", f"{sum(o >= 0.5 for o in ov) / len(ov):.2f}", " 방향 차이 30° 이상 쌍 비율", f"{sum(a >= 30 for a in ang) / len(ang):.2f}")

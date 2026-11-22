"""v5 표 3: 변화량 대신 설정별 실제 평균값(2026-11-13 교수 의견 '표가 복잡하다'로 바꿈).
집계는 main_summary.py·summary_new.py와 같다: 요청 값 = 한 응답 안 경로 평균, 표 값 = 요청 47개 평균.
경사·신호·시설은 본실험2.json, 다섯 성질은 본실험3.json. 길이 비율은 %로 보인다.
실행: python -I 표3_실제값.py  → 표3_실제값.out
"""
import collections
import json
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.join(HERE, "..", "..", "실험", "동선개선_1110")
out = open(os.path.join(HERE, "표3_실제값.out"), "w", encoding="utf-8")


def log(s):
    print(s)
    out.write(s + "\n")


ROWS = [  # (json, 설정 접두어, 지표 키, 표 이름, 배율, 소수 자리)
    ("본실험2.json", "평지", "slope", "경사 (%)", 1, 2),
    ("본실험2.json", "신호회피", "signals_per_km", "신호 교차로 (개/km)", 1, 2),
    ("본실험2.json", "시설", "facility_m", "편의시설 거리 (m)", 1, 1),
    ("본실험3.json", "조명", "lit_share", "조명 (%)", 100, 0),
    ("본실험3.json", "물가", "water_share", "물가 (%)", 100, 0),
    ("본실험3.json", "보도", "sidewalk_share", "보도 (%)", 100, 0),
    ("본실험3.json", "녹지", "green_share", "녹지 (%)", 100, 0),
    ("본실험3.json", "조용", "quiet_share", "조용한 길 (%)", 100, 0),
]
data = {}
for name in {r[0] for r in ROWS}:
    g = collections.defaultdict(list)
    for m in json.load(open(os.path.join(EXP, name), encoding="utf-8")):
        g[(m["start"], m["anchor_id"], m["setting"])].append(m)
    data[name] = g

log("지표 | 기준 | α=1 | α=3 | α=10 | 성공(1/3/10) | 정밀값")
for js, pre, key, nm, mul, nd in ROWS:
    g = data[js]
    reqs = sorted({(k[0], k[1]) for k in g})
    vals, succ = [], []
    for s in ["기준"] + [f"{pre}{a}" for a in (1, 3, 10)]:
        ks = [k for k in reqs if g[(k[0], k[1], s)]]
        assert len(ks) == 47, (s, len(ks))
        vals.append(float(np.mean([np.mean([m[key] for m in g[(k[0], k[1], s)]]) for k in ks])) * mul)
        succ.append(sum(any(m["err"] <= 0.1 for m in g[(k[0], k[1], s)]) for k in ks))
    log(f"{nm} | " + " | ".join(f"{v:.{nd}f}" for v in vals) + f" | {succ[1]}/{succ[2]}/{succ[3]} (기준 {succ[0]}) | "
        + ", ".join(f"{v:.4f}" for v in vals))

"""새 선호(조명·물가·보도·녹지·조용한 길) 실험 요약 (본실험3.json).
- 기준 설정이 본실험2.json 기준 설정과 같은지(노드열 기준) 확인한다.
- 설정별: 성공 요청, 거리 오차, 되밟기, 기준과 다른 길이 비율, 해당 지표(길이 비율) 평균.
- 짝 비교: 해당 지표의 설정 − 기준(클수록 나아짐), 나아진/나빠진 요청, 윌콕슨 부호순위(양측).
- 다른 선호 지표의 평균 변화(경사, 신호/km, 시설 거리, 다섯 비율).
요청 값 = 한 응답 안 고유 경로 평균. 결과: 새선호_요약.out   실행: py -I summary_new.py
"""
import collections
import json
import os
import sys

import numpy as np
from scipy.stats import wilcoxon

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, "본실험3.json"), encoding="utf-8"))
R2 = json.load(open(os.path.join(HERE, "본실험2.json"), encoding="utf-8"))
out = open(os.path.join(HERE, "새선호_요약.out"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    out.write(s + "\n")


g = collections.defaultdict(list)
for m in R:
    g[(m["start"], m["anchor_id"], m["setting"])].append(m)
reqs = sorted({(m["start"], m["anchor_id"]) for m in R})
g2 = collections.defaultdict(list)
for m in R2:
    if m["setting"] == "기준":
        g2[(m["start"], m["anchor_id"])].append(tuple(m["nodes"]))
same = sum(1 for k in reqs if sorted(tuple(m["nodes"]) for m in g[(k[0], k[1], "기준")]) == sorted(g2[k]))
log(f"기준 설정이 본실험2와 같은 요청: {same}/{len(reqs)}")

OWN = {"조명": ("lit_share", "밝은 길 비율"), "물가": ("water_share", "물가 50 m 비율"), "보도": ("sidewalk_share", "보도 비율"),
       "녹지": ("green_share", "공원 비율"), "조용": ("quiet_share", "조용한 길 비율")}
SETS = ["기준"] + [f"{p}{a}" for p in OWN for a in (1, 3, 10)]


def ekeys(m):
    n = m["nodes"]
    return [tuple(sorted((n[i - 1], n[i]))) for i in range(1, len(n))]


def val(k, s, key):
    ms = g[(k[0], k[1], s)]
    return float(np.mean([m[key] for m in ms])) if ms else np.nan


def other(k, s):
    be = set().union(*[set(ekeys(b)) for b in g[(k[0], k[1], "기준")]])
    return float(np.mean([sum(x for kk, x in zip(ekeys(m), m["seg"]) if kk not in be) / sum(m["seg"]) for m in g[(k[0], k[1], s)]]))


log("\n[1] 설정별 (요청 47회씩) | 성공 | 오차 | 되밟기 | 기준과 다른 길이 | 밝은 길 | 물가 | 보도 | 공원 | 조용")
for s in SETS:
    ks = [k for k in reqs if g[(k[0], k[1], s)]]
    succ = sum(any(m["err"] <= 0.1 for m in g[(k[0], k[1], s)]) for k in ks)
    f = lambda key: np.mean([val(k, s, key) for k in ks])
    oth = "-" if s == "기준" else f"{np.mean([other(k, s) for k in ks]):.2f}"
    log(f"{s} | {succ}/{len(reqs)} | {f('err'):.3f} | {f('retrace'):.3f} | {oth} | {f('lit_share'):.3f} | {f('water_share'):.3f} | "
        f"{f('sidewalk_share'):.3f} | {f('green_share'):.3f} | {f('quiet_share'):.3f}")

log("\n[2] 짝 비교 (해당 지표, 설정 − 기준, 클수록 나아짐) | 평균 차이 | 기준 대비 상대 | 나아짐/나빠짐/같음 | W, p")
for p, (key, nm) in OWN.items():
    for a in (1, 3, 10):
        s = f"{p}{a}"
        d = np.array([val(k, s, key) - val(k, "기준", key) for k in reqs])
        base = np.mean([val(k, "기준", key) for k in reqs])
        imp, wor = int((d > 1e-9).sum()), int((d < -1e-9).sum())
        ws = "차이 없음"
        if imp + wor:
            w = wilcoxon(d, zero_method="wilcox")
            ws = f"W={w.statistic:.0f}, p={w.pvalue:.2g}"
        log(f"{s} | {nm} | {d.mean():+.3f} | {d.mean() / base * 100:+.0f}% (기준 {base:.3f}) | {imp}/{wor}/{len(d) - imp - wor} | {ws}")

log("\n[3] 다른 지표 변화 (설정 − 기준 평균): 경사%p, 신호/km, 시설 m, 밝은 길, 물가, 보도, 공원, 조용")
keys = ["slope", "signals_per_km", "facility_m", "lit_share", "water_share", "sidewalk_share", "green_share", "quiet_share"]
for s in SETS[1:]:
    log(f"{s} | " + ", ".join(f"{np.mean([val(k, s, kk) - val(k, '기준', kk) for k in reqs]):+.3f}" for kk in keys))

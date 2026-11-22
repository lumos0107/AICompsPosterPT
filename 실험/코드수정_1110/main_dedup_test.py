"""본 실험 짝 비교의 민감도: 안내점이 달라도 (기준 응답, 설정 응답)이 똑같은 요청은 하나로 세고 윌콕슨 부호순위 검정을 다시 한다.
결과: 본실험_중복제거검정.out   실행: py -I main_dedup_test.py
"""
import collections
import json
import os
import sys

import numpy as np
from scipy.stats import wilcoxon

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
SRCJ = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "본실험.json")   # 인자: [결과 json] [출력 접미사]
SUF = sys.argv[2] if len(sys.argv) > 2 else ""
R = json.load(open(SRCJ, encoding="utf-8"))
out = open(os.path.join(HERE, f"본실험_중복제거검정{SUF}.out"), "w", encoding="utf-8")
g = collections.defaultdict(list)
for m in R:
    g[(m["start"], m["anchor_id"], m["setting"])].append(m)
reqs = sorted({(m["start"], m["anchor_id"]) for m in R})
OWN = {"평지": "slope", "신호회피": "signals_per_km", "시설": "facility_m"}
resp = lambda k, s: frozenset(tuple(m["nodes"]) for m in g[(k[0], k[1], s)])
val = lambda k, s, key: float(np.mean([m[key] for m in g[(k[0], k[1], s)]]))
base_distinct = len({(k[0], resp(k, "기준")) for k in reqs})
line = f"기준 설정: 요청 {len(reqs)}개 중 서로 다른 응답 {base_distinct}개"
print(line); out.write(line + "\n")
for p, key in OWN.items():
    for a in (1, 3, 10):
        s = f"{p}{a}"
        uniq = {}
        for k in reqs:
            uniq.setdefault((k[0], resp(k, "기준"), resp(k, s)), val(k, s, key) - val(k, "기준", key))
        d = np.array(list(uniq.values()))
        imp, wor = int((d < -1e-9).sum()), int((d > 1e-9).sum())
        w = wilcoxon(d, zero_method="wilcox")
        line = f"{s}: 서로 다른 짝 {len(d)}/{len(reqs)}, 평균 차이 {d.mean():+.3f}, 나아짐/나빠짐 {imp}/{wor}, W={w.statistic:.0f}, p={w.pvalue:.2g}"
        print(line); out.write(line + "\n")

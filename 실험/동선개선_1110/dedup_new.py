"""새 선호 짝 비교의 민감도 (../코드수정_1110/main_dedup_test.py와 같은 방식): 안내점이 달라도 (기준 응답, 설정 응답)이 똑같은 요청은 하나로 세고 윌콕슨 부호순위 검정을 다시 한다.
실행: py -I dedup_new.py   입력: 본실험3.json   결과: 새선호_중복제거검정.out
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
out = open(os.path.join(HERE, "새선호_중복제거검정.out"), "w", encoding="utf-8")
g = collections.defaultdict(list)
for m in R:
    g[(m["start"], m["anchor_id"], m["setting"])].append(m)
reqs = sorted({(m["start"], m["anchor_id"]) for m in R})
OWN = {"조명": "lit_share", "물가": "water_share", "보도": "sidewalk_share", "녹지": "green_share", "조용": "quiet_share"}
resp = lambda k, s: frozenset(tuple(m["nodes"]) for m in g[(k[0], k[1], s)])
val = lambda k, s, key: float(np.mean([m[key] for m in g[(k[0], k[1], s)]]))
line = f"기준 설정: 요청 {len(reqs)}개 중 서로 다른 응답 {len({(k[0], resp(k, '기준')) for k in reqs})}개"
print(line); out.write(line + "\n")
for p, key in OWN.items():
    for a in (1, 3, 10):
        s = f"{p}{a}"
        uniq = {}
        for k in reqs:
            uniq.setdefault((k[0], resp(k, "기준"), resp(k, s)), val(k, s, key) - val(k, "기준", key))
        d = np.array(list(uniq.values()))
        imp, wor = int((d > 1e-9).sum()), int((d < -1e-9).sum())
        w = wilcoxon(d, zero_method="wilcox")
        line = f"{s}: 서로 다른 짝 {len(d)}/{len(reqs)}, 평균 차이 {d.mean():+.3f}, 나아짐/나빠짐 {imp}/{wor}, W={w.statistic:.0f}, p={w.pvalue:.2g}"
        print(line); out.write(line + "\n")
line = "\n[출발점별 평균 차이 (나아진 요청/요청)]"
print(line); out.write(line + "\n")
for p, key in OWN.items():
    for a in (1, 3, 10):
        s = f"{p}{a}"
        parts = []
        for st in ("탑동", "도심", "연동", "이도"):
            ks = [k for k in reqs if k[0] == st]
            d = np.array([val(k, s, key) - val(k, "기준", key) for k in ks])
            parts.append(f"{st} {d.mean():+.3f} ({int((d > 1e-9).sum())}/{len(ks)})")
        line = f"{s} | " + " | ".join(parts)
        print(line); out.write(line + "\n")
line = "\n[설정별 되밟기 최대(요청 평균의 평균은 새선호_요약.out)]"
print(line); out.write(line + "\n")
for s in sorted({m["setting"] for m in R}):
    line = f"{s}: 경로 되밟기 최대 {max(m['retrace'] for m in R if m['setting'] == s):.3f}, 왕복형(≥0.4) {sum(1 for m in R if m['setting'] == s and m['retrace'] >= 0.4)}"
    print(line); out.write(line + "\n")

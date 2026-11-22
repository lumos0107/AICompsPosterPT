"""본 실험 요약: 설정 10개별 성공률·거리 오차·되밟기·기준 경로와 다른 길이 비율·선호 지표,
같은 안내점끼리 짝지은 기준 대비 비교(평균 차이, 나아진/나빠진/같은 요청 수, 윌콕슨 부호순위 검정 양측),
평지 선호의 50·100·200 m 경사 방향, 기준 경로의 비용 항 크기.
요청 단위 값 = 한 응답 안 고유 경로들의 평균(예비 경로와 같은 정의). 성공 요청 = 오차 ±10% 경로가 1개 이상.
결과: 본실험_요약.out, 본실험_요청별.csv   실행: py -I main_summary.py
"""
import collections
import csv
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
out = open(os.path.join(HERE, f"본실험_요약{SUF}.out"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    out.write(s + "\n")


SETS = ["기준"] + [f"{p}{a}" for p in ("평지", "신호회피", "시설") for a in (1, 3, 10)]
OWN = {"평지": ("slope", "경사 %"), "신호회피": ("signals_per_km", "신호 교차로 개/km"), "시설": ("facility_m", "시설 거리 m")}
STARTS = ["탑동", "도심", "연동", "이도"]
grp = collections.defaultdict(list)
for m in R:
    grp[(m["start"], m["anchor_id"], m["setting"])].append(m)
reqs = sorted({(m["start"], m["anchor_id"]) for m in R}, key=lambda k: (STARTS.index(k[0]), k[1]))
log(f"요청 단위(출발점·안내점) {len(reqs)}개 × 설정 {len(SETS)}개, 경로 {len(R)}개")


def ekeys(m):
    n = m["nodes"]
    return [tuple(sorted((n[i - 1], n[i]))) for i in range(1, len(n))]


def other_ratio(ms, base):
    be = set().union(*[set(ekeys(b)) for b in base])
    v = []
    for m in ms:
        L = sum(m["seg"])
        Lo = sum(s for k, s in zip(ekeys(m), m["seg"]) if k not in be)
        v.append(Lo / L)
    return float(np.mean(v))


def req_val(k, s, key):
    ms = grp[(k[0], k[1], s)]
    return float(np.mean([m[key] for m in ms])) if ms else np.nan


# 요청별 표
rows = []
for k in reqs:
    for s in SETS:
        ms = grp[(k[0], k[1], s)]
        if not ms:
            rows.append([k[0], k[1], s, 0] + [""] * 9)
            continue
        rows.append([k[0], k[1], s, len(ms), int(any(m["err"] <= 0.1 for m in ms)), round(req_val(k, s, "err"), 4), round(req_val(k, s, "retrace"), 4),
                     round(req_val(k, s, "slope"), 3), round(req_val(k, s, "signals_per_km"), 3), round(req_val(k, s, "facility_m"), 1),
                     "" if s == "기준" else round(other_ratio(ms, grp[(k[0], k[1], "기준")]), 3), round(float(np.mean([m["length"] for m in ms]))), round(ms[0]["sec"], 1)])
with open(os.path.join(HERE, f"본실험_요청별{SUF}.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["출발점", "안내점", "설정", "고유경로수", "성공", "거리오차", "되밟기", "경사%", "신호/km", "시설거리m", "기준과다른길이비율", "평균길이m", "응답초"])
    w.writerows(rows)

log(f"\n[1] 설정별 결과 (요청 {len(reqs)}회씩, 요청 단위 값의 평균)")
log("설정 | 고유 경로/요청 | 성공 요청 | 거리 오차 | 되밟기 | 왕복형(≥0.4) 경로 | 기준과 다른 길이 비율 | 경사 % | 신호/km | 시설 거리 m | 응답 초(중앙값)")
for s in SETS:
    ks = [k for k in reqs if grp[(k[0], k[1], s)]]
    ms = [m for k in ks for m in grp[(k[0], k[1], s)]]
    succ = sum(1 for k in ks if any(m["err"] <= 0.1 for m in grp[(k[0], k[1], s)]))
    f = lambda key: np.mean([req_val(k, s, key) for k in ks])
    oth = "-" if s == "기준" else f"{np.mean([other_ratio(grp[(k[0], k[1], s)], grp[(k[0], k[1], '기준')]) for k in ks]):.2f}"
    rt = sum(1 for m in ms if m["retrace"] >= 0.4)
    log(f"{s} | {len(ms) / len(ks):.2f} | {succ}/{len(reqs)} | {f('err'):.3f} | {f('retrace'):.3f} | {rt}/{len(ms)} | {oth} | {f('slope'):.2f} | {f('signals_per_km'):.2f} | {f('facility_m'):.1f} | {np.median([grp[(k[0], k[1], s)][0]['sec'] for k in ks]):.1f}")

log("\n[2] 같은 안내점끼리 짝지은 기준 대비 비교 (해당 선호 지표, 설정 − 기준)")
log("설정 | 지표 | 짝 수 | 평균 차이 | 중앙값 차이 | 나아짐/나빠짐/같음 | 윌콕슨 부호순위 (양측, 0 차이 제외) W, p")
for p, (key, nm) in OWN.items():
    for a in (1, 3, 10):
        s = f"{p}{a}"
        d = np.array([req_val(k, s, key) - req_val(k, "기준", key) for k in reqs])
        d = d[np.isfinite(d)]
        imp, wor = int((d < -1e-9).sum()), int((d > 1e-9).sum())
        same = len(d) - imp - wor
        if imp + wor > 0:
            wt = wilcoxon(d, zero_method="wilcox", alternative="two-sided")
            ws = f"W={wt.statistic:.0f}, p={wt.pvalue:.2g} (n={imp + wor})"
        else:
            ws = "차이 없음"
        log(f"{s} | {nm} | {len(d)} | {d.mean():+.3f} | {np.median(d):+.3f} | {imp}/{wor}/{same} | {ws}")

log("\n[2-1] 출발점별 평균 차이 (해당 선호 지표, 설정 − 기준) / 나아진 요청")
for p, (key, nm) in OWN.items():
    for a in (1, 3, 10):
        s = f"{p}{a}"
        parts = []
        for st in STARTS:
            d = np.array([req_val(k, s, key) - req_val(k, "기준", key) for k in reqs if k[0] == st])
            parts.append(f"{st} {d.mean():+.3f} ({int((d < -1e-9).sum())}/{len(d)})")
        log(f"{s} | " + " | ".join(parts))

log("\n[2-2] 다른 선호 지표의 변화 (설정 − 기준 평균)")
for p in OWN:
    for a in (1, 3, 10):
        s = f"{p}{a}"
        log(f"{s} | " + " | ".join(f"{nm} {np.mean([req_val(k, s, key) - req_val(k, '기준', key) for k in reqs]):+.3f}" for key, nm in OWN.values()))

log("\n[3] 경사 구간 길이 50·100·200 m: 평지 − 기준 평균, 세 길이의 방향이 같은지")
for a in (1, 3, 10):
    s = f"평지{a}"
    for st in STARTS + ["전체"]:
        ks = [k for k in reqs if st == "전체" or k[0] == st]
        v = {L: np.mean([np.mean([m["seg_slope"][str(L)] for m in grp[(k[0], k[1], s)]]) - np.mean([m["seg_slope"][str(L)] for m in grp[(k[0], k[1], "기준")]]) for k in ks]) for L in (50, 100, 200)}
        log(f"{s} {st}: 50m {v[50]:+.3f}, 100m {v[100]:+.3f}, 200m {v[200]:+.3f} → {'같음' if len({np.sign(x) for x in v.values()}) == 1 else '다름'}")

log("\n[4] 비용 항 크기: 기준 설정 경로를 α=1로 쟀을 때 경로 1 km당 비용(m)")
log("항 | 중앙값 | 사분위 범위 | 범위 | 사분위 범위/중앙값 | 같은 요청 안 고유 경로 사이 차이(최대−최소) 중앙값")
b = [m for m in R if m["setting"] == "기준"]
for key, nm in (("cost_slope_per_km", "경사"), ("cost_fac_per_km", "시설"), ("cost_sig_per_km", "신호")):
    v = np.array([m[key] for m in b])
    q1, q3 = np.percentile(v, [25, 75])
    within = [max(m[key] for m in grp[(k[0], k[1], "기준")]) - min(m[key] for m in grp[(k[0], k[1], "기준")]) for k in reqs if len(grp[(k[0], k[1], "기준")]) > 1]
    log(f"{nm} | {np.median(v):.0f} | {q1:.0f}~{q3:.0f} | {v.min():.0f}~{v.max():.0f} | {(q3 - q1) / np.median(v):.2f} | {np.median(within):.0f}")
log("\n[5] 요청 실패(응답 없음)·경로 0개: 요청 단위로 빠진 것", sum(1 for k in reqs for s in SETS if not grp[(k[0], k[1], s)]))

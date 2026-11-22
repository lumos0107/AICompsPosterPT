"""예비 경로 요약: 설정별 지표 평균, 기준 설정과의 차이, 비용 항 크기, 50·100·200 m 경사 방향. 결과: 예비경로_요약.out"""
import collections, json, os, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, "예비경로.json"), encoding="utf-8"))
out = open(os.path.join(HERE, "예비경로_요약.out"), "w", encoding="utf-8")
def log(*a):
    s = " ".join(str(x) for x in a); print(s); out.write(s + "\n")
SETS = ["기준", "평지", "신호회피", "시설"]
grp = collections.defaultdict(list)
for m in R:
    grp[(m["start"], m["anchor_id"], m["setting"])].append(m)
def edges(m):
    n = m["nodes"]; return {tuple(sorted((n[i - 1], n[i]))) for i in range(1, len(n))}
log("[설정별 평균] 요청 12회(출발점 4 × 안내점 3)씩, 고유 경로 평균")
log("설정 | 고유 경로 | 성공 요청(±10%) | 거리 오차 | 경사% | 신호/km | 시설 거리 m | 되밟기 | 비용/km 경사·시설·신호(α=1 기준 m)")
for s in SETS:
    ms = [m for m in R if m["setting"] == s]
    reqs = {(m["start"], m["anchor_id"]) for m in ms}
    succ = sum(1 for k in reqs if any(m["err"] <= 0.1 for m in grp[(k[0], k[1], s)]))
    f = lambda k: np.mean([m[k] for m in ms])
    log(f"{s} | {len(ms)} ({len(ms) / len(reqs):.2f}/요청) | {succ}/{len(reqs)} | {f('err'):.3f} | {f('slope'):.2f} | {f('signals_per_km'):.2f} | {f('facility_m'):.0f} | {f('retrace'):.3f} | {f('cost_slope_per_km'):.0f} · {f('cost_fac_per_km'):.0f} · {f('cost_sig_per_km'):.0f}")
log("\n[같은 출발점·안내점에서 기준 대비] 요청별 고유 경로 평균의 차이, 나아진 요청 수 / 12, 기준 경로와 다른 길이 비율")
for s, key, better in (("평지", "slope", -1), ("신호회피", "signals_per_km", -1), ("시설", "facility_m", -1)):
    diffs, imp, other = [], 0, []
    for (st, ai, ss), ms in grp.items():
        if ss != s: continue
        base = grp[(st, ai, "기준")]
        d = np.mean([m[key] for m in ms]) - np.mean([m[key] for m in base])
        diffs.append(d); imp += (d * better > 0)
        be = set().union(*[edges(m) for m in base])
        for m in ms:
            n = m["nodes"]; L = 0; Lo = 0
            for i in range(1, len(n)):
                seg = np.hypot(*(np.array(m["coords"][i]) - np.array(m["coords"][i - 1])) * [111320, 92800])
                L += seg; Lo += seg * (tuple(sorted((n[i - 1], n[i]))) not in be)
            other.append(Lo / L)
    log(f"{s}: 지표 {key} 평균 차이 {np.mean(diffs):+.3f}, 나아진 요청 {imp}/12, 기준 경로들과 다른 길이 비율 평균 {np.mean(other):.2f}")
log("\n[경사 구간 길이 50·100·200 m] 평지 − 기준 (요청 12회 평균), 방향이 셋 다 같은지")
for st in ["탑동", "도심", "연동", "이도", "전체"]:
    d = {k: [] for k in ("50", "100", "200")}
    for (s0, ai, ss), ms in grp.items():
        if ss != "평지" or (st != "전체" and s0 != st): continue
        base = grp[(s0, ai, "기준")]
        for k in d:
            d[k].append(np.mean([m["seg_slope"][k] for m in ms]) - np.mean([m["seg_slope"][k] for m in base]))
    v = {k: np.mean(x) for k, x in d.items()}
    log(f"{st}: 50m {v['50']:+.3f}, 100m {v['100']:+.3f}, 200m {v['200']:+.3f} → {'같음' if len({np.sign(x) for x in v.values()}) == 1 else '다름'}")
log("\n[비용 항 크기] 기준 설정 경로에서 α=1로 쟀을 때 1 km당 비용(m): 분포")
b = [m for m in R if m["setting"] == "기준"]
for k, nm in (("cost_slope_per_km", "경사"), ("cost_fac_per_km", "시설"), ("cost_sig_per_km", "신호")):
    v = np.array([m[k] for m in b]); log(f"{nm}: 중앙값 {np.median(v):.0f}, 범위 {v.min():.0f}~{v.max():.0f}")
log("[시간] 요청당 초: 중앙값", np.median([m["sec"] for m in R]))

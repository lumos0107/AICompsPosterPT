"""영상판정.csv와 samples.json을 합쳐 집계한다."""
import collections
import csv
import json
import os
import sys

from scipy.stats import beta

HERE = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\소구역점검_1109"
sys.stdout.reconfigure(encoding="utf-8")
out = open(os.path.join(HERE, "집계.out"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out.write(s + "\n")


def cp(k, n):
    """Clopper-Pearson 95% 구간."""
    lo = 0.0 if k == 0 else float(beta.ppf(0.025, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(0.975, k + 1, n - k))
    return lo, hi


sam = {s["id"]: s for s in json.load(open(os.path.join(HERE, "samples.json"), encoding="utf-8"))["samples"]}
rows = list(csv.DictReader(open(os.path.join(HERE, "영상판정.csv"), encoding="utf-8")))
assert len(rows) == len(sam) and {r["id"] for r in rows} == set(sam)

OUTLINE_KM, CLOSED_KM = 286.4, 224.6  # 표본추출.out
REAL_KM = CLOSED_KM / 2 + (OUTLINE_KM - CLOSED_KM)
log(f"독립 보행로: 선 길이 합 {OUTLINE_KM}km, 닫힌 선을 절반으로 친 길이 약 {REAL_KM:.1f}km")
walk = [r for r in rows if r["id"].startswith("W")]
n = len(walk)
for name, k in collections.Counter(r["판정"] for r in walk).most_common() + [("독립 산책로", 0)]:
    lo, hi = cp(k, n)
    log(f"  {name}: {k}/{n} = {k/n:.1%} (95% 구간 {lo:.1%}~{hi:.1%}), 환산 {k/n*REAL_KM:.0f}km ({lo*REAL_KM:.0f}~{hi*REAL_KM:.0f}km)")

groups = {g["id"]: g for g in json.load(open(os.path.join(HERE, "long_groups.json"), encoding="utf-8"))}
lrows = list(csv.DictReader(open(os.path.join(HERE, "영상판정_1km이상.csv"), encoding="utf-8")))
assert len(lrows) == len(groups) and {r["id"] for r in lrows} == set(groups)
log(f"\n1km 이상 묶음 전수 {len(lrows)}개 {sum(g['km'] for g in groups.values()):.1f}km (닫힌 선은 절반으로 친 길이 병기)")
agg = collections.defaultdict(lambda: [0, 0.0, 0.0])
for r in lrows:
    g = groups[r["id"]]
    a = agg[r["판정"]]
    a[0] += 1
    a[1] += g["km"]
    a[2] += g["km"] - g["closed_km"] / 2
for k, (c, km, real) in sorted(agg.items(), key=lambda t: -t[1][1]):
    log(f"  {k}: {c}개, 선 길이 {km:.2f}km, 환산 {real:.2f}km")

road = [r for r in rows if r["id"].startswith("R")]
log(f"\n도로 표본 {len(road)}개", dict(collections.Counter(r["판정"] for r in road)))
tab = collections.defaultdict(collections.Counter)
for r in road:
    s = sam[r["id"]]
    width = "폭 3m 미만" if s["width_m"] < 3 else "폭 3m 이상"
    tab[width][r["판정"]] += 1
    tab[s["stratum"]][r["판정"]] += 1
    tab[s["region"] + " " + width][r["판정"]] += 1
for k in sorted(tab):
    log(f"  {k}: {sum(tab[k].values())}개 {dict(tab[k])}")

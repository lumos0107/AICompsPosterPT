"""본 실험 효과 그림: 선호마다 한 판(단위가 달라 축을 나눔), 가로 α 1·3·10, 세로 '설정 − 기준'(요청 46개 각각 점, 평균은 굵은 표시).
색: 평지 파랑, 신호 회피 주황, 시설 청록(예비 그림과 같음, dataviz 검증 통과). 0 선은 회색.
결과: 본실험_효과.png   실행: py -I plot_main.py
"""
import collections
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRCJ = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "본실험.json")   # 인자: [결과 json] [출력 접미사]
SUF = sys.argv[2] if len(sys.argv) > 2 else ""
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False
R = json.load(open(SRCJ, encoding="utf-8"))
grp = collections.defaultdict(list)
for m in R:
    grp[(m["start"], m["anchor_id"], m["setting"])].append(m)
reqs = sorted({(m["start"], m["anchor_id"]) for m in R})
PANELS = [("평지", "slope", "경사 차이 (%p)", "#2a78d6", "평지 선호"),
          ("신호회피", "signals_per_km", "신호 교차로 차이 (개/km)", "#eb6834", "신호 회피"),
          ("시설", "facility_m", "가장 가까운 시설까지 거리 차이 (m)", "#1baf7a", "시설 근접")]
fig, axs = plt.subplots(1, 3, figsize=(15, 5.6), facecolor="#fcfcfb")
rng = np.random.default_rng(0)
for ax, (p, key, ylab, col, title) in zip(axs, PANELS):
    ax.axhline(0, color="#a3a29d", lw=1, zorder=1)
    for j, a in enumerate((1, 3, 10)):
        d = np.array([np.mean([m[key] for m in grp[(k[0], k[1], f"{p}{a}")]]) - np.mean([m[key] for m in grp[(k[0], k[1], "기준")]]) for k in reqs])
        x = j + rng.uniform(-0.12, 0.12, len(d))
        ax.scatter(x, d, s=16, color="#b9b8b2", zorder=2, linewidths=0)
        ax.plot([j - 0.22, j + 0.22], [d.mean()] * 2, color=col, lw=3, zorder=3, solid_capstyle="round")
        imp = int((d < -1e-9).sum())
        ax.annotate(f"평균 {d.mean():+.2f}\n나아짐 {imp}/{len(d)}", (j + 0.25, d.mean()), xytext=(4, 0), textcoords="offset points",
                    va="center", fontsize=10, color="#0b0b0b")
    ax.set_xticks([0, 1, 2], ["α = 1", "α = 3", "α = 10"])
    ax.set_xlim(-0.5, 2.9)
    ax.set_ylabel(ylab, color="#52514e")
    ax.set_title(title, loc="left", fontsize=13, color="#0b0b0b")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color("#d6d5d0")
    ax.tick_params(colors="#52514e")
fig.suptitle(f"본 실험: 같은 출발점·안내점에서 기준 설정과 비교한 차이 (점 = 요청 {len(reqs)}개, 굵은 선 = 평균, 0보다 낮으면 선호 쪽으로 나아짐)",
             fontsize=13, x=0.01, ha="left", color="#0b0b0b")
fig.subplots_adjust(left=0.06, right=0.98, top=0.86, bottom=0.08, wspace=0.32)
fig.savefig(os.path.join(HERE, f"본실험_효과{SUF}.png"), dpi=130, facecolor="#fcfcfb")
print("끝")

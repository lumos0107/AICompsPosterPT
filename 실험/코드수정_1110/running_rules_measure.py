"""러닝 동선 규칙으로 본 실험 '기준' 경로(127개)를 잰다. 측정만 하고 코드·실험은 바꾸지 않는다.
규칙과 지표:
  1 덜 꺾임   : 10 m 단순화(Douglas-Peucker) 뒤 45° 넘는 회전의 km당 수, 회전 사이 곧은 구간 길이(중앙값)
  2 단순한 고리: 둥근 정도 4πA/P²(원 1, 정사각형 0.79, 왕복 0), 같은 간선 두 번째 지나는 길이 비율
  3 길 종류   : 경로 길이 중 도로 폭(RVWD) 6 m 미만 / 6~12 m / 12 m 이상 비율
  5 서로 다름 : 같은 요청의 경로 쌍 겹침(소수 넷째 자리 좌표 집합, 작은 쪽 기준)
  6 거리     : 오차 5% 이내 경로 비율
결과: 러닝규칙_측정.out   실행: py -I running_rules_measure.py
"""
import collections
import json
import math
import os
import sys

import numpy as np
from pyproj import Transformer
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
SRCJ = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "본실험.json")   # 인자: [결과 json] [출력 접미사]
SUF = sys.argv[2] if len(sys.argv) > 2 else ""
EXP = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(EXP, "데이터진단_1109", "수집계획용", "에이전트검토"))
from lib_shp import dbf_columns

sys.stdout.reconfigure(encoding="utf-8")
out = open(os.path.join(HERE, f"러닝규칙_측정{SUF}.out"), "w", encoding="utf-8")


def log(s):
    print(s)
    out.write(s + "\n")


ROAD = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵\연속수치지도_제주_20261109\풀기\N3L_A0020000\N3L_A0020000"
g = np.load(os.path.join(EXP, "도심실험_1110", "그래프_도심_114칸.npz"))
xy, A, B, main, rec = g["xy"], g["A"], g["B"], g["main"], g["rec"]
wid = np.array([float(x or 0) for x in dbf_columns(ROAD, ["RVWD"])["RVWD"]])
E = np.where(main)[0]
mid = (xy[A[E]] + xy[B[E]]) / 2
emid_tree = cKDTree(mid)
ewid = wid[rec[E]]
fw = Transformer.from_crs(4326, 5179, always_xy=True)
R = json.load(open(SRCJ, encoding="utf-8"))
base = [m for m in R if m["setting"] == "기준"]


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


rows = []
for m in base:
    ll = np.array(m["coords"])
    X, Y = fw.transform(ll[:, 1], ll[:, 0])
    P = np.c_[X, Y]
    L = m["length"]
    S = dp(P, 10.0)
    v = np.diff(S, axis=0)
    h = np.degrees(np.arctan2(v[:, 1], v[:, 0]))
    dh = np.abs((np.diff(h) + 180) % 360 - 180)
    turn_idx = np.where(dh > 45)[0]
    seglen = np.hypot(*v.T)
    runs, cur = [], 0.0
    for k, s in enumerate(seglen):
        cur += s
        if k in set(turn_idx.tolist()):
            runs.append(cur)
            cur = 0.0
    runs.append(cur)
    area = 0.5 * abs(np.dot(P[:-1, 0], P[1:, 1]) - np.dot(P[1:, 0], P[:-1, 1]))
    comp = 4 * math.pi * area / (L * L)
    segm = (P[:-1] + P[1:]) / 2
    sl = np.hypot(*np.diff(P, axis=0).T)
    dd, ii = emid_tree.query(segm)
    w = ewid[ii]
    rows.append(dict(start=m["start"], key=(m["start"], m["anchor_id"]), turns_km=len(turn_idx) / L * 1000, run_med=float(np.median(runs)),
                     comp=comp, retrace=m["retrace"], err=m["err"],
                     w_narrow=float(sl[w < 6].sum() / sl.sum()), w_mid=float(sl[(w >= 6) & (w < 12)].sum() / sl.sum()), w_wide=float(sl[w >= 12].sum() / sl.sum()),
                     cells=set(f"{a:.4f},{b:.4f}" for a, b in m["coords"])))

q = lambda k: np.percentile([r[k] for r in rows], [25, 50, 75])
log(f"기준 설정 경로 {len(rows)}개 (요청 47개)")
for k, nm in (("turns_km", "1 km당 45° 넘는 회전 수"), ("run_med", "1 회전 사이 곧은 구간 길이 중앙값(m)"), ("comp", "2 둥근 정도 4πA/P²"), ("retrace", "2 되밟기 비율"),
              ("w_narrow", "3 폭 6 m 미만 도로 비율"), ("w_mid", "3 폭 6~12 m 도로 비율"), ("w_wide", "3 폭 12 m 이상 도로 비율")):
    a, b, c = q(k)
    log(f"{nm}: 사분위 {a:.2f} / 중앙 {b:.2f} / {c:.2f}")
log(f"6 오차 5% 이내 경로: {sum(r['err'] <= 0.05 for r in rows)}/{len(rows)}, 10% 이내 {sum(r['err'] <= 0.10 for r in rows)}/{len(rows)}")
grp = collections.defaultdict(list)
for r in rows:
    grp[r["key"]].append(r)
ov = []
for k, rs in grp.items():
    for i in range(len(rs)):
        for j in range(i + 1, len(rs)):
            s1, s2 = rs[i]["cells"], rs[j]["cells"]
            ov.append(len(s1 & s2) / min(len(s1), len(s2)))
log(f"5 같은 요청 경로 쌍 겹침: 쌍 {len(ov)}개, 중앙값 {np.median(ov):.2f}, 0.5 넘는 쌍 {sum(o > 0.5 for o in ov)}/{len(ov)}; 경로 1개뿐인 요청 {sum(len(v) == 1 for v in grp.values())}/{len(grp)}")
log("\n출발점별 중앙값 (회전/km, 곧은 구간 m, 둥근 정도, 폭 6 m 미만 비율)")
for st in ["탑동", "도심", "연동", "이도"]:
    rs = [r for r in rows if r["start"] == st]
    log(f"{st}: {np.median([r['turns_km'] for r in rs]):.1f}, {np.median([r['run_med'] for r in rs]):.0f}, {np.median([r['comp'] for r in rs]):.2f}, {np.median([r['w_narrow'] for r in rs]):.2f}")

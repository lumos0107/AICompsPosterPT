"""조각이 몰린 읍면동의 폭 값 변화를 5월 사본과 비교하고, 폭이 3m 이상에서 미만으로 바뀐 도로 표본을 뽑는다. 원본은 읽기만 한다.
실행: py -I check_pieces2.py
결과: 조각점검2.out, 폭변화표본.json
"""
import collections
import csv
import json
import os
import random
import sys

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

HERE = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\새그래프_1110"
sys.path.insert(0, r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\데이터진단_1109\수집계획용\에이전트검토")
from lib_shp import FILES, dbf_columns, read_shp

sys.stdout.reconfigure(encoding="utf-8")
out = open(os.path.join(HERE, "조각점검2.out"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out.write(s + "\n")
    out.flush()


RAW = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵"
ROAD = os.path.join(RAW, "연속수치지도_제주_20261109", "풀기", "N3L_A0020000", "N3L_A0020000")
EMD = os.path.join(RAW, "연속수치지도_제주_20261109_추가", "풀기", "N3A_G0110000", "N3A_G0110000")


def load(npz, base):
    d = dict(np.load(os.path.join(HERE, npz)))
    d["lines"] = [p for _, parts in read_shp(base, clip=False) for p in parts]
    at = dbf_columns(base, ["RVWD", "RDDV", "FMTA", "UFID"])
    d["wid"] = np.array([float(x or 0) for x in at["RVWD"]])
    d["rddv"] = np.array(at["RDDV"])
    d["fmta"] = np.array(at["FMTA"])
    return d


def densify(d, ei, step=5.0):
    p = d["lines"][d["line"][ei]][d["a"][ei]:d["b"][ei] + 1]
    c = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]
    if c[-1] <= 0:
        return p[:1]
    t = np.r_[np.arange(0, c[-1], step), c[-1]]
    return np.c_[np.interp(t, c, p[:, 0]), np.interp(t, c, p[:, 1])]


new = load("그래프_새자료.npz", ROAD)
may = load("그래프_5월사본.npz", FILES["road"])
names = dbf_columns(EMD, ["NAME"])["NAME"]
polys = [(names[rc], rings, np.vstack(rings)) for rc, rings in read_shp(EMD, clip=False)]
boxes = np.array([[p[2][:, 0].min(), p[2][:, 1].min(), p[2][:, 0].max(), p[2][:, 1].max()] for p in polys])


def emd_points(pts):
    """점마다 읍면동 번호(-1은 밖)."""
    res = -np.ones(len(pts), int)
    for i, (_, rings, _) in enumerate(polys):
        x0, y0, x1, y1 = boxes[i]
        idx = np.where((res < 0) & (pts[:, 0] >= x0) & (pts[:, 0] <= x1) & (pts[:, 1] >= y0) & (pts[:, 1] <= y1))[0]
        if len(idx) == 0:
            continue
        x, y = pts[idx, 0], pts[idx, 1]
        c = np.zeros(len(idx), bool)
        for r in rings:
            for xa, ya, xb, yb in zip(r[:-1, 0], r[:-1, 1], r[1:, 0], r[1:, 1]):
                if ya != yb:
                    c ^= ((ya > y) != (yb > y)) & (x < (xb - xa) * (y - ya) / (yb - ya) + xa)
        res[idx[c]] = i
    return res


def sample_points(d):
    P, W, E = [], [], []
    for ei in range(len(d["A"])):
        q = densify(d, ei)
        P.append(q)
        W.append(np.full(len(q), d["wid"][d["rec"][ei]]))
        E.append(np.full(len(q), ei))
    return np.vstack(P), np.concatenate(W), np.concatenate(E)


pn, wn, en = sample_points(new)
pm, wm, em = sample_points(may)
log("점 수", len(pn), len(pm))
tree = cKDTree(pm)
d, idx = tree.query(pn, workers=-1)
near = d <= 3.0
log(f"새 자료 점 중 5월 도로 3m 안: {near.mean():.1%}")
emd_n = emd_points(pn)
emd_m = emd_points(pm)
STEP_KM = 0.005
rows = []
for i, (nm, _, _) in enumerate(polys):
    a = emd_n == i
    b = emd_m == i
    if not a.any():
        continue
    down = a & near & (wm[idx] >= 3) & (wn < 3)
    up = a & near & (wm[idx] < 3) & (wn >= 3)
    rows.append(dict(읍면동=nm, 새도로km=a.sum() * STEP_KM, 새폭미달km=(a & (wn < 3)).sum() * STEP_KM, 월5도로km=b.sum() * STEP_KM, 월5폭미달km=(b & (wm < 3)).sum() * STEP_KM,
                     일치km=(a & near).sum() * STEP_KM, 넓음에서좁음km=down.sum() * STEP_KM, 좁음에서넓음km=up.sum() * STEP_KM))
rows.sort(key=lambda r: -r["넓음에서좁음km"])
log("\n[읍면동별 폭 값 변화 (5m 점 환산 km), 3m 기준으로 바뀐 길이 상위 12]")
log("읍면동 | 새 도로 | 새 폭미달 | 5월 도로 | 5월 폭미달 | 넓음→좁음 | 좁음→넓음")
for r in rows[:12]:
    log(f"{r['읍면동']} | {r['새도로km']:.0f} | {r['새폭미달km']:.0f} ({r['새폭미달km'] / r['새도로km']:.1%}) | {r['월5도로km']:.0f} | {r['월5폭미달km']:.0f} ({r['월5폭미달km'] / max(r['월5도로km'], 1):.1%}) | {r['넓음에서좁음km']:.1f} | {r['좁음에서넓음km']:.1f}")
tot_down = sum(r["넓음에서좁음km"] for r in rows)
tot_up = sum(r["좁음에서넓음km"] for r in rows)
log(f"전체 넓음→좁음 {tot_down:.1f}km, 좁음→넓음 {tot_up:.1f}km")

# 성산읍 폭 값
SS = [i for i, p in enumerate(polys) if p[0] == "성산읍"][0]
a = emd_n == SS
down = a & near & (wm[idx] >= 3) & (wn < 3)
log(f"\n[성산읍] 넓음→좁음 지점의 새 폭 값 상위 {collections.Counter(np.round(wn[down], 1).tolist()).most_common(8)}")
log(f"[성산읍] 넓음→좁음 지점의 5월 폭 값 상위 {collections.Counter(np.round(wm[idx][down], 1).tolist()).most_common(8)}")
ed = np.unique(en[down])
rec = new["rec"][ed]
log(f"[성산읍] 넓음→좁음 간선 {len(ed):,}개, 도로 구분 {collections.Counter(new['rddv'][rec].tolist()).most_common(5)}")
log(f"[성산읍] 넓음→좁음 간선 FMTA 상위 {collections.Counter(new['fmta'][rec].tolist()).most_common(6)}")
all_ss = np.unique(en[a])
log(f"[성산읍] 전체 간선 FMTA 상위 {collections.Counter(new['fmta'][new['rec'][all_ss]].tolist()).most_common(6)}")
others = np.unique(en[~a])
log(f"[성산읍 밖] 전체 간선 FMTA 상위 {collections.Counter(new['fmta'][new['rec'][others]].tolist()).most_common(6)}")

# 5월 조각 수 (읍면동별)
N = len(may["xy"])
m = ~may["narrow"]
n, lab = connected_components(coo_matrix((np.ones(int(m.sum())), (may["A"][m], may["B"][m])), shape=(N, N)), directed=False)
Lc = np.bincount(lab[may["A"][m]], weights=may["L"][m], minlength=n)
main = int(Lc.argmax())
mids = (may["xy"][may["A"]] + may["xy"][may["B"]]) / 2
ee = np.where(m & (lab[may["A"]] != main) & ~may["island"])[0]
first = {}
for e in ee.tolist():
    first.setdefault(int(lab[may["A"][e]]), e)
e_pts = mids[list(first.values())]
ee_emd = emd_points(e_pts)
c5 = collections.Counter(polys[i][0] if i >= 0 else "(밖)" for i in ee_emd.tolist())
piece = list(csv.DictReader(open(os.path.join(HERE, "조각목록_새자료.csv"), encoding="utf-8-sig")))
piece = [r for r in piece if r["섬"] == "0"]
cn = collections.Counter(r["읍면동"] for r in piece)
log("\n[읍면동별 조각 수 (섬 제외), 새 자료 상위 10과 5월 값]")
for nm, c in cn.most_common(10):
    log(f"{nm}: 새 {c}, 5월 {c5.get(nm, 0)}")
log(f"합계: 새 {sum(cn.values())}, 5월 {sum(c5.values())}; 성산읍 제외: 새 {sum(cn.values()) - cn['성산읍']}, 5월 {sum(c5.values()) - c5.get('성산읍', 0)}")

# 표본: 성산읍에서 폭이 3m 이상에서 미만으로 바뀌었고 조각에 붙은 간선
A, B = new["A"], new["B"]
piece_nodes = set()
N2 = len(new["xy"])
m2 = ~new["narrow"]
n2, lab2 = connected_components(coo_matrix((np.ones(int(m2.sum())), (A[m2], B[m2])), shape=(N2, N2)), directed=False)
Lc2 = np.bincount(lab2[A[m2]], weights=new["L"][m2], minlength=n2)
main2 = int(Lc2.argmax())
sel = []
for e in ed.tolist():
    if not new["narrow"][e]:
        continue
    if lab2[A[e]] != main2 or lab2[B[e]] != main2:
        sel.append(e)
log(f"\n[표본 모집단] 성산읍, 5월 폭 3m 이상→새 폭 3m 미만, 끝 노드가 조각에 붙은 간선 {len(sel)}개")
random.seed(20261110)
pick = random.sample(sel, min(12, len(sel)))
items = []
for i, e in enumerate(pick):
    q = densify(new, e)
    c = q[len(q) // 2]
    near_i = int(np.argmin(np.hypot(*(pn - c).T)))
    _, im = tree.query(c)
    items.append(dict(id=f"W{i + 1:02d}", x=round(float(c[0])), y=round(float(c[1])), z=13, e=e, 새폭=float(new["wid"][new["rec"][e]]), 월5폭=float(wm[im])))
json.dump(items, open(os.path.join(HERE, "폭변화표본.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(json.dumps([[i["id"], i["x"], i["y"], i["z"]] for i in items], separators=(",", ":")))
log("끝")

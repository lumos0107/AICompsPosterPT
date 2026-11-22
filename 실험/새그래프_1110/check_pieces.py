"""폭 3m 미만 제외 뒤 연결 요소가 5월 240개 -> 새 자료 686개로 늘어난 원인을 찾는다. 원본은 읽기만 한다.
조각마다: 전체 그래프에서 주 요소에 붙어 있었는지(폭 3m 미만 도로로만 이어진 곳), 소구역 안인지, 어느 읍면동인지,
같은 자리의 5월 도로가 어떤 상태였는지를 잰다.
실행: py -I check_pieces.py (build_graph.py 뒤)
결과: 조각점검.out, 조각목록_새자료.csv
"""
import collections
import csv
import os
import sys

import numpy as np
from pyproj import Transformer
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

HERE = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\새그래프_1110"
sys.path.insert(0, r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\데이터진단_1109\수집계획용\에이전트검토")
from lib_shp import FILES, dbf_columns, dbf_fields, read_shp

sys.stdout.reconfigure(encoding="utf-8")
out = open(os.path.join(HERE, "조각점검.out"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out.write(s + "\n")
    out.flush()


RAW = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵"
ROAD = os.path.join(RAW, "연속수치지도_제주_20261109", "풀기", "N3L_A0020000", "N3L_A0020000")
EMD = os.path.join(RAW, "연속수치지도_제주_20261109_추가", "풀기", "N3A_G0110000", "N3A_G0110000")
to5179 = Transformer.from_crs(4326, 5179, always_xy=True)
REGIONS = {"제주시 시험구역": (33.46, 33.54, 126.46, 126.58), "서귀포시내": (33.24, 33.27, 126.53, 126.60)}
BOXES = {}
for name, (la0, la1, lo0, lo1) in REGIONS.items():
    x0, y0 = to5179.transform(lo0, la0)
    x1, y1 = to5179.transform(lo1, la1)
    BOXES[name] = (x0, y0, x1, y1)


def cc(A, B, L, N, mask):
    n, lab = connected_components(coo_matrix((np.ones(int(mask.sum())), (A[mask], B[mask])), shape=(N, N)), directed=False)
    return n, lab, np.bincount(lab[A[mask]], weights=L[mask], minlength=n)


def load(npz, base):
    d = dict(np.load(os.path.join(HERE, npz)))
    d["lines"] = [p for _, parts in read_shp(base, clip=False) for p in parts]
    d["wid"] = np.array([float(x or 0) for x in dbf_columns(base, ["RVWD"])["RVWD"]])
    d["N"] = len(d["xy"])
    full = np.ones(len(d["A"]), bool)
    n, lab, Lc = cc(d["A"], d["B"], d["L"], d["N"], full)
    d["lab_full"], d["m_full"] = lab, int(Lc.argmax())
    m = ~d["narrow"]
    n2, lab2, Lc2 = cc(d["A"], d["B"], d["L"], d["N"], m)
    d["lab_w"], d["Lc_w"], d["m_w"], d["mask_w"] = lab2, Lc2, int(Lc2.argmax()), m
    return d


def densify(d, ei, step=5.0):
    p = d["lines"][d["line"][ei]][d["a"][ei]:d["b"][ei] + 1]
    c = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]
    if c[-1] <= 0:
        return p[:1]
    t = np.r_[np.arange(0, c[-1], step), c[-1]]
    return np.c_[np.interp(t, c, p[:, 0]), np.interp(t, c, p[:, 1])]


def pieces(d):
    """폭 제외 그래프의 주 요소 밖 조각. 반환: 조각 -> 간선 번호들."""
    A, lab, m, mask = d["A"], d["lab_w"], d["m_w"], d["mask_w"]
    out_ = collections.defaultdict(list)
    for ei in np.where(mask)[0].tolist():
        c = int(lab[A[ei]])
        if c != m:
            out_[c].append(ei)
    return out_


new = load("그래프_새자료.npz", ROAD)
may = load("그래프_5월사본.npz", FILES["road"])
log(f"폭 제외 그래프의 요소 수: 5월 {int((may['Lc_w'] > 0).sum())}, 새 자료 {int((new['Lc_w'] > 0).sum())}")

# 읍면동
emd_names = dbf_columns(EMD, ["NAME"])["NAME"] if "NAME" in [f[0] for f in dbf_fields(EMD)[3]] else None
log("읍면동 항목:", [f[0] for f in dbf_fields(EMD)[3]])
polys = [(rc, rings, np.vstack(rings)) for rc, rings in read_shp(EMD, clip=False)]
boxes = np.array([[p[2][:, 0].min(), p[2][:, 1].min(), p[2][:, 0].max(), p[2][:, 1].max()] for p in polys])


def in_ring(x, y, rings):
    c = False
    for r in rings:
        xs, ys = r[:, 0], r[:, 1]
        h = ((ys[:-1] > y) != (ys[1:] > y))
        if h.any():
            xi = (xs[1:][h] - xs[:-1][h]) * (y - ys[:-1][h]) / (ys[1:][h] - ys[:-1][h]) + xs[:-1][h]
            c ^= bool((x < xi).sum() % 2)
    return c


def emd_of(x, y):
    for i in np.where((boxes[:, 0] <= x) & (boxes[:, 2] >= x) & (boxes[:, 1] <= y) & (boxes[:, 3] >= y))[0].tolist():
        if in_ring(x, y, polys[i][1]):
            return emd_names[polys[i][0]] if emd_names else str(polys[i][0])
    return "(경계 밖)"


# 5월 도로 점 나무: 폭 3m 이상 여부, 폭 제외 그래프의 주 요소 여부
pts, flag_narrow, flag_main, wids = [], [], [], []
for ei in range(len(may["A"])):
    q = densify(may, ei)
    pts.append(q)
    flag_narrow.append(np.full(len(q), bool(may["narrow"][ei])))
    flag_main.append(np.full(len(q), (not may["narrow"][ei]) and may["lab_w"][may["A"][ei]] == may["m_w"]))
    wids.append(np.full(len(q), may["wid"][may["rec"][ei]]))
pts, flag_narrow, flag_main, wids = np.vstack(pts), np.concatenate(flag_narrow), np.concatenate(flag_main), np.concatenate(wids)
tree = cKDTree(pts)
log("5월 도로 점", len(pts))

# 조각별 분류 (새 자료)
A, B, L, xy, mask = new["A"], new["B"], new["L"], new["xy"], new["mask_w"]
narrow = new["narrow"]
inc = collections.defaultdict(list)
for ei in range(len(A)):
    inc[int(A[ei])].append(ei)
    inc[int(B[ei])].append(ei)
P = pieces(new)
log(f"새 자료 주 요소 밖 조각 {len(P)}개 (섬 조각 포함)")
rows = []
for c, es in P.items():
    es = np.array(es)
    isl = bool(new["island"][es].any())
    tied = bool(new["lab_full"][A[es[0]]] == new["m_full"])
    q = np.vstack([densify(new, e) for e in es.tolist()])
    d, idx = tree.query(q, workers=-1)
    near = d <= 3.0
    frac = float(near.mean())
    may_main = float(flag_main[idx[near]].mean()) if near.any() else 0.0
    may_narrow = float(flag_narrow[idx[near]].mean()) if near.any() else 0.0
    # 조각에 붙은 폭 3m 미만 간선과 그 자리의 5월 폭
    nodes = np.unique(np.r_[A[es], B[es]]).tolist()
    bord = sorted({e for n in nodes for e in inc[n] if narrow[e]})
    bq = np.vstack([densify(new, e) for e in bord]) if bord else np.empty((0, 2))
    if len(bq):
        d2, i2 = tree.query(bq, workers=-1)
        nb = d2 <= 3.0
        bm = float(nb.mean())
        b_ge3 = float((wids[i2[nb]] >= 3).mean()) if nb.any() else 0.0
    else:
        bm, b_ge3 = 0.0, 0.0
    if frac < 0.5:
        cat = "5월에 없던 자리"
    elif may_narrow >= 0.5:
        cat = "5월엔 폭 3m 미만"
    elif may_main >= 0.5:
        cat = "5월엔 주 요소"
    else:
        cat = "5월에도 조각"
    mx, my = q.mean(0)
    region = "밖"
    for nm, (x0, y0, x1, y1) in BOXES.items():
        if ((q[:, 0] >= x0) & (q[:, 0] <= x1) & (q[:, 1] >= y0) & (q[:, 1] <= y1)).any():
            region = nm
    rows.append(dict(조각=c, 길이m=round(float(L[es].sum()), 1), 간선=len(es), 섬=int(isl), 폭미달로만연결=int(tied and not isl), 소구역=region, 읍면동=emd_of(mx, my),
                     분류=cat, 일치비율=round(frac, 2), 붙은폭미달간선=len(bord), 붙은간선자리_5월있음=round(bm, 2), 그중5월폭3이상=round(b_ge3, 2), 평균폭=round(float(new["wid"][new["rec"][es]].mean()), 1), x=round(float(mx)), y=round(float(my))))
with open(os.path.join(HERE, "조각목록_새자료.csv"), "w", encoding="utf-8-sig", newline="") as f:
    wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    wr.writeheader()
    wr.writerows(rows)

# 같은 분류를 5월 사본에도 (전체 그래프 연결 여부만)
PM = pieces(may)
m_tied, m_sep, m_isl, m_t_km, m_s_km = 0, 0, 0, 0.0, 0.0
for c, es in PM.items():
    es = np.array(es)
    km = float(may["L"][es].sum() / 1000)
    if may["island"][es].any():
        m_isl += 1
    elif may["lab_full"][may["A"][es[0]]] == may["m_full"]:
        m_tied += 1
        m_t_km += km
    else:
        m_sep += 1
        m_s_km += km
main_rows = [r for r in rows if not r["섬"]]
n_t = [r for r in main_rows if r["폭미달로만연결"]]
n_s = [r for r in main_rows if not r["폭미달로만연결"]]
km = lambda rs: sum(r["길이m"] for r in rs) / 1000
log("\n[조각 분류: 주 요소 밖, 폭 제외 그래프]")
log(f"구분 | 5월 | 새 자료")
log(f"섬 조각 | {m_isl} | {sum(1 for r in rows if r['섬'])}")
log(f"폭 3m 미만 도로로만 이어져 있던 조각 | {m_tied}개 {m_t_km:.1f}km | {len(n_t)}개 {km(n_t):.1f}km")
log(f"전체 그래프에서도 떨어져 있던 조각 | {m_sep}개 {m_s_km:.1f}km | {len(n_s)}개 {km(n_s):.1f}km")

log("\n[새 자료 조각, 같은 자리 5월 상태]")
for k, g in sorted(collections.Counter(r["분류"] for r in main_rows).items(), key=lambda v: -v[1]):
    rs = [r for r in main_rows if r["분류"] == k]
    log(f"{k}: {g}개 {km(rs):.1f}km, 그중 폭 미달로만 연결 {sum(r['폭미달로만연결'] for r in rs)}개, 길이 중앙값 {np.median([r['길이m'] for r in rs]):.0f}m")

log("\n[길이 구간]")
for lo, hi, nm in [(0, 50, "50m 미만"), (50, 200, "50~200m"), (200, 1000, "200m~1km"), (1000, 5000, "1~5km"), (5000, 1e12, "5km 이상")]:
    rs = [r for r in main_rows if lo <= r["길이m"] < hi]
    log(f"{nm}: {len(rs)}개 {km(rs):.1f}km, 폭 미달로만 연결 {sum(r['폭미달로만연결'] for r in rs)}개")

log("\n[소구역]")
for nm in list(BOXES) + ["밖"]:
    rs = [r for r in main_rows if r["소구역"] == nm]
    log(f"{nm}: {len(rs)}개 {km(rs):.1f}km, 폭 미달로만 연결 {sum(r['폭미달로만연결'] for r in rs)}개, 전체에서도 분리 {sum(1 - r['폭미달로만연결'] for r in rs)}개")

log("\n[읍면동 상위 15, 새 자료]")
cnt = collections.Counter(r["읍면동"] for r in main_rows)
for nm, c in cnt.most_common(15):
    rs = [r for r in main_rows if r["읍면동"] == nm]
    log(f"{nm}: {c}개 {km(rs):.1f}km, 폭 미달로만 연결 {sum(r['폭미달로만연결'] for r in rs)}개")

mm = [r for r in main_rows if r["분류"] == "5월엔 주 요소"]
log("\n[5월엔 주 요소였던 조각: 붙은 폭 미달 간선 자리의 5월 상태]")
log(f"{len(mm)}개, 붙은 폭 미달 간선 자리가 5월에도 있던 평균 비율 {np.mean([r['붙은간선자리_5월있음'] for r in mm]) if mm else 0:.2f}, 그 자리 5월 폭 3m 이상 평균 비율 {np.mean([r['그중5월폭3이상'] for r in mm]) if mm else 0:.2f}")
log(f"붙은 폭 미달 간선 자리 5월 폭 3m 이상 비율 50% 이상인 조각 {sum(1 for r in mm if r['그중5월폭3이상'] >= 0.5)}개")
log("끝")

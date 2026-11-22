"""도로중심선 그래프를 만들고 연결·겹침 기준을 5월 사본과 새 자료에 같은 방식으로 잰다. 원본은 읽기만 한다.

규칙은 소구역점검_1109/check_connect.py와 같다.
  1cm 공유 꼭짓점 -> 분기점에서 자름 -> 막다른 노드 1m 보정 -> (전체 도로로 그래프를 만든 뒤) 폭·섬 제외.
섬은 폭을 빼기 전 전체 그래프에서 판별해 간선 표시로 들고 간다(폭 제외로 섬이 5km 밑으로 쪼개져도 빠지지 않게).
겹친 길은 데이터진단_1109 s4_graph.py(간선 15m 분할)와 s7_extra.py(선 단위, 분할 간격 민감도)와 같은 정의다.

실행: py -I build_graph.py
결과: 같은 폴더 그래프점검.out, 그래프점검.json, 그래프_새자료.npz
"""
import collections
import json
import os
import sys
import time

import numpy as np
from pyproj import Transformer
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

HERE = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\새그래프_1110"
sys.path.insert(0, r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\데이터진단_1109\수집계획용\에이전트검토")
from lib_shp import FILES, dbf_columns, dbf_fields, read_shp

sys.stdout.reconfigure(encoding="utf-8")
out = open(os.path.join(HERE, "그래프점검.out"), "w", encoding="utf-8")
RAW = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵\연속수치지도_제주_20261109\풀기"
SOURCES = {"5월 사본": FILES["road"], "새 자료": os.path.join(RAW, "N3L_A0020000", "N3L_A0020000")}
STAIR = os.path.join(RAW, "N3A_C0390000", "N3A_C0390000")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out.write(s + "\n")
    out.flush()


T0 = time.time()
to5179 = Transformer.from_crs(4326, 5179, always_xy=True)
to4326 = Transformer.from_crs(5179, 4326, always_xy=True)
REGIONS = {"제주시 시험구역": (33.46, 33.54, 126.46, 126.58), "서귀포시내": (33.24, 33.27, 126.53, 126.60)}
BOXES = {}
for name, (la0, la1, lo0, lo1) in REGIONS.items():
    x0, y0 = to5179.transform(lo0, la0)
    x1, y1 = to5179.transform(lo1, la1)
    BOXES[name] = (x0, y0, x1, y1)
TEST = BOXES["제주시 시험구역"]
ISLANDS = {"우도": (33.50, 126.95), "추자도": (33.95, 126.31), "가파도": (33.17, 126.27), "비양도": (33.41, 126.23), "마라도": (33.12, 126.27)}


def build(lines):
    """check_connect.py 1)~3)과 같은 순서."""
    allv = np.vstack([p for _, p in lines])
    lid = np.concatenate([np.full(len(p), i) for i, (_, p) in enumerate(lines)])
    uk, vid = np.unique(np.round(allv / 0.01).astype(np.int64), axis=0, return_inverse=True)
    vid = vid.ravel()
    nline = np.bincount(np.unique(np.c_[vid, lid], axis=0)[:, 0], minlength=len(uk))
    xy = uk * 0.01
    off = np.cumsum([0] + [len(p) for _, p in lines])
    edges = []
    for i, (_, p) in enumerate(lines):
        ids = vid[off[i]:off[i + 1]]
        cut = [0] + [j for j in range(1, len(p) - 1) if nline[ids[j]] >= 2] + [len(p) - 1]
        for a, b in zip(cut[:-1], cut[1:]):
            edges.append((int(ids[a]), int(ids[b]), float(np.hypot(*np.diff(p[a:b + 1], axis=0).T).sum()), i, a, b))
    u = np.array([e[0] for e in edges])
    v = np.array([e[1] for e in edges])
    elen = np.array([e[2] for e in edges])
    deg = np.bincount(u, minlength=len(uk)) + np.bincount(v, minlength=len(uk))
    dead = np.where(deg == 1)[0]
    used = np.unique(np.r_[u, v])
    adj = collections.defaultdict(set)
    for a, b in zip(u.tolist(), v.tolist()):
        adj[a].add(b)
        adj[b].add(a)
    snap = []
    for dn, g in zip(dead.tolist(), cKDTree(xy[used]).query_ball_point(xy[dead], 1.0, workers=-1)):
        cand = [int(used[j]) for j in g if int(used[j]) != dn and int(used[j]) not in adj[dn]]
        if cand:
            snap.append((dn, min(cand, key=lambda w: float(np.hypot(*(xy[w] - xy[dn]))))))
    parent = list(range(len(uk)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in snap:
        parent[find(a)] = find(b)
    root = np.array([find(i) for i in range(len(uk))])
    uu, vv = root[u], root[v]
    keep = uu != vv
    nodes = np.unique(np.r_[uu, vv])
    remap = -np.ones(len(uk), int)
    remap[nodes] = np.arange(len(nodes))
    return dict(A=remap[uu[keep]], B=remap[vv[keep]], L=elen[keep], kept=[e for e, k in zip(edges, keep) if k],
                N=len(nodes), xyN=xy[nodes], nsnap=len(snap), nself=int((~keep).sum()))


def cc(A, B, L, N, mask):
    n, lab = connected_components(coo_matrix((np.ones(int(mask.sum())), (A[mask], B[mask])), shape=(N, N)), directed=False)
    Lc = np.bincount(lab[A[mask]], weights=L[mask], minlength=n)
    return n, lab, Lc


def split(p, step):
    seg = np.hypot(*np.diff(p, axis=0).T)
    cum = np.r_[0, np.cumsum(seg)]
    if cum[-1] <= 0:
        return None
    n = max(1, int(round(cum[-1] / step)))
    t = np.linspace(0, cum[-1], n + 1)
    q = np.c_[np.interp(t, cum, p[:, 0]), np.interp(t, cum, p[:, 1])]
    return q[:-1], q[1:]


def overlap(pieces, step, box):
    """audit.py / s4 / s7의 겹친 길 정의. 반환: {옆 거리: (겹친 km, 전체 km)}."""
    x0, y0, x1, y1 = box
    a_, b_ = [], []
    for p in pieces:
        if p[:, 0].max() < x0 - 50 or p[:, 0].min() > x1 + 50 or p[:, 1].max() < y0 - 50 or p[:, 1].min() > y1 + 50:
            continue
        r = split(p, step)
        if r is not None:
            a_.append(r[0])
            b_.append(r[1])
    a_, b_ = np.vstack(a_), np.vstack(b_)
    ids = np.unique(np.round(np.r_[a_, b_] / 0.01).astype(np.int64), axis=0, return_inverse=True)[1].ravel()
    fi, ti = ids[:len(a_)], ids[len(a_):]
    mid = (a_ + b_) / 2
    L2 = np.hypot(*(b_ - a_).T)
    idx = np.where((mid[:, 0] >= x0) & (mid[:, 0] <= x1) & (mid[:, 1] >= y0) & (mid[:, 1] <= y1) & (L2 >= 3))[0]
    mx, my = mid[idx].T
    dx, dy = (b_ - a_)[idx].T
    LL = np.hypot(dx, dy) + 1e-9
    ang = np.degrees(np.arctan2(dy, dx)) % 180
    ux, uy = dx / LL, dy / LL
    Fk, Tk = fi[idx], ti[idx]
    tr = cKDTree(np.c_[mx, my])
    res = {}
    for radius, latmax in [(14, 12), (32, 30)]:
        pr = tr.query_pairs(radius, output_type="ndarray")
        i, j = pr[:, 0], pr[:, 1]
        diff = np.abs(ang[i] - ang[j])
        diff = np.minimum(diff, 180 - diff)
        vx, vy = mx[j] - mx[i], my[j] - my[i]
        lat = np.abs(vx * uy[i] - vy * ux[i])
        al = np.abs(vx * ux[i] + vy * uy[i])
        share = (Fk[i] == Fk[j]) | (Fk[i] == Tk[j]) | (Tk[i] == Fk[j]) | (Tk[i] == Tk[j])
        near = (diff < 12) & (lat >= 1.0) & (lat <= latmax) & (al <= (LL[i] + LL[j]) / 2) & (~share)
        fl = np.zeros(len(idx), bool)
        fl[i[near]] = True
        fl[j[near]] = True
        res[latmax] = (float(LL[fl].sum() / 1000), float(LL.sum() / 1000))
    return res


def run(name, base):
    log(f"\n{'=' * 20} {name} {'=' * 20}")
    lines = [(rec, p) for rec, parts in read_shp(base, clip=False) for p in parts]
    attr = dbf_columns(base, ["RVWD", "PVQT"])
    raw_w = attr["RVWD"]
    wid = np.array([float(x or 0) for x in raw_w])
    pv = np.array(attr["PVQT"])
    g = build(lines)
    A, B, L, N, xyN, kept = g["A"], g["B"], g["L"], g["N"], g["xyN"], g["kept"]
    rec_e = np.array([lines[e[3]][0] for e in kept])
    log(f"선 {len(lines):,}, 레코드 {len(raw_w):,}, 1m 보정 대상 {g['nsnap']}, 노드 {N:,}, 간선 {len(A):,}, 자기루프 제거 {g['nself']}, 총 {L.sum() / 1000:,.1f}km")
    log(f"폭 빈칸 {sum(1 for x in raw_w if not x):,}건, 폭 0 이하 {int((wid <= 0).sum()):,}건 (빈칸·0은 폭 3m 미만으로 셈, check_connect와 같음)")
    for c in ("RDQ005", "RDQ006", "RDQ000"):
        log(f"  포장 {c}: {L[pv[rec_e] == c].sum() / 1000:,.1f}km")
    log(f"  포장 그 외 값: {collections.Counter(pv.tolist()).most_common(6)}")

    # 섬 판별 (전체 그래프)
    allm = np.ones(len(A), bool)
    nc, lab, Lcc = cc(A, B, L, N, allm)
    main = int(Lcc.argmax())
    m_pts = []
    for e, c in zip(kept, lab[A].tolist()):
        if c == main:
            p = lines[e[3]][1][e[4]:e[5] + 1]
            cum = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]
            t = np.r_[np.arange(0, cum[-1], 2.0), cum[-1]]
            m_pts.append(np.c_[np.interp(t, cum, p[:, 0]), np.interp(t, cum, p[:, 1])])
    tm = cKDTree(np.vstack(m_pts))
    del m_pts
    o_pts, o_lab = [], []
    for e, c in zip(kept, lab[A].tolist()):
        if c != main:
            p = lines[e[3]][1][e[4]:e[5] + 1]
            o_pts.append(p)
            o_lab.append(np.full(len(p), c))
    o_pts, o_lab = np.vstack(o_pts), np.concatenate(o_lab)
    d_all = tm.query(o_pts, workers=-1)[0]
    dmin = np.full(nc, np.inf)
    np.minimum.at(dmin, o_lab, d_all)
    cnt = np.maximum(np.bincount(o_lab, minlength=nc), 1)
    cx, cy = np.bincount(o_lab, weights=o_pts[:, 0], minlength=nc) / cnt, np.bincount(o_lab, weights=o_pts[:, 1], minlength=nc) / cnt
    islands = {}
    for c in range(nc):
        if c == main or Lcc[c] <= 5000 or dmin[c] <= 500:
            continue
        lo, la = to4326.transform(cx[c], cy[c])
        for nm, (a, b) in ISLANDS.items():
            if abs(la - a) < 0.03 and abs(lo - b) < 0.03:
                islands.setdefault(nm, []).append(c)
    log("[섬 판별] " + ", ".join(f"{nm} {len(cs)}조각 {sum(Lcc[c] for c in cs) / 1000:.1f}km" for nm, cs in islands.items()))
    log(f"  판별된 섬 이름 {sorted(islands)}, 빠진 섬 {sorted(set(ISLANDS) - set(islands))}")
    isl_comp = [c for cs in islands.values() for c in cs]
    island = np.isin(lab[A], isl_comp)
    narrow = wid[rec_e] < 3
    mid = (xyN[A] + xyN[B]) / 2

    # 네 경우
    conds = {"전체": allm, "섬 제외": ~island, "폭 3m 미만 제외": ~narrow, "둘 다 제외": ~narrow & ~island}
    res = {"연결": {}, "소구역": {}}
    labs = {}
    for cname, mask in conds.items():
        n2, lab2, Lc2 = cc(A, B, L, N, mask)
        m2 = int(Lc2.argmax())
        labs[cname] = (lab2, m2)
        tot = L[mask].sum()
        res["연결"][cname] = dict(총km=tot / 1000, 주요소km=Lc2[m2] / 1000, 비율=Lc2[m2] / tot, 요소=int((Lc2 > 0).sum()))
        log(f"[{cname}] 도로 {tot / 1000:,.1f}km, 요소 {int((Lc2 > 0).sum()):,}, 주 요소 {Lc2[m2] / 1000:,.1f}km, 비율 {Lc2[m2] / tot:.2%}")
        res["소구역"][cname] = {}
        for rname, (x0, y0, x1, y1) in BOXES.items():
            ib = (mid[:, 0] >= x0) & (mid[:, 0] <= x1) & (mid[:, 1] >= y0) & (mid[:, 1] <= y1)
            in_m = mask & (lab2[A] == m2)
            d = L[ib & mask].sum()
            nb, lb, Lb = cc(A, B, L, N, ib & mask)
            res["소구역"][cname][rname] = dict(도로km=d / 1000, 주요소km=L[ib & in_m].sum() / 1000, 비율=L[ib & in_m].sum() / d, 상자안최대=Lb.max() / Lb.sum(), 상자안요소=int((Lb > 0).sum()))
            r = res["소구역"][cname][rname]
            log(f"   {rname}: 도로 {r['도로km']:,.1f}km, 전체 주 요소 소속 {r['비율']:.2%}, 상자 안만의 최대 요소 {r['상자안최대']:.2%} (요소 {r['상자안요소']:,})")

    # 폭 제외 뒤 섬이 5km 밑으로 쪼개지는지 (handoff 5장 주의)
    lab3, m3 = labs["폭 3m 미만 제외"]
    mask3 = ~narrow & island
    pieces = collections.Counter(lab3[A[mask3]].tolist())
    plen = np.bincount(lab3[A[mask3]], weights=L[mask3], minlength=lab3.max() + 1)
    small = [c for c in pieces if plen[c] <= 5000]
    big = [c for c in pieces if plen[c] > 5000]
    alt = conds["폭 3m 미만 제외"]
    Lmain3 = L[alt & (lab3[A] == m3)].sum()
    alt_den = L[alt].sum() - plen[big].sum()
    log(f"[폭 제외 뒤 섬] 남은 섬 도로 {L[mask3].sum() / 1000:.1f}km, 조각 {len(pieces)}개, 5km 초과 {len(big)}개 {plen[big].sum() / 1000:.1f}km, 5km 이하 {len(small)}개 {plen[small].sum() / 1000:.1f}km")
    log(f"  만약 폭을 뺀 뒤 5km 규칙으로 섬을 다시 판별했다면 비율 {Lmain3 / alt_den:.2%} (5km 이하 조각이 분모에 남음). 본 표는 전체 그래프에서 판별한 값을 쓴다.")
    res["폭제외뒤섬"] = dict(조각=len(pieces), 초과5km=len(big), 이하5km=len(small), 이하5km_km=float(plen[small].sum() / 1000), 재판별비율=float(Lmain3 / alt_den))

    # 겹친 길
    polys = [lines[e[3]][1][e[4]:e[5] + 1] for e in kept]
    polys_w = [p for p, n in zip(polys, narrow.tolist()) if not n]
    raw = [p for _, p in lines]
    raw_w_lines = [p for r, p in lines if wid[r] >= 3]
    res["겹침"] = {}
    r = overlap(polys, 15.0, TEST)
    r2 = overlap(polys_w, 15.0, TEST)
    res["겹침"]["간선15m"] = {"전체": r[12], "폭제외": r2[12], "전체30": r[30], "폭제외30": r2[30]}
    log(f"[겹친 길, 간선 15m 분할] 전체: 12m {r[12][0]:.1f}/{r[12][1]:,.1f}km = {r[12][0] / r[12][1]:.2%}, 30m {r[30][0] / r[30][1]:.2%} | 폭 제외: 12m {r2[12][0]:.1f}/{r2[12][1]:,.1f}km = {r2[12][0] / r2[12][1]:.2%}, 30m {r2[30][0] / r2[30][1]:.2%}")
    res["겹침"]["선분할"] = {}
    for step in (10.0, 15.0, 20.0, 30.0):
        r = overlap(raw, step, TEST)
        r2 = overlap(raw_w_lines, step, TEST)
        res["겹침"]["선분할"][str(int(step))] = {"전체": r[12], "폭제외": r2[12], "전체30": r[30], "폭제외30": r2[30]}
        log(f"[겹친 길, 선 단위 {int(step)}m 분할] 전체 12m {r[12][0] / r[12][1]:.2%} (총 {r[12][1]:,.0f}km), 폭 제외 12m {r2[12][0] / r2[12][1]:.2%} (총 {r2[12][1]:,.0f}km)")
    return res, g, lines, rec_e, narrow, island, labs


results = {}
kept_new = None
for nm, base in SOURCES.items():
    r, g, lines, rec_e, narrow, island, labs = run(nm, base)
    results[nm] = r
    if nm == "새 자료":
        kept_new = (g, lines, rec_e, narrow, island, labs)
    else:
        kept = g["kept"]
        np.savez_compressed(os.path.join(HERE, "그래프_5월사본.npz"), xy=g["xyN"], A=g["A"], B=g["B"], L=g["L"], rec=rec_e,
                            line=np.array([e[3] for e in kept]), a=np.array([e[4] for e in kept]), b=np.array([e[5] for e in kept]),
                            narrow=narrow, island=island)
    log(f"경과 {time.time() - T0:.1f}초")

# 계단: 새 자료에만 적용. 네 경우 비교에는 넣지 않는다.
g, lines, rec_e, narrow, island, labs = kept_new
A, B, L, N, kept = g["A"], g["B"], g["L"], g["N"], g["kept"]
log(f"\n{'=' * 20} 계단 (새 자료) {'=' * 20}")
n, hlen, rlen, fields = dbf_fields(STAIR)
log("계단 항목:", [f[0] for f in fields])
stru = np.array(dbf_columns(STAIR, ["STRU"])["STRU"])
log("STRU 분포", collections.Counter(stru.tolist()).most_common())
polys_st = [(rec, parts) for rec, parts in read_shp(STAIR, clip=False) if stru[rec] == "SRD001"]
ebox = np.array([[lines[e[3]][1][e[4]:e[5] + 1][:, 0].min(), lines[e[3]][1][e[4]:e[5] + 1][:, 1].min(),
                  lines[e[3]][1][e[4]:e[5] + 1][:, 0].max(), lines[e[3]][1][e[4]:e[5] + 1][:, 1].max()] for e in kept])


def inside(pts, rings):
    """짝홀 규칙. rings는 꼭짓점 배열 목록."""
    x, y = pts[:, 0], pts[:, 1]
    c = np.zeros(len(pts), bool)
    for r in rings:
        x0, y0 = r[:-1, 0], r[:-1, 1]
        x1, y1 = r[1:, 0], r[1:, 1]
        for a, b, cc_, d in zip(x0, y0, x1, y1):
            if b == d:
                continue
            c ^= ((b > y) != (d > y)) & (x < (cc_ - a) * (y - b) / (d - b) + a)
    return c


stair_len = np.zeros(len(A))
stair_hit = np.zeros(len(polys_st), int)
for pi, (_, rings) in enumerate(polys_st):
    allr = np.vstack(rings)
    bx0, by0, bx1, by1 = allr[:, 0].min(), allr[:, 1].min(), allr[:, 0].max(), allr[:, 1].max()
    cand = np.where((ebox[:, 2] >= bx0) & (ebox[:, 0] <= bx1) & (ebox[:, 3] >= by0) & (ebox[:, 1] <= by1))[0]
    for ei in cand.tolist():
        e = kept[ei]
        p = lines[e[3]][1][e[4]:e[5] + 1]
        cum = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]
        if cum[-1] <= 0:
            continue
        t = np.arange(0.25, cum[-1], 0.5)
        if len(t) == 0:
            continue
        q = np.c_[np.interp(t, cum, p[:, 0]), np.interp(t, cum, p[:, 1])]
        il = float(inside(q, rings).sum() * 0.5)
        if il > 0:
            stair_len[ei] += il
            stair_hit[pi] += 1
log(f"SRD001 면 {len(polys_st)}개, 도로와 겹치는 면 {int((stair_hit > 0).sum())}개, 겹치는 간선 {int((stair_len > 0).sum()):,}개")
for th in (0.5, 1, 3, 5, 10):
    m = stair_len >= th
    log(f"  계단 면 안 길이 {th}m 이상: 간선 {int(m.sum()):,}개 {L[m].sum() / 1000:.2f}km, 그중 폭 3m 이상 {int((m & ~narrow).sum()):,}개 {L[m & ~narrow].sum() / 1000:.2f}km")
ratio = stair_len[stair_len > 0] / L[stair_len > 0]
log(f"  간선 길이 중 계단 면 안 비율: 중앙값 {np.median(ratio):.2f}, 50% 이상 {int((ratio >= 0.5).sum()):,}개, 90% 이상 {int((ratio >= 0.9).sum()):,}개")

np.savez_compressed(os.path.join(HERE, "그래프_새자료.npz"), xy=g["xyN"], A=A, B=B, L=L, rec=rec_e,
                    line=np.array([e[3] for e in kept]), a=np.array([e[4] for e in kept]), b=np.array([e[5] for e in kept]),
                    narrow=narrow, island=island, stair_len=stair_len, main_all=labs["전체"][0][A] == labs["전체"][1],
                    main_both=labs["둘 다 제외"][0][A] == labs["둘 다 제외"][1])
json.dump(results, open(os.path.join(HERE, "그래프점검.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
log("\n끝", round(time.time() - T0, 1), "초")

"""예비 경로가 지나는 교차 중 입체 확인 후보를 고른다 (입체 점검 1110과 같은 기준).

경로가 한 도로 선(레코드)에서 다른 선으로 옮겨 타는 그래프 노드만 본다(같은 선을 따라 지나면 잘못된 연결이 경로에 영향 없음).
후보: (가) 교량·육교·입체교차부·입체교차점·인터체인지 면 안 또는 3 m 안, (나) 차수 4 이상이고 폭 15 m 이상 도로가 붙은 노드.
결과: 경로교차.json(후보와 캡처 좌표), 경로교차.out
실행: py -I route_crossings.py [결과json=예비경로.json] [접미사=예비]
"""
import collections
import json
import math
import os
import sys

import numpy as np
from matplotlib.path import Path
from pyproj import Transformer
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(EXP, "데이터진단_1109", "수집계획용", "에이전트검토"))
from lib_shp import read_shp, dbf_columns

sys.stdout.reconfigure(encoding="utf-8")
SRC = sys.argv[1] if len(sys.argv) > 1 else "예비경로.json"
TAG = sys.argv[2] if len(sys.argv) > 2 else "예비"
OUT = open(os.path.join(HERE, f"경로교차_{TAG}.out"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    OUT.write(s + "\n")


N3 = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵\연속수치지도_제주_20261109\풀기"
RAW = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본"
ROAD = os.path.join(N3, "N3L_A0020000", "N3L_A0020000")
POLY = [("입체교차부", os.path.join(RAW, "브이월드", "입체교차부_30223", "풀기", "N3A_A0090000")),
        ("교차로(입체교차점)", os.path.join(N3, "N3A_A0080000", "N3A_A0080000")),
        ("인터체인지", os.path.join(N3, "N3A_A0100000", "N3A_A0100000")),
        ("육교", os.path.join(N3, "N3A_A0063321", "N3A_A0063321")),
        ("교량", os.path.join(N3, "N3A_A0070000", "N3A_A0070000"))]
g = np.load(os.path.join(EXP, "도심실험_1110", "그래프_도심_114칸.npz"))
xy, A, B, main, rec, deg = g["xy"], g["A"], g["B"], g["main"], g["rec"], g["deg_full"]
wid = np.array([float(x or 0) for x in dbf_columns(ROAD, ["RVWD"])["RVWD"]])
E = np.where(main)[0]
gnodes = np.unique(np.r_[A[E], B[E]])     # build_v3_db.py와 같은 순서: v3 번호 = 위치 + 1
NG = len(gnodes)
inc = collections.defaultdict(list)       # 그래프 노드 → [(간선, 다른 끝)]
for e in E.tolist():
    inc[int(A[e])].append((e, int(B[e])))
    inc[int(B[e])].append((e, int(A[e])))
to_wgs = Transformer.from_crs(5179, 4326, always_xy=True)
from_wgs = Transformer.from_crs(4326, 5179, always_xy=True)

# 면
polys = []
x0, y0 = xy[gnodes].min(0) - 100
x1, y1 = xy[gnodes].max(0) + 100
for kind, base in POLY:
    kinds_attr = dbf_columns(base, ["KIND"])["KIND"] if kind == "교차로(입체교차점)" else None
    for k, (r, parts) in enumerate(read_shp(base, clip=False)):
        if kinds_attr is not None and kinds_attr[k] != "CRK002":   # 교차로 면은 입체교차점만
            continue
        for ring in parts:
            if ring[:, 0].max() < x0 or ring[:, 0].min() > x1 or ring[:, 1].max() < y0 or ring[:, 1].min() > y1:
                continue
            polys.append((kind, Path(ring), ring))


def near_poly(p):
    out = []
    for kind, path, ring in polys:
        if p[0] < ring[:, 0].min() - 3 or p[0] > ring[:, 0].max() + 3 or p[1] < ring[:, 1].min() - 3 or p[1] > ring[:, 1].max() + 3:
            continue
        if path.contains_point(p) or path.contains_point(p, radius=3.0) or path.contains_point(p, radius=-3.0):
            out.append(kind)
    return out


res = json.load(open(os.path.join(HERE, SRC), encoding="utf-8"))
gpos = {i + 1: int(n) for i, n in enumerate(gnodes.tolist())}   # v3 번호 → 원 그래프 노드
tg = cKDTree(xy[gnodes])
switch_total, cand = 0, {}
per_route = []
for ri, m in enumerate(res):
    nodes = m["nodes"]
    coords = m["coords"]
    sw, cs = 0, 0
    for k in range(1, len(nodes) - 1):
        v = nodes[k]
        if v not in gpos:
            continue
        n = gpos[v]
        if deg[n] < 3:   # 차수 2는 선 두 개가 끝끼리 이어진 곳이라 교차가 아님
            continue
        # 들어온·나간 방향의 원 간선: 앞뒤 경로 점에 가장 가까운 '이 노드에 붙은 간선'
        def edge_toward(c):
            px, py = from_wgs.transform(c[1], c[0])
            best, bd = None, 1e18
            for e, o in inc[n]:
                d = math.hypot(xy[o, 0] - px, xy[o, 1] - py)
                # 다른 끝까지가 아니라 방향으로 고른다
                vx, vy = xy[o] - xy[n]
                wx, wy = px - xy[n, 0], py - xy[n, 1]
                cosang = (vx * wx + vy * wy) / (math.hypot(vx, vy) * math.hypot(wx, wy) + 1e-9)
                if -cosang < bd:
                    bd, best = -cosang, e
            return best
        ein, eout = edge_toward(coords[k - 1]), edge_toward(coords[k + 1])
        if ein is None or eout is None or rec[ein] == rec[eout]:
            continue
        sw += 1
        kinds = near_poly(xy[n])
        wmax = max(wid[rec[e]] for e, _ in inc[n])
        wide = deg[n] >= 4 and wmax >= 15
        if kinds or wide:
            cs += 1
            c = cand.setdefault(n, dict(node=n, v3=v, x=round(float(xy[n, 0])), y=round(float(xy[n, 1])), kinds=kinds, deg=int(deg[n]),
                                        widths=sorted({float(wid[rec[e]]) for e, _ in inc[n]}, reverse=True), routes=[]))
            c["routes"].append(f"{m['start']}-{m.get('anchor_id', 0)}-{m['setting']}-{m['route']}")
    switch_total += sw
    per_route.append((m["start"], m["setting"], m["route"], sw, cs))
for r in per_route:
    log(f"{r[0]} {r[1]} 경로{r[2]}: 도로를 옮겨 타는 교차 {r[3]}곳, 입체 확인 후보 {r[4]}곳")
log(f"\n경로 {len(res)}개: 도로를 옮겨 타는 교차 합계 {switch_total}(경로별 합), 입체 확인 후보 노드 {len(cand)}곳(중복 제거)")
log("후보 종류:", collections.Counter(("면:" + "/".join(sorted(set(c["kinds"])))) if c["kinds"] else "넓은 도로 차수4+" for c in cand.values()).most_common())
items = []
for k, c in enumerate(sorted(cand.values(), key=lambda c: (c["x"], c["y"]))):
    c["id"] = f"X{k + 1:02d}"
    lo, la = to_wgs.transform(c["x"], c["y"])
    c["lat"], c["lon"] = round(la, 6), round(lo, 6)
    items.append(c)
    log(f"  {c['id']} {c['lat']},{c['lon']} 차수 {c['deg']} 폭 {c['widths'][:4]} 면 {c['kinds']} 경로 {len(c['routes'])}개")
json.dump(items, open(os.path.join(HERE, f"경로교차_{TAG}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
log("끝")

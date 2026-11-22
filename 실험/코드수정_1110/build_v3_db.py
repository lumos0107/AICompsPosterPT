"""실험 그래프(114칸)를 새 DB gildongmu_v3에 넣고 노드 속성 파일을 만든다 (2026-11-10).

- 그래프: ../도심실험_1110/그래프_도심_114칸.npz 의 주 요소(main). 간선 폴리라인의 원본 꼭짓점은
  누적 15 m마다 하나만 남겨 차수 2 노드로 넣는다(v2b와 같은 규칙, 팀 코드가 노드 사이 직선거리를 쓰므로).
- 고도: ../새그래프_1110/고도격자_10m.npy 쌍선형 보간. 1:5,000 교량 면(N3A_A0070000) 안의 노드는
  같은 사슬에서 교량 밖에 있는 앞뒤 노드 사이를 길이 비례로 직선 보간(계획서 '교량 양 끝 보간').
- 출발점·안내점 후보(osm_node_id): 차수≠2 노드(팀 코드는 osm_node_id가 있는 점에만 스냅).
- obstacles, places는 비워 둔다(선호 방식은 노드 속성 파일을 쓴다). users는 gildongmu_v2b에서 복사.
- 노드 속성 파일: point_id,signal,facility_m. 신호 = ../도심실험_1110/신호노드_114칸.csv,
  시설 거리 = ../새그래프_1110/편의시설.csv(화장실·편의점·공원) 중 가장 가까운 것까지 직선거리(m, 500 상한).
- 기존 DB(gildongmu, gildongmu_v2, gildongmu_v2b)는 건드리지 않는다. gildongmu_v3에 표가 있으면 중단.
실행: py -I build_v3_db.py [--rebuild]   결과: v3_stats.json, 노드속성_v3.csv, build_v3.log
"""
import collections
import csv
import json
import math
import os
import re
import sys
import time

import numpy as np
import pymysql
from matplotlib.path import Path
from pyproj import Transformer
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(EXP, "데이터진단_1109", "수집계획용", "에이전트검토"))
from lib_shp import read_shp

sys.stdout.reconfigure(encoding="utf-8")
LOG = open(os.path.join(HERE, "build_v3.log"), "w", encoding="utf-8")
T0 = time.time()


def log(*a):
    s = f"[{time.time() - T0:5.0f}s] " + " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.write(s + "\n")
    LOG.flush()


ROAD = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵\연속수치지도_제주_20261109\풀기\N3L_A0020000\N3L_A0020000"
BRIDGE = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵\연속수치지도_제주_20261109\풀기\N3A_A0070000\N3A_A0070000"
OLD_BUILD = r"C:\Users\seungjun\Documents\claude_code\논문\데이터사이언스학회\04_실험\새그래프_만들기\build_v2b_graph.py"
NEW_DB, USERS_FROM = "gildongmu_v3", "gildongmu_v2b"
RESAMPLE_M = 15.0

# ── 1. 그래프 ──
g = np.load(os.path.join(EXP, "도심실험_1110", "그래프_도심_114칸.npz"))
xy, A, B, main, gl, ga, gb, deg = g["xy"], g["A"], g["B"], g["main"], g["line"], g["a"], g["b"], g["deg_full"]
lines = [p for r, parts in read_shp(ROAD, clip=False) for p in parts]
E = np.where(main)[0]
gnodes = np.unique(np.r_[A[E], B[E]])
nid = {int(n): i for i, n in enumerate(gnodes.tolist())}   # 그래프 노드 → 새 번호(0부터)
NX, NY = list(xy[gnodes, 0]), list(xy[gnodes, 1])
chains = []   # 간선마다 [새 노드 번호들], [각 노드의 사슬 위 누적 길이]
for e in E.tolist():
    p = lines[gl[e]][ga[e]:gb[e] + 1]
    if np.hypot(*(p[0] - xy[A[e]])) > np.hypot(*(p[0] - xy[B[e]])):
        p = p[::-1]   # 폴리라인 방향을 A→B로 맞춤
    seg = np.hypot(*np.diff(p, axis=0).T)
    cum = np.r_[0, np.cumsum(seg)]
    ids, pos = [nid[int(A[e])]], [0.0]
    last = 0.0
    for k in range(1, len(p) - 1):
        if cum[k] - last >= RESAMPLE_M and cum[-1] - cum[k] >= RESAMPLE_M / 2:
            NX.append(p[k, 0]); NY.append(p[k, 1])
            ids.append(len(NX) - 1); pos.append(cum[k]); last = cum[k]
    ids.append(nid[int(B[e])]); pos.append(cum[-1])
    chains.append((ids, pos))
NX, NY = np.array(NX), np.array(NY)
N = len(NX)
edges = {}
for ids, pos in chains:
    for i in range(1, len(ids)):
        a, b = ids[i - 1], ids[i]
        if a == b:
            continue
        k = (min(a, b), max(a, b))
        L = pos[i] - pos[i - 1]
        edges[k] = min(L, edges.get(k, 1e18))
log(f"그래프 간선 {len(E):,}, 그래프 노드 {len(gnodes):,} → 노드 {N:,}, 간선 {len(edges):,}, 길이 {sum(edges.values()) / 1000:.1f}km")
degn = collections.Counter()
for a, b in edges:
    degn[a] += 1
    degn[b] += 1

# ── 2. 고도 ──
meta = json.load(open(os.path.join(EXP, "새그래프_1110", "고도격자_10m.json"), encoding="utf-8"))
Z = np.load(os.path.join(EXP, "새그래프_1110", "고도격자_10m.npy"))
fx = (NX - meta["x0"]) / meta["res"] - 0.5
fy = (NY - meta["y0"]) / meta["res"] - 0.5
ix, iy = np.floor(fx).astype(int), np.floor(fy).astype(int)
tx, ty = fx - ix, fy - iy
elev = (Z[iy, ix] * (1 - tx) * (1 - ty) + Z[iy, ix + 1] * tx * (1 - ty) + Z[iy + 1, ix] * (1 - tx) * ty + Z[iy + 1, ix + 1] * tx * ty)
log(f"고도: 누락 {int(np.isnan(elev).sum())}, 범위 {np.nanmin(elev):.1f}~{np.nanmax(elev):.1f}m")

# 교량 면 안 노드
x0, y0, x1, y1 = NX.min() - 50, NY.min() - 50, NX.max() + 50, NY.max() + 50
on_bridge = np.zeros(N, bool)
nb = 0
for rec, parts in read_shp(BRIDGE, clip=False):
    for ring in parts:
        if ring[:, 0].max() < x0 or ring[:, 0].min() > x1 or ring[:, 1].max() < y0 or ring[:, 1].min() > y1:
            continue
        nb += 1
        m = (NX >= ring[:, 0].min()) & (NX <= ring[:, 0].max()) & (NY >= ring[:, 1].min()) & (NY <= ring[:, 1].max())
        if m.any():
            idx = np.where(m)[0]
            on_bridge[idx[Path(ring).contains_points(np.c_[NX[idx], NY[idx]])]] = True
log(f"교량 면 {nb}개(범위 근처), 면 안 노드 {int(on_bridge.sum())}")
# 교량 면 안 노드 덩어리(간선으로 이어진 것)마다, 덩어리 밖 이웃 노드(경계)의 고도를 경로 거리 역수로 가중 평균한다.
# 직선 교량이면 양 끝 사이 길이 비례 보간과 같다.
adj = collections.defaultdict(list)
for (a_, b_), L_ in edges.items():
    adj[a_].append((b_, L_))
    adj[b_].append((a_, L_))
import heapq
seen = np.zeros(N, bool)
fixed, unfixed, maxchg, ncomp = 0, 0, 0.0, 0
elev2 = elev.copy()
for s0 in np.where(on_bridge)[0].tolist():
    if seen[s0]:
        continue
    comp, stack = [], [s0]
    seen[s0] = True
    while stack:
        u = stack.pop()
        comp.append(u)
        for v, _ in adj[u]:
            if on_bridge[v] and not seen[v]:
                seen[v] = True
                stack.append(v)
    ncomp += 1
    cs = set(comp)
    bnd = sorted({v for u in comp for v, _ in adj[u] if v not in cs})
    if not bnd:
        unfixed += len(comp)
        continue
    # 경계 노드마다 덩어리 안으로 다익스트라
    dist = {}
    for b0 in bnd:
        d = {b0: 0.0}
        pq = [(0.0, b0)]
        while pq:
            du, u = heapq.heappop(pq)
            if du > d.get(u, 1e18):
                continue
            for v, L_ in adj[u]:
                if v in cs and du + L_ < d.get(v, 1e18):
                    d[v] = du + L_
                    heapq.heappush(pq, (du + L_, v))
        dist[b0] = d
    for u in comp:
        ws = [(1.0 / max(dist[b0][u], 1e-6), elev[b0]) for b0 in bnd if u in dist[b0]]
        if not ws:
            unfixed += 1
            continue
        new = sum(w * z for w, z in ws) / sum(w for w, _ in ws)
        maxchg = max(maxchg, abs(new - elev[u]))
        elev2[u] = new
        fixed += 1
log(f"교량 보간: 덩어리 {ncomp}, 고친 노드 {fixed}(최대 변화 {maxchg:.1f}m), 못 고친 노드 {unfixed}")
elev = elev2

# ── 3. 노드 속성 ──
to_wgs = Transformer.from_crs(5179, 4326, always_xy=True)
LON, LAT = to_wgs.transform(NX, NY)
sig = [int(r["노드"]) for r in csv.DictReader(open(os.path.join(EXP, "도심실험_1110", "신호노드_114칸.csv"), encoding="utf-8-sig"))]
sig_new = {nid[n] for n in sig if n in nid}
fac = list(csv.DictReader(open(os.path.join(EXP, "새그래프_1110", "편의시설.csv"), encoding="utf-8-sig")))
F = np.array([(float(r["x5179"]), float(r["y5179"])) for r in fac])
fd = np.minimum(cKDTree(F).query(np.c_[NX, NY])[0], 500.0)
log(f"신호 노드 {len(sig)} 중 실험 그래프에 있는 것 {len(sig_new)}, 시설 {len(F)}개({collections.Counter(r['종류'] for r in fac).most_common()}), 노드 시설 거리 중앙값 {np.median(fd):.0f}m, 500m 상한 {np.mean(fd >= 500):.1%}")
with open(os.path.join(HERE, "노드속성_v3.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["point_id", "signal", "facility_m"])
    for i in range(N):
        w.writerow([i + 1, 1 if i in sig_new else 0, round(float(fd[i]), 1)])

# ── 4. DB ──
pw = re.search(r'password="([^"]*)"', open(OLD_BUILD, encoding="utf-8").read()).group(1)   # 기존 로컬 DB 설정을 그대로 씀(출력하지 않음)
con = pymysql.connect(host="localhost", user="root", password=pw, db=USERS_FROM)
c = con.cursor()
c.execute("SHOW TABLES")
tables = [r[0] for r in c.fetchall()]
c.execute(f"CREATE DATABASE IF NOT EXISTS {NEW_DB} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci")
c.execute(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='{NEW_DB}'")
if c.fetchone()[0] > 0:
    if "--rebuild" not in sys.argv:
        sys.exit(f"{NEW_DB}에 이미 표가 있음 — 덮어쓰지 않고 중단 (이 스크립트가 만든 DB만 --rebuild로 다시 만든다)")
    c.execute(f"SELECT COUNT(*) FROM {NEW_DB}.jeju_road_points WHERE road_type <> 'n3l_v3'")
    if c.fetchone()[0] > 0:
        sys.exit("gildongmu_v3에 이 스크립트가 넣지 않은 점이 있음 — 중단")
    c.execute(f"DROP DATABASE {NEW_DB}")
    c.execute(f"CREATE DATABASE {NEW_DB} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci")
    log(f"{NEW_DB}를 지우고 다시 만듦(--rebuild)")
for t in tables:
    c.execute(f"CREATE TABLE {NEW_DB}.`{t}` LIKE {USERS_FROM}.`{t}`")
c.execute("SELECT COLUMN_NAME FROM information_schema.columns WHERE table_schema=%s AND table_name='users' "
          "AND EXTRA NOT LIKE '%%GENERATED%%' ORDER BY ORDINAL_POSITION", (USERS_FROM,))
cols = ", ".join(f"`{r[0]}`" for r in c.fetchall())
c.execute(f"INSERT INTO {NEW_DB}.`users` ({cols}) SELECT {cols} FROM {USERS_FROM}.`users`")
con.commit()
log(f"{NEW_DB} 표 {len(tables)}개 생성({', '.join(tables)}), users 복사, obstacles·places 비움")
nw = pymysql.connect(host="localhost", user="root", password=pw, db=NEW_DB, autocommit=False)
nc = nw.cursor()
rows = [(i + 1, round(float(LAT[i]), 7), round(float(LON[i]), 7), None if np.isnan(elev[i]) else round(float(elev[i]), 2), "n3l_v3",
         (i + 1) if degn[i] != 2 else None) for i in range(N)]
for s in range(0, N, 20000):
    nc.executemany("INSERT INTO jeju_road_points (point_id, latitude, longitude, elevation_meters, road_type, osm_node_id) VALUES (%s,%s,%s,%s,%s,%s)", rows[s:s + 20000])
er = []
for (a, b), L in edges.items():
    er.append((a + 1, b + 1, round(L, 2), "n3l_v3"))
    er.append((b + 1, a + 1, round(L, 2), "n3l_v3"))
for s in range(0, len(er), 20000):
    nc.executemany("INSERT INTO jeju_road_edges (from_point_id, to_point_id, distance_meters, road_type) VALUES (%s,%s,%s,%s)", er[s:s + 20000])
nw.commit()
nc.execute("SELECT COUNT(*), SUM(osm_node_id IS NOT NULL) FROM jeju_road_points")
pc = nc.fetchone()
nc.execute("SELECT COUNT(*) FROM jeju_road_edges")
ec = nc.fetchone()[0]
log(f"넣음: 점 {pc[0]:,}(스냅 대상 {int(pc[1]):,}), 방향 간선 {ec:,}")

# 직선거리와 사슬 길이의 차이 (팀 코드는 노드 사이 직선거리를 쓴다)
ch = np.array([math.hypot(NX[a] - NX[b], NY[a] - NY[b]) for a, b in edges])
Ls = np.array(list(edges.values()))
stats = dict(db=NEW_DB, nodes=N, signal_nodes=len(sig_new), undirected_edges=len(edges), length_km=float(Ls.sum() / 1000),
             chord_over_length=float(ch.sum() / Ls.sum()), edge_len_pct={p: float(np.percentile(Ls, p)) for p in (5, 25, 50, 75, 95, 99)},
             snap_nodes=int(pc[1]), bridge_nodes=int(on_bridge.sum()), bridge_fixed=fixed, bridge_unfixed=unfixed,
             facility_median_m=float(np.median(fd)), resample_m=RESAMPLE_M)
json.dump(stats, open(os.path.join(HERE, "v3_stats.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
log("통계:", stats)
log("끝")

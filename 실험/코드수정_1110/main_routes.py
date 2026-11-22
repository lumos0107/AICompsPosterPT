"""본 실험 (2026-11-10): 출발점 4곳 × 범위 안 모든 방향의 안내점(합 46) × 선호 설정 10개, LOOP_V2 + 선호 비용, 서버는 gildongmu_v3.

- 설정: 기준 (0,0,0) + 평지 α_s, 신호 회피 α_c, 시설 근접 α_f 각각 1·3·10 (사용자 지시, 단계별 결과를 그대로 보고).
- 안내점: 서버 generateAnchorPoint 규칙대로 16방향(0.38T) 중 방향점이 실험 범위 안인 방향을 모두 쓴다
  (탑동 11, 도심 15, 연동 10, 이도 11, 합 47, 사용자 지시).
  경위: 1차 실행은 출발점 표의 '방향점 200 m 안 도로' 조건까지 넣어 46개(탑동 13번 방향 빠짐)로 돌렸다.
  사용자가 서버 규칙으로 맞추라고 해서 그 46개는 그대로 두고 탑동 13번만 `add13`으로 추가했다.
  1차 46개의 거리 배수는 시드 20261111에서 방향 순서대로 뽑았고, 탑동 13번은 시드 20261112에서 한 번 뽑았다.
  방향마다 거리 배수 m을 0.85~1.15에서 고르게 뽑고, 방향 i·거리 m·0.38T 위치에서 가장 가까운
  스냅 대상 노드(차수≠2, 실험 범위 안, 출발점에서 0.85~1.15·0.38T)를 안내점으로 한다. 열 설정 모두 같은 안내점을 넘긴다.
- 같은 요청은 결과가 같다(예비 경로에서 세 번 보내 확인) → 반복 없음.
- 지표 계산은 prelim_routes.py와 같다(마지막 점은 요청 출발 좌표라 첫 노드로 닫음, 한 응답 안 같은 경로는 하나로 셈).
실행: py -I main_routes.py (1차 46개) → py -I main_routes.py add13 (탑동 13번 추가, 46개 재현 확인 후 붙임)
결과: 본실험.json, 본실험_경로.csv, 본실험_안내점.csv, 본실험.out(1차), 본실험_추가13.out
"""
import csv
import json
import math
import os
import re
import sys
import time
import urllib.request

import numpy as np
import pymysql
from scipy.spatial import cKDTree

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
EXP_DIR = os.path.dirname(HERE)
API = "http://localhost:8080/api/routes/recommend"
ADD = len(sys.argv) > 1 and sys.argv[1] == "add13"
ADD_SEED = 20261112   # 탑동 13번 방향의 거리 배수 전용 시드(1차 46개의 배수를 바꾸지 않으려고 따로 둠)
OUT = open(os.path.join(HERE, "본실험_추가13.out" if ADD else "본실험.out"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    OUT.write(s + "\n")
    OUT.flush()


SCN = [("탑동", 33.515, 126.522, 3000), ("도심", 33.499, 126.531, 5000), ("연동", 33.489, 126.490, 3000), ("이도", 33.499, 126.541, 4000)]
SETS = [("기준", (0, 0, 0))] + [(f"{nm}{a}", tuple(a if j == k else 0 for j in range(3))) for k, nm in enumerate(["평지", "신호회피", "시설"]) for a in (1, 3, 10)]
TAU, KAPPA, CAP = 2.0, 100.0, 500.0   # Preference.java 확정값과 같게
SEED = 20261111

pw = re.search(r'password="([^"]*)"', open(r"C:\Users\seungjun\Documents\claude_code\논문\데이터사이언스학회\04_실험\새그래프_만들기\build_v2b_graph.py", encoding="utf-8").read()).group(1)
con = pymysql.connect(host="localhost", user="root", password=pw, db="gildongmu_v3")
cur = con.cursor()
cur.execute("SELECT point_id, latitude, longitude, elevation_meters, osm_node_id IS NOT NULL FROM jeju_road_points")
P = np.array([(int(a), float(b), float(c), float(d), int(e)) for a, b, c, d, e in cur.fetchall()])
con.close()
ids = P[:, 0].astype(int)
coslat = math.cos(math.radians(33.5))
tree = cKDTree(np.c_[P[:, 1] * 111320, P[:, 2] * 111320 * coslat])
elev_of = dict(zip(ids.tolist(), P[:, 3].tolist()))
attr = {int(r["point_id"]): (r["signal"] == "1", float(r["facility_m"])) for r in csv.DictReader(open(os.path.join(HERE, "노드속성_v3.csv"), encoding="utf-8"))}


def hav(a, b):
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    x = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(b[1] - a[1]) / 2) ** 2
    return 2 * 6371000 * math.asin(min(1, math.sqrt(x)))


CELLS = {tuple(int(v) for v in l.split(",")) for l in open(os.path.join(EXP_DIR, "도심실험_1110", "실험범위_114칸.txt"), encoding="utf-8") if l.strip() and not l.startswith("#")}


def inside(la, lo):
    return (math.floor(lo / 0.005), math.floor(la / 0.005)) in CELLS


from pyproj import Transformer
FW = Transformer.from_crs(4326, 5179, always_xy=True)
_g = np.load(os.path.join(EXP_DIR, "도심실험_1110", "그래프_도심_114칸.npz"))
TN = cKDTree(_g["xy"][np.unique(np.r_[_g["A"][_g["main"]], _g["B"][_g["main"]]])])
SNAP = P[(P[:, 4] == 1) & np.array([inside(a, b) for a, b in P[:, 1:3]])]
rng = np.random.default_rng(SEED)


def anchors_all_dirs(la, lo, T, only_dir=None, table_rule=True, gen=None):
    """only_dir: 이 방향만, table_rule: 출발점 표의 '200 m 안 도로' 조건 적용(1차 46개 재현용), gen: 거리 배수 난수."""
    gen = gen if gen is not None else rng
    ad = 0.38 * T
    out = []
    for i in range(16):
        if only_dir is not None and i != only_dir:
            continue
        r = math.radians(360 / 16 * i)
        dla, dlo = la + ad / 111000 * math.cos(r), lo + ad / (111000 * math.cos(math.radians(la))) * math.sin(r)
        if not inside(dla, dlo):
            continue
        if table_rule:
            # 1차 46개 재현용(출발점 표 정의, cut_area.py): EPSG:5179에서 0.38T 떨어진 방향점이 범위 안이고
            # 200 m 안에 실험 그래프(주 요소) 꼭짓점이 있어야 한다. 사용자 지시로 이 조건은 빼고 서버 규칙(47개)으로 맞췄다.
            px, py_ = FW.transform(lo, la)
            t5179 = (px + ad * math.sin(r), py_ + ad * math.cos(r))
            dn = TN.query(t5179)[0]
            if dn > 200 or not inside(*FW.transform(*t5179, direction="INVERSE")[::-1]):
                log(f"  방향 {i}: 출발점 표 정의로 제외(가장 가까운 그래프 꼭짓점 {dn:.0f} m)")
                continue
        m = float(gen.uniform(0.85, 1.15))
        tla, tlo = la + m * ad / 111000 * math.cos(r), lo + m * ad / (111000 * math.cos(math.radians(la))) * math.sin(r)
        best = None
        for q in SNAP:
            dq = hav((la, lo), (q[1], q[2]))
            if not (0.85 * ad <= dq <= 1.15 * ad):
                continue
            dt = hav((tla, tlo), (q[1], q[2]))
            if best is None or dt < best[0]:
                best = (dt, int(q[0]), float(q[1]), float(q[2]), dq)
        out.append(dict(dir=i, mult=m, node=best[1], lat=best[2], lng=best[3], snap_m=best[0], dist_from_start=best[4]))
    return out


def recommend(body):
    req = urllib.request.Request(API, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read().decode())


def metrics(pts, target):
    ll = [(p["latitude"], p["longitude"]) for p in pts]
    if len(ll) > 2 and hav(ll[-1], ll[0]) > 0.5:
        ll = ll[:-1] + [ll[0]]   # 마지막 점(요청 출발 좌표) 대신 첫 노드로 닫는다
    d, i = tree.query(np.array([(a * 111320, b * 111320 * coslat) for a, b in ll]))
    nodes = ids[i].tolist()
    seg = [hav(ll[k - 1], ll[k]) for k in range(1, len(ll))]
    L = sum(seg)
    el = [elev_of[n] for n in nodes]
    sl = [abs(el[k] - el[k - 1]) / s * 100 for k, s in enumerate(seg, 1) if s > 0.5]
    w = [s for s in seg if s > 0.5]
    mean_slope = sum(a * b for a, b in zip(sl, w)) / sum(w)
    cum = np.r_[0, np.cumsum(seg)]
    seg_slope = {}
    for step in (50, 100, 200):
        t = np.arange(0, cum[-1] + 1e-9, step)
        if len(t) < 2:
            continue
        e = np.interp(t, cum, el)
        seg_slope[step] = float(np.mean(np.abs(np.diff(e)) / step * 100))
    inner = nodes[1:-1]
    sig = sum(1 for n in inner if attr[n][0])
    fac = sum(s * (min(attr[nodes[k - 1]][1], CAP) + min(attr[nodes[k]][1], CAP)) / 2 for k, s in enumerate(seg, 1)) / L
    fs = sum(s * min(1, max(0, (abs(el[k] - el[k - 1]) / s * 100) - TAU) / 20) for k, s in enumerate(seg, 1) if s > 0.5)
    ff = sum(s * (min(attr[nodes[k - 1]][1], CAP) + min(attr[nodes[k]][1], CAP)) / 2 / CAP for k, s in enumerate(seg, 1))
    keys = [tuple(sorted((nodes[k - 1], nodes[k]))) for k in range(1, len(nodes))]
    seen, rt = set(), 0.0
    for k, s in zip(keys, seg):
        if k in seen:
            rt += s
        seen.add(k)
    return dict(length=L, err=abs(L - target) / target, slope=mean_slope, seg_slope=seg_slope, signals=sig, signals_per_km=sig / L * 1000,
                facility_m=fac, retrace=rt / L, cost_slope_per_km=fs / L * 1000, cost_fac_per_km=ff / L * 1000,
                cost_sig_per_km=sig * KAPPA / L * 1000, nodes=nodes, seg=seg, snap_max=float(d.max()), coords=ll)


EXPECT = {"탑동": 10, "도심": 15, "연동": 10, "이도": 11}   # 사용자 지시(출발점 표)
ANCH = {}
for name, la, lo, T in SCN:
    ANCH[name] = anchors_all_dirs(la, lo, T)
    log(f"{name} {T} m: 범위 안 방향 {len(ANCH[name])}/16 (기대 {EXPECT[name]})")
if any(len(ANCH[n]) != EXPECT[n] for n in EXPECT):
    log("방향 수가 기대와 다름 → 요청 전에 멈춤")
    sys.exit(1)

results, anchor_rows, fails = [], [], []
JOBS = [(name, la, lo, T, ai, an) for name, la, lo, T in SCN for ai, an in enumerate(ANCH[name])]
if ADD:
    # 1차 46개가 그대로 재현되는지 확인한 뒤, 탑동 13번 방향만 붙인다(안내점 번호 10).
    old_rows = list(csv.reader(open(os.path.join(HERE, "본실험_안내점.csv"), encoding="utf-8-sig")))[1:]
    if [int(r[4]) for r in old_rows] != [an["node"] for *_, an in JOBS]:
        log("1차 46개 안내점이 재현되지 않음 → 멈춤")
        sys.exit(1)
    log("1차 46개 안내점 재현 확인")
    results = json.load(open(os.path.join(HERE, "본실험.json"), encoding="utf-8"))
    anchor_rows = old_rows
    a13 = anchors_all_dirs(33.515, 126.522, 3000, only_dir=13, table_rule=False, gen=np.random.default_rng(ADD_SEED))
    log(f"탑동 방향 13 안내점: {a13}")
    JOBS = [("탑동", 33.515, 126.522, 3000, len(ANCH["탑동"]), a13[0])]
t_all = time.time()
for name, la, lo, T, ai, an in JOBS:
    if True:
        anchor_rows.append([name, ai, an["dir"], round(an["mult"], 4), an["node"], round(an["lat"], 6), round(an["lng"], 6), round(an["snap_m"], 1), round(an["dist_from_start"])])
        for sname, (a_s, a_c, a_f) in SETS:
            body = dict(latitude=la, longitude=lo, targetDistance=T, difficulty="normal", timeOfDay="day", algorithm="LOOP_V2",
                        alphaS=a_s, alphaC=a_c, alphaF=a_f, waypointLat=an["lat"], waypointLng=an["lng"])
            t0 = time.time()
            try:
                res = recommend(body)
            except Exception as e:
                log(f"{name} 안내점{ai} {sname}: 요청 실패 {e}")
                fails.append((name, ai, sname, str(e)))
                continue
            sec = time.time() - t0
            seen = set()
            nr = 0
            for ri, r in enumerate(res["routes"]):
                key = tuple((round(p["latitude"], 6), round(p["longitude"], 6)) for p in r["points"])
                if key in seen:
                    continue
                seen.add(key)
                m = metrics(r["points"], T)
                m.update(start=name, target=T, setting=sname, alpha=[a_s, a_c, a_f], anchor_id=ai, anchor=[an["lat"], an["lng"]], anchor_dir=an["dir"],
                         route=ri, n_routes=len(res["routes"]), sec=sec)
                results.append(m)
                nr += 1
            if nr == 0:
                log(f"{name} 안내점{ai} {sname}: 경로 0개")
        done = sum(1 for _ in results)
        log(f"  {name} 안내점{ai} (방향 {an['dir']}, 배수 {an['mult']:.3f}) 끝, 누적 경로 {done}, 경과 {time.time() - t_all:.0f}초")

json.dump(results, open(os.path.join(HERE, "본실험.json"), "w", encoding="utf-8"), ensure_ascii=False)
with open(os.path.join(HERE, "본실험_안내점.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["출발점", "안내점", "방향(16분할)", "거리배수", "노드", "위도", "경도", "목표위치까지m", "출발점에서m"])
    w.writerows(anchor_rows)
with open(os.path.join(HERE, "본실험_경로.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["출발점", "안내점", "설정", "경로", "길이m", "오차", "경사%", "경사50", "경사100", "경사200", "신호수", "신호/km", "시설거리m", "되밟기", "경사비용/km", "시설비용/km", "신호비용/km", "초"])
    for m in results:
        ss = m["seg_slope"]
        w.writerow([m["start"], m["anchor_id"], m["setting"], m["route"], round(m["length"]), round(m["err"], 3), round(m["slope"], 2), *(round(ss.get(k, ss.get(str(k), float("nan"))), 2) for k in (50, 100, 200)),
                    m["signals"], round(m["signals_per_km"], 2), round(m["facility_m"]), round(m["retrace"], 3), round(m["cost_slope_per_km"], 1), round(m["cost_fac_per_km"]), round(m["cost_sig_per_km"]), round(m["sec"])])
log(f"끝: 경로 {len(results)}, 요청 실패 {len(fails)}, 총 {time.time() - t_all:.0f}초")

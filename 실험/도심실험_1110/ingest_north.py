"""북쪽 1:1,000 도엽 19장을 정리한다 (2026-11-10 사용자 동의 후 국토정보맵에서 받음).

1. Downloads의 zip·xml 38개를 원본/국토정보맵/수치지형도_1000_표본/제주도심_북쪽19장/zip/ 으로 옮긴다.
2. zip을 풀기/<도엽번호>/ 에 푼다(압축 안 경로가 폴더 밖을 가리키면 중단).
3. xml에서 촬영·조사·제작년도를 읽는다.
4. 신호등(N1P_C0493376)·신호등제어기(N1P_C0503375 구분 '신호등제어기' 또는 IUD002) 점을 EPSG:5179로 바꿔 신호1000_북쪽19장.csv에 쓴다.
   기존 제주 도심 점과 1m 안에서 겹치면(도엽 경계 중복) 뺀다.
5. 실험범위_114칸.txt (95칸 + 19장) 를 만든다. 1:1,000 도엽이 없는 8칸은 넣지 않는다.
실행: py -I ingest_north.py
"""
import collections
import csv
import glob
import os
import re
import shutil
import struct
import sys
import zipfile

import numpy as np
from pyproj import Transformer
from scipy.spatial import cKDTree

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
G = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\새그래프_1110"
DL = r"C:\Users\seungjun\Downloads"
DST = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵\수치지형도_1000_표본\제주도심_북쪽19장"
WANT = ["336061559", "336061560", "336061568", "336061569", "336061570", "336071149", "336071158", "336071159", "336071160"] + [f"3360711{k}" for k in range(61, 71)]
out = open(os.path.join(HERE, "북쪽19장.out"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out.write(s + "\n")


os.makedirs(os.path.join(DST, "zip"), exist_ok=True)
moved = 0
for f in glob.glob(os.path.join(DL, "(B010)수치지도_*_2025_*")):
    m = re.search(r"수치지도_(\d{9})_", os.path.basename(f))
    if m and m.group(1) in WANT and not f.endswith(".irx"):
        shutil.move(f, os.path.join(DST, "zip", os.path.basename(f)))
        moved += 1
zips = sorted(glob.glob(os.path.join(DST, "zip", "*.zip")))
xmls = sorted(glob.glob(os.path.join(DST, "zip", "*.xml")))
log(f"옮긴 파일 {moved}, zip {len(zips)}, xml {len(xmls)}")
assert len(zips) == 19 and len(xmls) == 19, "19장이 다 있지 않음"

# 풀기
for z in zips:
    sh = re.search(r"수치지도_(\d{9})_", os.path.basename(z)).group(1)
    d = os.path.join(DST, "풀기", sh)
    os.makedirs(d, exist_ok=True)
    with zipfile.ZipFile(z) as zf:
        for n in zf.namelist():
            tgt = os.path.realpath(os.path.join(d, os.path.basename(n)))
            if not tgt.startswith(os.path.realpath(d)) or n.endswith("/"):
                continue
            with zf.open(n) as src, open(tgt, "wb") as dst:
                shutil.copyfileobj(src, dst)

# 시점
years = []
for x in xmls:
    t = open(x, encoding="utf-8").read()
    g = lambda k: (re.search(f"<{k}>([^<]*)</{k}>", t) or [None, ""])[1]
    years.append((g("도엽번호"), g("촬영년도"), g("조사년도"), g("제작년도"), g("고시일자")[:10]))
log("도엽 시점 (촬영, 조사, 제작):", collections.Counter((a, b, c) for _, a, b, c, _ in years).most_common())
for y in years:
    log("  ", *y)


def dbf_read(path):
    raw = open(path, "rb").read()
    n = struct.unpack("<I", raw[4:8])[0]
    hlen, rlen = struct.unpack("<2H", raw[8:12])
    off, pos, f = 1, 32, []
    while raw[pos] != 13:
        c = raw[pos:pos + 32]
        f.append((c[:11].split(b"\0")[0].decode("cp949", "replace"), off, c[16]))
        off += c[16]
        pos += 32
    return [{k: raw[hlen + i * rlen + o:hlen + i * rlen + o + l].decode("cp949", "replace").strip() for k, o, l in f} for i in range(n)]


def shp_points(path):
    d = open(path, "rb").read()
    pos, o = 100, []
    while pos < len(d):
        _, clen = struct.unpack(">2i", d[pos:pos + 8])
        s = pos + 8
        o.append(struct.unpack("<2d", d[s + 4:s + 20]) if struct.unpack("<i", d[s:s + 4])[0] != 0 else None)
        pos = s + clen * 2
    return o


to5179 = Transformer.from_crs(5186, 5179, always_xy=True)
to_wgs = Transformer.from_crs(5186, 4326, always_xy=True)
pts, cells = [], set()
prj_ok = 0
for sd in sorted(glob.glob(os.path.join(DST, "풀기", "*"))):
    sh = os.path.basename(sd)
    b = [np.inf, np.inf, -np.inf, -np.inf]
    for shp in glob.glob(os.path.join(sd, "*.shp")):
        x0, y0, x1, y1 = struct.unpack("<4d", open(shp, "rb").read(100)[36:68])
        if x1 > x0 or y1 > y0:
            b = [min(b[0], x0), min(b[1], y0), max(b[2], x1), max(b[3], y1)]
    prj = glob.glob(os.path.join(sd, "*.prj"))
    txt = open(prj[0], encoding="utf-8", errors="replace").read() if prj else ""
    if "Central_Belt_2010" in txt or ("GRS" in txt and "200000" in txt and "600000" in txt):  # EPSG:5186 (중부원점 2010)
        prj_ok += 1
    lo, la = to_wgs.transform((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
    cells.add((int(np.floor(lo / 0.005)), int(np.floor(la / 0.005))))
    for base, kind in (("N1P_C0493376", "신호등"), ("N1P_C0503375", "차단기")):
        p = os.path.join(sd, base)
        if not os.path.exists(p + ".shp"):
            continue
        for q, r in zip(shp_points(p + ".shp"), dbf_read(p + ".dbf")):
            if q is None:
                continue
            use = r.get("용도") if kind == "신호등" else r.get("구분")
            if kind == "차단기" and not (use or "").startswith(("신호등제어기", "IUD002")):
                continue
            x, y = to5179.transform(q[0], q[1])
            pts.append(("제주 도심 북쪽", sh, "SHP", "신호등" if kind == "신호등" else "제어기", use, x, y))
log(f"도엽 폴더 {len(cells)}칸, prj 확인 {prj_ok}/19 (첫 prj 앞부분은 아래)")
pj = glob.glob(os.path.join(DST, "풀기", "*", "*.prj"))
log("  ", open(pj[0], encoding="utf-8", errors="replace").read()[:120] if pj else "prj 없음")
log("점:", collections.Counter((p[3], p[4]) for p in pts).most_common())

old = [r for r in csv.DictReader(open(os.path.join(G, "신호1000.csv"), encoding="utf-8-sig")) if r["지역"] == "제주 도심"]
O = np.array([(float(r["x5179"]), float(r["y5179"])) for r in old])
P = np.array([(p[5], p[6]) for p in pts]) if pts else np.zeros((0, 2))
keep = np.ones(len(P), bool)
if len(P):
    keep &= cKDTree(O).query(P)[0] > 1.0  # 기존 95장과 경계 중복
    for tp in ("신호등", "제어기"):  # 새 19장끼리의 경계 중복
        idx = np.array([i for i, p in enumerate(pts) if p[3] == tp])
        if len(idx) > 1:
            pr = cKDTree(P[idx]).query_pairs(1.0, output_type="ndarray")
            if len(pr):
                keep[idx[pr.max(1)]] = False
log(f"새 점 {len(P)}, 중복 제거 뒤 {int(keep.sum())}")
with open(os.path.join(HERE, "신호1000_북쪽19장.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["지역", "도엽", "형식", "종류", "용도", "x5179", "y5179"])
    for i, p in enumerate(pts):
        if keep[i]:
            w.writerow([p[0], p[1], p[2], p[3], p[4], round(float(p[5]), 2), round(float(p[6]), 2)])

base = [tuple(map(int, l.split(","))) for l in open(os.path.join(HERE, "실험범위_95칸.txt"), encoding="utf-8") if l.strip() and not l.startswith("#")]
allc = sorted(set(base) | cells)
with open(os.path.join(HERE, "실험범위_114칸.txt"), "w", encoding="utf-8") as f:
    f.write("# 제주 도심 95칸 + 북쪽 19장 (1:1,000 도엽이 있는 칸만, 2026-11-10). 경도칸,위도칸 = floor(경도/0.005), floor(위도/0.005)\n")
    for i, j in allc:
        f.write(f"{i},{j}\n")
log(f"실험범위 {len(allc)}칸 (95 + 새 {len(cells - set(base))}, 겹침 {len(cells & set(base))})")
log("끝")

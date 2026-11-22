"""받은 자료의 건수·좌표계·기준일·제주 범위 안 건수를 파일에서 직접 잰다. 원본은 읽기만 한다.
상가정보는 전국 zip에서 제주 파일 하나만 꺼내 편의점을 센다.
실행: py -I 자료정리.py
결과: 같은 폴더 자료정리표.md
"""
import csv
import glob
import io
import os
import re
import struct
import sys
import zipfile

import numpy as np
from pyproj import Transformer

sys.stdout.reconfigure(encoding="utf-8")
HERE = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\새그래프_1110"
RAW = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본"
X0, Y0, X1, Y1 = 873000, 1458000, 952000, 1559000
to5179 = Transformer.from_crs(4326, 5179, always_xy=True)
md = []


def w(s=""):
    print(s, flush=True)
    md.append(s)


def crs_name(prj):
    if not os.path.exists(prj):
        return "prj 없음"
    t = open(prj, encoding="utf-8", errors="replace").read()
    cm = re.search(r'central_meridian"?,\s*([\d.]+)', t, re.I)
    fe = re.search(r'false_easting"?,\s*([\d.]+)', t, re.I)
    fn = re.search(r'false_northing"?,\s*([\d.]+)', t, re.I)
    if cm and fe and fn:
        key = (round(float(cm.group(1)), 3), round(float(fe.group(1))), round(float(fn.group(1))))
        name = {(127.5, 1000000, 2000000): "EPSG:5179", (127.0, 200000, 600000): "EPSG:5186"}.get(key)
        return name or f"미상{key}"
    return "미상"


def shp_stat(base):
    """레코드 수, 빈 도형 수, 제주 상자와 겹치는 레코드 수, dbf 헤더 날짜."""
    d = open(base + ".shp", "rb").read()
    stype = struct.unpack("<i", d[32:36])[0]
    pos, n, null, inbox = 100, 0, 0, 0
    while pos < len(d):
        _, clen = struct.unpack(">2i", d[pos:pos + 8])
        s = pos + 8
        st = struct.unpack("<i", d[s:s + 4])[0]
        n += 1
        if st == 0:
            null += 1
        elif st in (1, 11, 21):
            x, y = struct.unpack("<2d", d[s + 4:s + 20])
            inbox += X0 <= x <= X1 and Y0 <= y <= Y1
        else:
            x0, y0, x1, y1 = struct.unpack("<4d", d[s + 4:s + 36])
            inbox += x1 >= X0 and x0 <= X1 and y1 >= Y0 and y0 <= Y1
        pos = s + clen * 2
    h = open(base + ".dbf", "rb").read(32)
    nd = struct.unpack("<I", h[4:8])[0]
    date = f"{1900 + h[1]}-{h[2]:02d}-{h[3]:02d}"
    return stype, n, null, inbox, nd, date


def read_csv(path):
    raw = open(path, "rb").read()
    for enc in ("utf-8-sig", "cp949"):
        try:
            txt = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        txt, enc = raw.decode("cp949", "replace"), "cp949(대체)"
    rows = list(csv.reader(io.StringIO(txt)))
    return enc, rows[0], rows[1:]


def col(head, pats):
    for p in pats:
        for i, h in enumerate(head):
            if re.search(p, h.strip(), re.I):
                return i
    return None


def tofloat(s):
    try:
        return float(s)
    except ValueError:
        return np.nan


def csv_stat(path):
    enc, head, rows = read_csv(path)
    la, lo = col(head, ["위도", "^lat", "latitude"]), col(head, ["경도", "^lon", "^lng", "longitude"])
    dc = col(head, ["데이터기준일", "기준일", "기준일자"])
    addr = [i for i, h in enumerate(head) if re.search("주소|소재지|도로명|지번", h)]
    inbox = coord = "-"
    if la is not None and lo is not None:
        lat = np.array([tofloat(r[la]) if la < len(r) else np.nan for r in rows])
        lng = np.array([tofloat(r[lo]) if lo < len(r) else np.nan for r in rows])
        ok = np.isfinite(lat) & np.isfinite(lng) & (lat != 0) & (lng != 0)
        x, y = to5179.transform(lng[ok], lat[ok])
        coord = int(ok.sum())
        inbox = int(((x >= X0) & (x <= X1) & (y >= Y0) & (y <= Y1)).sum())
    dates = sorted({r[dc].strip() for r in rows if dc is not None and dc < len(r) and r[dc].strip()})
    date = "-" if not dates else (dates[0] if len(dates) == 1 else f"{dates[0]} ~ {dates[-1]} ({len(dates)}종)")
    has_addr = "-"
    if addr:
        has_addr = sum(1 for r in rows if any(i < len(r) and r[i].strip() for i in addr))
    return enc, len(rows), coord, inbox, has_addr, date


w("# 자료 정리표 (2026-11-10, `자료정리.py`로 파일에서 직접 잼)")
w()
w("제주 범위는 EPSG:5179 상자 x 873000~952000, y 1458000~1559000이다. 선·면은 도형의 외곽 상자가 이 범위와 겹치면 안으로 센다.")
w("날짜의 'dbf 작성일'은 파일을 만든 날이고 자료 시점이 아니다. 1:5,000의 자료 기준은 신청한 제작년도 2024다.")
w()

# 1. SHP
groups = [
    ("연속수치지도 1:5,000 교통·시설·지형", os.path.join(RAW, "국토정보맵", "연속수치지도_제주_20261109", "풀기")),
    ("연속수치지도 1:5,000 건물·식생·수계·경계·주기", os.path.join(RAW, "국토정보맵", "연속수치지도_제주_20261109_추가", "풀기")),
    ("브이월드 입체교차부(전국본)", os.path.join(RAW, "브이월드", "입체교차부_30223", "풀기")),
    ("브이월드 터널(전국본)", os.path.join(RAW, "브이월드", "터널_30238", "풀기")),
]
TYPES = {1: "점", 3: "선", 5: "면", 11: "점", 13: "선", 15: "면", 21: "점", 23: "선", 25: "면"}
for title, root in groups:
    bases = sorted(p[:-4] for p in glob.glob(os.path.join(root, "**", "*.shp"), recursive=True))
    w(f"## {title} ({len(bases)}개)")
    w()
    w("| 레이어 | 형태 | 레코드 | 빈 도형 | 제주 범위 안 | dbf 건수 | 좌표계 | dbf 작성일 |")
    w("|---|---|---:|---:|---:|---:|---|---|")
    for b in bases:
        st, n, null, inbox, nd, date = shp_stat(b)
        flag = "" if n == nd else " (shp·dbf 건수 불일치)"
        w(f"| {os.path.basename(b)} | {TYPES.get(st, st)} | {n:,} | {null:,} | {inbox:,} | {nd:,}{flag} | {crs_name(b + '.prj')} | {date} |")
    w()

# 2. CSV
w("## 공공데이터포털 CSV")
w()
w("| 자료 | 인코딩 | 건수 | 좌표 있음 | 제주 범위 안 | 주소 있음 | 데이터 안 기준일 |")
w("|---|---|---:|---:|---:|---:|---|")
for p in sorted(glob.glob(os.path.join(RAW, "공공데이터포털", "*", "*.csv"))):
    enc, n, coord, inbox, addr, date = csv_stat(p)
    c = f"{coord:,}" if coord != "-" else "-"
    i = f"{inbox:,}" if inbox != "-" else "-"
    a = f"{addr:,}" if addr != "-" else "-"
    w(f"| {os.path.basename(p)[:-4]} | {enc} | {n:,} | {c} | {i} | {a} | {date} |")
w()

# 3. 상가정보
zp = os.path.join(RAW, "공공데이터포털", "상가상권정보_전국", "상가상권정보_전국.zip")
z = zipfile.ZipFile(zp)
names = [i for i in z.infolist() if "제주" in i.filename or "제주" in i.filename.encode("cp437", "replace").decode("cp949", "replace")]
w("## 상가상권정보 (전국 zip에서 제주 파일만)")
w()
w(f"zip 안 파일 {len(z.infolist())}개, 제주 이름의 파일 {len(names)}개")
for info in names:
    raw = z.read(info)
    for enc in ("utf-8-sig", "cp949"):
        try:
            txt = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    rows = list(csv.reader(io.StringIO(txt)))
    head, body = rows[0], rows[1:]
    la, lo = col(head, ["위도"]), col(head, ["경도"])
    sm = col(head, ["상권업종소분류명"])
    lat, lng = np.array([tofloat(r[la]) for r in body]), np.array([tofloat(r[lo]) for r in body])
    x, y = to5179.transform(lng, lat)
    ib = (x >= X0) & (x <= X1) & (y >= Y0) & (y <= Y1)
    conv = np.array([r[sm].strip() == "편의점" for r in body])
    w(f"- 전체 {len(body):,}건, 제주 범위 안 {int(ib.sum()):,}건, 편의점 {int(conv.sum()):,}건, 편의점 중 제주 범위 안 {int((conv & ib).sum()):,}건, 인코딩 {enc}")
w()

w("## 1:1,000 수치지형도")
w()
root = os.path.join(RAW, "국토정보맵", "수치지형도_1000_표본")
w("건수와 제작년도는 `../수집확인_1109/`의 1:1,000 확인 결과이고 여기서 다시 세지 않았다. 좌표계는 SHP의 .prj로 EPSG:5186, NGI는 표기가 없어 추정이다.")
w()
for nm in sorted(os.listdir(root)):
    p = os.path.join(root, nm)
    if os.path.isdir(p):
        w(f"- {nm}: 파일·폴더 {len(os.listdir(p))}개")
w()
w("## 기록과 다른 값의 이유 (`자료정리_대조.py`)")
w()
w("1. 계획서의 제주시 화장실 '범위 안 459건'과 상가 '58,926건'은 위경도 상자(위도 33.6 이하)로 센 값이라 추자도 쪽이 빠졌다. 이 표는 EPSG:5179 상자라 추자도가 포함된다.")
w("2. 제주시 화장실 503건 중 좌표 없음 12건, 상자 밖 4건(위도 66.5 같은 입력 오류 포함)이고, 28건은 위도 33.6 초과지만 상자 안(추자도 쪽)이다. 기록의 '44건'은 이 12+4+28이다.")
w("3. 1:5,000 파일의 기록 '파일 생성 2025-10-22'는 zip 안 항목의 시각이다. dbf 머리글의 날짜는 2025-09-09~10이다. 둘 다 파일 날짜이고 자료 시점은 아니다.")
w()

open(os.path.join(HERE, "자료정리표.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
print("끝")

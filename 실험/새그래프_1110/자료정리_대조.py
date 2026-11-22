"""계획서 값(제주시 화장실 범위 안 459, 상가 범위 안 58,926)과 자료정리표 값이 다른 이유를 찾는다. 건수만 출력."""
import csv
import io
import os
import sys
import zipfile

import numpy as np
from pyproj import Transformer

sys.stdout.reconfigure(encoding="utf-8")
RAW = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\공공데이터포털"
to5179 = Transformer.from_crs(4326, 5179, always_xy=True)
BOXES = {
    "5179 상자": None,
    "위경도 33.1~33.6, 126.1~127.0 (본섬+가까운 섬)": (33.1, 33.6, 126.1, 127.0),
    "위경도 33.0~33.6, 126.0~127.0": (33.0, 33.6, 126.0, 127.0),
    "위경도 33.1~33.58, 126.14~126.98": (33.1, 33.58, 126.14, 126.98),
}


def f(s):
    try:
        return float(s)
    except ValueError:
        return np.nan


def report(name, lat, lng):
    ok = np.isfinite(lat) & np.isfinite(lng) & (lat != 0) & (lng != 0)
    print(f"[{name}] 전체 {len(lat):,}, 좌표 유효 {int(ok.sum()):,}, 위도 범위 {np.nanmin(lat[ok]):.4f}~{np.nanmax(lat[ok]):.4f}, 경도 범위 {np.nanmin(lng[ok]):.4f}~{np.nanmax(lng[ok]):.4f}")
    for k, b in BOXES.items():
        if b is None:
            x, y = to5179.transform(lng[ok], lat[ok])
            c = (x >= 873000) & (x <= 952000) & (y >= 1458000) & (y <= 1559000)
        else:
            c = (lat[ok] >= b[0]) & (lat[ok] <= b[1]) & (lng[ok] >= b[2]) & (lng[ok] <= b[3])
        print(f"   {k}: {int(c.sum()):,}")
    print(f"   위도 33.6 초과(추자도 쪽): {int((lat[ok] > 33.6).sum()):,}")


raw = open(os.path.join(RAW, "제주시_공중화장실", "제주시_공중화장실.csv"), "rb").read().decode("cp949")
rows = list(csv.reader(io.StringIO(raw)))
h = rows[0]
print("화장실 칸 수", len(h), "좌표 칸:", [(i, c) for i, c in enumerate(h) if "위도" in c or "경도" in c])
la = h.index([c for c in h if "위도" in c][0])
lo = h.index([c for c in h if "경도" in c][0])
lat = np.array([f(r[la]) if la < len(r) else np.nan for r in rows[1:]])
lng = np.array([f(r[lo]) if lo < len(r) else np.nan for r in rows[1:]])
report("제주시 화장실", lat, lng)

raw = open(os.path.join(RAW, "공중화장실표준_제주특별자치도_localdata", "공중화장실정보_제주특별자치도.csv"), "rb").read().decode("cp949")
rows = list(csv.reader(io.StringIO(raw)))
h = rows[0]
di = [i for i, c in enumerate(h) if "기준일" in c][0]
ai = [i for i, c in enumerate(h) if "소재지" in c or "도로명" in c]
import collections
cnt = collections.Counter()
for r in rows[1:]:
    addr = " ".join(r[i] for i in ai if i < len(r))
    si = "서귀포시" if "서귀포" in addr else ("제주시" if "제주시" in addr else "기타")
    cnt[(si, r[di].strip())] += 1
print("화장실 표준 시별 기준일", sorted(cnt.items()))

z = zipfile.ZipFile(os.path.join(RAW, "상가상권정보_전국", "상가상권정보_전국.zip"))
info = [i for i in z.infolist() if "제주" in i.filename or "제주" in i.filename.encode("cp437", "replace").decode("cp949", "replace")][0]
rows = list(csv.reader(io.StringIO(z.read(info).decode("utf-8-sig"))))
h = rows[0]
la, lo = h.index("위도"), h.index("경도")
lat = np.array([f(r[la]) for r in rows[1:]])
lng = np.array([f(r[lo]) for r in rows[1:]])
report("상가 제주 전체", lat, lng)

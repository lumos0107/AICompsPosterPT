"""도곽선에서 도엽별 제작년도·촬영년도를 집계한다. 사용: python -I check_dogak.py <N3A_H0010000 폴더> <결과 파일>"""
import collections
import os
import struct
import sys

from pyproj import Transformer

folder, result = sys.argv[1:3]
sys.stdout.reconfigure(encoding="utf-8")
out = open(result, "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out.write(s + "\n")


def find(ext):
    return next(os.path.join(r, f) for r, _, fs in os.walk(folder) for f in fs if f.lower().endswith(ext))


with open(find(".dbf"), "rb") as f:
    h = f.read(32)
    n = struct.unpack("<I", h[4:8])[0]
    hlen, rlen = struct.unpack("<2H", h[8:12])
    fields, off = {}, 1
    while True:
        c = f.read(32)
        if c[0] == 13:
            break
        fields[c[:11].split(b"\0")[0].decode("cp949", "replace")] = (off, c[16])
        off += c[16]
    f.seek(hlen)
    buf = f.read(n * rlen)
rows = [{k: buf[i * rlen + o:i * rlen + o + l].decode("cp949", "replace").strip() for k, (o, l) in fields.items()} for i in range(n)]
log("도엽 수", f"{n:,}", "항목", list(fields))
log("첫 줄", rows[0])
data = open(find(".shp"), "rb").read()
pos, centers = 100, []
while pos < len(data):
    _, clen = struct.unpack(">2i", data[pos:pos + 8])
    s = pos + 8
    x0, y0, x1, y1 = struct.unpack("<4d", data[s + 4:s + 36])
    centers.append(((x0 + x1) / 2, (y0 + y1) / 2))
    pos = s + clen * 2
to5179 = Transformer.from_crs(4326, 5179, always_xy=True)
BOX = {}
for name, (la0, la1, lo0, lo1) in {"제주시 시험구역": (33.46, 33.54, 126.46, 126.58), "서귀포시내": (33.24, 33.27, 126.53, 126.60)}.items():
    a, b = to5179.transform(lo0, la0)
    c, d = to5179.transform(lo1, la1)
    BOX[name] = (a, b, c, d)
year = lambda v: v[:4] if v else "(빈칸)"
for field in ("MYMD", "PYMD", "PRDT", "SCAL", "MCOM"):
    if field in fields:
        fn = year if field in ("MYMD", "PYMD") else (lambda v: v)
        log(f"{field}:", sorted(collections.Counter(fn(r[field]) for r in rows).items()) if field in ("MYMD", "PYMD") else collections.Counter(r[field] for r in rows).most_common(6))
for name, (a, b, c, d) in BOX.items():
    idx = [i for i, (x, y) in enumerate(centers) if a <= x <= c and b <= y <= d]
    log(f"[{name}] 도엽 {len(idx)}개, 제작년도 {sorted(collections.Counter(year(rows[i]['MYMD']) for i in idx).items())}, 촬영년도 {sorted(collections.Counter(year(rows[i]['PYMD']) for i in idx).items())}")

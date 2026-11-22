"""브이월드 전국 도로중심선 zip에서 제주 범위의 선을 세고 국토정보맵·5월 사본과 UFID를 대조한다. 압축은 풀지 않는다.

사용: python -I count_jeju_road.py <결과 파일> <국토정보맵 dbf> <5월 dbf> <zip> [<zip> ...]
"""
import os
import struct
import sys
import zipfile

import numpy as np

result, ngii_dbf, may_dbf, *zips = sys.argv[1:]
sys.stdout.reconfigure(encoding="utf-8")
out = open(result, "w", encoding="utf-8")
X0, Y0, X1, Y1 = 873000, 1458000, 952000, 1559000


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out.write(s + "\n")
    out.flush()


def ufids(path):
    with open(path, "rb") as f:
        h = f.read(32)
        n = struct.unpack("<I", h[4:8])[0]
        hlen, rlen = struct.unpack("<2H", h[8:12])
        off = 1
        while True:
            c = f.read(32)
            if c[0] == 13:
                break
            if c[:11].split(b"\0")[0] == b"UFID":
                o, l = off, c[16]
            off += c[16]
        f.seek(hlen)
        buf = f.read(n * rlen)
    return {buf[i * rlen + o:i * rlen + o + l].strip() for i in range(n)}


ngii, may = ufids(ngii_dbf), ufids(may_dbf)
log(f"국토정보맵 UFID {len(ngii):,}, 5월 UFID {len(may):,}, 둘의 겹침 {len(ngii & may):,}")
found = set()
tot_n, tot_km = 0, 0.0
for zp in zips:
    with zipfile.ZipFile(zp) as z:
        base = next(i.filename for i in z.infolist() if i.filename.lower().endswith(".shp"))[:-4]
        data = z.read(base + ".shp")
        pos, rec, idx, km = 100, 0, [], 0.0
        while pos < len(data):
            _, clen = struct.unpack(">2i", data[pos:pos + 8])
            s = pos + 8
            if struct.unpack("<i", data[s:s + 4])[0] != 0:
                x0, y0, x1, y1 = struct.unpack("<4d", data[s + 4:s + 36])
                if x1 >= X0 and x0 <= X1 and y1 >= Y0 and y0 <= Y1:
                    idx.append(rec)
                    np_, npts = struct.unpack("<2i", data[s + 36:s + 44])
                    parts = list(np.frombuffer(data, "<i4", np_, s + 44)) + [npts]
                    p = np.frombuffer(data, "<f8", npts * 2, s + 44 + 4 * np_).reshape(-1, 2)
                    for a, b in zip(parts[:-1], parts[1:]):
                        km += float(np.hypot(*np.diff(p[a:b], axis=0).T).sum()) / 1000
            pos = s + clen * 2
            rec += 1
        del data
        ids = set()
        if idx:
            with z.open(base + ".dbf") as f:
                h = f.read(32)
                hlen, rlen = struct.unpack("<2H", h[8:12])
                rest = f.read(hlen - 32)
                off, i = 1, 0
                while rest[i] != 13:
                    c = rest[i:i + 32]
                    if c[:11].split(b"\0")[0] == b"UFID":
                        o, l = off, c[16]
                    off += c[16]
                    i += 32
                want, cur = set(idx), 0
                while True:
                    r = f.read(rlen)
                    if len(r) < rlen:
                        break
                    if cur in want:
                        ids.add(r[o:o + l].strip())
                    cur += 1
    found |= ids
    tot_n += len(idx)
    tot_km += km
    log(f"{os.path.basename(zp)}: 전체 {rec:,}건 중 제주 범위 {len(idx):,}건 {km:,.1f}km")
log(f"\n합계 제주 범위 {tot_n:,}건 {tot_km:,.1f}km, 고유 UFID {len(found):,}")
log(f"국토정보맵과 UFID 겹침 {len(found & ngii):,} ({len(found & ngii) / max(len(found), 1):.1%}), 5월과 겹침 {len(found & may):,} ({len(found & may) / max(len(found), 1):.1%})")

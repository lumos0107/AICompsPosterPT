"""국토정보맵 연속수치지도 2차 확인: 코드 이름, 필수 항목 유무, 5월 사본과 비교, 등고선 간격.

사용: python -I check_ngii2.py <풀기 폴더> <설명서 pdf> <5월 도로 dbf> <결과 파일>
"""
import collections
import functools
import math
import os
import re
import struct
import sys

import numpy as np
import pdfplumber

root, pdf, old_dbf, result = sys.argv[1:5]
sys.stdout.reconfigure(encoding="utf-8")
out = open(result, "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out.write(s + "\n")
    out.flush()


def dbf(path, want):
    with open(path, "rb") as f:
        head = f.read(32)
        n = struct.unpack("<I", head[4:8])[0]
        hlen, rlen = struct.unpack("<2H", head[8:12])
        fields, off = {}, 1
        while True:
            c = f.read(32)
            if c[0] == 13:
                break
            fields[c[:11].split(b"\0")[0].decode("cp949", "replace")] = (off, c[16])
            off += c[16]
        f.seek(hlen)
        buf = f.read(n * rlen)
    return {k: [buf[i * rlen + fields[k][0]:i * rlen + fields[k][0] + fields[k][1]].decode("cp949", "replace").strip() for i in range(n)] for k in want}


def path(layer, ext):
    d = os.path.join(root, layer)
    for r, _, fs in os.walk(d):
        for f in fs:
            if f.lower().endswith(ext):
                return os.path.join(r, f)


def total_km(layer):
    data = open(path(layer, ".shp"), "rb").read()
    pos, km = 100, 0.0
    while pos < len(data):
        _, clen = struct.unpack(">2i", data[pos:pos + 8])
        s = pos + 8
        if struct.unpack("<i", data[s:s + 4])[0] != 0:
            np_, npts = struct.unpack("<2i", data[s + 36:s + 44])
            parts = list(np.frombuffer(data, "<i4", np_, s + 44)) + [npts]
            p = np.frombuffer(data, "<f8", npts * 2, s + 44 + 4 * np_).reshape(-1, 2)
            for a, b in zip(parts[:-1], parts[1:]):
                km += float(np.hypot(*np.diff(p[a:b], axis=0).T).sum()) / 1000
        pos = s + clen * 2
    return km


layers = sorted(os.listdir(root))
pat = re.compile(r"(?<![A-Z0-9])([A-H]\d{7})(?!\d)")
names, lines = {}, []
with pdfplumber.open(pdf) as doc:
    for page in doc.pages:
        for line in (page.extract_text() or "").splitlines():
            lines.append(line.strip())
            for code in pat.findall(line):
                names.setdefault(code, line.strip()[:60])
log("== 코드 이름")
for x in layers:
    log(f"  {x}: {names.get(x[4:], '설명서에 없음')}")
log("\n== 계획서 항목 낱말이 든 설명서 줄")
for w in ("입체교차", "도로분리", "터널", "계단", "표고점", "등고선", "도로중심선", "육교", "교량"):
    hit = [l[:70] for l in lines if w in l][:4]
    log(f"  {w}: {hit}")

log("\n== 도로중심선 5월 사본과 비교")
new = dbf(path("N3L_A0020000", ".dbf"), ["UFID", "PVQT", "RVWD", "RDDV", "FMTA", "SCLS"])
old = dbf(old_dbf, ["UFID"])
log("  UFID 예", new["UFID"][:3], "길이", collections.Counter(len(u) for u in new["UFID"]).most_common(3))
log("  FMTA", collections.Counter(new["FMTA"]).most_common(5), "SCLS", collections.Counter(new["SCLS"]).most_common(3))
a, b = set(new["UFID"]), set(old["UFID"])
log(f"  이번 고유 UFID {len(a):,}, 5월 {len(b):,}, 겹침 {len(a & b):,}, 이번에만 {len(a - b):,}, 5월에만 {len(b - a):,}")
log(f"  이번 도로 길이 {total_km('N3L_A0020000'):,.1f}km (5월 14,427.5km)")
log("  포장 코드", collections.Counter(new["PVQT"]).most_common())
w = np.array([float(v or 0) for v in new["RVWD"]])
log(f"  폭 3m 미만 선 비율 {np.mean(w < 3):.1%}")

log("\n== 면·선 속성 분포")
for layer, field in [("N3A_A0080000", "KIND"), ("N3A_A0063321", "NAME"), ("N3A_A0070000", "KIND"), ("N3L_A0033320", "KIND"), ("N3A_C0390000", "STRU"), ("N3L_C0520000", "STRU")]:
    log(f"  {layer} {field}:", collections.Counter(dbf(path(layer, ".dbf"), [field])[field]).most_common(6))

log("\n== 등고선과 표고점")
c = dbf(path("N3L_F0010000", ".dbf"), ["CONT", "DIVI"])
v = sorted({round(float(x), 2) for x in c["CONT"] if x})
log("  구분", collections.Counter(c["DIVI"]).most_common(5))
log(f"  높이 값 {len(v)}개, 범위 {v[0]}~{v[-1]}m, 최대공약수 {functools.reduce(math.gcd, [int(round(x)) for x in v if x])}")
log("  이웃한 높이 차 상위", collections.Counter(round(q - p, 2) for p, q in zip(v[:-1], v[1:])).most_common(4))
p = np.array([float(x) for x in dbf(path("N3P_F0020000", ".dbf"), ["NUME"])["NUME"] if x])
log(f"  표고점 {len(p):,}개, 범위 {p.min():.1f}~{p.max():.1f}m, 0 이하 {int((p <= 0).sum()):,}개")

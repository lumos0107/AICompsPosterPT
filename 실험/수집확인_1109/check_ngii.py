"""국토정보맵 연속수치지도 제주 파일 확인: 압축을 파일별 빈 폴더에 풀고 항목·건수·범위·기준일을 적는다.

사용: python -I check_ngii.py <zip폴더> <풀 폴더> <설명서 pdf> <결과 파일>
"""
import collections
import os
import re
import struct
import sys
import zipfile

import pdfplumber

zdir, outdir, pdf, result = sys.argv[1:5]
sys.stdout.reconfigure(encoding="utf-8")
out = open(result, "w", encoding="utf-8")
TYPES = {1: "점", 3: "선", 5: "면", 8: "다중점", 11: "점Z", 13: "선Z", 15: "면Z"}
JEJU = (873000, 1458000, 952000, 1559000)  # 기존 측정 코드의 제주 범위 (EPSG:5179)


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out.write(s + "\n")
    out.flush()


names = {}
with pdfplumber.open(pdf) as doc:
    for page in doc.pages:
        for line in (page.extract_text() or "").splitlines():
            for code in re.findall(r"\b([A-H]\d{7})\b", line):
                names.setdefault(code, line.strip()[:50])
log("설명서에서 찾은 코드", len(names))


def read_dbf(path):
    with open(path, "rb") as f:
        head = f.read(32)
        n = struct.unpack("<I", head[4:8])[0]
        hlen, rlen = struct.unpack("<2H", head[8:12])
        fields, off = [], 1
        while True:
            c = f.read(32)
            if c[0] == 13:
                break
            fields.append((c[:11].split(b"\0")[0].decode("cp949", "replace"), chr(c[11]), off, c[16]))
            off += c[16]
        f.seek(hlen)
        buf = f.read(n * rlen)
    return n, rlen, fields, buf


DATE = re.compile(rb"^(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])?$")
summary = []
for zn in sorted(os.listdir(zdir)):
    m = re.search(r"_(N3[APL]_[A-Z0-9]+)\.zip$", zn)
    layer = m.group(1)
    with zipfile.ZipFile(os.path.join(zdir, zn)) as z:
        infos = z.infolist()
        assert all(not i.filename.startswith(("/", "\\")) and ".." not in i.filename for i in infos), zn
        dest = os.path.join(outdir, layer)
        assert not os.path.exists(dest), dest
        os.makedirs(dest)
        z.extractall(dest)
        stamp = max(i.date_time for i in infos)
        size = sum(i.file_size for i in infos)
    files = {}
    for root, _, fs in os.walk(dest):
        for f in fs:
            files[os.path.splitext(f)[1].lower()] = os.path.join(root, f)
    with open(files[".shp"], "rb") as f:
        h = f.read(100)
    stype = struct.unpack("<i", h[32:36])[0]
    bbox = struct.unpack("<4d", h[36:68])
    n, rlen, fields, buf = read_dbf(files[".dbf"])
    inside = bbox[2] >= JEJU[0] and bbox[0] <= JEJU[2] and bbox[3] >= JEJU[1] and bbox[1] <= JEJU[3]
    dates = {}
    for nm, _, off, ln in fields:
        vals = collections.Counter(buf[i * rlen + off:i * rlen + off + ln].strip() for i in range(n))
        good = {k: v for k, v in vals.items() if DATE.match(k)}
        if good and sum(good.values()) >= n * 0.5:
            dates[nm] = (min(good).decode(), max(good).decode(), max(good, key=good.get).decode())
    code = layer[4:]
    summary.append((layer, n))
    log(f"\n[{layer}] {names.get(code, '설명서에 없음')}")
    log(f"  형태 {TYPES.get(stype, stype)}, {n:,}건, 범위 {bbox[0]:.0f} {bbox[1]:.0f} {bbox[2]:.0f} {bbox[3]:.0f}, 제주 범위 {'안' if inside else '밖'}, 푼 크기 {size/1048576:.1f}MB, 압축 안 시각 {stamp[:5]}")
    log(f"  파일 {sorted(files)}  항목 {[x[0] for x in fields]}")
    if dates:
        log(f"  날짜 항목 (최소, 최대, 최빈): {dates}")
prj = next(os.path.join(r, f) for r, _, fs in os.walk(os.path.join(outdir, "N3L_A0020000")) for f in fs if f.lower().endswith(".prj"))
log("\n도로중심선 좌표계:", open(prj, encoding="utf-8", errors="replace").read()[:80])
log("합계 레이어", len(summary), "건수", f"{sum(x[1] for x in summary):,}")

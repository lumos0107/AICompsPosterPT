"""1:1,000 도엽 zip 묶음을 도엽별 빈 폴더에 풀고 신호등·신호등제어기·조명·횡단보도를 집계한다.

사용: python -I check_1000_batch.py <zip 폴더> <풀 폴더> <결과 파일>
"""
import collections
import os
import re
import struct
import sys
import zipfile

zdir, outroot, result = sys.argv[1:4]
sys.stdout.reconfigure(encoding="utf-8")
out = open(result, "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out.write(s + "\n")


def read(path, field=None):
    raw = open(path, "rb").read()
    n = struct.unpack("<I", raw[4:8])[0]
    hlen, rlen = struct.unpack("<2H", raw[8:12])
    off, pos, where = 1, 32, None
    while raw[pos] != 13:
        c = raw[pos:pos + 32]
        if field and c[:11].split(b"\0")[0].decode("cp949", "replace") == field:
            where = (off, c[16])
        off += c[16]
        pos += 32
    if not where:
        return n, collections.Counter()
    o, l = where
    return n, collections.Counter(raw[hlen + i * rlen + o:hlen + i * rlen + o + l].decode("cp949", "replace").strip() for i in range(n))


LAYERS = {"신호등": ("N1P_C0493376", "용도"), "차단기": ("N1P_C0503375", "구분"), "조명": ("N1P_C0220000", "구분"), "횡단보도": ("N1A_A0043325", None)}
tot = {k: collections.Counter() for k in LAYERS}
count = collections.Counter()
has = collections.Counter()
years = collections.Counter()
zips = sorted(f for f in os.listdir(zdir) if f.lower().endswith(".zip"))
bad = 0
for zn in zips:
    sheet = zn.split("_")[1]
    dest = os.path.join(outroot, sheet)
    assert not os.path.exists(dest), dest
    os.makedirs(dest)
    try:
        with zipfile.ZipFile(os.path.join(zdir, zn)) as z:
            assert all(not i.filename.startswith(("/", "\\")) and ".." not in i.filename for i in z.infolist())
            assert z.testzip() is None
            z.extractall(dest)
    except Exception as e:
        bad += 1
        log("불량", zn, type(e).__name__)
        continue
    files = {f.lower(): os.path.join(r, f) for r, _, fs in os.walk(dest) for f in fs}
    for k, (layer, field) in LAYERS.items():
        p = files.get(layer.lower() + ".dbf")
        if p:
            n, c = read(p, field)
            count[k] += n
            has[k] += 1
            tot[k].update(c)
    xml = os.path.join(zdir, zn[:-4] + ".xml")
    if os.path.exists(xml):
        t = open(xml, encoding="utf-8", errors="replace").read()
        m1 = re.search(r"<촬영년도>(\d+)", t)
        m2 = re.search(r"<제작년도>(\d+)", t)
        years[(m1.group(1) if m1 else "?", m2.group(1) if m2 else "?")] += 1
log(f"도엽 {len(zips)}장, 불량 {bad}장")
log("(촬영년도, 제작년도) 분포", years.most_common())
for k in LAYERS:
    log(f"{k}: {count[k]:,}건, {has[k]}장에 있음, 구분 {tot[k].most_common()}")

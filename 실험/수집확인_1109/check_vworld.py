"""브이월드 전국 면 자료를 파일별 빈 폴더에 풀고 제주 범위에 드는 건수를 센다.

사용: python -I check_vworld.py <결과 파일> <zip> <풀 폴더> [<zip> <풀 폴더> ...]
"""
import os
import re
import struct
import sys
import zipfile

from pyproj import Transformer

sys.stdout.reconfigure(encoding="utf-8")
JEJU = (873000, 1458000, 952000, 1559000)
to4326 = Transformer.from_crs(5179, 4326, always_xy=True)
out = open(sys.argv[1], "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out.write(s + "\n")


args = sys.argv[2:]
for zp, dest in zip(args[0::2], args[1::2]):
    assert not os.path.exists(dest), dest
    os.makedirs(dest)
    with zipfile.ZipFile(zp) as z:
        assert all(not i.filename.startswith(("/", "\\")) and ".." not in i.filename for i in z.infolist())
        z.extractall(dest)
    name = next(f for f in os.listdir(dest) if f.lower().endswith(".shp"))
    data = open(os.path.join(dest, name), "rb").read()
    pos, total, hits = 100, 0, []
    while pos < len(data):
        _, clen = struct.unpack(">2i", data[pos:pos + 8])
        s = pos + 8
        if struct.unpack("<i", data[s:s + 4])[0] != 0:
            x0, y0, x1, y1 = struct.unpack("<4d", data[s + 4:s + 36])
            total += 1
            if x1 >= JEJU[0] and x0 <= JEJU[2] and y1 >= JEJU[1] and y0 <= JEJU[3]:
                hits.append(((x0 + x1) / 2, (y0 + y1) / 2))
        pos = s + clen * 2
    log(f"[{name}] 전국 {total:,}건, 제주 범위 안 {len(hits)}건")
    for x, y in hits[:20]:
        lo, la = to4326.transform(x, y)
        log(f"   {la:.5f}, {lo:.5f}")
    xml = open(os.path.join(dest, name + ".xml"), encoding="utf-8", errors="replace").read()
    log("   xml 날짜 태그", sorted(set(re.findall(r"<(\w*[Dd]ate\w*)[^>]*>\s*(\d{4}-?\d{2}-?\d{2})", xml)))[:8])

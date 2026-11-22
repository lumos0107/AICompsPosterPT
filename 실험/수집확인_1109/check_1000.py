"""1:1,000 수치지형도 도엽 zip을 빈 폴더에 풀고 레이어별 건수와 코드값을 적는다. 사용: python -I check_1000.py <zip> <풀 폴더> <결과 파일>"""
import collections
import os
import struct
import sys
import zipfile

zp, dest, result = sys.argv[1:4]
sys.stdout.reconfigure(encoding="utf-8")
out = open(result, "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out.write(s + "\n")


assert not os.path.exists(dest), dest
os.makedirs(dest)
with zipfile.ZipFile(zp) as z:
    infos = z.infolist()
    assert all(not i.filename.startswith(("/", "\\")) and ".." not in i.filename for i in infos)
    log("압축 안 파일", len(infos), "개, 확장자", collections.Counter(os.path.splitext(i.filename)[1].lower() for i in infos).most_common())
    z.extractall(dest)
FOCUS = {"DIVI", "SERV", "KIND", "STRU", "TYPE"}
TYPES = {1: "점", 3: "선", 5: "면", 11: "점Z", 13: "선Z", 15: "면Z"}
for r, _, fs in sorted(os.walk(dest)):
    for f in sorted(fs):
        if not f.lower().endswith(".dbf"):
            continue
        base = os.path.join(r, f[:-4])
        with open(base + ".dbf", "rb") as d:
            h = d.read(32)
            n = struct.unpack("<I", h[4:8])[0]
            hlen, rlen = struct.unpack("<2H", h[8:12])
            fields, off = {}, 1
            while True:
                c = d.read(32)
                if c[0] == 13:
                    break
                fields[c[:11].split(b"\0")[0].decode("cp949", "replace")] = (off, c[16])
                off += c[16]
            d.seek(hlen)
            buf = d.read(n * rlen)
        st = "?"
        if os.path.exists(base + ".shp"):
            with open(base + ".shp", "rb") as s:
                s.seek(32)
                st = TYPES.get(struct.unpack("<i", s.read(4))[0], "?")
        vals = {}
        for k in fields:
            if k in FOCUS or k == "SCLS":
                o, l = fields[k]
                vals[k] = collections.Counter(buf[i * rlen + o:i * rlen + o + l].decode("cp949", "replace").strip() for i in range(n)).most_common(6)
        log(f"{f[:-4]} {st} {n:,}건 {vals}")

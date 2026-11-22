"""설명서 정독 뒤 추가 확인: 코드값 분포. 사용: python -I check_ngii3.py <풀기 폴더> <결과 파일>"""
import collections
import os
import struct
import sys

root, result = sys.argv[1:3]
sys.stdout.reconfigure(encoding="utf-8")
out = open(result, "w", encoding="utf-8")


def dist(layer, field):
    d = os.path.join(root, layer)
    p = next(os.path.join(r, f) for r, _, fs in os.walk(d) for f in fs if f.lower().endswith(".dbf"))
    with open(p, "rb") as f:
        h = f.read(32)
        n = struct.unpack("<I", h[4:8])[0]
        hlen, rlen = struct.unpack("<2H", h[8:12])
        off, where = 1, None
        while True:
            c = f.read(32)
            if c[0] == 13:
                break
            if c[:11].split(b"\0")[0].decode("cp949", "replace") == field:
                where = (off, c[16])
            off += c[16]
        f.seek(hlen)
        buf = f.read(n * rlen)
    o, l = where
    return collections.Counter(buf[i * rlen + o:i * rlen + o + l].decode("cp949", "replace").strip() for i in range(n)).most_common(14)


for layer, field in [("N3P_C0380000", "DIVI"), ("N3A_A0053326", "STRU"), ("N3A_A0010000", "SCLS"), ("N3L_A0010000", "SCLS"), ("N3L_A0020000", "RDDV"), ("N3L_A0020000", "SCLS"), ("N3L_A0020000", "ONSD"), ("N3L_A0020000", "DVYN"), ("N3P_C0340000", "DIVI"), ("N3A_A0063321", "TYPE")]:
    s = f"{layer} {field}: {dist(layer, field)}"
    print(s, flush=True)
    out.write(s + "\n")

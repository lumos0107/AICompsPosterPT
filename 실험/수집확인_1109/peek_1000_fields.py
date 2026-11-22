"""1:1,000 도엽의 지정 레이어 항목과 값 분포를 적는다. 사용: python -I peek_1000_fields.py <풀기 폴더> <결과 파일> <레이어> [...]"""
import collections
import os
import struct
import sys

root, result, *layers = sys.argv[1:]
sys.stdout.reconfigure(encoding="utf-8")
out = open(result, "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out.write(s + "\n")


for layer in layers:
    p = next(os.path.join(r, f) for r, _, fs in os.walk(root) for f in fs if f.lower() == layer.lower() + ".dbf")
    raw = open(p, "rb").read()
    n = struct.unpack("<I", raw[4:8])[0]
    hlen, rlen = struct.unpack("<2H", raw[8:12])
    fields, off, pos = [], 1, 32
    while raw[pos] != 13:
        c = raw[pos:pos + 32]
        fields.append((c[:11].split(b"\0")[0].decode("cp949", "replace"), chr(c[11]), off, c[16]))
        off += c[16]
        pos += 32
    log(f"\n[{layer}] {n}건, 항목 {[f[0] for f in fields]}")
    for name, _, o, l in fields:
        vals = collections.Counter(raw[hlen + i * rlen + o:hlen + i * rlen + o + l].decode("cp949", "replace").strip() for i in range(n))
        log(f"  {name}: 값 {len(vals)}종 {vals.most_common(5)}")

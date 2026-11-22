"""끝이 잘린 zip의 앞쪽 파일 머리를 차례로 읽어 이름, 크기, 작성일을 적는다. 사용: python -I peek_lfh.py <zip>"""
import os
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8")
path = sys.argv[1]
size = os.path.getsize(path)
with open(path, "rb") as f:
    pos = 0
    while pos + 30 <= size:
        f.seek(pos)
        h = f.read(30)
        if h[:4] != b"PK\x03\x04":
            print("머리 표시가 아님, 위치", pos)
            break
        flags, _, tm, dt, _, csize, usize, nlen, xlen = struct.unpack("<HHHHIIIHH", h[6:30])
        name = f.read(nlen).decode("cp949", "replace")
        extra = f.read(xlen)
        if csize == 0xFFFFFFFF or usize == 0xFFFFFFFF:
            i = 0
            while i + 4 <= len(extra):
                hid, sz = struct.unpack("<HH", extra[i:i + 4])
                if hid == 1:
                    vals = struct.unpack(f"<{sz // 8}Q", extra[i + 4:i + 4 + sz])
                    usize, csize = vals[0], vals[1] if len(vals) > 1 else csize
                i += 4 + sz
        day = f"{(dt >> 9) + 1980}-{(dt >> 5) & 15:02d}-{dt & 31:02d}"
        print(f"{name}  원본 {usize:,}  압축 {csize:,}  작성일 {day}  표시 {flags:#x}  시작 {pos:,}")
        if flags & 8 and csize == 0:
            print("  크기가 파일 뒤쪽에 있어 더 걷지 못함")
            break
        pos += 30 + nlen + xlen + csize
    print("파일 크기", f"{size:,}", "마지막 위치", f"{pos:,}", "잘림" if pos > size else "끝까지 읽음")

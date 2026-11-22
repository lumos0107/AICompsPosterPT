"""zip을 풀지 않고 안의 SHP·DBF 머리만 읽어 범위와 건수를 적는다. 끝이 잘린 zip은 앞쪽 파일 머리에서 이름만 읽는다.

사용: python -I peek_zip.py <zip> [...]
"""
import os
import struct
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
JEJU = (873000, 1458000, 952000, 1559000)
for path in sys.argv[1:]:
    print(os.path.basename(path), f"{os.path.getsize(path) / 1048576:.1f}MB")
    try:
        z = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        with open(path, "rb") as f:
            head = f.read(30)
            name_len, extra_len = struct.unpack("<2H", head[26:30])
            name = f.read(name_len).decode("cp949", "replace")
        print(f"  zip 끝부분(목록)이 없음. 첫 파일 이름 {name}, 머리 표시 {head[:4]!r}")
        continue
    with z:
        for i in z.infolist():
            line = f"  {i.filename}  원본 {i.file_size:,}  압축 {i.compress_size:,}  시각 {i.date_time[:3]}"
            ext = i.filename.lower().rsplit(".", 1)[-1]
            if ext == "shp":
                with z.open(i) as f:
                    h = f.read(100)
                t = struct.unpack("<i", h[32:36])[0]
                b = struct.unpack("<4d", h[36:68])
                hit = b[2] >= JEJU[0] and b[0] <= JEJU[2] and b[3] >= JEJU[1] and b[1] <= JEJU[3]
                line += f"\n    머리: 형태 {t}, 범위 {b[0]:.0f} {b[1]:.0f} {b[2]:.0f} {b[3]:.0f}, 제주 범위와 {'겹침' if hit else '안 겹침'}"
            elif ext == "dbf":
                with z.open(i) as f:
                    h = f.read(32)
                n = struct.unpack("<I", h[4:8])[0]
                line += f"\n    머리: {n:,}건"
            print(line)

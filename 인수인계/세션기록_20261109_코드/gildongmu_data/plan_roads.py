"""PC에 있는 도로 관련 원본 파일의 형태를 본다. 읽기 전용."""
import glob
import os
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8")
H = os.path.expanduser("~")
D = os.path.join(H, "Downloads")
WORDS = ["도로", "인도", "보도", "자전거", "육교", "교량", "입체", "N3", "DEM", "수치표고", "표고", "등고", "횡단", "화장실", "상가", "상권"]
print("== 내려받기 폴더에서 이름이 맞는 항목")
for n in sorted(os.listdir(D)):
    if any(w in n for w in WORDS):
        p = os.path.join(D, n)
        print("  ", n, "폴더" if os.path.isdir(p) else f"{os.path.getsize(p):,}B")

TYPES = {1: "점", 3: "선", 5: "면", 11: "점Z", 13: "선Z", 15: "면Z", 21: "점M", 23: "선M", 25: "면M"}
print("== shp 파일")
for folder in sorted(os.listdir(D)):
    p = os.path.join(D, folder)
    if not os.path.isdir(p) or not any(w in folder for w in WORDS):
        continue
    shps = glob.glob(os.path.join(p, "**", "*.shp"), recursive=True)
    print("--", folder, "shp", len(shps))
    for s in shps[:12]:
        with open(s, "rb") as f:
            b = f.read(100)
        t = struct.unpack("<i", b[32:36])[0]
        x0, y0, x1, y1 = struct.unpack("<4d", b[36:68])
        shx = s[:-4] + ".shx"
        n = (os.path.getsize(shx) - 100) // 8 if os.path.exists(shx) else -1
        print("  ", os.path.basename(s), TYPES.get(t, t), "개수", n, f"범위 {x0:.0f},{y0:.0f},{x1:.0f},{y1:.0f}", f"{os.path.getsize(s):,}B")
        prj = s[:-4] + ".prj"
        if os.path.exists(prj):
            print("     좌표계", open(prj, encoding="utf-8", errors="replace").read()[:70])
        dbf = s[:-4] + ".dbf"
        if os.path.exists(dbf):
            with open(dbf, "rb") as f:
                head = f.read(32)
                hlen = struct.unpack("<H", head[8:10])[0]
                names = []
                while f.tell() < hlen - 1:
                    c = f.read(32)
                    if c[0] == 13:
                        break
                    names.append(c[:11].split(b"\0")[0].decode("cp949", "replace"))
            print("     열", names)

try:
    import pyproj
    print("pyproj", pyproj.__version__)
except Exception as e:
    print("pyproj 없음", e)
try:
    import shapefile
    print("pyshp", shapefile.__version__)
except Exception as e:
    print("pyshp 없음", e)

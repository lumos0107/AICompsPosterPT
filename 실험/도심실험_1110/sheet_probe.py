import glob, os, struct, sys, collections
import numpy as np
from pyproj import Transformer
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵\수치지형도_1000_표본\제주도심_95장\풀기"
to5179 = Transformer.from_crs(5186, 5179, always_xy=True)
to4326 = Transformer.from_crs(5186, 4326, always_xy=True)
rows = []
for sd in sorted(glob.glob(os.path.join(ROOT, "*"))):
    if not os.path.isdir(sd): continue
    sh = os.path.basename(sd)
    b = [np.inf, np.inf, -np.inf, -np.inf]; layers = []
    for shp in glob.glob(os.path.join(sd, "*.shp")):
        d = open(shp, "rb").read(100)
        x0, y0, x1, y1 = struct.unpack("<4d", d[36:68])
        if x1 > x0 or y1 > y0:
            b = [min(b[0], x0), min(b[1], y0), max(b[2], x1), max(b[3], y1)]
        layers.append(os.path.basename(shp)[:12])
    rows.append((sh, b, layers))
print(len(rows))
print(sorted(set(l for r in rows for l in r[2]))[:80])
for sh, b, _ in rows[:8]:
    lo0, la0 = to4326.transform(b[0], b[1]); lo1, la1 = to4326.transform(b[2], b[3])
    print(sh, [round(v, 1) for v in b], round(b[2]-b[0]), round(b[3]-b[1]), f"{lo0:.5f} {la0:.5f} {lo1:.5f} {la1:.5f}")

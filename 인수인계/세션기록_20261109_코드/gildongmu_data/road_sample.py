"""도로중심선에서 길이 비례로 표본 점을 뽑아 지역별로 나눈다. 읽기 전용."""
import glob
import json
import os
import struct
import sys

import numpy as np
from pyproj import Transformer

sys.stdout.reconfigure(encoding="utf-8")
D = os.path.join(os.path.expanduser("~"), "Downloads")
p = glob.glob(os.path.join(D, "(연속수치지형도)도로중심선_제주", "**", "N3L_A0020000_50.shp"), recursive=True)[0]
data = open(p, "rb").read()
pos, mids, lens = 100, [], []
while pos < len(data):
    _, clen = struct.unpack(">2i", data[pos:pos + 8])
    s = pos + 8
    if struct.unpack("<i", data[s:s + 4])[0] != 0:
        np_, npts = struct.unpack("<2i", data[s + 36:s + 44])
        pts = np.frombuffer(data, "<f8", npts * 2, s + 44 + 4 * np_).reshape(-1, 2)
        L = float(np.hypot(*np.diff(pts, axis=0).T).sum())
        if L > 0:
            mids.append(pts[len(pts) // 2])
            lens.append(L)
    pos = s + clen * 2
mids, lens = np.array(mids), np.array(lens)
tr = Transformer.from_crs(5179, 4326, always_xy=True)
lon, lat = tr.transform(mids[:, 0], mids[:, 1])
jeju = (33.47 <= lat) & (lat <= 33.53) & (126.45 <= lon) & (lon <= 126.62)
seogwi = (33.235 <= lat) & (lat <= 33.285) & (126.40 <= lon) & (lon <= 126.60)
rest = ~(jeju | seogwi)
rng = np.random.default_rng(20261109)
out = {}
for name, mask, n in [("제주시내", jeju, 150), ("서귀포시내", seogwi, 100), ("그 외", rest, 150)]:
    idx = np.where(mask)[0]
    pick = rng.choice(idx, size=n, replace=False, p=lens[idx] / lens[idx].sum())
    out[name] = [[int(mids[i, 0]), int(mids[i, 1])] for i in pick]
    print(name, "도로 길이", round(lens[idx].sum() / 1000), "km", f"{lens[idx].sum() / lens.sum():.1%}")
print(json.dumps(out, separators=(",", ":")))

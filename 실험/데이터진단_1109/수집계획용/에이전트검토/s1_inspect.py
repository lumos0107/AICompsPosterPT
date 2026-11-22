import collections
import struct
import sys
import numpy as np
sys.path.insert(0, r"C:\Users\seungjun\AppData\Local\Temp\plan_review_Br6p2s")
from lib_shp import *

sys.stdout.reconfigure(encoding="utf-8")
TYPES = {1: "pt", 3: "line", 5: "poly", 11: "ptZ", 13: "lineZ", 15: "polyZ", 23: "lineM"}
for k, b in FILES.items():
    with open(b + ".shp", "rb") as f:
        h = f.read(100)
    t = struct.unpack("<i", h[32:36])[0]
    bb = struct.unpack("<4d", h[36:68])
    n, hlen, rlen, flds = dbf_fields(b)
    prj = open(b + ".prj", encoding="utf-8", errors="replace").read()
    print(f"== {k}: type {TYPES.get(t, t)} bbox {[round(x) for x in bb]} records {n}")
    print("   prj:", prj[:160])
    print("   fields:", [(f[0], f[1], f[3]) for f in flds])

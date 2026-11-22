"""캡처한 영상 위에 도로 간선과 분기 노드를 로컬에서 겹쳐 그린다. 결과는 영상_표시/ 아래."""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\새그래프_1110"
sys.path.insert(0, r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\데이터진단_1109\수집계획용\에이전트검토")
from lib_shp import read_shp

sys.stdout.reconfigure(encoding="utf-8")
ROAD = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵\연속수치지도_제주_20261109\풀기\N3L_A0020000\N3L_A0020000"
RES = {10: 2.04, 12: 0.51, 13: 0.255}
d = np.load(os.path.join(HERE, "그래프_새자료.npz"))
xy, A, B, narrow, island, line, a, b = d["xy"], d["A"], d["B"], d["narrow"], d["island"], d["line"], d["a"], d["b"]
lines = [p for rec, parts in read_shp(ROAD, clip=False) for p in parts]
deg = np.bincount(A, minlength=len(xy)) + np.bincount(B, minlength=len(xy))
items = json.load(open(os.path.join(HERE, "입체위치.json"), encoding="utf-8"))
mid = (xy[A] + xy[B]) / 2
font = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 15)
os.makedirs(os.path.join(HERE, "영상_표시"), exist_ok=True)
for it in items:
    r = RES[it["z"]]
    im = Image.open(os.path.join(HERE, "영상", it["id"] + ".jpg")).convert("RGB")
    dr = ImageDraw.Draw(im)
    W = 400 * r + 200

    def px(P):
        return [(400 + (x - it["x"]) / r, 390 - (y - it["y"]) / r) for x, y in P]

    near = np.where((np.abs(mid[:, 0] - it["x"]) < W) & (np.abs(mid[:, 1] - it["y"]) < W))[0]
    for ei in near.tolist():
        p = lines[line[ei]][a[ei]:b[ei] + 1]
        dr.line(px(p), fill=(255, 150, 0) if narrow[ei] else (255, 240, 0), width=1)
    ns = np.unique(np.r_[A[near], B[near]])
    for n in ns[deg[ns] >= 3].tolist():
        X, Y = px([xy[n]])[0]
        R = 7 if deg[n] == 3 else 10
        dr.ellipse([X - R, Y - R, X + R, Y + R], outline=(255, 40, 40), width=2)
        dr.text((X + R + 1, Y - 8), str(int(deg[n])), fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    dr.text((8, 48), f"{it['id']} {it['name']} ({it['kind']}) 가로 {800 * r:.0f}m", fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    im.save(os.path.join(HERE, "영상_표시", it["id"] + ".jpg"), quality=85)
print("끝", len(items))

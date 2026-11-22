"""폭이 3m 이상에서 미만으로 바뀐 성산읍 간선 표본을 영상에 로컬로 겹쳐 그린다. 표본 간선은 빨강, 폭 3m 이상 도로는 노랑, 그 외 폭 미달은 주황."""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\새그래프_1110"
sys.path.insert(0, r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\데이터진단_1109\수집계획용\에이전트검토")
from lib_shp import read_shp

ROAD = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵\연속수치지도_제주_20261109\풀기\N3L_A0020000\N3L_A0020000"
d = np.load(os.path.join(HERE, "그래프_새자료.npz"))
xy, A, B, narrow, line, a, b = d["xy"], d["A"], d["B"], d["narrow"], d["line"], d["a"], d["b"]
lines = [p for r, parts in read_shp(ROAD, clip=False) for p in parts]
mid = (xy[A] + xy[B]) / 2
items = json.load(open(os.path.join(HERE, "폭변화표본.json"), encoding="utf-8"))
font = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 15)
R = 0.255
tiles = []
for it in items:
    im = Image.open(os.path.join(HERE, "영상", it["id"] + ".jpg")).convert("RGB")
    dr = ImageDraw.Draw(im)

    def px(P):
        return [(400 + (x - it["x"]) / R, 390 - (y - it["y"]) / R) for x, y in P]

    near = np.where((np.abs(mid[:, 0] - it["x"]) < 300) & (np.abs(mid[:, 1] - it["y"]) < 300))[0]
    for ei in near.tolist():
        c = (255, 40, 40) if ei == it["e"] else (255, 150, 0) if narrow[ei] else (255, 240, 0)
        if ei != it["e"]:
            dr.line(px(lines[line[ei]][a[ei]:b[ei] + 1]), fill=c, width=1)
    # 표본 간선은 도로를 가리지 않게 양 끝만 표시
    p = lines[line[it["e"]]][a[it["e"]]:b[it["e"]] + 1]
    for X, Y in px([p[0], p[-1]]):
        dr.ellipse([X - 6, Y - 6, X + 6, Y + 6], outline=(255, 40, 40), width=2)
    X, Y = 400, 390
    dr.line([(X - 22, Y), (X - 10, Y)], fill=(0, 255, 255), width=2)
    dr.line([(X + 10, Y), (X + 22, Y)], fill=(0, 255, 255), width=2)
    c = im.crop((240, 230, 560, 550)).resize((400, 400), Image.LANCZOS)
    ImageDraw.Draw(c).text((6, 4), f"{it['id']} 새 {it['새폭']}m / 5월 {it['월5폭']}m", fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    tiles.append(c)
M = Image.new("RGB", (1600, 1200), (255, 255, 255))
for i, t in enumerate(tiles):
    M.paste(t, (400 * (i % 4), 400 * (i // 4)))
M.save(os.path.join(HERE, "폭변화표본.jpg"), quality=88)
print("끝")

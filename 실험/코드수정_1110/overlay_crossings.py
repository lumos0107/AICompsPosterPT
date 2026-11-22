"""경로 교차 후보 영상에 도로선(노랑)·이 교차를 지나는 예비 경로(빨강)·노드(흰 원)를 로컬에서 겹쳐 그리고 4×4 모음을 만든다.
결과: 영상_표시/X??.jpg, 교차모음_??.jpg   실행: py -I overlay_crossings.py [접미사=예비] [경로json=예비경로.json]
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(EXP, "데이터진단_1109", "수집계획용", "에이전트검토"))
from lib_shp import read_shp

sys.stdout.reconfigure(encoding="utf-8")
TAG = sys.argv[1] if len(sys.argv) > 1 else "예비"
SRC = sys.argv[2] if len(sys.argv) > 2 else "예비경로.json"
R = 0.255
ROAD = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵\연속수치지도_제주_20261109\풀기\N3L_A0020000\N3L_A0020000"
g = np.load(os.path.join(EXP, "도심실험_1110", "그래프_도심_114칸.npz"))
xy, A, B, main, gl, ga, gb = g["xy"], g["A"], g["B"], g["main"], g["line"], g["a"], g["b"]
lines = [p for r, parts in read_shp(ROAD, clip=False) for p in parts]
mid = (xy[A] + xy[B]) / 2
items = json.load(open(os.path.join(HERE, f"경로교차_{TAG}.json"), encoding="utf-8"))
routes = {f"{m['start']}-{m.get('anchor_id', 0)}-{m['setting']}-{m['route']}": m for m in json.load(open(os.path.join(HERE, SRC), encoding="utf-8"))}
fw = Transformer.from_crs(4326, 5179, always_xy=True)
font = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 15)
big = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 26)
MARK = "영상_표시" if TAG == "예비" else f"영상_표시_{TAG}"
os.makedirs(os.path.join(HERE, MARK), exist_ok=True)
for it in items:
    c = np.array([it["x"], it["y"]], float)
    IMG = "영상" if TAG == "예비" else f"영상_{TAG}"
    MARK = "영상_표시" if TAG == "예비" else f"영상_표시_{TAG}"
    im = Image.open(os.path.join(HERE, IMG, it["id"] + ".jpg")).convert("RGB")
    dr = ImageDraw.Draw(im)
    px = lambda P: [(400 + (x - c[0]) / R, 390 - (y - c[1]) / R) for x, y in P]
    near = np.where(main & (np.abs(mid[:, 0] - c[0]) < 160) & (np.abs(mid[:, 1] - c[1]) < 160))[0]
    for e in near.tolist():
        dr.line(px(lines[gl[e]][ga[e]:gb[e] + 1]), fill=(255, 240, 0), width=2)
    for key in it["routes"][:6]:
        m = routes.get(key)
        if not m:
            continue
        ll = np.array(m["coords"])
        X, Y = fw.transform(ll[:, 1], ll[:, 0])
        P = np.c_[X, Y]
        sel = np.where(np.hypot(*(P - c).T) < 70)[0]
        if len(sel):
            k0, k1 = max(sel.min() - 1, 0), min(sel.max() + 2, len(P))
            dr.line(px(P[k0:k1]), fill=(255, 30, 30), width=4)
    X, Y = px([c])[0]
    dr.ellipse([X - 9, Y - 9, X + 9, Y + 9], outline=(255, 255, 255), width=3)
    dr.text((8, 48), f"{it['id']} 차수 {it['deg']} 폭 {it['widths'][:3]} {'/'.join(it['kinds'])} 가로 204m", fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    im.save(os.path.join(HERE, MARK, it["id"] + ".jpg"), quality=85)
for k in range(0, len(items), 16):
    sheet = Image.new("RGB", (4 * 300, 4 * 300), "white")
    for j, it in enumerate(items[k:k + 16]):
        im = Image.open(os.path.join(HERE, MARK, it["id"] + ".jpg")).crop((180, 170, 620, 610)).resize((300, 300))
        ImageDraw.Draw(im).text((6, 4), it["id"], fill=(255, 255, 255), font=big, stroke_width=3, stroke_fill=(0, 0, 0))
        sheet.paste(im, ((j % 4) * 300, (j // 4) * 300))
    sheet.save(os.path.join(HERE, f"교차모음_{k // 16 + 1:02d}.jpg" if TAG == "예비" else f"교차모음_{TAG}_{k // 16 + 1:02d}.jpg"), quality=85)
print("끝", len(items), "모음", (len(items) + 15) // 16)

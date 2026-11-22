"""무작위 20곳 영상에 도로·노드를 로컬에서 겹쳐 묶음 그림을 만들고, R13 노드가 후보에서 빠진 이유와 소구역 안 후보 수를 출력한다."""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\새그래프_1110"
sys.path.insert(0, r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\데이터진단_1109\수집계획용\에이전트검토")
from lib_shp import dbf_columns, read_shp

sys.stdout.reconfigure(encoding="utf-8")
ROAD = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵\연속수치지도_제주_20261109\풀기\N3L_A0020000\N3L_A0020000"
d = np.load(os.path.join(HERE, "그래프_새자료.npz"))
xy, A, B, narrow, island, rec, line, a, b = d["xy"], d["A"], d["B"], d["narrow"], d["island"], d["rec"], d["line"], d["a"], d["b"]
lines = [p for r, parts in read_shp(ROAD, clip=False) for p in parts]
at = dbf_columns(ROAD, ["RVWD", "DVYN", "NAME"])
wid = np.array([float(x or 0) for x in at["RVWD"]])
dv = np.array(at["DVYN"])
final = ~narrow & ~island
deg = np.bincount(A[final], minlength=len(xy)) + np.bincount(B[final], minlength=len(xy))
mid = (xy[A] + xy[B]) / 2
items = json.load(open(os.path.join(HERE, "입체위치2.json"), encoding="utf-8"))
font = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 15)
R = 0.255
tiles = []
for it in items:
    im = Image.open(os.path.join(HERE, "영상", it["id"] + ".jpg")).convert("RGB")
    dr = ImageDraw.Draw(im)

    def px(P):
        return [(400 + (x - it["x"]) / R, 390 - (y - it["y"]) / R) for x, y in P]

    near = np.where((np.abs(mid[:, 0] - it["x"]) < 300) & (np.abs(mid[:, 1] - it["y"]) < 300) & final)[0]
    for ei in near.tolist():
        dr.line(px(lines[line[ei]][a[ei]:b[ei] + 1]), fill=(255, 240, 0), width=1)
    ns = np.unique(np.r_[A[near], B[near]])
    for n in ns[deg[ns] >= 3].tolist():
        X, Y = px([xy[n]])[0]
        dr.ellipse([X - 8, Y - 8, X + 8, Y + 8], outline=(255, 40, 40), width=2)
    c = im.crop((200, 190, 600, 590))
    ImageDraw.Draw(c).text((6, 4), f"{it['id']} {it['name']}", fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    tiles.append(c)
for k, s in enumerate([tiles[:12], tiles[12:]]):
    rows = (len(s) + 3) // 4
    M = Image.new("RGB", (1600, 400 * rows), (255, 255, 255))
    for i, t in enumerate(s):
        M.paste(t, (400 * (i % 4), 400 * (i // 4)))
    M.save(os.path.join(HERE, f"무작위표본_{k + 1}.jpg"), quality=85)

# R13 노드
P = np.array([911902, 1497204])
n = int(np.argmin(np.hypot(*(xy - P).T)))
print("R13에 가장 가까운 노드", n, "거리", round(float(np.hypot(*(xy[n] - P))), 1), "전체 차수", int(((A == n) | (B == n)).sum()), "최종 차수", int(deg[n]))
for ei in np.where((A == n) | (B == n))[0].tolist():
    p = lines[line[ei]][a[ei]:b[ei] + 1]
    if B[ei] == n:
        p = p[::-1]
    c = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]
    t = min(15.0, c[-1])
    q = np.array([np.interp(t, c, p[:, 0]), np.interp(t, c, p[:, 1])]) - p[0]
    print(f"  간선 {ei}: 방위 {np.degrees(np.arctan2(q[1], q[0])) % 360:.0f}도, 길이 {c[-1]:.0f}m, 폭 {wid[rec[ei]]}, 분리대 {dv[rec[ei]]}, 폭미달 {bool(narrow[ei])}, 이름 {at['NAME'][rec[ei]]!r}")

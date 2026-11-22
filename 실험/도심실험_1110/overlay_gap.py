"""20m 밖 30m 안 묶음 27곳: 영상 위에 도로선·차수 3+ 노드·1:1,000 신호 점을 로컬에서 겹쳐 그리고, 그 교차로가 다른 점으로 20m 안에 이미 신호 노드인지 계산한다.

표시: 노란 선=실험 그래프 간선, 빨간 채운 원=20m 신호 노드, 빨간 빈 원=신호 노드 아님(차수 3+), 파란 점=이 묶음의 1:1,000 점, 하늘색 점=다른 묶음 점, 흰 원=가장 가까운 노드 중심 20m.
결과: 영상_표시/*.jpg, 묶음표_1.jpg~, 묶음_20과30사이_계산.csv
"""
import csv
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
G = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\새그래프_1110"
sys.path.insert(0, r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\데이터진단_1109\수집계획용\에이전트검토")
from lib_shp import read_shp

sys.stdout.reconfigure(encoding="utf-8")
ROAD = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵\연속수치지도_제주_20261109\풀기\N3L_A0020000\N3L_A0020000"
R = 0.255
g = np.load(os.path.join(HERE, "그래프_도심.npz"))
xy, A, B, main, line, a, b, deg = g["xy"], g["A"], g["B"], g["main"], g["line"], g["a"], g["b"], g["deg_full"]
lines = [p for r, parts in read_shp(ROAD, clip=False) for p in parts]
nodes = np.unique(np.r_[A[main], B[main]])
jn = nodes[deg[nodes] >= 3]
tj = cKDTree(xy[jn])
sig = [r for r in csv.DictReader(open(os.path.join(G, "신호1000.csv"), encoding="utf-8-sig")) if r["지역"] == "제주 도심"]
Q = np.array([(float(r["x5179"]), float(r["y5179"])) for r in sig])
marked = set(int(jn[i]) for lst in tj.query_ball_point(Q, 20.0) for i in lst)
items = json.load(open(os.path.join(HERE, "묶음_20과30사이.json"), encoding="utf-8"))
tq = cKDTree(Q)
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
pr = tq.query_pairs(30.0, output_type="ndarray")
_, cl = connected_components(coo_matrix((np.ones(len(pr)), (pr[:, 0], pr[:, 1])), shape=(len(Q), len(Q))), directed=False)
mid = (xy[A] + xy[B]) / 2
font = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 15)
big = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 22)
os.makedirs(os.path.join(HERE, "영상_표시"), exist_ok=True)
rows = []
for it in items:
    c = np.array([it["x"], it["y"]], float)
    own = set(np.where(cl == int(it["id"][1:]))[0].tolist())
    assert len(own) == it["n_light"] + it["n_ctrl"]
    n0 = it["node"]
    near30 = [int(jn[i]) for i in tj.query_ball_point(c, 40.0)]
    rows.append(dict(묶음=it["id"], 신호등=it["n_light"], 제어기=it["n_ctrl"], 최소거리=it["dmin"], 가장가까운노드=n0, 노드차수=it["deg"],
                     가장가까운노드가_다른점으로_20m신호노드=n0 in marked, 중심40m안_차수3노드=len(near30), 그중_20m신호노드=sum(n in marked for n in near30),
                     붙은도로폭=" ".join(str(w) for w in it["widths"])))
    im = Image.open(os.path.join(HERE, "영상", it["id"] + ".jpg")).convert("RGB")
    dr = ImageDraw.Draw(im)

    def px(P):
        return [(400 + (x - c[0]) / R, 390 - (y - c[1]) / R) for x, y in P]

    near = np.where(main & (np.abs(mid[:, 0] - c[0]) < 160) & (np.abs(mid[:, 1] - c[1]) < 160))[0]
    for ei in near.tolist():
        dr.line(px(lines[line[ei]][a[ei]:b[ei] + 1]), fill=(255, 240, 0), width=2)
    X, Y = px([xy[n0]])[0]
    rr = 20 / R
    dr.ellipse([X - rr, Y - rr, X + rr, Y + rr], outline=(255, 255, 255), width=2)
    ns = np.unique(np.r_[A[near], B[near]])
    for n in ns[deg[ns] >= 3].tolist():
        X, Y = px([xy[n]])[0]
        if n in marked:
            dr.ellipse([X - 7, Y - 7, X + 7, Y + 7], fill=(255, 40, 40), outline=(0, 0, 0))
        else:
            dr.ellipse([X - 7, Y - 7, X + 7, Y + 7], outline=(255, 40, 40), width=3)
    for i in tq.query_ball_point(c, 200).__iter__():
        X, Y = px([Q[i]])[0]
        if i in own:
            dr.ellipse([X - 6, Y - 6, X + 6, Y + 6], fill=(30, 120, 255), outline=(255, 255, 255))
        else:
            dr.ellipse([X - 4, Y - 4, X + 4, Y + 4], fill=(120, 230, 255), outline=(0, 0, 0))
    dr.text((8, 48), f"{it['id']} 신호등 {it['n_light']} 제어기 {it['n_ctrl']} 최소 {it['dmin']}m 차수 {it['deg']} 가로 204m", fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    im.save(os.path.join(HERE, "영상_표시", it["id"] + ".jpg"), quality=85)
with open(os.path.join(HERE, "묶음_20과30사이_계산.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
for r in rows:
    print(r)
print("가장 가까운 노드가 이미 신호 노드:", sum(r["가장가까운노드가_다른점으로_20m신호노드"] for r in rows), "/", len(rows))
# 모음 그림 (3x3, 가운데 560x560 잘라 380으로)
for k in range(0, len(items), 9):
    sheet = Image.new("RGB", (3 * 380, 3 * 380), "white")
    for j, it in enumerate(items[k:k + 9]):
        im = Image.open(os.path.join(HERE, "영상_표시", it["id"] + ".jpg")).crop((120, 110, 680, 670)).resize((380, 380))
        ImageDraw.Draw(im).text((6, 4), it["id"], fill=(255, 255, 255), font=big, stroke_width=3, stroke_fill=(0, 0, 0))
        sheet.paste(im, ((j % 3) * 380, (j // 3) * 380))
    sheet.save(os.path.join(HERE, f"묶음표_{k // 9 + 1}.jpg"), quality=88)
print("끝")

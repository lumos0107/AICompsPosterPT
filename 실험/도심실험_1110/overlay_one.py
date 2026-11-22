"""넓힌 범위에서 새로 생긴 20~30m 묶음 하나(S271)를 영상 위에 겹쳐 그린다. 표시는 overlay_gap.py와 같다. 실행: py -I overlay_one.py"""
import csv, json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = os.path.dirname(os.path.abspath(__file__))
G = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\새그래프_1110"
sys.path.insert(0, r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\데이터진단_1109\수집계획용\에이전트검토")
from lib_shp import read_shp
ROAD = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵\연속수치지도_제주_20261109\풀기\N3L_A0020000\N3L_A0020000"
R = 0.255
g = np.load(os.path.join(HERE, "그래프_도심_114칸.npz"))
xy, A, B, main, line, a, b, deg = g["xy"], g["A"], g["B"], g["main"], g["line"], g["a"], g["b"], g["deg_full"]
lines = [p for r, parts in read_shp(ROAD, clip=False) for p in parts]
nodes = np.unique(np.r_[A[main], B[main]]); jn = nodes[deg[nodes] >= 3]; tj = cKDTree(xy[jn])
sig = [r for r in csv.DictReader(open(os.path.join(G, "신호1000.csv"), encoding="utf-8-sig")) if r["지역"] == "제주 도심"]
sig += list(csv.DictReader(open(os.path.join(HERE, "신호1000_북쪽19장.csv"), encoding="utf-8-sig")))
Q = np.array([(float(r["x5179"]), float(r["y5179"])) for r in sig]); tq = cKDTree(Q)
pr = tq.query_pairs(30.0, output_type="ndarray")
_, cl = connected_components(coo_matrix((np.ones(len(pr)), (pr[:, 0], pr[:, 1])), shape=(len(Q), len(Q))), directed=False)
marked = set(int(jn[i]) for lst in tj.query_ball_point(Q, 20.0) for i in lst)
it = [i for i in json.load(open(os.path.join(HERE, "묶음_20과30사이_114칸.json"), encoding="utf-8")) if i["id"] == "S271"][0]
c = np.array([it["x"], it["y"]], float); own = set(np.where(cl == 271)[0].tolist())
im = Image.open(os.path.join(HERE, "영상", "N271.jpg")).convert("RGB"); dr = ImageDraw.Draw(im)
px = lambda P: [(400 + (x - c[0]) / R, 390 - (y - c[1]) / R) for x, y in P]
mid = (xy[A] + xy[B]) / 2
near = np.where(main & (np.abs(mid[:, 0] - c[0]) < 160) & (np.abs(mid[:, 1] - c[1]) < 160))[0]
for ei in near.tolist():
    dr.line(px(lines[line[ei]][a[ei]:b[ei] + 1]), fill=(255, 240, 0), width=2)
X, Y = px([xy[it["node"]]])[0]; rr = 20 / R
dr.ellipse([X - rr, Y - rr, X + rr, Y + rr], outline=(255, 255, 255), width=2)
ns = np.unique(np.r_[A[near], B[near]])
for n in ns[deg[ns] >= 3].tolist():
    X, Y = px([xy[n]])[0]
    if n in marked: dr.ellipse([X - 7, Y - 7, X + 7, Y + 7], fill=(255, 40, 40), outline=(0, 0, 0))
    else: dr.ellipse([X - 7, Y - 7, X + 7, Y + 7], outline=(255, 40, 40), width=3)
for i in tq.query_ball_point(c, 200):
    X, Y = px([Q[i]])[0]
    if i in own: dr.ellipse([X - 6, Y - 6, X + 6, Y + 6], fill=(30, 120, 255), outline=(255, 255, 255))
    else: dr.ellipse([X - 4, Y - 4, X + 4, Y + 4], fill=(120, 230, 255), outline=(0, 0, 0))
font = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 15)
dr.text((8, 48), f"S271 신호등 {it['n_light']} 최소 {it['dmin']}m 차수 {it['deg']} 가로 204m", fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
im.save(os.path.join(HERE, "영상_표시", "N271.jpg"), quality=85)
print("own", len(own), "nearest node already marked by others:", it["node"] in marked)

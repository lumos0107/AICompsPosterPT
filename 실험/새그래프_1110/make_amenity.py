"""편의시설(화장실, 편의점, 공원)을 하나의 표로 정리한다. 원본은 읽기만 한다.
화장실: 제주시 전용 자료(좌표, 빈 16건은 주소 변환 성공분으로 채움) + 표준 서귀포시(주소 변환 '성공'만).
        변환 '모호'와 '실패'는 넣지 않고 숫자를 기록한다.
편의점: 상가정보 제주 파일의 상권업종소분류명 '편의점'.
공원: 도시공원 표준 제주시·서귀포시. 공원은 점 1개라 넓은 공원은 입구 위치가 아니다(계획서 7장).
같은 종류 5m 안의 점은 하나로 합친다.
실행: py -I make_amenity.py
결과: 편의시설.csv, 편의시설.out
"""
import collections
import csv
import io
import os
import sys
import zipfile

import numpy as np
from pyproj import Transformer
from scipy.spatial import cKDTree

HERE = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\새그래프_1110"
RAW = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\공공데이터포털"
sys.stdout.reconfigure(encoding="utf-8")
out = open(os.path.join(HERE, "편의시설.out"), "w", encoding="utf-8")
to5179 = Transformer.from_crs(4326, 5179, always_xy=True)
X0, Y0, X1, Y1 = 873000, 1458000, 952000, 1559000


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out.write(s + "\n")
    out.flush()


def read(p):
    raw = open(p, "rb").read()
    for enc in ("utf-8-sig", "cp949"):
        try:
            return list(csv.DictReader(io.StringIO(raw.decode(enc))))
        except UnicodeDecodeError:
            continue
    raise ValueError(p)


def f(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return float("nan")


def in_box(x, y):
    return X0 <= x <= X1 and Y0 <= y <= Y1


rows = []  # 종류, 이름, x, y, 출처, 기준일
geo = list(csv.DictReader(open(os.path.join(HERE, "화장실_변환.csv"), encoding="utf-8-sig")))
log("주소 변환 결과:", collections.Counter((r["출처"], r["상태"]) for r in geo).most_common())
fix = {r["번호"]: r for r in geo if r["출처"] == "제주시_보완"}
jj = read(os.path.join(RAW, "제주시_공중화장실", "제주시_공중화장실.csv"))
nos = {c.replace(" ", ""): c for c in jj[0]}
used_fix = 0
for r in jj:
    la, lo = f(r[nos["위도좌표"]]), f(r[nos["경도좌표"]])
    x, y = (float("nan"), float("nan"))
    if la == la and lo == lo and la != 0 and lo != 0:
        x, y = to5179.transform(lo, la)
    src = "제주시 공중화장실"
    if not (x == x and in_box(x, y)):
        g = fix.get(r[list(jj[0].keys())[0]])
        if g is None or g["상태"] != "성공":
            continue
        x, y = float(g["x"]), float(g["y"])
        src = "제주시 공중화장실(주소 변환)"
        used_fix += 1
    rows.append(("화장실", r[nos["화장실명"]].strip(), x, y, src, [r[v] for k, v in nos.items() if "기준일" in k][0].strip()))
log(f"제주시 화장실 {sum(1 for r in rows if r[0] == '화장실')}건, 그중 주소 변환으로 채움 {used_fix}")
for r in geo:
    if r["출처"] == "표준_서귀포시" and r["상태"] == "성공":
        rows.append(("화장실", r["이름"].strip(), float(r["x"]), float(r["y"]), "공중화장실 표준 서귀포시(주소 변환)", r["기준일"].strip()))

z = zipfile.ZipFile(os.path.join(RAW, "상가상권정보_전국", "상가상권정보_전국.zip"))
info = [i for i in z.infolist() if "제주" in i.filename or "제주" in i.filename.encode("cp437", "replace").decode("cp949", "replace")][0]
sh = list(csv.DictReader(io.StringIO(z.read(info).decode("utf-8-sig"))))
conv = [r for r in sh if r["상권업종소분류명"].strip() == "편의점"]
for r in conv:
    x, y = to5179.transform(float(r["경도"]), float(r["위도"]))
    rows.append(("편의점", r["상호명"].strip(), x, y, "상가정보", "2026-09"))
log(f"편의점 {len(conv)}건")

for nm in ("도시공원표준_제주특별자치도_제주시_도시공원정보", "도시공원표준_제주특별자치도_서귀포시_도시공원정보"):
    pk = read(os.path.join(RAW, nm, nm + ".csv"))
    n1 = {c.replace(" ", ""): c for c in pk[0]}
    la = [v for k, v in n1.items() if "위도" in k][0]
    lo = [v for k, v in n1.items() if "경도" in k][0]
    nc = [v for k, v in n1.items() if "공원명" in k][0]
    dc = [v for k, v in n1.items() if "기준일" in k][0]
    for r in pk:
        x, y = to5179.transform(f(r[lo]), f(r[la]))
        rows.append(("공원", r[nc].strip(), x, y, nm.split("_")[1] + " 도시공원", r[dc].strip()))
log("정리 전:", collections.Counter(r[0] for r in rows).most_common())

out_rows = []
for kind in ("화장실", "편의점", "공원"):
    rs = [r for r in rows if r[0] == kind and in_box(r[2], r[3])]
    p = np.array([(r[2], r[3]) for r in rs])
    parent = list(range(len(rs)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    pairs = cKDTree(p).query_pairs(5.0, output_type="ndarray")
    for a, b in pairs.tolist():
        parent[find(a)] = find(b)
    roots = sorted({find(i) for i in range(len(rs))})
    log(f"{kind}: 범위 안 {len(rs)}건, 5m 안 쌍 {len(pairs)}, 합친 뒤 {len(roots)}건")
    for r0 in roots:
        out_rows.append(rs[r0])

g = np.load(os.path.join(HERE, "그래프_최종.npz"))
xy, A, B, main = g["xy"], g["A"], g["B"], g["main"]
mids = (xy[A[main]] + xy[B[main]]) / 2
t = cKDTree(mids)
for kind in ("화장실", "편의점", "공원"):
    p = np.array([(r[2], r[3]) for r in out_rows if r[0] == kind])
    d = t.query(p)[0]
    log(f"{kind}: 최종 그래프 간선 중점까지 중앙값 {np.median(d):.1f}m, 500m 초과 {int((d > 500).sum())}건")
with open(os.path.join(HERE, "편의시설.csv"), "w", encoding="utf-8-sig", newline="") as fo:
    w = csv.writer(fo)
    w.writerow(["종류", "이름", "x5179", "y5179", "출처", "기준일"])
    for r in out_rows:
        w.writerow([r[0], r[1], round(r[2], 2), round(r[3], 2), r[4], r[5]])
log(f"편의시설.csv {len(out_rows):,}건")
log("끝")

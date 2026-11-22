"""횡단·신호 자료를 서귀포시에 맞춰 다시 비교하고 묶음 수를 센다. 읽기 전용."""
import collections
import csv
import glob
import io
import math
import os
import sys

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\공공데이터포털"


def load(label):
    p = glob.glob(os.path.join(ROOT, label, "*.csv"))[0]
    raw = open(p, "rb").read()
    for enc in ("utf-8-sig", "cp949"):
        try:
            return list(csv.DictReader(io.StringIO(raw.decode(enc))))
        except UnicodeDecodeError:
            continue


def m(rows):
    out = []
    for r in rows:
        try:
            la, lo = float(r["위도"]), float(r["경도"])
        except (KeyError, TypeError, ValueError):
            continue
        out.append(((lo - 126.5) * 111320 * math.cos(math.radians(33.4)), (la - 33.4) * 110940))
    return np.array(out)


def clusters(a, d):
    pairs = cKDTree(a).query_pairs(d, output_type="ndarray")
    n = len(a)
    g = coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(n, n))
    return connected_components(g, directed=False)[0]


sig = load("제주_어린이보호구역_신호등")
print("어린이 신호등 구분", collections.Counter(r["신호등구분"] for r in sig).most_common())
print("어린이 신호등 시군구", collections.Counter(r["시군구명"] for r in sig).most_common())
a = m(sig)
print("어린이 신호등 묶음: 30m", clusters(a, 30), "50m", clusters(a, 50), "/", len(a))
ped = [r for r in sig if r["신호등구분"] == "보행등"]
if ped:
    print("보행등만", len(ped), "묶음 30m", clusters(m(ped), 30))

cross = load("제주_어린이보호구역_횡단보도")
print("어린이 횡단보도 시군구", collections.Counter(r["시군구명"] for r in cross).most_common())
print("어린이 횡단보도 보행신호", collections.Counter((r["시군구명"], r["보행자신호등유무"]) for r in cross).most_common())

std = load("횡단보도표준_제주특별자치도_서귀포시_횡단보도")
print("서귀포 표준 보행신호", collections.Counter(r["보행자신호등유무"] for r in std).most_common())
print("서귀포 표준 묶음: 15m", clusters(m(std), 15), "30m", clusters(m(std), 30), "/", len(std))

cs = [r for r in cross if "서귀포" in r["시군구명"]]
A, B = m(cs), m(std)
da, _ = cKDTree(B).query(A)
db, _ = cKDTree(A).query(B)
print("서귀포시 안에서: 어린이 횡단보도", len(A), "-> 표준", " ".join(f"{t}m {np.mean(da<=t):.1%}" for t in (10, 20, 30, 50, 100)))
print("서귀포시 안에서: 표준", len(B), "-> 어린이", " ".join(f"{t}m {np.mean(db<=t):.1%}" for t in (10, 20, 30, 50, 100)))
print("서귀포 표준의 동네 분포 상위", collections.Counter((r["소재지지번주소"] or r["소재지도로명주소"]).split(" ")[2] if len((r["소재지지번주소"] or r["소재지도로명주소"]).split(" ")) > 2 else "(주소없음)" for r in std).most_common(8))

st = load("제주_신호기현황")
print("신호기 시", collections.Counter(r["주소"].split(" ")[1] for r in st).most_common())
print("신호기 기하구조", collections.Counter(r["기하구조"] for r in st).most_common())
print("신호기 주소 형식: 도로명처럼 보임", sum(1 for r in st if any(x in r["주소"] for x in ["로 ", "길 "])), "/ 번지만", sum(1 for r in st if r["주소"].split(" ")[-1][:1].isdigit()), "/", len(st))
print("신호기 주소 관리부서", collections.Counter(r["관리부서"] for r in st).most_common(5))

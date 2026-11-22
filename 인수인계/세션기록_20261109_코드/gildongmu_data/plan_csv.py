"""이미 받은 공공데이터 CSV의 항목·좌표·중복을 본다. 읽기 전용."""
import csv
import glob
import io
import math
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\공공데이터포털"


def load(path):
    raw = open(path, "rb").read()
    for enc in ("utf-8-sig", "cp949"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = raw.decode("cp949", "replace")
        enc = "cp949(대체)"
    rows = list(csv.DictReader(io.StringIO(text)))
    return rows, enc


def xy(rows):
    pts = []
    for r in rows:
        la, lo = r.get("위도"), r.get("경도")
        try:
            la, lo = float(la), float(lo)
        except (TypeError, ValueError):
            continue
        if 33.1 < la < 33.6 and 126.1 < lo < 127.0:
            pts.append((la, lo))
    return pts


def meters(pts):
    a = np.array(pts)
    return np.c_[(a[:, 1] - 126.5) * 111320 * math.cos(math.radians(33.4)), (a[:, 0] - 33.4) * 110940]


sets = {}
for p in sorted(glob.glob(os.path.join(ROOT, "*", "*.csv"))):
    name = os.path.basename(p)[:-4]
    rows, enc = load(p)
    cols = list(rows[0].keys()) if rows else []
    pts = xy(rows)
    print("=====", name, "| 행", len(rows), "| 인코딩", enc, "| 제주 범위 안 좌표", len(pts))
    print("  항목:", cols)
    for key in cols:
        if any(k in key for k in ["기준일", "보행자신호", "신호시간", "주소", "횡단보도종류", "구분", "기하구조"]):
            filled = sum(1 for r in rows if (r.get(key) or "").strip())
            vals = sorted({(r.get(key) or "").strip() for r in rows})
            sample = vals[:5] if len(vals) <= 12 else [v for v in vals[::max(1, len(vals) // 3)]][:3]
            print(f"  [{key}] 채움 {filled}/{len(rows)} 값 종류 {len(vals)} 예 {sample}")
    if pts:
        sets[name] = meters(pts)
        t = cKDTree(sets[name])
        for d in (3, 10):
            n = sum(1 for g in t.query_ball_point(sets[name], d) if len(g) > 1)
            print(f"  같은 자료 안에서 {d}m 안에 다른 점이 있는 점 {n}/{len(pts)}")

names = list(sets)
print("===== 자료 간 겹침 (왼쪽 점 중 오른쪽 점이 d m 안에 있는 비율)")
for i, a in enumerate(names):
    for b in names:
        if a == b or "보안등" in a or "보안등" in b or "공원" in a or "공원" in b:
            continue
        d, _ = cKDTree(sets[b]).query(sets[a])
        print(f"  {a} -> {b}: 5m {np.mean(d<=5):.1%} 10m {np.mean(d<=10):.1%} 20m {np.mean(d<=20):.1%} 50m {np.mean(d<=50):.1%}")

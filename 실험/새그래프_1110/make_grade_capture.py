"""입체 후보 위치 목록을 만든다. 사이트에는 영상을 볼 중심 좌표와 줌만 넘기고 도로선은 넘기지 않는다."""
import csv
import json
import os
import sys

from pyproj import Transformer

sys.stdout.reconfigure(encoding="utf-8")
HERE = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\새그래프_1110"
PREV = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\소구역점검_1109\samples.json"
to5179 = Transformer.from_crs(4326, 5179, always_xy=True)
rows = list(csv.DictReader(open(os.path.join(HERE, "입체후보.csv"), encoding="utf-8-sig")))
items = []


def zoom(wh):
    w, h = [float(v) for v in wh.split("x")]
    s = max(w, h)
    return 10 if s > 700 else 12 if s > 120 else 13


for r in rows:
    k = r["종류"]
    if k in ("입체교차부", "인터체인지") or "CRK002" in r["면속성"] or (k == "교량" and int(r["경계3m안쪽분기"]) > 0):
        x, y = to5179.transform(float(r["경도"]), float(r["위도"]))
        pre = {"입체교차부": "G", "인터체인지": "I", "교차로": "C", "교량": "B"}[k]
        name = [p[5:] for p in r["면속성"].split(";") if p.startswith("NAME=")]
        items.append(dict(id=f"{pre}{int(r['레코드']):04d}", x=round(x), y=round(y), z=zoom(r["가로세로m"]), name=name[0] if name else "", kind=k))
s = [v for v in json.load(open(PREV, encoding="utf-8"))["samples"] if v["id"] == "R13"][0]
items.append(dict(id="R0013", x=round(s["x"]), y=round(s["y"]), z=13, name="R13 애조로 교차", kind="표본"))
json.dump(items, open(os.path.join(HERE, "입체위치.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(len(items))
print(json.dumps([[i["id"], i["x"], i["y"], i["z"]] for i in items], separators=(",", ":")))

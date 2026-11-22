"""본 실험 경로 교차 후보(경로교차_본실험.json)를 예비 후보(경로교차_예비.json)와 노드 번호로 맞춘다.
- 예비에서 이미 본 노드: 영상/{예비ID}.jpg를 영상_본실험/{본실험ID}.jpg로 복사하고 예비 판정을 이어 쓴다.
- 새 노드: 캡처 목록(capture_items_본실험.json, [ID, x, y, 13])에 넣는다.
결과: 교차대조_본실험.csv, capture_items_본실험.json   실행: py -I crossing_prep.py
"""
import csv
import json
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
pre = {c["node"]: c for c in json.load(open(os.path.join(HERE, "경로교차_예비.json"), encoding="utf-8"))}
cur = json.load(open(os.path.join(HERE, "경로교차_본실험.json"), encoding="utf-8"))
os.makedirs(os.path.join(HERE, "영상_본실험"), exist_ok=True)
cap, rows = [], []
for c in cur:
    p = pre.get(c["node"])
    if p:
        shutil.copyfile(os.path.join(HERE, "영상", p["id"] + ".jpg"), os.path.join(HERE, "영상_본실험", c["id"] + ".jpg"))
        rows.append([c["id"], p["id"], c["lat"], c["lon"], c["deg"], len(c["routes"]), "예비에서 확인"])
    else:
        cap.append([c["id"], c["x"], c["y"], 13])
        rows.append([c["id"], "", c["lat"], c["lon"], c["deg"], len(c["routes"]), "새로 캡처"])
with open(os.path.join(HERE, "교차대조_본실험.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["본실험ID", "예비ID", "위도", "경도", "차수", "지나는경로수", "처리"])
    w.writerows(rows)
json.dump(cap, open(os.path.join(HERE, "capture_items_본실험.json"), "w", encoding="utf-8"))
print(f"본 실험 후보 {len(cur)}곳: 예비에서 확인 {len(cur) - len(cap)}, 새로 캡처 {len(cap)}")

"""OSM 원본에서 지역별 신호등·횡단보도 점 개수를 비교한다. 읽기 전용."""
import collections
import os
import sys

import osmium

sys.stdout.reconfigure(encoding="utf-8")
SRC = r"C:\Users\seungjun\Documents\claude_code\논문\데이터사이언스학회\05_참고자료\기초자료\osm\south-korea-latest.osm.pbf"
LINK = r"C:\Users\seungjun\AppData\Local\Temp\gildongmu_data\kr2.osm.pbf"
if not os.path.exists(LINK):
    os.link(SRC, LINK)
BOX = {
    "제주(섬 전체)": (33.1, 33.6, 126.1, 127.0),
    "서울": (37.43, 37.70, 126.76, 127.18),
    "부산": (35.05, 35.30, 128.85, 129.25),
    "대전": (36.25, 36.45, 127.28, 127.52),
    "광주": (35.08, 35.25, 126.75, 126.98),
}
count = {k: collections.Counter() for k in BOX}


class H(osmium.SimpleHandler):
    def node(self, n):
        if not n.tags or not n.location.valid():
            return
        h = n.tags.get("highway")
        if h not in ("traffic_signals", "crossing"):
            return
        la, lo = n.location.lat, n.location.lon
        for name, (a, b, c, d) in BOX.items():
            if a < la < b and c < lo < d:
                count[name][h] += 1


H().apply_file(LINK)
os.remove(LINK)
for k, v in count.items():
    print(k, "신호등", v["traffic_signals"], "횡단보도", v["crossing"])

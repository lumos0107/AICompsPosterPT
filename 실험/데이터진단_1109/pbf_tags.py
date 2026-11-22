"""OSM pbf에서 제주의 횡단·편의시설 점 개수를 센다. 읽기 전용."""
import collections
import math
import os
import sys
import time

import osmium

sys.stdout.reconfigure(encoding="utf-8")
SRC = r"C:\Users\seungjun\Documents\claude_code\논문\데이터사이언스학회\05_참고자료\기초자료\osm\south-korea-latest.osm.pbf"
LINK = r"C:\Users\seungjun\AppData\Local\Temp\gildongmu_data\kr.osm.pbf"
print("파일 날짜", time.strftime("%Y-%m-%d", time.localtime(os.path.getmtime(SRC))), "MB", round(os.path.getsize(SRC) / 1048576))
if not os.path.exists(LINK):
    os.link(SRC, LINK)
SCN = [("탑동", 33.515, 126.522), ("도심", 33.499, 126.531), ("연동", 33.489, 126.490), ("이도", 33.499, 126.541)]
COS = math.cos(math.radians(33.45))
total = collections.Counter()
near = {s[0]: collections.Counter() for s in SCN}


class H(osmium.SimpleHandler):
    def node(self, n):
        if not n.tags or not n.location.valid():
            return
        lat, lon = n.location.lat, n.location.lon
        if not (33.1 < lat < 33.6 and 126.1 < lon < 127.0):
            return
        kinds = []
        h, a, s = n.tags.get("highway"), n.tags.get("amenity"), n.tags.get("shop")
        if h == "traffic_signals":
            kinds.append("신호등")
        if h == "crossing":
            kinds.append("횡단보도")
        if a == "toilets":
            kinds.append("화장실")
        if a == "drinking_water":
            kinds.append("음수대")
        if s == "convenience":
            kinds.append("편의점")
        for k in kinds:
            total[k] += 1
            for name, la, lo in SCN:
                if math.hypot((lon - lo) * COS * 111320, (lat - la) * 110940) <= 2000:
                    near[name][k] += 1


H().apply_file(LINK)
print("제주 전체", dict(total))
for k, v in near.items():
    print(k, "반경 2km", dict(v))
os.remove(LINK)

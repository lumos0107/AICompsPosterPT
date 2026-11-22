"""국토지리정보원 지도 정보 이력(도엽 목록)만 받아 제주 1:1000 도엽의 유무와 제작연도를 본다.

목록 파일 한 개만 임시 폴더에 받는다. 지도 자체는 받지 않는다.
포털이 자동등록방지 확인을 요구하면 멈춘다.
"""
import collections
import csv
import io
import json
import os
import re
import sys
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
BASE = "https://www.data.go.kr"
UA = {"User-Agent": "Mozilla/5.0"}
OUT = os.path.join(os.environ["TEMP"], "gildongmu_sheet_index")
os.makedirs(OUT, exist_ok=False)
PK = "15148179"


def post(url, data):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(), headers=UA)
    return urllib.request.urlopen(req, timeout=120).read().decode("utf-8", "replace")


page = urllib.request.urlopen(urllib.request.Request(f"{BASE}/data/{PK}/fileData.do", headers=UA), timeout=90).read().decode("utf-8", "replace")
m = re.search(r"fn_fileDataDown\('(\d+)',\s*'([^']+)',\s*'([^']*)',\s*'(\d+)'", page)
obj = json.loads(post(f"{BASE}/tcs/dss/selectFileDataDownload.do", {"publicDataDetailPk": m.group(2), "publicDataPk": m.group(1), "atchFileId": m.group(3), "fileDetailSn": m.group(4), "publicDataTyCode": "PR0051"}))
a, s = obj["atchFileId"], obj["fileDetailSn"]
name = obj["dataSetFileDetailInfo"]["dataNm"]
if json.loads(post(f"{BASE}/cmm/cmm/check-limit.json", {"atchFileId": a, "fileDetailSn": s})).get("needCaptcha"):
    print("자동등록방지 요구, 멈춤")
    sys.exit(0)
url = f"{BASE}/cmm/cmm/fileDownload.do?" + urllib.parse.urlencode({"atchFileId": a, "fileDetailSn": s, "dataNm": name})
raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300).read()
path = os.path.join(OUT, "sheet_index.csv")
with open(path, "wb") as f:
    f.write(raw)
for enc in ("utf-8-sig", "cp949"):
    try:
        text = raw.decode(enc)
        break
    except UnicodeDecodeError:
        continue
rows = list(csv.DictReader(io.StringIO(text)))
cols = list(rows[0].keys())
print("행", len(rows), "항목", cols)
print("예", rows[0])
key = next((c for c in cols if "도엽번호" in c or "도엽 번호" in c), None)
scale = next((c for c in cols if "축척" in c), None)
year = next((c for c in cols if "제작" in c and "년" in c), None)
nm = next((c for c in cols if "도엽명" in c), None)
print("쓰는 항목", key, scale, year, nm)
if scale:
    print("축척", collections.Counter(r[scale] for r in rows).most_common(8))
jeju = [r for r in rows if (nm and any(w in r[nm] for w in ("제주", "서귀", "한림", "애월", "조천", "구좌", "성산", "표선", "남원", "중문", "대정", "모슬포", "안덕", "우도", "추자")))]
print("제주 관련 도엽명 행", len(jeju))
if scale:
    print("제주 축척별", collections.Counter(r[scale] for r in jeju).most_common(8))
if year and scale:
    c = collections.Counter((r[scale], r[year][:4]) for r in jeju)
    print("제주 축척·제작연도", sorted(c.items())[:40])
if key:
    pre = collections.Counter(r[key][:5] for r in rows if r[key][:3] in ("336", "335", "334", "337"))
    print("도엽번호 앞자리(제주 부근)", pre.most_common(16))
print("표본", [{k: r[k] for k in cols[:7]} for r in jeju[:3]])

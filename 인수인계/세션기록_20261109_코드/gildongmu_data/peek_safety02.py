"""제주 안전데이터분석자료-02의 항목만 임시 폴더에 받아 본다. 프로젝트 폴더에는 저장하지 않는다."""
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
OUT = os.path.join(os.environ["TEMP"], "gildongmu_peek_safety02")
os.makedirs(OUT, exist_ok=True)
PK = "15076628"


def post(url, data):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(), headers=UA)
    return urllib.request.urlopen(req, timeout=120).read().decode("utf-8", "replace")


page = urllib.request.urlopen(urllib.request.Request(f"{BASE}/data/{PK}/fileData.do", headers=UA), timeout=90).read().decode("utf-8", "replace")
m = re.search(r"fn_fileDataDown\('(\d+)',\s*'([^']+)',\s*'([^']*)',\s*'(\d+)'", page)
obj = json.loads(post(f"{BASE}/tcs/dss/selectFileDataDownload.do", {"publicDataDetailPk": m.group(2), "publicDataPk": m.group(1), "atchFileId": m.group(3), "fileDetailSn": m.group(4), "publicDataTyCode": "PR0051"}))
a, s = obj["atchFileId"], obj["fileDetailSn"]
if json.loads(post(f"{BASE}/cmm/cmm/check-limit.json", {"atchFileId": a, "fileDetailSn": s})).get("needCaptcha"):
    print("자동등록방지 요구, 멈춤")
    sys.exit(0)
url = f"{BASE}/cmm/cmm/fileDownload.do?" + urllib.parse.urlencode({"atchFileId": a, "fileDetailSn": s, "dataNm": obj["dataSetFileDetailInfo"]["dataNm"]})
raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=200).read()
for enc in ("utf-8-sig", "cp949"):
    try:
        text = raw.decode(enc)
        break
    except UnicodeDecodeError:
        continue
rows = list(csv.DictReader(io.StringIO(text)))
print("행", len(rows), "항목", list(rows[0].keys()))
print("첫 행", rows[0])
for c in rows[0].keys():
    vals = collections.Counter((r.get(c) or "").strip() for r in rows)
    if len(vals) <= 25:
        print(f" [{c}]", vals.most_common(14))
    else:
        print(f" [{c}] 값 종류 {len(vals)}, 빈 값 {vals.get('', 0)}, 예 {[k for k, _ in vals.most_common(3)]}")

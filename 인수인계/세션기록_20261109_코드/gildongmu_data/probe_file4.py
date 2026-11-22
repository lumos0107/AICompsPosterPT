"""실제 파일 주소를 만드는 함수와 내려받기 응답 형식을 본다. 파일 본문은 받지 않는다."""
import json
import re
import sys
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0"}
BASE = "https://www.data.go.kr"


def get(url, data=None):
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=UA)
    return urllib.request.urlopen(req, timeout=90).read().decode("utf-8", "replace")


page = get(BASE + "/data/15028201/standard.do")
for m in list(re.finditer(r"function\s+fn_fileDataDown\w*\s*\(", page))[:3]:
    print("--- 표준 페이지", page[m.start():m.start() + 1200])

for path in ["/js/biz/cmm/cmm/script_cmmFunction.js", "/js/biz/datset/script_fileDetail.js", "/js/biz/cmm/cmm/script_cmmPopup.js"]:
    js = get(BASE + path)
    for m in list(re.finditer(r"fn_fileDataDownload\s*[=:(]?\s*(?:function)?", js))[:6]:
        ctx = js[m.start():m.start() + 700]
        if "location" in ctx or "fileDownload" in ctx or "action" in ctx or "href" in ctx:
            print("--- ", path)
            print(ctx)
            break

page = get(BASE + "/data/15110599/fileData.do")
m = re.search(r"fn_fileDataDown\('(\d+)',\s*'([^']+)',\s*'([^']*)',\s*'(\d+)'", page)
print("호출 인자", m.groups() if m else None)
if m:
    res = get(BASE + "/tcs/dss/selectFileDataDownload.do", {
        "publicDataDetailPk": m.group(2), "publicDataPk": m.group(1),
        "atchFileId": m.group(3), "fileDetailSn": m.group(4), "publicDataTyCode": "PR0051"})
    try:
        obj = json.loads(res)
        print("상태", obj.get("status"), "atchFileId", obj.get("atchFileId"), "sn", obj.get("fileDetailSn"), "오류", obj.get("error"))
        info = obj.get("dataSetFileDetailInfo") or {}
        print({k: info.get(k) for k in ["dataNm", "publicDataSj", "publicDataTyDetailCode", "orginlFileNm", "fileExtsn", "updtDt"]})
    except Exception as e:
        print("JSON 아님", e, res[:300])

"""파일데이터 페이지의 내려받기 호출 방식과 표준데이터 내려받기 스크립트를 본다. 읽기 전용."""
import re
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0"}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=90).read().decode("utf-8", "replace")


for pk in ["15110599", "15083033"]:
    page = get(f"https://www.data.go.kr/data/{pk}/fileData.do")
    print("=====", pk, len(page))
    for m in list(re.finditer(r"atchFileId|fileDetailSn|fileDownload|fn_fileDataDown|fileDataDown", page))[:14]:
        print("  ", re.sub(r"\s+", " ", page[max(0, m.start() - 90):m.end() + 130]))

js = get("https://www.data.go.kr/js/biz/mvc/std/std-download-manager.js")
print("===== std-download-manager.js", len(js))
print(js[:3500])

page = get("https://www.data.go.kr/data/15028201/standard.do")
for m in list(re.finditer(r"openFileDetailPopup|selectStdDataDetailView|stdExcelDown", page))[:10]:
    print("  ", re.sub(r"\s+", " ", page[max(0, m.start() - 120):m.end() + 260]))

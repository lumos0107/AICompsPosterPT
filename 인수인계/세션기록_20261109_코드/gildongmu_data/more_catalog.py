"""지형도 설명서의 전체 항목과 브이월드·공공데이터포털 목록을 본다. 파일은 받지 않는다."""
import html
import os
import re
import sys
import time
import urllib.parse
import urllib.request

import pdfplumber

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0"}
D = os.path.join(os.path.expanduser("~"), "Downloads")


def get(url):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=90).read().decode("utf-8", "replace")


def clean(s):
    s = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


print("===== 설명서 항목 목록")
with pdfplumber.open(os.path.join(D, "연속수치지형도_데이터_설명서.pdf")) as pdf:
    print("쪽 수", len(pdf.pages))
    for i in range(2, 10):
        for line in (pdf.pages[i].extract_text() or "").splitlines():
            if re.search(r"N[134][APLT]_", line):
                print(i + 1, line[:90])

print("===== 브이월드 목록")
VW = ["횡단보도", "신호등", "가로등", "안전지대", "터널", "해안선", "산책로", "등산로", "둘레길", "숲길", "토지피복", "보행", "표고점", "건물", "공원"]
first = True
for word in VW:
    url = "https://www.vworld.kr/dtmk/dtmk_ntads_s001.do?" + urllib.parse.urlencode({"searchKeyword": word, "pageSize": "20", "pageUnit": "20"})
    try:
        page = get(url)
    except Exception as e:
        print("--", word, "실패", e)
        continue
    if first:
        i = page.find(word, page.find("dtmk_ntads") if "dtmk_ntads" in page else 0)
        m = re.search(r"(onclick|href)=\"[^\"]*(?:s002|detail|Detail)[^\"]*\"", page)
        print("  [구조]", m.group(0)[:200] if m else "링크 형식 못 찾음")
        first = False
    ids = list(dict.fromkeys(re.findall(r"s002\.do\?[^\"']*dsId=(\w+)|fn\w*\('(\d{5,}\w*)'\)|data-dsid=\"(\w+)\"", page)))
    text = clean(page)
    items = re.findall(r"([^>]{4,140}?)\s+(SHP|CSV|GPKG|GeoJSON|GML|TIFF|IMG|XLSX|ZIP)[^가-힣]{0,20}유형\s+(\S+)\s+기관\s+(\S+(?:\s\S+)?)\s+다운로드\s+([\d,]+)", text)
    print("--", word, "| 항목", len(items), "| 번호 후보", [x for t in ids for x in t if x][:10])
    for it in items[:10]:
        print("    ", re.sub(r"^.*-->\s*", "", it[0]).strip()[:90], "|", it[1], "|", it[2], "|", it[3])
    time.sleep(1)

print("===== 공공데이터포털 검색")
WORDS = ["제주 올레", "제주 둘레길", "제주 숲길", "제주 산책로", "제주 가로등", "제주 음수대", "제주 안전비상벨", "제주 CCTV 설치",
         "제주 보행자 교통사고", "제주 교통량", "제주 공공체육시설", "제주 가로수", "제주 횡단보도", "제주 신호등", "제주 교차로",
         "표준노드링크", "보행 네트워크", "두루누비", "걷기길 코스", "보행자사고 다발지역"]
for word in WORDS:
    url = "https://www.data.go.kr/tcs/dss/selectDataSetList.do?" + urllib.parse.urlencode({"keyword": word, "currentPage": "1", "perPage": "20"})
    try:
        page = get(url)
    except Exception as e:
        print("--", word, "실패", e)
        continue
    seen, out = set(), []
    for m in re.finditer(r'href="(/data/(\d+)/(fileData|openapi|standard)\.do)[^"]*"[^>]*>(.*?)</a>', page, flags=re.S):
        pk, kind = m.group(2), m.group(3)
        t = clean(m.group(4))
        if pk in seen or len(t) < 4:
            continue
        seen.add(pk)
        out.append(f"{pk}/{kind}: {t[:62]}")
    n = re.search(r"총\s*<?[^>]*>?\s*([\d,]+)\s*건", page)
    print("--", word, "| 총", n.group(1) if n else "?")
    for o in out[:9]:
        print("    ", o)
    time.sleep(1)

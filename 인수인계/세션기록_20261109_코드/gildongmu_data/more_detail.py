"""추가 후보 자료의 항목·행 수·좌표와 브이월드 번호를 본다. 파일은 받지 않는다."""
import html
import re
import sys
import time
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0"}


def get(url, data=None):
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=UA)
    return urllib.request.urlopen(req, timeout=90).read().decode("utf-8", "replace")


def clean(s):
    s = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


CANDS = [("15096602", "fileData"), ("15076630", "fileData"), ("15129786", "fileData"), ("15075871", "openapi"),
         ("15096889", "fileData"), ("15043496", "fileData"), ("15124792", "fileData"), ("15141659", "fileData"),
         ("15096644", "fileData"), ("15055893", "fileData"), ("15096673", "fileData"), ("15109152", "fileData"),
         ("15158395", "fileData"), ("15025526", "fileData"), ("15105289", "openapi"), ("15029185", "standard"),
         ("15096855", "fileData")]
print("===== 후보 상세")
for pk, kind in CANDS:
    url = f"https://www.data.go.kr/data/{pk}/{kind}.do"
    try:
        page = get(url)
    except Exception as e:
        print("--", pk, "실패", e)
        continue
    title = re.search(r"<title>(.*?)</title>", page, flags=re.S)
    text = clean(page)
    print("--", pk, kind, "|", clean(title.group(1)).replace(" | 공공데이터포털", "")[:60] if title else "")
    d = re.search(r'"description"\s*:\s*"([^"]{10,520})', page)
    if d:
        print("   설명:", d.group(1)[:330])
    vals = []
    for key, pat in [("행", r"전체 행\s*([\d,]+)"), ("수정", r"수정일\s*([\d-]+)"), ("주기", r"업데이트 주기\s*(\S+)"), ("확장자", r"확장자\s*(\S+)")]:
        x = re.search(pat, text)
        if x:
            vals.append(f"{key} {x.group(1)}")
    print("   ", " | ".join(vals), "| 위도", text.count("위도"), "좌표", text.count("좌표"), "경로/GPX", text.count("GPX") + text.count("gpx") + text.count("SHP"), "| 제주", text.count("제주"))
    time.sleep(1)

print("===== 표준데이터·수치지도 검색")
for word in ["CCTV 표준데이터", "안전비상벨 표준데이터", "가로수길 표준데이터", "체육시설 표준데이터", "수치지형도", "수치지도 1:1000", "수치지형도 1/1000", "연속수치지형도"]:
    url = "https://www.data.go.kr/tcs/dss/selectDataSetList.do?" + urllib.parse.urlencode({"keyword": word, "currentPage": "1", "perPage": "20"})
    page = get(url)
    seen, out = set(), []
    for m in re.finditer(r'href="(/data/(\d+)/(fileData|openapi|standard)\.do)[^"]*"[^>]*>(.*?)</a>', page, flags=re.S):
        pk, kind = m.group(2), m.group(3)
        t = clean(m.group(4))
        if pk in seen or len(t) < 4:
            continue
        seen.add(pk)
        out.append(f"{pk}/{kind}: {t[:56]}")
    print("--", word)
    for o in out[:6]:
        print("    ", o)
    time.sleep(1)

print("===== 브이월드 연속수치지형도 번호")
got = {}
for n in range(1, 8):
    url = "https://www.vworld.kr/dtmk/dtmk_ntads_s001.do?" + urllib.parse.urlencode({"searchKeyword": "연속수치지형도", "pageSize": "30", "pageUnit": "30", "pageIndex": str(n)})
    page = get(url)
    marks = list(re.finditer(r"goDetail\('(\w+)',\s*'(\w+)'\)", page))
    before = len(got)
    for a, b in zip(marks, marks[1:] + [None]):
        chunk = clean(page[a.end():b.start() if b else a.end() + 3000])
        t = re.sub(r"^[^가-힣A-Za-z(]+", "", chunk)[:24]
        if a.group(2) not in got and "연속수치지형도" in chunk:
            got[a.group(2)] = t
    if len(got) == before:
        break
    time.sleep(1)
print("모은 항목", len(got))
WANT = ["등고선", "표고점", "교차로", "터널", "안전지대", "도로분리대", "계단", "해안선", "하천중심선", "지류계", "횡단보도", "신호등", "조명"]
for ds, t in got.items():
    if any(w in t for w in WANT):
        page = get(f"https://www.vworld.kr/dtmk/dtmk_ntads_s002.do?dsId={ds}")
        text = clean(page)
        sizes = re.findall(r"([^\s]+\.zip) 용량 ([\d.,]+ [KMG]B)", text)
        up = re.search(r"\.zip 용량 [\d.,]+ [KMG]B 구분 데이터 기준일 - 갱신일 ([\d-]+)", text)
        print("  ", ds, t, "|", [f"{a}={b}" for a, b in sizes][:4], "| 파일", len(sizes), "| 갱신", up.group(1) if up else "?")
        time.sleep(1)

print("===== 해외 공개 자료 존재 확인(머리글만)")
for name, url in [("ESA WorldCover 10m", "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N33E126_Map.tif"),
                  ("Copernicus DEM 30m", "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N33_00_E126_00_DEM/Copernicus_DSM_COG_10_N33_00_E126_00_DEM.tif")]:
    try:
        req = urllib.request.Request(url, headers=UA, method="HEAD")
        r = urllib.request.urlopen(req, timeout=60)
        print(" ", name, r.status, f"{int(r.headers.get('Content-Length', 0)):,}B")
    except Exception as e:
        print(" ", name, "실패", e)

"""제주 안전데이터분석자료 묶음과 ITS API 명세를 본다. 파일은 받지 않는다."""
import html
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0"}
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def get(url, t=40):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=t, context=ctx).read().decode("utf-8", "replace")


def clean(s):
    s = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


p = get("https://www.jejuits.go.kr/open_api/open_apiView.do")
t = clean(p)
print("===== ITS API 명세")
i = p.find("FTY17")
print(clean(p[max(0, i - 900):i + 260])[:900])
j = t.find("x_crdn")
print("--- 좌표 항목:", t[max(0, j - 240):j + 220])
for k in ["좌표계", "WGS", "EPSG", "UTM", "신청", "승인", "인증키", "API KEY", "api_key", "apiKey"]:
    hits = [t[max(0, x.start() - 50):x.end() + 80] for x in list(re.finditer(k, t))[:1]]
    if hits:
        print(f"  [{k}]", hits[0])

print("===== 안전데이터분석자료 묶음")
found = {}
for word in ["제주특별자치도_안전데이터분석자료", "안전데이터분석자료", "제주 안전데이터분석자료 횡단보도", "제주 안전데이터분석자료 신호"]:
    for page_no in (1, 2):
        url = "https://www.data.go.kr/tcs/dss/selectDataSetList.do?" + urllib.parse.urlencode({"keyword": word, "currentPage": str(page_no), "perPage": "40"})
        page = get(url)
        for m in re.finditer(r'href="(/data/(\d+)/(fileData|openapi|standard)\.do)[^"]*"[^>]*>(.*?)</a>', page, flags=re.S):
            t2 = clean(m.group(4))
            if "안전데이터" in t2.replace(" ", ""):
                found.setdefault(m.group(2), (m.group(3), t2))
        time.sleep(0.8)
print("찾은 묶음", len(found))
for pk, (kind, name) in sorted(found.items()):
    page = get(f"https://www.data.go.kr/data/{pk}/{kind}.do")
    text = clean(page)
    d = re.search(r'"description"\s*:\s*"([^"]{10,420})', page)
    r = re.search(r"전체 행\s*([\d,]+)", text)
    u = re.search(r"수정일\s*([\d-]+)", text)
    print("--", pk, name.replace(" ", "")[:58], "| 행", r.group(1) if r else "?", "| 수정", u.group(1) if u else "?", "| 위도", text.count("위도"), "좌표", text.count("좌표"), "횡단", text.count("횡단"), "신호", text.count("신호"))
    print("   ", d.group(1)[:230] if d else "")
    th = re.findall(r"<th[^>]*>\s*([^<]{1,24})\s*</th>", page)
    cols = [x for x in dict.fromkeys(th) if not re.search(r"제공기관|수정일|등록일|파일|분류|관리|전화|비용|이용|매체|키워드|확장자|보유|업데이트|다운로드|데이터", x)]
    if cols:
        print("    표 머리", cols[:24])
    time.sleep(0.8)

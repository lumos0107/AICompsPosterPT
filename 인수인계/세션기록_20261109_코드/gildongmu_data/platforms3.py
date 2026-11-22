"""UTIC 개방데이터 항목과 교통 데이터 오픈마켓 검색 결과를 본다. 파일은 받지 않는다."""
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


print("===== UTIC 개방데이터 항목")
for path in ["newUtisData", "utisRefSig", "utisRefSafe", "utisRefTCS", "newUtisDataWrite"]:
    url = f"https://www.utic.go.kr/guide/{path}.do"
    try:
        q = clean(get(url))
    except Exception as e:
        print("--", path, "실패", repr(e)[:70])
        continue
    i = q.find("교통안전데이터")
    body = q
    for mark in ["개방데이터", "데이터 항목", "제공항목", "항목명"]:
        j = q.find(mark, 400)
        if j > 0:
            body = q[j:]
            break
    print("--", path, len(q), "| 위도", q.count("위도"), "경도", q.count("경도"), "좌표", q.count("좌표"), "X", q.count("XCODE") + q.count("X좌표"), "제주", q.count("제주"), "신호", q.count("신호"), "횡단", q.count("횡단"))
    print("    ", body[:620])
    time.sleep(1)

print("===== 교통 데이터 오픈마켓 검색")
for word in ["횡단보도", "신호등", "신호교차로", "보행", "보도", "제주 횡단", "제주 신호", "제주 보행", "도로 경사", "가로등"]:
    url = "https://www.bigdata-transportation.kr/frn/prdt/search?" + urllib.parse.urlencode({"query": word})
    try:
        p = get(url)
    except Exception as e:
        print("--", word, "실패", repr(e)[:70])
        continue
    n = re.search(r"총\s*(?:<[^>]+>\s*)*([\d,]+)\s*(?:<[^>]+>\s*)*건", p)
    titles = []
    for m in re.finditer(r'href="(/frn/prdt/detail\?[^"]*)"[^>]*>(.*?)</a>', p, flags=re.S):
        t = clean(m.group(2))
        if 4 <= len(t) <= 90 and t not in titles:
            titles.append(t)
    if not titles:
        titles = [clean(x)[:70] for x in re.findall(r'class="[^"]*(?:tit|title|name)[^"]*"[^>]*>(.*?)</', p, flags=re.S)]
        titles = [t for t in dict.fromkeys(titles) if len(t) >= 4][:12]
    print("--", word, "| 총", n.group(1) if n else "?", "| 길이", len(p), "|", titles[:9])
    time.sleep(1)

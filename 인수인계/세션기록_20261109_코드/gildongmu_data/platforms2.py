"""교통 오픈마켓, UTIC, EGIS, TAAS 개방, 비짓제주에서 쓸 만한 항목을 찾는다. 파일은 받지 않는다."""
import html
import re
import ssl
import sys
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


print("===== 교통 데이터 오픈마켓")
p = get("https://www.bigdata-transportation.kr")
for m in list(re.finditer(r'<form[^>]*>', p))[:5]:
    print("  폼", m.group(0)[:150])
print("  입력", re.findall(r'<input[^>]*name="([^"]+)"', p)[:15])
print("  링크", list(dict.fromkeys(re.findall(r'href="(/[^"]*(?:prdt|product|goods|data|search)[^"]*)"', p)))[:14])
for url in ["https://www.bigdata-transportation.kr/frn/prdt/searchPrdtList?searchKeyword=%ED%9A%A1%EB%8B%A8%EB%B3%B4%EB%8F%84",
            "https://www.bigdata-transportation.kr/frn/search/searchList?query=%ED%9A%A1%EB%8B%A8%EB%B3%B4%EB%8F%84"]:
    try:
        q = get(url)
        print("  시도", url[-60:], len(q), clean(q)[:120])
    except Exception as e:
        print("  실패", url[-50:], repr(e)[:70])

print("===== UTIC")
p = get("https://www.utic.go.kr")
t = clean(p)
for k in ["오픈", "Open", "신호", "횡단", "교통안전시설", "CCTV"]:
    print(f"  [{k}]", t.count(k))
print("  링크", [x for x in dict.fromkeys(re.findall(r'href="([^"#]*(?:guide|open|api|Open)[^"]*)"', p))][:12])
for u in ["https://www.utic.go.kr/guide/newUtisData.do", "https://www.utic.go.kr/guide/utisData.do", "https://www.utic.go.kr/guide/cctvOpenData.do", "https://www.utic.go.kr/guide/imsOpenData.do"]:
    try:
        q = clean(get(u))
        print("  ", u[-26:], len(q), "| 신호", q.count("신호"), "횡단", q.count("횡단"), "|", q[:110])
    except Exception as e:
        print("  ", u[-26:], "실패", repr(e)[:60])

print("===== EGIS 토지피복")
p = get("https://egis.me.go.kr")
print("  링크", [x for x in dict.fromkeys(re.findall(r'href="([^"#]*(?:land|req|intro)[^"]*)"', p))][:14])
for u in ["https://egis.me.go.kr/intro/land.do", "https://egis.me.go.kr/req/intro.do"]:
    try:
        q = clean(get(u))
        print("  ", u[-20:], len(q), q[:500])
        for k in ["세분류", "1m", "1 m", "신청", "로그인", "SHP", "제주"]:
            hits = [q[max(0, x.start() - 30):x.end() + 50] for x in list(re.finditer(k, q))[:1]]
            if hits:
                print(f"    [{k}]", hits[0])
    except Exception as e:
        print("  ", u[-20:], "실패", repr(e)[:60])

print("===== TAAS 개방 API")
p = clean(get("https://opendata.koroad.or.kr/api/sample.do"))
for k in ["보행자", "다발지역", "위도", "인증키", "로그인"]:
    hits = [p[max(0, x.start() - 40):x.end() + 70] for x in list(re.finditer(k, p))[:2]]
    print(f"  [{k}]", hits)

print("===== 비짓제주 API")
p = get("https://www.visitjeju.net")
print("  API 언급", len(re.findall(r"openapi|open api|API", p, flags=re.I)))
try:
    q = clean(get("https://api.visitjeju.net/guide/overview.do"))
    print("  개발자 페이지", len(q), q[:300])
except Exception as e:
    print("  개발자 페이지 실패", repr(e)[:70])

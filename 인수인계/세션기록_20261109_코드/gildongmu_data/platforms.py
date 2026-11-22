"""브이월드 내려받기 조건과 다른 데이터 플랫폼의 접속 여부를 본다. 파일은 받지 않는다."""
import html
import re
import ssl
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0"}
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def get(url, t=25):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=t, context=ctx).read().decode("utf-8", "replace")


page = get("https://www.vworld.kr/dtmk/dtmk_ntads_s002.do?dsId=30182", 60)
i = page.find("download : function(dsId, fileNo, fileSize)")
print("===== 브이월드 내려받기 함수")
print(re.sub(r"\s+", " ", page[i:i + 1300]))
j = page.find("multiDownload : function")
print("===== 여러 파일 받기")
print(re.sub(r"\s+", " ", page[j:j + 700]))

print("===== 플랫폼 접속")
SITES = [
    ("통합데이터지도", "https://www.bigdata-map.kr"),
    ("교통 빅데이터", "https://www.bigdata-transportation.kr"),
    ("산림 빅데이터", "https://www.bigdata-forest.kr"),
    ("환경 빅데이터", "https://www.bigdata-environment.kr"),
    ("문화 빅데이터", "https://www.bigdata-culture.kr"),
    ("환경공간정보 EGIS", "https://egis.me.go.kr"),
    ("산림공간정보 FGIS", "https://fgis.forest.go.kr"),
    ("국가교통DB", "https://www.ktdb.go.kr"),
    ("국가교통정보센터", "https://www.its.go.kr"),
    ("경찰청 UTIC", "https://www.utic.go.kr"),
    ("제주 교통정보센터", "https://www.jejuits.go.kr"),
    ("TAAS 개방", "https://opendata.koroad.or.kr"),
    ("국가공간정보포털", "https://www.nsdi.go.kr"),
    ("한국데이터거래소", "https://kdx.kr"),
    ("비짓제주", "https://www.visitjeju.net"),
]
for name, url in SITES:
    try:
        p = get(url)
        t = re.search(r"<title[^>]*>(.*?)</title>", p, flags=re.S | re.I)
        print(f"  되는 곳 {name}: {html.unescape(t.group(1)).strip()[:40] if t else '(제목 없음)'} | 길이 {len(p):,}")
    except Exception as e:
        print(f"  안 되는 곳 {name}: {repr(e)[:70]}")

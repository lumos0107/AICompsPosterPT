"""제주 ITS 교통시설물 API의 안내와 정밀도로지도 포털 정보를 본다. 파일은 받지 않는다."""
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


found = {}
for word in ["제주 교통시설물", "제주특별자치도_교통시설물", "교통시설물정보 제주", "정밀도로지도", "제주 교통정보센터"]:
    url = "https://www.data.go.kr/tcs/dss/selectDataSetList.do?" + urllib.parse.urlencode({"keyword": word, "currentPage": "1", "perPage": "20"})
    page = get(url)
    for m in re.finditer(r'href="(/data/(\d+)/(fileData|openapi|standard)\.do)[^"]*"[^>]*>(.*?)</a>', page, flags=re.S):
        t = clean(m.group(4))
        if len(t) >= 4:
            found.setdefault(m.group(2), (m.group(3), t))
    time.sleep(1)
print("===== 포털 후보")
for pk, (kind, t) in found.items():
    if re.search(r"시설물|정밀도로|교통정보|신호", t.replace(" ", "")):
        print(" ", pk, kind, t[:60])

targets = [pk for pk, (k, t) in found.items() if re.search(r"시설물|정밀도로", t.replace(" ", ""))][:6]
for pk in targets:
    kind = found[pk][0]
    url = f"https://www.data.go.kr/data/{pk}/{kind}.do"
    page = get(url)
    t = re.search(r"<title>(.*?)</title>", page, flags=re.S)
    text = clean(page)
    d = re.search(r'"description"\s*:\s*"([^"]{10,620})', page)
    print("--", pk, kind, clean(t.group(1))[:66] if t else "")
    print("   설명:", d.group(1)[:420] if d else "")
    vals = []
    for key, pat in [("수정", r"수정일\s*([\d-]+)"), ("주기", r"업데이트 주기\s*(\S+)"), ("심의", r"심의유형\s*(\S+)"), ("확장자", r"확장자\s*(\S+)"), ("트래픽", r"(?:개발계정|운영계정)[^가-힣]*(\S+\s?\S*)")]:
        x = re.search(pat, text)
        if x:
            vals.append(f"{key} {x.group(1)}")
    print("   ", " | ".join(vals), "| FTY17", page.count("FTY17"), "| x_crdn", page.count("x_crdn"), "| 신호제어기", text.count("신호제어기"), "| 제주", text.count("제주"))
    for k in ["신호제어기", "x_crdn", "자동승인", "심의"]:
        for x in list(re.finditer(k, text))[:1]:
            print(f"    [{k}]", text[max(0, x.start() - 60):x.end() + 90])
    time.sleep(1)

print("===== 제주 교통정보센터 API 안내")
for url in ["https://www.jejuits.go.kr", "https://www.jejuits.go.kr/open_api/open_apiView.do", "https://www.jejuits.go.kr/jido/openApi/openApiIntro.do"]:
    try:
        p = get(url)
        text = clean(p)
        print("--", url, len(p), text[:160])
        print("   FTY17", p.count("FTY17"), "| x_crdn", p.count("x_crdn"), "| 시설물", text.count("시설물"), "| 링크", list(dict.fromkeys(re.findall(r'(?:href|location\.href)=["\']([^"\']*(?:api|Api|API)[^"\']*)', p)))[:12])
    except Exception as e:
        print("--", url, "실패", repr(e)[:80])

"""브이월드·공공데이터포털 페이지의 제공 형태만 읽는다. 파일은 받지 않는다."""
import html
import re
import sys
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0"}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=90).read().decode("utf-8", "replace")


def clean(s):
    s = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


VW = {"도로중심선": "30182", "인도": "30221", "입체교차부": "30223", "육교": "30220", "교량": "30168",
      "자전거도로중심선": "20250121DS00008", "보도중심선": "20250121DS00019"}
for name, ds in VW.items():
    url = f"https://www.vworld.kr/dtmk/dtmk_ntads_s002.do?dsId={ds}"
    try:
        page = get(url)
    except Exception as e:
        print("=====", name, "실패", e)
        continue
    text = clean(page)
    print("=====", name, ds, len(page))
    for key in ["최종 수정", "수정일", "갱신", "데이터 형식", "제공 형식", "좌표계", "로그인", "라이선스", "이용조건"]:
        for x in list(re.finditer(key, text))[:1]:
            print(f"  [{key}]", text[max(0, x.start() - 30):x.end() + 70])
    files = re.findall(r"[^\s<>\"']+\.(?:zip|z\d\d|shp|gpkg)\b", text)
    print("  파일 이름", len(files), sorted(set(files))[:16])
    print("  제주 언급", text.count("제주"))

PORTAL = {"공중화장실표준": "https://www.data.go.kr/data/15012892/standard.do",
          "상가정보": "https://www.data.go.kr/data/15083033/fileData.do"}
for name, url in PORTAL.items():
    page = get(url)
    text = clean(page)
    print("=====", name, len(page))
    for key in ["제공기관 수", "전체 행", "수정일", "업데이트 주기", "확장자", "이용허락범위", "위도", "좌표", "제주"]:
        for x in list(re.finditer(key, text))[:2]:
            print(f"  [{key}]", text[max(0, x.start() - 60):x.end() + 110])

for word in ["제주시 횡단보도", "제주시 공중화장실", "제주특별자치도 공중화장실", "제주 횡단보도"]:
    url = "https://www.data.go.kr/tcs/dss/selectDataSetList.do?" + urllib.parse.urlencode({"keyword": word, "perPage": "10"})
    page = get(url)
    titles = re.findall(r'<span class="title">\s*(.*?)\s*</span>', page, flags=re.S)
    links = re.findall(r'href="(/data/\d+/(?:fileData|openapi|standard)\.do)', page)
    print("===== 검색", word, "| 제목", [clean(t)[:48] for t in titles][:10])
    print("   주소", links[:10])

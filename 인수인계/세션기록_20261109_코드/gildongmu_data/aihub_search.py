"""AI Hub 데이터 목록을 키워드로 검색한다. 파일은 받지 않는다."""
import html
import re
import sys
import time
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


WORDS = ["횡단보도", "신호등", "보행", "인도", "도로 시설", "러닝", "달리기", "걷기", "경로", "GPS", "궤적", "토지피복", "항공", "위성", "제주", "가로수", "노면", "거리뷰"]
first = True
for word in WORDS:
    url = "https://www.aihub.or.kr/aihubdata/data/list.do?" + urllib.parse.urlencode({"pageIndex": "1", "currMenu": "115", "topMenu": "100", "dataSetSn": "", "srchOrder": "ORDER_DATE_DESC", "srchPagePer": "20", "srchDataRealmCode": "", "searchKeyword": word})
    try:
        page = get(url)
    except Exception as e:
        print("--", word, "실패", e)
        continue
    if first:
        print("페이지 길이", len(page))
        m = re.search(r"dataSetSn=(\d+)|fncDetail\('?(\d+)|data-sn=\"(\d+)\"", page)
        print("구조", m.group(0) if m else "번호 형식 못 찾음")
        first = False
    n = re.search(r"총\s*<?[^>]*>?\s*([\d,]+)\s*건|검색결과\D{0,20}([\d,]+)", page)
    seen, out = set(), []
    for m in re.finditer(r"<h3[^>]*>(.*?)</h3>|class=\"tit[^\"]*\"[^>]*>(.*?)</", page, flags=re.S):
        t = clean(m.group(1) or m.group(2))
        if 4 <= len(t) <= 80 and t not in seen:
            seen.add(t)
            out.append(t)
    print("--", word, "| 총", (n.group(1) or n.group(2)) if n else "?", "|", out[:12])
    time.sleep(1)

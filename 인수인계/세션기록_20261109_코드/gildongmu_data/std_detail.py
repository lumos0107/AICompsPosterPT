"""남은 제공기관 1건과 서귀포·대전 파일의 항목·행 수를 본다. 읽기 전용."""
import html
import re
import sys
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0"}
LIST = "https://www.data.go.kr/data/{}/standard.do"


def get(url, data=None):
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=UA)
    return urllib.request.urlopen(req, timeout=90).read().decode("utf-8", "replace")


def rows(page):
    part = page[page.find("데이터 목록 (제공기관 수"):]
    return [r for r in re.findall(r"<tr[^>]*>(.*?)</tr>", part, flags=re.S) if "파일데이터" in r or "fileData" in r]


def clean(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


print("== 신호등 16쪽")
for r in rows(get(LIST.format("15028198"), {"pageIndex": "16", "publicDataPk": "15028198", "searchKeyword2": ""})):
    print("  ", clean(r)[:120])

TARGETS = [("15028201", "서귀포시"), ("15028201", "대전광역시"), ("15028198", "대전광역시")]
for pk, word in TARGETS:
    print("=====", pk, word)
    found = None
    for n in range(1, 18):
        rs = rows(get(LIST.format(pk), {"pageIndex": str(n), "publicDataPk": pk, "searchKeyword2": ""}))
        if not rs:
            break
        for r in rs:
            if word in clean(r):
                found = r
                break
        if found:
            break
    if not found:
        print("  목록에서 못 찾음")
        continue
    print("  행:", clean(found)[:120])
    m = re.search(r"/data/(\d+)/fileData\.do", found) or re.search(r"(\d{8})", found)
    if not m:
        print("  링크 없음:", found[:400])
        continue
    fid = m.group(1)
    url = f"https://www.data.go.kr/data/{fid}/fileData.do"
    print("  주소:", url)
    page = get(url)
    text = re.sub(r"\s+", " ", clean(re.sub(r"<script.*?</script>|<style.*?</style>", " ", page, flags=re.S)))
    for key in ["전체 행", "수정일", "업데이트 주기", "위도", "경도", "보행자신호등", "신호시간"]:
        for x in list(re.finditer(key, text))[:1]:
            print(f"  [{key}]", text[max(0, x.start() - 30):x.end() + 70])
    d = re.search(r'"description"\s*:\s*"([^"]{10,500})', page)
    if d:
        print("  설명:", d.group(1)[:400])

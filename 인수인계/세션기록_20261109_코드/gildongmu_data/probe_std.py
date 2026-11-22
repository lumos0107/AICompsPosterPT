"""표준데이터 페이지에서 일괄 내려받기 경로와 제공기관 목록 구조를 찾는다. 읽기 전용."""
import re
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
PAT = r"[^\s\"'<>()]*(?:fileDownload|[Dd]ownload|atchFileId|\.csv|\.zip|selectStdData|Excel)[^\s\"'<>()]*"
for pk in ["15028198", "15028201"]:
    url = f"https://www.data.go.kr/data/{pk}/standard.do"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        page = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
    except Exception as e:
        print(pk, "실패", e)
        continue
    print("=====", pk, len(page))
    seen = set()
    for m in re.finditer(PAT, page):
        s = m.group(0)[:200]
        if s not in seen:
            seen.add(s)
            print("  링크:", s)
    for m in re.finditer(r"function\s+(\w*(?:[Dd]own|[Ee]xcel|[Ff]ile)\w*)\s*\([^)]*\)\s*\{(.{0,500})", page, flags=re.S):
        print("  함수:", m.group(1), "::", re.sub(r"\s+", " ", m.group(2))[:500])
    for key in ["제공기관", "전체 건수", "건수", "데이터 수", "전국통합"]:
        for x in list(re.finditer(key, page))[:2]:
            t = re.sub(r"<[^>]+>", " ", page[max(0, x.start() - 80):x.end() + 120])
            print(f"  [{key}]", re.sub(r"\s+", " ", t))

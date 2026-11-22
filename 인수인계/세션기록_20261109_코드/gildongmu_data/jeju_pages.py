"""제주 신호기·횡단보도 자료 페이지의 설명과 항목을 본다. 읽기 전용."""
import html
import re
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
for pk in ["15083015", "15110599", "15076542", "15076538"]:
    url = f"https://www.data.go.kr/data/{pk}/fileData.do"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        page = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
    except Exception as e:
        print(pk, "실패", e)
        continue
    text = html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>|<style.*?</style>", " ", page, flags=re.S)))
    text = re.sub(r"\s+", " ", text)
    print("=====", pk, len(page))
    m = re.search(r'"description"\s*:\s*"([^"]{10,600})', page)
    if m:
        print("설명:", m.group(1)[:500])
    m = re.search(r'"keywords"\s*:\s*\[?"?([^\]"]{3,200})', page)
    if m:
        print("키워드:", m.group(1))
    for key in ["위도", "경도", "좌표", "전체 행", "행 수", "데이터 건수", "관리부서", "업데이트 주기", "이용허락범위", "다운로드"]:
        hits = [text[max(0, x.start() - 40):x.end() + 60] for x in re.finditer(key, text)][:2]
        for h in hits:
            print(f"[{key}] {h}")

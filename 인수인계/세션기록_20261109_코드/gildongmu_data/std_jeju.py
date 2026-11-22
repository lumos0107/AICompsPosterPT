"""표준데이터 제공기관 목록에 제주가 있는지 본다. 읽기 전용."""
import re
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
NAMES = {"15028198": "신호등", "15028201": "횡단보도"}
for pk, name in NAMES.items():
    url = f"https://www.data.go.kr/data/{pk}/standard.do"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        page = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
    except Exception as e:
        print(pk, "실패", e)
        continue
    start = page.find("데이터 목록 (제공기관 수")
    part = page[start:]
    print("=====", name, "목록 시작", start, "목록 길이", len(part))
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", part, flags=re.S)
    print("표 행 수", len(rows))
    texts = []
    for r in rows:
        t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", r)).strip()
        if t:
            texts.append(t)
    for t in texts[:3]:
        print("  예:", t[:160])
    hit = [t for t in texts if "제주" in t or "서귀포" in t]
    print("제주·서귀포가 든 행", len(hit))
    for t in hit[:10]:
        print("  ", t[:200])
    print("페이지 전체에서 '제주' 등장", page.count("제주"), "/ 목록 뒤쪽", part.count("제주"))
    for x in list(re.finditer("제주", part))[:6]:
        print("   문맥:", re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", part[max(0, x.start() - 60):x.end() + 60])))
    pages = re.findall(r"fn_\w*[Pp]age\w*\((\d+)\)|goPage\((\d+)\)|page=(\d+)", part)
    print("쪽 넘김 흔적", len(pages), pages[:8])

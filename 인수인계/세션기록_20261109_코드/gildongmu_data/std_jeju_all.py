"""표준데이터 제공기관 목록을 모든 쪽에 걸쳐 모아 제주 포함 여부를 본다. 읽기 전용."""
import collections
import re
import sys
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0"}
NAMES = {"15028198": ("신호등", 76), "15028201": ("횡단보도", 55)}


def get(url, data=None):
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=UA)
    return urllib.request.urlopen(req, timeout=90).read().decode("utf-8", "replace")


def providers(page):
    part = page[page.find("데이터 목록 (제공기관 수"):]
    out = []
    for r in re.findall(r"<tr[^>]*>(.*?)</tr>", part, flags=re.S):
        t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", r)).strip()
        if t.startswith("파일데이터") or t.startswith("오픈 API") or t.startswith("OpenAPI"):
            out.append(t)
    return out


for pk, (name, total) in NAMES.items():
    url = f"https://www.data.go.kr/data/{pk}/standard.do"
    first = get(url)
    form = re.search(r'<form id="standDataVO".*?</form>', first, flags=re.S)
    inputs = {}
    if form:
        for tag in re.findall(r"<input[^>]*>", form.group(0)):
            n = re.search(r'name="([^"]+)"', tag)
            v = re.search(r'value="([^"]*)"', tag)
            if n:
                inputs[n.group(1)] = v.group(1) if v else ""
    print("=====", name, "폼 항목", list(inputs))
    part = first[first.find("데이터 목록 (제공기관 수"):]
    onclick = re.findall(r'onclick="([^"]*(?:[Pp]age|Link)[^"]*)"', part)[:4]
    print("쪽 넘김 호출", onclick)
    func = re.search(r"function\s+(\w+)\s*\(\s*\w*\s*\)\s*\{[^}]*(?:pageIndex|currentPage|curPage)[^}]*\}", first)
    if func:
        print("함수", re.sub(r"\s+", " ", func.group(0))[:300])

    p1 = providers(first)
    print("1쪽 행 수", len(p1))
    keys = [k for k in inputs if "page" in k.lower()] or ["currentPage", "pageIndex", "page"]
    all_rows = list(p1)
    used = None
    for key in keys:
        data = dict(inputs)
        data[key] = "2"
        try:
            p2 = providers(get(url, data))
        except Exception as e:
            print("  시도 실패", key, e)
            continue
        print("  시도", key, "2쪽 첫 행:", p2[0][:80] if p2 else "(없음)")
        if p2 and p2[0] != p1[0]:
            used = key
            break
    if not used:
        print("쪽 넘김 방법을 못 찾음")
        continue
    n = 1
    while len(set(all_rows)) < total and n < 15:
        n += 1
        data = dict(inputs)
        data[used] = str(n)
        rows = providers(get(url, data))
        if not rows:
            break
        all_rows.extend(rows)
    uniq = sorted(set(all_rows))
    print("모은 제공기관 행", len(uniq), "/ 안내된 총", total, "쪽 수", n)
    hit = [t for t in uniq if "제주" in t or "서귀포" in t]
    print("제주·서귀포:", hit if hit else "없음")
    c = collections.Counter()
    for t in uniq:
        m = re.search(r"(?:파일데이터|오픈 API|OpenAPI)\s+([^_\s]+)_", t)
        c[m.group(1) if m else "기타"] += 1
    print("시도별 제공기관 수", c.most_common())
    for t in uniq:
        if any(k in t for k in ["대전", "대구", "서울특별시 "]) and "구" in t:
            print("   ", t[:90])

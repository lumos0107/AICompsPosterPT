"""브이월드 번호, 수치지도 도엽 정보, 표준데이터의 제주 포함, 도로 속성 채움을 본다. 파일은 받지 않는다."""
import glob
import html
import os
import re
import struct
import sys
import time
import urllib.parse
import urllib.request
import collections

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0"}


def get(url, data=None):
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=UA)
    return urllib.request.urlopen(req, timeout=90).read().decode("utf-8", "replace")


def clean(s):
    s = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


print("===== 브이월드 번호")
for word in ["등고선", "표고점", "교차로", "터널", "해안선", "도로분리대", "계단", "하천중심선", "도시계획정보_보행자전용도로"]:
    url = "https://www.vworld.kr/dtmk/dtmk_ntads_s001.do?" + urllib.parse.urlencode({"searchKeyword": word, "pageSize": "20", "pageUnit": "20"})
    page = get(url)
    marks = list(re.finditer(r"goDetail\('(\w+)',\s*'(\w+)'\)", page))
    seen = set()
    for a, b in zip(marks, marks[1:] + [None]):
        if a.group(2) in seen:
            continue
        seen.add(a.group(2))
        chunk = clean(page[a.end() + 2:b.start() if b else a.end() + 2500])
        if word[:2] not in chunk[:60]:
            continue
        ds = a.group(2)
        pg = clean(get(f"https://www.vworld.kr/dtmk/dtmk_ntads_s002.do?dsId={ds}"))
        sizes = re.findall(r"([^\s]+\.zip) 용량 ([\d.,]+ [KMG]B)", pg)
        up = re.search(r"\.zip 용량 [\d.,]+ [KMG]B 구분 데이터 기준일 - 갱신일 ([\d-]+)", pg)
        print(f"  [{word}] {a.group(1)} {ds} | {chunk[:42]} | 파일 {len(sizes)} {[s[1] for s in sizes][:8]} | 갱신 {up.group(1) if up else '?'}")
        time.sleep(1)
    time.sleep(1)

print("===== 수치지도 도엽 정보")
for pk in ["15067685", "15148179", "15125058", "15059721"]:
    page = get(f"https://www.data.go.kr/data/{pk}/fileData.do")
    t = re.search(r"<title>(.*?)</title>", page, flags=re.S)
    d = re.search(r'"description"\s*:\s*"([^"]{10,520})', page)
    text = clean(page)
    r = re.search(r"전체 행\s*([\d,]+)", text)
    u = re.search(r"수정일\s*([\d-]+)", text)
    print("--", pk, clean(t.group(1))[:60] if t else "", "| 행", r.group(1) if r else "?", "| 수정", u.group(1) if u else "?")
    print("   ", d.group(1)[:380] if d else "")
    time.sleep(1)

print("===== 표준데이터의 제주")
for name, pk in [("안전비상벨", "15028206"), ("가로수길", "15021145"), ("CCTV", "15013094")]:
    try:
        page = get(f"https://www.data.go.kr/data/{pk}/standard.do", {"pageIndex": "1", "publicDataPk": pk, "searchKeyword2": "제주"})
    except Exception as e:
        print("--", name, "실패", e)
        continue
    t = re.search(r"<title>(.*?)</title>", page, flags=re.S)
    part = page[page.find("데이터 목록 (제공기관 수"):]
    rows = re.findall(r'data-public-pk="([^"]+)".*?</span>\s*([^<]+?)\s*</a>', part, flags=re.S)
    print("--", name, clean(t.group(1))[:40] if t else "", "| 제주 검색 결과", [r[1] for r in rows][:6])
    for pkk, nm in rows[:4]:
        if "제주" not in nm and "서귀포" not in nm:
            continue
        pop = clean(re.sub(r"<script.*?</script>", " ", get("https://www.data.go.kr/tcs/dss/selectDpkDetailInfo.do", {"publicDataDetailPk": pkk}), flags=re.S))
        r = re.search(r"전체 행 수\s*([\d,]+)", pop)
        u = re.search(r"수정일\s*([\d-]+)", pop)
        print("    ", nm, "| 행", r.group(1) if r else "?", "| 수정", u.group(1) if u else "?")
        time.sleep(1)
    time.sleep(1)

print("===== 도로중심선 속성 채움 (5월 사본)")
D = os.path.join(os.path.expanduser("~"), "Downloads")
p = glob.glob(os.path.join(D, "(연속수치지형도)도로중심선_제주", "**", "N3L_A0020000_50.dbf"), recursive=True)[0]
with open(p, "rb") as f:
    head = f.read(32)
    n = struct.unpack("<I", head[4:8])[0]
    hlen, rlen = struct.unpack("<2H", head[8:12])
    fields, off = [], 1
    while True:
        c = f.read(32)
        if c[0] == 13:
            break
        fields.append((c[:11].split(b"\0")[0].decode("cp949", "replace"), off, c[16]))
        off += c[16]
    f.seek(hlen)
    cnt = {nm: collections.Counter() for nm, _, _ in fields if nm in ("RDLN", "RVWD", "RDNM", "NAME", "RDNU", "FMTA")}
    for _ in range(n):
        r = f.read(rlen)
        for nm, o, l in fields:
            if nm in cnt:
                cnt[nm][r[o:o + l].decode("cp949", "replace").strip()] += 1
for nm, c in cnt.items():
    empty = c.get("", 0) + c.get("0", 0) + c.get("0.00", 0) + c.get("0.0", 0)
    print(f" {nm}: 비었거나 0인 행 {empty/n:.1%}, 값 종류 {len(c)}, 상위 {c.most_common(6)}")

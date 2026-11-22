"""DEM 해상도, 선 자료의 동일성, 코드표, 남은 출처를 본다. 파일은 새로 받지 않는다."""
import glob
import html
import os
import re
import struct
import sys
import urllib.parse
import urllib.request
import zipfile

import numpy as np
import pdfplumber

sys.stdout.reconfigure(encoding="utf-8")
D = os.path.join(os.path.expanduser("~"), "Downloads")
UA = {"User-Agent": "Mozilla/5.0"}

print("===== 공개 DEM")
p = os.path.join(D, "(B080)공개DEM_33607_img_2025.zip")
b = zipfile.ZipFile(p).read("33607/33607.img")
hp = struct.unpack("<I", b[16:20])[0]
root = struct.unpack("<I", b[hp + 8:hp + 12])[0]


def walk(ptr, depth=0):
    while ptr:
        nxt, _, _, child, data, size = struct.unpack("<6I", b[ptr:ptr + 24])
        name = b[ptr + 24:ptr + 88].split(b"\0")[0].decode("latin1")
        typ = b[ptr + 88:ptr + 120].split(b"\0")[0].decode("latin1")
        if typ == "Eimg_Layer":
            w, h = struct.unpack("<II", b[data:data + 8])
            lt, pt = struct.unpack("<HH", b[data + 8:data + 12])
            print(" 층", name, "가로", w, "세로", h, "자료형 코드", pt)
        if typ == "Eprj_MapInfo":
            n = struct.unpack("<I", b[data:data + 4])[0]
            q = data + 8 + n
            pro = b[data + 8:data + 8 + n].split(b"\0")[0].decode("latin1")
            ul = struct.unpack("<2d", b[q + 8:q + 24])
            q += 24
            lr = struct.unpack("<2d", b[q + 8:q + 24])
            q += 24
            ps = struct.unpack("<2d", b[q + 8:q + 24])
            print(" 지도정보", pro, "좌상", ul, "우하", lr, "격자 크기", ps)
        if child:
            walk(child, depth + 1)
        ptr = nxt


walk(root)

print("===== 인도와 자전거·보도 파일의 꼭짓점 일치")
X0, Y0, X1, Y1 = 873000, 1458000, 952000, 1559000


def verts(path):
    data = open(path, "rb").read()
    pos, out = 100, []
    while pos < len(data):
        _, clen = struct.unpack(">2i", data[pos:pos + 8])
        s = pos + 8
        if struct.unpack("<i", data[s:s + 4])[0] != 0:
            x0, y0, x1, y1 = struct.unpack("<4d", data[s + 4:s + 36])
            if x1 >= X0 and x0 <= X1 and y1 >= Y0 and y0 <= Y1:
                np_, npts = struct.unpack("<2i", data[s + 36:s + 44])
                out.append(np.frombuffer(data, "<f8", npts * 2, s + 44 + 4 * np_).reshape(-1, 2).copy())
        pos = s + clen * 2
    return np.vstack(out)


def key(a, r):
    return set(map(tuple, np.round(a / r).astype(np.int64)))


sw = verts(glob.glob(os.path.join(D, "N3L_A0033320", "**", "N3L_A0033320.shp"), recursive=True)[0])
for name, folder, fn in [("자전거도로", "국가기본도_자전거도로중심선", "TN_BCYCL_CTLN.shp"), ("보도중심선", "국가기본도_보도중심선", "TN_FTPTH_CTLN.shp")]:
    a = verts(glob.glob(os.path.join(D, folder, "**", fn), recursive=True)[0])
    for r in (0.01, 0.5):
        s = key(sw, r)
        hit = np.mean([tuple(x) in s for x in np.round(a / r).astype(np.int64)])
        print(f" {name} 꼭짓점 {len(a):,}개 중 인도 꼭짓점과 {r}m 격자에서 같은 것 {hit:.1%}")

print("===== 설명서 코드")
with pdfplumber.open(os.path.join(D, "연속수치지형도_데이터_설명서.pdf")) as pdf:
    seen = set()
    for i, page in enumerate(pdf.pages, 1):
        for line in (page.extract_text() or "").splitlines():
            if re.search(r"A00232|A00233|A0090|A0063|A0070|F00[12]0|등고|표고", line) and line not in seen:
                seen.add(line)
                print(i, line[:100])

print("===== 다른 출처")


def get(url):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=90).read().decode("utf-8", "replace")


def clean(s):
    s = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


for word in ["서귀포시 공중화장실", "서귀포시_공중화장실", "제주특별자치도 서귀포시 화장실"]:
    url = "https://www.data.go.kr/tcs/dss/selectDataSetList.do?" + urllib.parse.urlencode({"keyword": word, "perPage": "10"})
    page = get(url)
    links = list(dict.fromkeys(re.findall(r'href="(/data/\d+/(?:fileData|openapi|standard)\.do)', page)))
    print("검색", word, links[:8])
    for l in links[:6]:
        pg = get("https://www.data.go.kr" + l)
        t = re.search(r"<title>(.*?)</title>", pg, flags=re.S)
        title = clean(t.group(1))[:60] if t else ""
        if "화장실" in title:
            txt = clean(pg)
            r = re.search(r"전체 행\s*([\d,]+)", txt)
            u = re.search(r"수정일\s*([\d-]+)", txt)
            print("  ", l, title, "| 행", r.group(1) if r else "?", "| 수정", u.group(1) if u else "?", "| 위도 언급", txt.count("위도"))

pg = get("https://www.data.go.kr/data/15059920/fileData.do")
d = re.search(r'"description"\s*:\s*"([^"]{10,400})', pg)
t = re.search(r"<title>(.*?)</title>", pg, flags=re.S)
print("DEM 페이지", clean(t.group(1))[:70] if t else "", "|", d.group(1)[:300] if d else "")
txt = clean(pg)
for k in ["격자", "해상도", "5m", "90m", "m 간격"]:
    for x in list(re.finditer(k, txt))[:2]:
        print(f"  [{k}]", txt[max(0, x.start() - 50):x.end() + 70])

url = "https://www.vworld.kr/dtmk/dtmk_ntads_s001.do?" + urllib.parse.urlencode({"searchKeyword": "등고선", "pageSize": "10", "pageUnit": "10"})
pg = get(url)
hits = re.findall(r"dsId=([\w]+)", pg)
print("브이월드 등고선 검색 dsId", list(dict.fromkeys(hits))[:12], "| 본문 등고선 언급", clean(pg).count("등고선"))
for x in list(re.finditer("등고선", clean(pg)))[:6]:
    print("  ", clean(pg)[max(0, x.start() - 30):x.end() + 40])

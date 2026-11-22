"""제주시 후보 자료와 브이월드 용량·로그인 조건, 받아 둔 DEM의 형태를 본다. 파일은 새로 받지 않는다."""
import html
import os
import re
import sys
import urllib.request
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0"}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=90).read().decode("utf-8", "replace")


def clean(s):
    s = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


for pk, kind in [("3083697", "fileData"), ("15096923", "fileData"), ("15139404", "fileData"), ("15158398", "fileData"),
                 ("15075838", "openapi"), ("15110521", "fileData"), ("15056354", "fileData"), ("15075726", "fileData"), ("15109235", "openapi")]:
    url = f"https://www.data.go.kr/data/{pk}/{kind}.do"
    try:
        page = get(url)
    except Exception as e:
        print("=====", pk, "실패", e)
        continue
    title = re.search(r"<title>(.*?)</title>", page, flags=re.S)
    text = clean(page)
    print("=====", pk, kind, clean(title.group(1))[:70] if title else "")
    m = re.search(r'"description"\s*:\s*"([^"]{10,300})', page)
    if m:
        print("  설명:", m.group(1)[:220])
    for key, pat in [("제공기관", r"제공기관\s*(\S+\s*\S*)"), ("전체 행", r"전체 행\s*([\d,]+)"), ("수정일", r"수정일\s*([\d-]+)"), ("주기", r"업데이트 주기\s*(\S+)")]:
        x = re.search(pat, text)
        if x:
            print(f"  {key}: {x.group(1)}")
    print("  위도 언급", text.count("위도"), "좌표 언급", text.count("좌표"))

url = "https://www.vworld.kr/dtmk/dtmk_ntads_s002.do?dsId=30182"
page = get(url)
text = clean(page)
print("===== 브이월드 도로중심선 파일별 용량")
print(re.findall(r"도로중심선_00\d\.zip 용량 [\d.,]+ [KMG]B", text))
for x in list(re.finditer("로그인 후", text))[:3]:
    print("  문맥:", text[max(0, x.start() - 50):x.end() + 80])
for x in list(re.finditer(r"loginYn|isLogin|sessionUser|fn_login|라온|RAON|raonk", page))[:8]:
    print("  코드:", re.sub(r"\s+", " ", page[max(0, x.start() - 70):x.end() + 120]))

p = os.path.join(os.path.expanduser("~"), "Downloads", "(B080)공개DEM_33607_img_2025.zip")
with zipfile.ZipFile(p) as z:
    print("===== 공개DEM zip 내용")
    for i in z.infolist():
        print("  ", i.filename, f"{i.file_size:,}B")
    names = z.namelist()
try:
    import rasterio
    print("rasterio", rasterio.__version__)
    target = [n for n in names if n.lower().endswith(".img")]
    if target:
        with rasterio.open(f"zip://{p}!{target[0]}") as ds:
            print("크기", ds.width, ds.height, "해상도", ds.res, "좌표계", ds.crs, "범위", ds.bounds)
            arr = ds.read(1, masked=True)
            print("값 범위", float(arr.min()), float(arr.max()), "결측", int(arr.mask.sum()) if hasattr(arr.mask, "sum") else 0)
except Exception as e:
    print("rasterio 사용 불가", repr(e)[:160])

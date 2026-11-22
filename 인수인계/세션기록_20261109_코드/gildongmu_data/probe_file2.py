"""파일데이터 내려받기 함수 본문, 내려받기 한도 안내, 표준데이터 팝업 내용을 본다. 읽기 전용."""
import re
import sys
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0"}


def get(url, data=None):
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=UA)
    return urllib.request.urlopen(req, timeout=90).read().decode("utf-8", "replace")


page = get("https://www.data.go.kr/data/15110599/fileData.do")
i = page.find("fn_fileDataDown :")
if i < 0:
    i = page.find("fn_fileDataDown:")
if i < 0:
    m = re.search(r"fn_fileDataDown\s*[:=]?\s*function", page)
    i = m.start() if m else -1
print("함수 위치", i)
if i >= 0:
    print(page[i:i + 2600])
else:
    for src in re.findall(r'<script[^>]+src="([^"]+)"', page):
        print("  스크립트", src)

j = page.find('id="fileLimitCheck"')
print("===== 한도 안내", j)
if j >= 0:
    print(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", page[j:j + 1800]))[:700])

print("===== 표준데이터 팝업(서귀포 횡단보도)")
pop = get("https://www.data.go.kr/tcs/dss/selectDpkDetailInfo.do", {"publicDataDetailPk": "uddi:81478fd2-9649-4f8e-b085-9f891d85174f"})
print(len(pop))
print(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", pop))[:1500])
for m in list(re.finditer(r"onclick=\"[^\"]+\"|href=\"[^\"]*(?:down|Down|file)[^\"]*\"", pop))[:10]:
    print("  ", m.group(0)[:260])

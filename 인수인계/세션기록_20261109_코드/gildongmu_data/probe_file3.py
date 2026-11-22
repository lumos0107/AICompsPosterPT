"""파일데이터 내려받기 스크립트의 함수 본문을 본다. 읽기 전용."""
import re
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0"}
for path in ["/js/biz/datset/script_fileDetail.js"]:
    req = urllib.request.Request("https://www.data.go.kr" + path, headers=UA)
    js = urllib.request.urlopen(req, timeout=90).read().decode("utf-8", "replace")
    print("=====", path, len(js))
    for m in list(re.finditer(r"fn_fileDataDown", js))[:3]:
        print("--- 위치", m.start())
        print(js[max(0, m.start() - 100):m.start() + 2400])
    for m in list(re.finditer(r"limit|captcha|Captcha", js))[:12]:
        print("  한도:", re.sub(r"\s+", " ", js[max(0, m.start() - 100):m.end() + 140]))

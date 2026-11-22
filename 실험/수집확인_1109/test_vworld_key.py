"""브이월드 주소 변환 키 시험. 공개 시설 주소만 보내고 키와 요청 주소(URL)는 출력하지 않는다.

사용: python -I test_vworld_key.py <API키.txt>
"""
import json
import sys
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
key = dict(line.split("=", 1) for line in open(sys.argv[1], encoding="utf-8") if "=" in line)["브이월드"].strip()
print("키 길이", len(key))
ADDR = [("road", "제주특별자치도 제주시 임항로 191"), ("road", "제주특별자치도 서귀포시 중앙로 105"), ("parcel", "제주특별자치도 서귀포시 대포동 2211")]
for kind, addr in ADDR:
    q = urllib.parse.urlencode({"service": "address", "request": "getcoord", "version": "2.0", "crs": "epsg:5179", "address": addr, "refine": "true", "simple": "false", "format": "json", "type": kind, "key": key})
    try:
        req = urllib.request.Request("https://api.vworld.kr/req/address?" + q, headers={"User-Agent": "paper-data-check"})
        with urllib.request.urlopen(req, timeout=20) as r:
            res = json.load(r)["response"]
    except Exception as e:
        print(kind, addr, "실패", type(e).__name__)
        continue
    print(kind, addr, "상태", res.get("status"), "오류", (res.get("error") or {}).get("code"), (res.get("error") or {}).get("text"))
    if res.get("status") == "OK":
        p = res["result"]["point"]
        print("  좌표", round(float(p["x"]), 1), round(float(p["y"]), 1), res["refined"]["text"])

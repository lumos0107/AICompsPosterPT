"""로그인 없이 받을 수 있는 나머지 포털 파일을 받는다.

자료마다 새 폴더에 넣고 출처·크기·해시를 기록한다.
포털이 자동등록방지 확인을 요구하면 우회하지 않고 멈춘다.
"""
import datetime
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
BASE = "https://www.data.go.kr"
UA = {"User-Agent": "Mozilla/5.0"}
ROOT = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터"
ORIG = os.path.join(ROOT, "원본", "공공데이터포털")
LOG = os.path.join(ROOT, "수집기록_공공데이터포털.json")
TARGETS = [("제주시_공중화장실", "15110521"), ("상가상권정보_전국", "15083033")]
records = []


class Stop(Exception):
    pass


def post(url, data):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(), headers=UA)
    return urllib.request.urlopen(req, timeout=120).read().decode("utf-8", "replace")


def fetch(label, pk):
    folder = os.path.join(ORIG, label)
    if os.path.isdir(folder) and os.listdir(folder):
        print("이미 있음", label)
        return
    os.makedirs(folder, exist_ok=True)
    page = urllib.request.urlopen(urllib.request.Request(f"{BASE}/data/{pk}/fileData.do", headers=UA), timeout=90).read().decode("utf-8", "replace")
    m = re.search(r"fn_fileDataDown\('(\d+)',\s*'([^']+)',\s*'([^']*)',\s*'(\d+)'", page)
    if not m:
        print("호출 인자 못 찾음", label)
        return
    obj = json.loads(post(f"{BASE}/tcs/dss/selectFileDataDownload.do", {
        "publicDataDetailPk": m.group(2), "publicDataPk": m.group(1), "atchFileId": m.group(3),
        "fileDetailSn": m.group(4), "publicDataTyCode": "PR0051"}))
    if not obj.get("status"):
        print("실패(정보 조회)", label, obj.get("error"))
        records.append({"자료": label, "상태": "정보 조회 실패", "오류": obj.get("error")})
        return
    info = obj.get("dataSetFileDetailInfo") or {}
    a, s = obj["atchFileId"], obj["fileDetailSn"]
    name = info.get("publicDataSj") if info.get("publicDataTyDetailCode") == "DATY05" else info.get("dataNm")
    if json.loads(post(f"{BASE}/cmm/cmm/check-limit.json", {"atchFileId": a, "fileDetailSn": s})).get("needCaptcha"):
        raise Stop(f"{label}: 자동등록방지 확인 요구")
    url = f"{BASE}/cmm/cmm/fileDownload.do?" + urllib.parse.urlencode({"atchFileId": a, "fileDetailSn": s, "dataNm": name})
    tmp = os.path.join(folder, "받는중.tmp")
    h = hashlib.sha256()
    size = 0
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r, open(tmp, "wb") as f:
        disposition = r.headers.get("Content-Disposition", "")
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            f.write(b)
            h.update(b)
            size += len(b)
    with open(tmp, "rb") as f:
        head = f.read(512)
    if head[:4] == b"PK\x03\x04":
        ext = "zip"
    elif head.lstrip()[:1] == b"<":
        os.replace(tmp, os.path.join(folder, "실패_응답.html"))
        print("실패(웹 페이지 응답)", label, size)
        records.append({"자료": label, "상태": "웹 페이지 응답", "주소": url})
        return
    else:
        m2 = re.search(r"\.(csv|xls|xlsx|json)\b", disposition, flags=re.I)
        ext = m2.group(1).lower() if m2 else "csv"
    final = os.path.join(folder, f"{label}.{ext}")
    os.replace(tmp, final)
    print(f"완료 {label} {size:,}B {ext} ({name})")
    records.append({
        "자료": label, "상태": "완료", "파일": os.path.relpath(final, ROOT), "크기": size,
        "sha256": h.hexdigest(), "포털자료명": name, "publicDataPk": pk, "상세키": m.group(2),
        "수정일": info.get("updtDt"), "페이지정보": {"주소": f"{BASE}/data/{pk}/fileData.do"},
        "받은시각": datetime.datetime.now().isoformat(timespec="seconds"),
    })


try:
    for label, pk in TARGETS:
        fetch(label, pk)
        time.sleep(2)
except Stop as e:
    print("멈춤:", e)
finally:
    old = []
    if os.path.exists(LOG):
        with open(LOG, encoding="utf-8") as f:
            old = json.load(f)
    with open(LOG, "w", encoding="utf-8") as f:
        json.dump(old + records, f, ensure_ascii=False, indent=1)
    print("기록", len(records), "건")

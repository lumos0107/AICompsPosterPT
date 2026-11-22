"""공공데이터포털에서 제주 관련 파일을 받는다.

자료마다 새 폴더에 넣고, 출처·크기·해시를 기록한다.
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
FILE_DATA = [
    ("제주_신호기현황", "15110599"),
    ("제주_어린이보호구역_신호등", "15076538"),
    ("제주_어린이보호구역_횡단보도", "15076542"),
    ("제주_어린이보호구역_교차로", "15075789"),
]
STANDARD = [
    ("횡단보도표준", "15028201"),
    ("공중화장실표준", "15012892"),
    ("도시공원표준", "15012890"),
    ("보안등표준", "15017320"),
]
WORDS = ["제주", "서귀포"]
records = []


class Stop(Exception):
    pass


def post(url, data):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(), headers=UA)
    return urllib.request.urlopen(req, timeout=120).read().decode("utf-8", "replace")


def clean(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()


def list_rows(pk, word):
    url = f"{BASE}/data/{pk}/standard.do"
    seen = {}
    for n in range(1, 400):
        page = post(url, {"pageIndex": str(n), "publicDataPk": pk, "searchKeyword2": word})
        part = page[page.find("데이터 목록 (제공기관 수"):]
        found = re.findall(r'data-public-pk="([^"]+)".*?</span>\s*([^<]+?)\s*</a>', part, flags=re.S)
        new = [(a, b) for a, b in found if a not in seen]
        if not new:
            break
        for a, b in new:
            seen[a] = b
        time.sleep(1)
    return seen


def fetch(label, pk, detail, atch, sn, meta):
    folder = os.path.join(ORIG, label)
    if os.path.isdir(folder) and os.listdir(folder):
        print("이미 있음", label)
        return
    os.makedirs(folder, exist_ok=True)
    res = post(f"{BASE}/tcs/dss/selectFileDataDownload.do", {
        "publicDataDetailPk": detail, "publicDataPk": pk, "atchFileId": atch,
        "fileDetailSn": sn, "publicDataTyCode": "PR0051"})
    obj = json.loads(res)
    if not obj.get("status"):
        print("실패(정보 조회)", label, obj.get("error"))
        records.append({"자료": label, "상태": "정보 조회 실패", "오류": obj.get("error")})
        return
    info = obj.get("dataSetFileDetailInfo") or {}
    a, s = obj["atchFileId"], obj["fileDetailSn"]
    name = info.get("publicDataSj") if info.get("publicDataTyDetailCode") == "DATY05" else info.get("dataNm")
    limit = json.loads(post(f"{BASE}/cmm/cmm/check-limit.json", {"atchFileId": a, "fileDetailSn": s}))
    if limit.get("needCaptcha"):
        raise Stop(f"{label}: 자동등록방지 확인 요구")
    url = f"{BASE}/cmm/cmm/fileDownload.do?" + urllib.parse.urlencode({"atchFileId": a, "fileDetailSn": s, "dataNm": name})
    req = urllib.request.Request(url, headers=UA)
    tmp = os.path.join(folder, "받는중.tmp")
    h = hashlib.sha256()
    size = 0
    with urllib.request.urlopen(req, timeout=300) as r, open(tmp, "wb") as f:
        disposition = r.headers.get("Content-Disposition", "")
        ctype = r.headers.get("Content-Type", "")
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
        print("실패(웹 페이지 응답)", label, size, ctype)
        records.append({"자료": label, "상태": "웹 페이지 응답", "주소": url})
        return
    else:
        m = re.search(r"\.(csv|xls|xlsx|json)\b", disposition, flags=re.I)
        ext = m.group(1).lower() if m else "csv"
    final = os.path.join(folder, f"{label}.{ext}")
    os.replace(tmp, final)
    print(f"완료 {label} {size:,}B {ext} ({name})")
    records.append({
        "자료": label, "상태": "완료", "파일": os.path.relpath(final, ROOT), "크기": size,
        "sha256": h.hexdigest(), "포털자료명": name, "publicDataPk": pk, "상세키": detail,
        "수정일": info.get("updtDt"), "페이지정보": meta,
        "받은시각": datetime.datetime.now().isoformat(timespec="seconds"),
    })


def main():
    for label, pk in FILE_DATA:
        req = urllib.request.Request(f"{BASE}/data/{pk}/fileData.do", headers=UA)
        page = urllib.request.urlopen(req, timeout=90).read().decode("utf-8", "replace")
        m = re.search(r"fn_fileDataDown\('(\d+)',\s*'([^']+)',\s*'([^']*)',\s*'(\d+)'", page)
        if not m:
            print("호출 인자 못 찾음", label)
            continue
        fetch(label, m.group(1), m.group(2), m.group(3), m.group(4), {"주소": f"{BASE}/data/{pk}/fileData.do"})
        time.sleep(2)

    for base, pk in STANDARD:
        rows = {}
        for word in WORDS:
            got = list_rows(pk, word)
            hit = {k: v for k, v in got.items() if word in v}
            print(f"[{base}] 검색 '{word}': 받은 {len(got)}행, 이름에 포함 {len(hit)}행")
            rows.update(hit)
        if not rows:
            print(f"[{base}] 제주 제공기관 없음(검색 기준)")
        for detail, name in rows.items():
            pop = post(f"{BASE}/tcs/dss/selectDpkDetailInfo.do", {"publicDataDetailPk": detail})
            text = clean(re.sub(r"<script.*?</script>", " ", pop, flags=re.S))
            meta = {"주소": f"{BASE}/data/{pk}/standard.do", "포털이름": name}
            for key, pat in [("전체 행 수", r"전체 행 수\s*([\d,]+)"), ("수정일", r"수정일\s*([\d-]+)"), ("업데이트 주기", r"업데이트 주기\s*(\S+)"), ("이용허락", r"이용허락범위 이용허락범위\s*(\S+\s*\S*)")]:
                m = re.search(pat, text)
                if m:
                    meta[key] = m.group(1)
            m = re.search(r"fn_fileDataDown\('(\d+)',\s*'([^']+)',\s*'([^']*)',\s*'(\d+)'", pop)
            if not m:
                print("호출 인자 못 찾음", name)
                continue
            label = base + "_" + re.sub(r"[^\w가-힣]+", "_", name)
            fetch(label, m.group(1), m.group(2), m.group(3), m.group(4), meta)
            time.sleep(2)


try:
    main()
except Stop as e:
    print("멈춤:", e)
finally:
    old = []
    if os.path.exists(LOG):
        with open(LOG, encoding="utf-8") as f:
            old = json.load(f)
    os.makedirs(ROOT, exist_ok=True)
    with open(LOG, "w", encoding="utf-8") as f:
        json.dump(old + records, f, ensure_ascii=False, indent=1)
    print("기록", len(records), "건")

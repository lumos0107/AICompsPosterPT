"""브이월드 주소 변환. 공개 시설 주소(신호기 교차로, 공중화장실)만 보낸다. 키와 요청 URL은 출력·저장하지 않는다.

대상: 1) 신호기현황 15110599에서 단일로를 뺀 교차로 830건
      2) 공중화장실 표준 중 서귀포시
      3) 제주시 공중화장실 중 좌표가 없거나 제주 범위 밖인 건

분류 (주소를 보기 전에 정한 규칙):
  성공: 변환 성공, 돌려받은 주소가 입력 주소의 낱말을 모두 포함하고, 위치 설명이 없고, 제주 범위 안
  모호: 변환은 됐으나 (a) 입력에 '건너편·앞·뒤·반대편·맞은편·옆·부근·일원·인근' 설명이 있음
        (b) 돌려받은 주소가 입력의 동·리·번지와 다름 (c) 도로명과 지번 결과가 100m 넘게 다름 (d) 제주 범위 밖
  실패: 찾지 못함 또는 호출 오류

실행: py -I geocode.py <API키.txt>
결과: 주소변환_캐시.json, 신호위치.csv, 화장실_변환.csv, 주소변환.out
"""
import collections
import csv
import io
import json
import math
import os
import re
import sys
import time
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
HERE = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\새그래프_1110"
RAW = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\공공데이터포털"
key = dict(line.split("=", 1) for line in open(sys.argv[1], encoding="utf-8") if "=" in line)["브이월드"].strip()
out = open(os.path.join(HERE, "주소변환.out"), "w", encoding="utf-8")
CACHE_P = os.path.join(HERE, "주소변환_캐시.json")
cache = json.load(open(CACHE_P, encoding="utf-8")) if os.path.exists(CACHE_P) else {}
X0, Y0, X1, Y1 = 873000, 1458000, 952000, 1559000
OFFSET = re.compile(r"건너편|맞은편|반대편|앞|뒤|옆|부근|일원|인근")
sent = 0


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out.write(s + "\n")
    out.flush()


def call(kind, addr):
    """반환: dict(status, x, y, refined). 캐시 사용."""
    global sent
    k = f"{kind}|{addr}"
    if k in cache:
        return cache[k]
    q = urllib.parse.urlencode({"service": "address", "request": "getcoord", "version": "2.0", "crs": "epsg:5179", "address": addr, "refine": "true", "simple": "false", "format": "json", "type": kind, "key": key})
    res = None
    for attempt in range(3):
        try:
            req = urllib.request.Request("https://api.vworld.kr/req/address?" + q, headers={"User-Agent": "paper-data-check"})
            with urllib.request.urlopen(req, timeout=20) as r:
                j = json.load(r)["response"]
            st = j.get("status")
            if st == "OK":
                p = j["result"]["point"]
                res = dict(status="OK", x=float(p["x"]), y=float(p["y"]), refined=(j.get("refined") or {}).get("text", ""))
            elif st == "NOT_FOUND":
                res = dict(status="NOT_FOUND")
            else:
                res = dict(status="ERROR", code=(j.get("error") or {}).get("code"))
            break
        except Exception as e:
            res = dict(status="ERROR", code=type(e).__name__)
            time.sleep(1.0 + attempt)
    sent += 1
    time.sleep(0.12)
    if res["status"] != "ERROR":
        cache[k] = res
        if sent % 50 == 0:
            json.dump(cache, open(CACHE_P, "w", encoding="utf-8"), ensure_ascii=False)
    return res


def strip_note(a):
    """괄호 설명과 끝의 '번지'를 뺀 주소, 괄호 설명 반환."""
    note = " ".join(re.findall(r"\(([^)]*)\)", a))
    t = re.sub(r"\([^)]*\)", " ", a)
    t = re.sub(r"(\d)\s*번지", r"\1", t)
    return re.sub(r"\s+", " ", t).strip(), note


def tokens(a):
    return [x for x in re.sub(r"[,()]", " ", a).split() if x]


def norm_parcel(t):
    return re.sub(r"^산\s*", "산", t)


def covers(inp, refined):
    """입력 낱말이 돌려받은 주소에 모두 있는가."""
    r = refined.replace(" ", "")
    return all(x in r for x in tokens(inp))


def is_road(a):
    return bool(re.search(r"(로|길)\s*\d", a))


def inside(x, y):
    return X0 <= x <= X1 and Y0 <= y <= Y1


def classify(attempts, note):
    """attempts: [(kind, addr)]. 첫 성공을 쓰고 모든 OK 결과로 거리 차를 본다."""
    results = [(k, a, call(k, a)) for k, a in attempts]
    ok = [(k, a, r) for k, a, r in results if r["status"] == "OK"]
    if not ok:
        err = [r for _, _, r in results if r["status"] == "ERROR"]
        return dict(상태="실패", 사유="호출 오류" if err else "찾지 못함", x="", y="", 변환주소="", 사용유형="")
    match = [v for v in ok if covers(v[1], v[2]["refined"])]
    k, a, r = (match or ok)[0]
    reasons = []
    if note and OFFSET.search(note):
        reasons.append("위치 설명: " + note.strip())
    if not match:
        reasons.append("돌려받은 주소가 입력과 다름")
    if not inside(r["x"], r["y"]):
        reasons.append("제주 범위 밖")
    if len(ok) >= 2:
        d = max(math.hypot(u[2]["x"] - v[2]["x"], u[2]["y"] - v[2]["y"]) for u in ok for v in ok)
        if d > 100:
            reasons.append(f"도로명·지번 결과 {d:.0f}m 차이")
    return dict(상태="모호" if reasons else "성공", 사유="; ".join(reasons), x=round(r["x"], 2), y=round(r["y"], 2), 변환주소=r["refined"], 사용유형=k)


def read(p):
    raw = open(p, "rb").read()
    for enc in ("utf-8-sig", "cp949"):
        try:
            return list(csv.DictReader(io.StringIO(raw.decode(enc))))
        except UnicodeDecodeError:
            continue
    raise ValueError(p)


# 1) 신호기
sig = [r for r in read(os.path.join(RAW, "제주_신호기현황", "제주_신호기현황.csv")) if r["기하구조"] != "단일로"]
log("신호기 교차로", len(sig))
rows = []
for r in sig:
    a, note = strip_note(r["주소"].strip())
    att = [("road", a), ("parcel", a)] if is_road(a) else [("parcel", a)]
    c = classify(att, note)
    rows.append({"연번": r["연번"], "주소": r["주소"].strip(), "시": "서귀포시" if "서귀포시" in r["주소"] else "제주시", "기하구조": r["기하구조"], **c})
with open(os.path.join(HERE, "신호위치.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
json.dump(cache, open(CACHE_P, "w", encoding="utf-8"), ensure_ascii=False)
log("\n[신호기 교차로 830건]")
for si in ("제주시", "서귀포시", None):
    rs = [r for r in rows if si is None or r["시"] == si]
    c = collections.Counter(r["상태"] for r in rs)
    log(f"{si or '합계'}: 건수 {len(rs)}, 성공 {c['성공']} ({c['성공'] / len(rs):.1%}), 모호 {c['모호']}, 실패 {c['실패']}")
log("모호 사유:", collections.Counter(re.sub(r": .*|\d+m", "", x) for r in rows for x in r["사유"].split("; ") if r["상태"] == "모호").most_common())
log("실패 사유:", collections.Counter(r["사유"] for r in rows if r["상태"] == "실패").most_common())
xy = [(r["x"], r["y"]) for r in rows if r["x"] != ""]
log("같은 좌표로 변환된 건:", sum(v - 1 for v in collections.Counter(xy).values() if v > 1))

# 2) 화장실 표준 서귀포시
std = read(os.path.join(RAW, "공중화장실표준_제주특별자치도_localdata", "공중화장실정보_제주특별자치도.csv"))
codes = collections.Counter(r["개방자치단체코드"].strip() for r in std)
log("\n화장실 표준 자치단체코드", codes.most_common())
SG = {"대정읍", "남원읍", "성산읍", "안덕면", "표선면"}


def is_sg(r):
    t = (r["소재지도로명주소"] + " " + r["소재지지번주소"])
    if "서귀포시" in t:
        return True
    if "제주시" in t:
        return False
    return any(x in t for x in SG)


sg = [r for r in std if r["개방자치단체코드"].strip() == "6520000"]  # 서귀포시 코드. 주소로 고르면 시 이름이 빠진 주소 때문에 26건이 누락됨
log("서귀포시 선택", len(sg), "자치단체코드", collections.Counter(r["개방자치단체코드"].strip() for r in sg).most_common())


def toilet_row(name, road, jibun, source, base, ident):
    att, notes = [], []
    road, n1 = strip_note((road or "").strip())
    jibun, n2 = strip_note((jibun or "").strip())
    for t in (road,):
        if t:
            att.append(("road", t) if is_road(t) else ("parcel", t))
    if jibun and jibun != road:
        att.append(("parcel", jibun))
    note = " ".join(x for x in (n1, n2) if x)
    if not att:
        return {"출처": source, "번호": ident, "이름": name, "도로명": road, "지번": jibun, "기준일": base, "상태": "실패", "사유": "주소 없음", "x": "", "y": "", "변환주소": "", "사용유형": ""}
    return {"출처": source, "번호": ident, "이름": name, "도로명": road, "지번": jibun, "기준일": base, **classify(att, note)}


rows2 = [toilet_row(r["화장실명"], r["소재지도로명주소"], r["소재지지번주소"], "표준_서귀포시", r["데이터기준일자"], r["관리번호"]) for r in sg]

# 3) 제주시 전용 자료의 좌표 없음·범위 밖
from pyproj import Transformer

to5179 = Transformer.from_crs(4326, 5179, always_xy=True)
jj = read(os.path.join(RAW, "제주시_공중화장실", "제주시_공중화장실.csv"))
log("\n제주시 화장실 항목", list(jj[0].keys())[:14])
need = []
for r in jj:
    try:
        la, lo = float(r["위도 좌표"]), float(r["경도 좌표"])
    except ValueError:
        need.append(r)
        continue
    if la == 0 or lo == 0:
        need.append(r)
        continue
    x, y = to5179.transform(lo, la)
    if not inside(x, y):
        need.append(r)
log("제주시 좌표 보완 대상", len(need))
nosp = {c.replace(" ", ""): c for c in jj[0]}
nm = nosp["화장실명"]
road_c = nosp["도로명주소"]
jib_c = nosp["지번주소"]
base_c = [v for k, v in nosp.items() if "기준일" in k][0]
idc = list(jj[0].keys())[0]
rows3 = [toilet_row(r[nm], r[road_c], r[jib_c], "제주시_보완", r[base_c], r[idc]) for r in need]
all_t = rows2 + rows3
with open(os.path.join(HERE, "화장실_변환.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(all_t[0].keys()))
    w.writeheader()
    w.writerows(all_t)
json.dump(cache, open(CACHE_P, "w", encoding="utf-8"), ensure_ascii=False)
for src, rs in (("표준_서귀포시", rows2), ("제주시_보완", rows3)):
    c = collections.Counter(r["상태"] for r in rs)
    log(f"[{src}] 건수 {len(rs)}, 성공 {c['성공']}, 모호 {c['모호']}, 실패 {c['실패']}")
    log("  사유:", collections.Counter(re.sub(r": .*|\d+m", "", x) for r in rs for x in r["사유"].split("; ") if x).most_common())
log("\n이번 실행 호출 수", sent)
log("끝")

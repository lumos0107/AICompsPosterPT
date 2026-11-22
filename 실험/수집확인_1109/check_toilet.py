"""공중화장실 표준(제주) 확인: 항목, 건수, 주소, 기준일, 제주시 자료와 대조.

사용: python -I check_toilet.py <표준 csv> <제주시 csv> <결과 파일>
"""
import collections
import csv
import io
import re
import sys

path, jeju_path, result = sys.argv[1:4]
sys.stdout.reconfigure(encoding="utf-8")
out = open(result, "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out.write(s + "\n")


def load(p):
    raw = open(p, "rb").read()
    for enc in ("utf-8-sig", "cp949"):
        try:
            text = raw.decode(enc)
            return enc, list(csv.DictReader(io.StringIO(text)))
        except UnicodeDecodeError:
            continue
    raise ValueError(p)


enc, rows = load(path)
cols = list(rows[0])
log("인코딩", enc, "건수", f"{len(rows):,}", "항목 수", len(cols))
log("항목", cols)
log("첫 줄", {k: rows[0][k] for k in cols[:12]})
for c in cols:
    filled = sum(1 for r in rows if (r[c] or "").strip())
    if re.search(r"위도|경도|WGS|주소|데이터기준|최종|수정|갱신|관리기관|자치단체|시군구|구분", c):
        vals = collections.Counter((r[c] or "").strip() for r in rows)
        log(f"  {c}: 채움 {filled:,}/{len(rows):,}, 값 종류 {len(vals):,}, 상위 {vals.most_common(4)}")
road = next((c for c in cols if "도로명" in c and "주소" in c), None)
jibun = next((c for c in cols if "지번" in c and "주소" in c), None)
log("주소 항목", road, jibun)
city = collections.Counter()
both = none = 0
for r in rows:
    a, b = (r.get(road) or "").strip() if road else "", (r.get(jibun) or "").strip() if jibun else ""
    text = a or b
    city["서귀포시" if "서귀포" in text else "제주시" if "제주시" in text else "주소로 구분 안 됨"] += 1
    both += bool(a and b)
    none += not (a or b)
log("주소로 본 시", dict(city), "둘 다 있음", both, "둘 다 없음", none)
name = next(c for c in cols if "화장실명" in c)
log("중복 화장실명+주소", len(rows) - len({(r[name].strip(), (r.get(road) or r.get(jibun) or "").strip()) for r in rows}))

_, jr = load(jeju_path)
jc = list(jr[0])
log("\n제주시 자료 건수", f"{len(jr):,}", "항목", jc[:12])
norm = lambda s: re.sub(r"\s+", "", s or "")
CODE = {"6510000": "제주시", "6520000": "서귀포시"}
for code, nm in CODE.items():
    sub = [r for r in rows if r["개방자치단체코드"] == code]
    r_ok = sum(1 for r in sub if norm(r[road]))
    j_ok = sum(1 for r in sub if norm(r[jibun]))
    miss = sum(1 for r in sub if not norm(r[road]) and not norm(r[jibun]))
    log(f"{nm}(코드 {code}): {len(sub):,}건, 도로명칸 채움 {r_ok:,}, 지번칸 채움 {j_ok:,}, 둘 다 없음 {miss}, 기준일 {collections.Counter(r['데이터기준일자'] for r in sub).most_common(3)}")
A = {norm(r[name]) for r in rows if r["개방자치단체코드"] == "6510000"}
B = {norm(r["화장실 명"]) for r in jr}
log(f"제주시 이름 대조: 표준 {len(A):,}, 제주시 자료 {len(B):,}, 겹침 {len(A & B):,}, 표준에만 {len(A - B):,}, 제주시 자료에만 {len(B - A):,}")

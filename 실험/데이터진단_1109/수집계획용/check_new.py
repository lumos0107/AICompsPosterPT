"""새로 받은 제주시 화장실과 상가정보의 내용을 확인한다. 압축은 풀지 않고 읽는다."""
import collections
import csv
import glob
import io
import os
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
csv.field_size_limit(10 ** 7)
ROOT = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\공공데이터포털"


def decode(raw):
    for enc in ("utf-8-sig", "cp949"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return raw.decode("cp949", "replace"), "cp949(대체)"


def in_jeju(la, lo):
    try:
        return 33.0 < float(la) < 33.7 and 126.0 < float(lo) < 127.1
    except (TypeError, ValueError):
        return False


p = glob.glob(os.path.join(ROOT, "제주시_공중화장실", "*"))[0]
text, enc = decode(open(p, "rb").read())
rows = list(csv.DictReader(io.StringIO(text)))
cols = list(rows[0].keys())
print("화장실", os.path.basename(p), "행", len(rows), "인코딩", enc)
print(" 항목", cols[:14])
la = next((c for c in cols if "위도" in c), None)
lo = next((c for c in cols if "경도" in c), None)
print(" 좌표 항목", la, lo, "제주 범위 안", sum(in_jeju(r.get(la), r.get(lo)) for r in rows) if la and lo else "없음")

p = glob.glob(os.path.join(ROOT, "상가상권정보_전국", "*"))[0]
print("상가", os.path.basename(p), f"{os.path.getsize(p):,}B")
with zipfile.ZipFile(p) as z:
    infos = z.infolist()
    for i in infos:
        print("  ", i.filename.encode("cp437", "replace").decode("cp949", "replace") if i.flag_bits & 0x800 == 0 else i.filename, f"{i.file_size:,}B")
    pick = [i for i in infos if "제주" in (i.filename.encode("cp437", "replace").decode("cp949", "replace") if i.flag_bits & 0x800 == 0 else i.filename) and i.filename.lower().endswith(".csv")]
    print("제주 파일", len(pick))
    if pick:
        text, enc = decode(z.read(pick[0]))
        rows = list(csv.DictReader(io.StringIO(text)))
        cols = list(rows[0].keys())
        print(" 행", len(rows), "인코딩", enc)
        print(" 항목", cols)
        names = [c for c in cols if "소분류명" in c or "표준산업분류명" in c]
        la = next((c for c in cols if c.strip() == "위도"), None)
        lo = next((c for c in cols if c.strip() == "경도"), None)
        print(" 좌표 제주 범위 안", sum(in_jeju(r.get(la), r.get(lo)) for r in rows) if la and lo else "없음")
        for c in names:
            hit = collections.Counter(r[c] for r in rows if "편의점" in (r.get(c) or "") or "체인화 편의점" in (r.get(c) or ""))
            print(f" [{c}] 편의점 관련", hit.most_common(4))

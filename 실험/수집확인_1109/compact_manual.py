"""설명서_전문.txt의 지정 줄부터 반복 문구와 자료형을 덜어 항목명과 코드표만 남긴다. 내용 항목은 버리지 않는다.

사용: python -I compact_manual.py <전문 txt> <시작 줄> <결과 txt>
"""
import re
import sys

src, start, dst = sys.argv[1], int(sys.argv[2]), sys.argv[3]
lines = open(src, encoding="utf-8").read().splitlines()[start - 1:]
DROP = re.compile(r"^(지형지물 정의|구성 레이어|1/1,000 1/5,000 1/25,000$|연번 항목ID|● 항목설명|기본도 제작정보|제작정보$|각각의 정기|=== \d+쪽|\d+ UFID |\d+ SCLS |\d+ FMTA )")
FIELD = re.compile(r"^\d+\s+([A-Z]{2,5})\s+(.+?)\s+(?:VARCHAR2|NUMBER)")
out, fields = [], []


def flush():
    if fields:
        out.append("  항목: " + ", ".join(fields))
        fields.clear()


for raw in lines:
    line = raw.strip()
    if not line or DROP.match(line):
        continue
    m = FIELD.match(line)
    if m:
        fields.append(f"{m.group(1)}({m.group(2)})")
        continue
    flush()
    if line.startswith("분류그룹"):
        out.append("\n# " + line.replace("분류그룹 ", "").replace(" 명칭 ", " / "))
    else:
        out.append(line)
flush()
open(dst, "w", encoding="utf-8").write("\n".join(out))
print(len(out), "줄")

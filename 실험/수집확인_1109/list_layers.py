"""설명서의 지형지물 목록을 뽑아 축척별 유무와 이번에 받은 항목을 표시한다.

사용: python -I list_layers.py <설명서 pdf> <풀기 폴더> <결과 파일>
"""
import os
import re
import sys

import pdfplumber

pdf, root, result = sys.argv[1:4]
sys.stdout.reconfigure(encoding="utf-8")
out = open(result, "w", encoding="utf-8")
got = {x[4:] for x in os.listdir(root)}
pat = re.compile(r"^(\d+)\s+(교통|건물|시설|식생|수계|지형|경계|주기)\s+(.+)$")
rows = {}
with pdfplumber.open(pdf) as doc:
    for page in doc.pages[:12]:
        for line in (page.extract_text() or "").splitlines():
            m = pat.match(line.strip())
            if m and re.search(r"N\d[APL]_|-", m.group(3)):
                rows[int(m.group(1))] = (m.group(2), m.group(3))
for n, (group, rest) in sorted(rows.items()):
    name = re.split(r"\s+(?:N\d[APL]_|-\s)", rest)[0].strip()
    has = {s: bool(re.search(rf"N{s}[APL]_", rest)) for s in "134"}
    code = re.search(r"N\d[APL]_([A-H]\d{7})", rest)
    code = code.group(1) if code else ""
    mark = "받음" if code in got else ""
    line = f"{n:>3} {group} {name:<14} 1천:{'O' if has['1'] else '-'} 5천:{'O' if has['3'] else '-'} 2.5만:{'O' if has['4'] else '-'} {code} {mark}"
    print(line)
    out.write(line + "\n")
print("항목 수", len(rows))

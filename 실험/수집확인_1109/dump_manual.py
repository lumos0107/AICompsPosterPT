"""설명서 전문을 쪽 번호와 함께 텍스트로 뽑는다. 쪽마다 반복되는 머리글은 뺀다.

사용: python -I dump_manual.py <pdf> <결과 txt>
"""
import re
import sys

import pdfplumber

pdf, result = sys.argv[1:3]
SKIP = re.compile(r"^(데이터베이스설계서|데이터베이스 설계서|프로젝트명|단계명|활동명|작업명|.*작성일\s*:|국토지리정보원$|-\s*\d+\s*-|-\s*\d+\s*-\s*국토지리정보원)")
n_lines = 0
with pdfplumber.open(pdf) as doc, open(result, "w", encoding="utf-8") as out:
    for i, page in enumerate(doc.pages, 1):
        out.write(f"\n=== {i}쪽\n")
        for line in (page.extract_text() or "").splitlines():
            line = line.strip()
            if line and not SKIP.match(line):
                out.write(line + "\n")
                n_lines += 1
print("줄 수", n_lines)

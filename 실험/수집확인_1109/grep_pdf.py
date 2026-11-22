"""설명서 pdf에서 낱말이 든 줄을 찾는다. 사용: python -I grep_pdf.py <pdf> <낱말> [<낱말> ...]"""
import sys

import pdfplumber

sys.stdout.reconfigure(encoding="utf-8")
pdf, words = sys.argv[1], sys.argv[2:]
with pdfplumber.open(pdf) as doc:
    for n, page in enumerate(doc.pages, 1):
        text = (page.extract_text() or "").splitlines()
        for i, line in enumerate(text):
            if any(w in line for w in words):
                print(n, line[:90])

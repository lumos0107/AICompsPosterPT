import os
import sys
import pdfplumber
sys.stdout.reconfigure(encoding="utf-8")
D = os.path.join(os.path.expanduser("~"), "Downloads")
with pdfplumber.open(os.path.join(D, "연속수치지형도_데이터_설명서.pdf")) as pdf:
    for i in (13, 14, 16, 17, 128, 130):
        print(f"----- p{i}")
        print(pdf.pages[i-1].extract_text()[:2600])

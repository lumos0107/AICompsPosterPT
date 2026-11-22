import os
import re
import sys
import zipfile
import struct
import pdfplumber

sys.stdout.reconfigure(encoding="utf-8")
D = os.path.join(os.path.expanduser("~"), "Downloads")
pat = re.compile(r"RDD0|RDQ0|SWK0|SWQ0|BYC0|CSU0|ITH0|BDK0|A0023|A0033|A0020000|A0033320|F0010|F0020|A0063|A0070|A0090|입체|육교|교량|터널|계단|분리대|등고선|표고점|차로수|도로폭|RVWD|RDLN|PMTR|PVM0|BIW0")
with pdfplumber.open(os.path.join(D, "연속수치지형도_데이터_설명서.pdf")) as pdf:
    print("pages", len(pdf.pages))
    seen = set()
    for i, page in enumerate(pdf.pages, 1):
        for line in (page.extract_text() or "").splitlines():
            if pat.search(line) and line not in seen:
                seen.add(line)
                print(i, line[:140])

print("===== 공개 DEM 파일")
p = os.path.join(D, "(B080)공개DEM_33607_img_2025.zip")
z = zipfile.ZipFile(p)
print([(i.filename, i.file_size) for i in z.infolist()])

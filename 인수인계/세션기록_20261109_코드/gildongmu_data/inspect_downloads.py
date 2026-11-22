"""받아 둔 지형도 자료의 열 이름과 설명서의 도로 관련 항목을 본다. 읽기 전용."""
import glob
import os
import struct
import sys

import pdfplumber

sys.stdout.reconfigure(encoding="utf-8")
D = os.path.join(os.path.expanduser("~"), "Downloads")
for folder in ["(연속수치지형도)도로중심선_제주", "국가기본도_자전거도로중심선", "N3L_A0033320"]:
    for p in glob.glob(os.path.join(D, folder, "**", "*.dbf"), recursive=True)[:3]:
        with open(p, "rb") as f:
            head = f.read(32)
            n = struct.unpack("<I", head[4:8])[0]
            hlen = struct.unpack("<H", head[8:10])[0]
            names = []
            while f.tell() < hlen - 1:
                b = f.read(32)
                if b[0] == 13:
                    break
                names.append(b[:11].split(b"\0")[0].decode("cp949", "replace"))
        print(os.path.relpath(p, D), "행", n, "열", names)
with pdfplumber.open(os.path.join(D, "연속수치지형도_데이터_설명서.pdf")) as pdf:
    print("설명서 쪽 수", len(pdf.pages))
    for i, page in enumerate(pdf.pages, 1):
        text = page.extract_text() or ""
        for line in text.splitlines():
            if any(k in line for k in ["A00", "횡단", "인도", "보도", "육교", "도로"]):
                print(i, line[:110])

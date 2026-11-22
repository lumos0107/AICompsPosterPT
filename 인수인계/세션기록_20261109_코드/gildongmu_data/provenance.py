"""받아 둔 지형도 파일의 범위와 당시 수집 메모를 본다. 읽기 전용."""
import glob
import os
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8")
H = os.path.expanduser("~")
D = os.path.join(H, "Downloads")
for folder in ["(연속수치지형도)도로중심선_제주", "N3L_A0033320", "국가기본도_자전거도로중심선"]:
    for p in glob.glob(os.path.join(D, folder, "**", "*.shp"), recursive=True)[:2]:
        with open(p, "rb") as f:
            b = f.read(100)
        x0, y0, x1, y1 = struct.unpack("<4d", b[36:68])
        print(os.path.basename(p), "범위", round(x0), round(y0), round(x1), round(y1))
        prj = p[:-4] + ".prj"
        if os.path.exists(prj):
            print("   좌표계", open(prj, encoding="utf-8", errors="replace").read()[:90])
        xml = p[:-4] + ".xml"
        if os.path.exists(xml):
            print("   메타", open(xml, encoding="utf-8", errors="replace").read()[:300].replace("\n", " "))

memo = glob.glob(os.path.join(H, "Desktop", "3-1", "캡스톤", "캡스톤 지도 데이터 재포집", "*"))
print("메모 폴더:", [os.path.basename(x) for x in memo][:30])
try:
    import docx

    for p in memo:
        if p.lower().endswith(".docx"):
            d = docx.Document(p)
            print("==", os.path.basename(p))
            for para in d.paragraphs:
                if para.text.strip():
                    print("  ", para.text.strip()[:220])
            for rel in d.part.rels.values():
                if "hyperlink" in rel.reltype:
                    print("   링크", rel.target_ref[:200])
except Exception as e:
    print("docx 읽기 실패", e)

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
p = Path(r"C:\Users\seungjun\Documents\claude_code\논문\writing\drafts\정보기술학회\build_pdf.py")
s = p.read_text(encoding="utf-8")
reps = [
    ("""SERIF = "'Times New Roman','HYSinMyeongJo-Medium','HY신명조',serif"
GOTHIC = "'Times New Roman','HYGothic-Medium','HY중고딕',sans-serif"
HEAD_GOTHIC = "'HYGothic-Medium','HY중고딕',sans-serif"
""",
     """# 크롬은 윈도우에서 글꼴 이름 끝의 -Medium을 굵기로 읽어 HY신명조·HY중고딕을 못 찾는다. PostScript 이름으로 직접 지정한다.
FONT_FACES = \"\"\"
@font-face { font-family: 'KR Serif'; src: local('H2mjsM'), local('HY신명조'); }
@font-face { font-family: 'KR Gothic'; src: local('H2gtrM'), local('HY중고딕'); }
\"\"\"
SERIF = "'Times New Roman','KR Serif',serif"
GOTHIC = "'Times New Roman','KR Gothic',sans-serif"
HEAD_GOTHIC = "'KR Gothic',sans-serif"
"""),
    ("""  font: 10pt/1.5 {SERIF}; color: #000; letter-spacing: -0.03em;""",
     """  font: 10pt/1.5 {SERIF}; color: #000; letter-spacing: -0.06em;"""),
    ("""text-align: center; margin: 0 0 3mm; letter-spacing: -0.05em; }}""",
     """text-align: center; margin: 0 0 3mm; letter-spacing: -0.07em; }}"""),
    (""".authors {{ font: 11pt/1.4 {DOTUM}; text-align: center; margin-bottom: 4mm; }}""",
     """.authors {{ font: 11pt/1.4 {DOTUM}; text-align: center; margin-bottom: 4mm; letter-spacing: 0.05em; }}"""),
    ("""text-align: center; margin: 0 4mm 3mm; letter-spacing: -0.03em; }}""",
     """text-align: center; margin: 0 4mm 3mm; letter-spacing: -0.07em; }}"""),
    ("""text-align: center; letter-spacing: 0; margin-bottom: 5mm; }}
.abs-h""",
     """text-align: center; letter-spacing: 0.05em; margin-bottom: 5mm; }}
.abs-h"""),
    (""".abs.en {{ letter-spacing: -0.005em; word-break: normal; }}""",
     """.abs.en {{ letter-spacing: -0.04em; word-break: normal; }}"""),
    ("""margin: 6mm 0 3.5mm; break-after: avoid; letter-spacing: -0.02em; }}""",
     """margin: 6mm 0 3.5mm; break-after: avoid; letter-spacing: -0.06em; }}"""),
    ("""margin: 3.5mm 0 1.5mm; break-after: avoid; letter-spacing: -0.03em; }}""",
     """margin: 3.5mm 0 1.5mm; break-after: avoid; letter-spacing: -0.06em; }}"""),
    (""".cap {{ font: 9pt/1.32 {GOTHIC}; letter-spacing: -0.02em; }}""",
     """.cap {{ font: 9pt/1.32 {GOTHIC}; letter-spacing: -0.06em; }}"""),
    ("""  font: 10pt/1.36 'Times New Roman'; letter-spacing: 0; text-align: left; text-indent: -5.5mm;""",
     """  font: 10pt/1.36 'Times New Roman'; letter-spacing: -0.04em; text-align: left; text-indent: -5.5mm;"""),
    ("""f"<style>{CSS}</style><body>{head}<main>""", """f"<style>{FONT_FACES}{CSS}</style><body>{head}<main>"""),
    ("""<meta charset="utf-8"><style>{NOTE_CSS}</style><body>'""", """<meta charset="utf-8"><style>{FONT_FACES}{NOTE_CSS}</style><body>'"""),
    ("""body {{ font: 8.4pt/1.36 {SERIF}; letter-spacing: -0.015em;""", """body {{ font: 8.4pt/1.36 {SERIF}; letter-spacing: -0.04em;"""),
]
for a, b in reps:
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b)
p.write_text(s, encoding="utf-8")
print("patched", len(reps))

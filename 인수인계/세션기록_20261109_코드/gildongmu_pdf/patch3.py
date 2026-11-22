import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
p = Path(r"C:\Users\seungjun\Documents\claude_code\논문\writing\drafts\정보기술학회\build_pdf.py")
s = p.read_text(encoding="utf-8")
reps = [
    ("초안 v1 &nbsp; ★ 아직 구현하거나 측정하지 않은 부분, ○○ 재실험 후 채울 값",
     "초안 v1 (★ 아직 구현하거나 측정하지 않은 부분, ○○ 재실험 후 채울 값)"),
    ("# 크롬은 윈도우에서 글꼴 이름 끝의 -Medium을 굵기로 읽어 HY신명조·HY중고딕을 못 찾는다. PostScript 이름으로 직접 지정한다.",
     "# font-family 이름만 쓰면 HY신명조·HY중고딕이 잡히지 않고 바탕·맑은 고딕으로 대체된다. local(PostScript 이름)로 지정한다."),
]
for a, b in reps:
    assert s.count(a) == 1, a[:40]
    s = s.replace(a, b)
p.write_text(s, encoding="utf-8")

c = Path(r"C:\Users\seungjun\AppData\Local\Temp\gildongmu_pdf\check_pdf.py")
t = c.read_text(encoding="utf-8")
old = 'pages[0] = pages[0][:note_at] if note_at >= 0 else pages[0]\n'
new = old + 'pages[0] = re.sub(r"-\\d-$", "", pages[0])\n'
assert t.count(old) == 1
t = t.replace(old, new)
old2 = 'for word in ["딥또", "Dipto", "diptobiswas", "초안메모", "LOOP_V2"]:'
new2 = 'report("용지 190x260mm", all(abs(p.rect.width * 25.4 / 72 - 190) < 0.5 and abs(p.rect.height * 25.4 / 72 - 260) < 0.5 for p in doc))\nreport("깨진 글자(빈 네모) 없음", "\\u00a0" not in raw and "\\ufffd" not in raw)\n' + old2
assert t.count(old2) == 1
t = t.replace(old2, new2)
c.write_text(t, encoding="utf-8")
print("patched")

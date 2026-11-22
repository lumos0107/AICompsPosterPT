import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
p = Path(r"C:\Users\seungjun\Documents\claude_code\논문\writing\drafts\정보기술학회\build_pdf.py")
s = p.read_text(encoding="utf-8")
reps = [
 # 수식 판정: pandoc은 span 없이 math display=block으로 낸다
 ('''        if n.name == "p" and n.select_one("span.math.display"):
            out.append(f'<div class="eq"><div>{n.select_one("math")}</div><div class="eq-no">({tags[eq_no]})</div></div>')''',
  '''        if n.name == "p" and n.find("math", attrs={"display": "block"}):
            out.append(f'<div class="eq"><div>{n.find("math")}</div><div class="eq-no">({tags[eq_no]})</div></div>')'''),
 # 캡션 판정: "표 2는 ..." 같은 본문 문단을 캡션으로 오인하지 않게
 ('''        elif n.name == "p" and n.get_text().startswith("표 "):''',
  '''        elif n.name == "p" and n.find("strong") and re.match(r"표 \d+\.", n.get_text()):'''),
 # 양식처럼 글자 단위 줄바꿈
 ('''  word-break: keep-all; overflow-wrap: break-word; font-synthesis: none;
}}''', '''  word-break: normal; overflow-wrap: break-word; font-synthesis: none;
}}
.title, .authors, .title-en, .kw, h2, h3, .cap, table, .placeholder, .tempnote {{ word-break: keep-all; }}'''),
]
for a, b in reps:
    assert s.count(a) == 1, a[:40]
    s = s.replace(a, b)
p.write_text(s, encoding="utf-8")
print("ok")

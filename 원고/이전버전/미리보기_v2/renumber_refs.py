"""원고의 [키] 인용과 참고문헌 목록을 본문 첫 인용 순서로 번호를 매긴다. 실행: python -I renumber_refs.py <원고.md>"""
import re, sys
from pathlib import Path
p = Path(sys.argv[1]); s = p.read_text(encoding="utf-8")
body, rest = s.split("## 참 고 문 헌", 1)
refs_part, tail = rest.split("\n---\n", 1)
entries = re.findall(r"^\[([A-Za-z0-9]+)\] (.+)$", refs_part, flags=re.M)
emap = dict(entries)
order = []
for k in re.findall(r"\[([A-Za-z0-9]+)\]", body):
    if k in emap and k not in order:
        order.append(k)
missing = [k for k, _ in entries if k not in order]
if missing: print("본문에 인용 안 된 문헌:", missing)
num = {k: str(i + 1) for i, k in enumerate(order)}
body = re.sub(r"\[([A-Za-z0-9]+)\]", lambda m: f"[{num[m.group(1)]}]" if m.group(1) in num else m.group(0), body)
new_refs = "\n\n" + "\n\n".join(f"[{num[k]}] {emap[k]}" for k in order) + "\n\n"
p.write_text(body + "## 참 고 문 헌" + new_refs + "---\n" + tail, encoding="utf-8")
print("순서:", " ".join(f"{num[k]}={k}" for k in order))

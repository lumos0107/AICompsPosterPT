import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\seungjun\Documents\claude_code\논문\writing\drafts\정보기술학회")
import re, build_pdf as b, fitz
from bs4 import BeautifulSoup, Tag
md = b.SRC.read_text(encoding="utf-8").split("## 초안 메모")[0]
md = re.sub(r"\s*\tag\{\d+\}", "", md)
soup = BeautifulSoup(b.to_html(md), "html.parser")
nodes = [n for n in soup.children if isinstance(n, Tag)]
i = next(k for k, n in enumerate(nodes) if n.name == "h2" and n.get_text().replace(" ", "") == "참고문헌")
for n in nodes[i+1:]:
    t = n.get_text()
    if not t.startswith("["):
        print(n.name, repr(t[:90]))

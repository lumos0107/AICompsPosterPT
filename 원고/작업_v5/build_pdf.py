"""논문_정보기술학회_v1.md를 학술대회 양식 모양의 PDF로 만든다.

실행: python -I build_pdf.py
양식 수치(학술대회논문양식_표준형식.hwp에서 측정): 용지 190x260mm, 본문 x 20~170mm, y 27.5~242.5mm,
단 폭 71mm, 단 간격 8mm, 첫 쪽 아래 전체 폭에 소속과 사사.
휴먼명조·휴먼고딕은 한글 전용 글꼴(HFT)이라 HY신명조·HY중고딕으로 대체한다. 장평 90%는 적용하지 못한다.
'초안 메모' 절은 PDF에 넣지 않는다.
"""
import base64
import io
import re
import subprocess
import sys
from pathlib import Path

import fitz
from bs4 import BeautifulSoup, NavigableString, Tag
from PIL import Image
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
# 실행: python -I build_pdf.py [원고 파일명]  (생략하면 v1)
SRC = HERE / (sys.argv[1] if len(sys.argv) > 1 else "논문_정보기술학회_v1.md")
OUT = SRC.with_suffix(".pdf")
if HERE.name.startswith("작업_v"):   # 11/11 폴더 정리(v5부터 작업_v5): 작업 원본은 원고/작업_v4, 최신 PDF는 원고/ 맨 위에 둔다
    OUT = HERE.parent / OUT.name
VER = re.search(r"_(v\d+)\.md$", SRC.name).group(1)
FLAGS = sys.argv[2:]
JANG90 = "--jang90" in FLAGS   # 장평 90% 효과 측정용 PDF를 따로 만든다
DRAFT_LABEL = ("초안 v1 (★ 아직 구현하거나 측정하지 않은 부분, ○○ 재실험 후 채울 값)" if VER == "v1"
               else f"초안 {VER} (★ 아직 하지 않은 부분)")
if VER in ("v4", "v5"):
    DRAFT_LABEL = ""   # v4는 제출본처럼 맨 위 초안 표시를 뺀다(사용자 11/11)
WIDE_TABLES = {"2", "3"}  # 7열이라 2단 안에 들어가지 않는 표
if VER != "v1":
    WIDE_TABLES = {"1", "2", "3"}  # v2부터 표 1도 전체 폭(단 안에서는 줄바꿈이 많아 길어짐)
WIDE_FIGS = set()
if VER in ("v4", "v5"):   # v4: 표 3(행렬형)은 단 안, 그림 3·4·5(지도 여러 칸)는 전체 폭. 그림 2(반환점 예시, 11/11 추가)는 단 안
    WIDE_TABLES, WIDE_FIGS = set(), set()   # 표·그림 모두 양식대로 한 단 폭(사용자 11/11). 전체 폭 판은 그림_v4/*_전체폭.png
FIG2_CROP_TOP = 60 if VER == "v1" else 0  # v1 임시 그림 맨 위의 내부 실험 제목을 잘라 낸다(px). v2부터 원고용 그림이라 자르지 않음
FIRST_PAGE_BOTTOM_MM = 35  # 첫 쪽은 소속·사사 자리만큼 아래를 비운다
NOTE_HEIGHT_MM = 19  # 소속 2줄 + 사사 2줄

# font-family 이름만 쓰면 HY신명조·HY중고딕이 잡히지 않고 바탕·맑은 고딕으로 대체된다. local(PostScript 이름)로 지정한다.
FONT_FACES = """
@font-face { font-family: 'KR Serif'; src: local('H2mjsM'), local('HY신명조'); }
@font-face { font-family: 'KR Gothic'; src: local('H2gtrM'), local('HY중고딕'); }
"""
SERIF = "'Times New Roman','KR Serif',serif"
GOTHIC = "'Times New Roman','KR Gothic',sans-serif"
HEAD_GOTHIC = "'KR Gothic',sans-serif"
DOTUM = "'Dotum','돋움',sans-serif"
TITLE_EN = "'HYMyeongJo-Extra','HY견명조',serif"

CSS = f"""
@page {{
  size: 190mm 260mm;
  margin: 27.5mm 20mm 17.5mm 20mm;
  @top-center {{
    content: "- 2026 한국정보기술학회 추계 종합학술대회 논문집 -";
    font: 9.2pt {DOTUM}; vertical-align: top; padding-top: 16.8mm;
  }}
  @bottom-center {{
    content: "- " counter(page) " -";
    font: 10pt 'Times New Roman'; vertical-align: top; padding-top: 4mm;
  }}
}}
@page :first {{
  margin-bottom: {FIRST_PAGE_BOTTOM_MM}mm;
  @bottom-center {{
    content: "- " counter(page) " -";
    font: 10pt 'Times New Roman'; vertical-align: top; padding-top: {FIRST_PAGE_BOTTOM_MM - 13.5}mm;
  }}
}}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; }}
body {{
  font: 10pt/1.5 {SERIF}; color: #000; letter-spacing: -0.06em;
  word-break: normal; overflow-wrap: break-word; font-synthesis: none;
}}
.title, .authors, .title-en, .kw, h2, h3, .cap, table, .placeholder, .tempnote {{ word-break: keep-all; }}
p {{ margin: 0; }}
strong {{ font-weight: normal; }}
math {{ font-family: 'Cambria Math', math; letter-spacing: 0; }}

.draft {{ font: 7.8pt/1.3 {HEAD_GOTHIC}; color: #C2410C; text-align: center; margin-bottom: 2.5mm; letter-spacing: 0; }}
.title {{ font: 17pt/1.28 {SERIF}; text-align: center; margin: 0 0 3mm; letter-spacing: -0.07em; }}
.authors {{ font: 11pt/1.4 {DOTUM}; text-align: center; margin-bottom: 4mm; letter-spacing: 0.05em; }}
.title-en {{ font: 15pt/1.25 {TITLE_EN}; text-align: center; margin: 0 4mm 3mm; letter-spacing: -0.07em; }}
.authors-en {{ font: 10pt/1.4 'Times New Roman'; text-align: center; letter-spacing: 0.05em; margin-bottom: 5mm; }}
.abs-h {{ font: 10pt/1.4 {DOTUM}; text-align: center; margin: 3.5mm 0 2mm; letter-spacing: 0; }}
.abs {{ margin: 0 5mm; font-size: 9.2pt; line-height: 1.5; text-align: justify; text-indent: 1em; }}
.abs.en {{ letter-spacing: -0.04em; word-break: normal; }}
.kw-h {{ font-size: 9.2pt; text-align: center; margin-top: 3mm; letter-spacing: 0; }}
.kw {{ font-size: 9.2pt; text-align: center; letter-spacing: 0; margin-bottom: 5mm; }}

main {{ column-count: 2; column-gap: 8mm; column-fill: auto; }}
main p {{ text-align: justify; text-indent: 1em; orphans: 2; widows: 2; }}
h2 {{ font: normal 11pt/1.4 {HEAD_GOTHIC}; text-align: center; margin: 6mm 0 3.5mm; break-after: avoid; letter-spacing: -0.06em; }}
h3 {{ font: normal 11pt/1.4 {HEAD_GOTHIC}; margin: 3.5mm 0 1.5mm; break-after: avoid; letter-spacing: -0.06em; }}
main > h2:first-child {{ margin-top: 0; }}

.eq {{ display: flex; align-items: center; justify-content: space-between; gap: 2mm; font-size: 9pt; margin: 2mm 0; break-inside: avoid; }}
.eq-no {{ flex: none; font-family: 'Times New Roman'; letter-spacing: 0; }}

.cap {{ font: 9pt/1.32 {GOTHIC}; letter-spacing: -0.06em; }}
.tbl {{ margin: 3mm 0; break-inside: avoid; }}
.tbl.wide {{ column-span: all; margin: 3mm 0 4mm; }}
.tbl .cap {{ margin-bottom: 1.2mm; }}
.tnote {{ font: 8pt/1.3 {GOTHIC}; letter-spacing: -0.01em; margin-top: 0.8mm; }}
table {{ width: 100%; border-collapse: collapse; font: 8pt/1.3 {GOTHIC}; letter-spacing: -0.01em; }}
th, td {{ border: 0.6pt solid #000; padding: 0.7mm 1mm; font-weight: normal; }}
th {{ text-align: center !important; }}

figure {{ margin: 3mm 0; break-inside: avoid; }}
figure .cap {{ text-align: center; margin-top: 1.2mm; }}
figure img {{ width: 100%; display: block; }}
figure.wide {{ column-span: all; margin: 3mm 0 4mm; }}
.placeholder {{
  border: 0.6pt dashed #C2410C; padding: 5mm 3mm; font: 8pt/1.4 {HEAD_GOTHIC};
  color: #444; text-align: center; letter-spacing: -0.01em;
}}
.tempnote {{ font: 7.5pt/1.3 {HEAD_GOTHIC}; color: #C2410C; text-align: center; margin-top: 1mm; }}

.refs p {{
  font: 10pt/1.36 'Times New Roman'; letter-spacing: -0.04em; text-align: left; text-indent: -5.5mm;
  padding-left: 5.5mm; word-break: normal; overflow-wrap: anywhere; margin-bottom: 0.5mm;
}}
.flag {{ color: #C2410C; font-size: 0.8em; letter-spacing: -0.02em; }}
.blank {{ color: #C2410C; letter-spacing: 0; }}
"""

NOTE_CSS = f"""
@page {{ size: 150mm {NOTE_HEIGHT_MM}mm; margin: 0; }}
html, body {{ margin: 0; padding: 0; }}
body {{ font: 8.4pt/1.36 {SERIF}; letter-spacing: -0.04em; color: #000; word-break: keep-all; }}
.rule {{ width: 58mm; border-top: 0.6pt solid #000; margin-bottom: 1.2mm; }}
p {{ margin: 0 0 0 1mm; }}
"""


def to_html(md: str) -> str:
    done = subprocess.run(
        ["pandoc", "-f", "markdown-implicit_figures-smart", "-t", "html5", "--mathml", "--wrap=preserve", "--columns=100000"],
        input=md.encode("utf-8"), capture_output=True, check=True,
    )
    return done.stdout.decode("utf-8")


def fig_data_uri(src: str) -> str:
    img = Image.open((SRC.parent / src).resolve())
    img = img.crop((0, FIG2_CROP_TOP, img.width, img.height))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def mark_flags(soup: BeautifulSoup) -> None:
    """초안 표시([★...], ○○)에 색을 입힌다."""
    pattern = re.compile(r"(\[★[^\]]*\]|○○)")
    for text in list(soup.find_all(string=pattern)):
        if text.find_parent("math"):
            continue
        parts = pattern.split(str(text))
        new_nodes = []
        for part in parts:
            if not part:
                continue
            if part == "○○" or part.startswith("[★"):
                span = soup.new_tag("span", attrs={"class": "blank" if part == "○○" else "flag"})
                span.string = part
                new_nodes.append(span)
            else:
                new_nodes.append(NavigableString(part))
        for node in new_nodes:
            text.insert_before(node)
        text.extract()


def inner(tag: Tag) -> str:
    return "".join(str(c) for c in tag.contents)


def caption(tag: Tag) -> str:
    return "<br>".join(inner(s) for s in tag.find_all("strong"))


def build_body(nodes: list, tags: list) -> str:
    out, k, eq_no = [], 0, 0
    while k < len(nodes):
        n = nodes[k]
        if n.name == "p" and n.find("math", attrs={"display": "block"}):
            out.append(f'<div class="eq"><div>{n.find("math")}</div><div class="eq-no">({tags[eq_no]})</div></div>')
            eq_no += 1
        elif n.name == "p" and n.find("img"):
            note_block = nodes[k + 1]
            paras = note_block.find_all("p")
            k += 1
            fno = re.match(r"\s*그림 (\d+)", paras[-1].get_text())
            fcls = ' class="wide"' if fno and fno.group(1) in WIDE_FIGS else ""
            out.append(
                f'<figure{fcls}><img src="{fig_data_uri(n.find("img")["src"])}">'
                + ('<div class="tempnote">★ 임시 그림 (재실험 후 교체)</div>' if VER == "v1" else '')
                + f'<div class="cap">{caption(paras[-1])}</div></figure>'
            )
        elif n.name == "blockquote":
            paras = n.find_all("p")
            head = paras[0].find("strong").extract().get_text()
            out.append(
                f'<figure><div class="placeholder">{head}<br>{inner(paras[0]).strip()}</div>'
                f'<div class="cap">{caption(paras[-1])}</div></figure>'
            )
        elif n.name == "p" and n.find("strong") and re.match(r"표 \d+\.", n.get_text()):
            num = re.match(r"표 (\d+)", n.get_text()).group(1)
            cls = "tbl wide" if num in WIDE_TABLES else "tbl"
            note = ""
            if k + 2 < len(nodes) and nodes[k + 2].name == "p" and nodes[k + 2].get_text().startswith("주:"):
                note = f'<div class="tnote">{inner(nodes[k + 2])}</div>'   # 표 바로 아래 '주:' 문단은 표 안에 작은 글씨로
                k += 1
            out.append(f'<div class="{cls}"><div class="cap">{caption(n)}</div>{nodes[k + 1 - (1 if note else 0)]}{note}</div>')
            k += 1
        else:
            out.append(str(n))
        k += 1
    return "\n".join(out)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    md = SRC.read_text(encoding="utf-8").split("## 초안 메모")[0]
    tags = re.findall(r"\\tag\{(\d+)\}", md)
    md = re.sub(r"\s*\\tag\{\d+\}", "", md)
    soup = BeautifulSoup(to_html(md), "html.parser")
    mark_flags(soup)
    nodes = [n for n in soup.children if isinstance(n, Tag)]

    def at(text: str) -> int:
        return next(i for i, n in enumerate(nodes) if n.name == "h2" and n.get_text().replace(" ", "") == text)

    abs_ko, abs_en = nodes[at("요약") + 1], nodes[at("Abstract") + 1]
    kw_head, kw = nodes[at("Abstract") + 2], nodes[at("Abstract") + 3]
    start, ref_at = at("Ⅰ.서론"), at("참고문헌")
    tail = nodes[ref_at + 1:]
    refs = [n for n in tail if n.name == "p" and n.get_text().startswith("[")]
    notes = [n for n in tail if n.name == "p" and not n.get_text().startswith("[")]
    affil = notes[0].get_text().strip().split("\n")
    ack = notes[1].get_text().strip()

    head = f"""
{f'<div class="draft">{DRAFT_LABEL}</div>' if DRAFT_LABEL else ''}
<div class="title">{inner(nodes[0])}</div>
<div class="authors">{inner(nodes[2])}</div>
<div class="title-en">{inner(nodes[1].find("strong"))}</div>
<div class="authors-en">{inner(nodes[3])}</div>
<div class="abs-h">요 약</div><p class="abs">{inner(abs_ko)}</p>
<div class="abs-h">Abstract</div><p class="abs en">{inner(abs_en)}</p>
<div class="kw-h">{inner(kw_head.find("strong"))}</div><div class="kw">{inner(kw)}</div>
"""
    body = build_body(nodes[start:ref_at], tags)
    ref_html = '<h2>참 고 문 헌</h2><div class="refs">' + "".join(str(r) for r in refs) + "</div>"
    css = FONT_FACES + CSS
    if VER == "v1":
        body_html = f"<body>{head}<main>{body}{ref_html}</main></body>"
    else:
        # 양식처럼 1쪽 키워드 바로 아래에서 2단 서론이 시작하도록, 머리 부분을 2단 영역 안의 전체 폭 요소로 둔다.
        # (머리를 2단 영역 밖에 두면 크롬이 1쪽에 남은 23 mm 정도에 2단 영역을 시작하지 않고 다음 쪽으로 넘긴다.)
        body_html = f'<body><main><div class="head">{head}</div>{body}{ref_html}</main></body>'
        css += ".head{column-span:all} .head + h2{margin-top:0}"
    if JANG90:
        # 장평 90% 측정: 글자를 90%로 줄이는 대신 쪽 폭·단 폭·단 간격을 1/0.9배로 넓힌다. 그림은 실제 크기(단 폭의 90%)로 둔다.
        css += (f"@page{{size:{190 + 150 * (1 / 0.9 - 1):.2f}mm 260mm}} main{{column-gap:{8 / 0.9:.2f}mm}}"
                f" .abs{{margin:0 {5 / 0.9:.2f}mm}} figure img{{width:90%;margin:0 auto}}")
    page_html = (
        f'<!doctype html><html lang="ko"><meta charset="utf-8"><title>{nodes[0].get_text()}</title>'
        f"<style>{css}</style>{body_html}</html>"
    )
    note_html = (
        f'<!doctype html><html lang="ko"><meta charset="utf-8"><style>{FONT_FACES}{NOTE_CSS}</style><body>'
        '<div class="rule"></div>' + "".join(f"<p>{line}</p>" for line in affil) + f"<p>{ack}</p></body></html>"
    )

    if "--html" in FLAGS:   # 배치 시험용: 본문 HTML만 저장
        (HERE / "미리보기_v2" / "본문.html").write_text(page_html, encoding="utf-8")
        return
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(page_html)
        page.evaluate("document.fonts.ready")
        main_pdf = page.pdf(prefer_css_page_size=True, print_background=True)
        page.set_content(note_html)
        page.evaluate("document.fonts.ready")
        note_pdf = page.pdf(prefer_css_page_size=True, print_background=True)
        browser.close()

    doc = fitz.open(stream=main_pdf, filetype="pdf")
    note = fitz.open(stream=note_pdf, filetype="pdf")
    mm = 72 / 25.4
    top = 260 - FIRST_PAGE_BOTTOM_MM + 1.5
    if len(note) != 1:
        raise RuntimeError("소속·사사 칸이 넘침: NOTE_HEIGHT_MM을 늘릴 것")
    doc[0].show_pdf_page(fitz.Rect(20 * mm, top * mm, 170 * mm, (top + NOTE_HEIGHT_MM) * mm), note, 0)
    out = OUT.with_name(OUT.stem + "_장평90측정.pdf") if JANG90 else OUT
    doc.save(out, garbage=4, deflate=True)
    last = [b for b in doc[-1].get_text("blocks") if b[4].strip() and not b[4].strip().startswith("- ")]
    half = doc[-1].rect.width / 2
    fill = [max([b[3] for b in last if (b[0] < half) == left] or [0]) / 72 * 25.4 for left in (True, False)]
    print("저장:", out, "쪽 수:", len(doc), f"마지막 쪽 글 끝 위치(mm, 본문 끝 242.5) 왼쪽 단 {fill[0]:.0f}, 오른쪽 단 {fill[1]:.0f}")


if __name__ == "__main__":
    main()

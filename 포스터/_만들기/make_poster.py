"""정보기술학회 논문(원고 v5) 포스터 한글판 v1 (2026-11-13).

양식: AI융합콜로퀴움 포스터 양식의 디자인 2(파랑, 슬라이드 2), 2열. 틀(절 머리띠, 소제목, 표 선, 그림 설명)은
콜로퀴움 포스터 v42(3학년_2학기/AI웅합콜로퀴움/분석/32·36·38·54_포스터.py)와 같게 맞췄다.
숫자와 표현은 원고/작업_v5/논문_정보기술학회_v5.md 그대로(표 3은 v5 값). 원고 그림은 원고/작업_v4/그림_v4/의 PNG를 쓴다(v5와 같음).
포스터 전용 그림은 _만들기/그림/(make_fig_beam.py, make_fig_flow.py, 그림 1(a)·자료 지도 잘라낸 것).
수식은 matplotlib 수식 글꼴로 PNG를 만들어 넣는다(수식/).

출력: ../포스터_v1_한글.pptx (PDF는 to_pdf.ps1).  실행: python make_poster.py
실행 끝에 열마다 어디까지 내려왔는지 찍는다(한계 BOTTOM).
"""
import copy
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from lxml import etree
from PIL import Image, ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
POSTER = os.path.dirname(HERE)
PAPER = os.path.dirname(POSTER)
ROOT = os.path.dirname(os.path.dirname(PAPER))
TEMPLATE = os.path.join(ROOT, "3학년_2학기", "AI웅합콜로퀴움", "대회자료", "AI융합콜로퀴움_논문포스터PPT-1.pptx")
FIG = os.path.join(PAPER, "원고", "작업_v4", "그림_v4")
EQ = os.path.join(HERE, "수식")
OUT = os.path.join(POSTER, "포스터_v1_한글.pptx")

FONT = "맑은 고딕"
LANG_TAG = "ko-KR"  # 글자 언어 표시(영어판은 en-US)
DOC = dict(title="러너의 선호를 경로 비용에 반영한 목표 거리 순환 경로 생성", author="강승준, 이은, 조민영, 길준민",
           subject="AICompS 2026 (The 3rd International Conference on Artificial Intelligence and Computing Systems) 포스터")
INK, INK2, BLUE, NOTE = "191817", "52514E", "2A78D6", "6B6A64"
NAVY, PALEB, HEAD_GRAY = "014399", "E3EEFB", "C8C7C1"
DARK, THIN = "52514E", "BDBCB6"
LX, RX, CW = 0.65, 7.47, 6.36
HW, GUT = 3.06, 0.24
TOP, BOTTOM = 4.36, 21.38
BODY, CAP, SUB, FOOT = 12, 12.5, 14, 10
EXPL = 11  # 수식 기호 설명
GAP_SUB, GAP_FIG = 0.08, 0.08
LINE = 1.23  # 맑은 고딕 한 줄 높이(글자 크기 배수). PowerPoint PDF에서 잰 값 약 1.22
# 양식 슬라이드 2에서 남길 것: 배경, 절 머리띠 그림 4개, 머리글·제목·소속·바닥글, 절 제목 글상자 4개 (로고 2·5·6·7은 뺌)
KEEP = {120, 122, 124, 125, 126, 127, 128, 129, 130, 131, 134, 34, 88, 103, 118}

REG = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 100)
BOLD = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 100)


def text_width(s, size, bold=False):
    return (BOLD if bold else REG).getlength(s) / 100 * size / 72


def wrap_count(runs, size, width):
    """[(글, 굵게)]를 낱말 단위로 줄바꿈했을 때의 줄 수."""
    words = []
    for txt, bold in runs:
        parts = txt.split(" ")
        for i, w in enumerate(parts):
            words.append((w + (" " if i < len(parts) - 1 else ""), bold))
    lines, cur = 1, 0.0
    for w, bold in words:
        wd = text_width(w, size, bold)
        if cur + text_width(w.rstrip(), size, bold) > width and cur > 0:
            lines += 1
            cur = 0.0
        cur += wd
    return lines


def set_font(rpr):
    for tag in ("a:latin", "a:ea", "a:cs"):
        el = rpr.find(qn(tag))
        if el is None:
            el = rpr.makeelement(qn(tag), {})
            hl = rpr.find(qn("a:hlinkClick"))
            rpr.insert(list(rpr).index(hl), el) if hl is not None else rpr.append(el)
        el.set("typeface", FONT)


def keep_words(p):
    """한글 낱말이 줄 끝에서 잘리지 않게 한다."""
    ppr = p._p.get_or_add_pPr()
    ppr.set("latinLnBrk", "0")
    ppr.set("eaLnBrk", "1")


def replace_text(shape, lines, size=None, bold=None):
    body = shape.text_frame._txBody
    paras = body.findall(qn("a:p"))
    proto = next(p for p in paras if p.find(qn("a:r")) is not None)
    for p in paras:
        body.remove(p)
    for line in lines:
        p = copy.deepcopy(proto)
        runs = p.findall(qn("a:r"))
        for r in runs[1:]:
            p.remove(r)
        for el in p.findall(qn("a:br")) + p.findall(qn("a:fld")):
            p.remove(el)
        r = runs[0]
        r.find(qn("a:t")).text = line
        rpr = r.find(qn("a:rPr"))
        rpr.attrib.pop("err", None)
        rpr.set("lang", LANG_TAG)
        if size:
            rpr.set("sz", str(int(size * 100)))
        if bold is not None:
            rpr.set("b", "1" if bold else "0")
        set_font(rpr)
        body.append(p)


def split_sub(s):
    """'_{...}' 표시를 아래 첨자 조각으로 나눈다. [(글, 첨자 여부)]"""
    out = []
    for i, t in enumerate(re.split(r"_\{([^}]*)\}", s)):
        if t:
            out.append((t, i % 2 == 1))
    return out


def rt(s, color=INK):
    """'**굵게**'와 '_{첨자}' 표시를 글자 조각 (글, 굵게, 색, 첨자)로 나눈다."""
    out = []
    for i, t in enumerate(s.split("**")):
        for u, sub in split_sub(t):
            out.append((u, i % 2 == 1, color, sub))
    return out


def line_el(tag, width, color):
    ln = etree.Element(qn(tag), w=str(width), cap="flat", cmpd="sng", algn="ctr")
    if color is None:
        etree.SubElement(ln, qn("a:noFill"))
    else:
        fill = etree.SubElement(ln, qn("a:solidFill"))
        etree.SubElement(fill, qn("a:srgbClr"), val=color)
        etree.SubElement(ln, qn("a:prstDash"), val="solid")
    return ln


# ------------------------------------------------------------------ 수식 그림
EQUATIONS = {
    "식1": r"$p(u,v)=\ell(u,v)\left[\alpha_s\,f_s+\alpha_f\,f_f+\sum_{k\in K}\alpha_k\,f_k\right]+\alpha_c\,\kappa_c\,\mathbb{1}[v\in V_{\mathrm{sig}}]$",
    "식2": r"$c(u,v)=\ell(u,v)\left(1+\gamma\,\mathbb{1}_{\mathrm{out}}+\gamma_p\,\mathbb{1}_{\mathrm{near}}\right)+p(u,v)+c_t\,\mathbb{1}_{\mathrm{turn}}$",
}
EQ_PT = 16  # 수식 글자 크기(pt). 그림을 원래 크기(300 dpi)로 놓아 글자 크기를 맞춘다.


def make_equations():
    os.makedirs(EQ, exist_ok=True)
    plt.rcParams["mathtext.fontset"] = "stix"
    for name, tex in EQUATIONS.items():
        fig = plt.figure(figsize=(10, 1))
        fig.text(0, 0.5, tex, fontsize=EQ_PT, color="#" + INK, va="center")
        fig.savefig(os.path.join(EQ, name + ".png"), dpi=300, bbox_inches="tight", pad_inches=0.02, transparent=True)
        plt.close(fig)


# ------------------------------------------------------------------ 포스터 틀
class Poster:
    def __init__(self):
        self.prs = Presentation(TEMPLATE)
        lst = self.prs.slides._sldIdLst
        ids = list(lst)
        for sid in (ids[2], ids[0]):
            self.prs.part.drop_rel(sid.rId)
            lst.remove(sid)
        self.s = self.prs.slides[0]
        for sh in list(self.s.shapes):
            if sh.shape_id not in KEEP:
                sh._element.getparent().remove(sh._element)
        self.sh = {x.shape_id: x for x in self.s.shapes}
        # 배경 그림(그림 119)을 오른쪽 위 흰 상자를 지운 판으로 바꾼다(make_bg.py)
        bg = self.sh[120]
        part = self.s.part.related_part(bg._element.blipFill.blip.rEmbed)
        with open(os.path.join(HERE, "그림", "배경_상자없음.jpg"), "rb") as f:
            part._blob = f.read()
        self.bars = [(122, 34), (124, 88), (125, 103), (126, 118)]
        self.x, self.y = LX, TOP
        self.report = []
        self.first_sub = False

    def text(self, x, y, w, paras, name, align=None, anchor=None, h=None):
        """paras: [(글 또는 [(글, 굵게, 색)], 크기, 굵게, 색, 문단 뒤 간격pt)]. 쓴 높이(인치)를 돌려준다."""
        total = 0.0
        norm = []
        for txt, size, bold, color, after in paras:
            runs = [(txt, bold, color)] if isinstance(txt, str) else txt
            runs = [r if len(r) == 4 else (*r, False) for r in runs]
            n = wrap_count([(t, b) for t, b, _, _ in runs], size, w - 0.04)
            total += n * size * LINE / 72 + after / 72
            norm.append((runs, size, after))
        total -= norm[-1][2] / 72
        tb = self.s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h or total))
        tb.name = name
        tf = tb.text_frame
        tf.word_wrap = True
        if anchor:
            tf.vertical_anchor = anchor
        for m in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
            setattr(tf, m, 0)
        for i, (runs, size, after) in enumerate(norm):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.space_after = Pt(after)
            p.line_spacing = 1.0
            keep_words(p)
            if align:
                p.alignment = align
            for t, b, c, sub in runs:
                r = p.add_run()
                r.text = t
                r.font.size, r.font.bold, r.font.color.rgb = Pt(size), b, RGBColor.from_string(c)
                rpr = r._r.get_or_add_rPr()
                rpr.set("lang", LANG_TAG)
                if sub:
                    rpr.set("baseline", "-25000")
                set_font(rpr)
        return total

    # --- 절 머리띠(양식 그림을 옮겨 쓴다)
    def section(self, title, column=None):
        if column == "right":
            self.report.append(("왼쪽", self.y))
            self.x, self.y = RX, TOP
        elif self.y > TOP:
            self.y += 0.16
        bar, label = self.bars.pop(0)
        b, l = self.sh[bar], self.sh[label]
        b.left, b.top = Inches(self.x), Inches(self.y)
        l.left, l.top, l.width = Inches(self.x + 0.14), Inches(self.y + 0.02), Inches(6.0)
        replace_text(l, [title])
        self.y += 0.34 + 0.12
        self.first_sub = True

    def body(self, s, name, after=0.07, size=BODY, w=None, x=None):
        x = self.x if x is None else x
        self.y += self.text(x, self.y, w or CW, [(rt(s), size, False, INK, 0)], name) + after

    def bullets_at(self, x, y, w, items, name, size=BODY):
        """• 글머리 목록을 (x, y)에 놓는다. 둘째 줄부터 들여 쓴다. 쓴 높이를 돌려준다."""
        ind, y0 = 0.2, y
        for k, s in enumerate(items):
            self.text(x, y, ind, [("•", size, True, BLUE, 0)], f"{name} 점 {k + 1}")
            y += self.text(x + ind, y, w - ind, [(rt(s), size, False, INK, 0)], f"{name} {k + 1}") + 0.05
        return y - y0 - 0.05

    def bullets(self, items, name, after=0.07, size=BODY):
        self.y += self.bullets_at(self.x, self.y, CW, items, name, size) + after

    # --- 본론 소제목: 번호(파랑) + 제목 + 가는 선
    def sub_at(self, x, y, w, num, title):
        h = self.text(x, y, w, [([(num + "  ", True, BLUE), (title, True, INK)], SUB, True, INK, 0)], f"소제목 {num}")
        r = self.s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y + h + 0.015), Inches(w), Inches(0.014))
        r.fill.solid()
        r.fill.fore_color.rgb = RGBColor.from_string(NAVY)
        r.line.fill.background()
        r.shadow.inherit = False
        r.name = "소제목 선"
        return h + 0.08

    def sub(self, num, title):
        if not self.first_sub:
            self.y += GAP_SUB
        self.first_sub = False
        self.y += self.sub_at(self.x, self.y, CW, num, title)

    # --- 그림
    def picture(self, x, y, w, png, alt, folder=FIG):
        path = os.path.join(folder, png)
        if not os.path.exists(path):
            path = os.path.join(HERE, "그림", png)
        with Image.open(path) as im:
            ratio = im.height / im.width
        pic = self.s.shapes.add_picture(path, Inches(x), Inches(y), width=Inches(w))
        pic.name = png
        pic._element.find(".//" + qn("p:cNvPr")).set("descr", alt)
        return w * ratio

    def fig_note(self, x, y, w, tag, msg):
        return self.text(x, y, w, [([(tag + "  ", True, INK2), (msg, False, INK2)], FOOT, False, INK2, 0)], f"{tag} 설명")

    def figure(self, png, tag, msg, w=CW):
        x = self.x + (CW - w) / 2
        self.y += self.picture(x, self.y, w, png, tag + " " + msg)
        self.y += 0.04 + self.fig_note(self.x, self.y + 0.04, CW, tag, msg) + GAP_FIG

    def flow(self, items, strong=(), h=0.56, size=10.5):
        """가로 흐름 상자. items: [(첫 줄, 둘째 줄)]. strong 칸은 파랑 바탕·흰 글자, 나머지는 옅은 회색. 화살표로 잇는다."""
        n, gap = len(items), 0.2
        w = (CW - gap * (n - 1)) / n
        for i, pair in enumerate(items):
            txt, strong_i = "\n".join(pair), i in strong
            x = self.x + i * (w + gap)
            for line in txt.split("\n"):
                if text_width(line, size, True) > w - 0.06:
                    print(f"  주의: 흐름 칸이 좁음 {line}")
            box = self.s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(self.y), Inches(w), Inches(h))
            box.name = f"흐름 {i + 1}"
            box.adjustments[0] = 0.12
            box.fill.solid()
            box.fill.fore_color.rgb = RGBColor.from_string(BLUE if strong_i else "EEEEE9")
            box.line.fill.background()
            style = box._element.find(qn("p:style"))
            if style is not None:
                box._element.remove(style)
            tf = box.text_frame
            tf.word_wrap = True
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf.margin_top = tf.margin_bottom = 0
            tf.margin_left = tf.margin_right = Inches(0.02)
            for j, line in enumerate(txt.split("\n")):
                p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
                p.alignment = PP_ALIGN.CENTER
                p.line_spacing = 0.95
                keep_words(p)
                r = p.add_run()
                r.text = line
                r.font.size, r.font.bold = Pt(size), j == 0
                r.font.color.rgb = RGBColor.from_string("FFFFFF" if strong_i else INK)
                rpr = r._r.get_or_add_rPr()
                rpr.set("lang", LANG_TAG)
                set_font(rpr)
            if i < n - 1:
                c = self.s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x + w + 0.03), Inches(self.y + h / 2),
                                                Inches(x + w + gap - 0.03), Inches(self.y + h / 2))
                c.name = f"흐름 화살표 {i + 1}"
                c.line.color.rgb = RGBColor.from_string(INK2)
                c.line.width = Pt(1.5)
                ln = c.line._get_or_add_ln()
                ln.append(ln.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"}))
        self.y += h

    def equation(self, name, num):
        """옅은 파랑 띠 가운데에 수식 그림, 오른쪽 끝에 번호."""
        path = os.path.join(EQ, name + ".png")
        with Image.open(path) as im:
            w, h = im.width / 300, im.height / 300
        bh = h + 0.14
        r = self.s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(self.x), Inches(self.y), Inches(CW), Inches(bh))
        r.fill.solid()
        r.fill.fore_color.rgb = RGBColor.from_string(PALEB)
        r.line.fill.background()
        r.shadow.inherit = False
        r.name = "수식 바탕"
        if w > CW - 0.7:
            print(f"  주의: 수식이 넓음 {name} {w:.2f}")
        self.picture(self.x + (CW - 0.4 - w) / 2, self.y + 0.07, w, name + ".png", f"수식 ({num})", folder=EQ)
        self.text(self.x + CW - 0.5, self.y, 0.42, [(f"({num})", BODY, False, INK, 0)], f"수식 번호 {num}",
                  align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE, h=bh)
        self.y += bh + 0.08

    # --- 표(맨 위·아래와 머리줄 아래는 진한 선, 안쪽은 가는 선, 머리줄 회색)
    def table(self, x, y, widths, rows, name, size=10.5, pad=0.07, left_cols=(0,), hl_col=None, hl_rows=()):
        n, m = len(rows), len(widths)
        heights = [max(c.count("\n") + 1 for c in row) * size * LINE / 72 + pad for row in rows]
        gf = self.s.shapes.add_table(n, m, Inches(x), Inches(y), Inches(sum(widths)), Inches(sum(heights)))
        gf.name = name
        t = gf.table
        t.first_row = t.horz_banding = False
        t._tbl.tblPr.find(qn("a:tableStyleId")).text = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"  # 양식 없음
        for j, w in enumerate(widths):
            t.columns[j].width = Inches(w)
        for i in range(n):
            t.rows[i].height = Inches(heights[i])
            for j in range(m):
                c = t.cell(i, j)
                c.margin_left = c.margin_right = Inches(0.05)
                c.margin_top = c.margin_bottom = Inches(0.01)
                c.vertical_anchor = MSO_ANCHOR.MIDDLE
                head = i == 0
                hi = (not head) and (j == hl_col or i in hl_rows)
                for k, line in enumerate(rows[i][j].split("\n")):
                    bold = head or hi
                    if text_width(re.sub(r"_\{([^}]*)\}", r"\1", line), size, bold) > widths[j] - 0.1:
                        print(f"  주의: 표 칸이 좁음 [{name}] {line}")
                    p = c.text_frame.paragraphs[0] if k == 0 else c.text_frame.add_paragraph()
                    p.alignment = PP_ALIGN.LEFT if j in left_cols else PP_ALIGN.CENTER
                    p.line_spacing = 1.0
                    for piece, sub in split_sub(line):
                        r = p.add_run()
                        r.text = piece
                        r.font.size, r.font.bold = Pt(size), bold
                        r.font.color.rgb = RGBColor.from_string(INK)
                        rpr = r._r.get_or_add_rPr()
                        rpr.set("lang", LANG_TAG)
                        if sub:
                            rpr.set("baseline", "-25000")
                        set_font(rpr)
                if head or hi:
                    c.fill.solid()
                    c.fill.fore_color.rgb = RGBColor.from_string(HEAD_GRAY if head else PALEB)
                else:
                    c.fill.background()
                tcpr = c._tc.get_or_add_tcPr()
                top_dark, bottom_dark = i in (0, 1), i in (0, n - 1)
                items = [line_el("a:lnL", 6350, THIN if j > 0 else None),
                         line_el("a:lnR", 6350, THIN if j < m - 1 else None),
                         line_el("a:lnT", 12700 if top_dark else 6350, DARK if top_dark else THIN),
                         line_el("a:lnB", 12700 if bottom_dark else 6350, DARK if bottom_dark else THIN)]
                for k2, el in enumerate(items):
                    tcpr.insert(k2, el)  # 스키마 순서상 채우기보다 앞
        return sum(heights)

    def full_table(self, tag, msg, widths, rows, note=None, **kw):
        if abs(sum(widths) - CW) > 0.01:
            print(f"  주의: {tag} 너비 합 {sum(widths):.2f} ≠ {CW}")
        self.y += self.text(self.x, self.y, CW, [([(tag + "  ", True, BLUE), (msg, True, INK)], CAP, True, INK, 0)], f"{tag} 제목") + 0.04
        self.y += self.table(self.x, self.y, widths, rows, tag, **kw)
        if note:
            self.y += 0.04 + self.text(self.x, self.y + 0.04, CW, [(note, FOOT, False, NOTE, 0)], f"{tag} 주")
        self.y += GAP_FIG

    # --- 머리글
    def header(self):
        sh = self.sh
        replace_text(sh[127], ["AICompS 2026  |  The 3rd International Conference on Artificial Intelligence and Computing Systems"])
        sh[127].width = Inches(13.4)  # 오른쪽 머리글(128)이 비어 있어 넓게 쓴다
        replace_text(sh[128], [" "])  # 소속은 저자 줄과 오른쪽 상자에 있으므로 비운다
        replace_text(sh[129], ["러너의 선호를 경로 비용에 반영한", "목표 거리 순환 경로 생성"], size=44)
        sh[129].left, sh[129].top, sh[129].width = Inches(0.4), Inches(0.66), Inches(13.9)
        for p in sh[129].text_frame.paragraphs:
            p.line_spacing = 0.9
        replace_text(sh[130], ["Generating Target-Distance Loop Routes by Incorporating Runner Preferences into Route Costs"], size=15)
        sh[130].left, sh[130].top, sh[130].width = Inches(0.4), Inches(2.08), Inches(10.3)
        replace_text(sh[131], ["강승준, 이은, 조민영, 길준민(교신저자) | 제주대학교 컴퓨터공학과"], size=14)
        sh[131].left, sh[131].top = Inches(0.3), Inches(2.42)
        replace_text(sh[134], ["러너의 선호를 경로 비용에 반영한 목표 거리 순환 경로 생성"])
        # 오른쪽 위 로고 상자: 배경의 상자는 지우고(make_bg.py) 더 위에 도형으로 그린다. 로고만, 여백은 좁게.
        lw = 2.6
        with Image.open(os.path.join(HERE, "그림", "제주대로고.png")) as im_:
            lh = lw * im_.height / im_.width
        bx, by, bw, bh = 14.05 - lw - 0.24, 0.5, lw + 0.24, lh + 0.2
        box = self.s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(bx), Inches(by), Inches(bw), Inches(bh))
        box.name = "소속 상자"
        box.adjustments[0] = 0.06
        box.fill.solid()
        box.fill.fore_color.rgb = RGBColor.from_string("FFFFFF")
        box.line.color.rgb = RGBColor.from_string("24447D")
        box.line.width = Pt(1.5)
        box.shadow.inherit = False
        style = box._element.find(qn("p:style"))
        if style is not None:
            box._element.remove(style)
        self.picture(bx + 0.12, by + 0.1, lw, "제주대로고.png", "제주대학교 로고")
        # 사사: 왼쪽 아래 파랑 띠(바닥글 상자 왼쪽 빈 곳)에 흰 글씨로
        self.text(0.35, 21.6, 4.2, [("첨단분야 혁신융합대학사업(교육부·한국연구재단) 지원", 9.5, False, "FFFFFF", 0)],
                  "사사", anchor=MSO_ANCHOR.MIDDLE, h=0.25)

    def finish(self):
        self.report.append(("오른쪽", self.y))
        for col, y in self.report:
            print(f"{col} 열 끝 y = {y:.2f} (한계 {BOTTOM})" + ("  넘침!" if y > BOTTOM else f"  남음 {BOTTOM - y:.2f}"))
        for el in self.s.shapes._spTree.iter():
            if el.tag in (qn("a:latin"), qn("a:ea"), qn("a:cs")):
                el.set("typeface", FONT)
        cp = self.prs.core_properties
        cp.title, cp.author, cp.subject = DOC["title"], DOC["author"], DOC["subject"]
        cp.keywords = cp.comments = ""
        cp.last_modified_by = "강승준"
        self.prs.save(OUT)
        print("저장:", OUT)


# ------------------------------------------------------------------ 내용 (원고 v5를 핵심만 개조식으로)
def intro(P):
    P.section("서론")
    P.bullets([
        "**문제 1**  러닝은 정한 거리를 달려 돌아옴 → 길 안내로는 코스를 얻기 어려움",
        "**문제 2**  러너는 신호 대기·잦은 회전을 꺼림 → 낯선 곳에선 피하기 어려움",
        "**예**  제주 도심에서 선호를 반영하지 않은 경로: km당 신호 교차로 **2.7곳**",
        "**한계점**  기존 고정 길이 순환 경로 연구는 길이·모양 중심 → 선호 조절 어려움",
        "**제안 방법**  러너의 선호를 경로 비용에 반영한 순환 경로 생성(그림 1)",
    ], "서론", after=0)


def method(P):
    P.section("본론 ① 제안 방법")
    P.sub("1", "전체 구조")
    P.figure("그림1_구조_포스터.png", "그림 1", "제안 방법의 구조(T: 목표 거리, 파랑: 선호 비용 p(식 (1)) 사용)")

    P.sub("2", "선호 비용")
    P.bullets(["싫어하는 길일수록 길이를 더 길게 쳐서 피하게 함(기호는 표 1)"], "선호 비용 설명", after=0.06)
    P.equation("식1", 1)
    rows = [["기호", "뜻"],
            ["ℓ(u,v)", "구간 (u,v)의 길이(m)"],
            ["α", "항목별 가중치(0이면 고려하지 않음)"],
            ["f_{s}", "경사: 가파를수록 큰 벌점"],
            ["κ_{c}, 𝟙[v∈V_{sig}]", "신호 교차로: 지날 때마다 벌점(약 100 m)"],
            ["f_{f}", "편의시설: 화장실·편의점·공원에서 멀수록 큰 벌점"],
            ["f_{k}, k∈K", "길의 성질 K = {조명, 물가, 보도, 녹지, 조용한 길}: 그 성질이 없으면 벌점"]]
    P.full_table("표 1", "식 (1)의 기호(f는 0~1의 벌점 정도)", [1.5, 4.86], rows, left_cols=(0, 1), size=10, pad=0.06,
                 note="예: 조명 가중치 3 → 조명 없는 길 100 m에 300 m를 더함. "
                      "자료: 수치지형도(신호등·조명·도로·해안선·하천·인도), 고도 격자, 제주시 도시공원, 편의시설 2,289곳")

    P.sub("3", "진출 구간: 다양성 빔 탐색")
    P.figure("진출구간_빔.png", "그림 2", "그림 1의 ② 진출 구간: 빔 9개가 안내점 방향 ±45°로 나뉘어 출발, 지나온 거리 0.51T에서 멈춤"
             "(개념도, 겹침: 후보 20 m 안을 지난 다른 빔의 비율)")

    P.sub("4", "반환 구간: 최소 비용 탐색")
    P.bullets([
        "빔 탐색으로 돌아오면 거리를 못 맞추거나 나간 길로 그대로 돌아옴",
        "→ 반환 구간은 비용이 가장 작은 길을 찾는 Dijkstra 탐색으로 구함",
        "반환점: 후보마다 다시 탐색, 오차 ±10% 안에서 같은 길을 가장 적게 달린 후보(그림 3)",
    ], "반환 구간", after=0.06)
    P.equation("식2", 2)
    # 왼쪽: 식 (2)의 간선 비용 표, 오른쪽: 그림 3
    top, fw = P.y, 3.6
    wl = CW - fw - GUT
    rows = [["기호", "뜻"],
            ["ℓ(u,v)", "간선 길이(m)"],
            ["p(u,v)", "선호 비용(식 (1))"],
            ["γ·𝟙_{out}", "나간 길을 다시 달리면\n벌점(γ = 5)"],
            ["γ_{p}·𝟙_{near}", "나간 길 100 m 안\n옆길이면 벌점(γ_{p} = 3)"],
            ["c_{t}·𝟙_{turn}", "45° 넘게 꺾으면\n벌점(c_{t} = 60 m)"]]
    hl = P.text(P.x, top, wl, [([("표 2  ", True, BLUE), ("식 (2)의 기호", True, INK)], CAP, True, INK, 0)], "표 2 제목") + 0.04
    hl += P.table(P.x, top + hl, [0.92, 1.6], rows, "표 2", size=9.5, pad=0.05, left_cols=(0, 1))
    xf = P.x + wl + GUT
    hf = P.picture(xf, top, fw, "그림2_반환점.png", "그림 3 반환점 선택의 예")
    hf += 0.04 + P.fig_note(xf, top + hf + 0.04, fw, "그림 3", "그림 1의 ③·④: 반환점 선택의 예(가상 도로, 한 칸 100 m, 목표 2,600 m, P1~P5: 반환점 후보)")
    P.y = top + max(hl, hf) + GAP_FIG


def experiment(P):
    P.section("본론 ② 실험 및 결과", column="right")
    P.sub("5", "실험 설정")
    P.bullets([
        "**도로망**  제주 도심 도로중심선(노드 24,756개, 476 km)",
        "**출발점**  탑동 3 km · 시청 5 km · 연동 3 km · 이도동 4 km",
        "**요청**  출발점마다 16방향(범위 밖 제외) → **47개**",
        "**설정**  기준(α = 0) + 선호 8가지 × 가중치 1·3·10 → **1,175회** 실행",
        "**성공 조건**  목표 거리 ±10% 안의 순환 경로를 1개 이상 만든 요청",
    ], "실험 설정")

    P.sub("6", "구성 요소별 비교")
    rows = [["지표", "빔 탐색 반환", "최소 비용(γ=0)", "최소 비용(γ=5)", "+ 모양 항(제안)"],
            ["성공 요청", "30/47", "40/47", "47/47", "47/47"],
            ["거리 오차", "6%", "6%", "4%", "3%"],
            ["왕복형 경로", "23/78", "30/118", "0/127", "0/137"],
            ["둥근 정도", "0.04", "0.09", "0.27", "0.38"],
            ["꺾임 수(/km)", "1.84", "2.20", "3.08", "2.21"],
            ["응답 시간(s)", "0.7", "2.2", "1.8", "4.2"]]
    P.full_table("표 3", "구성 요소별 비교(기준 설정, 요청 47개)", [1.48, 1.22, 1.22, 1.22, 1.22], rows, hl_col=4,
                 note="둥근 정도 4πa/L²(a: 고리 안 넓이, L: 길이, 원 1, 정사각형 0.79), 꺾임 수: km당 45° 넘게 꺾인 횟수, "
                      "왕복형: 두 번 지난 길이가 40% 이상인 경로. 오차·응답 시간은 평균, 둥근 정도·꺾임 수는 중앙값.")
    P.bullets([
        "같은 길 벌점(γ = 5)부터 47개 요청 모두 성공, 왕복형 0",
        "모양 항 추가 → 꺾임 수 3.08 → **2.21**, 둥근 정도 0.27 → **0.38**",
    ], "표 3 해석")
    P.figure("그림2_비교_전체폭.png", "그림 4", "구성 요소별 경로의 예(연동 3 km, ■ 출발점, ▲ 안내점)", w=5.5)

    P.sub("7", "선호 가중치에 따른 변화")
    rows = [["선호 (지표)", "기준", "α = 1", "α = 3", "α = 10"],
            ["경사(%)", "2.33", "2.24", "2.12", "1.96 (46)"],
            ["신호 교차로(개/km)", "2.73", "1.79", "1.33", "1.08"],
            ["편의시설 거리(m)", "86.1", "79.2", "73.5", "72.1 (44)"],
            ["조명 길(%)", "72", "82", "85", "89 (46)"],
            ["물가 길(%)", "7", "15", "24 (42)", "27 (28)"],
            ["보도 있는 길(%)", "71", "82", "85", "89"],
            ["녹지 길(%)", "6", "12", "20 (44)", "22 (39)"],
            ["조용한 길(%)", "53", "86 (46)", "92 (45)", "94 (42)"]]
    P.full_table("표 4", "선호 가중치별 해당 지표 평균(요청 47개)", [1.96, 0.98, 1.08, 1.12, 1.22], rows,
                 note="기준: 선호 가중치 α를 모두 0으로 둔 설정. 실패 요청을 포함한 47개 평균이며, 위 세 줄은 작을수록, "
                      "아래 다섯 줄(경로 길이 중 그 길의 비율)은 클수록 선호에 맞는다. 괄호: 성공 요청 수(47개 미만일 때).")
    P.bullets([
        "가중치↑ → 해당 지표 개선: α = 10에서 신호 교차로 **약 60%↓**, 선호한 길 **16~41%p↑**",
        "24개 설정 모두 유의(p < 0.01), 선호를 켠 실행의 **96%** 성공",
        "드문 물가·녹지는 α = 10에서 성공 요청이 28·39개로 줄어듦",
        "일부 선호는 서로 부딪침: 조용한 길 → 조명 길 비율 25%p↓",
    ], "표 4 해석")
    P.figure("그림3_새선호_전체폭.png", "그림 5", "선호에 따른 경로의 예(이도동 4 km, 점선: 기준 경로)")


def conclusion(P):
    P.section("결론")
    P.bullets([
        "**제안**  러너 선호 8가지를 경로 비용으로 표현해 진출·반환 탐색에 함께 사용",
        "**결과 1**  목표 거리 준수(47/47 성공, 평균 오차 3%), 모양 항으로 둥글고 덜 꺾임",
        "**결과 2**  가중치를 높일수록 선택한 선호의 지표가 나아짐",
        "**한계**  보행 가능 여부·공사 구간 미반영, 선호는 하나씩만, 러너 평가 없음",
        "**향후 연구**  러너 평가, 선호 조합, 기록으로 가중치 학습, 휠체어·유모차로 확장",
    ], "결론", after=0)


def main():
    make_equations()
    P = Poster()
    P.header()
    intro(P)
    method(P)
    experiment(P)
    conclusion(P)
    P.finish()


if __name__ == "__main__":
    main()

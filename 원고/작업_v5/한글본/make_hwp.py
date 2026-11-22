"""v4 원고(md)를 학회 한글 양식(학술대회논문양식_표준형식.hwp)에 옮겨 한글본을 만든다(2026-11-11 사용자 요청).
1) rhwp로 제목·저자·요약·Abstract·Key words·소속·사사 자리를 바꾼다(한글 프로그램 안 띄움).
2) 새 한글 인스턴스(사용자 한글 창에는 안 붙음)로 열어 양식 견본 문단(장 제목·본문·캡션·식·참고문헌)의 글자·문단 모양을 떠 두고,
   예시 본문과 안내 상자를 지운 뒤 v4 본문을 같은 모양으로 채운다. 그림은 그림 파일, 수식은 한글 수식, 표는 한글 표.
3) 원고/논문_정보기술학회_v4.hwp 로 저장하고, 확인용 PDF를 한글본/확인용.pdf 로 저장한다.
실행: py -I 한글본/make_hwp.py (작업_v4 폴더에서). 끝나면 내가 띄운 한글 프로세스만 닫는다.
"""
import os
import re
import shutil
import subprocess
import sys

import psutil
import win32com.client as win32
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))          # 원고/작업_v4/한글본
WORK = os.path.dirname(HERE)                                # 원고/작업_v4
TOP = os.path.dirname(WORK)                                 # 원고
TEMPLATE = next(p for p in (os.path.join(WORK, "학술대회논문양식_표준형식.hwp"), os.path.join(TOP, "학술대회논문양식_표준형식.hwp"))
                if os.path.exists(p))   # 양식은 작업_v4로 옮길 예정(11/11 한글에서 열려 있어 맨 위에 남음)
MD = os.path.join(WORK, "논문_정보기술학회_v5.md")
BUILD = os.path.join(HERE, "build")
OUT_HWP = os.path.join(TOP, "논문_정보기술학회_v5.hwp")
OUT_PDF = os.path.join(HERE, "확인용.pdf")
RHWP = os.path.join(os.environ["LOCALAPPDATA"], "rhwp", "rhwp", "rhwp.exe")
COL_MM = 70.0   # 한 단 폭(확인용 PDF에서 잰 본문 폭 약 70 mm)
os.makedirs(BUILD, exist_ok=True)

md = open(MD, encoding="utf-8").read().split("## 초안 메모")[0]
lines = md.split("\n")


# ---------------- 원고에서 앞부분 뽑기 ----------------
def section(after, stop_prefixes):
    i = next(k for k, l in enumerate(lines) if l.strip() == after)
    out = []
    for l in lines[i + 1:]:
        if any(l.startswith(p) for p in stop_prefixes):
            break
        if l.strip():
            out.append(l.strip())
    return out


TITLE_KO = lines[0].lstrip("# ").strip()
TITLE_EN = lines[2].strip().strip("*")
AUTH_KO = lines[4].replace("\\*", "*").strip()
AUTH_EN = lines[6].replace("\\*", "*").strip()
ABS_KO = section("## 요 약", ["## "])[0]
ABS_EN = section("## Abstract", ["**Key words**", "## "])[0]
KEYWORDS = section("**Key words**", ["---", "## "])[0]
AFFIL = [l.replace("\\*", "*").strip() for l in lines if l.startswith("\\*")]
AFFIL_LINE = ", ".join(AFFIL)
ACK = next(l.strip() for l in lines if l.startswith("※"))
print("소속", AFFIL_LINE)
print("사사", ACK[:40])

tpl_txt = os.path.join(HERE, "양식분석", "학술대회논문양식_표준형식_001.txt")
T = open(tpl_txt, encoding="utf-8").read().split("\n")
TPL_ABS_KO = "".join(T[8:12])
TPL_ABS_EN = "".join(T[15:20])


# ---------------- 1) rhwp 치환 ----------------
def rhwp_replace(src, dst, find, repl, occ=None):
    cmd = [RHWP, "edit", "replace-text", src, "--find", find, "--replace", repl, "-o", dst]
    if occ:
        cmd += ["--occurrence", str(occ)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if not os.path.exists(dst):
        raise SystemExit(f"치환 실패: {find[:30]} / {r.stdout} {r.stderr}")
    print("치환", find[:24], "→", repl[:24])


cur = os.path.join(BUILD, "s0.hwp")
shutil.copyfile(TEMPLATE, cur)
REPL = [("한글제목", TITLE_KO, None), ("저자*, 저자**", AUTH_KO, None), ("영문제목", TITLE_EN, None),   # 양식 3쪽 같은 글자는 뒤에서 지워짐
        ("저자영문명*, 저자영문명**", AUTH_EN, None), (TPL_ABS_KO, ABS_KO, None), (TPL_ABS_EN, ABS_EN, None),
        ("shape recovery, shape from focus, artificial nural ntwork, depth estimation, focus measure", KEYWORDS, None),
        ("*소속, Email, **소속, Email(교신저자표시), ...", AFFIL_LINE, None), ("※ 지원기관표기(사사표기)", ACK, None)]
for k, (f, r, occ) in enumerate(REPL, 1):
    nxt = os.path.join(BUILD, f"s{k}.hwp")
    if os.path.exists(nxt):
        os.remove(nxt)
    rhwp_replace(cur, nxt, f, r, occ)
    cur = nxt
STEP1 = cur

# ---------------- 수식 안 글자 → 글자 조각(아래·위 첨자) ----------------
CMD = {r"\alpha": "α", r"\gamma": "γ", r"\lambda": "λ", r"\kappa": "κ", r"\Delta": "Δ", r"\pi": "π", r"\ell": "ℓ",
       r"\in": "∈", r"\ge": "≥", r"\le": "≤", r"\approx": "≈", r"\to": "→", r"\times": "×", r"\cdot": "·",
       r"\lvert": "|", r"\rvert": "|", r"\min": "min", r"\max": "max", r"\sum": "Σ", r"\mid": "|", r"\sim": "~",
       r"\{": "{", r"\}": "}", r"\,": " ", r"\;": " ", r"\%": "%"}


def math_runs(s):
    """LaTeX 한 토막을 [(글자, 'n'|'sub'|'sup')]로. \\mathbb{1}은 𝟙."""
    s = s.replace(r"\mathbb{1}", "𝟙")
    s = re.sub(r"\\(mathrm|text|mathit|operatorname)\{([^{}]*)\}", r"\2", s)
    out, i = [], 0

    def take_group(j):
        if j < len(s) and s[j] == "{":
            depth, k = 1, j + 1
            while k < len(s) and depth:
                depth += {"{": 1, "}": -1}.get(s[k], 0)
                k += 1
            return s[j + 1:k - 1], k
        if j < len(s) and s[j] == "\\":
            m = re.match(r"\\[A-Za-z]+", s[j:])
            return m.group(0), j + len(m.group(0))
        return s[j:j + 1], j + 1

    def plain(t):
        t = re.sub(r"\\[A-Za-z]+|\\[{},;%]", lambda m: CMD.get(m.group(0), m.group(0).lstrip("\\")), t)
        return t.replace("{", "").replace("}", "").replace("-", "−")

    buf = ""
    while i < len(s):
        c = s[i]
        if c in "_^":
            if buf:
                out.append((plain(buf), "n"))
                buf = ""
            g, i = take_group(i + 1)
            out.append((plain(g), "sub" if c == "_" else "sup"))
            continue
        buf += c
        i += 1
    if buf:
        out.append((plain(buf), "n"))
    return out


def text_runs(t):
    """본문 한 줄(마크다운+인라인 수식)을 글자 조각으로."""
    t = t.replace("**", "").replace("\\*", "*").replace("\\{", "{").replace("\\}", "}")
    runs = []
    for k, part in enumerate(re.split(r"\$([^$]+)\$", t)):
        if k % 2:
            runs += math_runs(part)
        elif part:
            runs.append((part, "n"))
    return runs


# ---------------- 본문 블록 ----------------
body = md[md.index("## Ⅰ. 서 론"):]
body = body.split("\n---\n")[0]           # 참고문헌 뒤 소속·사사 앞까지
blocks, bl = [], body.split("\n")
k = 0
while k < len(bl):
    l = bl[k].rstrip()
    if not l.strip():
        k += 1
        continue
    if l.startswith("## "):
        blocks.append(("head", l[3:].strip()))
    elif l.startswith("### "):
        blocks.append(("sub", l[4:].strip()))
    elif l.startswith("$$"):
        eq = l
        while not eq.rstrip().endswith("$$") or eq.strip() == "$$":
            k += 1
            eq += bl[k]
        blocks.append(("eq", int(re.search(r"\\tag\{(\d+)\}", eq).group(1))))
    elif l.startswith("!["):
        blocks.append(("img", re.search(r"\(([^)]+)\)", l).group(1)))
    elif l.startswith("> **그림") or l.startswith("> **Fig."):
        blocks.append(("fcap_ko" if "그림" in l[:8] else "fcap_en", l[2:].strip().strip("*")))
    elif l.startswith("**표") or l.startswith("**Table"):
        blocks.append(("tcap_ko" if l.startswith("**표") else "tcap_en", l.strip().strip("*")))
    elif l.startswith("|"):
        rows = []
        while k < len(bl) and bl[k].startswith("|"):
            cells = [c.strip() for c in bl[k].strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-+:?", c) for c in cells):
                rows.append(cells)
            k += 1
        blocks.append(("table", rows))
        continue
    elif l.startswith("주:"):
        blocks.append(("tnote", l))
    elif re.match(r"\[\d+\]", l):
        blocks.append(("ref", l))
    else:
        blocks.append(("body", l))
    k += 1
print("블록", len(blocks), {t: sum(1 for b in blocks if b[0] == t) for t in set(b[0] for b in blocks)})

EQ = {
    1: "LPILE{p(u,v)= ell (u,v) LEFT [ alpha _{s} f _{s} + alpha _{f} f _{f} + sum _{k in K} alpha _{k} f _{k} RIGHT ]"
       " # ~~~~~~~~~~~~~~ + alpha _{c} kappa _{c} {bold 1} LEFT [ v in V _{\"sig\"} RIGHT ]}",
    2: "S(c| b)= A(u,c)- lambda _{p} {p(u,c)} over {ell _{0}} - lambda _{1} {DELTA _{b} (c)} over {180°} - lambda _{2} D(c)",
    3: "LPILE{c _{i} (u,v)= ell (u,v) ( 1+ gamma {bold 1} _{\"out\"} + gamma _{p} {bold 1} _{\"near\"} )"
       " # ~~~~~~~~~~~~~~ +p(u,v)+c _{t} {bold 1} _{\"turn\"}}",
}
TABLE_W = {1: [13, 29, 24], 2: [16, 12.5, 12.5, 12.5, 12.5], 3: [22, 11, 11, 11, 11]}   # 합 66 mm(칸 여백 포함해 단 폭 안)

# ---------------- 2) 한글 자동화 ----------------
before = {p.pid for p in psutil.process_iter(["name"]) if (p.info["name"] or "").lower().startswith("hwp")}
hwp = win32.Dispatch("HWPFrame.HwpObject")
print("모듈 등록", hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule"))


def ins(t):
    p = hwp.HParameterSet.HInsertText
    hwp.HAction.GetDefault("InsertText", p.HSet)
    p.Text = t
    hwp.HAction.Execute("InsertText", p.HSet)


def put(runs):
    for t, m in runs:
        if not t:
            continue
        if m == "sub":
            hwp.Run("CharShapeSubscript")
        elif m == "sup":
            hwp.Run("CharShapeSuperscript")
        ins(t)
        if m == "sub":
            hwp.Run("CharShapeSubscript")
        elif m == "sup":
            hwp.Run("CharShapeSuperscript")


LANG = ("Hangul", "Latin", "Hanja", "Japanese", "Other", "Symbol", "User")
KEYS = {"CharShape": [p + l for p in ("FaceName", "FontType", "Size", "Ratio", "Spacing", "Offset") for l in LANG]
        + ["Height", "Bold", "Italic", "TextColor", "UnderlineType", "StrikeOutType", "SuperScript", "SubScript"],
        "ParaShape": ["AlignType", "LeftMargin", "RightMargin", "Indentation", "PrevSpacing", "NextSpacing",
                      "LineSpacingType", "LineSpacing", "BreakLatinWord", "BreakNonLatinWord", "Condense",
                      "WidowOrphan", "KeepWithNext", "KeepLinesTogether", "PageBreakBefore", "TextAlignment"]}


class Shape(dict):
    """글자·문단 모양 값을 사전으로 들고 있다가 apply()로 커서 위치에 입힌다."""
    def __init__(self, kind, d):
        super().__init__(d)
        self.kind = kind

    def SetItem(self, k, v):
        self[k] = v


ACT = {"CharShape": "CharShape", "ParaShape": "ParagraphShape"}   # 문단 모양 동작 이름은 ParagraphShape


def grab(kind):
    ps = getattr(hwp.HParameterSet, "H" + kind)
    hwp.HAction.GetDefault(ACT[kind], ps.HSet)
    d = {}
    for k in KEYS[kind]:
        try:
            d[k] = getattr(ps, k)
        except Exception:
            pass
    return Shape(kind, d)


def apply(shape):
    ps = getattr(hwp.HParameterSet, "H" + shape.kind)
    hwp.HAction.GetDefault(ACT[shape.kind], ps.HSet)
    for k, v in shape.items():
        setattr(ps, k, v)
    hwp.HAction.Execute(ACT[shape.kind], ps.HSet)


def para_text():
    hwp.Run("MoveParaBegin")
    hwp.Run("MoveSelParaEnd")
    t = hwp.GetTextFile("TEXT", "saveblock") or ""
    hwp.Run("Cancel")
    return t.strip()


try:
    hwp.Open(STEP1, "HWP", "forceopen:true")
    # 견본 문단 모양 뜨기(본문 문단만 차례로 훑음)
    want = {"head": lambda t: t.startswith("Ⅰ. 서"), "body": lambda t: t.startswith("비접촉"),
            "tcap_ko": lambda t: t.startswith("표 1."), "tcap_en": lambda t: t.startswith("Table 1."),
            "fcap_ko": lambda t: t.startswith("그림 1."), "fcap_en": lambda t: t.startswith("Fig. 1."),
            "refhead": lambda t: t.replace(" ", "").startswith("참고문헌"), "ref": lambda t: t.startswith("[1]"),
            "after_eq": lambda t: t.startswith("위 식에서")}
    C, P, prev_pos = {}, {}, None
    hwp.MovePos(2, 0, 0)
    for _ in range(200):
        pos = hwp.GetPos()
        t = para_text()
        for key, f in want.items():
            if key not in C and f(t):
                if key == "after_eq":
                    hwp.SetPos(*prev_pos)
                    hwp.Run("MoveParaEnd")
                    C["eq"], P["eq"] = grab("CharShape"), grab("ParaShape")
                    hwp.SetPos(*pos)
                else:
                    hwp.Run("MoveParaEnd")
                    C[key], P[key] = grab("CharShape"), grab("ParaShape")
                    hwp.SetPos(*pos)
        prev_pos = pos
        if not hwp.HAction.Run("MoveNextParaBegin"):
            break
    print("뜬 모양", sorted(C))
    for key in sorted(P):
        print(f"  {key}: 정렬{P[key].get('AlignType')} 들여{P[key].get('Indentation')} 줄간격{P[key].get('LineSpacing')} "
              f"| {C[key].get('FaceNameHangul')} {C[key].get('Height')}")
    if "--probe" in sys.argv:
        raise SystemExit
    if "fcap_en" not in C and "tcap_en" in C:   # 양식은 그림 캡션 두 줄이 한 문단이라 영문 견본이 따로 없음 → 같은 글꼴인 표 영문 캡션 모양
        C["fcap_en"], P["fcap_en"] = Shape("CharShape", C["tcap_en"]), Shape("ParaShape", P["fcap_ko"])
    missing = {"head", "body", "tcap_ko", "tcap_en", "fcap_ko", "fcap_en", "ref", "eq"} - set(C)
    if missing:
        raise SystemExit(f"견본을 못 찾음: {missing}")
    if "refhead" not in C:
        C["refhead"], P["refhead"] = C["head"], P["head"]
    # 파생 모양: 소제목(중고딕 11), 표 칸(본문 8pt), 표 주(본문 8pt, 들여쓰기 없음), 그림 문단(그림 캡션 문단 모양)
    hwp.MovePos(2, 0, 0)
    hwp.Run("MoveParaEnd")
    C["sub"], P["sub"] = grab("CharShape"), grab("ParaShape")
    for key in ("FaceNameHangul", "FaceNameLatin", "FaceNameHanja", "FaceNameJapanese", "FaceNameOther", "FaceNameSymbol", "FaceNameUser"):
        C["sub"].SetItem(key, "한양중고딕")
    C["sub"].SetItem("Height", 1100)
    P["sub"].SetItem("AlignType", 1)
    # 본문 견본으로 다시 가서 표 칸·주 모양
    hwp.MovePos(2, 0, 0)
    for _ in range(50):
        if para_text().startswith("비접촉"):
            break
        hwp.HAction.Run("MoveNextParaBegin")
    hwp.Run("MoveParaEnd")
    C["cell"], P["cell"] = grab("CharShape"), grab("ParaShape")
    C["cell"].SetItem("Height", 800)
    for key in ("Indentation", "LeftMargin", "RightMargin", "PrevSpacing", "NextSpacing"):
        P["cell"].SetItem(key, 0)
    P["cell"].SetItem("AlignType", 3)
    C["tnote"], P["tnote"] = grab("CharShape"), grab("ParaShape")
    C["tnote"].SetItem("Height", 800)
    P["tnote"].SetItem("Indentation", 0)
    P["cell_l"] = grab("ParaShape")
    for key in ("Indentation", "LeftMargin", "RightMargin", "PrevSpacing", "NextSpacing"):
        P["cell_l"].SetItem(key, 0)
    P["cell_l"].SetItem("AlignType", 1)
    C["img"], P["img"] = C["fcap_ko"], P["fcap_ko"]

    # 예시 본문(제목 'Ⅰ. 서 론'부터 끝까지)과 안내 상자 지우기
    hwp.MovePos(2, 0, 0)
    assert para_text().startswith("Ⅰ. 서"), para_text()
    hwp.MovePos(2, 0, 0)
    hwp.Run("MoveSelDocEnd")
    hwp.Run("Delete")
    ctrl, gone = hwp.HeadCtrl, 0
    while ctrl:
        nxt = ctrl.Next
        if ctrl.CtrlID == "gso":
            hwp.DeleteCtrl(ctrl)
            gone += 1
        ctrl = nxt
    print("안내 상자 지움", gone)

    # 본문 채우기
    hwp.MovePos(3, 0, 0)
    first, tno = True, 0

    def start(kind):
        global first
        if not first:
            hwp.Run("BreakPara")
        first = False
        apply(P[kind])
        apply(C[kind])

    for kind, val in blocks:
        if kind in ("head", "sub", "body", "fcap_ko", "fcap_en", "tcap_ko", "tcap_en", "tnote"):
            start(kind)
            put(text_runs(val))
        elif kind == "ref":
            start("ref")
            put(text_runs(val))
        elif kind == "img":
            start("img")
            path = os.path.join(WORK, val)
            w, h = Image.open(path).size
            hwp.InsertPicture(path, True, 1, False, False, 0, COL_MM, COL_MM * h / w)
            hwp.MovePos(3, 0, 0)
        elif kind == "eq":
            start("eq")
            e = hwp.HParameterSet.HEqEdit
            hwp.HAction.GetDefault("EquationCreate", e.HSet)
            e.string = EQ[val]
            e.BaseUnit = 850 if val == 1 else 900
            hwp.HAction.Execute("EquationCreate", e.HSet)
            hwp.MovePos(3, 0, 0)
            ins(f"  ({val})")
        elif kind == "table":
            tno += 1
            rows = val
            start("cell")
            t = hwp.HParameterSet.HTableCreation
            hwp.HAction.GetDefault("TableCreate", t.HSet)
            t.Rows, t.Cols = len(rows), len(rows[0])
            t.WidthType, t.HeightType = 2, 0
            t.WidthValue = hwp.MiliToHwpUnit(sum(TABLE_W[tno]))
            t.CreateItemArray("ColWidth", len(rows[0]))
            for j, wmm in enumerate(TABLE_W[tno]):
                t.ColWidth.SetItem(j, hwp.MiliToHwpUnit(wmm))
            t.TableProperties.TreatAsChar = 1
            hwp.HAction.Execute("TableCreate", t.HSet)
            tbl = hwp.ParentCtrl            # 커서가 첫 칸에 있으므로 표 조판부호
            pr = tbl.Properties
            pr.SetItem("TreatAsChar", True)  # 글자처럼 취급: 떠 있는 표가 서로 겹치지 않게
            tbl.Properties = pr
            for r_, row in enumerate(rows):
                for c_, cell in enumerate(row):
                    left = tno == 1 and c_ > 0 and r_ > 0
                    apply(P["cell_l" if left else "cell"])
                    apply(C["cell"])
                    put(text_runs(cell))
                    if not (r_ == len(rows) - 1 and c_ == len(row) - 1):
                        hwp.Run("TableRightCell")
            hwp.MovePos(3, 0, 0)
    for f in (OUT_HWP, OUT_PDF):
        if os.path.exists(f):
            os.remove(f)
    hwp.SaveAs(OUT_HWP, "HWP", "")
    hwp.SaveAs(OUT_PDF, "PDF", "")
    print("저장", OUT_HWP, "/", OUT_PDF, "쪽 수", hwp.PageCount)
finally:
    try:
        hwp.Clear(1)
    except Exception:
        pass
    for p in psutil.process_iter(["name"]):
        if (p.info["name"] or "").lower().startswith("hwp") and p.pid not in before:
            p.kill()

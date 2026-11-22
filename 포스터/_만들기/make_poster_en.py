"""정보기술학회 논문(원고 v5) 포스터 영어판 v1 (2026-11-13).

틀(양식, 절 머리띠, 표·그림·수식 놓는 방법)은 한글판 make_poster.py를 그대로 불러 쓰고,
글꼴(Arial)·언어 표시·글·그림 파일만 영어로 바꾼다. 내용과 숫자는 한글판(원고 v5)과 같다.
용어는 원고의 영어 초록(Abstract)과 맞췄다: outbound part, return part, diverse beam search, least-cost search,
reuse·proximity·turn penalty, shape terms, roundness, out-and-back.
영어 그림은 make_en_figs12.py(그림 1·2), make_en_turn.py(그림 3), make_en_maps.py(그림 4·5)로 먼저 만든다.
출력: ../포스터_v1_영어.pptx (PDF: pwsh -File to_pdf.ps1 포스터_v1_영어).  실행: python make_poster_en.py
"""
import importlib.util
import os

from PIL import ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("make_poster", os.path.join(HERE, "make_poster.py"))
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)
globals().update({k: v for k, v in vars(M).items() if not k.startswith("__") and k not in ("HERE",)})

M.FONT = "Arial"
M.REG = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 100)
M.BOLD = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 100)
M.LINE = 1.18
M.LANG_TAG = "en-US"
M.OUT = os.path.join(M.POSTER, "포스터_v1_영어.pptx")
TITLE = "Generating Target-Distance Loop Routes by Incorporating Runner Preferences into Route Costs"
M.DOC = dict(title=TITLE, author="Seung-Jun Kang, Eun Lee, Min-Young Jo, Joon-Min Gil",
             subject="AICompS 2026 (The 3rd International Conference on Artificial Intelligence and Computing Systems) poster")


def header(self):
    sh = self.sh
    replace_text(sh[127], ["AICompS 2026  |  The 3rd International Conference on Artificial Intelligence and Computing Systems"])
    sh[127].width = Inches(13.4)
    replace_text(sh[128], [" "])
    replace_text(sh[129], ["Generating Target-Distance Loop Routes", "by Incorporating Runner Preferences", "into Route Costs"], size=32)
    sh[129].left, sh[129].top, sh[129].width = Inches(0.4), Inches(0.62), Inches(10.6)
    for p in sh[129].text_frame.paragraphs:
        p.line_spacing = 0.9
    replace_text(sh[130], ["Seung-Jun Kang, Eun Lee, Min-Young Jo, Joon-Min Gil†"], size=15)
    sh[130].left, sh[130].top, sh[130].width = Inches(0.4), Inches(2.12), Inches(10.3)
    replace_text(sh[131], ["Department of Computer Engineering, Jeju National University, Korea   († corresponding author)"], size=13)
    sh[131].left, sh[131].top = Inches(0.3), Inches(2.45)
    replace_text(sh[134], [TITLE], size=13)
    for p in sh[134].text_frame.paragraphs:  # 왼쪽 아래 사사와 겹치지 않게 바닥글 제목은 오른쪽 정렬
        p.alignment = PP_ALIGN.RIGHT
    # 오른쪽 위 로고 상자: 영문 로고(make_logo_en.py가 원본 문양 + 영문 글자로 만든 것)
    lw = 2.6
    with Image.open(os.path.join(HERE, "그림", "제주대로고_영문.png")) as im_:
        lh = lw * im_.height / im_.width
    bx, by, bw, bh = 14.05 - lw - 0.24, 0.5, lw + 0.24, lh + 0.2
    box = self.s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(bx), Inches(by), Inches(bw), Inches(bh))
    box.name = "로고 상자"
    box.adjustments[0] = 0.06
    box.fill.solid()
    box.fill.fore_color.rgb = RGBColor.from_string("FFFFFF")
    box.line.color.rgb = RGBColor.from_string("24447D")
    box.line.width = Pt(1.5)
    box.shadow.inherit = False
    style = box._element.find(qn("p:style"))
    if style is not None:
        box._element.remove(style)
    self.picture(bx + 0.12, by + 0.1, lw, "제주대로고_영문.png", "Jeju National University logo")
    # 사사: 왼쪽 아래 파랑 띠에 흰 글씨 두 줄(가운데 바닥글 제목과 겹치지 않게)
    ack = ("This research was supported by the ANCHOR COSS program through the Jeju ANCHOR Center, funded by "
           "the Ministry of Education (MOE) and the Jeju ANCHOR Center, Republic of Korea. (2026-ANCHOR-17-001)")
    self.text(0.35, 21.5, 4.4, [(ack, 7.5, False, "FFFFFF", 0)], "Acknowledgment", anchor=MSO_ANCHOR.MIDDLE, h=0.43)


M.Poster.header = header


def intro(P):
    P.section("Introduction")
    P.bullets([
        "**Problem 1**  A run loops back to the start → navigation cannot give a course",
        "**Problem 2**  Runners dislike signals and turns → hard to avoid in new places",
        "**Example**  Routes ignoring preferences in central Jeju: **2.7** signals per km",
        "**Limitations**  Loop studies focus on length and shape → no preference control",
        "**Proposed method**  Put runner preferences into route costs (Fig. 1)",
    ], "Introduction", after=0)


def method(P):
    P.section("Proposed Method")
    P.sub("1", "Overall Structure")
    P.figure("그림1_구조_포스터_en.png", "Fig. 1", "Structure of the proposed method (T: target distance; blue: uses preference cost p, Eq. (1))")

    P.sub("2", "Preference Cost")
    P.bullets(["Disliked roads count as longer, so the route avoids them (symbols in Table 1)"], "Preference cost", after=0.06)
    P.equation("식1", 1)
    rows = [["Symbol", "Meaning"],
            ["ℓ(u,v)", "Length of segment (u,v) (m)"],
            ["α", "Weight of each item (0 = ignored)"],
            ["f_{s}", "Slope: steeper → larger penalty"],
            ["κ_{c}, 𝟙[v∈V_{sig}]", "Traffic signal: penalty each time it is passed (about 100 m)"],
            ["f_{f}", "Amenities: farther from toilets, stores, and parks → larger penalty"],
            ["f_{k}, k∈K", "Street features K = {lighting, waterside, sidewalk, green, quiet}:\npenalty if the feature is missing"]]
    P.full_table("Table 1", "Symbols in Eq. (1) (f: penalty level, 0–1)", [1.5, 4.86], rows, left_cols=(0, 1), size=10, pad=0.06,
                 note="Example: lighting weight 3 → +300 m per 100 m of unlit road. "
                      "Data: topographic maps, elevation grid, city parks, 2,289 amenities")

    P.sub("3", "Outbound Part: Diverse Beam Search")
    P.figure("진출구간_빔_en.png", "Fig. 2", "② in Fig. 1: 9 beams start within ±45° of the guide direction and stop at 0.51T traveled "
             "(concept; overlap: share of other beams within 20 m of a candidate)")

    P.sub("4", "Return Part: Least-Cost Search")
    P.bullets([
        "Beam-search return misses the target length or comes back the same way",
        "→ The return part uses Dijkstra's least-cost search",
        "Turnaround: re-search candidates, pick the least reuse within ±10% (Fig. 3)",
    ], "Return part", after=0.06)
    P.equation("식2", 2)
    top, fw = P.y, 3.6
    wl = CW - fw - GUT
    rows = [["Symbol", "Meaning"],
            ["ℓ(u,v)", "Edge length (m)"],
            ["p(u,v)", "Preference cost (Eq. (1))"],
            ["γ·𝟙_{out}", "Reusing the\noutbound road\n(penalty γ = 5)"],
            ["γ_{p}·𝟙_{near}", "Within 100 m of the\noutbound road\n(penalty γ_{p} = 3)"],
            ["c_{t}·𝟙_{turn}", "Turning over 45°\n(penalty c_{t} = 60 m)"]]
    hl = P.text(P.x, top, wl, [([("Table 2  ", True, BLUE), ("Symbols in Eq. (2)", True, INK)], CAP, True, INK, 0)], "Table 2 title") + 0.04
    hl += P.table(P.x, top + hl, [0.86, 1.66], rows, "Table 2", size=9.5, pad=0.05, left_cols=(0, 1))
    xf = P.x + wl + GUT
    hf = P.picture(xf, top, fw, "turnaround_en.png", "Fig. 3 turnaround selection")
    hf += 0.04 + P.fig_note(xf, top + hf + 0.04, fw, "Fig. 3", "③·④ in Fig. 1: turnaround selection (synthetic grid, 100 m cells, "
                                                               "target 2,600 m, P1–P5: candidates)")
    P.y = top + max(hl, hf) + GAP_FIG


def experiment(P):
    P.section("Experiments and Results", column="right")
    P.sub("5", "Experimental Setup")
    P.bullets([
        "**Network**  Road centerlines of central Jeju (24,756 nodes, 476 km)",
        "**Starts**  Tapdong 3 km · City Hall 5 km · Yeon-dong 3 km · Ido-dong 4 km",
        "**Requests**  16 directions per start (out-of-area removed) → **47**",
        "**Settings**  Baseline (α = 0) + 8 preferences × weights 1, 3, 10 → **1,175** runs",
        "**Success criterion**  At least one loop within ±10% of the target distance",
    ], "Experimental setup")

    P.sub("6", "Comparison by Component")
    rows = [["Metric", "Beam\nreturn", "Least-cost\n(γ = 0)", "Least-cost\n(γ = 5)", "+ Shape terms\n(ours)"],
            ["Successful requests", "30/47", "40/47", "47/47", "47/47"],
            ["Length error", "6%", "6%", "4%", "3%"],
            ["Out-and-back routes", "23/78", "30/118", "0/127", "0/137"],
            ["Roundness", "0.04", "0.09", "0.27", "0.38"],
            ["Turns (/km)", "1.84", "2.20", "3.08", "2.21"],
            ["Response time (s)", "0.7", "2.2", "1.8", "4.2"]]
    P.full_table("Table 3", "Comparison by component (baseline, 47 requests)", [1.6, 1.12, 1.18, 1.18, 1.28], rows, hl_col=4,
                 note="Roundness 4πa/L² (a: enclosed area, L: length; circle 1, square 0.79); turns: turns over 45° per km; "
                      "out-and-back: at least 40% of the length traversed twice. Error and time: mean; roundness and turns: median.")
    P.bullets([
        "With the reuse penalty (γ = 5): all 47 requests succeed, no out-and-back routes",
        "Adding shape terms → turns 3.08 → **2.21** per km, roundness 0.27 → **0.38**",
    ], "Table 3 findings")
    P.figure("compare_en.png", "Fig. 4", "Routes by component (Yeon-dong, 3 km; ■ start, ▲ guide point)", w=5.5)

    P.sub("7", "Effect of Preference Weights")
    rows = [["Preference (metric)", "Baseline", "α = 1", "α = 3", "α = 10"],
            ["Slope (%)", "2.33", "2.24", "2.12", "1.96 (46)"],
            ["Signals (/km)", "2.73", "1.79", "1.33", "1.08"],
            ["Amenity distance (m)", "86.1", "79.2", "73.5", "72.1 (44)"],
            ["Lit roads (%)", "72", "82", "85", "89 (46)"],
            ["Waterside (%)", "7", "15", "24 (42)", "27 (28)"],
            ["With sidewalk (%)", "71", "82", "85", "89"],
            ["Green (%)", "6", "12", "20 (44)", "22 (39)"],
            ["Quiet streets (%)", "53", "86 (46)", "92 (45)", "94 (42)"]]
    P.full_table("Table 4", "Mean of each metric by preference weight (47 requests)", [1.96, 0.98, 1.08, 1.12, 1.22], rows,
                 note="Baseline: all weights α = 0. Means over 47 requests including failures; top three rows: lower is better; "
                      "bottom five (share of route length): higher is better. Parentheses: successful requests when fewer than 47.")
    P.bullets([
        "Higher weight → better: at α = 10, signals **~60%↓**, preferred roads **+16–41 pp**",
        "All 24 settings significant (p < 0.01); **96%** of runs with preferences succeed",
        "Rare waterside/green roads: only 28 and 39 successful requests at α = 10",
        "Some preferences conflict: quiet streets → lit-road share 25 pp↓",
    ], "Table 4 findings")
    P.figure("prefs_en.png", "Fig. 5", "Routes by preference (Ido-dong, 4 km; dashed: baseline route)")


def conclusion(P):
    P.section("Conclusion")
    P.bullets([
        "**Proposal**  8 runner preferences as route costs for outbound and return search",
        "**Result 1**  Target length kept (47/47, error 3%); rounder, fewer turns",
        "**Result 2**  Higher weight → better metric for the chosen preference",
        "**Limitations**  No walkability data; one preference at a time; no runner study",
        "**Future work**  Runner study, combined preferences, learned weights, wheelchairs",
    ], "Conclusion", after=0)


M.intro, M.method, M.experiment, M.conclusion = intro, method, experiment, conclusion

if __name__ == "__main__":
    M.main()

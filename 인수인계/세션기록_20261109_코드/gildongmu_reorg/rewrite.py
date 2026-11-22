"""재배치 뒤 문서·코드의 옛 경로를 새 경로로 고친다. 사용: rewrite.py dry | apply"""
import collections
import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
APPLY = sys.argv[1] == "apply"
BASE = r"C:\Users\seungjun\Documents\claude_code"
R = os.path.join(BASE, "논문")
B = os.path.join(R, "데이터사이언스학회")
N = os.path.join(R, "정보기술학회")
MEM = r"C:\Users\seungjun\.claude\projects\c--Users-seungjun-Documents-claude-code\memory"
DS = "데이터사이언스학회"
E = f"{DS}/04_실험"
J = f"{E}/6월_학술대회_측정"
I = f"{DS}/06_받은자료"


def read(p):
    with open(p, "rb") as f:
        return f.read().decode("utf-8")


def write(p, s):
    if APPLY:
        with open(p, "wb") as f:
            f.write(s.encode("utf-8"))


# ---------- 1. 코드·링크: 파일별 정확한 치환 ----------
FIG_J = [
    ('"..", "writing", "figures", "en"', '"..", "..", "03_그림", "영문"'),
    ('"..", "writing", "figures"', '"..", "..", "03_그림"'),
    ('os.path.join(HERE, "..", "writing", "course_descriptions.txt")', 'os.path.join(HERE, "course_descriptions.txt")'),
    ('os.path.join(HERE, "..", "writing", "course_requests.txt")', 'os.path.join(HERE, "course_requests.txt")'),
    ("../writing/figures/en/", "../../03_그림/영문/"),
    ("../writing/figures/", "../../03_그림/"),
    ("→ writing/figures/", "→ ../../03_그림/"),
]
RUNS = [
    ('"v2b_run"', '"새그래프v2b_실행"'),
    ('os.path.join(EXP, f"team_direction_run', 'os.path.join(EXP, "6월_학술대회_측정", f"team_direction_run'),
    ('os.path.join(EXP, "ablation_proposed.csv")', 'os.path.join(EXP, "6월_학술대회_측정", "ablation_proposed.csv")'),
    ("../build_multirun_stats.py", "../6월_학술대회_측정/build_multirun_stats.py"),
    ("../writing/figures/en/", "../../03_그림/영문/"),
]
MAKE = [
    ('HERE, "figures", "en"', 'HERE, "..", "영문"'),
    ('HERE, "figures", "icons"', 'HERE, "..", "아이콘"'),
    ('os.path.join(FIG, "icons")', 'os.path.join(FIG, "아이콘")'),
    ('HERE, "figures"', 'HERE, ".."'),
    ('HERE, "drafts", "논문v', 'HERE, "..", "..", "01_원고", "지난판", "논문v'),
    ('HERE, "drafts", "길동무_', 'HERE, "..", "..", "02_발표자료", "길동무_'),
    ('HERE, "..", "experiments", "gildongmu-experiment"', 'HERE, "..", "..", "04_실험", "gildongmu-experiment"'),
    ('HERE, "쉬운설명_길동무', 'HERE, "..", "..", "01_원고", "쉬운설명_길동무'),
    ('os.path.join(HERE, m.group(2))', 'os.path.join(HERE, "..", "..", "01_원고", m.group(2))'),
    ('HERE, "발표_대본_중간보고.md"', 'HERE, "..", "..", "02_발표자료", "발표_대본_중간보고.md"'),
    ("path='drafts/길동무_중간보고.pptx'", "path='../../02_발표자료/길동무_중간보고.pptx'"),
    ("→ drafts/길동무_", "→ ../../02_발표자료/길동무_"),
    ("출력: drafts/논문v", "출력: ../../01_원고/지난판/논문v"),
    ("(writing/drafts/논문v4.md)", "(01_원고/지난판/논문v4.md)"),
    ("출력: figures/", "출력: ../"),
    ("→ figures/", "→ ../"),
    ("experiments/team-latest-back", "04_실험/team-latest-back"),
]
exact = []
exact += [(p, FIG_J) for p in glob.glob(os.path.join(B, "04_실험", "6월_학술대회_측정", "*.py"))]
exact += [(os.path.join(B, "04_실험", "gildongmu-real", "build_route_figures.py"),
           [('"..", "..", "writing", "figures"', '"..", "..", "03_그림"'), ("../writing/figures/", "../../03_그림/")])]
for run in ["귀환재설계_결과", "새그래프v2_실행", "새그래프v2b_실행"]:
    exact += [(p, RUNS) for p in glob.glob(os.path.join(B, "04_실험", run, "*.py"))]
exact += [(os.path.join(B, "04_실험", "별도탐색_OSM", "osm_coverage_pbf.py"),
           [('"reading", "references_data", "osm"', '"05_참고자료", "기초자료", "osm"'),
            ("논문/reading/references_data/osm/", "논문/데이터사이언스학회/05_참고자료/기초자료/osm/")])]
exact += [(p, MAKE) for p in glob.glob(os.path.join(B, "03_그림", "만들기_코드", "*.py"))]
exact += [(os.path.join(B, "02_발표자료", "화면시안", "ai_ui.html"), [("../figures/", "../../03_그림/")])]
exact += [(p, [("](../figures/", "](../../03_그림/"), ("](../../experiments/", "](../../04_실험/")])
          for p in glob.glob(os.path.join(B, "01_원고", "지난판", "*.md"))]
exact += [(os.path.join(B, "01_원고", "쉬운설명_길동무.md"), [("](figures/", "](../03_그림/")])]
exact += [(os.path.join(N, "원고", "논문_정보기술학회_v1.md"),
           [("](../../../experiments/loopv2_run/", "](../../데이터사이언스학회/04_실험/귀환재설계_결과/")])]
exact += [(os.path.join(B, "07_인수인계", "README.md"), [("](2026-11-08-handoff.md)", "](../../정보기술학회/인수인계/2026-11-08-handoff.md)")])]

stats = collections.Counter()
for p, pairs in exact:
    s = read(p)
    new = s
    for a, b in pairs:
        n = new.count(a)
        if n:
            stats[(os.path.basename(p) if len(pairs) < 3 else "코드", a, b)] += n
            new = new.replace(a, b)
    if new != s:
        write(p, new)
print("=== 정확 치환")
for (f, a, b), n in sorted(stats.items(), key=str):
    print(f"{n:3d}  {a}  =>  {b}")

# ---------- 2. 문서 본문의 경로 ----------
keys = {
    "writing/drafts/정보기술학회": "정보기술학회/원고",
    "writing/drafts/학회지": f"{DS}/01_원고/학회지",
    "writing/drafts/길동무_": f"{DS}/02_발표자료/길동무_",
    "writing/drafts/논문v": f"{DS}/01_원고/지난판/논문v",
    "writing/drafts/IV_": f"{DS}/01_원고/지난판/IV_",
    "writing/drafts/": f"{DS}/01_원고/",
    "writing/figures/en": f"{DS}/03_그림/영문",
    "writing/figures/icons": f"{DS}/03_그림/아이콘",
    "writing/figures": f"{DS}/03_그림",
    "writing/references": f"{DS}/05_참고자료/참고문헌",
    "writing/mockup": f"{DS}/02_발표자료/화면시안",
    "writing/build_": f"{DS}/03_그림/만들기_코드/build_",
    "writing/check_": f"{DS}/03_그림/만들기_코드/check_",
    "writing/쉬운설명": f"{DS}/01_원고/쉬운설명",
    "writing/발표_": f"{DS}/02_발표자료/발표_",
    "writing/포스터_": f"{DS}/02_발표자료/포스터_",
    "writing/course_": f"{J}/course_",
    "writing/": f"{DS}/01_원고/",
    "experiments/loopv2_run": f"{E}/귀환재설계_결과",
    "experiments/v2_graph": f"{E}/새그래프_만들기",
    "experiments/v1_run": f"{E}/기존그래프_실행",
    "experiments/v2_run": f"{E}/새그래프v2_실행",
    "experiments/v2b_run": f"{E}/새그래프v2b_실행",
    "experiments/osm_coverage": f"{E}/별도탐색_OSM",
    "experiments/seoul_dev": f"{E}/별도탐색_서울",
    "experiments/_dump": f"{E}/DB덤프",
    "experiments/code": f"{E}/코드",
    "experiments/data": f"{E}/데이터",
    "experiments/results": f"{E}/결과",
    "experiments/team_direction_": f"{J}/team_direction_",
    "experiments/ablation_": f"{J}/ablation_",
    "experiments/measure_": f"{J}/measure_",
    "experiments/run5": f"{J}/run5",
    "experiments/": f"{E}/",
    "reading/papers": f"{DS}/05_참고자료/논문",
    "reading/notes": f"{DS}/05_참고자료/요약",
    "reading/references_data": f"{DS}/05_참고자료/기초자료",
    "reading/": f"{DS}/05_참고자료/",
    "handoff/2026-11-08-handoff.md": "정보기술학회/인수인계/2026-11-08-handoff.md",
    "handoff/": f"{DS}/07_인수인계/",
    "specs/": f"{DS}/07_인수인계/설계문서/",
    "source/backend": f"{DS}/08_앱소스/백엔드",
    "source/frontend": f"{DS}/08_앱소스/프론트엔드",
    "source/": f"{DS}/08_앱소스/",
    "_개인기록/": f"{DS}/_개인기록/",
    "_inbox/중간보고_배리어프리": "_inbox/중간보고_배리어프리",
    "_inbox/": f"{I}/",
}
for name in os.listdir(os.path.join(B, "04_실험", "6월_학술대회_측정")):
    keys[f"experiments/{name}"] = f"{J}/{name}"
for sub in ["이전_논문본", "학회양식", "팀_코드와문서"]:
    for name in os.listdir("\\\\?\\" + os.path.join(B, "06_받은자료", sub)):
        keys[f"_inbox/{name}"] = f"{I}/{sub}/{name}"
for name in os.listdir(os.path.join(B, "02_발표자료", "받은자료")):
    keys[f"_inbox/{name}"] = f"{DS}/02_발표자료/받은자료/{name}"
bare = {"loopv2_run": "귀환재설계_결과", "v2_graph": "새그래프_만들기", "v1_run": "기존그래프_실행", "v2_run": "새그래프v2_실행",
        "v2b_run": "새그래프v2b_실행", "osm_coverage": "별도탐색_OSM", "seoul_dev": "별도탐색_서울"}


def pattern(k):
    return re.escape(k).replace("/", r"[/\\]+")


alt = "|".join(pattern(k) for k in sorted(keys, key=len, reverse=True))
bare_alt = "|".join(sorted(bare, key=len, reverse=True))
rx = re.compile(rf"(?<![\w./\\-])(?P<pre>논문[/\\]+)?(?:(?P<key>{alt})|(?P<bare>{bare_alt})(?![\w.-]))")
root_docs = re.compile(r"논문[/\\]+(MASTER\.md|팀최신본_분석\.md)")
norm = {re.sub(r"[/\\]+", "/", k): v for k, v in keys.items()}
pairs = collections.Counter()


def sub(m):
    pre = "논문/" if m.group("pre") else ""
    if m.group("bare"):
        new = pre + bare[m.group("bare")]
    else:
        new = pre + norm[re.sub(r"[/\\]+", "/", m.group("key"))]
    pairs[(m.group(0), new)] += 1
    return new


docs = [os.path.join(R, "CLAUDE.md"), os.path.join(B, "MASTER.md"), os.path.join(B, "팀최신본_분석.md"),
        os.path.join(BASE, "README.md"), os.path.join(BASE, "베리어프리", "README.md")]
for pat in ["07_인수인계/*.md", "07_인수인계/설계문서/*.md", "_개인기록/*.md", "01_원고/*.md", "01_원고/*/*.md", "02_발표자료/*.md"]:
    docs += glob.glob(os.path.join(B, pat))
docs += glob.glob(os.path.join(N, "*", "*.md"))
docs += [os.path.join(MEM, f) for f in ["capstone2-barrier-free-navigation.md", "gildongmu-journal-paper.md", "gildongmu-running-route-app.md",
                                         "MEMORY.md", "vscode-git-reconnect.md", "workspace-reorg-2026-10-14.md"]]
EXTRA = [
    ("\\논문\\experiments\\", "\\논문\\데이터사이언스학회\\04_실험\\"),
    ("cd 논문\\experiments;", "cd 논문\\데이터사이언스학회\\04_실험\\6월_학술대회_측정;"),
    ("cd 논문\\writing;", "cd 논문\\데이터사이언스학회\\03_그림\\만들기_코드;"),
    ('"drafts\\논문v5.md"', '"..\\..\\01_원고\\지난판\\논문v5.md"'),
    ('"drafts/논문v5.md"', '"../../01_원고/지난판/논문v5.md"'),
    ("`../../figures/en/`", "`../../03_그림/영문/`"),
    ("`figures/en/fig", "`03_그림/영문/fig"),
    ("`drafts/길동무_중간보고.pptx`", "`길동무_중간보고.pptx`"),
    ("논문/experiments", "논문/데이터사이언스학회/04_실험"),
]
left = re.compile(r"experiments|writing[/\\]|_inbox|handoff[/\\]|reading[/\\]|specs[/\\]|source[/\\]|figures[/\\]|drafts[/\\]|loopv2_run|v2b_run|v2_graph|seoul_dev")
leftovers = []
for p in docs:
    s = read(p)
    new = rx.sub(sub, s)
    new = root_docs.sub(lambda m: f"논문/{DS}/{m.group(1)}", new)
    for a, b in EXTRA:
        new = new.replace(a, b)
    if new != s:
        write(p, new)
    for i, line in enumerate(new.splitlines(), 1):
        if left.search(line):
            leftovers.append(f"{os.path.relpath(p, BASE)}:{i}: {line.strip()[:140]}")
print("=== 문서 경로 치환", sum(pairs.values()), "곳, 종류", len(pairs))
for (a, b), n in sorted(pairs.items(), key=lambda x: x[0][0]):
    print(f"{n:3d}  {a}  =>  {b}")
print("=== 남은 옛 이름", len(leftovers))
for x in leftovers:
    print(x)

vs = os.path.join(BASE, ".vscode", "settings.json")
s = read(vs)
new = s.replace('"논문/experiments"', '"논문/데이터사이언스학회/04_실험"')
print("=== vscode 변경:", s != new)
if new != s:
    write(vs, new)

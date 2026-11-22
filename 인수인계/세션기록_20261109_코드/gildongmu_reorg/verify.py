"""재배치 후 경로 검사 (읽기 전용): 코드 문법, 코드 속 경로, md 링크, 문서에 적힌 새 경로."""
import ast
import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
BASE = r"C:\Users\seungjun\Documents\claude_code"
R = os.path.join(BASE, "논문")
B = os.path.join(R, "데이터사이언스학회")
N = os.path.join(R, "정보기술학회")
L = "\\\\?\\"
bad = 0

scripts = []
for pat in ["03_그림/만들기_코드/*.py", "04_실험/6월_학술대회_측정/*.py", "04_실험/귀환재설계_결과/*.py", "04_실험/새그래프v2_실행/*.py",
            "04_실험/새그래프v2b_실행/*.py", "04_실험/별도탐색_OSM/*.py", "04_실험/gildongmu-real/*.py"]:
    scripts += glob.glob(os.path.join(B, pat))
scripts += [os.path.join(N, "원고", "build_pdf.py")]
ok_syntax = checked = 0
join = re.compile(r"os\.path\.join\((HERE|EXP)((?:\s*,\s*f?\"[^\"]*\")+)")
for p in scripts:
    s = open(p, encoding="utf-8", errors="replace").read()
    try:
        ast.parse(s)
        ok_syntax += 1
    except SyntaxError as e:
        bad += 1
        print("문법 오류", p, e)
    here = os.path.dirname(p)
    roots = {"HERE": here, "EXP": os.path.dirname(here)}
    for m in join.finditer(s):
        parts = re.findall(r"(f?)\"([^\"]*)\"", m.group(2))
        cur = roots[m.group(1)]
        for is_f, part in parts:
            if is_f or "{" in part:
                break
            cur = os.path.normpath(os.path.join(cur, part))
        folder = cur if os.path.isdir(cur) else os.path.dirname(cur)
        checked += 1
        if not os.path.isdir(folder):
            bad += 1
            print("폴더 없음", os.path.basename(p), m.group(0)[:90])
print(f"스크립트 {len(scripts)}개 중 문법 정상 {ok_syntax}개, 코드 속 경로 {checked}곳 검사")

docs = [os.path.join(R, "CLAUDE.md"), os.path.join(R, "README.md")]
for d, ds, fs in os.walk(R):
    ds[:] = [x for x in ds if x not in {"node_modules", ".git", ".gradle", "build", "bin", "06_받은자료", "08_앱소스", "gildongmu-real", "gildongmu-experiment", "team-latest-back"}]
    docs += [os.path.join(d, f) for f in fs if f.endswith((".md", ".html"))]
docs = sorted(set(docs))
link = re.compile(r"\]\(([^)\s]+)\)|\bsrc=\"([^\"]+)\"")
links = broken = 0
for p in docs:
    for line in open(p, encoding="utf-8", errors="replace"):
        for m in link.finditer(line):
            t = m.group(1) or m.group(2)
            if t.startswith(("http", "#", "data:", "mailto")) or "<" in t:
                continue
            links += 1
            if not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(p), t.split("#")[0]))):
                broken += 1
                bad += 1
                print("깨진 링크", os.path.relpath(p, R), "->", t[:80])
print(f"문서 {len(docs)}개의 상대 링크 {links}개 중 깨진 것 {broken}개")

token = re.compile(r"(?:논문/)?((?:데이터사이언스학회|정보기술학회)/[^\s`'\"()\[\],;:|*{}<>]+)")
seen = miss = 0
for p in docs + [os.path.join(BASE, ".vscode", "settings.json")]:
    for i, line in enumerate(open(p, encoding="utf-8", errors="replace"), 1):
        for m in token.finditer(line):
            t = m.group(1).rstrip(".").rstrip("/")
            seen += 1
            if not os.path.exists(L + os.path.normpath(os.path.join(R, t))):
                miss += 1
                print(f"없는 경로 {os.path.relpath(p, R)}:{i}: {t[:110]}")
print(f"문서에 적힌 새 경로 {seen}곳 중 실제로 없는 것 {miss}곳")
print("코드·링크 판정:", "통과" if not bad else f"확인 필요 {bad}")

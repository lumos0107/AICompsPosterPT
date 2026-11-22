"""논문 폴더 재배치. 삭제 없이 같은 드라이브 이동만 한다. 사용: moves.py test | all"""
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
R = r"C:\Users\seungjun\Documents\claude_code\논문"
ARCHIVE = r"C:\Users\seungjun\Documents\claude_code\기타\_정리보관"
B = "데이터사이언스학회"
N = "정보기술학회"
L = "\\\\?\\"


def abs_(p):
    return os.path.normpath(p if os.path.isabs(p) else os.path.join(R, p))


def mkdir(p):
    os.makedirs(L + abs_(p), exist_ok=True)


def mv(a, b):
    src, dst = abs_(a), abs_(b)
    if not os.path.lexists(L + src):
        if os.path.lexists(L + dst):
            print("이미 옮김:", a)
            return
        raise SystemExit(f"없음: {a}")
    if os.path.lexists(L + dst):
        raise SystemExit(f"이미 있음: {b}")
    try:
        os.rename(L + src, L + dst)
    except PermissionError as e:
        print("os.rename 실패, Move-Item 시도:", a, e)
        env = dict(os.environ, MV_SRC=src, MV_DST=dst)
        r = subprocess.run(["pwsh", "-NoProfile", "-Command", "Move-Item -LiteralPath $env:MV_SRC -Destination $env:MV_DST -ErrorAction Stop"], capture_output=True, env=env)
        if r.returncode != 0 or os.path.lexists(L + src):
            raise SystemExit(f"이동 실패: {a}\n{r.stderr.decode('cp949', 'replace')[:400]}")
    print("옮김:", a, "->", b)


def children(p):
    return sorted(os.listdir(L + abs_(p)))


mode = sys.argv[1]
if mode == "test":
    mkdir(B)
    mv("experiments", f"{B}/04_실험")
    sys.exit(0)

# 1. 맨 위 폴더
for sub in ["원고", "인수인계", "실험", "그림"]:
    mkdir(f"{N}/{sub}")
for sub in ["01_원고/지난판", "02_발표자료/받은자료"]:
    mkdir(f"{B}/{sub}")
mv("reading", f"{B}/05_참고자료")
mv("_inbox", f"{B}/06_받은자료")
mv("handoff", f"{B}/07_인수인계")
mv("specs", f"{B}/07_인수인계/설계문서")
mv("source", f"{B}/08_앱소스")
mv("_개인기록", f"{B}/_개인기록")
for f in ["MASTER.md", "팀최신본_분석.md", "논문 평가및 수정제안 프럼프트.txt"]:
    mv(f, f"{B}/{f}")
mv(f"{B}/07_인수인계/2026-11-08-handoff.md", f"{N}/인수인계/2026-11-08-handoff.md")

# 2. 현재 초안
for f in ["논문_정보기술학회_v1.md", "논문_정보기술학회_v1.pdf", "build_pdf.py"]:
    mv(f"writing/drafts/정보기술학회/{f}", f"{N}/원고/{f}")

# 3. writing 나누기
mv("writing/drafts/학회지", f"{B}/01_원고/학회지")
for f in children("writing/drafts"):
    if f == "정보기술학회" or f == ".gitkeep":
        continue
    if f.startswith("길동무_"):
        mv(f"writing/drafts/{f}", f"{B}/02_발표자료/{f}")
    elif f.startswith(("논문v", "IV_")):
        mv(f"writing/drafts/{f}", f"{B}/01_원고/지난판/{f}")
    else:
        raise SystemExit(f"분류 안 된 파일: {f}")
mv("writing/figures", f"{B}/03_그림")
mv(f"{B}/03_그림/en", f"{B}/03_그림/영문")
mv(f"{B}/03_그림/icons", f"{B}/03_그림/아이콘")
mkdir(f"{B}/03_그림/만들기_코드")
mv("writing/references", f"{B}/05_참고자료/참고문헌")
mv("writing/mockup", f"{B}/02_발표자료/화면시안")

# 4. 실험 안쪽 (writing의 course_*.txt가 들어오므로 먼저)
E = f"{B}/04_실험"
J = f"{E}/6월_학술대회_측정"
for f in children(E):
    if os.path.isfile(L + abs_(f"{E}/{f}")):
        mkdir(J)
        mv(f"{E}/{f}", f"{J}/{f}")
for f in children("writing"):
    p = f"writing/{f}"
    if os.path.isdir(L + abs_(p)):
        continue
    if f.endswith(".py"):
        mv(p, f"{B}/03_그림/만들기_코드/{f}")
    elif f.startswith("쉬운설명_"):
        mv(p, f"{B}/01_원고/{f}")
    elif f.startswith(("발표_", "포스터_")):
        mv(p, f"{B}/02_발표자료/{f}")
    elif f.startswith("course_"):
        mv(p, f"{J}/{f}")
    else:
        raise SystemExit(f"분류 안 된 파일: {f}")
for a, b in [("loopv2_run", "귀환재설계_결과"), ("v2_graph", "새그래프_만들기"), ("v1_run", "기존그래프_실행"),
             ("v2_run", "새그래프v2_실행"), ("v2b_run", "새그래프v2b_실행"), ("osm_coverage", "별도탐색_OSM"),
             ("seoul_dev", "별도탐색_서울"), ("_dump", "DB덤프"), ("code", "코드"), ("data", "데이터"), ("results", "결과")]:
    mv(f"{E}/{a}", f"{E}/{b}")

# 5. 참고자료·앱소스 안쪽
for a, b in [("papers", "논문"), ("notes", "요약"), ("references_data", "기초자료")]:
    mv(f"{B}/05_참고자료/{a}", f"{B}/05_참고자료/{b}")
for a, b in [("backend", "백엔드"), ("frontend", "프론트엔드")]:
    mv(f"{B}/08_앱소스/{a}", f"{B}/08_앱소스/{b}")

# 6. 받은자료 나누기
I = f"{B}/06_받은자료"
for sub in ["이전_논문본", "학회양식", "팀_코드와문서"]:
    mkdir(f"{I}/{sub}")
for f in ["메가해커톤_수정본.pdf", "메가해커톤_수정본.pptx", "ICOIN-2026 (poster)-v2.pptx", "KDS2026_poster_final.pdf"]:
    mv(f"{I}/{f}", f"{B}/02_발표자료/받은자료/{f}")
for f in ["20260609-논문.docx", "논문v1.docx", "논문v2.docx", "논문v2_수식_설명.md", "논문 중간검증.docx", "형식에 맞춘 최종본.docx",
          "형식에 맞춘 최종본_축약.docx", "한국데이터사이언스-하계종합학술대회-장려상.pdf", "_v1.txt", "_v2.txt"]:
    mv(f"{I}/{f}", f"{I}/이전_논문본/{f}")
for f in ["국내 학술대회 논문지양식.docx", "심사용_논문지양식.hwp"]:
    mv(f"{I}/{f}", f"{I}/학회양식/{f}")
for f in ["--main", "algorithm_최신", "backend_latest", "database", "project_md_가장최신프럼프트", "src", "ALGORITHM.md", "database_create.md",
          "길동무_프로젝트_진척도.md", "전체 컨텍스트 문서.md", "프로젝트 전체 개요.md", "프로젝트 수행계획서.pdf", "재포집 데이터 설명.txt", "재포집 데이터.png",
          "논문 평가및 수정제안 프럼프트.txt"]:
    mv(f"{I}/{f}", f"{I}/팀_코드와문서/{f}")

# 7. 비고 남은 껍데기(.gitkeep, 캐시)는 지우지 않고 보관
print("writing에 남은 것:", [os.path.join(d, f)[len(L + R) + 1:] for d, _, fs in os.walk(L + abs_("writing")) for f in fs])
mv("writing", os.path.join(ARCHIVE, "논문_writing_빈폴더_1109"))
print("논문 맨 위:", children("."))
print("받은자료 맨 위:", children(I))

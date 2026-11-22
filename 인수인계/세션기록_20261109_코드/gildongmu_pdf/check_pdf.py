"""생성된 PDF를 원고 md·측정 결과와 대조한다 (읽기 전용)."""
import json
import re
import sys
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding="utf-8")
base = Path(r"C:\Users\seungjun\Documents\claude_code\논문")
folder = base / r"writing\drafts\정보기술학회"
md_full = (folder / "논문_정보기술학회_v1.md").read_text(encoding="utf-8")
md = md_full.split("## 초안 메모")[0]
doc = fitz.open(folder / "논문_정보기술학회_v1.pdf")
summ = json.loads((base / r"experiments\loopv2_run\conditions_summary.json").read_text(encoding="utf-8"))

HEADER = "-2026한국정보기술학회추계종합학술대회논문집-"
squash = lambda s: re.sub(r"\s+", "", s)

pages = [squash(p.get_text()).replace(HEADER, "") for p in doc]
pages = [re.sub(r"-\d-$", "", t) for t in pages]
# 첫 쪽은 위에 덧붙인 소속·사사가 본문 흐름 끝에 끼므로 잘라 낸다
note_at = pages[0].find("*제주대학교")
note_text = pages[0][note_at:] if note_at >= 0 else ""
pages[0] = pages[0][:note_at] if note_at >= 0 else pages[0]
pages[0] = re.sub(r"-\d-$", "", pages[0])
pdf_text = "".join(pages)
raw = squash("".join(p.get_text() for p in doc))

ok = True


def report(name, passed, detail=""):
    global ok
    ok &= bool(passed)
    print(("통과" if passed else "실패"), name, detail)


report("쪽 수 5쪽 이하", len(doc) <= 5, f"({len(doc)}쪽)")
report("용지 190x260mm", all(abs(p.rect.width * 25.4 / 72 - 190) < 0.5 and abs(p.rect.height * 25.4 / 72 - 260) < 0.5 for p in doc))
report("깨진 글자(빈 네모) 없음", "\u00a0" not in raw and "\ufffd" not in raw)
for word in ["딥또", "Dipto", "diptobiswas", "초안메모", "LOOP_V2"]:
    report(f"PDF에 없음: {word}", word not in raw)
for word in ["딥또", "Dipto", "diptobiswas"]:
    report(f"md에 없음: {word}", word not in md_full)
ack = squash("※ 본 과제(결과물)는 교육부와 한국연구재단의 재원으로 지원을 받아 수행된 첨단분야 혁신융합대학사업의 연구결과입니다.")
report("사사 문구", ack in note_text)
report("소속", squash("*제주대학교 컴퓨터공학과, {wind5973, leeeun2022, tnssid}@stu.jejunu.ac.kr") in note_text)
report("교신저자", squash("**제주대학교 컴퓨터공학과(교신저자), jmgil@jejunu.ac.kr") in note_text)
report("저자 줄", squash("강승준*, 이은*, 조민영*, 길준민**") in raw and squash("Seung-Jun Kang*, Eun Lee*, Min-Young Jo*, Joon-Min Gil**") in raw)

labels = ["기존 그래프 + 빔 귀환", "새 그래프 + 빔 귀환"]
keys = ["A 기존그래프+DIRECTION", "B v2b+DIRECTION", "C 기존그래프+LOOP_V2(γ5)", "D v2b+LOOP_V2(γ5)",
        "E v2b+LOOP_V2(γ0)", "F v2b+LOOP_V2(γ5,외향0.6T)"]
for key in keys:
    s = summ[key]
    row = squash("".join([s["routes"], s["err"], s["success"], s["out_and_back"], s["overlap"], s["elapsed"]]))
    report(f"표 2 {key[0]}행", row in raw, "" if row in raw else row)

for n in range(1, 6):
    report(f"수식 번호 ({n})", f"({n})" in raw)
for n in range(1, 12):
    report(f"참고문헌 [{n}]", f"[{n}]" in pdf_text)
report("표 캡션", all(squash(c) in raw for c in ["표 1. 선호 항목의 정의와 자료", "Table 2. Results by road graph", "표 3. 선호 설정별 결과"]))
report("그림 캡션", all(squash(c) in raw for c in ["그림 1. 제안 방법의 구성", "그림 2. 목표 거리 순환 경로 생성 예", "Fig. 2. Examples of generated loop routes"]))
report("초안 표시 수", raw.count("★") >= 15 and raw.count("○○") >= 20, f"(★ {raw.count('★')}, ○○ {raw.count('○○')})")

# 본문 문단 대조: 수식을 뺀 조각을 12자 단위로 끊어 PDF에 있는지 본다
missing, total = [], 0
for line in md.splitlines():
    line = line.strip()
    if not line or line.startswith(("|", "$$", "!", "---", "#", ">", "**표", "**Table", "**Key", "\\*", "※", "Seung-Jun", "강승준")):
        continue
    plain = line.replace("**", "").replace("\\*", "*")
    for segment in re.split(r"\$[^$]*\$", plain):
        s = squash(segment)
        for i in range(0, len(s) - 11, 12):
            total += 1
            piece = s[i:i + 12]
            if piece not in pdf_text:
                missing.append(piece)
print(f"본문 조각 {total}개 중 PDF에서 못 찾은 것 {len(missing)}개")
for piece in missing:
    print("   ", piece)

fonts = sorted({f[3] for p in doc for f in p.get_fonts(full=True)})
print("포함된 글꼴:", [re.sub(r"^[A-Z]{6}\+", "", f) for f in fonts])
print("이미지 수:", sum(len(p.get_images()) for p in doc))
print("파일 크기(KB):", round(Path(doc.name).stat().st_size / 1024))
print("전체 판정:", "통과" if ok and not missing else "확인 필요")

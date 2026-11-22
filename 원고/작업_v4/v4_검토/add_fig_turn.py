"""v4에 반환점 선택 그림(새 그림 2)을 넣고 기존 그림 2·3을 그림 3·4로 미룬다(2026-11-11 사용자 요청).
그림 파일 이름(그림2_비교.png, 그림3_새선호.png)은 그대로 둔다. 실행: py -I v4_검토/add_fig_turn.py (원고 폴더에서)"""
import re
from pathlib import Path

P = Path(__file__).resolve().parent.parent / "논문_정보기술학회_v4.md"
s = P.read_text(encoding="utf-8")
assert "그림2_반환점.png" not in s, "이미 넣었음"

# 1) 기존 번호 미루기(3→4 먼저, 그다음 2→3). 파일 이름 '그림2_', '그림3_'은 건드리지 않는다.
s = re.sub(r"그림 3(?![_\d])", "그림 4", s)
s = s.replace("Fig. 3.", "Fig. 4.")
s = re.sub(r"그림 2(?![_\d])", "그림 3", s)
s = s.replace("Fig. 2.", "Fig. 3.")

# 2) 반환점 문단 끝에 그림 참조, 문단 뒤에 그림 넣기
old = "오차 ±10% 안에서 되밟은 길이가 가장 짧은 노드를 반환점으로 정한다."
assert s.count(old) == 1
fig = (
    "오차 ±10% 안에서 되밟은 길이가 가장 짧은 노드를 반환점으로 정한다(그림 2).\n\n"
    "![그림 2](그림_v4/그림2_반환점.png)\n\n"
    "> **그림 2. 반환점 선택의 예 (가상 도로, 한 칸 100 m, 목표 2,600 m, ○ 반환점 후보, (b)의 수치는 1단계 길이 → 다시 잰 길이)**\n"
    "> **Fig. 2. Example of turnaround selection (synthetic grid)**"
)
s = s.replace(old, fig)

# 3) 초안 메모의 그림 목록
s = s.replace(
    "그림 1 흐름도, 그림 3 구성 요소별 경로(연동, 중앙값 요청), 그림 4 선호별 경로(이도, 중앙값 요청).",
    "그림 1 흐름도, 그림 3 구성 요소별 경로(연동, 중앙값 요청), 그림 4 선호별 경로(이도, 중앙값 요청). "
    "그림 2 반환점 선택 예시는 `그림_v4/make_fig_turn.py`(가상 바둑판, 예시는 `v4_검토/find_toy.py`로 고름).",
)
P.write_text(s, encoding="utf-8")
for m in re.finditer(r".{0,25}(그림 [1-4]|Fig\. [1-4]).{0,15}", s):
    print(m.group(0).replace("\n", " "))

"""v4 4.1에 실험 자료 그림(새 그림 3)을 넣고 기존 그림 3·4를 그림 4·5로 미룬다(2026-11-11 사용자: 분량은 신경 쓰지 말고 넣자).
그림 파일 이름은 그대로 둔다. 실행: py -I v4_검토/add_fig_data.py (원고 폴더에서)"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
P = Path(__file__).resolve().parent.parent / "논문_정보기술학회_v4.md"
s = P.read_text(encoding="utf-8")
assert "그림_자료.png" not in s, "이미 넣었음"

# 1) 기존 번호 미루기(4→5 먼저, 그다음 3→4). 파일 이름 '그림3_' 등은 건드리지 않는다.
s = re.sub(r"그림 4(?![_\d])", "그림 5", s)
s = s.replace("Fig. 4.", "Fig. 5.")
s = re.sub(r"그림 3(?![_\d])", "그림 4", s)
s = s.replace("Fig. 3.", "Fig. 4.")

# 2) 4.1 도로망 문장에 참조를 달고 첫 문단 뒤에 그림 넣기
old = "(노드 24,756개, 간선 평균 17.7 m, 476 km)."
assert s.count(old) == 1
s = s.replace(old, "(노드 24,756개, 간선 평균 17.7 m, 476 km, 그림 3).")
para_end = "둥근 정도가 가장 큰 값)으로 골랐다."
assert s.count(para_end) == 1
s = s.replace(para_end, para_end + "\n\n"
              "![그림 3](그림_v4/그림_자료.png)\n\n"
              "> **그림 3. 실험 도로망과 선호 항목별 노드 속성 (제주 도심 약 6.8 × 5.3 km, 회색: 도로망, 파랑: 해당 항목, ■ 출발점)**\n"
              "> **Fig. 3. Road network and node attributes used in the experiment**")

# 3) 초안 메모의 그림 목록
s = s.replace("그림 1 흐름도, 그림 4 구성 요소별 경로(연동, 중앙값 요청), 그림 5 선호별 경로(이도, 중앙값 요청).",
              "그림 1 흐름도, 그림 4 구성 요소별 경로(연동, 중앙값 요청), 그림 5 선호별 경로(이도, 중앙값 요청). "
              "그림 3 실험 자료 지도는 `그림_v4/make_fig_data.py`(로컬 DB와 노드속성_v3c.csv만 읽음).")
P.write_text(s, encoding="utf-8")
for m in re.finditer(r".{0,20}(그림 [1-5]|Fig\. [1-5]).{0,12}", s):
    print(m.group(0).replace("\n", " "))

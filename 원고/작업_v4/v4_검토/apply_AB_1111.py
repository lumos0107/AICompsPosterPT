"""4.2~결론 점검 반영(2026-11-11 사용자: A1·A2, B5·B6·B7). 실행: py -I v4_검토/apply_AB_1111.py (원고 폴더에서)"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
P = Path(__file__).resolve().parent.parent / "논문_정보기술학회_v4.md"
s = P.read_text(encoding="utf-8")
PAIRS = [
    # A1 그림 4 캡션: 수치가 오른쪽 아래 표로 옮겨 감
    ("칸 안 수치는 이 요청의 값, ■ 출발점", "오른쪽 아래 표는 이 요청의 값, ■ 출발점"),
    # A2 성공 정의에 맞춤(선호 실험엔 왕복형 0개라 숫자 같음)
    ("1,080회(96%)가 목표 거리를 지켰으나", "1,080회(96%)가 성공하였으나"),
    # B5 표 3으로 계산되는 값(−1.65/2.73 = 60.5%)에 맞춤
    ("신호 교차로는 최대 61% 줄고", "신호 교차로는 최대 약 60% 줄고"),
    ("intersections fell by up to 61%", "intersections fell by up to about 60%"),
    ("신호 교차로는 기준 평균의 61%,", "신호 교차로는 기준 평균의 약 60%,"),
    # B6 표 2 거리 오차를 %로(요약의 '평균 오차 3%'와 맞춤)
    ("| 거리 오차 | 0.06 | 0.06 | 0.04 | 0.03 |", "| 거리 오차 | 6% | 6% | 4% | 3% |"),
    # B7 측정이 아니라 탐색을 기존 점수로 함
    ("선호 비용을 지원하지 않아 기존 점수로 측정하였다.", "선호 비용을 지원하지 않아 기존 엔진의 점수로 탐색하였다."),
]
for a, b in PAIRS:
    n = s.count(a)
    print(n, "|", a[:40])
    assert n == 1, a
    s = s.replace(a, b)
P.write_text(s, encoding="utf-8")

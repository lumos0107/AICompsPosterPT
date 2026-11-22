"""영어판 그림 1(구조)·그림 2(진출 구간)를 만든다 (2026-11-13).

한글판 스크립트(make_fig_flow.py, make_fig_beam.py)를 고치지 않고, 라벨·글꼴·출력 이름만 바꾼 사본
make_fig_flow_en.py, make_fig_beam_en.py를 만들어 실행한다. 한글판을 고친 뒤 이 파일을 다시 돌리면 영어판도 따라간다.
바꿀 글이 한글판에서 사라지면 assert로 멈춘다.
실행: python make_en_figs12.py → 그림/그림1_구조_포스터_en.png, 그림/진출구간_빔_en.png
"""
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = ('plt.rcParams["font.family"] = "Malgun Gothic"', 'plt.rcParams["font.family"] = ["Arial", "Malgun Gothic"]')  # ①~⑤는 맑은 고딕으로

FLOW = [
    FONT,
    ('OUT = os.path.join(HERE, "그림", "그림1_구조_포스터.png")', 'OUT = os.path.join(HERE, "그림", "그림1_구조_포스터_en.png")'),
    ('"(a) 순환 경로의 구성"', '"(a) Loop route"'),
    ('    G = np.array([4.85, yc])', '    G = np.array([5.05, yc])'),
    ('ax.text(2.33, yc + 0.47, "② 진출 구간"', 'ax.text(2.33, yc + 0.47, "② Outbound part"'),
    ('ax.text(2.38, yc + 0.47, "빔 탐색(그림 2)"', 'ax.text(2.38, yc + 0.47, "beam search (Fig. 2)"'),
    ('ax.text(3.45, yc - 0.42, "④ 반환 구간"', 'ax.text(3.45, yc - 0.42, "④ Return part"'),
    ('ax.text(4.32, yc - 0.42, "최소 비용 탐색(식 (2))"', 'ax.text(4.42, yc - 0.42, "least-cost search (Eq. (2))"'),
    ('"진출 + 반환 = 목표 거리 $T$ (±10%)"', '"Outbound + return = $T$ (±10%)"'),
    ('ax.text(R[0] + 0.1, R[1] + 0.08, "③ 반환점"', 'ax.text(R[0] + 0.1, R[1] + 0.08, "③ Turnaround"'),
    ('ax.text(R[0] + 0.7, R[1] + 0.08, "(그림 3)", fontsize=FS_S, color=BLUE, ha="left", va="bottom")',
     'ax.text(R[0] + 0.12, R[1] - 0.07, "(Fig. 3)", fontsize=FS_S, color=BLUE, ha="left", va="top")'),
    ('"① 안내점"', '"① Guide point"'),
    ('"방향만 정함(직선 0.38$T$)"', '"sets direction only\\n(straight 0.38$T$)"'),
    ('ax.text(S[0] - 0.12, S[1], "출발점"', 'ax.text(S[0] - 0.12, S[1], "Start"'),
    ('("① 안내점 선택", ["출발점에서 직선", "0.38$T$ 떨어진 점", "(16방향 중 하나)"], False)',
     '("① Guide point", ["0.38$T$ straight", "from the start", "(1 of 16 directions)"], False)'),
    ('("② 진출 구간", ["다양성 빔 탐색", "(그림 2)"], True)', '("② Outbound", ["Diverse beam", "search (Fig. 2)"], True)'),
    ('("③ 반환점 후보", ["전체 길이가 $T$에", "가까운 노드 5개"], False)',
     '("③ Turnaround", ["5 candidates with", "total length near $T$"], False)'),
    ('("④ 반환 구간", ["최소 비용 탐색", "(식 (2))"], True)', '("④ Return", ["Least-cost search", "(Eq. (2))"], True)'),
    ('("⑤ 경로 선택", ["오차 ±10% 안에서", "최대 3개"], False)', '("⑤ Select", ["Error within ±10%,", "up to 3 routes"], False)'),
    ('FS_H, FS_B = 9.0, 8.2', 'FS_H, FS_B = 9.0, 7.8'),
    ('"(b) 처리 흐름"', '"(b) Processing flow"'),
    ('"+ 선호 비용 $p$"', '"uses cost $p$"'),
    ('    iw = 2.62', '    iw = 3.2'),
    ('"입력: 출발점 $s$, 목표 거리 $T$, 선호 가중치 $\\\\alpha$"', '"Input: start $s$, target distance $T$, weights $\\\\alpha$"'),
    ('"빔 9개마다 반복"', '"Repeat for each of the 9 beams"'),
    ('x5, ow = xs[4] + cw / 2, 1.15', 'x5, ow = xs[4] + cw / 2, 1.45'),
    ('"출력: 순환 경로"', '"Output: loop routes"'),
]
BEAM = [
    FONT,
    ('OUT = os.path.join(HERE, "그림", "진출구간_빔.png")', 'OUT = os.path.join(HERE, "그림", "진출구간_빔_en.png")'),
    ('"(a) 그림 1의 진출 구간은 빔 9개 중 하나(3개만 표시)"', '"(a) Fig. 1 outbound = 1 of 9 beams"'),
    ('"② 진출 구간"', '"② Outbound"'),
    ('"③ 반환점"', '"③ Turnaround"'),
    ('"① 안내점"', '"① Guide point"'),
    ('ax.text(-0.08, 0, "출발점"', 'ax.text(-0.14, 0, "Start"'),
    ('"● ×  누적 거리 0.51T에서 멈춤"', '"● ×  stop at 0.51T traveled"'),
    ('"(b) 한 단계: 점수가 가장 높은 이웃으로"', '"(b) One step: best-scoring neighbor"'),
    ('"다른 빔의 길"', '"other beam"'),
    ('"이 빔의 방위"', '"this beam\'s heading"'),
    ('"u(현재 노드)"', '"u (current node)"'),
    ('"신호 교차로\\n– 선호 비용"', '"traffic signal\\n– preference cost"'),
    ('"– 다른 빔과 겹침"', '"– overlap"'),
    ('"방위와 반대\\n– 방위 차이"', '"against heading\\n– heading gap"'),
    ('"점수 최고 → 다음 노드"', '"best score → next node"'),
    ('"다음 노드 점수 = 안내점 쪽 진행 – 선호 비용 – 방위 차이 – 다른 빔과 겹침"',
     '"Score = progress to guide point – preference cost – heading gap – overlap"'),
]

for src, rules in (("make_fig_flow.py", FLOW), ("make_fig_beam.py", BEAM)):
    s = open(os.path.join(HERE, src), encoding="utf-8").read()
    for a, b in rules:
        assert s.count(a) >= 1, (src, a)
        s = s.replace(a, b)
    dst = os.path.join(HERE, src.replace(".py", "_en.py"))
    open(dst, "w", encoding="utf-8").write(f'"""자동 생성: make_en_figs12.py가 {src}에서 라벨만 영어로 바꾼 사본. 직접 고치지 말 것."""\n' + s)
    subprocess.run([sys.executable, dst], check=True)

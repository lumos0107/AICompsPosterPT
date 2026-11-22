"""영어판 그림 3(반환점 선택)을 만든다 (2026-11-13).

원고 그림 스크립트(원고/작업_v5/그림_v4/make_fig_turn.py)를 고치지 않고, 라벨만 영어로 바꾼 사본
make_fig_turn_en.py를 이 폴더에 만들어 실행한다. 계산(가상 바둑판, 비용, 후보 선택)은 원고와 같다.
실행: python make_en_turn.py → 그림/turnaround_en.png
"""
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(os.path.dirname(HERE)), "원고", "작업_v5", "그림_v4", "make_fig_turn.py")
DST = os.path.join(HERE, "make_fig_turn_en.py")

s = open(SRC, encoding="utf-8").read()
R = [
    ('plt.rcParams["font.family"] = "Malgun Gothic"', 'plt.rcParams["font.family"] = "Arial"'),
    ('fig.savefig(os.path.join(HERE, "그림2_반환점.png")', 'fig.savefig(os.path.join(HERE, "그림", "turnaround_en.png")'),
    ('"강"', '"river"'),
    ('"출발점"', '"Start"'),
    ('"(a) 한 번 탐색해 후보 5개"', '"(a) One search gives 5 candidates"'),
    ('"색 점선: 한 번의 탐색으로 얻은 돌아오는 길"', '"Colored dashes: return paths from one search"'),
    ('"(b) 후보마다 다시 탐색해 선택"', '"(b) Re-search each, then pick"'),
    ('f"반환점 {NAME[k]}: 전체 {best[\'sum\']:,} m, 되밟기 {best[\'retr\']} m"',
     'f"Turnaround {NAME[k]}: total {best[\'sum\']:,} m, reuse {best[\'retr\']} m"'),
]
for a, b in R:
    assert s.count(a) == 1, a
    s = s.replace(a, b)
s = '"""자동 생성: make_en_turn.py가 원고 make_fig_turn.py에서 라벨만 영어로 바꾼 사본. 직접 고치지 말 것."""\n' + s
open(DST, "w", encoding="utf-8").write(s)
subprocess.run([sys.executable, DST], check=True)

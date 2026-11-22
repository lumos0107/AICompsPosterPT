"""인도 파일(N3L_A0033320)의 선이 면 테두리처럼 닫혀 있는지 잰다. 5월 사본, 읽기 전용.

표본 좌표에서 같은 길을 2~3m 간격으로 왕복하는 닫힌 선이 보여서 확인한다.
닫힘: 시작점과 끝점이 1m 안. 도로 쪽도 같은 방식으로 재서 비교한다.
"""
import os
import sys

import numpy as np

HERE = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\소구역점검_1109"
sys.path.insert(0, r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\데이터진단_1109\수집계획용\에이전트검토")
from lib_shp import FILES, read_shp

sys.stdout.reconfigure(encoding="utf-8")
out = open(os.path.join(HERE, "테두리점검.out"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out.write(s + "\n")


for key in ("sidewalk", "road"):
    P = [p for _, parts in read_shp(FILES[key], clip=True) for p in parts]
    L = np.array([float(np.hypot(*np.diff(p, axis=0).T).sum()) for p in P])
    gap = np.array([float(np.hypot(*(p[0] - p[-1]))) for p in P])
    closed = gap <= 1.0
    log(f"[{key}] 선 {len(P):,}개 {L.sum()/1000:,.1f}km, 닫힌 선 {closed.sum():,}개 ({closed.mean():.1%}), 닫힌 선의 길이 {L[closed].sum()/1000:,.1f}km ({L[closed].sum()/L.sum():.1%})")

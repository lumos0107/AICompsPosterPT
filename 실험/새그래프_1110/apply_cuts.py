"""영상으로 확인한 잘못된 평면 연결을 끊고 계단 간선을 빼서 최종 그래프를 만든다.
한 노드에서 '분리할 축'의 간선 둘을 새 노드로 옮긴다. 나머지 간선은 원래 노드에 남는다.
계단은 SRD001 면 안 길이 1m 이상인 간선을 뺀다(사용자 확인 2026-11-10).
실행: py -I apply_cuts.py
결과: 그래프_최종.npz, 끊은연결.csv, 최종그래프.out
"""
import csv
import os
import sys

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

HERE = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\새그래프_1110"
sys.stdout.reconfigure(encoding="utf-8")
out = open(os.path.join(HERE, "최종그래프.out"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out.write(s + "\n")
    out.flush()


d = dict(np.load(os.path.join(HERE, "그래프_새자료.npz")))
xy, A, B, L, narrow, island, stair = d["xy"], d["A"].copy(), d["B"].copy(), d["L"], d["narrow"], d["island"], d["stair_len"]
# 위치, 노드, 분리할 축(간선 2개). 남는 쪽은 원래 노드에 그대로.
CUTS = [
    ("공항지하차도", 160142, (67390, 67391), "지하차도 축을 지상 교차로에서 분리"),
    ("제2태흥교", 281364, (416025, 416026), "다리 밑 도로를 분리"),
    ("동명교", 46165, (67788, 67789), "다리 밑 도로를 분리"),
    ("제6광령교(광령4교차로)", 130258, (69735, 69736), "평화로 본선을 다리 위 도로에서 분리"),
    ("제4광령교", 133752, (69997, 69998), "평화로 본선을 다리 위 도로에서 분리"),
    ("해안육교", 140808, (70761, 70762), "육교 위 도로를 애조로에서 분리"),
    ("우남육교", 113003, (311955, 311956), "육교 위 도로를 중산간도로에서 분리"),
    ("색달육교", 120810, (312087, 312088), "육교 위 도로를 중산간도로에서 분리"),
    ("이름 없는 다리 B1295", 110490, (312125, 312126), "다리 밑 고리형 도로를 분리"),
    ("R13 애조로", 193297, (93830, 93865), "애조로 위 도로를 분리"),
]
N0 = len(xy)
newxy = []
rows = []
for name, n, (e1, e2), memo in CUTS:
    for e in (e1, e2):
        assert A[e] == n or B[e] == n, (name, e)
    nn = N0 + len(newxy)
    newxy.append(xy[n])
    for e in (e1, e2):
        if A[e] == n:
            A[e] = nn
        else:
            B[e] = nn
    rows.append(dict(위치=name, 원래노드=n, 새노드=nn, x=round(float(xy[n][0]), 1), y=round(float(xy[n][1]), 1), 옮긴간선1=e1, 옮긴간선2=e2, 메모=memo))
XY = np.vstack([xy, np.array(newxy)])
N = len(XY)
base = ~narrow & ~island
keep = base & (stair < 1)


def stat(a, b, m, name):
    n, lab = connected_components(coo_matrix((np.ones(int(m.sum())), (a[m], b[m])), shape=(N, N)), directed=False)
    Lc = np.bincount(lab[a[m]], weights=L[m], minlength=n)
    log(f"{name}: 도로 {L[m].sum() / 1000:,.1f}km, 요소 {int((Lc > 0).sum())}, 주 요소 비율 {Lc.max() / L[m].sum():.2%}")
    return lab, int(Lc.argmax())


stat(d["A"], d["B"], base, "끊기 전 (둘 다 제외)")
stat(A, B, base, "10곳 끊은 뒤")
lab, m = stat(A, B, keep, "10곳 끊고 계단 간선 뺀 뒤 (최종)")
main = keep & (lab[A] == m)
log(f"최종 주 요소 간선 {int(main.sum()):,}, 노드 {len(np.unique(np.r_[A[main], B[main]])):,}, {L[main].sum() / 1000:,.1f}km")
with open(os.path.join(HERE, "끊은연결.csv"), "w", encoding="utf-8-sig", newline="") as f:
    wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    wr.writeheader()
    wr.writerows(rows)
np.savez_compressed(os.path.join(HERE, "그래프_최종.npz"), xy=XY, A=A, B=B, L=L, rec=d["rec"], line=d["line"], a=d["a"], b=d["b"], keep=keep, main=main, narrow=narrow, island=island, stair_len=stair)
log("끝")

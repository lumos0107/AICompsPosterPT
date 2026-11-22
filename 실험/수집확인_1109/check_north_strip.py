"""제주 도심 도엽 범위(위도 33.515 북쪽 경계) 밖, 해안 쪽 띠에 잘려 나간 도로 길이를 0.005도 칸별로 센다. 읽기만 한다.
실행: py -I check_north_strip.py
"""
import sys

import numpy as np
from pyproj import Transformer

sys.stdout.reconfigure(encoding="utf-8")
G = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\새그래프_1110\그래프_최종.npz"
g = np.load(G)
xy, A, B, L, keep = g["xy"], g["A"], g["B"], g["L"], g["keep"]
to_wgs = Transformer.from_crs(5179, 4326, always_xy=True)
mid = (xy[A] + xy[B]) / 2
lo, la = to_wgs.transform(mid[:, 0], mid[:, 1])
lo, la = np.asarray(lo), np.asarray(la)
STEP = 0.005

m = keep & (la >= 33.515) & (lo >= 126.48) & (lo < 126.55)
print(f"위도 33.515 북쪽, 경도 126.480~126.550 최종 그래프 도로: {L[m].sum() / 1000:.2f}km, 간선 {int(m.sum())}")
for j in range(int(np.floor(33.515 / STEP)), int(np.floor(33.530 / STEP))):
    row = []
    for i in range(int(np.floor(126.48 / STEP)), int(np.floor(126.55 / STEP))):
        c = m & (np.floor(lo / STEP).astype(int) == i) & (np.floor(la / STEP).astype(int) == j)
        row.append(f"{L[c].sum() / 1000:4.2f}")
    print(f"위도 {j * STEP:.3f}~: " + " ".join(row))
print("열: 경도 " + " ".join(f"{i * STEP:.3f}" for i in range(int(np.floor(126.48 / STEP)), int(np.floor(126.55 / STEP)))))

# 탑동 출발점 1.8km(0.7T의 대략) 원 안에서 위도 33.515 북쪽 도로
p = np.array(Transformer.from_crs(4326, 5179, always_xy=True).transform(126.522, 33.515))
d = np.hypot(*(mid - p).T)
for r in (500, 1000, 1800):
    c = keep & (d <= r)
    n = c & (la >= 33.515)
    print(f"탑동 반경 {r}m 안 도로 {L[c].sum() / 1000:.2f}km 중 위도 33.515 북쪽 {L[n].sum() / 1000:.2f}km ({L[n].sum() / max(L[c].sum(), 1):.1%})")

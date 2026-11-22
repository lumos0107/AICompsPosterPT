"""1:1,000 도엽 번호 규칙을 받아 둔 95장으로 확인하고, 북쪽 확장에 필요한 칸의 번호를 만든다.
가정한 규칙: 앞 7자리 = 0.05도 칸(1:10,000), 끝 두 자리 = 그 안 10x10 칸을 북서쪽부터 행 우선 1~100 (100은 '00').
결과: 확장도엽.out, 확장도엽목록.csv
"""
import glob, os, struct, sys, csv, collections
import numpy as np
from pyproj import Transformer
sys.path.insert(0, r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\데이터진단_1109\수집계획용\에이전트검토")
from lib_shp import read_shp
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
out = open(os.path.join(HERE, "확장도엽.out"), "w", encoding="utf-8")
def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); out.write(s + "\n")
ROOT = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵\수치지형도_1000_표본"
S5186 = Transformer.from_crs(5186, 4326, always_xy=True)
to_wgs = Transformer.from_crs(5179, 4326, always_xy=True)
STEP = 0.005
known = {}
for sd in glob.glob(os.path.join(ROOT, "제주도심_95장", "풀기", "*")):
    if not os.path.isdir(sd): continue
    b = [np.inf, np.inf, -np.inf, -np.inf]
    for shp in glob.glob(os.path.join(sd, "*.shp")):
        d = open(shp, "rb").read(100); x0, y0, x1, y1 = struct.unpack("<4d", d[36:68])
        if x1 > x0 or y1 > y0: b = [min(b[0], x0), min(b[1], y0), max(b[2], x1), max(b[3], y1)]
    lo, la = S5186.transform((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
    known[(int(np.floor(lo / STEP)), int(np.floor(la / STEP)))] = os.path.basename(sd)
# 0.05도 칸별 앞 7자리
pref = {}
bad = 0
for (i, j), sh in known.items():
    I, J = i // 10, j // 10
    r = 9 - (j - J * 10); c = i - I * 10
    idx = r * 10 + c + 1
    if f"{idx % 100:02d}" != sh[-2:]: bad += 1
    pref.setdefault((I, J), set()).add(sh[:7])
log(f"받은 95장으로 규칙 확인: 끝 두 자리 불일치 {bad}건")
for k, v in sorted(pref.items()):
    log(f"  0.05도 칸 경도 {k[0] * 0.05:.2f}~ 위도 {k[1] * 0.05:.2f}~ : 앞 7자리 {sorted(v)}")
def number(i, j):
    I, J = i // 10, j // 10
    p = pref.get((I, J))
    if not p or len(p) != 1: return None
    r = 9 - (j - J * 10); c = i - I * 10
    return f"{next(iter(p))}{(r * 10 + c + 1) % 100:02d}"
# 최종 그래프 도로 길이를 칸별로
G = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\새그래프_1110"
ROAD = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\국토정보맵\연속수치지도_제주_20261109\풀기\N3L_A0020000\N3L_A0020000"
g = np.load(os.path.join(G, "그래프_최종.npz"))
lines = [p for r, parts in read_shp(ROAD, clip=False) for p in parts]
cellL = collections.Counter()
M, S = [], []
gl, ga, gb, gk = g["line"], g["a"], g["b"], g["keep"]  # npz는 접근마다 다시 풀므로 한 번만 읽는다
for e in np.where(gk)[0].tolist():
    p = lines[gl[e]][ga[e]:gb[e] + 1]
    M.append((p[1:] + p[:-1]) / 2); S.append(np.hypot(*np.diff(p, axis=0).T))
M, S = np.vstack(M), np.concatenate(S)
lo, la = to_wgs.transform(M[:, 0], M[:, 1])  # 한 번에 변환
ii, jj = np.floor(np.asarray(lo) / STEP).astype(int), np.floor(np.asarray(la) / STEP).astype(int)
sel = (ii >= 25290) & (ii <= 25315) & (jj >= 6690) & (jj <= 6715)
for a_, b_, s_ in zip(ii[sel].tolist(), jj[sel].tolist(), S[sel].tolist()):
    cellL[(a_, b_)] += s_
I0, I1 = 25296, 25309  # 경도 126.480~126.550
J_top = 6702            # 위도 33.510~33.515 (현재 맨 위 줄)
north = sum(v for (i, j), v in cellL.items() if I0 <= i <= I1 and j > J_top)
row1 = sum(v for (i, j), v in cellL.items() if I0 <= i <= I1 and j == J_top + 1)
log(f"\n경도 126.480~126.550, 위도 33.515 북쪽 최종 그래프 도로 {north / 1000:.1f}km, 바로 위 줄(33.515~33.520) {row1 / 1000:.1f}km")
rows = []
for j in range(J_top + 1, J_top + 10):
    for i in range(I0, I1 + 1):
        if cellL[(i, j)] > 0:
            rows.append(("북쪽 줄" if j == J_top + 1 else "그 위", i, j, cellL[(i, j)]))
for (i, j) in [(i, j) for i in range(I0, I1 + 1) for j in range(6696, J_top + 1) if (i, j) not in known]:
    rows.append(("빈 칸", i, j, cellL[(i, j)]))
row_cells = [(i, J_top + 1) for i in range(I0, I1 + 1)]
log(f"북쪽 줄 14칸 중 도로 있는 칸 {sum(cellL[c] > 0 for c in row_cells)}")
with open(os.path.join(HERE, "확장도엽목록.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f); w.writerow(["구분", "도엽번호", "경도", "위도", "도로m"])
    for kind, i, j, L in rows:
        n = number(i, j)
        w.writerow([kind, n, f"{i * STEP:.3f}~{(i + 1) * STEP:.3f}", f"{j * STEP:.3f}~{(j + 1) * STEP:.3f}", round(L)])
        log(f"{kind} {n} 경도 {i * STEP:.3f}~{(i + 1) * STEP:.3f} 위도 {j * STEP:.3f}~{(j + 1) * STEP:.3f} 도로 {L:.0f}m")
log(f"합계 {len(rows)}장, 도로 {sum(r[3] for r in rows) / 1000:.1f}km")

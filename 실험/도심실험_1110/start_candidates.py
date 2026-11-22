"""탑동이 도엽 밖이라 대체 후보를 같은 지표로 잰다. 후보 좌표는 지도에서 고른 공개 장소의 대략 위치(경위도)."""
import os, sys
import numpy as np
from pyproj import Transformer
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
g = np.load(os.path.join(HERE, "그래프_도심.npz"))
xy, A, B, L, main = g["xy"], g["A"], g["B"], g["L"], g["main"]
N = len(xy)
to_wgs = Transformer.from_crs(5179, 4326, always_xy=True); fw = Transformer.from_crs(4326, 5179, always_xy=True)
nodes = np.unique(np.r_[A[main], B[main]]); tn = cKDTree(xy[nodes])
W = coo_matrix((L[main], (A[main], B[main])), shape=(N, N)); W = W + W.T
lo0, lo1, la0, la1 = 126.480, 126.550, 33.480, 33.515
def inside(p):
    lo, la = to_wgs.transform(p[0], p[1]); return lo0 <= lo < lo1 and la0 <= la < la1  # 빈 칸 3개는 북쪽 끝(서쪽)이라 아래 후보와 무관함을 따로 확인
CAND = [("탑동(초안)", 33.515, 126.522, 3000),
        ("탑동 -> 도엽 안 가장 가까운 노드", None, None, 3000),
        ("동문로터리", 33.5125, 126.5277, 3000),
        ("제주종합경기장", 33.4925, 126.5105, 3000),
        ("신산공원", 33.5070, 126.5340, 3000)]
for nm, la, lo, T in CAND:
    if la is None:
        x, y = fw.transform(126.522, 33.515)
        dd, ii = tn.query([x, y], k=50)
        for d_, i_ in zip(dd, ii):
            if inside(xy[nodes[i_]]): s = int(nodes[i_]); break
        p = xy[s]; lo, la = to_wgs.transform(*p); dn = d_
    else:
        p = np.array(fw.transform(lo, la)); dn, i_ = tn.query(p); s = int(nodes[i_])
    ok = 0
    for ang in np.arange(16) * 22.5:
        t = p + 0.38 * T * np.array([np.sin(np.radians(ang)), np.cos(np.radians(ang))])
        if tn.query(t)[0] <= 200 and inside(t): ok += 1
    edge = min(abs(to_wgs.transform(*p)[0] - lo0) * 92600, abs(to_wgs.transform(*p)[0] - lo1) * 92600, abs(to_wgs.transform(*p)[1] - la0) * 111000, abs(to_wgs.transform(*p)[1] - la1) * 111000)
    reach = int(np.isfinite(dijkstra(W, indices=s, limit=0.6 * T)).sum())
    print(f"{nm} ({la:.5f}, {lo:.5f}) {T/1000:.0f}km: 도엽 안 {inside(p)}, 노드까지 {dn:.1f}m, 바깥 사각형 경계까지 약 {edge:.0f}m, 0.38T 16방향 중 안내점 가능 {ok}, 도로 거리 0.6T 안 노드 {reach:,}")

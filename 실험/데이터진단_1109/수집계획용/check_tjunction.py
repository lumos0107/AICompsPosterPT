"""도로중심선 끝점 중 다른 끝점과 만나지 않는 것이 다른 선의 중간에 닿는지 잰다. 읽기 전용."""
import glob
import os
import struct
import sys

import numpy as np
from scipy.spatial import cKDTree

sys.stdout.reconfigure(encoding="utf-8")
D = os.path.join(os.path.expanduser("~"), "Downloads")
p = glob.glob(os.path.join(D, "(연속수치지형도)도로중심선_제주", "**", "N3L_A0020000_50.shp"), recursive=True)[0]
data = open(p, "rb").read()
pos, lid = 100, 0
ends, end_id, vs, v_id, samp, samp_id = [], [], [], [], [], []
while pos < len(data):
    _, clen = struct.unpack(">2i", data[pos:pos + 8])
    s = pos + 8
    if struct.unpack("<i", data[s:s + 4])[0] != 0:
        np_, npts = struct.unpack("<2i", data[s + 36:s + 44])
        pts = np.frombuffer(data, "<f8", npts * 2, s + 44 + 4 * np_).reshape(-1, 2).copy()
        ends.append(pts[[0, -1]])
        end_id += [lid, lid]
        vs.append(pts)
        v_id.append(np.full(len(pts), lid))
        seg = np.hypot(*np.diff(pts, axis=0).T)
        cum = np.r_[0, np.cumsum(seg)]
        if cum[-1] > 0:
            t = np.r_[np.arange(0, cum[-1], 2.0), cum[-1]]
            samp.append(np.c_[np.interp(t, cum, pts[:, 0]), np.interp(t, cum, pts[:, 1])])
            samp_id.append(np.full(len(t), lid))
        lid += 1
    pos = s + clen * 2
ends = np.vstack(ends)
end_id = np.array(end_id)
vs, v_id = np.vstack(vs), np.concatenate(v_id)
samp, samp_id = np.vstack(samp), np.concatenate(samp_id)
print("선", lid, "끝점", len(ends), "꼭짓점", len(vs), "2m 표본", len(samp))

t = cKDTree(ends)
counts = np.array([len(g) for g in t.query_ball_point(ends, 0.01)])
open_idx = np.where(counts == 1)[0]
print(f"다른 끝점과 1cm 안에서 안 만나는 끝점 {len(open_idx):,}개 ({len(open_idx)/len(ends):.1%})")

tv = cKDTree(vs)
touch = 0
for i in open_idx:
    g = tv.query_ball_point(ends[i], 0.01)
    if any(v_id[j] != end_id[i] for j in g):
        touch += 1
print(f" 그중 다른 선의 중간 꼭짓점과 1cm 안에서 일치 {touch:,}개 ({touch/len(open_idx):.1%})")

ts = cKDTree(samp)
dist = np.full(len(open_idx), np.inf)
for n, i in enumerate(open_idx):
    d, j = ts.query(ends[i], k=40, distance_upper_bound=20)
    for a, b in zip(np.atleast_1d(d), np.atleast_1d(j)):
        if np.isfinite(a) and samp_id[b] != end_id[i]:
            dist[n] = a
            break
for lim in (2, 5, 10, 20):
    print(f" 다른 선까지 {lim}m 안(2m 표본 기준) {np.mean(dist <= lim):.1%}")

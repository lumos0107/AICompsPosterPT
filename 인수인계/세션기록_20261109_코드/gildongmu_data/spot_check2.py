"""검토 에이전트의 수치를 별도 구현으로 다시 잰다. 읽기 전용."""
import collections
import csv
import glob
import io
import os
import re
import struct
import sys

import numpy as np
import pdfplumber
from pyproj import Transformer
from scipy.spatial import cKDTree

sys.stdout.reconfigure(encoding="utf-8")
D = os.path.join(os.path.expanduser("~"), "Downloads")
ROOT = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\공공데이터포털"
X0, Y0, X1, Y1 = 873000, 1458000, 952000, 1559000


def lines(p):
    data = open(p, "rb").read()
    pos, idx = 100, 0
    while pos < len(data):
        _, clen = struct.unpack(">2i", data[pos:pos + 8])
        s = pos + 8
        if struct.unpack("<i", data[s:s + 4])[0] != 0:
            x0, y0, x1, y1 = struct.unpack("<4d", data[s + 4:s + 36])
            if x1 >= X0 and x0 <= X1 and y1 >= Y0 and y0 <= Y1:
                n_, m_ = struct.unpack("<2i", data[s + 36:s + 44])
                parts = list(np.frombuffer(data, "<i4", n_, s + 44)) + [m_]
                pts = np.frombuffer(data, "<f8", m_ * 2, s + 44 + 4 * n_).reshape(-1, 2)
                for a, b in zip(parts[:-1], parts[1:]):
                    if b - a >= 2:
                        yield idx, pts[a:b]
        pos = s + clen * 2
        idx += 1


def field(dbf, names):
    with open(dbf, "rb") as f:
        head = f.read(32)
        n = struct.unpack("<I", head[4:8])[0]
        hlen, rlen = struct.unpack("<2H", head[8:12])
        off, where = 1, {}
        while True:
            c = f.read(32)
            if c[0] == 13:
                break
            nm = c[:11].split(b"\0")[0].decode("cp949", "replace")
            if nm in names:
                where[nm] = (off, c[16])
            off += c[16]
        f.seek(hlen)
        out = {k: [] for k in names}
        for _ in range(n):
            r = f.read(rlen)
            for k, (o, l) in where.items():
                out[k].append(r[o:o + l].decode("cp949", "replace").strip())
    return out


def sample(pts, step):
    seg = np.hypot(*np.diff(pts, axis=0).T)
    cum = np.r_[0, np.cumsum(seg)]
    if cum[-1] <= 0:
        return pts[:1], 0.0
    t = np.r_[np.arange(0, cum[-1], step), cum[-1]]
    return np.c_[np.interp(t, cum, pts[:, 0]), np.interp(t, cum, pts[:, 1])], float(cum[-1])


rp = glob.glob(os.path.join(D, "(연속수치지형도)도로중심선_제주", "**", "N3L_A0020000_50.shp"), recursive=True)[0]
attr = field(rp[:-4] + ".dbf", ["RVWD", "PVQT"])
wid = np.array([float(v or 0) for v in attr["RVWD"]])
pv = np.array(attr["PVQT"])
L_all, S2, W3, S3, seg_a, seg_b, V_list, slices, pv_len = [], [], [], [], [], [], [], [], collections.Counter()
offset = 0
for i, pts in lines(rp):
    V_list.append(pts)
    slices.append((offset, offset + len(pts)))
    offset += len(pts)
    s2, L = sample(pts, 2.0)
    S2.append(s2)
    s3, _ = sample(pts, 3.0)
    S3.append(s3)
    W3.append(np.full(len(s3), wid[i]))
    pv_len[pv[i]] += L / 1000
V = np.vstack(V_list)
key = np.round(V * 100).astype(np.int64)
_, inv = np.unique(key, axis=0, return_inverse=True)
inv = inv.ravel()
a_all, b_all = [], []
for s, e in slices:
    a_all.append(inv[s:e - 1])
    b_all.append(inv[s + 1:e])
A, B = np.concatenate(a_all), np.concatenate(b_all)
keep = A != B
E = np.unique(np.c_[np.minimum(A[keep], B[keep]), np.maximum(A[keep], B[keep])], axis=0)
deg = np.bincount(E.ravel(), minlength=inv.max() + 1)
first = np.zeros(inv.max() + 1, dtype=np.int64)
first[inv[::-1]] = np.arange(len(inv))[::-1]
nodes3 = V[first[deg >= 3]]
print("노드", inv.max() + 1, "차수3+ 노드", len(nodes3))
print("포장 코드별 길이(km)", {k: round(v) for k, v in pv_len.items()}, "합", round(sum(pv_len.values())))
with pdfplumber.open(os.path.join(D, "연속수치지형도_데이터_설명서.pdf")) as pdf:
    seen = set()
    for page in pdf.pages:
        for line in (page.extract_text() or "").splitlines():
            if re.search(r"RDQ00\d", line) and line not in seen:
                seen.add(line)
                print("  코드표:", line[:70])

t3 = cKDTree(nodes3)
S2 = np.vstack(S2)
rng = np.random.default_rng(1109)
pick = S2[rng.choice(len(S2), 20000, replace=False)]
d, _ = t3.query(pick)
print(f"[무작위 도로 점 → 차수3+ 노드] 30m {np.mean(d<=30):.1%} (검토 61.3) / 50m {np.mean(d<=50):.1%} (검토 79.5)")

tr = Transformer.from_crs(4326, 5179, always_xy=True)


def load(label):
    p = glob.glob(os.path.join(ROOT, label, "*.csv"))[0]
    raw = open(p, "rb").read()
    for enc in ("utf-8-sig", "cp949"):
        try:
            return list(csv.DictReader(io.StringIO(raw.decode(enc))))
        except UnicodeDecodeError:
            continue


def xy(rows):
    return np.c_[tr.transform([float(r["경도"]) for r in rows], [float(r["위도"]) for r in rows])]


cx = xy(load("제주_어린이보호구역_교차로"))
d, _ = t3.query(cx)
print(f"[어린이 교차로 127] 20m {np.mean(d<=20):.1%} (78.7) / 30m {np.mean(d<=30):.1%} (82.7) / 50m {np.mean(d<=50):.1%} (89.0)")
std = load("횡단보도표준_제주특별자치도_서귀포시_횡단보도")
y = xy([r for r in std if r["보행자신호등유무"] == "Y"])
d, _ = t3.query(y)
print(f"[보행신호 {len(y)}개] 차수3+ 노드 10m 안 {np.mean(d<=10):.1%} (7.6) / 30m {np.mean(d<=30):.1%} / 50m {np.mean(d<=50):.1%}")
ty = cKDTree(y)
nbr = ty.query_ball_point(y, 50)
for k, label in [(385, "77.6"), (323, "70.3")]:
    cov = np.zeros(len(y), bool)
    for _ in range(k):
        gains = [(~cov[g]).sum() for g in nbr]
        b = int(np.argmax(gains))
        cov[nbr[b]] = True
    print(f"[탐욕 배치 {k}개] 844개 중 50m 포함 {cov.mean():.1%} (검토 {label})")

P3 = np.vstack(S3)
W3 = np.concatenate(W3)
tr3 = cKDTree(P3)
sp = glob.glob(os.path.join(D, "N3L_A0033320", "**", "N3L_A0033320.shp"), recursive=True)[0]
ind = []
for i, pts in lines(sp):
    s, L = sample(pts, 10.0)
    dd, _ = tr3.query(s)
    if np.mean(dd > 12) >= 0.8:
        ind.append((s, pts[[0, -1]], L))
print("[독립 인도]", len(ind), "개", round(sum(x[2] for x in ind) / 1000, 1), "km (3,362, 506.4)")
wide, rest = 0.0, []
for s, ep, L in ind:
    near = tr3.query_ball_point(s, 30)
    if np.mean([bool(g) and W3[g].max() >= 15 for g in near]) >= 0.8:
        wide += L / 1000
    else:
        rest.append((s, ep, L))
print(f" 폭 15m 이상 도로 30m 안 {wide:.1f} km (208.9), 나머지 {len(rest)}개 {sum(x[2] for x in rest)/1000:.1f} km")
ends = np.vstack([x[1] for x in rest])
parent = list(range(len(rest)))


def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


for i, j in cKDTree(ends).query_pairs(2.0):
    parent[find(i // 2)] = find(j // 2)
groups = collections.defaultdict(list)
for i in range(len(rest)):
    groups[find(i)].append(i)
none, link, link_km = 0, 0, 0.0
for g in groups.values():
    ep = np.vstack([rest[i][1] for i in g])
    dd, _ = tr3.query(ep)
    near = ep[dd <= 15]
    if len(near) == 0:
        none += 1
    elif len(near) >= 2:
        span = np.hypot(*(near[:, None] - near[None, :]).transpose(2, 0, 1)).max()
        if span >= 100:
            link += 1
            link_km += sum(rest[i][2] for i in g) / 1000
print(f" 묶음 {len(groups)}개 (1,556), 도로 15m 안 끝점 없는 묶음 {none} (1,331), 두 도로 지점(100m 이상) 잇는 묶음 {link}개 {link_km:.1f} km (5개, 1.0km)")

print("[기하 교차] 제주시내 상자에서 공유 꼭짓점 없이 교차하는 선분")
bx0, by0, bx1, by1 = 903000, 1498000, 918000, 1504000
idx = np.where((V[:, 0] > bx0) & (V[:, 0] < bx1) & (V[:, 1] > by0) & (V[:, 1] < by1))[0]
inside = np.zeros(len(V), bool)
inside[idx] = True
segs = []
for ln, (s, e) in enumerate(slices):
    if inside[s:e].any():
        for k in range(s, e - 1):
            if inv[k] != inv[k + 1]:
                segs.append((k, ln))
cells = collections.defaultdict(list)
C = 30.0
for n, (k, ln) in enumerate(segs):
    p, q = V[k], V[k + 1]
    for cx_ in range(int(min(p[0], q[0]) // C), int(max(p[0], q[0]) // C) + 1):
        for cy_ in range(int(min(p[1], q[1]) // C), int(max(p[1], q[1]) // C) + 1):
            cells[(cx_, cy_)].append(n)


def orient(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


found, tested = set(), 0
for lst in cells.values():
    for x in range(len(lst)):
        for y_ in range(x + 1, len(lst)):
            i, j = lst[x], lst[y_]
            if segs[i][1] == segs[j][1] or (i, j) in found:
                continue
            ki, kj = segs[i][0], segs[j][0]
            if {inv[ki], inv[ki + 1]} & {inv[kj], inv[kj + 1]}:
                continue
            tested += 1
            a, b, c, d_ = V[ki], V[ki + 1], V[kj], V[kj + 1]
            if orient(a, b, c) * orient(a, b, d_) < 0 and orient(c, d_, a) * orient(c, d_, b) < 0:
                found.add((i, j))
print(f" 선분 {len(segs):,}개, 검사 쌍 {tested:,}, 교차 {len(found)}건 (검토: 섬 전체 0건)")

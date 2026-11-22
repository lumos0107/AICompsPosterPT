"""검토 지적 중 결정에 영향을 주는 것을 직접 다시 잰다. 읽기 전용."""
import collections
import csv
import glob
import html
import io
import os
import re
import ssl
import struct
import sys
import urllib.request

import numpy as np
from scipy.spatial import cKDTree

sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\데이터\원본\공공데이터포털"
raw = open(glob.glob(os.path.join(ROOT, "제주_신호기현황", "*.csv"))[0], "rb").read()
rows = list(csv.DictReader(io.StringIO(raw.decode("cp949"))))
print("신호기 시별 기하구조", collections.Counter((r["주소"].split(" ")[1], r["기하구조"]) for r in rows).most_common())

D = os.path.join(os.path.expanduser("~"), "Downloads")
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
                np_, npts = struct.unpack("<2i", data[s + 36:s + 44])
                parts = list(np.frombuffer(data, "<i4", np_, s + 44)) + [npts]
                pts = np.frombuffer(data, "<f8", npts * 2, s + 44 + 4 * np_).reshape(-1, 2)
                for a, b in zip(parts[:-1], parts[1:]):
                    if b - a >= 2:
                        yield idx, pts[a:b]
        pos = s + clen * 2
        idx += 1


def sample(pts, step):
    seg = np.hypot(*np.diff(pts, axis=0).T)
    cum = np.r_[0, np.cumsum(seg)]
    if cum[-1] <= 0:
        return pts[:1]
    t = np.r_[np.arange(0, cum[-1], step), cum[-1]]
    return np.c_[np.interp(t, cum, pts[:, 0]), np.interp(t, cum, pts[:, 1])]


def field(dbf, name):
    with open(dbf, "rb") as f:
        head = f.read(32)
        n = struct.unpack("<I", head[4:8])[0]
        hlen, rlen = struct.unpack("<2H", head[8:12])
        off, pos_, ln = 1, None, None
        while True:
            c = f.read(32)
            if c[0] == 13:
                break
            nm = c[:11].split(b"\0")[0].decode("cp949", "replace")
            if nm == name:
                pos_, ln = off, c[16]
            off += c[16]
        f.seek(hlen)
        out = []
        for _ in range(n):
            r = f.read(rlen)
            out.append(r[pos_:pos_ + ln].decode("cp949", "replace").strip())
    return out


rp = glob.glob(os.path.join(D, "(연속수치지형도)도로중심선_제주", "**", "N3L_A0020000_50.shp"), recursive=True)[0]
wid = np.array([float(v or 0) for v in field(rp[:-4] + ".dbf", "RVWD")])
P, W = [], []
for i, pts in lines(rp):
    s = sample(pts, 3.0)
    P.append(s)
    W.append(np.full(len(s), wid[i]))
P, W = np.vstack(P), np.concatenate(W)
t = cKDTree(P)
sp = glob.glob(os.path.join(D, "N3L_A0033320", "**", "N3L_A0033320.shp"), recursive=True)[0]
kind = field(sp[:-4] + ".dbf", "KIND")
Q, K = [], []
for i, pts in lines(sp):
    s = sample(pts, 10.0)
    Q.append(s)
    K += [kind[i]] * len(s)
Q, K = np.vstack(Q), np.array(K)
print("인도 표본 KIND", collections.Counter(K.tolist()).most_common())

# 각 인도 표본에서 반경 60m 안의 가장 넓은 도로를 기준으로 폭별 거리를 본다
d0, j0 = t.query(Q)
near = t.query_ball_point(Q, 60)
wide = np.array([W[g].max() if g else 0 for g in near])
for lo, hi in [(0, 12), (12, 20), (20, 25), (25, 30), (30, 999)]:
    m = (wide >= lo) & (wide < hi)
    print(f"반경 60m 안 최대 폭 {lo}~{hi}m: 표본 {m.sum():,}, 가장 가까운 도로까지 12m 밖 {np.mean(d0[m] > 12):.1%}, 중앙값 {np.median(d0[m]):.1f}m")
for lo, hi in [(25, 30), (30, 999)]:
    m = (W[j0] >= lo) & (W[j0] < hi)
    print(f"가장 가까운 도로의 폭 {lo}~{hi}m: 표본 {m.sum():,}, 12m 밖 {np.mean(d0[m] > 12):.1%}, 중앙값 {np.median(d0[m]):.1f}m")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
url = "https://file.localdata.go.kr/file/public_restroom_info/info"
try:
    p = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=40, context=ctx).read().decode("utf-8", "replace")
    print("화장실 표준 페이지", len(p), re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", p)))[:260])
    print("내려받기 단서", list(dict.fromkeys(re.findall(r'(?:href|onclick)="([^"]*(?:down|Down|csv|xlsx)[^"]*)"', p)))[:10])
except Exception as e:
    print("화장실 표준 페이지 실패", repr(e)[:90])

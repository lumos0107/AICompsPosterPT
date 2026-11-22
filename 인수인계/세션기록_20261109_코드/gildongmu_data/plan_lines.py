"""제주 범위에서 도로중심선과 인도·보도·자전거·도로구간 선의 겹침을 잰다. 읽기 전용."""
import collections
import glob
import os
import struct
import sys

import numpy as np
from scipy.spatial import cKDTree

sys.stdout.reconfigure(encoding="utf-8")
D = os.path.join(os.path.expanduser("~"), "Downloads")
X0, Y0, X1, Y1 = 873000, 1458000, 952000, 1559000
FILES = {
    "도로중심선": ("(연속수치지형도)도로중심선_제주", "N3L_A0020000_50.shp"),
    "인도": ("N3L_A0033320", "N3L_A0033320.shp"),
    "보도중심선": ("국가기본도_보도중심선", "TN_FTPTH_CTLN.shp"),
    "자전거도로": ("국가기본도_자전거도로중심선", "TN_BCYCL_CTLN.shp"),
    "도로구간": ("(도로명주소)도로구간_제주", "TL_SPRD_MANAGE_50_202605.shp"),
}


def path(folder, name):
    return glob.glob(os.path.join(D, folder, "**", name), recursive=True)[0]


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
        return pts[:1], 0.0
    t = np.r_[np.arange(0, cum[-1], step), cum[-1]]
    return np.c_[np.interp(t, cum, pts[:, 0]), np.interp(t, cum, pts[:, 1])], float(cum[-1])


def dbf_values(p, wanted, indices=None):
    with open(p, "rb") as f:
        head = f.read(32)
        n = struct.unpack("<I", head[4:8])[0]
        hlen, rlen = struct.unpack("<2H", head[8:12])
        fields, off = [], 1
        while True:
            c = f.read(32)
            if c[0] == 13:
                break
            name = c[:11].split(b"\0")[0].decode("cp949", "replace")
            fields.append((name, off, c[16]))
            off += c[16]
        f.seek(hlen)
        out = {w: collections.Counter() for w in wanted}
        for i in range(n):
            r = f.read(rlen)
            if indices is not None and i not in indices:
                continue
            for name, o, l in fields:
                if name in out:
                    out[name][r[o:o + l].decode("cp949", "replace").strip()] += 1
    return out


layer = {}
for name, (folder, fn) in FILES.items():
    p = path(folder, fn)
    pts_all, km, ids, per = [], 0.0, set(), []
    for idx, pts in lines(p):
        s, L = sample(pts, 3.0 if name == "도로중심선" else 10.0)
        pts_all.append(s)
        km += L / 1000
        ids.add(idx)
        per.append((idx, s, pts[[0, -1]], L))
    layer[name] = {"pts": np.vstack(pts_all), "km": km, "n": len(per), "per": per, "path": p, "ids": ids}
    print(f"{name}: 제주 범위 선 {len(per):,}개, 길이 {km:,.0f} km")

road = cKDTree(layer["도로중심선"]["pts"])
print("== 도로중심선과의 거리 (표본점 비율, 길이 비율과 거의 같음)")
print("자료            0~2m   2~12m  12~30m 30~50m >50m")
for name in ["인도", "보도중심선", "자전거도로", "도로구간"]:
    d, _ = road.query(layer[name]["pts"])
    bins = [np.mean(d <= 2), np.mean((d > 2) & (d <= 12)), np.mean((d > 12) & (d <= 30)), np.mean((d > 30) & (d <= 50)), np.mean(d > 50)]
    print(f"{name:12s} " + " ".join(f"{b:6.1%}" for b in bins), f"(중앙값 {np.median(d):.1f}m)")
    layer[name]["d"] = d

print("== 서로 간 거리 (왼쪽 표본점 중 오른쪽 선이 12m 안에 있는 비율)")
for a in ["인도", "보도중심선", "자전거도로"]:
    for b in ["인도", "보도중심선", "자전거도로"]:
        if a != b:
            d, _ = cKDTree(layer[b]["pts"]).query(layer[a]["pts"])
            print(f"  {a} -> {b}: {np.mean(d <= 12):.1%}")

print("== 도로에서 떨어진 독립 보행 구간 (표본의 80% 이상이 도로에서 12m 초과)")
for name in ["인도", "보도중심선", "자전거도로"]:
    km_ind, ends, ok5, ok15, n = 0.0, 0, 0, 0, 0
    for idx, s, ep, L in layer[name]["per"]:
        d, _ = road.query(s)
        if np.mean(d > 12) >= 0.8:
            n += 1
            km_ind += L / 1000
            de, _ = road.query(ep)
            ends += 2
            ok5 += int((de <= 5).sum())
            ok15 += int((de <= 15).sum())
    print(f"  {name}: {n:,}개 {km_ind:,.0f} km, 끝점 중 도로 5m 안 {ok5/max(ends,1):.1%}, 15m 안 {ok15/max(ends,1):.1%}")

print("== 속성 값")
r = layer["도로중심선"]
v = dbf_values(r["path"][:-4] + ".dbf", ["RDDV", "DVYN", "SCLS", "ONSD", "REST", "PVQT"])
for k, c in v.items():
    print(" 도로중심선", k, c.most_common(8))
for name, w in [("인도", ["KIND", "QUAL", "BYYN", "SCLS"]), ("보도중심선", ["PMTR_SE", "MESRMTH_SE", "MNENT_NM"]), ("자전거도로", ["BCYKND_SE", "PMTR_SE", "MNENT_NM"])]:
    v = dbf_values(layer[name]["path"][:-4] + ".dbf", w, layer[name]["ids"])
    for k, c in v.items():
        print(f" {name}", k, c.most_common(6))

ep = np.vstack([e for _, _, e, _ in r["per"]])
t = cKDTree(ep)
same = sum(1 for g in t.query_ball_point(ep, 0.01) if len(g) > 1)
print(f"도로중심선 끝점 {len(ep):,}개 중 다른 끝점과 정확히(1cm) 만나는 것 {same/len(ep):.1%}")

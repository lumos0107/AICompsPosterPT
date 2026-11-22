"""SHP/DBF 읽기 도구. 읽기 전용."""
import os
import struct
import numpy as np

D = os.path.join(os.path.expanduser("~"), "Downloads")
X0, Y0, X1, Y1 = 873000, 1458000, 952000, 1559000
FILES = {
    "road": os.path.join(D, "(연속수치지형도)도로중심선_제주", "N3L_A0020000_50"),
    "sidewalk": os.path.join(D, "N3L_A0033320", "N3L_A0033320"),
    "foot": os.path.join(D, "국가기본도_보도중심선", "TN_FTPTH_CTLN"),
    "bike": os.path.join(D, "국가기본도_자전거도로중심선", "TN_BCYCL_CTLN"),
    "seg": os.path.join(D, "(도로명주소)도로구간_제주", "TL_SPRD_MANAGE_50_202605"),
}


def read_shp(base, clip=True):
    """반환: list of (record index(0-base), [part arrays]). bbox 교차 조건은 plan_lines.py와 같다."""
    data = open(base + ".shp", "rb").read()
    pos, idx, out = 100, 0, []
    while pos < len(data):
        _, clen = struct.unpack(">2i", data[pos:pos + 8])
        s = pos + 8
        st = struct.unpack("<i", data[s:s + 4])[0]
        if st != 0:
            x0, y0, x1, y1 = struct.unpack("<4d", data[s + 4:s + 36])
            if (not clip) or (x1 >= X0 and x0 <= X1 and y1 >= Y0 and y0 <= Y1):
                np_, npts = struct.unpack("<2i", data[s + 36:s + 44])
                parts = list(np.frombuffer(data, "<i4", np_, s + 44)) + [npts]
                pts = np.frombuffer(data, "<f8", npts * 2, s + 44 + 4 * np_).reshape(-1, 2).copy()
                out.append((idx, [pts[a:b] for a, b in zip(parts[:-1], parts[1:]) if b - a >= 2]))
        pos = s + clen * 2
        idx += 1
    return out


def dbf_fields(base):
    with open(base + ".dbf", "rb") as f:
        head = f.read(32)
        n = struct.unpack("<I", head[4:8])[0]
        hlen, rlen = struct.unpack("<2H", head[8:12])
        fields, off = [], 1
        while True:
            c = f.read(32)
            if c[0] == 13:
                break
            name = c[:11].split(b"\0")[0].decode("cp949", "replace")
            fields.append((name, chr(c[11]), off, c[16]))
            off += c[16]
    return n, hlen, rlen, fields


def dbf_columns(base, names, enc="cp949"):
    """요청 항목을 문자열 리스트(레코드 순서)로 돌려준다."""
    n, hlen, rlen, fields = dbf_fields(base)
    fmap = {f[0]: f for f in fields}
    out = {k: [None] * n for k in names}
    with open(base + ".dbf", "rb") as f:
        f.seek(hlen)
        buf = f.read(n * rlen)
    for i in range(n):
        r = buf[i * rlen:(i + 1) * rlen]
        for k in names:
            _, _, o, l = fmap[k]
            out[k][i] = r[o:o + l].decode(enc, "replace").strip()
    return out


def seg_length(p):
    return float(np.hypot(*np.diff(p, axis=0).T).sum())

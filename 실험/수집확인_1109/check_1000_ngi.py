"""NGI·NDA 도엽 묶음의 신호등·신호등제어기·조명·횡단보도를 집계한다. 글자 파일로 읽기만 한다.

사용: python -I check_1000_ngi.py <ngi 폴더> <결과 파일>
"""
import collections
import csv
import io
import os
import re
import sys

root, result = sys.argv[1:3]
sys.stdout.reconfigure(encoding="utf-8")
out = open(result, "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out.write(s + "\n")


LAYERS = {"신호등": ("C0493376", "용도"), "차단기": ("C0503375", "구분"), "조명": ("C0220000", "구분"), "횡단보도": ("A0043325", None)}
tot = {k: collections.Counter() for k in LAYERS}
count = collections.Counter()
has = collections.Counter()
years = collections.Counter()
ndas = sorted(f for f in os.listdir(root) if f.lower().endswith(".nda"))
for f in ndas:
    text = open(os.path.join(root, f), "rb").read().decode("cp949", "replace")
    blocks = {}
    for b in re.split(r"<LAYER_START>", text)[1:]:
        m = re.search(r'\$LAYER_NAME\s*"([^"]+)"', b)
        if m:
            blocks[m.group(1)] = b
    for k, (layer, field) in LAYERS.items():
        b = blocks.get(layer)
        if b is None:
            continue
        fields = re.findall(r'ATTRIB\("([^"]+)"', b)
        rows = list(csv.reader(io.StringIO("\n".join(x.strip() for x in re.findall(r"^\s*\d+,\s*.+$", b, flags=re.M))), skipinitialspace=True))
        count[k] += len(rows)
        has[k] += 1
        if field and field in fields:
            i = fields.index(field)
            tot[k].update(r[i] for r in rows if len(r) > i)
    xml = os.path.join(root, f[:-4] + ".xml")
    if os.path.exists(xml):
        t = open(xml, encoding="utf-8", errors="replace").read()
        m1, m2 = re.search(r"<촬영년도>(\d+)", t), re.search(r"<제작년도>(\d+)", t)
        years[(m1.group(1) if m1 else "?", m2.group(1) if m2 else "?")] += 1
log(f"NGI 도엽 {len(ndas)}장")
log("(촬영년도, 제작년도) 분포", years.most_common())
for k in LAYERS:
    log(f"{k}: {count[k]:,}건, {has[k]}장에 있음, 구분 {tot[k].most_common()}")

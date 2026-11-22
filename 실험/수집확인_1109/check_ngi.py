"""NGI·NDA 도엽 파일의 구조와 레이어별 건수를 본다. 글자 파일로 읽기만 한다. 사용: python -I check_ngi.py <ngi> <nda> <결과 파일>"""
import collections
import re
import sys

ngi, nda, result = sys.argv[1:4]
sys.stdout.reconfigure(encoding="utf-8")
out = open(result, "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out.write(s + "\n")


text = open(ngi, "rb").read().decode("cp949", "replace")
lines = text.splitlines()
log("NGI 줄 수", f"{len(lines):,}")
log("앞부분:", " | ".join(x.strip() for x in lines[:26]))
log("섹션 표지 상위:", collections.Counter(x.strip() for x in lines if x.strip().startswith(("<", "$"))).most_common(14))
parts = re.split(r"<LAYER_START>", text)[1:]
log("레이어 수", len(parts))
for p in parts:
    m = re.search(r"\$LAYER_NAME\s*\"?([^\"\r\n]+)\"?", p)
    name = m.group(1).strip() if m else "?"
    kinds = collections.Counter(re.findall(r"^\s*(POINT|LINESTRING|POLYGON|TEXT|NODE|MULTI\w+)\b", p, flags=re.M))
    log(f"  {name}: {dict(kinds)}")
log("\nNDA")
t2 = open(nda, "rb").read().decode("cp949", "replace")
l2 = t2.splitlines()
log("줄 수", f"{len(l2):,}")
log("앞부분:", " | ".join(x.strip() for x in l2[:24]))
for key in ("C0493376", "C0503375", "C0220000"):
    i = t2.find(key)
    log(f"\n[{key}] 위치 {i}", " | ".join(x.strip() for x in t2[i:i + 900].splitlines()[:24]) if i >= 0 else "없음")

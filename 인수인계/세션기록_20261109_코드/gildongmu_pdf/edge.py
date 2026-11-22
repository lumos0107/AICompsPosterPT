import sys, fitz, re
sys.stdout.reconfigure(encoding="utf-8")
d = fitz.open(sys.argv[1])
mm = 25.4/72
for i, p in enumerate(d):
    rows = []
    for b in p.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            t = "".join(s["text"] for s in l["spans"]).strip()
            if t:
                rows.append((round(l["bbox"][0]*mm), round(l["bbox"][1]*mm, 1), round(l["bbox"][3]*mm, 1), t))
    left = sorted([r for r in rows if r[0] < 95 and 27 < r[1] < 243], key=lambda r: r[1])
    right = sorted([r for r in rows if r[0] >= 95 and 27 < r[1] < 243], key=lambda r: r[1])
    print(f"p{i+1} 왼쪽 끝 y={left[-1][2]} '{left[-1][3][-28:]}' | 오른쪽 처음 '{right[0][3][:24]}' | 오른쪽 끝 y={right[-1][2]} '{right[-1][3][-28:]}'")

import sys, fitz
sys.stdout.reconfigure(encoding="utf-8")
d = fitz.open(sys.argv[1])
mm = 25.4/72
for pno in (0,1):
    p = d[pno]
    print("== page", pno+1, round(p.rect.width*mm,1), round(p.rect.height*mm,1))
    lines=[]
    for b in p.get_text("dict")["blocks"]:
        for l in b.get("lines",[]):
            t="".join(s["text"] for s in l["spans"]).strip()
            if t:
                s=l["spans"][0]
                lines.append((round(l["bbox"][1]*mm,1),round(l["bbox"][0]*mm,1),round(l["bbox"][2]*mm,1),round(s["size"],1),t[:26]))
    lines.sort()
    for x in lines[:60]: print(x)
try:
    import bs4; print("bs4", bs4.__version__)
except Exception as e: print("no bs4", e)

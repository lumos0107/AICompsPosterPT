import sys, fitz
src, outdir = sys.argv[1], sys.argv[2]
d = fitz.open(src)
for i, p in enumerate(d):
    p.get_pixmap(dpi=70).save(f"{outdir}/form_{i+1}.png")
print(len(d))

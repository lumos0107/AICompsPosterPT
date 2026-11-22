import sys, fitz, glob, os
src, outdir = sys.argv[1], sys.argv[2]
for f in glob.glob(outdir + "/draft_*.png"):
    os.remove(f)
d = fitz.open(src)
for i, p in enumerate(d):
    p.get_pixmap(dpi=100).save(f"{outdir}/draft_{i+1}.png")
print("pages", len(d))

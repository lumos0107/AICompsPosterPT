import fitz, sys
for tag, f in (("pdf", "논문_정보기술학회_v5.pdf"), ("hwp", "작업_v5/한글본/확인용.pdf")):
    d = fitz.open(f)
    for i, p in enumerate(d):
        r = p.search_for("Table 3.")
        if r:
            W = p.rect.width
            x0 = 0 if r[0].x0 < W / 2 else W / 2 - 15
            p.get_pixmap(dpi=170, clip=fitz.Rect(x0, r[0].y0 - 20, min(W, x0 + 290), r[0].y0 + 300)).save(f"작업_v5/_표3_{tag}.png")
            print(tag, "page", i + 1, "of", len(d))

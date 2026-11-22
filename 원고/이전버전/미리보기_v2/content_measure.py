"""장평 측정본에서 쪽 배치 빈칸을 빼고 내용 분량을 잰다.
쪽마다 단별로 글 블록·그림·표 선이 차지한 세로 구간을 합친다(사이 간격 4 mm 이하는 이어진 것으로 봄).
전체 폭 요소(표·머리)는 두 단 모두에 센다. 용량: 1쪽 197.5 mm(소속·사사 자리 제외), 2쪽부터 215 mm, 단 2개.
실행: python -I content_measure.py <pdf>"""
import sys
import fitz
MM = 25.4 / 72
d = fitz.open(sys.argv[1])
W = d[0].rect.width
TOP, BOT = 27.5, 242.5
total = 0.0
for pno, pg in enumerate(d):
    rects = [fitz.Rect(b[:4]) for b in pg.get_text("blocks") if b[4].strip() and not b[4].strip().startswith("- ")
             and b[1] * MM > TOP - 1]
    rects += [fitz.Rect(i["bbox"]) for i in pg.get_image_info()]
    rects += [fitz.Rect(dr["rect"]) for dr in pg.get_drawings() if dr["rect"].height < 200]
    bottom = (260 - 35) if pno == 0 else BOT
    used = []
    for col in (0, 1):
        x0, x1 = (0, W / 2) if col == 0 else (W / 2, W)
        iv = sorted((max(r.y0 * MM, TOP), min(r.y1 * MM, bottom)) for r in rects
                    if (r.x1 > x0 + 5 and r.x0 < x1 - 5) and r.y1 * MM > TOP)
        s, cur = 0.0, None
        for a, b in iv:
            if cur and a <= cur[1] + 4:
                cur[1] = max(cur[1], b)
            else:
                if cur: s += cur[1] - cur[0]
                cur = [a, b]
        if cur: s += cur[1] - cur[0]
        used.append(s)
    total += sum(used)
    print(f"{pno + 1}쪽: 왼쪽 {used[0]:.0f} mm, 오른쪽 {used[1]:.0f} mm")
cap = 2 * ((260 - 35 - TOP) + 4 * (BOT - TOP))
print(f"내용 합계 {total:.0f} 단-mm, 5쪽 용량 {cap:.0f} 단-mm, 비율 {total / cap:.3f}")

"""본 실험 교차 후보 중 새로 캡처한 곳만 4×4 모음으로 만든다. 결과: 교차모음_본실험새_??.jpg"""
import json, os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
ids = [c[0] for c in json.load(open(os.path.join(HERE, "capture_items_본실험.json"), encoding="utf-8"))]
big = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 26)
for k in range(0, len(ids), 16):
    sheet = Image.new("RGB", (1200, 1200), "white")
    for j, i in enumerate(ids[k:k + 16]):
        im = Image.open(os.path.join(HERE, "영상_표시_본실험", i + ".jpg")).crop((180, 170, 620, 610)).resize((300, 300))
        ImageDraw.Draw(im).text((6, 4), i, fill=(255, 255, 255), font=big, stroke_width=3, stroke_fill=(0, 0, 0))
        sheet.paste(im, ((j % 4) * 300, (j // 4) * 300))
    sheet.save(os.path.join(HERE, f"교차모음_본실험새_{k // 16 + 1:02d}.jpg"), quality=85)
print(len(ids), (len(ids) + 15) // 16)

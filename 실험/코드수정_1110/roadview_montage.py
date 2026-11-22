"""산지천 다리 3곳 로드뷰 판정 사진 모음 (카카오 로드뷰 2026년 3월 촬영, 좌표만 넘겨 받은 화면).
결과: 로드뷰/로드뷰모음_산지천.jpg   실행: py -I roadview_montage.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "로드뷰")
ITEMS = [("X171_b.png", "X171 가령로 다리 위 → 동쪽 둑길: 같은 높이, 횡단보도로 이어짐"),
         ("X171_d.png", "X171 가령로 다리 위 → 서쪽 골목: 같은 높이, 차가 들어옴"),
         ("X190_p140.png", "X190 연삼로 다리 서쪽 끝 → 남동 둑길: 보도와 같은 높이"),
         ("X190nw_p0.png", "X190 연삼로 다리 서쪽 끝 → 북서 둑길: 보도·광장과 같은 높이"),
         ("X191nw_p0.png", "X191 연삼로 다리 동쪽 끝 → 북쪽 둑길(도서관 쪽): 같은 높이"),
         ("X191se_p180.png", "X191 연삼로 다리 동쪽 끝 → 남쪽 둑길: 같은 높이, 보행자 통행")]
font = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 26)
W, H = 960, 600
canvas = Image.new("RGB", (W * 2, (H + 50) * 3), "white")
dr = ImageDraw.Draw(canvas)
for k, (fn, cap) in enumerate(ITEMS):
    im = Image.open(os.path.join(D, fn)).convert("RGB").resize((W, H))
    x, y = (k % 2) * W, (k // 2) * (H + 50)
    canvas.paste(im, (x, y + 50))
    dr.text((x + 10, y + 10), cap, fill="black", font=font)
canvas.save(os.path.join(D, "로드뷰모음_산지천.jpg"), quality=85)
print("끝")

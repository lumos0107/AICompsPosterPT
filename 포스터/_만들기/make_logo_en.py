"""영어판 포스터용 제주대 로고(영문만) (2026-11-13).

원본 로고(그림/제주대로고.png, 한글 '제주대학교' + 작은 영문)에서 왼쪽 문양만 잘라 쓰고,
오른쪽에 'JEJU / NATIONAL / UNIVERSITY'를 원본 글자색(회색)으로 세 줄로 크게 새로 쓴다.
원본이 551×219로 작아 3배로 키운 캔버스에 그린다(문양은 확대, 글자는 새로 그려 선명).
실행: python make_logo_en.py → 그림/제주대로고_영문.png
"""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "그림", "제주대로고.png")
OUT = os.path.join(HERE, "그림", "제주대로고_영문.png")
K = 3                                   # 확대 배율
COLOR = (114, 112, 113, 255)            # 원본 글자색(잰 값)
FONT = "C:/Windows/Fonts/NotoSans-Bold.ttf"
LINES = ["JEJU", "NATIONAL", "UNIVERSITY"]

src = Image.open(SRC).convert("RGBA")
sym = src.crop((10, 5, 156, 205))       # 문양(잉크 x 15~150, y 10~199)
sym = sym.resize((sym.width * K, sym.height * K), Image.LANCZOS)
H = sym.height
pitch = H / len(LINES)                  # 줄 간격: 세 줄이 문양 높이를 채우게
probe = ImageFont.truetype(FONT, 100)
cap100 = probe.getbbox("H")[3] - probe.getbbox("H")[1]
size = int(round(0.66 * pitch / cap100 * 100))
font = ImageFont.truetype(FONT, size)
cap = font.getbbox("H")[3] - font.getbbox("H")[1]
gap = int(0.16 * H)
tw = max(font.getlength(t) for t in LINES)
canvas = Image.new("RGBA", (int(sym.width + gap + tw + 0.04 * H), H), (255, 255, 255, 0))
canvas.alpha_composite(sym, (0, 0))
d = ImageDraw.Draw(canvas)
for i, t in enumerate(LINES):
    base = i * pitch + (pitch + cap) / 2
    d.text((sym.width + gap, base), t, font=font, fill=COLOR, anchor="ls")
canvas.save(OUT)
print("저장:", OUT, canvas.size, "글자 크기", size)

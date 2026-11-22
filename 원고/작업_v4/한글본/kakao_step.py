"""카톡 '나와의 채팅'(강승준) 창 찾기와 화면 캡처(전송 전 확인용). 실행: py -I 한글본/kakao_step.py"""
import sys

from PIL import ImageGrab
from pywinauto import Desktop

sys.stdout.reconfigure(encoding="utf-8")
wins = [w for w in Desktop(backend="win32").windows() if w.is_visible() and w.window_text() in ("강승준", "카카오톡")]
for w in wins:
    r = w.rectangle()
    print(repr(w.window_text()), w.class_name(), (r.left, r.top, r.right, r.bottom))
img = ImageGrab.grab(all_screens=True)
print("화면 크기", img.size)
img.save(r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\원고\작업_v4\한글본\_screen.png")

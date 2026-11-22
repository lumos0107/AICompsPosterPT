"""카톡 '나와의 채팅'(강승준)으로 파일 보내기. 단계별로 실행하고 매번 캡처로 확인한다.
  py -I 한글본/kakao_send.py look          : 창을 앞으로 가져와 캡처(_k_look.png)
  py -I 한글본/kakao_send.py clip X Y      : 창 기준 (X, Y)를 클릭하고 캡처
  py -I 한글본/kakao_send.py open          : 열기 대화상자에 폴더·파일 이름 넣고 '열기'
  py -I 한글본/kakao_send.py send          : '파일 전송' 창의 'N개 전송' 클릭
"""
import sys
import time

from PIL import ImageGrab
from pywinauto import Desktop

sys.stdout.reconfigure(encoding="utf-8")
OUTDIR = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\원고\작업_v4\한글본"
FOLDER = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\원고"
FILES = ['"논문_정보기술학회_v4.hwp"', '"논문_정보기술학회_v4.pdf"']


def chat():
    ws = [w for w in Desktop(backend="win32").windows() if w.is_visible() and w.window_text() == "강승준"
          and w.class_name() == "EVA_Window_Dblclk"]
    assert len(ws) == 1, f"강승준 창 {len(ws)}개"
    return ws[0]


def shot(name, win=None):
    time.sleep(0.8)
    img = (win or chat()).capture_as_image()
    img.save(f"{OUTDIR}\\{name}")
    print("캡처", name, img.size)


cmd = sys.argv[1]
if cmd == "look":
    w = chat()
    w.set_focus()
    r = w.rectangle()
    print("창", (r.left, r.top, r.width(), r.height()))
    shot("_k_look.png", w)
elif cmd == "clip":
    w = chat()
    w.set_focus()
    w.click_input(coords=(int(sys.argv[2]), int(sys.argv[3])))
    time.sleep(1.2)
    dlg = [d for d in Desktop(backend="win32").windows() if d.is_visible() and d.class_name() == "#32770"]
    print("대화상자", [(d.window_text(), d.rectangle()) for d in dlg])
    if dlg:
        shot("_k_dlg.png", dlg[0])
    else:
        shot("_k_after.png", w)
elif cmd == "open":
    dlg = [d for d in Desktop(backend="win32").windows() if d.is_visible() and d.class_name() == "#32770"][0]
    print("대화상자", dlg.window_text())
    d = Desktop(backend="win32").window(handle=dlg.handle)
    edit = d.child_window(class_name="Edit", found_index=0)
    edit.set_edit_text(FOLDER)
    edit.type_keys("{ENTER}")
    time.sleep(1.2)
    edit = d.child_window(class_name="Edit", found_index=0)
    edit.set_edit_text(" ".join(FILES))
    time.sleep(0.5)
    shot("_k_open.png", dlg)
    d.child_window(title="열기(&O)", class_name="Button").click()
    time.sleep(1.5)
    tops = [x for x in Desktop(backend="win32").windows() if x.is_visible() and ("전송" in x.window_text() or x.window_text() == "")
            and x.class_name().startswith("EVA")]
    print("카톡 창들", [(x.window_text(), x.class_name(), x.rectangle()) for x in tops][:6])
    ImageGrab.grab(all_screens=True).save(f"{OUTDIR}\\_k_full.png")
elif cmd == "send":
    print("수동 확인 후 진행")

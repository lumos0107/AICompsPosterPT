"""학회 한글 양식 사본을 새 한글 인스턴스로 열어 문단마다 스타일 번호·이름과 글머리를 출력한다(읽기만, 저장 안 함).
사용자가 열어 둔 한글 창(GetActiveObject)에는 붙지 않는다. 끝나면 내가 띄운 한글 프로세스만 닫는다.
실행: py -I 한글본/probe_template.py (작업_v4 폴더에서)"""
import os
import shutil
import sys

import psutil
import win32com.client as win32

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(os.path.dirname(HERE)), "학술대회논문양식_표준형식.hwp")
COPY = os.path.join(HERE, "양식분석", "양식_사본.hwp")
shutil.copyfile(SRC, COPY)

before = {p.pid for p in psutil.process_iter(["name"]) if (p.info["name"] or "").lower().startswith("hwp")}
hwp = win32.Dispatch("HWPFrame.HwpObject")
print("모듈 등록", hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule"))
try:
    hwp.Open(COPY, "HWP", "forceopen:true")
    names = {}
    # 스타일 이름 목록
    i = 0
    hwp.MovePos(2, 0, 0)
    seen = 0
    while True:
        hwp.HAction.GetDefault("Style", hwp.HParameterSet.HStyle.HSet)
        idx = hwp.HParameterSet.HStyle.Apply
        hwp.Run("MoveSelParaEnd")
        txt = hwp.GetTextFile("TEXT", "saveblock").strip().replace("\r\n", " ")[:50]
        hwp.Run("Cancel")
        pos = hwp.GetPos()
        print(f"{seen:3d} 위치{pos} 스타일{idx:2d} | {txt}")
        seen += 1
        if not hwp.HAction.Run("MoveNextParaBegin") or seen > 80:
            break
finally:
    after = [p for p in psutil.process_iter(["name"]) if (p.info["name"] or "").lower().startswith("hwp") and p.pid not in before]
    try:
        hwp.Clear(1)
    except Exception:
        pass
    for p in after:
        p.kill()
    print("닫음", [p.pid for p in after])

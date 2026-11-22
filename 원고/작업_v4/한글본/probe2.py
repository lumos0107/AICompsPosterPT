"""양식 사본에서 견본 문단(장 제목, 본문, 표·그림 캡션, 식, 참고문헌, 표 칸)의 글자·문단 모양을 읽어 출력한다. 저장 안 함.
실행: py -I 한글본/probe2.py (작업_v4 폴더에서)"""
import os
import sys

import psutil
import win32com.client as win32

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
COPY = os.path.join(HERE, "양식분석", "양식_사본.hwp")
SAMPLES = ["한글제목", "저자*", "영문제목", "요  약", "초기의 SFF", "Abstract", "The previous", "Key words", "shape recovery",
           "*소속", "※ 지원기관", "Ⅰ. 서", "비접촉 삼차원", "표 1. 실험", "Table 1. Exp", "데이터개수", "2,000", "Ⅱ. 초점",
           "phi", "위 식에서", "그림 1. 그림제목", "Fig. 1. 영문", "참 고 문 헌", "[1] S. K. Nayar", "논문 양은"]

before = {p.pid for p in psutil.process_iter(["name"]) if (p.info["name"] or "").lower().startswith("hwp")}
hwp = win32.Dispatch("HWPFrame.HwpObject")
hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")


def find(s):
    hwp.MovePos(2, 0, 0)
    ps = hwp.HParameterSet.HFindReplace
    hwp.HAction.GetDefault("RepeatFind", ps.HSet)
    ps.FindString = s
    ps.Direction = 0
    ps.IgnoreMessage = 1
    ps.FindType = 1
    return hwp.HAction.Execute("RepeatFind", ps.HSet)


try:
    hwp.Open(COPY, "HWP", "forceopen:true")
    for s in SAMPLES:
        ok = find(s)
        if not ok:
            print(f"[없음] {s}")
            continue
        pos = hwp.GetPos()
        hwp.Run("Cancel")
        cs = hwp.HParameterSet.HCharShape
        hwp.HAction.GetDefault("CharShape", cs.HSet)
        ps = hwp.HParameterSet.HParaShape
        hwp.HAction.GetDefault("ParaShape", ps.HSet)
        print(f"[{s}] 위치{pos} 글꼴 {cs.FaceNameHangul}/{cs.FaceNameLatin} {cs.Height / 100:.1f}pt 장평{cs.RatioHangul} 자간{cs.SpacingHangul} 굵게{cs.Bold} "
              f"| 정렬{ps.AlignType} 들여{ps.Indentation} 왼{ps.LeftMargin} 줄간격{ps.LineSpacing}({ps.LineSpacingType}) 위{ps.PrevSpacing} 아래{ps.NextSpacing}")
    # 식 문단 원문(탭 여부)
    if find("위 식에서"):
        hwp.Run("Cancel")
        hwp.Run("MovePrevParaBegin")
        hwp.Run("MoveSelParaEnd")
        print("식 문단:", repr(hwp.GetTextFile("UNICODE", "saveblock")))
        hwp.Run("Cancel")
    # 단 정의
    ctrl = hwp.HeadCtrl
    while ctrl:
        if ctrl.CtrlID in ("cold", "secd", "gso", "tbl", "$pic", "eqed"):
            print("조판부호", ctrl.CtrlID, ctrl.UserDesc)
        ctrl = ctrl.Next
finally:
    try:
        hwp.Clear(1)
    except Exception:
        pass
    for p in psutil.process_iter(["name"]):
        if (p.info["name"] or "").lower().startswith("hwp") and p.pid not in before:
            p.kill()

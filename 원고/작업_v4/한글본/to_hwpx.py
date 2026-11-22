"""v4 hwp -> hwpx 저장 (한글 COM 새 인스턴스). 원본은 건드리지 않음.
사용: python -I to_hwpx.py 입력.hwp 출력.hwpx
"""
import os
import sys

import psutil
import win32com.client as win32

src, dst = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
if os.path.exists(dst):
    sys.exit(f"이미 있음: {dst}")


def hwp_pids():
    return {p.pid for p in psutil.process_iter(["name"]) if (p.info["name"] or "").lower().startswith("hwp")}


before = hwp_pids()
hwp = win32.Dispatch("HWPFrame.HwpObject")
mine = hwp_pids() - before
print("module", hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule"))
try:
    print("open hwp", hwp.Open(src, "HWP", "forceopen:true"))
    pages_src = hwp.PageCount
    text_src = hwp.GetTextFile("UNICODE", "")
    print("saveas hwpx", hwp.SaveAs(dst, "HWPX", ""))
    hwp.Clear(1)
    print("reopen hwpx", hwp.Open(dst, "HWPX", "forceopen:true"))
    pages_dst = hwp.PageCount
    text_dst = hwp.GetTextFile("UNICODE", "")
    hwp.Clear(1)
    print("pages", pages_src, pages_dst)
    print("text chars", len(text_src), len(text_dst), "same" if text_src == text_dst else "DIFF")
finally:
    try:
        hwp.Quit()
    except Exception:
        pass
    for p in psutil.process_iter(["pid"]):
        if p.pid in mine and p.is_running():
            p.kill()
print("size", os.path.getsize(dst))

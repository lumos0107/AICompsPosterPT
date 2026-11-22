import sys
sys.stdout.reconfigure(encoding="utf-8")
from fontTools.ttLib import TTFont
for f in ["H2MJSM.TTF","H2MJRE.TTF","H2GTRM.TTF","H2GTRE.TTF"]:
    t = TTFont(r"C:\Windows\Fonts\%s" % f, lazy=True)
    seen = set()
    for r in t["name"].names:
        if r.nameID in (1,4,6,16):
            try:
                seen.add((r.nameID, r.toUnicode()))
            except Exception:
                pass
    print(f, sorted(seen))

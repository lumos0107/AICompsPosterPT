import sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
import fitz
wanted = ["H2MJRE","H2MJSM","H2GTRM","H2GTRE","H2GSRB","H2HDRM","HMKMRHD","HMFMMUEX","HMFMOLD","HYHWPEQ","HANDotum","HANBatang"]
for f in sorted(Path(r"C:\Windows\Fonts").iterdir()):
    if any(f.name.upper().startswith(w.upper()) for w in wanted):
        try:
            print(f.name, "|", fitz.Font(fontfile=str(f)).name)
        except Exception as e:
            print(f.name, "ERR", e)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch()
    print("chromium", b.version)
    b.close()

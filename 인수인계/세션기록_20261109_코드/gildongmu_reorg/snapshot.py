"""논문 폴더의 파일 목록(상대경로, 크기)을 기록한다. 읽기 전용. 긴 경로도 읽는다."""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
root = "\\\\?\\C:\\Users\\seungjun\\Documents\\claude_code\\논문"
out = sys.argv[1]
items, errs = {}, 0
for d, dirs, files in os.walk(root):
    for f in files:
        p = os.path.join(d, f)
        try:
            items[os.path.relpath(p, root).replace("\\", "/")] = os.path.getsize(p)
        except OSError as e:
            errs += 1
            print("ERR", p[-80:], e)
json.dump(items, open(out, "w", encoding="utf-8"), ensure_ascii=False)
print("files", len(items), "bytes", sum(items.values()), "errors", errs)

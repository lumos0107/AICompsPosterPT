"""이동 전후 파일을 (파일 이름, 크기) 묶음으로 대조한다. 읽기 전용."""
import collections
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
before = json.load(open("before.json", encoding="utf-8"))
after = json.load(open("after.json", encoding="utf-8"))
archive = "\\\\?\\C:\\Users\\seungjun\\Documents\\claude_code\\기타\\_정리보관\\논문_writing_빈폴더_1109"
arch = {}
for d, _, fs in os.walk(archive):
    for f in fs:
        p = os.path.join(d, f)
        arch[os.path.relpath(p, archive)] = os.path.getsize(p)
print("보관으로 옮긴 파일:", list(arch))
key = lambda k, v: (k.replace("\\", "/").split("/")[-1], v)
a = collections.Counter(key(k, v) for k, v in before.items())
b = collections.Counter(key(k, v) for k, v in after.items())
b.update(key(k, v) for k, v in arch.items())
print("이전 파일 수", len(before), "이후 파일 수", len(after), "+ 보관", len(arch))
print("이전 바이트", sum(before.values()), "이후 바이트", sum(after.values()) + sum(arch.values()))
missing = a - b
extra = b - a
print("없어진 것", sum(missing.values()), list(missing.items())[:20])
print("새로 생긴 것", sum(extra.values()), list(extra.items())[:20])

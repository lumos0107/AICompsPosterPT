"""지난 세션 대화 원본에서 1:1,000 내려받기 때 쓴 Playwright 호출 코드를 뽑아 파일로 저장한다.
실행: py -I dump_pw_calls.py
"""
import json
import os
import sys

SRC = r"C:\Users\seungjun\.claude\projects\c--Users-seungjun-Documents-claude-code\3045652e-d54b-4788-ae7c-72551d95155f.jsonl"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pw_calls.txt")
start = int(sys.argv[1]) if len(sys.argv) > 1 else 2150
end = int(sys.argv[2]) if len(sys.argv) > 2 else 2400
with open(SRC, encoding="utf-8") as f, open(OUT, "w", encoding="utf-8") as o:
    for n, line in enumerate(f, 1):
        if n < start or n > end:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        msg = d.get("message") or {}
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for c in content:
            if c.get("type") == "tool_use" and "playwright" in c.get("name", ""):
                inp = c.get("input", {})
                code = inp.get("code") or json.dumps(inp, ensure_ascii=False)
                o.write(f"===== line {n} {c['name']}\n{code[:2500]}\n")
            elif c.get("type") == "text" and msg.get("role") == "user":
                o.write(f"----- line {n} USER: {c['text'][:200]}\n")
            elif c.get("type") == "text" and msg.get("role") == "assistant":
                o.write(f"----- line {n} ME: {c['text'][:300]}\n")
print(OUT)

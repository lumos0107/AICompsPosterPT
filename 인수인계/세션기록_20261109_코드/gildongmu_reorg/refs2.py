"""스크립트의 HERE·EXP 사용, md 링크, 다른 프로젝트의 참조를 뽑는다. 읽기 전용."""
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
base = r"C:\Users\seungjun\Documents\claude_code"
root = os.path.join(base, "논문")
skip = {"node_modules", ".git", ".gradle", "build", "bin", "__pycache__", "--main", "backend_latest", ".venv", "venv", "dist"}

print("=== writing 스크립트의 HERE 사용")
for f in sorted(os.listdir(os.path.join(root, "writing"))):
    if f.endswith(".py"):
        for i, line in enumerate(open(os.path.join(root, "writing", f), encoding="utf-8", errors="replace"), 1):
            if re.search(r"\bHERE\b|\bFIG\b\s*,|open\(['\"]|sys\.path", line) and "abspath(__file__)" not in line and len(line) < 300:
                print(f"{f}:{i}: {line.strip()[:150]}")

print("=== experiments EXP / .. / sys.path")
for d, dirs, files in os.walk(os.path.join(root, "experiments")):
    dirs[:] = [x for x in dirs if x not in skip | {"src"}]
    for f in files:
        if f.endswith((".py", ".sh")):
            p = os.path.join(d, f)
            for i, line in enumerate(open(p, encoding="utf-8", errors="replace"), 1):
                if re.search(r"\bEXP\b|\"\.\.\"|'\.\.'|sys\.path|cd \.\.|\.\./", line) and "abspath(__file__)); EXP" not in line and len(line) < 300:
                    print(f"{os.path.relpath(p, root)}:{i}: {line.strip()[:150]}")

print("=== md·html 링크")
link = re.compile(r"\]\(([^)\s]+)\)|\bsrc=\"([^\"]+)\"")
for d, dirs, files in os.walk(root):
    dirs[:] = [x for x in dirs if x not in skip | {"_inbox", "source", "experiments"}]
    for f in files:
        if f.endswith((".md", ".html")):
            p = os.path.join(d, f)
            for line in open(p, encoding="utf-8", errors="replace"):
                for m in link.finditer(line):
                    t = m.group(1) or m.group(2)
                    if not t.startswith(("http", "#", "data:", "mailto")):
                        print(f"{os.path.relpath(p, root)} -> {t[:90]}")

print("=== 다른 프로젝트에서 논문 폴더 참조")
pat = re.compile(r"논문[/\\]+(experiments|writing|_inbox|handoff|reading|specs|source|MASTER|팀최신본)")
for d, dirs, files in os.walk(base):
    if os.path.abspath(d).startswith(root):
        dirs[:] = []
        continue
    dirs[:] = [x for x in dirs if x not in skip]
    for f in files:
        if f.lower().endswith((".md", ".py", ".sh", ".txt", ".json", ".ps1", ".bat", ".html", ".yml", ".yaml")):
            p = os.path.join(d, f)
            try:
                if os.path.getsize(p) > 3_000_000:
                    continue
                n = 0
                for line in open(p, encoding="utf-8", errors="replace"):
                    if pat.search(line):
                        n += 1
                if n:
                    print(f"{n}  {os.path.relpath(p, base)}")
            except OSError:
                pass

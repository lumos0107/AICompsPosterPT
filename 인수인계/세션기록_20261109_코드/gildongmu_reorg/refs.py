"""코드·문서에서 폴더 경로를 참조하는 줄을 뽑는다. 읽기 전용."""
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
root = r"C:\Users\seungjun\Documents\claude_code\논문"
skip = {"node_modules", ".git", ".gradle", "build", "bin", "__pycache__", "--main", "backend_latest", "src"}
code_ext = {".py", ".sh", ".bat", ".html", ".gradle", ".ps1"}
pat = re.compile(r"figures|drafts|_inbox|experiments|writing|handoff|reading|mockup|icons|references|loopv2_run|v1_run|v2_run|v2b_run|v2_graph|osm_coverage|seoul_dev|_dump|team-latest-back|gildongmu-real|gildongmu-experiment|parents?\[|\.parent|__file__|\.\./|course_(requests|descriptions)")
for d, dirs, files in os.walk(root):
    dirs[:] = [x for x in dirs if x not in skip]
    for f in sorted(files):
        p = os.path.join(d, f)
        if os.path.splitext(f)[1].lower() not in code_ext:
            continue
        rel = os.path.relpath(p, root)
        if rel.startswith("_inbox") or rel.startswith("source"):
            continue
        if f in ("tag_inventory.html", "data_viewer.html", "point-editor.html"):
            continue
        try:
            text = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if len(line) < 400 and pat.search(line):
                print(f"{rel}:{i}: {line.strip()[:170]}")

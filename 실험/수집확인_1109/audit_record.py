"""이번 세션 기록을 실제 대화 파일과 대조한다. 사용자 발언 중 세션기록에 없는 것과, 인수인계 문서의 경로 중 없는 것을 적는다.

사용: python -I audit_record.py <jsonl> <세션기록 md> <인수인계 md> <정보기술학회 폴더>
"""
import json
import os
import re
import sys

jl, rec, hand, root = sys.argv[1:5]
sys.stdout.reconfigure(encoding="utf-8")
norm = lambda s: re.sub(r"\s+", "", s)
record = norm(open(rec, encoding="utf-8").read())
said = []
for line in open(jl, encoding="utf-8"):
    try:
        o = json.loads(line)
    except ValueError:
        continue
    texts = []
    if o.get("type") == "user" and not o.get("isMeta"):
        c = (o.get("message") or {}).get("content")
        if isinstance(c, str):
            texts.append(c)
        elif isinstance(c, list):
            texts += [b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text"]
    a = o.get("attachment") or {}
    if a.get("type") in ("queued_command", "queued_commands"):
        p = a.get("prompt")
        if isinstance(p, str):
            texts.append(p)
        elif isinstance(p, list):
            texts += [b.get("text", "") for b in p if isinstance(b, dict) and b.get("type") == "text"]
    for t in texts:
        t = re.sub(r"<ide_[^>]*>.*?</ide_[^>]*>", "", t, flags=re.S)
        t = re.sub(r"<[^>]+>.*?</[^>]+>", "", t, flags=re.S).strip()
        t = re.sub(r"\[Image[^\]]*\]", "", t).strip()
        if t and len(t) < 200 and not t.startswith(("This came from", "Another Claude", "[Request")):
            said.append(t)
seen, order = set(), []
for t in said:
    if t not in seen:
        seen.add(t)
        order.append(t)
missing = [t for t in order if norm(t) not in record]
print("사용자 발언", len(order), "개, 세션기록에 없는 것", len(missing), "개")
for t in missing:
    print(" -", t)
text = open(hand, encoding="utf-8").read()
paths = set(re.findall(r"`((?:국토정보맵|브이월드|공공데이터포털|실험|데이터|원고)/[^`]+?)/?`", text))
bad = []
for p in sorted(paths):
    if "*" in p or "..." in p:
        continue
    cand = [os.path.join(root, p), os.path.join(root, "데이터", "원본", p), os.path.join(root, "실험", "수집확인_1109", p)]
    if not any(os.path.exists(c) for c in cand):
        bad.append(p)
print("\n인수인계의 경로", len(paths), "개, 없는 것", len(bad), "개", bad)
for f in re.findall(r"`([\w가-힣_]+\.(?:py|out|md|csv))`", text):
    hit = any(f in fs for _, _, fs in os.walk(os.path.join(root, "실험"))) or any(f in fs for _, _, fs in os.walk(os.path.join(root, "인수인계"))) or any(f in fs for _, _, fs in os.walk(os.path.join(root, "데이터")))
    if not hit:
        print("없는 파일:", f)

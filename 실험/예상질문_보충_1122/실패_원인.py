"""실패한 요청은 길이 때문인가, 왕복형 때문인가 (2026-11-22, 예상 질문 답 보충).

성공 요청 = 오차 10% 이하이고 되밟기 비율 0.4 미만인 경로가 1개 이상인 요청(논문 4.1).
실패 요청을 다음 셋으로 나눈다.
- 길이: 오차 10% 이하인 경로가 하나도 없다
- 왕복형: 오차 10% 이하인 경로는 있으나 모두 되밟기 0.4 이상이다
자료: ../코드수정_1110/표2.json(논문 표 2의 빔 반환·γ=0·γ=5 열), ../동선개선_1110/본실험3.json(새 선호)
실행: python -I 실패_원인.py → 실패_원인.out
"""
import collections
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.join(HERE, "..")
out = []


def classify(routes):
    within = [r for r in routes if r["err"] <= 0.10]
    if any(r["retrace"] < 0.4 for r in within):
        return "성공"
    return "왕복형" if within else "길이"


T2 = json.load(open(os.path.join(EXP, "코드수정_1110", "표2.json"), encoding="utf-8"))
out.append("## 논문 표 2 (기준 설정)")
for conf in dict.fromkeys(r["conf"] for r in T2):
    c = collections.Counter(classify(r["routes"]) for r in T2 if r["conf"] == conf)
    out.append(f"- {conf}: {dict(c)}")

M3 = json.load(open(os.path.join(EXP, "동선개선_1110", "본실험3.json"), encoding="utf-8"))
req = collections.defaultdict(list)
for m in M3:
    req[(m["setting"], m["start"], m["anchor_id"])].append(m)
out.append("\n## 새 선호 설정 (실패가 있는 설정만, 출발점별 실패 수 포함)")
for s in dict.fromkeys(m["setting"] for m in M3):
    keys = [k for k in req if k[0] == s]
    c = collections.Counter(classify(req[k]) for k in keys)
    if c.get("성공", 0) < len(keys):
        by_start = collections.Counter(k[1] for k in keys if classify(req[k]) != "성공")
        out.append(f"- {s}: {dict(c)}, 실패 출발점 {dict(by_start)}")

text = "\n".join(out)
print(text)
open(os.path.join(HERE, "실패_원인.out"), "w", encoding="utf-8").write(text + "\n")

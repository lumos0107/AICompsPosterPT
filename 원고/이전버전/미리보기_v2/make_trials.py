"""표 3 위치만 바꾼 시험 사본 두 개를 만든다(배치 빈칸 확인용, 원고는 그대로).
A: 4.4 제목 바로 앞, B: 결론 바로 앞. 결과: ../trialA_v2.md, ../trialB_v2.md"""
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
s = (HERE / "논문_정보기술학회_v2.md").read_text(encoding="utf-8")
t0 = s.index("**표 3.")
t1 = s.index("| 시설 근접 $\\alpha_f$=10 |", t0)
t1 = s.index("\n", t1) + 1
tbl = s[t0:t1]
base = s[:t0] + s[t1:]
h = base.index("### 4.4")
(HERE / "trialA_v2.md").write_text(base[:h] + tbl + "\n" + base[h:], encoding="utf-8")
c = base.index("## Ⅴ.")
(HERE / "trialB_v2.md").write_text(base[:c] + tbl + "\n" + base[c:], encoding="utf-8")
print("ok")

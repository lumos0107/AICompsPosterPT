"""v3 분량 줄이기 후보를 하나씩 적용한 시험 사본을 만든다(원고는 그대로). 끝에 전부 적용한 사본(ALL)도 만든다.
결과: ../trial{키}_v3.md   실행: python -I 미리보기_v3/make_trials_v3.py  (측정은 build_pdf.py --jang90 + 미리보기_v2/content_measure.py)
후보:
 M 표 3을 행렬형(선호 8행 × 기준·α 1·3·10)으로, 오차·다른 길이 비율은 본문 범위로
 A 요약·초록을 v2 길이 가까이로 줄임
 T 표 1의 성질 다섯 행을 한 행으로
 G 표 2에서 γ=0 행을 뺌(본문 문장도)
 F 그림 2를 뺌(본문 언급도)
 R 4.3절 본문을 줄임
"""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
S = (HERE / "논문_정보기술학회_v3.md").read_text(encoding="utf-8")


def cut(s, a, b_incl):
    i = s.index(a)
    j = s.index(b_incl, i) + len(b_incl)
    return s[:i], s[i:j], s[j:]


def M(s):
    i = s.index("| 설정 ($\\alpha$) |")
    j = s.index("| 조용한 길 $\\alpha_k$=10 |", i)
    j = s.index("\n", j) + 1
    tbl = """| 선호 (해당 지표) | 기준 | $\\alpha$=1 | $\\alpha$=3 | $\\alpha$=10 |
|---|:---:|:---:|:---:|:---:|
| 평지 (경사 %) | 2.33 | −0.09 (34) | −0.21 (39) | −0.37 (43)ᵃ |
| 신호 회피 (개/km) | 2.73 | −0.94 (45) | −1.40 (47) | −1.65 (47) |
| 시설 근접 (m) | 86.1 | −6.9 (35) | −12.6 (41) | −14.0 (41)ᵇ |
| 조명 (비율) | 0.72 | +0.10 (39) | +0.13 (43) | +0.17 (45)ᵃ |
| 물가 (비율) | 0.07 | +0.09 (39) | +0.17 (44)ᶜ | +0.20 (39)ᵈ |
| 보도 (비율) | 0.71 | +0.11 (41) | +0.15 (44) | +0.19 (47) |
| 녹지 (비율) | 0.06 | +0.06 (43) | +0.14 (46)ᵇ | +0.16 (42)ᵉ |
| 조용한 길 (비율) | 0.53 | +0.33 (47)ᵃ | +0.39 (47)ᶠ | +0.41 (47)ᶜ |

주: 칸은 기준 대비 요청별 차이의 평균(나아진 요청 수). 표시가 없으면 성공 요청 47/47이고, ᵃ 46, ᵇ 44, ᶜ 42, ᵈ 28, ᵉ 39, ᶠ 45이다.
"""
    s = s[:i] + tbl + s[j:]
    s = s.replace("해당 지표 변화는 기준 설정과의 요청별 차이의 평균이고(길의 성질은 길이 비율의 차이), 괄호 안은 나아진 요청 수이다.",
                  "평균 거리 오차는 기준 0.03, 각 설정 0.03~0.07이었고 물가 $\\alpha_k=10$만 0.18이었다.")
    return s


def A(s):
    k0 = s.index("## 요 약\n\n") + len("## 요 약\n\n")
    k1 = s.index("\n", k0)
    kr = ("기존 경로 안내는 목적지까지의 시간과 거리를 줄이는 데 중심을 두어 사용자마다 다른 요구를 제한적으로만 반영한다. "
          "본 논문은 그중 목적지 없이 정한 거리를 달려 출발점으로 돌아와야 하는 러너에 주목하여, 경사·신호 교차로·편의시설·조명·물가·보도·녹지·조용한 길에 대한 선호를 경로 비용으로 표현해 목표 거리에 맞는 순환 경로를 생성한다. "
          "나가는 구간은 방향을 달리한 빔 탐색으로, 돌아오는 구간은 재사용·근접·회전과 선호 비용에 벌점을 준 최단 비용 탐색으로 만든다. "
          "제주 도심 안내 방향 47개 실험에서 기준 설정은 모든 요청이 목표 거리 ±10% 안에 들었고(평균 오차 0.03) 왕복형 경로가 없었으며, 모양 항으로 둥근 정도는 0.27에서 0.38로 늘었다. "
          "선호 크기를 1, 3, 10으로 키우면 신호 교차로는 34~61%, 경사는 4~16%, 시설 거리는 8~16% 줄고 각 성질의 길이 비율은 6~41%p 늘었으나, 드문 성질은 거리 정확도와, 밝은 길은 조용한 길과 맞바꾸는 관계였다. "
          "끝으로 다른 사용자 유형으로의 확장을 논의한다.")
    s = s[:k0] + kr + s[k1:]
    e0 = s.index("## Abstract\n\n") + len("## Abstract\n\n")
    e1 = s.index("\n", e0)
    en = ("Route guidance has mainly focused on reducing travel time and distance to a destination, reflecting the differing needs of users only to a limited extent. "
          "This paper focuses on runners, who need a route of a given length that returns to the start, and expresses their preferences for slope, signalized intersections, amenities, lighting, waterside, sidewalks, green space, and quiet streets as route costs to generate loop routes matching a target distance. "
          "The outbound part is built by a beam search with separated headings, and the return part by a least-cost search that penalizes reuse of and proximity to the outbound path, turns, and preference costs. "
          "In experiments with 47 guide directions in central Jeju City, every baseline request produced a route within ±10% of the target (mean error 0.03) with no out-and-back routes, and the shape terms raised roundness from 0.27 to 0.38. "
          "With preference weights of 1, 3, and 10, signalized intersections per kilometer fell by 34–60%, slope by 4–16%, and amenity distance by 8–16%, and the length shares of the preferred qualities rose by 6–41 percentage points, "
          "while rare qualities traded off against distance accuracy and lit streets against quiet streets. We also discuss extensions to other user groups.")
    return s[:e0] + en + s[e1:]


def T(s):
    i = s.index("| 조명 | 25 m 안에")
    j = s.index("괄호는 그 성질을 가진 노드의 비율이다.", i) + len("괄호는 그 성질을 가진 노드의 비율이다.")
    row = ("| 길의 성질 $f_k$ | 성질이 있는 노드: 조명(25 m 안 조명, 50%), 물가(해안선·하천 50 m 안, 10%), 보도(20 m 안 인도, 38%), 녹지(도시공원 안, 7%), 조용한 길(폭 20 m 미만 도로, 87%) "
           "| 1:1,000 수치지형도 조명 12,117개, 연속수치지형도 해안선·하천·인도·도로 폭, 제주시 도시공원 82곳(같은 면적의 원 + 20 m로 어림) |")
    return s[:i] + row + s[j:]


def G(s):
    s = re.sub(r"\| 제안 귀환\(\$\\gamma\$=0\) \|[^\n]*\n", "", s)
    return s.replace("제안 귀환은 47회 모두 성공하였고, 재사용 벌점이 없는 $\\gamma=0$에서 30/118이던 왕복형 경로가 $\\gamma=5$에서는 0/127이 되었다.",
                     "제안 귀환은 47회 모두 성공하였고 재사용 벌점이 없으면($\\gamma=0$) 경로의 25%이던 왕복형 경로가 없어졌다.")


def F(s):
    i = s.index("![그림 2]")
    j = s.index("(downtown, 5 km; median improvement)**", i) + len("(downtown, 5 km; median improvement)**")
    s = s[:i] + s[j:]
    return s.replace("표 2는 돌아오는 구간 생성 방식과 러닝 동선 모양 반영에 따른 결과이고, 그림 2는 모양 반영 전후의 예이다.",
                     "표 2는 돌아오는 구간 생성 방식과 러닝 동선 모양 반영에 따른 결과이다.")


def R(s):
    a = s.index("그러나 $\\gamma=5$ 경로도 둥근 정도가")
    b = s.index("응답 시간은 4.2초로 길어졌다.", a) + len("응답 시간은 4.2초로 길어졌다.")
    new = ("그러나 $\\gamma=5$ 경로는 나간 길 옆으로 되돌아오는 가는 고리가 많았고, 모양 항을 더하자 둥근 정도가 0.27에서 0.38로 늘고 km당 회전은 3.08에서 2.21로 줄었으며 "
           "서로 다른 응답도 34개에서 45개로 늘었다. 대신 응답 시간은 4.2초로 길어졌다.")
    return s[:a] + new + s[b:]


def L(s):  # 4.4절 둘째 문단부터 줄임 (M 적용 뒤에 쓴다)
    a = s.index("$\\alpha$를 키울수록 해당 지표가 더 나아져")
    b = s.index("세 항 중 가장 좁다.", a) + len("세 항 중 가장 좁다.")
    new = ("$\\alpha$를 키울수록 해당 지표가 나아져 신호 교차로는 34~61%, 경사는 4~16%, 시설 거리는 8~16% 줄고 성질별 길이 비율은 6~41%p 늘었으며, "
           "24개 설정 모두 부호순위 검정에서 $p<0.01$이었다(응답이 같은 요청을 하나로 세어도 같음). 대신 기준 경로와 다른 길이 비율은 $\\alpha=1$의 0.34~0.61에서 "
           "$\\alpha=10$의 0.51~0.75로 늘었고, 되밟는 길이 비율은 평균 0.03 이하였다.\n\n"
           "드문 성질인 물가(노드의 10%)와 녹지(7%)는 $\\alpha_k=10$에서 성공 요청이 28, 39개로 줄었다. 조명·보도와 조용한 길은 반대로 움직여, "
           "조명·보도 $\\alpha_k=10$은 km당 신호 교차로를 0.47, 0.74곳 늘렸고 조용한 길 $\\alpha_k=10$은 1.82곳 줄였으나 밝은 길과 보도 비율을 0.25, 0.29 낮췄다. "
           "제주 도심에서 조명과 보도가 신호가 많은 큰길에 몰려 있기 때문이다. 시설 근접은 연동에서 23~29 m 줄었으나 탑동에서는 5 m 이하였는데, "
           "기준 경로의 km당 시설 비용은 중앙값 161 m로 크지만 사분위 범위가 중앙값의 0.27배로 좁아 경로마다 비슷하다.")
    return s[:a] + new + s[b:]


def C(s):
    a = s.index("본 논문은 낯선 곳에서 달리는 러너를 위해")
    b = s.index("사용자 유형으로 확장할 계획이다.", a) + len("사용자 유형으로 확장할 계획이다.")
    new = ("본 논문은 낯선 곳에서 달리는 러너를 위해 여덟 가지 선호를 경로 비용으로, 러닝 경로의 모양 기준을 돌아오는 구간 비용으로 표현한 순환 경로 생성 방법을 제안하였다. "
           "제주 도심 실험에서 목표 거리를 지키면서 경로가 더 둥글고 덜 꺾였고 선호를 키울수록 해당 지표가 나아졌으나, 드문 성질의 선호는 거리 정확도와, 밝은 길의 선호는 조용한 길의 선호와 맞바꾸는 관계였다.\n\n"
           "다만 그래프는 도로중심선이어서 실제 보행 가능 여부와 공사 구간을 반영하지 못하고, 녹지와 조용한 길은 공원 면적과 도로 폭으로 어림하였다. "
           "입체 교차와 신호 위치의 영상 판정은 교차 검증하지 않았고 신호에는 횡단보도 신호가 일부 섞여 있으며, 제주 도심만 실험하고 러너의 평가는 수행하지 않았다. "
           "향후 사용자 평가, 여러 선호의 조합, 올레길·그늘 자료의 추가와 러너 기록에서 선호 크기를 학습하는 방법을 다루고, 통행 불가 조건과 결합하여 휠체어·유모차 이용자로 확장할 계획이다.")
    return s[:a] + new + s[b:]


def N(s):
    a = s.index("도로 그래프는 국토지리정보원 연속수치지형도의")
    b = s.index("교량 밖 이웃 노드로 보간하였다.", a) + len("교량 밖 이웃 노드로 보간하였다.")
    new = ("도로 그래프는 국토지리정보원 연속수치지형도의 제주 도로중심선에서 폭 3 m 미만 도로를 빼고 영상으로 확인한 입체 교차 10곳의 연결을 끊어 만들었다. "
           "신호 자료가 있는 1:1,000 수치지형도 범위(제주 도심)의 가장 큰 연결 요소를 15 m 간격으로 표집해 노드 24,756개, 476 km를 얻었고, "
           "고도는 등고선과 표고점으로 만든 10 m 격자에서 보간하였다(검증 오차 중앙값 0.85 m).")
    return s[:a] + new + s[b:]


VAR = {"M": M, "A": A, "T": T, "G": G, "F": F, "R": R}
MORE = {"L": L, "C": C, "N": N}
for k, f in VAR.items():
    (HERE / f"trial{k}_v3.md").write_text(f(S), encoding="utf-8")
for k, f in MORE.items():
    (HERE / f"trial{k}_v3.md").write_text(f(M(S)) if k == "L" else f(S), encoding="utf-8")
s = S
for f in VAR.values():
    s = f(s)
(HERE / "trialALL_v3.md").write_text(s, encoding="utf-8")
for f in MORE.values():
    s = f(s)
(HERE / "trialALL2_v3.md").write_text(s, encoding="utf-8")
s2 = S
for k in "MATRLCN":
    s2 = {**VAR, **MORE}[k](s2)
(HERE / "trialKEEP_v3.md").write_text(s2, encoding="utf-8")  # 그림 2와 표 2 γ=0 행은 남김
print("ok", list(VAR) + list(MORE) + ["ALL", "ALL2", "KEEP"])

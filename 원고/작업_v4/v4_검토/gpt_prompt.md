당신은 한국정보기술학회 추계 종합학술대회의 심사위원(경로 탐색·공간정보 분야 컴퓨터공학 교수)이다. 아래 학부생 논문 초안(5쪽 이하 2단 학술대회 논문, 우수논문상 지원 예정)을 심사한다. 도구(셸, 파일, 웹 검색)를 쓰지 말고 첨부 원고만으로 답하라. 그림은 이미지 없이 캡션만 남겼다. 한국어로 답한다.

평가할 것:
1. 기여와 새로움: 서론의 (1)(2)(3)이 기여로 설득력이 있는가. 관련 연구와 비교해 무엇이 약한가.
2. 논리와 근거: 주장과 실험 결과가 맞는가. 과장, 근거 없는 주장, 숫자끼리 안 맞는 곳(요약·서론·본문·표 사이)을 찾아라.
3. 방법 설명: 식 (1)~(3)과 3.4절의 설명이 재현 가능할 만큼 분명한가. 정의 없이 쓴 용어.
4. 실험 설계의 약점: 심사위원이 물을 질문 5개.
5. 분량: 목표는 3~4쪽이다. 지금 원고에서 줄이거나 뺄 곳을 우선순위로 제안하라(문장 단위로 구체적으로).
6. 우수논문상 관점에서 가장 먼저 고칠 3가지.

출력 형식: 1~6 항목별로 번호 목록. 문제마다 '위치(절·문장) / 문제 / 고칠 방향'.

===== 원고 =====
# 러너의 선호를 경로 비용에 반영한 목표 거리 순환 경로 생성

**Generating Target-Distance Loop Routes by Incorporating Runner Preferences into Route Costs**

강승준\*, 이은\*, 조민영\*, 길준민\*\*

Seung-Jun Kang\*, Eun Lee\*, Min-Young Jo\*, Joon-Min Gil\*\*

> 2026 한국정보기술학회 추계 종합학술대회 제출용 초안 v4 (2026-11-11, 6월 원고처럼 그림·표 중심으로 다시 짠 시험판. v3는 그대로 둠).
> ★ 표시는 아직 하지 않은 부분이다. 할 일은 문서 끝 초안 메모에 모았다.

---

## 요 약

러닝은 목적지 없이 정한 거리를 달려 돌아오는 운동이어서 길 안내로는 코스를 얻기 어렵고, 낯선 곳의 러너는 오르막과 신호 위치를 모른다. 본 논문은 경사·신호 교차로·편의시설·조명·물가·보도·녹지·조용한 길에 대한 러너의 선호를 가중치를 둔 경로 비용으로 표현하고, 나가는 구간은 다양성 빔 탐색으로, 돌아오는 구간은 되밟기·근접·회전 벌점과 선호 비용을 더한 최소 비용 탐색으로 만들어 목표 거리에 맞는 순환 경로를 생성한다. 제주 도심 47개 요청에서 기준 설정은 모두 목표 거리 ±10% 안에 들었고(평균 오차 3%) 왕복형 경로가 없었으며, 모양 항으로 경로의 둥근 정도가 0.27에서 0.38로 늘었다. 선호 가중치를 1, 3, 10으로 키우면 신호 교차로는 최대 61% 줄고 각 성질의 길이 비율은 최대 41%p 늘었으며, 선호를 켠 요청의 96%가 목표 거리를 지켰다. 끝으로 다른 사용자 유형으로의 확장을 논의한다.

## Abstract

Running is an activity of covering a chosen distance and returning to the start without a destination, so route guidance rarely yields a running course, and runners in unfamiliar places do not know where the hills and traffic signals are. This paper expresses runner preferences for slope, signalized intersections, amenities, lighting, waterside, sidewalks, green space, and quiet streets as weighted route costs, and generates loop routes of a target length: the outbound part by a diverse beam search and the return part by a least-cost search that adds reuse, proximity, and turn penalties to the preference cost. In 47 requests in central Jeju City, every baseline request produced a route within ±10% of the target (mean error 3%) with no out-and-back routes, and the shape terms raised roundness from 0.27 to 0.38. With preference weights of 1, 3, and 10, signalized intersections fell by up to 61%, the length shares of the preferred qualities rose by up to 41 percentage points, and 96% of the requests with preferences kept the target distance. We also discuss extensions to other user groups.

**Key words**

running route, loop route generation, user preference, beam search, road network

---

## Ⅰ. 서 론

러닝은 목적지 없이 정한 거리를 달려 출발점으로 돌아오는 운동이어서, 출발지에서 목적지까지의 길을 찾는 길 안내로는 코스를 얻기 어렵다. 특히 여행지처럼 낯선 곳에서는 어느 길이 오르막이고 어디서 신호에 걸리는지 알 수 없는데, 러너는 신호 대기와 잦은 회전을 달리기의 흐름을 끊는 요인으로 꼽는다[1]. 연 1,300만 명이 찾는 제주[2]의 도심에서도 선호를 반영하지 않은 경로는 km당 신호 교차로를 2.7곳, 5 km면 약 14곳 지난다.

고정 길이 순환 경로 연구[3][4]는 길이와 모양에 초점을 두어 러너마다 다른 선호를 조절하기 어렵다. 이에 본 논문은 낯선 곳의 러너를 위한 순환 경로 생성 방법을 제안한다. 핵심은 (1) 경사·신호 교차로·조명·물가 등 여덟 가지 선호를 가중치를 둔 m 단위 비용으로 표현한 선호 비용, (2) 이 비용을 나가는 구간의 다양성 빔 탐색과 돌아오는 구간의 최소 비용 탐색에 함께 쓰는 생성 구조, (3) 경로를 둥글고 덜 꺾이게 하는 모양 항이다. 제주 도심 실험에서 요청의 96%가 목표 거리 ±10% 안에 들었고, 가중치를 높일수록 경로가 러너가 원하는 길로 바뀌었다.

## Ⅱ. 관련 연구

최단 경로 알고리즘[5]과 대규모 도로망 탐색 기법[6]은 단일 비용을 최소화하고, 쾌적한 길[7][8]이나 안전한 길[9]을 찾는 연구는 여러 기준을 결합하지만 목적지를 전제로 한다. 순환 경로는 Gemsa 등[3]이 주변 환경, 원형에 가까운 모양, 회전 수를 기준으로 조깅 경로 문제를 정식화했고, Lewis와 Corcoran[4]은 고정 길이 순환 경로를 빠르게 계산하였다. 러너 선호는 Hänsel 등[1]이 설문과 면접으로 조사해 경로 추천에 썼고, Trail Router[10]는 녹지와 경사를 반영한 지정 거리 경로를 제공한다.

여러 경로를 제시하는 방법으로는 겹침을 제한한 k개 경로 탐색[11]과 다양성 빔 탐색[12]이 있다. 본 논문은 다양성 빔 탐색을 나가는 구간에 적용하되, 선호 비용을 오가는 길 모두에 반영하는 데 초점을 둔다.

## Ⅲ. 제안 방법

### 3.1 전체 구조

도로망을 그래프 $G=(V,E)$, 간선 길이를 $\ell(u,v)$, 출발 노드를 $s$, 목표 거리를 $T$라 하면, 순환 경로 $P$는 $s$에서 출발해 $s$로 돌아오는 노드열이고 거리 오차는 $E(P)=|L(P)-T|/T$이다($L$은 간선 길이의 합). 제안 방법은 그림 1의 다섯 단계로 $E(P)\le 0.1$인 경로를 최대 3개 만든다. 출발점에서 $0.38T$ 떨어진 안내점을 정하고(①), 나가는 구간을 빔 탐색으로 만든 뒤(②), 나가는 경로 위의 반환점 후보(③)마다 출발점까지 최소 비용으로 돌아오는 길을 붙이고(④), 그중 최종 경로를 고른다(⑤).

> **그림 1. 제안 방법의 흐름**
> **Fig. 1. Overview of the proposed method**

### 3.2 선호 비용

선호는 경사 $\alpha_s$, 신호 교차로 $\alpha_c$, 편의시설 $\alpha_f$와 길의 성질 $k\in K$=\{조명, 물가, 보도, 녹지, 조용한 길\}별 $\alpha_k$의 가중치로 나타내며, 0이면 고려하지 않는다. 성질은 러너가 밝고 나무가 늘어선 길과 보도[13], 물가와 공원, 교통 소음이 적은 길[1]을 선호한다는 조사에 따라 골랐다. 구간 $(u,v)$의 선호 비용은 수식 (1)이고, 신호 교차로는 지날 때마다, 나머지는 달린 길이에 비례해 m 단위로 더한다(표 1).

$$\begin{aligned}p(u,v)={}&\ell(u,v)\Bigl[\alpha_s f_s+\alpha_f f_f+\sum_{k\in K}\alpha_k f_k\Bigr]\\&+\alpha_c\,\kappa_c\,\mathbb{1}[v\in V_{sig}]\end{aligned} \tag{1}$$

$f_k$는 두 끝 노드 중 성질 $k$가 없는 노드의 비율이다. 신호 하나의 비용 $\kappa_c=100$ m는 신호 대기 약 30초에 달리기 속도 약 3 m/s를 곱한 가정이다.

**표 1. 선호 항목의 정의와 자료**
**Table 1. Definitions and data sources of preference terms**

| 항목 | 정의 (괄호: 그 성질을 가진 노드 비율) | 자료 |
|---|---|---|
| 경사 $f_s$ | $\min(1,\max(0,\lvert g\rvert-2)/20)$, $g$는 구간 경사(%) | 등고선·표고점으로 만든 10 m 고도 격자 |
| 신호 교차로 | 노드가 신호 교차로이면 1 (300곳) | 1:1,000 수치지형도 신호등 1,289개를 교차 노드에 지정 |
| 편의시설 $f_f$ | 두 끝 노드의 $\min(d,500)/500$ 평균, $d$는 최근접 시설 거리(m) | 화장실·편의점·공원 2,289곳 |
| 길의 성질 $f_k$ | 조명 25 m 안(50%), 해안·하천 50 m 안(10%), 인도 20 m 안(38%), 도시공원 안(7%), 폭 20 m 미만 도로(87%) | 1:1,000 조명 12,117개, 연속수치지형도 해안선·하천·인도·도로 폭, 제주시 도시공원 82곳 |

### 3.3 나가는 구간: 다양성 빔 탐색

빔 9개에 안내점 방향 기준 $-45°$~$+45°$의 서로 다른 방위를 주고, 각 빔은 현재 노드 $u$의 이웃 $c$를 수식 (2)의 점수로 확장한다.

$$S(c\mid b)=A(u,c)-\lambda_p\,\frac{p(u,c)}{\ell_0}-\lambda_1\frac{\Delta_b(c)}{180°}-\lambda_2 D(c) \tag{2}$$

$A$는 진행 방향 유도와 지그재그·재사용 벌점을 담은 기하 점수, $\Delta_b$는 빔의 방위와 후보 방향의 차이, $D$는 다른 빔이 지나간 정도이다($\lambda_1=0.55$, $\lambda_2=0.35$). 선호 비용은 노드 간격 $\ell_0=15$ m로 나눠 점수 단위로 바꾼다($\lambda_p=1$). 빔은 누적 거리가 $0.51T$에 이르거나 $0.48T$ 이상이면서 출발점에서 직선 2 km 이상 떨어지면 멈춘다.

### 3.4 돌아오는 구간: 최소 비용 탐색

나간 뒤 다시 빔 탐색으로 돌아오면 목표 거리를 맞추지 못하거나 왔던 길을 되밟기 쉽다(4.2절). 그래서 돌아오는 구간은 출발점에서의 Dijkstra 탐색[5]으로 구하고, 나가는 경로의 $k$번째 노드를 반환점으로 할 때 간선 비용을 수식 (3)으로 둔다.

$$\begin{aligned}c_k(u,v)={}&\ell(u,v)\bigl(1+\gamma\,\mathbb{1}_{out}+\gamma_p\,\mathbb{1}_{near}\bigr)\\&+p(u,v)+c_t\,\mathbb{1}_{turn}\end{aligned} \tag{3}$$

첫째, $\mathbb{1}_{out}$은 이미 지난 간선에 벌점 $\gamma=5$를 주어 되밟기를 막되, 금지하지는 않아 막다른 길에서도 경로가 닫힌다. 둘째, $\mathbb{1}_{near}$는 나간 길에서 도로 거리 $r=100$ m 안의 간선에 벌점 $\gamma_p=3$을 주어 나간 길 바로 옆으로 돌아오는 가는 고리를 막는다. 셋째, $\mathbb{1}_{turn}$은 45°보다 크게 꺾을 때마다 $c_t=60$ m를 더해 계단식 경로를 줄인다. 둘째와 셋째 항은 둥글고 덜 꺾이는 러닝 경로의 기준[3][1]을 옮긴 것이다. 넷째, $p$는 나가는 구간과 같은 선호 비용이어서, 돌아오는 길은 가장 짧은 길이 아니라 선호와 모양을 반영해 비용이 가장 작은 길이 된다. 반환점은 전체 길이가 $T$에 가까운 후보 5개 가운데 오차 ±10% 안에서 되밟기가 가장 짧은 것으로 정하고, 마지막으로 빔별 경로 중 점수와 서로 겹치지 않는 정도의 합이 큰 최대 3개를 고른다.

## Ⅳ. 실험 및 결과

### 4.1 실험 설정

도로망은 국토지리정보원 연속수치지형도의 제주 도로중심선에서 폭 3 m 미만 도로를 빼고 영상으로 확인한 입체 교차 10곳의 연결을 끊어, 신호 자료가 있는 제주 도심을 15 m 간격으로 표집하였다(노드 24,756개, 476 km). 출발점은 탑동(3 km), 도심(5 km), 연동(3 km), 이도동(4 km)이고, 안내점은 16방향 중 범위 안의 방향을 모두 써서 요청은 47개이다. 모양 값($r$, $\gamma_p$, $c_t$, 지그재그 벌점 1/4)은 본 실험과 따로 뽑은 예비 요청 12개에서 미리 정한 규칙으로 골랐다. 성공 요청은 오차 ±10% 안의 경로를 1개 이상 만든 요청, 왕복형은 길이의 40% 이상을 되밟은 경로, 둥근 정도는 $4\pi A/L^2$(원 1)이며, 설정 간 비교는 같은 요청끼리 짝지은 윌콕슨 부호순위 검정으로 한다.

### 4.2 구성 요소별 비교

표 2와 그림 2는 돌아오는 방법과 모양 항을 차례로 더한 결과이다.

**표 2. 구성 요소별 비교 (기준 설정, 요청 47개)**
**Table 2. Comparison by component (baseline setting, 47 requests)**

| 구성 | 성공 요청 | 거리 오차 | 왕복형 경로 | 경로 수 | 둥근 정도 | 회전(/km) | 응답(s) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 빔으로 돌아오기 | 41/47 | 0.06 | 23/78 | 1.66 | 0.04 | 1.84 | 0.7 |
| 최소 비용 귀환 ($\gamma$=0) | 47/47 | 0.06 | 30/118 | 2.51 | 0.09 | 2.20 | 2.2 |
| 최소 비용 귀환 ($\gamma$=5) | 47/47 | 0.04 | 0/127 | 2.70 | 0.27 | 3.08 | 1.8 |
| + 모양 항 (제안) | 47/47 | 0.03 | 0/137 | 2.91 | 0.38 | 2.21 | 4.2 |

주: 빔으로 돌아오기는 선호 비용을 지원하지 않아 기존 점수로 측정하였다. 둥근 정도와 회전은 경로 중앙값이다.

> **그림 2. 구성 요소별 경로 (연동 3 km, ■ 출발점, ▲ 안내점)**
> **Fig. 2. Routes by component (Yeon-dong, 3 km)**

첫째, 빔으로 돌아오면 6개 요청에서 목표 거리를 맞추지 못했고 경로의 29%가 왕복형이었으나(그림 2(a)), 최소 비용 귀환은 47개 모두 성공하였다. 둘째, 되밟기 벌점이 없으면($\gamma=0$) 경로의 25%가 여전히 왕복형이었고 $\gamma=5$에서 없어졌다. 셋째, 그래도 나간 길 옆으로 돌아오는 가는 고리가 남았는데(그림 2(b)), 모양 항을 더하자 둥근 정도가 0.27에서 0.38로 늘고 km당 회전이 3.08에서 2.21로 줄었으며 거리 오차도 0.03으로 줄었다(그림 2(c)). 대신 응답 시간은 4.2초로 늘었다.

### 4.3 선호 가중치에 따른 변화

**표 3. 선호 가중치별 해당 지표 변화 (요청 47개씩)**
**Table 3. Change of each metric by preference weight**

| 선호 (지표) | 기준 | $\alpha$=1 | $\alpha$=3 | $\alpha$=10 |
|---|:---:|:---:|:---:|:---:|
| 평지 (경사 %) | 2.33 | −0.09 | −0.21 | −0.37ᵃ |
| 신호 회피 (개/km) | 2.73 | −0.94 | −1.40 | −1.65 |
| 시설 근접 (m) | 86.1 | −6.9 | −12.6 | −14.0ᵇ |
| 조명 (길이 비율) | 0.72 | +0.10 | +0.13 | +0.17ᵃ |
| 물가 (길이 비율) | 0.07 | +0.09 | +0.17ᶜ | +0.20ᵈ |
| 보도 (길이 비율) | 0.71 | +0.11 | +0.15 | +0.19 |
| 녹지 (길이 비율) | 0.06 | +0.06 | +0.14ᵇ | +0.16ᵉ |
| 조용한 길 (길이 비율) | 0.53 | +0.33ᵃ | +0.39ᶠ | +0.41ᶜ |

주: 기준 대비 요청별 차이의 평균. 표시가 없으면 성공 요청 47/47이고, ᵃ 46, ᵇ 44, ᶜ 42, ᵈ 28, ᵉ 39, ᶠ 45이다.

> **그림 3. 선호에 따른 경로 변화 (이도동 4 km, 점선: 기준 경로, 주황 점: 그 성질이 있는 도로)**
> **Fig. 3. Routes by preference (Ido-dong, 4 km)**

표 3은 같은 요청에서 한 가지 선호만 1, 3, 10으로 둔 결과이다. 첫째, 가중치를 키울수록 모든 선호의 지표가 나아져 신호 교차로는 34~61%, 경사는 4~16%, 시설 거리는 8~16% 줄고 성질별 길이 비율은 6~41%p 늘었으며, 24개 설정 모두 $p<0.01$이었다. 둘째, 선호를 켠 1,128개 요청 중 96%가 목표 거리를 지켰으나, 노드의 10%와 7%에만 있는 물가와 녹지는 $\alpha=10$에서 성공이 28개와 39개로 줄어 드문 성질은 가중치를 낮게 두는 것이 낫다. 셋째, 선호끼리 부딪치기도 하였다. 조명을 높이면 밝은 큰길을 따라 신호가 늘고(그림 3(b)), 조용한 길을 높이면 신호는 km당 1.82곳 줄지만 밝은 길 비율이 0.25 줄었다(그림 3(d)). 제주 도심에서는 조명과 보도가 신호 많은 큰길에 몰려 있어, 한 경로가 모든 선호를 만족할 수 없으므로 러너가 가중치로 우선순위를 고르는 방식이 필요하다.

## Ⅴ. 결 론

본 논문은 낯선 곳의 러너를 위해 여덟 가지 선호를 가중치를 둔 경로 비용으로 표현하고, 나가는 구간의 다양성 빔 탐색과 돌아오는 구간의 최소 비용 탐색에 함께 써서 목표 거리 순환 경로를 생성하는 방법을 제안하였다. 제주 도심 실험에서 경로는 목표 거리를 지키면서 더 둥글고 덜 꺾였고, 가중치를 높일수록 러너가 원하는 길로 바뀌었다. 다만 도로중심선 그래프는 실제 보행 가능 여부와 공사 구간을 반영하지 못하고, 녹지와 조용한 길은 공원 면적과 도로 폭으로 어림하였으며, 실제 러너의 평가는 하지 않았다. 향후 (1) 러너 평가, (2) 여러 선호를 함께 쓸 때의 조합, (3) 올레길·그늘 등 자료 추가와 러너 기록에서 가중치를 학습하는 방법, (4) 통행 불가 조건을 더한 휠체어·유모차 이용자로의 확장을 다룰 계획이다.

## 참 고 문 헌

[1] K. Hänsel et al., "The experience of running: Recommending routes using sensory mapping in urban environments", International Journal of Human-Computer Studies, vol. 201, 103512, 2025.

[2] 제주특별자치도관광협회, "관광객 입도 현황(2024년)", 2025. [★출처 확인]

[3] A. Gemsa, T. Pajor, D. Wagner, and T. Zündorf, "Efficient computation of jogging routes", Experimental Algorithms (SEA 2013), LNCS, vol. 7933, pp. 272-283, 2013.

[4] R. Lewis and P. Corcoran, "Fast algorithms for computing fixed-length round trips in real-world street networks", SN Computer Science, vol. 5, no. 7, 868, 2024.

[5] E. W. Dijkstra, "A note on two problems in connexion with graphs", Numerische Mathematik, vol. 1, no. 1, pp. 269-271, 1959.

[6] H. Bast et al., "Route planning in transportation networks", Algorithm Engineering, LNCS, vol. 9220, pp. 19-80, 2016.

[7] D. Quercia, R. Schifanella, and L. M. Aiello, "The shortest path to happiness: Recommending beautiful, quiet, and happy routes in the city", Proc. 25th ACM Conf. on Hypertext and Social Media, pp. 116-125, 2014.

[8] T. Novack, Z. Wang, and A. Zipf, "A system for generating customized pleasant pedestrian routes based on OpenStreetMap data", Sensors, vol. 18, no. 11, 3794, 2018.

[9] R. Sarraf and M. P. McGuire, "Integration and comparison of multi-criteria decision making methods in safe route planner", Expert Systems with Applications, vol. 154, 113399, 2020.

[10] Trail Router, "Trail Router: Running Route Generator", https://trailrouter.com

[11] T. Chondrogiannis, P. Bouros, J. Gamper, U. Leser, and D. B. Blumenthal, "Finding k-shortest paths with limited overlap", The VLDB Journal, vol. 29, no. 5, pp. 1023-1047, 2020.

[12] A. K. Vijayakumar et al., "Diverse beam search for improved description of complex scenes", Proc. AAAI Conf. on Artificial Intelligence, vol. 32, no. 1, 2018.

[13] N. Schuurman, L. Rosenkrantz, and S. A. Lear, "Environmental preferences and concerns of recreational road runners", International Journal of Environmental Research and Public Health, vol. 18, no. 12, 6268, 2021.

---

\*제주대학교 컴퓨터공학과, {wind5973, leeeun2022, tnssid}@stu.jejunu.ac.kr
\*\*제주대학교 컴퓨터공학과(교신저자), jmgil@jejunu.ac.kr

※ 본 과제(결과물)는 교육부와 한국연구재단의 재원으로 지원을 받아 수행된 첨단분야 혁신융합대학사업의 연구결과입니다.

---


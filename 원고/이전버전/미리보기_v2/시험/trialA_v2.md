# 러너의 선호를 경로 비용에 반영한 목표 거리 순환 경로 생성

**Generating Target-Distance Loop Routes by Incorporating Runner Preferences into Route Costs**

강승준\*, 이은\*, 조민영\*, 길준민\*\*

Seung-Jun Kang\*, Eun Lee\*, Min-Young Jo\*, Joon-Min Gil\*\*

> 2026 한국정보기술학회 추계 종합학술대회 제출용 초안 v2 (2026-11-10, 본 실험 반영).
> ★ 표시는 아직 하지 않은 부분이다. 할 일은 문서 끝 초안 메모에 모았다.

---

## 요 약

기존 경로 안내는 목적지까지의 시간과 거리를 줄이는 데 중심을 두어 사용자의 선호를 제한적으로만 반영한다. 러닝은 목적지 없이 정해진 거리를 달려 출발점으로 돌아와야 하므로 이 틀로 다루기 어렵다. 본 논문은 경사, 신호 교차로, 편의시설에 대한 러너의 선호를 경로 비용으로 표현하여 목표 거리에 맞는 순환 경로를 생성하는 방법을 제안한다. 나가는 구간은 진행 방향을 달리한 빔 탐색으로, 돌아오는 구간은 지나온 길의 재사용과 선호 비용에 벌점을 준 최단 비용 탐색으로 만든다. 제주 도심 4개 출발점의 안내 방향 47개로 실험한 결과, 기준 설정의 모든 요청에서 목표 거리 ±10% 이내의 경로를 생성하였고(평균 거리 오차 0.04) 왕복형 경로는 없었다. 선호 크기를 1, 3, 10으로 바꾸면 km당 신호 교차로 경유는 39~56%, 평균 경사는 7~20%, 시설까지의 거리는 7~18% 줄었고, 선호가 클수록 기준 경로와 달라지는 길이도 늘었다. 끝으로 다른 사용자 유형으로의 확장을 논의한다.

## Abstract

Route guidance has mainly focused on reducing travel time and distance to a destination, reflecting user preferences only to a limited extent. Running differs because a runner needs a route of a given length that returns to the start. This paper expresses runner preferences for slope, signalized intersections, and amenities as route costs and generates loop routes that match a target distance. The outbound part is built by a beam search with separated headings, and the return part by a least-cost search that penalizes reuse of the outbound path and preference costs. In experiments with 47 guide directions at four start locations in central Jeju City, every baseline request produced a route within ±10% of the target distance (mean error 0.04) with no out-and-back routes. With preference weights of 1, 3, and 10, signalized intersections per kilometer decreased by 39–56%, mean slope by 7–20%, and the distance to amenities by 7–18%, while the route length differing from the baseline grew with the weight. We also discuss extensions to other user groups.

**Key words**

running route, loop route generation, user preference, beam search, road network

---

## Ⅰ. 서 론

경로 탐색 연구와 서비스는 출발지에서 목적지까지의 시간이나 거리를 줄이는 문제를 중심으로 발전해 왔다[1]. 그러나 같은 두 지점 사이에서도 사람들이 원하는 길은 다르다. 최단 경로보다 조금 길더라도 쾌적한 길을 추천하는 연구[2]나 녹지와 소음을 반영한 보행 경로 연구[3]는 이러한 차이를 보여 준다.

러닝은 문제의 형태도 다르다. 러너에게는 도착지가 없고, 달릴 거리 자체가 목표이며, 출발한 곳으로 돌아와야 한다. 가파른 길, 신호 대기, 화장실이나 편의점과의 거리에 대한 선호도 러너마다 다르다. 고정 길이 순환 경로를 계산하는 기존 연구[4][5]는 길이 조건에 초점을 두어 이러한 선호를 경로 비용으로 함께 다루는 데 한계가 있다.

이에 본 논문은 경사·신호 교차로·편의시설에 대한 선호를 하나의 비용 구조로 표현하여 나가는 구간과 돌아오는 구간에 함께 적용하고, 빔 탐색과 재사용 벌점을 둔 최단 비용 탐색을 결합하여 목표 거리의 순환 경로를 만든다. 또한 제주 도로망에서 선호 설정에 따른 경로 변화를 분석한다.

## Ⅱ. 관련 연구

최단 경로 알고리즘[6]과 대규모 도로망 탐색 기법[1]은 단일 비용의 최소화에 효과적이며, 다기준 의사결정 기법을 적용한 안전 경로[7]와 쾌적성을 반영한 보행 경로[2][3] 연구는 출발지와 목적지가 주어진 경로를 다룬다. 순환 경로 생성은 Gemsa 등[4]이 조깅 경로 문제로 정식화하였고, Lewis와 Corcoran[5]은 고정 길이 왕복 경로를 빠르게 계산하는 방법을 제안하였다. 서비스로는 Trail Router[8]가 녹지 선호와 경사 회피를 반영한 지정 거리 경로를 제공한다.

여러 경로를 제시하는 연구로는 겹침을 제한한 k개 경로 탐색[9]과 빔 그룹 간 유사성에 벌점을 주는 다양성 빔 탐색[10]이 있다. 본 논문은 이를 순환 경로의 나가는 구간에 적용하되, 러너의 선호 비용을 나가는 구간과 돌아오는 구간에 함께 반영하는 데 초점을 둔다[★문헌 보강].

## Ⅲ. 제안 방법

### 3.1 문제 정의

도로망을 그래프 $G=(V,E)$로 나타내고, 간선 $(u,v)$의 길이를 $\ell(u,v)$라 한다. 출발 좌표에서 가장 가까운 노드를 $s$, 목표 거리를 $T$라 할 때 순환 경로는 $s$에서 출발해 $s$로 돌아오는 노드열 $P=(v_0=s,\dots,v_n=s)$이다. 경로 길이와 거리 오차는 수식 (1)과 같다.

$$L(P)=\sum_{i=1}^{n}\ell(v_{i-1},v_i),\qquad E(P)=\frac{|L(P)-T|}{T} \tag{1}$$

목표는 $E(P)\le 0.1$을 만족하면서 선호 비용이 작고 서로 겹침이 적은 순환 경로를 최대 3개 찾는 것이다.

### 3.2 선호 비용

러너의 선호는 벡터 $\alpha=(\alpha_s,\alpha_c,\alpha_f)$로 나타내며, 0이면 해당 요소를 고려하지 않는다. 경사와 편의시설은 달린 길이에 비례하는 비용으로, 신호 교차로는 지날 때마다 드는 비용으로 두어 단위를 m로 맞춘다. 구간 $(u,v)$의 선호 비용은 수식 (2)와 같고 각 항은 표 1과 같다.

$$\begin{aligned}p(u,v)={}&\ell(u,v)\bigl[\alpha_s f_s(u,v)+\alpha_f f_f(u,v)\bigr]\\&+\alpha_c\,\kappa_c\,\mathbb{1}[v\in V_{sig}]\end{aligned} \tag{2}$$

$V_{sig}$는 신호 교차로 노드의 집합이다. 신호 하나의 비용 $\kappa_c=100$ m는 신호 대기 약 30초와 달리기 속도 약 3 m/s를 곱해 어림한 가정이다. 경사 면제 임계값 $\tau=2\%$는 기존 구현의 8%로는 실험 범위 도로 길이의 95%가 면제되어 낮춘 값으로, 러너 자료로 정한 값은 아니다.

**표 1. 선호 항목의 정의와 자료**
**Table 1. Definitions and data sources of preference terms**

| 항목 | 정의 | 자료 |
|---|---|---|
| 경사 $f_s$ | $\min(1,\max(0,\lvert g\rvert-\tau)/20)$, $g$는 구간 경사(%) | 등고선·표고점으로 만든 10 m 고도 격자 |
| 신호 교차로 $\mathbb{1}[v\in V_{sig}]$ | 노드 $v$가 신호 교차로이면 1 | 1:1,000 수치지형도 신호등·신호등제어기 1,289개를 30 m로 묶은 276곳마다 20 m 안 교차 노드(없으면 30 m 안 최근접 노드)를 지정한 300개(묶음의 91.7%) |
| 편의시설 $f_f$ | 두 끝 노드의 $\min(d,500)/500$ 평균, $d$는 가장 가까운 시설까지의 거리(m) | 화장실·편의점·공원 2,289곳 |

### 3.3 나가는 구간 탐색

나가는 구간은 출발 노드에서 시작하는 빔 탐색으로 만든다. 먼저 출발점에서 $0.38T$ 떨어진 16개 방향 가운데 실험 범위 안의 방향에서 도로 노드 하나를 안내점 $g$로 고른다. 빔 9개에는 안내점 방향 기준 $-45°$~$+45°$의 서로 다른 방위를 주고, 각 빔은 현재 노드 $u$의 이웃 노드 $c$만 확장한다. 빔 $b$에서 후보의 점수는 수식 (3)과 같다.

$$S(c\mid b)=A(u,c)-\lambda_p\,\frac{p(u,c)}{\ell_0}-\lambda_1\frac{\Delta_b(c)}{180°}-\lambda_2 D(c) \tag{3}$$

$A$는 진행 방향을 유도하고 지그재그와 재사용(최근 100 m 제외)에 벌점을 주는 기하 점수, $\Delta_b$는 후보 이동 방위와 빔의 선호 방위의 차이, $D$는 다른 빔 가운데 후보 반경 20 m 안을 지나간 빔의 비율이다($\lambda_1=0.55$, $\lambda_2=0.35$). 선호 비용은 노드 간격 $\ell_0=15$ m로 나누어 점수 단위로 바꾸고 $\lambda_p=1$로 둔다. 매 단계 빔별 상위 3개 후보를 돌아가며 뽑아 빔 9개를 채우고, 방문한 노드, 막다른 길, 연속 급회전은 제외한다. 누적 거리가 $0.51T$에 이르거나, $0.48T$ 이상이면서 출발점에서 직선 2 km 이상 떨어진 빔은 종료한다.

### 3.4 돌아오는 구간 생성

돌아오는 구간은 최단 비용 탐색으로 만든다. 나가는 경로 $P_{out}$의 $k$번째 노드를 반환점으로 할 때, 출발 노드에서 Dijkstra 탐색[6]을 수행하며 간선 비용은 수식 (4)로 둔다.

$$\begin{aligned}c_k(u,v)={}&\ell(u,v)\bigl(1+\gamma\,\mathbb{1}[(u,v)\in P_{out}^{0..k}]\bigr)\\&+p(u,v)\end{aligned} \tag{4}$$

지나온 간선은 금지하지 않고 벌점($\gamma=5$)만 주므로 막다른 길이나 다리에서도 경로가 닫힌다. $p$는 돌아오는 구간에도 같은 선호를 적용하는 항으로, 길이를 포함하므로 괄호 밖에 더한다. 탐색 범위는 출발점에서 직선 $0.7T$ 이내이다.

반환점은 나가는 경로 전체에 벌점을 준 1회 탐색으로 전체 길이가 목표 거리에 가까운 5개를 고른 뒤, 각 후보의 앞부분에만 벌점을 주어 다시 탐색하여 오차 ±10% 이내를 우선하고 되밟는 길이가 가장 짧은 것을 선택한다. 길이는 실제 간선 길이의 합이다.

### 3.5 최종 경로 선택

빔별 순환 경로 중 오차 ±10% 이내인 경로가 있으면 그 경로만 후보로 두고, 정규화한 누적 점수(가중치 0.55)와 이미 고른 경로와 겹치지 않는 정도(0.45)를 합한 점수가 높은 순서로 최대 3개를 고른다. 겹침은 두 경로의 중간 구간(노드의 20~80%)에서 좌표가 겹치는 비율이며, 0.85 이상인 경로는 제외하고 3개를 채우지 못하면 기준을 단계적으로 완화한다.

## Ⅳ. 실험 및 결과

### 4.1 실험 환경

도로 그래프는 국토지리정보원 연속수치지형도의 제주 도로중심선으로 만들었다. 꼭짓점을 공유하거나 끝점이 1 m 이내인 선을 잇고, 폭 3 m 미만 도로를 빼고, 영상으로 확인한 입체 교차 10곳의 평면 연결을 끊었다. 신호 자료가 있는 1:1,000 수치지형도 범위(0.005° 칸 114개, 제주 도심)로 자른 뒤 가장 큰 연결 요소(길이의 99.95%)를 15 m 간격으로 다시 표집하여 노드 24,756개, 간선 26,887개, 476 km의 그래프를 얻었다. 고도는 5 m 간격 등고선과 표고점으로 만든 10 m 격자에서 보간하였고(검증 오차 중앙값 0.85 m), 교량 위 노드는 교량 밖 이웃 노드로 보간하였다.
실험은 탑동(3 km), 제주 도심(5 km), 연동(3 km), 이도동(4 km)에서 수행하였다. 안내점은 16방향 중 실험 범위 안의 방향을 모두 쓰고(11, 15, 10, 11개, 총 47개), 방향마다 거리 배수 0.85~1.15를 고정 시드로 뽑았다. 같은 요청은 같은 결과를 내므로 반복하지 않았다.

### 4.2 평가 지표

거리 오차는 수식 (1)의 $E(P)$이고, 성공 요청은 오차 ±10% 이내 경로를 1개 이상 만든 요청이다. 왕복형 경로는 같은 길을 두 번 지나는 길이의 비율이 0.4 이상인 경로이고, 경로 간 겹침은 소수 넷째 자리로 반올림한 좌표 집합의 겹침 비율을 경로 쌍별로 평균한 값이다. 선호 지표는 거리 가중 평균 경사, km당 신호 교차로 경유 수, 가장 가까운 시설까지의 평균 거리(최대 500 m)이다. 기준 경로와 다른 길이 비율은 같은 요청의 기준 설정 경로가 지나지 않은 간선의 길이 비율이며, 설정 간 비교는 같은 안내점끼리 짝지은 윌콕슨 부호순위 검정(양측)으로 한다.

### 4.3 순환 경로 생성 결과

표 2는 돌아오는 구간 생성 방식에 따른 결과이다.

**표 2. 돌아오는 구간 생성 방식에 따른 결과 (기준 설정, 요청 47회)**
**Table 2. Results by return generation method (baseline setting, 47 requests)**

| 구성 | 경로 수 | 거리 오차 | 성공 요청 | 왕복형 경로 | 경로 간 겹침 | 응답 시간(s) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| 빔 귀환 | 1.66±0.70 | 0.06±0.06 | 41/47 | 23/78 | 0.21±0.18 | 0.7±0.2 |
| 제안 귀환($\gamma$=0) | 2.51±0.83 | 0.06±0.02 | 47/47 | 30/118 | 0.32±0.15 | 2.2±0.7 |
| 제안 귀환($\gamma$=5) | 2.70±0.69 | 0.04±0.02 | 47/47 | 0/127 | 0.24±0.18 | 1.8±0.4 |

주: 빔 귀환은 돌아오는 구간도 빔 탐색으로 찾고 남은 구간을 너비 우선 탐색으로 잇는 방식으로, 선호 비용을 지원하지 않아 기존 점수(경사 가중치 0.5, 임계값 8%)로 측정하였다.

빔 귀환은 가장 빠르지만 6개 요청에서 ±10% 이내 경로를 만들지 못했고 경로의 29%가 왕복형이었다. 제안 귀환은 47회 모두 성공하였고, 재사용 벌점이 없는 $\gamma=0$에서 30/118이던 왕복형 경로가 $\gamma=5$에서는 0/127이 되었으며 거리 오차도 0.04로 가장 작았다.

**표 3. 선호 설정별 결과 (요청 47회씩)**
**Table 3. Results by preference setting (47 requests each)**

| 설정 ($\alpha$) | 성공 요청 | 거리 오차 | 기준 경로와 다른 길이 비율 | 해당 지표 변화 (나아진 요청) |
|---|:---:|:---:|:---:|:---:|
| 기준 (0, 0, 0) | 47/47 | 0.041 | - | 경사 2.40%, 신호 2.57개/km, 시설 84.0 m |
| 평지 $\alpha_s$=1 | 47/47 | 0.042 | 0.26 | −0.17%p (34) |
| 평지 $\alpha_s$=3 | 46/47 | 0.039 | 0.42 | −0.28%p (42) |
| 평지 $\alpha_s$=10 | 45/47 | 0.043 | 0.55 | −0.48%p (43) |
| 신호 회피 $\alpha_c$=1 | 47/47 | 0.042 | 0.36 | −1.01개/km (46) |
| 신호 회피 $\alpha_c$=3 | 47/47 | 0.041 | 0.46 | −1.34개/km (47) |
| 신호 회피 $\alpha_c$=10 | 47/47 | 0.040 | 0.50 | −1.45개/km (47) |
| 시설 근접 $\alpha_f$=1 | 47/47 | 0.043 | 0.24 | −6.0 m (37) |
| 시설 근접 $\alpha_f$=3 | 47/47 | 0.041 | 0.46 | −12.4 m (41) |
| 시설 근접 $\alpha_f$=10 | 46/47 | 0.041 | 0.55 | −14.9 m (39) |

### 4.4 선호 설정에 따른 경로 변화

표 3은 같은 출발점과 안내점에서 한 가지 선호만 1, 3, 10으로 둔 결과이다. 해당 지표 변화는 기준 설정과의 요청별 차이의 평균이고, 괄호 안은 나아진 요청 수이다. 그림 2는 신호 회피의 예로, 첫 경로의 km당 신호 차이가 47개 요청의 중앙값인 요청이다.


$\alpha$를 키울수록 해당 지표가 더 나아져 기준 대비 신호 교차로는 39~56%, 경사는 7~20%, 시설 거리는 7~18% 줄었고, 9개 설정 모두 부호순위 검정에서 $p<0.001$이었다(응답이 같은 요청을 하나로 세어도 같음). 대신 기준 경로와 다른 길이 비율이 $\alpha=1$의 0.24~0.36에서 $\alpha=10$의 0.50~0.55로 늘었고, 성공 요청은 $\alpha_s=10$에서 45/47, $\alpha_f=10$에서 46/47로 줄었다. 되밟는 길이 비율은 모든 설정에서 0.01 이하였다. 다른 지표는 평균으로 경사 0.03%p, 신호 0.002개/km, 시설 0.5 m 이내에서만 나빠졌다. 이도동에서는 $\alpha_s=1$이 11개 중 3개 요청만 나아졌고, 시설 근접은 $\alpha_f=3$, 10에서도 효과가 없었다.

![그림 2](../실험/코드수정_1110/그림2_본실험.png)

> **그림 2. 기준 경로와 신호 회피($\alpha_c$=10) 경로의 예 (탑동 3 km, 원은 신호 교차로, 채운 원은 경로가 지나는 곳)**
> **Fig. 2. Baseline and signal-avoiding ($\alpha_c$=10) routes (Tapdong, 3 km; circles: signalized intersections, filled: passed)**

시설 근접의 효과가 작은 것은 시설 비용이 경로마다 비슷하기 때문으로, 기준 경로의 km당 시설 비용은 중앙값 163 m로 경사(57 m)보다 크지만 사분위 범위가 중앙값의 0.29배로 세 항 중 가장 좁다.

## Ⅴ. 결 론

본 논문은 러너의 선호를 경로 비용으로 표현한 순환 경로 생성 방법을 제안하고, 제주 도심 실험에서 목표 거리를 지키면서 선호를 키울수록 해당 지표가 나아짐을 확인하였다.

다만 그래프는 폭 3 m 미만 도로를 뺀 도로중심선이어서 실제 보행 가능 여부를 보장하지 않으며, 공사 중인 구간처럼 자료와 현장이 다른 곳이 있다. 입체 교차와 신호 위치는 영상으로 확인하였으나 판정을 교차 검증하지 않았고, 신호 교차로에는 횡단보도 신호가 일부 섞여 있다. 신호 자료가 있는 제주 도심만 실험하여 서귀포 등 다른 지역에서의 차이를 확인하지 못했고, 실제 러너의 평가도 수행하지 않았다. 향후에는 출발점을 늘리고 사용자 평가를 진행하며, 통행 불가 조건과 선호 비용을 결합하여 휠체어나 유모차 이용자처럼 목적지가 있고 지날 수 없는 구간이 있는 사용자 유형으로 확장할 계획이다.

## 참 고 문 헌

[1] H. Bast et al., "Route planning in transportation networks", Algorithm Engineering, LNCS, vol. 9220, pp. 19-80, 2016.

[2] D. Quercia, R. Schifanella, and L. M. Aiello, "The shortest path to happiness: Recommending beautiful, quiet, and happy routes in the city", Proc. 25th ACM Conf. on Hypertext and Social Media, pp. 116-125, 2014.

[3] T. Novack, Z. Wang, and A. Zipf, "A system for generating customized pleasant pedestrian routes based on OpenStreetMap data", Sensors, vol. 18, no. 11, 3794, 2018.

[4] A. Gemsa, T. Pajor, D. Wagner, and T. Zündorf, "Efficient computation of jogging routes", Experimental Algorithms (SEA 2013), LNCS, vol. 7933, pp. 272-283, 2013.

[5] R. Lewis and P. Corcoran, "Fast algorithms for computing fixed-length round trips in real-world street networks", SN Computer Science, vol. 5, no. 7, 868, 2024.

[6] E. W. Dijkstra, "A note on two problems in connexion with graphs", Numerische Mathematik, vol. 1, no. 1, pp. 269-271, 1959.

[7] R. Sarraf and M. P. McGuire, "Integration and comparison of multi-criteria decision making methods in safe route planner", Expert Systems with Applications, vol. 154, 113399, 2020.

[8] Trail Router, "Trail Router: Running Route Generator", https://trailrouter.com

[9] T. Chondrogiannis, P. Bouros, J. Gamper, U. Leser, and D. B. Blumenthal, "Finding k-shortest paths with limited overlap", The VLDB Journal, vol. 29, no. 5, pp. 1023-1047, 2020.

[10] A. K. Vijayakumar et al., "Diverse beam search for improved description of complex scenes", Proc. AAAI Conf. on Artificial Intelligence, vol. 32, no. 1, 2018.

---

\*제주대학교 컴퓨터공학과, {wind5973, leeeun2022, tnssid}@stu.jejunu.ac.kr
\*\*제주대학교 컴퓨터공학과(교신저자), jmgil@jejunu.ac.kr

※ 본 과제(결과물)는 교육부와 한국연구재단의 재원으로 지원을 받아 수행된 첨단분야 혁신융합대학사업의 연구결과입니다.

---

## 초안 메모 (제출 전 삭제)

**v1에서 바꾼 것 (2026-11-10)**

| 위치 | 내용 | 근거 |
|---|---|---|
| 요약, 초록, 결론 | 재실험 값으로 채움(47회, 오차 0.04, 왕복형 0, 선호별 감소율) | `실험/코드수정_1110/본실험_결과.md` |
| 3.2, 표 1 | 수식 (2)를 m 단위로, '횡단 지점'을 '신호 교차로'로, $\kappa_c$·$\tau$ 근거, 자료를 1:1,000 신호와 시설 2,289곳으로 | `수식대조.md` |
| 3.3 | 수식 (3)에 $/\ell_0$, 재사용 판정 최근 100 m 제외, 종료 규칙을 실제 코드값($0.51T$ 또는 $0.48T$+직선 2 km)으로. v1의 '$0.6T$'는 본 실험에 쓰지 않은 설정이었음 | `LoopV2Engine` 기본값, 본 실험 요청에 outboundStopRatio 없음 |
| 3.4 | 수식 (4)에서 $p$를 괄호 밖으로 | `수식대조.md` |
| 4.1 | 새 그래프(연속수치지형도, 폭 3 m 미만 제외, 입체 10곳, 114칸, 등고선·표고점 고도), 안내점 47개 | `도심실험_결과.md`, `신호검증_결과.md`, `v3_stats.json` |
| 표 2 | v3·안내점 47개·기준 설정에서 세 구성만 다시 잼. 기존 그래프 행과 $0.6T$ 행은 뺌 | `실험/코드수정_1110/표2.out`, `table2_routes.py` |
| 표 3, 4.4 | 10행, 열 다섯 개. 되밟기와 검정은 본문에 | `본실험_요약.out`, `본실험_중복제거검정.out` |
| 결론 | 한계를 네 문장으로 | `본실험_결과.md` 8장 |

**남은 것**

| 구분 | 위치 | 할 일 |
|---|---|---|
| 분량 | 전체 | 11/10 사용자 지시로 (가) 관련 연구 2문단, (나) 서론 축소, (다) 3.5절 식 (5) 삭제, (라) 그림 1 삭제·그림 2를 본 실험 예(`실험/코드수정_1110/plot_fig2.py`, 중앙값 요청)로 교체. 그래도 PDF 6쪽(일반 약 0.65쪽, 장평 90% 측정 약 0.2쪽 넘침). 더 줄일 곳은 사용자 답 대기 |
| 문헌 | Ⅱ장 | 선호를 반영한 순환 경로 연구를 더 찾아 '한계가 있다'는 서술을 뒷받침 |
| 확인 | 저자 영문 표기 | 6월 제출본은 Kang Seung-jun 형식, 이 초안은 Seung-Jun Kang 형식 |
| 확인 | 마감일 | 미정 |

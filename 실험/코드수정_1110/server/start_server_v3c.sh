#!/usr/bin/env bash
# gildongmu_v3 + 노드 속성 v3c(조명·물가·보도·녹지·조용한 길 열 추가)로 서버 실행. 작업 폴더를 이 폴더로 두어 graph_cache.bin이 여기에 생기게 함.
# 설정 파일은 고치지 않고 환경변수·명령행 인자로 덮어씀. DB 비밀번호는 기존 시작 스크립트에서 읽음(출력하지 않음).
cd "$(dirname "$0")"
export JAVA_HOME="/c/Program Files/Microsoft/jdk-17.0.19.10-hotspot"
export SPRING_DATASOURCE_URL="jdbc:mysql://localhost:3306/gildongmu_v3?useSSL=false&serverTimezone=Asia/Seoul&allowPublicKeyRetrieval=true"
export SPRING_DATASOURCE_USERNAME=root
export SPRING_DATASOURCE_PASSWORD="$(sed -n 's/^export SPRING_DATASOURCE_PASSWORD=//p' '../../../../데이터사이언스학회/04_실험/새그래프v2b_실행/start_server_v2b.sh')"
export GOOGLE_API_KEY=unused-dummy
H="$(cd .. && pwd -W)"
exec "$JAVA_HOME/bin/java" -Xmx16g -jar ../../../../데이터사이언스학회/04_실험/team-latest-back/build/libs/gildongmu-0.0.1-SNAPSHOT.jar \
  --gildongmu.experiment-area-file="$H/../도심실험_1110/실험범위_114칸.txt" \
  --gildongmu.node-attr-file="$H/../동선개선_1110/노드속성_v3c.csv" > server_v3.log 2>&1

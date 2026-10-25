# 기능·모듈·데이터 계약 연결
2026-10-25. 아래는 2+3 요구의 연결 지도다. 구체적 변경 파일은 GP23-02에서 실제 호출 경로로 확정한다.

| 기능계층 v2.0 | 책임/계약 | 의존 데이터 | 구현 큐 |
|---|---|---|---|
| 3.1 | 조합·사용자·역할 입력 | 챔피언/포지션/10픽/부분 입력 | 01~12 |
| 3.2 | 비교표·전체/사용자 방향 | 공통 계획과 지원 범위 | 10~12,29 |
| 3.3 | 라인관리·딜교·초반 정글 | 양 정글 정보 상태, 웨이브, 자원, 합류 | 13~20 |
| 3.4 | 운영·목표·비용 | 사이드/합류/오브젝트 조건 | 17,30 |
| 3.5 | 교전·한타 목표/위협/전환 | 실효 인원, 위협 도달성, 지형, 알려진 기술 | 21~28 |
| 3.6 | 가정·초기화 | observed/assumed/unknown/stale, 입력 출처 | 10,13,32 |
| 3.7 | 설명·지도·출처 | 판단 근거·자료 버전 | 08,27,34 |

공통 설계: ARCHITECTURE.md. 기존 구현 기록: docs/gameplan-content/frontend-v2-implementation.md.
판단 변경은 스키마→엔진→태그→화면→검사→예시→문서 순서로 영향을 확인한다. 이 표만으로 진행률을 올리지 않는다.

## 확인한 파일 의존 경로와 회귀 책임

| 경로 | 책임 | 변경 시 확인 |
|---|---|---|
| loading.js / loading-draft.js → loading-engine.js | 수동/공유/부분 입력·인계·정규화 | legacy/v2/v3/v4/제안 v5, 부분 입력, 알려지지 않은 픽, 중복·역할 검증 |
| loading-engine.js → loading-coach.js → loading-planboard.js | 같은 입력·가정으로 조건/후보/비용/전환 판단 | stale/unknown/assumed, 정글 양쪽·웨이브 가능성·실효 인원·목표 충돌 |
| loading-planboard.js → delivery / snapshot / dependencyTree | 5행동·코칭·태그·범위·추적 | 기존 delivery-v1/snapshot-v1 소비자, 원문/근거 연결, 태그 모순·잔류 |
| loading-presentation.js → loading-coach-view.js / loading.css | 상단2/하단3 읽기 순서와 공유·상세·복귀 | 320/390/desktop/200%/키보드, visible action/stop, 비교표·legacy·지도 보존 |
| gameplan_input.py → pregame_server.py pc_gameplan_input | privacy-filtered LCU/수동 capture | 세션/본인/관측 미검증 gate 보존; 전송 liveness를 전술 freshness로 재사용 금지 |
| official_catalog / manifests → build_loading_catalog.py → direction profiles / registry | 공식 사실·역할/패치 바인딩 | URL·해시·필수 슬롯·source patch, 기존 profile version2 범위; 무결성 ≠ 전술 승인 |
| scripts/export_gameplan_five.js / build_gameplan_preview.js | 같은 실제 엔진 원문·미리보기 | 입력·출력·화면 문장·SHA·지원 범위·seed 보존, 수동 보정 금지 |
| 학습 taxonomy → source/claim/lesson index → 검색/구간 UI | 6.4/6.5/6.6 및 3.7.4/5.5.2/2.4 연결 | 80 ID·미분류·중복·구간 검증·접근 상태·private notes 경계; 후보를 coaching으로 승격 금지 |

학습실 신규 모듈의 최종 파일명과 실제 검사 receipts는 작업자가 구현 후 상태 문서에 기록한다. 현황표·관리 그래프·Notion은 최종 근거를 소유한 상위 인계 작업에서 갱신하며 이 지도만으로 진행률을 바꾸지 않는다.

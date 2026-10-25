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

## 티어·상대 확장 — canonical IA와 실제 경로

| 기능ID | 실제파일경로 | 책임·회귀·잔여조건 |
|---|---|---|
|2.2.2,2.2.5 |outcome_stats.py / champion_insights.py → build_champion_insights.py → champion-insights.json |전체summary·tier/patch/source/available/missing/N/CI.2.2.1은기본방향이며tier집계ID로쓰지않음. |
|2.2.3,2.2.4,2.2.5 |champion-insights.js select/opponentRows → champion-page.js renderInsights/advancedtable |같은역할frequentN순·A팀최종승률·정확선택tier.고급표F1도같은select결과사용;다른tierCHfallback금지. |
|2.2.3~5,7.2 |matchup_results.py → riot_collector.py → collect_power_stats.py / resolve_riot_collection.py |미래cross-role은반대팀관측role+승리자료필요.동일hash충돌/중복/알수없는role차단;실제roster자료0. |
|2.4.1,2.4.4,2.4.7 |champion_matchup_references.json → champion_matchup_knowledge.py / build_champion_matchup_knowledge.py → champion-matchup-knowledge.json |LANING/JUNGLE5profile조건부참고,39candidate/6reference;다른phase승격·USER승인·엔진활성없음.2.4.2/3은미충족,2.4.5selecteddetail도자료부족유지. |
|2.1.3~6,2.6.1~5 |champion-state.js / champion-page.js → loading-draft.js return_state |MASTER_PLUS기본값·tierURL/dialog/back보존;통계tier는navmetadata,현재경기/상대role추정으로전달하지않음. |
|2.2.2~5,7.4 |pregame_server.py 인증POST selector;build_directions_web.py의3공개자산 |동일selector·allowlist·CSP·privatepaths차단;roster/ledger/notes공개금지. |
|7.2.1,7.2.1.1,7.2.2 |riot_collection_policy.py / policyJSON / 기존riot-power-collection.yml |10leaf/40slot기존단일cron,예산공유·인증즉시중단·허용창gate.실제수집은BLOCKED,작업별freshreceipt전성공표시안함. |

원자료·역사v1validator/계약·독립CH성장참고·GP23/학습실160ID를보존한다.10,000상태한도의archival/rollover는장기획득전별도capacity후속이며지금한도를늘리거나history를지우지않는다.전체stable검사/새제품CI·배포·실환경·NotionPENDING.관리추정은기존45.3/52.5유지;행별평가나출고증거를이표로대체하지않는다.

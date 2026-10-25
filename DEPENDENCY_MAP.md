# 기능·모듈·데이터 계약 연결

## 최신 티어·상대 출고 영수증 — 2026-10-25
PR145 head `d9f18a84352204f21a7da1ba00d555e4624b74ed` 정상병합12:06:14UTC → 이전main `b0a2be870184e3893ca4c9d6b8d1bf3414e36fa7`, PR3 SUCCESS40191299959/40191299982·이전main3 SUCCESS40191661761/40191661643. 이전artifactaf297cac8c3f5827a40429409e94db9a614176b0/native40192218449SUCCESS이나전체LIVE는320bodyCSS200%실패했다.
PR146 head `7e319acc27c4f4fa564b87ae64239b4100322c10` 정상병합12:42:12UTC → 이전main `b236bd736a2de4413a257604d338d9221d21b7a7`,PR3SUCCESS40193983033/40193983036. artifact `e1f273fae59c51e9df1441889831f314577a0600`/native40194626840SUCCESS후body·100.0%는통과했으나native-dialog가실패해전체LIVE_FAILED_DIALOG다. 두실제실패는각각 `live-initial-responsive-failed/`, `live-second-dialog-failed/`에보존한다.
세번째CSS/native-dialog·browser전용[PR147](https://github.com/kco994553-star/lol-coach/pull/147) head `f196a47a225709f29b4b1f18a6cd54ce5e2f04ec` 정상병합13:16:46UTC → 최신제품main `be0b83faf24db19a5f2ff05410c9c2ed979f33db`. PR147필수3 SUCCESS40196588961/40196588989. 정확최신main필수3 **SUCCESS3**(40196881621/40196881598). 새Pages artifact **9fc318cc6725e4e5ccb3fdf3be1c0e44a9590049** /native **40197492425** /상태 **SUCCESS**. 새실제HTTPS/강화브라우저 **ACTUAL_PUBLIC_HTTPS PASS:109/109assetSHA·14private404·root/.nojekyll200·71browser(29old+31tier+11responsive)·74uniquePNG;8saved200cases/6tablekeyboard/3touchEMULATION;errors/external/API/nonGET0**,관측시각 **2026-10-25T13:26:14.324558~13:27:04.403035UTC**. 최종증거 `evidence/actual-evidence/champion-tiers-20261025/result.md`.
e1/sourceb236은dialog문제가있던이전공개제품이며현재9fc318cc/sourcebe0로교체후실제검증통과했다. 두nativeSUCCESS나개별정상검사를전체LIVE_SUCCESS로승격하지않는다. 초기wrapgreen도saved100.0%case로무효화해재수정한역사를유지한다.


최신POST-DIALOG전체1018PASS/159.188s(13:13:42~13:16:21UTC)·CURRENTstart/endSHA동일·변경0,sourcechecks/buildcheckPASS. 수정전1018PASS149.999s/POSTCSS155.284s는역사범위로보존한다. 최신repo36+legacy55/targeted43·독립LOCALPASS. 같은strongharness전체가LOCAL_STAGE에서두번PASS:8saved200cases·touchEMULATION3(실물기기아님)·keyboardtables6·11checks/9PNG·109assetSHAstable. **LOCAL_STAGING_NOT_LIVE**이며로컬stage를거친뒤위별도실제공개71검사로최종통과했다. pointer+.focus()후키입력없이focus-visibleoutline을요구한초기단언은HARNESS_FALSE_POSITIVE로확인했고realTab/ShiftTab으로같은outline을검사해수정했으며이력보존했다. 실제dialogoverflow실패와harness단언오류를서로구분한다.

기존CHALLENGER-seed50경기만보유;MASTER_PLUS/ALLpartial·다른9leafEMPTY,A경기당시rankUNKNOWN,crossrole0·N20순위eligible0(maxpairN6),newacquired/provider0.5champ-role/5author39조건부+6전체참고,source26.x↔Riot16.20.1대응미검증,USER/TACTICAL승인0·coaching=false·게임효과N0 UNMEASURED.갱신허용창은저장기준2026-10-16종료이며새403관측아님.

관리추정은동일160행0/.5/1,전체74/160=**46.25%정확값**,FE84/160=**52.5%**.변경은2.4.1/2.4.4/2.4.7overall0→.5만이며FE그대로·PARTIAL/full_feature_acceptance=false.코드·통계·sourcecoverage와전술검증을혼동하지않는다.2.4.2/3운영·한타와2.4.5선택상대상세·더넓은지식/패치검토는미완료다.새Notion4페이지상태 **SYNCED_READBACK4_OF4 (기존본문/자식ID보존)**.10,000상태capacity/rollover는후속이다.

## 이전 설계·출고전 기록 — 당시 상태 보존
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

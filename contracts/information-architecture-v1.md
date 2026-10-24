# Information architecture v1 — USER2026-10-18

## Purpose and boundary

Rearrange current features into five responsibilities, using the existing shared shell,
engine and source registry. No framework/backend migration, new match/video collection,
fake records, unvalidated recommendations or live coaching authorization. Inherit main
c446862/public5bbcf7c and prior completed evidence. AUTO30/HOLD20/USER0/advice7/Frozen350,
source originals, holds/failures, official skill-owner/name(key), Windows/manual preserved.
N0/human30secUNMEASURED/WindowsBLOCKED_EXTERNAL unchanged.

## Fresh implementation map (before changes)

| Existing feature | Current location | New location | Data | Actual implementation | Change |
|---|---|---|---|---|---|
| Riot ID/region search | index (dashboard.html) | 전적 검색 | account-profile-v1, private POST lookup | PC authenticated path; static explicitly unavailable | KEEP; primary search |
| Personal dashboard/recent/champions | index below hero | 전적 검색 dashboard view | same account response/statistical window | actual records only; no public backend | ADAPT route view |
| Verified LCK soloqueue reference | index pro card | 전적 검색/pro reference | pro-dashboard-v1, queue420, verified registry | existing projection and refresh | KEEP; no duplicate collection |
| Review entry | small dashboard card | 경기 복기 | selected safe recent record, optional private postgame | no public raw match/timeline connection | ADAPT safe record selection; separate analysis status |
| Manual10pick/role/line opponent | loading.html | 게임플랜 input | loading-input-v4 | works without account | KEEP |
| Line recommendations/bans/personal mastery ranking | absent (old draft is manual journal) | 게임플랜 optional recommendation stage | future partial-draft + typed criteria | MISSING | queue; no dummy candidates/score |
| Team analysis/role | loading engine+legacy details | 게임플랜 summary | one report + planboard | works from10picks | ADAPT four one-sentence conclusions |
| Lane metrics/purpose/wave/trade | modern coach + nested legacy | 게임플랜 lane | same coach/planboard, exact matchup source scope | qualitative supported/unknown separated | ADAPT purpose/grid/direction/changes first |
| Macro | coach operations | 게임플랜 operations | same area_context/operations | conditional composition application | ADAPT placement/connection/fallback first |
| Teamfight | coach fight | 게임플랜 fight | same role/threat/step/map | conditional tools/positions | ADAPT role/threat/start/exit first |
| Preference/scenarios/cost comparison | optional coach methods/conditions | gameplan optional details | preferences vs assumptions distinct | actual selection; not strength mutation | KEEP, after basic plan |
| Maps/line zoom/evidence | coach/directions | relevant optional detail | same selected report/step, official assets | existing supported geometry only | KEEP; no relabelled unsupported map |
| Item-gold/item-value | game-info | 경기 중 도우미 | one GameInfo inventory/catalog calculation | manual comparison; local observation withheld | KEEP single feature |
| Connection status/cash/team totals | game-info | helper connection first | authenticated game-info status; snapshot withheld | BLOCKED_EXTERNAL, display_eligible=false | ADAPT hierarchy, no auto live claims |
| Camp/objective/inhibitor/ultimate timers | game-info limitations | helper capability detail | missing verified events/patch rules/CD fields | NOT_SUPPORTED | keep null + reason; no countdown |
| Enemy jungle last-seen/path inference | absent | helper future | future last_seen separate from inferred directions | MISSING; no raw position field | queue; no fake marker |
| Own jungle routes | absent | helper/learning future | reviewed route knowledge + available input | MISSING | queue; no path generator |
| Live reference to gameplan | loading link | helper → gameplan | existing static pregame analysis | no live dynamic strategy permission | link only; no in-match recommendation |
| Private finished-game analysis | local /postgame | review → authenticated PC | PostgameStore/plan_id/timeline/end gate | existing local only | KEEP private boundary |
| Scene learning/six scenes | directions + loading-study | 학습실 | same25source/29claim registry +6scenes | works, hypotheses remain typed | ADAPT entry hierarchy, keep practice |
| Collection/quota/CI | status/source details | separate 작업 상태 link | snapshot + actual Actions/Handoff | snapshot not real-time | separate from five play menus |

## Navigation and views

Exactly five primary links: 전적 검색, 게임플랜, 경기 중 도우미, 경기 복기, 학습실.
Desktop sidebar and mobile bottom navigation share the same link nodes/current state;
status is a secondary link, not sixth primary item. Common tokens, focus/pressed/disabled,
readable rem sizes (mobile strategy grid uses body-small14px rather than shrinking to10/11px), actual-nav-height reserved padding, reduced motion and skip links remain.
Routes retain index/loading/game-info/directions URLs; index hashes select search,
dashboard/pro or review. Unknown/stale review selection shows missing data, not a fake match.
Guest goes directly to manual gameplan; account/pro dashboard remains reachable separately.
Decorative art session/pick independence and API secret boundary remain unchanged.
Latest official-art requirement limits active initial/manual choices to24official splashes;
the existing25-entry registry and generated decoration history remain preserved.

## Shared screen data contracts

| Screen/model | Input → output fields | Source | Refresh | Missing | Next |
|---|---|---|---|---|---|
| Static champions/items | catalog patch/version/hash → champion facts/slots, item prices/assets | existing Data Dragon catalogs | catalog deployment | null+reason/version mismatch | input, strategy, inventory, learning |
| Search/account | riot_id+region → rank, recent_matches, champions, statistics period/N, retrieved_at | private Account/League/Match APIs | explicit lookup; stale response generation guard | distinct input/notfound/auth/API unavailable | dashboard/gameplan/review |
| Pro reference | verified roster+account+queue420 → safe profiles, scope/refreshed_at | existing verified projection | existing schedule/manual only | preserve last safe result/failure marker | reference dashboard/review |
| Statistics | patch/population/role/champion/matchup → periods+denominators+omissions | preserved archives | deployment, no recollection | no role→matchup substitution | strategy Why/learning |
| Knowledge/review | exact matchup/patch/claim IDs → accepted scope/excerpts/conditions/counterexamples | one loading-knowledge registry + immutable history | source-version publication | limited claim only, no AI evidence promotion | engine/learning/future recommendations |
| Strategy input |10picks+own+role+optional assumptions/preferences → one report | loading-input-v4 | analyze/input edit invalidates old report | validation/unknown role | briefing/details/maps |
| Strategy result | report.coach.planboard → briefing_v2, lane/wave/operations/fight/area_context | same evaluate result | same report revision/period/scenario | unknown never contested/safe | optional method/cost/map/Why |
| Live observation | authenticated transport → status,current,received_at,snapshot=null,display_eligible=false | existing official local route, real PC not verified | explicit request/shared server throttle | disconnected/stale/blocked; no zero timer | manual item reference, connection status |
| Inventory | held slots+counts+selected patch → subtotal,total,difference,missing | one GameInfo + official item catalog | explicit compare; clear on edit | whole difference null for missing | helper calculation details |
| Review selection | safe recent row + USER/PRO_REFERENCE scope → displayed observed result, period/source; analysis_status=UNCONNECTED | existing record response in memory only | row selection; clear on profile invalidation | no plan/timeline/video fabricated | local finished-game analysis, learning |
| Actual postgame | match_id+plan_id → ended-game result and preserved plan/version | existing private PostgameStore | existing authenticated flow/end gate | no ended evidence → no analysis | local review |
| Learning | matchup/role/claim ID → same claim/conditions/source links + scenario practice | loading-study reads same registry | catalog deployment | unsupported topic marked absent | exact loading lesson or method |
| Work status | snapshot timestamps → support/collection status, Actions/Handoff links | existing status JSON + real external links | explicit deployed snapshot | stale snapshot labelled | technical records |

briefing_v2 is additive: four items our_plan/enemy_plan/my_role/key_change, one sentence
per item, source pointers/origin retained. Existing loading_summary and detailed objects
remain for compatibility. No separate UI-only advice or change to objective metrics.
Lane first view purpose→qualitative grid→basic wave/trade→key change. Context/counterplay,
steps, costs, maps and evidence open optionally; macro and fight have distinct first views.

## Deferred contracts, not fake implementation

Recommendation input must later support partial known picks, selected role, banned/unavailable
IDs and optional explicit mastery/preference. Output max3 eligible candidates; each has
criterion statuses for lane matchup/duo, composition gap, ally tools, enemy response,
mastery and unknown-pick resilience; reason, weakness, conditions and claim IDs, no aggregate
score. Account disconnected → mastery NOT_EVALUATED. No current engine evaluates these
criteria, so no selectable recommendation button/candidate is delivered in this change.
Future recommendation selection must use the same normalized final report and knowledge.

Jungle: observed last_seen(value,time,source,perspective) and inferred possible_directions
(rule,conditions,limits) are distinct; unknown position never an actual map marker. Own
route guidance requires reviewed route knowledge. These lack actual data/permission here.
Timers require source event+game clock+patch rule; ultimate availability cannot be inferred
from learned skill level. Price totals are not cash/earned gold/combat strength.

No live behavioral feature is enabled by this reorganization. Fresh official docs/policies
are checked separately and linked in the evidence; endpoint availability does not confer
permission for a dynamic overlay. Preserve current route's snapshot withholding.

## Verification and rollback

Meaningful before/after PC1440/mobile390 plus320 width/200% text: five primary targets,
status separate, guest10pick→brief→three tabs, edit invalidation, selected steps/zoom,
unknown/unsupported states, real-record-to-review selection and clearing, public no private
provider calls, stable hero, no fake mastery/timers. Required protected CI retained.
Rollback public5bbcf7c or sourcec446862 consumers, retaining all evidence/history. Functional
and deployment success != tactical knowledge approval/coaching accuracy/30sec understanding.


## Current v1.1 intake baseline — 2026-10-23 UTC

현재 유효한 요구는 사용자가 제공한 통합명세 v1.1·Argon 본문과 추가 대기 비용 지시이다. 상단의 2026-10-18 설계/짧은 요약/선택형 상세 기록은 **과거 결정**이며, 최신 기본 노출 요구를 대체하지 않는다. 기존 시각 기준은 유지한다. 1~6 및 1.1 부모 묶음은 이동·신설·삭제하지 않았다. 아래 신규 세부 식별자는 기존 이 파일에 같은 의미 번호가 없어 그대로 추가했다. 과거 REC-REQ 식별자는 contracts/requirements.json에 원문 보존하며 재사용하지 않는다.

같은 목적의 현황표를 새 파일로 늘리지 않고 이 표를 갱신한다. 세션 계획/검증은 [기존 콘텐츠 인수 기록](../docs/gameplan-content/2026-10-19.md), 우선 대기열은 [QUEUE](../docs/queue/QUEUE.md), 최신 재개점은 [CURRENT_HANDOFF](../CURRENT_HANDOFF.md). ZIP/참고HTML/별도 원문MD는 미확보이며 실제로 읽었다고 가정하지 않는다.

검사 열은 이번 실행 또는 재사용 범위이며 코드 경로 존재를 전체 기능 완료로 올리지 않는다. 새 변경의 병합·배포는 별도 결과 기록의 정확 SHA가 기준이다. 인수 시 공개 source는 1b3171f9ec10bad32f71975ca3d30c1917240bdd(HTTPS 확인). 과거 경기의 완전한 전략 버전 보존과 실제 라이브 연결은 여기서 완료 처리하지 않는다. 콘텐츠 효과 N=0, 전술 검토는 별도 상태다.

| 기능 번호·요구 | 요구 출처 | 현재 상태 | 실제 진입 경로 | 데이터 의존성 | 구현 근거 | 검사 결과·범위 | 배포·실사용 확인 | 다음 작업 |
|---|---|---|---|---|---|---|---|---|
| 1.1.1 Riot ID·지역 입력 | USER-v1.1 | 부분 지원 | index.html / PC /dashboard | KR 계정 API 또는 공개 프로 projection | dashboard.js · account_dashboard.py | 기존 경로 재검사(하위 모든 조건 보증 아님) | 미확인 | 실제 계정 연결·전체 상세·필터 보강 |
| 1.1.2 검색 결과·조회 상태 | USER-v1.1 | 부분 지원 | index.html / PC /dashboard | KR 계정 API 또는 공개 프로 projection | dashboard.js · account_dashboard.py | 기존 경로 재검사(하위 모든 조건 보증 아님) | 미확인 | 실제 계정 연결·전체 상세·필터 보강 |
| 1.1.3 검색 계정 유지·변경 | USER-v1.1 | 부분 지원 | index.html / PC /dashboard | KR 계정 API 또는 공개 프로 projection | dashboard.js · account_dashboard.py | 기존 경로 재검사(하위 모든 조건 보증 아님) | 미확인 | 실제 계정 연결·전체 상세·필터 보강 |
| 1.1.4 계정 없이 이용 | USER-v1.1 | 부분 지원 | index.html / PC /dashboard | KR 계정 API 또는 공개 프로 projection | dashboard.js · account_dashboard.py | 기존 경로 재검사(하위 모든 조건 보증 아님) | 미확인 | 실제 계정 연결·전체 상세·필터 보강 |
| 1.2.1 계정·랭크 요약 | USER-v1.1 | 부분 지원 | index.html / PC /dashboard | KR 계정 API 또는 공개 프로 projection | dashboard.js · account_dashboard.py | 기존 경로 재검사(하위 모든 조건 보증 아님) | 미확인 | 실제 계정 연결·전체 상세·필터 보강 |
| 1.2.2 주 포지션·주 챔피언 요약 | USER-v1.1 | 부분 지원 | index.html / PC /dashboard | KR 계정 API 또는 공개 프로 projection | dashboard.js · account_dashboard.py | 기존 경로 재검사(하위 모든 조건 보증 아님) | 미확인 | 실제 계정 연결·전체 상세·필터 보강 |
| 1.2.3 준비·복기·학습 이어가기 | USER-v1.1 | 부분 지원 | index.html / PC /dashboard | KR 계정 API 또는 공개 프로 projection | dashboard.js · account_dashboard.py | 기존 경로 재검사(하위 모든 조건 보증 아님) | 미확인 | 실제 계정 연결·전체 상세·필터 보강 |
| 1.2.4 인게임 정보 진입·현재 경기 픽 확인 | USER-v1.1 | 미착수·외부 연결 미확인 | 현재 경기 진입 없음 | 현재 경기 조회·사용자 대응·필드/허용범위 | dashboard.js 계정 기록과 별개 | 실데이터 미실행 | 미확인 | 서버 spectator/지원 입력 계약과 진입 UI 구현 |
| 1.3.1 경기 목록·필터 | USER-v1.1 | 부분 지원 | index.html / PC /dashboard | KR 계정 API 또는 공개 프로 projection | dashboard.js · account_dashboard.py | 기존 경로 재검사(하위 모든 조건 보증 아님) | 미확인 | 실제 계정 연결·전체 상세·필터 보강 |
| 1.3.2 선택 경기 상세 | USER-v1.1 | 부분 지원 | index.html / PC /dashboard | KR 계정 API 또는 공개 프로 projection | dashboard.js · account_dashboard.py | 기존 경로 재검사(하위 모든 조건 보증 아님) | 미확인 | 실제 계정 연결·전체 상세·필터 보강 |
| 1.3.3 경기 복기로 이동 | USER-v1.1 | 부분 지원 | index.html / PC /dashboard | KR 계정 API 또는 공개 프로 projection | dashboard.js · account_dashboard.py | 기존 경로 재검사(하위 모든 조건 보증 아님) | 미확인 | 실제 계정 연결·전체 상세·필터 보강 |
| 1.4.1 사용·성적 기록 | USER-v1.1 | 부분 지원 | index.html / PC /dashboard | KR 계정 API 또는 공개 프로 projection | dashboard.js · account_dashboard.py | 기존 경로 재검사(하위 모든 조건 보증 아님) | 미확인 | 실제 계정 연결·전체 상세·필터 보강 |
| 1.4.2 성장·구매 경향 | USER-v1.1 | 부분 지원 | index.html / PC /dashboard | KR 계정 API 또는 공개 프로 projection | dashboard.js · account_dashboard.py | 기존 경로 재검사(하위 모든 조건 보증 아님) | 미확인 | 실제 계정 연결·전체 상세·필터 보강 |
| 1.4.3 준비에 활용 | USER-v1.1 | 부분 지원 | index.html / PC /dashboard | KR 계정 API 또는 공개 프로 projection | dashboard.js · account_dashboard.py | 기존 경로 재검사(하위 모든 조건 보증 아님) | 미확인 | 실제 계정 연결·전체 상세·필터 보강 |
| 1.5.1 선수·계정 목록 | USER-v1.1 | 부분 지원 | index.html / PC /dashboard | KR 계정 API 또는 공개 프로 projection | dashboard.js · account_dashboard.py | 기존 경로 재검사(하위 모든 조건 보증 아님) | 미확인 | 실제 계정 연결·전체 상세·필터 보강 |
| 1.5.2 솔로랭크 경기·빌드 조회 | USER-v1.1 | 부분 지원 | index.html / PC /dashboard | KR 계정 API 또는 공개 프로 projection | dashboard.js · account_dashboard.py | 기존 경로 재검사(하위 모든 조건 보증 아님) | 미확인 | 실제 계정 연결·전체 상세·필터 보강 |
| 1.5.3 정기 갱신 결과 확인 | USER-v1.1 | 부분 지원 | index.html / PC /dashboard | KR 계정 API 또는 공개 프로 projection | dashboard.js · account_dashboard.py | 기존 경로 재검사(하위 모든 조건 보증 아님) | 미확인 | 실제 계정 연결·전체 상세·필터 보강 |
| 1.5.4 미연결 상태의 참고 콘텐츠 | USER-v1.1 | 부분 지원 | index.html / PC /dashboard | KR 계정 API 또는 공개 프로 projection | dashboard.js · account_dashboard.py | 기존 경로 재검사(하위 모든 조건 보증 아님) | 미확인 | 실제 계정 연결·전체 상세·필터 보강 |
| 2.1.1 10픽 입력 | USER-v1.1 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-engine.js / loading-planboard.js | 현재 완성 입력 유효성 검사만 | 미확인 | 미공개 픽·불확실 위치 보존과 제한 분석 구현 |
| 2.1.1.1 미공개 픽·불확실한 포지션 | USER-v1.1 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-engine.js / loading-planboard.js | 현재 완성 입력 유효성 검사만 | 미확인 | 미공개 픽·불확실 위치 보존과 제한 분석 구현 |
| 2.1.2 포지션별 추천 후보 | USER-v1.1 | 미착수 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | 추천 엔진/후보 UI 없음 | 미실행 | 미확인 | 부분 픽·밴·이유·약점 추천 구현 |
| 2.1.3 추천 이유 비교 | USER-v1.1 | 미착수 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | 추천 엔진/후보 UI 없음 | 미실행 | 미확인 | 부분 픽·밴·이유·약점 추천 구현 |
| 2.1.3.1 라인전 대응 | USER-v1.1 | 미착수 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | 추천 엔진/후보 UI 없음 | 미실행 | 미확인 | 부분 픽·밴·이유·약점 추천 구현 |
| 2.1.3.2 아군 조합 보완·연계 | USER-v1.1 | 미착수 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | 추천 엔진/후보 UI 없음 | 미실행 | 미확인 | 부분 픽·밴·이유·약점 추천 구현 |
| 2.1.3.3 상대 조합 대응 | USER-v1.1 | 미착수 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | 추천 엔진/후보 UI 없음 | 미실행 | 미확인 | 부분 픽·밴·이유·약점 추천 구현 |
| 2.1.3.4 사용자 적합성·미공개 픽 대응 | USER-v1.1 | 미착수 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | 추천 엔진/후보 UI 없음 | 미실행 | 미확인 | 부분 픽·밴·이유·약점 추천 구현 |
| 2.1.4 픽 확정·자동 입력 연결 | USER-v1.1 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading.js importDraft / engine.importDraft | 기존 PC draft import·수동 생성만 | 미확인 | 검색 경기→동일 정규화 입력 연결·출처/시점/경합 |
| 2.1.4.1 인게임 조회와 동일 입력 계약 | USER-v1.1 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading.js importDraft / engine.importDraft | 기존 PC draft import·수동 생성만 | 미확인 | 검색 경기→동일 정규화 입력 연결·출처/시점/경합 |
| 2.2.1 우리·상대 조합 비교 | USER-v1.1 + USER-v1.3 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-coach executionBlocked / planboard decisions / 동일 UI projection | source439f554106 + cf2c59090·원본보존·실제 Chromium PASS; 콘텐츠AI검토(전술효과 아님) | product3013f30 / Pagesee839fc / 공개90해시·1440/390/320 PASS (result.md) | 미지원 구도·포지션·정량 웨이브·실전효과 별도 검토 |
| 2.2.1.1 팀 관점 고정 | USER-v1.1 + USER-v1.3 | 구현 완료(관점·기본 표시) | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-coach executionBlocked / planboard decisions / 동일 UI projection | source439f554106 + cf2c59090·원본보존·실제 Chromium PASS; 콘텐츠AI검토(전술효과 아님) | product3013f30 / Pagesee839fc / 공개90해시·1440/390/320 PASS (result.md) | 미지원 구도·포지션·정량 웨이브·실전효과 별도 검토 |
| 2.2.2 이번 판의 기본 작전 | USER-v1.1 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-engine.js / loading-planboard.js | 구조 동일성 검사, 전술 일관성 전수 미검토 | 미확인 | 고정 분류 잔여·전략 충돌 반례·팀 내용 검토 |
| 2.2.2.1 주전략·보조 수단·상대 제약 | USER-v1.1 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-engine.js / loading-planboard.js | 구조 동일성 검사, 전술 일관성 전수 미검토 | 미확인 | 고정 분류 잔여·전략 충돌 반례·팀 내용 검토 |
| 2.2.3 사용자 역할 코칭 | USER-v1.1 + USER-v1.3 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-coach executionBlocked / planboard decisions / 동일 UI projection | source439f554106 + cf2c59090·원본보존·실제 Chromium PASS; 콘텐츠AI검토(전술효과 아님) | product3013f30 / Pagesee839fc / 공개90해시·1440/390/320 PASS (result.md) | 미지원 구도·포지션·정량 웨이브·실전효과 별도 검토 |
| 2.2.3.1 사용자 행동과 설명 깊이 | USER-v1.1 + USER-v1.3 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-coach executionBlocked / planboard decisions / 동일 UI projection | source439f554106 + cf2c59090·원본보존·실제 Chromium PASS; 콘텐츠AI검토(전술효과 아님) | product3013f30 / Pagesee839fc / 공개90해시·1440/390/320 PASS (result.md) | 미지원 구도·포지션·정량 웨이브·실전효과 별도 검토 |
| 2.2.4 단계별 계획 연결 | USER-v1.1 + USER-v1.3 | 구현 완료(관점·기본 표시) | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-coach executionBlocked / planboard decisions / 동일 UI projection | source439f554106 + cf2c59090·원본보존·실제 Chromium PASS; 콘텐츠AI검토(전술효과 아님) | product3013f30 / Pagesee839fc / 공개90해시·1440/390/320 PASS (result.md) | 미지원 구도·포지션·정량 웨이브·실전효과 별도 검토 |
| 2.2.5 조합 상세·계획 전환 | USER-v1.1 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-engine.js / loading-planboard.js | 영향 검사·브라우저(기능 전체 효과 아님) | 미확인 | 미지원 구도·예외·근거 범위 확장 |
| 2.3.1 기본 목적과 코칭 | USER-v1.1 + USER-v1.3 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-coach executionBlocked / planboard decisions / 동일 UI projection | source439f554106 + cf2c59090·원본보존·실제 Chromium PASS; 콘텐츠AI검토(전술효과 아님) | product3013f30 / Pagesee839fc / 공개90해시·1440/390/320 PASS (result.md) | 미지원 구도·포지션·정량 웨이브·실전효과 별도 검토 |
| 2.3.1.1 바텀 2대2와 포지션별 목적 | USER-v1.1 + USER-v1.3 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-coach executionBlocked / planboard decisions / 동일 UI projection | source439f554106 + cf2c59090·원본보존·실제 Chromium PASS; 콘텐츠AI검토(전술효과 아님) | product3013f30 / Pagesee839fc / 공개90해시·1440/390/320 PASS (result.md) | 미지원 구도·포지션·정량 웨이브·실전효과 별도 검토 |
| 2.3.2 강약 구간·성장 전환점 | USER-v1.1 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-engine.js / loading-planboard.js | 영향 검사·브라우저(기능 전체 효과 아님) | 미확인 | 미지원 구도·예외·근거 범위 확장 |
| 2.3.3 웨이브 방향·실행 | USER-v1.1 + USER-v1.3 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-coach executionBlocked / planboard decisions / 동일 UI projection | source439f554106 + cf2c59090·원본보존·실제 Chromium PASS; 콘텐츠AI검토(전술효과 아님) | product3013f30 / Pagesee839fc / 공개90해시·1440/390/320 PASS (result.md) | 미지원 구도·포지션·정량 웨이브·실전효과 별도 검토 |
| 2.3.4 교전 유형·라인 유지력 | USER-v1.1 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-engine.js / loading-planboard.js | 영향 검사·브라우저(기능 전체 효과 아님) | 미확인 | 미지원 구도·예외·근거 범위 확장 |
| 2.3.5 양쪽 상대법·응징·실행 변수 | USER-v1.1 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-engine.js / loading-planboard.js | 영향 검사·브라우저(기능 전체 효과 아님) | 미확인 | 미지원 구도·예외·근거 범위 확장 |
| 2.3.5.1 스킬 선택의 근거 | USER-v1.1 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-engine.js / loading-planboard.js | 영향 검사·브라우저(기능 전체 효과 아님) | 미확인 | 미지원 구도·예외·근거 범위 확장 |
| 2.3.6 정글 개입·귀환·복구 | USER-v1.1 + USER-v1.3 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-coach executionBlocked / planboard decisions / 동일 UI projection | source439f554106 + cf2c59090·원본보존·실제 Chromium PASS; 콘텐츠AI검토(전술효과 아님) | product3013f30 / Pagesee839fc / 공개90해시·1440/390/320 PASS (result.md) | 미지원 구도·포지션·정량 웨이브·실전효과 별도 검토 |
| 2.3.7 정글 사용자 초반 계획 | USER-v1.1 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | planboard.waiting / action_summaries / coaching_explanation | 카이사–직스·양 서포터 교체·LOW/UNKNOWN/호응부재·역할 검사 | d9f515c 배포·공개 PC/모바일 기본흐름 확인(개별 상성 효과 미검증) | 대기 비용 사례 확장·기술/전술 검토(완성된 일반 전술 체계 아님) |
| 2.4.1 기본 방향과 코칭 | USER-v1.1 + USER-v1.3 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-coach executionBlocked / planboard decisions / 동일 UI projection | source439f554106 + cf2c59090·원본보존·실제 Chromium PASS; 콘텐츠AI검토(전술효과 아님) | product3013f30 / Pagesee839fc / 공개90해시·1440/390/320 PASS (result.md) | 미지원 구도·포지션·정량 웨이브·실전효과 별도 검토 |
| 2.4.2 사이드·본대·합류 | USER-v1.1 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-engine.js / loading-planboard.js | 영향 검사·브라우저(기능 전체 효과 아님) | 미확인 | 미지원 구도·예외·근거 범위 확장 |
| 2.4.3 압박·교전의 이득 전환 | USER-v1.1 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-engine.js / loading-planboard.js | 영향 검사·브라우저(기능 전체 효과 아님) | 미확인 | 미지원 구도·예외·근거 범위 확장 |
| 2.4.4 목표물 준비 | USER-v1.1 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-engine.js / loading-planboard.js | 영향 검사·브라우저(기능 전체 효과 아님) | 미확인 | 미지원 구도·예외·근거 범위 확장 |
| 2.4.5 계획 변경·손실 제한 | USER-v1.1 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-engine.js / loading-planboard.js | 영향 검사·브라우저(기능 전체 효과 아님) | 미확인 | 미지원 구도·예외·근거 범위 확장 |
| 2.5.1 역할·행동 요약과 코칭 | USER-v1.1 + 2026-10-24 독립본문 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | planboard.narrative_decisions / coaching_explanation / 동일 요약·상세 | source4cddd19 영향103·실제본문AI검토·Chromium1440/390/320 기본/상세/키보드/복원 PASS | maina8f3bc1 / Pages6334985·HTTPS90파일 확인; 공개화면 증거 result.md | 미지원 조합/포지션 관계 확장·실제 이해도/전술효과 검토 |
| 2.5.1.1 운영 역할과 한타 역할 분리 | USER-v1.1 + 2026-10-24 독립본문 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | planboard.narrative_decisions / coaching_explanation / 동일 요약·상세 | source4cddd19 영향103·실제본문AI검토·Chromium1440/390/320 기본/상세/키보드/복원 PASS | maina8f3bc1 / Pages6334985·HTTPS90파일 확인; 공개화면 증거 result.md | 미지원 조합/포지션 관계 확장·실제 이해도/전술효과 검토 |
| 2.5.2 양쪽 교전 구도 | USER-v1.1 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-engine.js / loading-planboard.js | 영향 검사·브라우저(기능 전체 효과 아님) | 미확인 | 미지원 구도·예외·근거 범위 확장 |
| 2.5.3 위협 대응·기회 만들기 | USER-v1.1 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-engine.js / loading-planboard.js | 영향 검사·브라우저(기능 전체 효과 아님) | 미확인 | 미지원 구도·예외·근거 범위 확장 |
| 2.5.4 배치·연결·지역별 예시 | USER-v1.1 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-engine.js / loading-planboard.js | 영향 검사·브라우저(기능 전체 효과 아님) | 미확인 | 미지원 구도·예외·근거 범위 확장 |
| 2.5.5 재평가·이탈·전환 | USER-v1.1 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-engine.js / loading-planboard.js | 영향 검사·브라우저(기능 전체 효과 아님) | 미확인 | 미지원 구도·예외·근거 범위 확장 |
| 2.6.1 기준 상황·조건 변경 | USER-v1.1 + USER-v1.3 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-coach executionBlocked / planboard decisions / 동일 UI projection | source439f554106 + cf2c59090·원본보존·실제 Chromium PASS; 콘텐츠AI검토(전술효과 아님) | product3013f30 / Pagesee839fc / 공개90해시·1440/390/320 PASS (result.md) | 미지원 구도·포지션·정량 웨이브·실전효과 별도 검토 |
| 2.6.2 리스크 감수 성향 | USER-v1.1 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-engine.js / loading-planboard.js | 영향 검사·브라우저(기능 전체 효과 아님) | 미확인 | 미지원 구도·예외·근거 범위 확장 |
| 2.6.3 행동·이득·비용 비교 | USER-v1.1 + USER-v1.3 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-coach executionBlocked / planboard decisions / 동일 UI projection | source439f554106 + cf2c59090·원본보존·실제 Chromium PASS; 콘텐츠AI검토(전술효과 아님) | product3013f30 / Pagesee839fc / 공개90해시·1440/390/320 PASS (result.md) | 미지원 구도·포지션·정량 웨이브·실전효과 별도 검토 |
| 2.6.4 기본 계획 복원 | USER-v1.1 + USER-v1.3 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-coach executionBlocked / planboard decisions / 동일 UI projection | source439f554106 + cf2c59090·원본보존·실제 Chromium PASS; 콘텐츠AI검토(전술효과 아님) | product3013f30 / Pagesee839fc / 공개90해시·1440/390/320 PASS (result.md) | 미지원 구도·포지션·정량 웨이브·실전효과 별도 검토 |
| 2.7.1 개념 설명 | USER-v1.1 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-engine.js / loading-planboard.js | 영향 검사·브라우저(기능 전체 효과 아님) | 미확인 | 미지원 구도·예외·근거 범위 확장 |
| 2.7.2 지도·장면 보기 | USER-v1.1 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-engine.js / loading-planboard.js | 영향 검사·브라우저(기능 전체 효과 아님) | 미확인 | 미지원 구도·예외·근거 범위 확장 |
| 2.7.3 근거·적용 범위 확인 | USER-v1.1 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-engine.js / loading-planboard.js | 영향 검사·브라우저(기능 전체 효과 아님) | 미확인 | 미지원 구도·예외·근거 범위 확장 |
| 2.7.4 관련 학습으로 이동 | USER-v1.1 | 부분 지원 | loading.html / PC /loading | 공식16.20.1·실제 입력·제한 지식 | loading-engine.js / loading-planboard.js | 영향 검사·브라우저(기능 전체 효과 아님) | 미확인 | 미지원 구도·예외·근거 범위 확장 |
| 3.1.1 연결 상태와 대상 경기 | USER-v1.1 | 부분 지원 | game-info.html / loading.html 참고 | 실제 로컬 관측·표시 허용범위 | game-info.js / game_info.py (관측 snapshot 비공개) | manual item/상태 브라우저, 실제 연결 미실행 | 미확인 | 실제 취득/허용/연결 검증 후 활성화 |
| 3.1.2 경기 시각·자료 신선도 | USER-v1.1 | 부분 지원 | game-info.html / loading.html 참고 | 실제 로컬 관측·표시 허용범위 | game-info.js / game_info.py (관측 snapshot 비공개) | manual item/상태 브라우저, 실제 연결 미실행 | 미확인 | 실제 취득/허용/연결 검증 후 활성화 |
| 3.1.3 미연결 상태의 이용 | USER-v1.1 | 부분 지원 | game-info.html / loading.html 참고 | 실제 로컬 관측·표시 허용범위 | game-info.js / game_info.py (관측 snapshot 비공개) | manual item/상태 브라우저, 실제 연결 미실행 | 미확인 | 실제 취득/허용/연결 검증 후 활성화 |
| 3.2.1 보유 아이템 가격 합계 | USER-v1.1 | 부분 지원 | game-info.html / loading.html 참고 | 실제 로컬 관측·표시 허용범위 | game-info.js / game_info.py (관측 snapshot 비공개) | manual item/상태 브라우저, 실제 연결 미실행 | 미확인 | 실제 취득/허용/연결 검증 후 활성화 |
| 3.2.2 맞상대·팀 비교 | USER-v1.1 | 부분 지원 | game-info.html / loading.html 참고 | 실제 로컬 관측·표시 허용범위 | game-info.js / game_info.py (관측 snapshot 비공개) | manual item/상태 브라우저, 실제 연결 미실행 | 미확인 | 실제 취득/허용/연결 검증 후 활성화 |
| 3.2.3 구성 해석 | USER-v1.1 | 부분 지원 | game-info.html / loading.html 참고 | 실제 로컬 관측·표시 허용범위 | game-info.js / game_info.py (관측 snapshot 비공개) | manual item/상태 브라우저, 실제 연결 미실행 | 미확인 | 실제 취득/허용/연결 검증 후 활성화 |
| 3.3.1 정글 캠프 타이머 | USER-v1.1 | 미지원 | game-info.html / loading.html 참고 | 실제 로컬 관측·표시 허용범위 | game-info.js / game_info.py (관측 snapshot 비공개) | 실제 라이브 미실행 | 미확인 | 실제 취득/허용/연결 검증 후 활성화 |
| 3.3.2 목표물 타이머 | USER-v1.1 | 미지원 | game-info.html / loading.html 참고 | 실제 로컬 관측·표시 허용범위 | game-info.js / game_info.py (관측 snapshot 비공개) | 실제 라이브 미실행 | 미확인 | 실제 취득/허용/연결 검증 후 활성화 |
| 3.3.3 억제기 타이머 | USER-v1.1 | 미지원 | game-info.html / loading.html 참고 | 실제 로컬 관측·표시 허용범위 | game-info.js / game_info.py (관측 snapshot 비공개) | 실제 라이브 미실행 | 미확인 | 실제 취득/허용/연결 검증 후 활성화 |
| 3.3.4 공통 표시·불확실성 | USER-v1.1 | 미지원 | game-info.html / loading.html 참고 | 실제 로컬 관측·표시 허용범위 | game-info.js / game_info.py (관측 snapshot 비공개) | 실제 라이브 미실행 | 미확인 | 실제 취득/허용/연결 검증 후 활성화 |
| 3.4.1 아군 사용 가능 상태 | USER-v1.1 | 미지원 | game-info.html / loading.html 참고 | 실제 로컬 관측·표시 허용범위 | game-info.js / game_info.py (관측 snapshot 비공개) | 실제 라이브 미실행 | 미확인 | 실제 취득/허용/연결 검증 후 활성화 |
| 3.4.2 잔여 시간·미확인 | USER-v1.1 | 미지원 | game-info.html / loading.html 참고 | 실제 로컬 관측·표시 허용범위 | game-info.js / game_info.py (관측 snapshot 비공개) | 실제 라이브 미실행 | 미확인 | 실제 취득/허용/연결 검증 후 활성화 |
| 3.5.1 마지막 확인 정보 | USER-v1.1 | 미지원 | game-info.html / loading.html 참고 | 실제 로컬 관측·표시 허용범위 | game-info.js / game_info.py (관측 snapshot 비공개) | 실제 라이브 미실행 | 미확인 | 실제 취득/허용/연결 검증 후 활성화 |
| 3.5.2 접근 가능성·동선 후보 | USER-v1.1 | 미지원 | game-info.html / loading.html 참고 | 실제 로컬 관측·표시 허용범위 | game-info.js / game_info.py (관측 snapshot 비공개) | 실제 라이브 미실행 | 미확인 | 실제 취득/허용/연결 검증 후 활성화 |
| 3.5.3 내 라인의 대응 | USER-v1.1 | 미지원 | game-info.html / loading.html 참고 | 실제 로컬 관측·표시 허용범위 | game-info.js / game_info.py (관측 snapshot 비공개) | 실제 라이브 미실행 | 미확인 | 실제 취득/허용/연결 검증 후 활성화 |
| 3.6.1 기본 동선 참고 | USER-v1.1 | 미착수/미확인 | game-info.html / loading.html 참고 | 실제 로컬 관측·표시 허용범위 | game-info.js / game_info.py (관측 snapshot 비공개) | 미실행 | 미확인 | 실제 취득/허용/연결 검증 후 활성화 |
| 3.6.2 관측 변화에 따른 대안 | USER-v1.1 | 미착수/미확인 | game-info.html / loading.html 참고 | 실제 로컬 관측·표시 허용범위 | game-info.js / game_info.py (관측 snapshot 비공개) | 미실행 | 미확인 | 실제 취득/허용/연결 검증 후 활성화 |
| 3.7.1 경기 전 계획 열람 | USER-v1.1 | 부분 지원 | game-info.html / loading.html 참고 | 실제 로컬 관측·표시 허용범위 | game-info.js / game_info.py (관측 snapshot 비공개) | 게임플랜 재열람, 라이브 강조 미검증 | 미확인 | 실제 취득/허용/연결 검증 후 활성화 |
| 3.7.2 변화 관련 강조 | USER-v1.1 | 미착수/미확인 | game-info.html / loading.html 참고 | 실제 로컬 관측·표시 허용범위 | game-info.js / game_info.py (관측 snapshot 비공개) | 미실행 | 미확인 | 실제 취득/허용/연결 검증 후 활성화 |
| 4.1.1 결과·조합·역할 | USER-v1.1 | 부분 지원(경로) | index.html#review-card / private postgame | 실제 선택 경기·타임라인·당시 계획 버전 | dashboard.js reviewRow / coach_v1 postgame 경로 | 안전한 기록 선택만 재검사 | 미확인 | 실경기–당시 계획·관측·타임라인 연결 |
| 4.1.2 주요 기록 | USER-v1.1 | 부분 지원(경로) | index.html#review-card / private postgame | 실제 선택 경기·타임라인·당시 계획 버전 | dashboard.js reviewRow / coach_v1 postgame 경로 | 안전한 기록 선택만 재검사 | 미확인 | 실경기–당시 계획·관측·타임라인 연결 |
| 4.2.1 성장 변화 | USER-v1.1 | 부분 지원(경로) | index.html#review-card / private postgame | 실제 선택 경기·타임라인·당시 계획 버전 | dashboard.js reviewRow / coach_v1 postgame 경로 | 안전한 기록 선택만 재검사 | 미확인 | 실경기–당시 계획·관측·타임라인 연결 |
| 4.2.2 주요 사건 | USER-v1.1 | 부분 지원(경로) | index.html#review-card / private postgame | 실제 선택 경기·타임라인·당시 계획 버전 | dashboard.js reviewRow / coach_v1 postgame 경로 | 안전한 기록 선택만 재검사 | 미확인 | 실경기–당시 계획·관측·타임라인 연결 |
| 4.2.3 관측 한계 | USER-v1.1 | 부분 지원(경로) | index.html#review-card / private postgame | 실제 선택 경기·타임라인·당시 계획 버전 | dashboard.js reviewRow / coach_v1 postgame 경로 | 안전한 기록 선택만 재검사 | 미확인 | 실경기–당시 계획·관측·타임라인 연결 |
| 4.3.1 사용한 게임플랜 확인 | USER-v1.1 | 부분 지원(경로) | index.html#review-card / private postgame | 실제 선택 경기·타임라인·당시 계획 버전 | dashboard.js reviewRow / coach_v1 postgame 경로 | 안전한 기록 선택만 재검사 | 미확인 | 실경기–당시 계획·관측·타임라인 연결 |
| 4.3.2 판단과 행동 비교 | USER-v1.1 | 부분 지원(경로) | index.html#review-card / private postgame | 실제 선택 경기·타임라인·당시 계획 버전 | dashboard.js reviewRow / coach_v1 postgame 경로 | 안전한 기록 선택만 재검사 | 미확인 | 실경기–당시 계획·관측·타임라인 연결 |
| 4.3.3 대안 검토 | USER-v1.1 | 부분 지원(경로) | index.html#review-card / private postgame | 실제 선택 경기·타임라인·당시 계획 버전 | dashboard.js reviewRow / coach_v1 postgame 경로 | 안전한 기록 선택만 재검사 | 미확인 | 실경기–당시 계획·관측·타임라인 연결 |
| 4.4.1 동일 경기 연결 | USER-v1.1 | 미지원 | index.html#review-card / private postgame | 실제 선택 경기·타임라인·당시 계획 버전 | 동일경기 영상 연결 미확인 | 미실행 | 미확인 | 동일 경기 식별·영상 근거 확보 |
| 4.4.2 판단 전·후 장면 | USER-v1.1 | 미지원 | index.html#review-card / private postgame | 실제 선택 경기·타임라인·당시 계획 버전 | 동일경기 영상 연결 미확인 | 미실행 | 미확인 | 동일 경기 식별·영상 근거 확보 |
| 4.4.3 화면과 발언 구분 | USER-v1.1 | 미지원 | index.html#review-card / private postgame | 실제 선택 경기·타임라인·당시 계획 버전 | 동일경기 영상 연결 미확인 | 미실행 | 미확인 | 동일 경기 식별·영상 근거 확보 |
| 4.5.1 다음 경기의 실천 항목 | USER-v1.1 | 부분 지원(경로) | index.html#review-card / private postgame | 실제 선택 경기·타임라인·당시 계획 버전 | dashboard.js reviewRow / coach_v1 postgame 경로 | 안전한 기록 선택만 재검사 | 미확인 | 실경기–당시 계획·관측·타임라인 연결 |
| 4.5.2 관련 개념·연습 | USER-v1.1 | 부분 지원(경로) | index.html#review-card / private postgame | 실제 선택 경기·타임라인·당시 계획 버전 | dashboard.js reviewRow / coach_v1 postgame 경로 | 안전한 기록 선택만 재검사 | 미확인 | 실경기–당시 계획·관측·타임라인 연결 |
| 5.1.1 역할과 판단 순서 | USER-v1.1 | 부분 지원 | directions.html / 게임플랜 학습·근거 펼치기 | 동일 지식 registry·공식 사실·제한 사례 | loading-study.js / directions.js / loading-knowledge.json | 기존 학습 경로, 모든 포지션/강의 내용 미검증 | 미확인 | 원문 학습 구성·사례·출처 범위 확장 |
| 5.1.2 단계별 사고 틀 | USER-v1.1 | 부분 지원 | directions.html / 게임플랜 학습·근거 펼치기 | 동일 지식 registry·공식 사실·제한 사례 | loading-study.js / directions.js / loading-knowledge.json | 기존 학습 경로, 모든 포지션/강의 내용 미검증 | 미확인 | 원문 학습 구성·사례·출처 범위 확장 |
| 5.2.1 유형별 강점·비용 | USER-v1.1 | 부분 지원 | directions.html / 게임플랜 학습·근거 펼치기 | 동일 지식 registry·공식 사실·제한 사례 | loading-study.js / directions.js / loading-knowledge.json | 기존 학습 경로, 모든 포지션/강의 내용 미검증 | 미확인 | 원문 학습 구성·사례·출처 범위 확장 |
| 5.2.2 챔피언별 차이 | USER-v1.1 | 부분 지원 | directions.html / 게임플랜 학습·근거 펼치기 | 동일 지식 registry·공식 사실·제한 사례 | loading-study.js / directions.js / loading-knowledge.json | 기존 학습 경로, 모든 포지션/강의 내용 미검증 | 미확인 | 원문 학습 구성·사례·출처 범위 확장 |
| 5.2.3 조합에 따른 역할 변경 | USER-v1.1 | 부분 지원 | directions.html / 게임플랜 학습·근거 펼치기 | 동일 지식 registry·공식 사실·제한 사례 | loading-study.js / directions.js / loading-knowledge.json | 기존 학습 경로, 모든 포지션/강의 내용 미검증 | 미확인 | 원문 학습 구성·사례·출처 범위 확장 |
| 5.3.1 양쪽 기본 구도 | USER-v1.1 | 부분 지원 | directions.html / 게임플랜 학습·근거 펼치기 | 동일 지식 registry·공식 사실·제한 사례 | loading-study.js / directions.js / loading-knowledge.json | 기존 학습 경로, 모든 포지션/강의 내용 미검증 | 미확인 | 원문 학습 구성·사례·출처 범위 확장 |
| 5.3.2 핵심 상호작용·성장 전환 | USER-v1.1 | 부분 지원 | directions.html / 게임플랜 학습·근거 펼치기 | 동일 지식 registry·공식 사실·제한 사례 | loading-study.js / directions.js / loading-knowledge.json | 기존 학습 경로, 모든 포지션/강의 내용 미검증 | 미확인 | 원문 학습 구성·사례·출처 범위 확장 |
| 5.3.3 조건·예외·반례 | USER-v1.1 | 부분 지원 | directions.html / 게임플랜 학습·근거 펼치기 | 동일 지식 registry·공식 사실·제한 사례 | loading-study.js / directions.js / loading-knowledge.json | 기존 학습 경로, 모든 포지션/강의 내용 미검증 | 미확인 | 원문 학습 구성·사례·출처 범위 확장 |
| 5.4.1 개념 단위 강의 | USER-v1.1 | 부분 지원 | directions.html / 게임플랜 학습·근거 펼치기 | 동일 지식 registry·공식 사실·제한 사례 | loading-study.js / directions.js / loading-knowledge.json | 기존 학습 경로, 모든 포지션/강의 내용 미검증 | 미확인 | 원문 학습 구성·사례·출처 범위 확장 |
| 5.4.2 영상·이미지 사례 | USER-v1.1 | 부분 지원 | directions.html / 게임플랜 학습·근거 펼치기 | 동일 지식 registry·공식 사실·제한 사례 | loading-study.js / directions.js / loading-knowledge.json | 기존 학습 경로, 모든 포지션/강의 내용 미검증 | 미확인 | 원문 학습 구성·사례·출처 범위 확장 |
| 5.4.3 글 요약·관련 계획 | USER-v1.1 | 부분 지원 | directions.html / 게임플랜 학습·근거 펼치기 | 동일 지식 registry·공식 사실·제한 사례 | loading-study.js / directions.js / loading-knowledge.json | 기존 학습 경로, 모든 포지션/강의 내용 미검증 | 미확인 | 원문 학습 구성·사례·출처 범위 확장 |
| 5.5.1 선택과 이유 | USER-v1.1 | 부분 지원 | directions.html / 게임플랜 학습·근거 펼치기 | 동일 지식 registry·공식 사실·제한 사례 | loading-study.js / directions.js / loading-knowledge.json | 기존 학습 경로, 모든 포지션/강의 내용 미검증 | 미확인 | 원문 학습 구성·사례·출처 범위 확장 |
| 5.5.2 조건 변경 연습 | USER-v1.1 | 부분 지원 | directions.html / 게임플랜 학습·근거 펼치기 | 동일 지식 registry·공식 사실·제한 사례 | loading-study.js / directions.js / loading-knowledge.json | 기존 학습 경로, 모든 포지션/강의 내용 미검증 | 미확인 | 원문 학습 구성·사례·출처 범위 확장 |
| 5.5.3 세부 실행과 회복 | USER-v1.1 | 부분 지원 | directions.html / 게임플랜 학습·근거 펼치기 | 동일 지식 registry·공식 사실·제한 사례 | loading-study.js / directions.js / loading-knowledge.json | 기존 학습 경로, 모든 포지션/강의 내용 미검증 | 미확인 | 원문 학습 구성·사례·출처 범위 확장 |
| 5.6.1 주장·출처 | USER-v1.1 | 부분 지원 | directions.html / 게임플랜 학습·근거 펼치기 | 동일 지식 registry·공식 사실·제한 사례 | loading-study.js / directions.js / loading-knowledge.json | 기존 학습 경로, 모든 포지션/강의 내용 미검증 | 미확인 | 원문 학습 구성·사례·출처 범위 확장 |
| 5.6.2 적용 범위·신뢰 정보 | USER-v1.1 | 부분 지원 | directions.html / 게임플랜 학습·근거 펼치기 | 동일 지식 registry·공식 사실·제한 사례 | loading-study.js / directions.js / loading-knowledge.json | 기존 학습 경로, 모든 포지션/강의 내용 미검증 | 미확인 | 원문 학습 구성·사례·출처 범위 확장 |
| 5.6.3 충돌·검토 이력 | USER-v1.1 | 부분 지원 | directions.html / 게임플랜 학습·근거 펼치기 | 동일 지식 registry·공식 사실·제한 사례 | loading-study.js / directions.js / loading-knowledge.json | 기존 학습 경로, 모든 포지션/강의 내용 미검증 | 미확인 | 원문 학습 구성·사례·출처 범위 확장 |
| 6.1.1 기능별 지원 상태 | USER-v1.1 | 부분 지원 | status.html / private review / 저장소 인수 기록 | 실제 CI·수집·검토 결과 | directions-status.json / 기존 evidence·review / 본 대응표 | 실행/문서/전술효과 분리 | 미확인 | 상태 UI와 실제 운영 결과 연결 |
| 6.1.2 콘텐츠 적용 범위 | USER-v1.1 | 부분 지원 | status.html / private review / 저장소 인수 기록 | 실제 CI·수집·검토 결과 | directions-status.json / 기존 evidence·review / 본 대응표 | 실행/문서/전술효과 분리 | 미확인 | 상태 UI와 실제 운영 결과 연결 |
| 6.2.1 수집·갱신 요약 | USER-v1.1 | 부분 지원 | status.html / private review / 저장소 인수 기록 | 실제 CI·수집·검토 결과 | directions-status.json / 기존 evidence·review / 본 대응표 | 실행/문서/전술효과 분리 | 미확인 | 상태 UI와 실제 운영 결과 연결 |
| 6.2.1.1 갱신·검토 운영 상태 | USER-v1.1 | 부분 지원 | status.html / private review / 저장소 인수 기록 | 실제 CI·수집·검토 결과 | 기존 Actions cron 및 scheduler-runs.json | 등록·최근 실행 조회, 일/주/月 신규 파이프라인 미등록 | 미확인 | 공식 변경 확인/주간 내용/월간 범위 작업의 기존 scheduler 내 구현 |
| 6.2.2 연결 문제 안내 | USER-v1.1 | 부분 지원 | status.html / private review / 저장소 인수 기록 | 실제 CI·수집·검토 결과 | directions-status.json / 기존 evidence·review / 본 대응표 | 실행/문서/전술효과 분리 | 미확인 | 상태 UI와 실제 운영 결과 연결 |
| 6.3.1 검토 결과 목록 | USER-v1.1 | 부분 지원 | status.html / private review / 저장소 인수 기록 | 실제 CI·수집·검토 결과 | directions-status.json / 기존 evidence·review / 본 대응표 | 실행/문서/전술효과 분리 | 미확인 | 상태 UI와 실제 운영 결과 연결 |
| 6.3.1.1 오류와 반례의 재현 정보 | USER-v1.1 | 부분 지원 | status.html / private review / 저장소 인수 기록 | 실제 CI·수집·검토 결과 | 현 입력·규칙 ID·공식 fact 링크, 일부 immutable history | 전체 의존성 영향 재현 미검증 | 미확인 | 문장/규칙 버전·반례·기술 변경 영향 완전 추적 |
| 6.3.2 변경 영향 | USER-v1.1 | 부분 지원 | status.html / private review / 저장소 인수 기록 | 실제 CI·수집·검토 결과 | directions-status.json / 기존 evidence·review / 본 대응표 | 실행/문서/전술효과 분리 | 미확인 | 상태 UI와 실제 운영 결과 연결 |
| 6.3.2.1 판단규칙의 추적 | USER-v1.1 | 부분 지원 | status.html / private review / 저장소 인수 기록 | 실제 CI·수집·검토 결과 | 현 입력·규칙 ID·공식 fact 링크, 일부 immutable history | 전체 의존성 영향 재현 미검증 | 미확인 | 문장/규칙 버전·반례·기술 변경 영향 완전 추적 |
| 6.4.1 버전·배포·검사 | USER-v1.1 | 부분 지원 | status.html / private review / 저장소 인수 기록 | 실제 CI·수집·검토 결과 | directions-status.json / 기존 evidence·review / 본 대응표 | 실행/문서/전술효과 분리 | 미확인 | 상태 UI와 실제 운영 결과 연결 |
| 6.4.2 사용량·호출 기록 | USER-v1.1 | 부분 지원 | status.html / private review / 저장소 인수 기록 | 실제 CI·수집·검토 결과 | directions-status.json / 기존 evidence·review / 본 대응표 | 실행/문서/전술효과 분리 | 미확인 | 상태 UI와 실제 운영 결과 연결 |
| 6.4.3 검증 종류 구분 | USER-v1.1 | 부분 지원 | status.html / private review / 저장소 인수 기록 | 실제 CI·수집·검토 결과 | directions-status.json / 기존 evidence·review / 본 대응표 | 실행/문서/전술효과 분리 | 미확인 | 상태 UI와 실제 운영 결과 연결 |


## 2026-10-24 v1.3 delta (implemented and tested; publication receipts in result.md)

Current requirement source is the attached v1.3; original v1.1 IDs above remain unchanged. Requirement-by-requirement comparison and actual ZIP discrepancy are in docs/gameplan-content/2026-10-19.md. 2.2.1–4: default overall commentary and no duplicate full prose in details. Partial 2.3.1/2.3.3–6/2.4.1, 2.6.1–4: optional income/opportunity/enemy-wave assumptions, separate necessity/feasibility, shared action/prose/detail, relative wave/move costs. Source: planboard.reconcileSituation / composeNarrative; same loading.html and PC /loading paths. Retained official16.20.1 data and unreviewed tactical scope. Product PR127/128 merged to3013f30. Source439f554 affected106 and sourcecf2c590 affected90, both source/preservation/full local Chromium/requiredPR3 PASS; exact product main3 PASS. Final publication and public verification receipts are in evidence/actual-evidence/handoff-v11/result.md. Prior deployment cells remain historical. Remaining all-matchup content, actual coaching effects and external live scope are not marked complete.

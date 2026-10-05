# R7 Player-grounded evidence continuation

2026-10-05 KST. Risk **DEEP**, D1/D2 evidence scope. R8 개발 아님. 실제 원 업로더의15초 Player-style POV sequence1개를 확보하고 Reference-first·blind selective Vision·기존 State reducer 경계를 검증했다. **새 실제 관찰이 생겼지만 Primary acceptance의 VERIFIED Player State/완전한 Decision Reference/동일 경기 Player–Truth pair는 아직0이다.** 이 미완료를 완료로 보고하지 않는다.

| Repository / provenance | 이번 확인 |
|---|---|
| 실제 시작 main HEAD | `47a5ebc60dcdb7182cc1aef791c3c8814566ad61` |
| 종료 HEAD | 이 보고서를 포함한 게시 commit을 GitHub main ref에서 별도 fresh-read하여 최종 응답에 기록; self-referential SHA를 문서에 추측해 넣지 않음 |
| 실제 materialization | GitHub240/240 blobs 일치 후 시작; 현재 Work의 로컬은 Git checkout이 아닌 materialized tree |
| handoff 인수 | CURRENT_HANDOFF, continuation report/input package, R7/real/continuation contracts·fixtures·evidence·verifiers·Freeze와 최신 test/workflow 확인 |
| 시작 branch / PR / Actions | main1개 / open PR0 / workflow runs0; 실제 게시 후 다시 확인 |
| 과거 근거 | 기존26direct/2derived와 R0–R7-continuation 보존·재사용; 새 실적으로 재계수하지 않음 |

## 무엇이 실제로 개선됐는가

Primary source: <https://vimeo.com/651298214>. 공개 원 업로더 페이지 → 페이지에 표시된 public embed → HLS init+3ordered video segments. native bytes를 그대로 연결했고 변환·오버레이 추가·오디오 취득은 없다. 1920×1080/30fps/15.033333초, SHA-256 `94ee285b5270ea0157170645d4a8d845b9e14205fbc55b0a11d393d7210f4372`. 공개 원본·playlist·조각/프레임 hashes와 획득 제한은 `evidence/r7-player-grounded/public-pov-audit.json`에 기록했다. signed temporary URL과 전체 원본을 Git에 재게시하지 않았다.

Tristana의 native HP/resource/skill HUD·minimap·clock16:43→16:57과 같은 화면 sequence가 있다. uploader=실제 조종자 여부, matchId, patch, queue/mode는 독립 인증되지 않았다. 파일명2021.11.29는 patch 인증이 아니다. 오른쪽 외부 통계와 minimap timer overlay는 제외했다. 기존2024 HF 경기와 합치지 않았다.

| 분모 / 결과 | 값 | 해석 |
|---|---:|---|
| 유지한 source-level direct / derived | 26 / 2 | 기존 동일 pair 근거; 신규 Player 검증 아님 |
| 신규 사용 가능한 POV sequence | 1 | 원본 native 연속 영상; 관전자 화면 승격 아님 |
| 신규 exploratory Player sequence Reference | 1 | AI operator의 선고정 기록; complete Decision Reference 아님 |
| 신규 selective clip Vision | 1 | 고정4프레임+보조3프레임; 프레임7개를 경기7개로 세지 않음 |
| 선고정 기록 vs blind AI 전사 | 64/64 | null6개 포함. 일치율은 human-gold accuracy가 아님 |
| PLAYER VERIFIED_DIRECT / VERIFIED_DERIVED | 0 / 0 | AI 일치와 수동 기록을 VERIFIED로 승격하지 않음 |
| 완전한 Player Decision Reference | 0 | 필요한 초기 문맥·버전 Knowledge·독립 검증 부족 |
| 동일 경기·동일시각 독립 Player/Truth pair | 0 | 같은 영상의 나중 kill banner는 독립 Ground Truth 아님 |
| 실제 Decision / Coaching validation N | 0 / 0 | 미검증 State에서 판단 정확도를 계산하지 않음 |
| Accuracy | null | 임의 수치/목표 없음 |

기존10 Representative slots를 유지했다. R7-REP-01 Lane trade에 새 partial sequence를 연결했고 R7-REP-02의 CS 변화는 같은 영상 보충 관찰이다. 이를 독립 사례2개로 세지 않았다. 정글·teamfight 유형은 새 검증 없음. 원본 baseline fixture는 그대로이고 새 overlay만 추가했다.

## Reference → Observation → State

`fixtures/r7-player-grounded/player-reference-initial.json`을09:27:43 KST에 잠근 후 context를 공유하지 않은 blind extractor가09:30:09 KST에 전사했다. 원본 lock SHA `591f3d2d2d25c4e0423e15ff74480723a39cd4a4702d9da0759b28c4d45a98a8` 유지. Human annotator0이며 두 AI의 동의를 ground truth로 사용하지 않는다. 보조7/11/12초 프레임에는 선고정 정답이 없어 정확도 비교 분모에서 제외했다.

F1 clip0.1초/game16:43의 own HP987/1341, resource337/465, level9, KDA1/3/0, CS57 등을 별도 source hash/시각·관점으로 기존 R3 Observation에 넣었다. 모두 MANUAL/quality UNVERIFIED다. DERIVED health_fraction은 원 HP/maxHP를 lineage로 연결하며 **CONDITIONAL**을 유지한다. 전체 KNOWN0. null cooldown은 unreadable/no numeric display이며 READY로 해석하지 않는다. Patch는 실제 버전 대신 명시적 audit sentinel `UNKNOWN_FROM_CAPTURE`다.

L0 관찰: 읽을 수 있는 HUD와 제한된 화면 geometry. L1: 계보가 있는 HP비율 진단만. L2 Strategic/action permission 생성0. 기존29변수 overlay는 pending12/Vision-required12/inference3/manual2를 유지했고, 새 clip에서 관찰한13개 변수의 부분 범위만 추가했다. 숫자 cooldown은 Skill Availability 전체나 key ultimate permission을 검증하지 않는다. 화면 위치는 world coordinate/거리나 안전한 퇴로가 아니다.

## No-hindsight 실제 경계 검사

새 `scripts/audit_player_pov_r7.py`는 기존 Observation/Snapshot/reducer와 비교 함수를 재사용한다. 원 video와7frame hashes, 원 Reference lock, Reference-before-extraction을 fresh 검사했다.

- 이후3기준 프레임에서 온 **51개 Observation/Derived를 FUTURE_EVENT로 제외**했다.
- later KDA2/3/0·level10과 shutdown 결과를 넣어도 F1 State는 own kills1/level9를 유지하며, F1-only State와 동일하다.
- 독립 Ground Truth는 UNAVAILABLE로 별도 유지. enemy jungle/return path/follow-up/skill readiness는 UNKNOWN.
- 실제 HF pair의 다른 session observation을 이 POV request에 join하면 cross-session 거절. 외부 overlay 값은 입력0.
- REAL ReviewInput은 기존 evidence_kind guard에서만 거절됐음을 확인했다. SYNTHETIC 재라벨·Engine 실행0.

**PASS의 범위는 실제 자료의 시간/session/입력 경계다. 같은 경기 Player/Truth 대조나 Decision Quality PASS가 아니다.** sparse sample의 공중 이동·W20 표시·kill banner는 observation이며 skill target/order·의도·판단 품질 확정은 하지 않는다.

## Structured schema gap 처리

기존 LiveClient extractor의 이 Match/Timeline 입력 PRESENT0/17은 **UNSUPPORTED_SOURCE_SCHEMA**이며 데이터 없음이 아니다. 새 `coach_audit/postgame.py`는 이미 보존한 exact pair만 허용하는 additive **archive-only diagnostic**이다. 일반 모든 Match-v5 지원이나 real Coach importer로 보고하지 않는다.

- exact byte hashes, match/game/roster participant join, BSON int64, timestamp monotonicity/clock basis 검사.
- archive cutoff 이하 마지막 frame만 선택. interpolation/TTL 추정 없음.
-13raw 진단 출력과2파생 출력(HP비율/CS), source pointers/hash/formula/parents. 이는 기존26/2와 별도의 새 검증 사례 수가 아니다.
- 상대 archive coordinate는 POST_GAME_ONLY/visibility UNKNOWN/player_known false. future frames·모든 timeline events·Match final stats/time/outcome 제외.
- Player Information/Truth=None, decision_candidate facts=[], strategic0, Engine/Coach disabled.

이전 scratch raw는 새 Work에 없어 보존된 exact206 byte range를 한 번씩 복원하고 기존 hash와 일치시켰다. HF 재탐색/새 pair 계수는 하지 않았다. 영향 분석과 targeted17검사는 `SCHEMA_ADAPTER.md` 및 `schema-adapter-impact.json`에 있다.

## Missing information과 판단 검증 제한

F1 이전 영상은0.1초뿐이다. 이전5–10초의 opponent skill cast/last-seen/정글 접근·wave 흐름·행동 개시 이유를 모른다. 적이 화면에 없다는 것을 맵에 없음으로 바꾸지 않았다. 공격 후 kill/CS 증가만으로 당시 ALL_IN이나 CHASE를 정당화하지 않는다.

기존 exploratory Information Requirement를 사용하면 THREAT→DEEP_CHASE의 필요한 source-backed KNOWN 정보가 부족하다. 모든 missing을 자동 수집하거나 NO_ACTION으로 확정하지 않는다. 낮은 commitment/되돌릴 수 있는 행동 후보도 자기 위치·상대 위치·시야·퇴로/응답창의 당시 근거가 있을 때만 검토 가능하며 현재 action permission은 NOT_EVALUATED다. Patch 적용 Knowledge/Strategy/Decision/Execution/Coach는 State gate 뒤에서 NOT_RUN, Outcome은 별도 관찰만 남겼다.

오류 판정: **EVIDENCE_GAP**(완전한 Player reference·독립 truth·Knowledge 부족), 기존 **UNSUPPORTED_SOURCE_SCHEMA**(새 exact pair archive diagnostic에서만 지원), **EXTERNAL_ENVIRONMENT_BLOCKER**(사용자의 game PC가 아닌 Work에서 기존 local process/listener 부재). 새 STATE/DECISION/COACH 오류 판정0이며, 비교 불일치0은 오류가 없다는 일반 주장도 아니다.

## 검증·보호·실패 이력

Fresh baseline111/111, protected9/9. R6 browser/mobile는 hash/scope가 동일한 **Historical** evidence이며 fresh browser PASS로 보고하지 않는다. Adapter targeted17/17(skip0) 추가; 기존111 expected와 core 수정0. Freeze Manifest27files의 hash를 최종 재검사하고 모든 historical240blobs는 mutable CURRENT_HANDOFF 외에 보존한다. 새로운 evidence run directory만 append했다.

최초 실패를 `task-history.json`과 public audit에 보존: blob response decoding·큰 stdin 전달 문제 → repair 후240/240; 이전 raw scratch 부재 → pinned206/hash 복원; specific public403/404 → 다른 공개 primary route; bare Vimeo config403 → 사이트에 표시된 public embed로 정상 성공. local endpoint retry0. 최초 실패를 최종 PASS로 지우지 않았다.

Dynamic Workflow: fresh intake/PLAN → 독립 public source와 schema 영향 분석만 fan-out → Reference-first 독립 Vision → deterministic hash/schema/targeted gate → completeness check. 같은 source의 반복 조사나 agent 다수결은 없었다. Frozen 의미/Core Contract/Invariant/old Golden/expected 변경0. 기존 C3_REAL_AUDIT_PROPOSAL은 미승인·미구현으로 보존한다. 이번 D1/D2 진단에 **새 D3 없음**. 보호된 real Engine 활성화는 이 continuation에서 구현하지 않았다.

## Acceptance와 다음 단계

Primary3조건은 아직 미충족이다. D1/D2에서 가능한 내부 evidence 재사용 감사, Library의 관련 보존자료 검색, 공개 candidate/원 업로더 연결 감사, schema adapter 영향/구현·검증, existing minimum input package 확인은 완료했다. 새 POV 획득 성공으로 **현재 환경에서 Player POV 전체 획득 불가라는 B 결론도 사용하지 않는다.** 정확한 남은 blocker는 이 원본의 독립 same-time Player reference/patch·문맥·truth 연결 부재와 기존 실제 Engine 입력 계약 경계다. 공개 route의 bounded audit는 public-pov-audit의 추가 결과를 따른다; 전체 인터넷이 소진됐다는 주장이 아니다.

중복 요청 문서는 만들지 않았다. 기존 [MINIMUM_INPUT_PACKAGE](../r7-continuation/MINIMUM_INPUT_PACKAGE.md)를 사용한다. 다음 최소 자료는 한 장면의 Player POV15–30초(결정 전5–10초+행동/응답/이탈), native clock/minimap/HP/level/skills와 간단한 자기 champion/영상시각·게임clock/촬영 관점 메모다. patch/matchId는 아는 경우만, 모르면 UNKNOWN. **현재 클립의 정적 전사를 독립 검증할 수 있는 operator source-backed review도 먼저 쓸 수 있다.** Screenshot1장은 해당 시점 정적 State 검증에만 사용하고 sequence/intent/퇴로 확정에 쓰지 않는다. 관전자 Replay는 같은 경기·시각 연결이 있을 때 별도 Truth/Extractor 검증용이며 Player input 자동 승격 없음. Credential/API secret·유료 서비스·PC 원격접속 불필요.

새 자료가 확보되면 자동 순서는 기존 bytes 복원/연결 검사 → Operator Reference 잠금 → 해당 변수의 extraction 비교/quality 판정 → Player/Truth 분리·no-hindsight → version Knowledge·Decision/Coach gate다. Source가 검증되지 않으면 그대로 UNKNOWN/CONDITIONAL. 패치/HUD 기반 높은 영향·낮은 비용 필드부터 자동화하며 큰 Vision framework·intent/심리 자동화는 우선하지 않는다. 이번 실행 뒤 자동 대기나 백그라운드 수집은 설정하지 않았다.

# C3 Proposal — 실제 자료의 offline 평가 계약

상태: **PROPOSED / NOT_APPROVED / NOT_IMPLEMENTED**. R8 기능·제품 활성화 제안이 아니다.

## 막힌 지점과 근거

현재 실제 자료는 source/observation/state 진단까지 처리했다. 기존 `ReviewInput.evidence_kind`는 `SYNTHETIC`만 받는다(`coach_v1/models.py`). 실제 화면 관찰을 넣은 완전한 `REAL` 요청 5개는 모두 이 필드의 `literal_error`로 거절됐다. `engine.py/run_review`의 TEST + allow_synthetic + SYNTHETIC 관문도 독립적으로 실제 실행을 막는다. 실행 결과의 evidence/mode/annotation 표기도 합성 전용이다.

자료를 SYNTHETIC으로 재명명하거나 기존 관문을 제거하면 실제 검증과 합성 계보가 섞인다. 이는 사용자가 보호한 Core Contract/Invariant 경계다. `docs/r7/REFERENCE_PROTOCOL.md`의 실제 자료 강제 주입 금지와 별도 proposal 규칙에 따라 D3로 분리한다. 독립 read-only boundary 검토도 같은 첫 관문과 두 번째 관문을 확인했다. Frozen27 변경 필요성은 확인되지 않았다.

## 선택지

| 선택 | 승인 후 범위 | 영향 |
|---|---|---|
| **1. offline REAL_AUDIT 계약만 승인 — 추천** | 별도 실제 근거 입력/출력 계약, 기존 비교 로직의 공유 가능성 검토, 검증된 State/Knowledge에서만 Decision 단계 진입, 기준 자료와 단계별 평가 연결 | 실제 자료의 진실한 분류를 유지한다. 데이터·지식이 부족한 사례는 계속 BLOCKED. 제품/실시간 기능을 활성화하지 않는다. |
| 2. 현재 계약 유지 | D1/D2 수집·참조·진단만 계속, 기존 엔진 평가 NOT_RUN 유지 | 계약 변경 없음. 실제 Coaching N은 엔진에서 늘릴 수 없다. |

결제·credential 요청이 아니라 보호 계약 변경 승인이다. 이 문서 자체는 변경 승인이 아니다.

## 선택 1의 구체적인 제한

- 기존 SYNTHETIC/TEST 입력·출력과 111개 테스트 expected, 보호9, Frozen27, R6/R7 evidence는 그대로 둔다.
- 별도 명시적인 `REAL_AUDIT` namespace에서만 실제 자료를 수용한다. 기존 `run_review`의 guard를 완화하지 않는다. 동일한 symbolic comparison을 공유하려면 내부 순수 로직만 추출하고 합성 경로와 실제 경로를 각각 검증한다.
- source hash/session/clock/patch/perspective/visibility/reference revision을 연결하고, 알 수 없는 값은 UNKNOWN/CONDITIONAL 그대로 유지한다. MANUAL/Vision 동의를 VERIFIED 사실로 승격하지 않는다.
- State가 검증되지 않으면 Knowledge 이후를 평가하지 않는다. Knowledge가 검토되지 않으면 strategy/decision 평가는 NOT_RUN이다. 입력자가 FAVORABLE이라고 적었다는 이유만으로 실제 정확도를 PASS로 만들지 않는다.
- 출력은 단계별 판정·분모·누락·불일치·출처를 포함한 offline 감사 결과다. recommendation 생성, 자동 게임 행동, LIVE/PRE_GAME/POST_GAME UI 노출은 범위 밖이다.
- 기존 POST_GAME 종료 확인, 모드 분리, release gates를 유지한다. 공개 스크린샷의 업로드 날짜를 patch 또는 경기 종료 증명으로 사용하지 않는다.
- 합성 경로 회귀, 실제/합성 분류 분리, observer/future/cross-session 누설 차단, unknown·manual lineage 비승격, 실제 평가 N 산정과 단계 순서에 targeted 검증을 붙인다.

## 승인 후 자동 진행

계약·schema를 먼저 작성 → 기존 경로와 별도 offline adapter 구현 → 보호 회귀 → 검증 가능한 실제 기준 자료 연결 → State/Knowledge 관문 → eligible 사례에서만 Decision/Coach 평가 → 분모와 blocker 보고. 현재 4개 player-style still에는 patch/경기/종료 확인과 연속 동작이 없어 승인만으로 Coaching N이나 Accuracy가 생기지 않는다.

CRITICAL 경계 제안이며, 구현은 승인 전 중단한다. Frozen 문서 또는 판단 규칙을 추가로 바꿔야 한다는 근거가 나오는 경우 새 proposal로 분리한다.

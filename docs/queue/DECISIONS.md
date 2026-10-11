# Queue v1.1 결정 기록

## 2026-10-11 USER_QUEUE_V1.1
사용자가 선택한 TOP/JUNGLE/MID/BOTTOM/SUPPORT 모두 경기 전 게임플랜 대상이다.
2026-10-09 원딜 한정 범위를 대체한다. 자주 하는 네 챔피언은 범위 제한이 아니다.
설계·구현·무료 의존성·검증·게시·병합은 사전 승인, 실제 비용만 재승인 대상이다.
지식 승인 권한은 사용자 웹 조작에만 있다. 합성 테스트 승인은 실제 사용자 승인과 구분한다.

## MAIN_ADDENDUM_2026-10-11
기존 Frozen 계약과 PR10 원문을 수정하지 않고 별도 경기 전 계약을 추가한다.
기존 TEST 엔진의 실제 경기 차단을 유지하고 상태의 출처/누락/충돌 처리 원칙을 재사용한다.
기존 main/research SQLite schema2를 그대로 유지하며 확장 입력·계획은 별도 sidecar에 저장한다.
새 서버는 기존 Workbench를 확장하여 기존 모든 경로와 /pregame 화면을 함께 제공한다.
기존 서버 실행법도 보존한다. 새 화면에서 기존 수동 픽창 저장본을 직접 선택하여 가져온다.
기존 백업 format1은 두 기존 DB만 포함한다. 새 sidecar는 별도 명시적 export/restore 대상으로 안내한다.

저장소에 현재 플레이 패치의 확정값이 없다. Golden 입력의 patch는 null/미확인으로 시작한다.
Q05가 확보한16.20.1은 날짜·출처가 있는 정적 데이터 버전이며 플레이 패치를 자동 확정하지 않는다.
실제 사용자는 자신의 경기 패치를 확인하여 입력해야 한다. 패치 미확인은 규칙 적용을 보류한다.

완료 주장은 Q01~Q14 상태와 실제 검증 증거로 한다. 실제 코칭 N=0/accuracy=null을 유지한다.

Phase correction: original null/arbitrary phase maps UNKNOWN, never confirms PRE_GAME. Input phase supports UNKNOWN and explicitly user-confirmed PRE_GAME; UNKNOWN holds all tactical rules. RED→GREEN import-phase receipts preserved.

Plan retry correction: idempotency binds original HTTP expected_revision request, not later evaluator content. Replay after input/knowledge changes returns original saved plan with current EXPIRED state; source loss/rejection never regenerates old output as new. Archive validates retry fingerprint and rolls back hostile rows. RED/GREEN receipts preserved.

## 2026-10-11 USER_QUEUE_V1.4 / additive Q15–Q18
v1.4 supersedes earlier queue directives. All five selected roles remain supported; four frequent champions are preferences. Existing PR11/PR12 receipts and immutable sources reused. New v2 guards/initiative/operations and v3 conditional movement keep legacy v1 serialization/digests and frozen payloads unchanged. Automatic free publication and merge authorized; user web knowledge decisions never impersonated.

Minute frames with jitter use explicit elapsed-minute floor bins and exact annotation timestamps; no phase inferred from minutes. Q15 actual collection uses trusted main-only workflow RIOT_API_KEY environment, anonymous aggregate artifacts7days; raw/private memory discarded at termination and never uploaded to public artifacts. Auth failure is BLOCKED_EXTERNAL and never an empty usable statistic. Position-population resource rate statistics and cumulative matchup differences disclose different units, cluster sample counts and limitations. Most-common completed nonboot item candidate pair is not confirmed champion core knowledge.

Real current gameplay patch remains unavailable in repository. Data Dragon16.20.1 is a static source archive, not a runtime-patch decision. Actual golden input patch=null until user provides it; separate numeric16.19 synthetic data is labelledTEST and isolated. Reviewer found framejitter, units, expired-card, phase/source/CI validation defects; RED/GREEN evidence preserved. Q10–Q14 and postgame Q16/Q17/Q18 need actual PC/video/independent reference; coaching N0/accuracy=null.

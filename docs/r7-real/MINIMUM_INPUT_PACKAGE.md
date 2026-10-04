# 실제 검증을 unlock하는 최소 입력 패키지

현재 공개 화면의 획득 자체는 해결됐다. 부족한 것은 같은 경기의 검증 가능한 patch·시계·관점·동작과 필요한 지식이다. 계정 비밀번호·API secret·유료 서비스는 필요하지 않다.

## 가장 작은 자료

세 유형을 처음부터 한꺼번에 보낼 필요는 없다. 아래 한 장면 패키지부터 검증할 수 있다.

| 자료 | 권장 형식/길이 | 용도 |
|---|---|---|
| 플레이어 시점 짧은 영상 | MP4/WebM, 대략 15–30초: 결정 전 5–10초와 행동·이탈이 보일 만큼. 마지막 결과만 있는 킬 하이라이트는 부족하다. | trade sequence, 움직임, 스킬 상호작용, 피해/위협 흡수, 지원 접근성을 구분 |
| 플레이어 시점 정지 화면 | PNG/JPEG, 본 화면·minimap·시간·HP/자원·레벨·스킬 HUD가 읽히는 원본 해상도. 1080p 권장, 필수 규칙 아님. | 한 시점 HUD 값, 가시 인원, 대략적인 wave geometry/spacing. 연속 과정·의도·안전한 퇴로는 확정 불가 |
| 짧은 sidecar 메모 | JSON 또는 텍스트: patch(알면), game clock, 영상 시간, 자기 챔피언, POV 종류, matchId(알면), 촬영/수집 방법. 모르는 값은 UNKNOWN | 출처·버전·시계·관점 연결. 실제 POST_GAME 실행에는 별도 검증 가능한 종료 정보가 필요 |
| 구조화 수집물 — 있으면 | 실제 게임 PC에서 기존 `scripts/collect_local.py`로 만든 원본 JSON과 수집 receipt/CA hash. 또는 **동일 matchId** Match+Timeline과 수집 provenance | 화면과 비영상 자료 비교. 사후 opponent coordinates는 당시 player-known으로 옮기지 않음 |

길이·해상도는 입력 준비 안내이며 새로운 acceptance cutoff/TTL/정확도 목표가 아니다. 사용자의 닉네임이나 채팅은 가려도 되지만 필요한 HUD·minimap·clock을 가리지 않는다.

## 세 유형의 우선순위

1. Lane/CS/trade: 공격 전 minion·HP·스킬 상태, 실제 공격/응답, 종료 또는 이탈이 보이는 player POV.
2. Jungle uncertainty/reachability: 당시 마지막으로 적을 봤던 정보가 있으면 함께 기록. 실제 위치를 모르더라도 UNKNOWN 기준 상태로 유효하다. 숨겨진 적 위치를 억지로 채우지 않는다.
3. Teamfight/threat absorption/damage window: 진입 전 진형, 핵심 스킬 대상, 캐리 위치, 후속 접근과 이탈이 보이는 player POV. 정지 화면 하나로 absorption이나 damage attribution을 확정하지 않는다.

## 관전자 Replay 사용 범위

관전자 화면은 따로 GROUND_TRUTH/Extractor 검증 자료로 쓸 수 있다. 같은 경기·시계와 player POV의 관계가 확인되어야 한다. 관전자 scoreboard, fog 해제, 숨겨진 정글 위치, 이후 결과는 당시 Decision 입력에서 제외한다. 팀 fog를 선택한 관전자도 양 팀 HUD 등 추가 정보가 있으므로 player POV와 동일하지 않다. 현재 확보한 관전자와 player-style blog 이미지들은 같은 경기라는 증거가 없어 join을 금지했다.

## 사용자 도움 없이 이미 완료한 대안

공개 원본 이미지 5개, source hash/위치, Reference-first lock, 독립 AI Vision, structured archive schema 진단, 실제 observer 제외/cross-session 거절, 기존111/보호9 재현을 완료했다. 이 패키지는 단순한 Replay 요청 대신 남은 각 blocker를 해제하는 데 필요한 자료를 정의한다. 실제 Engine 평가 계약 승인(C3)과 자료 보강은 서로 다른 조건이다.

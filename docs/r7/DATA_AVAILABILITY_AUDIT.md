# R7 데이터 가용성 감사

대상은 Source → State → Decision(출처→상태→판단) 연결을 위한 **문서·보존 표본의 가용성**이다. 실제 경기 수집, 인식 정확도 또는 경기 종료 검증 완료를 주장하지 않는다. 기계 판독 목록과 실제 감사 시각은 `contracts/r7/sources.json`에 있다. Frozen 설계·코어는 변경하지 않았다.

## 증거 수준과 결과

| ID | 확인한 근거 | 현재 판정 |
|---|---|---|
| SRC-LIVE-DOC | 공식 Game Client/Live Client 문서와 이벤트 예제 새 조회 | DOCUMENTED_ONLY(문서 확인만) |
| SRC-LIVE-SAMPLE | R5 공식 예제 원문·receipt, SHA-256 재계산 | 문서 예제 무결성 확인; 실경기 미검증 |
| SRC-MATCH-DOC | 공식 Timeline 참조 열기 및 제한된 검색 | REFERENCE_SHELL_ONLY(스키마 확보 실패) |
| SRC-DDRAGON | 공식 정적 데이터·버전 문서 | DOCUMENTED_ONLY |
| SRC-REPLAY-DOC | 공식 재생·카메라·녹화 제어 문서 | DOCUMENTED_ONLY |

모든 출처의 `actual_match_sample_verified`, `decision_eligible`, `coaching_enabled`는 false다. 실경기 VERIFIED 항목은 없다. 이 표의 미확보는 API에 기능이 존재하지 않는다는 증명이 아니다.

## 공식 문서에서 직접 확인한 경계

- [Game Client/Live Client](https://developer.riotgames.com/docs/lol#game-client-api): 로컬 HTTPS 및 실행 중 경기 데이터 경로를 설명한다. 문서가 있다는 사실만으로 현재 PC 접근 가능성이 확보되지는 않는다.
- [이벤트 예제](https://static.developer.riotgames.com/docs/lol/liveclientdata_events.json): 시작·미니언 생성·처치·목표물 이벤트 예제가 있다. ID와 시각은 반복된 0이며, 조회한 목록에 `GameEnd`는 없다. 실제 순차 기록으로 사용하지 않는다.
- [Data Dragon](https://developer.riotgames.com/docs/lol#data-dragon): 정적 콘텐츠이며 갱신 지연·지역별 버전 차이가 가능하다. 경기 상태를 제공하는 출처로 취급하지 않는다.
- [Replay API](https://developer.riotgames.com/docs/lol#replay-api): 기본 비활성 상태의 로컬 재생·카메라·녹화 제어다. 전술 객체 추출 기능이 검증됐다는 뜻은 아니다.

운영 빈도·수신 지연·이벤트 완전성은 조회 근거로 확정하지 못했다. 공통 초 단위 TTL이나 수집 주기를 새 판단 기준으로 만들지 않는다. TLS 검증을 끄는 대안은 사용하지 않는다.

## 보존 예제: 직접 확인한 필드와 과잉해석 금지

출처: [공식 응답 예제](https://static.developer.riotgames.com/docs/lol/liveclientdata_sample.json).

- 원문: `evidence/r5/official-sample-retry-20261004/raw.json`
- 수집 증빙: 같은 디렉터리의 `receipt.json`
- 수집 시각: `2026-10-04T10:25:30.131161+00:00`
- 크기: 6,561 bytes
- SHA-256: `d754b6c27edf950679dd9478742a8c4b9402e70101a3b46764c28f2aeafd72d3`
- 이번 감사에서 실제 바이트를 다시 해시해 receipt와 일치를 확인했다. 일치는 파일 동일성만 증명한다.

| 직접 읽은 JSON 경로 | 확인 가능한 구조 | 확정하면 안 되는 상태 | 최소 보완 |
|---|---|---|---|
| `/activePlayer/championStats/currentHealth`, `maxHealth`, `resourceValue`, `resourceMax` | 자기 상태 수치 필드가 예제에 존재 | 현재 경기의 실제 체력·자원, 적 체력 | 실제 로컬 수집과 해당 시점 HUD 대조 |
| `/activePlayer/currentGold`, `/activePlayer/level` | 골드·레벨 필드 | 시각 사이 증가 원인·정확한 레벨업 시점 | 연속 수집·화면 시점 정렬 |
| `/activePlayer/abilities/Q` 등 | 스킬 ID·이름·설명·레벨 | 준비 여부·남은 재사용 대기시간·시전 성공 | 스킬 상태의 별도 관찰·적용 규칙 근거 |
| `/allPlayers/*/position` | 보존 표본 첫 항목은 빈 문자열 `""`; 새 조회 공식 문서의 예시는 `MIDDLE` | 맵 x/y 좌표, 현재 정글 위치 | 위치가 보이는 플레이어 관점 영상 |
| `/allPlayers/*/scores` | CS·처치 등의 점수 구조 | 웨이브 방향·미니언 전투 기여 | 미니언 종류·체력·위치·공격 대상 장면 |
| `/allPlayers/*/isDead`, `respawnTimer`, `items`, `summonerSpells` | 상태·아이템·주문 메타데이터 구조 | 업데이트 지연 없음, 주문 사용 가능, 예상 교전 승리 | 각 필드 의미·시점·누락 검증 |
| `/events/Events` | 보존 예제에는 `GameStart` 한 건 | 모든 사건 포함·진짜 경기 종료 | 실제 사건 전후 수집·종료 확인 독립 계약 |
| `/gameData/gameTime`, `gameMode`, `mapName`, `mapNumber`, `mapTerrain` | 게임 시각·모드·맵 구조 | 실제 경기 ID·패치·영상과 동일한 시간축 | 경기 식별·패치·시계 연결 근거 |

이 예제는 `gameTime=0`이며 여러 상태 수치도 0이다. 0을 누락으로 단정하거나 실제 경기 측정값으로 승격하지 않는다. 미니언별 객체, 실제 이탈 가능성, 아군 호응 의도, 숨겨진 적 위치는 이 예제로 확보하지 못했다.

**스키마 변화 근거:** 현재 공식 문서는 RiotID 계열 필드를 설명하지만 보존 예제의 해당 구조는 `summonerName`만 포함한다. 오래된 예제에 맞춘 파서 통과를 최신 클라이언트 호환성으로 표시해서는 안 된다.

## Match/Timeline 확보 한계

조회 대상: [Match 참조](https://developer.riotgames.com/apis#match-v5/GET_getMatch), [Timeline 참조](https://developer.riotgames.com/apis#match-v5/GET_getTimeline).

Timeline URL을 실제 열었으나 도구가 반환한 문서는 36줄짜리 API 포털 외곽 구조뿐이며 응답 스키마는 없었다. 공식 사이트 대상으로 시도한 제한된 검색도 필요한 스키마를 확보하지 못했다. 무관한 검색 결과는 근거에서 제외했다.

따라서 이 감사에서 Match/Timeline의 `confirmed_response_fields=[]`다. 기억이나 제3자 자료로 좌표·타임스탬프 단위·프레임 간격을 채우지 않는다. 특히 “1분마다 프레임”, “정확한 교전 위치·스킬 상태를 얻음”을 확인 사실로 쓰지 않는다. 공식 스키마와 권한 있는 실제 응답이 확보되기 전까지 연결된 상태는 UNKNOWN(미확인)으로 유지한다.

## 연결 계약에 적용할 보완 및 차단 요인

아래는 외부 문서 인용이 아니라 **이번 감사의 구현 권고**다.

1. 원문 hash·JSON pointer·수집시각·게임시각·출처 버전·관점·경기/세션 ID를 함께 유지한다. 직접 값과 파생값의 lineage(근거 계보)를 분리한다.
2. `DOCUMENTATION_SAMPLE` → `REAL_SAMPLE` 자동 승격을 금지한다. GameEnd라는 문자열이 들어가도 종료 인증은 별도로 검증한다.
3. 실제 필드 누락/충돌/지연 시 이유를 보존하고 종속 판단을 제한한다. 스키마 예제의 0이나 기본 위치를 보충값으로 넣지 않는다.
4. Data Dragon 자산은 버전·언어·hash와 경기 패치 대응이 확보된 뒤 규칙에 연결한다. 자산 날짜를 경기 패치로 간주하지 않는다.
5. 영상/리플레이 시계와 게임 시계를 연결하고 당시 플레이어에게 보인 정보와 관전자 사후 정보를 분리한다. 실제 영상 판독과 사례 적용은 root 담당 검증에 연결한다.

현재 실데이터 활성화 차단 요인은 실제 로컬 표본, 최신 OpenAPI, 필드 의미/누락/갱신 검증, 경기 식별·패치·관점·시계 연결, 독립 종료 확인, Match/Timeline 공식 스키마 미확보다. 이것은 합성 계약 검증 진행을 막지 않지만 실제 코칭 판정의 근거는 될 수 없다.

## 감사 정정 이력

초기 감사는 공식 문서의 `MIDDLE`을 보존 표본의 값으로 잘못 기재했다. root의 독립 확인 후 실제 보존 원문을 다시 읽어 `/allPlayers/0/position=""`를 확인하고 위 표와 출처 목록을 정정했다. 원문·해시는 변경하지 않았다. 어느 쪽도 x/y 좌표 근거가 아니다.

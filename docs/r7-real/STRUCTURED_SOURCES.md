# R7 실제 자료 후속 — 공개 구조화 자료 조사

2026-10-04 UTC. 기준 remote main `6951f5cafbc360c4637107fe3a3fb4dc0eed0d25`.
**공개 Match/Timeline 후보 원본 2개 확보·Git blob 무결성 확인. 동일 경기 pair는 아니며, 실제 경기/player Reference 검증 분모는 여전히 0이다.**

이 조사는 R7의 자료 확보 후속이다. 코어·Source Matrix·동결 계약·기존 fixture/기대값/과거 evidence를 수정하지 않았다. Match/Timeline adapter, R8 기능, 실제 engine mode를 추가하지 않았고 실제 자료를 SYNTHETIC으로 바꾸어 넣지 않았다.

## 확보한 최소 자료

공개 프로젝트 [eoinpinaqui/machine-learning](https://github.com/eoinpinaqui/machine-learning)의 [고정 README](https://github.com/eoinpinaqui/machine-learning/blob/ef01002ec22f5815abfd10490f43f5cab758d81c/README.md)는 프로젝트 dataset을 Riot API로 수집했다고 설명한다. 수집 코드에는 timeline 호출이 있다. 이는 **publisher의 수집 주장**이며 root의 두 JSON 파일 각각에 대한 first-party 응답 영수증은 아니다. 특히 `match.json`의 `queueId=400`은 README가 설명한 ranked/high-ranked 수집 범위와 다르다. 현실적인 숫자만으로 실제 원천을 검증했다고 판정하지 않는다.

| 확보 원본 | 직접 관찰한 내용 | 무결성·판정 |
|---|---|---|
| [match.json](https://github.com/eoinpinaqui/machine-learning/blob/ef01002ec22f5815abfd10490f43f5cab758d81c/match.json) | `EUW1_5564229827`; version `11.23.409.111`; start `1637337220017`, end `1637338775965`; participant 10명; participant 1 Yorick/team 100 | 69,604 bytes; Git blob `c9b5aca569e950ecaad95b0480ae669c2dd62449` 일치. `PUBLISHER_COLLECTED_CANDIDATE_NOT_INDEPENDENTLY_VERIFIED` |
| [timeline.json](https://github.com/eoinpinaqui/machine-learning/blob/ef01002ec22f5815abfd10490f43f5cab758d81c/timeline.json) | `EUW1_5584130728`; frame 35개; `frameInterval=60000`; 시간·participant frame·health/resource/gold/level·position·이벤트가 실제 확보 JSON에 존재 | 1,751,842 bytes; Git blob `d56d832f4d5b99515036238a19e6dd4724304c5c` 일치. 같은 후보 등급이며 player-visible 여부 미확인 |

두 `metadata.matchId`가 다르므로 **JOIN REJECTED**다. Match의 patch, champion/participant identity, 절대 시작 시각을 Timeline으로 전파하지 않았다. Timeline `/info/gameVersion`, `/info/gameStartTimestamp`는 없다. Timeline 내부 participant 번호/PUUID의 존재도 두 경기의 동일 identity, 관점, 당시 가시성을 대신하지 않는다.

Timeline frame 1의 timestamp는 `60003`이고 participant 1의 health/maxHealth는 `574/586`, level은 `1`, position은 `(8147,5066)`, currentGold는 `0`, minionsKilled는 `1`이다. 같은 frame 첫 이벤트는 `SKILL_LEVEL_UP`, participant `7`, skillSlot `3`, timestamp `3075`다. 이는 선택한 사후 구조화 필드의 관찰이다. opponent position을 PLAYER_INFORMATION_STATE에 넣지 않았고, PLAYER_INFORMATION_STATE와 GROUND_TRUTH_STATE 둘 다 성립했다고 주장하지 않는다.

## Reference 선동결과 현재 추출기 확인

현재 추출기를 호출하기 **전에**, 위 원본 표시에서 선택한 23개 direct field를 수동 전사하여 audit의 `manual_reference`에 동결했다. Freeze timestamp는 `2026-10-04T11:33:03.435502+00:00`, canonical SHA256은 `57e0b05e9a125f245903fef01a42dcfbc7e9db8fae3652d3654bb002ec044271`이다. 이후 검사에서 reference hash는 변하지 않았다.

| 확인 | 결과 | 해석 |
|---|---|---|
| 선택 direct field의 원본 전사 대조 | 23/23 일치 | 선택한 source field의 정확한 전사 확인. 독립 실제 경기/player-state accuracy가 아님 |
| 기존 `coach_audit.extraction.extract` → Match 원본 | allowlist 17개 중 PRESENT 0, MISSING 17 | 현재 추출기는 Live Client 경로를 읽는다. `/metadata`, `/info` Match 경로 지원 없음 |
| 같은 추출기 → Timeline 원본 | PRESENT 0, MISSING 17 | Timeline field가 없는 것이 아니라 현재 추출기의 schema coverage가 없음 |
| Health fraction | UNKNOWN | `/activePlayer/championStats/...` 입력이 없어서 계산하지 않음 |
| Engine/실제 코칭 | 미호출 / disabled | source authenticity, matched patch/clock/POV/reference 미확인 |

현재 추출기에 원본 SHA256을 전달해 integrity 확인은 true다. Source authenticity는 false, coaching은 false로 유지되었다. 이 결과는 `EXTRACTION_ERROR`의 schema coverage gap 후보와 `EVIDENCE_GAP`을 분리하는 근거이며 실제 상태/판단 정확도 수치가 아니다. 새 adapter 구현·기존 fixture 변경은 이 후속 범위에 없다.

## 다른 경로와 접근 한계

3개 targeted search round와 후보별 제한된 경로 확인 후 탐색을 종료했다. 대량 수집·credential·결제는 없었다.

| 원천 | 현재 확인한 접근·자료 | 채택/차단 이유 |
|---|---|---|
| [Riot Developer Portal](https://developer.riotgames.com/docs/portal) | 공식 getting-started/API-key/401 설명으로 인증 필요 확인 | API key 없이 직접 Match/Timeline 수집하지 않음. API reference web reader는 service index만 반환하여 상세 schema 표를 fresh-read했다고 주장하지 않음 |
| [AngryBacteria dataset](https://huggingface.co/datasets/AngryBacteria/league_of_legends) / [files](https://huggingface.co/datasets/AngryBacteria/league_of_legends/tree/main) | publisher는 Riot API 수집 13,000+ 경기와 minute timeline/XY를 주장. 공개 파일 표시는 Match 1.34 GB, Timeline 14.5 GB | complete matching record 미확보. 단일 file web open은 Internal Error. 대량 파일 다운로드하지 않음 |
| [GPTilt current catalogue](https://github.com/gptilt/datasets) | 현재 외부 published 표는 Leaguepedia esports entity/match 자료. Riot 내부 표는 league-entry/rank snapshot | 과거 real-match dataset 발표로 현재 raw match/timeline 접근을 추정하지 않음 |
| [ddori curation](https://github.com/ddori/LeagueOfLegends_Data_Curation) | collector는 Match/Timeline 저장 코드, inspected `SoloQ/data`는 515-byte clean CSV 1개 | raw pair 아님. `provenance.json`은 43,635-byte clean CSV와 510,886-byte raw CSV를 설명하므로 현재 515-byte 파일을 인증하지 못함 |
| [artoria data-science-lol](https://github.com/artoria-dev/data-science-lol) | API 수집 설명과 코드. README 전체 구조는 pseudo-version, participant fragment는 완전한 tied record가 아님 | inspected get-data/readme-files에서 bounded complete JSON pair 없음. 문서 fragment를 실제 Reference로 승격하지 않음 |

큰 timeline의 commit-pinned raw connector 호출은 HTTP 400(file too large/unsupported)으로 실패했다. 같은 Git blob endpoint로 받아 UTF-8 원본을 보존했고, 파일 길이와 `SHA1("blob " + length + NUL + bytes)`가 GitHub blob SHA와 각각 일치했다. 필드·schema·값을 변환하지 않았다.

## 무결성, 공개 범위, 다음 unlock

| 원본 | SHA256 |
|---|---|
| Match | `0b599f9af3ee3cbdc9b316ca336008102f8b591835961f8ecdf80814bc0387bd` |
| Timeline | `b4f75ac8aae6ffdb3afdb4235084481f80dc93dc37f9d8c7eca4724aad1a9726` |

원본은 public repository 밖에 보관했다. 공개 audit에는 이름·PUUID·account ID를 넣지 않았으며 raw 재배포 license는 `NOT_ESTABLISHED`다. Git 무결성은 진짜 Riot 수집 인증 또는 player 당시 정보 인증이 아니다.

기계 판독 결과: `evidence/r7-real/structured-source-audit.json`.
현재 `verified_real_matches=0`, `verified_player_references=0`, state/coaching accuracy는 null이다. 다만 시간·position·자원·event 경로의 후보 가용성 자체를 문서 예제로 숨기지는 않는다.

다음 unlock은 같은 matchId의 Match+Timeline과 exact-file 수집 provenance, 그 경기의 patch/절대 시각, player POV 화면·시계·당시 visibility reference를 묶는 것이다. Replay metadata/실제 replay 원본은 이번 조사에서 확보하지 못했다. 확보된 사후 coordinate를 당시 opponent knowledge로 치환하지 않으며 engine의 SYNTHETIC_ONLY 제한도 유지한다.

# R7 실제 근거 추가 검증

2026-10-04 UTC. Dynamic Workflow v1.0의 D1/D2 evidence 작업, 위험 DEEP 유지. R8 개발과 제품 활성화는 수행하지 않았다.

**동일 경기 Match·Timeline 기준 자료 1개와 새 교전 화면 관찰을 추가했다. 완전한 플레이어 Reference 3개 및 실제 State/Decision 검증은 아직 미완료다.**

## Actual HEAD와 보존

시작 시 GitHub main을 fresh-read한 실제 HEAD는 `16adaf60753663c95d236e586c34b466fc929f43`였다. 사용자가 보고한 `6951f5cafbc360c4637107fe3a3fb4dc0eed0d25`의 직접 후속 커밋이며, 기존 R7-real 공개 화면 감사가 이미 포함되어 있었다. 실제 Git checkout의 201개 tracked blob을 대조했고 변경 전 모두 일치했다. 이후 반영 커밋은 GitHub main/commit receipt로 확인한다.

기존 R7 verifier를 고정 dependency pydantic 2.13.5, Python 3.12.14에서 실행했다. **111/111, skipped0·failure0·error0, 보호9/9 PASS**. Frozen27 hash도 일치한다. verifier 내부의 `baseline_head=884a435`는 보존된 R6 기준점이며 이번 실행 HEAD가 아니다. 새 binding은 `evidence/r7-continuation/repository-baseline.json`이다.

R6 browser·390px mobile 결과는 변경 없는 코드와 함께 Historical로 보존했다. 이번에 새 browser PASS를 주장하지 않는다. R6/R7/R7-real 과거 evidence, 기존 expected와 10 Representative Replay 슬롯은 그대로 보존한다.

## Reference와 Source → State

| 범위 | 실제 결과 | 검증 한계 |
|---|---|---|
| 동일 경기 구조화 Source | Match·Timeline 1쌍, `EUW1_7095952008`, version `14.17.613.973`, 31 Timeline frames | publisher의 Riot 수집 주장; 독립 Riot 응답 인증은 없음 |
| 사후 원본 필드 Reference | **ESTABLISHED_SOURCE_FIELD_REFERENCE 1개**, 선동결26개 pointer 값·타입26/26 일치 | POST_GAME_DATASET 범위; PLAYER_INFORMATION_STATE가 아님 |
| Source-only 파생 기준 | HP `261/1177`, CS `24+0`의 부모·공식·버전 확인 | 현재 Extractor의 파생 출력 또는 player-known 사실로 승격하지 않음 |
| 기존 Extractor | 두 원본 각각 PRESENT0/MISSING17, health fraction UNKNOWN | 현재 Live Client 경로의 미지원 schema; 새 adapter 없음 |
| 기존 화면 근거 | 원본5/5와 PDF container hash fresh 재확인; 기존 감사 재실행 | 신규5사례로 재계수하지 않음 |
| 새 교전 화면 | Garen HUD 12:26, 선택14필드 operator/독립 AI Vision14/14 일치 | 부분 기준1개; teamfight와 lane skirmish 분류 미확정, human precision gold 아님 |
| 완전한 플레이어 Replay Reference | **0** | 기존3 부분 슬롯과 새 contested C 후보를 완전한3유형으로 세지 않음 |
| 29변수의 PLAYER 검증 | **VERIFIED_DIRECT0 / VERIFIED_DERIVED0** | source 필드 검증과 PLAYER State 검증의 분모를 구분 |

구조화 원본은 [고정 Hugging Face dataset](https://huggingface.co/datasets/AngryBacteria/league_of_legends/tree/477404f532b1014b7fc61c3b1c024e988f883a26)의 BSON-JSON Mongo export다. `$numberLong` wrapper를 원본에 보존했다. 변환되지 않은 Riot HTTP 응답이라고 부르지 않는다. Match와 Timeline의 matchId, gameId, 10명 participant 관계, 최종 level/CS 및 winner가 일치했다. Match 최종 KDA/레벨을 5분의 상태로 혼합하지 않았다.

전체 대용량 파일 대신 제한된 head에서 pair를 찾고, Match113,459bytes와 Timeline1,199,490bytes의 exact range를 고정 revision에서 다시 받았다. HTTP206, Content-Range, SHA256, 앞서 받은 slice와 byte 일치를 확인했다. 전체 LFS 파일을 검증했다는 주장은 하지 않는다. 원본은 Git 밖에 두고 공개 evidence에 이름·PUUID·account 값을 재게시하지 않았다.

먼저 고정한 Reference는 Timeline frame5, participant1(Aatrox), timestamp300153ms, level5, HP261/1177, CS24, position(5597,13531) 등이다. 사후 record의 필드는 재현 가능한 직접 자료이며 AI끼리의 게임 판단 합의를 정답으로 사용하지 않았다. 당시 player POV·opponent visibility는 UNKNOWN이다. 추가 source 인증 미확인은 정확한 JSON 전사 비교를 무효화하는 조건으로 추가하지 않았다.

현재 extractor 비교는 기존 함수를 그대로 실행했다. Match/Timeline 데이터가 없다는 뜻이 아니라 현재 path allowlist가 다른 schema를 읽지 못한다는 뜻이다. agent 원본 receipt의 `EXTRACTION_ERROR_SCHEMA_COVERAGE_GAP` 라벨은 보존하되, 최종 원인 분류는 **EVIDENCE_GAP / UNSUPPORTED_SOURCE_SCHEMA**다. 지원한다고 약속한 adapter가 실제 값을 오독한 오류는 발견하지 않았다.

## Source Matrix 재분류

R7 최초 baseline은 pending11 / Vision-required13 / inference3 / manual2였다. 실제 시작 HEAD의 기존 overlay는 Champion Position의 사후 Timeline 경로를 반영하여 **pending12 / Vision-required12 / inference3 / manual2**였다. 이번에도 이 PLAYER 가용성 집계는 유지한다.

새 additive overlay에서는 Champion/Role/Level/CS/Time/Position/HP·Resource의 **7행 선택 subfield**에 실제 structured provenance를 연결했다. 이는 전체7변수의 의미가 모두 해결되었다는 집계가 아니다. source-level direct26개 필드와 derived2개 기준을 별도로 기록한다. Vision/manual 결과와 source archive의 좌표를 PLAYER DIRECT로 승격하지 않는다. source 경로가 생긴 변수도 cooldown, visibility, wave geometry 등 남은 의미를 그대로 보존한다.

## Selective Vision와 Missing Information

새 [GameStar 원본 화면](https://images.cgames.de/images/gamestar/287/league-of-legends_2664879.jpg)을 기준 작성 전에 확인하고 hash와 reference를 잠근 뒤 별도 blind AI Vision을 실행했다. 기존5화면의 Vision receipt는 보존·재대조했고, 새 화면1개만 fresh Vision이다. 정적 spacing/배치/가시 인원과 HUD만 관찰했다. 위협 흡수, carry 역할, skill order, damage window, follow-up permission, trade sequence는 미확인이다.

Garen은 HUD 주인이지만 주 화면에 보이지 않는다. **카메라 중심을 플레이어의 실제 위치로 바꾸지 않았다.** 화면에는 아군3·적 Lux1과 Bot 표기가 보인다. 이것만으로 사람 간 경쟁 경기나 완전한 teamfight를 확정하지 않는다.

| Decision Point | 알았던 정보 | 미확인 정보와 조건부 행동 | 필요한 추가 정보 |
|---|---|---|---|
| Garen lane / Irelia CS, 기존 A | HUD·주 화면의 적/minion | trade·last-hit timing, 적 응답, cooldown, 퇴로 | 결정 전 player POV sequence와 필요한 HUD |
| Ryze, 기존 B | HUD와 주 화면 적0 | 적 정글 last-seen·접근 경로, map visibility; chase/all-in은 조건부 | 당시 보였던 last-seen/event와 행동 목표 |
| 새 Garen camera, contested C | own HUD, 보이는3아군/1적의 정적 배치 | own position, 도달 가능성, skill timing/target, 역할, 퇴로; commit/absorb/window advice 미판정 | own position과 전후 상호작용이 보이는 짧은 POV sequence |
| Aatrox 사후 frame5 | record의 level·HP·CS·좌표 | 플레이어 시야·행동 목표·적 응답·wave/skill sequence 없음 | 같은 경기·시계의 player reference; 사후 좌표를 대체 정보로 쓰지 않음 |

기존 PDF의 Garen06:19 장면과 GameStar의 다른 인코딩 이미지가 같은 화면인 것도 확인했다. PDF bibliography에 GameStar가 있으므로 PDF 게시를 원촬영자 인증이나 두 독립 원천으로 해석하지 않는다. 기존 hash/기록을 지우지 않고 새 provenance 한계로 기록했다.

## No-hindsight와 단계별 평가

실제 observer 화면 제외 및 cross-session 거절은 기존 감사에서 다시 PASS였다. 그러나 같은 경기·시각의 player/ground-truth pair는 **0**이다. 따라서 실제 Decision no-hindsight 품질 검증은 **미완료**다. 새 Timeline의 사후 enemy coordinates·최종 winner·미래 events는 source archive에만 보관했고 Decision input을 생성하지 않았다.

| 평가 단계 | 결과 |
|---|---|
| State correctness | source 필드26/26 확인; 기존 extractor 미지원, PLAYER State 검증 미완료 |
| Knowledge applicability | 새 dataset patch는 확인; 특정 행동에 필요한 지식 적용 검토 NOT_RUN |
| Strategy correctness / Decision validity | NOT_RUN; 검증된 player State와 행동 문맥 부족 |
| Execution advice / Coach fidelity | NOT_RUN; 실제 advice/output 없음 |
| Coaching validation | **N=0, Accuracy=null** |

현재 `ReviewInput` schema와 `run_review`는 여전히 SYNTHETIC/TEST 경로만 허용한다. 실제 자료를 SYNTHETIC으로 이름만 바꾸거나 guard를 완화하지 않았다. 이번 추가 코드는 원본 bytes/hash·reference·기존 추출 결과를 다시 확인하는 offline verification harness뿐이다.

Frozen 의미 변경이 필요하다는 새 근거는 없다. **이번 범위 D3 불필요**, 기존 C3 proposal은 미승인/미구현 상태로 보존한다. 그 문서의 존재를 이유로 사용자에게 승인받은 D1/D2 source/reference 작업을 중단하지 않았다. 향후 실제 평가 연결은 기존 계약을 보존할 수 있는지 영향분석부터 수행한다.

## Layer별 오류와 Retry / Repair / Replan

- EXTRACTION_ERROR: 기존 observer HP 오독2필드는 revision/history와 함께 보존. 신규 선택14필드 불일치0은 해당 전사 비교 범위뿐이다.
- STATE_ERROR: 같은 경기의 상대 가시성·시계가 검증되지 않음. 서로 다른 source를 join하거나 관전자 정보를 넣은 실제 오판은 발생시키지 않았다.
- KNOWLEDGE/STRATEGY/DECISION/EXECUTION/COACH: 평가하지 않았으며 오류0 또는 정확도PASS로 보고하지 않는다.
- EVIDENCE_GAP: player 시야·시점 관계, 연속 동작, source 원촬영자/독립 Riot 인증 한계, 미지원 Match/Timeline schema.
- Local: 프로세스/2999 listener 없음, IPv4·IPv6 ECONNREFUSED, strict HTTPS는 TLS 전에 종료. permission/certificate/구현 버그라고 추정하지 않고 **EXTERNAL_ENVIRONMENT_BLOCKER**로 분류했다. Work PC와 사용자 게임 PC의 연결/VPN 경로도 미구성이다. 추가 retry0.
- HF: splits200 → first-rows500·parquet conversion failure → 제한된 HTTP206 head → 같은 경기 발견 → exact range fresh 확인으로 REPLAN. 전체GB 다운로드·유료/API credential 없음.
- 화면: 기존5hash 복구 → publisher gallery의 제한된 JPEG18개(약3.27MB) 탐색 → 새 기준1개 선택·선동결 → blind Vision. 18downloads를18references로 세지 않았다. Medal404/Reddit403은 각각1회 후 중단; 실패한 YouTube 경로는 재시도하지 않았다.

## 완료 기준과 다음 자동 단계

**A는 미충족**이다. source Reference1개와 부분 화면 기준을 완전한3 actual State/Decision 시나리오로 바꾸어 세지 않는다. **B도 전체 자료 획득 불가로 확인되지 않았다.** 공개 화면·동일 경기 데이터 획득에 성공했고, 로컬 endpoint만 환경 blocker다. 이번 결과를 사용자가 지정한 최종 acceptance 완료로 처리하지 않는다.

현재 확보 자료로 할 수 있는 D1/D2 원본 무결성·reference 비교·지원 schema 진단·선택 Vision·정보 경계·회귀를 수행했다. 추가 player 자료와 행동 문맥이 없으므로 downstream 정확도는 미측정이다. 최소 입력은 [MINIMUM_INPUT_PACKAGE.md](MINIMUM_INPUT_PACKAGE.md)에 구체화했다. 자동 대기나 백그라운드 수집은 설정하지 않았다.

다음은 player POV 한 장면의 source/시계/관점 확인 → operator Reference 선확정 → 현재 extraction과 비교/오류 분류 → decision-relevant 누락만 보충 → patch 지식 적용 검토 → 실제 평가 계약 영향분석 순서다. 기존10슬롯 중 A/B/C에서 검증 가능한 장면을 먼저 연결하고, 사후 자료는 별도 archive로 유지한다.

## 재현

원본 취득에는 아래 고정 URL의 range를 사용한다. 응답이 HTTP206과 지정 Content-Range가 아니거나 SHA256이 다르면 중단한다. 경기 객체·닉네임을 공개 repository에 재게시하지 않는다.

```sh
mkdir -p private/r7-continuation
curl --fail --location --range 9334672-9448130 --output private/r7-continuation/match.json 'https://huggingface.co/datasets/AngryBacteria/league_of_legends/resolve/477404f532b1014b7fc61c3b1c024e988f883a26/match_v5.json'
curl --fail --location --range 1-1199490 --output private/r7-continuation/timeline.json 'https://huggingface.co/datasets/AngryBacteria/league_of_legends/resolve/477404f532b1014b7fc61c3b1c024e988f883a26/timeline_v5.json'
python3 scripts/verify_r7_source_reference.py --match private/r7-continuation/match.json --timeline private/r7-continuation/timeline.json --out private/r7-continuation/recheck-new.json
python3 scripts/verify_r7.py
```

고정 range receipt는 `evidence/r7-continuation/source-range-receipts.json`에 있다. Source reference, 최초 visual reference, lock, 비교 결과, fresh baseline binding과 최종 gate는 `evidence/r7-continuation/` 및 `fixtures/r7-continuation/`에 보관했다.

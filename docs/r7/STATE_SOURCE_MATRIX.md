# R7 State Source Matrix(상태별 출처 대조표)

**29개 변수의 입력 가능성 조사표**이며 실경기 검증·실시간 기능 활성화 선언이 아니다. Frozen(동결) 설계와 R3 코드는 변경하지 않았다.

L0는 Raw State(원천 상태), L1은 Tactical State(전술 상태), L2는 Strategic/Decision State(전략·판단 상태)다. L2는 행동 허용·피해 기회·불가피한 손실·회복 계획 등 판단 결과를 뜻하며 역할·의도 가설을 자동 승격시키는 계층이 아니다. 이는 신뢰도나 구현 진척 등급이 아니다. 상태는 현재 접근 가능한 자료·구현을 기준으로 분류했다. `VERIFIED_DIRECT`·`VERIFIED_DERIVED`로 승격한 실경기 변수는 없다.

| ID | 변수 | 계층 | 우선 조사 출처 | 현재 경로 상태 | 핵심 구분 |
|---|---|---|---|---|---|
| R7-SV-01 | Draft/Champion | L0 | SRC-LIVE-DOC | UNKNOWN_PENDING_VERIFICATION | 진행 중 챔피언 목록이 픽창 revision·ban·phase를 증명하지 않음 |
| R7-SV-02 | Role | L0 | SRC-MANUAL | UNKNOWN_PENDING_VERIFICATION | API position은 지도 좌표가 아님; lane label도 현재 전술적 역할 확정 아님 |
| R7-SV-03 | Level | L0 | SRC-LIVE-DOC | UNKNOWN_PENDING_VERIFICATION | 현재 레벨로 과거 교전 레벨을 덮어쓰지 않음 |
| R7-SV-04 | Item | L0 | SRC-LIVE-DOC | UNKNOWN_PENDING_VERIFICATION | 아이템 보유만으로 액티브·중첩·사용 가능 상태 확정 금지 |
| R7-SV-05 | Rune | L0 | SRC-LIVE-DOC | UNKNOWN_PENDING_VERIFICATION | Data Dragon 정적 룬 정보는 이번 경기 발동 증거 아님 |
| R7-SV-06 | Summoner Spell | L0 | SRC-LIVE-DOC | UNKNOWN_PENDING_VERIFICATION | 시전 관찰만으로 현재 재사용 불가를 확정하지 않음 |
| R7-SV-07 | KDA/CS | L0 | SRC-LIVE-DOC | UNKNOWN_PENDING_VERIFICATION | CS 증가를 wave 위치·방향·우위의 증거로 변환 금지 |
| R7-SV-08 | Game Time | L0 | SRC-LIVE-DOC | UNKNOWN_PENDING_VERIFICATION | 영상 업로드 시각·영상 재생 시간은 game time 아님 |
| R7-SV-09 | Objective | L1 | SRC-LIVE-DOC | UNKNOWN_PENDING_VERIFICATION | objective event는 현재 준비·획득 가능성 또는 팀 우선순위가 아님 |
| R7-SV-10 | Tower | L1 | SRC-LIVE-DOC | UNKNOWN_PENDING_VERIFICATION | 타워 존재만으로 수비 안전을 확정하지 않음 |
| R7-SV-11 | Recall | L0 | SRC-VISION | VISION_REQUIRED | 정지·화면 이탈 또는 집 근처 출현만으로 중간 채널 과정 추정 금지 |
| R7-SV-12 | Champion Position | L0 | SRC-REPLAY-DOC | VISION_REQUIRED | 관전자 위치는 플레이어가 당시 알았던 위치와 별도 저장 |
| R7-SV-13 | Enemy Jungle Information | L0 | SRC-VISION | VISION_REQUIRED | 숨겨진 정글이 관전자에 보였어도 당시 판단 근거로 누설 금지 |
| R7-SV-14 | Jungle Reachability | L1 | SRC-VISION | VISION_REQUIRED | 오래된 last_seen과 직선거리만으로 도착 불가 확정 금지 |
| R7-SV-15 | Wave State | L1 | SRC-VISION | VISION_REQUIRED | CS 누계나 정지화면 마릿수만으로 흐름·crash 완료 확정 금지 |
| R7-SV-16 | Wave Mass | L1 | SRC-VISION | VISION_REQUIRED | 큰 웨이브=전투 우위로 치환 금지 |
| R7-SV-17 | Skill Availability | L1 | SRC-VISION | VISION_REQUIRED | 최근 사용을 현재 unavailable로 바꾸려면 patch 규칙과 시계 검증 필요 |
| R7-SV-18 | Key Ultimate Availability | L1 | SRC-VISION | VISION_REQUIRED | 적 궁극기 실시간 추적 출력은 비활성; 관전자 정보 누설 금지 |
| R7-SV-19 | HP/Resource | L0 | SRC-LIVE-DOC | UNKNOWN_PENDING_VERIFICATION | fixture maxHealth=0은 실제 체력 0 또는 사용 가능한 비율 증거 아님 |
| R7-SV-20 | Numbers | L1 | SRC-VISION | VISION_REQUIRED | 생존 아군 수를 유효 지원 인원으로 자동 집계 금지 |
| R7-SV-21 | Carry Exposure | L1 | SRC-VISION | INFERENCE_ONLY | 캐리 identity와 노출 정도는 KDA 순위 하나로 확정 불가 |
| R7-SV-22 | Follow-up Access | L1 | SRC-VISION | VISION_REQUIRED | 도착 가능=구조/후속 피해 가능 아님; 아군 반응 확정 금지 |
| R7-SV-23 | Return Path | L1 | SRC-VISION | VISION_REQUIRED | 뒤쪽 빈 공간은 안전한 퇴로가 아님 |
| R7-SV-24 | Vision/Fog Information | L0 | SRC-REPLAY-DOC | VISION_REQUIRED | 관전자에서 보이는 적을 PLAYER KNOWN으로 승격 금지 |
| R7-SV-25 | Spacing | L1 | SRC-VISION | VISION_REQUIRED | 픽셀 거리만으로 hit 여부 또는 안전 간격 확정 금지 |
| R7-SV-26 | Formation | L1 | SRC-VISION | INFERENCE_ONLY | 포지션 문자열 또는 정지화면 위치만으로 지속 진형 우세 단정 금지 |
| R7-SV-27 | Player-available Information | L1 | SRC-VISION | MANUAL_ONLY | 보였음과 실제로 알아차렸음도 구분; 시스템 수신 지연과 시야 여부는 별개 |
| R7-SV-28 | Ground Truth | L0 | SRC-REPLAY-DOC | MANUAL_ONLY | 당시 알 수 없던 사실은 outcome-only; 합성 expectation은 실제 정답 아님 |
| R7-SV-29 | Intent Hypothesis | L1 | SRC-MANUAL | INFERENCE_ONLY | 자막 발언은 진술 증거일 뿐 실제 의도·화면 사건 증명 아님 |

`VISION_REQUIRED`는 현재 구조화 예제와 자막으로 부족한 세밀 상태를 장면 관찰로 확인해야 한다는 뜻이다. 향후 검증된 구조화 provider(자료 제공 경로)가 있으면 영상 의존성을 줄일 수 있다. `MANUAL_ONLY`도 수동 진술을 사실로 승격시키지 않는다. `INFERENCE_ONLY`는 가설·조건을 보존한다.

29개 항목은 판단 입력 목록이므로 L2 출력 슬롯을 채우기 위해 입력을 승격하지 않았다. Role(역할)의 명시적 배정 metadata(기록값)는 L0이며, 보호/진입 같은 기여 역할 가설은 별도 L1이다. Carry Exposure(딜러 노출), Follow-up Access(호응 접근성), Formation(진형)은 L1이다. Intent Hypothesis(의도 가설)는 `hypotheses.intent`라는 별도 가설 공간의 L1 입력이며 L2 확정 사실이 아니다.

## 현재 근거와 미확인 범위

- 공식 문서 예제의 `activePlayer/allPlayers/events/gameData` 파싱·hash 검사는 실제 게임 데이터 취득 검증이 아니다.
- 예제는 플레이어 1명과 GameStart 사건만 포함한다. 목표물·타워·귀환 갱신이나 상대 체력 전체 범위를 입증하지 않는다.
- `allPlayers.position`은 좌표로 취급하지 않는다. 역할 라벨·현재 공간 위치·전술적 역할은 별도 의미다.
- 로컬 수집 기록은 `ENDPOINT_UNAVAILABLE`; 실제 지연·누락·갱신·patch·관점은 미검증이다.
- 자막 후보는 발언 검색 결과다. 화면 사건, 의도, 플레이어 인지, 당시 game time을 증명하지 않는다.

## 적용 규칙

1. 수치 TTL(유효 시간), confidence(신뢰도), 거리·쿨다운 cutoff(판정 기준)는 만들지 않는다. JSON 각 행에 사건별 재검증 조건과 필요한 정밀도를 적었다.
2. 현재 R3의 AT_EVENT 관찰은 snapshot과 event_time이 같지 않으면 STALE(오래된 정보)이다. 이번 조사표가 이를 완화하지 않는다.
3. 역사적 목격·시전 사건은 보존해도 현재 위치·재사용 불가로 승격하지 않는다.
4. Ground Truth(사후 확인 사실)와 Player-available Information(당시 플레이어가 접근 가능했던 정보)은 별도 계보로 둔다. 숨겨진 적의 사후 위치를 당시 결정 입력으로 전달하지 않는다.
5. Objective(목표물) 사건과 readiness(준비 상태), 지형상 Return Path(복귀 경로)와 실제 이탈 가능성, Wave Mass(웨이브 규모)와 전투 지원을 분리한다.
6. preferred_source(우선 조사 출처)는 조사 우선순위다. 연결되었거나 해당 필드가 API에서 검증됐다는 의미가 아니다.
7. 수동 입력은 작성자·자료·시각을 갖는 MANUAL(수동 진술)이고 자동으로 OBSERVED(직접 관찰 사실)가 되지 않는다.

## 기계 판독 파일

`contracts/r7/state_source_matrix.json`에 29개 행의 요구 정밀도, provenance(출처 계보), 사건별 신선도, 취득 가능성, 수동 대안, 의미 제한 및 읽은 로컬 근거 SHA-256을 보존했다. 공식 외부 문서의 최신 capability(취득 능력)·정책 검토는 별도 source audit(출처 감사)와 결합해야 한다.

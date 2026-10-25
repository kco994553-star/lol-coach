# 게임플랜 2+3 실제 v5 원문 사례 평가

상태: **실제 v5 엔진 원문 내부 평가 / 최종 소스 커밋 봉인 대기**. 아래 점수는 2026-10-25 실제 `E.analyze` 및 `P.project` 결과를 읽고 평가했다. 소스가 작업 중이어서 `WORKTREE_SNAPSHOT`, `source_commit:null`이다. 내부 문장 평가를 출시 승인이나 실전 전술 검증으로 표시하지 않는다. 실경기 코칭 효과는 **UNMEASURED, N=0**이다.

## 재현과 원문 보존

`node scripts/export_gameplan_2plus3.js --seed 20261025 --require-bound`를 최종 소스 커밋 후 실행한다. 기본 목적지는 `evidence/actual-evidence/gameplan-2plus3-20261025/examples/`이다. 다른 폴더는 `--output <directory>`로 지정한다. `--require-bound`는 실행에 사용한 파일이 HEAD에 없거나 HEAD와 다르면 실패한다. 옵션 없이 실행한 임시 결과는 `WORKTREE_SNAPSHOT`, `source_commit:null`로 표시한다. 다른 작업자의 변경이 실행 도중 발생해도 실패한다. 근거 커밋 이후 증거 파일만 커밋해도 근거 커밋 식별자는 그대로 보존한다.

선정은 정렬한 전체 카탈로그 ID, seed 20261025, xorshift32, Fisher–Yates를 사용한다. 각 팀 5포지션과 중복 없는 10명을 구성하고, 사용자 포지션은 TOP/JUNGLE/MID/BOTTOM/SUPPORT 순서로 한 번씩 고정한다. TOP만 공식 `Tank` 태그와 보존된 공식 둔화/속박/기절/공중 띄우기 설명이 있는 후보로 제한한다. 카탈로그 태그 및 해당 기술 원문·URL·해시를 `selection_basis`에 보존한다. 다른 포지션은 임의 배치이며 역할 적합성이나 정석 픽이라고 주장하지 않는다. 이 제약을 정한 뒤 출력 품질에 따른 재추첨은 하지 않는다.

각 JSON에 원래 입력, 조건 변경 입력, 각각의 전체 `E.analyze` 보고서와 `P.project(report,{currentOnly:true})` 결과, 화면 투영 문자열, 지원 한계, 변경된 입력·출력 경로가 있다. `.md`의 JSON 문자열 값은 같은 투영 문자열의 이스케이프된 원문이다. 문장을 수작업으로 개선하지 않는다. `manifest.json`은 코드/데이터/공식 선택 근거 파일의 SHA-256, 정확한 소스 커밋 또는 미봉인 상태, 각 사례 JSON 해시를 기록한다. 선정·실행은 외부 API나 난수 시스템 시계에 의존하지 않는다.

이번 v5 짝 비교는 같은 가정 출처·상태를 유지하고 `situation.fields.ally_followup.value`의 AVAILABLE → UNAVAILABLE 한 필드만 바꾼다. 나머지 상황 정보는 unknown이다. 출처는 `user-scenario`, 관측 시각은 null이며 실제 경기 관측으로 표시하지 않는다. 이전 v4 예비 실행의 점수는 이 평가에서 제거했다. 서로 다른 입력 버전의 실행을 짝으로 혼합하지 않는다.

## 평가 척도와 별도 차단 판정

내부 문장 평가는 여섯 항목 각각 0~2점이다. 정확성은 보존한 사실·입력·지원 한계와 문장의 부합 범위만 평가하며 승률·실전 전술 정확도를 측정하지 않는다.

| 항목 | 0 | 1 | 2 |
|---|---|---|---|
| 정확성 | 입력/역할/근거와 불일치 | 범위를 제한한 일반 원칙 | 해당 입력과 근거에 부합하는 구체 판단 |
| 구체성 | 역할을 바꿔도 같은 문장 | 역할 또는 조건 연결 | 실제 픽 수단·상황·전환의 구체 연결 |
| 실행 가능성 | 행동 선택 불가/잘못된 행동 | 일반 행동과 일부 중단 조건 | 가능한 즉시 행동·금지·전환이 명확 |
| 위험/목표 가시성 | 핵심 목표/위험 누락 | 일반 목표/위험 노출 | 목표·상위 위협·위치·행동·중단이 기본 노출 |
| 불확실성 | 미확인을 사실로 표시 | 일부 제한만 표시 | 가정·미확인·비지원 범위를 명시 |
| 모순 | 실제 모순 발견 | 제한적 연결/완전 검증 불가 | 관련 상하단·짝 비교의 정합성 확인 |

**P0/P1은 점수와 별도로 차단한다.** 총점이 높아도 허위 관측·소스 위조·위험한 판단 모순·핵심 사용자 흐름 실패를 상쇄하지 않는다. P0/P1 확인 전에는 출시 PASS를 기록하지 않는다. 비지원 입력의 낮은 구체성은 지원 범위를 공개하고 보류할 수 있으며, 평가 문서나 사례 원문만 손으로 고쳐 통과시키지 않는다.

## 평가 대상과 소스 상태

원문 폴더는 `/workspace/gp23-artifacts/examples-v5-provisional/`이다. 재현 seed는 20261025이며 TOP Trundle / JUNGLE Darius / MID Ekko / BOTTOM Aurora / SUPPORT Karthus를 그대로 유지했다. TOP은 공식 Tank·제어 사실로 제한했고 나머지는 임의 포지션 배치다. Aurora BOTTOM을 사수 챔피언 고유 지원으로, Karthus SUPPORT를 검증된 보호 전문 전술 지원으로 집계하지 않는다.

이번 실행의 기준 HEAD는 `a12330d7030c7b74dc748820b68e8b7841940148`이고 변경 파일 해시는 이 폴더 `manifest.json`의 `source.sha256`에 있다. 엔진·UI가 바뀌는 도중이므로 이 HEAD가 실행 소스와 동일하다고 주장하지 않는다. 최종 소스 봉인 후 root가 같은 seed로 다시 실행하며, 내용이 달라진 경우 아래 인용·판정을 재확인한다.

| 사례 JSON | 사용자 | SHA-256 |
|---|---|---|
| `01-top.json` | TOP Trundle | `a38ec9a2da3b68ff9e71a1cc6d442aa25dcbbfa30c0dc64f02579158103d69e9` |
| `02-jungle.json` | JUNGLE Darius | `98da2e072e5b9cda3edf7800a5c254e96df9618338e80e3e83c611b806486efe` |
| `03-mid.json` | MID Ekko | `35eff1263ea21d0618fbe1b409b3f152b2653d23eab393d451aca7845b67193f` |
| `04-bottom.json` | BOTTOM Aurora | `a10c2c8d6c77978a27ab7103ee831f90170f7801ceca124f643f2fa8f94d4a2e` |
| `05-support.json` | SUPPORT Karthus | `2fe8cccaa548647c3cd9801e6a666b2ff6a2bb6e5b531cfd303dc117117ee0e6` |

각 사례의 원문 기준 경로는 `baseline/view/...`, 조건 변경은 `changed/view/...`이다. 이 원문에는 2개 상단 개요, 비교표, 하단 3카드, 각 단계 행동 5개가 함께 보존된다. 모든 사례의 `baseline/report/coach/supported`는 false이며 15개 카드의 coverage는 `GENERAL_ONLY`다. 이 제한은 실패를 숨기기 위한 문구가 아니라 현재 실제 지원 범위다.

## 여섯 차원 평가 — 두 조건을 함께 검토

아래 **정확성 1은 범위가 제한된 일반 원칙으로서의 부합**이다. 경기 결과 정확도 점수가 아니다. 구체성 0을 보존했다. 이름이 들어간 기능 후보가 있다고 해당 챔피언의 현재 주요 위협·최적 전술이 확인됐다고 평가하지 않았다. 모순 2는 이 5쌍에서 입력→판단→태그·본문이 같은 조건을 따름을 확인한 좁은 점수이며, 모든 조합에서 모순이 없다는 뜻이 아니다. 총점으로 출시 여부를 판정하지 않는다.

| 사례 | 정확성 | 구체성 | 실행 가능성 | 위험/목표 가시성 | 불확실성 | 모순 |
|---|---|---|---|---|---|---|
| 01 TOP Trundle | 1 — L1/U 범위 | 0 — F1, 탱커 사실만으로 개별 실행안 없음 | 1 — L1/L2 일반 확인·수급 행동 | 1 — F1/P, 현재 위협 우선순위 미확인 | 2 — I/U/P | 2 — L1→L2, O1→O2, X |
| 02 JUNGLE Darius | 1 — J1/J2, 라이너 자기 막타 지시 제거 | 1 — 캠프/라인 손실 역할 연결 J1/J2, 고유 매치업 없음 | 1 — J1/J2의 개입·대기 선택 | 1 — J1/F1/P, 구체 위협 미확인 | 2 — I/U/P | 2 — J3, O1→O2, X |
| 03 MID Ekko | 1 — L1/U 범위 | 0 — L1/F1은 TOP/BOTTOM과 같은 원칙 | 1 — L1/L2의 확인·회복 선택 | 1 — F1/P, 제드 기능 후보는 현재 우선순위 아님 | 2 — I/U/P | 2 — L1→L2, O1→O2, X |
| 04 BOTTOM Aurora | 1 — L1/U 범위, 사수 고유 지원 주장 없음 | 0 — F1, 사수 위협 대응 개별 근거 없음 | 1 — L1/L2 일반 자원 선택 | 1 — F1/P, 공격 공간·대상별 도달 구체화 부족 | 2 — I/U/P | 2 — L1→L2, O1→O2, X |
| 05 SUPPORT Karthus | 1 — S1/S2의 아군 수급 지원 범위 | 1 — 서포터 수급 원칙 S1/S2, 고유 보호 수단 검증 없음 | 1 — S1 조건부 정리·귀환 준비 | 1 — S1/F1/P, 대상별 위험 미확인 | 2 — I/U/P | 2 — S1의 조건부 유지·태그 변경, O1→O2, X |

원문 인용의 약어는 다음과 같다. 아래 따옴표 문장은 원문을 발췌한 것이며, 평가자가 개선해 넣은 코칭 문장이 아니다.

| 인용 | 사례·경로 | 실제 출력 원문/값 |
|---|---|---|
| U | 모든 사례 `/baseline/view/cards/0/coverage/detail` | “아래 행동과 본문은 공통 원칙입니다. 이 조합에 맞춘 개별 계획으로 검증되지 않았습니다.” |
| I | 모든 사례 `/baseline/report/coach/planboard/gp23/information/label` | “경기 전 선택 가정 · 실제 관측 아님” |
| L1 | 01/03/04 `/baseline/view/cards/0/decision/action` | “현재 보이는 미니언 방향·체력과 내 처리·반격 자원을 확인하고, 확인된 거리에서 받을 자원만 고른다.” |
| L2 | 01/03/04 `/changed/view/cards/0/decision/action` | “조작할 여건이 부족하면 더 나가서 웨이브를 바꾸려 하지 말고, 닿는 자원과 포기할 CS·지원·귀환을 비교한다.” |
| J1 | 02 `/baseline/view/cards/0/decision/action` | “지원 조건이 부족하거나 미확인이면 갱킹을 강제하지 않고, 확인된 캠프 성장·회복·귀환과 아군 방어 요청을 비교한다.” |
| J2 | 02 `/baseline/view/cards/0/decision/reason` | “대기하면 캠프 경험치와 다음 지원 시간을 잃지만, 무리한 개입도 라인 손실과 역갱 위험을 남긴다. 상대 동선·도착 시간은 계산하지 않는다.” |
| J3 | 02 `/baseline/view/cards/0/decision/decision_id` → `/changed/view/cards/0/decision/decision_id` | “JUNGLE_CHECK → JUNGLE_PREPARE” |
| S1 | 05 `/baseline/view/cards/0/decision/action` | “아군이 받을 경험치·막타 자리를 보호하고, 호응·자원이 없으면 진입 대신 함께 정리·귀환할 여건을 준비한다.” |
| S2 | 05 `/baseline/view/cards/0/decision/reason` | “서포터 자신의 막타보다 아군의 접근·체력과 로밍할 때 남는 위험을 함께 비교한다.” |
| O1 | 01/03/04/05 `/baseline/view/cards/1/decision/action` | “선택한 웨이브 행동을 실제 마쳤는지 확인한 뒤 아군과 이동할 길·목표물을 고른다. 처리만으로 자유로운 합류가 생겼다고 가정하지 않는다.” |
| O2 | 모든 사례 `/changed/view/cards/1/decision/action` | “아군이 움직일 수 없거나 자원이 부족하면 가까운 회복·구매와 받을 자원을 고르고, 지원·재집결로 다음 행동의 여건을 바꾼다.” |
| F1 | 모든 사례 `/baseline/view/cards/2/decision/action` | “배운 공격·제어와 남은 반격·퇴로를 확인해 가까운 대상에 기여할 행동을 고르고, 기여할 수 없다면 자리와 목표를 바꾼다.” |
| P | 모든 사례 `/baseline/view/cards/2/decision/threat_priority/label` | “현재 위협 우선순위 미확인” |
| X | 모든 사례 `/baseline/view/cards/2/decision/execution` → `/changed/view/cards/2/decision/execution` | “UNKNOWN → BLOCKED” |
| R | 모든 사례 `/baseline/view/cards/1/explanation/{0,1}` | “기다리면 성장·포탑·목표물 접근 기회를 잃을 수 있지만, 먼저 움직이는 이득도 복귀 손실과 아군이 버틸 수 있는 시간에 따라 달라진다.” |

O1은 후속이 AVAILABLE이라는 **가정**에서도 처리 완료를 확인하라고 요구한다. O2는 후속이 없어지면 재집결 준비로 바뀐다. 그 외 16개 상황 필드는 계속 unknown이다. X처럼 교전 실행 허용은 UNKNOWN에서 BLOCKED로 바뀌지만, F1은 이미 진입을 확정하지 않는 준비 문장이므로 그대로 남는다. 동일한 문장이라고 무조건 불일치로 보지 않았다. J3과 SUPPORT의 경우도 기본 행동이 조건부여서 태그/선택 ID가 바뀌고 일부 행동 본문이 유지된다.

## 반례 검토와 심각도 — 총점과 별도

원문 5쌍 외 추가 재현 결과는 `/workspace/gp23-artifacts/examples-v5-counterexamples.json`에 전체 입력·보고서·화면을 보존했다. 이는 아래 안전 경계 확인용이며 선정된 5개 사례를 좋은 결과로 바꾸는 재추첨이 아니다. 소스 수정 중 실행한 추가 probe이므로 별도 미봉인 관찰이다.

| 문제 ID / 반례 | 관찰·판정 | 심각도 / 상태 | 조치·지원 경계 |
|---|---|---|---|
| F-CE-01 누락/오래된 정보: MID 사례의 정글 정보를 REVIEW/stale/AWAY, source replay frame 123, 관측 시각 2026-10-20T10:00:00Z로 입력 | effective null, lane CHECK_WAVE 유지. 불확실성 원문 “상대 정글 정보 정보 오래됨”. 반대편이라는 오래된 기록으로 현재 푸시를 허가하지 않음 | P0 회귀 경계 / 이 probe에서 재현 안 됨 | 유효한 현재 관측으로 승격 금지 유지. 중복 “정보” 표현은 P3 문구 개선 후보 |
| F-CE-02 목표 충돌: Trundle TOP의 교전 기여·기술·지형·도달/후속 READY 가정, 적 딜러 DISRUPTABLE와 아군 딜러 COVERED → THREATENED만 변경 | goal DISRUPT_ENEMY_CARRY → PROTECT_ALLY. 무조건 깊게 진입하지 않고 아군 보호로 바뀜. 후속까지 UNAVAILABLE로 바꾸면 실행 BLOCKED | P1 회귀 경계 / 이 probe에서 재현 안 됨 | 탱커 공식 태그만으로 방해 진입을 권하지 않음. 조건이 없는 실제5샘플에서는 CONDITIONAL_ROLE·일반 원칙 범위를 유지 |
| F-CE-03 잘못된 일반화: MID DUEL과 외부 아군 후속 UNAVAILABLE, 자기·상대 기여 등 나머지 실행 조건 READY | DUEL_CONTRIBUTION, execution READY. “배운 수단과 내 대응·이탈 예산이 남는 가정에서 상대에게 닿는 공격을 비교하고, 끊으면 얻을 자원·복귀 이득도 함께 고른다.” 중단도 내 자원/상대 증원 기준 | 기존 CORE-P1-02 회귀 경계 / 이 probe에서 해소 확인 | 외부 아군이 반드시 함께 공격해야 한다는 이전 모순을 제거한 범위만 확인. 솔로 승리·처치 보장 없음 |
| F-P2-01 낮은 구체성: 5사례 모두 CONDITIONAL_ROLE 및 GENERAL_ONLY | F1 동일, 실제 대상별 현재 위협은 P처럼 UNKNOWN. 01/03/04 구체성 0, 02/05도 역할 원칙 1 | P2 / 지원 축소·보류 | 가짜 정밀도나 모든 챔피언 고유 전술을 더하지 않음. GP23-22는 정성 기여 게이트, GP23-23은 순위 미확인/수단 후보, GP23-26은 제한된 역할 원칙으로 명시 |
| F-P2-02 분량 중복: 5사례 운영 본문 첫 두 문단이 R 원문으로 완전히 동일 | 실제 원문은 그대로 보존. 중복 문장으로 분량을 채우므로 제거 필요 | P2 / 엔진 담당자가 이후 수정, 최종 봉인 재확인 대기 | 같은 이유와 기다림 비용을 두 번 쓰던 경로를 분리했다는 보고 및 core 회귀 13개 통과를 수신. 이 임시 원문을 손으로 고치지 않음 |

이번 5쌍과 추가 probe에서는 **새 P0/P1을 확인하지 않았다**. 이는 전체 출시의 P0/P1 부재 판정이 아니다. 첫 core 검토가 발견한 현재 위협 우선순위 오인(CORE-P1-01)은 이번 5쌍에서 `threat_priority.status:UNKNOWN`, P 문구, `CAPABILITY_CANDIDATE_NOT_CURRENT_PRIORITY`로 제한되는 것을 확인했다. 이전 DUEL 모순은 F-CE-03에서 직접 재실행했다. UI가 같은 제한을 실제로 노출하는지와 최종 코드의 별도 P0/P1 게이트는 root/브라우저 검증에서 판정한다.

## F39 결정과 다음 작업

더할 것: 최종 root 소스 커밋의 `--require-bound` 결과와 case hashes, 수정된 중복 문단을 같은 seed로 재확인한 기록.

뺄 것: 같은 운영 이유를 두 번 출력하는 경로. 출력 품질에 따른 사례 교체, 원문 수작업 보정, 총점에 의한 중대 결함 상쇄도 허용하지 않는다.

고칠 것: F-P2-02의 중복 제거를 최종 실제 엔진 출력에서 확인한다. 나머지 낮은 구체성은 현재 GENERAL_ONLY 지원으로 축소하고, 챔피언별 상황 자료가 없는 범위를 검증 완료로 올리지 않는다.

지금 하지 않을 것: 대상별 도달·남은 기술·정밀 합류 인원/ETA를 입력 없이 생성하거나, 정성 기여를 숫자 우세로 바꾸거나, 임의 배치 다섯 건을 모든 챔피언 고유 전술 검증으로 일반화하지 않는다. 실경기 N=0을 유지한다.

검증: `python -m unittest tests_pregame.test_gameplan_2plus3_examples -v` **4/4 PASS**. 입력 선정 재현, 각 쌍의 한 필드 변경, 실제 엔진 원문과 JSON 직렬화 결과 동일성, 반복 export 모든 파일 바이트 동일성, 수정/미추적 소스의 허위 커밋 봉인 차단을 검사했다. 이 테스트는 전술 정확도·브라우저 가시성·실경기 효과를 대신하지 않는다.

남은 절차: root의 안정 소스 커밋 → `node scripts/export_gameplan_2plus3.js --seed 20261025 --require-bound` → 최종 원문과 이 인용 비교 및 F-P2-02 재판정 → 정확한 소스·사례 해시 기록 → 증거/평가 문서 커밋. 소스 봉인 대기 때문에 F36 전체 완료를 미리 주장하지 않는다.

# 실행 대기열 v1.1 — 2026-10-11

Main branch feat/queue-gameplan-v1.1-2026-10-11; intake0337d915633f6ad5719f55de1252f05e06621c9b.
공통 claim work/main-execution-claim token main-20261011-queue-v11-root.
모든 작업은 사용자 사전 승인 안에서 진행, 유료 비용만 별도 승인.

| ID | 상태 | 소유자/수정 범위 | 의존성/완료 기준 |
|---|---|---|---|
| Q01 | DONE | q01_data / docs/queue/Q01_PRE_GAME_DATA.md, evidence/queue/q01 | 경기 전 데이터·쿨타임 정책 출처 목록 |
| Q02 | DONE | q02_audit / docs/queue/Q02_EXISTING_AUDIT.md, evidence/queue/q02 | 코드·승인 지식·합성·실행 연결 점검 |
| Q03 | DONE | Main / contracts/pregame*, coach_v1/pregame_contract.py | Q01,Q02; typed 실행/쿨타임 계약 확정 |
| Q04 | DONE | Main / coach_v1/pregame_store.py | Q01,Q03; 원본 픽창+10슬롯+내 역할+룬/주문 불변 저장 |
| Q05 | RUNNING | q05_content / knowledge_candidates, docs/queue/Q05_KNOWLEDGE_CANDIDATES.md, evidence/queue/q05* | 초기13 상세·173명 목록·추천10 확보; 나머지160명 원문 확장, 승인 안 함 |
| Q06 | DONE | q06_evaluator + Main / coach_v1/pregame_evaluator.py | Q03; 3값/반례/중단/충돌/이력; 독립 리뷰 수정 포함 |
| Q07 | DONE | Main / coach_v1/pregame_store.py, pregame_server.py | Q04,Q06; REVIEWED만 계획 생성·만료·revision |
| Q08 | DONE | q08_ui / web_r4/pregame* | Q07;7영역·입력/버전/출처/미확인 조회; 실제서버13/격리fixture17 검증 |
| Q09 | DONE | q09_verification / tests_pregame, scripts/verify_pregame.py, browser_pregame.py | Q07,Q08;5포지션 실제 브라우저104/104 + 기능49/의미12 PASS |
| Q10 | BLOCKED_EXTERNAL | q01_data / docs/queue/Q10*, evidence/queue/q10 | Q01; 실제 PC 수집 절차·원본 결과 양식 준비 DONE; 실제 수집 미실행 |
| Q11 | BLOCKED_EXTERNAL | Main | Q10 실제 원본 의존 |
| Q12 | BLOCKED_EXTERNAL | Main | Q11+본인 시점 영상 의존 |
| Q13 | BLOCKED_EXTERNAL | Main | Q09,Q12; 행동 전 근거 의존 |
| Q14 | BLOCKED_EXTERNAL | Main | Q13+독립 검토 의존 |

진척: DONE8/14; 종료 blocker0. 구현 검증을 코칭 정확도로 표현하지 않는다.
기존 검증 재사용: evidence/queue/intake.json 및 baseline PASS.

## 인수와 검증

공통 계약 Main627c77a와 phase 보강7224135를 확정한 뒤 소비 구현을 시작했다.
Q01/Q02/Q05는 각 work/q01-data, work/q02-audit, work/q05-knowledge 분리 브랜치로 수행했다.
Q06/Q08/Q09도 별도 worktree와 파일 범위에서 실행했고 Main이 커밋·범위·실행 증거를 인수했다.
현재 검증 코드9f9d9b9 + UI86a0df6; 수정 전 RED와 수정 후 GREEN은 evidence/queue에 보존한다.
독립 리뷰에서 쿨타임 충돌2건·복원 구조1건을 수정하고49개 기능 검사와 추가 admission5건을 통과했다.
기존 Frozen27·보호 파일·핵심 엔진·승인 코드·기존 웹은 바뀌지 않았다. 기존 브라우저124개 PASS 증거를 재사용한다.

## 외부 입력과 재개 조건

| 작업 | 필요한 입력 | 재개 조건 |
|---|---|---|
| Q10 | 본인 Windows 게임 PC의 공식 수집 원본·receipt·환경 진술·필드 제공 여부 | Q10_GAME_PC_CAPTURE.md의 개인 자료 묶음과 해시가 실제 존재 |
| Q11 | Q10 실제 단계/모드별 원본 샘플 | 원본 제공 범위·누락·정책이 확인된 뒤 출처 연결 변환기 구현 |
| Q12 | 같은 경기 본인 시점 영상·수집 시각/게임 시각 연결 | Q11 관측과 영상의 기준점으로 오차/누락 계산 가능 |
| Q13 | Q09 통과 + Q12 정렬 자료 | 당시 관측만으로 계획 적용·대안 복기; 사후 정보 소급 금지 |
| Q14 | Q13 실제 사례 + 독립 참조/검토 자료 | 표본·실패·방법을 분리하여 성능 평가 가능 |

승인 지식·실제 경기 패치가 없다는 사실은 준비 흐름의 중단 이유가 아니다.
웹에서 사용자가 출처·범위를 검토하면 새 지식 버전으로 생성한다. 합성 연결 검증은 실제 승인이 아니다.
유료 서비스 사용0; BLOCKED_PAYMENT0. 실제 경기 표본0, 정확도 미산정.

단계 A 최종 증거: evidence/queue/q09-final.json;25출처 해시 Main과 일치.
추가 화면 경합 발견은4d054cd에서 수정, 독립 브라우저3건 재검토 PASS.
병합 전 CI는 기존 MVP2개 + 새 pregame1개를 실제 GitHub에서 확인한다.

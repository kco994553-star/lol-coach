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
| Q05 | VERIFYING | q05_content / knowledge_candidates, docs/queue/Q05_KNOWLEDGE_CANDIDATES.md, evidence/queue/q05 | 출처·패치·반례 후보/추천10, 승인 안 함 |
| Q06 | DONE | evaluator agent 예정 / coach_v1/pregame_evaluator.py | Q03; 3값/반례/중단/충돌/이력 |
| Q07 | DONE | Main / coach_v1/pregame_store.py, pregame_server.py | Q04,Q06; REVIEWED만 계획 생성·만료·revision |
| Q08 | RUNNING | UI agent 예정 / web_r4/pregame* | Q07;7영역·입력/버전/출처/미확인 조회 |
| Q09 | RUNNING | verifier agent 예정 / tests_pregame, scripts/verify_pregame.py | Q07,Q08;5포지션 실제 브라우저 |
| Q10 | BLOCKED_EXTERNAL | collector-prep agent 예정 / docs/queue/Q10*, scripts/* | Q01; 실제 PC 없으면 절차+BLOCKED_EXTERNAL |
| Q11 | BLOCKED_EXTERNAL | Main | Q10 실제 원본 의존 |
| Q12 | BLOCKED_EXTERNAL | Main | Q11+본인 시점 영상 의존 |
| Q13 | BLOCKED_EXTERNAL | Main | Q09,Q12; 행동 전 근거 의존 |
| Q14 | BLOCKED_EXTERNAL | Main | Q13+독립 검토 의존 |

진척: DONE6/14; 종료 blocker0. 구현 검증을 코칭 정확도로 표현하지 않는다.
기존 검증 재사용: evidence/queue/intake.json 및 baseline PASS.

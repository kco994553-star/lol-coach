# CURRENT HANDOFF — LoL Coach

2026-10-04: Design v1.0 동결 후 R3 근거·상태·복기 기반 구현.
설계 원본은 docs/HANDOFF.md 및 FREEZE_MANIFEST.json에 당시 상태 그대로 유지한다.
현재 구현 설명: docs/R3_IMPLEMENTATION.md. 다음 작업자는 이 파일부터 읽는다.

## 현재 상태
- R3: 구현·합성 검증 완료. 제품 활성화 상태 SYNTHETIC_ONLY.
- 새 namespace coach_v1. frozen 파일과 legacy/backend 13개 원본 변경 없음.
- 합성 JSON → 출처/시점 상태 → 후보 비교 → 복기 JSON 실행 가능.
- 실제 경기 입력 adapter, 경기 종료 확인, 자동 인식, API/DB/UI는 미구현.
- 최종 검증은 evidence/r3의 실행 증거. 과거 R1 32/32 재현 주장 없음.

## 다음 자동 구현 범위
실제 표본 유무를 먼저 확인한다. 없으면 계약에 맞는 합성 개발은 계속 가능하나 real-data gate는 해제하지 않는다.
API/DB/job/UI를 붙일 경우 TEST 모드는 개발 인터페이스로 격리하며 실제 플레이어용 기능으로 노출하지 않는다.
실제 adapter는 sample semantics/누락/시점/종료 근거 검증 후 도입.
새 게임 수치 정책·유료 AI·실시간 자동 기능·Freeze 변경은 D3.

## 실행
    python3 scripts/verify_r3.py
    python3 -m coach_v1 examples/r3/insufficient-evidence.json --synthetic

첫 명령은 과거 검증을 임시 복사본에서 실행해 기존 evidence를 덮어쓰지 않는다.

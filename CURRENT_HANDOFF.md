# CURRENT HANDOFF — LoL Coach

2026-10-04: Design v1.0 동결 유지. R3 코어에 R4 로컬 합성 복기 워크벤치 구현.
현재 설명·실행 명령: docs/R4_IMPLEMENTATION.md.
설계 원본과 동결 시점 상태는 docs/HANDOFF.md 및 FREEZE_MANIFEST.json 그대로 보존한다.

- 구현: SQLite 입력 버전/결과 저장, 비동기 작업/취소/재시작, 인증 API, 반응형 웹, 재열람/내려받기/삭제.
- 격리된 실제 원본 1회 수집 도구 준비. 실제 연결/표본 검증은 미실행.
- 검증: evidence/r4. python3 scripts/verify_r4.py 및 scripts/browser_r4.py.
- R3/과거 증거는 보존. 최초 실패와 수정은 evidence/r4/HISTORY.md.
- 제품 상태 SYNTHETIC_ONLY. 실제 경기 adapter, 종료 확인, 코칭 정확도, 공개 서비스는 미완료.
- 다음 의존성: 실제 LoL 실행 PC 또는 실제 원본 표본. 제공되면 출처/시점/관점/누락/종료 검증 후 adapter 구현.
- 유료 지출 등 실제 사용자 권한이 필요한 행동은 요청한다. 일반 구현·수정·재검증은 자율 진행한다.

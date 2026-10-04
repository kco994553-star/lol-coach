# LoL Coach Design v1.0 — Reconstructed Baseline(재구성 기준본)

개인용 웹 코치의 설계 계약. 2026-10-04 사용자가 원본 검색 후 없으면 스스로 재구성하도록 승인했다.
이는 과거 R0/R1 Git 이력 복구나 과거 32/32 테스트 재현 인증이 아니다.
최종 판정은 `FREEZE_MANIFEST.json`, 감사는 `docs/AUDIT.md`, 실행 결과는 `evidence/validation.json` 참조.

## 읽는 순서
1. `docs/PROVENANCE.md`: 확보한 원본, 미확보 이력, 새 기준의 권한.
2. `docs/DESIGN.md`: 제품·상태·판단·지식·어댑터·화면·API·저장·출시 계약.
3. `contracts/requirements.json`: 요구사항과 계약·검증 추적표.
4. `contracts/scenarios.json`: 대표 장면과 기대 동작; 실경기 테스트 결과가 아님.
5. `docs/MIGRATION.md`: 기존 코어와 새 설계의 차이 및 구현 전환 조건.
6. `docs/HANDOFF.md`: 다음 단계와 보호 경계.

## 재검증
Python 3.11 이상, pydantic 2.13.5에서 검증했다. 다른 환경은 실행 결과에 버전 기록.
`python3 -m validation` (패키지 루트에서 실행).
표준 라이브러리 기반 문서·해시 검사와 보존 코어 동작 검사를 실행한다.
새 v1.0 판단 엔진의 구현/실경기 검증은 아직 없다.
기존 backend 13개 파일은 `legacy/backend/`에 원문 그대로 보존한다.

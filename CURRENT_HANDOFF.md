# CURRENT HANDOFF — LoL Coach

2026-10-04 KST. Design v1.0 동결 유지. R6로 기존 웹에 자료·복기 노트 통합.
현재 설명: docs/R6_IMPLEMENTATION.md. 서버 실행: docs/R4_IMPLEMENTATION.md. 자료 수집: docs/R5_DATA_ACCESS.md.

- 기존 합성 분석 흐름 유지. 추가 메뉴에서 공식 JSON 진단·공개 영상 후보·주제 필터 제공.
- 후보별 당시 근거/의도/다른 선택/사후 결과 노트 저장·재열람·내려받기·삭제 구현.
- 별도 research SQLite로 기존 DB schema 보존. 노트 immutable revision+CAS 충돌 차단.
- 원본 JSON/지원 자막을 로컬 처리하되 서버에는 진단/색인만 저장. 노트는 사용자 작성으로 남음.
- 모든 실제 자료/노트 자동 코칭 승격 차단. 제품 SYNTHETIC_ONLY 유지.
- 현재 evidence/r6. 이전 evidence/r3,r4,r5 및 동결 파일 유지.
- 남은 외부 의존성: 실제 프레임 관찰과 LoL 실행 PC. 실제 코칭 정확도·자동 픽 감지·실시간 기능 미완료.
- 유료 결제·계정정보 등 실제 권한 필요 지점 외 구현·수정·검증은 자율 진행.

# CURRENT HANDOFF — LoL Coach

2026-10-04 KST. Design v1.0 동결, R3 합성 코어, R4 로컬 합성 웹 유지. R5 데이터 접근 대안 구현.
현재 실행/제한: docs/R5_DATA_ACCESS.md. 웹 실행: docs/R4_IMPLEMENTATION.md.

- 공식 JSON 표본 실제 수신·해시·진단 완료. DOCUMENTATION_SAMPLE이며 실제 경기 표본 아님.
- 공개 YouTube 자동자막 1,230구간 확보, 주제별 후보33개 색인·HTML 보고서. 화면 미검증.
- 인증서 자동 준비·로컬 수집·오류 진단 구현. collect_windows.cmd 또는 scripts/collect_local.py.
- 로컬 HTTPS 전송은 가짜 서버로 검증. 실제 LoL endpoint는 현 환경에서 연결 불가.
- 상태 SYNTHETIC_ONLY 유지. 수집 자료는 코칭 엔진으로 자동 승격하지 않음.
- evidence/r5에 실패/재시도/공개 자료/새 검증. 이전 동결·R3·R4 파일과 증거 유지.
- 다음 의존성: 영상 화면 기반 검증은 재생 가능한 프레임, 본인 경기 수집 검증은 LoL 실행 PC. 공개 자료 개발과 분리.
- 유료 결제·계정정보 등 실제 사용자 권한이 필요한 지점 외에는 구현·수정·검증을 자율 진행한다.

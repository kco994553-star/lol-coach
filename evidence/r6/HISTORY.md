# R6 실행·수정 이력

2026-10-04 KST. 과거 evidence/r3,r4,r5는 덮어쓰지 않는다.

- 자료 저장 backend는 독립 작업자 구현. SQLite/동시 수정/이력/연쇄 삭제/스키마 검증9개 통과.
- 표적 API 검사에서 기존 TestCase를 직접 import해 unittest가 기존8개도 중복 발견했다. module import로 수정해 중복 제거. 처음22개 PASS를 신규22개로 계산하지 않는다.
- 화면 전환 읽기 중 편집을 막는 처리 추가 과정의 문자열 수정이 rAdd에도 try를 넣어 JavaScript SyntaxError 발생. static check로 발견, finally 보완 후 통과.
- 최초 브라우저 실행은 위 JS 구문 오류 때문에 자료 버튼 표시 전 시간 초과. 수정 후 전 흐름 재실행 PASS.
- 모바일390px screenshot 직접 확인: 한글 표시 정상, 가로 넘침 없음.
- 실제 경기·영상 프레임 검증은 실행하지 않았다. 합성/공개 자막/전송 테스트와 구분한다.

- 독립 Challenger가 A 파일 읽기 중 B를 선택하면 A가 먼저 처리되고 B가 폐기되는 경합1건을 Node VM으로 재현. 별도 단조 증가 파일 읽기 토큰+파일 동일성 검사 추가. 기존 화면 epoch 검사 유지. 표적 재실행 결과는 ui-file-race.json에 별도 보존.

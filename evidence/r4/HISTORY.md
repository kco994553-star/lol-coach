# R4 검증 이력

2026-10-04. 실패 기록은 최종 PASS로 삭제하지 않는다.

1. 독립 Challenger가 Node VM으로 이전 삭제 응답/이전 파일 읽기 완료가 새 화면의 미저장 편집을 지우는 반례 2건 발견. epoch/대상 ID/파일 선택 guard 수정. 동일 반례 2/2 통과. ui-races.json에 구분 기록.
2. 브라우저 기본 실행 파일 부재. 자동 다운로드는 유효하지 않은 archive로 실패. 기존 /tmp/chromium 사용으로 복구.
3. 별도 실행 세션의 loopback 접근 실패 및 같은 DB lock 확인. 테스트 서버와 브라우저를 동일 실행 흐름에서 격리 임시 DB로 실행하도록 수정.
4. 브라우저 테스트의 CSS :hidden 선택자 오류. Playwright state:hidden API로 수정. 제품 분석/저장/재열람까지는 이 실패 전에 이미 실행됨. 전체 재실행 통과.
5. 최초 통합 63개 중 대형 요청 테스트 1개 BrokenPipeError. 서버가 Content-Length로 즉시 413 후 연결 종료하므로 업로드와 종료가 경합. 테스트가 oversized header만 보내 거부 응답을 직접 확인하도록 수정. 통합 재실행 63/63, 보호 회귀9/9 통과. 실패 JSON/log도 유지.
6. 모바일 screenshot의 한글 글꼴 누락 발견. 시스템 패키지 설치는 권한 제한으로 실패. 공식 Google Fonts Noto Sans KR를 사용자 글꼴 폴더에 설치해 렌더링 재확인. 앱은 OS 한국어 글꼴을 사용하며 원격 폰트 요청 없음.

원본 수집의 JSON 보존/해시/미승격/리다이렉트 거부는 단위검사. 실제 LoL TLS 연결은 실행하지 않았으며 실제 경기 PASS로 표시하지 않는다.

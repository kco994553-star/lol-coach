# MVP 저장 응답과 편집 상태 분리

2026-10-05. Risk DEEP. 사용자 Autonomous Execution Authority v1.0 범위의 버그 수정이다.
Frozen27, Core Contract, 엔진, 기존 Fixture/Expected Result는 변경하지 않는다.

## 재현과 최소 변경

서버 저장 버전1에서 PUT를 보낸 뒤 응답이 오기 전에 편집하면, 서버는 버전2를
커밋하지만 기존 화면은 응답을 버려 버전1에 남았다. 다음 저장은 expected_revision=1을
다시 보내 409가 됐다. 같은 사례를 재열람하면 저장되지 않은 입력도 확인 없이 사라졌다.
`evidence/mvp/save-race-before.json`은 실제 기존 JS를 실행한 최초3/7 실패를 보존한다.
별도 검증자도 서버2/화면1/PUT[1,1] 및 확인 없는 재열람을 독립 재현했다.

`web_r4/app.js`에서 선택한 사례의 생애(selectionEpoch)와 입력 편집(epoch)을 분리했다.
같은 선택에 대한 저장 응답은 서버의 새 ID/버전을 반영한다. 응답 도중 새로 쓴 문자는
그대로 유지하고 추가 저장 전까지 분석은 차단한다. 선택을 바꾸거나 초기화한 뒤의
옛 응답은 계속 무시한다. 재열람/예제/파일 불러오기에는 기존 미저장 입력 확인을 둔다.
다른 변경 파일의 응답, 삭제, 실제자료/합성자료 경계는 이 수정의 대상이 아니다.

## 대안과 검증

입력 자체를 저장 동안 잠그는 대안은 개인 사용 시 입력을 중단시킨다.
편집 epoch만으로 저장 응답을 무시하는 기존 방식은 이미 커밋된 버전을 잃는다.
선택 생애와 편집을 분리하면 서버 버전과 로컬 초안을 함께 보존할 수 있다.

최초 source SHA256 `c3986df5508c19dead28085bfe4a479c3a87f74dbf6f13cdf6bd2547869eab18`,
수정 source SHA256 `2d644c17d041210f5a7691278a32911401944613bc7bdcb8d4f95901fbcd9393`.
수정 후 `evidence/mvp/save-race-after.json`은7/7 PASS다. Node VM 검증과 실제 브라우저
검증은 별개다. 실제 실행 결과와 소스 바인딩은 신규 MVP verification/browser receipt에
기록하며, 설치/실행 실패도 삭제하지 않는다.

원래 `scripts/verify_r7.py`는 이전 앱의 정확한 바이트를 동결해 두었다. 이 verifier와
옛 baseline을 수정하지 않는다. 현재 앱에서 그 역사적 identity gate는 FAIL이다.
`scripts/verify_mvp.py`가 허용된 앱 수정 및 별도 최초/수정 receipt를 검증하고,
Frozen27, 나머지 옛 바이트, 기존111 tests와 protected9를 그대로 재검증한다.
이는 Invariant/Expected 변경이나 옛 R7 PASS의 현재 승격이 아니다.

Rollback은 부모 main `30c36de871de4ab7ac190d0f3f876f577994698a`의 앱 한 파일을
새 커밋으로 복구하는 방식이다. 과거 기록이나 branch history를 지우지 않는다.

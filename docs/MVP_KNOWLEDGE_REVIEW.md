# 사용자 지식 결정 계약 v1.1 — 2026-10-09

사용자 결정으로 PRE_GAME 픽 단계 게임플랜을 최우선 목표로 전환한다.
대상은 원딜 유나라·애쉬·카이사·케이틀린이다. PRE_GAME은 Player 영상 없이
진행하므로 기존 PARKED_EXTERNAL을 이 작업의 실행 차단 조건에서 해제한다.
POST_GAME 실경기 복기는 후순위이며 기존 실제 경기 증거를 늘렸다고 주장하지 않는다.

이번 납품은 지식 후보의 사용자 승인·거절 흐름이다. 게임플랜 생성은 다음 작업이다.
픽창 기록과 REVIEWED 지식으로만 생성하며 근거 없는 칸은 “미확인”,
AI 자유 생성 문장·수치는 금지한다. 이번 변경은 그 생성 기능을 활성화하지 않는다.

## 승인된 변경과 보존 경계

2026-10-09 사용자 결정 2가 D3 권한이다. 동결 v1.0 원문과
FREEZE_MANIFEST.json의 27개 payload를 보존하고 아래 제한된 v1.1 추가 계약을
contracts/amendments/2026-10-09-knowledge-review.json으로 연결한다.
동결 설계 KNOWLEDGE/API/PERSISTENCE의 사용자 결정 흐름만 구체화한다.
“AI 다수 동의만으로 REVIEWED 승격 금지”와 출처·버전 보존 원칙을 유지한다.
기존 schema2 SQL, EXPLORATORY proposal.v1 저장본, legacy 엔진은 그대로 읽힌다.
새 knowledge-decision.v1 저장본만 REVIEWED/REJECTED를 허용한다.
백업의 순수 검증도 같은 새 계약을 사용한다. SQL 마이그레이션은 없다.

## 사용자 흐름

저장된 특정 버전을 웹에서 열고 “조회 버전 승인” 또는 “조회 버전 거절”을 누른다.
네이티브 확인창에 조회 버전을 표시한다. 취소하면 요청과 저장이 없다.
승인은 patch_range 및 applicability의 champion/role/matchup/level/context가
모두 명시적 문자열이어야 한다. 빈 값, 공백, UNKNOWN(대소문자 무관), 미확인은
거부한다. 사용자는 구체적 적용 범위나 명시적 무제한 조건을 직접 입력한다.
패치 문법·실제 패치 존재·주장의 정확도를 AI가 추정하거나 인증하지 않는다.
거절은 기존 UNKNOWN 범위도 보존할 수 있다. 후보의 주장·작성자·근거·출처를
바꿨다면 먼저 EXPLORATORY 새 버전으로 저장해야 한다.

POST /dev/v1/knowledge/proposals/{rule_id}/decisions:
selected_version, expected_version, decision, patch_range, applicability.
selected_version은 조회한 정확한 과거/현재 버전이다. expected_version은
조회 시점의 최신 버전이며 최신이 바뀌면 409 REVISION_CONFLICT로 거부한다.
결정 저장본의 supersedes는 최신 버전, review_decision.selected_version은
선택한 버전이다. 두 식별자는 의도적으로 다를 수 있다.
선택한 버전의 저장 JSON 해시와 source_refs의 자료/노트 해시를 그대로 보존한다.
선택한 버전의 내용 중 패치·적용 조건 외에는 바꿀 수 없다.
coaching_enabled=false를 유지하며 REVIEWED는 실경기 코칭 성능 인증이 아니다.
후속 편집은 다시 EXPLORATORY이며 이전 결정은 덮어쓰지 않는다.
기존 출처 삭제와 전체 후보 삭제의 명시적 연쇄 삭제 정책은 그대로 적용한다.

## 사용자 조작 경계와 검증 한계

일반 propose API/스토어, AI actor 입력, 자동·일반 HTTP 클라이언트는 승격할
권한이 없다. 서버의 전용 경로는 인증·Host/Origin 검증과 브라우저 Fetch Metadata
same-origin/mode same-origin/dest empty를 요구한다. 그 경로만 스토어의 내부
권한 객체를 전달한다. 클라이언트 JSON으로 actor나 coaching_enabled를 설정할 수 없다.
웹 핸들러는 closure 안에서 trusted click 및 활성 사용자 제스처를 요구한다.
DOM .click()/dispatchEvent 및 전역 함수 호출로 결정하는 경로는 제공하지 않는다.

이는 신뢰하는 로컬 웹 화면과 서버 코드 안에서의 실행 경계다. 인증키를 가진
공격자가 HTTP 헤더를 위조하거나 Python 내부 권한 객체를 가져오거나 브라우저를
직접 제어하는 경우까지 인간임을 암호학적으로 증명하지는 않는다.
실제 브라우저 테스트는 Playwright 입력으로 사용자 버튼/확인 흐름을 검증한다.
“AI나 자동화가 브라우저 자체를 제어해도 절대 승격할 수 없다”는 증명으로
그 결과를 해석하지 않는다. 그 요구에는 별도 사용자 인증/물리적 확인 계약이 필요하다.

## 필수 검증

기존 회귀와 브라우저 검사를 보존한다. 새 실제 HTTP/SQLite 검사와 브라우저
검사는 승인·거절, 과거 버전 선택, 불변 이력/해시, 빈 조건, CAS/동시 저장,
인증/자동 경로 차단, 스크립트 클릭 차단, 네이티브 취소, 재시작/백업 복구를 확인한다.
실패 실행과 수정 전 소스는 영수증에 보존하며 실제 경기 근거로 집계하지 않는다.

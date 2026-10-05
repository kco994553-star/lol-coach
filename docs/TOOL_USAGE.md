# 도구 사용 기록

2026-10-05 KST. GitHub가 코드·계약·검증 근거·인수 기록의 기준이다.
연결 상태는 다른 서비스의 프로젝트·DB·디자인·배포가 준비됐다는 근거가 아니다.

| 실제 사용 도구 | 목적 / 대상 | 범위 | 결과와 근거 |
| --- | --- | --- | --- |
| GitHub | 최신 main·공통 owner·PR·Actions 인수, 검증된 트리 게시 | Read-only(읽기 전용) 인수 후 Write(쓰기): 비강제 ref, PR, 조건 충족 병합 | [PR6](https://github.com/kco994553-star/lol-coach/pull/6), 트리 86cccef58af92d2ec5f88c25c97fcc64c1711960; 실제 CI 최초 실패 knowledge-ci-37268245767-failure.json 보존 |
| Superpowers | 기존 Knowledge 구현의 Review(검토), Verification(검증), CI 실패의 Debugging(디버깅); 다음 노트 복구의 Bounded planning(좁은 계획) | 절차와 읽기 전용 분석; 실제 저장소 코드/검사는 별도 기록 | 기존 설계를 재시작하지 않음. 독립 SQLite/Node 검토와 로컬 필수 회귀 PASS. 실제 브라우저 최초 실패는 아래 별도 근거이며 완료 선언하지 않음 |
| Browser Verification(브라우저 검증), 기존 GitHub Actions Chrome | 실제 격리 개발 서버·HTTP·SQLite에서 업로드/선택/저장/코칭 카드/390px/오류/다운로드 검사 | 임시 합성 자료만 Write(쓰기); 개인 실제 자료/서비스 배포 없음 | [실행37268245767](https://github.com/kco994553-star/lol-coach/actions/runs/37268245767): 서버 회귀 PASS, 브라우저 다운로드 검사 FAIL. 실제 Coach N0, accuracy=null |

Context7·MagicPath·Figma·Linear·Supabase·Vercel은 이 기록에서 사용하지 않았다.
외부 프로젝트·이슈·디자인·배포 생성 없음. 신규 의존성·유료 지출 없음.
현재 구현은 로컬 진단/합성 워크플로와 EXPLORATORY(탐색) 후보 저장이다.
실제 경기 검증과 도구 또는 디자인 완성을 같은 상태로 보고하지 않는다.

새 도구가 필요한 경우 실제 저장소 의존성과 대상부터 확인하고, 목적·읽기/쓰기
범위·실제 결과·근거·정확한 링크를 추가한다. 이후 결과는 기존 기록을 삭제하지
않고 CURRENT_HANDOFF 및 additive(이력 보존 추가) 증거에 연결한다.


후속 실제 결과: PR6 병합594ef3c, PR37268750816 및 postmerge(병합 후)37268897569
SUCCESS(성공), 실제 Chrome79/79 및176 입력 해시 일치. 최초 실패는 그대로 보존.
노트 복구의 native textarea(실제 다중행 입력창) 줄 끝 동작을 확인하기 위해
[공식 HTML Standard](https://html.spec.whatwg.org/multipage/form-elements.html#the-textarea-element)
API value 항목을 Read-only(읽기 전용) 조회했다(2026-10-05, 문서 갱신2026-10-04).
줄바꿈 LF 정규화는 원래 이력 바이트와 구분해 실제 브라우저에서 검사한다.
문서 조회는 구현 완료 또는 검사 통과로 계산하지 않는다. 외부 대상 생성 없음.


2026-10-05 후속 실제 결과: [PR7](https://github.com/kco994553-star/lol-coach/pull/7)
병합0f2b333e, [PR 검사37271933712](https://github.com/kco994553-star/lol-coach/actions/runs/37271933712)
및 [병합 후37272079828](https://github.com/kco994553-star/lol-coach/actions/runs/37272079828)
SUCCESS(성공), 실제 Chrome89/89와194 입력 해시 일치. 최초 브라우저 실패와
완료 시점 검사 수리 이력은 그대로 보존했다. 실제 코칭 N은 증가하지 않았다.

수동 픽창 기록에서는 Superpowers writing-plans(계획 기록), executing-plans
(기존 계획 실행), TDD(검사 먼저 작성), independent review(독립 검토),
verification(검증) 중 현재 필요한 절차만 적용했다. 대상은 기존 Frozen
TEAM_DRAFT 입력 수집과 개인 DB/HTTP/UI/백업이다. Read-only(읽기 전용)
최신 GitHub/공통 소유권 인수 뒤 Write(쓰기) 범위는 이 저장소의 코드·검사·
이력 보존 근거다. 동일 UNKNOWN 행 손실의 실제 Node 반례를 수리 중이며,
새 실제 Chrome 결과는 완료된 Actions 근거로만 추가한다. 서비스 프로젝트·
DB 서비스·디자인·배포·의존성·유료 지출을 만들지 않았다.

# 출처·권한·역사 보존

## 확인된 원본
- Library `/롤/lol-coach-v0.1-core.zip`, libfile_27204ae0e98c8191a301ca3eabd8e661, 2026-09-27 생성.
- ZIP: README 1개, backend Python 13개. README는 Fixture Runner 미포함을 명시.
- 원본 ZIP 및 파일별 SHA-256은 `evidence/source_manifest.json`에 기록한다.
- 2026-10-04 GitHub kco994553-star/lol-coach: 메타데이터 size=0, branches=[], contents 404 'This repository is empty.', commits/refs 409 'Git Repository is empty.'. 이는 당시 확인 결과다.
- Library 제목 검색 LoL/coach/롤/R1 및 /롤 폴더 전체 목록 확인: 코어 ZIP과 README만 발견. 검색으로 모든 외부 저장 위치의 부재를 증명하지 않는다.

## 역사적 보고 / 미확보
R0/R1 같은 브랜치 commit/push, 32/32 PASS, 13개 core 해시 보호는 과거 대화 보고다.
그 commit SHA, Git history, 테스트 원본, 당시 해시 목록은 확보하지 못했다.
GF-001/002 의미의 과거 요약은 신규 관찰 사례 설계에 참고했으나 기존 fixture 원문으로 표시하지 않는다.
DA-001~028, WF-REPLAY-001/002, SYS-001~004, 18 invariants, 7-Pass 원문 역시 미확보.
이 번호들은 예약된 역사적 ID이며 새 내용으로 채우거나 통과 처리하지 않는다.
새 요구는 REC-REQ-*, 새 사례는 REC-SC-*, 새 감사는 REC-PASS-*를 사용한다.

## 현재 승인
사용자: '라이브러리에서 찾아보고 원본이 없으면 스스로 만들고 진행시켜'.
이를 누락 설계·검증 패키지 재구성 권한으로 적용한다. 역사적 성공을 새로 꾸미는 권한이 아니다.
원본 코어는 불변 보관; 현재 설계는 새 기준본으로 명시한다.
기존 R0/R1 동일성 주장은 UNKNOWN, 새 패키지 무결성 및 현재 실행 결과만 FRESH 증거다.

## Freeze 의미
Design Freeze는 명시 범위의 계약·실패 처리·추적 가능성 확정이다.
실제 입력 정확도, 경기 코칭 효과, 운영·배포·Riot 승인, 제품 구현 완료의 인증이 아니다.
외부 데이터가 없어도 동작을 명확히 정의한다: 결손 근거를 보존하고 평가를 제한/보류한다.
출시 차단 조건은 설계에서 삭제하지 않고 `docs/DESIGN.md`의 RELEASE 절에 고정한다.
기존 설계와의 역사적 동일성이 아니라 승인된 재구성 기준의 완결성을 감사한다.

## 외부 정책 근거
Riot 공식 문서 https://developer.riotgames.com/docs/lol — 2026-10-04 확인.
첫 `/docs/lol/` 직접 열기는 404, 이후 공식 도메인 검색으로 본문 확인했다.
정책 요약: 실시간 비공개 경기 정보 및 적 궁극기 추적, 결정을 지시하는 사용례는 제한된다.
LCU는 제3자용 공식 지원 서비스가 아니며, 실제 제품 사용은 해당 접근 방법과 정책 검토가 필요하다.
개인용이라는 이유로 정책 예외를 가정하지 않는다. 공개/운영 전 최신 정책·등록 요건 재확인.

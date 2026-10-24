# Gameplan backend contract Implementation Plan

**Goal:** 기존 코칭의 고정 출력과 내부 판단을 구분하고 재현·패치 추적 기반을 구현한다.
**Architecture:** 기존 planboard의 순수 함수를 확장한다. presentation은 delivery를 읽되 구버전 보고서는 기존 경로를 유지한다.
**Tech Stack:** JavaScript UMD, Python unittest + Node.
**Spec:** docs/gameplan-content/backend-design-v1.md

## Constraints and review focus
새 전술·스코어·API·화면 항목 없음. 잘못된 규칙과 미확인은 구분. 정확히 세 단계/다섯 행동. 내부 근거가 화면으로 새어나오지 않음. 부분 추적을 전체로 표시하지 않음. 사용자 결정 자료 보존.

## Task 1: 조건·출력·추적 계약
- [x] tests_pregame/test_gameplan_backend.py에서 evaluateCondition, buildDelivery, dependencyTree, affectedOutputs의 실패 검사.
- [x] loading-planboard.js에 순수 함수 구현, evaluate 최종 반환에 delivery와 internal_dependencies 연결, 기본 방향 사실 존재 조건에 evaluateCondition 사용.
- [x] loading-presentation.js에서 delivery의 headline/actions/paragraphs/details 우선 사용.
- [x] 실제 생성 5개 역할·미지원 조합·가정 초기화·레거시 보고서·잘못된 개수 검사.
- [x] 전체 관련 tests_pregame discovery 실행, 실패가 있으면 기존 기준에서도 재현해 분리.
- [x] 새 테스트를 기존 source-bound 검증 경로에 등록하고 source 보호 검증.
- [x] 독립 리뷰, 결과 문서, 커밋 및 파일 전달.

## Execution ledger
인수: PR130 OPEN/DRAFT f514ab1; canonical writer_active=false. 기존 clean 작업 디렉터리에서 새 전용 브랜치 생성.
선택: 전술 확대보다 고정 출력 경계와 부분 영향 추적부터 구현. 전체 규칙 엔진 완성은 후속으로 남긴다.

결과: 관련57 PASS; 전체794 중 기존3 실패(main d00c255 동일 재현). 독립 리뷰2건 RED→GREEN 수정. 브라우저/배포 미실행. 전체 규칙 엔진 후속.


# Scoped conditions Implementation Plan

**Goal:** 조건의 대상·단계·시점·출처를 보존하고 기본 방향 적용/제외를 추적한다.
**Spec:** docs/gameplan-content/backend-design-v1.md 및 게임플랜 후속 합의.
**Architecture:** 기존 UMD 순수 함수에 scoped condition 및 rule evaluation 추가. 별도 화면이나 전술 점수 없음.
**Tech Stack:** JavaScript, unittest/Node.

## Constraints / review focus
- 같은 입력은 같은 기록. 실제 관측을 생성하지 않음.
- 대상·단계·시점 불일치, 출처 누락은 UNKNOWN. 잘못된 자료는 오류.
- 제외 조건 미확인은 적용 확정 불가. 제외 MET는 EXCLUDED.
- 기존 delivery 유지. 지원 불가와 잘못된 데이터 구별.
- 조건 배열 구멍·중복 ID·입력 변형 검사.

## Tasks
- [x] scoped condition와 rule trace 실패 검사 후 구현.
- [x] 실제 기본 방향 자료 적용 기록 연결 및 출력 동일성 검사.
- [x] 영향 검사와 전체 suite, 독립 리뷰, 문서/PR/노션 갱신.

## Ruling
사용자가 승인한 후속 구현을 현재 격리된 전용 브랜치에서 이어간다. 최초 연결은 기본 방향의 적용 자격 검사이며 전술 후보 선택은 후속이다. 시점은 호출자가 주는 snapshot ID이며 실제 시간 추정이나 자동 최신성 판정이 아니다.

실행 기록: 최초 신규 2개 실패 확인 후 구현. 리뷰의 패치 경계·원본 범위 기록 문제 1개 복합 테스트 RED→GREEN. 관련 56 PASS. 전체 799 중 기존 PC 코칭 2개/v2.3 binding 1개 실패. 테스트 수집 부작용 파일은 scratch로 이동하고 기존 자료 복원. 기존/신규 delivery 2개 조합×5개 사용자 포지션 10건 동일.

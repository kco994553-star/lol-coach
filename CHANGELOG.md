# 변경 이력
기능계층 버전, 게임 패치 버전, 출력 계약 버전, 배포 커밋은 서로 다르다.

## 2026-10-25 — 게임플랜 2+3 설계 보충
- 2개 기본 방향 + 3개 단계 구조, 라인관리와 교전 판단 기준을 명문화.
- 교전·한타 범위, 정보 불확실성, 태그 파생 원칙과 44개 신규 실행 대기열 추가.
- 기능계층 v2.0 및 기존 160행 유지. 현재 런타임 출력 계약 버전·게임 패치·배포는 변경하지 않음.
- ARCHITECTURE / SOURCE_REGISTRY / DECISION_LOG / DEPENDENCY_MAP / RELEASE_CHECKLIST 진입 문서 추가.
- 신규 기능 구현·실경기 정확성·배포 완료를 의미하지 않음.

기존 제품 변경 근거는 docs/gameplan-content/frontend-v2-implementation.md와 Git 이력에서 확인한다.
향후 항목은 패치/출력 계약 before→after, 호환성, 변경 커밋, 검사와 배포 상태를 분리 기록한다.

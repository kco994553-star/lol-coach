# 아키텍처 책임과 경계
2026-10-25. 현행 구조의 진입점과 2+3 구현 목표를 구분한다. 이 문서는 신규 구현 완료 증거가 아니다.

## 현행 확인 경로
- 기능계층: contracts/information-architecture-v1.md (v2.0, 160행).
- 백엔드 설계: docs/gameplan-content/backend-design-v1.md.
- 챔피언 기본 정보: docs/gameplan-content/champion-baseline-backend-v1.md.
- 프론트 상태: docs/gameplan-content/frontend-v2-implementation.md.
- 공통 서버 진입: coach_v1/pregame_server.py. 실제 게임플랜 호출 흐름은 GP23-02에서 추적한다.

## 2+3 구현 목표
입력 어댑터(Riot/LCU/수동 가정)는 출처와 시각을 정규화하고, 공통 판단 계층은 방향·행동·이유·제약·전환을 반환한다. 프론트엔드는 같은 결과를 2+3 카드와 태그로 표시한다.
기본 정보, 로딩 전 조합 계획, 경기 중 확인 정보의 책임을 분리한다. 로딩 모드는 현재 정글 위치를 추정 관측으로 만들지 않는다.
정글/라이너 표현 차이는 공통 판단 결과의 역할별 표시이며 별도 전술 사실 저장소를 복제하지 않는다.
상세 계약: [게임플랜 2+3](docs/gameplan-content/gameplan-2-plus-3-v1.md). 모듈 변경은 DEPENDENCY_MAP.md와 함께 갱신한다.

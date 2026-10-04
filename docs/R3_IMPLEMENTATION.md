# R3 — Evidence-to-Review Foundation(근거에서 복기까지의 실행 기반)

기준: main 99288ed6782858713bbb4bb61cc594094d83f2f6, Design v1.0 FROZEN.
승인: 2026-10-04 사용자가 구조 설명 후 구현 계속 진행 요청.
기존 설계·legacy·Freeze 문서 변경 없이 새 coach_v1 namespace에서 구현.

## 처음 보는 사람을 위한 구조
장면·경기 정보 → 근거 정리(확인/미확인/충돌) → 당시 상황 재구성 → 선택 비교 → 복기.
패치·상성·역할 지식은 비교를 지원하며, 경기 전·후 모드 제한이 적용된다.
이번 구현은 근거에서 복기까지의 데이터 처리·검사 기반과 모드 차단이다.
현재 입력은 JSON 합성 사례. 경기 영상이나 Riot API를 읽어 자동 판단하는 앱은 아직 아니다.
예시의 행동 우위와 비교 관계는 합성 주석으로 제공한다. 엔진은 근거 적격성·필수 정보·모순·우열 조건을 검사한다.
대미지 계산/상성 추론/실경기 예측을 새로 만들지 않았다.

## R3 완료 조건
1. 필수 출처·시간·관점·patch·품질·계보를 가진 관찰 입력과 불변 상태 스냅샷.
2. 중복·지연·충돌·미확인·관전자 정보·유효성/계보 문제 처리.
3. 충분성과 유불리 분리, 상황 전체의 다차원 비교, 종료/중단 및 정보 요청 마감 처리.
4. 합성 예시를 CLI(명령줄 실행기)로 읽어 JSON 복기 출력, 출처와 제한 표시.
5. 회귀 및 기존 보호 검증, 독립 반례 수정, GitHub 보존.

## 파일별 역할
|파일|역할|
|---|---|
|coach_v1/models.py|입력 타입·enum·참조·필수 출처 검증|
|coach_v1/state.py|시점/관점별 상태, 충돌·계보 보존, 내용 기반 ID|
|coach_v1/engine.py|모드 잠금, 정보 검사, 조건별 평가, 우열/동등 모순 탐지, 정보 요청|
|coach_v1/__main__.py|합성 입력 CLI, 오류 처리·덮어쓰기 방지|
|tests_r3/|새 R3 회귀 테스트; 과거 R1 테스트 아님|
|examples/r3/|실행 가능한 입력 2개와 실제 출력|
|schemas/r3-review-input.schema.json|현재 입력의 기계 판독 schema|

## 실행
Python 3.12.14 / pydantic 2.13.5에서 확인. 새 엔진은 legacy import 없음.

    python3 -m unittest discover -s tests_r3 -t . -v
    python3 -m coach_v1 examples/r3/insufficient-evidence.json --synthetic
    python3 -m coach_v1 examples/r3/compare-wait-retreat.json --synthetic

출력을 저장하려면 --output 새파일.json. 기존 파일 덮어쓰기는 오류로 종료한다.
명시 --synthetic 없이 실행하거나 TEST 외 모드를 사용하면 거부한다.
source quality/knowledge REVIEWED 값도 합성 주석이며 진짜 경기 증거 검증을 대신하지 않는다.

## 결과 해석
- 첫 사례: enemy:response 결손으로 해당 후보 INSUFFICIENT/UNDETERMINED. 정글 last_seen은 현재 위치가 되지 않는다.
- 두 번째: 모든 합성 상황에서 대기의 성장 손실을 명시했을 때만 후퇴가 남는다. 현실의 무조건 후퇴 규칙이 아니다.
- alternatives는 검토에 남은 후보이며 실행 권고가 아니다. recommendation=null 유지.
- 의도 미제공은 UNKNOWN, 실행 위반은 NOT_EVALUATED. 사후 결과는 평가 입력으로 사용하지 않는다.
- scenario 완전성·주석의 게임적 타당성은 R3에서 검증하지 않으며 출력에 명시한다.
- 유효성 미검증 현재 상태는 관찰 시점 밖에서 STALE. 임의 TTL 없음.
- PLAYER_REVIEW의 knowledge_cutoff는 분석 수신 마감, RECEIVED_AS_OF는 당시 시스템 수신 마감.
  두 경우 모두 event-time과 당시 player visibility를 적용한다.

## 검토와 수정 이력
- 작성자 검사: 파생 정보가 충돌하는 원관찰 한쪽을 사용해 KNOWN으로 승격되는 경로 차단.
- 작성자 검사: 과거 파생 이벤트가 이후 원관찰을 참조하는 미래 계보 차단.
- 작성자 검사: 불충분/EXPLORATORY 후보에 비교표만 붙여 대안을 제거하는 경로 차단.
- 독립 F-R3-01: 만료 행동에 정보 요청이 생성됨. 만료/IMPOSSIBLE 대상 제외, 활성·비활성 ID와 보류 사유 보존.
- 독립 F-R3-02: A>B, B>C, A=C 모순을 탐지 못함. scenario/dimension별 SAME 양방향 edge를 포함한 엄격 순환 탐지 추가.
  모순 시 비교 기반 후보 제외를 보류하고 conflict IDs 출력.
- 독립 재검토: 표적 반례 3/3 PASS, 해당 범위 남은 차단 요인 없음. 전체 suite는 주 작성자가 실행.
- 도구 실행 스크립트 문법 오류 1회: 파일 생성 전 실패, 구문 수정 후 재실행. 제품 코드 실패와 구분.
실패 반례와 수정 후 검증을 구분하며 이전 설계 감사 이력은 수정하지 않는다.

## 완료 범위와 다음 작업
R3는 SYNTHETIC_ONLY(합성 검증 전용) 기반. 실제 PRE_GAME/POST_GAME/LIVE 기능은 차단 상태다.
후속: 실제 원자료와 검증된 adapter → 종료 검증 → 실제 입력/지식 검토 연결 → API/DB → 웹 화면.
모바일 웹·자동 픽 감지·자동 영상 처리·실제 상성 지식·SQLite/job/API·외부 AI는 아직 구현하지 않았다.
실제 표본 없이 실경기 사용 가능 제품으로 표시하지 않는다.
진행률: R3의 위 5개 완료 조건 기준. 전체 제품 구현률 미산정.
Design v1.0의 24개 설계 요구 검토 완료를 제품 기능 24개 구현 완료로 환산하지 않는다.

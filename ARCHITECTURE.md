# 아키텍처 책임과 경계
2026-10-25 · 관찰 기준 main `8e67cce63a29decae9f64a21f7c387bf73824507`. 경로 확인과 새 기능 완료를 구분한다.

## 확인한 실행 경로
1. `web_r4/loading.js`의 `analyze()`는 수동/공유/복원 입력을 `window.LoadingStrategy.analyze`로 보낸다. `loading-draft.js`는 불완전한 픽·챔피언 검색 인계를 보존하며 완성 입력과 구분한다.
2. `web_r4/loading-engine.js`의 `validate`/`analyze`는 legacy, input-v2/v3/v4를 검증하고 탐색·웨이브·교전·교환 모듈 및 `LoadingCoach.evaluate`를 호출한다. 보고서는 `lol-coach-loading-report-v3`다.
3. `web_r4/loading-coach.js`의 `evaluate`는 같은 보고서·가정·구간·자료로 `LoadingPlanboard.evaluate`를 호출한다. `web_r4/loading-planboard.js`가 조건·후보·비용·단계별 행동·코칭·근거를 묶고 `buildDelivery`가 `gameplan-delivery-v1`을 만든다.
4. `web_r4/loading-presentation.js`의 `project` → `web_r4/loading-coach-view.js`의 `renderPresentation`이 같은 `report.coach.planboard`를 화면으로 투영한다. 비교표·5개 행동·지도·상세·legacy 경로를 보존한다. `LoadingPresentation.encode/decode`의 공유 상태 버전 1은 입력/구간/상세만 저장한다.
5. `scripts/export_gameplan_five.js`와 `scripts/build_gameplan_preview.js`는 같은 engine/presentation을 사용한다. 원문 예시는 엔진 결과 그대로 보존하며 수작업 문구를 섞지 않는다.

## 서버와 입력 어댑터 경계
`coach_v1/pregame_server.py`는 정적 모듈과 인증된 `/dev/v1/pregame/pc-status`를 제공한다. `pc_gameplan_input` → `coach_v1/gameplan_input.py.normalize`는 이미 privacy-filtered LCU 선택/수동 8필드 입력을 정규화한다. 브라우저 판단 엔진을 새 서버 엔진으로 복제하지 않는다. 기본 2초는 연결 liveness이며 정글 위치의 전술 신선도가 아니다. `live_coaching_enabled=False`와 실제 클라이언트/세션/본인 연결 미검증 경계를 유지한다.

## 2+3 및 확장 결정
사용자 승인: 상단 전체 조합 방향/사용자 기본 방향, 하단 라인전/운영/교전·한타. 정글은 초반 정글/중반 운영으로 표현한다. 출처·시각·unknown/assumed/observed/stale과 선택·이유·금지·전환은 공통 판단의 책임이고 태그/화면은 그 결과를 표시한다. 로딩 입력은 실제 정글 위치·기술·ETA를 생성하지 않는다.

입력 v5 확장은 **구현 제안 / 검증 대기**다. 같은 planboard에 상황 입력을 연결하고 기존 소비자 호환을 검사한다. 임의 출력 버전 승격이나 별도 태그 판단 엔진을 만들지 않는다. 중복 제거 후보는 view의 정책 선택과 기존 planboard의 정책 중복이며, 실제 삭제는 반례·호환 검사 후 판단한다. 새 런타임 AI 호출은 필수 경로가 아니다.

## 학습실 추가 범위
`docs/learning-room/video-topic-taxonomy-v0.1.md`의 읽기 전용 taxonomy/source/claim/lesson 인덱스와 검색 UI를 별도 작업으로 연결한다. 80 leaf는 확보 영상·전술 수가 아니다. 6.1~6.6과 160행 유지. speech candidate/visual review/claim review/게시를 구분하고 `coaching_enabled`를 자동 승격하지 않는다. 새 모듈의 실제 파일/테스트는 해당 작업의 증거가 생긴 뒤 아래 상태 문서에 기록한다.

관련: [의존 관계](DEPENDENCY_MAP.md), [출처](SOURCE_REGISTRY.md), [상태](docs/gameplan-content/gameplan-2-plus-3-status.md), [반례 검토](docs/gameplan-content/gameplan-2-plus-3-review.md). 이 문서의 경로 확인은 새 코드·CI·브라우저·배포 통과가 아니다.

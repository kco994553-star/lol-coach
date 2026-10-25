# GP23·6.학습실 통합 결과

2026-10-25. 제품 [PR143](https://github.com/kco994553-star/lol-coach/pull/143) head `739851e9c4258defc72bf91d3b68a2f38dd8db09`를 정상 병합한 main `d1d00053dfd3710bb94e08549c7ca256ab0c43ee`가 출고 정본이다. 아래 검증·게시·실환경 확인은 완료됐다. 현재 `work/gp23-learning-results-20261025`는 영수증·관리 추정·인계만 기록하는 결과 전용 브랜치이며 이 브랜치의 push/PR/CI/병합은 상위 실행자가 별도로 수행한다. 동일 제품을 재게시하지 않는다.

## 바뀐 것

- **3.2~3.7 / GP23-01~44:** 기존 planboard에 strict input-v5와 17개 출처 상태 필드를 더했다. 새 화면의 상단은 전체 조합 방향·사용자 기본 방향, 하단은 라인전(정글은 초반 정글)·운영·교전/한타다. 비교표·단계별5행동·독립 코칭·상세·지도와 기존 v1~v4 링크를 유지한다.
- 관측/가정/미확인/stale은 직렬화와 검증을 분리한다. 현재 버전은 명시한 가정만 실행 비교에 사용한다. 과거 observed/stale 정보는 신선도 미검증 참고이며 현재 정글 위치·기술·ETA로 승격하지 않는다. 웨이브 가능성·자원·호응·기회 종료·실제 기여·지형·보호/방해 목표에서 같은 결과로 문장·행동·태그를 갱신한다.
- **6.1~6.6:** `learning.html`에서 4/20/80 분류, 검색·챔피언/포지션/상대/상황/패치/근거 필터, 11항목 카드, 출처와 조건 변경 성찰을 구현했다. 기존29개 claim 참조와29개 성찰, 영상8개 링크 후보를 분리한다. 원래 `loading-knowledge.json`과 학습6장면은 보존했다.
- `coach_intake.video.index_transcript`를 재사용하는 허용된 오프라인 자막 어댑터, 결정별 구간 색인과 명시적 접근/재사용/해시/길이 검사를 구현했다. 새 실제 자막·구간·장면 수용은0건이다. 링크만으로 본문 확보·시각 검증·전술 승인으로 기록하지 않는다.
- **2.4 / 3.7.4 / 5.5.2:** 챔피언·게임플랜·복기에서 관련 학습으로 이동한다. 공개 URL에는 허용 필터와 불투명한 세션 복귀 토큰만 넣는다. 전체 픽/개인 기록은 세션에 두고 원래 화면으로 돌아간다. 인증 검색 POST API와 공개 정적 검색은 같은 자료와 의미를 사용한다.

## 검증

| 구분 | 실제 결과·근거 |
|---|---|
| 전체 회귀 | `python -m unittest discover -v -s tests_pregame`: **965 PASS / 164.112s**. 실행 전후 CURRENT 전체 해시 동일. `full-pregame-stable.json`, `logs/full-pregame-stable.log` |
| 기능 의미 | 출처/stale/웨이브/호응/정글/탱커/solo/기회 소진/지원 범위/동일결과 태그 검사. 학습20개 데이터·11개 프론트·6개 통합, FE/Python 검색37벡터 및 HTTP 원본 패치12개 라벨 검증. 수량은 전체965와 중복 합산하지 않는다. |
| 새 브라우저 | `browser_gameplan_2plus3.py`:1440/390/320·200%·키보드·공유/변경/초기화/기존 링크/지원 부족. `browser_learning.py`:33검사. `browser_champions.py`:55검사·18PNG. `browser/`의 소스 해시/영수증 참조. |
| 기존 브라우저 | 기존 current DOM·legacy widget/지도/조건/스킬/개인·프로 fixture 흐름 통과. 마지막 presentation 단계의 예전 한타 제목 단언은 새 요구에 맞춰 정확한 새 제목으로 수정했고5그룹을 재실행해 PASS. 기존6장면 directions와 game-info도 별도 PASS. 최초 실패 전체 로그를 보존했다. 정확 PR/main의 원격 browser-regression에서 전체 순서와 강화된 코칭 본문 단언을 다시 통과했다. |
| 독립 검토 | 두 도메인 검토와 최종 whole-branch 검토. 검색 맥락 유실, HTTP 패치/역할 정규화, 기회 종료 문장·태그 불일치를 RED→GREEN으로 수정하고 재검토했다. 최종 SPEC PASS / QUALITY PASS(명시 P2 후속). `reviews/final-review.md` |
| 원문5쌍 | `node scripts/export_gameplan_2plus3.js --seed 20261025 --require-bound`: EXACT_COMMIT6e2e255, 10회 재실행·5개 단일 조건 변화 일치. 원문 수작업 교정 없음. `examples/manifest.json` |
| 실영상·실경기 | **UNMEASURED / N=0**. 실제 Windows/LCU·새 영상·코칭 효과 검사 PASS가 아니다. `live-evaluation-plan.md` |
| 원격 CI·배포 | PR143 필수3 SUCCESS, 정확 main 필수3 SUCCESS. Pages `47e241dbf8ddddc612b22902141ed3a2e2411372` / run40188291641 SUCCESS. 실제 HTTPS106/106 자산 SHA·29브라우저검사·24PNG PASS. `pr143-ci.json`, `product-main-ci.json`, `pages-ci.json`, `live/receipt.json` |

## 냉철한 품질 판정과 미완성

고정 seed의 임의10픽5개는 탑 Trundle / 정글 Darius / 미드 Ekko / 바텀 Aurora / 서포터 Karthus다. 임의 역할 배치는 실제 그 포지션의 적합성 검증이 아니다. 좋은 출력만 고르지 않았다. 내부 평가 점수는 **7/8/7/7/8(각12점)**이며, 모든30개 단계 카드는 `GENERAL_ONLY`다. 구체성이 부족한 사실을 숨기지 않는다. 실제 평가표와 인용은 `docs/gameplan-content/gameplan-2-plus-3-evaluation.md`에 있다.

GP23-23의 대상별 현재 위협 우선순위는 UNKNOWN이다. 상세의 이름/기술은 무순위 수단 후보이고, 누가 지금 닿을 수 있는지 확인된 사실이 아니다. GP23-26의 다른 역할별 고유 전술과 GP23-39의 낮은 구체성 개선도 PARTIAL로 유지한다. 명목 인원으로 전투 우세·승률을 만들지 않으며 기여/도착 순서는 정성 조건이다.

학습 카드의 목표·위협·이유·대기 비용·회복이 원문에 없으면 미확인이다. 반례를 확인된 회복 행동으로 바꾸지 않는다. 바텀 조합 주장에 Lux가 등장한다고 SUPPORT 적용 강의를 생성하지 않는다. `validate_index` 단독으로 외부 claim의 진위를 인증한다고 보장하지 않는다. 정상 builder와 오프라인 bridge의 결속 범위를 유지한다.

## 정확 출고·실환경 영수증

| 단계 | 정확 대상·실제 결과 |
|---|---|
| 정상 PR | [PR143](https://github.com/kco994553-star/lol-coach/pull/143), head739851e9c4258defc72bf91d3b68a2f38dd8db09. [40186976680](https://github.com/kco994553-star/lol-coach/actions/runs/40186976680) pregame / [40186976699](https://github.com/kco994553-star/lol-coach/actions/runs/40186976699) regression·browser-regression 전부 SUCCESS |
| 정확 제품 main | `d1d00053dfd3710bb94e08549c7ca256ab0c43ee`. [40187456643](https://github.com/kco994553-star/lol-coach/actions/runs/40187456643) pregame / [40187456649](https://github.com/kco994553-star/lol-coach/actions/runs/40187456649) regression·browser-regression 전부 SUCCESS |
| 공개 게시 | artifact `47e241dbf8ddddc612b22902141ed3a2e2411372`, [native Pages40188291641](https://github.com/kco994553-star/lol-coach/actions/runs/40188291641) SUCCESS. `pages-ci.json` |
| 실제 HTTPS | 2026-10-25 11:23:28.444602~11:23:44.604393 UTC. [공개 사이트](https://kco994553-star.github.io/lol-coach/)의106/106자산 SHA·root/build-info·비공개경로 경계 PASS. `live/receipt.json` |
| 실제 브라우저 | 29검사·24PNG,1440/768/390/320폭·200%·키보드. input-v5→학습→정확한 계획 복귀, 챔피언→학습→필터 복귀, 실제 기존 공개 PRO_REFERENCE Galio승리7/4/6→복기→학습→같은 원래 기록 복귀 PASS. route/fixture/숫자 주입0, API/provider 호출0. `live/browser.json` |
| 보존·롤백 | 공개 pro SHA `64d4830149af4ba515ac3b5e6c745629f80d00b0b7e416c30a5e27d4afd8c6e3`, typed validation·export 전후 일치. 이전 artifact `b0ec3cb8e15f0fa4cc6aa0454897317c23e979c9`를 롤백 대상으로 기록. `publication-prepared.json` |
| Notion | 기존 관리자/상세/그래프/학습실/게임플랜5개에 최신 절만 append,5/5읽기 재확인. ID·이전본문·자식링크 보존. `notion-sync.json`, `notion-sync.md` |

첫 실환경 harness 실행의 IPv6 보조 요청 실패는 `/workspace/gp23-artifacts/live/release-d1d0005`에 그대로 남긴다. 소스/자료 결함으로 판정하지 않았으며 최종 성공은 별도 `release-d1d0005-final`에서 확보해 `live/`에 보존했다. 기존 presentation의 구 한타 제목 단언 실패도 로그로 보존하고 새 정확 제목으로 고친 뒤5그룹 PASS; 강화된 코칭 본문 검사는 원격 CI에서 실행했다. 실패를 성공으로 덮어쓰지 않았다.

**실제 outage/retry는 NOT_RUN**: 실제 공개 source outage가 없었다. 로컬 fixture의 오류·재시도 상태 검사는 PASS이며 실제 장애 복구 측정과 구분한다. 원래 live receipt의 `source_error_state=BLOCKED`는 장애가 없는 재현조건 부재를 의미하며 최종 정상 흐름 실패가 아니다.

## 동기화·관리 추정·아직 못 하는 것

GP23-01~44는 **DONE41 / PARTIAL3(23,26,39)**다. 현재 대상별 위협순위 UNKNOWN, 다른 역할 고유전술·임의픽 원문의 구체성 부족을 공개한다. 실제 새 영상/수용자막/시각검토/게임효과 **N=0, UNMEASURED**. 허용 자막 미확보만 BLOCKED이며 구현된 색인·검색·조건 성찰·복귀를 막지 않는다. 외부 claim을 validate_index 단독으로 인증하지 않는 P2 경계와 지원범위 발견성 개선도 남아 있다.

현재 **MANAGEMENT_ESTIMATE 전체45.3% / 프론트52.5%, 학습실50.0% /61.8%, 게임플랜44.8% /49.0%**. `progress-assessment.json`과 기존160행 feature matrix의 동일가중0/0.5/1 판정을 사용한다. 실제 제품 기준은 main `d1d00053dfd3710bb94e08549c7ca256ab0c43ee`이며 테스트 통과율·taxonomy80개·자료수·실경기 전술 정확도가 아니다. 이 결과 브랜치의 변경된 평가/신규 영수증은 정상 PR·CI 후 main에 들어간다. 이미 출고한 제품의 성공과 결과문서 병합 상태를 혼동하지 않는다.

사용자 승인 방향·기존160 ID·Frozen350·보호 결정·원자료/실패이력·쿼터·스케줄·인증을 보존했다. 신규 유료/AI/provider 호출0, 새 USER 전술승인0. Notion5개 최신절의 상세URL과 readback/source hashes는 `notion-sync.json`에 있다. 전체 과거 페이지 내용은 공개 저장소에 복사하지 않았다.

## 다음 작업 — 기존 목표 유지

1. 상위 실행자는 결과 전용 브랜치 push → 정상 PR → 필수 CI → 일반 병합을 수행한다. source seal과 정확 결과 SHA/CI는 최종 인계에 추가한다. 동일 product 재게시 없음.
2. 사용자 추가 목표 **티어/상대포지션 확장 IN_PROGRESS**는 별도 `/workspace/lol-coach-champion-tiers`에서 계속한다. 실제 신규 확보0, 만료키/기존 호출창으로 실제 수집 BLOCKED이며 이번 GP23 출고·관리 추정에 포함하지 않는다. 관련 독립 준비 작업은 진행한다.
3. GP23 후속은 source-bound 역할/매치업 고유 내용·대상별 위협 근거·지원 범위 발견성, 허용 오프라인 자막/장면 검토다. 새 허용 원문이 없으면 자료 수용만 BLOCKED, 가짜 예시나 자동 승인으로 채우지 않는다.

원문재현 `node scripts/export_gameplan_2plus3.js --seed 20261025 --require-bound`; 전체검사 `python -m unittest discover -v -s tests_pregame`. 자막 재개는 `contracts/learning-room-v1.md`의 기존 manifest CLI를 따른다. 현재 소스에 재실행할 때 원문6e2e255과 실행 source가 일치하는지 먼저 확인한다.

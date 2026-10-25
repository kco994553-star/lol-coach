# 프론트엔드 v2 구현·인수 기록

기준일: 2026-10-25. 기능계층 **v2.0**과 게임플랜 콘텐츠 **v1.3**은 별개다. 제품 main `ac48506c8f6493778d3fcdf675041d66f89c5390`의 구현·검사·정상 병합·공개 배포와 2026-10-25 08:42:22 UTC 실제 HTTPS 검사를 기록한다. 검증 범위는 출고 코드/자료와 명시적 UI 흐름이며 전160개 기능 완료·전술 정확도·실경기 효과를 뜻하지 않는다. 상세 영수증은8절에 둔다.

## 1. 범위와 상태

목표는 계정 없이 **챔피언 선택 → 자료 범위를 확인하는 상세 → 명시적 게임플랜 전달**이다. 기존 vanilla HTML/CSS/UMD JS와 Python 익명 집계를 사용한다. 런타임 AI·유료 호출·인증 완화·사용자 결정 변경은 없다.

작업 시작 기준 main은 `b26269247537561e3c172364bb895f5078cacc41`이다. 재사용 선행 작업 PR #137은 필수 CI3개 후 정상 병합 `d489bcaf`, PR #138은 필수 CI3개·독립 검토·로컬439개 검사 후 정상 병합 `2ccb7352e7e7d31e52f5fc5faf487f030691e466`이다. 이 근거는 선행 설계/검색·기본조회 범위에 한정한다. 새 프론트엔드·통계 projection·성장 표시·전달 UI는 [PR140](https://github.com/kco994553-star/lol-coach/pull/140)으로 정상 병합되어 제품 main `ac48506c8f6493778d3fcdf675041d66f89c5390`에 포함되었다. 공개 artifact는 `b0ec3cb8e15f0fa4cc6aa0454897317c23e979c9`이며 Pages 배포와 실제 HTTPS 검사를 통과했다. 현재 파일 존재는 전체 기능 인수 완료와 별개다.

| 상태 축 | 인정하는 근거 |
|---|---|
| 명세 대응 | 현재 본문의 고유 기능 ID와 12필드 대응표 |
| 구현 | 해당 조건의 실제 코드와 남은 기능 명시 |
| 검사 | 정확 소스에 대해 실행한 명령·결과·반례·로그 |
| 통합 | 원격 main 커밋, PR 병합, 필수 CI 결과 |
| 배포 | export/publication 커밋과 배포 결과 |
| 실환경 | 실제 URL/PC 경로의 브라우저·네트워크 확인 |
| 코칭 효과 | 별도 실제 경기 평가. 현재 UNMEASURED |

## 2. 160행과 과거 125행 보존

정본은 [기능계층](../../contracts/information-architecture-v1.md) 최상단 **v2.0 본문**이다. 부록 C는 역사 자료다. [기능 대응표](frontend-v2-feature-matrix.json)는 현재 160개 고유 ID, 기존 125개 `legacy_id`, 추가·연결 35개를 구분한다. 각 행에 목적·기존 구현·부족 기능·입력·출력·예외·완료 조건·검사·의존성·위험·상태·근거를 둔다. `scope`가 부분 구현과 전체 인수를 분리한다. 입수 당시 main/로컬 상태는 `intake_context`와 행별 `intake_status`에 보존하고 최종 상태는 제품 main의 영수증으로 갱신했다. `status`는 `NOT_STARTED / IMPLEMENTED / TESTED / INTEGRATED / DEPLOYED / LIVE_VERIFIED`만 사용한다. `coverage`의 `PARTIAL / NOT_SUPPORTED / NOT_STARTED / SCOPED_IMPLEMENTATION`은 지원 범위이며 개발 단계와 별개다. 부분 구현의 `IMPLEMENTED`는 `scope.evaluated_scope`의 실제 코드만 뜻하고, 전체 기능 완료를 뜻하지 않는다. `missing`과 `full_feature_acceptance`를 함께 읽는다. `MET_FOR_DECLARED_SCOPE`도 명시한 소프트웨어 흐름/자료 범위의 수용일 뿐 전 챔피언·상대의 전술 완성을 뜻하지 않는다. 미지원 기능은 `status=NOT_STARTED`, 검증된 자료부족 UI는 별도 `ui_status=LIVE_VERIFIED`로 분리한다.

기존 1번은 유지하고, 기존 2~6번은 현재 3~7번으로 연결한다. 예를 들어 **v1.1 2.3.1 → v2.0 3.3.1**이다. 과거 파일·검사·원래 ID를 새 번호로 치환하지 않는다. 대응표의 `HISTORICAL_MAPPING`은 근거의 연결이며 새 기능 검사 결과가 아니다.

기존 게임플랜 인수는 [handoff-v11/result.md](../../evidence/actual-evidence/handoff-v11/result.md)의 당시 커밋·범위에만 적용한다. 그 기록이 새 챔피언 페이지·전달 어댑터의 검사를 대신하지 않는다.

## 3. 화면과 사용자 흐름

여섯 메인 메뉴는 **전적 검색 / 챔피언 검색 / 게임플랜 / 경기 중 도우미 / 경기 복기 / 학습실**이다. 작업 상태는 보조 링크다. 데스크톱·모바일의 순서와 선택 상태를 같게 유지한다.

| 화면 | 책임과 주요 상태 |
|---|---|
| `index.html` | 계정 검색·최근 표본·프로 참고. 정적 사이트의 개인 API 미연결을 표시 |
| `champions.html` | 173명 검색, 관측 포지션/미분류 필터, 결과 수, 최근 최대8명, 탐색 복귀 |
| `champion.html` | 기준 챔피언/역할 고정, 정확 모집단 결과·빈 그래프·기본 원문·상대/서포터 문맥 |
| 챔피언 변경 창 | 임시 선택 → 적용/취소, Escape·포커스 이동/복귀. 적용 전 상세 상태 보존 |
| `loading.html` | 전달 미리보기·명시 적용·부분 입력 보존, 완성 후 기존 strict10 분석 |
| `game-info.html` | 수동 아이템 정가 비교와 인증 PC 연결 상태, 미지원 라이브 정보 |
| `index.html#review-card` | 선택된 안전한 기록의 복기 진입. 실제 private 분석은 인증 PC `/postgame` |
| `directions.html` | 동일 source/claim registry의 제한 학습·사례·연습 |
| `status.html` | 기준 시각이 있는 지원·갱신·검토·검사 상태 |

별도 `review.html`이 있다고 가정하지 않는다. 8개 대표 페이지의 desktop/mobile 16장과 변경 창 2장의 총18 PNG는 실제 출고 UI를 캡처하고 URL·viewport·소스 해시를 함께 기록한다. 디자인 이미지 자체는 동작 검사나 데이터 근거가 아니다.

공통 상태는 조회 중·자료 없음·표본 부족·해설 준비 중·미지원 조건·갱신 지연/패치 불일치·연결 실패다. 0경기 승률은 null이며 0%가 아니다. 늦은 요청은 새 선택에 섞지 않고, 손상된 저장소나 저장 실패에서도 탐색을 계속할 수 있어야 한다.

## 4. 실제 자료와 공개 계약

통계 정본은 [champion-statistics-v1.md](champion-statistics-v1.md)다. 공개 `champion-stats.json`의 `format`은 `lol-coach-champion-statistics-v1`이다.

| 자료 | 실제 범위·용도 |
|---|---|
| 공식 카탈로그 | `loading-data.json`의 173명·공식 기술명/패시브·Q/W/E/R·검증된 로컬 초상화 |
| 기본 원문 | Caitlyn/BOTTOM, Ezreal/BOTTOM, Fiora/TOP, Graves/JUNGLE의 4개 프로필 |
| 최종 결과 표본 | 2026-10-11 snapshot의 실제50경기, KR·queue420·patch16.20·현재 CHALLENGER 수집 출발점 |
| 관측 포지션 | 현재는 같은 결과50경기의 **고유 경기 해시 합집합**을 내부에서 계산한 공개 count |
| 별도 성장 참고 자료 | 2026-10-13 full-power275경기의 자원 rate/최초 관측 레벨 marker를 `growth_source`로 사용. per-cohort member hash가 없어 관측 포지션의 고유 경기 분모로는 사용하지 않음 |

현재50경기 자료의 canonical digest는 `1f6f276d153bc11978670b0644ee31b16b28f260deb1be23196aabf0053d64fc`, gzip SHA-256은 `597a14e6d104bd914b60953abddfb9f2ef57ce307d8a38db7fd43153f78a1a10`이다. 이후 재생성 시 실제 파일의 metadata를 다시 읽는다. 50·275경기를 합쳐325로 세지 않는다. CHALLENGER는 전 참가자의 당시 티어를 증명하지 않는다.

`source`·`position_source`·`growth_source`는 각자 patch/region/queue/tier 의미/조회시각/기간/digest/경기 수를 갖는다. 현재 값이 같더라도 서로 다른 사용 목적을 숨기지 않는다. 후자는275경기 자료를 사용하지 못한 이유도 기록한다. 분당 관측 행의 합계나 최댓값을 고유 경기 수로 쓰지 않는다.

`champions[id].positions[ROLE]`은 `summary`, `duration`, 같은 역할의 `opponents[id]`, 별도 `growth`를 갖는다. 승리 수와 경기 수를 각각 합산하고 승률과 Wilson95 구간을 다시 계산한다. 다른 패치·티어·역할·상대 자료로 fallback하지 않는다. 공개 파일에는 계정/플레이어 식별자·원본 경기 ID·member-hash 목록이 없다.

기본 원문은 **REFERENCE_ONLY**, `delivery=null`, `tags=[]`, 전술 검토 상태는 `TACTICAL_UNREVIEWED`다. 단독 보기용 5행동이 없어 완전 기본 게임플랜으로 세지 않는다. 카이사는 검색되지만 기본 프로필이 없다. 원문4명, 관측 역할 표본, 검색173명은 서로 다른 지원 범위다. 공식 기전 source binding은 전술 승인이나 브라우저에서 외부 원문을 재검증했다는 뜻이 아니다.

픽률·밴률·룬·아이템 빌드·스킬순서는 `unsupported_metrics`다. 바텀 네 챔피언 2대2 결과 통계도 없다. 서포터 선택으로 원딜 상대 통계 분모가 바뀐 것처럼 표시하지 않는다.

## 5. 그래프 정의와 자료 부족

새 챔피언 그래프를 그리기 전에 확정한 **사용자 지정9개 결정**은 다음과 같다. 종료시간 결과와 자원 성장 참고를 구분하며 이 표를 관리자·상세·그래프의 같은 계약으로 사용한다.

| 번호 | 결정 | 실제 계약과 제한 |
|---|---|---|
| 1 | 원본 자료 | manifest/hash 검증된 outcome50의 최종 결과, 별도 full-power275의 자원/marker. 원본 보존, 런타임 수집 없음 |
| 2 | 모집단 | KR/420/16.20·현재 CHALLENGER 수집 출발점. outcome50·역할관측50·growth275의 분모/기간/digest를 분리. 전 참가자 당시 티어·전체 모집단을 뜻하지 않음 |
| 3 | 구간 | 결과는 `[0,5)…[55,60),[60,∞)`13개. 성장은5/10/15/20/25/30분 floor bin의 마지막 수신 프레임 기준. 없는 분 보간 없음 |
| 4 | 최소 표본·정밀도 | 결과선은 각 구간n≥100. 성장 자료는 기존 `visible`/`omission_reason` 정밀도 정책 사용, 결과N100을 전용하지 않음 |
| 5 | 산식·불확실성 | 결과는 Σwins/Σn와 재계산 Wilson95. 자원은 관측 누적값/실제 경과분, champion−pooled-role rate 차이의 기존 Student-t95 CI이며 champion평균의 CI가 아님 |
| 6 | 비교 관점 | 결과 전체선과 A-vs-B선은 동일 A·역할·집계조건. 성장선은 선택 champion과 보존된 pooled-role 표본의 rate이며 그 표본에 champion이 포함될 수 있음 |
| 7 | 없는 자료 | 결과 부족구간과 성장 source-hidden 행은 gap, null/누락 유지. 다른 cohort/분당 자료로 결과 fallback하지 않음. marker 없는 레벨/아이템을 생성하지 않음 |
| 8 | 해설·전환 조건 | 실제4개 원문의 조건부 참고 방향만 재사용. LEVEL marker는 최초 수신 프레임의 구간 검열 관측이며 정확 레벨업/스킬준비/파워 spike가 아님. 인과·최적 구성 판단 없음 |
| 9 | 캐시·갱신 | 오프라인 결정적 생성/배포된 로컬 JSON을 페이지 시작에서 catalog와 각각1회 fetch하고 화면 내 재사용. 조회마다 AI/네트워크 집계 없음. source/digest가 바뀌면 새 게시물로 갱신하며 영속 분석 캐시는 구현하지 않음 |

기존 복기의 자원9개는 개인 누적 골드/경험치/CS, 같은 역할 상대 대비 세 자원 차이, 역할 모집단 대비 세 자원/분 차이다. 정의·개인/참고 CI·원본 공백·좌표 proxy의 별도 경계는 [복기 자원 의미](../queue/R3_PERSONAL_POSTGAME.md)에 보존한다. 이 기존 그래프 수와 위9개 사전 결정을 혼합하지 않는다.

**새 챔피언 기본 그래프의 목적**은 시간대별 강약과 활용/전환 조건을 읽는 것이다. 승률 자료를 쓰면 ‘승률 기반 파워 경향’과 승률(%) 축을 표시한다. 실제 수치는 **해당 종료구간에 끝난 경기 중 기준 A팀 승리 비율**이며, 현재 분 시점의 승리확률·라인전 승률·인과적 전투력이 아니다. 전체 선과 A vs B 선은 같은 A 관점·같은 source 조건이다.

새 공개 계약의 구간은 `[0,5), …, [55,60), [60,∞)`의13개이며 끝 경계는 배타적이다. `n>=100`만 그린다. 현재 전체 표본이50이므로 모든 선택/구간에서 선은 부족 상태가 정상이다. 상세 수치·n·Wilson95는 설명과 함께 확인할 수 있으나 임의 선·보간·0점·minute-resource 대체는 금지한다. 상대선이 없으면 유효한 전체선만 유지하되, 현재 자료에서는 전체선도 임계치 미달이다.

별도 성장 참고는 `growth_source`275경기의 ROLE_POPULATION 자료이며 164명·284개 역할의 자원/marker를 포함한다. 선택된4,536개 자원 행 중 source-visible은3,222개이고, metric별 중복을 n에 더하지 않고 합친 LEVEL record는1,299개다. 현재 ITEM marker는0개이며 대응 공식 아이템 catalog가 없어 이름을 만들지 않는다. outcome에 없는 champion/role은 결과n나 관측 포지션 count를 만들지 않고 성장 자료만 제공할 수 있다.

각 성장점의 `champion_n`은 champion 관측 참가자 수, `reference_n`은 보존된 역할표본 참가자 수, `n`은 source 추정기의 역할 참고 경기 수다. 화면은 세 n을 구분하고 source-hidden 값의 평균/차이/CI를 숨긴다. `delta_ci95`는 **champion−pooled-role rate 차이의 구간**이며 `champion_mean`의 구간으로 표시하지 않는다. rate는 누적 자원/실제 경과분으로, 그1분에 새로 번 자원이 아니다.

LEVEL2/3/6/11/16의 median/IQR/n은 해당 수준 이상을 **처음 관측한 수신 프레임**의 분포다. 시간 간격 때문에 정확 획득 시점은 알 수 없고 실제 스킬 습득·쿨다운 준비·필수 타이밍·전투력 급등을 증명하지 않는다. ITEM이 이후 존재하더라도 관측 구매 후보 ID/순서일 뿐 전체 빌드나 최적 아이템 추천이 아니다.

성장 이유·활용 행동·중단 조건은 실제 준비된 챔피언/상대 원문 범위로 제한한다. 레벨6·첫 아이템 완성은 실제 시각 또는 명시 가정이 없으면 그래프 아래 조건으로 설명하며 고정 분 위치에 그리지 않는다. 50경기로 완전한 파워 곡선·패치별 추이·전 매치업 해설을 제공했다고 주장하지 않는다.

## 6. 부분 입력과 보존 안전 전달

공개 인터페이스는 `LoadingDraft.createIntent({champion,position,opponent?,opponent_position?,ally_support?,enemy_support?,reference?,return_state?})`, `previewTransfer(intent,draft)`, `applyTransfer(preview,{replacements,targets},expectedRevision)`, `toCompleteInput(draft)`다. intent는 검증된 불변 plain data이며 링크는 `loading.html#handoff=<encodeURIComponent(JSON.stringify(intent))>`다.

1. 상세의 두 명시 버튼만 전달을 시작한다. 탐색·상대 선택·취소는 저장된 계획을 바꾸지 않는다.
2. 미리보기가 각 대상 슬롯의 기존값/새값·충돌을 보여준다. 차지한 슬롯은 명시 교체, 불명 슬롯은 명시 대상 선택이 필요하다. 중복 챔피언을 자동 삭제하거나 포지션을 추정하지 않는다.
3. 적용은 revision을 다시 확인한다. 오래된 preview는 재생성한다. 나머지 픽·진영·패치·선호·v3 scenario·v4 planning을 보존한다.
4. 미완성은 별도 session key `lol-coach-gameplan-draft-v1`에 보존한다. 빈5슬롯 배열/불명 포지션을 허용하는 draft와 기존 완성 분석 계약은 별개다.
5. 완성은 기존 엄격 검증/분석을 다시 실행하고 새 `#plan`을 만든다. 부분 적용은 오래된 `#plan`을 제거/전환하고 완성 결과로 보여주지 않는다. 기존 `#plan`을 읽을 때 우선하는 규칙과 새로고침 보존을 검사한다.
6. 취소는 URL·draft·기존 저장 계획을 보존한다. 복귀 링크는 허용된 로컬 champion 경로와 탐색 상태만 복원한다. 통계 필터는 실제 경기 사실로 적용하지 않는다.

## 7. 다른 메뉴의 정본·부족 상태 검토

| 영역 | 정본과 현재 경계 | 부족 기능/필수 예외 |
|---|---|---|
| 1 전적 | 인증 PC account API의 최근 솔로420 기록, 공식 랭크 조회, 공개 프로 projection | 실제 계정과 공통 통계 분리; 개인 챔피언 기록→공통 상세 링크는 정규형 ID면 상세, 그 외 검색어로 선택 페이지에 연결하며 포지션은 다시 선택하고 개인 통계를 전달하지 않음. 다지역·포지션별 기록·구매/룬 상세·현재 픽창 자동 연결 미완성. 미연결/없음/실패·늦은 응답 구분 |
| 4 경기 중 | 수동 inventory+공식 정가 catalog, 인증된 PC 관측 상태 | 실제 라이브 취득/표시 실증 별도. 타이머·궁극기 잔여·상대정글 추적·정글 경로 미지원. 가격합계≠현금/총골드/전투력. stale/불명 값은 null |
| 5 복기 | 인증 PC `PostgameStore`, 명시 import된 match/timeline·참가자·plan_id | 공개 안전 기록 선택만으로 private 원본 연결되지 않음. 영상/실제 실행/인과효과 미확인. 계획의 패치/역할/현재성 확인, 사건 공백과 추정 분리 |
| 6 학습 | 기존 source/claim registry·제한 장면·동일 게임플랜 근거 | 모든 챔피언/역할/상대 강의와 연습 미완성. 공식 사실/조건부 해석/미검토 전술·반례를 구분하고 없는 사례를 생성하지 않음 |

이번 목표에 위 메뉴의 수집기·라이브 타이머·추천 엔진·신규 전술 corpus 확대를 추가하지 않는다. 기존3단계 각5행동·독립 코칭 문단·추가 상세의 순서를 보존한다.

## 8. 검사·인수 영수증

제품 main `ac48506c8f6493778d3fcdf675041d66f89c5390`에서 전체906개 검사를139.948초에 다시 실행해 PASS했다. [전체 로그](../../evidence/actual-evidence/frontend-v2-20261025/full-pregame-merged-main.log)는 병합된 소스의 실제 결과다. 최종 targeted50개 검사·handoff 수정 후24개 검사·통계46개 및 단위10개 결과는 각 시점의 범위로만 인용하며906개와 더해 고유 검사 수로 세지 않는다.

| 근거 | 정확 범위와 영수증 |
|---|---|
| 병합·필수 CI | [PR140](https://github.com/kco994553-star/lol-coach/pull/140), [main](https://github.com/kco994553-star/lol-coach/commit/ac48506c8f6493778d3fcdf675041d66f89c5390); PR 및 exact main 필수3개 성공. [MVP40177148325](https://github.com/kco994553-star/lol-coach/actions/runs/40177148325), [Pregame40177148293](https://github.com/kco994553-star/lol-coach/actions/runs/40177148293) |
| 독립 검토·targeted | [최종 검토](../../evidence/actual-evidence/frontend-v2-20261025/final-review.md), [최종 수정 검토](../../evidence/actual-evidence/frontend-v2-20261025/final-fix-review.md), [targeted 로그](../../evidence/actual-evidence/frontend-v2-20261025/champion-final-targeted.log), [handoff 검토](../../evidence/actual-evidence/frontend-v2-20261025/handoff-fix-review.md) |
| 로컬 실제 Chromium | [screens/runner.json](../../evidence/actual-evidence/frontend-v2-20261025/screens/runner.json):55개 확인·18 PNG·107개 소스 해시. source head `f30da7fbd5658928403b7131456d20e19722ecc8`의 앱 소스는 병합 main과 동일하며 문서 영수증 갱신을 소급해 검사했다고 주장하지 않음 |
| 공개 export·배포 | [artifact](https://github.com/kco994553-star/lol-coach/commit/b0ec3cb8e15f0fa4cc6aa0454897317c23e979c9), [native Pages40177555880](https://github.com/kco994553-star/lol-coach/actions/runs/40177555880) SUCCESS. 공개 허용100개 파일과 private 제외 확인. [release-info](../../evidence/actual-evidence/frontend-v2-20261025/release-info.json) |
| 실제 공개 HTTPS | [라이브 사이트](https://kco994553-star.github.io/lol-coach/), [live-verification.json](../../evidence/actual-evidence/frontend-v2-20261025/live-verification.json):08:42:22 UTC까지57개 확인·100개 공개 파일 해시·29개 화면. exact main build-info/실제 응답 바이트와 선택·자료·전달 흐름 확인 |
| Notion | 기존4페이지 쓰기와 재조회 완료(08:47 UTC). root도4페이지의 main·45%/49%·자료 한계를 독립 재조회했다. 기존ID/자식/이전 원문은 보존했다. [동기화 기록](frontend-v2-notion-sync.md) |

실패는 감추거나 검사를 약화하지 않고 수정 이력으로 보존했다. handoff의4개 race/보존 반례를 수정했고, 기존5메뉴 assertion은 승인된6개와 순서까지 확인하도록 고쳤다. 모바일5열 잔존을6열로 맞춰 hero26px 수평 넘침을 해결했다. CI의 실제 Playwright 런타임 설치 누락을 보완했으며 실패한 검사를 skip하거나 허용치를 약화하지 않았다.

기존 공개 프로 참고 자료는 typed validation을 통해4,228바이트·SHA-256 `64d4830149af4ba515ac3b5e6c745629f80d00b0b7e416c30a5e27d4afd8c6e3`로 보존했다. source placeholder를 배포하지 않았고 이전 갱신 실패 표식도 유지했다. 이 과정은 새로운 Riot/API 수집이나 성공한 최신 갱신을 뜻하지 않는다. [보존 근거](../../evidence/actual-evidence/frontend-v2-20261025/preserved-pro-reference.json).

로컬·HTTPS 검사는 실제 출고 DOM/자료와 공개 흐름을 검증한다. 로컬 PC import는 격리 fixture이며 실제 계정/provider·Windows LCU·실경기 효과 성공을 대신하지 않는다. 실제 결과50경기는 여전히N100 미달이며 없는 승률선을 생성하지 않았다.

## 9. 진행률과 Notion 반영

제품 main `ac48506c8f6493778d3fcdf675041d66f89c5390`, 기준시각 **2026-10-25 08:42:22 UTC**의 [160행 평가](../../evidence/actual-evidence/frontend-v2-20261025/progress-assessment.json)에 따라 전체 **44.7% → 약45%**, 프론트엔드 **49.4% → 약49%**로 추정한다. 행별0/0.5/1의 동일 가중 합계/160이며 테스트 통과율·투입 노력·전술 정확도가 아니다. 프론트엔드는 실제 제공하는 화면/흐름 범위를 별도로 평가하며 없는 전술 데이터가 생긴 것으로 세지 않는다.

| 영역 | 행 수 | 전체 추정 | 프론트엔드 추정 |
|---|---:|---:|---:|
| 1 전적 검색 | 19 | 50.0% | 50.0% |
| 2 챔피언 검색 | 32 | 54.7% | 78.1% |
| 3 게임플랜 | 48 | 43.8% | 43.8% |
| 4 경기 중 도우미 | 19 | 21.1% | 21.1% |
| 5 경기 복기 | 13 | 38.5% | 38.5% |
| 6 학습실 | 17 | 50.0% | 50.0% |
| 7 작업 상태·지원 | 12 | 50.0% | 50.0% |

0은 미착수/요구 자료 부족,0.5는 일부 지원과 남은 조건,1은 선언된 범위의 완성 흐름을 뜻한다. 미병합 코드는 포함하지 않는다. 명세160/160 매핑은 문서 커버리지100%일 뿐 제품100%가 아니다. 기존 **전체35%·프론트엔드34%**는 영역별 Notion 관리 추정의 carryover였으며 다른 평가 방법의 당시 역사로 보존한다. 이를 이번 새 평가와 같은 측정값의 상승폭으로 해석하지 않는다.

[Notion 동기화 기록](frontend-v2-notion-sync.md)은 기존 관리자·상세·그래프와 허브를 유지하고45%/49%·같은 main·동일 자료 한계를 반영한다. 실제4페이지 쓰기/재조회와 root 독립 재조회를 완료했다. [영수증](../../evidence/actual-evidence/frontend-v2-20261025/notion-sync-report.json)이 확인 범위를 기록한다.

## 10. 남은 기능과 제한

현재 자료로는 모든 챔피언의 기본5행동, 전 상대의 라인/운영/한타 대응, 실제 N100 파워 곡선·패치별 추이, 룬/빌드/스킬순서 통계, 바텀2대2 통계, 픽 추천·현재 픽 자동 연결, 라이브 타이머/정글 추적, 동일 경기 영상·코칭 효과 검증이 완료되지 않는다. 검색·정확 부분 통계·공식 기술명·제한 원문·명시적 보존 안전 전달을 각각의 지원 범위로 인수한다.

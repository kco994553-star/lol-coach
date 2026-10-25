# 프론트엔드 v2 구현·인수 기록

기준일: 2026-10-25. 기능계층 **v2.0**과 게임플랜 콘텐츠 **v1.3**은 별개다. 이 기록의 현재 범위는 로컬 작업 트리의 코드·데이터·요구 대응이며 새 검사 통과, 원격 병합, 공개 배포 또는 실경기 효과를 증명하지 않는다. 실제 영수증은 아래 8절에 정확한 소스 해시와 함께 추가한다.

## 1. 범위와 상태

목표는 계정 없이 **챔피언 선택 → 자료 범위를 확인하는 상세 → 명시적 게임플랜 전달**이다. 기존 vanilla HTML/CSS/UMD JS와 Python 익명 집계를 사용한다. 런타임 AI·유료 호출·인증 완화·사용자 결정 변경은 없다.

작업 시작 기준 main은 `b26269247537561e3c172364bb895f5078cacc41`이다. 재사용 선행 작업 PR #137은 필수 CI3개 후 정상 병합 `d489bcaf`, PR #138은 필수 CI3개·독립 검토·로컬439개 검사 후 정상 병합 `2ccb7352e7e7d31e52f5fc5faf487f030691e466`이다. 이 근거는 선행 설계/검색·기본조회 범위에 한정한다. 새 프론트엔드·통계 projection·성장 표시·전달 UI는 아직 원격 병합 전이며 해당 신규 소스의 검사/CI/배포 영수증을 별도로 붙인다. 현재 파일 존재는 전체 기능 인수 완료와 별개다.

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

정본은 [기능계층](../../contracts/information-architecture-v1.md) 최상단 **v2.0 본문**이다. 부록 C는 역사 자료다. [기능 대응표](frontend-v2-feature-matrix.json)는 현재 160개 고유 ID, 기존 125개 `legacy_id`, 추가·연결 35개를 구분한다. 각 행에 목적·기존 구현·부족 기능·입력·출력·예외·완료 조건·검사·의존성·위험·상태·근거를 둔다. `scope`가 부분 구현과 전체 인수를 분리한다. `status`는 `NOT_STARTED / IMPLEMENTED / TESTED / INTEGRATED / DEPLOYED / LIVE_VERIFIED`만 사용한다. `coverage`의 `PARTIAL / NOT_SUPPORTED / NOT_STARTED / SCOPED_IMPLEMENTATION`은 지원 범위이며 개발 단계와 별개다. 부분 구현의 `IMPLEMENTED`는 `scope.evaluated_scope`의 실제 코드만 뜻하고, 전체 기능 완료를 뜻하지 않는다. `missing`과 `full_feature_acceptance=PENDING`을 함께 읽는다.

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

이 절의 명령은 **인수 대상**이며 실행/통과 기록이 아니다. 실행자는 결과·시각·정확 소스 SHA·범위와 실패를 추가한다.

```sh
python -m unittest tests_pregame.test_champion_statistics tests_pregame.test_champion_frontend tests_pregame.test_champion_handoff tests_pregame.test_champion_publication -v
python scripts/build_champion_statistics.py --output /tmp/champion-stats-review.json
python scripts/browser_champions.py --output /workspace/frontend-v2-artifacts/browser
python scripts/browser_champions.py --screens-only --output /workspace/frontend-v2-artifacts/images
```

필수 확인은 정확 cohort·가중 n/CI·경계/60+·n99/n100·gap·원본 보존, 선택/변경창/저장소 오류/늦은 응답, 미리보기·교체/중복/불명 슬롯/revision·취소/부분 새로고침·기존 가정 보존, strict10/기존5행동 본문 회귀다. 실제 Chromium PC와 공개 `/lol-coach/` subpath에서1440/390/320px·200%·키보드/터치·overflow·JS 오류·외부 요청·인증 경계를 확인한다. export 허용 목록/서버 정적 경로·CI source binding·private 제외를 별도 확인한다.

| 새 영수증 | 현재 기록 |
|---|---|
| 로컬 자동/브라우저 실행 | 최종 실행자의 정확 로그 대기 |
| 18 PNG·실제 UI source manifest | 캡처 실행자의 파일 목록/해시 대기 |
| 독립 검토·필수 CI | 검토/CI 실행 결과 대기 |
| 원격 main 병합 | 선행 PR137 `d489bcaf`·PR138 `2ccb7352e7e7d31e52f5fc5faf487f030691e466` 정상 병합. 신규 프론트엔드 SHA/PR 영수증 대기 |
| 공개 export·배포·실환경 | publication SHA·URL·검사 영수증 대기 |
| Notion 동일 페이지 반영/재조회 | 별도 동기화 실행 영수증 대기 |

## 9. 진행률과 Notion 반영

[동기화 기록](frontend-v2-notion-sync.md)의 기존 관리자·상세·그래프 페이지를 갱신한다. 상세 근거를 먼저 반영하고 관리자 상태, 그래프를 같은 버전으로 맞춘다. 여기서는 Notion을 쓰지 않았다.

진행률은 **원격 main의160행 전체 인수 범위**를 분모로 한다. 로컬/미병합·문서 대응·화면의 미지원 안내는 기능 완료 분자에 넣지 않는다. 행마다 `0=미착수/미지원`, `0.5=main에서 일부 수용되고 부족 기능이 명시됨`, `1=전체 완료조건의 검사/연결이 main에서 확인됨`을 동일 가중으로 합산해 `100×합계/160`으로 추정한다. 이는 기능 수 기반 **추정치**이며 노력·전술 정확도 비율이 아니다. 부가 표는 메뉴별 같은 산식, 기반 SHA, 평가 시각, 각 행 판정 근거를 공개한다.

현재 대응표는 로컬 코드 목록이므로 이 상태 문자열을 바로 위 산식에 넣지 않는다. 새 main 행별 평가를 붙이기 전에는 기존 **전체35%·프론트엔드34% 역사적 추정치**는 Notion 영역별 관리 추정을 현행160행의 메뉴별19/32/48/19/13/17/12개 비중으로 가중한 carryover 값으로만 보존한다. 이는 신규 main의 행별 인수 재평가가 아니다. 이를 이번 신규 소스의 완료율로 승격하지 않는다. 최종 보고에서는 실행자가 main의160행0/0.5/1을 실제 계산한 최신 추정치를 표시하며 ‘미산정’으로 남기지 않는다. `160/160=100%`는 요구 매핑 커버리지에만 사용할 수 있다. 과거의 백분율·미산정·다른 분모의 통계가 공존하면 원래 평가시각/분모를 남기고 새 근거표와 조정 사유를 기록한다. 원격 통합/재평가 이후 실행자가 실제 숫자를 추가한다.

## 10. 남은 기능과 제한

현재 자료로는 모든 챔피언의 기본5행동, 전 상대의 라인/운영/한타 대응, 실제 N100 파워 곡선·패치별 추이, 룬/빌드/스킬순서 통계, 바텀2대2 통계, 픽 추천·현재 픽 자동 연결, 라이브 타이머/정글 추적, 동일 경기 영상·코칭 효과 검증이 완료되지 않는다. 검색·정확 부분 통계·공식 기술명·제한 원문·명시적 보존 안전 전달을 각각의 지원 범위로 인수한다.

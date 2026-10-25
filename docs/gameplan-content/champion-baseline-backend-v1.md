# 챔피언 검색·기본 방향 조회 백엔드 v1

기준: 2026-10-25 KST. 기능: 2.1 입력·연결 / 2.3~2.5 기본 방향 자료 / 2.7 근거 추적.
설계: PR #137 `GP-CHAMPION-SEARCH-BASELINE` v0.1, 설계 blob `37343d9460dd36b5fa6a098a2e3206b3a1447f8c`.
기존 `2.1~2.7` 번호, 10픽 계약, 전술 승인 이력을 변경하지 않는다.

## 이번 구현 범위

`web_r4/loading-champion-baseline.js`는 네트워크·DOM·AI·저장소에 의존하지 않는 JavaScript 조회 모듈이다. Node와 브라우저에서 같은 입력에 같은 결과를 반환한다. 별도 서버나 DB를 새로 만들지 않는다.

저장소에 게시된 173명 목록을 검색한다. 기본 방향 원문은 기존 `loading-direction-profiles.js` v2의 케이틀린/바텀, 이즈리얼/바텀, 피오라/탑, 그레이브즈/정글 4개를 재사용한다. 조회 때 전술 원문을 재작성하거나 새로운 전략을 생성하지 않는다.

**현재 데이터는 문단만 있으며 단독 보기용 5개 행동은 없다.** 따라서 이 구현은 `REFERENCE_ONLY`로 자료 문단을 제공하며 `delivery=null`, `tags=[]`를 유지한다. 완전한 `gameplan-delivery-v1` 또는 출시 가능한 전체 기본 게임플랜으로 집계하지 않는다. 카이사는 검색되지만 기본 프로필은 `NO_PROFILE`이다. 생성된 이미지의 룬·빌드·승률은 이번 기능의 데이터가 아니다.

## 호출 계약

```javascript
// Node. 브라우저에서는 프로필 스크립트를 먼저 로드한 뒤
// LoadingChampionBaseline.createService(catalog)를 사용한다.
const {createService}=require('./web_r4/loading-champion-baseline.js');
const catalog=require('./web_r4/loading-data.json');
const service=createService(catalog);

service.search({query:'카이사', position:null, limit:20});
service.getBaseline({champion:'Caitlyn', position:'BOTTOM', patch:'16.20'});
service.prepareHandoff({champion:'Caitlyn', position:'BOTTOM'}, currentDraft);
```

생성 시 자료 스냅샷을 소유한다. 원본이나 반환 객체를 변경해도 이미 생성한 서비스의 다른 결과는 바뀌지 않는다. 새 자료로 갱신하려면 새 서비스를 만든다. 영속 캐시와 캐시 키는 이번에 구현하지 않았다.

### 검색

`search({query='', position=null, limit=20})`. 검색어 최대 100자, 결과 한도 1~200, 포지션은 `TOP/JUNGLE/MID/BOTTOM/SUPPORT` 또는 null이다. NFKC·대소문자·공백·문장부호를 정규화하며 정확 → 접두 → 부분 일치, 동순위는 이름/ID의 고정 문자 순서로 정렬한다. 강함·승률 순이 아니다.

`selection`은 언제나 null이다. 검색어가 정확하더라도 자동으로 사용자 픽을 선택하지 않는다. 같은 별칭의 여러 후보를 그대로 보여준다. 사용자가 선택한 정확한 대소문자의 정규 ID는 독립 식별자로 사용한다. 그 외 이름/별칭을 직접 조회할 때 모호하면 `CHAMPION_AMBIGUOUS` 오류다.

`authored_positions`는 프로필에 기록된 위치이며 실제 메타의 추천 포지션 또는 완성된 코칭 지원을 뜻하지 않는다. 검색의 포지션 필터도 **작성 자료 포지션 필터**다. 공식 Marksman/Support 같은 역할군을 실제 포지션으로 추측하지 않는다. `selectable_positions`는 5개 전체이므로 미지원 위치도 선택하여 자료 부족을 확인할 수 있다.

카탈로그 로드 실패/형식 오류는 `CATALOG_INVALID`, 검색 결과 없음은 `NO_RESULTS`로 구분한다. 데이터 로딩·재시도·상태 안내는 호출자의 책임이다.

### 기본 자료

입력 키: `champion`, `position`, 선택적 `patch`, `game='LOL'`, `mode='SUMMONERS_RIFT'`. 다른 게임·모드와 알 수 없는 키는 거부한다. 10픽 객체를 이 입력으로 받아들이지 않는다.

출력은 `gameplan-champion-baseline-v1`, `view_mode=BASELINE`, `composition=null`, `observation=false`다. 팀 우열, 실제 체력·쿨다운·웨이브, 최적 빌드 등을 만들지 않는다. 자료/프로필/정규화/엔진 버전과 단계별 상태를 반환한다.

| 상태 | 의미 |
|---|---|
| POSITION_REQUIRED | 포지션 선택 필요; 다른 포지션을 임의로 고르지 않음 |
| NO_PROFILE / UNSUPPORTED_POSITION | 챔피언 또는 해당 위치의 기본 자료 없음 |
| NO_PHASE_CONTENT | 해당 단계 자료 없음; 다른 유효 단계를 지우지 않음 |
| SOURCE_REVIEW_REQUIRED | 자료 형식·패치·근거 연결이 맞지 않아 해당 자료 차단 |
| REFERENCE_ONLY | 기존 작성 문단만 조회 가능; 5개 행동/태그는 미완성 |
| PARTIAL | 일부 단계의 원문은 읽을 수 있지만 다른 단계는 부족/차단 |

원문 `gain/method/explanation`과 `{Q}` 등의 표시 치환을 사용한다. 기술의 공식 한국어 이름은 카탈로그의 해당 슬롯과 연결한다. 단계에 필요한 슬롯별 ID·패치·출처 경로·해시가 카탈로그 source bindings와 일치해야 한다. 이 검사는 **게시 묶음 내부의 참조 일관성 검사**이지 브라우저에서 외부 원문을 재다운로드하거나 해시를 재계산하는 것이 아니다. 실제 파일 바이트 검증은 기존 게시·CI 소스 바인딩의 책임이다. 공식 기전 근거를 전술 승인으로 승격하지 않는다.

2자리 패치는 같은 게임 패치의 자료와 비교하고, 3자리 패치는 정확히 비교한다. 패치 미입력은 `NOT_CONFIRMED`이며 원래 자료 패치를 밝힌 참고 문단만 제공한다. 패치 불일치는 문단/행동을 현재 적용 자료처럼 반환하지 않는다. 이 구현은 최신 패치를 자동 수집하거나 현재 지역 클라이언트 버전을 알아내지 않는다.

조회 결과의 문자열은 HTML이 아니다. 화면에서는 textContent 또는 동등한 이스케이프 경로로 출력해야 한다.

### 조합 전달

`prepareHandoff(selection, draft=null)`은 **변경 제안(intent)**만 반환한다. `intent={own_champion,own_position}`이고 나머지 9픽을 만들지 않는다. 기존 드래프트는 깊은 복사로 그대로 보존하며, 실제 폼·저장소를 수정하지 않는다.

기존 슬롯 교체·다른 역할에 같은 아군 픽·미확인 위치는 `CONFIRMATION_REQUIRED`, 상대 팀 중복·기존 중복/포지션 충돌은 `BLOCKED`로 반환한다. 충돌이 없으면 `READY`지만 `apply_automatically=false`, `composition_ready=false`다. 이는 분석 가능 판정이 아니라 전달 제안 준비 상태다. 명시적인 사용자 교체 확인, 적용, 뒤로가기 보존은 화면 연결 단계에서 구현한다. 최종 분석은 기존 `LoadingStrategy.analyze`의 10픽 검증을 반드시 다시 거친다.

## 통합과 검증 경계

PC 서버의 기존 정적 파일 허용 목록과 공개 export 허용 목록에 새 모듈만 추가한다. 비공개 API 인증 경계나 화면 스크립트 실행 경로는 바꾸지 않는다. HTML에 검색 화면을 연결하거나 공개 사이트를 배포하지 않았다.

테스트: `python -m unittest -v tests_pregame.test_champion_baseline`.
회귀: 기존 gameplan backend/direction/content, loading strategy/HTTP.
프로젝트 무결성: `python scripts/verify_actual_evidence.py --prepare` 후 `python scripts/verify_actual_evidence.py --tests`.

검색/조회/전달 계약·Node 및 브라우저 UMD 경로·로컬 HTTP·export 검증은 실제 코드로 실행한다. 브라우저 UMD 검사는 Node vm 격리 컨텍스트 검사이며, 실제 Chromium UI/E2E 검사를 뜻하지 않는다. 기존 4명의 원문 재사용은 전술의 품질·효과 검증이 아니다.

## 남은 작업

1. 4명의 각 단계에 검토 가능한 5개 역할 행동과 본문·태그 근거 계약을 작성하고 별도 지원 승격 테스트를 추가한다. 현재 어댑터는 미래 확장 필드를 완성된 delivery로 승격하지 않는다.
2. 검색/포지션/자료 상태를 화면에 연결하고, 조합 이동 충돌의 명시적 확인·적용·취소를 구현한다.
3. 360/768/1440px·키보드·재시도·보기 전환·저장 결과 브라우저 회귀 후 배포와 실환경을 별도로 확인한다.
4. 카이사 등 신규 프로필과 다중 포지션은 자료 계약을 확장한 뒤 검증한다. 현재 프로필 스키마는 챔피언당 한 포지션이다.

완료 상태는 PR 및 검증 영수증으로 보고한다. 이 문서 자체를 전체 설계 AC-01~16 통과 증거로 사용하지 않는다.

# LoL Coach 프론트엔드 v2 구현·공개 검증 결과

기준: 2026-10-25 UTC. 기능계층 v2.0과 게임플랜 콘텐츠 v1.3은 별개다.

## 1. 전체 요약

챔피언 선택→상세→명시적 게임플랜 전달의 핵심 사용자 흐름을 구현·통합·배포하고 실제 공개 Chromium에서 확인했다. 전체 기능계층160행의 완성을 뜻하지 않는다. 모든 챔피언 상성·실시간 관측·충분한 파워 곡선·전술 효과 검증은 미완성이다.

제품 main: `ac48506c8f6493778d3fcdf675041d66f89c5390`. 제품 PR: [#140](https://github.com/kco994553-star/lol-coach/pull/140). 공개 artifact: `b0ec3cb8e15f0fa4cc6aa0454897317c23e979c9`. [챔피언 검색](https://kco994553-star.github.io/lol-coach/champions.html).

## 2. 현재 설계 상태

정본160행과 과거125행 연결을 보존했다. P0 탐색/변경창/부분 초안/전달/자료 상태 계약은 구현되어 검증되었다. P1의 정확 상대 결과 집계, 성장 자원과 관측 레벨 참고 자료는 제공하지만 전투력·현재 승리확률·인과 효과로 해석하지 않는다. 미확정 핵심 제품 선택은 없으며 미지원 데이터와 전술은 별도 지원 상태로 남긴다.

[160행 명세·코드 대응표](../../../docs/gameplan-content/frontend-v2-feature-matrix.json) · [입출력·화면·예외·검사 상세](../../../docs/gameplan-content/frontend-v2-implementation.md) · [통계 계약](../../../docs/gameplan-content/champion-statistics-v1.md).

## 3. 구현 결과

| 기능 ID | 실제 변경과 입출력 |
|---|---|
| 2.1.1–6 | 공식173명·이름/별칭·실제 관측 포지션→선택/상세. 최근8개 챔피언/포지션, 변경 창 적용/취소/Escape, 필터/스크롤/복귀 보존 |
| 2.2.1–5 | 기존4개 참고 프로필, 실제50경기 exact cohort→전체/특정 상대 최종 게임 승률·표본·Wilson95·검색/정렬 목록. 같은 포지션 상대만 통계 비교 |
| 2.3.1–5 | 종료5분 구간의 승리수/경기수 재합산, N100 미만 곡선 공백. 별도275경기의 자원 rate와 최초 관측 레벨 median/IQR/N. 패치별 추이는 미지원 |
| 2.4 / 2.5 | 단계별 자료 부족 상태, 바텀 파트너 문맥과 정글 별도 이름, 공식 스킬명과키. 새 상성 판단·룬/빌드/스킬순서 통계를 발명하지 않음 |
| 2.6.1–5 / 3.1.5 | 불변 intent→슬롯별 미리보기→명시 적용. 다른 픽/미입력/가정 보존, 중복/교체/revision 확인. 완성 시 strict10 재분석, 미완성은 별도 draft URL |
| 1.4.4 / 7 | 개인 기록에서 챔피언 식별자만 공통 상세로 연결. 개인표본을 공통 통계로 넘기지 않음. 기능·검증·배포 근거를 분리 |

주요 코드: `web_r4/champions.html`, `champion.html`, `champion-state.js`, `champion-picker.js`, `champion-page.js`, `loading-draft.js`, `loading.js`, `coach_v1/champion_stats.py`, `scripts/build_champion_statistics.py`. 정적 서버/exporter·공통 셸·CI·소스 결속도 함께 연결했다.

## 4. 검증 결과

- **전체 회귀:** 병합된 제품 main에서 `tests_pregame` **906개 PASS**,139.948초. [원본 로그](full-pregame-merged-main.log). 관련50개·전달87개 등의 별도 검사는 이906개와 중복 합산하지 않는다.
- **로컬 실제 브라우저:** 출시 후보 f30da7f와 제품 main의 애플리케이션 파일 동일성을 확인. **55항목·18PNG·107소스 해시 PASS**, 출처/PNG 해시를 root가 독립 재계산했다. [영수증](screens/runner.json).
- **기존 화면 회귀:** 현재 게임플랜·보존된 레거시·반응형·키보드·아이템 화면 Chromium PASS. [로그](gameplan-regression-six-nav.log).
- **독립 검토:** 데이터·전달 단위, 전달 수정 재검토, 브랜치 전체 명세/품질 검토와 마지막 수정 검토 모두 승인. [최종 검토](final-review.md) · [최종 수정 검토](final-fix-review.md).
- **원격 CI:** [PR #140](https://github.com/kco994553-star/lol-coach/pull/140)과 정확한 병합 main에서 regression/browser-regression/pregame 모두 SUCCESS. [MVP main](https://github.com/kco994553-star/lol-coach/actions/runs/40177148325) · [Pregame main](https://github.com/kco994553-star/lol-coach/actions/runs/40177148293).
- **배포:** [Native Pages40177555880](https://github.com/kco994553-star/lol-coach/actions/runs/40177555880) SUCCESS. 배포 전 기존91파일 해시를 모두 검증했다. 기존 확인된 프로 기록1개는 원본4228바이트 그대로 유지하고 기존 typed 계약으로 재검증했다. source의 초기화 placeholder로 대체하지 않았다. [기존 배포](previous-publication.json) · [보존 근거](preserved-pro-reference.json).
- **실환경:** 08:41:44–08:42:22 UTC에 공개 HTTPS의 main 일치·**100파일 해시·57브라우저 항목·29PNG** 확인.1440/390/320px·200%·입력/적용/취소/복귀·strict10·3단계 각5행동/문단 PASS. 정상 요청의 JS/console/HTTP 오류와 외부/provider 요청0.12개 비공개/구 경로 probe는404. [실환경 영수증](live-verification.json).
- **실경기 효과:** 미측정/N=0. 실제 Riot 계정/Windows 클라이언트·전술 효과를 검증한 것으로 세지 않는다.

## 5. 진행률

**전체45%·프론트엔드49%**는 관리용 추정이다(원값44.7%/49.4%).160개 기능행을0/0.5/1로 같은 가중으로 평가하고 미지원 해설·자료를 구현 완료로 세지 않았다. 화면의 부분 구현은 프론트엔드 축에서 따로 평가했다. 테스트 통과율·전술 정확도·실경기 효과와 무관하다. 이전35%/34%는 다른 heuristic 평가이므로 그대로 성과 차이로 해석하지 않는다. [행별 값·근거·분모](progress-assessment.json).

## 6. 문제점과 수정 이력

공유 #plan 복원 후 챔피언 화면을 다녀올 때 초안이 비는 문제, Back에서 가정이 되돌아가는 문제, 저장 불가/늦은 PC 응답의 이전 미리보기 적용 문제를 실제 브라우저로 재현한 후 수정했다. 원격 CI의 Playwright 실행 환경 누락을 고정버전 설치와 브라우저 경로로 보완했고, 기존5메뉴 검사를 정확한6개 라벨 검사로 강화했다. 모바일5열에6번째 메뉴가 두 번째 줄로 겹쳐 기존 버튼을 가리던 문제는6열로 수정했다. 검사 삭제·완화·skip 추가는 없다.

남은 자료 제약은16.20/16.20.1 보관 패치, outcome50/position50/growth275의 다른 모집단,4개 REFERENCE_ONLY 프로필, 모든 승률 구간의 N100 미달이다. 프로 참고 자료의 이전 갱신 실패 상태도 보존했다. 누락된 내용과 실시간 정보를 확인 사실로 바꾸지 않았다.

## 7. GitHub·Notion 반영

[#137](https://github.com/kco994553-star/lol-coach/pull/137)의 문서 결속 실패를 수정해 정상 병합했고, [#138](https://github.com/kco994553-star/lol-coach/pull/138)을 최신 main·439개 관련 검사·독립 검토 후 정상 병합했다. [#139](https://github.com/kco994553-star/lol-coach/pull/139)의 기능계층을 유지하며 #140으로 제품을 통합했다. 이 결과 기록의 PR은 별도 결과 동기화이며 동일 제품을 다시 배포하지 않는다.

Notion 기존 [관리자](https://app.notion.com/p/403f975df2e881bb9e5be4f6d1dbaba8)·[상세](https://app.notion.com/p/403f975df2e8814ba9bfcd3a05d22b4d)·[그래프](https://app.notion.com/p/404f975df2e881beae11e44680a1fa91)·허브4페이지를 갱신·재조회했다. 기존ID/자식/과거 원문을 보존했고, root 독립 재조회에서 같은 main과45%/49%·자료 조건을 확인했다. [영수증](notion-sync-report.json).

## 8. 남은 작업

- **P0:** 핵심 공개 사용자 흐름에 알려진 차단 버그 없음. 새로운 실제 자료·지원 범위를 추가할 때 같은 상태/보존 계약을 유지한다.
- **P1:** 기존 예산 안에서 정확 outcome 누적·중복 제거 상태, 충분한 시간구간 표본, 근거 있는 라인/운영/한타 상성 및 바텀2대2 해설·통계 확대. 기존50경기를275경기처럼 재사용하지 않는다.
- **P2:** 룬/아이템/스킬순서/시너지 조건별 자료, 실제 계정·복기·학습 연결, 허용된 실시간 필드 연결. 일반 플레이 지식을 모든 챔피언의 검증 전술로 표시하지 않는다.

## 9. 다음 자율 작업

다음 우선 작업은 기존 수집 예산과 권한을 유지하는 exact-outcome 누적 companion 계약·검사와 현재 실제 자료가 지지하는 전술 콘텐츠의 범위별 확장이다. 기존 원자료·사용자 결정·실패 이력·일정을 보존한다. 유료 호출이나 조회마다 AI 호출을 전제로 하지 않는다.

## 10. 페이지별 이미지와 승인 경계

[8개 페이지+변경 창의 데스크톱/모바일18PNG](screens/README.md) · [실제 공개 데스크톱](live-screens/desktop-champion.png) · [모바일](live-screens/mobile-champion.png) · [320px](live-screens/narrow-champion.png) · [적용 미리보기](live-screens/full-handoff-preview.png).

승인된 구현·테스트·PR·검증 후 병합/배포·문서 동기화는 수행했다. 핵심 제품 목적 변경·데이터 파괴·보안 경계 완화·유료 서비스 사용은 수행하지 않았으며 별도 승인 대상으로 유지한다.

작업 판단: 사용자 FAN-OUT 지시에 따라 파일 소유권으로 병렬 구현했고, 별도 worktree로 원본 main 작업 공간을 보존했다. 잘못 판단했을 때의 비용은 파일 충돌 및 작업 위치 정리이며, 공유 파일은 통합 담당만 수정해 통제했다. 기존 공개 프로 자료 보존은 검증된 최신 데이터를 초기화하지 않기 위한 배포 판단이며 원본 해시·typed 검증과 이전 artifact로 재현/복구할 수 있다.

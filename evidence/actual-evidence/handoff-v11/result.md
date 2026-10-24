# 2026-10-24 독립 코칭 본문 — 공개 반영 및 실제 화면 확인

사용자는 세 영역에서 다섯 행동을 빠르게 확인한 뒤, 이번 조합을 어떻게 풀어갈지 연결된 본문을 바로 읽고 그 아래에서 상황별 판단·예외·대안을 펼칠 수 있다. 본문 제목·밝기·문단 간격을 개선했다. 기본1+3/15행동을 유지하고 모바일320px 다중 초상화 가로넘침과 카드 제목 중복도 고쳤다.

- 콘텐츠 데이터: 기존 공식 한국어16.20.1 원문·버전·승인 상태 변경 없음. 입력 조합/역할과 실제 기술 기전을 참조한다. 새 판단은 전술 해석이며 공식 사실·상성검증으로 승격하지 않는다.
- 생성: `composeNarrative`의 단계별 pressure/cost/response/payoff/fallback과 근거에서 본문을 구성하고 동일 결과를 요약·상세에 반영한다. 기존 지원 매치업/수동 상대/구간별 습득/자원·웨이브·지원 가정이 우선한다. 단일10픽 조회나 외부AI 호출을 추가하지 않았다.
- 화면: `loading-presentation`은 판단을 새로 만들지 않는다. 기본본문과 상세는 같은 배열을 표시한다. 단계별 본문 제목,16px 밝은 본문·줄간격1.85,문단 간격,본문 아래 키보드/터치 펼치기,다중초상화 줄바꿈을 제공한다.
- 기능: 2.2.4 표시 요건 구현·검사·공개확인; 2.3.1/2.3.1.1/2.4.1/2.5.1/2.5.1.1 콘텐츠는 범위 내 개선한 부분 지원이다. 모든 상성·추가포지션 완료가 아니다.

## 실제 생성 결과와 변경 비교

[기준10픽 세 단계 전문과 콘텐츠 검토](../../../docs/gameplan-content/2026-10-19.md#기준10픽-실제-생성-본문-2026-10-24), [원본 입력·네 변형의 판단/본문/요약/상세](narrative-outputs.json).

라인전은 직스·카르마의 밀기/견제와 후퇴 비용 → 노틸러스·카이사 공격 거리 → 남은 폭약/둔화/보호·속박 → 막타 접근·귀환 시간을 연결한다. 운영은 직스 앞의 대치 비용 → 바이·노틸러스와의 경로·아리 합류 → 이득 전환·경로가 없거나 기회를 놓친 경우를 설명한다. 한타는 실제 아군 제어와 피해 연결 → 레넥톤·오리아나 공의 위험 → 후속 진입의 고립 비용을 설명한다.

럭스 교체는 속박 적중/실패와 보호 복귀, 룰루 교체는 보호막 시간·변이·함께 후퇴로 판단이 달라진다. 이즈리얼 교체는 직스 고유 W/E·포격 대치를 제거하며 새 우열은 미확인이다. 바꾸지 않은 레넥톤/오리아나 위협은 유지한다. 같은 팀 다섯 사용자 관점의 팀 결과 일치를 검사했다. 이 평가는 실제 출력을 읽은 AI 콘텐츠/코드 검토이며 전문가 검증이 아니다.

## 검사·병합·배포를 구분한 증거

| 구분 | 실제 결과 |
|---|---|
| 구현·검사 SHA | `4cddd1934f7e56c79dfcececc54c313399e6002b` |
| 자동검사 | [source binding](narrative-source-binding.json), 영향103 PASS·원본 보존/승인 보호 PASS |
| 로컬 화면 | [full Chromium](narrative-browser.json), PC/공개하위경로·기존 basic/edge/조건/v1.1/신규본문 PASS; [인게임 화면](narrative-game-info-browser.json)도 PASS |
| 통합 | [PR125](https://github.com/kco994553-star/lol-coach/pull/125) 정상 병합 → main `a8f3bc1ffa080823ee707cf6492a5444f9d7916f`; [PR required3](narrative-pr-ci.json) / [main required3](narrative-main-ci.json) SUCCESS |
| 배포 | artifact `6334985c76677d003a8c44effac1be5e7a057c2d`; [Pages40048002506](narrative-pages-ci.json) build/deploy/report SUCCESS |
| 공개 실환경 | [HTTPS90파일](narrative-public-https.json)·root/build-info/pro/riot PASS; [실제1440/390/320](narrative-public-browser.json) 기본15행동/본문·상세일치·키보드·새로고침·가로넘침 PASS, 페이지오류0 |
| 효과 | 전술 정확도/전문가검증/실전효과 미검증, N=0 |

[모바일 라인전 실제 화면](public-viewport-390-lane.png) · [운영](public-viewport-390-operations.png) · [한타](public-viewport-390-fight.png). 전체 기본카드 캡처도 narrative-390-*.png로 보존한다.

중간 실패: 수동상대 무시·미습득기술·FARM/RECALL/NEAR덮어쓰기를 RED→GREEN; 고정R근거/룰루진입자 표현은 실제출력 리뷰 후 수정;320px초상화 overflow 실제실패 후CSS수정. 수정 중 export/최신예상 불일치는 고정SHA로 재실행했다. 미추적실행cjs의 bounded inventory실패는 scratch 이동/허용증거 저장으로 해결했고 규칙을 완화하지 않았다. 초기PR CI는 최신push로 cancelled되었고 성공으로 계산하지 않았다.

재사용/미실행: 기존 source-bound CI가 무관한 과거pilot/v2.3검사를 재사용·생략한다. 전체 과거suite는 이번에 재실행하지 않았다. 이전 인수의 PC2/v23바인딩1 실패는 해결 주장하지 않는다. 실제 라이브계정/WindowsLCU/전술효과는 미검증이다.

## 남은 범위·재개

바텀 동료 노틸러스/럭스/룰루/알리스타와 제한된 위협 관계를 다룬다. 나머지 조합은 짧은 기본계획과 한계를 유지하며 긴 일반문장으로 상세지원처럼 채우지 않는다. 다음 우선순위는 (1) 미지원 조합/포지션·반례 및 실제 이해도 검토, (2) 기존 계정→현재경기·부분픽/추천 연결, (3) 과거계획 버전·복기와 나머지 기능이다. 최신 사용자 본문 개선 지시를 먼저 수행했으며 기존 대기열을 삭제하지 않았다.

이번 범위에 사용자만 제공할 필수 입력은 없다. 별도예시 전문/스크린샷 원래10픽은 미확보로 남겼고 추정하지 않았다. 라이브 기능에는 안전한 서버Riot/실제LCU·허용필드 증거가 여전히 필요하지만 이번 본문과 수동플랜에는 영향 없다.

현재 결과 브랜치는 `work/coaching-narrative-results-20261024`. 최종 branch/SHA·미커밋/소유권 해제·결과PR CI는 canonical `work/main-execution-claim`의 최상단을 재확인한다. 결과전용 변경은 제품파일과 동일하여 재배포하지 않는다.

공개 재현: `ROOT=https://kco994553-star.github.io OUT=/tmp/lol-coach-narrative PUBLIC_PROXY="$HTTPS_PROXY" node < evidence/actual-evidence/handoff-v11/narrative-public-probe.md` (출력폴더·Node Playwright 필요, 기존proxy/CA유지). 로컬 전체검사: `python scripts/browser_loading.py`. 롤백은 PR125 제품변경 정상revert와 기존allowlist게시로 수행하며 사용자자료 마이그레이션·삭제는 없다.

---

이전 v1.1 인수 기록(이번 본문 지시 이전):

# v1.1 인수·게임플랜 기본 노출 결과

사용자는 상세를 열기 전에 우리/상대 팀 네 기준 비교와 라인전(정글은 초반 정글)·운영(중반 운영)·한타 각각의 행동5개와 코칭 이유를 읽을 수 있다. 넓은 PC는 세 열, 모바일은 같은 순서의 한 열이다. 상세·가정 변경·초기화·키보드·복귀는 같은 결과를 사용한다.

- 완료된 표시/관점 기능: 2.2.1.1, 2.2.4. 비교표2.2.1의 기본 노출 구현. 내용 범위는 여전히 조건부·부분 지원.
- 부분 개선: 2.2.3/2.3.1/2.3.1.1/2.3.3~7. 대기할 때 잃는 자원·주도권, 교환 조건과 대안·전환을 역할별로 설명한다. 카이사–직스는 양 서포터, 기술·레벨·자원·웨이브·호응 조건을 함께 다루는 필수 검사 사례다. 일반 전술 판단 체계의 완성을 주장하지 않는다.
- 기능 번호125개 현황은 기존 contracts/information-architecture-v1.md에 통합했다. 과거 REC-REQ·원문·보류·USER 결정·350후보·기존 할당량은 보존했다.

## 구현·검사·통합·배포 증거

- #122 HEAD5031980은 재구현 없이55개/원본/Chromium/원격필수3으로 검증하고 1f99329로 정상 병합했다.
- #123 구현 HEAD `1b6fbd936030e1344e008dae8bd047b7c5c6f216`; 최종102개 영향 검사 및 현행 source·원본·해시 보존 PASS. exact-source-tests.log, verification-summary.json.
- 독립 코드 검토에서 제목 스크롤, 호응 부재/정글 자원 게이트 문제를 재현·수정했다. RED 로그와 최종60개 GREEN 보존; 재검토 차단 없음.
- 구현 PR 필수3 PASS: pregame120714344359/regression120714344639/browser120714344813. 정상 병합 `d9f515c4a48ee17d024923059669a94daaf4386a`.
- 정확 product-main 필수3 PASS: pregame120715535081/regression120715535076/browser120715535117. source102와 바인딩, 실제 Chromium, 기존 보호 경로 확인. 과거 전체 검사 일부는 CI 설정에 따라 재사용/생략하며 이를 새 실행으로 세지 않는다.
- 기존 gh-pages에 artifact `4cc14ab3f4442252a564b7f7bf5ba1c0cbe357f0` 게시. native Pages40042463683의 build/report/deploy SUCCESS. 기존 자동 갱신의 최신 pro-dashboard.json과 riot.txt 바이트 보존. 기존 공개 allowlist90파일만 반영하고 다른 파일은 삭제하지 않았다.
- https://kco994553-star.github.io/lol-coach/ 공개 root·build-info·.nojekyll·90파일 SHA-256 일치 PASS(public-https.json). 실제 공개 1440/390/320에서4기준/15행동/줄글 기본 표시, 상세 일치·키보드·제목 가시성·복귀·새로고침·호응 가정/초기화 PASS(public-v11-result.json/캡처).
- 결과/Handoff만의 후속 PR은 제품을 다시 배포하지 않는다. 최종 결과 branch/SHA·CI·release는 공유 work/main-execution-claim 상단에 남긴다.

## 실패·미실행·근거 제한

전체 pregame778 실행은 **최종 검토 수정 전 dirty tree(기준1f99329)**에서3건 실패했다. 당시 dirty-tree 전체 해시는 미수집으로 기록했다. 해당3건은 변경 전 clean1f99329에서도 모두 재현했다: test_pc_coach의 held-advice/source-integrity 두 건, test_v23_binding의 preserved/bounded 검사 한 건. 최종 커밋 전체 suite PASS를 주장하지 않는다. 두 PC 테스트는 현재 공식 사실/가설 정책과 대조가 필요하고, 과거 v23은 현재 트리와 동결 범위가 달라 현재 actual-evidence 계약으로 분리 검증한다. 현재 보호 게이트를 완화하거나 과거 증거를 고치지 않았다.

초기 브라우저 probe 선택자 strict-mode 실패와 수정 전 제품 실패를 구분해 보존했다. 최종 실제 화면은 성공한 로그·캡처만 성공 증거로 사용한다.

픽은 현재 체력·마나·스킬 사용 여부·동료 호응의 관측이 아니다. 전술은 설계/기전 연결 가설; 우세 확률·승률·전문가 승인·실전 효과를 추가하지 않았다. 실제 코칭 N=0/accuracy=null. 실제 Riot 계정→현재 경기/Windows 연결, 모든 매치업/추가 포지션·핵심 스킬 중요도, 과거 경기별 완전한 전략 버전 연결은 미검증/미구현이다.

## 운영·재개점

기존 pro18:30KST/expert18:00KST/Riot12:17KST cron을 유지하고 실제 최근 scheduled 성공은 scheduler-runs.json에 기록했다. 작업 성공과 provider/자료 내용 승인은 구분한다. 일간 공식 변경/주간20~30내용/월간 범위 파이프라인의 완전한 구현·등록은 확인되지 않았다. 새 중복 스케줄을 만들지 않았다.

기존 전체 검사 중 공식CDN이16.21.1을 발견했다. 실제 manifest/해시는 official-change.json, 테스트 갱신 포인터는 별도 증거에 보존하고 제품 자료16.20.1은 원래 바이트로 유지했다. 아이템 의존 규칙을 재검토 대상으로 표시했다. 공식 기술 변경이나 새 패치 전술 승인은 추정하지 않았다. 인증 Riot/Gemini/영상/유료 호출은 하지 않았다.

다음 우선순위: (1) 계정→현재 경기의 서버 계약/화면/사용자 대응/신선도·응답 경합, (2) 미공개 픽·포지션 정정·추천, (3) 역할·스킬 선택/팀 모순·대기 비용 반례/공식 변경 검토, (4) 과거 계획 버전·복기·나머지 전적/도우미/학습. 코드는 다음 작업1도 아직 필요하며 외부 키만 추가하면 완성되는 상태가 아니다. 현재 환경에는 RIOT_API_KEY가 없고 공개 사이트는 정적 backend 미연결이다. 필요한 외부 입력은 안전한 서버 자격증명/실제 로컬 연결·허용 필드 증거, 미확보 원본ZIP·HTML이다.

## 재현

- 수동 사용: 공개 사이트의 계정 없이 게임플랜 → 실제 아군/상대10픽·사용자 포지션 → 생성. 예시 버튼은 예시로만 사용하며 현재 경기라고 표시하지 않는다.
- 로컬 실제 조작: `python scripts/browser_loading.py` (Python dependencies, Node Playwright, Chromium 필요). PC 격리 fixture와 공개 하위경로 export를 검사한다.
- 공개 조작: `mkdir -p /tmp/lol-coach-v11-public` 후 `ROOT=https://kco994553-star.github.io OUT=/tmp/lol-coach-v11-public node < evidence/actual-evidence/handoff-v11/public-probe.md`. 기존 환경 proxy/CA를 유지한다. Node Playwright가 필요하다.
- 결과 되돌리기: 제품 PR123 변경을 정상 revert하고 기존 public allowlist로 게시. 사용자 자료 마이그레이션·삭제는 없다. 프로 자동 갱신과 riot.txt는 그대로 보존한다.

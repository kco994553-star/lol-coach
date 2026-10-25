# 챔피언 티어·상대 탐색 — 실제 출고 결과

2026-10-25 UTC. 제품 PR [145](https://github.com/kco994553-star/lol-coach/pull/145)·[146](https://github.com/kco994553-star/lol-coach/pull/146)·[147](https://github.com/kco994553-star/lol-coach/pull/147) 정상 병합. 최신 기능 소스 `be0b83faf24db19a5f2ff05410c9c2ed979f33db`, 공개 artifact `9fc318cc6725e4e5ccb3fdf3be1c0e44a9590049`, native Pages [40197492425](https://github.com/kco994553-star/lol-coach/actions/runs/40197492425) SUCCESS. [챔피언 검색](https://kco994553-star.github.io/lol-coach/champions.html).

## 1. 실제 완료 범위와 미완성

기본 MASTER_PLUS(MASTER+GRANDMASTER+CHALLENGER), 개별10티어와ALL, 정확한 선택 범위·빈 자료·잘못된 URL 처리, 같은 포지션의 실제 대면 빈도순 상대, 출처 기반 조건부 어려움/수월함 최대5개씩, 상대5포지션별 A팀 최종 게임 승률 상·하위5개 기능을 구현·통합·게시·실제 브라우저 검증했다. 수동 비교는 고급 영역에 보존했고, 필터·상대·파트너·저장된 게임플랜·학습실 왕복을 유지한다. 전술 지식과 통계는 별도다.

실제 자료는 기존 CHALLENGER 시드 집단50경기다. 새 Riot 획득0, MASTER_PLUS/ALL은PARTIAL, 다른9티어EMPTY, 경기 당시 A의 티어UNKNOWN, 다른 역할 결과 원장0, 적격N20순위0(현재 최대쌍N6)이다. 숫자나5명을 임의로 채우지 않는다. 전체 티어의 실제 자료 확보는 미완료다. 성장275참고와 종료승패50을 합산하지 않는다.

기존 GP23는DONE41/PARTIAL3(23위협우선순위·26역할고유성·39구체성), 학습실4/20/80분류·29기존claim카드/연습·8링크영상 상태를 보존했다. 실제 수용 자막·시각 장면·전술 효과 검증N0는UNMEASURED다. 분류80을 콘텐츠80으로 세지 않는다.

## 2. 설계·데이터 계약

[계약](../../../contracts/champion-insights-v1.md), [실행대장](../../../docs/gameplan-content/champion-tier-opponent-implementation.md), [수집](../../../docs/gameplan-content/all-tier-collection-v1.md), [지식 출처](../../../docs/gameplan-content/champion-matchup-knowledge-v1.md).

티어는 현재 리그 수집 출발집단이며 전체 참가자의 당시 랭크/MMR을 증명하지 않는다. 범위의 unique hash 승패/N/Wilson95를 다시 계산하고, 중복·패치충돌·원장 누락은 보수적으로 처리한다. 맞역할 기존대면과 반대팀의 실제 관측역할 원장은 구별한다. 순위 최소N20, 상·하위 독립선택, 동률·중복을 공개한다. 이 승률은 A팀 최종 게임 승률이며 상대 때문에 졌다는 인과나 라인전/교전 승률을 뜻하지 않는다. 다른 티어로 대체하지 않는다.

인터넷 참고는5저자/5champ-role/45기록(39조건부 후보+6전체매치 참고)이다. 어려움/수월함은Caitlyn4/3,Ezreal3/2,Fiora5/5,Graves5/5,Yunara5/2. 같은 범주 이름순은 난도 순위가 아니다. 원저자 범주·한국어 요약·AI행동/제한조건을 구분하고, source/claim 계보를 연결한다. source26.x↔Riot16.20.1 대응과 해당 문단의 현행성은미검증이다. USER/전술승인으로 승격하지 않는다. 운영·한타·바텀2대2·그외 챔피언은 근거 부족 상태를 유지한다.

## 3. 기능 ID·수정 파일·입출력

- `2.1/2.2.2~5/2.6`: champion-state/page/insights JS, champion HTML/CSS, loading-draft 복귀 메타데이터. 입력은 챔피언·본인/상대 포지션·티어·상대·파트너·탐색 상태, 출력은 해당 범위의 통계·빈도·조건부 카드·명시적 게임플랜 전달이다.
- `2.2.2~5`: coach_v1/champion_insights.py·matchup_results.py·outcome_stats.py, 두 builder/공개 집계, 인증 POST `/dev/v1/champion/insights`. 입력 champion/position와 선택 tier/patch, 출력 범위·승패/N/CI·맞역할 빈도·상대 역할별 순위. 엄격한 요청키/패치/포지션 검증, 공개 allowlist·CSP·loopback 인증을 보존한다.
- `2.4.1/2.4.4/2.4.7`: champion_matchup_knowledge.py·config/champion_matchup_references.json·builder·공개JSON. 출처·단계·조건부 난도·해설·재검토 조건을 표시하며 별도 전술 엔진을 만들지 않는다.
- `7.2/7.4`: 기존 collector/policy/resolver/수집workflow 재사용.10티어·40슬롯 회전,650요청/300경기/40선수/1페이지/900초·첫401/403중단·public7일/private90일보존 유지. 익명 결과 동반자료와 별도 완전성 원장은 비공개다.

전체 제품 수정 경로는 [changed-files.json](changed-files.json), 파일별 실행/반례/완료 기준은 [실행대장](../../../docs/gameplan-content/champion-tier-opponent-implementation.md)과 테스트 영수증에 있다. PR137/138/139는 모두 병합 상태를 재확인했고,138의 기존 검색·기본 방향 백엔드를 재사용했다.

## 4. 실행한 검증

`python -m unittest discover -v -s tests_pregame`: 최신 변경 후 **1018개 PASS159.188초**,13:13:42–13:16:21UTC, CURRENT 전체 시작/종료SHA동일·변경0. [원본](dialog-fix/full-stable.json). 관련43개 자동검사, 신규36개/기존55개 브라우저, 독립 코드·CSS 검토, source guard·실제 두 projection 재생성 검사 통과. 두 번의 전체 PUBLIC 스테이징은 LOCAL_STAGING_NOT_LIVE로 기록한다.

최신 PR147와 정확mainbe0의필수 regression/browser-regression/pregame 모두SUCCESS. mainruns40196881621/40196881598; 최초제품145·수정146의CI와전체회귀도별도기록했다.

실제 HTTPS **13:26:14–13:27:04UTC**,109/109파일SHA=manifest=게시물,root/.nojekyll200,비공개14경로모두404. **71브라우저검사**(기존GP23/학습/실제공개Galio7/4/6왕복29 +티어/출처31 +반응형/터치11),4너비×CSS/글자200%의저장상대8조건,표ArrowRight6회,터치에뮬레이션3흐름 통과. 수치100.0%한줄·모든카드/컨트롤fit·변경창최초제목/닫기·유효후보후Apply·실제Tab/ShiftTab포커스·Escape원상태를확인했다. JS/console/HTTP/external/API/nonGET오류·요청0. [최종 요약](live-final/final-summary.json)·[원본 영수증](live-final/receipt.json).74PNG,그중페이지/주요영역9개.

실물 터치 장치·Safari/Firefox·실경기 전술효과·새 실제 영상 확보는NOT_RUN/UNMEASURED다. 실제 source outage/retry는 발생한 장애가 없어BLOCKED이며 가상으로PASS를 만들지 않았다.

## 5. 실패·반례 보존

첫전체1016개2FAIL(등록경로를미등록으로간주한음성fixture/이전패치가수집한도를소모하던실제Recall회귀)을보존하고,엄격한미등록거부와원래Recall검사를유지해수정했다. Wilson0/1끝값반올림·교차소스hash패치충돌·비명시cache패치pin·고급표CH우회도반례로수정했다.

공개af297/sourceb0는320CSS200에서폭436으로실패,다음e1/sourceb236은native변경창이화면위로벗어나실패했다. 첫wrap/reflow범위PASS후저장100.0%카드반례도보존했다. 모두최종PASS로덮어쓰지않았다. pointer+.focus뒤키입력없이focus-visible을요구한검사오탐은별도HARNESS_CONTRACT_FALSE_POSITIVE로분류하고,실제Tab/ShiftTab뒤같은solid2px조건을검사한다. [첫공개실패](live-initial-responsive-failed/receipt.json)·[두번째공개실패](live-second-dialog-failed/receipt.json)·[반응형수정](responsive-fix/report.md)·[변경창수정](dialog-fix/report.md).

## 6. GitHub·Notion·진행률

세 제품PR145/146/147은정상병합했고브랜치보호/필수CI를우회하지않았다. 최신공개sourcebe0/artifact9fc/native40197492425는실제검증완료다. 기존READY프로참고와실패갱신상태를typed검증후그대로보존했으며SHA64d4830149af4ba515ac3b5e6c745629f80d00b0b7e416c30a5e27d4afd8c6e3동일,신규provider요청0. 이전게시물e1은직전배포기록(확대창실패),기능추가전검증기준47e241d는별도보존한다.

Notion챔피언·관리자·상세·그래프4페이지append/readback통과. 원문prefix·기존child URL/ID는보존했다. [동기화 영수증](notion-sync.json)·[읽기 쉬운 동기화 기록](notion-sync.md).

160개동일가중0/0.5/1 관리추정: **전체74/160=46.25%,프론트엔드84/160=52.5%**. 새 부분근거는2.4.1/4/7에각0.5만반영,모두PARTIAL/full_feature_acceptance=false다. 나머지157행·FE점수·IA125역사매핑을보존한다.2번영역은19/32=59.375%,FE25/32=78.125%. 이는테스트통과율·전술정확도·실제전티어확보율이아니다. [산정 근거](progress-assessment.json).

## 7. 남은 작업과 재개 위치

- P0출고/왕복/UI/자료부족처리는검증된범위내완료. 정본기능대장·보호원자료·source/claim·원래6.1~6.6을유지한다.
- P1실제수집BLOCKED:저장된키허용창은2026-10-16에끝났고신규키probe/HTTP403을이번에관측했다고주장하지않는다. **GitHub보안설정의갱신Riot키와명시한허용기간**을확보한뒤같은무료예산내전티어/결과원장을누적해N20순위를재평가한다. 개인계정/전체모집단·당시티어UNKNOWN구분을계속한다.
- P1자율가능:인터넷프로필확장·패치대응/문단현행성확인·선택상대상세/운영/한타/바텀2대2와GP23고유성보완·허용된영상설명/장면자료확보. 근거없는값/승인/고유판단을만들지않는다.
- P2룬/아이템/시너지·다른영역연결·실물touch/추가브라우저. 누적private상태1만건한계는failclosed이며장기수집전파괴없는보존회전이필요하다.
- 유료서비스,권한완화,데이터파괴,중요전술승인변경은실행하지않았고필요시별도승인사항이다. 일반구현/검증/문서화는기존승인범위에서진행한다.

## 8. 페이지별 이미지

[6개메뉴와챔피언상세/상성/상대역할의독립PNG목록](page-images.md). 실제공개UI캡처이며게임플랜이미지의입력은수동예시,복기는기존공개프로기록이다. 실제전술/실경기효과검증으로세지않는다. 별도네이티브애플리케이션구현은추가하지않았다.

결과문서브랜치`work/champion-tier-results-20261025`는이제품과별도문서/증거통합이며동일앱재게시를요구하지않는다. 출고전상태는[당시기록](prerelease-result.md)에보존한다.

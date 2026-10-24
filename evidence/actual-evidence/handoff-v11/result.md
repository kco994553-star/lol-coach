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

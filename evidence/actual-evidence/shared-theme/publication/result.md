공통 디자인과 조작을 실제 웹에 반영했습니다.
시작 화면부터 대시보드·10픽·전략 상세·전술 연습까지 연결했습니다.
PC·모바일의 공개 화면과 실패 시 대안을 확인했습니다.
개인 계정 API와 실제 Windows 연결은 여전히 미연결입니다.
영상 한도·기존 근거·보류 이력·실전 코칭 N=0을 유지했습니다.

[사용 URL](https://kco994553-star.github.io/lol-coach/) · [작업 상태](https://kco994553-star.github.io/lol-coach/status.html)

시작→계정 없이 경기 전 준비 또는 프로 참고→대시보드의 **이번 판 준비하기**→10픽/내 챔피언/포지션→요약·상세·조건 비교 순서입니다. 하단 카드는 입력 전에는 수동10픽으로 안내하고 실제 분석 후 라인전(웨이브 우선)/운영/한타 해당 영역으로 이어집니다. 개인 계정 검색은 로그인·소유권 인증이 아니며 공개 정적 사이트에서는 연결 불가와 수동 재시도를 표시합니다. 계정 API를 호출한 성공 증거는 이번 범위에 없습니다.

| 공통화한 부분 | 실제 동작 |
|---|---|
| coach-theme.css | 의미별 색·한글 서체·rem 크기·여백·모서리·테두리·주요/보조/비활성·hover/focus/pressed/selected/error. 페이지별 색상표 대신 공유 토큰. 지도 의미별 색은 보존 |
| coach-shell.js | PC 사이드바/모바일 메뉴·고정 링크·동일 선 아이콘·현재 메뉴·skip link·키보드/Escape/터치/바깥 닫기 |
| hero-art.json + 기존 로더 | 공식 기본 아리·케이틀린 출처/해시/화면별 자르기. 새 세션 무작위1장, 새로고침 유지, 다른 후보 선다운로드 없음. 수동 변경 시 입력/지역/초점/스크롤/폼 크기 유지 |
| 세 전략 카드 | 동일 비율·테두리·그라데이션·글자. 사용자가 허용한 AI 가상 일러스트1회 생성, WebP221432bytes. 각 카드 AI 표시·전체 클릭/키보드·실제 영역 연결. 실제 게임화면·공식 원화·전술 근거로 취급하지 않음 |
| 검색/빈 상태 | 입력/조회중/오류/재시도, 이미지 실패·목록 비어 있음에도 검색/게스트/수동 준비. 가짜 티어·승률·코칭 점수 없음 |

시작 화면만 변경하지 않았습니다. 아래는 실제 공개 HTTPS에서 저장한 화면입니다.

| 화면 | PC1440×1000 | 모바일390×844 |
|---|---|---|
| 시작 | [화면](desktop-shared-home.png) | [화면](mobile-shared-home.png) |
| 대시보드 | [화면](desktop-shared-dashboard.png) | [화면](mobile-shared-dashboard.png) |
| 수동10픽 | [화면](desktop-shared-prepare.png) | [화면](mobile-shared-prepare.png) |
| 전략/조건 | [화면](desktop-shared-analysis.png) | [화면](mobile-shared-analysis.png) |
| 전술 연습 | [화면](desktop-shared-practice.png) | [화면](mobile-shared-practice.png) |
| 카드→라인전 | [이동 결과](desktop-entry-lane.png) | [이동 결과](mobile-entry-lane.png) |
| 카드→운영 | [이동 결과](desktop-entry-operations.png) | [이동 결과](mobile-entry-operations.png) |
| 카드→한타 | [이동 결과](desktop-entry-fight.png) | [이동 결과](mobile-entry-fight.png) |

같은 뷰포트의 [PC 변경 전후](desktop-before-after.png) / [모바일 변경 전후](mobile-before-after.png).
첨부 원본을 그대로 보존하고 해당 화면 부분만 분리한 [PC 시안 비교952×688](desktop-reference-comparison.png) / [모바일 시안 비교282×690](mobile-reference-comparison.png). 원본 첨부 해시·분리 좌표·실제 공개 화면 해시는 screen-comparisons.json에 기록했습니다. 시안의 네이비·보라색·일러스트·입력·카드 구도를 따르되 공식 기본 원화, 명확한 미연결 안내, 접근성 메뉴와 터치 크기를 사용합니다. 픽셀 동등성을 주장하지 않습니다. 좁은 모바일에서는 카드 목록을 세로 스크롤합니다.

실제 검증: 45개 영향 단위검사와 source-bound PC/mobile Chromium 증거를 재사용했고 변경된 이미지 자르기를 추가로 확인했습니다. 새 세션 두 후보/세션 유지/첫1장 요청, 마우스·키보드·tap, 입력/초점/스크롤 유지, 이미지실패/빈목록/API실패/재시도/게스트, 페이지별 공통 스타일, 실제10픽→구간→지도 확대/닫기, 메뉴·200%글자·가로 넘침 PASS. 기존 웨이브·교전·리스크·공식 스킬이름(키)/소유자·카드/단계/미니맵 회귀는 필수 CI로 확인했습니다. 독립 검토의 남은 중대한 문제0. 최종 actual HTTPS probe의 page error0/HTTP error0/provider 요청0.

게시: PR72·73 정상 병합. 제품 source main **84003a4efc9fcb9de180bfa5c44f16e668bf5c7c**, artifact **96447216db5903508643eb79220d34c74e3bf702**. PR72와73 각각 feature 및 post-main의 필수 pregame/regression/browser-regression 모두 SUCCESS. Pages run **39032180568**의 build/report/deploy 모두 SUCCESS. manifest47파일+root/build-info/.nojekyll 실제 HTTPS/해시 일치. 이전 프로 참고5경기 JSON은 이전 공개본과 바이트가 같습니다. deployment.json 및 CI JSON/log, public-browser.json, source-binding.json이 상세 증거입니다. 준비만 하고 게시하지 않은 중간 export는 disposition 기록으로 구분했습니다.

완료하지 않은 범위: 공개 개인 계정 API 실제 연결·개인화 코칭 분석, 전술의 실경기 유효성, 실제 Windows 롤 클라이언트 실증. 30초 이해 미측정·실전N0·WindowsBLOCKED_EXTERNAL. 기존 조언7/AUTO30/HOLD20/USER0/Frozen350·원문·보류·실패·수동 입력/Windows 실행 경로 보존. 신규 전술 재작성0/추가 경기 수집0/Gemini0/10월17일 영상3/3 유지/유료 전환0. 이미지 생성1회는 사용자 허용 장식 제작이며 코칭 근거가 아닙니다. 같은 성향/조건의 이전 전술 결과를 새 디자인이 검증된 전략으로 승격하지 않습니다.

다음 외부 의존 작업은 기존 근거 질문3개와 허용일의 영상 진단·실제 Windows 연결이며 이번 프론트엔드 완료와 분리합니다. 사용자가 새로 수집하거나 전수 검토할 일은 없습니다. 결과·Handoff 전용 후속 PR에는 제품 소스를 바꾸거나 같은 Pages 산출물을 다시 게시하지 않습니다.

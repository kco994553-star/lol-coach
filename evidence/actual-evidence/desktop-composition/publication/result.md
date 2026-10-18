데스크톱 화면의 큰 빈 공간과 카드 겹침을 수정했습니다.
창을 세로로 늘려도 검색창·배경 변경·세 카드가 한 묶음으로 유지됩니다.
검색창은 한 줄, 계정 없이 준비 버튼은 그 아래로 분리했습니다.
시안에 맞춰 공통 SVG 아이콘을 정리했고 운영 지도 아이콘은 그대로입니다.
배경25개·실제 게임 카드3개·기존 분석과 수동 입력을 보존했습니다.

URL: https://kco994553-star.github.io/lol-coach/

[PC 화면](composition-1440x900.png) · [시안 크기952×688](composition-952x688.png) · [세로 긴 데스크톱980×1800](composition-980x1800.png) · [모바일 화면](mobile-shared-home.png)

재현 전980×800/980×1800의 첫 화면 높이는800/1800px였습니다. 수정 후에는 같은980폭에서 모두684.36px로 유지됩니다. 입력창과 검색 버튼은48px 한 줄이며, 세 카드가 각 칸 안에 들어오고16px 간격이 보입니다.952×688 시안 프레임에도 카드3개가 들어옵니다. 사용자 기기 자체에서 실행했다는 뜻은 아니며 실제 Chromium CSS 뷰포트 재현입니다.

고정된 화면 높이/그림 비율로 내용을 자르지 않고 실제 콘텐츠가 높이를 정합니다. 검색 오류/재시도도 정상 흐름에서 늘어나며 준비 버튼을 덮지 않습니다. 검색의 로그인·소유권 인증 아님/공개 API 미연결 안내를 유지했습니다. 로고·홈·라인전/연습의 검·한타 인원·준비·복기·검색/새로고침·메뉴 아이콘을 공통 컴포넌트로 관리하며 운영 지도 SVG 경로는 변경하지 않았습니다.

영향 단위20 PASS, 독립 검토 중대한 미해결0. 실제 공개 HTTPS PC1440/mobile390 및980×800/1800,952×688,1920×1080,701×900,282×690에서 구도/카드 간격/검색 행/오류 확장과 기존25hero/session/input/focus/scroll/failure/retry/guest10pick/3card destinations/maps/zoom를 확인했습니다. pageerror0/HTTPerror0/provider0. 독립 검토는200% 글자와 PC 인증 오류·키보드 초점도 확인했습니다. 원래 실패·변경 전 화면과 중간 기록은 ../에 보존합니다.

PR79 feature+post-main 필수 pregame/regression/browser-regression 모두 SUCCESS. 제품 source main **ab17d505546f63d339851cb672c2e7db298a84c9**, Pages artifact **4b7fb944b5e8b910e6c5cc69c5ce36207ba5d614**, native Pages run **39083506747** 실제 build/report/deploy SUCCESS. 공개 manifest74파일+root/build-info/.nojekyll HTTP/해시 일치. 이전 프로 참고 JSON과 이미지 데이터는 그대로입니다. 결과/Handoff 후속 PR은 제품/Pages를 다시 게시하지 않습니다.

Gemini/이미지 생성/신규 경기/유료 전환0. 기존 웨이브·교전·성향·공식 스킬이름(키)·지도·Windows/수동 경로·조언7·AUTO30/HOLD20/USER0·Frozen350·원문/보류/실패/원장을 보존했습니다. 실전 코칭N=0·30초 이해 미측정·WindowsBLOCKED_EXTERNAL 유지. 기능과 디자인 검증을 전략 정확도로 해석하지 않습니다.

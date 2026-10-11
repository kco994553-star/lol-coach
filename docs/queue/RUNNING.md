# v1.6 실행: 9개 카드와 전문가 발언 후보

현재 게임플랜은 선택한 5개 포지션을 모두 지원하며 카드 ①~⑨를 표시합니다. 이전 단계 A
설명은 아래에 보존했습니다. 자료가 없는 칸은 미확인이고, 합성 그래프는 실제 계획에 표시하지 않습니다.

기존 실행 명령으로 서버를 켠 뒤 `http://127.0.0.1:8765/experts`에서 같은 접속키를 사용합니다.
**영상 요약 입력**에 공개 YouTube URL·제목·채널명·확인한 영상 길이·발언 시각·짧은 의역 요지를
입력합니다. 챔피언·포지션·단계·발언자·날짜를 확인하지 못했다면 미확인으로 둡니다. 고급 JSON 입력도
접힌 영역에 있습니다. 시각 링크로 원문을 열어 맥락·조건·반례를 확인한 뒤 사용자가 승인·거절합니다.
입력과 가져오기는 자료 노트와 EXPLORATORY 후보만 만들고 승인하지 않습니다.

자동 수집은 기본 브랜치의 **Free expert video collection** Actions에서 수동 또는 일정 실행합니다.
`YOUTUBE_API_KEY`, `GEMINI_API_KEY`는 GitHub Secrets UI에 등록하고 값을 게시하지 않습니다.
사용자가 승인한 15개 채널 중 활동 재확인 대상 1개는 비활성화하며 클템은 제외했습니다.
공식 무료 조건·무료 전용 프로젝트·보존된 할당량 기록을 확인한 뒤 최대 2개 영상을 처리합니다.
실패·취소 예약도 해제하지 않습니다. 입력 미확인은 BLOCKED_EXTERNAL, 비용 조건은 BLOCKED_PAYMENT입니다.
전체 영상·자막·모델 원문 응답은 공개 저장소나 artifact에 보관하지 않습니다.

Main이 `expert-public-safe` artifact의 상태와 짧은 요약을 검증한 뒤 `data/expert_claims/`에 게시합니다.
로컬 앱은 기본적으로 이 폴더를 읽거나 `--expert-claims-dir private/expert-claims`로 명시한 폴더를 읽습니다.
시작 알림은 새 후보 수만 표시합니다. 수집 성공은 발언 사실성·코칭 정확도 검증과 별개입니다.
통계 대조에는 명시적 수치 기준과 맞는 실제 Q15 자료가 필요하며, 없으면 측정 불가 또는 표본 부족입니다.
일치해도 규칙 승인이나 인과관계 증명이 아닙니다. Riot ID는 사용자 확인 전 사용하지 않습니다.

Q15 보조 경기 결과 자료가 있으면 기존 명령에 `--outcome-data private/outcome-data.json`을 추가합니다.
라인 상세의 접힌 표는 **그 시간에 끝난 경기의 결과**와 Wilson 95% 구간을 보여주며 그 시점의 강함으로
해석하지 않습니다. 획득 실패를 0으로 바꾸지 않습니다.

전문가 import journal은 `<기본 DB>.research.sqlite.expert.sqlite`에 저장됩니다. 앱을 종료한 뒤 기본·
Research·expert journal DB를 함께 복사해 백업합니다. 기존 backupformat1에는 새 journal이 포함되지
않습니다. 원문 자료와 journal을 각각 다른 시점으로 복원하면 안전하게 보류될 수 있습니다.

검사: `python scripts/verify_experts.py` 및 `python scripts/browser_experts.py`.
브라우저 환경은 아래 검사 설명을 따릅니다. API 실제 호출 없이 형식·누락·할당량·출처·승인 경계를 검사합니다.

---

# 경기 전 게임플랜 실행

무료 로컬 실행이며 자동 게임 수집이나 경기 중 코칭을 시작하지 않는다.
Python 3.12 환경에서 `python3 -m pip install -r requirements-r3.txt` 실행 후:

```bash
python3 -m coach_v1.pregame_server --db private/workbench.sqlite --port 8765 --token-file private/token.txt --max-body-bytes 1000000 --max-observations 100 --max-actions 100 --max-scenarios 100 --max-comparisons 100 --max-pending-jobs 10
```

토큰 파일이 없으면 서버가 새 토큰을 만들고 파일 경로를 알린다. 파일의 토큰으로
`http://127.0.0.1:8765/pregame`에 연결한다. 토큰은 개인 자료 접근용이므로 게시하지 않는다.
기존 화면과 모든 기존 API는 같은 서버의 `/`에서 계속 사용한다.

1. 예시 입력 또는 양 팀 10명, 내 포지션·챔피언·슬롯을 입력한다. 실제 확인하지 못한
   포지션·룬·소환사 주문·패치는 미확인으로 둔다. 정적 데이터 버전을 경기 패치로 옮기지 않는다.
2. 입력을 저장한 뒤 게임플랜을 생성한다. 7영역 카드에서 저장 입력·규칙 버전·출처·제외 이유를 연다.
3. 픽·패치·포지션 또는 승인 지식이 바뀌면 과거 계획은 만료된다. 새 저장 revision으로 다시 생성한다.
4. 후보를 읽고 정확한 출처·패치 범위·반례를 검토한다. 실행 가능한 후보의 패치 범위를
   확인한 후 원문 JSON을 편집·미리보기·후보 등록할 수 있다. 승인은 사용자가 웹 버튼에서 직접 한다.
   AI는 후보를 REVIEWED로 만들지 않는다. 승인 지식 또는 게임 패치가 없으면 해당 칸은 미확인이다.

내 위치에 맞는 역할·라인/동선·한타 근거가 없으면 그 칸만 미확인이다. 기본 쿨타임도
서로 다른 두 출처·패치·유형·승인된 교전 조건이 충족될 때만 경기 전 표시된다.
현재 후보에는 확정한 쿨타임 값이 없으며 남은 쿨타임·경기 중 타이머는 제공하지 않는다.

## 백업과 재개

기존 backupformat1은 기본 DB와 Research DB만 보존한다. 새 경기 전 입력·계획·정확한
재시도 기록은 `<기본 DB>.pregame.sqlite`에 별도로 저장된다. 새 화면의 **경기 전 내보내기**를
함께 보관한다. 원본 픽창 참조를 포함했다면 먼저 기존 백업을 복원한 뒤, 비어 있는 경기 전 DB에
새 내보내기 파일을 복원한다. 기본·Research 자료가 없으면 원본 참조 검증에 실패하거나 계획이
만료될 수 있다. 일반 JSON 입력으로 지식 승인이나 원본 수집 사실을 만들어낼 수 없다.

게임 PC 수집은 [Q10 절차](Q10_GAME_PC_CAPTURE.md), 현재 상태는 [대기열](QUEUE.md)을 따른다.
영상·게임 계정 인증·결제 없이 할 수 있는 구현은 진행했으며 실제 수집·복기·성능 측정은
요구된 실제 자료가 도착해야 재개한다. 테스트 통과를 코칭 정확도로 표시하지 않는다.

## 검사

```bash
python3 scripts/verify_pregame.py
NODE_PATH=/path/to/node_modules CHROMIUM_EXECUTABLE=/path/to/chromium python3 scripts/browser_pregame.py
```

브라우저 검사는 실제 앱의 미승인/패치 미확인 흐름과 격리된 합성 REVIEWED 조회 fixture를
구분한다. 합성 fixture는 실제 지식 승인을 저장하지 않으며 코칭 성능 검증이 아니다.

## v1.4 graphs and conditional movement
After trusted main workflow collects anonymous files, download riot-power-aggregate artifact (public-safe only, retention7days). Inspect power status; BLOCKED_EXTERNAL is not a dataset with usable zero statistics. Start existing server with --power-data private/power-data.json and, if produced, --movement-data private/movement-data.json. No raw match uploads, credentials or identifiers are required by the UI. Actual server refuses SYNTHETIC aggregate files; isolated browser runner labelsTEST. Match your manually verified game patch and collection tier. Minute-only movement statistics do not create phase roles without exact reviewed sources/verified stage annotations.

Development keys expire24hours. For personal project key, register project at https://developer.riotgames.com/ and review Riot policy/product scope; no paid service required. Update GitHub repositorySecret RIOT_API_KEY through GitHub Secrets UI; never paste it into repository/issues/logs or command arguments. Secret enumeration permission failure does not imply missing key.401/403 cannot distinguish expiry/authorization/unsupportedpath; preserve collection reason and correct portal access/key before rerunning.

Five-position9-card smoke test: python scripts/verify_pregame.py; python scripts/browser_pregame.py; python scripts/browser_v13.py. Run evidence-preservation verifier python scripts/verify_mvp_experts.py alone after other evidence-producing jobs finish; concurrent new evidence intentionally triggers its conservation gate. Use CHROMIUM_EXECUTABLE=/usr/bin/chromium locally when Playwright's bundled binary is absent. Existing per-job CI environments avoid concurrent proof mutation.

## First real collection — 2026-10-11

PR14 is merged; actual main Actions run38116217243 failed acquisition with Riot403 on the first request. The workflow completed and kept a safe status artifact, but no usable statistics were acquired. Check developer portal key/project access and update GitHub SecretRIOT_API_KEY via the Secrets UI; rerun the main workflow. A403 response does not establish key expiry by itself. Do not load a blocked receipt as zero statistics. CLI artifact download returned403, then the GitHub connector fallback succeeded; the anonymous blocked receipt passed strict validation.

Current product has nine cards; the earlier seven-card instructions above describe the preserved StageA version. Use the five-position nine-card smoke commands above for current acceptance. User approves knowledge in the web UI; AI cannot approve it. Real coaching accuracy remains unmeasured.

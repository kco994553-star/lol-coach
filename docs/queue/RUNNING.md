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

Five-position9-card smoke test: python scripts/verify_pregame.py; python scripts/browser_pregame.py; python scripts/browser_v13.py. Run evidence-preservation verifier python scripts/verify_mvp.py alone after other evidence-producing jobs finish; concurrent new evidence intentionally triggers its conservation gate. Use CHROMIUM_EXECUTABLE=/usr/bin/chromium locally when Playwright's bundled binary is absent. Existing per-job CI environments avoid concurrent proof mutation.

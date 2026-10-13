# v2.0 로컬 사용

저장소 루트에서 Python3.11 이상을 사용합니다.

```text
python -m pip install -r requirements-r3.txt
python -m coach_v1.pregame_server --db private/work.sqlite --token-file private/app-token.txt --port 8765 --max-body-bytes 12000000 --max-observations 1000 --max-actions 100 --max-scenarios 100 --max-comparisons 100 --max-pending-jobs 10
```

접속키는 `private/app-token.txt`를 로컬에서 읽어 앱 연결 칸에 넣습니다. 채팅·Git·공개 로그에 올리지 않습니다. 토큰과 자체 경기 원본은 개인 폴더에 보존합니다. Windows에서는 개인 폴더 NTFS 권한을 본인 계정만 접근하도록 설정해야 하며, 앱의 chmod는 NTFS 보호를 검증하지 않습니다.

- `http://127.0.0.1:8765/review-queue`: 지식 후보를 한 개씩 검토. 패치가 미확인이면 자동으로 실행 지식을 만들지 않습니다. 편집해 조건·패치를 확인한 뒤 직접 승인합니다. 나중에 목록과 다음20개 묶음에서 재열 수 있습니다.
- `/pregame`: 경기 전 입력·저장·9개 카드.
- `/statistics`: 같은 패치에서 상위 티어와 내 티어대를 선택해 비교. 아직 없는 티어·기본곡선 자료는 미확인.
- `/postgame`: 내 경기·타임라인 원본 선택 → 내 챔피언 참가자 확인 → 로컬 저장 → 복기. CLI와 앱은 기본적으로 같은 `private/postgame/`를 사용합니다. 원본은 Git에 커밋하지 않습니다.
- `/experts`: Gemini 앱에서 만든 타임스탬프 요약을 수동 후보로 입력. 출처·시간·발언 조건을 직접 확인합니다. 자동 요약 실패 중에도 사용 가능합니다.
- `/setup`: PC 한 번 수집·OBS·게임 시계 기준점 안내.

기존 실제50경기 집계는 `data/riot/2026-10-11/`의 gzip으로 보존돼 있습니다. 원본 경기 JSON이 아니라 익명 집계입니다. 압축을 개인 작업 폴더에 풀고 `--power-data PATH/power-data.json --movement-data PATH/movement-data.json --outcome-data PATH/outcome-data.json`을 서버 시작 명령에 추가하면 기존자료를 볼 수 있습니다.

새 일정 수집 artifact의 `power-패치-티어.json`, `progress-패치-티어.json`을 같은 개인 폴더에 놓고 `--power-data-dir PATH`를 추가합니다. 같은패치·티어 중복 파일이 다르면 시작을 거절합니다. 집계/원본 파일을 섞지 마세요. 기존단일파일과동일scope의 새 누적 결과를 함께 지정하지 않습니다.

실제 Riot 기록 수집은 U1(Riot ID·서버)·U3(키 갱신)가 있어야 합니다. 키는 `RIOT_API_KEY` 로컬 환경 설정으로 공급하며 명령 인자·채팅에 넣지 않습니다. `python scripts/collect_personal_matches.py --riot-id "닉네임#태그" --server KR --private-directory private/postgame --count 1`은 현재 KR만 지원합니다.

R2 일정은 U3 확인 후 `key_renewed=true` 수동실행 또는 저장소변수 `RIOT_KEY_RENEWED=true`로 켭니다. U2 현재 티어는 `RIOT_USER_TIER`에 설정합니다. 무료기준·20/초·100/2분·첫401/403멈춤은 유지합니다. 개발용 키가 다시 만료되면 그 실행을 멈추고 키만료 사용자귀속과관측HTTP를 분리해기록합니다.

게임 중 실시간 코칭·쿨타임 추적은 제공하지 않습니다. 기록의 분 단위 한계·영상 미확인·코칭 정확도 미산정은 계속 표시됩니다.

## 사용자가 제공한 프로 기준 선수

`config/pro_reference_players.json`의 원문명단(25명·백업9명·ShowMaker 추가계정)을 사용합니다. `/postgame`의 “25명 명단·백업 규칙 보기”에서 확인할 수 있습니다. 프로계정 주인·당시티어/판수는 사용자확인이고 앱의독립검증은 아닙니다.

키갱신 후 **로컬에서만** `python scripts/collect_pro_reference.py --config config/pro_reference_players.json --private-directory private/pro-reference`를 실행합니다. 최초성공 Account-V1조회 이후 PUUID를비공개캐시에고정합니다. 띄어쓰기/특수문자/대소문자를 바꾸지 않고, 추가계정은같은선수로합칩니다. 원본·PUUID를Git/Actionsartifact에올리지않습니다.

출력한 익명기준집계파일을 명시적으로 서버의 `--pro-reference-data private/pro-reference/reference-data.json`에 지정하면 별도 “선택한 프로 선수” 누적 총량 그래프가 표시됩니다. 파일명은 실제 CLI 출력경로를 확인합니다. 이 표본은 일반티어집계와 다르므로 합치지 않습니다. 부족한 표본은 그대로 미확인입니다. “포지션 비중이 낮음”의기본운영기준은 최근수집솔로랭크표본의50%미만이며 CLI에서바꿀수있고 교체사유가 기록됩니다.

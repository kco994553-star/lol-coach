# v2.0 로컬 사용

저장소 루트에서 Python3.11 이상을 사용합니다.

```text
python -m pip install -r requirements-r3.txt -r requirements-private-cache.txt
python -m coach_v1.pregame_server --db private/work.sqlite --token-file private/app-token.txt --port 8765 --max-body-bytes 12000000 --max-observations 1000 --max-actions 100 --max-scenarios 100 --max-comparisons 100 --max-pending-jobs 10
```

접속키는 `private/app-token.txt`를 로컬에서 읽어 앱 연결 칸에 넣습니다. 채팅·Git·공개 로그에 올리지 않습니다. 토큰과 자체 경기 원본은 개인 폴더에 보존합니다. Windows에서는 개인 폴더 NTFS 권한을 본인 계정만 접근하도록 설정해야 하며, 앱의 chmod는 NTFS 보호를 검증하지 않습니다.

- `http://127.0.0.1:8765/review-queue`: 지식 후보를 한 개씩 검토. 패치가 미확인이면 자동으로 실행 지식을 만들지 않습니다. 편집해 조건·패치를 확인한 뒤 직접 승인합니다. 나중에 목록과 다음20개 묶음에서 재열 수 있습니다.
- `/pregame`: 경기 전 입력·저장·9개 카드.
- `/statistics`: 같은 패치 CHALLENGER 기본 곡선과 남은 표본을 확인합니다. 부족한 동일 구간에만 GRANDMASTER 보조를 표시합니다. 본인 티어는 필요하지 않습니다.
- `/postgame`: 프로 기준 사례의 단계별 기본 위치와 막힘 신호를 봅니다. 본인 경기 가져오기는 선택 기능이며 원본은 로컬 `private/postgame/`에만 둡니다.
- `/experts`: Gemini 앱에서 만든 타임스탬프 요약을 수동 후보로 입력. 출처·시간·발언 조건을 직접 확인합니다. 자동 요약 실패 중에도 사용 가능합니다.
- `/setup`: PC 한 번 수집·OBS·게임 시계 기준점 안내.

기존 실제50경기 집계는 `data/riot/2026-10-11/`의 gzip으로 보존돼 있습니다. 원본 경기 JSON이 아니라 익명 집계입니다. 압축을 개인 작업 폴더에 풀고 `--power-data PATH/power-data.json --movement-data PATH/movement-data.json --outcome-data PATH/outcome-data.json`을 서버 시작 명령에 추가하면 기존자료를 볼 수 있습니다.

새 일정 수집 artifact의 `power-패치-티어.json`, `progress-패치-티어.json`을 같은 개인 폴더에 놓고 `--power-data-dir PATH`를 추가합니다. 같은패치·티어 중복 파일이 다르면 시작을 거절합니다. 집계/원본 파일을 섞지 마세요. 기존단일파일과동일scope의 새 누적 결과를 함께 지정하지 않습니다.

본인 Riot ID·티어 입력은 필요하지 않습니다. 선택적으로 본인 기록을 가져올 경우에만 로컬 환경의 `RIOT_API_KEY`와 `collect_personal_matches.py`를 사용합니다.

일정 수집은 사용자 확인 개발 키의 24시간 창 안에서 CHALLENGER를 수집합니다. GRANDMASTER는 같은 패치의 부족한 구간만 보조합니다. 만료된 창에서는 호출하지 않으며 첫401/403이면 해당 실행을 멈추고 사용자 지시의 키 만료 귀속과 관측HTTP를 분리해 기록합니다. 수동 실행도 `key_renewed=true`와 동일 제한을 따릅니다. 무료기준·20/초·100/2분은 유지합니다.

게임 중 실시간 코칭·쿨타임 추적은 제공하지 않습니다. 기록의 분 단위 한계·영상 미확인·코칭 정확도 미산정은 계속 표시됩니다.

## 사용자가 제공한 프로 기준 선수

`config/pro_reference_players.json`의 원문명단(25명·백업9명·ShowMaker 추가계정)을 사용합니다. `/postgame`의 “25명 명단·백업 규칙 보기”에서 확인할 수 있습니다. 프로계정 주인·당시티어/판수는 사용자확인이고 앱의독립검증은 아닙니다.

로컬에서 수집하려면 `python scripts/collect_pro_reference.py --config config/pro_reference_players.json --private-directory private/pro-reference`를 실행합니다. 최초성공 Account-V1조회 이후 PUUID를비공개캐시에고정합니다. 띄어쓰기/특수문자/대소문자를 바꾸지 않고, 추가계정은같은선수로합칩니다. 원본·PUUID는 Git과 공개 평문 artifact에 올리지 않습니다. 신뢰된 Actions는 암호화된 비공개 캐시만 보존하며 공개 출력은 익명 집계입니다.

출력한 익명기준집계파일을 명시적으로 서버의 `--pro-reference-data private/pro-reference/reference-data.json`에 지정하면 별도 “선택한 프로 선수” 누적 총량 그래프가 표시됩니다. 파일명은 실제 CLI 출력경로를 확인합니다. 이 표본은 일반티어집계와 다르므로 합치지 않습니다. 부족한 표본은 그대로 미확인입니다. “포지션 비중이 낮음”의기본운영기준은 최근수집솔로랭크표본의50%미만이며 CLI에서바꿀수있고 교체사유가 기록됩니다.

## 2026-10-13 결정 이후 기본 경로

본인 Riot ID·티어는 필요하지 않습니다. 기존 본인 경기 수집 절차는 선택 기능으로 남아 있고 기본 복기는 지정한 프로25명과 백업의 기준 사례입니다. PC에서 /review-queue에 접속하면 원문·조건·통계를 나란히 봅니다. /statistics는 CHALLENGER를 우선하며 표본이 부족한 동일 구간만 GRANDMASTER 보조로 표시합니다.

프로 기준 사례는 신뢰된 수집의 공개 안전 artifact에 있는 reference-cases.json만 가져옵니다. --pro-cases-data PATH/reference-cases.json을 서버 명령에 추가하세요. 저장소 data/pro_reference/2026-10-13/reference-cases.json이 있으면 기본으로 읽습니다. 원본 경기·PUUID를 넣는 칸이 아닙니다. /postgame은 내 경기 입력 없이 기본 위치 분포와 막힘 신호의 관측 사례를 보여줍니다. 단계는 시간/첫타워 이벤트로 정의한 운영 구간이고 전술 단계 자체는 미확인입니다. 벗어남이나 신호를 잘못으로 판정하지 않습니다.

경기 전9개 카드의 상대 권리 표시는 검토 지식·명시적으로 검토한 권리 진술·표본을 갖춰야 위험/안전이 됩니다. 근거가 없으면 미확인입니다. 현재 REVIEWED0이므로 모두 미확인인 것이 정상입니다. 선택적 --opponent-rights-annotations PATH/annotations.json은 기존 검토된 주장에 수동 연결한 sidecar를 읽습니다. 이 파일이 지식 승인이나 통계 증거를 대신하지 않습니다.

기본 영상 경로는 /experts의 수동 타임스탬프 요약입니다. 자동화는 명시적 단계별400 진단과 별개이며 API200만으로 재개하지 않습니다. 키는 Secret/로컬 환경에만 보관하고 채팅에 올리지 않습니다.


## 현재 실제 자료 — 2026-10-13

기본 실행은 data/riot/2026-10-13의 실제275경기·16.20 CHALLENGER 곡선과 data/pro_reference/2026-10-13의 실제87경기 프로 기준 사례를 자동으로 읽습니다. 별도 Riot ID·티어·영상 입력이 필요하지 않습니다. PC에서 /statistics는5포지션 ×3기본 자원 곡선과 챔피언 차이 곡선을 구분해 보여줍니다. 기본33분 구간은 표시 기준을 통과했고 후반8분 구간은 추가표본추정/미확인으로 남습니다. 기본곡선이 표시되어도 특정챔피언의 부족한점까지 충분하다는 뜻은 아닙니다.

기본 통계파일은 원래852개 ROLE_POPULATION 집계만 값 변경 없이 분리해 조회를 빠르게 합니다. 전체6090개 집계(매치업 포함)는 archives/full-power-16.20-CHALLENGER.json.gz와 manifest.json에 원본해시를 보존했습니다. 매치업까지 필요한 경우 개인 작업 폴더에서 전체파일을 풀고 --power-data로 지정합니다. 기본투영과전체원본을 동시에같은패치/티어로넣으면 충돌을거절합니다. 16.19와16.20을합치지않습니다.

프로 화면은5포지션·3운영구간의 위치분포와 기록된신호를 보여줍니다. 경기단위 좌표CI가 넓은 항목은 미확인이며 신호 자체는 잘못이나원인판정이 아닙니다. 영상은 미확인이고 웨이브·보이지않는상대·스킬상태를 추정하지 않습니다.

공식YouTube예시 진단은429(프로젝트할당량초과)로끝났습니다. /experts의 수동타임스탬프요약이 기본경로입니다. 구간/형식추가나재시도는하지않았고 자동수집은보류입니다. 사용자는기존EXPLORATORY후보를 원문·조건과함께 직접검토합니다.

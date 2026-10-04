# R5 — 실제 자료 접근 대안과 영상 복기 준비

2026-10-04 KST. 위험 DEEP. 이전 Design/R3/R4 소스와 증거를 보존했다.

## 무엇을 해결했나

사용자 PC 접근 하나에 전체 개발을 묶어 둘 필요는 없다. 두 공개 경로를 실제 실행했다.

| 경로 | 확보·실행 결과 | 사용할 수 있는 범위 |
|---|---|---|
| Riot 공식 Live Client 응답 예제 | HTTPS 다운로드·원본 해시·필드 진단 완료 | 입력 형식·누락·변환 검증. 실제 경기 표본으로 간주하지 않음 |
| PekinWoof 공개 YouTube 영상 | 페이지 확인, 자동자막 1,230구간 확보, 주제 후보33개 색인 | 검토할 시점 찾기와 해설 주장 분리. 화면·코칭 정확도 검증 아님 |
| 사용자 PC의 로컬 클라이언트 | 공식 인증서 자동 다운로드 성공. 현 환경 endpoint 연결 불가 확인 | 게임 실행 PC에서 수집할 준비 완료. 실제 수신은 미완료 |

공식 출처: https://developer.riotgames.com/docs/lol
공식 예제: https://static.developer.riotgames.com/docs/lol/liveclientdata_sample.json
공식 인증서: https://static.developer.riotgames.com/docs/lol/riotgames.pem
영상: https://www.youtube.com/watch?v=CejHqSces8Q
확인한 예제에는 게임 시간이 0이고 최대 체력도 0인 값이 있어 의미 검증 필요로 표시했다.
공개 예제의 PATCH, 관점, 종료 여부는 추정하지 않는다.

## 바로 실행

coach_intake는 Python 표준 라이브러리만 사용한다. Python3.10+면 pip/API 키/계정/결제가 필요 없다.
명령의 출력 폴더는 새 경로여야 한다. 실패 기록을 지우지 않고 새 폴더로 재시도한다.

```sh
python3 -m coach_intake sample --out private/sample-001 --max-bytes 2000000 --timeout-seconds 15
python3 -m coach_intake inspect private/sample-001/raw.json --out private/audit-001.json --max-bytes 2000000
python3 scripts/collect_local.py
```

Windows에서는 저장소의 collect_windows.cmd를 실행한다. Python이 있으면 인증서 준비→한 번 수집→진단까지 진행한다.
Python이 없으면 설치 필요를 알리고 끝난다. 관리자 권한이나 시스템 인증서 저장소 변경은 없다.
Windows 실제 실행은 미검증이며 동일 Python 수집 경로는 Linux에서 실행했다.
이 앱은 사용자의 원격 PC를 자동으로 켜거나 게임에 로그인하지 않는다.

결과 폴더에는 원본(raw.json), 출처 기록(receipt.json), 식별자 값을 내보내지 않는 진단(audit.json), 실행 상태(status.json)가 생긴다.
실패 시 status.json을 남긴다. 원본과 접속 정보는 private 아래에 두며 커밋하지 않는다.
공개 표본 다운로드는 환경의 정상 HTTPS 프록시 사용을 허용한다. 게임 endpoint는 프록시 없이 고정 루프백으로만 연결한다.
리디렉트·잘못된 인증서·크기 초과·중복 JSON 키·비유한 숫자를 거부한다.
해시 일치가 출처의 진위를 증명하는 것으로 표시되지 않으며 모든 자료는 코칭 비활성 상태다.

## 영상 경로

영상 시간과 게임 시간은 다르다. 편집·일시정지·여러 경기·중계 전환 때문에 하나의 고정 시간차로 환산하지 않는다.
개인 화면(POV)인지 관전자 화면인지 장면별 검증이 필요하다. 관전자 시야를 플레이어가 알았던 정보로 넣지 않는다.
자막은 해설 주장으로만 저장한다. 승패를 알고 난 사후 설명을 과거 판단의 근거로 합치지 않는다.

현재 구현은 시간표시 자막의 키워드 색인이다. 이벤트 탐지, 전체 영상 자동 인식, 게임 실력 평가가 아니다.
영상 플레이어는 이 브라우저에서 00:00에 머물러 실제 프레임 검토를 확인하지 못했다. 자막 확보는 별도로 성공했다.
원문 전체 자막·동영상은 저장소에 재배포하지 않는다. 출처·해시·시점·주제·짧은 독자적 요약만 보존했다.

```sh
python3 -m coach_intake video transcript.txt --video-id CejHqSces8Q --out private/video-index.json --max-bytes 2000000
python3 scripts/video_report.py private/video-index.json --out private/video-report.html
```

현재 후보 보고서: evidence/r5/video-report.html. 자막 언어는 en이며 영어 키워드만 지원한다.
색인33개는 조사 후보 수이고 코칭 정확도나 중요한 장면의 전체 포착률이 아니다.
원본 자막은 공개 영상에서 다시 확보할 수 있지만 자동자막 변경 가능성이 있어 SHA-256로 버전을 구분한다.

## 다음 단계와 실제 의존성

공개 자료를 이용한 개발은 계속 가능해졌다. 실제 화면 기반 복기 검증에는 재생 가능한 영상 프레임이 필요하고,
사용자 본인의 자동 수집 검증에는 LoL이 실행된 PC가 필요하다. 둘을 같은 blocker로 취급하지 않는다.
현재 확보 자료만으로 실제 경기 코칭 gate를 해제하지 않는다.

추가 확인: 지원 미디어 다운로드도 60초 시간 초과. 영상 화면 검증은 미완료로 보존했다. 통합 검사82/82, 보호 회귀9/9 통과(실제 LoL 검증 제외).

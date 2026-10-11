# 실제 Riot 익명 집계 — 2026-10-11

기본 브랜치의 [수집 실행 38135582016](https://github.com/kco994553-star/lol-coach/actions/runs/38135582016)에서 얻은 실제 50경기입니다. 패치는 **16.20**, 티어는 **현재 챌린저 목록에서 고른 수집 출발점**을 뜻합니다. 경기 참가자 모두가 당시 챌린저였다는 뜻은 아닙니다. 다른 패치·티어로 합치지 않습니다.

세 gzip 파일은 Actions artifact11700808186의 검증된 익명 집계 JSON을 내용 변경 없이 압축했습니다. [manifest.json](manifest.json)에 원본/압축 파일 SHA256, 스키마, 데이터 digest, 실행 HEAD가 있습니다. 키·PUUID·소환사명·Riot ID·원본 경기 JSON은 없습니다. 경기 ID 해시는 중복 제거용이며 재식별 불가능성을 보증하지 않습니다.

저장소 루트에서 다음 명령으로 기존 로컬 서버에 연결합니다. 압축을 푼 파일도 집계 자료뿐입니다.

```bash
mkdir -p private/riot-20261011
for name in power-data movement-data outcome-data; do gzip -dc "data/riot/2026-10-11/$name.json.gz" > "private/riot-20261011/$name.json"; done
python3 -m coach_v1.pregame_server --db private/workbench.sqlite --port 8765 --token-file private/token.txt --max-body-bytes 1000000 --max-observations 100 --max-actions 100 --max-scenarios 100 --max-comparisons 100 --max-pending-jobs 10 --power-data private/riot-20261011/power-data.json --movement-data private/riot-20261011/movement-data.json --outcome-data private/riot-20261011/outcome-data.json
```

`/pregame`에 접속키로 연결한 뒤 직접 확인한 게임 패치를 입력하고 통계 티어 CHALLENGER를 선택합니다. 통계 파일의 패치를 현재 경기 패치로 자동 복사하지 않습니다. 정확한 패치·챔피언·포지션 자료가 없거나 정밀도 기준을 충족하지 못하면 미확인입니다. 맞라이너 표본이 부족하면 같은 포지션 표본 평균으로 대체하고 비교 집단을 표시합니다. 0분 누적 차이를 분당 값으로 나눌 수 없으므로 혼합 비교 화면에서는 해당 점을 그리지 않습니다.

1749개 power cohort에서 45930개 점 중 6963개가 운영 정밀도 기준을 충족했습니다. 이는 전투력·코칭 정확도 검증이 아닙니다. 레벨·아이템 표시는 비인과 기술 통계와 후보 빌드입니다. 이동 자료는 분 단위 좌표이며 단계 annotation이 없어 단계별 전술은 계속 미확인입니다. 종료 시간별 승률은 그 시간에 끝난 경기의 결과이며 그 시점의 강함이 아닙니다.

실제 production 서버와 Chromium의 근거·표본·CI·대체·패치 누락 검증은 [실제 브라우저 증거](../../../evidence/queue/resume-20261011/cause-real-browser/runner.json), 통계·개인정보 독립 검토는 [검토 기록](../../../evidence/queue/resume-20261011/riot-actual-independent-review.md)에 있습니다. 픽 입력은 브라우저 검증용 수동 사례이며 실제 현재 픽창/게임 플레이로 주장하지 않습니다. REVIEWED 지식 승인과 코칭 성능 평가를 대신하지 않습니다.

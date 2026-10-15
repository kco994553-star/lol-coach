# Queue v2.3 — 귀환·저체력 관측 계약

사용자 2026-10-15 V1–V6 지시를 구현한다. v2.1 완료 증거는 재사용한다.
Main이 공통 계약·HTTP·화면 투영을 소유한다. 기존 USER 결정·Frozen 계약·350개
후보·30개 자동 검토 패킷과 그 검토 증거는 변경하지 않는다.

## 입력과 자료 경계
- PC 로컬 경기 전 계획과 경기 후 관측만 제공한다. 게임 중 자동 지시 금지.
- `recall_stats.extract_match(match, timeline, *, population)`은 비공개 Match-V5
  원본을 받아 익명 경기 단위 관측을 반환한다. population은 CHALLENGER 또는
  PRO_REFERENCE이며 합치지 않는다. 패치·챔피언·포지션별로 분리한다.
- `recall_stats.build_dataset(observations, *, population, retrieved_at)`과
  `validate_dataset(data)`은 `recall-observations.v1` 엄격 익명 집계를 만든다.
  계정·PUUID·Riot ID·원본 match ID·원문 payload는 공개 출력에 없다.
- `recall_stats.recall_view(data, *, champion, position, patch)`는 정확한 챔피언
  표본이 5경기 미만이면 같은 패치·모집단·포지션 전체, 이것도 5 미만이면
  UNKNOWN을 반환한다. 5는 출력 최소 표본 규칙이며 통계적 충분성 보장이 아니다.

## 측정 규칙
- 첫 구매 묶음은 게임 시작 120초 이후 첫 ITEM_PURCHASED 묶음(30초 이내)
  으로 정의한다. 이는 시작 아이템을 분리하는 분석 규칙이며 좋은 귀환 시각이 아니다.
  그 전 사망이 관측되면 첫 귀환 표본에서 제외한다. ITEM_UNDO는 취소한다.
- 구매 시각은 귀환 완료의 대리 관측이다. 구매 없는 귀환·정확한 귀환 시작·
  웨이브·의도는 UNKNOWN이다. 골드는 직전 수신 프레임의 currentGold이며
  구매 순간 골드가 아니다. 중앙값·Q1·Q3·유효 n·누락 n을 별도 표시한다.
- 저체력 기준은 수신 프레임 health/healthMax <=0.30, 결과 창은 120초다.
  이는 사용자 요청을 실행 가능하게 하는 분석상의 구간 정의이며 게임 권장 수치가
  아니다. 출처는 Match-V5 타임라인 필드와 본 계약이다. 0.20/0.40 및
  60/180초 민감도 결과도 보존하여 단일 경계로 정답을 판정하지 않는다.
- 저체력 후 사망 전 구매와, 다음 프레임에 라인 위치가 실제 관측된 잔류를
  구분한다. 관측 불충분/사망 후 구매/정글 포지션/라인 위치 불명은 따로 제외한다.
  라인 구간은 기하학적 관측 규칙을 자료에 공개하고 웨이브 상태로 해석하지 않는다.
- 결과는 이후 창 내 본인 사망, 상대 라이너의 다른 라인 위치에서의 킬 관여,
  상대 팀 방패·정글 오브젝트 이벤트 건수다. 관측된 관여만 센다. 사건 위치가
  없거나 시간창 끝까지 수신되지 않으면 알려진 0으로 대체하지 않는다.
- 선귀환 뒤 같은 창의 상대 방패·다른 라인 관여·오브젝트도 비인과적 집계다.
  신호는 FIRST_RECALL_PRIORITY_GAP / LOW_HEALTH_STAY_DEATH /
  LOW_HEALTH_RECALL_OPPONENT_ROAM이며 확정 실수나 의도 판정이 아니다.

## 공식 아이템과 분류·조언
- `official_items.refresh_if_due()`는 최신 공식 Data Dragon item.json ko_KR을
  URL·버전·SHA256과 함께 버전별 보존한다. `items_response(patch)`는 실제
  입력 패치 불일치를 표시하며 불일치 가격으로 목표 골드를 만들지 않는다.
- 첫 구매 목표 골드는 실제 구매 묶음의 관측 최빈 아이템과 공식 gold.total로
  계산한다. 사전에 가진 부품/할인을 모르면 완성 아이템 가격 합계는 참고값으로
  표시하고 구매 순간 필요 골드라고 단정하지 않는다.
- 웨이브 처리 속도·저체력 유지력·마무리 능력은 별도 후보다. 공식 설명의
  광역/이동/사거리/처형 등은 출처 사실이며 빠름/높음 등의 전투 성능은 해석이다.
  별도 작성·근거·반론·기계 검사를 통과하기 전에는 미검토 가설 또는 UNKNOWN.
- 귀환/저체력 전술은 상황/할 것/하지 말 것/상대 권리/무효 조건/근거/패치 형식,
  원문 없는 일반 롤 상식을 AUTO_VERIFIED로 승격하지 않는다.

## PC 통합과 검증
- POST `/dev/v1/pregame/recall-reference`는 엄격한
  `{champion,position,patch,opponent_champion}` 요청과
  `{schema_version:'recall-reference.v1',own:[view],opponent:[view],items,markers}` 응답이다.
  공개 익명 자료만 `data/recall/YYYY-MM-DD/{pro,challenger}/recall-data.json`에서 읽는다.
- PC 카드의 선택적 `graph`는 `{title,units,points:[{minute,value}],
  markers:[{minute,who:'OWN'|'OPPONENT',label}]}`다. 기존 Q15의 관측 자원
  차이 그래프이며 세로선은 해당 모집단 첫 구매 묶음 중앙값이다. 개인 예측/강세가 아니다.
- 기존 pc-coach.v1 cards에 RECALL/LOW_HEALTH 섹션을 추가한다. 카드 3줄·
  펼침 상세·근거 수준·패치 경고·원문 링크/해시를 유지한다.
- 챔피언과 맞라이너의 첫 귀환 분포·구매 표본과 시각 marker를 함께 반환한다.
  UNKNOWN도 사유를 표시한다. 진행 중 게임이면 전술과 집계를 노출하지 않는다.
- 이번 변경의 단위/통합/실제 Chromium 흐름만 검증한다. 완료 v2.1을 재검증하지 않는다.
  실제 Windows/LCU 검증만 BLOCKED_EXTERNAL. 테스트 수는 코칭 정확도가 아니다.

# REC 시나리오별 R3 구현 연결

PARTIAL은 전체 시나리오 통과가 아니다. 동결된 기대동작 원문과 runtime_status는 변경하지 않았다.
테스트별 실행 결과는 evidence/r3/*.log, 입력·실행 코드 버전은 같은 시각 JSON에 기록한다.

|기존 설계 사례|구현 범위|상세|
|---|---|---|
|REC-SC-001|PARTIAL|미확인/계보 검사; 실제 교환 판단·미니언 모델 미구현|
|REC-SC-002|PARTIAL|cast_event로 readiness 자동 생성 금지; 실제 재사용 규칙 미구현|
|REC-SC-003|PARTIAL|과거 last_seen 보존; 현재 위치 추정 미구현|
|REC-SC-004|PARTIAL|CS로 웨이브 자동 추론 금지; 실제 미니언 처리 미구현|
|REC-SC-005|PARTIAL|대안·정보/비용 비교 기반; 다이브 전투 모델 없음|
|REC-SC-006|PARTIAL|판단 마감/정보 요청; 귀환·경로 adapter 없음|
|REC-SC-007|NOT_IMPLEMENTED|실제 매복/로밍 의도·경로 평가 없음|
|REC-SC-008|PARTIAL|후보 계약/만료·비교; 팀 반응 모델 없음|
|REC-SC-009|NOT_IMPLEMENTED|한타·시너지 실제 평가 없음|
|REC-SC-010|PARTIAL|목표 명시·임의 생존 우선순위 없음; 넥서스 모델 없음|
|REC-SC-011|NOT_IMPLEMENTED|draft collector/gameplan 없음|
|REC-SC-012|PARTIAL|중복/지연/충돌/관점 및 source group; DB 없음|
|REC-SC-013|PARTIAL|관점·당시 지식 cutoff; 실제 영상 가시성 검증 없음|
|REC-SC-014|PARTIAL|의도 UNKNOWN·결과 평가 분리; 실제 실행 위반 평가 없음|
|REC-SC-015|PARTIAL|patch/EXPLORATORY 차단; 지식 저장/검토 워크플로 없음|
|REC-SC-016|PARTIAL|실제 모드 차단·입력 텍스트 미실행; AI 서비스 없음|
|REC-SC-017|PARTIAL|CLI 파싱/덮어쓰기 거부; upload/job/delete API 없음|
|REC-SC-018|PARTIAL|frozen 보호 회귀·synthetic 명시; real sample/release 미검증|

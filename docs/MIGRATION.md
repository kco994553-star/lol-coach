# 보존 코어와 v1.0의 전환 경계

legacy/backend는 과거 ZIP의 보존본이며 v1.0 제품 엔진이 아니다. 원본 바이트 수정 없음.

|확인한 기존 구현|v1.0 계약|전환 작업|
|---|---|---|
|FAVORABLE+CS_APPROACH → PUNISH|접근과 의도, 충분성과 우위 분리|관찰·의도·판단 축 추가|
|정글 UNKNOWN이면 P3 cap/CHASE INVALID|근거별 가능한 상황·이탈·손익 비교|legacy 결과 직접 승계 금지|
|CONFIRMED_FAR는 유효시간 없음|last_seen와 현재 상태 분리|field validity·clock·provenance 구현|
|Wave EVEN 등 기본값|미관찰은 UNKNOWN|명시 observation envelope 구현|
|return_path 입력을 판단에 사용하지 않음|지형/실제 이탈 별도|행동별 필수 입력 및 sensitivity 구현|
|ActionType 16개, 정의는 9개|후보 vocabulary와 구현 지원 표시|지원 여부·실행 가능성 검증|
|trace에는 기회/permission만|행동별 근거·반례·비용·만료|새 trace 계약 구현|
|기본 WAIT 추천|대기 비용도 비교|유일 최적해를 강제하지 않는 selector 구현|

위 차이를 패치로 원본에 숨기지 않는다. 향후 별도 v1 엔진 namespace 및 adapter를 만들고,
legacy fixture는 역사적 동작을 보존하는 테스트로만 유지한다. legacy 실패를 v1 정답으로 바꾸지 않는다.
R1 32/32 원본 재현 불가. REC-CORE-*는 새로 관찰하는 동작이며 GF-001/002 원본으로 이름 붙이지 않는다.

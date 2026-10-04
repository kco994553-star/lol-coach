# R7 Reference State 작성·검증 절차

실제 프레임 없는 현재 10유형 슬롯은 NOT_ESTABLISHED다. 다음 내용은 실행 준비 프로토콜이며 수동 확인을 했다는 증거가 아니다.

1. 장면 출처/원본 hash/영상 시간/게임 시간/patch/경기 식별 관계를 기록한다. 영상과 게임 시간을 일괄 offset으로 추정하지 않는다. 한 장면의 결과를 알기 전 결정 직전 t를 고정한다.
2. PLAYER_INFORMATION_STATE를 먼저 작성한다. 당시 HUD·minimap·본 화면에서 알 수 있는 observation만 기록하고 시야 밖 위치는 UNKNOWN. 보이는 것과 실제로 주의를 기울였다는 것은 구분한다. 참고 화면은 source ID+frame timestamp+영역+관점+가림 여부를 연결한다.
3. 별도 GROUND_TRUTH_STATE는 관전자/이후 화면 등을 사용하되 player reference에 복사하지 않는다. 결과는 post_hoc_outcome_note에만 적는다.
4. 필요한 각 field에 값/단위/상태/원천시각/취득시각/시계기준/patch/가시성/출처hash/annotator/불확실성/lineage를 남긴다. 최소 정밀도는 각 action의 결론 변경 가능성으로 판단하며 임의 픽셀→게임 좌표 변환은 금지한다.
5. Intent는 `{hypothesis, supporting_observation_refs, contradicting_observation_refs, alternatives, confidence, author}`로 별도 작성한다. confidence는 근거 설명이며 임의 숫자 점수를 붙이지 않는다. "Good play/Bad play/Intentional bait/Tilted"는 observation 값이 아니다.
6. 운영자 reference를 pipeline output을 보기 전에 확정한다. 그 다음 구조화만으로 만든 state의 값뿐 아니라 누락·시점·관점·freshness를 비교한다. reference와 pipeline 모두 UNKNOWN이면 정확한 state 추출 성공으로 세지 않는다.
7. 불일치는 raw path/hash부터 조사한다: 원시 파싱/추출 오류→EXTRACTION_ERROR; 시계/관점/상태 연결 오류→STATE_ERROR. 근거가 부족하면 EVIDENCE_GAP. 뒤 단계 실패가 이전 실패를 덮어쓰지 않게 보존한다.
8. 현재 신뢰 가능한 저비용 source로 결론이 정해지면 추가 Vision을 생략한다. 미해결 변수 중 행동 결론을 바꿀 것에만 정지화면→짧은 클립을 적용한다. 화면 밖/가려짐은 추정으로 메우지 않는다.
9. State 검증을 통과한 경우에만 Knowledge→Strategy→Decision→Execution→Coach→Outcome을 평가한다. 현재 SYNTHETIC_ONLY 엔진에는 실제 데이터를 강제 주입하지 않는다. 실제 평가 연결에 core 변경이 필요하면 별도 proposal.
10. material한 새 상황은 원본 replay evidence→새 EXPLORATORY fixture→counterfactual 조작 가능 여부→독립 evidence 검토→Golden 후보 순서다. 기존 fixture expected는 고치지 않는다.

측정 분모: extraction accuracy는 검증 가능한 player reference field와 pipeline field 비교 집합, completeness는 해당 action의 요구 field 집합, freshness는 시간 유효성을 판정할 수 있는 요구 field 집합, decision resolvability는 state+knowledge가 검증되어 decision 평가를 실시한 사례 집합이다. Vision/manual/unresolved rate는 사전에 포함 기준을 정한 실제 사례 cohort가 분모다. 서로 다른 분모를 섞지 않고 제외 사유/샘플 수를 함께 보고한다.
현재 실제 cohort는 0이므로 이 비율들은 null/NOT_RUN이다. 임의 목표값은 설정하지 않았다.

# LoL Coach Design v1.0 — 재구성 설계 계약

## SCOPE
목표: 개인이 자기 플레이의 판단·실행을 개선하는 Web MVP(최소 기능 웹 제품).
코어 흐름: 입력 → 근거 분류 → 시점별 상태 → 정보 충분성 → 가능한 행동 비교 → 설명·추가 관찰 → 복기.
지원 설계 범위: 라인전, 정글 개입, 웨이브, 귀환·로밍·매복, 조합/역할/정글 시너지, 한타, 팀의 무리한 진입 대응, 불리한 수비, 개인 복기.
개인용 단일 사용자. 결제·다중 사용자 SaaS·자동 게임 조작·부정행위 탐지/처벌·대체 랭킹은 범위 밖.
정확한 자동 영상 이해/판단 모델 및 모든 챔피언 상성 지식 완성은 구현·데이터 검증 범위이며 이 문서의 성능 약속이 아니다.
제품 모드는 PRE_GAME(경기 전), POST_GAME(경기 후), LIVE_STATIC(실시간 정적 표시)로 분리한다.
POST_GAME 분석 결과를 LIVE_STATIC으로 전달하거나 게임 진행 중 복기 모드로 우회 노출하지 않는다.
POST_GAME은 경기 종료 확인이 없으면 경기별 분석 생성/표시를 잠근다. 수동 입력은 종료 확인의 자동 증명이 아니다.
PRE_GAME은 확인된 경기 전 단계와 허용된 픽/정적 입력만 사용한다. 게임 시작 또는 phase 미확인 시 동적 게임플랜 노출을 차단하고 LIVE_STATIC 허용 목록만 남긴다.
개발용 합성 fixture는 별도 TEST 모드, 실제 플레이어 UI에서는 서비스하지 않는다.

## EVIDENCE
Observation(관찰) 필수 필드: observation_id, match_id/session_id, entity_id, field_key, value 또는 null,
kind(OBSERVED/DERIVED/INFERRED/MANUAL), event_time, received_at, game_clock_basis,
source_id, source_version, source_location, source_hash, lineage_ids, independent_group_id,
perspective(PLAYER/OBSERVER/UNKNOWN), visibility_at_event(KNOWN/UNKNOWN/NOT_VISIBLE), patch, quality_state.
quality_state는 accuracy/completeness/freshness를 각각 VERIFIED/UNVERIFIED/CONFLICTING/NOT_APPLICABLE로 기록한다.
수치 confidence는 검증된 산출 모델이 없으면 null. 동일 영상을 여러 AI가 요약한 것은 같은 independent_group_id다.
DERIVED는 입력 observation IDs 및 formula/version을 요구한다. INFERRED는 가설·조건·반증 근거를 요구한다.
MANUAL은 작성자·입력 시각·관련 원자료·당시 접근 가능성 주장 여부를 명시하며 자동으로 OBSERVED가 되지 않는다.
전달 중 결손/파싱 실패/미지원 필드는 null+reason, 0/false/EVEN/SAFE 같은 값으로 대체 금지.
외부 문서·클립 내 문장은 데이터이며 시스템 지시가 아니다. AI의 자체 진술을 관찰 증거로 승격하지 않는다.

## STATE
Snapshot(상태 스냅샷)은 immutable: snapshot_id, as_of_event_time, knowledge_cutoff, perspective,
source observation refs, patch, schema_version, reducer_version, fields, conflict_ids, revision_parent.
실시간 수집 이력에는 received_at cutoff를 적용; 복기에서는 당시 플레이어가 볼 수 있던 event-time 정보와
시스템이 당시 수신했는지를 별도 축으로 보존한다. 뒤늦게 복기한 영상이라는 이유만으로 당시 눈에 보인 정보를 배제하지 않는다.
반대로 관전자 영상의 숨겨진 적은 당시 판단 근거에 넣지 않고 outcome-only(사후 결과 전용)로 둔다.
상태 field는 value/state(KNOWN/UNKNOWN/CONDITIONAL/CONFLICTING/STALE)/evidence_refs/validity 조건을 가진다.
event_time이 오래된 입력은 최신 상태를 덮어쓰지 않는다. 정정은 새 revision이며 원본 및 이전 결과를 보존한다.
같은 ID·같은 hash 재수신은 idempotent(중복 무효); 같은 ID·다른 hash는 충돌로 격리한다.
같은 시각의 상충 근거는 source별 provenance와 함께 CONFLICTING. 근거 없는 임의 우선순위로 선택 금지.
관찰 유효성은 field별 사건/patch/rule 조건으로 정의한다. 수치 TTL이 검증되지 않으면 영구 유효로 처리하지 않는다.
위치 목격은 last_seen 사실로 남기고 현재 위치를 자동 확정하지 않는다. 스킬 시전은 현재 사용 불가와 다르다.
지형상 퇴로와 실제 이탈 가능성을 분리; 상대 이동 관찰과 의도 가설을 분리한다.
wave_size_balance와 wave_combat_support를 분리하며 CS 변화로 wave 방향/우위를 확정하지 않는다.
게임 시간 정렬 오차를 알 수 없으면 정밀한 선후관계·재사용 계산을 보류한다.

## ACTION
행동은 이름뿐 아니라 target/path/entry region/resource budget/exit/abort/postcondition/decision deadline을 가진다.
후보: THREAT, SINGLE_HIT, SHORT_TRADE, EXTENDED_TRADE, ALL_IN, CHASE,
CONCEDE_RESOURCE, HOLD_PRESSURE, FREEZE, SLOW_PUSH, CRASH, CLAIM_SPACE, CLAIM_RESOURCE,
WAIT, PROBE, DISENGAGE, FULL_COMMIT, LIMITED_SUPPORT, EXIT_COVER, CROSS_MAP_TRADE, RECALL, ROAM, AMBUSH.
이 이름은 v1 계약 vocabulary다. legacy ActionType 전 항목이 이미 구현됐다는 뜻이 아니다.
현재 위치 유지/경험치만 확보/일부 CS/완전 이탈은 각각 WAIT/CONCEDE_RESOURCE/CLAIM_RESOURCE/DISENGAGE의 다른 매개변수다.
후보 실행 가능성은 POSSIBLE/IMPOSSIBLE/UNKNOWN. 불가능한 후보는 추천에서 제외하되 이유를 보존한다.
UNKNOWN 후보를 확정 대안으로 제시하지 않는다. 짧은 교환은 공통 초 수가 아닌 목적 달성과 이탈 사건으로 정의한다.
대기·후퇴도 비용이 있으며 항상 안전/정답으로 기본 선택하지 않는다.

행동별 핵심 요구:
|행동군|판단 필수 조건|결손 시|
|---|---|---|
|위협·한 대 응징|접근/공격/반격 범위, 상대 강제 교전, 복귀|조건부 또는 평가 보류|
|짧은 교환|양측 자원·대응 수단, 미니언 기여, 종료/이탈, 개입 노출|종료 가능한지 모르면 유리 확정 금지|
|긴 교전·올인|지속 전투력, 탈출·반격, 증원, 타워/레벨 변화|결과를 뒤집는 자원 미확인 표시|
|추격·매복|경로 시야, 진입/대기/복귀, 적 증원, 잃는 웨이브|확정 처치/안전 보상 금지|
|웨이브·귀환|미니언 종류/체력/위치, 처리 능력, 상대 개입, 귀환 취소/완료|CS만으로 crash/freezing 성공 판단 금지|
|합류·제한 지원|효과 도착 시점, 아군 생존, 실제 기여, 적 증원, 자리 이탈 비용|도착만 가능하다고 구조 가능 판단 금지|
|반대편 교환·로밍|이동+완료+복귀, 상대 대응, 목적물 가치의 맥락|보상을 확정으로 계상 금지|
|대기·수비·후퇴|성장/구조물/넥서스 손실, 추격·다이브, 남는 선택권|생존을 무조건 최우선으로 고정 금지|
필수 여부는 결론 민감도로 평가한다. 점멸 유무가 결론을 바꾸지 않는 근거 범위라면 이번 판단의 필수 입력이 아니다.

## DECISION
세 출력 축을 분리: sufficiency(SUFFICIENT/CONDITIONAL/INSUFFICIENT),
assessment(FAVORABLE/UNFAVORABLE/CONTESTED/UNDETERMINED), coaching(근거·대안·중단·추가 관찰).
legacy VALID와 P0~P5를 이 축의 값으로 직접 변환하지 않는다.
순서: 모드/정책 Gate → 시점·patch·근거 Gate → 실행 가능한 후보 → 근거와 양립하는 scenario 범위
→ 후보별 평가 → 비교 → 판단 마감/만료 → 설명.
scenario는 supported/contradicted/unknown constraint를 보존. 모든 상상 가능한 위험을 넣지 않는다.
범위를 제한할 근거가 없으면 INSUFFICIENT. 검토한 범위를 가능한 세계 전체로 주장하지 않는다.
상대 의도나 아군 호응의 확률을 임의로 부여하지 않는다. 확률 없이도 조건별 결론을 표현한다.
한 scenario만 비교하거나 결과가 뒤집히는 scenario가 남으면 해당 조건을 출력에 명시한다.
비교 dimensions: 생존·노출, 체력/마나/스킬, 골드/경험치, 위치/웨이브, 시간/목표물, 남는 선택권.
각 항목은 서술/근거 있는 범위와 UNKNOWN을 허용. 임의 종합 점수나 교환비율 없음.
Dominance(명백한 우열)는 동일 scenario·시간 범위에서 모든 비교 가능한 dimension이 나쁘지 않고
하나 이상 더 나으며, 관련 UNKNOWN이 없어야 인정한다. 이는 해당 scenario 안에서의 우열이다.
후보를 전체 비교에서 제외하려면 같은 대안이 평가 범위의 모든 scenario에서 나쁘지 않고,
적어도 한 scenario·항목에서 엄격히 더 나으며, 관련 UNKNOWN 또는 우열 역전 조건이 없어야 한다.
서로 엇갈리거나 범위를 제한할 근거가 부족하면 조건부 후보를 유지한다.
현재 목표(예: 넥서스 수비)를 명시하고 팀/개인 목표 충돌을 설명한다. 가치 가중치가 없으면 유일 최적해를 만들지 않는다.
정보 요청은 결론을 가르는 missing field → 최소 관찰 → 당시 확인 가능 시간/비용 → 요청 순서.
화면 1장으로 사건 변화가 확인 안 되면 시작/종료 사건을 포함한 clip 필요. 고정 5초/공통 TTL 없음.
확인 시간이 마감 이후면 당시 대안으로 요청하지 않는다. Fallback도 실행 가능성과 비용을 검토한다.
판단은 입력/지식/patch/목표가 바뀌거나 abort 사건·마감에 도달하면 만료; 새 decision_id와 parent로 재평가한다.
이미 쓴 자원은 후속 투입 정당화 근거가 아니다. 아군 실수 여부와 그 이후 최선 대응은 따로 판단한다.

## KNOWLEDGE
KnowledgeRule: rule_id, version, patch_range, champion/role/matchup/level/context applicability,
required_fields, claim, mechanism, source_refs, counterexamples, author, review_state, supersedes.
review_state=EXPLORATORY/REVIEWED/REJECTED/RETIRED. EXPLORATORY는 가설로만 출력하고 확정 결론의 단독 근거 불가.
REVIEWED도 현재 입력/patch/적용 범위를 만족해야 사용. 검증 근거 없으면 수치 cutoff·데미지·쿨다운·승률을 채우지 않는다.
설계 계약과 상성 콘텐츠는 별도 버전. 콘텐츠 수정은 기존 결과를 덮지 않고 새 분석 revision으로 비교.
지식 충돌은 보존하고 조건 차이가 설명되지 않으면 결과를 제한한다. AI 다수 동의만으로 REVIEWED 승격 금지.
Data Dragon 같은 정적 자료는 규칙/수치의 출처 후보이며 실경기 상태를 제공하는 증거가 아니다.
Patch 미지원이면 정적 일반 원칙만 범위를 명시하여 제공하고 patch-sensitive 평가는 차단한다.

## TEAM_DRAFT
경기 전 draft snapshot: session_id, revision, phase, visible picks/bans, role assignments+uncertainty,
patch, observed_at, source, adapter capability. 불완전 픽/역할은 미확인 유지; 바뀌면 이전 gameplan 만료.
자동 반영은 접근 방식·정책·필드 검증을 통과한 adapter만 사용. 없으면 수동 입력으로 작동하고 자동 기능은 UNAVAILABLE.
게임플랜: 라인별 유리/불리/경합/미확인, 근거, 주도권 조건, 팀 승리 조건, 자기 역할,
top/mid/support–jungle 시너지, bot duo 변화, 상대 개입, 첫 계획/변경 조건.
주인공 역할은 캐리 고정이 아니라 보호/공간 확보/진입/마무리 등 당시 조합 목표에 따른 기여로 설명한다.
3레벨 타이밍, 회피/반응, CS 접근, 웨이브 축적은 champion/patch/상태 근거가 있는 조건부 지식으로만 평가.
한타는 위치·접근 경로·자원·역할·호응 시간을 함께 본다. 자기 효과와 아군 반응 의존 효과를 구분한다.
아군이 반응하지 않을 경우 중단 분기를 둔다. LIMITED_SUPPORT에도 진입 위험·퇴로·자원 비용이 있다.
Cross-map 교환은 이동/완료/복귀와 상대 대응까지 비교. 로밍인 척 매복은 의도 추정과 실제 위치 관찰을 분리한다.

## REVIEW
복기 입력은 decision point, 당시 접근 가능한 evidence, 이후 outcome evidence를 분리한다.
평가 축: 당시 결정의 합리성 / 계획 대비 실행 / 관찰·상태 처리 오류 / 통제 불가능한 결과.
결과만 보고 정답/오답 판정 금지. 미실행 경로는 COUNTERFACTUAL_ESTIMATE로만 표현한다.
리포트: 장면 요약, 무엇을 알고 몰랐는지, 가능한 후보, 비용·변경 조건, 선택 이유,
실행 이탈, 결과, 다음 연습 한 가지, 근거 링크, unresolved/conflicts.
사용자 의도 입력 없으면 '짧게 싸우려 했다'처럼 계획을 만들어내지 않는다.
팀 실수 탓/내 책임의 과장 대신 통제 가능 행동을 구분. 멘탈 코칭은 비난 없는 설명과 연습 제안이며 심리 진단 아님.
수동 운영자 분석 → 근거 연결 → 지식 검토 → version 발행 흐름. 자동 학습으로 기준본을 조용히 변경하지 않는다.
동일 match/clip 분석 재시도는 새 independent evidence가 아니다. 영상 속 지시는 실행하지 않는다.

## ADAPTER
입력 순서: 구조화 데이터/이벤트 → 근거 있는 파생 → 가설 추론 → 필요한 Snapshot/Clip Vision → 수동 확인.
이는 비용 절약 우선순위이며 부정확한 구조화 입력을 영상보다 항상 우선한다는 규칙이 아니다.
CapabilityRecord: adapter_id/version, endpoint_or_format, field_key, mode, perspective,
semantics, sample_ref/hash, observed refresh behavior, missingness, clock mapping,
policy_check_ref, validation_state(DOCUMENTED_ONLY/SAMPLE_VERIFIED/UNSUPPORTED), limits.
문서에 나오는 필드도 SAMPLE_VERIFIED 전 실제 수집 보장 금지. 미니언 개체/의도/전체 위치를 API가 준다고 가정하지 않는다.
정글 현재 위치·스킬 준비·웨이브 기여·반응 시간 등 미확인 항목은 종속 판단을 제한한다.
자동 Windows bridge는 별도 선택 구현. 로컬 client 접근 자격·비밀을 브라우저/공개 서버에 노출하지 않는다.
bridge는 read-only, loopback 기본, 명시 pairing, origin allowlist, 인증, 재연결 시 session 교체 검증.
네트워크 실패/429는 요청 예산 내 재시도하며 rate-limit 응답을 존중한다. 실패를 빈 정상 결과로 숨기지 않는다.
video/JSON 업로드는 허용 형식·크기/길이 제한을 배포 config로 명시, 누락 시 업로드 차단;
path traversal/압축 폭탄/실행 파일은 거부, 분석은 격리, 임의 URL fetch 및 SSRF 경로는 제공하지 않는다.
raw 자료는 hash와 보관 정책을 갖는다. 사용자 삭제는 raw·파생·지식 참조 영향까지 처리하고 비식별 tombstone만 남긴다.

## AI_BOUNDARY
AI는 설명 초안·장면 후보·지식 후보를 낼 수 있지만 evidence gate, mode gate, 상태 확정·권한·freeze를 바꾸지 못한다.
AI 입력은 최소 장면·익명화 식별자와 근거. 외부 전송은 사용자의 설정과 동의, 비용 한도 충족 시만 실행.
유료 API 연결/자동 결제는 현재 승인 아님. AI 비활성/실패 시 구조화 리포트와 수동 검토가 동작해야 한다.
ChatGPT 구독을 앱 API 사용 권한/요금 포함으로 간주하지 않는다.
출력은 schema 검사, 모든 사실 claim의 evidence refs 검증, 금지 모드 검사 후 표시.
불일치면 AI 설명만 격리하고 기초 기록 유지. 번역도 UNKNOWN/CONDITIONAL/CONFLICTING 의미를 보존한다.

## INTERFACE
모바일 대응 웹 화면: 홈(수집/분석 상태) → 경기/장면 가져오기 → 시점별 근거 → 후보 비교 → 복기 → 지식 검토/설정.
경기 전 탭은 draft revision과 가정 표시; 실시간 탭은 정책 검토된 정적 자료만.
사용자 문구는 충분성/행동 평가를 다른 배지로 표현. 미확인은 빨간 위험 확정 배지로 바꾸지 않는다.
각 claim에서 원자료 위치/시각/관점/patch와 만료 이유까지 열람 가능. 색상 외 텍스트·키보드 탐색 제공.
로딩/부분자료/오류/검토 필요/취소/삭제를 별도 상태로 표시. 최근 완료 리포트를 새 경기 결과처럼 보여주지 않는다.

API version `/v1`, JSON schema_version 명시. 계약 요약:
|endpoint|입출력 및 실패|
|---|---|
|POST /sessions|mode, patch → session_id/revision; 미지원 mode 422|
|POST /sessions/{id}/observations|observation batch+idempotency_key → accepted/rejected/conflicts 각각; 부분 성공 명시|
|POST /sessions/{id}/drafts|expected_revision+visible draft → 새 revision; 오래된 revision 409|
|POST /sessions/{id}/reviews|snapshot_ref, objective, analysis_version → job_id; 종료 미확인 409, 금지모드 403|
|GET /jobs/{id}|QUEUED/RUNNING/NEEDS_INPUT/COMPLETED/FAILED/CANCELLED, reason, result_ref|
|POST /jobs/{id}/cancel|취소 요청; 이미 완료면 원결과 유지하고 상태 명시|
|GET /reviews/{id}|revision, evidence refs, sufficiency, assessments, alternatives, expiry, limitations|
|POST /knowledge/proposals|draft rule → EXPLORATORY; 자동 REVIEWED 승격 없음|
|DELETE /sessions/{id}|명시 삭제 요청, job 취소, raw/derived 제거 및 완료 상태|
오류 공통: error_code, message, retryable, missing_fields, correlation_id. 비밀·raw traceback 반환 금지.
인증 없는 외부 요청은 거부. 로컬 개인용도 원격 노출 시 인증·HTTPS·접근 제어 필요.
동일 idempotency_key+payload 재호출은 같은 결과, 다른 payload는 409. 실행 중 revision 변경 시 기존 결과를 STALE로 표시.

## PERSISTENCE
초기 SQLite/로컬 파일 저장을 설계 대상으로 한다. 브라우저만으로 Windows 로컬 API 접근 가능하다고 가정하지 않는다.
tables: sessions(id,mode,patch,revision,status), sources(id,hash,location,retention),
observations(id,session_id,source_id,event_time,received_at,body_hash,payload),
snapshots(id,session_id,parent_id,schema_version,payload), decisions(id,snapshot_id,rule_versions,objective,payload),
review_jobs(id,session_id,input_revision,status,result_ref), knowledge_rules(id,version,status,payload),
audit_events(id,subject_id,event_type,time,payload), tombstones(subject_id,deleted_at).
복합 rule PK=(id,version); FK 활성화; 모든 immutable row 변경은 새 revision. 비밀은 DB 분석 payload 밖 credential store.
트랜잭션 내 입력·job 생성; raw 파일은 hash 경로 원자 쓰기 후 DB 연결, 실패 시 고아 정리 목록.
삭제는 관련 job/참조를 추적하고 개인 자료를 audit payload에 재복제하지 않는다.
schema migration 전 백업, 버전 불일치시 읽기 전용, 실패시 rollback. 복구 실증은 release gate.
보관 기간/업로드 예산/API 비용은 deployment config이며 미설정 시 관련 자동 기능 disabled. 임의 숫자 기본값 없음.

## VALIDATION
증거 종류: HISTORICAL_REPORT / SOURCE_ARTIFACT / FRESH_EXECUTION / DESIGN_EXPECTATION / REAL_SAMPLE.
서로 대체 금지. 합성 사례로 실제 인식 정확도·사용 효과를 주장하지 않는다.
검증 순서: 보호 source hash → 문서·ID·참조 schema → 보존 core 관찰 → contract 사례 감사 → 필요한 독립 검토.
v1 구현 시 scenario 각각 실행 테스트, metamorphic 관계(정보 삭제가 근거 강화를 만들지 않음 등),
외부 입력 누락/충돌/지연, AI injection, 모드 우회, 취소/삭제/재시도, 모바일 접근성을 검증한다.
정밀 판단의 gold label은 독립 근거·전문 검토가 필요; 같은 AI 출력끼리 일치한다고 정답 label로 쓰지 않는다.
Freeze gate: 계약 범위 모두 문서화, REC 요구/사례 연결 완결, 7개 새 감사 PASS,
보호 바이트 유지, 현재 검증 PASS, unresolved material design conflict 없음, 권한·출시 제한 명시.
과거 18 invariants/DA/WF/SYS의 검증을 완료했다고 선언하지 않는다.

## RELEASE
Design Freeze 이후에도 제품 출시에는 다음 모든 적용 gate를 만족해야 한다.
1. 실제 입력 표본 확보와 각 활성 capability의 의미/누락/갱신/시점 검증. 비활성 기능은 화면에서 미지원 표시.
2. 새 엔진 및 API/UI/persistence 구현, 모든 REC scenario 실행 검증, legacy와의 명시적 migration 승인 범위 준수.
3. Riot 정책·등록/접근 방법 검토 완료; LIVE_STATIC 허용 목록 사전 검토. 적 궁극기 추적/즉시 행동 지시 미제공.
4. 데이터 삭제·백업 복구·인증·모드 격리·AI fail-closed·비용 설정·개인정보 외부 전송 통제 검증.
5. 대표 실제 경기 복기에서 관찰 오류/판단 오류를 구분하고 성능 주장에 대응하는 검증 근거 확보.
수치 성능 목표는 평가셋·방법을 먼저 정한 뒤 결정. 미설정 상태에서 '정확도 합격' 선언 금지.
완전 자동 replay vision/실시간 동적 코치/자동 픽 감지는 구현 가능·정책 적합이 검증되기 전 활성화하지 않는다.

## AUTHORITY
D1: 문서·추적표·fixture 기대동작 정리, 동일 입력 검증, evidence 수집.
D2: 승인된 구조 내 실패 수정/재검증, 상성 지식의 근거 있는 EXPLORATORY 추가.
D3: 이 Freeze 계약 의미 변경, 보존 legacy 수정/대체, 새로운 수치 판단 기준/정책 예외,
유료 서비스 활성화, 외부 공개·민감 정보 전송 범위 확대, 자동 실시간 기능 활성화.
이번 재구성 승인으로 누락 기준본 작성·설계 Freeze는 진행한다. 이후 새로운 변경은 version 및 영향분석을 남긴다.
원본이 나중에 발견되면 별도 경로로 보관하고 차이 검토; 이력·ID·새 검증 결과를 조용히 덮어쓰지 않는다.

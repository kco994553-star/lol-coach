# 게임플랜 2+3 실행 상태
2026-10-25 · 잠정 실행 대장 · 시작 SHA `8e67cce63a29decae9f64a21f7c387bf73824507`.

사용자 승인 방향과 작성자 제안을 분리한다. 기존 queue44 이력을 상속하지 않는다. 아래 상태는 문서 감사/준비 작업의 근거로 시작했으며 동시 진행 코드 작업의 최종 상태가 아니다. 상위 실행자가 실제 명령·SHA·결과·지원 범위를 확인한 뒤 갱신한다. 문서 DONE은 코드/CI/브라우저/배포 DONE이 아니다.

## 요구·호환·자료 기준
- 상단 전체 조합 방향/사용자 기본 방향; 하단 라인전/운영/교전·한타. 비교표·각 단계5행동·항상 보이는 실행/전환 문장·상세/지도/legacy 보존.
- 입력v5·공통상태 스키마·최대2태그는 구현 선택이며 USER 전술 승인이 아니다. 시작점 input legacy/v2/v3/v4, report-v3, delivery-v1, share-v1. 새 버전은 코드와 호환 검사로 확정한다.
- IA v2.0 본문 `contracts/information-architecture-v1.md`의 160행/게임플랜48행/3.2~3.7의37행을 보존. 3.2 전체/역할/2+3, 3.3 웨이브/딜교/정글, 3.4 운영/이익/손실, 3.5 소규모 교전~5v5, 3.6 가정/성향/비용/초기화, 3.7 설명/지도/근거/학습 연결. 상세 하위 ID는 아래 매핑.
- 기본 프로필4 TACTICAL_UNREVIEWED; searchable roster ≠ tactical coverage. 실제 경기 코칭 효과 UNMEASURED N=0. 학습 taxonomy80 ≠ 확보 영상/승인 수; 신규 실영상 검토 N=0(별도 증거 전까지).
- 이전 원문5건: `/workspace/gp23-artifacts/before/raw.json`, `examples.md`. 이는 before 실행 원문이며 GP23 after/seeded5/성공 근거로 재사용하지 않는다.

## 현재 명령/증거
`git rev-parse HEAD` → 시작 SHA 위와 같음. `cat`/`sed`/Python JSON/`rg`로 요구,실제 호출 경로,manifest를 확인했다. 명령은 읽기 전용이며 신규 제품 검사는 NOT_RUN. audit 상세 `/workspace/gp23-artifacts/docs-audit.md`는 작업공간 감사 산출물이다. 영구 검증 receipts는 상위 인계에서 저장소 안에 봉인한다.

## 문서 변경 검증
- 상태44행 고유·6개 차원·A~G 반례14개·기존 matrix160행 확인: `DOCUMENT_STRUCTURE_OK`.
- 소유8문서만 `git diff --check -- <owned paths>`: exit0. 전역 검사는 동시 진행 파일의 공백을 별도 발견했으며 그 파일 소유자에게 전달했다.
- Python SHA-256으로 official_catalog/official_items current pointer와 보존 manifest 일치 확인. 네트워크 freshness/라이선스/새 gameplay 검증 아님.
- 제품 테스트/CI/브라우저/배포는 이 문서 작업에서 NOT_RUN.

## 44개 작업
상태: TODO / IN_PROGRESS / DONE / PARTIAL / BLOCKED / DEFERRED. 차원 상태 `PENDING`은 이번 작업에서 아직 실행하지 않았다는 뜻이다. `EXISTING`은 이전 구현/문서가 있다는 뜻이며 새 수용 기준 통과가 아니다. 실경기는 전행 UNMEASURED N=0, 배포는 전행 NOT_RUN으로 시작한다.

| ID / 작업 | 의존성 | 상태 | 문서 | 코드 | CI | 브라우저 | 실경기 | 배포 | 변경/검토 파일 | 결정·반례 / 명령·결과 | 남은 위험·재개 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| GP23-01 최신 main·작업 트리·AGENTS·배포 SHA 확인 | 없음/앞 A 작업 | PARTIAL | DOCUMENTED | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | AGENTS.md; contracts/information-architecture-v1.md; docs/gameplan-content/gameplan-2-plus-3-review.md | A-01/A-02; 문서/경로/manifest 읽기; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; HEAD confirmed; historical deployment receipt exists, current live SHA/remote latest main not checked here |
| GP23-02 실제 백엔드/프론트/데이터/테스트 경로 추적 | 없음/앞 A 작업 | TODO | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | AGENTS.md; contracts/information-architecture-v1.md; docs/gameplan-content/gameplan-2-plus-3-review.md | A-01/A-02; 문서/경로/manifest 읽기; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; Entry modules named only; parent must trace real call graph |
| GP23-03 사용자 확정 사항과 작성자 제안, 미정 사항 분리 | 없음/앞 A 작업 | DONE | DONE | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | AGENTS.md; contracts/information-architecture-v1.md; docs/gameplan-content/gameplan-2-plus-3-review.md | A-01/A-02; 문서/경로/manifest 읽기; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; Approved/proposed/unknown split documented above; preserve this distinction through implementation |
| GP23-04 기존 160행에 요구 매핑 | 없음/앞 A 작업 | DONE | DONE | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | AGENTS.md; contracts/information-architecture-v1.md; docs/gameplan-content/gameplan-2-plus-3-review.md | A-01/A-02; 문서/경로/manifest 읽기; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; 37 existing IDs in 3.2–3.7 explicitly mapped above, total 160 preserved |
| GP23-05 기존 출력에서 누락·중복·모순 수집 | 없음/앞 A 작업 | TODO | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | AGENTS.md; contracts/information-architecture-v1.md; docs/gameplan-content/gameplan-2-plus-3-review.md | A-01/A-02; 문서/경로/manifest 읽기; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; Need captured engine input/output originals for missing/duplicate/contradictory content |
| GP23-06 초기 설계 반례 검토 | 없음/앞 A 작업 | PARTIAL | DOCUMENTED | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | AGENTS.md; contracts/information-architecture-v1.md; docs/gameplan-content/gameplan-2-plus-3-review.md | A-01/A-02; 문서/경로/manifest 읽기; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; Initial counterexamples/severities above; parent must bind actual outputs and resolve P0/P1 |
| GP23-07 ARCHITECTURE.md를 실제 경로로 보강 | A(01~06) | PARTIAL | DOCUMENTED | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | ARCHITECTURE.md; SOURCE_REGISTRY.md; DECISION_LOG.md; CHANGELOG.md; DEPENDENCY_MAP.md; RELEASE_CHECKLIST.md | B-01/B-02; 문서/경로/manifest 읽기; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; Root architecture scaffold exists; concrete runtime graph remains |
| GP23-08 SOURCE_REGISTRY.md 보강 | A(01~06) | PARTIAL | DOCUMENTED | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | ARCHITECTURE.md; SOURCE_REGISTRY.md; DECISION_LOG.md; CHANGELOG.md; DEPENDENCY_MAP.md; RELEASE_CHECKLIST.md | B-01/B-02; 문서/경로/manifest 읽기; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; Retained source URLs/versions/hashes/times and freshness boundaries audited; root registry not yet amended |
| GP23-09 DECISION_LOG.md·CHANGELOG.md·DEPENDENCY_MAP.md·RELEASE_CHECKLIST.md 정합화 | A(01~06) | PARTIAL | DOCUMENTED | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | ARCHITECTURE.md; SOURCE_REGISTRY.md; DECISION_LOG.md; CHANGELOG.md; DEPENDENCY_MAP.md; RELEASE_CHECKLIST.md | B-01/B-02; 문서/경로/manifest 읽기; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; Six root docs align on unverified status; new decision/compatibility/test/release receipts absent |
| GP23-10 기본 방향·상황 변경·불확실성 공통 스키마 설계 | A(01~06) | TODO | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | ARCHITECTURE.md; SOURCE_REGISTRY.md; DECISION_LOG.md; CHANGELOG.md; DEPENDENCY_MAP.md; RELEASE_CHECKLIST.md | B-01/B-02; 문서/경로/manifest 읽기; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; Four-state design proposal exists, final serialized/validated tactical schema not demonstrated |
| GP23-11 2+3 출력 계약 및 이전 소비자 호환 결정 | A(01~06) | PARTIAL | DOCUMENTED | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | ARCHITECTURE.md; SOURCE_REGISTRY.md; DECISION_LOG.md; CHANGELOG.md; DEPENDENCY_MAP.md; RELEASE_CHECKLIST.md | B-01/B-02; 문서/경로/manifest 읽기; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; Requirements and retained v1 presentation contract known; additive 2+3 compatibility choice remains |
| GP23-12 계약 반례/호환성 검사 | A(01~06) | TODO | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | ARCHITECTURE.md; SOURCE_REGISTRY.md; DECISION_LOG.md; CHANGELOG.md; DEPENDENCY_MAP.md; RELEASE_CHECKLIST.md | B-01/B-02; 문서/경로/manifest 읽기; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; New partial/unsupported/jungle/reset contract regression not run |
| GP23-13 양 정글 정보 상태와 출처/시각 처리 | B(07~12) | TODO | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | web_r4/loading-planboard.js (구현/검증 대기) | C-01/C-02; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; No audited proof of both-jungle information state/provenance/time handling |
| GP23-14 웨이브 행동 가능성 모델 | B(07~12) | TODO | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | web_r4/loading-planboard.js (구현/검증 대기) | C-01/C-02; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; Need feasible wave model and impossible-freeze counterexample |
| GP23-15 체력·마나·기술·상대 압박·지원 가능성 반영 | B(07~12) | TODO | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | web_r4/loading-planboard.js (구현/검증 대기) | C-01/C-02; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; Need resource/skill/pressure/followup priority in common result |
| GP23-16 딜교 길이·푸시·스킬 사용 비용 연결 | B(07~12) | TODO | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | web_r4/loading-planboard.js (구현/검증 대기) | C-01/C-02; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; Need trade-wave cost linkage and agreement checks |
| GP23-17 귀환·오브젝트·합류 이익과 기다리는 비용 반영 | B(07~12) | PARTIAL | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | web_r4/loading-planboard.js (구현/검증 대기) | C-01/C-02; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; Prior backend doc describes qualitative waiting effects; new recall/objective/arrival integration unverified |
| GP23-18 기본 방향과 조건부 전환 생성 | B(07~12) | TODO | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | web_r4/loading-planboard.js (구현/검증 대기) | C-01/C-02; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; Need baseline→conditional action/reason/tag atomic update |
| GP23-19 정글 사용자용 초반 동선/갱/역갱/지원 표현 | B(07~12) | PARTIAL | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | web_r4/loading-planboard.js (구현/검증 대기) | C-01/C-02; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; Graves authored jungle reference exists; new own-jungle role translation unverified |
| GP23-20 C 반례 회귀 | B(07~12) | TODO | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | web_r4/loading-planboard.js (구현/검증 대기) | C-01/C-02; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; New C counterexample regression not run |
| GP23-21 전투 문맥 모델 | B(07~12) | TODO | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | web_r4/loading-planboard.js (구현/검증 대기) | D-01/D-02; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; Fight contexts approved, context-model implementation unverified |
| GP23-22 실효 인원과 도착 순서 | B(07~12) | TODO | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | web_r4/loading-planboard.js (구현/검증 대기) | D-01/D-02; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; Effective participants/arrival order unverified |
| GP23-23 주요 위협 후보와 우선순위 | B(07~12) | TODO | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | web_r4/loading-planboard.js (구현/검증 대기) | D-01/D-02; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; Reachability/contribution/terrain/uncertainty threat ordering unverified |
| GP23-24 원딜 목표와 공격 공간/시간 | B(07~12) | PARTIAL | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | web_r4/loading-planboard.js (구현/검증 대기) | D-01/D-02; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; Existing two ADC profile prose describes space/attack continuity; new threat/stop behavior unverified |
| GP23-25 탑 탱커의 방해/보호 전환 | B(07~12) | TODO | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | web_r4/loading-planboard.js (구현/검증 대기) | D-01/D-02; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; Top tank disruption/protection transition and counterexamples unverified |
| GP23-26 다른 역할의 목표 선택 | B(07~12) | TODO | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | web_r4/loading-planboard.js (구현/검증 대기) | D-01/D-02; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; Context-dependent other-role objectives unverified |
| GP23-27 전투 목표→위협→위치→행동→중단 출력 | B(07~12) | TODO | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | web_r4/loading-planboard.js (구현/검증 대기) | D-01/D-02; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; Five-part fight output contract unverified |
| GP23-28 D 반례 회귀 | B(07~12) | TODO | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | web_r4/loading-planboard.js (구현/검증 대기) | D-01/D-02; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; New D counterexample regression not run |
| GP23-29 상단 전체 조합 방향/사용자 기본 방향 구현 | C/D(13~28) | TODO | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | web_r4/loading-coach-view.js; loading-presentation.js; loading.css (구현/검증 대기) | E-01/E-02; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; New upper-card responsibility separation not browser-verified |
| GP23-30 하단 라인전/운영/교전·한타 구현 | C/D(13~28) | PARTIAL | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | web_r4/loading-coach-view.js; loading-presentation.js; loading.css (구현/검증 대기) | E-01/E-02; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; Legacy five-action delivery exists; new 2+3 lower-card/key-visibility preservation unverified |
| GP23-31 최종 판단에서 태그 생성 | C/D(13~28) | PARTIAL | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | web_r4/loading-coach-view.js; loading-presentation.js; loading.css (구현/검증 대기) | E-01/E-02; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; Existing delivery tag source-path projection exists; final common judgment/max-two/contradiction checks unverified |
| GP23-32 가정 변경·초기화·이전 결과 정리 | C/D(13~28) | TODO | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | web_r4/loading-coach-view.js; loading-presentation.js; loading.css (구현/검증 대기) | E-01/E-02; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; New condition/reset stale text/tag/observation removal unverified |
| GP23-33 데스크톱/390/320 폭·200% 확대·키보드 점검 | C/D(13~28) | TODO | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | web_r4/loading-coach-view.js; loading-presentation.js; loading.css (구현/검증 대기) | E-01/E-02; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; No new desktop/390/320/200%/keyboard receipts |
| GP23-34 E 비판 검토 | C/D(13~28) | TODO | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | web_r4/loading-coach-view.js; loading-presentation.js; loading.css (구현/검증 대기) | E-01/E-02; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; No new E actual-screen critical review |
| GP23-35 임의 10픽 사례 5개 고정 | E(29~34) | TODO | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | 증거 원문/쌍 비교/평가 파일 (대기) | F-01/F-02; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; Five seeded role-balanced 10-pick inputs not generated by this audit |
| GP23-36 실제 엔진 실행 및 원문 저장 | E(29~34) | TODO | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | 증거 원문/쌍 비교/평가 파일 (대기) | F-01/F-02; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; No new engine raw input/output/prose/SHA/coverage bundle |
| GP23-37 각 사례의 조건 변경 짝 비교 | E(29~34) | TODO | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | 증거 원문/쌍 비교/평가 파일 (대기) | F-01/F-02; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; No fresh one-variable condition-change pairs |
| GP23-38 품질 평가 | E(29~34) | TODO | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | 증거 원문/쌍 비교/평가 파일 (대기) | F-01/F-02; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; No fresh six-axis internal scoring; game efficacy remains unmeasured |
| GP23-39 F 냉철한 판정 | E(29~34) | TODO | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | 증거 원문/쌍 비교/평가 파일 (대기) | F-01/F-02; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; No evidence-based F disposition yet |
| GP23-40 변경 범위별 필수 테스트와 CI 실행 | A~F | TODO | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | 검사/브라우저/릴리스/외부 동기화 receipts (대기) | G-01/G-02; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; No new GP23 tests/CI run; historical 906-pass receipt cannot transfer |
| GP23-41 실제 브라우저 통합 검증 | A~F | TODO | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | 검사/브라우저/릴리스/외부 동기화 receipts (대기) | G-01/G-02; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; No new actual-browser full flow; historical screenshots cannot transfer |
| GP23-42 실경기 검증 계획/가능한 관측 | A~F | TODO | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | 검사/브라우저/릴리스/외부 동기화 receipts (대기) | G-01/G-02; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; Need concrete evaluation plan; execution currently UNMEASURED N=0, independent handoff permitted |
| GP23-43 릴리스 검토와 허용된 배포 | A~F | TODO | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | 검사/브라우저/릴리스/외부 동기화 receipts (대기) | G-01/G-02; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; No new release review/deploy attempt; use BLOCKED only after identifying actual permission/environment/check failure |
| GP23-44 GitHub/Notion/관리자 표/그래프 동기화 및 최종 인계 | A~F | TODO | PENDING | PENDING | NOT_RUN | NOT_RUN | UNMEASURED N=0 | NOT_RUN | 검사/브라우저/릴리스/외부 동기화 receipts (대기) | G-01/G-02; 새 실행 NOT_RUN | 새 코드·반례 검사 뒤 근거로 갱신; No new GitHub/Notion/admin/graph synchronization; mutation needs authorized parent workflow |

## 세부 IA 매핑


The canonical IA v2.0 contains 160 total rows, 48 in gameplan, and **37 in 3.2–3.7**. Preserve all numbers and hierarchy. The current feature matrix marks each of those 37 rows `status=INTEGRATED`, `coverage=PARTIAL`, `overall_score=0.5`, `frontend_score=0.5`, `full_feature_acceptance=false`; INTEGRATED is scoped legacy code, not GP23 acceptance. No matrix score increase follows from a mapping/doc change.

| Existing IA IDs | GP23 responsibility | Queue connection |
|---|---|---|
| 3.2.1, 3.2.1.1 | Retain both-team comparison and stable team perspective when changing own champion | 04, 11, 29, 34 |
| 3.2.2, 3.2.2.1 | Whole-composition direction, primary strategy, supporting tools and enemy constraints | 10–12, 29 |
| 3.2.3, 3.2.3.1 | User baseline/role, full sentences and visible action/reason/stop/change | 10–12, 18, 24–27, 29 |
| 3.2.4 | Three phase cards, five actions and independent coaching in each | 11–12, 30 |
| 3.2.5 | Team transition and supporting comparison details | 18, 27, 29, 34 |
| 3.2.6 | Distinguish champion baseline, composition changes and situation/assumption plan | 10–12, 18, 29, 32 |
| 3.3.1, 3.3.1.1 | Lane purpose/five actions/coaching; bottom 2v2 and own-role wording | 12, 16, 19, 30 |
| 3.3.2 | Scoped level/skill/item transitions; no winrate-to-combat-strength conversion | 15–18 |
| 3.3.3 | Feasible wave maintenance/push/clear/return, CS/XP loss | 13–18, 20 |
| 3.3.4 | Trade length, sustain/resources and wave cost | 15–16, 20 |
| 3.3.5, 3.3.5.1 | Both sides' aims, punish windows, distance/resources/followup, real skill names/keys | 15–16, 20 |
| 3.3.6 | Both jungles, recall, recovery and switching when constraints fail | 13, 15, 17–18, 20 |
| 3.3.7 | Own-jungle early route/gank/countergank/support, not own-laner instructions | 12, 19–20 |
| 3.4.1 | Operations objective/five actions/coaching | 17–18, 30 |
| 3.4.2 | Side/main-group assignments, real contribution and arrival order | 17, 22, 26 |
| 3.4.3 | Convert pressure/fight to tower/vision/objective gains | 17, 21, 27 |
| 3.4.4 | Wave/recall/vision/arrival preparation before objectives | 17, 21–22 |
| 3.4.5 | Costs and alternatives when joining/protection/wave conditions fail | 17–18, 25, 27 |
| 3.5.1, 3.5.1.1 | Fight purpose/five actions/coaching; separate operations and fight roles | 21, 24–27, 30 |
| 3.5.2 | Both sides' fight starts, access and protection; effective participation | 21–23, 25–26 |
| 3.5.3 | Ranked reachable threats, ADC space/time, tank disruption/protection | 23–26, 28 |
| 3.5.4 | Position/connectivity/terrain/map examples under scoped support | 21–23, 27–28 |
| 3.5.5 | Re-evaluate/exit/change objectives when attack/protection/followup fails | 24–28 |
| 3.6.1 | Baseline versus manual assumptions, refresh all dependent outputs | 10, 13, 18, 32, 37 |
| 3.6.2 | Risk preference cannot modify objective growth/matchup scores | 12, 32, 40 |
| 3.6.3 | Benefit, failed-action cost and waiting cost; necessity ≠ feasibility | 15–17, 22, 28 |
| 3.6.4 | Reset all summaries/prose/tags/detail to same baseline | 12, 32, 41 |
| 3.7.1 | Inline concepts explaining the selected plan | 27, 30, 34 |
| 3.7.2 | Existing context-linked maps/formation/scenes | 11, 27, 30, 41 |
| 3.7.3 | Source, patch, applicability, uncertainty and exceptions | 08, 10–12, 27, 36 |
| 3.7.4 | Preserve champion/opponent/topic in learning links | 11, 30, 41 |

Fight scope clarifies existing 3.5 rather than adding a top-level feature. Input prerequisites stay in 3.1 and champion-stat power-graph requirements stay in 2.3; neither should be renumbered into GP23.


## 학습실 추가 작업 (GP23 번호/분모 보존)
새 taxonomy/index/backend/UI 구현은 GP23을 대체하지 않는 추가 범위다. 기준 문서 `docs/learning-room/video-topic-taxonomy-v0.1.md`; 실제 모듈·계약·검사·브라우저 receipts는 담당 구현 뒤 갱신한다. 상태 DOCUMENTED / 코드 PENDING / CI NOT_RUN / 브라우저 NOT_RUN / 실영상 N=0 / 배포 NOT_RUN. 3.7.4↔6.4/6.5/6.6, 5.5.2, 2.4 기존 ID로 연결한다. private notes·개인 식별정보와 공개 export를 분리하고, 새 lesson candidate는 전술 적용/승인을 만들지 않는다.

## 재개 절차
현재 HEAD/작업트리 확인 → 같은 입력의 before/after 원문과 변경 파일 확인 → 해당 A~G 반례 최소2개 재실행 → 변경 범위 tests → 브라우저 → 원문/평가 → 소스 seal/CI/배포 권한 및 제한 → 실제 receipts로 행/집계 갱신. 학습실은 taxonomy ID/필터/구간·출처/복귀/권한 경계를 독립 검증한다. 권한/클라이언트/비용 의존 작업만 구체 원인과 함께 BLOCKED; 독립 작업은 계속한다.

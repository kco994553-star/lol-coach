# CURRENT HANDOFF — LoL Coach

## 최신 R7 추가 근거 — 2026-10-04 UTC

- 실제 시작 main HEAD는 `16adaf60753663c95d236e586c34b466fc929f43`였다. 보고된6951f5c보다 앞선 기존 R7-real을 먼저 읽고 이어서 진행했다. 작업은 실제 Git checkout이며, 변경 전201 tracked blobs 일치.
- 현재 보고: `docs/r7-continuation/CONTINUATION_REPORT.md`; 최소 입력: `docs/r7-continuation/MINIMUM_INPUT_PACKAGE.md`; 실행 근거: `evidence/r7-continuation/`.
- 신규 같은 경기 Match/Timeline pair1: `EUW1_7095952008`, version14.17.613.973, timeline31frames. pinned HF revision·exact HTTP206 ranges·hash·참가자10명 연결 확인. publisher BSON-JSON export이며 Riot 수집은 publisher assertion이다.
- 선동결26개 source field26/26, source-only HP비율/CS 파생 기준2개. ESTABLISHED_SOURCE_FIELD_REFERENCE1은 POST_GAME_DATASET 범위이며 PLAYER reference가 아니다. 기존 LiveClient extractor는 각각0/17 PRESENT, schema 미지원. `scripts/verify_r7_source_reference.py`는 offline 재검사만 하고 importer/coach를 추가하지 않는다.
- 기존 화면5hash fresh 복구와 감사 재실행. 새 GameStar 교전 후보1개를 선동결 후 blind Vision14/14 선택 전사 일치. Garen HUD12:26이나 own champion 주 화면 없음; camera center를 own position으로 바꾸지 않았다. Teamfight/소규모 교전 분류 contested, Bot 표기 관찰. AI 일치를 정확도/gold로 쓰지 않음.
- 29개 PLAYER 변수 DIRECT0/DERIVED0, 완전한 player Replay reference0, 같은 경기 player/truth pair0, Coaching N0/accuracy null. 기존10slots와3partial 유지, C partial 후보1 추가. Source-level26direct/2derived 및7행 subfield 경로는 별도로 집계.
- Frozen27·기존111expected·보호9·R6/R7/R7-real evidence 보존. fresh111/111 + 보호9/9 PASS. 새 source bytes 변조/기존evidence 덮어쓰기 거절2/2; 새 manual snapshot KNOWN0, derivedCONDITIONAL,4required UNKNOWN. R6 browser/mobile는 Historical.
- Local EXTERNAL_ENVIRONMENT_BLOCKER fresh 재확인: game/client process0,2999listener0,TCP거절,TLS이전실패. retry0. 전체 공개 Source 획득 불가로 확대하지 않음.
- A미충족/B전체미입증을 그대로 보고했다. 실제 State/Decision acceptance는 미완료. 동일 경기 player POV와 행동 문맥을 확보하면 Reference-first 비교부터 이어간다. source 경로/공개 링크를 optional로 요청했으며 자동 대기·백그라운드 수집은 없음.
- 이번 D1/D2 범위에서 Frozen 의미 변경 필요 없음/D3불필요. 기존 C3 proposal은 미승인·미구현으로 보존하지만, 그것을 추가 evidence 검증의 일괄 중단 사유로 사용하지 않는다. 합성 guard를 완화하거나 REAL을 SYNTHETIC으로 바꾸지 않았다. 실제 평가 연결 전에 기존 계약 보존 여부를 영향분석한다.

## 아래는16adaf6에 기록된 이전 인수인계

2026-10-04 KST. Design v1.0 동결 유지. **R7 real-evidence 후속: 실제 공개 화면 진단 완료, Decision/Coach 엔진 연결은 D3/Core Contract 경계에서 중단. R8 아님.**

- 시작 실제 GitHub main HEAD `6951f5cafbc360c4637107fe3a3fb4dc0eed0d25`: remote165/local165 blob 일치. 로컬은 materialized tree, Git checkout 아님.
- 상세 결과 `docs/r7-real/REAL_EVIDENCE_REPORT.md`. C3 제안 `docs/r7-real/C3_REAL_AUDIT_PROPOSAL.md`는 **미승인/미구현**. 최소 자료 조건 `docs/r7-real/MINIMUM_INPUT_PACKAGE.md`.
- R7 baseline fresh111/111·보호9/9·Frozen27 PASS. `evidence/r7-real/r7-fresh/` 및 binding receipt. R6 browser/mobile는 hash 동일한 Historical evidence 재사용이며 이번 fresh browser PASS 아님.
- 실제 원본5화면 확보: player-style4 + observer1. 기존10 슬롯 유지, lane trade/CS access/jungle uncertainty3 슬롯은 PARTIAL reference. fully verified real replay0, authenticated match0, human annotator0.
- 먼저 고정한 AI operator reference vs blind AI Vision: player53/53 선택 필드 일치. 최초 전체56/58; observer HP/maxHP 오독2필드는 원본 재확인 후 별도 revision. 원본 lock/불일치 history 보존. 이는 human-gold/state accuracy 아님.
- Selective Vision RUN: HUD·정지 geometry 관찰, sequence/흡수/damage window/intent 미확인. Observer NOT_PLAYER_KNOWN 제외 및 실제 cross-session 거절 PASS; 같은 경기 player/ground-truth pair0.
- public Match/Timeline 파일 취득·23경로 전사 확인; 서로 다른 matchId join 거절. 기존 LiveClient extractor는 두 파일 모두0/17 present(미지원 schema). 실제 원천 인증·patch/player visibility 연결 미완료.
- source overlay29: pending12/Vision-required12/inference3/manual2, VERIFIED_DIRECT0/DERIVED0. Timeline x/y로 사후 position의 비영상 경로 후보 확인; player-known 승격 없음. 원본 R7 matrix/evidence/fixture 그대로.
- Local EXTERNAL_ENVIRONMENT_BLOCKER: Linux Work에서 LoL/Riot process0/listener0, 한 TCP refused. CA 검증 완료·TLS handshake 전 실패. YouTube frame 획득 실패 후 공개 원본 PDF/blog 이미지로 대체 성공.
- 재현 `python3 scripts/audit_real_r7.py --media-dir <original-assets-directory>`. 공개 URL/hash와 PDF page/image 순번은 `evidence/r7-real/visual-source-manifest.json`; 최종 run은 `AUDIT_INDEX.json`. media와 전체 publisher raw JSON을 Git에 재게시하지 않음.
- 기존 엔진은 `ReviewInput.evidence_kind=SYNTHETIC` 및 `run_review` TEST guard. 실제 REAL 요청5개 schema 거절; 합성으로 바꾸지 않음. 실제 Coach N0/Accuracy null. Frozen27/core/old111 expected 변경0.
- Stop A/B 미충족: 3완전한 실제 Decision Reference가 아니며 공개 화면 확보 불가는 아님. D1/D2 evidence work는 완료했고 실제 엔진 평가 계약 변경만 D3 요청한다. 승인 후 별도 offline REAL_AUDIT 계약/adapter/회귀를 구현하되 자료·Knowledge 미검증 사례는 계속 차단한다.
- 결제/credential/외부 메시지/백그라운드 수집/사용자 PC 연결 없음. C3 승인 전 실제 평가 경로를 구현하거나 기존 mode guard를 완화하지 않는다.

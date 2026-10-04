# CURRENT HANDOFF — LoL Coach

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

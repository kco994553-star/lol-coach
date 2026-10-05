# Manual Draft Capture Implementation Plan

> **For agentic workers:** Execute this bounded plan inline with independent storage/backup/test scopes; keep one common writer claim. Tests precede implementation. Existing authority authorizes implementation and gated publication.

**Goal:** Record operator-entered pre-game picks, bans and uncertain roles as immutable manual input, separate from synthetic analysis.
**Architecture:** Main SQLite v2 adds isolated draft capture and snapshot tables under DraftStore(Store). Legacy TEST-only tables and methods remain unchanged. The authenticated workbench exposes dedicated capture routes and a separate tab; two-database backup format1 accepts exact main1/2.
**Tech Stack:** Existing Python3.12/SQLite/stdlib and vanilla JS/HTML; no dependency or external service.
**Spec:** docs/DESIGN.md#TEAM_DRAFT, REC-REQ-013 and bounded capture portion of REC-SC-011; frozen bytes retained. Risk CRITICAL; automatic collection/gameplan/actual coaching remain unavailable.

## Global Constraints
- Original storage.py, Research/Knowledge storage and frozen contracts/fixtures/expected/history bytes remain unchanged.
- Capture IDs are absent from legacy sessions. Existing /sessions accepts TEST only; capture IDs cannot become cases/jobs.
- Null phase/patch/observation time/champion/role means unknown. No inferred game clock, numeric confidence, applicability, decision or intent.
- Source author/perspective/description are explicit operator declarations, not verified player reference. Validation UNVERIFIED; real CoachN0/accuracy null.
- Actual private validated main-v1 recovery copy precedes additive migration; snapshot failure leaves v1, DDL failure retains recovery copy, no overwrite. New empty installs create exact v2 without pretending a prior-data backup.
- UI downloads the saved record only; edited draft is not export. Historical snapshots never mutate; current latest CAS remains explicit. Session deletion physically removes snapshots; personal backup archives remain separately retained.

## Interfaces
Input capture exact fields: title(nonblank<=200), phase(null or nonblank<=100), patch(null or nonblank<=100), observed_at(null or ISO8601 offset timestamp), visible_picks / visible_bans (arrays, max10 each, exact rows {side:ALLY|ENEMY,slot:1..5,champion:null or nonblank<=100}, no duplicate side+slot), role_assignments(max10 exact rows {side,slot,role:null|TOP|JUNGLE|MID|BOTTOM|SUPPORT,uncertainty:nonblank<=2000}, no duplicate side+slot), source(exact {author:nonblank<=200,perspective:PLAYER|UNKNOWN,description:nonblank<=2000}). All text is valid UTF8; arrays may be empty; booleans are not integers.
Record includes schema_version=mvp.manual-draft.v1, id(snapshot32hex), session_id(capture32hex), revision(1-based), parent_id(previous snapshot id/null), received_at(actual server UTC), capture(input object unchanged), input_sha256(canonical sorted compact UTF8 input), adapter_capability={automatic_collection:UNAVAILABLE,manual_capture:AVAILABLE}, validation_state=UNVERIFIED, gameplan_status=NOT_GENERATED, coaching_enabled=false.
DraftStore methods: create_capture(capture,max_bytes), list_captures(max_bytes), get_capture(cid,revision=None,max_bytes), capture_history(cid,max_bytes), put_capture(cid,capture,expected_revision,max_bytes), delete_capture(cid,expected_revision,max_bytes). Default method budget explicit integer positive (use existing HTTPbodylimit). Create returns record201; update200; current revision mismatch409 REVISION_CONFLICT; absent404 DRAFT_CAPTURE_NOT_FOUND; unknown fields422 INVALID_DRAFT_CAPTURE; exceeded response413 DRAFT_CAPTURE_TOO_LARGE.
Tables: draft_captures(id primary key,title notnull,revision integer notnull), draft_snapshots(id primary key,session_id FK draft_captures ON DELETE CASCADE,revision intnotnull,parent_id,payload notnull, UNIQUE(session_id,revision),UNIQUE(session_id,id), FOREIGN KEY(session_id,parent_id) REFERENCES draft_snapshots(session_id,id)); no overwrite/history update API.
Deletion returns count-only {id,status:DELETED,deleted_snapshots}; expected_revision required. Keep anonymous/random tombstone only if needed, no private payload log.
Pure draft.validate_schema(db) checks exact main-v2 SQL/PK/FK/objects. draft.validate_draft_content(db) verifies every stored capture/history/hash/parent/identity/timestamp/budget and excludes collisions with legacy session IDs. Existing backup main-content TEST semantics remain strict.
HTTP routes /dev/v1/draft-captures GET/POST{capture}; /draft-captures/<32hex> GET/PUT{capture,expected_revision}/DELETE{expected_revision}; /.../history GET; /.../revisions/<positive> GET. Same existing token/Host/Origin/body caps/duplicatekey/refusal; no raw URL fetch.

## Review Focus
- Wrong-mode draft IDs on legacy case/job APIs remain rejected.
- Partial input and unknown role/time survive save/restart/backup exactly; timestamps never fabricated.
- Concurrent stale save conflicts retain new draft; cancellation/navigation/late replies cannot overwrite another capture.
- Pre-migration failure/corrupt backups refuse safely and preserve exact old data.
- Delete clears current export/history and late replies; authentic old download is immutable; mobile usable.

## Task1: Storage, provenance and recovery
Files create coach_v1/draft.py, tests_mvp/test_draft_capture.py. Write negative/positive migration, exact-history/CAS/Unicode/null/provenance/schema/FK/mode tests, run absent API RED with recorded first failure, implement wrapper and pure validators, rerun targeted GREEN. Source and first failure archives additive. Do not edit storage.py or server.py.

## Task2: Offline backup compatibility
Files modify coach_v1/backup.py; create tests_mvp/test_draft_backup.py. Keep existing main validator unchanged; include draft tables for exact main2; accept manifest actual main1/2; pure content validation, never constructor/job execution. Write v2 roundtrip/corruption/manifest/version/schema/privacy tests RED before support, then GREEN; prior backup23/Knowledge19 remain required.

## Task3: Authenticated routes and usable manual tab
Root modifies coach_v1/server.py, web_r4/index.html and creates web_r4/draft.js. Wire DraftStore and dedicated routes/assets/status capabilities without changing synthetic core mode. UI title/patch/phase/declaredtime/sourceauthor/perspective/description plus two-side five-slot picks/bans/roles/uncertainty; explicit unknown placeholders. New/list/load/current-save/history/read-only old preview/exact download/delete; dirty confirmation, CAS, current/stale errors, epoch/edit/deletion guard; no auto-save. Existing tab clicks hide manual view and clear stale preview; logout purges draft. Existing Research/KnowledgeJS remain unchanged by DOM event wiring in draft.js.

## Task4: Actual verification and publication
Create authenticated HTTP tests and browser_draft_capture.cjs, retain prior89 IDs and add literal fixed cases/count. Write failing tests first, retain RED receipts, run actual HTTP/SQLite and targeted deterministic guards; verify hard preservation/source-version transition. Run mandatory script with old111/protected9/Frozen27/backup23 and all prior guards + new suites; actualChrome flow upload/input/list/save/CAS/history/download/delete/empty/error/mobile. One independent critical review, repair reproduced failures. Record local versus actualCI separately, testedtree/parents/hashmatch, publicfreeCIbasis, reviews/conflicts0, expectedmain/claim. API publish, gatedmerge/postmerge, actualSHA/handoff. No product completion or realCoachpromotion claimed.

## Current execution
PR7 merged0f2b333e, actualPR37271933712/post37272079828 SUCCESS Chrome89/all194inputs, firstfailure retained. New common claim36c7bcad tokenmain-20261005T0630-manual-draft-capture-root, owner feat/manual-draft-capture-2026-10-05. Existing authority supplies native execution; no repeated user approval. Independent storage and backup implementation scopes may parallelize after interface agreement; root owns integration/UI.


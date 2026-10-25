# Learning data/index implementation report

Commit: `2862f3b` (explicit six owned paths only). Base: `8e67cce`. Shared worktree: `/workspace/lol-coach-gp23`.

## Delivered

- Deterministic offline read-only normalized public index and generator with `--check`.
- Exact Korean 4×5×4 taxonomy with unique stable IDs, 29 existing registry claim references, 8 existing link-only YouTube candidates, 29 condition-change reflection practices, 0 segments and 0 new visually reviewed videos.
- All eleven card fields present; null unknown fields stay null. Existing tactical text/conditions/counterexamples resolve through `{claim_id,field}` into the unchanged registry. No second tactical corpus or review authority.
- Pure NFC/casefold search with AND filters, hierarchical/unclassified topic selection, stable paging/deep copy, explicit source patch mismatch and unknown counts.
- Typed recorded acquisition failures retained only for actually attempted IDs. Candidate transcript/visual/access/patch facts remain UNKNOWN.
- HTTPS/video binding, identity/reference, interval/game-clock, permitted segment rights, transcript/visual distinction and disabled-coaching validation.
- Whitelisted public projection excludes private identity/notes/transcript/excerpts; no ingestion/provider/quota/approval flow changes.

## Contract/API

`build_index(root, *, knowledge=None, candidates=None)`; `search_index(index, query="", *, topic_id=None, role=None, champion=None, opponent=None, situation=None, evidence_state=None, patch=None, limit=100, offset=0)`; `validate_index(index)`; `validate_segment(segment)`.

Full documentation: `contracts/learning-room-v1.md`. Frontend author and root received early shape/API and actual artifact.

## Verification

- RED first: 10 tests failed because the read-only index API did not exist; retained `learning-data-red.log`.
- Additional RED hardening: index-level coaching enable and mismatched video URL were accepted before validation changes; retained `learning-data-red-hardening.log`.
- GREEN final: `python -m unittest tests_pregame.test_learning_room`: 12 tests PASS (0.116 seconds final run).
- `python scripts/build_learning_room.py --check`: PASS exact current artifact.
- `git diff --check -- <six owned paths>`: PASS.
- Focused green log: `/workspace/gp23-artifacts/learning-data-green.log`.
- Full pregame run was started against concurrently changing integration files, showed intermediate failure markers, and was stopped at root request with SIGINT (exit130) so root can run the final stable tree. Because unittest was nonverbose and interrupted before failure summary, failed test names are not recoverable from this incomplete log; **no full-suite pass is claimed**. The interrupted active test is `test_pc_coach.PcCoachTests.test_unreadable_original_sources_also_hide_revised_hypotheses`, stack in existing pc_coach/auto_review. Log: `/workspace/gp23-artifacts/learning-data-full-pregame.log`. Root reported its base906 run already passed and owns final complete integration run.

## Scope limits

- Existing source claims are conditional references, not newly independently verified expert evidence or current-patch compatibility.
- No acquired video/transcript/visual segment; link-only status remains truthful and new visual sample N=0.
- Taxonomy leaf mappings are navigation labels, not newly sourced tactical statements.
- Reflection prompts are explicitly app-authored, ungraded and tied to existing conditions/counterexamples; no new tactical engine.
- Browser, export/server integration, deployment, public HTTPS and efficacy verification belong to root/integration workers.
- Final full-suite verification remains pending root stable-tree run.

## Owned file SHA-256

- `coach_v1/learning_room.py`: `6a95618192386ccac7076426475b3235777ec50d1f0889ab915ea57945447f64`
- `scripts/build_learning_room.py`: `60e5148254cf5172f911a575c7d70323d19e1ce5c90caf71ef2c658d20e2c171`
- `config/learning_topics.json`: `6a30fe50b183ab49f232bbcc426cb3bd4c64ddb068704665cd93b8aa4037f7e3`
- `web_r4/learning-room.json`: `954d0997d88d31d979e0dd4bdce3e5440501388051b6f66aed05cd54750ea71d`
- `contracts/learning-room-v1.md`: `007a6c8d826aae867901f2fcccb9d79128a43f6fcf0c318b5311be33e8092a94`
- `tests_pregame/test_learning_room.py`: `c15f46a6c9bf2719041f55860d7f2657336c295850a2d25cc6b6da7e2e721060`


## Scoped review corrections and offline transcript adapter (uncommitted)

Root requested centralized commits, so this follow-up contains no git commit or amend. Five owned files changed; config taxonomy remains unchanged.

- Corrected `alternative_or_recovery`: null unless an explicit existing source `alternative_or_recovery` field exists. Counterexamples are no longer mislabeled as recovery.
- Added pure `append_transcript(index, raw_bytes, video_id, *, access_state, license_or_access_state, source_provenance, topic_assignments=None)`, reusing the existing `coach_intake.video.index_transcript` parser. Both permissions must be PERMITTED, visibility PUBLIC, raw hash exact, and duration explicit. ID/cue/time/order validation fails closed.
- Metadata-only transcript source and cue-window segment references; no raw transcript, private metadata, input paths or source text copied. Speech candidates remain unverified speech with scene false/game clock null/coaching false. Existing acquisition failures and link-only lessons are preserved.
- Optional per-cue operator decisions support multiple lessons sharing a segment, including a valid nonkeyword cue with empty lexical hints. Repeated identical ingestion is idempotent. No real raw input was accepted; default artifact remains zero accepted transcripts/segments/visual reviews.
- Build supports explicit accepted offline bundles. CLI `--accepted-inputs <manifest> --output <metadata file>` reads raw only and refuses raw/manifest/source-registry output collisions, including hardlink aliases. Resume manifest and exact command documented in contract.
- Search now NFKC/casefold term-AND. Optional `knowledge` resolves existing registry prose rather than storing a second corpus. `patch` filters exact source labels and separate `patch_state` filters metadata state. Root API must supply the loaded registry for full prose parity. Frontend worker received canonical signature and schema.
- `validate_segment` now projects `timestamp_state:VALIDATED` after actual rights/time validation. Frontend must also validate access/rights, integer bounds, source hash and video binding before opening a segment.

Verification: 20 focused tests PASS (latest log learning-transcript-green.log); default build --check PASS; scoped git diff --check PASS. RED evidence retained in learning-transcript-red.log, learning-transcript-search-red.log, learning-transcript-hardening-red.log and learning-transcript-raw-preservation-red.log. The raw-preservation counterexample caught an output hardlink alias before its fix. No full concurrent suite rerun, at root request; final complete stable-tree run belongs to root.

Latest file SHA-256 (supersedes earlier file hashes):
- `coach_v1/learning_room.py`: `12510f38a67ed69e5188e739b61eaadb66908ccdc17ea129daedc8ced1c1ad5c`
- `scripts/build_learning_room.py`: `958d6a386c9a63ea853e6999b4749225acd8ec243a678461e56e5ff6f5d0b352`
- `config/learning_topics.json`: `6a30fe50b183ab49f232bbcc426cb3bd4c64ddb068704665cd93b8aa4037f7e3`
- `web_r4/learning-room.json`: `b7a71d3bfe809b2388d34b358b7f5f7ebce162d6eccb0571d52f9d36d0e7de6f`
- `contracts/learning-room-v1.md`: `71442efb51bc6e538b027a5b987d01056002dd43791e4280fe7f7dbd953ef26c`
- `tests_pregame/test_learning_room.py`: `27914195dc9037751d9f942371fc23e028a0843033b107882f9e5b727a793dde`

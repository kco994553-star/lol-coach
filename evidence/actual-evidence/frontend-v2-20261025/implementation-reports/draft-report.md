# Frontend v2 partial draft / handoff report

## 1. Scope
Implemented only `web_r4/loading-draft.js`, `web_r4/loading.js`, `web_r4/loading.html`, and `tests_pregame/test_champion_handoff.py`; this requested report is the only additional file. No staging or commits. No engine, source facts, exporter, server, shell, or seal changes.

## 2. Adapter interface
Pure UMD `LoadingDraft` exports `createIntent`, `fromInput`, `previewTransfer`, `applyTransfer`, `toCompleteInput`, intent/draft encode/decode, session persistence helpers, and `returnLink`.

`createIntent` consumes the exact plan contract: champion, position, optional opponent/opponent_position, ally_support, enemy_support, reference, return_state. Opponent context requires its explicit position. Intent and nested state are immutable plain JSON. `previewTransfer` accepts a draft wrapper or raw input. A wrapper has `{schema_version:'lol-coach-gameplan-draft-v1',revision,input}`. `applyTransfer(preview,{replacements:['allies:3'],targets:{own:'allies:3'}},expectedRevision)` returns a new wrapper; it never mutates its source. Target keys are own/opponent/ally_support/enemy_support. Complete projection returns null while picks or own identity are incomplete.

## 3. Partial preservation
Both teams retain exactly five slots with `{champion:null,position:null}` blanks. Unknown positions remain unknown. No picks or positions are filled by inference. Side, patch, preferences and v3 scenario/v4 planning survive. Existing Coach validators validate scenario/planning; the strict engine remains the only complete-analysis entry point. PR138 baseline and its conflict semantics remain intact; the new adapter extends these for partial slot choices and does not call its narrower two-field service.

## 4. Explicit preview and conflicts
The real loading page shows each intended change, old/new champion and position, and a slot selector when no role target is known. Occupied slots require individual replacement checkboxes. Existing duplicates across either team block transfer with no automatic deletion. Correcting a duplicate in the form regenerates the preview and clears previous confirmations. Unrelated slots remain untouched.

## 5. Revisions and routes
The adapter checks expectedRevision. The page checks both current form revision and serialized session snapshot before applying; stale input regenerates the preview. Cancel only hides the preview and leaves URL and session draft unchanged. Complete apply analyzes before writes and produces a fresh #plan. Partial apply uses #draft and hides analysis. Existing #plan routes retain priority when read. Incoming handoffs use existing saved draft/plan context. Separate key: `lol-coach-gameplan-draft-v1`; existing complete-plan key remains supported.

## 6. Loading form repairs
fillForm clears all ten rows before filling a shorter/partial input. readInput carries schema, scenario and planning context. saveRoute updates that context after coach comparison controls so later transfer/form edits retain the changed assumptions. Existing PC import and engine/prose/scenario routes remain in place.

## 7. Defensive and storage behavior
Malformed routes, oversized/deep JSON, forbidden prototype keys, unknown fields/roles, invalid draft versions and external return targets are rejected. Catalog membership is checked before preview. Session read/write failures are caught; a failed set does not overwrite prior storage, and URL state remains available. Return state uses the agreed ChampionState fields, including finite 0..100000 detail_scroll and section enum overview/power/baseline/skills/matchup, plus optional local champion(s).html target. Return links use #state JSON.

## 8. Tests and red evidence
18 handoff tests include five real Chromium page tests (cancel/partial refresh, complete replacement/form clearing, scenario preservation after coach edits, storage revision race, duplicate correction, plus state contracts in Node). Initial missing-adapter RED: `/workspace/frontend-v2-artifacts/handoff-red.log`; missing-preview RED: `handoff-browser-red.log`; validation RED: `handoff-hardening-red.log`; duplicate correction RED: `handoff-duplicate-red.log`; malformed route RED: `handoff-route-red.log`; new return fields RED: `handoff-return-red.log`.

The initial scenario harness tried a control before opening its detail; that timeout log is retained as `handoff-scenario-red.log`. After correcting the harness, the real regression failed on missing scenario.overrides. A clean mutation check serves loading.js without its context save in memory (no shared file mutation) and reproduces that failure: `handoff-scenario-mutation-red.log`.

## 9. Final verification
`python -m unittest tests_pregame.test_champion_handoff tests_pregame.test_champion_baseline tests_pregame.test_loading_presentation tests_pregame.test_loading_strategy tests_pregame.test_loading_coach tests_pregame.test_loading_context -v`: **81 tests passed**, final log `/workspace/frontend-v2-artifacts/handoff-regression.log`. Node syntax checks for both changed JS files and git diff --check passed. Root requested ownership of the whole-repository run; no full-suite claim is made here. Earlier intermediate green logs predate the final return-state extension; final regression log is authoritative.

## 10. Integration handoff
QA worker has the real hooks: #handoff-preview, .handoff-change[data-key], select[data-handoff-target], input[data-handoff-replace], #handoff-apply, #handoff-cancel, #handoff-return. Root owns export allowlisting of the new asset, shared integration, full-suite checks, seal and publication. Independent browser QA is in progress outside this scope. No deployment claim.

### Independent review follow-up
Review found preservation defects in actual document navigation and asynchronous PC import, which the initial same-document tests missed. Added six real Chromium regressions (24 handoff tests total, 11 browser): fresh explicit plan → actual champion CTA round trip with cancel/apply; Back after edited comparison assumptions; blocked-session PC import with an active old preview; held PC response after newer example input; held PC response after newer coach assumptions; and explicit-plan priority plus invalid-restore storage preservation.

Restored plans now save canonical input only after strict analysis and supported-period validation succeed. The explicit URL remains unchanged and outranks older session drafts. Restored history gets a planGroup so edited assumptions survive Back to the summary, and popstate forwards its original event. fillForm invalidates active previews and advances an input epoch regardless of storage. Manual edits and programmatic scenario/planning/preference changes also advance the epoch. PC import checks its captured epoch before applying a response, preserving newer edits. Programmatic draft restores preserve their supplied draft revision while still advancing the separate request epoch.

RED evidence: `handoff-review-red.log` (round trip and Back), `handoff-review-pc-red.log` (storage-blocked preview and late form import), `handoff-review-coach-red.log` (late import versus coach assumptions). These are real behavior failures, followed by green runs; the first Back fix required assigning initial history metadata in addition to forwarding the event. No source validation was relaxed, no authentication handling was changed, and PC tests use isolated synthetic fixtures.

Final follow-up verification: `python -m unittest tests_pregame.test_champion_handoff tests_pregame.test_champion_baseline tests_pregame.test_loading_presentation tests_pregame.test_loading_strategy tests_pregame.test_loading_coach tests_pregame.test_loading_context -v` passed **87 tests**. Authoritative updated log: `/workspace/frontend-v2-artifacts/handoff-review-regression.log`. Node syntax and diff whitespace checks passed. Root continues to own the full-suite run, export/seal and integration. Files released for independent QA and sealing.

# GP23 F evidence-runner report

Status: final EXACT_COMMIT evidence re-evaluated and evaluation document updated. Source commit 6e2e255dc774525b0054ae1e711d9a7953d83957. Earlier provisional observations below are historical. No agent commit made, per root instruction.

Owned changes: `scripts/export_gameplan_2plus3.js`, `tests_pregame/test_gameplan_2plus3_examples.py`, `docs/gameplan-content/gameplan-2-plus-3-evaluation.md`. No shared implementation files changed.

## Selection and evidence

Seed 20261025. xorshift32/Fisher-Yates over sorted catalog IDs. Five independent role-complete 10-pick samples; 10 unique champions each. Synthetic arbitrary assignments disclosed. TOP selection constrained to official Tank tag plus official control-mechanic fact, with source excerpt/URL/hash retained. Final selection after correcting pre-freeze control-word regex: TOP Trundle, JUNGLE Darius, MID Ekko, BOTTOM Aurora, SUPPORT Karthus. No engine output quality filtering or redraw.

V5 inputs use `loading-situation.js.defaultState()` with only ally_followup assumed AVAILABLE, source user-scenario, observed_at null. Paired input changes only `/situation/fields/ally_followup/value` to UNAVAILABLE. Every other situation field remains unknown.

Exporter calls actual E.analyze and P.project(currentOnly:true), stores full supplied input/full report/full view, every projected string with JSON pointer, exact JSON-escaped strings in Markdown, support limits, input/output changed paths, source SHA plus SHA-256 file hashes and case hashes. --require-bound rejects source files not equal to HEAD (including new untracked modules); unbound export says WORKTREE_SNAPSHOT/source_commit:null. Runtime source mutations during export cause failure. N=0, UNMEASURED throughout.

## Tests and current dependency

RED: initial four tests failed because exporter absent. Initial v4 GREEN: 4/4 passed, including real-engine raw-output replay and independent isolated git repo source-binding mutation test. V5 one-leaf test then RED (v4 input version), adapted to v5 and passed. Current v5 test run: 4/4 PASS after core resolver landed. Actual-output integration includes byte-for-byte repeat-export checks across all generated artifacts.

Provisional v4 evidence only: `/workspace/gp23-artifacts/examples-provisional/` (WORKTREE_SNAPSHOT, not committed, not final evidence). Evaluation draft contains six 0–2 dimensions per each of five actual provisional outputs, exact path citations and identifying case hashes, explicit separate P0/P1 gate. It notes low specificity/GENERAL_ONLY for all five and flags jungle generic last-hit self-action wording versus camp goal for GP23-19 review. No tactical approval or gameplay accuracy claim.

## Earlier root finalization checklist (completed for evidence)

1. Complete v5 resolver/projection.
2. Run `python -m unittest tests_pregame.test_gameplan_2plus3_examples -v` and relevant integration suite.
3. Commit all stable runtime source and exporter; do not generate bound output from dirty source.
4. Run `node scripts/export_gameplan_2plus3.js --seed 20261025 --require-bound`.
5. Re-evaluate final five pairs and replace provisional review with actual final-source citations; retain poor scores and limits honestly. Check P0/P1 separately.
6. Commit generated evidence/doc changes, preserving manifest source_commit (runtime source commit, which can precede evidence-only commit).

Final source-bound artifacts are now in the repository; see the final re-evaluation below.

## Actual v5 evaluation update

Generated unbound original v5 data at `/workspace/gp23-artifacts/examples-v5-provisional/`; source base a12330d7030c7b74dc748820b68e8b7841940148, WORKTREE_SNAPSHOT/source_commit:null with runtime file hashes. Kept synthetic roster and seed unchanged. Replaced evaluation draft with actual v5 six-dimension scores and exact output quotations for all five pairs. All 15 baseline phase cards GENERAL_ONLY. All five fight CONDITIONAL_ROLE, current threat priority UNKNOWN, execution UNKNOWN→BLOCKED on allyfollowup loss. Specificity 0 for TOP/MID/BOTTOM and 1 role-principle-only for JUNGLE/SUPPORT; no champion-unique claim. Old v4 evaluation removed.

Concrete P2 found in this exact original v5 snapshot: duplicated identical operations paragraphs 0/1 across all five. Engine owner fixed afterward and reported core 13 tests PASS; original outputs retained unmodified, final bound regeneration must confirm fix.

Saved separate additional actual-engine counterexamples `/workspace/gp23-artifacts/examples-v5-counterexamples.json` (unbound in-progress probe, not a replacement for selected five): stale AWAY remains ineffective and CHECK_WAVE; ready TOP tank DISRUPT→PROTECT when ally carry threatened, then BLOCKED on followup loss; DUEL with unavailable external allied followup gets coherent solo action/stop and READY. Evaluation classifies P0/P1 safety boundaries separately and finds no new P0/P1 in these narrow probes, without certifying whole-release absence. Threat priority remains unresolved and contribution qualitative; unsupported role output generic, documented as PARTIAL support.

No commits made. Root source freeze and final exact-bound folder still pending.

## Final bound five re-evaluation

Source `6e2e255dc774525b0054ae1e711d9a7953d83957`, manifest EXACT_COMMIT, repository `evidence/actual-evidence/gameplan-2plus3-20261025/examples/`. Read-only verification recomputed every manifest source hash and all five case hashes; replayed E.analyze and P.project for 10/10 supplied inputs and got serialized full-report/full-view identity. Exactly one leaf differs in 5/5 pairs: `/situation/fields/ally_followup/value`. All 30 phase cards remain GENERAL_ONLY. All 10 outputs have distinct operations paragraphs 0/1: duplicated-prose P2 resolved by engine, without raw evidence editing.

Final six dimensions in order accuracy/specificity/actionability/risk-goal visibility/uncertainty/coherence:

- TOP Trundle: 1/0/1/1/2/2 = 7/12.
- JUNGLE Darius: 1/1/1/1/2/2 = 8/12.
- MID Ekko: 1/0/1/1/2/2 = 7/12.
- BOTTOM Aurora: 1/0/1/1/2/2 = 7/12.
- SUPPORT Karthus: 1/1/1/1/2/2 = 8/12.

Scores and exact final file links/hashes/quotations are in docs/gameplan-content/gameplan-2-plus-3-evaluation.md. Low specificity retained: all five fight goals CONDITIONAL_ROLE; current per-actor threat priority UNKNOWN; contributions qualitative, unsupported roles generic, arbitrary role assignments do not prove champion role suitability or champion-unique tactical support. Aurora BOTTOM is not a Marksman mechanics validation. N=0/UNMEASURED.

Re-ran stale-jungle, tank protect/disrupt/followup loss, and solo-without-external-followup counterexamples against the same hash-verified frozen runtime. All retained intended bounded behavior. No new P0/P1 observed within these five pairs and probes; global release gate remains separate. Historical provisional findings retained in evaluation history paragraph.

Owned final changes: evaluation.md only plus this external report. No changes to manifests/raw evidence/runtime; no commits. Root can commit final evaluation and hand off overall integration state.

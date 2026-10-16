# Independent whole-branch review — coaching-quality pilot

Reviewer: `/root/pilot_branch_review`. Compared the working branch, including new files, with main `9da650ae1ec000f3bb66d90be351174fe3c731f3`. Read `AGENTS.md`, the pilot contract and implementation plan. Reviewed new advice and receipts, PC integration and screenshot/browser receipt, offline extraction and trusted workflow, reporting, source amendment, required CI selection, and new tests. No provider calls, collection, private cache access, USER writes or predecessor test execution occurred.

## Findings

1. **P2 — impossible champion-level histories can become exact observations.** `coach_v1/pilot_observations.py:80` checks duplicate timestamps only within the requested level. A participant with `LEVEL_UP(level=2,timestamp=120000)` and `LEVEL_UP(level=3,timestamp=60000)` is accepted as exact for both targets. With opponent level 2 at 125000, the audit asserts `earlier_n=1` rather than retaining UNKNOWN. Reproduced with an isolated fabricated envelope accepted by `PostgameStore`; no actual game is claimed. Cross-level ordering conflicts should invalidate the participant's level history without frame fallback. Status: reported to implementer, awaiting fix/review.

2. **P2 — imported anonymous output is not checked against its source binding.** `scripts/report_quality_pilot.py:29` accepts any schema-valid `observations.json` and labels it AVAILABLE; `scripts/verify_quality_pilot.py:118` validates only that schema. Neither requires or verifies the workflow's `source-binding.json`, expected checkpoint, report-byte hash, extractor source hashes, or selected 89-match/108-participant scope. A stale report or the isolated fabricated test envelope's valid report can therefore be presented as trusted existing-cache output. Require the sibling binding and validate it before making the availability claim and before accepting published data. Status: reported to implementer, awaiting fix/review.

3. **P2, resolved during review — restore could select a different checkpoint.** The generic recovery helper selects newest trusted history. The workflow now explicitly checks run `38410710876` and artifact `11822391323` before decryption (`.github/workflows/coaching-quality-offline.yml:43`) and 89 distinct matches / 108 selected participant observations after extraction (`:62`). A changed source fails instead of silently substituting another PRO cache. Inspected the fix; actual restoration remains pending trusted Actions.

## Product and evidence assessment

The seven revisions give concrete choices while retaining legitimate uncertainty. Ornn/Fiora compares wall entry with response without the dash and does not treat Riposte confirmation as sufficient. Ahri/Zed separates available follow-up from chasing. Caitlyn compares hit angle and recoil position and exempts urgent defense from a preparation checklist. Lee Sin follow-up compares forward/current/allied-side choices instead of a blanket retreat. Nautilus anchor and ultimate cards reassess actual endpoints or moving paths without guaranteeing another location. Ashe ties scouting to the next intended segment, distinguishes unusable/inapplicable information, and keeps unknown routes unknown.

The new versions remain HYPOTHESIS/HOLD, with source facts and unvalidated tactical proposals separate. Original objection/rejection blocks the revised lineage. Only a matching valid revision suppresses its corresponding legacy display. The UI visibly labels both hypothesis evidence and the independent skill-interaction topic; the inspected screenshot shows the revised Caitlyn card and retains unrelated legacy cards. No USER approval is inherited.

The observation model otherwise preserves meaningful limits: selected participants and distinct matches are separate, SKILL_LEVEL_UP is not champion level, equal events deduplicate, frame bounds remain intervals, overlap/touching stays UNKNOWN, 10/15 gold requires an exact shared frame, and jungle kill involvement is explicitly not first gank. Output uses closed vocabularies and recursive numeric/key checks rather than emitting raw identities. Trusted Actions keeps plaintext ephemeral and uploads only anonymous output and its binding.

The Q15 report uses actual MATCHUP absolute sampled-bin gold, never pooled ROLE_POPULATION rates; unavailable matchup cohorts remain absent, wide-interval omissions remain omitted and a missing eligible denominator remains null. No matched player-known POV exists, so eligible/evaluated scenes are zero and action agreement/effect/accuracy remain null. This is improved conditional wording and descriptive measurement, not demonstrated coaching efficacy.

## Verification reviewed

The independent changed-scope test command ran only the four new pilot modules and passed (27 tests at the time of this review). Existing `delta-local-after.log` likewise records the pilot-only checks. Reused browser receipt `browser-20261016T104508452366Z/runner.json` passes its four changed scenarios with no browser errors or unexpected writes; its UI/advice source hashes match the reviewed files. Screenshot inspected. The amended verifier preserves predecessor bytes except the explicit six allowed modifications and archives their originals; required workflows select pilot checks and reuse completed v2.3 evidence. Final source sealing, fresh expected-head CI and actual trusted cache restoration are implementer follow-ups, not claims made by this review.


## Implementer fix evidence (after independent review)

- Cross-level event chronology and event-vs-frame contradictions now invalidate
  level history with UNKNOWN, without a frame fallback over inconsistent events.
  `test_cross_level_chronology_and_event_frame_contradiction_are_unknown`
  witnessed RED then GREEN. Two existing NEW synthetic exact-event fixtures were
  corrected to keep their earlier minute frame below the event level; historical
  tests/fixtures remain untouched.
- `load_bound_report` now requires the sibling exact binding, expected checkpoint,
  89/108 scope, byte hash, fixed source-file set, source commit ancestry/git bytes
  and current extractor hashes, zero network/provider requests and no accuracy.
  Both report and verifier use it; workflow self-validates its public output.
  Schema-valid unbound/fabricated reports are rejected. Missing/invalid binding
  RED→GREEN receipt: review-fixes-{red,green}.log. Positive real-artifact validation
  awaits the first offline trusted run rather than a fabricated REAL assertion.
- Targeted changed statistics/report tests:18PASS. No old suites, provider calls
  or actual private inputs used in this fix pass. Checkpoint pin was already fixed.
  These are implementer verification notes, not a second independent approval.

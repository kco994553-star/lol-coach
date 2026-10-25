# Champion statistics task report

Status: implemented and targeted verification passes. No staging or commits.

Files owned and added:

- `coach_v1/champion_stats.py`
- `scripts/build_champion_statistics.py`
- `web_r4/champion-stats.json`
- `tests_pregame/test_champion_statistics.py`
- `docs/gameplan-content/champion-statistics-v1.md`

Exact-scope public summaries and 13 disjoint five-minute ending-duration bins
are implemented, with exact opponent summaries, weighted total wins/N,
recomputed Wilson95, null empty gaps and fixed n>=100 drawable threshold.
Public projection is an allowlist with no match/member-hash arrays or player IDs.
Unsupported pick/ban/rune/build/skill-order fields are explicit. Existing
outcome/power APIs, source/raw data and authored profiles remain unchanged.

Real generation validates October11 outcome50 gzip/raw/canonical hashes and the
strict outcome schema; checks October13 full power275 gzip/raw/canonical hashes
and the strict power schema. The full275 archive lacks per-cohort member hashes,
so it cannot provide exact champion-role unique-match N. The public
`position_source` therefore explicitly uses outcome50 and records the considered
275 archive, digest and fallback reason. No minute-row counts, max-N estimate,
snapshot pooling or minute-resource fallback are used.

Command: `python scripts/build_champion_statistics.py` (optional `--output PATH`).
The generated real file contains 125 observed champions; both source counts are
50. Identical generation runs produced byte-identical output. Summary status is
NO_DATA/INSUFFICIENT_DATA/READY, with READY at n>=100. Current real50 means no
real curve bin is drawable; descriptive percentages still expose sample N.

Verification:

- Initial test-first red: 8 expected assertion failures for missing module,
  `/workspace/frontend-v2-artifacts/data-red.log`.
- Extra exact coverage-scope test-first red: mismatch accepted before guard,
  `/workspace/frontend-v2-artifacts/data-scope-red.log`.
- Green: `python -m unittest tests_pregame.test_champion_statistics tests_pregame.test_outcome_stats tests_pregame.test_power_stats -v`:
  **43 tests passed**, including 10 new tests, 6.422s;
  `/workspace/frontend-v2-artifacts/data-green.log`.
- New tests cover known Wilson values, weighting, exact absent opponent/patch/tier,
  0/5/10/60+ boundaries, gaps, 99/100 draw threshold, count/hash/rate/scope rejection,
  source-scope mismatch, hash reader rejection, distinct coverage provenance,
  private-field exclusion, input preservation and real deterministic generation.
- Full `unittest discover -s tests_pregame -t . -q` was started per TDD skill,
  then interrupted at root's request because root coordinates final stable full
  suite and existing tests can mutate shared fixtures. Exit130/SIGINT, no
  completed-suite claim. At interruption it was running
  `test_champion_handoff.ChampionHandoffTests.test_browser_complete_replacement_clears_form_and_keeps_context`;
  `/workspace/frontend-v2-artifacts/data-suite.log`. No failures had been
  printed before interruption. No restoration performed and no official
  data/current-pointer tracked changes were detected. Baseline HEAD:
  `fe6526a97345826818a6159fde491bbbeb32dfc9`.

Remaining integration: root's final stable full suite/browser/export review.
No live data acquisition, network/model calls, tactic claims or n100 threshold
relaxation. Role coverage beyond the retained outcome50 is explicitly unavailable.

## Approved P1 follow-up — resource/marker references

Added `growth_dataset=` support, a distinct real275 `growth_source`, and each
position's `growth` resource/marker projection. FE worker received and confirmed
the exact contract. Selected resource bins are 5/10/15/20/25/30; source
champion/reference means, separate participant/match Ns, delta Student-t CI and
legacy visible/omission decision are preserved. CI explicitly belongs to the
champion-minus-pooled-role rate delta, not the champion average. Resource
visibility does not use the outcome n100 rule. Level markers are first-observed
frame interval censored; item markers remain observed purchase candidates, not
build advice. Metric-duplicated markers are deduplicated without multiplying N.
No official item names added because real275 has no matched item catalog or
item markers.

The new public artifact is minified: 3,033,345 bytes, SHA256
`3c0d85514a8f2b9e0fb5039efebd84657e9e9c2c6a47c279ea031d26303aa763`.
It contains 164 champions, 284 growth roles, 4,536 resource rows (3,222 visible),
1,299 deduplicated LEVEL markers, zero ITEM markers. Extra champions/roles have
no invented outcome or observed-role N. Outcome and role coverage remain50;
resource source remains275. The new resource references account for the larger
artifact despite removing formatting whitespace.

Red evidence: `/workspace/frontend-v2-artifacts/data-growth-red.log` records the
three new behavioral tests rejecting the absent growth API (expected TypeError).
Green evidence: 13 champion projection tests passed in6.277s;
`/workspace/frontend-v2-artifacts/data-growth-green.log`. Targeted outcome/power
regression result is recorded in `data-growth-regression.log`. No full shared
suite started for this follow-up. Root coordinates final suite/review.

Final P1 targeted verification: `python -m unittest tests_pregame.test_champion_statistics tests_pregame.test_outcome_stats tests_pregame.test_power_stats -v`
passed **46 tests in6.440s**, exit0; `data-growth-regression.log`.

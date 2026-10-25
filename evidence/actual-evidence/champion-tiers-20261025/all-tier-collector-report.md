# All-tier collection implementation report

Date: 2026-10-25 UTC. Workspace: `/workspace/lol-coach-champion-tiers`, assigned base `maind1d0005`. Scope: local implementation and fixture verification only. No commit/amend, provider dispatch, credential attempt, external write or delegated agent performed by this worker.

## Implemented

- Admission now accepts exactly ten leaf League-V4 seed tiers; ALL/MASTER_PLUS/unknown are rejected as acquisition targets. Config records the new user amendment and default browser MASTER_PLUS independently from leaf admission. Historical Master+-only contract and collected records remain unchanged.
- New additive policy document: `docs/gameplan-content/all-tier-collection-v1.md`. Existing independent Challenger reference auxiliary policy remains intact (`auxiliary_needed` and its tests retained).
- Resolver/workflow now select one bounded tier/division target per existing scheduled run. Forty slots cycle ten leaf tiers and four division inputs; apex endpoints ignore division, explicitly disclosed. Lower-tier sampling is still at most page 1 and 40 players, with no full-tier coverage claim. Manual all-ten leaf selection is available. Existing daily cron, trusted main secret path, pinned actions, concurrency, renewal gate, request/match/player/page/retry/deadline settings and response pacing remain.
- Collector produces the new private `champion.opponent-results.v1` companion through the data owner's `coach_v1.matchup_results` module. New match/timeline pairs require no additional result request. Power-known/result-missing IDs trigger match-detail-only backfill, with no extra timeline. All work shares the original request counter/rate/deadline and match-work ceiling.
- Result identity is independent of power completeness. The digest-bound `champion.result-completeness.v1` sidecar records only validated result hashes and must agree with exact private state before provider work. Missing/corrupt ledger or conflicting result evidence fails closed. Failed/ineligible result evidence does not become complete. Already fully complete same-tier power/result records skip match-work slots so bounded later backfill can progress.
- Previously retained anonymous results can add a newly observed seed membership without redundant detail/timeline fetches. Membership provenance carries tier, sampled division, retrieval/window and safe run digest. Unspecified patch pins on the first reused eligible result before another patch can be admitted.
- New result companion and completeness sidecar are restored/retained only in the private 90-day sufficient-state artifact. The public seven-day aggregate artifact receives no private result roster. CLI prevents new private state paths under its public aggregate directory. Publish-only initializes/restores result state without provider requests and never manufactures final results from legacy power records.

## Files owned and changed

`coach_v1/riot_collection_policy.py`, `config/riot_collection_policy.json`, `scripts/resolve_riot_collection.py`, `scripts/collect_power_stats.py`, approved expanded ownership `coach_v1/riot_collector.py`, `.github/workflows/riot-power-collection.yml`, `tests_pregame/test_riot_collection_policy.py`, `tests_pregame/test_master_statistics_policy.py`, `tests_pregame/test_riot_collector.py`, new `docs/gameplan-content/all-tier-collection-v1.md`.

No old v1 validator, historical contract/data, protected decision record, source candidate, reference API or raw-history file was edited. Data-source module changes belong to the separate data worker.

## Evidence

RED fixture evidence was captured before implementing the new interfaces/admission behavior:

- `/workspace/gp23-artifacts/all-tier-policy-red.log`
- `/workspace/gp23-artifacts/all-tier-results-red.log`
- `/workspace/gp23-artifacts/all-tier-result-state-red.log`

Final focused run, after the patch-pinning review correction: **41 tests PASS**.

```
python -m unittest tests_pregame.test_master_statistics_policy tests_pregame.test_riot_collection_policy tests_pregame.test_riot_collector
```

Log: `/workspace/gp23-artifacts/all-tier-collector-targeted-green.log`. Covers all 10×4 endpoint routes, one-target rotation, expired resolver/no network, aggregate/unknown leaf rejection, first401/403 zero retry, bounded429 waits, original request ceiling, result detail-only backfill, new-pair zero extra requests, cross-tier membership reuse, completed-result starvation prevention, exact first patch, requested match identity, invalid result omissions, digest-ledger tamper rejection before provider, CLI round trip/private output exclusion, publish-only restoration and original collector safeguards.

Compatibility run after final collector changes: **58 tests PASS**.

```
python -m unittest tests_pregame.test_outcome_collection tests_pregame.test_outcome_stats tests_pregame.test_power_stats tests_pregame.test_v20_stats tests_pregame.test_role_baseline_view tests_pregame.test_challenger_reference
```

Log: `/workspace/gp23-artifacts/all-tier-collector-compatibility-green.log`. An earlier command named two nonexistent test modules; that invocation failure is transparently retained in `/workspace/gp23-artifacts/all-tier-collector-compatibility-invocation-error.log`. The correct accumulator/progress regression coverage resides in `test_v20_stats` and `test_role_baseline_view`.

Scoped `git diff --check` passed with no whitespace errors.

## Present acquisition limits

The checked-in renewal window still ends `2026-10-16T10:16:49Z`; no new Riot request was made. Current local all-tier acquisition is not claimed. Seed cohorts do not verify A's or other participants' historical ranks. Old power-only records still require authorized future detail backfill; restoration does not invent their winners. Ranking/display minimums, free-only/no-paid rules and user decision boundaries remain unchanged. This worker does not claim frontend/public projection completion; those are root/data worker responsibilities.


## Full-suite compatibility correction — final collector freeze

The root's stable full pregame suite exposed one actual regression in unchanged `tests_pregame.test_recall_collection_v23.RecallCollectionTests.test_actual_challenger_extraction_filters_exact_patch_and_exports_safe_dataset`: the new work counter consumed `max_matches=1` on an older-patch detail before finding the eligible requested-patch match. The original recall test was not edited or weakened.

Reproduced independently RED: `/workspace/gp23-artifacts/all-tier-recall-regression-red.log`.

Minimal collector correction moves in-scope work accounting after exact-patch/queue checks. Legacy collection retains its original accepted-pair ceiling used by RecallCollector. Result mode counts scoped detail/backfill/membership work. Off-patch details still consume the unchanged request/deadline budget and never trigger old-patch timeline requests. A new collector test covers both legacy and result-backfill paths plus tight shared request-budget exhaustion.

Immediate collector + unchanged recall + outcome-collection regression run: **46 PASS**, `/workspace/gp23-artifacts/all-tier-recall-regression-green.log`.

Final expanded collector/policy/unchanged recall/outcome/power/accumulator/reference compatibility run: **111 PASS** (12.068s); see `/workspace/gp23-artifacts/all-tier-collector-recall-outcome-compat-green.log`. The new doc's match-ceiling wording was clarified to preserve the inherited accepted-pair semantics. No request quota, auth behavior, source history, existing recall test or other worker source changed. Source frozen again after this fix.

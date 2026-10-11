# Q15 auxiliary ending-duration outcomes

Authority: USER_QUEUE_V1.6_2026-10-11; `contracts/outcome-v1.md` at `6f0e9b3`,
its timestamp clarification `contracts/outcome-v1-amendment.md` at `5e6cbf5`,
and `contracts/outcome-v1-consistency.md` at `9657177`. This companion leaves
`pregame.power-data.v1` unchanged. It describes results of sampled games that
ended in a duration bin, without explaining fighting strength or game phases.

## Official fields and source boundaries

The [official Riot Match-V5 schema](https://developer.riotgames.com/api-details/match-v5)
was retrieved on 2026-10-11: 167797 bytes, SHA256
`fb40838f6160a3ede81ce59b844e295328fda4c7ecb5f0d18f4f2f6869f2d64d`.
The official portal's `api_reference_page.dc62e0a4d2b9.js` loads this schema.
No Riot game API call or credential was needed for that documentation check.

Only already-fetched private match/timeline response pairs are read. Their KR
match metadata IDs must agree. Match info must identify queue420, map11,
CLASSIC, a supported exact patch and a collection-window start timestamp. Each
team needs one participant in each of the five canonical positions. Official
MIDDLE and UTILITY map to MID and SUPPORT; canonical aliases are also accepted.
All ten participant IDs are distinct, champions are canonical bounded names,
and both teams have opposite known boolean `win` fields. All ten participant
`win` fields must be actual booleans agreeing with their team. Missing,
conflicting, string, numeric or unknown result values contribute no trial.

Riot's schema states that older Match-V5 `gameDuration` values used milliseconds,
while the post11.20 representation uses the maximum participant `timePlayed`
in seconds. This module requires patch>=11.20, a positive integer
`gameDuration`, known nonnegative integer `gameStartTimestamp` and
`gameEndTimestamp`, and end>=start. The end timestamp certifies the modern
representation; it never supplies a duration. Riot warns that it can occur
later than the actual end, so even a greatly delayed timestamp does not change
the reported-duration bin.

Timeline metadata must match, but frame count, frame interval and frame
statistics do not determine result eligibility. Thus the outcome companion can
have more eligible matches than the power dataset. Consumers must bind the
collection provider, patch, tier, window and digest honestly, without asserting
equal eligible hash sets. No extra API request is required.

The current League seed tier defines the cohort; historical ranks of every
participant are unavailable. League selection, repeated players, convenience
sampling and outcome-dependent duration can affect coverage and independence.
The official schema does not establish a reviewed termination enum or reliable
remake classifier here. No early-duration cutoff guesses either one; observed
consistent wins include surrender outcomes. These limits appear in every
dataset. Real acquired samples remain0 and coaching accuracy remains null.

## Estimator and uncertainty

For each eligible match, `minute=floor(reported_duration_seconds/60)` labels
the left-closed interval `[minute,minute+1)` in minutes. This is a display bin,
not a gameplay threshold. A match whose duration is119 seconds contributes to
minute1;120 and179 seconds contribute to minute2. Missing bins are absent.

Each cohort contains at most one binary result per distinct match. Same-role
opponents playing the same champion are excluded from that champion's cohorts;
other nonmirrored roles can still contribute. `CHAMPION_ROLE` describes that
champion/position against all sampled opponents, rather than subtracting a
population win rate. `MATCHUP` restricts the actual opposing champion. The
selector chooses an available exact matchup per ending bin, then the all-
opponent cohort. It applies no arbitrary sample-sufficiency threshold.

With `n>=1` eligible distinct matches and `w` observed wins, `p=w/n`. The
[NIST Wilson score interval](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm)
supplies the nominal two-sided95% interval. With
`z=statistics.NormalDist().inv_cdf(0.975)`:

```text
d = 1 + z²/n
center = (p + z²/(2n))/d
half = z*sqrt(p*(1-p)/n + z²/(4n²))/d
CI = [max(0,center-half), min(1,center+half)]
```

This is `WILSON_SCORE_95.v1`, with no external numerical dependency. One trial
makes a CI calculable, without establishing sample sufficiency or population
accuracy. For a single observed loss the interval is approximately
`[0,0.793450685623]`; for one win it is `[0.206549314377,1]`. Five wins in ten
games yield approximately `[0.236593090513,0.763406909487]`. Finite-sample
coverage and independence are not certified for this convenience sample.

The consumer displays an auxiliary table with interval, `w`, `n`, `p`, and CI.
It draws no trend line and offers no tactical, causal, phase or strength claim.

## Typed public API and allowlist

`coach_v1/outcome_stats.py` implements:

```python
build_outcome_dataset(pairs, *, source) -> dict
validate_outcome_dataset(dataset) -> dict  # copied object or ValueError
select_outcome_view(dataset, champion, position, patch, tier,
                    opponent_champion=None) -> dict
```

The builder accepts exactly the twelve safe source base fields: provider,
platform, regional, queue_id, map_id, tier, patch, window_start, window_end,
retrieved_at, sample_kind, endpoints. It derives formula_version,
duration_bin_policy, mirror_policy, result_policy and all eight fixed
limitations from the contract. Power-specific precision, collection and item
catalog fields must be stripped before calling it. A null patch may select
the first eligible exact patch; later patches are withheld, never combined.

The dataset permits only schema_version, status, source, samples, cohorts and
coaching_accuracy. Source permits only the twelve base and five derived fields.
Samples permit real_matches, synthetic_matches and hashed_match_ids. Cohorts
permit champion, position, patch, tier, comparison, opponent_champion and
points. Points permit minute, n, wins, win_rate, ci95 and input_match_hashes;
ci95 permits only low/high. Every identifier is a SHA256 whole-match hash.
No player identities, raw IDs, raw responses, API keys or arbitrary fields are
permitted. Provider/sample_kind parity prevents synthetic data being counted
as acquired real data.

The validator checks finite values, exact field allowlists and source policies,
deduplicated cohort identities, exact cohort patch/tier lineage, unique bins,
point hash count equal to `n`, hash membership in the dataset and disjoint
hashes across bins within each cohort. Every dataset hash contributes to a
point. Nonempty data requires a modern post11.20 patch and both official
match/timeline endpoint declarations. Empty older-patch requests withhold
observations without guessing the old duration unit. It recomputes `w/n` and
Wilson intervals within1e-12. It cannot prove the
authenticity of a raw result from anonymous counts alone: caller trust and
documented collection provenance remain necessary. Hashes permit binding and
deduplication, without publishing the original responses.

Complete builder-produced cohorts are required. At each champion/position/
patch/tier/minute, matchup hashes form a disjoint partition of CHAMPION_ROLE
hashes; their `n` and wins sum to its totals. Reversed A-vs-B and B-vs-A points
have the same minute, hash set and `n`, and complementary wins summing to `n`.
Each whole-match hash has one ending minute globally across roles and comparisons.
The validator rejects missing base/reverse cohorts, reassigned bins/hashes and
contradictory totals even when each point's Wilson interval is individually
correct. These public consistency checks do not establish raw authenticity.

`READY` requires nonempty points. `INSUFFICIENT_DATA` and `BLOCKED_EXTERNAL`
contain no points or sample estimates. Selected points add comparison and
opponent_champion. Missing or blocked views return UNKNOWN with absent points.
Main owns optional collector/CLI/workflow outputs and server/UI integration;
external collection failure leaves no usable companion, never an empty
result masquerading as an estimated win rate. Public artifacts contain only
validated anonymous aggregates; all raw data stays in temporary memory.

## Verification

Twelve synthetic tests initially failed with the expected missing-module
assertion, then passed after implementation. A thirteenth test exposed and
then guarded unsupported nonempty patch/endpoint provenance. Three further
tests first exposed inconsistent public aggregation, then passed after the
complete-partition/reverse-result checks. A further RED/GREEN case binds each
whole-match hash to one global ending minute. All17 targeted tests pass. They check the
Wilson values above, true zero-win uncertainty, duration boundaries, delayed
end timestamps, missing/conflicting booleans, modern duration units, paired
metadata, five official role labels, mirrored champions, deduplication,
sourcekind separation, per-bin fallback, absent frames and input immutability.
Malformed public counts, formulas, CIs, hashes, mixed lineage and leaked fields
are rejected. Fixture claims are always SYNTHETIC unless testing explicit
lineage validation; no test receipt demonstrates real acquisition.

`python -m unittest discover -q` passed454 tests with one preserved external
source skip in45.265s before the final partition-only refinement. The skip is
`setUpClass (tests_r7_player_grounded.test_postgame.PinnedPostGameSourceTests)`:
`R7_POSTGAME_RAW_DIR` is required for exact-byte source integration. Main
authorized targeted outcome checks after that refinement and owns the final
integration/browser/CI verification. No real games were fetched for these tests.

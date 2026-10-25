# Champion statistics public projection v1

`web_r4/champion-stats.json` uses format `lol-coach-champion-statistics-v1`.
It is generated offline from preserved anonymous aggregates. It makes no network
or model calls and does not change source aggregates or existing statistics APIs.

Generate deterministically from the repository root:

```sh
python scripts/build_champion_statistics.py
python -m unittest tests_pregame.test_champion_statistics -v
```

The generator checks compressed-file SHA-256, decoded-file SHA-256, canonical
dataset digest, source scope and existing strict dataset validators before
writing the public result. A failed binding leaves the existing output unchanged.
There is no generation timestamp; identical sources produce identical bytes.
`--output PATH` writes a review artifact elsewhere without changing the public file.

## Source and role coverage

Ending results use the manifest-bound October 11 snapshot: 50 real KR ranked
solo queue (420) matches, patch 16.20, current CHALLENGER league seed cohort.
This tier does not establish every participant's rank when the match occurred.
The source records the retrieval time, sampled period, exact canonical digest,
compressed-file hash and retained local snapshot path. Sample dates are not a
claim of continuous or representative population coverage.

The October 13 full power archive contains 275 matches. Its gzip, original-file
and canonical hashes are checked and the full dataset is validated. However,
it retains only a global match list and minute/resource cohort counts, with no
per-cohort member hashes. Therefore exact unique champion-role counts cannot be
recovered from it. Neither summing minute counts nor choosing the maximum count
establishes that union. `position_source` explicitly records this limitation and
identifies the considered archive separately. Observed role coverage currently
uses the exact 50-match outcome source, with `count_basis` equal to
`UNIQUE_OUTCOME_MATCH_HASH_UNION`. Coverage is distinct from the authored champion
profile library and does not imply authored tactical guidance.

## Public fields and behavior

`champions[id].observed_positions` lists observed canonical roles with unique
match counts, in TOP/JUNGLE/MID/BOTTOM/SUPPORT order. Counts union member hashes
across one champion-role cohort's ending bins. Opponent cohorts never multiply
these counts. The public file contains no member-hash lists or account/player
identifiers.

`champions[id].positions[ROLE]` contains `summary`, `duration` and `opponents`.
Each exact opponent entry has its own `summary` and `duration`. Python
`summarize_outcome(dataset, champion, position, patch, tier,
opponent_champion=None)` and `duration_outcomes(...)` validate the dataset and
match the complete supplied scope. An absent opponent, role, patch or tier
returns zero trials and null rates; it never substitutes the all-opponent cohort
or minute-resource observations. Omitting `opponent_champion` deliberately selects
the exact champion-role cohort across all observed opponents.

A summary has `status`, `n`, `wins`, `win_rate_pct`, `ci_low_pct` and
`ci_high_pct`. Wins and trials sum disjoint ending bins; the rate and Wilson 95%
interval are recomputed from those totals. Per-bin rates/intervals are never
averaged. `NO_DATA` means n=0 and null rate/interval. `INSUFFICIENT_DATA` means
0<n<100; `READY` means n>=100. Descriptive values remain available below the draw
threshold, with sample size clearly available to the consumer.

Duration has thirteen bins: [0,5), [5,10), …, [55,60), [60,infinity). The upper
bound is exclusive, and the final `end_minute` is null. Every bin is present,
including empty gaps. Each has `n`, `wins`, the same percentage fields, and
`drawable` equal to n>=100. `draw_min_n` is fixed at 100. Empty bins retain null
rate/interval and are never drawn, interpolated, zero-filled or replaced with
another cohort. These bins condition on final match duration and describe match
results; they are not a time-varying strength or fight-win curve.

`pick_rate`, `ban_rate`, `runes`, `item_builds` and `skill_order` are explicitly
listed in `unsupported_metrics`. There are also no bot-duo/support-pair outcome
statistics, optimal-action estimates, causal claims or measured coaching accuracy.

## Verification

Behavioral unit tests cover weighted totals and independent Wilson expectations,
exact opponent/patch/tier absence, five-minute boundaries and 60+ tail,
n=99/n=100 drawing, empty gaps, unique-match role counts, separate source
provenance, malformed hashes/counts/rates/scopes, deterministic manifest-bound
real generation, public privacy and input preservation. Red/green logs are kept
outside the repository under `/workspace/frontend-v2-artifacts/data-*.log`.

## Separate resource growth references

The optional Python `growth_dataset=` argument and the real generator attach a
separate `growth_source` from the manifest-bound October13 full power275 archive.
It has its own 275-match denominator, sampling period, digest, source hash,
formula versions and original limitations. It does not change the outcome50
source or outcome50 observed-role counts. A power-only champion/role may appear
with no outcome trials and no observed-role count. The public JSON is minified
and deterministic; source aggregates remain unchanged.

`champions[id].positions[ROLE].growth` has `status`, `points` and `markers`.
`AVAILABLE` means at least one retained reference is present, including withheld
resource rows; `NO_DATA` has empty arrays. Only exact `ROLE_POPULATION` resource
cohorts are projected, at observed minute bins 5, 10, 15, 20, 25 and 30. Missing
minutes are absent and never interpolated or replaced with matchups.

Each resource point contains `metric`, `minute`, `unit`, `champion_mean`,
`champion_n`, `reference_mean`, `reference_n`, `n`, `mean_delta`, `delta_ci95`,
`visible` and `omission_reason`. The units are GOLD_PER_MINUTE, XP_PER_MINUTE
and CS_PER_MINUTE. These source means are cumulative resource values divided by
actual elapsed minutes, with the latest frame in each floored minute bin. They
are not per-minute gains or a measure of fighting strength.

`champion_n` is the observed champion participant count; `reference_n` is the
sampled role participant count; `n` is the role reference match count used by the
source estimator. In particular, `n` must never be labeled champion matches or
replaced with outcome50. The confidence interval is the source's Student-t95
interval for the champion-minus-pooled-role rate difference (`mean_delta`),
**not an interval for `champion_mean`**. `growth_source.uncertainty_scope` records
this distinction. The source `visible`/`omission_reason` precision decision is
preserved; clients withhold a row's values when it is not visible. The outcome
n>=100 drawing rule does not apply to these distinct resource references.

Markers contain the original `kind`, `level`, `item_id`, `item_order`, `n`,
`median_minute`, `q1_minute`, `q3_minute` and `label`, plus `observation`:

- LEVEL2/3/6/11/16 records are
  `FIRST_OBSERVED_FRAME_INTERVAL_CENSORED`. Their median and IQR describe the
  first received frame observing at least that level, not an exact level-up
  time, a skill learned, a required timing or an inferred power spike.
- ITEM records are
  `OBSERVED_NONBOOT_NONCONSUMABLE_COMPLETE_ITEM_PURCHASE_CANDIDATE`. They retain
  the source's modal purchase-candidate selection and uncertainty. They are not
  full builds or optimal-item recommendations. IDs are retained; no item names
  are added without a version/hash-matched official catalog. The current real
  archive contains no item catalog or item markers.

Each source marker repeats in three metric cohorts; projection deduplicates by
kind/level/item/order without summing its N. Conflicting repeated markers fail
closed. Marker timing and descriptive/noncausal labels are preserved. There are
no fabricated fixed level-up times, missing-level placeholders or power claims.

The current real artifact has 164 champions, 284 roles with resource/marker
references, 4,536 selected resource rows (3,222 source-visible), and 1,299 distinct
LEVEL records. Its role-count coverage still comes only from outcome50. Growth
behavior tests cover separate denominators, units, CI meaning, selected minutes,
privacy, source scope, preserved inputs, hidden rows, missing outcome coverage,
marker deduplication, first-observed timing and item-candidate IDs.

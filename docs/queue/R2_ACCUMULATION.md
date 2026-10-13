# R2 exact accumulation and confidence progress

READY implementation is complete without making a new Riot request. U3 renewed
key and U2 user's actual tier remain external inputs. HTTP401/403 alone still
means `UNAUTHORIZED_OR_EXPIRED_OR_UNSUPPORTED_PATH`; a user report of expiry is
stored separately as `user_key_expiry_attribution=USER_REPORTED_EXPIRED` in the
CLI diagnostic when `--user-reported-key-expired` is supplied. No expiry is
inferred from HTTP. First401/403 stops the collector without retry or later
requests. The old standalone paired front diagnosis is available for deliberate
diagnostics; routine scheduled acquisition does not invoke it.

`PowerAccumulator` keeps exact per-match sufficient derived records: anonymous
SHA256 match identity, patch, elapsed frame evidence, local role slots, champion,
gold/XP/CS, levels, and item purchase/undo evidence. It strips Riot/player IDs,
names, coordinates, raw provider dictionaries and unrelated events. Local slots
are mathematical role indexes, not retained provider participant identifiers.
The anonymous state is private derived material; it is never returned by UI
routes or uploaded with public aggregate artifacts. Saving is atomic with0600
file permissions; recovery fails closed on unknown fields, duplicate hashes,
invalid numbers, inconsistent patch and bounded-size violations. Current bounds
are40 patch/tier buckets,10000 sufficient records,200 frames/match,4000 item
events/match and64MiB uncompressed state; no silent eviction or approximate
merge occurs at a bound. An operator must retain/archive state before changing
these limits. A bound failure preserves the preceding saved state.

Same-patch, same-current-seed-tier runs are recomputed together through the
immutable power builder. Hash overlap is included once, with conflicting
duplicate evidence rejected. Every match keeps the original paired resources
and role contributions, so cluster variance, overlapping champion/population
covariance, CI, marker quantiles and modal ordered item pair remain exact.
Summary means alone cannot accomplish this. Patch rollover creates a separate
bucket, and tier rotation creates separate seed cohorts. A match can legitimately
belong to multiple seed cohorts; network deduplication is therefore scoped to
the selected tier and requested patch, never the global hash union. Collection
windows are unioned within a bucket, with original per-match acquisition-window
eligibility established before projection. Tier means current League seed, not
the historical rank of every participant.

The retained2026-10-11 REAL50 summary is reusable as original evidence and is
also seeded into fresh state. It cannot recover its original per-match resource
rates or clustered reference SD. It is retained separately, never added blindly
to new sufficient records. New exact batches show their own count; REAL50 is
not an invented increment of that count. The original dataset remains selectable
at `data/riot/2026-10-11/power-data.json.gz`. Movement and ending-duration
companions continue to describe each bounded acquisition run; R2 does not claim
to accumulate their strict source schemas.

Default bounded acquisition increases from50 matches/250 requests/600seconds
to300 matches/650 requests/900seconds with40 seed players. Conservative local
sliding windows enforce20 API requests/second and100/120seconds per official
host even when rate headers are absent. Server rate headers/429 may require
additional waits; all waits and transport timeouts share the same900second
deadline. These are ceilings, not promised sample yield. Existing hashes are
skipped before match/timeline requests. No scraping or price-based item guess is
introduced.

The daily trusted-main workflow restores a previous trusted main workflow's
`riot-power-accumulator` artifact before acquisition, validates it, publishes
current derived views, then refreshes the state artifact with90day retention.
Artifact provenance must match this workflow path, main branch, and schedule or
manual event; pull-request artifacts cannot seed it. Recovery API/download
errors stop the job rather than silently reset history. With no previous
unexpired artifact, the job explicitly reports a REAL50-only seed reset.
Public aggregate/progress artifacts still have7day retention. Restoring and
refreshing occurs even while acquisition is disabled; thus ordinary daily runs
renew state before expiry. GitHub scheduling must remain enabled and at least
one run must finish within90days; retain an external private copy if scheduling
is paused longer. Artifact storage is not permanent repository storage.

Actual requests require manual `key_renewed=true`, or the repository variable
`RIOT_KEY_RENEWED=true` for schedule. This gate is currently disabled until U3.
Manual tier `ROTATE` and schedules cycle CHALLENGER→GRANDMASTER→MASTER.
Once U2 supplies `RIOT_USER_TIER`, every fourth scheduled rotation uses that
explicit cohort; manual tier selection remains available. No tier is guessed
from a champion or previous match.

## Progress estimands

`progress_response(dataset)` returns five role rows. Existing champion-versus-role
curves retain their Q03 clustered influence SD/CI. For each observed point it
solves `2*t(.975,n-1)*observed_SD/sqrt(n) <= width_limit`; the default limit is
that same observed SD, giving18 matches for a nonconstant sample. Constant
samples need at least2 and retain the existing warning that zero variance does
not prove population certainty. Explicit width overrides are solved in their
recorded metric units, not replaced with arbitrary targets. Unknown SD stays
UNKNOWN, required/remaining counts null, and completion percentage is always
null. Champion-population points also project the at-least2 appearances rule
using current observed champion coverage. This is a conditional estimate,
not a promise of future coverage, a confidence percentage or gameplay sufficiency.

The compact default `champion_graphs` contains ROLE_POPULATION comparisons for
at most20 champions per role, ordered by maximum observed appearances then
canonical name. Explicit total/returned/omitted graph counts distinguish this
bounded catalog view from the complete dataset. Role summaries still use every
observed curve; omitted champions remain available in the selected power view.
matchup statistics remain available through the existing power view. Each graph
reports observed first/last minute, total/visible/unknown point counts, and the
maximum additional matches required across all its observed minute bins. One
undefined point makes that entire-graph estimate UNKNOWN. The role
`basic_curve_summary`/`champion_graph_summary` has a different explicit scope:
the minimum known additional matches until **any observed champion/minute/metric
segment** becomes eligible. A0 there means at least one existing segment is
visible; it does not mean all champions/minutes or the pooled baseline are done.

Old power aggregates do not retain pooled-role-reference SD. Their
`role_baseline` therefore remains UNKNOWN with
`POOLED_REFERENCE_SD_NOT_RETAINED_IN_AGGREGATE`. New anonymous sufficient records
enable `PowerAccumulator.progress(patch,tier)`: each match contributes the mean
of its two same-role resource rates at the selected received frame for each
minute, and Student-t uncertainty uses the SD of these independent match
contributions. This is an absolute descriptive pooled resource-rate baseline
with GOLD_PER_MINUTE/XP_PER_MINUTE/CS_PER_MINUTE units, distinct from a champion
resource-delta curve. It does not estimate absolute fighting strength.

Named public files are `power-<patch>-<tier>.json` and
`progress-<patch>-<tier>.json`. Progress is bound to the exact canonical power
SHA256. `validate_progress(progress,power)` checks strict fields, five roles,
size, exact champion summaries and the numerical baseline Student-t projection
from anonymous aggregate precision evidence. Detailed points are available only
through explicit `include_points=True`, not the default catalog response.

## Retained REAL50 demonstration and verification

`R2_REAL50_PROGRESS.json` records literal progress computed from the retained
50 REAL CHALLENGER seed matches on16.20. Visible champion-versus-role points:
TOP1503, JUNGLE1236, MID1521, BOTTOM1113, SUPPORT1278. Every pooled-role basic
baseline remains UNKNOWN because the legacy reference SD cannot be reconstructed.
The expanded exact-baseline pipeline is ready, but actual new five-role baseline
acceptance is **BLOCKED_EXTERNAL U3** until sufficient renewed-key matches arrive.
This demo makes no new provider call and creates no synthetic REAL receipt.

Meaningful tests in `tests_pregame/test_v20_stats.py` cover overlap equality
including clustered CI/markers, conflicting duplicate rejection, patch split,
private strict persistence/recovery, legacy50 separation, mathematical Q03
targets, UNKNOWN estimates, exact role baseline, receipt binding/tampering,
rate windows without headers, scoped network skipping and zero-call recovery.
Final targeted verification ran53 tests successfully:

```sh
python -m unittest tests_pregame.test_v20_stats \
  tests_pregame.test_riot_collector tests_pregame.test_riot_diagnostics \
  tests_pregame.test_power_stats -q
```

Python compilation, workflow YAML parsing and `git diff --check` also passed.

Restore/publish privately without touching Riot:

```sh
python scripts/collect_power_stats.py --publish-only \
  --accumulator private/power-accumulator.json.gz \
  --seed-data data/riot/2026-10-11/power-data.json.gz \
  --aggregate-directory private/power-views \
  --output private/power-data.json
```

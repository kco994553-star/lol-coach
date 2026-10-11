# Q15 descriptive power statistics and collection

Authority: USER_QUEUE_V1.3_2026-10-11; interface frozen in
[pregame-v2](../../contracts/pregame-v2.md), contract commit `e6e6698`.
Implementation and synthetic verification are separate from real acquisition.
No real matches have been collected in this workspace; coaching accuracy is
`null`. This module never approves knowledge or enables live coaching.

## Public interfaces

`coach_v1.power_stats.build_power_dataset(pairs, *, source,
ci_width_limits=None, complete_item_ids=())` consumes private in-memory
`{match, timeline}` Riot response pairs. Matching metadata match IDs, KR origin,
queue 420, map 11, CLASSIC mode, exact patch, collection window, unique paired
five-role assignments, and actual frames are required. Duplicate whole match
IDs count once. Invalid or missing frames supply no substitute observation.
Automatic patch selection pins the first eligible match and excludes every
other patch. It means the first encountered eligible patch, not a verified
globally latest patch. Cohort tier identifies current League seed rank; it
does not authenticate historical rank or the other nine players' rank.

`select_power_view(dataset, champion, position, patch, tier,
opponent_champion=None)` returns `{status, points, markers, reasons, source,
samples}`. Points add `metric`, `comparison`, and `opponent_champion` to the
frozen point shape. Each observed time/metric selects a visible MATCHUP point,
then ROLE_POPULATION, otherwise omits the point and records insufficiency.
No absent times are synthesized. Markers add champion and comparison lineage.
Main may call it separately for both champions and supply a dataset digest.
SYNTHETIC is retained for isolated tests; actual loaders must reject it.

`validate_power_dataset(dataset)` returns an independent validated copy or
raises `ValueError`. Unknown fields, mixed patch/tier lineage, raw-ID fields,
invalid hashes/counts, non-finite values, asymmetric intervals, unsupported
item IDs, and intervals marked visible against their precision policy fail
closed. It validates structure and mathematical consistency; an anonymous
file alone cannot independently authenticate its producer's provenance.

## Formula and operational precision

For each observed frame, subtract the enemy participant in the same canonical
role for MATCHUP: `gold_delta = own.totalGold − opponent.totalGold`,
`xp_delta = own.xp − opponent.xp`, and
`cs_delta = (own.minionsKilled + own.jungleMinionsKilled) −
(opponent.minionsKilled + opponent.jungleMinionsKilled)`. Missing numeric
fields are withheld, including possibly omitted zero-valued Riot fields.
There is no unknown-to-zero conversion. Frame time is the actual timeline
timestamp divided by 60,000; fractional observed minutes are retained.

Supplemental Main-approved correction before publication: ROLE_POPULATION
compares the champion's mean per-minute gold/XP/CS rate with the pooled mean
rate of all eligible same-position participants at that observed time. Other
champions' matches therefore affect the reference. This is the sampled
position population, not a census of all players. At `t>0`, rate is `R/t`.

To retain match-level clustering for this overlapping comparison, let M be
the number of eligible matches at that role/time/metric, k the number of
champion appearances, S_i the sum of champion rates in match i (zero only
when the champion is known absent), and P_i the mean of the two same-position
participants' rates in match i. Form `C_i = (M/k)*S_i − P_i`.
`mean(C)` equals champion pooled mean rate minus population pooled mean rate.
Compute the Student-t interval from these M cluster contributions. Mirrors
remain one match cluster; k counts both appearances. Frames with missing
resource fields are excluded from both reference and champion numerator.
This does not invent observations for a missing frame. No cohort point is
created when k=0, and k<=1 is withheld even if M is large.

This influence approximation holds empirical denominators fixed. Random
champion coverage, dependence and interval calibration remain unverified;
the interval is not an exact unconditional guarantee for randomly estimated
ratio denominators. Default precision uses contribution SD, not the
champion-only rate spread. An independent three-match example proves that
another champion changes the population reference and checks the CI against
the closed-form df=2 Student-t quantile. A mirror test verifies match counts.
Markers use the first participant record when a synthetic mirror exists.

ROLE_POPULATION formula version is `POOLED_ROLE_RATE_MATCH_INFLUENCE_T95.v1`.
Its point n=M counts match clusters, champion_n=k, reference_n=2*M,
champion_mean and reference_mean expose both sampled rates. The frozen mean
equals champion_mean−reference_mean. Global source.population_reference
identifies this estimator and eligible match/position participant counts;
actual observed time/metric counts remain on the point.
MATCHUP units are GOLD/XP/CS; ROLE_POPULATION units are
GOLD_PER_MINUTE/XP_PER_MINUTE/CS_PER_MINUTE. The metric keys stay frozen, and
the source precision-policy unit map is nested by comparison. A numeric width
override is applied in each comparison's explicitly recorded unit; callers
must not present the two comparison kinds as interchangeable cumulative units.
Minute zero has no per-minute reference and is omitted from ROLE_POPULATION.

Formula version `PAIRED_ROLE_DELTA_STUDENT_T95.v1` uses sample mean and
sample SD with denominator `n−1`; the two-sided interval is
`mean ± t(0.975,n−1) × SD / sqrt(n)`. The implementation evaluates the
regularized incomplete beta continued fraction and bisects the Student-t CDF
using Python's standard library. Independent tests compare published critical
values for degrees of freedom 1, 2, 17, 100, and 194, plus the NIST mean-CI
example (tolerance accommodates rounded published inputs).
[NIST mean confidence limits](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm)
and [critical values](https://www.itl.nist.gov/div898/handbook/eda/section3/eda3672.htm)
support the formula. They do not endorse this app's display policy.

Policy `CI_WIDTH_LE_SAMPLE_SD.v1` requires `n>=2` and full interval width
no greater than empirical sample SD. The stated operational rationale is that
estimation uncertainty should not exceed typical observed individual spread.
This is a descriptive precision heuristic, not validated tactical sufficiency
or coaching accuracy. Constant samples have SD=0 and width=0 and may display;
they do not establish population certainty. Optional positive finite
`ci_width_limits` overrides only named metric units and is recorded verbatim
in source lineage. n alone never becomes a confidence/strength score.

The t interval assumes an adequate sampling model. League seed convenience
sampling, player overlap, match dependence, small/constant samples, survival
to later frames, tier selection and coverage remain unverified. These limits
must remain visible. Signed resource deltas are not total fighting strength.

## Descriptive markers

Levels 2/3/6/11/16 use the first observed frame whose level reaches or exceeds
the target; the true transition is interval-censored by frame cadence. Median
and IQR use linearly interpolated order-statistic quantiles with index
`(n−1)p`. Counts include only observed transitions; no extrapolation.

Item classification `PINNED_COMPLETE_NONCONSUMABLE.v1` requires official
patch-matched Data Dragon metadata: map 11, purchasable, in-store, a nonempty
recipe, and no purchasable successor. Consumable, Trinket and Jungle tags are
excluded. A successor that only transforms into a non-purchasable item does
not disqualify a completed item. Classification uses recipe/shop metadata,
never a price cutoff. Non-purchasable transformations and recipe-free items
are outside this definition; boots with recipes are included. The precise
ID allowlist, source version, URL and source byte hash are persisted.

For each participant, completion purchases are ordered by actual event time,
with ITEM_UNDO reversing the latest corresponding purchase and restoring the
after-item when classified. Sales/destruction do not erase a past purchase
milestone. For order one and two, select the most common item; ties choose
the lower item ID deterministically. n and median/IQR include only matches
with that selected item at that order. Other builds are excluded, not
counterfactual comparisons. Every marker is `DESCRIPTIVE_NON_CAUSAL`.

## Official collection and failures

`RiotCollector.collect(tier='GOLD', division='I', patch=None,
start_time=None, end_time=None, collect_items=True, ci_width_limits=None)`
uses KR League-V4 entries (or elite-tier league entries), consumes provided
PUUIDs transiently, requests ASIA Match-V5 ranked/queue-420 match IDs, then
match and timeline. Missing PUUIDs block with UNSUPPORTED_LEAGUE_IDENTITY;
there is no scraping, guessed identity, or player-name lookup.

The key comes from `RIOT_API_KEY` in trusted Actions, never a command-line
argument, query parameter, file or log. This workspace has no configured
Riot secret. Key kind is UNKNOWN; 401/403 stop immediately and report
UNAUTHORIZED_OR_EXPIRED_OR_UNSUPPORTED_PATH. Riot documents that 403 also
covers unsupported paths, so these responses do not identify key lifetime.
Failure is `BLOCKED_EXTERNAL`, even if some anonymous observations were
already accumulated. A blocked view exposes no usable graph.

429 honors Retry-After seconds or HTTP dates. App limits are isolated by host
and method limits by host/endpoint. Exhausted count headers impose a
conservative full-window wait. Missing Retry-After, bounded retry exhaustion,
network/server failures, request budgets or deadlines stop with fixed enum
reasons. No unbounded retries; waits are split into at most 60-second calls.
Defaults: 250 requests, 50 match pairs, one league page, 20 seeds, two retries
per request, 600-second deadline. More matches still require the same
precision rule. These are job bounds, not claims about an API key's limits.
See [Riot portal responses and rate limits](https://developer.riotgames.com/docs/portal)
and [routing and Data Dragon](https://developer.riotgames.com/docs/lol).

Example trusted job (Main owns workflow, secret binding and public upload):

```bash
python scripts/collect_power_stats.py --output "$RUNNER_TEMP/power-data.json" \
  --tier GOLD --division I --patch 16.19 --max-matches 50
```

The script writes an atomic validated aggregate and prints only status,
anonymous sample count, fixed collection reason and null accuracy. Missing
key writes a BLOCKED_EXTERNAL receipt, allowing CI to preserve the reason;
exit 0 means the receipt was written, not collection success. Consumers must
inspect `status`. The default bounded window is the previous seven days.

## Public schema and retention

The frozen dataset fields are `schema_version`, `status`, `source`, `samples`,
`cohorts`, `coaching_accuracy`. Required source fields: provider, platform,
regional, queue_id, map_id, tier, patch, window_start, window_end, retrieved_at,
sample_kind, endpoints, formula_version, precision_policy, limitations.
Endpoints are fixed method codes, not identifier-bearing request URLs.
The precision policy has exactly version, ci_width_limits, units (nested
MATCHUP/ROLE_POPULATION metric-unit maps), rationale.

Optional `source.collection` has exactly key_kind, status_code, reason,
request_count, retry_count, limits, and optional division (I/II/III/IV, or null
for elite tiers). Limits have max_requests, max_matches,
max_pages, max_players, max_retries, deadline_seconds. Optional
`source.item_catalog` has exactly version, sha256, url, complete_item_ids,
classification. complete_item_ids are positive integers; catalog URL/version
are official pinned Data Dragon metadata for REAL sources.
Optional source.population_reference has exactly kind
POOLED_SAME_POSITION_RATE_MEAN_CLUSTERED, formula_version
POOLED_ROLE_RATE_MATCH_INFLUENCE_T95.v1, position_participants_per_match=2,
match_count and position_participant_count=2*match_count. Every
ROLE_POPULATION point requires this source plus reference_n=2*n,
champion_n, champion_mean and reference_mean. k<=1 is withheld with
CHAMPION_N_LT_2 when an interval is otherwise estimable; n<2 remains N_LT_2.

Raw response pairs, PUUIDs, names, Riot IDs, participant IDs and match IDs are
private ephemeral memory only. They are never written by this implementation.
Only deduplication SHA256 match IDs survive with anonymous aggregates and
fixed metadata. Job termination discards raw memory. Public GitHub artifacts
are public; they must never retain raw data even with an expiry policy.
Hashing a match ID is a deduplication mechanism, not an anonymity guarantee
against an attacker with a candidate ID set. No per-player records survive.
Only the synthetic red/green receipts and public source metadata are committed
under `evidence/queue/q15`; they are not real Riot acquisition receipts.

Q18 movement/stage statistics use a separate future contract. This module
does not infer stages from minutes, respawn risk, formation, vision, causal
strength windows or tactical recommendations.

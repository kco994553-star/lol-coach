# Champion tier and opponent insights v1

This additive contract implements the user's 2026-10-25 direction: collect all
ten authorized leaf tiers within existing budgets, expose leaf filters plus
`ALL`, and default the champion browser to `MASTER_PLUS`. It preserves the
existing outcome/power v1 schemas, validators, historical snapshots, and the
independent Challenger-reference product. No provider calls occur in the
builder. The historical Master+ intake contract is amended separately; this
contract does not weaken credentials, request ceilings, privacy, free-only
rules, or protected user decision records.

## Meaning and source boundaries

Leaf tiers, in order, are IRON, BRONZE, SILVER, GOLD, PLATINUM, EMERALD,
DIAMOND, MASTER, GRANDMASTER, CHALLENGER. `MASTER_PLUS` selects the unique
match union of the final three; `ALL` selects the ten leaf cohorts. Aggregates
are filters and cannot be supplied as Riot source tiers. They are never added
to one another to form another aggregate.

Tier means `CURRENT_LEAGUE_SEED_COHORT_NOT_ALL_PARTICIPANT_RANKS`. It identifies
the seed account's current League-V4 discovery cohort. The selected champion
participant's rank at match time is `UNKNOWN`; no participant rank, match MMR,
representative tier population, or random sample is established. Partial
division/page selection remains a convenience sample. Observed roles come
from official `teamPosition`; unknown roles are excluded rather than inferred.

Patch/platform/queue/map/sample kind are exact. Default patch is the latest
retained patch, not a claim about the current official patch. Selecting an
unavailable patch, tier, champion, or own role returns `NO_DATA`; there is no
fallback to another tier, patch, position, power archive, or resources. Real
public builds reject synthetic evidence and mixed real/synthetic inputs.

## Private anonymous result companion

`coach_v1.matchup_results` provides:

```python
normalize_match(raw_match, seed_tier, *, patch=None, sample_kind='REAL', provenance=None)
build_matchup_results(pairs, *, source)
empty_matchup_results()
validate_matchup_results(dataset)
merge_matchup_results(*datasets)
```

`normalize_match` returns a validated record or `None` for ineligible provider
evidence. Invalid caller scope/provenance raises. The batch builder reads
already-fetched match/timeline pairs and requires matching metadata IDs. It
does not fetch, persist, log, or return raw responses. Its source argument
accepts the existing base outcome source mapping, plus optional division and
digest provenance. Inputs remain unmodified.

The private envelope is exactly:

```json
{
  "schema_version": "champion.opponent-results.v1",
  "source": {"platform":"KR","regional":"ASIA","queue_id":420,"map_id":11},
  "records": [],
  "omissions": {}
}
```

Each private record has exactly `hash`, `patch`, `queue_id`, `map_id`,
`sample_kind`, `winner`, `teams`, `seed_tiers`, `provenance`. Hash is SHA256 of
the transient provider match ID, compatible with existing anonymous hashes.
Winner is integer 0 for the first canonical team (provider team100), or 1 for
the second (team200). `teams` has two arrays, each with five anonymous slots
`{champion,position}`. Positions are TOP/JUNGLE/MID/BOTTOM/SUPPORT or null.
Slots are canonically sorted by observed role then champion; provider array
order and participant IDs are not retained. Duplicate observed roles on a
team are ineligible. Canonical champion spellings follow the existing
ASCII champion-key format.

`seed_tiers` is a sorted unique nonempty leaf-tier membership set.
`provenance` is a deduplicated list whose exact optional allowlist is `tier`,
`division`, `window_start`, `window_end`, `retrieved_at`, `source_digest`,
`run_digest`. Tier is mandatory, and its union equals seed membership.
Division is null or I/II/III/IV; windows are integer seconds or null;
retrieval is an offset-aware ISO timestamp; digests are SHA256. Unknown
provenance fields are rejected. PUUID, player/summoner/Riot IDs, raw responses,
keys, provider participant IDs, and unhashed match IDs are never persisted.

Eligibility requires KR ranked solo 420, map11 CLASSIC, exact numeric patch
at least 11.20, reported positive integer seconds duration, integer start/end
with end >= start, source window agreement, exactly two opposite boolean
team results and ten participants whose boolean results agree with their
teams. Missing or contradictory wins never become losses. Remake/early-end
classification remains unverified. Unknown roles may be retained as null so
the unaffected observed slots remain usable; no statistical trial uses an
unknown own/enemy role.

Merge deduplicates by hash and unions memberships/provenance. Same hash with
different roster, winner, patch, queue/map or sample kind raises before
producing output. Repeat identical snapshots do not multiply trials. The
private validator bounds each retained companion to 100,000 records; normal
acquisition retains its much smaller existing per-run ceiling. Companion
records and member hashes must stay in private storage/artifacts. Public
publication is exclusively the aggregate projection below. The collector
maintains result completeness separately from power-history hashes; a power
record does not establish retained final results.

## Public aggregate projection

`coach_v1.champion_insights.build_champion_insights(outcome_datasets=(), *,
result_datasets=(), ranking_min_n=20, allow_synthetic=False)` is pure and emits
`lol-coach-champion-insights-v1`. `validate_champion_insights` enforces an
exact public allowlist and recomputes row rates and Wilson 95% intervals.

Top-level fields are `format`, `default_tier`, `default_patch`, `patches`,
`tiers`, `sample_kind`, `ranking_min_n`, `ranking_policy`, `ranking_ties`,
`ranking_overlap`, `denominator_basis`, `limitations`, `sources`, `scopes`,
`summaries`, `matchups`, `omissions`. Normalized shared tables avoid a complete
duplicated champion tree for every scope. No raw companion, roster, private
record, or member hash appears in these tables.

`sources` carries aggregate kind, dataset digest, patch, tier, sample kind,
source match count, window start/end, retrieval timestamp and sampled division.
Each patch/tier scope carries requested/available/missing leaf tiers,
`coverage` COMPLETE/PARTIAL/EMPTY, unique `matches`, `cross_role_matches`,
cross-role available/missing tiers, `cross_role_status`, source digests,
tier meaning and `a_rank_at_match: UNKNOWN`. COMPLETE means requested seed
cohorts are present; it does not prove population/division/page completeness.
Cross-role status `NO_RETAINED_ROSTER_RESULTS` does not erase valid legacy
same-role observations.

Summary rows have `patch`, `tier`, `champion`, `position`, `n`, `wins`,
`win_rate`, `ci95`, `status`. Matchup rows add `enemy_position`,
`enemy_champion`, `basis`. Rates are fractions in [0,1]; Wilson intervals use
`{low,high}`. Status is READY at the publication minimum, otherwise
INSUFFICIENT_DATA. Zero-denominator selector summaries use null rate/CI and
NO_DATA. The publication minimum is a presentation policy, not validated
tactical certainty.

`basis: SAME_ROLE_ENCOUNTERS` can use old exact outcome cohorts.
`basis: ENEMY_TEAM_ROSTER` requires the new anonymous result evidence. A
trial finds A in its exact own champion/position slot, uses the opposite
team's observed enemy position/champion, and counts A team's final game win.
Allies never contribute enemy observations. Reverse A-own/B-enemy pairs
have complementary wins with their exact reversed roles. Mirrored
champion/same-role endpoints are excluded as both own and enemy endpoints
to preserve one result per match/key and symmetric reverse-role comparisons;
unaffected roles remain usable.
Different enemy-position tables intentionally reuse matches; never sum their
denominators into an overall match count. This describes sampled team-result
associations, not lane strength, combat success, causal counters, or personal
win probability.

Result unions count each hash once and recompute integer wins/N and Wilson
intervals. They never average source win rates. A legacy snapshot may be
used alone or with provably disjoint legacy member sets. Partial legacy
overlap raises because point-level aggregate wins cannot recover overlap
outcomes. A legacy snapshot wholly covered by private results is redundant
only after every cohort's members, opponents and aggregate wins agree with
the private evidence; any disagreement fails closed. Result sources cannot
be fabricated from power resources or intersected outcome membership alone.

## Selection and display policy

```python
select_insights(index, champion, position, tier='MASTER_PLUS', patch=None)
```

Returns `status`, `scope`, `summary`, `frequent_opponents`,
`by_enemy_position`, `ranking_min_n`, `limitations`. Every enemy role returns
`best`, `worst`, `eligible_count`, `status`, `overlap_policy`, `overlap_count`,
`all_tied`, `rate_ties`. Frequent opponents use same-role encounter rows,
ordered N descending then canonical enemy champion ascending; N>=1 is
visible with CI and an insufficient-sample warning. No manual enemy choice
is needed to show these actual frequent opponents.

Statistical tables require N>=20 by default, returning up to five highest
and five lowest final A-team rates independently. Sort ties use N descending
then canonical champion ascending solely for deterministic display. Best and
worst lists may overlap when few entries qualify; `overlap_count` discloses
this and the UI must warn that a small candidate set overlaps and does not
establish superiority. `all_tied` means no observed rate difference; neither
N nor alphabetical order creates a strength distinction. CI overlap and
multiple comparisons remain visible limitations. Fewer than five entries
and empty tables are valid results. Empty knowledge coverage is not filled
from these statistical sorts.

For the enemy position matching A's own position, ranking uses the exact
`SAME_ROLE_ENCOUNTERS` union, including legitimate legacy final-result
evidence. The other four positions require `ENEMY_TEAM_ROSTER`. The two
bases are never added for the same own-role pair; source basis remains on
each row for display and review.

Knowledge-based hardest/easiest matchups are a separate sourced, conditional
artifact and review state. Statistical wins never order that artifact or
create USER approval, tactical verification, or engine activation.

## Reproducible offline build and present coverage

`python scripts/build_champion_insights.py` reads the checked-in manifest-bound
50-match CHALLENGER outcome snapshot on patch16.20 and writes
`web_r4/champion-insights.json`. `--check` compares deterministic bytes without
writing. `--outcome path` and `--results path` can repeat for explicitly
provided validated local snapshots; gzip/JSON inputs are bounded to 32MiB
encoded / 128MiB decoded. No network or credentials are used.

At initial publication MASTER_PLUS is PARTIAL with only CHALLENGER available
and MASTER/GRANDMASTER missing. ALL is PARTIAL with nine missing leaf tiers.
Other leaf scopes are EMPTY. All 50 retained matches provide legacy same-role
results; no local anonymous final-result roster companion exists. Cross-role
result coverage is therefore zero, and no cross-role statistical ranking is
invented. The largest current same-role sample is N=6, below N20. These are
retained historical samples, not an all-tier acquisition claim.

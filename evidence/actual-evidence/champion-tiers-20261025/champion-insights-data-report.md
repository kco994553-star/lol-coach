# Champion insights data implementation report

Date: 2026-10-25 UTC. Workspace: `/workspace/lol-coach-champion-tiers`.
Assigned data-contract owner only; no commits, amends, network/provider calls,
external application writes, or subagents. Existing outcome/power v1 code,
validators, persisted source bytes and legacy builder remain unchanged by this
worker. Collector/policy/publication/server/frontend owners work separately.

## Owned deliverables

- `coach_v1/matchup_results.py`: anonymous private final-result normalization,
  canonical 2×5 rosters, observed nullable roles, team-result agreement,
  strict allowlist validators, deterministic membership/provenance union,
  same-hash conflict rejection and omission counts.
- `coach_v1/champion_insights.py`: public aggregate-only shared tables,
  all ten leaf scopes plus MASTER_PLUS/ALL, global hash/patch binding, exact
  unique union, integer win/N and Wilson recomputation, strict serialization
  validation and pure `select_insights`.
- `scripts/build_champion_insights.py`: offline manifest-bound default build,
  optional explicit local outcome/result inputs, gzip/JSON size bounds,
  deterministic output and `--check` without writes.
- `web_r4/champion-insights.json`: checked-in actual historical aggregate
  projection, 429,817 bytes; one patch16.20, 12 scopes, 483 summary rows,
  1266 same-role encounter rows, one validated source. No roster-result rows.
- `contracts/champion-insights-v1.md`: complete private/public APIs, scope
  meanings, proof limits, publication/ranking policy and current coverage.
- `tests_pregame/test_champion_insights.py`: 15 isolated adversarial tests.

## Frozen public contract

Private APIs are `normalize_match(raw_match,seed_tier,*,patch=None,
sample_kind='REAL',provenance=None)`, `build_matchup_results(pairs,*,source)`,
`empty_matchup_results()`, `validate_matchup_results(dataset)` and
`merge_matchup_results(*datasets)` in `coach_v1.matchup_results`.

The private companion is `champion.opponent-results.v1` with exact top-level
schema_version/source/records/omissions. Winner is 0 for canonical team100,
1 for canonical team200. Teams have five `{champion,position}` slots each;
unknown roles stay null. Record hashes are SHA256 of transient IDs, seed
memberships are leaf sets, source provenance is allowlisted and ID-free.
Repeated record/source discovery unions memberships without multiplying
trials. Any patch/roster/winner conflict rejects the union. Private result
completeness is independent of power-history completeness; collector owner
was informed and uses these APIs.

Public format is `lol-coach-champion-insights-v1`. Shared `scopes`, `summaries`,
`matchups` tables plus aggregate `sources` retain exact patch/tier boundaries.
Rows have champion/position and enemy_position/enemy_champion where applicable;
N/wins, fractional win_rate, Wilson `{low,high}` and publication status. Basis
distinguishes SAME_ROLE_ENCOUNTERS from ENEMY_TEAM_ROSTER.

`select_insights(index,champion,position,tier='MASTER_PLUS',patch=None)` returns
status/scope/summary/frequent_opponents/by_enemy_position/ranking_min_n/
limitations. Missing scope has no fallback. Default patch is latest retained,
not claimed current. Same-role frequent rows are ordered N desc/name asc at
N>=1. Statistical own-position ranking uses exact SAME_ROLE_ENCOUNTERS
(legitimate legacy evidence); the other four roles require ENEMY_TEAM_ROSTER.
This choice was explicitly approved by root and forwarded to frontend owner.

N>=20 is the explicit publication minimum, not tactical certainty. Best and
worst lists independently return up to five eligible rows, rate descending/
ascending then N desc/name asc only for deterministic ties. Root corrected
the initial disjoint-list approach; final selector reports overlap_count,
all_tied and rate_ties. Small candidate sets may appear in both lists with a
warning. Many-comparison/overlapping-CI limitations remain explicit. Knowledge
hardest/easiest is separately sourced, and statistical rows never order it.

## Exactness and privacy decisions

Unique unions recompute wins/N and Wilson; they never average rates. Legacy
partial overlap fails because point-level aggregate wins cannot identify
overlap outcomes. A completely covered legacy source can be dropped only
after each legacy cohort's members/opponents/wins agrees with private trials.
Same match hash across different source patches fails globally before scopes
are built, including legacy-vs-private contradictions.

Cross-role association finds A's exact observed own slot and the actual
opposite team's enemy slot. Allies do not count as enemies. Unknown roles are
excluded only at affected endpoints; they are never inferred. Mirrored
champion/role endpoints are symmetrically excluded to retain reverse-pair
complementarity while preserving unaffected roles. Five role tables overlap
by design and their N must not be summed as overall matches.

Public rows contain no private member hashes, rosters, raw match payloads,
PUUIDs, Riot/player IDs or unhashed match IDs. Unknown identity fields in
private/projection/provenance inputs fail allowlists. Real UI builds reject
synthetic evidence and mixed real/synthetic sources. The tier meaning is
CURRENT_LEAGUE_SEED_COHORT_NOT_ALL_PARTICIPANT_RANKS and A rank at match is
UNKNOWN. Coverage means seed-cohort presence, not exhaustive division/page
or population coverage.

## Current actual coverage

Default MASTER_PLUS is PARTIAL: only CHALLENGER exists; MASTER and GRANDMASTER
are missing. ALL is PARTIAL with nine missing leaf tiers. Unrelated tiers
are EMPTY. The actual snapshot is 50 historical CHALLENGER matches on16.20,
and its maximum same-role matchup is Qiyana JUNGLE vs LeeSin N6, A wins4.
No retained final-result roster companion exists, so cross-role coverage is0.
Every current statistical ranking is empty at minN20. Power275 is not
relabeled as outcome data. No all-tier or fresh acquisition claim is made.

## Verification and review history

The focused regression command is:

```sh
python -m unittest tests_pregame.test_champion_insights tests_pregame.test_outcome_stats tests_pregame.test_champion_statistics
python scripts/build_champion_insights.py --check
```

The first 10 new checks passed; expanded checks cover fifteen cases including
unique Master/GM/CH/GOLD unions, rate10% vs average50%, exact reverse-role
perspective, ally exclusion, two indistinguishable legacy worlds with
different correct enemy junglers, unknown roles, mirrored endpoints,
privacy sentinels, conflicts, real/synthetic isolation, exact patch/role/tier
queries, partial legacy overlap, own-role legacy ranking, minN exclusion,
independent top/bottom overlap, and equal-rate tie disclosure.

Independent reviewer `/root/tier_data_review` identified the cross-source
hash/patch edge. Its dedicated new test was run RED (ValueError not raised),
then GREEN after the global binding fix; deterministic default bytes remain
unchanged. A prior focused44-test run passed, and the final focused45-test
run passed: `Ran 45 tests in 8.826s — OK`; deterministic `--check` also passed.
No full concurrent repository suite
was run by this worker.

## Existing legacy numerical issue for root-owned follow-up

While adding a legitimate N20 legacy ranking fixture, an untouched legacy
Wilson numerical edge surfaced: `build_outcome_dataset([pair(i) for i in
range(20)],source=source())` rejects its own extreme20/20 interval because
floating rounding makes ci.high slightly smaller than the exact rate1.
The reverse0/20 cohort has the corresponding low-end issue. This is a real
future-data case, not merely a synthetic fixture concern. This worker did
not modify outcome_stats.py because root owns compatibility-sensitive fixes;
root explicitly accepted ownership of a bounded calculation correction
without relaxing validators/schema/records. Full traceback, exact interval
values and minimal reproduction are preserved at
`/workspace/gp23-artifacts/champion-insights-wilson20-repro.txt`. The new legacy
ranking fixture uses10/20 so it can verify the independent source-selection
behavior while that fix is handled separately.

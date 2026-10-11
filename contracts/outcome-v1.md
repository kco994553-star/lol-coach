# Q03 additive outcome contract v1 — 2026-10-11

Authority USER_QUEUE_V1.4_2026-10-11. Main owns this additive contract. Existing
pregame contracts and power-data.v1 remain unchanged. This is Q15's auxiliary
ending-game result statistic, never strength at a point in a still-running game.

## Source and calculation

Source: official Riot Match-V5 match info from already fetched private pairs.
https://developer.riotgames.com/api-details/match-v5 (2026-10-11 schema SHA256
fb40838f6160a3ede81ce59b844e295328fda4c7ecb5f0d18f4f2f6869f2d64d).
Only matched KR metadata IDs, queue420/map11/CLASSIC, exactly paired canonical
five roles, exact patch/current League seed tier/window are eligible. Inputs
are deduplicated by whole match ID. Timeline metadata must match; timeline
frames are not a result-quality gate. Raw IDs/identities/responses stay in memory.

Reported gameDuration must be a positive integer, patch >=11.20 and a known
numeric gameEndTimestamp must exist: the official schema distinguishes older
millisecond durations from current seconds. Never infer duration from timestamps
or missing fields. Both teams have known opposite boolean win fields, all ten
participant win booleans agree with their team, and champions/roles are valid.
Missing or conflicting result/duration inputs contribute no substitute trial.
Mirrored same-champion/same-role opponents are excluded from that champion's
cohorts to preserve binary trials with at most one trial per match/cohort.
Early termination/remake classification is unverified; do not guess it.

Bin minute=floor(reported duration_seconds/60); interval [minute,minute+1).
This is display resolution, not a gameplay stage or strength threshold. For n
distinct eligible matches and w wins, p=w/n. Wilson 95% CI with
z=NormalDist().inv_cdf(0.975): denominator=1+z²/n,
center=(p+z²/(2n))/denominator,
half=z*sqrt(p(1-p)/n+z²/(4n²))/denominator, [center-half,center+half].
Source: https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm.
One trial makes the interval calculable, not sufficient evidence. Display a
separate auxiliary table with n, w, p and CI; draw no trend line and attach no
strength/phase/tactical claim or arbitrary sufficient-sample cutoff.

## Immutable public shape

Module coach_v1/outcome_stats.py owns build_outcome_dataset(pairs, *, source),
validate_outcome_dataset(dataset), select_outcome_view(dataset, champion,
position, patch, tier, opponent_champion=None). Validator returns a copied
validated object or ValueError, rejects unknown/raw/nonfinite/mixed-lineage
fields, and recomputes ratios and Wilson intervals.

Dataset exact fields: schema_version=pregame.outcome-data.v1;
status=READY|INSUFFICIENT_DATA|BLOCKED_EXTERNAL; source; samples;
cohorts; coaching_accuracy=null. samples={real_matches,synthetic_matches,
hashed_match_ids}; hashes unique SHA256; sample kind determines which count is0.
READY requires points; INSUFFICIENT_DATA/BLOCKED_EXTERNAL have no points.

Source exact fields: provider=RIOT_API|SYNTHETIC, platform=KR, regional=ASIA,
queue_id=420, map_id=11, tier (existing bounded enum), patch (exact numeric patch
or null only if no eligible samples), window_start/window_end (integer or null),
retrieved_at (bounded timestamp or null), sample_kind=REAL|SYNTHETIC,
endpoints (existing official endpoint enums), formula_version=WILSON_SCORE_95.v1,
duration_bin_policy={kind:ENDING_GAME_DURATION_FLOOR_MINUTE,width_seconds:60,
unit:SECONDS}, mirror_policy=EXCLUDE_SAME_CHAMPION_SAME_ROLE_BOTH_TEAMS.v1,
result_policy=PARTICIPANT_TEAM_WIN_BOOLEAN_AGREEMENT.v1, limitations (fixed codes).
Provider/sample-kind parity required. No credentials, player identities or raw
match ID field is permitted.

Cohort={champion,position,patch,tier,comparison:MATCHUP|CHAMPION_ROLE,
opponent_champion:null|string,points}. CHAMPION_ROLE means all sampled opponents,
not population-centered subtraction. Cohort patch/tier match source. Unique
cohort identities. Point={minute:integer>=0,n:integer>=1,wins:integer0..n,
win_rate:wins/n,ci95:{low,high},input_match_hashes}. Hashes unique and n equals
their count, subset of sample hashes; a hash occurs only once in each cohort's
duration bins. All numeric values finite; interval recomputed within1e-12.

select_outcome_view returns {status:KNOWN|UNKNOWN,points,reasons,source,samples}.
Selected points add comparison/opponent_champion. For each observed ending
minute choose the exact MATCHUP if present, else CHAMPION_ROLE. No absent bins
or zero-sample values are synthesized. A blocked dataset yields UNKNOWN.

## Integration and privacy

Optional RiotCollector.collect(...,collect_outcome=False) produces validated
collector.outcome_data without extra API calls. Failure sets outcome_status=
BLOCKED_EXTERNAL and no usable companion/file. CLI --outcome-output writes
only validated anonymous companion atomically; removes a stale output on failure.
Trusted main workflow requests it and retains only anonymous aggregate files.

Server internal outcome_data defaultsNone; CLI --outcome-data validates and
rejects SYNTHETIC outside isolated tests. New authenticated, bounded POST
/dev/v1/pregame/outcome-view accepts exactly {champion,position,patch,tier,
opponent_champion}; patch/tier/opponent may be null. Reuse existing power_request
bounds; response {view,test_mode}. View adds dataset_digest/schema_version.
No source or no matching patch/champion/role/tier yields UNKNOWN; null tier may
resolve the one dataset tier. Existing power API/status/plan fingerprints are
unchanged. Actual UI never renders synthetic results; tests require both
internal server test_mode and UI fixture flag, and show TEST visibly. Auxiliary
table on lane detail uses the current saved plan and existing navigation/auth/
dirty/expiry guards; never attach a late result to a changed plan.

Fixed limitations include ENDING_DURATION_CONDITIONAL_OUTCOME_NOT_STRENGTH,
CURRENT_LEAGUE_SEED_NOT_HISTORICAL_PARTICIPANT_TIER,
CONVENIENCE_SAMPLE_INDEPENDENCE_AND_COVERAGE_UNVERIFIED,
N_ONE_COMPUTABLE_NOT_SAMPLE_SUFFICIENCY,
PAIRED_TIMELINE_METADATA_ONLY_NO_FRAME_GATE,
REPORTED_DURATION_SECONDS_POST_11_20_ONLY,
EARLY_TERMINATION_OR_REMAKE_CLASSIFICATION_UNVERIFIED,
MIRRORED_CHAMPION_ROLE_TRIALS_EXCLUDED. User approval of tactical knowledge is
separate; this computed descriptive statistic never changes knowledge reviews.

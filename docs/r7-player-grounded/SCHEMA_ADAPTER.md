# D1/D2 post-game source schema adapter

The preserved `EUW1_7095952008` Match/Timeline pair is now supported by a separate archive diagnostic in `coach_audit/postgame.py`. The old LiveClient extractor still reads its original paths and still reports 0/17 PRESENT for each file. Source support closes this narrow schema coverage gap; it establishes no PLAYER state variables and enables no coaching.

## Binding and supported input

`diagnose_postgame(match_bytes, timeline_bytes, expected_match_id=..., participant_id=..., archive_cutoff_ms=...)` accepts bytes only. Its public entry requires the exact preserved R7 byte lengths and SHA256 values. The revision, exact ranges, response status and receipt path accompany the result. It does not fetch data and does not accept caller-supplied replacement source hashes.

| Source | Preserved bytes | SHA256 |
|---|---:|---|
| Match | 113459 | `767330c58d9f9168c5ea4a6f0827bde7b0890eeae2317ea19ae52812a3792b14` |
| Timeline | 1199490 | `9fb74d4ce6cd16f3e04aa0953638e0e18cd80c5cce652eac83126ed55050d51a` |

Revision: `477404f532b1014b7fc61c3b1c024e988f883a26`. Preserved provenance: `evidence/r7-continuation/source-range-receipts.json`. Restoring these same bytes for execution is not a second source pair, a new source reference or independent authentication. The source remains a publisher-attested Riot collection exported as BSON-JSON; no first-party response authenticity is asserted.

Strict JSON rejects duplicate keys and nonfinite values. Joins validate Match/Timeline matchId and gameId, ordered metadata identities, participant IDs and identity relations across both rosters, the requested participant, and selected participant-frame key/ID relations. Raw identities are used internally for the join and omitted from the output.

BSON `$numberLong` decoding is allowed only at each `/info/gameId`. It requires exactly one wrapper key, a decimal string with no float or exponent notation, and the signed int64 range. Conversion uses Python integers, retaining exact values above the floating-point safe integer limit. The output records the original literal, source pointer and `SIGNED_INT64_EXACT` semantics. Other selected scalar or ancestor BSON wrappers raise `UNSUPPORTED_SOURCE_SCHEMA`; they are never recursively unwrapped or coerced. Start/end timestamp wrappers and all other final-match fields are ignored.

## Archive time and information boundary

The cutoff is strictly an integer of elapsed game milliseconds, with `ELAPSED_GAME_MS` as its clock basis. Noninteger, negative, different-clock, out-of-source-end cutoffs and nonincreasing frame timestamps are rejected. The latest frame with timestamp less than or equal to the cutoff is selected. No interpolation or freshness assumption is made. A cutoff before the first frame keeps `SUPPORTED_SOURCE_SCHEMA` and reports `MISSING_AT_ARCHIVE_CUTOFF`; selected values are UNKNOWN.

Timeline facts include selected health/max health, resource/max resource, current gold, level, lane/jungle CS and own archive coordinates. Static champion, team and role labels are copied only from the joined Match participant. Missing, null, invalid scalar and absent participant-frame values remain UNKNOWN with explicit reasons; no missing field becomes zero. A real zero remains zero.

`health_fraction = health / health_max` requires both valid integer parents, positive capacity and `0 <= health <= health_max`. `cs = lane_cs + jungle_cs` requires both valid nonnegative integer parents and a signed int64 sum. Each derived diagnostic retains its formula version, both parent source pointers/hashes and the selected frame timestamp. Invalid health invariants produce UNKNOWN, not a ratio.

All facts and derivations carry `POST_GAME_DATASET`, `POST_GAME_ONLY`, `player_known=false`, `decision_eligible=false` and `coaching_eligible=false`. Opponent coordinates remain explicitly POST_GAME_ONLY with player visibility UNKNOWN. This archive output has no `Observation`, `Snapshot`, `ReviewInput` or engine conversion. It leaves `player_information_state` and `ground_truth_state` null, emits an empty blocked `decision_candidate`, executes no engine, and keeps coaching N=0 and accuracy=null.

The adapter never reads Timeline events into its result, including events that precede the cutoff. Future participant values, final Match statistics, outcome, winner and final-match time fields are excluded. Tests change these categories and confirm that the archive candidate and empty decision candidate do not change. Post-game coordinates cannot substitute for a player reference or decision-time visibility.

## Impact and validation

This is an additive D1/D2 source diagnostic. No changes are required to Frozen27, the protected CoreGuard, models, state reduction, the synthetic-only engine, old111 expected values or old evidence. Existing schema-coverage and failure history are preserved. There is no REAL engine mode, evaluator, synthetic relabeling or PLAYER verification claim. Connecting real inputs to an evaluator would be a separate contract impact decision.

The targeted tests use small, explicitly synthetic schema-mechanics fixtures only through a private schema helper. The public byte-bound entry is exercised separately against the exact actual pair, including a byte-mutation rejection. Test records retain `SYNTHETIC_SCHEMA_TEST_ONLY` origin and `pinned_bytes_verified=false`, and the helper always labels its output `UNPINNED_SCHEMA_DIAGNOSTIC`. Only the byte-verified public entry can set `PINNED_SOURCE_BYTES_VERIFIED`; test records are not new source references.

```sh
R7_POSTGAME_RAW_DIR=/workspace/scratch/7240cfa27170/private-r7-player-grounded python3 -m unittest tests_r7_player_grounded.test_postgame -v
python3 -m unittest tests_r7.test_audit -q
```

Result: targeted tests 17/17 PASS, skipped0; preserved audit tests 15/15 PASS. Existing `scripts/verify_r7_source_reference.py` was called offline on the same restored byte pair: 26/26 preserved reference checks matched, with PLAYER verified variables0. These are source transcription and archive-boundary checks, not State/Decision acceptance or coaching accuracy. The root continuation verification records the complete baseline gates separately.

Private raw locations used for execution: `/workspace/scratch/7240cfa27170/private-r7-player-grounded/match.json` and `/workspace/scratch/7240cfa27170/private-r7-player-grounded/timeline.json`. Full raw participant records remain outside the repository.

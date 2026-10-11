# Additive PRE_GAME API v3

The queue v1.4 supplement preserves legacy route authorization, strict body and origin checks, manual-only input admission, proposal approval boundaries, and immutable saved history.

New plans use `pregame.plan.v3`. Saved plans replay using their original v1, v2, or v3 evaluator. A restored payload becomes CURRENT only when its complete version-specific generated fields equal the source-bound deterministic evaluator result. A different movement dataset digest expires a v3 plan with `MOVEMENT_STATISTICS_CHANGED`; historical input, output, and original digest remain unchanged.

Candidate resources use `pregame.rule-source.v1`, `.v2`, or `.v3` matching the enclosed executable rule version. Mismatched resource/spec versions remain unbound. Candidate import creates EXPLORATORY proposals only. The additive initiative catalog expands the list from 177 to 190 without approving any entry.

`POST /dev/v1/pregame/power-view` requires exactly `champion`, `position`, `patch`, `tier`, and `opponent_champion`. The final three fields accept null. Position and tier use bounded enumerations; champion IDs and patch strings are bounded identifiers. The response contains `view`, optional `opponent_view`, and `test_mode`; each view carries a validated aggregate dataset digest and schema version. Missing data, unknown patch, or ambiguous tier yields UNKNOWN with empty points and a reason, never fabricated zeros. There is no raw-match or full-dataset endpoint.

`GET /dev/v1/pregame/status` adds `test_mode` and available `power_tiers`; `current_patch` remains null because no authoritative patch adapter is available. `/pregame_power.js` is served as a local static asset. Normal servers initialize `test_mode=False`; no HTTP operation changes the mode or datasets. Synthetic datasets are withheld outside isolated internal fixture mode.

CLI flags `--power-data` and `--movement-data` accept aggregate-only JSON files validated by their corresponding modules. CLI startup rejects synthetic data and closes the server on validation failure. No key, identity, raw match, live location, stage observation, or cooldown timer is introduced.

Verification history: six new HTTP tests failed before implementation (five failures, one error). With the shared v3 model/storage contract present, all six passed. One intermediate fixture attempted restore into a nonempty store and correctly received `RESTORE_REQUIRES_EMPTY_PREGAME`; the fixture was corrected to exercise HTTP restore into a fresh store. Tests cover all three source wrapper versions, mismatched wrapper rejection, three historical evaluator versions, genuine archive restoration, forged generated-result expiry, graph authorization and malformed bodies, inaccessible HTTP test-mode mutation, and unchanged approval state. These are synthetic software checks, not coaching accuracy measurements.

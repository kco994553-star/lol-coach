# Actual-data projection delta review

Reviewer: `/root/v23_code_review`. Scope: working projection changes against local HEAD `f4fa37a501fe78679d3a11e39162437c89f58cab`: `RecallDataset`, PC archive bounds/cache/labels, unsupported draft patches, affected new tests, and the corrected report consumer. No provider requests, private input access, completed-check reruns, or tests were performed by this reviewer. Existing new RED/GREEN logs and actual-data Chromium receipts were read.

## Findings and disposition

1. **P2, corrected during review — report consumer still assumed dictionaries.** `load_datasets` now stores `RecallDataset` objects, while `scripts/report_queue_v23.py` initially indexed `d['samples']`/`d['cohorts']`. That would raise TypeError with loaded actual data. Main added a copied `summary()` accessor and switched the report consumer to it. Reviewed the correction; `report.json` was subsequently generated at 12:00:17 UTC and includes the loaded populations.
2. **Performance acceptance remains unmet in available evidence.** The actual-data browser receipt at `actual-browser-20261015T115919460605Z/runner.json` reports 5396.4ms own-pick and 7269.3ms opponent-pick input-to-card latency, with `goal_under_1000ms:false`. Both populations now load, no browser errors or unexpected writes occur, and zero USER decisions are created. This establishes functional projection, not the one-second goal. Four populated recall cards invoke `_resource_graph`, which calls the existing `power_response` separately for each card; own/opponent Q15 datasets are therefore repeatedly processed across the two populations in addition to the existing statistics card. This is a concrete remaining optimization target. No timing probe was rerun.

## Correctness and safety

- `RecallDataset` strictly validates and privately deep-copies the anonymous dataset once. Its tuple index preserves exact-champion/role/patch lookup semantics, and each returned view deep-copies only selected output/cohort data. Mutating the input dictionary or a returned view cannot mutate the stored snapshot. The digest uses the same sorted compact UTF-8 JSON/SHA256 algorithm as the earlier per-request projection.
- The PC loader's 32000000-byte limit admits the actual 12366272-byte Challenger archive while retaining a finite local file boundary and full schema validation. Invalid newest data still produces UNKNOWN rather than silent fallback. HTTP requests add no fetch or provider path.
- Replacing a dictionary with its validated snapshot is internal caching only. Populations remain separate, source digests remain attached to views, live-phase suppression remains ahead of data projection, and unsupported existing draft patches remain explicit UNKNOWN cards.
- The PRO label now describes a recorded user-roster reference and discloses possible preselection candidates/unverified pro status. Challenger discovery does not imply every participant's rank. Low-health details now disclose first observed low-health frame sampling instead of implying every low-health episode.
- Acquisition artifact/source binding remains the original trusted `f4fa37...` provenance. Projection optimization does not retroactively rebind or regenerate those source artifacts. Extraction/coverage policy semantics are unchanged.
- `actual-projection-green.log` records 45 passing new statistics/PC tests after the two cache/size regressions were reproduced in RED. The isolation case asserts a single validation across repeated requests and protects the measurement policy/digest against input/output mutation; the size case admits a bounded archive above the previous 12MB cap and rejects above32MB. This reviewer did not rerun those checks.

## Verdict

Projection correctness/security: **PASS after the report-consumer correction; no unresolved important correctness findings**. Performance/spec acceptance: **NOT MET in the available actual-data receipt**; preserve that result and obtain fresh affected evidence after any additional optimization. This report does not claim final source sealing, remote CI, actual Windows/LCU execution, or coaching accuracy.

Reviewed source hashes after the report correction:

- `coach_v1/recall_stats.py`: `f5dfd253600e1e3ae8608811b015bc42eb09a60852e55454522f9d8237edbc30`
- `coach_v1/recall_pc.py`: `428c3bda638c2c3b8b2270960042f618168466e1c5ffa59a69e7bbc13d9b7e32`
- `scripts/report_queue_v23.py`: `785587bafbd5be092c3ca4838f6232f51d4597c50e15b7972358b12b542f6761`
- `tests_pregame/test_recall_pc_v23.py`: `ffdc306b0e6e0328cdf3f46ea558f69bc366088118a0cac7dc3966fdf4d02bc7`

The newest browser receipt's statistics hash precedes the copied-summary accessor; its original source binding must remain intact. The accessor/report consumer correction has separate generation evidence and does not change the measured browser projection behavior.

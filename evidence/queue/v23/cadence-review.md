# Scoped frame-cadence correction review

Reviewer: `/root/v23_code_review`. Read-only review of `/workspace/scratch/v23-cadence-fix.diff`, the current extractor/contract/tests, and existing cadence RED/GREEN reports. No test reruns, provider calls, or private records were used. The four new cases are recorded in `statistics-cadence-green.log` (29 tests total); the original completed statistics evidence remains unchanged.

## Initial finding

**P2 — a lost final regular frame can still become a known zero.** The 90-second adjacent-gap tolerance admits a missing regular minute immediately before a short final frame. Start with received frames at `0,60,120,180,240,270` seconds, own first purchase at 140 seconds, opposite-laner purchase at 150 seconds, and own death at 220 seconds in frame 240's event batch. Removing frame 240 leaves `180→270=90` seconds, which passes the proposed guard. The final timestamp still covers the first-recall outcome window ending at 260 seconds, so the erased death can again be reported as known zero. The existing jitter/short-final acceptance test does not exercise a missing regular frame before that final frame.

The origin and declared-interval checks are conservative and correctly applied before extraction; exact measurement-policy equality correctly prevents old datasets from being silently treated as corrected evidence. Nevertheless, the final-short boundary needs a targeted correction before the missing-frame protection is considered complete. This report does not require rerunning unaffected UI or completed historical checks.

## Data consequences

The changed `POLICY` intentionally invalidates pre-guard public datasets. They must be rebuilt from retained private originals or replaced by a new trusted acquisition; changing their policy metadata would not verify their original coverage. The existing loader returns UNKNOWN for an invalid newest archive and does not fall back silently. An invalid input currently fails the collection/export attempt conservatively; this preserves safety at the cost of availability. Final source seals must bind the corrected code, contract, and new regression bytes.

## Final correction review

Main addressed the finding with `FRAME_ORIGIN_AND_CADENCE.v2`. The extractor validates the full raw cadence at a 65000ms maximum gap (minute cadence plus explicitly disclosed 5000ms analysis tolerance), then withholds the final received frame from position/health/gold observations and completion coverage. Events remain chronologically ordered across received buckets and are clipped to the retained coverage timestamp. At least two received frames are required. Both public and private extraction use this same boundary.

The final270s case is rejected for its 90-second gap. The final241s case may pass the raw 61-second cadence check, but retained coverage ends at180s: the first-purchase outcome window ending260s remains UNKNOWN, the final position cannot establish STAY, and purchases after180s are not treated as observed. This closes the reported counterexample while conservatively losing the final observation interval. Contract and PC/postgame limitation text disclose that loss. Strict policy equality invalidates both unguarded and earlier guard-version aggregates.

Read the two new terminal-boundary regression cases, the adjusted incomplete-window fixture, and `statistics-terminal-report.md`. `statistics-terminal-green.log` records **31 tests, OK**; earlier RED/GREEN files are retained. The changed incomplete-window fixture preserves its original assertion while keeping its observed purchase before the new conservative coverage endpoint. This reviewer ran no tests.

Reviewed final hashes:

- `coach_v1/recall_stats.py`: `43684c859d4b656e859d21b58cea963b86b472ea9441d80cc7df3556932dc8e8`
- `contracts/queue-v23.md`: `1a95cc699b9da8c49d7a93383f17f15921b1f50071f45c8967ee550dac531a78`
- `tests_pregame/test_recall_stats_v23.py`: `b052ad654132d4be87b3d6cf2f1ad37970ecbbd4fe4220a6e43147a6dc2f4528`

## Verdict

Final scoped spec/code verdict: **PASS; no unresolved important findings in the cadence correction**. The initial blocker above is resolved. This verdict does not claim that pre-correction artifacts were collected with the new guard, that the pending final UI/collection integration run has passed, or that remote sealing/CI/acquisition has finished. The intermediate `cadence-integration.log` contains fixture failures from older sparse timelines; Main owns the separately announced realistic-fixture correction and fresh affected evidence. No historical checks need to be rerun for this review.

## Subsequent graph ownership correction

Read the two production-line changes and two new PC cases without executing tests. Each recall card now passes its view's champion into the Q15 graph query, so an opponent card no longer repeats the user's resource curve. The graph title also names that selected champion. The draft copy preserves the same patch/position and does not mutate the original draft; markers retain their original OWN/OPPONENT identities and population filtering. Source locator follows the selected champion as well.

`pc-graph-owner-red.log` records the missing explicit champion title before correction. `pc-graph-owner-green.log` records **11 tests, OK**, including real five-match recall extraction/view/card assembly that observes separate Ahri then Syndra power queries and a Syndra opponent graph title. Only the power-data projection is stubbed in that new ownership case. The earlier browser evidence is not claimed as execution of these later graph bytes; Main owns the final source seal and remote affected checks.

Scoped graph correction verdict: **PASS; no important findings**. No provider calls, private data access, or test reruns were performed by this reviewer.

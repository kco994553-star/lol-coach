# Final-frame boundary correction

The cadence review identified a counterexample to the earlier 90000ms gap allowance: removing regular frame240s from `[0,60,120,180,240,270]` leaves an accepted 90s gap before a short final frame. The final timestamp could then produce a false known zero for an erased death. The two new regression cases failed before this correction, as recorded in `statistics-terminal-red.log`.

The extractor now permits at most 65000ms between raw received frames: the declared minute cadence plus an explicit 5000ms timestamp-jitter tolerance. It validates the entire received timeline first and requires at least two frames. The final received frame is then excluded from frame-based observations and completion coverage. Event timestamps are gathered from all original frame buckets and clipped to the final retained timestamp; bucket placement does not override chronological event timestamps. Health/action frames, preceding-frame gold, first-purchase eligibility, and every outcome window use the retained coverage. The first frame must still be timestamp0; an optional declared frameInterval must still be integer60000. These are analysis integrity rules, not gameplay advice.

The public `coverage_guard` policy version is now `FRAME_ORIGIN_AND_CADENCE.v2`, with `max_internal_gap_ms:65000`, `timestamp_jitter_tolerance_ms:5000`, and `final_frame_excluded_from_observation:true`. Exact policy equality prevents earlier policy datasets from projecting silently as corrected evidence. No prior dataset or completed evidence was relabeled.

New regressions cover both boundaries:

- Removing240s before final270s now raises a cadence ValueError.
- Removing240s before final241s leaves an allowed61s raw gap but observation coverage ends at180s. A first140s recall window ending260s is UNKNOWN, the final241s position cannot establish STAY, and purchases after retained coverage are unavailable.

The partial-window fixture was adjusted from final240s to final300s so retained coverage240s still observes the200s purchase while its low-health180–300s window remains incomplete. This preserves the original missing-data assertion under the conservative endpoint rule. Timestamp jitter and short-final cases continue to pass.

Verification command:

```text
python -m unittest tests_pregame.test_recall_stats_v23
```

`statistics-terminal-green.log`: **31 tests, OK**. Only the changed statistics module was rerun; earlier25/29-test logs and completed wider checks remain intact. No provider calls, commits, pushes, collection dispatches, or unrelated edits were made.

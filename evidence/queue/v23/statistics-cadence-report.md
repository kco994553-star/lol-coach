# Queue v2.3 frame-coverage correction

The read-only reproduction confirmed a missing internal timeline frame could erase its event batch while the final timestamp still passed the window-completion check. A frame-local death at 220000ms in frame 240000ms was observed as one first-recall-window death in the complete input. Removing frame 240000ms changed that result to known zero and incorrectly established a low-health STAY observation at 300000ms. No provider calls were needed to reproduce this.

The smallest conservative correction validates sampling integrity before any extraction. The first received timestamp must equal 0, protecting early death/purchase eligibility. An optional declared `frameInterval` must be an integer 60000. Adjacent received-frame gaps may be at most 90000ms, allowing ordinary minute-frame timestamp jitter; a short final interval remains valid. A missing minute frame creating a 120000ms gap now raises ValueError for both public extraction and private postgame context. The 90000ms tolerance concerns analysis sampling integrity and is not gameplay advice.

`measurement_policy.coverage_guard` records this rule as `FRAME_ORIGIN_AND_CADENCE.v1`. Strict dataset validation requires the new policy, so an old dataset cannot silently project as corrected evidence. Old source-bound artifacts and completed evidence remain intact. CHALLENGER raw inputs discarded by the old collection cannot be retrospectively verified; retained private caches can be reprocessed locally when authorized. This work made no provider calls, commits, pushes, or collection changes.

Verification was limited to the changed statistics test module:

```text
python -m unittest tests_pregame.test_recall_stats_v23
```

`statistics-cadence-red.log` records the missing-frame, missing-origin, and missing-policy regressions failing before the correction. `statistics-cadence-green.log` records **29 tests, OK**, comprising the existing 25 statistics cases plus four new cadence-policy tests. New cases also cover 60030ms timestamp increments, a short final interval, rejected unsupported/incorrectly typed declared intervals, and rejection of pre-guard policy data. Earlier `statistics-green.log` and completed checks were preserved. No existing broader test suites were rerun.

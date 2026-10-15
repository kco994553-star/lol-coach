# Queue v2.3 statistics implementation evidence

Scope: only `coach_v1/recall_stats.py`, `tests_pregame/test_recall_stats_v23.py`, and `evidence/queue/v23/statistics-*`. Binding contract and implementation plan were read first. Existing USER decisions, candidate files, frozen contracts, and completed v2.1 evidence were not modified or rechecked.

## Result

The four public aggregate APIs are implemented: `extract_match(match, timeline, *, population, participant_ids=None)`, `build_dataset(observations, *, population, retrieved_at)`, `validate_dataset(data)`, and `recall_view(data, *, champion, position, patch)`.

`extract_private_context(match, timeline, participant_id)` additionally returns only the selected anonymous participant observation for local postgame use. It does not assign the user to CHALLENGER or PRO_REFERENCE; its internal LOCAL_PRIVATE extraction path is rejected by public population extraction and dataset builders. It strips cluster/population labels and returns only champion, position, first_recall, low_health, and sensitivity. For observed low-health actions, private context additionally includes `low_health.post_action_outcomes` over `(action_timestamp_ms, original_low_health_timestamp_ms + 120000]`. This distinguishes an opponent roam before versus after purchase without extending the original coverage requirement or changing any public aggregate shape. Signal names on action groups describe candidate observation types; consumers must require positive known outcomes before emitting an individual death/roam signal.

`extract_match` processes raw Match-V5 envelopes in memory, chronologically sorts frames/events, cancels ITEM_UNDO purchases, separates purchases after 120 seconds from starting items, and excludes first-purchase proxies preceded by death. A later death also terminates the first bundle, preventing postdeath shop items from entering it. Current gold comes from the frame strictly before the purchase. PRO_REFERENCE requires explicitly selected private participant IDs, while retaining the full match for opponent context. The extracted cluster key is a SHA256 digest used privately for deduplication; the public dataset contains neither that digest nor raw IDs, account fields, coordinates, or payloads.

Dataset cohorts separate population, patch, champion, and role. Each role pool counts distinct matches and up to two participant windows per match. First-purchase timing and preceding-frame gold report participant quantiles, valid n, distinct valid match n, and missing n; these descriptive quantiles are not independent participant confidence estimates. Outcome means give each valid match equal weight after averaging its valid participant windows. Counts include valid distinct-match n, participant n, missing n, known-window total, and observed total. Overlapping windows may count the same event, which is disclosed. No confidence, causality, mistake, intent, or coaching-accuracy claim is made.

Following Main's clarified contract, view selection requires **five distinct valid first-purchase timing matches** in the exact champion cohort, then five in the same-patch role pool; otherwise it returns UNKNOWN. Total matches with no valid first recall do not satisfy the rule. Timing/current-gold distributions separately expose UNKNOWN when fewer than five valid matches exist. Outcomes with no complete valid windows expose UNKNOWN and null mean/total, while a completely observed zero remains a known zero.

Low-health grouping uses the first positive-health frame at health/healthMax <= 0.30. A purchase before the next received frame and before death is PURCHASE; otherwise the next received frame must actually show the participant in their own lane before death to establish STAY. Jungle participants, missing health, missing next frame, unknown lane geometry, other-lane next frames, and death before action are separate exclusions. This selection rule is explicit and cannot establish why a player stayed or recalled. The 3x3 sensitivity grid preserves thresholds 0.20/0.30/0.40 and windows 60/120/180 seconds.

Outcome windows measure own death, observed opponent-laner kills/assists in another geometrically observed lane, enemy-team turret plates, and enemy-team jungle objectives. They require the window end to have been received. Missing relevant event location or team attribution yields missing data, never zero. Jungle first-recall counterpart roam remains UNKNOWN. Missing frame event streams are rejected. First-recall priority-gap outcomes use the same 120-second window and remain descriptive.

## New checks only

Command for each red/green cycle:

```text
python -m unittest tests_pregame.test_recall_stats_v23
```

- `statistics-red.log`: initial 12 behavioral assertions fail because the module is absent.
- `statistics-red-edge.log`: first-bundle postdeath contamination and missing per-metric sufficiency fields exposed before correction.
- `statistics-red-fallback.log`: both inadequate-valid-recall fallback cases fail before correction.
- `statistics-red-outcomes.log`: missing unknown-versus-known-zero outcome status exposed before correction.
- `statistics-red-boundaries.log`: missing event stream and jungle lane-roam false zero both fail before correction.
- `statistics-red-malformed.log`: malformed envelope and malformed metric types exposed before correction.
- `statistics-red-private.log`: missing private per-player context API exposed before implementation.
- `statistics-red-post-action.log`: private post-purchase roam timing exposed before correction (190s roam before 200s purchase; 220s after; 310s outside original 180–300s window).
- `statistics-green.log`: **25 tests, OK** after all changes.

The new tests cover chronological sorting, undo, bundles, death exclusions, pre-purchase gold, first-recall priority gaps, actual next-frame lane observation, low-health purchase versus stay, postdeath shop, opponent assist location, team plates/objectives, truncated windows, missing locations/health/gold, jungle exclusions, sensitivity cells, population isolation, patch isolation, selector validation, identity/shape allowlisting, deduplication, fallback, and unequal-window match weighting (0.25 match-weighted mean versus 1/3 naive participant mean).

Only newly implemented functionality was checked. Completed v2.1 checks and the full existing suite were intentionally not rerun, as instructed by the user. No commits or pushes were made by this workstream. The interface example in `statistics-shape.json` is explicitly synthetic and truncates the sensitivity grid for readability; it is not a real statistical dataset or coaching validation.

## Limits

All evidence here uses synthetic raw-shaped fixtures, so it proves implementation behavior rather than tactical correctness, representative sampling, or live Windows/LCU behavior. First-purchase timing misses recalls with no purchase and cannot establish exact recall start/completion. Frame gold is approximate, and item IDs describe actual purchase bundles rather than required cash or official item prices. Lane geometry is operational and does not measure wave state. Group assignments and first-observed low-health sampling introduce selection and survivorship effects. Five matches is an output minimum, not a guarantee of statistical sufficiency. Riot seed selection, population coverage, overlap, frame resolution, and unavailable variables remain limitations.

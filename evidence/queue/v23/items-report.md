# Queue v2.3 official items and candidate author report

Implemented `coach_v1/official_items.py`, new `tests_pregame/test_official_items_v23.py`, append-only `data/official_items/versions/16.20.1/`, mutable current/status pointers, and separate `knowledge_candidates/recall-v23.json`. No shared modules, existing reviewed packets, protected issues, USER rows, or completed all-roster archives were modified. No commit/push was made.

## Official item source

- Latest versions discovery: https://ddragon.leagueoflegends.com/api/versions.json
- Item URL: https://ddragon.leagueoflegends.com/cdn/16.20.1/data/ko_KR/item.json
- Exact source bytes: 733122; item rows: 870; source SHA256: `8fd60c77bddc212fd1550850f0db01caa68c05c9f11e377d52df03a9627f8085`.
- Machine source manifest: `data/official_items/versions/16.20.1/manifest.json`; full output example: `items-source-summary.json`.
- Network used inherited proxy and CA verification. Each request has 12-second timeout; discovery <=200000 bytes, item source <=5000000 bytes, item rows <=5000. URL allowlist and redirects rejected.
- An initial bounded fetch revealed four official mode/unused rows with an empty name. The initial validator rejected them (`ValueError: item text`). A regression test first reproduced this failure; validation now preserves official empty names, map flags, and store flags without inventing a display name. The subsequent bounded acquisition was published from its exact retained bytes. No champion-network collection or full catalog revalidation was performed.

## API for Main

`refresh_if_due(*, max_age_seconds=86400, force=False, fetch=None)` returns `schema_version=official-items.refresh.v1`, `state` (UPDATED/UNCHANGED/FRESH/OFFLINE_FALLBACK/UNAVAILABLE), check timestamp and epoch, catalog_version/item_count when available. Native process lock serializes publication. Retry after failure is bounded to at most one hour; read-only UI calls never fetch. Existing version archives are read/verified and never overwritten. Current pointer is retained on failed release acquisition. Corrupt source/hash/manifest fails closed.

`items_response(patch=None)` returns `schema_version=official-items.v1`, `status`, `requested_patch`, `catalog_version`, `catalog_patch`, `patch_match`, `patch_status`, `prices_usable`, `source`, `items`, `warnings`, `reference_only=true`, `approval_required=false`, `price_basis=FULL_ITEM_TOTAL_NOT_REMAINING_PURCHASE_COST`, and available refresh_status.

`source` contains url/version/sha256/archive_path/retrieved_at. Each item has string `id`, original `name`, `gold.total`, `from` component IDs, `maps` eligibility booleans, `in_store`, `required_ally`, `required_champion`. Consumers must check map/store/requirements and handle empty official names. Full game versions such as 16.20.1.1234 compare major.minor=16.20. Unknown/invalid/mismatched input patch returns no item rows and prices_usable=false; catalog metadata/source are retained. No cross-patch price is exposed for goal calculation.

Full item totals are reference costs, not remaining purchase gold; owned components, discounts, recipe details, eligibility, actual inventory, and special transformations still require consumer handling. Map/store flags are factual availability fields, not recommendations.

## Separate candidate packet

`recall-candidates.v1`: 20 rows, including four preferred champions (Yunara, Ashe, Kaisa, Caitlyn) × three classification dimensions (wave_clear_speed/low_health_sustain/opponent_finishing), plus eight RECALL/LOW_HEALTH advice rows. All rows have the seven Korean advice fields, exact archived Korean descriptions, URL/patch/SHA256/path/locator/excerpt, counterarguments, limitations and hold reasons. All values remain null; performance ratings were not invented. Low-health sustain means lane survival/pressure using mobility, range and ranged wave tools; selected descriptions do not establish actual safety without opponent range, vision, resources and cooldowns.

All 20 rows remain review_status=HOLD and tactical_verification=UNKNOWN; 16 HYPOTHESIS and four UNKNOWN classification/advice statuses. Eight advice rows have explicit macro_conditions.good/avoid entries marked HYPOTHESIS, source_support=UNKNOWN, scenario_origin=USER_REQUESTED_NOT_OBSERVED, intended_choice, per-condition 상대 권리/무효 조건, and empty executable conditions. RECALL rows cover all four requested good and three avoid scenarios; LOW_HEALTH rows cover all four stay and five recall scenarios. Objective timing requires actual observation; no timing threshold is invented. Official descriptions do not directly substantiate recall timing, wave priority, safety of staying at low health, or causal opponent roaming: no tactical AUTO_VERIFIED claim is made. Separate source/counter review remains pending and is not self-approved by authoring tests.

`candidate-author-build.py` records deterministic authorship; `candidate-author-summary.json` pins packet hash and reused source paths. Only the four required existing archive files are consulted for excerpts; completed 173-champion/865-fact evidence is reused unchanged. No source collection/approval work is delegated to the user.

## Verification evidence

- `python -m unittest tests_pregame.test_official_items_v23 -v`: initial RED had eight missing-feature failures (`items-tests-red.txt`).
- Updated candidate-schema RED: missing separate packet (`candidate-author-tests-red.txt`).
- Empty official-name RED: one expected failed publication (`items-unnamed-red.txt`).
- Final `python -m unittest tests_pregame.test_official_items_v23 -v`: 10 tests passed (`items-tests-green.txt`). Includes official byte/hash provenance, major.minor matching, unknown/mismatch price suppression, append-only publication, offline fallback/throttling, corruption rejection, malformed/bounded inputs, lock contention, unnamed mode items, all 20 source-locator/quote boundary checks, low-health mobility/range/wave definition, and full scenario/opponent-right/invalidator coverage.
- New artifact was read offline with items_response('16.20.1.1234'): 870 items, 254 with map11 and in_store true. Mismatch 16.21 suppresses all prices.
- Completed v2.1 and all-roster tests were deliberately not rerun per user instruction. No broad suite result is claimed. Main owns new integration/browser checks. Actual Windows lock/LCU execution remains outside this Linux task.

Candidate packet frozen for independent reviews at SHA256 `201d3421e7899ba6aae0296f1bfbedd1097284bceeba63893da16638f0fceedf`. Later edits after the first draft corrected low-health interpretation to the user definition and expanded the exact V6 scenarios. Expected failing regressions are preserved in `candidate-author-lowhealth-red.txt` and `candidate-author-scenarios-red.txt`. No packet edits occur during independent reviews.

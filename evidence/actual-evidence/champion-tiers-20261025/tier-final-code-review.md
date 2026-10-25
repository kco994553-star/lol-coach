# Final champion-tier/opponent code review — 2026-10-25

Verdict: **ONE P2 FINDING; resolve before completion**. Read-only review against product main `d1d00053dfd3710bb94e08549c7ca256ab0c43ee`; new untracked source files included.

## F1 — Advanced opponent table bypasses the selected tier projection

- Path: `web_r4/champion-page.js:30`, `opponentRecords()`.
- The default summary/frequent section uses `I.select(insights,...,state.tier)`, but advanced opponent records still use `S.opponents(...,stats,...)` against the old CHALLENGER-only artifact. The gate permits this for MASTER_PLUS and ALL. Its heading, caption and row counts do not disclose that it is a distinct Challenger-only sample.
- Counterexample: once a MASTER companion adds A-vs-B results, the default MASTER_PLUS row uses the unique M/GM/CH union while the advanced same-role table still shows only old CH results under the same tier selector. Under GOLD, the advanced table is forced empty even if exact GOLD encounter rows are present in the new index.
- Impact: contradictory or missing values in the same opponent exploration flow, misleading selected-tier provenance. Present CH-only data does not expose the contradiction, but the newly authorized acquisition path does.
- Fix: search/sort the selected exact `frequent_opponents` for the advanced table, keeping source basis and comparison behavior; alternatively clearly label and isolate a legacy-only reference, but that would still leave the selected tier without advanced search.

## Inspected boundaries

- Unique seed-cohort union, integer wins/N + Wilson recomputation, symmetric own/enemy roster observations, unknown roles, exact patch/tier, min N20, independent top/bottom overlap/ties and no fabricated cross-role samples.
- Public aggregate allowlist/private result schema, reuse of source references and unreviewed qualitative knowledge, endpoint authentication/private path denial, browser return-state metadata, public-only dependency content versions, preserved original source archives.
- Parallel collector-only review found no immediate blocker and ran 41 collector/policy tests PASS (3.045s) using local fixtures only. Existing budgets and no-provider/expired-window behavior retained.
- Future capacity risk: retained power/result state has a 10,000-record ceiling without rollover. It fails closed rather than deleting history; archival/rollover remains future work before sustained collection reaches capacity.

No providers, protected decision issues, or Git/source mutations were performed. This is a code/data-contract review, not tactical efficacy, real-game verification, new Riot acquisition, or deployment approval.

## Snapshot hashes

```json
{
  "coach_v1/champion_insights.py": "df3d10db95bcded661de999b9ecc4877e9a5ff31ae3f01f95983f76d7e0aae9d",
  "coach_v1/matchup_results.py": "8202c580fd3fc89f753f3380dcdc72a83617b40b10a7cc37e191f7d35370be8a",
  "coach_v1/champion_matchup_knowledge.py": "82df14658e5c31cdd49d4648d2f076032e294f18efeadac1be45329255ea9376",
  "coach_v1/riot_collector.py": "cc04027e83070a71ad5602f8238990cd3e24e29e5972f87ecdd0e070505b3ad6",
  "scripts/collect_power_stats.py": "749b038c7eb2737e3d40efe84f6d871a36b6a7deb139351d5ae0e7a29a8d2d05",
  "web_r4/champion-page.js": "0ec3729aa79231c2532e66037dd75e44d38b23770377e139ffda8d4920d6d19e",
  "web_r4/champion-insights.js": "9aa56036613e3bb1fcb1c60d4972e0396c3e9a72ea642f9e01fcd90282458d9f",
  "scripts/build_directions_web.py": "920072a8770124896a0f38e3b17d0a7ded0976422e92c6e86861ea65a43d50f7"
}
```

## Bounded follow-up — fixes frozen

Final verdict: **PASS for reviewed implementation scope**. F1 is resolved; no remaining confirmed blocker in this code/data-contract review.

- `I.opponentRows` now derives advanced search/sort/percentage/CI from exact selected `I.select(...).frequent_opponents`; the page passes the selected tier, and caption/count include selected patch/tier/role/basis. Isolated GOLD and MASTER_PLUS fixtures demonstrate different exact sample/rate values without CH fallback. Comparison buttons preserve the selected state.
- Collector processing now counts companion in-scope detail/backfill work only after queue/patch admission; legacy no-companion jobs continue counting accepted match/timeline pairs. Off-patch details still use the original request budget. Inspected the bounded regression fixture for both modes and the unchanged original RecallCollector test; no scope or budget relaxation found.
- Source-authority negative fixture now adds a deliberately unregistered synthetic path and explicitly asserts it is absent from CURRENT. This keeps the intended rejection test after `riot_collector.py` became an explicitly authorized archived successor; no security assertion was weakened.
- Root's full initial 1,016-test run found these two unrelated regressions and retains failure evidence. That run is not reported as PASS. This bounded follow-up does not replace the pending full stable rerun.

Bounded verification command:

```sh
python -m unittest -q tests_pregame.test_champion_insights_frontend tests_pregame.test_riot_collector.AllTierResultCollectionTests.test_off_patch_detail_does_not_consume_scoped_match_ceiling tests_pregame.test_recall_collection_v23 tests_pregame.test_actual_evidence_binding
```

Output: `---------------------------------------------------------------------- / Ran 20 tests in 0.691s /  / OK`. No provider calls, source/Git changes, deployment, actual acquisition, or tactical efficacy checks occurred in this follow-up.

```json
{
  "web_r4/champion-insights.js": "e33cc2de637a3db13d8d18c720757788285df7009c95c9767491a2534bcfff8d",
  "web_r4/champion-page.js": "eaf6dec5e882b0f579254f4100a0019eecba16cea062a0667d18b4d5f9c13b40",
  "coach_v1/riot_collector.py": "12b37794770b08d2dbb7aed2d20f0ad004474252464adc9bb5549de7d1a7149d",
  "tests_pregame/test_champion_insights_frontend.py": "69f9f50844d0f7b5711a191e704d0a0edad65efca5f6fd872c0d999fcf0531e8",
  "tests_pregame/test_riot_collector.py": "e976d8b34a63b5dc3e818f0bead20d822833b593b26a1d35d6032f6e4fb6d3d6",
  "tests_pregame/test_actual_evidence_binding.py": "b4177041a2141de7a010cd48966866e6ed13769bf8995ba6a01335b65de6ee2c",
  "tests_pregame/test_recall_collection_v23.py": "944613ccfba2e8cef56548e891f511cc6f81dffe8e4a9f71aa89cc363275b769"
}
```

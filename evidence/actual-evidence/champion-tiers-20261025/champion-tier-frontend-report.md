# Champion tier/opponent frontend report

Implemented in `/workspace/lol-coach-champion-tiers`; frontend source frozen after the passing seventh isolated browser run. No commits, full-suite runs, provider calls, Riot collection, or external requests were made by this subtask.

## Files

- `web_r4/champion-state.js`: absent tier defaults to MASTER_PLUS; 12 valid scope choices survive URL/modal/list/recent/opponent navigation. An explicitly unknown tier stays INVALID, renders empty, and requires selecting a valid scope; it never broadens to MASTER_PLUS.
- `web_r4/champion-insights.js` (new): pure exact patch/tier/champion/position selector matching Python selection, independent same-role frequent opponents (N>=1), own-role SAME_ROLE_ENCOUNTERS and other-role ENEMY_TEAM_ROSTER rankings (N>=20), independent maximum-five best/worst, overlap/tie disclosure metadata, and conditional phase-only qualitative knowledge selection.
- `web_r4/champion-page.js`: renders selected-scope summary and exact provenance; frequent opponent comparison; distinct qualitative source-author lists; five enemy-position statistical groups with N/Wilson95/scope/hash disclosures; same-document hash changes; conditional CHALLENGER legacy growth/duration references; isolated loading/parse-error/empty/insufficient states.
- `web_r4/champion.html` / `champion.css`: tier selector and responsive insights, manual opponent/support form remains collapsed advanced details with the same original IDs and behavior.
- `tests_pregame/test_champion_insights_frontend.py` (new): five test groups covering defaults/state/fact separation, real partial/empty/wrong-tier, synthetic ranking basis/threshold/order/top-five/ties/overlap, conditional source phase/category/top-five limits, and Python/JavaScript exact-scope parity.
- `scripts/browser_champion_insights.py` (new): source-hash-bound loopback harness with `run(env, output)` and standalone `--output`/optional `--base`. `INSIGHTS_BASE` accepts either a PC origin or public subpath. Screenshots and receipts write outside source.
- `scripts/browser_champions.py`: only explicit advanced-details opening before existing hidden controls are manipulated. Every existing assertion is preserved. Existing `test_champion_frontend.py` remains unchanged.

## Verified behavior

Default MASTER_PLUS accurately discloses PARTIAL with CHALLENGER available and MASTER/GRANDMASTER missing; retained 50 matches are the seed cohort, never all participants' match-time ranks. GOLD and every absent exact scope remain empty; zero-N rates are null. The separate 275-match growth reference and 50-match duration data appear only when the selected band contains CHALLENGER at the exact data patch, with explicit CHALLENGER and partial-source labels. GOLD/unknown scopes show no legacy means, markers, duration rows, or graph points.

Frequent same-role opponents are sorted by encounter N, retain A-team final-result perspective and Wilson intervals, and synchronize the preserved comparison controls. Own-role statistics use exact SAME_ROLE_ENCOUNTERS, other four roles require ENEMY_TEAM_ROSTER. Current retained data have no eligible N20 rankings; no cross-role ranking is fabricated. Independent high/low lists are capped at five, ties are display-ordered only by N/name, all-tied and overlaps are explicitly disclosed.

Qualitative lists use only CONDITIONAL_CANDIDATE LANING/JUNGLE records applicable to the chosen own role, preserve source-author categories, and explain reason -> action -> reconsider. RELATIVELY_EASIER_CONDITIONAL is independent from final-game winrate. OVERALL_UNSPECIFIED is never promoted into lane/jungle lists. Each source detail exposes author/expertise, guide patch, page/paragraph date distinction, patch-label uncertainty, evidence locator/hashes, retrieval time, URL, and REVIEW_TACTICAL_UNREVIEWED/AI attribution. Current gaps remain visible: Caitlyn4/3, Ezreal3/2, Fiora5/5, Graves5/5, Yunara5/2. No missing candidate is padded.

Handoff carries tier only in navigation return_state, never as a top-level gameplan fact. Root owns the strict loading-draft tier adapter. Unknown tier disables handoff until reset. Existing roster/search/recent/dialog/official facts/basic direction/growth/evidence/learning link/six-menu navigation remain in place.

## Verification

`python -m unittest tests_pregame.test_champion_frontend tests_pregame.test_champion_insights_frontend` -> **15 passed** (latest 0.837s). This is targeted verification only, not the whole suite.

`node --check web_r4/champion-page.js` and `node --check web_r4/champion-insights.js` -> passed.

`python scripts/browser_champion_insights.py --output /workspace/gp23-artifacts/champion-insights-browser-seventh` -> **passed**, source unchanged during run, 17 checks, 4 screenshots. Zero external requests, browser exceptions, or HTTP failures.

The browser verifies default PARTIAL exact N/wins, all five honest role groups, separate source-author categories/phase eligibility, GOLD reload/no source fallback, unknown-tier empty/reset, cancel/apply/list role filtering, preserved manual support controls, explicit context handoff and tier return, tablet820/390/320/200% layout and keyboard controls, explicit loading, and isolated aggregate/knowledge parse-error states.

Receipt: `/workspace/gp23-artifacts/champion-insights-browser-seventh/runner.json`. Screenshots cover desktop/tablet/mobile/narrow. Earlier failed harness runs are preserved rather than overwritten: first exposed scroll-snapshot timing; second/third exposed same-document unknown-tier re-render/placeholder behavior; fourth/fifth correctly found unavailable heroes under the test's observed MID filter; sixth found the test toggled an already open advanced details closed. The final harness synchronizes navigation/scroll and resets the keyboard details test state. No failed run is claimed as passing evidence.

The initial new navigation test was RED with INPUT_INVALID while the root-owned return-state tier adapter was pending; it passed after that adapter landed. The remaining implementation was exercised with targeted regressions and final DOM checks, not claimed as a preimplementation TDD sequence.

## Limits and root integration

No actual cross-role retained roster-result rows are present and no current matchup meets N20. Knowledge is unreviewed conditional source interpretation, not measured effectiveness or user-approved tactical advice. No live deployment/Windows LCU/real-match coaching effect was tested. The root owns public export/server/CI allowlists, publication seal, source audits, full-suite/independent review, docs, and commits. The old full `browser_champions.py` runner was not executed by this subtask; root can run it after all sources freeze.

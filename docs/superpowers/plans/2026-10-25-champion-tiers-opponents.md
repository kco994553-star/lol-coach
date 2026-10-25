# Champion tier and opponent insights implementation plan

> Use disjoint owners and source-bound RED→GREEN checks; the user's tier/statistics amendments are approved for routine implementation.

**Goal:** Default statistics to MASTER_PLUS, admit all ten leaf tiers within existing collection limits, replace the large manual context form with frequent lane opponents, source-based lane difficulty references, and enemy-role outcome lists.
**Architecture:** Existing outcome/power v1 data and validators remain; an identity-free private result/roster companion permits exact future cross-role aggregation. A static public index shares the same typed selection as the authenticated read-only API. Knowledge references are source-author opinions/paraphrases, separate from wins and tactical approval.
**Tech stack:** Existing Python, vanilla HTML/CSS/UMD JavaScript, unittest and Chromium. No new framework, paid service or runtime AI.
**Spec:** User's 2026-10-25 all-tier/default-Master+ and screenshot replacement instructions; contracts/champion-insights-v1.md; docs/gameplan-content/all-tier-collection-v1.md; docs/gameplan-content/champion-matchup-knowledge-v1.md.

## Constraints and review focus
IA v2.0 retains160 IDs. MASTER_PLUS = MASTER/GRANDMASTER/CHALLENGER; ALL=ten tiers; aggregate unique samples and recompute wins/N/Wilson, never average percentages. Current seed cohort does not establish A's historical rank. Missing tiers never fall back to CH. Same-role encounters cannot manufacture other-role associations. Preserve650 requests/300 matches/40 players/one page/900s and original cron/free/auth stops. Expired renewal window blocks real collection. Public data contains aggregates only; roster/result ledger remains private. Internet categories require correct lane/jungle phase and disclosed patch uncertainty; do not pad to five. Invalid URLs must fail closed. Preserve existing champion selection, drafts, saved picks, source evidence and learning roundtrips.

## Owned deliverables and acceptance
- [x] Audit actual tier admission, retained data and screenshot flow; record unrecoverable cross-role outcomes and expired credential window.
- [x] Data: matchup_results.normalize_match/build/merge; champion_insights build/select; strict unique hash/patch/roster/winner conflict tests, band coverage, N20/ties/overlap.
- [x] Collection: dated user admission amendment, bounded40-slot leaf/division rotation, separate private result completeness and detail-only backfill; original budgets and stops retained.
- [x] Knowledge: curated direct-lane/jungle references for five champion profiles; source URL/hash/locators, short paraphrases, overall-only exclusions and fewer-than-five disclosure.
- [x] Frontend: tier state, frequent opponents, separate hard/easy reference cards, five enemy-role outcome sections, advanced manual controls, empty/invalid/error and mobile states.
- [x] Integration: return-state tier remains reference metadata; explicit assets/API and source CI inventory, exact-scope tests. Clamp Wilson floating boundary without weakening strict validator.
- [ ] Full stable regression, private/public browser export, independent whole-branch review, required PR/main CI, verified publication/live, same-ID evidence and Notion update.

Ruling: one bounded daily target rotates all tiers instead of increasing request limits — respects existing free budget — acquisition breadth takes multiple runs and remains blocked until an allowed renewed key window.
Ruling: statistical ranking requires at least20 observations per exact opponent row — avoids ranking tiny counts as broad evidence — current N<=6 yields honest empty lists.
Ruling: top/bottom5 are independent rate sorts; overlap and rate ties are disclosed — preserves the requested math — small eligible populations can appear in both lists and do not imply causal opponent strength.
Ruling: only direct lane/jungle evidence enters difficulty lists; overall/scaling categories stay reference-only — avoids changing source meaning — some profiles have fewer than5 supported entries.
Ruling: only generated projection changes; old raw datasets/approval records are untouched — preserves evidence — actual cross-role counts await fresh permitted collection.

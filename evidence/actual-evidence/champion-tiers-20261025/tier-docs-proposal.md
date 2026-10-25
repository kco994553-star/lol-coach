# Tier/opponent follow-up — read-only documentation and progress proposal

2026-10-25 UTC. Inspected `/workspace/lol-coach-champion-tiers`, branch `work/champion-tier-opponents-20261025`, HEAD/base `d1d00053dfd3710bb94e08549c7ca256ab0c43ee` plus frozen uncommitted implementation. Parent reports GP23 results PR144 normally merged at11:45:06UTC to `f366d75dabc30464398c818d15b1350ecc0abd4a`; that results main CI was still pending at dispatch. This audit did not inspect later CI or claim a tier product commit/deploy/live success.

**No repository, Notion, provider or Git mutation.** Only this external artifact was written. No tests or network requests executed by this agent. Repository data below was read and counted; test/browser outcomes are explicitly attributed to existing receipts/reviews.

## Baseline to preserve

Use the **post-GP23**160-row feature matrix, not the tier worktree's pre-results baseline. Read `/workspace/lol-coach-gp23/docs/gameplan-content/frontend-v2-feature-matrix.json` and its progress assessment:

-160 canonical leaf rows, equally weighted0/0.5/1.
- Overall exact score sum72.5 →45.3125%, displayed45.3%.
- Frontend exact score sum84.0 →52.5%.
- Area2:32 rows, overall17.5/32=54.6875% (54.7), frontend25/32=78.125% (78.1).
- GP23 DONE41/PARTIAL3 and previous source/CI/Pages/live receipts remain their own release. Tier work must not inherit GP23 deployment or pass status.
- No denominator growth, new top-level area, cross-role rows, new taxonomy80 completion count or additive video/approval count.

## What exists and what remains unavailable

Reviewed `contracts/champion-insights-v1.md`, `all-tier-collection-v1.md`, `champion-matchup-knowledge-v1.md`, `champion-tier-opponent-implementation.md`, current IA2.x body, actual aggregate/knowledge JSON, `champion-page.js`, frontend tests and browser assertions.

| Dimension | Current confirmed scope | State that must remain explicit |
|---|---|---|
| Acquisition admission |10 leaf seed tiers; deterministic40tier/division slots using existing single schedule; MASTER_PLUS/ALL are union filters, not API source tiers | Implementation/fixture scope; no newly authorized key window and no current provider probe |
| Retained observations |50 unique REAL CHALLENGER-seed cohort matches, patch16.20, source digest1f6f276d153bc11978670b0644ee31b16b28f260deb1be23196aabf0053d64fc | New acquisitions0; A participant's rank at match UNKNOWN. Seed cohort is not all participants' rank/MMR or a representative tier population |
| MASTER_PLUS |50 retained matches; only CHALLENGER; MASTER/GRANDMASTER missing, PARTIAL | Must not call this complete Master+ data |
| ALL |Same50 unique matches; nine leaf tiers missing, PARTIAL | Must not add50+50+50 across aliases or present all-tier acquisition |
| Other9 leafs |EMPTY/null rate/N0, no fallback | No inherited CH numbers/growth/curves for GOLD/invalid/unknown scopes |
| Same-role opponents |N-descending observed encounters; rate is A-team final game win;1266 public rows across CH/MASTER_PLUS/ALL are repeated scope projections | Not1266 new matches; largest current pair N6; zero actual N20-eligible ranking rows |
| Cross-role |Private anonymous result companion and aggregate code exist; fields use opposite team observed positions |Zero retained roster-result matches, zero ENEMY_TEAM_ROSTER rows; each cross-role ranking empty. Code/fixture success is not acquisition |
| Knowledge |5 authors/5 champion-role profiles,45 records=39 CONDITIONAL_CANDIDATE+6 REFERENCE_ONLY |Not USER-reviewed, not tactical-approved, coaching=false; not173 champion coverage or80 completed content topics |
| Source specificity |Caitlyn BOTTOM4difficult/3easy/2reference; Ezreal3/2/4; Fiora TOP5/5/0; Graves JUNGLE5/5/0; Yunara BOTTOM5/2/0 |Counts are sourced conditional records, not reliable top5 worldwide. Same-category alphabetical order is display stability, not stronger/weaker ranking |
| Patch/source |MOBAFire5 authors, public HTTPS reads in retained research; source HTML/quote/paragraph hashes and locators, actual final URL |16.20.1 Riot catalog versus source26.x mapping UNVERIFIED; current title/page date is not paragraph currency or expert credential verification |
| Graphs/other features |Tier guards prevent unsupported scope fallback; growth275 remains separate CH reference |No new N100 outcome curves, patch time series, runes/build statistics, bot2v2 conditioning or participant rank evidence |

Authors are rowzkit, Pengwan, Anoying bro5, Coach Myga, inFinem. Source categories/author paraphrase, AI conditional action and AI limiting condition stay separately labeled. Public artifacts contain no continuous original quotes/full HTML; retained research bytes stay outside repository/public outputs. Existing protected decisions/Frozen350 remain unchanged.

Existing key window expired `2026-10-16T10:16:49Z`. This is a stored gate fact; **do not claim a fresh observed403/key validation failure**. Actual collection BLOCKED pending secure renewed key plus explicit allowed window, while independent implementation proceeds. Keep existing650requests/300attempted matches/40players/onepage/2retries/900s shared ceilings and immediate first401/403 stop.

## Canonical affected rows and conservative scores

The implementation task document loosely maps some items to2.4 and maps tier aggregates to2.2.1. The **IA body is canonical**:2.2.1 is champion basic directions, not aggregate tier statistics. Use2.2.2/2.2.5 for that responsibility.

Scores are `(overall, frontend)`. The table proposes **future deltas only after exact source CI and deployment/live gates**. During the current unshipped verification window, publish no score increase.

| IA ID(s) | Existing scores | Actual responsibility / recommended action | Proposed gated scores |
|---|---|---|---|
|2.1.1,2.1.3~2.1.6 |1,1 |Tier state/default/filter persistence through selection/dialog/recent/return adds compatibility evidence; already full scoped flow |Unchanged1,1 |
|2.1.2 |0.5,1 |Roster/name/observed-role search is not new representative role evidence; no score for adding tier dropdown |Unchanged0.5,1 |
|2.2.1 |0.5,0.5 |Champion baseline-direction delivery not completed by tier aggregation or separate matchup candidates |Unchanged0.5,0.5 |
|2.2.2 |0.5,0.5 |DefaultMASTER_PLUS/ALL/leaf summary adds exact wins/N/CI/cohort coverage. Population pick/ban rates still absent |Unchanged0.5,0.5; update evidence/missing |
|2.2.3 |1,1 |Same-role A-team final outcome relation now honors exact tier scope; real cross-role unavailable |Unchanged1,1; no duplicate completion credit |
|2.2.4 |1,1 |Frequent observed same-role opponents, deterministicN order, selection and advanced manual comparison; conceptual2.4 cross-role addition should be traced here and2.2.3/5 without adding rows |Unchanged1,1 |
|2.2.5 |1,1 |Tier meaning/available/missing/patch/source/time/N/CI and UNKNOWN participant rank; collector status separate |Unchanged1,1 |
|2.3.1,2.3.2,2.3.4 |0.5,1 |Scope guard preserves graph/growth semantics; actual curves/spikes/support unchanged |Unchanged0.5,1 |
|2.3.3 |0,0 |No patch-series winrate trend |Unchanged0,0 |
|2.3.5 |1,1 |GOLD/invalid unavailable state and no-fallback regression are renewed evidence, not new capability points |Unchanged1,1 |
|**2.4.1** |**0,0.5** |New source-bound LANING conditional reasons/actions/change_if for4 non-jungle champion-role profiles. Qualification as reference content must remain; no current tactical validity |**0.5,0.5** recommended partial content; full acceptance=false |
|2.4.2 |0,0.5 |No operations matchup content. Generic statistics and OVERALL_UNSPECIFIED references do not fulfill operations |Unchanged0,0.5 |
|2.4.3 |0,0.5 |No fight matchup content; final team win association is not fight strength |Unchanged0,0.5 |
|**2.4.4** |**0,0.5** |Separate difficult/easier conditional lists, author categories, scope/missing<5 and source details. Only LANING/JUNGLE; all phases not done |**0.5,0.5** recommended partial content; full acceptance=false |
|2.4.5 |0,0.5 |**Still unfulfilled as selected-opponent detailed response.** `matchupCards()` still renders lane/operations/fight data-insufficient placeholders; separate list cards are not wired into selected-opponent details |Unchanged0,0.5; references may link as partial evidence but no score |
|2.4.6 |0,0.5 |Manual supports persist; no actual four-champion2v2 matchup evidence |Unchanged0,0.5 |
|**2.4.7** |**0,0.5** |Graves JUNGLE10conditional records address jungle tracking/invasion/camps/countergank/objective conditions, separate from laning |**0.5,0.5** recommended partial content; one champion-role only, full acceptance=false |
|2.5.1,2.5.2,2.5.4 |0,0.5 |Rune/build/synergy statistics absent |Unchanged0,0.5 |
|2.5.3 |0.5,1 |No new verified skill-order/spike statistics |Unchanged0.5,1 |
|2.6.1~2.6.5 |1,1 |Tier stays navigation metadata in return_state; not transmitted as match/tactical fact. Manual same-/cross-role relation and saved composition preserved |Unchanged1,1; exact return regression required |
|7.2.1,7.2.1.1,7.2.2 |0.5,0.5 |New admission/schedule/private companion/result-ledger gate and missing-authorization disclosure; no actual run/acquisition/live environment proof |Unchanged0.5,0.5 |

Frontend values intentionally remain conservative. No overall row gets1: the new content is partial research/reference, not all-phase or all-champion tactical acceptance. Row2.4.4's stage-wide UI is incomplete because operations/fight still lack candidate lists. Honest empty cross-role tables do not implement cross-role data acquisition.

### Optional frontend-only increments requiring a separate acceptance finding

The reviewer/root may later consider2.4.1 and2.4.7 frontend0.5→1 **only if** exact new-source browser/live receipts establish the entire presentation contract for their bounded reference-card projection, all5 profile/role scope branches, unsupported states, source disclosure/patch uncertainty, errors/loading,320/390/desktop/200%/keyboard. Existing17-check local insight receipt alone should not imply every supported profile and every hidden-state branch was rendered.

Do not infer these frontend upgrades just because cards exist. Recommended first update leaves frontend52.5 unchanged. If root decides the frontend acceptance is fully met for these two rows, keep coveragePARTIAL and full_feature_acceptance=false, and explain that frontend1 describes representation/navigation, not content validation.

## Formula and scenarios — do not compute from rounded45.3

For each dimension independently: `P =100 × sum(160 row scores)/160`.
Each0.5 point adds exactly0.3125 percentage points to total;1point adds0.625.

| Scenario | Overall sum/percentage | Frontend sum/percentage | Area2 overall / frontend |
|---|---|---|---|
|NOW: awaiting tier exact CI/deploy/live |72.5 /45.3125% → existing45.3 |84 /52.5% |17.5/32=54.6875%;25/32=78.125% |
|Recommended gated partial content:2.4.1/4/7 each+0.5overall |74 /**46.25% exact** |84 /**52.5%** |19/32=59.375%;25/32=78.125% |
|Optional after separately proven full reference UI on2.4.1/7 |74 /46.25% |85 /**53.125%** |19/32=59.375%;26/32=81.25% |

The exact overall46.25% lands on a one-decimal rounding tie. Python's `round(46.25,1)` gives46.2, decimal half-up gives46.3. **Root must retain its existing display-rounding rule and record it**, rather than choosing the larger number. Store exact sum74/raw46.25 regardless. This proposal does not silently change the project's rounding convention.

If final knowledge/source review fails on any row, withhold that row's0.5. No weighted credit by39records/5authors/173roster/80taxonomy or number of green tests. No cross-role/ALL data score until actual permitted evidence is acquired. An honest acquisition blocker must remain even after code/deployment succeeds.

## Proposed row metadata edits (when permitted)

For the three content rows: status scoped IMPLEMENTED then LIVE_VERIFIED only after actual flow; `coverage=PARTIAL`; `overall_score=0.5`; `frontend_score=0.5` recommended; `full_feature_acceptance=false`. Record exact evaluated scope as "source-bound conditional author references with separately labeled AI action/limitations for the listed champion-role pairs; no USER/tactical approval, no runtime engine activation". Do not call NOT_SUPPORTED false globally; identify unsupported roles/phases separately.

Update `missing` distinctly:
-2.4.1: broader champion/role/matchup and current-patch tactical validity absent; source mapping unverified; candidate-only.
-2.4.4: only laning/jungle, no operations/fight candidate coverage; fewer-than-five/unknown scopes not padded.
-2.4.7: GravesJUNGLE reference-only conditional slice; all-jungler route/matchup/population validation absent.
-2.4.5 unchanged functional gap: selected-opponent panel does not yet render candidate response.
-2.2.3/4/5 retain full scoped legacy acceptance but add new exact tier-filter and empty cross-role receipts; do not overwrite historical source evidence.

## Evidence update plan and gates

A new `evidence/actual-evidence/champion-tiers-20261025/` should receive product result/source manifest, exact product commit/normal PR/required jobs/mainCI, stable full-suite log+before/after source binding, independent reviews with fixed findings, local browser source-bound receipts, fresh export/hash/private-boundary/pro-retention and rollback, native Pages and actual publicHTTPS/browser evidence. Do not copy GP23 receipts as a new tier pass.

Fresh data provenance receipt must explicitly count unique CH50, MASTER_PLUSpartial50, ALLpartial50, other9empty, roster-results0, cross-role0, N20rankings0, new acquired0, source meaning/current key-window blocker.1266 rendered matchup table rows are scope projections, not underlying observation count. Source coverage receipt should separate39conditional/6reference/5authors/5champ-role and5MOBAFire URLs; original research bytes remain private, public source/quote/paragraph hashes/locators preserved.

`/workspace/gp23-artifacts/tier-data-review.md` records a bounded SPEC/QUALITY review with cross-patch conflict and reused-patch pinning corrections plus focused local tests. `/workspace/gp23-artifacts/tier-final-browser/insights/runner.json` reports local17checksPASS, source unchanged, finished11:45:32UTC. These are existing scoped receipts only. An earlier `champion-insights-browser-fourth/runner.json` is failed/moving-source history and must not be relabeled finalPASS. Root said stable full suite was running; this audit does not provide its result.

Source hashes observed (uncommitted/frozen snapshot; final root source binding remains authoritative):
- `contracts/champion-insights-v1.md`:6d3c033d85dfee7cfa375f115a8ed989fe1c13b482a8675f130122ac933ab5c6
- `docs/gameplan-content/champion-tier-opponent-implementation.md`:9aeee72184106baf204dd724e6b88bb33e397ee27054e02206ca5ebd43536b61
- `docs/gameplan-content/all-tier-collection-v1.md`:555dbe4dbdb62cf44edaff0da3f9f82507203829bfa35d9ce36e4518b9b7de85
- `docs/gameplan-content/champion-matchup-knowledge-v1.md`:f2bceed72be420253d144b8f3a5c033e78014945f6a7aa19da06fd3b19ec318a
- `web_r4/champion-insights.json`:366287cc6c294c46113420d7fd753e2e937987cacf2f6ae4823d6b70924a7bc6
- `web_r4/champion-matchup-knowledge.json`:d44a9bb9b96522687e81b31dffa1f3703289ca5d48d82955e2125a1a2dcb85bb

## Notion proposal — no writes performed

Future append/readback only after actual tier CI/deploy/live. Read these4 existing pages again immediately before authorized writes; preserve IDs/children/history:

- Champion page404f975df2e881f1a25edb8faf35ba79 — https://app.notion.com/p/404f975df2e881f1a25edb8faf35ba79
- Admin403f975df2e881bb9e5be4f6d1dbaba8 — https://app.notion.com/p/403f975df2e881bb9e5be4f6d1dbaba8
- Details403f975df2e8814ba9bfcd3a05d22b4d — https://app.notion.com/p/403f975df2e8814ba9bfcd3a05d22b4d
- Graph404f975df2e881beae11e44680a1fa91 — https://app.notion.com/p/404f975df2e881beae11e44680a1fa91

Latest section should say: tier/opponent selector implemented/verified at exact new product commit, acquired0/CH50only, MASTER_PLUS/ALLpartial, cross-role0/N20empty; separate39conditional/6reference/5authors/5champions with unverifiedpatch/review state; no tactical approval. Admin uses approved final score delta with160denominator, details links exact contract/source/test receipts, graph distinguishes implemented projection edges from unacquired result-companion/cross-role data, champion page explains frequentN versus conditionalknowledge versus final-team-win role tables. Keep source acquisition blocker visible. Do not append a "complete all tiers" or "all matchups" headline.

## Next write ownership

Root owns source freeze/final hashes/fullsuite verdict, Git/seal/PR/CI/main/Pages/live, collection authorization and final scoring decision. Root must first reconcile GP23 results-main f366 receipt with this product branch ancestry; no assumption that startingd1d already contains results-only history. Matrix writer uses latest GP23 score baseline72.5/84 and preserves unaffected160 IDs. A separately authorized docs/Notion writer can then apply the agreed metadata/score changes and append to the4existing pages, saving before/readback hashes and links. This audit agent is frozen; no permission or user approval inferred from preparing this proposal.

# Champion frontend implementation report

## Scope
Owned files only: `web_r4/champions.html`, `champion.html`, `champion.css`, `champion-state.js`, `champion-picker.js`, `champion-page.js`, and `tests_pregame/test_champion_frontend.py`. No staging or commits. No shell, exporter, server, seal, loading page, or draft module edits.

## Delivered behavior
- Responsive dark violet/gold selector with all 173 champions through PR138 baseline `search({limit:200})`, normalized Korean/English name search, real validated local sprite portraits and text fallbacks, count/no-result/reset, observed-position and unclassified filters, recent list capped at eight.
- Observed positions derive from the statistics publication, separate from authored profile roles. Position filter and provenance explicitly describe retained observations.
- Detail requires an explicit own position; retains champion/position across overview, statistics, outcome-based duration chart, baseline, official skill, and matchup sections. Optional opponent position/support fields remain explicit.
- Headline rates use the selected exact source scope and disclose N and summary confidence interval. Same-role A-vs-B rate always uses A perspective. Different opponent role prevents a misleading comparison.
- Ending-duration chart uses 13 published bins, draws only bins with `drawable` and N >=100, breaks at gaps, and retains an accessible data table. No invented curve for the actual sparse publication. Graph text states ending-condition outcomes are not directly measured strength and explains missing level/item/skill attribution.
- Baseline uses PR138 `getBaseline`; only verified `REFERENCE_ONLY` reference paragraphs render. Missing profile/position/phase states are explicit; no synthetic five-action plan. Official P/Q/W/E/R names/descriptions link to safe official Data Dragon URLs.
- Matchup phase commentary, bot 2v2 statistics, unsupported runes/builds/order/pick/ban rates display honest unavailable states.
- Two explicit CTAs call `LoadingDraft.createIntent` and navigate to encoded `loading.html#handoff`. Own-only versus full opponent context is deliberate. Browsing never writes a complete saved plan.
- Native dialog has temporary selection, Apply/Cancel, Escape, explicit Tab trapping and focus restoration. Its filters persist when reopened; cancel keeps applied state. Applying changes champion while preserving role and opponent context.
- Whitelisted hash state preserves query/filter/selector scroll/champion/role/context and round-trips through `intent.return_state`. Section scroll links preserve state on refresh. Invalid hash/storage input is guarded.

## Test evidence
`python -m unittest tests_pregame.test_champion_frontend`: 5 tests passing. Red run first failed all five on missing state implementation, recorded in `/workspace/frontend-v2-artifacts/frontend-red.log`; green in `frontend-green.log`.

Tests exercise real baseline service search over the production catalog, 173 coverage, Korean normalization, observed-vs-authored roles, state whitelist/corruption, recent limit/dedup/failing storage, temporary selection, and non-interpolated N99/N100 duration gaps with unchanged A perspective.

`node --check` passed for champion state/picker/page scripts. Direct Node interoperability test verified `LoadingDraft.createIntent` + `returnLink` + `ChampionState.decode` preserves the return state.

Full `python -m unittest discover -s tests_pregame` was started then interrupted at root request to avoid concurrent mutable suites; log preserved at `frontend-suite.log`. One earlier failure's progress index maps to `test_champion_handoff.ChampionHandoffTests.test_return_link_is_local_and_restores_state`; full details not emitted before interruption. Interrupted during `test_skill_display.SkillDisplayTests.test_unqualified_name_only_in_explicitly_typed_name_field`. Root owns final stable full suite. Do not treat this incomplete run as passing.

## DOM hooks and integration
Ready: `body[data-champion-ready="true"]`; selector `#champion-search`, `#position-filter`, `#champion-grid .champion-card[data-champion]`, `#result-count`, `#recent-champions`, `#empty-results`.
Detail `#champion-detail`, `#own-position`, `#change-champion`; modal `#champion-dialog`, `#dialog-search`, `#dialog-position`, `#dialog-grid`, `#dialog-selection`, `#dialog-apply`, `#dialog-cancel`, `#dialog-close`. Context `#context-opponent`, `#opponent-position`, `#ally-support`, `#enemy-support`; handoff buttons `#gameplan-own`/`#gameplan-context`.
Table rows have `data-series="all|opponent"`, `data-n`, `data-wins`, `data-perspective="A"`; plotted circles expose series/N/perspective. First/third headline metrics expose N/wins/perspective. Root integrates shared six-menu shell, export/server publication; QA worker handles real browser layouts and interaction evidence.

## Remaining validation
Browser QA and root stable integration/full suite pending at report time. No deployment or merge claims. Current actual sample is sparse; graph unavailability is expected rather than an implementation failure.

## Final IA completion and QA fix
- Added actual same-position opponent records with A-perspective win rate, wins/N, normalized Korean/English search, N-descending default, name sorting, and A-win-rate ascending/descending options. Rate sorting shows an explicit small-sample warning. Rows select the actual opponent and confirm its position to the already chosen own role.
- Added three separate matchup phase cards (lane or early jungle, operations, fight), each tagged `자료 부족` and showing explicit missing reason/action/reconsideration content. No tactical placeholder is promoted into an action recommendation.
- CTA labels now exactly `이 챔피언으로 게임플랜` and `이 상대를 넣어 게임플랜`.
- Added `detail_scroll` finite/clamped 0..100000 and `section` enum `overview|power|baseline|skills|matchup` to shared state. Selected tab and actual detail scroll survive reload/handoff return without replacing list query/filter/scroll. Coordinated strict `LoadingDraft` validator with handoff worker; direct interoperability confirmed.
- Browser QA reported desktop 200% CSS content-zoom overflow from `.hero-stamp`. Captured red evidence is `/workspace/frontend-v2-artifacts/zoom-probe/browser-result.json`. Hero flex wrapping, zero intrinsic heading minimum, control wrapping, and right alignment now accommodate reduced content width. QA rerun is owned by QA worker.
- Frontend test count now **7 passing**. New tests cover detail-scroll/section whitelist and actual same-role opponent summary/search/N-name-rate sorting/row-selection state. New red/green evidence: `frontend-ia-red.log`, `frontend-ia-green.log`, `frontend-sort-red.log`, `frontend-sort-green.log`. Node syntax checks still pass.
- New hooks: `#opponent-search`, `#opponent-sort` (sample/name/rate-desc/rate-asc), `#opponent-sort-warning`, `#opponent-count`, `#opponent-table-body tr[data-champion][data-n][data-wins][data-perspective=A]`; row buttons carry `data-champion`; `#matchup-content article[data-matchup-phase=lane|operations|fight]`; active detail tab has `aria-current=location`.

## Growth projection (root-assigned follow-up, final frontend freeze)
Added a separate read-only growth section within `#power`, using `growth_source` and the selected role's `growth` object. Growth275 and ending-outcome50 source counts/digests remain separate. Three plots show actual published champion/pooled-role sample resource rates in gold/minute, XP/minute and CS/minute. The title and explanatory copy identify cumulative observed resource divided by actual elapsed time. No N>=100 growth rule is invented; growth uses the publication's existing `visible` flag. Hidden values yield gaps and explicit missing/precision states, with N retained but no numerical means/delta/CI exposed. The table separates champion mean, role-sample mean, champion N, reference N, effective N, mean difference and **difference-only** 95% interval. The pooled reference is explicitly a retained sample and can include the champion.

Markers display only real retained LEVEL/ITEM records. Labels give median, interquartile range and N; level text identifies first saved-frame observation rather than exact achievement or skill-learning time. Item candidates display IDs without invented names. Copy explicitly excludes power, optimal-build and causal claims. The current real Caitlyn/BOTTOM slice has five LEVEL and zero ITEM markers.

Added a test-first pure `ChampionState.growthPoints` projection test for visible/hidden means, retained N/reason and difference-CI separation. Red evidence `frontend-growth-red.log`; green `frontend-growth-green.log`. Final frontend suite is **8 passing**; state/picker/page Node syntax checks pass.

Growth hooks: `#growth`, `#growth-source`, `#growth-provenance`, `#growth-charts .growth-chart-card[data-metric]`; actual chart circles `[data-growth-series=champion|reference][data-minute][data-mean][data-n]`; `#growth-table tr[data-metric][data-minute][data-n][data-champion-n][data-reference-n][data-visible]` (visible rows additionally expose exact raw means/delta); `#growth-markers .growth-marker[data-kind][data-n]`.

QA reported pre-growth **45 checks and 18 screenshots passing** in `qa-eighth`, then an expanded full pre-growth pass in `qa-ninth`. Final growth-aware QA rerun and final root suite remain root/QA ownership. No publication/merge/deployment is claimed here.

## Final plan-compliance corrections: position filter and recent roles
Root identified that selecting an explicit position filter must carry that role into detail. Added shared `selectChampion` projection used by both normal selection and rendered link URLs, so new tabs receive the same role. Valid explicit TOP/JUNGLE/MID/BOTTOM/SUPPORT filters provide the selected role. ALL/UNCLASSIFIED introduce no role and preserve only an already selected role; fresh ALL remains blank. Link modifier gestures now retain normal browser new-tab/window behavior.

Recent storage now retains at most eight deduplicated champion+position pairs under the existing separate recent key. `recentSelections` reads both new records and legacy ID-only arrays (legacy IDs retain unknown position); existing `recent()` remains backward-compatible and returns IDs. Explicit role changes and hero/modal selection update the pair. Recent cards expose role labels and `data-position`, restore a known saved role, and regenerate actual hrefs when filters change. A known recent role takes precedence over the current filter; unknown legacy positions use the normal explicit-filter/previous-role rule.

Added test-first role projection and recent-pair migration/dedup/roundtrip coverage. Red logs `frontend-filter-red.log`, `frontend-recent-red.log`; green `frontend-filter-recent-green.log`. Final frontend suite is **10 passing**, all three Node syntax checks pass. QA notified of final freeze and corrected explicit-filter versus fresh-ALL expectations.

## Mobile six-menu regression and metric trust-copy correction
Root assigned minimal shared `coach-theme.css` fix after actual mobile shared-theme regression. Followed measured debugging: standalone browser probe served the real dashboard and focused Riot ID form, returned to scroll0, then tapped the real hero-cycle button at390x844 and320x844.

RED at390: six links occupied two rows (y705.625/774), fixed navigation height145.375/y698.625, hero-cycle bottom707.547 (8.922px overlap), tap changed scroll0→26. At320 the navigation still incorrectly used two rows, though the shorter hero placement avoided overlap. Source mobile CSS still defined five grid columns despite six entries.

Single product fix: mobile navigation grid `repeat(5,minmax(0,1fr))` → `repeat(6,minmax(0,1fr))`. GREEN at390 and320: navigation height81.375, all six links y769.625, minimum target52x68.375, no horizontal overflow. Hero tap preserves scroll0, focused Riot ID, entered value and account-form bounds. Red/green measurements and logs: `/workspace/frontend-v2-artifacts/frontend-nav-{red,green}.{json,log}`; reproducible focused probe `/workspace/frontend-v2-artifacts/frontend-nav-probe.py`. QA owns permanent single-row/six-touch-target browser assertions; root owns old full browser rerun/reseal. No full unit suite run here.

Root also assigned small headline trust-copy fix: the third metric now names actual selected champions (`own vs opponent 게임 승률`) or own champion's specific-opponent metric without an opponent. Its own note independently flags N<100 `표본 부족`, names the perspective, and discloses available summary95%CI. Data/hooks unchanged. Frontend10 unit tests and champion-page syntax check remain green.

# GP23 A: UI + QA read-only audit

Audit date: 2026-10-25 UTC. Repository: `/workspace/lol-coach-gp23`. Starting HEAD: `8e67cce63a29decae9f64a21f7c387bf73824507`; `git status --short` empty before and after inspection/tests. No repository source, protected decision issue, approval history, external service, or tactical grade changed. Only this report and browser evidence under `/workspace/gp23-artifacts` were written. Read `AGENTS.md`, `docs/gameplan-content/gameplan-2-plus-3-v1.md`, and `codex-gameplan-2-plus-3-queue-v1.md`.

## Evidence and current execution path

- Shipped page: `web_r4/loading.html:35`, `body[data-gameplan-view=current]`, with only `#loading-coach` current result host; legacy result IDs deliberately absent. The preserved historical document is `tests_pregame/fixtures/loading-legacy.html`.
- Manual form -> `web_r4/loading.js:284 readInput` -> `:552 analyze` -> `web_r4/loading-engine.js:254 analyze` -> strict `:25 validate` -> `:295 LoadingCoach.evaluate` -> `web_r4/loading-coach.js:127 Planboard.evaluate` -> `web_r4/loading-planboard.js:912 buildDelivery` -> `web_r4/loading-presentation.js:9 project` -> `web_r4/loading-coach-view.js:384 renderPresentation`.
- Input supports old unversioned/v2, v3 scenario, v4 scenario+planning, with exact allowlisted keys. Ten distinct picks and valid own champion/role are required; unknown role assignments are allowed. Partial draft handoff does not run the strict engine until complete.
- Production delivery remains `gameplan-delivery-v1`: `phases.lane/operations/fight`, headline, exactly five actions, paragraphs, conditional details, coverage and tags. Current projection rejects a missing delivery contract; legacy projection still falls back to old fields (`test_loading_presentation.py`). Detached `gameplan-snapshot-v1` preserves input, delivery, versions; it is explicitly not a historical catalog loader.
- Existing engine data available for the new top cards: `team_plan`, `composition.{ours_full,theirs_full,role}`, `overall_commentary`, `direction_hierarchy`, `wave`, `operations`, `fight`, action summaries and narrative decisions. Keep selection/judgment in this common engine; view should project the same result.

## Fit to approved 2+3 direction

| Requirement | Current evidence | Gap / action |
| --- | --- | --- |
| Upper whole-composition + user-basic cards | View renders hero/title/support, four-row team comparison and `overall_commentary`; `loading-coach-view.js:399-407` | No distinct pair of top cards or common typed top-card delivery. Give each card a distinct responsibility; do not duplicate current paragraphs merely to fill space. |
| Preserve comparison | Four dimensions: win plan, good fight, macro, risk (`loading-presentation.js:16-21`) | Reuse unchanged. Mobile table becomes stacked rows with visible team labels. |
| Lower lane / operations / engagement+teamfight | `project` maps three cards (`loading-presentation.js:15`) | Fight is labeled `한타` and heading `한타를 풀어가는 방법`; detail title `한타 — 이렇게 싸우세요`. Update presentation wording and ensure expanded non-5v5 scope comes from contract. |
| Jungler translation | Lane -> `초반 정글`, operations -> `중반 운영` already exists | Retain; fresh current-page browser probe passed Sejuani/JUNGLE labels. |
| Five actions + visible coaching + folded details | `loading-coach-view.js:413-415`, default ordered actions and paragraphs; `:420+` detail panel | Already reusable. Preserve all 15 visible phase actions and visible execution/transition core; lower density must not hide essential action sentences. |
| Max-two short decision tags (proposal to validate) | `loading-planboard.js:175 deliveryTags`, action+condition+warning can all append; test asserts <=3 | Fresh 30-input probe found max 3. Caitlyn preset0 emits 3 on each phase. Select maximum two in final delivery, then projection/tests follow. No view-level tag decision engine. |
| Unknown / assumed / observed / stale | Current controls explicitly say hypothetical, not observation | New structured situation contract needed. Existing source draft freshness (`coach_v1/gameplan_input.py`) concerns pick imports, not per-jungler tactical facts. |
| Expanded combat output | `fight.awareness`, threats, start/target/stop and five action summaries exist | Current view has no dedicated typed always-visible objective/top-threat/immediate-action trio. Do not claim new threat reachability/participation/arrival/terrain assessment merely by renaming the card. |

## Scenario changes, reset, stale output and URL behavior

- Current controls are in folded `conditions()` (`loading-coach-view.js:85-105`), explicitly labeled `가상의 조건을 바꿔 비교합니다. 현재 게임에서 관측한 정보가 아닙니다.` Existing scenario enums: resources SUFFICIENT/LOW/UNKNOWN; wave EVEN/BUILDING/INCOMING/UNDER_TOWER/RETURNING/UNKNOWN; enemy_key AVAILABLE/SPENT/UNKNOWN; engage NONE/THEIRS/OURS/UNKNOWN; Darius start_skill.
- Planning controls: enemy_jungle UNKNOWN/AWAY/NEAR, goal, clear_window, optional enemy_support, ally_followup, enemy_wave, income, opportunity. They cannot represent two junglers with information state/source/time/location; freshness; wave size/location/manipulability separately; HP/mana and individual spell facts; combat context or actual contributor/arrival order.
- `change()` snapshots scenario/planning/period/preference, preserves focus hint and rejects stale asynchronous responses with request sequence. `loading.js:542` reruns full `LoadingStrategy.analyze`, then coach evaluation for selected period, updates report/preference, saves URL, and returns replacement report. `renderPresentation` replaces DOM children; tags/prose follow the same replaced report.
- Reset at `loading-coach-view.js:96` resets scenario and planning overrides to `{}`. It intentionally preserves selected period and risk preference. New situation state must be reset alongside both existing assumptions, and displayed assumptions must clear with tags/reasons.
- Editing any base-form input triggers `stale()` (`loading.js:288`): destroys current view, hides `#loading-results`, removes plan-ready state and saves partial draft route; new analysis required. Existing `inputContext` preserves scenario/planning across editing/handoff; when adding observation fields, define which are invalidated by roster/context change. Preserved assumptions must never silently become new observations.
- `LoadingPresentation.encode/decode` (`:24-33`) stores `version:1`, normalized allowlisted input, period, detail in `#plan=...`; max fragment length 20,000. It carries no output prose/source credentials. New input version/key needs engine validator, projection input-key list, draft adapter and server input schema work together. Existing links remain readable. Restore reanalyzes, validates period, then restores selected detail. SessionStorage is optional; URL is sufficient.
- Existing key-spent conditional apply only changes a supported lane scenario. Clicking again sets enemy_key UNKNOWN, rather than restoring an implicit observed cooldown. Existing operations/fight conditional examples have no apply button. Preserve this epistemic distinction when adding controls.

## Browser and mobile risks

- Fresh **shipped** probe passed desktop PC `/loading` at 1440x1000 and exported public `/lol-coach/loading.html` at 390x844. It verifies current DOM only, four comparison rows, five actions each phase, coaching text, detail open/close, risk/input updates, reset equality, period, URL/reload/fresh-page restore, general-only scope, jungler labels, contextual Malphite plan, stale-hidden form edits, no horizontal overflow, no JS errors. Receipt: `/workspace/gp23-artifacts/ui-baseline-browser/result.json`; screenshots `desktop-current-gameplan.png` and `mobile-current-gameplan.png`.
- **Important coverage boundary:** `scripts/browser_loading.py` runs `browser_current_gameplan.run` first; its large following JS suite routes loading URLs to the historical fixture. `scripts/browser_loading_presentation.py:128-129` rewrites every page creation through `legacyPage`, so BASIC/EDGES/CONDITIONS/V11/NARRATIVE all run the historical DOM. Their 320px, 200% root-font, keyboard, maps, legacy links and narrative checks are regression evidence, not shipped-current-page 320/200% certification.
- Add true current DOM tests at 320 and 390 widths, 200% text, keyboard-only open/return/change/reset, long labels and unknown/stale field cases. Test all top+lower cards, not only global scrollWidth. Check clipped descendants/long selects, tag wrapping and visible stop conditions.
- Existing CSS uses minmax(0,1fr), overflow-wrap:anywhere, wrapping tags, 44px+ detail buttons and visible focus. At >=1280px unopened lower cards are three columns; below1280 open detail hides master. New upper cards need their own two-column desktop/one-column mobile layout with min-width:0 and long text checks.
- Header art and long prose currently make a tall mobile page: every phase has five actions plus 2-5 paragraphs. Do not shorten with clamps or move core actions into disclosures; measure real reading load/duplication after 2+3 insertion.
- Tag colors include purple action/condition, amber warning and gray scope. Visible label plus aria-label conveys meaning independently of color. New two-tag policy must preserve actual risk/uncertainty, not discard it solely to make all tags purple.
- Existing detail/maps/formations remain in shared files and historical presentation branches; currentOnly deliberately omits `.plan-retained` and old DOM routes. Do not reintroduce old DOM wholesale or accidentally remove the reusable map/formation consumers.

## Exact test/run/export/seal entry points

From `/workspace/lol-coach-gp23`:

```bash
# Executed in this audit: 62 tests, PASS, 9.497s; no bytecode writes.
PYTHONDONTWRITEBYTECODE=1 python -m unittest -q tests_pregame.test_loading_presentation tests_pregame.test_gameplan_coaching_content tests_pregame.test_gameplan_backend tests_pregame.test_gameplan_direction tests_pregame.test_gameplan_input tests_pregame.test_gameplan_registry

# Source seal verification (read-only); selected affected tests are chosen under --tests.
python scripts/verify_actual_evidence.py
python scripts/verify_actual_evidence.py --tests

# Full existing loading browser orchestrator; creates repository evidence and also runs game-info.
NODE_PATH=/opt/codex/cua_node/lib/node_modules CHROMIUM_EXECUTABLE=/usr/bin/chromium python scripts/browser_loading.py

# Static public allowlist output; directory must be absent or empty.
python scripts/build_directions_web.py --output /tmp/gp23-public/lol-coach
python -m http.server 8766 --directory /tmp/gp23-public
# Open http://127.0.0.1:8766/lol-coach/loading.html

# Optional actual local PC server; writes only to supplied data dir.
python scripts/launch_pc.py --port 8765 --data-dir /tmp/gp23-pc --no-browser
# Open http://127.0.0.1:8765/loading
```

`browser_current_gameplan.py` is a callable `run(env,out)` helper, not a standalone CLI: environment keys LOADING_PC, LOADING_WEB, LOADING_OUT, NODE_PATH, CHROMIUM_EXECUTABLE. This audit created isolated `create_server(...,port=0)` and exported static ThreadingHTTPServer instances in a temporary directory, invoked only that helper, then closed both. No provider or LCU call was made.

- Public assets: explicit `scripts/build_directions_web.py:FILES`; exports shared loading engine/view/CSS/data and existing map assets, no private app/data. Adds `build-info.json` with source commit and exported hashes. It versions five key loading assets with hash query strings; PC server deliberately rejects queries. New asset modules need export and server allowlists.
- PC routes: explicit mapping in `coach_v1/pregame_server.py:377+`, `/loading` and `/loading.html`, script/CSS/JSON. New input/context fields also need Python normalizer routes where used.
- Browser source watcher: `scripts/browser_loading.py:SOURCES` and `affected()`. Include new modules so changes cannot skip current/legacy browser work; absent GITHUB_EVENT_PATH runs checks.
- Source authority: `scripts/verify_actual_evidence.py:CURRENT` contains exact source paths. `allowed_new()` accepts only CURRENT/SEAL/archived predecessor paths, JSON data roots, and `.json/.md/.log/.png` under `evidence/actual-evidence/`. A new GP23 doc/test/module path outside these sets must be added deliberately or bounded_changes fails.
- `--prepare` is the authorized implementation workflow to regenerate `contracts/amendments/2026-10-16-actual-evidence.json` after final edits. It archives exact predecessor bytes, preserves existing archives, updates current source/data hashes, keeps inherited approval false, created decisions0 and coaching_accuracy null. Do not hand-edit protected predecessor hashes or imply approvals. Run `python scripts/verify_actual_evidence.py --prepare`, then verify and --tests. **Not executed in this read-only audit.**
- CI `.github/workflows/pregame-ci.yml` chooses evidence mode when actual-evidence contract exists; installs pinned Python requirements and Playwright1.62.1, runs source verifier+affected unittest modules, then actual-evidence/directions/loading browser runners. `private-mvp-ci.yml` supplies corresponding private regression. Reuse previous historical receipts only for unchanged behavior, never as proof of new GP23 decisions.

## Existing generated-output reproduction options

1. `node scripts/export_gameplan_five.js /workspace/gp23-artifacts/baseline-five` writes untouched engine `input`, current projection `view`, delivery to raw.json and prose/comparison/tags/actions to examples.md. Five fixed roles: Caitlyn preset0/BOTTOM, Fiora preset1/TOP, Graves preset1/JUNGLE, Ahri preset0/MID, Lux preset0/SUPPORT. Source patch and all `loading-*.js/json` hashes are stored. Default writes tracked docs, so pass external output during audit.
2. `node scripts/build_gameplan_preview.js /workspace/gp23-artifacts/gameplan-preview.html` makes offline embedded preview from production analysis, portraits/data embedded, Graves/Fiora/Caitlyn fixed cases. Preview uses non-currentOnly projection and its own template: useful as an old artifact, not proof that shipped UI is 2+3. Its download saves input/area/hashes, not complete output.
3. Pure Node `const E=require('./web_r4/loading-engine.js'), C=require('./web_r4/loading-data.json'); C.coaching_knowledge=require('./web_r4/loading-knowledge.json'); const input=E.exampleInput(C,0); const report=E.analyze(input,C);` reproduces without network. `P.project(report,{currentOnly:true})` gives exact current projected structure. Save entire report/input/view and git SHA externally for new cases.
4. Existing docs raw output: `docs/gameplan-content/five-examples/{raw.json,examples.md}`; older direction results: `evidence/actual-evidence/gameplan-direction-20261024/generated.json`, historical narrative/v13 outputs under handoff-v11. These retain their historical scope and must not be relabeled new GP23 output.

Current exporter is insufficient for GP23-35~38 without changes: no random seed/selection algorithm; TOP case is Fiora rather than tank; no paired single-change cases; raw.json lacks explicit git commit/full report and quality evaluation; hash list excludes `loading.js` and non-`loading-*` dependencies such as directions-engine/skill display. Preserve old outputs and create fresh new-case evidence with SHA/support boundary.

## Prioritized findings and counterexamples

| ID | Severity | Evidence / counterexample | Disposition |
| --- | --- | --- | --- |
| UI-01 | P1 scope gap | Three current cards + prose cannot demonstrate distinct whole-team vs user-basic contract | Add engine-backed upper pair; preserve four-row comparison and lower5/prose |
| UI-02 | P1 integration dependency | Unknown/stale enemy jungle observation cannot be represented; current enums are user assumptions only | Add typed situation input + same report output before presenting observation badges |
| UI-03 | P2 | Caitlyn preset0/BOTTOM produces 3 tags on each phase; proposed baseline is2 | Enforce two in delivery; test final decision consistency, keep uncertainty text visible |
| UI-04 | P2 | Fight card says 한타; 1v1/gank/objective combat has no exposed typed context | Rename only alongside shared expanded combat result; preserve source limits |
| UI-05 | P1 verification gap for new release | Current-only browser covers1440/390; 320/200% checks all use fixture | Add shipped-current 320/200%/keyboard tests for new controls/cards |
| UI-06 | P2 reproducibility | Fixed five output example includes Fiora and lacks SHA/paired changes | New seeded tank/jungle/mid/ADC/support cases, raw input/report/view, hashes/SHA and bounds |

Counterexample1: stale enemy-jungle source timestamp + unchanged assumed near/away must not display as current observed position; input contract must reject/expire observation or display stale with no invented ETA. Counterexample2: upper basic push plan plus lower large-wave/resource/followup restrictions must express a conditional transition, not simultaneous unconditional push/pull. Counterexample3: tank target selected without ally followup or with threatened carry must not promote deep engage by a new tag. Counterexample4: reset after scenario + future situation edits must remove all old tags/reasons/badges together, including URL/reload restoration.

Add: typed top2/situation projections and exact current DOM coverage. Remove: repeated top/lower filler sentences only if equivalent core meaning stays visible. Fix: max tags, fight wording, new state propagation/reset. Do not do now: tactical approval, support-count promotion, real-match efficacy claims, protected issue mutation, deployment claims, or full legacy DOM restoration.

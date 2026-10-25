# GP23 UI implementation handoff

Status: owned UI implementation complete and verified locally. No agent commits/amends. Root owns final source seal, combined validation/CI, release decisions and deployment. No protected issue, approval history, external service, tactical grade, or live-game connection changed. Real coaching N=0.

## What changed

- New normal Analyze submits v5 with explicit unknown situation defaults. Existing v1-4 links replay without migration; editing their existing assumption controls preserves the v4 legacy flow. Draft/handoff capture preserves inputContext version; only explicit normal Analyze upgrades it.
- `loading-presentation.js` projects core `gp23.top.teams/user` as two overview cards and uses core phase output for the three lower cards. Whole-team comparison stays intact. Fight wording is `교전·한타`; jungle translations remain.
- Each lower card retains exactly five visible engine action rows plus coaching prose. Goal appears once in the first action row; combat threat status follows that goal, then the existing location/action/limit/transition rows. Current priority is explicitly unknown when actor-specific information is missing. Named mechanism samples are disclosed as candidates, including means/reason/unknown reach; they do not become named main threats. Core scenario_effect stays visible.
- Optional controls derive keys/options from `LoadingSituation.fields`. Pre-game changes create only assumed/user-scenario/null-timestamp or unknown/null records. Current state and unknown count are visible; historical REVIEW source/time/stale states are labeled and controls read-only. Reset clears scenario, planning and situation together. Existing save/restore/Back/focus paths carry situation.
- Duplicate legacy resources/wave/ally-followup/enemy-jungle/enemy-wave controls are hidden only for current v5; carried values get a read-only note. Old plans and historical views keep all controls and semantics. Enemy-specific key comparison remains separate from own key_skill, per core clarification. Existing cost/goal/opportunity/risk/period/reset remain.
- Learning links use `LearningRoom.createLearningURL` with champion/role and only claim IDs attached to current phase actions and known report claims. If none, champion/role alone. Full plan return URL stays in session storage behind opaque token; the learning URL contains no ten picks or scenario fields.
- Responsive overview cards stack on mobile. Source labels, wrapping controls, keyboard focus and core content remain visible at tested widths and text sizes.

Owned files changed: `web_r4/loading.js`, `web_r4/loading.html`, `web_r4/loading-coach-view.js`, `web_r4/loading-presentation.js`, `web_r4/loading-presentation.css`; new `tests_pregame/test_gameplan_2plus3_ui.py` and `scripts/browser_gameplan_2plus3.py`. `loading-coach.css` assigned but unchanged. Other files in shared git status belong to other task owners.

## Verification

- Initial read-only audit: `/workspace/gp23-artifacts/ui-audit.md`; baseline current DOM receipt/screens at `ui-baseline-browser`.
- New unit contract/projection/replay tests: 3 PASS. Combined with existing loading presentation, coaching content, backend, direction modules: **52 PASS**, final run 9.296s, `gp23-ui-regression-final.log`.
- Exact preexisting browser tests `test_browser_handoff_preserves_coach_edited_scenario` and `test_browser_back_from_detail_keeps_updated_assumptions`: **2 PASS**, 4.307s, `ui-archive-regression.log`.
- New shipped browser runner: **PASS** at 1440 desktop PC, 390 public mobile, 320 public narrow. Each checks top2, comparison, lower15actions, prose, <=2 tags, hypothetical wrappers/source labels, atomic reset, share/new-page/reload, detail Back, historical stale/read-only/reset, current learning claim scope, 200% root text, keyboard activation, unsupported scope, partial input hides stale output, and archived v2 edits preserve v4. Final receipts: `/workspace/gp23-artifacts/gp23-ui-final-browser/{runner.json,result.json,browser.log}`; normal/200% screenshots included. No JS errors.
- `git diff --check` and changed JS syntax checks PASS.

Commands:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest -q tests_pregame.test_gameplan_2plus3_ui tests_pregame.test_loading_presentation tests_pregame.test_gameplan_coaching_content tests_pregame.test_gameplan_backend tests_pregame.test_gameplan_direction
PYTHONDONTWRITEBYTECODE=1 NODE_PATH=/opt/codex/cua_node/lib/node_modules CHROMIUM_EXECUTABLE=/usr/bin/chromium python -m unittest -v tests_pregame.test_champion_handoff.ChampionHandoffTests.test_browser_handoff_preserves_coach_edited_scenario tests_pregame.test_champion_handoff.ChampionHandoffTests.test_browser_back_from_detail_keeps_updated_assumptions
PYTHONDONTWRITEBYTECODE=1 python scripts/browser_gameplan_2plus3.py --output /workspace/gp23-artifacts/gp23-ui-final-browser
```

Runner uses isolated PC create_server and temporary explicit public export, no provider/LCU service. Output directory is required, so CI/root can choose artifact location. Source receipt stores commit plus current file hashes; final combined source SHA/seal is root responsibility.

## RED → GREEN evidence and rulings

- Initial tests failed because overview absent / old fight label; new v5 dependency temporarily ReferenceError while core owner implemented resolver. New projection tests now PASS.
- Unsupported Ornn scope falsely promoted to CONDITIONAL_PLAN on first integration: `ui-browser-first`; core owner corrected inherited coverage, final strict browser assertion remains GENERAL_ONLY3.
- Generic threat formatting omitted functional means: `ui-threat-red`; corrected candidate formatting.
- Reviewer found arbitrary named capability samples could read as priority: `ui-priority-red`; core provided unknown priority record and UI moved samples into disclosure. `ui-priority-green` PASS; final version also includes visible scenario constraint after `ui-threat-effect-red`.
- Archival edits auto-upgraded v5: `ui-legacy-red`; onChange now preserves old flow. Root found handoff draft capture still upgraded: readInput now defaults no upgrade and only Analyze opts in. Exact two old browser regressions PASS.
- Learning link inherited old phase claim ID: `ui-learning-claim-red`; now uses current gp23 action claims only. Final browser PASS.
- Ruling: old shared reports remain their original contract and have no synthetic new top2; explicit new Analyze opts into v5. This preserves archive semantics rather than silently rewriting their assumptions.
- Ruling: hide only overlapping v5 controls, show old carried values read-only, and preserve old controls/other costs. This avoids contradictory duplicate inputs without removing legacy behavior; agreed with root.
- Ruling: threats with no actor-specific priority remain unknown in main content. Mechanism candidates remain accessible and explicitly unranked. Generic reach assumptions do not identify a primary champion threat.

## Remaining boundaries

- Named per-actor current threat ranking remains partial/unknown in core; UI does not disguise samples as selected threats.
- Browser coverage confirms flow/layout, not tactical accuracy or real-match benefit. No coaching efficacy sample was created.
- Root still needs final seal refresh, integrated required verification/CI, source-bound artifact publication and release decision. This agent did not rerun historical full collections or source-preservation tests whose shared scope is root-owned.
- Existing comprehensive map/formation/legacy fixture regression remains available through `scripts/browser_loading.py`; the new runner tests the actual shipped current DOM and archived current links. No old map code was removed or modified.

## Post-freeze existing current-only helper finding

The unchanged `scripts/browser_current_gameplan.py` helper was run against final integrated source after UI freeze. It failed desktop unsupported-scope check at generated probe line35: Ornn/TOP correctly has GENERAL_ONLY3, but `data-tag-kind=ACTION` count3 instead of0. Receipt/log: `/workspace/gp23-artifacts/ui-current-regression-final/current-gameplan.log`. This is an engine GP23 tag scope regression, sent to root/core owner; view must not filter/rejudge engine tags. Existing new runner tested coverage and <=2, but did not test unsupported ACTION0; the unchanged older guard catches it. UI implementation remains frozen. Root/core will resolve and rerun; until then the existing current regression is FAIL, distinct from the new runner's PASS.

## Required tag regression follow-up

Root authorized adding only the unsupported-scope guard to the new browser runner. `scripts/browser_gameplan_2plus3.py` SHA256 is `b144950f63d4c898b0a4d70af5f23443e714906fb531029c36d744efd7e391a2`. After core fix (`loading-planboard.js` SHA256 `5f1be074de90b40f2e0e6f2dbff755ef8d62738897fb4aeabb76ec786a32fe28`), the expanded runner PASS at `/workspace/gp23-artifacts/gp23-ui-tag-final-browser`, including GENERAL_ONLY3 and ACTION0 at all three widths.

The unchanged existing helper passed the previously failed tag check, then found its own contextual fixture still spreads v5 situation into a declared v4 input. Strict validator rejects the extra field; this is test-fixture version mismatch rather than a UI exception. Log `/workspace/gp23-artifacts/ui-current-tag-final/current-gameplan.log`. Test-only correction requested from root; no further UI product edits.

## Final resolution of required follow-up

Root authorized one fixture-only edit in `scripts/browser_current_gameplan.py`: destructure the v5-only situation field out before explicitly constructing legacy v4 input, with an explanatory comment. Strict validator and all existing contextual coverage/name/tag assertions remain unchanged. Its SHA256 is `91776fa5cb323d3d803544b93a927109db311f7501674a611eca7ef5382c9489`.

Final existing current helper **PASS** desktop1440 and mobile390 at `/workspace/gp23-artifacts/ui-current-fixture-final/result.json`, covering current DOM/five actions/reset/period restore/jungle/stale flow, unsupported GENERAL_ONLY3/ACTION0 and contextual legacy case, with no JS errors. This resolves the two post-freeze findings above. Expanded new runner remains **PASS** at `/workspace/gp23-artifacts/gp23-ui-tag-final-browser`; its source was unchanged after that run. No further UI product code changed; only the authorized new assertion and existing fixture correction were made after freeze.

# Loading interactive flow v3 — 2026-10-17

Authority USER_INTERACTIVE_FRONTEND_STRATEGY_SELECTION. Extends loading-v1/context-v2;
Frozen DESIGN ACTION/DECISION boundaries remain. No provider calls, champion expansion,
new tactical approval, damage/win/risk scores or production R3 adapter.

## Intake audit

| Requirement | Fresh main/fa22713 state | Action |
|---|---|---|
| Manual10pick/shared analysis/summary | UI+engine implemented | KEEP |
| Context separation/six lane rows | UI+engine implemented | KEEP full table |
| Risk preference | Missing in input, engine and UI | ADD v2 input preference |
| Six-dimensional comparison | Legacy Python synthetic-only contract; no loading connection | REUSE vocabulary, do not enable gated synthetic production adapter |
| Future conditions | Existing separate directions6scene engine/UI; no loading decision connection | ADD bounded Lv2 future assumptions |
| Level selection | Engine six rows, UI full table only | CONNECT selected-row details |
| Basic/alternative comparison | Existing row alternatives as text, no selection | ADD supported action IDs/costs/requirements |
| Map step selection/zoom | Card→map implemented; map→card missing | ADAPT keyboard/touch bidirectional selection |
| Claim evidence | Evidence section supports facts; row has IDs but no direct why path | CONNECT selected row to exact relevant facts |
| Matchup optimal action/effects | Insufficient expert/realplay evidence | REMAIN DESIGN_HYPOTHESIS/N0 |

## Input / state boundaries

Legacy8-key loading input remains valid; it normalizes to schema_version
`lol-coach-loading-input-v2`, preferences:{risk:LOSS_LIMIT|BALANCED|OPPORTUNITY}; BALANCED
default. V2 requires these two extra fields, rejects invalid/extra fields. Preferences
are user choices, never game observations. PC sanitized draft uses default preference.

Pure UMD LoadingExploration.defaultState() => {milestone:LEVEL2,assumptions:{binding:UNKNOWN,
followup:UNKNOWN,exit_cover:UNKNOWN}}; evaluate(report,catalog,state) returns the exploration
from normalized report.input.preferences. No UI-selected plan or step enters game input.
The UI view state holds selected panel/step/previewPlan separately; recomputation updates
summary status, selected details, comparison and map atomically. Dirty pick input hides
results and clears exploration; no stale result masquerades as a new analysis.

All assumptions are future hypothetical, not observed. binding HIT/MISS/UNKNOWN;
followup READY/UNAVAILABLE/UNKNOWN includes W learned/available, installation/activation,
attack distance, resources and wave; exit_cover AVAILABLE/BROKEN/UNKNOWN includes ally
connection and ability to handle Nautilus/Kaisa response with an exit. No economy mandatory.
Only exact representative duo, assigned positions, Lv2, matching source patch and retained
required fact IDs support interactive action comparison. Other milestones still show their
existing row/conditions/alternatives/why, but no unreviewed map or risk-dependent new action.

## Candidate contract / selection

Each plan carries id,title,objective,steps[{number,text,action_id}],gain,costs,requirements,
opponent_response,abort,next_if_unknown,evidence_ids,feasibility,dimensions. Six dimensions
exactly survival_exposure/resources/growth/position_wave/time_objectives/options, qualitative
text + source IDs; no pairwise dominance claim and no scalar utility. Costs include missed
CS/pressure when waiting, not just attack exposure. Evidence sufficiency and feasibility
separate from user preference: tactical sufficiency CONDITIONAL or INSUFFICIENT, assessment
UNDETERMINED, hypothesis grade never raised by selecting a condition.

SHORT_FOLLOW is POSSIBLE only inside all three explicit positive assumptions and matching
patch/facts; otherwise UNKNOWN or IMPOSSIBLE. RECEIVE_WITH_LUX requires exit_cover AVAILABLE;
otherwise do not call that receiving line safe. PREPARE_WINDOW is an information/resource
preparation plan, not a trade or assured CS: reduces current resource target and compares
visible next receiving position without walking into unknown space.
LOSS_LIMIT prefers RECEIVE_WITH_LUX among eligible trade/resource alternatives. BALANCED
and OPPORTUNITY may prefer SHORT_FOLLOW when all gates pass; no claim it is objectively
optimal. If only one eligible plan, all preferences return same selection with a reason.
Feasibility/evidence gates precede preference. Unknown never becomes ready, missing patch/
facts never becomes supported, conditions cannot promote AUTO/USER status.

## Maps / why / rollback

Only exact representative Lv2 plans receive dedicated hypothetical allied Caitlyn/Lux
geometry, BLUE/RED reflected without unknown enemy portraits. Numbered actions and map
steps share selected state; SVG number markers are keyboard/touch controls, zoom mirrors
selection. All geometry is DESIGN_HYPOTHESIS illustration, not exact ranges/safe route.
Unsupported row/patch/duo shows explicit unsupported reason. Why shows source-supported
mechanics separately from tactical claim, assumptions, exceptions and queued counterexamples.
Raw quote/source metadata unchanged; L3 trace is separately expandable.

Impact: loading input normalization/report additive exploration and selection controls;
existing full summary/table/gameplan/fight/oldscenes/source and launcher remain. Reuse plain
JS, CSS, SVG and retained official assets, add no framework/network adapter. Validate legacy
input, positive/missing/impossible cases, one-condition action-ID transitions, semantic
preference invariance, stale input, keyboard/touch/map/zoom, source links and 390px overflow.
Rollback: revert additive exploration module/UI/integration/input v2 normalization and deploy
previous verified Pages096234e8; no original knowledge/ledger/source/history removal.

# GP23 core implementation handoff

Worktree: `/workspace/lol-coach-gp23`. Started at `8e67cce63a29decae9f64a21f7c387bf73824507`. Changes are uncommitted for root's central integration; no child agents, external writes, protected issue actions, source adoption, frozen350 changes or edits to original raw examples were performed.

## Changed and owned files

- `web_r4/loading-situation.js`: new pure 17-field typed situation boundary. Exports fields/defaultState/validate/effective/project. Strict PRE_GAME assumed/unknown and REVIEW historical observed/stale with source/time. No clock/TTL, current observation inference, API calls or tactic decisions.
- `web_r4/loading-engine.js`: exact input-v5 = v4 + situation; validates and retains normalized situation; Node/browser module dependency. V1–v4 strict fields and interpretation preserved.
- `web_r4/loading-planboard.js`: final v5 reconciliation inside existing resolver and existing scoped candidate helpers. One typed decision supplies top team/user responsibilities, each phase goal/threat/position/action/stop, five visible actions, independent prose, conditional details and max two decision tags. Existing delivery v1 and retained summary/coach wave consumers synchronize from that final decision. Old input versions never take this branch.
- `contracts/gameplan-situation-v1.md`: exact input/API/output/ownership/provenance/compatibility and unsupported-scope boundaries.
- `tests_pregame/test_gameplan_situation.py`: 13 production-path behavior tests.

Other agents own current UI routing/projection/browser, input adapter/server, examples/source seals, learning room and docs. Their changes were not staged, committed or overwritten by this task.

## Exact interface to UI/root/F runner

Input-v5 requires `situation = LoadingSituation.defaultState()` with fields constructed dynamically from `LoadingSituation.fields`. Unknown wrapper is `{status:'unknown',value:null,source:null,observed_at:null}`. Explicit UI scenario wrapper is `{status:'assumed',value:<enum>,source:'user-scenario',observed_at:null}`. Observed/stale require REVIEW + source + valid UTC timestamp and never supply a current effective value in v1.

Output is `report.coach.planboard.gp23`, schema `gameplan-2plus3-v1`:

- `top.teams` and `top.user`: id/label/title/paragraphs/tags, comparison on teams, explicit baseline_scope on user.
- `phases.lane|operations|fight`: id/label/decision_id/goal_id/goal/threats/position/action/stop/reason/prohibitions/transition/uncertainties/actions[5]/paragraphs/details/tags[<=2]/coverage/evidence_ids.
- `information`, `source_states`, `situation`, `mode`, `legacy_assumptions`, `live_coaching_enabled:false`.
- Fight: context/execution/effective_contribution/advantage:UNDETERMINED/probability:null and threat_priority/threat_candidates.
- Lane: feasible candidate diagnostics, existing resolver trace, costs and completed:false.

The action string is the phase headline. `board.delivery` remains gameplan-delivery-v1 and uses the same actions/headline/prose/details/tags. Current route can project gp23 preferentially; explicit old links retain old-version output. UI has been notified of all field and threat scope details.

## Reproduced defects corrected in v5

1. Missing patch no longer leaves active ACQUIRE_PUSH while claiming source review is required.
2. Unknown resources/wave/support cannot fall through legacy standard defaults into pressure actions/tags.
3. Unavailable follow-up revises headline/actions/tags together.
4. Low resources with allied-building wave does not invent an incoming wave or a feasible pull/freeze.
5. Nearby enemy jungle plus large incoming wave can compare trimming when manipulation is feasible; nearby jungle does not prohibit every clear. Declared achievable crash and reset compare with waiting cost, but no crash completion is claimed.
6. Historical/stale observations preserve metadata but cannot become current AWAY/safe/available/ETA claims.
7. Top tank goal can change from enemy carry disruption to allied carry protection with evidence, follow-up and carry risk. Unavailable follow-up, unknown required means or restricted terrain cannot unlock disruption.
8. Real contribution and arrival constraints replace nominal head-count assumptions; no numerical advantage or probability is generated.
9. DUEL prose no longer requires an unavailable outside ally merely because the role is MID; actual encounter participants remain explicit categorical inputs.
10. Named capability samples no longer claim current threat reach/priority: main priority is UNKNOWN, per-actor reach UNKNOWN, generic reach assumption separate. UI owner is presenting this unresolved statement visibly and samples with mechanisms in disclosure.
11. Unsupported phase coverage remains its previous source scope; selecting a role objective does not promote Ornn or arbitrary champion matchups into supported tactics.
12. Operations no longer repeats the same waiting-cost paragraph to fill space; blocked/spent own skill protection asks to confirm remaining means instead of counting the spent skill again.

## Verification evidence

- Initial TDD RED: `/workspace/gp23-artifacts/gp23-core-red.log`, 9 expected failures for missing typed situation boundary.
- First implementation run: `/workspace/gp23-artifacts/gp23-core-first-green-attempt.log`; eight tests passed and one safe-fallback prose regex was over-specific. That assertion was corrected to test typed decision/headline identity rather than incidental wording.
- Review RED: `/workspace/gp23-artifacts/gp23-core-review-red.log`, 3 expected failures for solo mismatch, missing unresolved-priority state and stale retained selection.
- Prose RED: `/workspace/gp23-artifacts/gp23-core-prose-red.log`, duplicate operation paragraph caught before correction.
- Final focused core GREEN: `/workspace/gp23-artifacts/gp23-core-green.log`, **13 tests passed**.
- Focused existing/core regression: `/workspace/gp23-artifacts/gp23-core-regression-final.log`, **100 tests passed** across situation, direction, backend, coaching content, loading strategy/wave/engagement/coach/presentation and formation. This run preceded the final tiny duplicate-prose/protection-wording correction; the current 13-test suite covers that correction. Root will perform consolidated final/full-suite verification on the frozen integrated source.
- Latest `node --check` on the three owned JS modules and owned-path `git diff --check`: exit 0.

Exact production probes and initial audit are `/workspace/gp23-artifacts/engine-audit-probes.cjs`, `engine-audit-probes.json`, `engine-audit.md`. Probe JSON retains raw old engine reports and is audit evidence, not the new five-case GP23 sample set.

## Coverage and remaining limitations

B input/output/provenance/old-consumer compatibility contracts are implemented in this scope. C wave choices and costs use explicit qualitative user assumptions; individual HP/mana/skill measurements, precise minion geometry and verified continuous freeze are unsupported. All old fields remain available as labeled legacy assumptions; they do not populate canonical unknowns.

D encounter context, categorical contribution/arrival, ADC attack-space objective and tank disruption/protection arbitration are implemented within factual kit/source scopes. **Per-actor threat ranking is intentionally incomplete**: the schema has a generic encounter-level reach field, no named actor contribution/geometry/timing. The report therefore explicitly states current priority unresolved rather than selecting an alphabetic enemy as primary. Candidate context/mechanisms are retained as unranked evidence, not a simulated ranking. Numeric effective counts and win/kill/pursuit probabilities remain unsupported. Generic non-covered roles remain GENERAL_ONLY.

Observed REVIEW evidence is historical and freshness-unverified; no source-specific freshness policy has been invented. A future current-observation path needs an explicit datum/source/clock/invalidation policy. This preserves the required boundary, but does not claim fresh-observed live coaching support.

All outputs remain conditional design hypotheses, TACTICAL_UNREVIEWED, real_coaching_n=0. Internal consistency tests do not measure gameplay effectiveness. The UI/current-priority disclosure and consolidated browser/full-suite/source-seal checks remain root integration responsibilities.

No new optional scope is planned. Resume with root's consolidated review; only concrete review/test defects should change these files before sealing.

## Scoped post-freeze compatibility correction

The existing current-gameplan browser guard exposed ACTION tags on Ornn/TOP GENERAL_ONLY phases. Core now emits only the coverage STATUS tag when phase coverage is not CONDITIONAL_PLAN (including GENERAL_ONLY and BASELINE_ONLY). Supported conditional phases retain the maximum-two final-decision tags. Delivery v1 copies the same scope-correct tags.

New behavioral test was captured RED in `gp23-core-scope-tags-red.log`, then the entire current core suite passed **14 tests** in `gp23-core-green.log`. Latest owned source syntax/diff checks pass. Code freeze was renewed with loading-planboard.js SHA256 `5f1be074de90b40f2e0e6f2dbff755ef8d62738897fb4aeabb76ec786a32fe28` and tests SHA256 `50fff1679dae180ac7ba0027e70d4d0ddf8c6d9deecfb07876e1955f85762cbd`. Root/UI rerun consolidated/browser checks and reseal evidence against these bytes.

# GP23 B/C/D independent core review — first pass

Read-only source review and five focused production-engine counterexamples, 2026-10-25. Repository HEAD observed: `a12330d7030c7b74dc748820b68e8b7841940148`; shared implementation was still changing. This is a pre-fix review, not final release approval. No repository files edited, no networking, no full-suite rerun. Review requirements: root `AGENTS.md`, `docs/gameplan-content/gameplan-2-plus-3-v1.md`, GP23 queue, v5 situation boundary, engine/planboard, presentation and threat formatter, `tests_pregame/test_gameplan_situation.py`. `contracts/gameplan-situation-v1.md` did not exist when inspected.

Reviewed source hashes: loading-situation.js `8e0528de93a2d6c6351ef95d2378bb8b9c4a828199b3ec773b09d1da23016a96`; loading-planboard.js `a4a8817b1d6c83d3409fc03d6164639def1f31aab76d3cd0ef02db485ac2fc59`; loading-coach-view.js `3bbdcab1a30c36eface6cec258513c1c42a52a916690458d959bf78583b29f84`; test_gameplan_situation.py `cec1fc31708b886fcf5c4e421d41172007ce3b40164244c1c7d7361488c5c977`.

## SPEC

**CHANGES REQUIRED at this snapshot.**

### CORE-P1-01: an unranked alphabetic capability sample appears as the major threat judgment

Requirements: GP23-23 and GP23-27; specification says threat candidates must consider reach/contribution/resources/terrain and present main threats without listing every opponent. Source: `loading-planboard.js` first-pass lines 997–1000 sorts ACCESS/ASSASSIN/PICK then champion ID and slices two. `loading-coach-view.js` lines 423–424 labels that array `주요 위협`; `plain()` lines 10–15 formats only name and reason, dropping candidate scope, mechanism (`means`) and reach.

Reproduction: production `E.analyze(input(), catalog).coach.planboard.gp23.phases.fight`, using the test PRELUDE's default ten picks (Ornn/Sejuani/Ahri/Caitlyn/Lux vs Fiora/LeeSin/Zed/Kaisa/Nautilus), all situation fields unknown. Actual candidates are `Fiora`, `Kaisa`, each `reach: UNKNOWN`, `scope: CAPABILITY_CANDIDATE_NOT_CURRENT_PRIORITY`. Visible text is nevertheless under `주요 위협`, with the same generic reason. The sole global `threat_reach` assumption cannot establish named per-actor reach; changing it attaches the same reach to both arbitrary samples. JSON honesty does not repair the rendered priority implication.

Fix criterion: main threat judgment explicitly states current priority unresolved unless actual supported inputs identify it; any bounded capability examples visibly say they are examples and show mechanisms plus per-actor uncertainty. No alphabetical ordering represented as tactical danger ranking, and no excluded sample represented as absent. Source/report/presentation/detail consumers agree. Add meaningful regression for the above unknown case and context changes. Engine and UI owners notified; root agreed scoped P1. Pending fix and fresh verification.

### CORE-P1-02: 1v1 execution is ready while its action requires an ally explicitly unavailable

Requirements: GP23-21, 27, 28 and same-decision action/tag consistency. First-pass source: `loading-planboard.js` lines 992–996 exempts DUEL from ally_followup, but lines 1024–1026 use the cooperative MID/JUNGLE action; common stop at line 1028 still makes lost allied followup a stop condition.

Reproduction using test PRELUDE: `input({...fightReady, combat_context:'DUEL', ally_followup:'UNAVAILABLE'}, 'MID')`. Actual: context DUEL, execution READY, goal CREATE_CONNECTED_WINDOW, tag `선택 가정에서 실행`; action `배운 수단이 닿고 아군도 함께 공격할 수 있는 대상에 기여한다...`; stop `아군 후속·보호가 끊기거나...진입과 추격을 멈추고...`. Input says allied followup cannot happen. The promised solo flow has no coherent ready action. This is a contract/coherence failure, not a claim about which duel is winnable.

Fix criterion: DUEL goals/position/action/stop reason about the user and actual encounter participants; external allied assistance must not be required after being exempted by the execution gate. Document whether contribution includes the user; avoid conflating absent drafted allies with encounter participants. Verify no chase/kill/advantage guarantee is added. Engine owner confirmed reproduction and is implementing context-specific prose. Pending fix and fresh verification.

### Scope requirements that remain PARTIAL unless separately implemented

- GP23-22: `ally_contribution`, `enemy_contribution`, arrival-order categories gate actions, and advantage stays UNDETERMINED/probability null. There are no actor-level effective counts or nominal headcount input. This safely avoids invented 3v2 advantage; it does not implement numeric effective fighters. Status must state qualitative contribution gating.
- GP23-23: global reach plus static capability examples cannot implement named present-threat priority. Narrow honest scope is acceptable for release once CORE-P1-01 is resolved; queue status should remain PARTIAL for actor-specific ranking.
- GP23-26: MID/JUNGLE primarily share CREATE_CONNECTED_WINDOW and SUPPORT ENABLE_ALLY. These are bounded role principles, not independently verified assassin/poke/protect objective selection for every composition.
- Missing situation contract file is integration work in progress. The rule ID `gameplan-situation-v1` is already emitted; final contract must describe assumptions-only execution, historical observed/stale values projected ineffective, qualitative contribution and unranked candidate limits.

## QUALITY

No additional P0 was found in this focused pass. This is not proof of no P0 elsewhere.

Source-supported positive findings:

- v5 is explicit and prior v1–4 inputs do not enter the new resolver. Strict input and situation exact-key boundaries are retained.
- Only `assumed` values are executable. `observed`/`stale` require REVIEW provenance/time and project to ineffective historical data. `live_coaching_enabled:false`, `TACTICAL_UNREVIEWED`, N=0 prevent these hypothetical plans being advertised as verified current observations or tactical effectiveness.
- Feasibility candidates prevent a forced freeze. Resources LOW, access DENIED or no allied followup precede enemy-jungle distance; nearby jungle plus incoming large wave can trim rather than blindly accumulate. Unknown jungle is not blanket push permission or blanket retreat.
- Tank disruption requires usable control evidence, ready combat, available followup, covered allied carry and reachable enemy carry; threatened allied carry changes goal to protection. Marksman actions preserve attack space and protection distance. No nominal count is used to assert advantage.
- Same final phase supplies headline/actions/paragraphs/tags; five action objects are retained. The known stale old wave/diagram/summary consumers were reported by the engine owner and are not signed off here.

Focused extra outputs inspected without rerunning the reported test suites:

1. All unknown: CHECK_WAVE; fight UNKNOWN; no invented probability/advantage.
2. DUEL with unavailable allied followup: CORE-P1-02 reproduced.
3. DUEL plus unavailable contribution: BLOCKED; semantics need documented encounter participants (does not by itself establish a bug).
4. Incoming wave + RECALL + crash READY + losing income/opportunity available: TRIM_RECEIVE, not impossible CRASH. Correct feasibility-first decision, but first-pass action/prose did not carry the recall/waiting-cost explanation; engine owner already adding that link.
5. SUPPORT building wave: generic aid to allied wave choice, no own-CS instruction; action tag SLOW_PUSH but prose deliberately conditions on ally's requested wave direction.

The old `b.lane.can_push/should_push` still contained the standard Caitlyn/Lux push advantage in the all-unknown v5 probe; owner is re-syncing legacy consumers. Do not claim this review verified the later repair.

### Review decisions

Add: explicit current threat uncertainty; actual DUEL user action; permanent scope contract and selective semantic regressions.
Remove: implication that an arbitrary capability sample is current priority; cooperative requirements from solo-ready text.
Fix: the two P1s, stale old-consumer synchronization and recall/cost explanation already owned by engine/UI workers.
Do not do now: invent precise effective counts, per-enemy cooldowns/reach, ETA, combat odds, or tactical effectiveness evidence.

Performance evaluation remains **UNMEASURED, real coaching N=0**. This review evaluates observable contracts, coherence and boundedness. Passing a unit/browser regression would establish that the implemented contract holds for those cases, not real-match tactical accuracy.

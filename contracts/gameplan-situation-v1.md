# Gameplan 2+3 situation contract v1

Implementation amendment for GP23; user-approved direction is `docs/gameplan-content/gameplan-2-plus-3-v1.md`. Field choices below are implementation judgments, not tactical approval. Frozen350, original source quotations, original raw examples, user decision issues and approval counts remain unchanged. Real-game effectiveness remains UNMEASURED, N=0.

## Version and input boundary

`lol-coach-loading-input-v5` contains exactly the v4 fields plus required `situation`. Legacy eight-field input and v2/v3/v4 retain their existing exact key sets, defaults, output and interpretation; adding a v5 field to those versions is rejected. There is no automatic migration of saved historical inputs or `pregame.plan.v1/v2/v3` API archives.

`LoadingSituation.defaultState(mode='PRE_GAME')` returns a fresh, serializable object:

```json
{
  "schema_version": "lol-coach-situation-v1",
  "mode": "PRE_GAME",
  "fields": {
    "enemy_jungle": {"status":"unknown","value":null,"source":null,"observed_at":null}
  }
}
```

The example shows one field for brevity; all 17 fields listed below are required. Every field uses the same **exact** four keys. Top-level situation uses exactly schema_version/mode/fields. No implicit current-state defaults or extra fields are allowed.

| Field | Values other than null | Meaning and limits |
|---|---|---|
| ally_jungle, enemy_jungle | NEAR, AWAY | Selected relative region class. No inferred precise location, path, ETA or safety. |
| wave_direction | EVEN, BUILDING, INCOMING, UNDER_TOWER, RETURNING | Current comparison flow; BUILDING means allied residual wave advances. Low resources do not create INCOMING. |
| wave_size | NORMAL, LARGE | Qualitative pressure, not invented minion counts or damage. |
| wave_access | READY, DENIED | Ability to manipulate while preserving processing, response and escape budget. This is a user-selected aggregate, not inferred HP/mana/skill measurements. |
| wave_crash | READY, BLOCKED | Separate reach-to-tower/remaining-enemy-clear/additional-wave feasibility. READY does not mark crash completed. |
| resources | SUFFICIENT, LOW | Selected combined processing/fighting/response budget; individual health, mana and skill values remain unspecified. |
| ally_followup | AVAILABLE, UNAVAILABLE | Same-target follow-up in the comparison. It is not inferred from drafted presence. |
| combat_context | DUEL, DUO, GANK, COUNTERGANK, RIVER_JUNGLE, PICK_CHASE, OBJECTIVE, TEAMFIGHT | Encounter context, separate from loading milestone. |
| ally_contribution, enemy_contribution | READY, LIMITED, UNAVAILABLE | Actual participants' attack/protection contribution in this encounter, including the user on their side. Unrelated drafted allies are not counted. No numeric superiority or population estimate is derived. |
| arrival_order | ALLY_FIRST, EVEN, ENEMY_FIRST | Coarse selected order, no travel times. |
| threat_reach | REACHABLE, UNREACHABLE | An encounter-level threat constraint. It does **not** assign reach/current importance to a named champion. |
| ally_carry_risk | THREATENED, COVERED | Need to protect allied carry versus protection being connected in this scenario. |
| enemy_carry_access | DISRUPTABLE, UNREACHABLE | Whether own control can interrupt enemy carry attacks while connected. Not a kill/dive guarantee. |
| combat_space | OPEN, RESTRICTED | Chosen action and retreat feasibility; not a generated geometry/path simulation. |
| key_skill | AVAILABLE, SPENT | Own action's required learned/available means. Does not assert all enemy skills are available or all control is gone. |

`LoadingSituation.fields` exports `{key,label,options}` descriptors for the same enum map; clients should construct fields from this API instead of duplicating defaults. `validate(raw)` returns a detached validated copy. `effective(info)` operates on normalized data; it supplies a value only for an explicit assumed field. `project(raw)` retains source states and exposes effective values plus the read-only interpretation label.

## Information, source and freshness

- `unknown`: value/source/observed_at are all null. Unknown is independent for each field.
- `assumed`: value is a listed enum, source is an explicit nonempty user-input identifier (UI uses `user-scenario`), observed_at is null. This is a selected hypothetical condition, never an observation.
- `observed` and `stale`: accepted only in REVIEW, with a listed value, nonempty source identifier and valid UTC ISO observation timestamp. PRE_GAME rejects them. Observation metadata is retained verbatim; a syntactically valid source identifier does not verify the source's truth.
- REVIEW means historical review and never enables live coaching. Both observed and stale records have UNVERIFIED_HISTORICAL freshness and **no effective current value** in v1. A user can explicitly choose an assumed replay scenario to compare behavior, without converting the retained record into current observation.

No machine clock, generic age threshold or fixed freshness seconds is introduced. The composition capture's transport-liveness max_age is not gameplay freshness. A future source-specific policy must identify datum, clock, source, applicability and invalidation before using observations as current. Unknown/stale/old sightings never grant an empty region, safe push, available skill or real arrival.

## One planboard decision path

The situation module performs validation/provenance projection only. `LoadingStrategy.analyze()` validates v5 and carries normalized situation into the existing report. `LoadingCoach.evaluate()` still calls `LoadingPlanboard.evaluate()`. The v5 final reconciliation inside that resolver uses the existing scoped candidate/condition helpers and official catalogue evidence; there is no provider call or separate tactic engine.

Canonical v5 fields own overlapping execution conditions even when unknown. Old scenario/planning resource/wave/enemy-jungle/follow-up/wave-size overrides cannot fill canonical unknowns. They remain inspectable in `gp23.legacy_assumptions` as legacy comparison assumptions. Explicit existing planning goal/income/opportunity retain their declared-purpose and waiting-cost meaning, without becoming observations. Legacy enemy-key metrics remain a separately scoped comparison; own key_skill does not describe enemy cooldowns.

Wave choice evaluates feasibility before purpose. Candidate diagnostics include receive-limited, maintain, slow/fast push, crash, trim incoming, tower receipt, returning wave and check-information; sustained freeze is explicitly unsupported. Low resources or denied manipulation do not create a wave that can be pulled. Nearby enemy jungle does not prohibit every clear: a large incoming wave may need trimming when feasible, and a declared achievable crash can be compared with waiting/dive/reset cost. Crash completion remains false until a separate supported observation contract exists. Trade length, wave processing and response resources are not double-counted.

Combat evaluates context, actual contribution, arrival order, own required means, resources, generic threat reach and terrain constraints independently of nominal head count. A top tank's enemy-carry-disruption goal requires own official control-mechanism evidence, connected follow-up, executable contribution and covered allied carry. A threatened allied carry changes the objective to protection. A damage carry links survival to attack space/time rather than blanket fight refusal. DUEL prose uses self/opponent contribution, not an unavailable external ally. No numerical probability, winner or pursuit permission is inferred.

Current per-actor threat priority remains **UNKNOWN**: generic threat_reach cannot rank named enemies. `threat_priority` gives a visible unresolved-current-priority label, reason and generic scenario effect. At most two contextual functional capability candidates are retained separately with source mechanisms; their per-actor reach remains UNKNOWN and display order is not current danger rank. Candidate omissions do not establish absence. DUEL uses designated comparison opponent, DUO lane candidates, gank/countergank lane and jungle candidates. Broader actual target/geometry ranking is unsupported and is a remaining extension, not silently simulated.

## Additive output and consumer compatibility

The report remains `lol-coach-loading-report-v3`. V5 adds `report.coach.planboard.gp23`:

```text
gp23.schema_version = gameplan-2plus3-v1
gp23.mode, situation, information, source_states, legacy_assumptions
gp23.live_coaching_enabled = false
gp23.top.teams = {id, label, title, paragraphs, comparison, tags}
gp23.top.user  = {id, label, title, paragraphs, baseline_scope, tags}
gp23.phases.{lane,operations,fight} = {
  id,label,decision_id,goal_id,goal,threats,position,action,stop,reason,
  prohibitions,transition,uncertainties,actions,paragraphs,details,tags,
  coverage,evidence_ids,observation:false,review_state:TACTICAL_UNREVIEWED
}
```

The user top card is explicitly `COMPOSITION_DEFAULT_NOT_CURRENT_ACTION`. Team comparison and user baseline have separate responsibilities. Jungle labels are 초반 정글 / 중반 운영. Fight label is 교전·한타. Each phase has exactly five visible actions, independent visible explanatory prose, conditional details and at most two final-decision tags. Goal/action/conditions and switches remain visible, not hidden in source metadata.

Fight also exposes context/execution/effective_contribution/threat_priority/threat_candidates/advantage/probability; advantage is UNDETERMINED and probability null. Lane adds feasibility candidates, comparison trace, costs, completed:false. Coverage preserves the previous same-phase source scope; selecting a generic role goal does not promote unsupported matchups, official facts or taxonomy labels into validated tactics.

`gameplan-delivery-v1` keeps its required phase fields and version; its v5 headline/actions/paragraphs/details/tags are projected from the same final GP23 decisions. Existing board summary, wave selection, fight/operations action fields and coach selection are synchronized for retained consumers. V1–v4 never enter this reconciliation, so their existing schemas and outputs remain unchanged. The older top-level report.wave/engagement/exchange models remain explicitly legacy scoped comparison models and are not the v5 canonical decision.

UI performs serialization, source-state display, reset and projection only; it does not choose tactics, targets or tags. Reset discards assumptions and historical metadata and re-runs from a fresh unknown state. Restoring an explicit legacy link retains its original input version. New evidence captures include exact input, report, versions/SHA, source scope and output without manually edited prose.

## Verification and release limits

Behavioral tests cover strict status/source/time handling, no live observation promotion, stale rejection as current, v1–v4 compatibility, unknown overwrite prevention, feasible wave actions, near-jungle large-wave/away-jungle low-resource counterexamples, reset/arrival/goal cost, jungle translation, tank disruption/protection, unknown skills, restricted terrain, unavailable contributors, aimless pursuit boundaries, source coverage and headline/action/tag consistency. Browser and evidence runner validate the actual production path separately.

No new tactical approval, quantified coaching accuracy or gameplay effect follows from passing those checks. Current threat priority, numerical effective head counts, individual actor timing, exact minion manipulation and fresh observed-state execution remain unsupported. Protected source/approval artifacts must remain unchanged.

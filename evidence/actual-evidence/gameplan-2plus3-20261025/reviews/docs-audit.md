# GP23 documentation and requirement audit

Audit basis: `/workspace/lol-coach-gp23`, HEAD `8e67cce63a29decae9f64a21f7c387bf73824507`, 2026-10-25. Read-only repository audit; this report alone adds no product implementation, deployment, CI success, tactical approval, or real-game evidence. Only this artifact was written. The parent implementation may supersede the conservative baseline below with fresh evidence.

## Authority and approved scope

Read: root `AGENTS.md`; both GP23 specification/queue documents; all six root architecture/source/decision/change/dependency/release documents; `contracts/gameplan-presentation-v1.md`; the actual v2.0 body of `contracts/information-architecture-v1.md` (filename remains v1); existing feature matrix and source/input maintenance documents.

**Approved direction:** upper cards mean 전체 조합 방향 / 사용자 기본 방향; lower cards mean 라인전 / 운영 / 교전·한타. Preserve the comparison, exactly five actions per phase, always-visible coaching/key execution and transition sentences, retained details/maps/source routes, and disclosure only for additional detail. Upper/lower repeated filler does not satisfy this requirement. Jungle translates lane/operations to early-jungle/midgame operations. Fight includes 1v1, 2v2, gank/countergank, river/jungle encounters, picks/chases, objectives and 5v5. Sequence: own objective → threats → relevant actors/position → action → change/stop conditions. ADC must secure attack space/time against reachable threats. Top tank chooses enemy carry disruption or ally protection by circumstances. Short violet tags aid reading but do not replace prose.

**Implementation proposals, not blanket user approval:** extending a shared judgment contract, exact schema/field names and algorithms, four serialized information states, maximum two tags/card, tag prioritization, and exact responsive lengths/contrast thresholds. The spec adopts these as reasonable implementation defaults subject to verification; D05 explicitly labels them proposals. Choosing them as reversible engineering decisions requires a rationale/compatibility note, not renewed approval of the already-approved 2+3 direction.

**Unresolved until evidence:** data-type-specific freshness thresholds; source/channel authorization and current service readiness; observed tactical-state acquisition; real travel ETA, enemy skill availability, numeric success likelihood; backward compatibility of any new output field; supported role/champion/context coverage; actual rendered accessibility; five raw examples and paired condition comparisons; live-game effect. No global seconds value is justified for all tactical facts.

**Protection:** no writes/comments/reactions/closure on registered `[지식 검토]` decisions. Preserve original 350 candidates, frozen contracts and human decision provenance. Official Korean source validation supplies reference facts, not USER or tactical approval. Actual user approvals remain zero without actual user decisions. No auto-promotion of four reference profiles or searchable champions to tactical support.

## Existing 160-row mapping

The canonical IA v2.0 contains 160 total rows, 48 in gameplan, and **37 in 3.2–3.7**. Preserve all numbers and hierarchy. The current feature matrix marks each of those 37 rows `status=INTEGRATED`, `coverage=PARTIAL`, `overall_score=0.5`, `frontend_score=0.5`, `full_feature_acceptance=false`; INTEGRATED is scoped legacy code, not GP23 acceptance. No matrix score increase follows from a mapping/doc change.

| Existing IA IDs | GP23 responsibility | Queue connection |
|---|---|---|
| 3.2.1, 3.2.1.1 | Retain both-team comparison and stable team perspective when changing own champion | 04, 11, 29, 34 |
| 3.2.2, 3.2.2.1 | Whole-composition direction, primary strategy, supporting tools and enemy constraints | 10–12, 29 |
| 3.2.3, 3.2.3.1 | User baseline/role, full sentences and visible action/reason/stop/change | 10–12, 18, 24–27, 29 |
| 3.2.4 | Three phase cards, five actions and independent coaching in each | 11–12, 30 |
| 3.2.5 | Team transition and supporting comparison details | 18, 27, 29, 34 |
| 3.2.6 | Distinguish champion baseline, composition changes and situation/assumption plan | 10–12, 18, 29, 32 |
| 3.3.1, 3.3.1.1 | Lane purpose/five actions/coaching; bottom 2v2 and own-role wording | 12, 16, 19, 30 |
| 3.3.2 | Scoped level/skill/item transitions; no winrate-to-combat-strength conversion | 15–18 |
| 3.3.3 | Feasible wave maintenance/push/clear/return, CS/XP loss | 13–18, 20 |
| 3.3.4 | Trade length, sustain/resources and wave cost | 15–16, 20 |
| 3.3.5, 3.3.5.1 | Both sides' aims, punish windows, distance/resources/followup, real skill names/keys | 15–16, 20 |
| 3.3.6 | Both jungles, recall, recovery and switching when constraints fail | 13, 15, 17–18, 20 |
| 3.3.7 | Own-jungle early route/gank/countergank/support, not own-laner instructions | 12, 19–20 |
| 3.4.1 | Operations objective/five actions/coaching | 17–18, 30 |
| 3.4.2 | Side/main-group assignments, real contribution and arrival order | 17, 22, 26 |
| 3.4.3 | Convert pressure/fight to tower/vision/objective gains | 17, 21, 27 |
| 3.4.4 | Wave/recall/vision/arrival preparation before objectives | 17, 21–22 |
| 3.4.5 | Costs and alternatives when joining/protection/wave conditions fail | 17–18, 25, 27 |
| 3.5.1, 3.5.1.1 | Fight purpose/five actions/coaching; separate operations and fight roles | 21, 24–27, 30 |
| 3.5.2 | Both sides' fight starts, access and protection; effective participation | 21–23, 25–26 |
| 3.5.3 | Ranked reachable threats, ADC space/time, tank disruption/protection | 23–26, 28 |
| 3.5.4 | Position/connectivity/terrain/map examples under scoped support | 21–23, 27–28 |
| 3.5.5 | Re-evaluate/exit/change objectives when attack/protection/followup fails | 24–28 |
| 3.6.1 | Baseline versus manual assumptions, refresh all dependent outputs | 10, 13, 18, 32, 37 |
| 3.6.2 | Risk preference cannot modify objective growth/matchup scores | 12, 32, 40 |
| 3.6.3 | Benefit, failed-action cost and waiting cost; necessity ≠ feasibility | 15–17, 22, 28 |
| 3.6.4 | Reset all summaries/prose/tags/detail to same baseline | 12, 32, 41 |
| 3.7.1 | Inline concepts explaining the selected plan | 27, 30, 34 |
| 3.7.2 | Existing context-linked maps/formation/scenes | 11, 27, 30, 41 |
| 3.7.3 | Source, patch, applicability, uncertainty and exceptions | 08, 10–12, 27, 36 |
| 3.7.4 | Preserve champion/opponent/topic in learning links | 11, 30, 41 |

Fight scope clarifies existing 3.5 rather than adding a top-level feature. Input prerequisites stay in 3.1 and champion-stat power-graph requirements stay in 2.3; neither should be renumbered into GP23.

## Sources and freshness: confirmed local evidence

| Source | Concrete retained evidence | Constraint / remaining gap |
|---|---|---|
| Official champion facts | `data/official_catalog/current.json` → source_patch 16.20.1, manifest SHA e61307d1acf1f8b27e66dd144b4136384dda35451a22e932a307e06c8885c406; version manifest `collected_at=2026-10-15T10:19:35.604285+00:00`; manifest stores Korean roster/per-champion URL+SHA | Stored version only. No remote freshness check performed by this audit. Explicitly distinguish patch 16.20 from source version 16.20.1. |
| Official items | `data/official_items/current.json` → version 16.20.1, manifest SHA d7b89641deccbf91e076386a3bc60a4065e4edce35293fc65238d5686dd738ee; retained manifest `retrieved_at=2026-10-15T10:59:54.562761+00:00` | 870 catalog items is source inventory, not 870 tactical recommendations. |
| Canonical URLs | `https://ddragon.leagueoflegends.com/api/versions.json`; `/cdn/16.20.1/data/ko_KR/champion.json`; `/cdn/16.20.1/data/ko_KR/champion/{Champion}.json`; `/cdn/16.20.1/data/ko_KR/item.json` | Inspect exact local manifest source hashes; don't invent license/permission. This audit did not re-fetch URLs or independently establish current licensing. |
| Static refresh implementation | `scripts/update_official_catalog.py` delegates to `coach_v1.official_catalog.refresh_if_due`, default `max_age_seconds=86400`, force flag; bounded official URLs, no redirects, validation/publication/fallback | 86400 is refresh eligibility, not proof of an operating daily scheduler or tactical observation freshness. Frozen official_reference archive is preserved. |
| Bound authored baselines | `web_r4/loading-direction-profiles.js` schema gameplan-direction-profiles-v1, data version 2, patch 16.20.1; Caitlyn/Ezreal BOTTOM, Fiora TOP, Graves JUNGLE; `review_state=TACTICAL_UNREVIEWED` | Source binding checks excerpt/hash; not tactical validity, current patch freshness, matchup/composition indexing, or USER review. All other profiles/roles must retain explicit missing/unsupported statuses. |
| LCU/manual composition boundary | `coach_v1/gameplan_input.py` supports only MANUAL/LCU_CHAMP_SELECT, eight legacy fields, privacy-filtered projection, detached structures; `live_coaching_enabled=False` | Default 2 seconds is transport liveness only. Never reuse for jungle observation age. No actual jungle location/skills/ETA are acquired here. Manual captures have a composition timestamp, not verified tactical observation provenance. |
| LCU current integration docs | `docs/gameplan-content/input-integration-v1.md` records missing trusted session/self linkage, side, finality, observation/freshness verification, Linux host inability to validate Windows client | Existing `/dev/v1/game-info` display gate remains closed; no implicit live permission. Do not copy historical Windows blocker as a newly executed environment result. |
| Riot scope/policy references | Input doc cites `https://developer.riotgames.com/docs/lol` and `https://developer.riotgames.com/policies/general` (checked in historical document on 2026-10-24) | Existing document says LCU unsupported for third-party apps and application endpoint/use disclosure. Historical doc is not product audit evidence; no permission/current endpoint scope inferred. |
| Experts/user decisions | AGENTS and source-maintenance docs require original URL/time/context, preserved human decision provenance | No new expert source, human tactical approval, real-game observation or fresh external source was acquired. |

Four tactical information labels must preserve meaning if adopted: `unknown` has no observation; `assumed` is explicitly user-selected hypothetical context; `observed` needs a credible source and observation time; `stale` must not be rendered as current. Snapshot IDs are caller scope identity, not wall-clock freshness (`loading-planboard.js` comment and contract). A fake observed state is P0. Absent data must remain missing, not be replaced with confident defaults. Loading screen cannot claim hidden live enemy knowledge.

## Documentation changes the implementer should make

| File | Concrete gap / required bounded change |
|---|---|
| ARCHITECTURE.md | Presently a 15-line entrypoint scaffold. Replace GP23-02 future tracing with confirmed input→normalizer→evaluation/judgment→delivery→view call graph and exact module/function anchors. Mark server/offline and manual/LCU boundaries. Identify duplicate policy candidates; do not assert removal without code evidence. |
| SOURCE_REGISTRY.md | Presently category policy, no concrete source URL/hash/last-success table. Add the retained sources above plus actual adapter boundaries and confirmed refresh trigger. Distinguish archive acquisition time, refresh check time, transport liveness, tactical validity and assumed state. Permission/license unknown stays unknown. |
| DECISION_LOG.md | Keep D01–D06 and authority intact. Add engineering decision IDs with rationale, rejected alternatives, affected IA IDs, compatibility and checks. Do not silently convert D05 into user approval. |
| CHANGELOG.md | Existing entry is documentation-only. New entry must separate engine/presentation/schema changes, unchanged versus changed versions, new test/evidence SHA, deployment status and live-game status. |
| DEPENDENCY_MAP.md | Existing group map is useful but GP23-02 module tracing is missing. Add exact contract/adapter/engine/tag/view/test/export dependencies and patch/profile impact scope. Preserve all existing IA IDs. |
| RELEASE_CHECKLIST.md | Keep distinct design, code/CI, browser, raw examples, real-game and deployment receipts. Check boxes only with task-specific evidence; state UNMEASURED N=0 for unplayed games, and BLOCKED with cause when deployment cannot run. |
| contracts/gameplan-presentation-v1.md | Historical presentation contract still speaks of three cards; reconcile with the approved 2+3 layout additively while preserving five-action and retained detail/map/source/legacy routes. Explicitly choose old-consumer compatibility. Existing additive delivery/snapshot versions must not be casually bumped. |
| contracts/information-architecture-v1.md | Body already v2.0 and contains 2+3 supplement. No renumbering, row growth, or rewrite of historical evidence. Existing 3.5 heading can retain its ID with clear fight scope. |
| docs/gameplan-content/gameplan-2-plus-3-status.md | Missing at audit start. Add 44 task rows with per-dimension evidence, dependency, decisions/counterexamples, exact commands/results, risk/next work. Keep previous queue44 separate. |
| frontend-v2-feature-matrix.json / management exports | Preserve baseline 160-row denominator and 0/0.5/1 scoped acceptance policy. Add fresh GP23 receipts only to evaluated scopes. Historic integrated UI status must not become full GP23/tactical acceptance. |

## Counterexample review to carry into implementation

| Problem | Requirement/proposal | Counterexamples | Severity / decision |
|---|---|---|---|
| Information provenance | No fabricated current observations; four-state serialization is proposal | Old enemy jungle sighting presented as current; manual far-jungle setting presented as observed | P0; preserve source/time/state and invalidate dependent outputs |
| Wave decision | Feasible conditional actions and costs | Enemy jungle nearby + large incoming dive wave still requires trimming/receiving; enemy jungle far + low health/losing lane still cannot push | P1; test feasibility before simplistic jungle-location policy |
| Combat contribution | Evaluate available contribution/order, not nominal numbers | 3v2 with two allies unable to join; unknown key skill cooldown rendered as certainly absent | P1/P0 respectively; unknown stays unknown and no fabricated numerical superiority |
| Tank objective | Conditional disruption versus protection | Deep engage with no allied followup; tank abandons threatened carry | P1; require followup/protection and explicit abort condition |
| Plan visibility/coherence | Core actions always visible, tags derived from final judgment | Upper says push and lower says pull; stale tag persists after reset while prose changes | P1; common result and atomic regeneration/reset |
| Coverage/approval | Reference-only is not tactical proof | 173 searchable champions reported as tactical coverage; profile-binding hash reported as human approval | P0; separate inventories, binding integrity, review and game effect |

Each group needs at least one stale/missing-info and one conflicting-objective counterexample. Record add/remove/fix/defer decisions without manufacturing changes. P0/P1 must block affected release; independent work continues.

## Conservative 44-item baseline from this documentation audit

These statuses describe only what this audit can substantiate at the original HEAD, not the parent's subsequent code work. DONE is scoped audit acceptance for requirements/mapping, not product release. PARTIAL means reusable documentation exists but required implementation/verification is unproven. Code, CI, browser, deployment all remain **NOT_RUN in this audit**; game effect remains **UNMEASURED, N=0**. No task is marked DONE by inheriting an old release.

| ID | Suggested baseline | Evidence / next acceptance |
|---|---|---|
| GP23-01 | PARTIAL | HEAD confirmed; historical deployment receipt exists, current live SHA/remote latest main not checked here |
| GP23-02 | TODO | Entry modules named only; parent must trace real call graph |
| GP23-03 | DONE | Approved/proposed/unknown split documented above; preserve this distinction through implementation |
| GP23-04 | DONE | 37 existing IDs in 3.2–3.7 explicitly mapped above, total 160 preserved |
| GP23-05 | TODO | Need captured engine input/output originals for missing/duplicate/contradictory content |
| GP23-06 | PARTIAL | Initial counterexamples/severities above; parent must bind actual outputs and resolve P0/P1 |
| GP23-07 | PARTIAL | Root architecture scaffold exists; concrete runtime graph remains |
| GP23-08 | PARTIAL | Retained source URLs/versions/hashes/times and freshness boundaries audited; root registry not yet amended |
| GP23-09 | PARTIAL | Six root docs align on unverified status; new decision/compatibility/test/release receipts absent |
| GP23-10 | TODO | Four-state design proposal exists, final serialized/validated tactical schema not demonstrated |
| GP23-11 | PARTIAL | Requirements and retained v1 presentation contract known; additive 2+3 compatibility choice remains |
| GP23-12 | TODO | New partial/unsupported/jungle/reset contract regression not run |
| GP23-13 | TODO | No audited proof of both-jungle information state/provenance/time handling |
| GP23-14 | TODO | Need feasible wave model and impossible-freeze counterexample |
| GP23-15 | TODO | Need resource/skill/pressure/followup priority in common result |
| GP23-16 | TODO | Need trade-wave cost linkage and agreement checks |
| GP23-17 | PARTIAL | Prior backend doc describes qualitative waiting effects; new recall/objective/arrival integration unverified |
| GP23-18 | TODO | Need baseline→conditional action/reason/tag atomic update |
| GP23-19 | PARTIAL | Graves authored jungle reference exists; new own-jungle role translation unverified |
| GP23-20 | TODO | New C counterexample regression not run |
| GP23-21 | TODO | Fight contexts approved, context-model implementation unverified |
| GP23-22 | TODO | Effective participants/arrival order unverified |
| GP23-23 | TODO | Reachability/contribution/terrain/uncertainty threat ordering unverified |
| GP23-24 | PARTIAL | Existing two ADC profile prose describes space/attack continuity; new threat/stop behavior unverified |
| GP23-25 | TODO | Top tank disruption/protection transition and counterexamples unverified |
| GP23-26 | TODO | Context-dependent other-role objectives unverified |
| GP23-27 | TODO | Five-part fight output contract unverified |
| GP23-28 | TODO | New D counterexample regression not run |
| GP23-29 | TODO | New upper-card responsibility separation not browser-verified |
| GP23-30 | PARTIAL | Legacy five-action delivery exists; new 2+3 lower-card/key-visibility preservation unverified |
| GP23-31 | PARTIAL | Existing delivery tag source-path projection exists; final common judgment/max-two/contradiction checks unverified |
| GP23-32 | TODO | New condition/reset stale text/tag/observation removal unverified |
| GP23-33 | TODO | No new desktop/390/320/200%/keyboard receipts |
| GP23-34 | TODO | No new E actual-screen critical review |
| GP23-35 | TODO | Five seeded role-balanced 10-pick inputs not generated by this audit |
| GP23-36 | TODO | No new engine raw input/output/prose/SHA/coverage bundle |
| GP23-37 | TODO | No fresh one-variable condition-change pairs |
| GP23-38 | TODO | No fresh six-axis internal scoring; game efficacy remains unmeasured |
| GP23-39 | TODO | No evidence-based F disposition yet |
| GP23-40 | TODO | No new GP23 tests/CI run; historical 906-pass receipt cannot transfer |
| GP23-41 | TODO | No new actual-browser full flow; historical screenshots cannot transfer |
| GP23-42 | TODO | Need concrete evaluation plan; execution currently UNMEASURED N=0, independent handoff permitted |
| GP23-43 | TODO | No new release review/deploy attempt; use BLOCKED only after identifying actual permission/environment/check failure |
| GP23-44 | TODO | No new GitHub/Notion/admin/graph synchronization; mutation needs authorized parent workflow |

Baseline counts: 2 DONE, 11 PARTIAL, 31 TODO, 0 BLOCKED, 0 DEFERRED, 0 IN_PROGRESS. These are conservative documentation-audit labels; parent must recompute from its final evidence rather than copy them as final GP23 totals.

## Reproduction and evidence boundary

Read commands used: `git rev-parse HEAD`; `cat AGENTS.md` and specified docs/contracts; `sed` of IA body between gameplan and in-game headings; Python JSON reads of feature matrix/current pointers/manifests/release-info; `rg` of normalizer/source/compiler/profile files. No test command, external fetch, deployment, source refresh, human approval import, GitHub/Notion write, or repository modification was performed. An attempted search for nonexistent `web_r4/gameplan-contract.js` returned a missing-file message and is not evidence of a runtime failure.

Historical receipt `evidence/actual-evidence/frontend-v2-20261025/release-info.json` binds main `ac48506c8f6493778d3fcdf675041d66f89c5390`, artifact `b0ec3cb8e15f0fa4cc6aa0454897317c23e979c9`, pages run 40177555880 and live verification 2026-10-25T08:42:22Z. It is neither this HEAD's deployment nor GP23 correctness evidence. Preserve it as historical scope only.

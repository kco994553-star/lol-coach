# Information architecture v1 — USER2026-10-18

## Purpose and boundary

Rearrange current features into five responsibilities, using the existing shared shell,
engine and source registry. No framework/backend migration, new match/video collection,
fake records, unvalidated recommendations or live coaching authorization. Inherit main
c446862/public5bbcf7c and prior completed evidence. AUTO30/HOLD20/USER0/advice7/Frozen350,
source originals, holds/failures, official skill-owner/name(key), Windows/manual preserved.
N0/human30secUNMEASURED/WindowsBLOCKED_EXTERNAL unchanged.

## Fresh implementation map (before changes)

| Existing feature | Current location | New location | Data | Actual implementation | Change |
|---|---|---|---|---|---|
| Riot ID/region search | index (dashboard.html) | 전적 검색 | account-profile-v1, private POST lookup | PC authenticated path; static explicitly unavailable | KEEP; primary search |
| Personal dashboard/recent/champions | index below hero | 전적 검색 dashboard view | same account response/statistical window | actual records only; no public backend | ADAPT route view |
| Verified LCK soloqueue reference | index pro card | 전적 검색/pro reference | pro-dashboard-v1, queue420, verified registry | existing projection and refresh | KEEP; no duplicate collection |
| Review entry | small dashboard card | 경기 복기 | selected safe recent record, optional private postgame | no public raw match/timeline connection | ADAPT safe record selection; separate analysis status |
| Manual10pick/role/line opponent | loading.html | 게임플랜 input | loading-input-v4 | works without account | KEEP |
| Line recommendations/bans/personal mastery ranking | absent (old draft is manual journal) | 게임플랜 optional recommendation stage | future partial-draft + typed criteria | MISSING | queue; no dummy candidates/score |
| Team analysis/role | loading engine+legacy details | 게임플랜 summary | one report + planboard | works from10picks | ADAPT four one-sentence conclusions |
| Lane metrics/purpose/wave/trade | modern coach + nested legacy | 게임플랜 lane | same coach/planboard, exact matchup source scope | qualitative supported/unknown separated | ADAPT purpose/grid/direction/changes first |
| Macro | coach operations | 게임플랜 operations | same area_context/operations | conditional composition application | ADAPT placement/connection/fallback first |
| Teamfight | coach fight | 게임플랜 fight | same role/threat/step/map | conditional tools/positions | ADAPT role/threat/start/exit first |
| Preference/scenarios/cost comparison | optional coach methods/conditions | gameplan optional details | preferences vs assumptions distinct | actual selection; not strength mutation | KEEP, after basic plan |
| Maps/line zoom/evidence | coach/directions | relevant optional detail | same selected report/step, official assets | existing supported geometry only | KEEP; no relabelled unsupported map |
| Item-gold/item-value | game-info | 경기 중 도우미 | one GameInfo inventory/catalog calculation | manual comparison; local observation withheld | KEEP single feature |
| Connection status/cash/team totals | game-info | helper connection first | authenticated game-info status; snapshot withheld | BLOCKED_EXTERNAL, display_eligible=false | ADAPT hierarchy, no auto live claims |
| Camp/objective/inhibitor/ultimate timers | game-info limitations | helper capability detail | missing verified events/patch rules/CD fields | NOT_SUPPORTED | keep null + reason; no countdown |
| Enemy jungle last-seen/path inference | absent | helper future | future last_seen separate from inferred directions | MISSING; no raw position field | queue; no fake marker |
| Own jungle routes | absent | helper/learning future | reviewed route knowledge + available input | MISSING | queue; no path generator |
| Live reference to gameplan | loading link | helper → gameplan | existing static pregame analysis | no live dynamic strategy permission | link only; no in-match recommendation |
| Private finished-game analysis | local /postgame | review → authenticated PC | PostgameStore/plan_id/timeline/end gate | existing local only | KEEP private boundary |
| Scene learning/six scenes | directions + loading-study | 학습실 | same25source/29claim registry +6scenes | works, hypotheses remain typed | ADAPT entry hierarchy, keep practice |
| Collection/quota/CI | status/source details | separate 작업 상태 link | snapshot + actual Actions/Handoff | snapshot not real-time | separate from five play menus |

## Navigation and views

Exactly five primary links: 전적 검색, 게임플랜, 경기 중 도우미, 경기 복기, 학습실.
Desktop sidebar and mobile bottom navigation share the same link nodes/current state;
status is a secondary link, not sixth primary item. Common tokens, focus/pressed/disabled,
readable rem sizes (mobile strategy grid uses body-small14px rather than shrinking to10/11px), actual-nav-height reserved padding, reduced motion and skip links remain.
Routes retain index/loading/game-info/directions URLs; index hashes select search,
dashboard/pro or review. Unknown/stale review selection shows missing data, not a fake match.
Guest goes directly to manual gameplan; account/pro dashboard remains reachable separately.
Decorative art session/pick independence and API secret boundary remain unchanged.
Latest official-art requirement limits active initial/manual choices to24official splashes;
the existing25-entry registry and generated decoration history remain preserved.

## Shared screen data contracts

| Screen/model | Input → output fields | Source | Refresh | Missing | Next |
|---|---|---|---|---|---|
| Static champions/items | catalog patch/version/hash → champion facts/slots, item prices/assets | existing Data Dragon catalogs | catalog deployment | null+reason/version mismatch | input, strategy, inventory, learning |
| Search/account | riot_id+region → rank, recent_matches, champions, statistics period/N, retrieved_at | private Account/League/Match APIs | explicit lookup; stale response generation guard | distinct input/notfound/auth/API unavailable | dashboard/gameplan/review |
| Pro reference | verified roster+account+queue420 → safe profiles, scope/refreshed_at | existing verified projection | existing schedule/manual only | preserve last safe result/failure marker | reference dashboard/review |
| Statistics | patch/population/role/champion/matchup → periods+denominators+omissions | preserved archives | deployment, no recollection | no role→matchup substitution | strategy Why/learning |
| Knowledge/review | exact matchup/patch/claim IDs → accepted scope/excerpts/conditions/counterexamples | one loading-knowledge registry + immutable history | source-version publication | limited claim only, no AI evidence promotion | engine/learning/future recommendations |
| Strategy input |10picks+own+role+optional assumptions/preferences → one report | loading-input-v4 | analyze/input edit invalidates old report | validation/unknown role | briefing/details/maps |
| Strategy result | report.coach.planboard → briefing_v2, lane/wave/operations/fight/area_context | same evaluate result | same report revision/period/scenario | unknown never contested/safe | optional method/cost/map/Why |
| Live observation | authenticated transport → status,current,received_at,snapshot=null,display_eligible=false | existing official local route, real PC not verified | explicit request/shared server throttle | disconnected/stale/blocked; no zero timer | manual item reference, connection status |
| Inventory | held slots+counts+selected patch → subtotal,total,difference,missing | one GameInfo + official item catalog | explicit compare; clear on edit | whole difference null for missing | helper calculation details |
| Review selection | safe recent row + USER/PRO_REFERENCE scope → displayed observed result, period/source; analysis_status=UNCONNECTED | existing record response in memory only | row selection; clear on profile invalidation | no plan/timeline/video fabricated | local finished-game analysis, learning |
| Actual postgame | match_id+plan_id → ended-game result and preserved plan/version | existing private PostgameStore | existing authenticated flow/end gate | no ended evidence → no analysis | local review |
| Learning | matchup/role/claim ID → same claim/conditions/source links + scenario practice | loading-study reads same registry | catalog deployment | unsupported topic marked absent | exact loading lesson or method |
| Work status | snapshot timestamps → support/collection status, Actions/Handoff links | existing status JSON + real external links | explicit deployed snapshot | stale snapshot labelled | technical records |

briefing_v2 is additive: four items our_plan/enemy_plan/my_role/key_change, one sentence
per item, source pointers/origin retained. Existing loading_summary and detailed objects
remain for compatibility. No separate UI-only advice or change to objective metrics.
Lane first view purpose→qualitative grid→basic wave/trade→key change. Context/counterplay,
steps, costs, maps and evidence open optionally; macro and fight have distinct first views.

## Deferred contracts, not fake implementation

Recommendation input must later support partial known picks, selected role, banned/unavailable
IDs and optional explicit mastery/preference. Output max3 eligible candidates; each has
criterion statuses for lane matchup/duo, composition gap, ally tools, enemy response,
mastery and unknown-pick resilience; reason, weakness, conditions and claim IDs, no aggregate
score. Account disconnected → mastery NOT_EVALUATED. No current engine evaluates these
criteria, so no selectable recommendation button/candidate is delivered in this change.
Future recommendation selection must use the same normalized final report and knowledge.

Jungle: observed last_seen(value,time,source,perspective) and inferred possible_directions
(rule,conditions,limits) are distinct; unknown position never an actual map marker. Own
route guidance requires reviewed route knowledge. These lack actual data/permission here.
Timers require source event+game clock+patch rule; ultimate availability cannot be inferred
from learned skill level. Price totals are not cash/earned gold/combat strength.

No live behavioral feature is enabled by this reorganization. Fresh official docs/policies
are checked separately and linked in the evidence; endpoint availability does not confer
permission for a dynamic overlay. Preserve current route's snapshot withholding.

## Verification and rollback

Meaningful before/after PC1440/mobile390 plus320 width/200% text: five primary targets,
status separate, guest10pick→brief→three tabs, edit invalidation, selected steps/zoom,
unknown/unsupported states, real-record-to-review selection and clearing, public no private
provider calls, stable hero, no fake mastery/timers. Required protected CI retained.
Rollback public5bbcf7c or sourcec446862 consumers, retaining all evidence/history. Functional
and deployment success != tactical knowledge approval/coaching accuracy/30sec understanding.

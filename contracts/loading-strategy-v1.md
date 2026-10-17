# Loading Strategy MVP v1 — additive public/PC composition flow

Authority: USER_LOADING_STRATEGY_MVP_2026-10-17. Extend the existing project/Pages URL.
No repeated conversational implementation/publishing approvals. Main owns this contract,
shared engine and integration. No new games/video/provider calls or paid work.

## Reuse / change map

| Existing part | Disposition | Implementation |
|---|---|---|
| Six directions scenes, card/map geometry, zoom | KEEP | Remain intact; related scenes become optional detail links |
| Official ko_KR173 roster/skills, candidate profiles/rules | KEEP/ADAPT | Offline, source-hashed public catalog; candidate interpretation stays exploratory |
| PC LCU sanitized cached draft and manual fallback | KEEP/ADAPT | Optional loopback-only import into the same pure analysis input |
| Economy/wave/vision inputs | ADAPT | Optional future scenarios only; never required for loading analysis |
| Public homepage / core summary | REPLACE entry point | Loading 10-pick page; old directions page remains directly accessible |
| Composition-linked plan / lane milestones / teamfight | MISSING | Add a deterministic pure engine with conditions, alternatives and sources |
| Current hosting, launcher, AUTO/HOLD/USER, Gemini/history | KEEP | Existing gated GitHub/Pages publication; no migration or grade inheritance |

## Public catalog contract — loading-data.json

`format`, `source_patch`, `champions` (object keyed by canonical ID). Each champion:
`id,name,aliases[],key,official_tags[],portrait:{sprite,x,y,w,h},facts[]`.
Fact: `slot` P/Q/W/E/R, `name,text,raw_excerpt,url,patch,sha256,local_source,locator`.
`profile`: `threats[],protection[],strong_when[],lane_style[],jungle_style[],initiative[],needs[]`,
`review_state:EXPLORATORY`, `rule_refs[]` (id/version/local_source/sha256),
`classification_incomplete:true`. Absent labels mean UNKNOWN, never absence/weakness.
`statistics[]` may contain only validated existing anonymous descriptive projections with
patch/population/champion/position/opponent scope, valid denominator, omissions and limits.
Do not invent statistics or promote role supplementation into matchup evidence.
`directions` is an exact copy of the existing directions-data.json, hash-bound for reuse.
`assets[]` records bounded official sprite URLs/path/version/hash; `source_bindings[]` hashes
all local reused inputs; `legacy` documents preserved advice/review/source-queue boundaries.

## Pure engine — loading-engine.js

UMD `LoadingStrategy` browser global / Node export.
Functions: `resolveChampion(query,catalog)` returns canonical ID or null;
`exampleInput(catalog,index=0)`; `fromDraft(draft,catalog)` sanitizes an existing InputDraft;
`analyze(input,catalog)` returns the complete loading report without economy inputs.

Input exact keys: `allies,enemies` arrays of5 `{champion,position}` (position is null or
TOP/JUNGLE/MID/BOTTOM/SUPPORT); `own_champion,own_position,side,patch,opponent_mode,lane_opponent`.
Own champion must be in allies,10 champions distinct, known positions unique per team;
own role conflicts reject. Side BLUE/RED. Patch null or numeric patch. Opponent mode
ASSIGNED/UNKNOWN/MANUAL; manual opponent must belong to enemies; unknown preserves null.
Champion search accepts Korean names/English names and canonical IDs. Analyze normalizes
aliases then validates. No current/future resources, economy, skill readiness or enemy intent
is inferred. fromDraft whitelists pick/position data only, rejects non-PRE_GAME draft.

Output: `schema_version,input,summary,composition,gameplan,lane,teamfight,scenarios,evidence`.
`summary:{our_plan,enemy_plan,collision,my_role,lane_key,fight_key,remember[],uncertainties[]}`;
remember <=3. Strings read in10–30seconds; source/dev detail stays below.
`composition:{allies,enemies}` each `{strengths[],weaknesses[],conditions[],signals[]}`;
signal names its actual champion/source refs and remains conditional interpretation.
`gameplan:{base,prepare[],fallback,switch_when[],stages[],side_vs_group,objectives,conversion}`.
`lane:{opponent:null|{id,name,position},status,rows[],interactions[],wave,jungle,reset_roam,recovery}`.
Exactly6 rows, IDs LEVEL1/LEVEL2/LEVEL3_5/LEVEL6/FIRST_PURCHASE/FIRST_CORE,
each `{id,period,judgment,why,action,changes,evidence_ids[],level}`. Unknown matchup advantage
does not hide supported mechanics. Skill unlock/rank/readiness is never assumed from level.
`teamfight:{role,partners[],threats[],setup[],actions[],switch_when[],exit[],after[],map}`;
partners/threats name actual picks and conditional means, not generic filler.
Partner/threat shape: `{champion,name,means,condition,evidence_ids[]}`. Stages:
`{stage,role,conditions[]}`. Teamfight map uses reusable decision geometry only after
role applicability is checked, contains actual allied picks, no unseen enemy positions,
and has three arrows numbered to the three teamfight actions. Unknown role does not
receive a forced engage diagram. Source class tags alone are not tactical approval.
`scenarios[]`: only applicable links to unchanged6 scene presets, own champion/role binding,
future assumption/prereqs/exceptions and illustrative map. Do not swap portrait to force fit.
`evidence:{facts[],rules[],statistics[],lectures:[],unknowns[],limits[],patch_status,
strategy_level:DESIGN_HYPOTHESIS,real_coaching_n:0,accuracy:null}`.
Facts official, existing exploratory rules and new interpretation are separate axes.

## UI / PC / publication

New responsive loading.html/js/css use the shared catalog+engine; root public index becomes
loading.html. Existing directions assets/page remain, with relative scene deep links.
Entry: choose/paste10 picks, own champion/position, optional assignments/opponent correction,
analyze → compact7-part summary → composition/lane/operations/teamfight/source details.
No economy input on required path. English terms include Korean meanings.
Existing cached PC connection can be imported only by explicit local action with existing
session token, same-origin loopback pc-status and ChampSelect. Public website never requests
local APIs or stores/exports credentials. Imported draft and manual draft use analyze().
No new live game adapter. Loading guidance is pre-game; live tactical approval is independent.

Acceptance: actual10-pick/role/composition counterfactuals; unknown enemy position and patch;
six milestone rows without fake scores; actual champion skill/partner/threat names; applicable
scene only; manual and sanitized PC import equivalence; mobile/PC summary→details; no economy
required; existing directions/launcher/auth/Frozen preservation. New functional checks and
required CI only, fresh independent review, expected-head normal merge and post-main evidence.
Publish the exact allowlisted static export to the existing gh-pages ref using non-force CAS;
preserve previous artifact and old failures. Rollback: deploy prior artifact6c950ca6 or use
the intact directions entry; no existing knowledge rows or archives are changed.

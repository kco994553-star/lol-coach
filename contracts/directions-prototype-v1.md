# Situational directions prototype v1 — DESIGN_HYPOTHESIS

Authority: user situational/minimap implementation and subsequent mobile-web instruction, 2026-10-17.
This additive learning/review prototype does not rewrite the existing seven advice revisions,
inherit AUTO/USER approvals, collect games/video, or connect to a live game. PC remains primary.

## Shared implementation

One pure JavaScript engine (`web_r4/directions-engine.js`) evaluates a public, curated
catalog (`web_r4/directions-data.json`) in both the PC server and exported mobile website.
No accounts, tokens, private match records, provider calls or persistent user inputs are needed.
UMD exports `DirectionEngine` in a browser and `module.exports` in Node.
API: `defaultInput(catalog)`, `evaluate(input, catalog)`. Invalid enum/extra fields reject.

Input fields: phase LANE/POST_LANE; decision RECALL/SIDE_GROUP/OBJECTIVE (must agree with
phase); champion Caitlyn/Fiora/Ornn; role TOP/JUNGLE/MID/BOTTOM/SUPPORT; side BLUE/RED;
review_mode PRE_GAME_LEARNING/POST_GAME_REVIEW; patch string or null; economy five roles,
each BEHIND/EVEN/AHEAD/UNKNOWN; metrics total_earned_difference/purchased_value_difference/
current_gold (number or null), observed_at (string or null); conditions as catalog enums.
Unknown is not even. No numeric classification thresholds. Metrics are manually supplied,
not independently verified and never interchangeable. Numeric values without an observation
time remain explicitly undated. Position is not the same as the situational tactical role.

Output fields: input; plan {id,title,direction,role,steps:[{number,text}],why:[],requirements:[],
alternative:{title,when,steps:[]},switch_when:[]}; champion {id,name,primary_type,secondary_types};
economy {states,metrics:[{key,label,value,unit,source,observed_at,missing,limit}],note};
evidence {level,label,official_facts:[],statistics:[],expert_statements:[],limits:[]};
map {asset,caption,entities:[{id,team,self,champion,portrait,start:{x,y},target:{x,y}|null}],
arrows:[{step,kind,from:{x,y},to:{x,y}}],landmarks:[{id,kind,label,x,y,step}],notes:[]}.
Coordinates normalized 0–100, x right/y down. Objective anchors stay geographically fixed;
RED changes friendly lane/base anchors without swapping top/bottom or dragon/baron.
Unknown enemy means no enemy portrait coordinate. All entities are illustrative examples.

## Six scenes, three reusable decisions

1. Lane management/recall: crashed wave + purchase ready vs large incoming wave, same economy.
2. Post-lane side/group: usable exit + connected allies vs unavailable exit, same economy.
3. Post-lane objective/trade: observed approach + known numbers/resources vs insufficient
   numbers/unobserved approach, same economy. No economy state is a fight-win prediction.

Representative champions Caitlyn/Fiora/Ornn deliberately contrast pressure, side and front
connection. General type, present role, official skill facts and unverified tactical
interpretation are separate. Type assignment and all action plans are design hypotheses.
Statistics and expert statements are empty when absent; no existing approval is inherited.

## Acceptance / publication

Meaningful engine tests then actual Chromium: six scene cards and maps, condition
counterfactual with same economy, economy reuse, champion-specific method, UNKNOWN,
RED anchors, numbered card/map steps, mobile zoom and no private/provider requests.
These establish behavior, not coaching effectiveness or Windows/LCU validation.
Export only an explicit public allowlist; PC serves the same assets. Publish only after
independent review, required CI, exact-head normal merge and applicable post-main checks.
Live tactical integration remains blocked pending product/data-path policy clearance.

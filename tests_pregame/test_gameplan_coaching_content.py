"""Real report behavior: role changes, absent actors and unknown-state boundaries."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRELUDE = """
const assert=require('node:assert/strict'), E=require('./web_r4/loading-engine.js'),
 C=require('./web_r4/loading-coach.js'), P=require('./web_r4/loading-presentation.js'),
 catalog=require('./web_r4/loading-data.json');
function input(role='JUNGLE') {const x=E.exampleInput(catalog,1);
 x.own_position=role;x.own_champion=x.allies.find(p=>p.position===role).champion;return x;}
function run(x=input()){return E.analyze(x,catalog).coach.planboard;}
"""

class GameplanCoachingContentTests(unittest.TestCase):
    def node(self, body):
        p = subprocess.run(['node', '-e', PRELUDE + body], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr[-5000:])

    def test_graves_jungle_plan_connects_growth_side_and_central_defense(self):
        self.node(r"""
const b=run();assert.match(b.operation_headline,/사이드.*중앙/);
assert.match(b.action_summaries.lane.items[0].text,/캠프|성장/);
assert.match(b.operations.placement,/중앙/);assert.match(b.operations.connection,/피오라/);
assert.match(b.fight.start,/빨리 뽑기\(E\)/);
assert.match(b.fight.target,/진입|들어온/);
assert.equal(b.briefing_v2.items.find(x=>x.id==='my_role').text,b.composition.role);
assert(b.condition_responses.operations.some(x=>x.id==='SIDE_DRAWS_TWO'));
assert(b.condition_responses.lane.some(x=>x.id==='JUNGLE_OPPOSITE'));
assert(b.coaching_explanation.operations.length>=2);
const v=P.project(E.analyze(input(),catalog));assert.equal(v.cards[0].label,'초반 정글');
assert.deepEqual(v.cards[1].explanation,b.coaching_explanation.operations);
""")

    def test_fiora_and_graves_have_different_jobs_in_same_team_plan(self):
        self.node(r"""
const f=run(input('TOP')),g=run();assert.deepEqual(f.team_plan.rows,g.team_plan.rows);
assert.match(f.operation_headline,/사이드/);assert.notEqual(f.operations.placement,g.operations.placement);
assert.match(f.fight.start,/응수\(W\)/);
assert(f.condition_responses.operations.some(x=>x.id==='SIDE_DEFENDER_LEAVES'));
assert.match(f.coaching_explanation.lane.join(' '),/공격 속도/);
for(const b of [f,g])for(const area of ['lane','operations','fight'])assert.equal(b.action_summaries[area].items.length,5);
assert.match(g.team_plan.theirs.opening,/말파이트.*자르반/);
assert.match(g.team_plan.theirs.damage,/오리아나.*징크스/);
""")

    def test_removed_champions_are_not_mentioned_by_new_rules(self):
        self.node(r"""
const x=input();x.allies[0].champion='Ornn';x.enemies[0].champion='Garen';
x.enemies[1].champion='Ivern';x.enemies[2].champion='Viktor';x.enemies[3].champion='Ezreal';
const b=run(x),text=JSON.stringify([b.coaching_explanation,b.team_plan,b.operations,b.fight,b.reminders]);
for(const absent of ['피오라','말파이트','자르반','오리아나','징크스'])assert(!text.includes(absent),absent);
assert(!b.condition_responses.operations.some(x=>x.id==='SIDE_DRAWS_TWO'));
assert.match(b.operation_headline,/성장/);
""")

    def test_missing_patch_and_wrong_role_do_not_gain_supported_coaching(self):
        self.node(r"""
let x=input();x.patch='1.1';assert(!run(x).coaching_explanation);
x=input();x.allies.find(p=>p.position==='JUNGLE').position='TOP';x.allies[0].position='JUNGLE';x.own_position='TOP';
assert(!run(x).coaching_explanation?.lane?.join(' ').includes('정글 캠프'));
""")

    def test_new_advice_does_not_promote_matchup_strength_or_live_state(self):
        self.node(r"""
const x=input(),r=E.analyze(x,catalog),b=r.coach.planboard;
assert.equal(b.coverage.status,'UNSUPPORTED');assert.equal(b.fight.kill,'UNDETERMINED');
for(const area of ['lane','operations','fight'])for(const c of b.condition_responses[area]){
 assert.equal(c.observation,false);assert(c.trigger&&c.action&&c.stop);
}
const f=E.analyze(input('TOP'),catalog);
const low=C.evaluate(f,catalog,{standard:'lane-standard-v1',overrides:{resources:'LOW'}},'LEVEL6').planboard;
assert.match(low.action_summaries.lane.items[0].text,/체력|회복/);
assert.match(low.action_summaries.lane.items[2].text,/교환.*줄|공격.*강제|무리/);
const lowJ=C.evaluate(r,catalog,{standard:'lane-standard-v1',overrides:{resources:'LOW'}},'LEVEL6').planboard;
assert.match(lowJ.action_summaries.lane.items[2].text,/회복|구매/);
""")

    def test_five_users_share_whole_team_plan_with_fixed_opponent_perspective(self):
        self.node(r"""
for(const n of [0,1]){
 const x=E.exampleInput(catalog,n),plans=x.allies.map(p=>E.analyze({...x,own_champion:p.champion,own_position:p.position},catalog).coach.planboard);
 for(const b of plans){assert.deepEqual(b.team_plan,plans[0].team_plan);for(const row of b.team_plan.rows)assert(!row.theirs.includes('아군'),row.theirs);}
 assert(new Set(plans.map(b=>b.composition.role)).size>1);
 const swap={...x,allies:x.enemies,enemies:x.allies,own_champion:x.enemies[0].champion,own_position:x.enemies[0].position,side:'RED'};
 assert.notDeepEqual(E.analyze(swap,catalog).coach.planboard.team_plan.rows,plans[0].team_plan.rows);
}
""")

    def test_team_comparison_four_basics_keep_actual_team_result(self):
        self.node(r"""
const x=input(),r=E.analyze(x,catalog),v=P.project(r);
assert.deepEqual(v.comparison.map(row=>row.label),['원하는 승리 방식','좋은 싸움','운영의 핵심','주요 위험']);
assert.equal(v.comparison[0].ours,r.coach.planboard.team_plan.ours.win);
assert.equal(v.comparison[2].theirs,r.coach.planboard.team_plan.theirs.macro);
assert.equal(v.comparison[3].ours,r.coach.planboard.team_plan.ours.avoid);
assert(v.comparison[1].theirs.includes(r.coach.planboard.team_plan.theirs.opening));
x.patch='1.1';assert.deepEqual(P.project(E.analyze(x,catalog)).comparison,[]);
""")

    def test_waiting_costs_do_not_force_kaisa_mage_engage_and_follow_support_changes(self):
        self.node(r"""
const x=E.exampleInput(catalog,0);x.allies[3].champion='Kaisa';x.allies[4].champion='Alistar';x.enemies[3].champion='Ziggs';x.own_champion='Kaisa';
const r=E.analyze(x,catalog),w=r.coach.planboard.waiting;
assert(w,'waiting costs must be part of the generated report');
assert.match(w.loss,/CS.*경험치|경험치.*CS/);assert.match(w.loss,/체력/);assert.match(w.loss,/웨이브|미니언/);assert.match(w.loss,/주도권/);
assert.equal(w.observation,false);assert.equal(w.outcome,'UNDETERMINED');assert.match(w.window,/레벨|배운/);assert.match(w.window,/알리스타/);assert.match(w.window,/노틸러스/);assert.match(w.window,/직스/);
assert.match(w.fallback,/귀환|지원/);assert.match(w.switch,/웨이브|미니언/);
x.allies[4].champion='Lux';const other=E.analyze(x,catalog).coach.planboard.waiting;
assert.notEqual(other.window,w.window);assert.match(other.window,/빛의 속박\(Q\)/);assert(!other.window.includes('알리스타'));
x.enemies[4].champion='Lulu';const protectedEnemy=E.analyze(x,catalog).coach.planboard.waiting;assert.match(protectedEnemy.window,/변덕쟁이\(W\)/);assert.match(protectedEnemy.window,/반격|기본 공격|스킬/);assert(!protectedEnemy.window.includes('닻줄 견인'));
x.enemies[4].champion='Nautilus';
const low=C.evaluate(r,catalog,{standard:'lane-standard-v1',overrides:{resources:'LOW'}},'LEVEL6').planboard.waiting;
assert.equal(low.mode,'LIMIT_LOSS');assert.match(low.window,/강제하지/);
const noHelp=JSON.parse(JSON.stringify(x));noHelp.schema_version='lol-coach-loading-input-v4';noHelp.preferences={risk:'BALANCED'};noHelp.scenario={standard:'lane-standard-v1',overrides:{}};noHelp.planning={basis:'loading-plan-example-v1',overrides:{ally_followup:'UNAVAILABLE'}};const unsupported=E.analyze(noHelp,catalog).coach.planboard.waiting;
assert.equal(unsupported.mode,'LIMIT_LOSS');
const missing=C.evaluate(r,catalog,{standard:'lane-standard-v1',overrides:{resources:'UNKNOWN',wave:'UNKNOWN'}},'LEVEL1').planboard.waiting;
assert.equal(missing.mode,'CHECK_CONDITIONS');assert.match(missing.fallback,/확인|지원/);
x.patch='1.1';assert.equal(E.analyze(x,catalog).coach.planboard.waiting.mode,'SOURCE_REVIEW_REQUIRED');
""")

    def test_waiting_alternatives_match_roles_and_existing_branch_stays_specific(self):
        self.node(r"""
for(const role of ['TOP','JUNGLE','MID','BOTTOM','SUPPORT']){
 const b=run(input(role)),w=b.waiting;assert(w&&w.loss&&w.window&&w.fallback&&w.switch);
 if(role==='SUPPORT'){assert(!/캠프|개인.*수급/.test(w.fallback));assert.match(w.fallback,/보호|시야|아군/);}
 if(role==='JUNGLE')assert.match(w.loss,/캠프/);
}
const b=run(),late=b.condition_responses.operations.find(c=>c.id==='LATE_JOIN');
if(late)assert.match(late.action,/늦|합류|따라/);
""")

    def test_missing_followup_and_unknown_jungle_conditions_gate_primary_and_detail_together(self):
        self.node(r"""
const x=E.exampleInput(catalog,0);x.schema_version='lol-coach-loading-input-v4';x.preferences={risk:'OPPORTUNITY'};x.scenario={standard:'lane-standard-v1',overrides:{enemy_key:'SPENT'}};x.planning={basis:'loading-plan-example-v1',overrides:{ally_followup:'UNAVAILABLE'}};
const r=E.analyze(x,catalog),b=r.coach.planboard;
assert.equal(r.coach.wave.selected.id,'CHECK_WAVE');assert.equal(b.wave.plan_id,'CHECK_WAVE');
assert.match(b.wave.combat,/호응/);assert.match(b.action_summaries.lane.items[2].text,/호응/);
assert.match(b.condition_responses.lane.find(c=>c.id==='ENEMY_KEY_SPENT').action,/호응/);
assert(!r.coach.actions.some(a=>['SHORT_POKE','COUNTER_FOCUS_ADC'].includes(a.id)&&a.feasible==='POSSIBLE'));
const g=E.analyze(input(),catalog),u=C.evaluate(g,catalog,{standard:'lane-standard-v1',overrides:{resources:'UNKNOWN',wave:'UNKNOWN'}},'LEVEL6').planboard;
const j=E.exampleInput(catalog,0);j.own_champion='Sejuani';j.own_position='JUNGLE';const lowJ=C.evaluate(E.analyze(j,catalog),catalog,{standard:'lane-standard-v1',overrides:{resources:'LOW'}},'LEVEL6').planboard;assert.match(lowJ.action_summaries.lane.items[2].text,/회복|구매/);
assert.match(u.action_summaries.lane.items[2].text,/미확인|확인/);assert.match(u.coaching_explanation.lane.join(' '),/미확인/);
""")

    def test_independent_narrative_shares_decisions_across_three_phases(self):
        self.node(r"""
const x=input('BOTTOM'),roles=['TOP','JUNGLE','MID','BOTTOM','SUPPORT'];
x.allies=['Ornn','Vi','Ahri','Kaisa','Nautilus'].map((champion,i)=>({champion,position:roles[i]}));
x.enemies=['Renekton','Graves','Orianna','Ziggs','Karma'].map((champion,i)=>({champion,position:roles[i]}));x.own_champion='Kaisa';
const r=E.analyze(x,catalog),b=r.coach.planboard,v=P.project(r);
assert(b.narrative_decisions,'causal decisions must exist before prose');
for(const area of ['lane','operations','fight']){
 const d=b.narrative_decisions[area];assert(d.pressure&&d.cost&&d.response&&d.payoff&&d.fallback);
 assert.equal(d.observation,false);assert.equal(d.outcome,'UNDETERMINED');
 assert.deepEqual(v.cards.find(c=>c.id===area).explanation,b.coaching_explanation[area]);
 assert.equal(b.action_summaries[area].items.length,5);
 assert(!b.coaching_explanation[area].some(p=>b.action_summaries[area].items.some(a=>a.text===p)));
 assert(d.actors.every(id=>[...x.allies,...x.enemies].some(p=>p.champion===id)));
}
assert.match(b.coaching_explanation.operations.join(' '),/직스/);assert.match(b.coaching_explanation.operations.join(' '),/바이/);assert.match(b.coaching_explanation.operations.join(' '),/아리/);
assert(b.narrative_decisions.fight.evidence_ids.includes('official:Ahri:E'));assert(!b.narrative_decisions.fight.evidence_ids.includes('official:Ahri:R'));
assert.match(b.coaching_explanation.fight.join(' '),/레넥톤/);assert.match(b.coaching_explanation.fight.join(' '),/오리아나/);
assert.match(b.coaching_explanation.lane.join(' '),/노틸러스/);assert.match(b.coaching_explanation.lane.join(' '),/카르마/);
const swap=structuredClone(x);swap.allies[4].champion='Lulu';const other=run(swap);
assert.notEqual(other.narrative_decisions.lane.response,b.narrative_decisions.lane.response);
assert.equal(other.narrative_decisions.fight.pressure,b.narrative_decisions.fight.pressure);
assert(!JSON.stringify(other.coaching_explanation).includes('노틸러스'));assert.match(other.operations.connection,/룰루의 보호·방해/);
const enemy=structuredClone(x);enemy.enemies[3].champion='Ezreal';const changed=run(enemy);
assert.notEqual(changed.narrative_decisions.operations.pressure,b.narrative_decisions.operations.pressure);
assert.equal(changed.narrative_decisions.fight.pressure,b.narrative_decisions.fight.pressure);
assert(!JSON.stringify(changed.coaching_explanation).includes('직스'));
for(const p of x.allies)assert.deepEqual(run({...x,own_champion:p.champion,own_position:p.position}).team_plan,b.team_plan);
x.patch='1.1';assert(!run(x).narrative_decisions);
""")

    def test_narrative_respects_manual_opponent_existing_kit_and_limited_window(self):
        self.node(r"""
const x=E.exampleInput(catalog,0);const old=run(x);
assert(!old.coaching_explanation.lane.join(' ').includes('프리즘 보호막(W)'),'unlearned Lux W must not replace reviewed level-one plan');
x.allies[3].champion='Kaisa';x.own_champion='Kaisa';x.enemies[3].champion='Ziggs';x.opponent_mode='MANUAL';x.lane_opponent=x.enemies[2].champion;
const manual=run(x);assert(!manual.coaching_explanation.lane.join(' ').includes('직스'),'manual lane opponent remains authoritative');
x.opponent_mode='ASSIGNED';x.lane_opponent=null;
const r=E.analyze(x,catalog),low=C.evaluate(r,catalog,{standard:'lane-standard-v1',overrides:{resources:'LOW'}},'LEVEL1').planboard;
assert(!low.condition_responses.lane.some(c=>c.id==='PLAN_WINDOW'));assert(low.condition_responses.lane.some(c=>c.id==='PREPARE_WINDOW'));
assert.match(low.action_summaries.lane.items[2].text,/부족|여건/);
""")

    def test_narrative_preserves_planning_and_wave_constraints(self):
        self.node(r"""
const x=E.exampleInput(catalog,0);x.allies[3].champion='Kaisa';x.own_champion='Kaisa';x.allies[4].champion='Nautilus';x.enemies[4].champion='Karma';x.enemies[3].champion='Ziggs';
x.schema_version='lol-coach-loading-input-v4';x.preferences={risk:'BALANCED'};x.scenario={standard:'lane-standard-v1',overrides:{}};
for(const overrides of [{enemy_jungle:'NEAR'},{goal:'FARM'},{goal:'RECALL'}]){
 x.planning={basis:'loading-plan-example-v1',overrides};const b=run(x);
 assert(b.condition_responses.lane.some(c=>c.id==='PREPARE_WINDOW'));
 assert(!b.coaching_explanation.lane[1].includes('적 미니언을 지나며'));
 assert.equal(b.action_summaries.lane.items[2].text,b.wave.combat);
}
""")

    def test_v13_waiting_need_and_feasibility_are_independent(self):
        self.node(r"""
const x=input('BOTTOM'),roles=['TOP','JUNGLE','MID','BOTTOM','SUPPORT'];
x.allies=['Ornn','Vi','Ahri','Kaisa','Nautilus'].map((champion,i)=>({champion,position:roles[i]}));
x.enemies=['Renekton','Graves','Orianna','Ziggs','Karma'].map((champion,i)=>({champion,position:roles[i]}));x.own_champion='Kaisa';
x.schema_version='lol-coach-loading-input-v4';x.preferences={risk:'BALANCED'};
function variant(overrides,scenario={}){return run({...x,planning:{basis:'loading-plan-example-v1',overrides},scenario:{standard:'lane-standard-v1',overrides:scenario}});}
const normal=variant({income:'NORMAL',opportunity:'AVAILABLE',ally_followup:'AVAILABLE'}),loss=variant({income:'LOSING',opportunity:'AVAILABLE',ally_followup:'AVAILABLE'}),low=variant({income:'LOSING',opportunity:'AVAILABLE',ally_followup:'AVAILABLE',enemy_wave:'LARGE'},{resources:'LOW',wave:'INCOMING'}),alone=variant({income:'LOSING',opportunity:'AVAILABLE',ally_followup:'UNAVAILABLE'}),missed=variant({income:'LOSING',opportunity:'MISSED'});
assert.equal(normal.engagement_decision.state,'WAIT_AND_PREPARE');
assert.equal(loss.engagement_decision.state,'CREATE_WINDOW');
for(const b of [low,alone]){assert.equal(b.engagement_decision.necessity,'CHANGE_NEEDED');assert.equal(b.engagement_decision.feasibility,'BLOCKED');assert.equal(b.engagement_decision.state,'PREPARE_CONDITIONS');}
assert.equal(missed.engagement_decision.state,'OPPORTUNITY_MISSED');
for(const b of [normal,loss,low,alone,missed]){
 const d=b.engagement_decision;assert.equal(d.observed,false);assert.equal(d.spec_version,'1.3');
 assert.equal(b.action_summaries.lane.items[2].text,d.action);assert.equal(b.wave.combat,d.action);
 assert(b.coaching_explanation.lane.join(' ').includes(d.reason));
 assert.equal(b.condition_responses.lane[0].action,d.action);
 assert.deepEqual(b.team_plan,normal.team_plan);
 assert.deepEqual(b.coaching_explanation.fight,normal.coaching_explanation.fight);
 assert(b.overall_commentary.length);assert.equal(b.versions.spec,'1.3');
}
assert.notEqual(normal.coaching_explanation.lane.join(' '),loss.coaching_explanation.lane.join(' '));
assert.match(low.engagement_decision.alternative,/경험치|귀환/);
for(const role of ['JUNGLE','SUPPORT']){const a={...x,scenario:{standard:'lane-standard-v1',overrides:{}},own_position:role,own_champion:x.allies.find(p=>p.position===role).champion,planning:{basis:'loading-plan-example-v1',overrides:{income:'LOSING',ally_followup:'UNAVAILABLE'}}};const b=run(a);assert(!b.engagement_decision.action.includes('막타'));if(role==='SUPPORT')assert(!b.engagement_decision.alternative.includes('캠프'));}
""")

    def test_v13_missing_mechanism_limits_specific_coaching_and_preserves_input(self):
        self.node(r"""
const x=input('BOTTOM'),roles=['TOP','JUNGLE','MID','BOTTOM','SUPPORT'];
x.allies=['Ornn','Vi','Ahri','Kaisa','Nautilus'].map((champion,i)=>({champion,position:roles[i]}));
x.enemies=['Renekton','Graves','Orianna','Ziggs','Karma'].map((champion,i)=>({champion,position:roles[i]}));x.own_champion='Kaisa';
const before=JSON.stringify(x),r=E.analyze(x,catalog),v=P.project(r);assert.equal(JSON.stringify(x),before);
assert.deepEqual(v.overall_commentary,r.coach.planboard.overall_commentary);assert(v.overall_commentary[1].includes('오른·바이·아리·노틸러스'));assert(v.overall_commentary[1].includes('공격'));
const modified=structuredClone(catalog);modified.champions.Nautilus.facts=modified.champions.Nautilus.facts.filter(f=>f.slot!=='Q');
const limited=E.analyze(x,modified).coach.planboard;
assert(!limited.coaching_explanation.lane.join(' ').includes('닻줄 견인(Q)'));
assert.match(limited.coaching_scope.limitation,/미지원/);
const again=E.analyze(x,catalog);assert.deepEqual(again.coach.planboard,r.coach.planboard);
x.patch='1.1';const patch=E.analyze(x,catalog).coach.planboard;assert(!patch.narrative_decisions);assert(!patch.overall_commentary?.length);
""")

    def test_v13_limits_reach_legacy_actions_and_perspectives(self):
        self.node(r"""
for(const overrides of [{income:'LOSING',opportunity:'MISSED'},{income:'NORMAL',enemy_wave:'LARGE'}]){
 const x=E.exampleInput(catalog,0);x.schema_version='lol-coach-loading-input-v4';x.preferences={risk:'OPPORTUNITY'};x.scenario={standard:'lane-standard-v1',overrides:{}};x.planning={basis:'loading-plan-example-v1',overrides};
 const r=E.analyze(x,catalog),b=r.coach.planboard,d=b.engagement_decision;
 assert(!r.coach.actions.some(a=>['SHORT_POKE','COUNTER_FOCUS_ADC'].includes(a.id)&&a.feasible==='POSSIBLE'));
 assert.equal(b.area_context.lane.ours,b.matchup_playbook.ours.means);
 assert.equal(b.area_context.lane.matchup,d.reason);
 assert.equal(b.condition_responses.lane[0].action,d.action);
 assert(!b.condition_responses.lane.some(c=>['ENEMY_KEY_SPENT','LUX_BIND_HIT','PLAN_WINDOW'].includes(c.id)));
 if(overrides.enemy_wave)assert.equal(d.state,'PREPARE_CONDITIONS');
}
""")

    def test_v13_role_fallback_does_not_assign_lane_income_to_support_or_jungle(self):
        self.node(r"""
const base=require('./evidence/actual-evidence/handoff-v11/v13-outputs.json').variants.base.input;
const boards=base.allies.map(p=>run({...base,own_champion:p.champion,own_position:p.position}));
for(const b of boards)assert.equal(b.overall_commentary[0],boards[0].overall_commentary[0]);
assert.equal(new Set(boards.map(b=>b.overall_commentary[1])).size,5);
const j=boards[1],s=boards[4];
assert.match(j.operations.priority,/캠프/);assert.match(s.operations.priority,/아군.*시야|시야.*아군/);
for(const b of [j,s]){
 assert(!b.coaching_explanation.operations.join(' ').includes('미니언을 먼저 잡아야'));
 assert(!b.condition_responses.operations.some(c=>c.trigger.includes('미니언도 많이 놓친다면')));
 assert.equal(b.action_summaries.operations.items[2].text,b.operations.priority);
 assert.equal(b.loading_summary.items.find(i=>i.id==='operations').support,b.operations.fallback);
}
const sej=E.exampleInput(catalog,0);sej.own_champion='Sejuani';sej.own_position='JUNGLE';const preserved=run(sej);assert.equal(preserved.operations.concept,'밀어 넣는 라인을 돕고, 함께 들어갈 시야 만들기');assert.match(preserved.operations.priority,/아군의 밀어 넣기를 도와 귀환/);
assert(!s.operations.fallback.includes('캠프'));assert.match(s.coaching_explanation.operations.join(' '),/아군.*귀환|귀환.*아군/);
""")

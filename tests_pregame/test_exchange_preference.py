"""Trade-length candidates are hypotheses, not encounter-win evidence."""
import unittest
import tests_pregame.test_loading_strategy as legacy
class ExchangePreferenceTests(unittest.TestCase):
 run_node=legacy.LoadingStrategyTests.run_node
 prefix="""
assert(fs.existsSync('./web_r4/loading-exchange.js'),'relative exchange output missing');
const T=require('./web_r4/loading-exchange'),G=require('./web_r4/loading-engagement'),a=E.exampleInput(C,0);a.allies.find(p=>p.position==='BOTTOM').champion='Yunara';a.allies.find(p=>p.position==='SUPPORT').champion='Lulu';a.enemies.find(p=>p.position==='BOTTOM').champion='Lucian';a.own_champion='Yunara';const gs=G.defaultState();gs.milestone='LEVEL6';gs.assumptions={...gs.assumptions,resources:'READY',window:'ENEMY_Q_SPENT',followup:'BOTH',space:'PLAYABLE',intervention:'DUO_ONLY',growth:'COMPARABLE',spells:'BOTH_READY',initiator:'ALLY',hit:'ALLY_HIT'};const state=T.defaultState();
const get=(risk='BALANCED',goal='SPACE')=>{const base=E.analyze(a,C),report={...base,input:{...base.input,preferences:{risk}}},g=G.evaluate(report,C,gs,goal);return T.evaluate(report,C,g,state);};
const ready=()=>{state.ours={window:'REPEAT_ACTIVE',cover:'ACTIVE',contact:'CONNECTED'};state.theirs={window:'HIT_WINDOW',cover:'ACTIVE',contact:'CONNECTED'};};
"""
 def test_missing_information_cannot_be_filled_by_selected_type_or_risk(self):
  self.run_node(self.prefix+"""
for(const type of Object.keys(G.typeNames))for(const risk of ['LOSS_LIMIT','BALANCED','OPPORTUNITY']){gs.type=type;const x=get(risk);assert.equal(x.ours.classification,'UNKNOWN');assert.equal(x.theirs.classification,'UNKNOWN');assert.equal(x.actual_matchup_advantage,'UNKNOWN');assert.equal(x.observation,'HYPOTHETICAL');assert.equal(x.attack_gate,'UNCHANGED');}
assert(E.analyze(a,C).exchange);assert.throws(()=>T.evaluate(E.analyze(a,C),C,G.evaluate(E.analyze(a,C),C,gs),{...state,ours:{...state.ours,contact:'safe'}}));
""")
 def test_conditional_repeat_switches_to_short_loss_limit_on_ending_cover(self):
  self.run_node(self.prefix+"""
ready();let x=get();assert.equal(x.ours.classification,'CONDITIONAL');assert.equal(x.ours.mode,'REPEATED');assert.equal(x.actual_matchup_advantage,'UNKNOWN');assert(x.ours.attack_order.some(t=>t.includes('유나라의 영혼 단련(Q)')));assert(x.ours.end.some(t=>t.includes('종료')));assert(x.ours.continue_if.length);
state.ours.cover='ENDING';x=get();assert.equal(x.ours.mode,'SHORT');assert.equal(x.attack_gate,'NO_ADDITIONAL_ATTACK');assert.equal(x.ours.short_may_only_limit_loss,true);assert.equal(x.actual_matchup_advantage,'UNKNOWN');assert(x.ours.attack_order.some(t=>t.includes('추가 공격을 시작하지')));
""")
 def test_preference_unchanged_under_risk_and_wave_goal_but_cost_blocks_adoption(self):
  self.run_node(self.prefix+"""
ready();const loss=get('LOSS_LIMIT'),opp=get('OPPORTUNITY');assert.deepEqual(loss.ours,opp.ours);assert.deepEqual(loss.theirs,opp.theirs);
const reset=get('OPPORTUNITY','RESET');assert.deepEqual(reset.ours,opp.ours);assert.equal(reset.wave.adoption,'WITHHELD_FOR_RESET');assert(reset.wave.cost.includes('처리'));assert.equal(reset.all_in_supported,false);assert.equal(reset.chase_supported,false);
""")
 def test_opponent_has_different_cycles_not_a_permanent_stereotype(self):
  self.run_node(self.prefix+"""
ready();assert.equal(get().theirs.mode,'SHORT');state.theirs.window='REPEAT_ACTIVE';const x=get();assert.equal(x.theirs.mode,'REPEATED');assert(x.theirs.reason.includes('루시안의 빛의 사수(P)'));assert(x.theirs.reason.includes('노틸러스'));assert(x.theirs.cover_owner==='Nautilus');assert(x.theirs.intent==='UNKNOWN');assert(x.theirs.attack_order.some(t=>t.includes('재사용')||t.includes('가용')));
""")
 def test_caitlyn_sources_are_not_replaced_with_yunara_loop(self):
  self.run_node(self.prefix+"""
const b=E.exampleInput(C,0),r=E.analyze(b,C);ready();state.ours.window='HIT_WINDOW';let x=T.evaluate(r,C,G.evaluate(r,C,gs,'SPACE'),state);assert.equal(x.ours.mode,'SHORT');assert(x.ours.attack_order.some(t=>t.includes('케이틀린의 헤드샷(P)')));assert(x.ours.attack_order.some(t=>t.includes('다시')&&t.includes('이탈')));assert(!JSON.stringify(x).includes('유나라의'));
state.ours.window='REPEAT_ACTIVE';x=T.evaluate(r,C,G.evaluate(r,C,gs,'SPACE'),state);assert.equal(x.ours.classification,'UNKNOWN');assert.notEqual(x.ours.mode,'REPEATED');
""")
 def test_explicit_end_filters_existing_attack_without_altering_original_or_win(self):
  self.run_node(self.prefix+"""
ready();state.ours.contact='BREAKING';const r=E.analyze(a,C),g=G.evaluate({...r,input:{...r.input,preferences:{risk:'OPPORTUNITY'}}},C,gs,'SPACE');assert.equal(g.selected_action_id,'SHORT_WINDOW');const x=T.evaluate(r,C,g,state),filtered=T.constrainEngagement(g,x);assert(!filtered.actions.some(p=>p.id==='SHORT_WINDOW'));assert.equal(g.selected_action_id,'SHORT_WINDOW');assert.equal(filtered.advantage,'UNKNOWN');assert.equal(T.waveMeans({selected_plan_id:'SHORT_FOLLOW'},x).selected_plan_id,'PREPARE_WINDOW');
""")
 def test_patch_phase_assignment_and_source_history(self):
  self.run_node(self.prefix+"""
ready();const r=E.analyze(a,C);for(const patch of [null,'16.19'])assert(!T.evaluate(E.analyze({...a,patch},C),C,G.evaluate(E.analyze({...a,patch},C),C,gs),state).supported);
assert(!T.evaluate(E.analyze({...a,opponent_mode:'UNKNOWN'},C),C,G.evaluate(E.analyze({...a,opponent_mode:'UNKNOWN'},C),C,gs),state).supported);
gs.milestone='LEVEL1';assert.equal(get().ours.classification,'UNKNOWN');gs.milestone='LEVEL6';const before=JSON.stringify(C),x=get();assert.equal(JSON.stringify(C),before);assert(x.evidence.facts.every(f=>f.url&&f.sha256&&f.patch));assert(x.ours.reason.includes('룰루의'));assert(x.ours.end.every(s=>!/[35]초/.test(s)));assert.equal(x.evidence.matchup_comparisons,0);
""")
 def test_unsupported_duo_and_invalid_phase_do_not_emit_other_duo_attack_plans(self):
  self.run_node(self.prefix+"""
const b=E.exampleInput(C,0);b.enemies.find(p=>p.position==='BOTTOM').champion='Jinx';const r=E.analyze(b,C),x=T.evaluate(r,C,G.evaluate(r,C,gs),state);assert(!x.supported);assert(!JSON.stringify(x).includes('카이사'));assert.equal(x.theirs.cover_owner,null);assert.deepEqual(x.theirs.attack_order,[]);
ready();gs.milestone='LEVEL1';gs.assumptions.window='ALL_READY';const y=get();assert.equal(y.ours.classification,'UNKNOWN');assert(y.ours.attack_order.every(t=>!t.includes('영혼 단련(Q)')));
""")
if __name__=='__main__':unittest.main()

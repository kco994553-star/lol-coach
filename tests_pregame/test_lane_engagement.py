"""Conditional encounter mechanics, not real-game win validation."""
import unittest
import tests_pregame.test_loading_strategy as legacy
class LaneEngagementTests(unittest.TestCase):
 run_node=legacy.LoadingStrategyTests.run_node
 prefix="""
assert(fs.existsSync('./web_r4/loading-engagement.js'),'engagement engine missing');
const G=require('./web_r4/loading-engagement'),a=E.exampleInput(C,0);a.allies.find(p=>p.position==='BOTTOM').champion='Yunara';a.allies.find(p=>p.position==='SUPPORT').champion='Lulu';a.enemies.find(p=>p.position==='BOTTOM').champion='Lucian';a.own_champion='Yunara';const r=E.analyze(a,C),s=G.defaultState();
const ready=()=>{s.milestone='LEVEL6';s.assumptions={growth:'COMPARABLE',resources:'READY',window:'ENEMY_Q_SPENT',level_stage:'UNKNOWN',hit:'ALLY_HIT',followup:'BOTH',space:'PLAYABLE',intervention:'DUO_ONLY',spells:'BOTH_READY',initiator:'ALLY'};};
const get=(risk='BALANCED')=>G.evaluate({...r,input:{...r.input,preferences:{risk}}},C,s);
"""
 def test_no_false_win_and_preference_is_not_evidence(self):
  self.run_node(self.prefix+"""
for(const period of G.periods)for(const type of Object.keys(G.typeNames)){s.milestone=period;s.type=type;for(const risk of ['LOSS_LIMIT','BALANCED','OPPORTUNITY']){const x=get(risk);assert.equal(x.advantage,'UNKNOWN');assert.equal(x.probability,null);assert.equal(x.all_in_supported,false);assert.equal(x.observation,'HYPOTHETICAL');}}
ready();s.type='SHORT';const l=get('LOSS_LIMIT'),o=get('OPPORTUNITY');assert.equal(l.advantage,o.advantage);assert.notEqual(l.selected_action_id,o.selected_action_id);assert.equal(l.evidence.grade,'DESIGN_HYPOTHESIS');s.assumptions.hit='UNKNOWN';assert(!get('OPPORTUNITY').actions.some(a=>a.id==='SHORT_WINDOW'));assert(r.engagement);assert.equal(r.evidence.real_coaching_n,0);
""")
 def test_spent_spell_is_not_allin_and_remaining_counter_is_explicit(self):
  self.run_node(self.prefix+"""
ready();s.assumptions.window='ALL_READY';assert(get().remaining_counters.some(t=>t.startsWith('노틸러스의 닻줄 견인(Q)')));s.assumptions.window='ENEMY_Q_SPENT';assert(!get().remaining_counters.some(t=>t.startsWith('노틸러스의 닻줄 견인(Q)')));s.type='ALL_IN';let x=get('OPPORTUNITY');assert(!x.actions.some(a=>a.id==='ALL_IN'));assert(x.remaining_counters.some(t=>t.includes('강력한 일격(P)')));assert(x.remaining_counters.some(t=>t.includes('폭뢰(R)')));assert(x.wave_bridge.includes('푸시'));
s.milestone='LEVEL3_5';x=get();assert(!x.remaining_counters.some(t=>t.startsWith('노틸러스의 폭뢰(R)')));assert(x.period_change.includes('궁극기'));
s.milestone='LEVEL6';s.type='SHORT';s.assumptions.followup='UNKNOWN';x=get('OPPORTUNITY');assert(!x.actions.some(a=>a.id==='SHORT_WINDOW'));assert(x.required_checks.length>0);
""")
 def test_default_and_negative_information_do_not_unlock_push(self):
  self.run_node(self.prefix+"""
assert.equal(get().wave_constraint,'UNCHANGED');ready();s.assumptions.window='ALLY_DEFENCE_SPENT';assert.equal(get().wave_constraint,'LIMIT_EXPOSURE');
s.assumptions.window='ENEMY_Q_SPENT';s.assumptions.space='UNKNOWN';assert(!get().actions.some(a=>a.id==='CS_WINDOW'));ready();s.milestone='LEVEL2';s.assumptions.window='ALL_READY';assert.equal(get().scenario_valid,false);assert(!get().actions.some(a=>a.id==='SHORT_WINDOW'));assert.throws(()=>G.evaluate(r,C,{...s,assumptions:{...s.assumptions,window:'guessed'}}));
const original=JSON.parse(fs.readFileSync('./evidence/actual-evidence/lane-engagement/review-queue.json'));assert.equal(original.user_hypothesis.adopted,false);assert.equal(original.user_hypothesis.user_decision_created,false);
""")
 def test_context_patch_sources_and_input_order(self):
  self.run_node(self.prefix+"""
ready();const x=get();assert(x.supported);assert.equal(x.matchup,'Yunara_Lulu__Lucian_Nautilus');assert.deepEqual(G.evaluate(E.analyze({...a,allies:[...a.allies].reverse(),enemies:[...a.enemies].reverse()},C),C,s),x);
const c=copy(C);c.champions.Lulu.facts=c.champions.Lulu.facts.filter(f=>f.slot!=='R');assert(!G.evaluate(r,c,s).supported);assert(!G.evaluate(E.analyze({...a,patch:'16.19'},C),C,s).supported);
assert(x.evidence.facts.some(f=>f.id==='official:Yunara:R'));assert(x.period_change.includes('自己')||x.period_change.includes('자기 초월(R)'));assert(x.evidence.facts.every(f=>f.url&&f.sha256&&f.patch));
""")
 def test_review_negative_gate_unknown_assignment_and_separate_ultimates(self):
  self.run_node(self.prefix+"""
const W=require('./web_r4/loading-wave'),b=E.exampleInput(C,0),br=E.analyze(b,C),ws=W.defaultState();ws.assumptions=W.preset();const cs=G.defaultState();cs.assumptions.resources='LOW';cs.assumptions.window='ALL_READY';let g=G.evaluate(br,C,cs);assert.equal(g.scenario_valid,false);assert.equal(g.wave_constraint,'LIMIT_EXPOSURE');const constrained=G.constrainWave(br,C,ws,null,g,W);assert.equal(constrained.selected_plan_id,'CHECK_WAVE');assert.equal(constrained.state.assumptions.access,'READY');assert.equal(constrained.execution_assumptions.access,'DENIED');assert.equal(ws.assumptions.access,'READY');
ready();assert(!G.evaluate(E.analyze({...a,opponent_mode:'UNKNOWN'},C),C,s).supported);s.assumptions.window='ENEMY_R_SPENT';const x=get();assert(x.remaining_counters.some(t=>t.includes('루시안의 빛의 심판(R)')));assert(!x.remaining_counters.some(t=>t.startsWith('노틸러스의 폭뢰(R)')));
s.type='COUNTER';s.assumptions.initiator='ALLY';assert.equal(get().initiator,'ENEMY');assert(!get().reason.includes('첫 행동·진입 측 우리부터'));s.type='SHORT';s.assumptions.hit='ENEMY_HIT';assert.equal(get().wave_constraint,'LIMIT_EXPOSURE');assert(!get().actions.some(a=>a.id==='CS_WINDOW'));s.assumptions.hit='ALLY_HIT';s.milestone='FIRST_PURCHASE';s.assumptions.window='UNKNOWN';assert(!get().evidence.facts.some(f=>f.slot==='R'));
""")
if __name__=='__main__':unittest.main()

"""Wave choice semantics in hypothetical scenes; no coaching accuracy claim."""
import unittest
import tests_pregame.test_loading_strategy as legacy

class LoadingWaveTests(unittest.TestCase):
    run_node=legacy.LoadingStrategyTests.run_node
    prefix="""
assert(fs.existsSync('./web_r4/loading-wave.js'),'wave-first engine missing');
const W=require('./web_r4/loading-wave'),a=E.exampleInput(C,0),r=E.analyze(a,C),s=W.defaultState();
const ready=()=>{s.assumptions={flow:'BUILDING',access:'READY',response:'MANAGEABLE',purpose:'SPACE',crash:'UNKNOWN'};};
const get=(risk='BALANCED')=>W.evaluate({...r,input:{...r.input,preferences:{risk}}},C,s);
"""
    def test_missing_information_is_not_push_permission(self):
        self.run_node(self.prefix+"""
for(const risk of ['LOSS_LIMIT','BALANCED','OPPORTUNITY']){const x=get(risk);assert.equal(x.selected_plan_id,'CHECK_WAVE');assert.equal(x.observation,'NOT_OBSERVED');assert.equal(x.evidence.level,'DESIGN_HYPOTHESIS');assert.equal(x.first_push.status,'UNKNOWN');assert(x.first_push.reason.includes('광역'));}
ready();s.assumptions.response='UNKNOWN';assert.equal(get('OPPORTUNITY').selected_plan_id,'CHECK_WAVE');
s.assumptions.response='DISRUPTS';assert.equal(get('OPPORTUNITY').selected_plan_id,'CHECK_WAVE');
assert.throws(()=>W.evaluate(r,C,{...s,assumptions:{...s.assumptions,flow:'probably'}}));
""")
    def test_preference_compares_wave_actions_and_costs_without_fixed_push_pull(self):
        self.run_node(self.prefix+"""
ready();const loss=get('LOSS_LIMIT'),opp=get('OPPORTUNITY');assert.equal(loss.selected_plan_id,'SLOW_PUSH');assert.equal(opp.selected_plan_id,'FAST_PUSH');assert.notDeepEqual(loss.selected.steps,opp.selected.steps);assert.notDeepEqual(loss.selected.costs,opp.selected.costs);
s.assumptions.flow='INCOMING';s.assumptions.access='DENIED';for(const risk of ['LOSS_LIMIT','BALANCED','OPPORTUNITY'])assert.equal(get(risk).selected_plan_id,'TRIM_RECEIVE');
ready();s.assumptions.purpose='RESET';for(const risk of ['LOSS_LIMIT','BALANCED','OPPORTUNITY'])assert.equal(get(risk).selected_plan_id,'FAST_PUSH');
""")
    def test_fast_processing_is_not_crash_and_trim_is_not_freeze(self):
        self.run_node(self.prefix+"""
ready();s.assumptions.purpose='RESET';let x=get();assert.equal(x.selected_plan_id,'FAST_PUSH');assert.equal(x.crash_completion,'NOT_OBSERVED');assert.notEqual(x.plans.find(p=>p.id==='CRASH').feasibility,'POSSIBLE');assert(x.selected.completion.includes('완료'));
s.assumptions.crash='READY';assert.equal(get().selected_plan_id,'CRASH');assert.equal(get().crash_completion,'NOT_OBSERVED');
s.assumptions.crash='BLOCKED';assert.equal(get().selected_plan_id,'FAST_PUSH');
s.assumptions.flow='INCOMING';s.assumptions.access='DENIED';x=get();assert.equal(x.selected_plan_id,'TRIM_RECEIVE');assert.equal(x.plans.find(p=>p.id==='FREEZE').feasibility,'UNSUPPORTED');assert(x.selected.maintenance.includes('프리징'));
""")
    def test_period_does_not_force_wave_choice_and_punishment_serves_goal(self):
        self.run_node(self.prefix+"""
ready();for(const row of r.lane.rows){s.milestone=row.id;const x=get();assert.equal(x.selected_plan_id,'SLOW_PUSH');assert(x.period_note.length);for(const p of x.plans){for(const k of ['objective','start','processing','skills','maintenance','completion','failure','next','opponent_goal','conversion'])assert(p[k],p.id+' '+k);assert.equal(p.punishment.length,4);for(const q of p.punishment)for(const k of ['trigger','goal','means','reply','end','wave_effect'])assert(q[k]);}}
s.milestone='LEVEL2';const means={supported:true,selected_plan_id:'SHORT_FOLLOW'};let x=W.evaluate(r,C,s,means);assert(x.punishment_follow_allowed);s.assumptions.purpose='RESET';x=W.evaluate(r,C,s,means);assert(!x.punishment_follow_allowed);assert(x.punishment_reason.includes('처리'));assert(x.counterexamples.some(t=>t.includes('미니언')));assert(x.counterexamples.some(t=>t.includes('소모')));
""")
    def test_source_scope_and_original_question_history(self):
        self.run_node(self.prefix+"""
const original=fs.readFileSync('./evidence/actual-evidence/loading-readability/prioritized-evidence-questions.json','utf8');
const map=JSON.parse(fs.readFileSync('./evidence/actual-evidence/loading-wave/question-links.json','utf8'));assert.deepEqual(map.links.map(q=>q.question_id).sort(),['DUO-L2','DUO-L3_5','DUO-L6']);assert(map.links.every(q=>q.wave_plans.length&&q.status==='HOLD_NO_MATCHING_LECTURE_SEGMENT'));assert.equal(require('node:crypto').createHash('sha256').update(original).digest('hex'),map.original_sha256);
let b=copy(a);b.allies.find(p=>p.position==='SUPPORT').champion='Janna';let x=W.evaluate(E.analyze(b,C),C,s);assert(!x.supported);assert.equal(x.selected,null);assert.deepEqual(x.question_ids,[]);assert.equal(x.map_scenario,null);
for(const patch of [null,'16.19'])assert(!W.evaluate(E.analyze({...a,patch},C),C,s).supported);
assert(r.wave);assert(r.summary.lane_key.indexOf('웨이브')<r.summary.lane_key.indexOf('럭스'));assert(r.summary.lane_key.includes('조건'));assert.equal(r.evidence.real_coaching_n,0);
""")
    def test_subordinate_means_cannot_override_primary_wave_goal(self):
        self.run_node(self.prefix+"""
const vm=require('node:vm'),scope={window:{}};vm.runInNewContext(fs.readFileSync('./web_r4/loading-interactive.js','utf8'),scope);const gate=scope.window.LoadingInteractive.waveAllowsMeans;assert.equal(typeof gate,'function','wave compatibility gate missing');
ready();s.assumptions.purpose='RESET';s.assumptions.crash='READY';let x=get();assert.equal(gate(x,'SHORT_FOLLOW'),false);assert.equal(gate(x,'RECEIVE_WITH_LUX'),false);assert(gate(x,'PREPARE_WINDOW'));
ready();x=W.evaluate(r,C,s,{supported:true,selected_plan_id:'SHORT_FOLLOW'});assert(gate(x,'SHORT_FOLLOW'));assert(!gate(x,'RECEIVE_WITH_LUX'));
s.assumptions.flow='INCOMING';x=get();assert(gate(x,'RECEIVE_WITH_LUX'));assert(!gate(x,'SHORT_FOLLOW'));
""")

    def test_period_facts_are_required_for_period_guidance(self):
        self.run_node(self.prefix+"""
for(const [period,champ,slot] of [['LEVEL3_5','Caitlyn','E'],['LEVEL3_5','Lux','W'],['LEVEL6','Nautilus','R'],['LEVEL6','Kaisa','R']]){const c=copy(C);c.champions[champ].facts=c.champions[champ].facts.filter(f=>f.slot!==slot);s.milestone=period;const x=W.evaluate(r,c,s);assert(!x.supported,period+champ+slot+' missing');assert.equal(x.map_scenario,null);}
""")

    def test_diagrams_are_symbolic_and_map_has_no_hidden_enemy_locations(self):
        self.run_node(self.prefix+"""
ready();const x=get();assert.equal(x.diagram.observation,'HYPOTHETICAL');assert.equal(x.diagram.counts,'SYMBOLS_NOT_QUANTITIES');assert.equal(x.diagram.after,'DESIRED_NOT_PREDICTED');assert.equal(x.selected.steps.length,3);assert.deepEqual(x.map_scenario.plan.steps,x.selected.steps);assert(x.map_scenario.map.entities.every(e=>e.team==='ALLY'));assert(x.map_scenario.map.notes.some(t=>t.includes('合流')||t.includes('합류')));
const html=fs.readFileSync('./web_r4/loading.html','utf8');assert(html.includes('./loading-wave.js'));assert(html.includes('./loading-wave-view.js'));
""")
if __name__=='__main__':unittest.main()

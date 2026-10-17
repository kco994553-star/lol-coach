"""Hypothetical action selection and gates, not real-game coaching validation."""
import unittest
import tests_pregame.test_loading_strategy as legacy

class LoadingInteractiveTests(unittest.TestCase):
    run_node=legacy.LoadingStrategyTests.run_node
    def test_browser_entry_loads_real_exploration_and_interaction_modules(self):
        self.run_node("""
const html=fs.readFileSync('./web_r4/loading.html','utf8');
assert(html.includes('src="./loading-exploration.js"'),'pure exploration must be loaded');
assert(html.indexOf('src="./loading-exploration.js"')<html.indexOf('src="./loading-engine.js"'));
assert(html.includes('src="./loading-interactive.js"'));assert(html.includes('id="interactive-flow"'));assert(html.includes('id="zoom-selected-action"'),'modal needs its selected action text');
""")

    def test_legacy_input_defaults_and_preference_is_versioned(self):
        self.run_node("""
const a=E.exampleInput(C,0),r=E.analyze(a,C);assert.equal(r.input.schema_version,'lol-coach-loading-input-v2');
assert.deepEqual(r.input.preferences,{risk:'BALANCED'});assert.equal(r.exploration.preference.source,'USER_PREFERENCE');
const b={...a,schema_version:'lol-coach-loading-input-v2',preferences:{risk:'OPPORTUNITY'}};
assert.equal(E.analyze(b,C).input.preferences.risk,'OPPORTUNITY');assert.throws(()=>E.analyze({...b,preferences:{risk:99}},C));assert.throws(()=>E.analyze({...a,preferences:{risk:'BALANCED'}},C));
""")
    def test_preference_selects_actual_supported_actions_with_different_costs(self):
        self.run_node("""
assert(fs.existsSync('./web_r4/loading-exploration.js'),'exploration engine missing');const X=require('./web_r4/loading-exploration');
const a=E.exampleInput(C,0),state=X.defaultState();state.assumptions={binding:'HIT',followup:'READY',exit_cover:'AVAILABLE'};
const get=risk=>X.evaluate(E.analyze({...a,schema_version:'lol-coach-loading-input-v2',preferences:{risk}},C),C,state);
const loss=get('LOSS_LIMIT'),opp=get('OPPORTUNITY');assert.equal(loss.selected_plan_id,'RECEIVE_WITH_LUX');assert.equal(opp.selected_plan_id,'SHORT_FOLLOW');
assert.notDeepEqual(loss.plans.find(p=>p.id===loss.selected_plan_id).steps.map(s=>s.action_id),opp.plans.find(p=>p.id===opp.selected_plan_id).steps.map(s=>s.action_id));
for(const p of opp.plans){assert.equal(Object.keys(p.dimensions).length,6);assert(p.costs.length);assert(p.abort.length);assert(p.evidence_ids.length);}
assert.equal(opp.evidence.sufficiency,'CONDITIONAL');assert.equal(opp.evidence.assessment,'UNDETERMINED');assert.equal(opp.evidence.level,'DESIGN_HYPOTHESIS');
""")
    def test_unknown_and_impossible_are_not_unlocked_by_opportunity(self):
        self.run_node("""
const X=require('./web_r4/loading-exploration'),a=E.exampleInput(C,0),r=E.analyze({...a,schema_version:'lol-coach-loading-input-v2',preferences:{risk:'OPPORTUNITY'}},C);
let s=X.defaultState(),x=X.evaluate(r,C,s);assert.equal(x.selected_plan_id,'PREPARE_WINDOW');assert(x.same_choice_across_preferences);assert(x.selection_reason.includes('현재 조건에서는 선택이 같습니다'));
s.assumptions={binding:'MISS',followup:'READY',exit_cover:'AVAILABLE'};x=X.evaluate(r,C,s);assert.equal(x.selected_plan_id,'RECEIVE_WITH_LUX');assert.equal(x.plans.find(p=>p.id==='SHORT_FOLLOW').feasibility,'IMPOSSIBLE');
s.assumptions.binding='UNKNOWN';x=X.evaluate(r,C,s);assert.equal(x.plans.find(p=>p.id==='SHORT_FOLLOW').feasibility,'UNKNOWN');assert.notEqual(x.selected_plan_id,'SHORT_FOLLOW');
s.assumptions.exit_cover='BROKEN';x=X.evaluate(r,C,s);assert.equal(x.selected_plan_id,'PREPARE_WINDOW');assert(!x.map_scenario.map.entities.some(e=>e.team==='ENEMY'));
""")
    def test_one_condition_changes_actions_and_map_while_same_preference_is_retained(self):
        self.run_node("""
const X=require('./web_r4/loading-exploration'),r=E.analyze(E.exampleInput(C,0),C),s=X.defaultState();s.assumptions={binding:'HIT',followup:'READY',exit_cover:'AVAILABLE'};
const ready=X.evaluate(r,C,s);s.assumptions.binding='MISS';const miss=X.evaluate(r,C,s);assert.equal(ready.selected_plan_id,'SHORT_FOLLOW');assert.equal(miss.selected_plan_id,'RECEIVE_WITH_LUX');assert.notDeepEqual(ready.map_scenario.map.arrows,miss.map_scenario.map.arrows);
assert.equal(miss.preference.risk,ready.preference.risk);assert.deepEqual(miss.row,r.lane.rows[1]);assert(miss.required_checks.length);assert.equal(miss.assumption_status,'NOT_OBSERVED');
""")
    def test_unsupported_milestone_matchup_patch_and_missing_fact_stay_unsupported(self):
        self.run_node("""
const X=require('./web_r4/loading-exploration'),a=E.exampleInput(C,0),s=X.defaultState();
for(const id of ['LEVEL1','LEVEL3_5','LEVEL6','FIRST_PURCHASE','FIRST_CORE']){s.milestone=id;const x=X.evaluate(E.analyze(a,C),C,s);assert(!x.supported);assert.equal(x.row.id,id);assert.equal(x.map_scenario,null);assert.equal(x.selected_plan_id,null);}
s.milestone='LEVEL2';const b=copy(a);b.allies.find(p=>p.position==='SUPPORT').champion='Janna';const unrelated=X.evaluate(E.analyze(b,C),C,s);assert(!unrelated.supported);assert.equal(unrelated.evidence.question_id,null);assert(!/럭스|노틸러스|덫/.test(JSON.stringify(unrelated.evidence.counterexamples)));
for(const patch of [null,'16.19'])assert(!X.evaluate(E.analyze({...a,patch},C),C,s).supported);
const c=copy(C);c.champions.Lux.facts=c.champions.Lux.facts.filter(f=>f.slot!=='Q');assert(!X.evaluate(E.analyze(a,C),c,s).supported);
assert.throws(()=>X.evaluate(E.analyze(a,C),C,{...s,assumptions:{...s.assumptions,binding:'probably'}}));
""")
    def test_blue_red_maps_are_bound_to_exact_allied_duo_and_legacy_analysis_preserved(self):
        self.run_node("""
const X=require('./web_r4/loading-exploration'),a=E.exampleInput(C,0),s=X.defaultState();s.assumptions={binding:'HIT',followup:'READY',exit_cover:'AVAILABLE'};
const blue=X.evaluate(E.analyze(a,C),C,s),red=X.evaluate(E.analyze({...a,side:'RED'},C),C,s);
assert.deepEqual(blue.map_scenario.map.entities.map(e=>e.champion),['Caitlyn','Lux']);assert.notDeepEqual(blue.map_scenario.map.entities,red.map_scenario.map.entities);assert(red.map_scenario.map.entities.every(e=>e.start.x>60&&e.start.y>60),'red bottom lane must stay bottom, not rotate into top');
const before=E.analyze(a,C),after=E.analyze({...a,schema_version:'lol-coach-loading-input-v2',preferences:{risk:'LOSS_LIMIT'}},C);for(const key of ['summary','lane','roles','contexts','gameplan','teamfight','evidence','scenarios'])assert.deepEqual(before[key],after[key]);
""")

if __name__=='__main__':unittest.main()

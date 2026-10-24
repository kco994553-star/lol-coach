"""Fixed delivery and tri-state semantics, exercised through real reports."""
import unittest
from tests_pregame import test_gameplan_coaching_content as runner


class GameplanBackendTests(unittest.TestCase):
    node = runner.GameplanCoachingContentTests.node

    def test_three_value_conditions(self):
        self.node(r"""
const B=require('./web_r4/loading-planboard.js');
assert.equal(typeof B.evaluateCondition,'function');
const f=B.evaluateCondition;
for(const [input,expected] of [[true,'MET'],[false,'UNMET'],[null,'UNKNOWN'],[{all:[true,null]},'UNKNOWN'],[{all:[false,null]},'UNMET'],[{any:[false,null]},'UNKNOWN'],[{any:[true,null]},'MET'],[{not:null},'UNKNOWN'],[{not:false},'MET']])assert.equal(f(input),expected);
for(const invalid of [{all:[]},{any:[]},{all:Array(1)},{any:Array(1)},{all:[true],not:false},{wat:true},'false',0,undefined])assert.throws(()=>f(invalid),/INVALID_CONDITION/);
""")

    def test_delivery_is_fixed_detached_and_used_by_view(self):
        self.node(r"""
const B=require('./web_r4/loading-planboard.js'),r=E.analyze(E.exampleInput(catalog,0),catalog),b=r.coach.planboard;
assert.ok(b.delivery,'backend delivery must exist');
assert.deepEqual(Object.keys(b.delivery.phases),['lane','operations','fight']);
for(const id of ['lane','operations','fight']){
 const d=b.delivery.phases[id];assert.equal(d.actions.length,5);
 assert.deepEqual(d.paragraphs,b.coaching_explanation[id]);
 assert.deepEqual(P.project(r).cards.find(c=>c.id===id).explanation,d.paragraphs);
}
const original=JSON.stringify(b.delivery);b.coaching_explanation.lane.push('INTERNAL_ONLY');b.action_summaries.lane.items[0].text='STALE_FIELD';
assert.equal(JSON.stringify(b.delivery),original);assert(!JSON.stringify(P.project(r)).includes('INTERNAL_ONLY'));
assert.notEqual(P.project(r).cards[0].actions[0].text,'STALE_FIELD');
for(const mutate of [z=>z.action_summaries.lane.items=Array(5).fill(null),z=>z.action_summaries.lane.items[0].text='',z=>z.coaching_explanation.lane={bad:'shape'},z=>z.coaching_explanation.lane=[null],z=>z.condition_responses.lane={}]){
 const invalid=structuredClone(b);mutate(invalid);assert.throws(()=>B.buildDelivery(invalid),/INVALID_DELIVERY:lane/);
}
assert(P.project(r).cards[0].source_paths.includes('delivery.phases.lane'));
const bad=structuredClone(b);bad.action_summaries.lane.items.pop();assert.throws(()=>B.buildDelivery(bad),/ACTION_COUNT:lane/);
delete r.coach.planboard.delivery;assert(P.project(r).cards[0].explanation.includes('INTERNAL_ONLY'));
""")

    def test_patch_impact_is_partial_and_output_scoped(self):
        self.node(r"""
const B=require('./web_r4/loading-planboard.js'),b=run(E.exampleInput(catalog,0));
assert.ok(b.internal_dependencies,'dependency tree must exist');
assert.equal(b.internal_dependencies.coverage,'PARTIAL_REPORT_TRACE');
const refs=b.direction_hierarchy.lane.baseline.evidence_refs;
const impact=B.affectedOutputs(b.internal_dependencies,[refs[0]]);
assert(impact.affected.includes('delivery.phases.lane'));
assert.deepEqual(B.affectedOutputs(b.internal_dependencies,['untracked']),{coverage:'PARTIAL_REPORT_TRACE',affected:[],untracked:['untracked']});
assert.deepEqual(B.affectedOutputs(b.internal_dependencies,[refs[0],refs[0]]),impact);
assert(!JSON.stringify(P.project(E.analyze(E.exampleInput(catalog,0),catalog))).includes('PARTIAL_REPORT_TRACE'));
""")

    def test_roles_unknown_scope_and_reset_reproduce(self):
        self.node(r"""
for(const role of ['TOP','JUNGLE','MID','BOTTOM','SUPPORT']){
 const x=input(role),before=JSON.stringify(x),a=run(x),b=run(x);
 assert.ok(a.delivery);assert.deepEqual(a.delivery,b.delivery);assert.equal(JSON.stringify(x),before);
 for(const phase of Object.values(a.delivery.phases))assert.equal(phase.actions.length,5);
}
const x=E.exampleInput(catalog,0),base=run(x);x.allies[4].champion='Blitzcrank';
assert.equal(run(x).direction_hierarchy.lane.coverage,'BASELINE_ONLY');
x.allies[4].champion='Lux';assert.deepEqual(run(x).delivery,base.delivery);
""")

    def test_direction_data_validation_and_patch_boundary(self):
        self.node(r"""
const B=require('./web_r4/loading-planboard.js'),data=require('./web_r4/loading-direction-profiles.js');
const original=JSON.stringify(data),p=B.resolveDirectionProfiles(data,'Caitlyn','BOTTOM',catalog);
assert.equal(p.version,'1');assert.equal(p.phases.lane.explanation,run(E.exampleInput(catalog,0)).direction_hierarchy.lane.baseline.explanation);
assert.equal(B.resolveDirectionProfiles(data,'Garen','TOP',catalog),null);
assert.equal(B.resolveDirectionProfiles(data,'Caitlyn','TOP',catalog),null);
const mismatch=structuredClone(catalog);mismatch.source_patch='99.1.1';assert.equal(B.resolveDirectionProfiles(data,'Caitlyn','BOTTOM',mismatch),null);
const missing=structuredClone(catalog);missing.champions.Caitlyn.facts=missing.champions.Caitlyn.facts.filter(f=>f.slot!=='W');assert.equal(B.resolveDirectionProfiles(data,'Caitlyn','BOTTOM',missing),null);
for(const mutate of [d=>d.schema_version='bad',d=>d.version='',d=>d.champions.Caitlyn.phases.lane.keys=['X'],d=>d.champions.Caitlyn.phases.lane.explanation='{X}',d=>delete d.champions.Caitlyn.phases.fight,d=>d.champions.Caitlyn.phases.extra={},d=>d.champions.Caitlyn.phases.lane.gain='']){
 const bad=structuredClone(data);mutate(bad);assert.throws(()=>B.resolveDirectionProfiles(bad,'Caitlyn','BOTTOM',catalog),/INVALID_DIRECTION_DATA/);
}
p.phases.lane.gain='mutated';assert.equal(JSON.stringify(data),original);
const baseline=run(E.exampleInput(catalog,0)).internal_dependencies.phases[0].nodes.find(n=>n.kind==='baseline');assert.equal(baseline.source_path,'web_r4/loading-direction-profiles.js');assert.equal(baseline.data_version,'1');
""")

    def test_direction_browser_module_and_script_order(self):
        self.node(r"""
const fs=require('node:fs'),vm=require('node:vm'),ctx=vm.createContext({});
vm.runInContext(fs.readFileSync('web_r4/loading-direction-profiles.js','utf8'),ctx);
vm.runInContext(fs.readFileSync('web_r4/loading-planboard.js','utf8'),ctx);
assert.equal(ctx.LoadingPlanboard.resolveDirectionProfiles(ctx.LoadingDirectionProfiles,'Ezreal','BOTTOM',catalog).version,'1');
for(const file of ['loading.html','directions.html']){const html=fs.readFileSync('web_r4/'+file,'utf8');assert(html.indexOf('loading-direction-profiles.js')>=0);assert(html.indexOf('loading-direction-profiles.js')<html.indexOf('loading-planboard.js'));}
""")

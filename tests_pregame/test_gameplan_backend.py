"""Fixed delivery and tri-state semantics, exercised through real reports."""
import unittest
from tests_pregame import test_gameplan_coaching_content as runner


class GameplanBackendTests(unittest.TestCase):
    node = runner.GameplanCoachingContentTests.node

    def test_general_plan_is_not_disguised_as_individual_tactics(self):
        self.node(r"""
let draft=E.exampleInput(catalog,0);draft.own_champion='Ornn';draft.own_position='TOP';
let r=E.analyze(draft,catalog),v=P.project(r,{currentOnly:true});
assert(v.cards.every(a=>a.coverage?.status==='GENERAL_ONLY'));
assert(v.cards.every(a=>a.tags.length===1&&a.tags[0].kind==='STATUS'));
assert(v.cards.every(a=>!a.tags.some(t=>t.kind==='ACTION')));
draft=E.exampleInput(catalog,0);draft.allies.find(x=>x.position==='BOTTOM').champion='Ezreal';draft.allies.find(x=>x.position==='SUPPORT').champion='Braum';draft.own_champion='Ezreal';
r=E.analyze(draft,catalog);v=P.project(r,{currentOnly:true});
assert(v.cards.every(a=>a.coverage?.status==='BASELINE_ONLY'));
assert(v.cards.every(a=>a.tags.every(t=>t.kind==='STATUS')));
""")

    def test_tags_follow_final_actions_and_suppress_stale_role_labels(self):
        self.node(r"""
const B=require('./web_r4/loading-planboard.js');let r=E.analyze(E.exampleInput(catalog,0),catalog),b=r.coach.planboard;
assert(b.delivery.phases.lane.tags?.some(t=>t.kind==='ACTION'));
assert(b.delivery.phases.fight.tags?.some(t=>t.label==='앞라인 공격'));
const before=JSON.stringify(P.project(r).cards.map(a=>a.tags));r.roles.proposed.id='PROTECT';b.wave.plan_id='TOWER_CS';
assert.equal(JSON.stringify(P.project(r).cards.map(a=>a.tags)),before);
const negated=structuredClone(b);negated.action_summaries.operations.items[2].text='상대를 사이드에 묶으려 하지 않는다.';
assert(!B.buildDelivery(negated).phases.operations.tags.some(t=>t.kind==='ACTION'));
const draft=E.exampleInput(catalog,0);draft.schema_version='lol-coach-loading-input-v4';draft.preferences={risk:'BALANCED'};draft.scenario={standard:'lane-standard-v1',overrides:{}};draft.planning={basis:'loading-plan-example-v1',overrides:{income:'LOSING',opportunity:'MISSED'}};
r=E.analyze(draft,catalog);const lane=r.coach.planboard.delivery.phases.lane;
assert(lane.tags.some(t=>t.label==='추격 중단'));
assert(!lane.tags.some(t=>/견제|밀기|교환/.test(t.label)));
for(const a of Object.values(r.coach.planboard.delivery.phases)){
 assert(a.tags.length<=3);assert(a.tags.filter(t=>t.kind==='ACTION').length<=1);
 assert(a.tags.every(t=>t.source_paths.length&&t.label.length<=18));
}
""")

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
assert.equal(p.version,data.version);assert.equal(p.phases.lane.explanation,run(E.exampleInput(catalog,0)).direction_hierarchy.lane.baseline.explanation);
assert.equal(B.resolveDirectionProfiles(data,'Garen','TOP',catalog),null);
assert.equal(B.resolveDirectionProfiles(data,'Caitlyn','TOP',catalog),null);
const mismatch=structuredClone(catalog);mismatch.source_patch='99.1.1';assert.equal(B.resolveDirectionProfiles(data,'Caitlyn','BOTTOM',mismatch),null);
const missing=structuredClone(catalog);missing.champions.Caitlyn.facts=missing.champions.Caitlyn.facts.filter(f=>f.slot!=='W');assert.equal(B.resolveDirectionProfiles(data,'Caitlyn','BOTTOM',missing),null);
for(const mutate of [d=>d.schema_version='bad',d=>d.version='',d=>d.champions.Caitlyn.phases.lane.keys=['X'],d=>d.champions.Caitlyn.phases.lane.explanation='{X}',d=>delete d.champions.Caitlyn.phases.fight,d=>d.champions.Caitlyn.phases.extra={},d=>d.champions.Caitlyn.phases.lane.gain='']){
 const bad=structuredClone(data);mutate(bad);assert.throws(()=>B.resolveDirectionProfiles(bad,'Caitlyn','BOTTOM',catalog),/INVALID_DIRECTION_DATA/);
}
p.phases.lane.gain='mutated';assert.equal(JSON.stringify(data),original);
const baseline=run(E.exampleInput(catalog,0)).internal_dependencies.phases[0].nodes.find(n=>n.kind==='baseline');assert.equal(baseline.source_path,'web_r4/loading-direction-profiles.js');assert.equal(baseline.data_version,data.version);
""")

    def test_direction_browser_module_and_script_order(self):
        self.node(r"""
const fs=require('node:fs'),vm=require('node:vm'),ctx=vm.createContext({});
vm.runInContext(fs.readFileSync('web_r4/loading-direction-profiles.js','utf8'),ctx);
vm.runInContext(fs.readFileSync('web_r4/loading-planboard.js','utf8'),ctx);
assert.equal(ctx.LoadingPlanboard.resolveDirectionProfiles(ctx.LoadingDirectionProfiles,'Ezreal','BOTTOM',catalog).version,ctx.LoadingDirectionProfiles.version);
for(const file of ['loading.html','directions.html']){const html=fs.readFileSync('web_r4/'+file,'utf8');assert(html.indexOf('loading-direction-profiles.js')>=0);assert(html.indexOf('loading-direction-profiles.js')<html.indexOf('loading-planboard.js'));}
""")

    def test_scoped_conditions_and_rule_audit(self):
        self.node(r"""
const B=require('./web_r4/loading-planboard.js');
assert.equal(typeof B.evaluateScopedCondition,'function');
const scope={subject:'allies:Caitlyn',phase:'lane',snapshot:'pregame:1'};
const c={id:'followup',value:true,...scope,source:{kind:'ASSUMPTION',ref:'planning.followup'}};
const before=JSON.stringify(c);
assert.equal(B.evaluateScopedCondition(c,scope).state,'MET');
for(const key of ['subject','phase','snapshot'])assert.equal(B.evaluateScopedCondition({...c,[key]:'different'},scope).state,'UNKNOWN');
assert.equal(B.evaluateScopedCondition({...c,source:null},scope).state,'UNKNOWN');
assert.equal(B.evaluateScopedCondition({...c,value:null},scope).state,'UNKNOWN');
assert.equal(B.evaluateScopedCondition({...c,value:false},scope).state,'UNMET');
assert.throws(()=>B.evaluateScopedCondition({...c,value:'true'},scope),/INVALID_SCOPED_CONDITION/);
assert.equal(JSON.stringify(c),before);
const rule={id:'followup-rule',version:'1',requires:[c],excludes:[]};
assert.equal(B.evaluateRule(rule,scope).status,'APPLIED');
assert.equal(B.evaluateRule({...rule,requires:[{...c,value:false}]},scope).status,'EXCLUDED');
assert.equal(B.evaluateRule({...rule,excludes:[{...c,id:'risk',value:null}]},scope).status,'CONDITIONAL');
assert.equal(B.evaluateRule({...rule,excludes:[{...c,id:'risk'}]},scope).status,'EXCLUDED');
for(const requires of [[],Array(1),[c,c]])assert.throws(()=>B.evaluateRule({...rule,requires},scope),/INVALID_RULE/);
assert.deepEqual(B.evaluateRule(rule,scope),B.evaluateRule(rule,scope));
""")

    def test_direction_rule_audit_integrates_without_new_output(self):
        self.node(r"""
const B=require('./web_r4/loading-planboard.js'),x=E.exampleInput(catalog,0),b=run(x);
assert.ok(b.internal_rule_trace);
assert.equal(b.internal_rule_trace.coverage,'DIRECTION_ELIGIBILITY_ONLY');
assert.equal(b.internal_rule_trace.rules.length,3);
assert(b.internal_rule_trace.rules.every(r=>r.status==='APPLIED'));
assert(!JSON.stringify(b.delivery).includes('DIRECTION_ELIGIBILITY_ONLY'));
assert.deepEqual(b.delivery,B.buildDelivery(b));
const other=run(input('MID'));assert(other.internal_rule_trace.rules.every(r=>r.status==='EXCLUDED'));
assert.deepEqual(run(E.exampleInput(catalog,0)).internal_rule_trace,b.internal_rule_trace);
""")

    def test_trace_rejects_report_patch_mismatch_and_preserves_original_scope(self):
        self.node(r"""
const B=require('./web_r4/loading-planboard.js'),x=E.exampleInput(catalog,0);
x.patch='1.1';const b=run(x);
assert(!b.direction_hierarchy);
assert(b.internal_rule_trace.rules.every(r=>r.status==='EXCLUDED'));
const scope={subject:'allies:Caitlyn',phase:'lane',snapshot:'pregame:1'};
const c={id:'state',value:true,subject:'enemies:Caitlyn',phase:'fight',snapshot:'old',source:{kind:'ASSUMPTION',ref:'scenario'}};
const trace=B.evaluateScopedCondition(c,scope);
assert.equal(trace.value,true);assert.deepEqual(trace.actual_scope,{subject:c.subject,phase:c.phase,snapshot:c.snapshot});
assert.deepEqual(trace.expected_scope,scope);
""")

    def test_candidate_comparison_abstains_on_conflict_or_missing_information(self):
        self.node(r"""
const B=require('./web_r4/loading-planboard.js');assert.equal(typeof B.resolveCandidates,'function');
const scope={subject:'allies:Caitlyn',phase:'lane',snapshot:'one'};
const make=(id,value,conflicts=[])=>({id,conflicts_with:conflicts,rule:{id:'rule:'+id,version:'1',requires:[{id:'eligible',value,...scope,source:{kind:'ASSUMPTION',ref:'test'}}],excludes:[]}});
const resolve=xs=>B.resolveCandidates(xs,scope);
assert.equal(resolve([make('fight',true),make('wait',false)]).selected,'fight');
for(const value of [true,null]){const r=resolve([make('fight',true),make('wait',value)]);assert.equal(r.selected,null);assert.equal(r.status,'UNRESOLVED');}
assert.equal(resolve([make('fight',false)]).status,'NO_ELIGIBLE_CANDIDATE');
const xs=[make('fight',true,['wait']),make('wait',true)],before=JSON.stringify(xs),r=resolve(xs);
assert.equal(r.status,'CONFLICT');assert.equal(r.selected,null);assert.deepEqual(r.conflicts,[{candidates:['fight','wait'],status:'CONFIRMED'}]);
assert.deepEqual(resolve([...xs].reverse()),r);assert.equal(JSON.stringify(xs),before);
assert.equal(resolve([make('fight',true,['wait']),make('wait',null)]).conflicts[0].status,'POSSIBLE');
assert.equal(resolve([make('fight',true,['wait']),make('wait',false)]).selected,'fight');
for(const bad of [[],Array(1),[make('a',true),make('a',false)],[make('a',true,['missing'])],[make('a',true,['a'])],[make('a',true,Array(1))]])assert.throws(()=>resolve(bad),/INVALID_CANDIDATES/);
""")

    def test_waiting_candidates_are_integrated_and_keep_unknown_explicit(self):
        self.node(r"""
const x=E.exampleInput(catalog,0);
x.schema_version='lol-coach-loading-input-v4';x.preferences={risk:'BALANCED'};x.scenario={standard:'lane-standard-v1',overrides:{}};
x.planning={basis:'loading-plan-example-v1',overrides:{income:'LOSING',opportunity:'AVAILABLE',ally_followup:'AVAILABLE'}};
let b=run(x);assert.ok(b.internal_candidate_comparison);assert.equal(b.internal_candidate_comparison.selected,'CREATE_WINDOW');assert.equal(b.engagement_decision.state,'CREATE_WINDOW');
x.planning.overrides.ally_followup='UNAVAILABLE';b=run(x);assert.equal(b.internal_candidate_comparison.selected,'PREPARE_CONDITIONS');
x.planning.overrides.opportunity='MISSED';b=run(x);assert.equal(b.internal_candidate_comparison.selected,'OPPORTUNITY_MISSED');
x.patch='1.1';b=run(x);assert.equal(b.internal_candidate_comparison.selected,'SOURCE_REVIEW_REQUIRED');
assert(!JSON.stringify(b.delivery).includes('internal_candidate_comparison'));
""")

    def test_effect_comparison_requires_matching_scope_and_preserves_tradeoffs(self):
        self.node(r"""
const B=require('./web_r4/loading-planboard.js');assert.equal(typeof B.compareEffects,'function');
const scope={subject:'allies:Caitlyn',phase:'lane',snapshot:'one'};
const effect=(id,dimension,impact)=>({id,dimension,measure:'qualitative-direction',horizon:'next-wave',category:'GOAL_GAIN',impact,...scope,source:{kind:'ASSUMPTION',ref:'fixture:'+id,version:'1'}});
const a=[effect('a','income','BENEFIT'),effect('b','health','LOSS')],b=[effect('c','income','UNCHANGED'),effect('d','health','UNCHANGED')];
const before=JSON.stringify(a);
assert.equal(B.compareEffects(a,b,scope).status,'TRADEOFF');
assert.equal(B.compareEffects([a[0]],[b[0]],scope).status,'LEFT_DOMINATES_DECLARED_EFFECTS');
assert.equal(B.compareEffects(b,b,scope).status,'EQUAL_DECLARED_EFFECTS');
for(const change of [e=>e.snapshot='old',e=>e.subject='allies:Lux',e=>e.horizon='later',e=>e.measure='other',e=>e.impact='UNKNOWN',e=>delete e.source,e=>delete e.source.version,e=>e.source.kind='KNOWLEDGE']){
 const other=structuredClone(b);change(other[0]);const r=B.compareEffects(a,other,scope);assert.equal(r.status,'INCOMPARABLE');assert(r.reasons.length);
}
assert.equal(B.compareEffects(a,[b[0]],scope).status,'INCOMPARABLE');
assert.equal(B.compareEffects([],[],scope).status,'INCOMPARABLE');
assert.equal(JSON.stringify(a),before);
assert.deepEqual(B.compareEffects([...a].reverse(),[...b].reverse(),scope),B.compareEffects(a,b,scope));
for(const bad of [Array(1),[null],[{...a[0],impact:10}],[a[0],{...a[0],id:'duplicate-coordinate'}]])assert.throws(()=>B.compareEffects(bad,b,scope),/INVALID_EFFECTS/);
""")

    def test_waiting_effects_are_assumptions_and_do_not_turn_loss_into_a_fight(self):
        self.node(r"""
const B=require('./web_r4/loading-planboard.js'),x=E.exampleInput(catalog,0);
x.schema_version='lol-coach-loading-input-v4';x.preferences={risk:'BALANCED'};x.scenario={standard:'lane-standard-v1',overrides:{resources:'LOW'}};
x.planning={basis:'loading-plan-example-v1',overrides:{income:'LOSING',opportunity:'AVAILABLE',ally_followup:'AVAILABLE'}};
let b=run(x),c=b.internal_candidate_comparison;
assert.ok(c.effects,'waiting comparison must retain the underlying noncombat cost evidence');
assert.equal(c.effects.waiting_loss[0].impact,'LOSS');assert.equal(c.effects.waiting_loss[0].source.kind,'ASSUMPTION');
assert.equal(c.effects.action_cost[0].impact,'UNKNOWN');assert.equal(c.effects.goal_gain[0].impact,'UNKNOWN');
assert.equal(c.selected,'PREPARE_CONDITIONS');assert.equal(c.selection_basis,'POLICY_ELIGIBILITY_ONLY');
assert.equal(c.effect_comparison.status,'INCOMPARABLE');
assert(c.candidates.filter(c=>c.evaluation.status==='EXCLUDED').every(c=>c.exclusion_reasons.length));
assert(B.affectedOutputs(b.dependency_tree||B.dependencyTree(b),['waiting-necessity-feasibility-v1']).affected.includes('delivery.phases.lane'));
assert(!JSON.stringify(b.delivery).includes('qualitative-direction'));
x.planning.overrides.income='NORMAL';b=run(x);assert.equal(b.internal_candidate_comparison.effects.waiting_loss[0].impact,'UNCHANGED');
x.planning.overrides.income='UNKNOWN';b=run(x);assert.equal(b.internal_candidate_comparison.effects.waiting_loss[0].impact,'UNKNOWN');
""")

    def test_versioned_snapshots_compare_delivery_without_claiming_causality(self):
        self.node(r"""
const B=require('./web_r4/loading-planboard.js');assert.equal(typeof B.createPlanSnapshot,'function');assert.equal(typeof B.comparePlanSnapshots,'function');
const x=E.exampleInput(catalog,0),board=run(x),before=B.createPlanSnapshot(board,x);
assert(Object.isFrozen(before));assert(Object.isFrozen(before.delivery.phases.lane.actions));
const changed=structuredClone(board),nextInput=structuredClone(x);
changed.delivery.phases.operations.paragraphs.push('Changed operation explanation.');nextInput.own_champion='Ezreal';
const after=B.createPlanSnapshot(changed,nextInput),diff=B.comparePlanSnapshots(before,after);
assert.deepEqual(diff.changed_phases,['operations']);assert.deepEqual(diff.changed_inputs,['input.own_champion']);
assert(diff.changed_output_paths.some(p=>p.startsWith('delivery.phases.operations.paragraphs')));
assert.equal(diff.causality,'NOT_INFERRED');
assert.deepEqual(B.comparePlanSnapshots(before,B.createPlanSnapshot(board,x)).changed_output_paths,[]);
board.delivery.phases.lane.paragraphs.push('Later mutation');x.own_champion='Lux';
assert(!JSON.stringify(before).includes('Later mutation'));assert.notEqual(before.input.own_champion,'Lux');
const versionOnly=structuredClone(after);versionOnly.versions.rules='next';
assert(B.comparePlanSnapshots(after,versionOnly).changed_versions.includes('versions.rules'));
assert.deepEqual(B.comparePlanSnapshots(after,versionOnly).changed_phases,[]);
assert.throws(()=>B.comparePlanSnapshots({},after),/INVALID_PLAN_SNAPSHOT/);
""")

    def test_candidate_effects_never_override_eligibility_or_resolve_tradeoffs(self):
        self.node(r"""
const B=require('./web_r4/loading-planboard.js'),scope={subject:'allies:Caitlyn',phase:'lane',snapshot:'one'};
const make=(id,eligible,impact)=>({id,conflicts_with:[],rule:{id:'rule:'+id,version:'1',requires:[{id:'ready',value:eligible,...scope,source:{kind:'ASSUMPTION',ref:'fixture'}}],excludes:[]},effects:[{id:'effect:'+id,dimension:'income',measure:'qualitative-direction',horizon:'next-wave',category:'GOAL_GAIN',impact,...scope,source:{kind:'ASSUMPTION',ref:'fixture',version:'1'}}]});
let r=B.resolveCandidates([make('advance',true,'BENEFIT'),make('wait',true,'UNCHANGED')],scope);
assert.ok(r.effect_comparisons);assert.equal(r.effect_comparisons[0].comparison.status,'LEFT_DOMINATES_DECLARED_EFFECTS');assert.equal(r.selected,null);
r=B.resolveCandidates([make('advance',false,'BENEFIT'),make('wait',true,'UNKNOWN')],scope);assert.equal(r.selected,'wait');assert.deepEqual(r.effect_comparisons,[]);
const a=make('a',true,'BENEFIT'),b=make('b',true,'LOSS');b.effects[0].source.version='2';
assert.equal(B.compareEffects(a.effects,b.effects,scope).status,'INCOMPARABLE');
""")

    def test_snapshots_reject_malformed_or_lossy_payloads(self):
        self.node(r"""
const B=require('./web_r4/loading-planboard.js'),x=E.exampleInput(catalog,0),b=run(x),good=B.createPlanSnapshot(b,x);
for(const edit of [s=>s.input=true,s=>s.versions=true,s=>s.delivery.schema_version='wrong',s=>s.delivery.phases.lane=true,s=>s.delivery.phases.lane.actions.pop(),s=>s.delivery.phases.lane.paragraphs=[undefined],s=>s.delivery.phases.fight.details=[{trigger:'x',action:42}]]){
 const bad=structuredClone(good);edit(bad);assert.throws(()=>B.comparePlanSnapshots(bad,good),/INVALID_PLAN_SNAPSHOT/);
}
for(const bad of [{value:NaN},{value:undefined},{value:Infinity},{value:()=>1},{value:Array(1)},{toJSON(){return {}}},new Date()])assert.throws(()=>B.createPlanSnapshot(b,bad),/INVALID_PLAN_SNAPSHOT/);
const cycle={};cycle.self=cycle;assert.throws(()=>B.createPlanSnapshot(b,cycle),/INVALID_PLAN_SNAPSHOT/);
assert.throws(()=>B.createPlanSnapshot({delivery:{schema_version:'wrong',phases:{lane:'bad'}}},{}),/INVALID_PLAN_SNAPSHOT/);
const scope={subject:'self',phase:'lane',snapshot:'one'},e={id:'x',dimension:'income',measure:'sign',horizon:'wave',category:'GOAL_GAIN',impact:'BENEFIT',...scope,source:{kind:'ASSUMPTION',ref:'x',version:'1'},magnitude:999};
assert.throws(()=>B.compareEffects([e],[e],scope),/INVALID_EFFECTS/);
""")

    def test_effect_provenance_cannot_disappear_during_copy(self):
        self.node(r"""
const B=require('./web_r4/loading-planboard.js'),scope={subject:'self',phase:'lane',snapshot:'one'};
const e={id:'x',dimension:'income',measure:'sign',horizon:'wave',category:'GOAL_GAIN',impact:'BENEFIT',...scope,source:Object.create({kind:'ASSUMPTION',ref:'fixture',version:'1'})};
assert.throws(()=>B.compareEffects([e],[e],scope),/INVALID_EFFECTS/);
e.source={kind:'ASSUMPTION',ref:'fixture',version:'1',toJSON(){return {}}};assert.throws(()=>B.compareEffects([e],[e],scope),/INVALID_EFFECTS/);
""")

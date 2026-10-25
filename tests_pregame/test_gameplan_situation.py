"""GP23 provenance, feasible choices and role goals through the production report.

Wrong branches caught: stale/as-observed current promotion; impossible pulling;
blanket near-jungle retreat; unsupported dive; divergent headline/actions/tags.
"""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRELUDE = r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
assert(fs.existsSync('./web_r4/loading-situation.js'),'Missing typed situation boundary');
const S=require('./web_r4/loading-situation.js'),E=require('./web_r4/loading-engine.js'),C=require('./web_r4/loading-coach.js');
const catalog=JSON.parse(fs.readFileSync('./web_r4/loading-data.json'));
catalog.coaching_knowledge=JSON.parse(fs.readFileSync('./web_r4/loading-knowledge.json'));
const assumed=value=>({status:'assumed',value,source:'user-scenario',observed_at:null});
function input(values={},role='BOTTOM',index=0){const x=E.exampleInput(catalog,index);x.own_position=role;x.own_champion=x.allies.find(p=>p.position===role).champion;
 return {...x,schema_version:'lol-coach-loading-input-v5',preferences:{risk:'BALANCED'},scenario:{standard:'lane-standard-v1',overrides:{}},planning:{basis:'loading-plan-example-v1',overrides:{}},situation:{...S.defaultState(),fields:{...S.defaultState().fields,...Object.fromEntries(Object.entries(values).map(([k,v])=>[k,assumed(v)]))}}};}
const run=x=>E.analyze(x,catalog).coach.planboard;
const ready={wave_direction:'BUILDING',wave_size:'NORMAL',wave_access:'READY',resources:'SUFFICIENT',ally_followup:'AVAILABLE'};
const fightReady={resources:'SUFFICIENT',ally_followup:'AVAILABLE',combat_context:'TEAMFIGHT',ally_contribution:'READY',enemy_contribution:'READY',arrival_order:'EVEN',combat_space:'OPEN',key_skill:'AVAILABLE',threat_reach:'REACHABLE'};
"""

class GameplanSituationTests(unittest.TestCase):
    def node(self, body):
        p = subprocess.run(['node', '-e', PRELUDE + body], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr[-6000:])

    def test_provenance_serialization_and_no_live_observation(self):
        self.node(r"""
const initial=S.defaultState(),before=JSON.stringify(initial);assert.deepEqual(S.validate(initial),initial);
assert.equal(S.effective(initial.fields.enemy_jungle),null);assert.equal(JSON.stringify(initial),before);
const x=input({enemy_jungle:'AWAY'});assert.equal(S.effective(x.situation.fields.enemy_jungle),'AWAY');
assert.deepEqual(S.validate(JSON.parse(JSON.stringify(x.situation))),x.situation);
const observed={status:'observed',value:'AWAY',source:'replay frame 123',observed_at:'2026-10-20T10:00:00Z'};
x.situation.fields.enemy_jungle=observed;assert.throws(()=>S.validate(x.situation),/SITUATION/);
x.situation.mode='REVIEW';assert.equal(S.effective(S.validate(x.situation).fields.enemy_jungle),null);
assert.equal(S.project(x.situation).live_coaching_enabled,false);assert.match(S.project(x.situation).label,/과거|복기/);
x.situation.fields.enemy_jungle={...observed,source:null};assert.throws(()=>S.validate(x.situation),/SITUATION/);
x.situation.fields.enemy_jungle={...observed,observed_at:'yesterday'};assert.throws(()=>S.validate(x.situation),/SITUATION/);
x.situation.fields.enemy_jungle={...observed,status:'stale'};assert.equal(S.effective(S.validate(x.situation).fields.enemy_jungle),null);
const unknown=S.defaultState();unknown.fields.enemy_jungle.value='AWAY';assert.throws(()=>S.validate(unknown),/SITUATION/);
assert.throws(()=>S.validate({...S.defaultState(),extra:true}),/SITUATION/);
""")

    def test_v5_strict_and_legacy_versions_unchanged(self):
        self.node(r"""
const old=E.exampleInput(catalog);assert.equal(run(old).gp23,undefined);assert.equal(run(old).wave.plan_id,'ACQUIRE_PUSH');
for(const version of [2,3,4]){const x={...old,schema_version:'lol-coach-loading-input-v'+version,preferences:{risk:'BALANCED'}};
 if(version>=3)x.scenario={standard:'lane-standard-v1',overrides:{}};if(version>=4)x.planning={basis:'loading-plan-example-v1',overrides:{}};
 assert.equal(run(x).gp23,undefined);assert.throws(()=>run({...x,situation:S.defaultState()}));}
const x=input(),saved=JSON.stringify(x),b=run(x);assert.equal(JSON.stringify(x),saved);assert.equal(b.gp23.schema_version,'gameplan-2plus3-v1');
assert.throws(()=>run({...x,extra:true}));const missing=structuredClone(x);delete missing.situation;assert.throws(()=>run(missing));
assert.deepEqual(Object.keys(b.gp23.top),['teams','user']);assert.equal(b.gp23.top.user.baseline_scope,'COMPOSITION_DEFAULT_NOT_CURRENT_ACTION');
for(const phase of ['lane','operations','fight']){const d=b.gp23.phases[phase];assert.equal(d.actions.length,5);assert(d.tags.length<=2);assert(d.paragraphs.length>=2);assert(d.goal&&d.action&&d.stop&&d.position);assert.deepEqual(b.delivery.phases[phase].actions,d.actions);assert.equal(b.delivery.phases[phase].headline,d.action);}
""")

    def test_unknown_and_stale_never_unlock_push_or_old_pressure_tags(self):
        self.node(r"""
let x=input(),b=run(x);assert.equal(b.gp23.phases.lane.decision_id,'CHECK_WAVE');assert(!b.gp23.phases.lane.tags.some(t=>/푸시|압박/.test(t.label)));
assert(!b.gp23.phases.lane.actions.some(a=>/처리 우위를 만든다|견제해 카이사의 막타를 방해/.test(a.text)));
x=input({...ready,enemy_jungle:'AWAY'});x.situation.mode='REVIEW';x.situation.fields.enemy_jungle={status:'stale',value:'AWAY',source:'replay',observed_at:'2026-10-20T10:00:00Z'};
b=run(x);assert.equal(b.gp23.information.fields.enemy_jungle.effective,null);assert(b.gp23.phases.lane.uncertainties.some(v=>/정글/.test(v)));assert.equal(b.gp23.live_coaching_enabled,false);
const reset=run(input());assert.deepEqual(reset.gp23,run(input()).gp23);assert(!JSON.stringify(reset.gp23.source_states).includes('replay'));
""")

    def test_wave_feasibility_precedes_cost_and_jungle_location(self):
        self.node(r"""
let b=run(input({...ready,enemy_jungle:'AWAY',resources:'LOW'}));assert.equal(b.gp23.phases.lane.decision_id,'RECEIVE_LIMITED');assert(!['TRIM_RECEIVE','FREEZE'].includes(b.wave.plan_id));
b=run(input({...ready,enemy_jungle:'AWAY',wave_access:'DENIED'}));assert.equal(b.gp23.phases.lane.decision_id,'RECEIVE_LIMITED');
b=run(input({...ready,enemy_jungle:'NEAR',wave_direction:'INCOMING',wave_size:'LARGE'}));assert.equal(b.gp23.phases.lane.decision_id,'TRIM_RECEIVE');assert.match(b.gp23.phases.lane.reason,/다이브|누적/);assert(b.gp23.phases.lane.costs.length);
b=run(input({...ready,enemy_jungle:'NEAR',wave_direction:'UNDER_TOWER',wave_size:'LARGE',wave_access:'DENIED'}));assert.equal(b.gp23.phases.lane.decision_id,'RECEIVE_LIMITED');assert.match(b.gp23.phases.lane.stop,/다이브|수급|경험치/);
for(const direction of ['EVEN','BUILDING']){b=run(input({...ready,wave_direction:direction}));assert(!['TRIM_RECEIVE','FREEZE'].includes(b.wave.plan_id));}
""")

    def test_reset_and_waiting_cost_do_not_invent_crash_or_block_all_actions(self):
        self.node(r"""
let x=input({...ready,enemy_jungle:'NEAR',wave_crash:'READY'});x.planning.overrides={goal:'RECALL',income:'LOSING',opportunity:'AVAILABLE'};
let b=run(x);assert.equal(b.gp23.phases.lane.decision_id,'CRASH');assert.match(b.gp23.phases.lane.action,/밀어 넣|포탑/);assert.equal(b.gp23.phases.lane.completed,false);
x.situation.fields.wave_crash=assumed('BLOCKED');b=run(x);assert.notEqual(b.gp23.phases.lane.decision_id,'CRASH');assert.match(b.gp23.phases.lane.stop,/포탑|도달|귀환/);
x=input({...ready,ally_followup:'UNAVAILABLE'});b=run(x);assert.equal(b.gp23.phases.lane.decision_id,'RECEIVE_LIMITED');assert.equal(b.delivery.phases.lane.headline,b.gp23.phases.lane.action);assert(!b.delivery.phases.lane.tags.some(t=>/압박|진입/.test(t.label)));
x=input(ready);x.patch=null;b=run(x);assert.equal(b.gp23.phases.lane.decision_id,'CHECK_WAVE');assert.equal(b.gp23.phases.fight.coverage.status,'GENERAL_ONLY');
""")

    def test_jungler_actions_are_not_self_lane_manipulation(self):
        self.node(r"""
const x=input({...ready,enemy_jungle:'NEAR'},'JUNGLE'),b=run(x),p=b.gp23.phases.lane;
assert.equal(p.label,'초반 정글');assert.equal(b.gp23.phases.operations.label,'중반 운영');assert.match(p.goal,/캠프|지원/);
assert(!p.actions.some(a=>/내 웨이브|내 막타|프리징/.test(a.text)));assert.match(p.stop,/호응|지원|도착/);
x.situation.fields.ally_followup=assumed('UNAVAILABLE');assert.equal(run(x).gp23.phases.lane.decision_id,'JUNGLE_PREPARE');
""")

    def test_tank_disruption_and_protection_are_real_goal_conflict(self):
        self.node(r"""
let x=input({...fightReady,ally_carry_risk:'COVERED',enemy_carry_access:'DISRUPTABLE'},'TOP'),b=run(x),f=b.gp23.phases.fight;
assert.equal(f.goal_id,'DISRUPT_ENEMY_CARRY');assert(f.evidence_ids.includes('official:Ornn:R')||f.evidence_ids.includes('official:Ornn:E'));assert.match(f.action,/공격.*끊|방해|딜로스/);
x.situation.fields.ally_carry_risk=assumed('THREATENED');f=run(x).gp23.phases.fight;assert.equal(f.goal_id,'PROTECT_ALLY');assert.match(f.stop,/후속|보호|진입/);
x.situation.fields.ally_followup=assumed('UNAVAILABLE');f=run(x).gp23.phases.fight;assert.notEqual(f.goal_id,'DISRUPT_ENEMY_CARRY');
x=input({...fightReady,ally_carry_risk:'COVERED',enemy_carry_access:'DISRUPTABLE'},'TOP');const missing=structuredClone(catalog);missing.champions.Ornn.facts=[];
// Generic engine expects Q/E/R facts; retain descriptive facts but remove control mechanisms.
missing.champions.Ornn.facts=catalog.champions.Ornn.facts.map(v=>({...v,text:'효과 미확인'}));f=E.analyze(x,missing).coach.planboard.gp23.phases.fight;assert.notEqual(f.goal_id,'DISRUPT_ENEMY_CARRY');
""")

    def test_combat_contribution_arrival_unknown_skills_and_terrain_gate_entry(self):
        self.node(r"""
for(const context of ['DUEL','DUO','GANK','COUNTERGANK','RIVER_JUNGLE','PICK_CHASE','OBJECTIVE','TEAMFIGHT']){
const x=input({...fightReady,combat_context:context}),f=run(x).gp23.phases.fight;assert.equal(f.context,context);assert.equal(f.advantage,'UNDETERMINED');assert.equal(f.probability,null);assert(f.threats.length<=2);}
let x=input({...fightReady,ally_contribution:'UNAVAILABLE'},'TOP'),f=run(x).gp23.phases.fight;assert.equal(f.execution,'BLOCKED');assert.notEqual(f.goal_id,'DISRUPT_ENEMY_CARRY');
x=input({...fightReady,arrival_order:'ENEMY_FIRST'},'TOP');assert.notEqual(run(x).gp23.phases.fight.execution,'READY');
x=input({...fightReady,combat_space:'RESTRICTED'},'TOP');assert.notEqual(run(x).gp23.phases.fight.execution,'READY');
x=input({...fightReady,ally_carry_risk:'COVERED',enemy_carry_access:'DISRUPTABLE'},'TOP');x.situation.fields.key_skill=S.defaultState().fields.key_skill;assert.notEqual(run(x).gp23.phases.fight.goal_id,'DISRUPT_ENEMY_CARRY');
x=input({...fightReady,threat_reach:'REACHABLE'});f=run(x).gp23.phases.fight;assert.equal(f.goal_id,'SURVIVE_AND_DAMAGE');assert.match(f.position,/아군|공격/);assert.match(f.stop,/추격|보호|거리/);
""")

    def test_scope_fallback_never_borrows_champion_tactics(self):
        self.node(r"""
const x=input(fightReady,'MID');x.allies[2].champion='Aatrox';x.own_champion='Aatrox';const b=run(x);
assert.equal(b.gp23.phases.fight.coverage.status,'GENERAL_ONLY');assert.equal(b.gp23.phases.fight.goal_id,'CONDITIONAL_ROLE');
assert(!JSON.stringify(b.gp23.phases.fight.actions).includes('매혹'));
for(const key of Object.keys(x.situation.fields)){const bad=structuredClone(x);bad.situation.fields[key]=assumed('NOT_A_VALUE');assert.throws(()=>run(bad),/SITUATION/);}
""")

    def test_duel_does_not_require_an_unavailable_external_ally(self):
        self.node(r"""
const x=input({...fightReady,combat_context:'DUEL',ally_followup:'UNAVAILABLE'},'MID'),f=run(x).gp23.phases.fight;
assert.equal(f.execution,'READY');assert.equal(f.goal_id,'DUEL_CONTRIBUTION');assert(!/아군도 함께 공격/.test(f.action));
assert.match(f.stop,/내|상대/);
""")

    def test_threat_samples_do_not_become_named_current_priorities(self):
        self.node(r"""
const f=run(input(fightReady)).gp23.phases.fight;assert(f.threat_priority,'Missing explicit unresolved priority');assert.equal(f.threat_priority.status,'UNKNOWN');
assert.equal(f.threat_selection,'FUNCTIONAL_CANDIDATES_NO_DANGER_RANK');
for(const t of f.threats){assert.equal(t.reach,'UNKNOWN');assert.equal(t.scenario_reach,'REACHABLE');assert(t.means&&t.reason);}
const duel=run(input({...fightReady,combat_context:'DUEL'})).gp23.phases.fight;
assert(duel.threats.every(t=>t.champion==='Kaisa'));assert.match(duel.threat_priority.reason,/他|다른|범위|후보/);
""")

    def test_existing_scope_and_retained_consumers_share_v5_decision(self):
        self.node(r"""
let x=input({},'TOP'),b=run(x);assert.equal(b.gp23.phases.fight.coverage.status,'GENERAL_ONLY');
x=input();b=run(x);assert.equal(b.wave.plan_id,'CHECK_WAVE');assert.equal(b.wave.axes.pace.id,'CHECK_WAVE');assert.equal(b.wave.diagram.supported,false);
const r=E.analyze(x,catalog);assert.equal(r.coach.wave.selected_plan_id,'CHECK_WAVE');assert.equal(r.coach.selected.action,b.gp23.phases.lane.action);assert.equal(r.summary.fight_key,b.gp23.phases.fight.action);
x.scenario.overrides={resources:'SUFFICIENT',wave:'BUILDING'};x.planning.overrides={enemy_jungle:'AWAY',ally_followup:'AVAILABLE'};
b=run(x);assert.equal(b.gp23.phases.lane.decision_id,'CHECK_WAVE');assert.equal(b.gp23.legacy_assumptions.scenario.resources,'SUFFICIENT');
""")

    def test_prose_never_fills_space_by_duplicate_paragraphs(self):
        self.node(r"""
const b=run(input());for(const phase of Object.values(b.gp23.phases))assert.equal(new Set(phase.paragraphs).size,phase.paragraphs.length);
const x=input({...fightReady,ally_carry_risk:'THREATENED',key_skill:'SPENT'},'TOP'),f=run(x).gp23.phases.fight;
assert.equal(f.goal_id,'PROTECT_ALLY');assert.equal(f.execution,'BLOCKED');assert.match(f.action,/남은.*확인|지원.*확인/);
""")

    def test_uncovered_role_tags_do_not_imply_tactical_support(self):
        self.node(r"""
const b=run(input({},'TOP'));for(const phase of Object.values(b.gp23.phases)){
assert.equal(phase.coverage.status,'GENERAL_ONLY');assert(phase.tags.length<=2);
assert(phase.tags.every(t=>t.kind==='STATUS'));assert(!phase.tags.some(t=>t.kind==='ACTION'));
assert.deepEqual(b.delivery.phases[phase.id].tags,phase.tags);}
const supported=run(input(ready));for(const phase of Object.values(supported.gp23.phases))assert(phase.tags.length<=2);
assert(supported.gp23.phases.lane.tags.some(t=>t.kind==='ACTION'));
""")

    def test_missed_opportunity_updates_operation_branch_without_inventing_shortage(self):
        self.node(r"""
const x=input({...ready,...fightReady}),before=run(x).gp23.phases.operations;
x.planning.overrides={opportunity:'MISSED'};const b=run(x),after=b.gp23.phases.operations;
assert.equal(before.decision_id,'CONNECT_GAIN');assert.equal(after.decision_id,'RESET_OPPORTUNITY');
assert.notEqual(after.action,before.action);assert.match(after.action,/끝난 기회|기회.*끝/);
assert.match(after.reason,/기회.*끝|끝난 기회/);assert(!after.action.includes('아군이 움직일 수 없거나 자원이 부족하면'));
assert(after.tags.some(t=>t.kind==='ACTION'&&t.label==='다음 기회 준비'));assert(!after.tags.some(t=>t.label==='이득 전환 준비'));
assert.equal(x.situation.fields.resources.value,'SUFFICIENT');assert.equal(x.situation.fields.ally_followup.value,'AVAILABLE');
assert.equal(after.actions.length,5);assert.deepEqual(b.delivery.phases.operations.tags,after.tags);assert.equal(b.delivery.phases.operations.headline,after.action);
""")

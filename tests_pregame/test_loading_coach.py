"""Semantic contracts for explicit standard comparisons; never game accuracy tests."""
import hashlib,json,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PRELUDE="""const assert=require('node:assert/strict'),E=require('./web_r4/loading-engine.js'),c=require('./web_r4/loading-data.json');
function input(id){let x=E.exampleInput(c,0);if(id==='B'){x.allies[3].champion='Yunara';x.allies[4].champion='Lulu';x.enemies[4].champion='Alistar';x.own_champion='Yunara';}if(id==='C'){x.allies[0].champion='Darius';x.enemies[0].champion='Ambessa';x.own_champion='Darius';x.own_position='TOP';}if(id==='D'){x.allies[3].champion='Ezreal';x.own_champion='Ezreal';}return x;}
function run(id,overrides={},risk='BALANCED'){let x=input(id);x.schema_version='lol-coach-loading-input-v3';x.preferences={risk};x.scenario={standard:'lane-standard-v1',overrides};return E.analyze(x,c);}
"""
class LoadingCoachTests(unittest.TestCase):
 def node(self,body):
  r=subprocess.run(['node','-e',PRELUDE+body],cwd=ROOT,capture_output=True,text=True)
  self.assertEqual(r.returncode,0,r.stderr[-4500:])
 def test_ten_picks_default_plan_without_setting_controls(self):
  self.node("const r=E.analyze(input('A'),c);assert(r.coach,'default coach missing');assert.equal(r.coach.matchup_id,'A');assert.equal(r.coach.context.observations.resources,null);assert.equal(r.coach.context.assumptions.origin,'STANDARD_COMPARISON');assert(r.coach.summary.lane.length>15);assert.notEqual(r.coach.wave.selected_plan_id,'CHECK_WAVE');assert.equal(r.coach.periods.length,6);assert.equal(r.coach.periods[0].metrics.SHORT.assessment,'ALLY');")
 def test_matchup_binding_and_permutation(self):
  self.node("for(const id of ['A','B','C','D']){const x=input(id),a=E.analyze(x,c).coach;x.allies.reverse();x.enemies.reverse();const b=E.analyze(x,c).coach;assert.equal(a.matchup_id,id);assert.deepEqual(a.periods,b.periods);}let x=input('A');x.allies[4].position=null;assert.equal(E.analyze(x,c).coach.supported,false);x=input('B');x.enemies[3].champion='Lucian';x.enemies[4].champion='Nautilus';assert.notEqual(E.analyze(x,c).coach.matchup_id,'B');")
 def test_preference_does_not_change_advantage_or_unlock(self):
  self.node("for(const id of ['A','B','C','D']){const rows=['LOSS_LIMIT','BALANCED','OPPORTUNITY'].map(r=>run(id,{},r).coach);assert.deepEqual(rows[0].periods,rows[2].periods);assert.deepEqual(rows[0].evidence.claims,rows[2].evidence.claims);const low=run(id,{resources:'LOW'},'OPPORTUNITY').coach;assert(low.actions.every(a=>a.id!==low.selection.id||a.feasible==='POSSIBLE'));assert.notEqual(low.wave.selected_plan_id,'CRASH');}assert.notEqual(run('A',{},'LOSS_LIMIT').coach.selection.id,run('A',{},'OPPORTUNITY').coach.selection.id);assert.equal(run('A',{resources:'LOW'},'LOSS_LIMIT').coach.selection.id,run('A',{resources:'LOW'},'OPPORTUNITY').coach.selection.id);")
 def test_unknown_is_not_contested_or_safe(self):
  self.node("const r=run('A',{wave:'UNKNOWN',resources:'UNKNOWN',enemy_key:'UNKNOWN'}).coach;assert.equal(r.selected.metrics.PUSH.assessment,'INSUFFICIENT');assert.equal(r.wave.selected_plan_id,'CHECK_WAVE');assert(!r.actions.some(a=>a.id===r.selection.id&&a.feasible!=='POSSIBLE'));assert.equal(r.context.assumptions.scenario.overrides.resources,'UNKNOWN');")
 def test_first_hit_does_not_force_retreat_and_remaining_tools(self):
  self.node("let br=run('B',{engage:'THEIRS'});const b=require('./web_r4/loading-coach.js').evaluate(br,c,br.input.scenario,'LEVEL3_5');assert(b.actions.some(a=>a.id==='COUNTER_FOCUS_ADC'));assert(b.selected.engagements.find(a=>a.id==='COUNTER_INIT').order.join(' ').includes('카이사'));assert(b.selected.engagements.find(a=>a.id==='COUNTER_INIT').exceptions.length);assert.equal(b.selected.engagements.find(a=>a.id==='COUNTER_INIT').kill,'UNDETERMINED');assert.equal(br.coach.actions.find(a=>a.id==='COUNTER_FOCUS_ADC').feasible,'IMPOSSIBLE');assert.equal(run('B',{engage:'THEIRS',resources:'LOW'}).coach.actions.find(a=>a.id==='COUNTER_FOCUS_ADC').feasible,'IMPOSSIBLE');const a=run('A',{enemy_key:'SPENT'}).coach;assert(a.selected.engagements.every(e=>e.kill==='UNDETERMINED'&&e.chase==='UNDETERMINED'));assert(a.trade.theirs.reason.includes('강력한 일격'));")
 def test_start_skill_branch_does_not_copy_duel_result(self):
  self.node("const w=run('C',{start_skill:'W'}).coach,q=run('C',{start_skill:'Q'}).coach,u=run('C',{start_skill:'UNKNOWN'}).coach;assert.notEqual(w.selected.action,q.selected.action);assert.equal(u.selected.metrics.EXTENDED.assessment,'INSUFFICIENT');assert(w.selected.action.includes('CS'));assert(w.selected.engagements.every(e=>e.chase==='UNDETERMINED'));assert(q.sustain.actors[0].in_fight_heal.includes('바깥날'));")
 def test_shields_and_sustain_actors_are_distinct(self):
  self.node("const a=run('A').coach,b=run('B').coach;assert.equal(a.sustain.actors.length,4);assert.equal(b.sustain.actors.length,4);assert(a.sustain.actors.find(a=>a.champion==='Lux').shield.includes('회복'));assert(b.sustain.actors.find(a=>a.champion==='Alistar').between_trade.includes('회복'));assert(b.sustain.summary.includes('반복'));assert.notEqual(b.trade.ours.label,b.trade.actual_advantage);")
 def test_growth_event_is_not_fixed_three_item_reversal(self):
  self.node("const d=run('D').coach;assert(d.growth.length);const g=d.growth.find(g=>g.id==='KAISA_EVOLVED_ACCESS');assert(g);assert.equal(g.global_reversal,'UNDETERMINED');assert.equal(g.positional_punish_risk,'INCREASED_CONDITIONAL');assert(g.remaining_strength.includes('견제'));assert(!d.growth.some(g=>g.kind==='TIME'||g.id==='THREE_ITEMS_WIN'));const k=require('./web_r4/loading-knowledge.json');const b=k.build_examples.D;assert.notEqual(b.costs.Ezreal,b.costs.Kaisa);assert.equal(b.equal_gold,false);")
 def test_versioned_input_does_not_accept_live_observation(self):
  self.node("assert.equal(E.analyze(input('A'),c).input.schema_version,'lol-coach-loading-input-v2');const x=input('A');x.schema_version='lol-coach-loading-input-v3';x.preferences={risk:'BALANCED'};x.scenario={standard:'lane-standard-v1',overrides:{enemy_location:'TOP'}};assert.throws(()=>E.analyze(x,c));assert.equal(run('A').input.schema_version,'lol-coach-loading-input-v3');")
 def test_learned_skill_scope_and_unsupported_actions(self):
  self.node("const G=require('./web_r4/loading-coach.js');const b=run('B',{engage:'THEIRS'}).coach;assert.equal(b.actions.find(a=>a.id==='COUNTER_FOCUS_ADC').feasible,'IMPOSSIBLE');assert(!b.selected.engagements.find(e=>e.id==='COUNTER_INIT').order[0].includes('를 카이사에게 사용'));for(const start_skill of ['Q','E','UNKNOWN']){const c1=run('C',{start_skill}).coach;assert(!c1.trade.ours.order[0].includes('평타·다리우스의 마비의 일격'));}let x=input('A');x.allies[3].champion='Jinx';x.own_champion='Jinx';const u=E.analyze(x,c).coach;assert.equal(u.supported,false);assert(!u.trade.ours.order.join(' ').match(/비전 이동|신비한 화살/));assert(run('D').coach.trade.ours.start[0].includes('아직'));const passive=run('A',{},'LOSS_LIMIT').coach,active=run('A',{},'OPPORTUNITY').coach;assert.notEqual(passive.wave.selected.steps[1].text,active.wave.selected.steps[1].text);assert.equal(active.diagram.steps[1].text,active.selected.action);")
 def test_patch_mismatch_does_not_keep_advantage_or_execution(self):
  self.node("const x=input('A');x.patch='1.1';const r=E.analyze(x,c);assert.equal(r.evidence.patch_status,'MISMATCH');assert.equal(r.coach.supported,false);assert(r.coach.periods.every(p=>Object.values(p.metrics).every(m=>m.assessment==='INSUFFICIENT')));assert.equal(r.coach.selection.id,'CHECK_WAVE');assert.equal(r.coach.diagram.supported,false);assert(r.coach.context.patch.label.includes('버전 차이'));x.patch=null;const u=E.analyze(x,c);assert.equal(u.coach.context.observations.patch,null);assert(u.coach.context.patch.label.includes('미확인'));assert.equal(u.coach.context.assumptions.origin,'STANDARD_COMPARISON');")
 def test_source_quotes_bound_and_review_is_not_user_grade(self):
  p=ROOT/'web_r4/loading-knowledge.json';self.assertTrue(p.exists(),'knowledge file absent')
  k=json.loads(p.read_text());ids={s['id'] for s in k['sources']}
  for s in k['sources']:
   self.assertTrue(s['url'].startswith('https://'));self.assertTrue(s['excerpts'])
   for e in s['excerpts']:self.assertEqual(e['sha256'],hashlib.sha256(e['text'].encode()).hexdigest())
  for m in k['matchups']:
   for claim in m['claims']:
    self.assertTrue(set(claim['source_ids'])<=ids);self.assertNotIn(claim['review'],['REVIEWED','USER','AUTO_VERIFIED']);self.assertTrue(claim['counterexamples'])
  self.assertEqual(k['legacy_grades_changed'],False)
if __name__=='__main__':unittest.main()

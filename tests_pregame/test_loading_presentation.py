"""View projection/route correctness, not tactical efficacy."""
import subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PRE="""const assert=require('node:assert/strict'),E=require('./web_r4/loading-engine.js'),c=require('./web_r4/loading-data.json'),P=require('./web_r4/loading-presentation.js');
function run(own='Caitlyn'){let i=E.exampleInput(c,0);i.own_champion=own;i.own_position=own==='Ahri'?'MID':'BOTTOM';return E.analyze(i,c);}
"""
class PresentationTests(unittest.TestCase):
 def node(self,body):
  r=subprocess.run(['node','-e',PRE+body],cwd=ROOT,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr[-3000:])
 def test_projection_same_report_two_real_roles_and_unknown_scope(self):
  self.node("for(const own of ['Caitlyn','Ahri']){const r=run(own),v=P.project(r);assert.equal(v.own.champion,own);assert.equal(v.cards.length,3);assert.equal(v.teams.allies.length+v.teams.enemies.length,10);assert(v.remember.length<=3);assert.equal(v.cards[0].actions,r.coach.planboard.action_summaries.lane.items);assert.equal(v.cards[0].perspectives,r.coach.planboard.area_context.lane);assert.equal(v.cards[0].text,r.coach.planboard.loading_summary.items[0].support);assert(v.cards.every(x=>x.source_paths.length));}assert.equal(P.project(run('Ahri')).cards[0].perspectives.basis,'INSUFFICIENT');assert.notEqual(P.project(run()).title,P.project(run('Ahri')).title);")
 def test_source_change_projects_without_champion_specific_copy(self):
  self.node("const r=run();r.coach.planboard.loading_summary.items[0].conclusion='새 조건의 실제 결과';r.coach.planboard.loading_summary.changes=['변경 하나'];const v=P.project(r);assert.equal(v.cards[0].title,'새 조건의 실제 결과');assert.deepEqual(v.remember,['변경 하나']);assert.equal(r.coach.selected.metrics.ALLIN.assessment,'INSUFFICIENT');")
 def test_visual_labels_follow_existing_plan_not_champion_or_new_judgment(self):
  self.node("const r=run(),v=P.project(r);assert.equal(v.cards[0].concept,'먼저 밀고, 견제할 공간 만들기');assert.equal(v.hero_title,'먼저 밀어 견제할 공간을 만드세요');assert(v.cards[0].conditions.length<=2);r.coach.planboard.wave.plan_id='TOWER_CS';const changed=P.project(r);assert.equal(changed.cards[0].concept,'포탑 아래에서 성장 지키기');assert.notEqual(changed.hero_title,v.hero_title);r.coach.planboard.wave.plan_id='UNSUPPORTED_NEW';assert.equal(P.project(r).hero_title,r.coach.planboard.headline);assert.equal(P.project(r).cards[0].title,v.cards[0].title);assert.equal(r.coach.selected.metrics.ALLIN.assessment,'INSUFFICIENT');")
 def test_url_roundtrip_contains_only_input_and_view_not_sources_or_secrets(self):
  self.node("const r=run(),h=P.encode(r.input,'LEVEL6','fight');const v=P.decode(h);assert.deepEqual(v.input,r.input);assert.equal(v.period,'LEVEL6');assert.equal(v.detail,'fight');assert(!h.includes('source_ids'));assert.throws(()=>P.encode({...r.input,token:'secret'},'LEVEL1',null));assert.throws(()=>P.decode('#plan=garbage'));assert.throws(()=>P.encode(r.input,'LEVEL1','wrong'));assert.equal(P.decode('#loading-lane'),null);assert.throws(()=>P.decode('#plan='+encodeURIComponent(JSON.stringify({version:999,input:r.input}))));")
if __name__=='__main__':unittest.main()

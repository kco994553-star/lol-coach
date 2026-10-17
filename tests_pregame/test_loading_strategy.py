"""New composition-linked strategy behavior; no real-game accuracy assertion."""
import json
from pathlib import Path
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]


class LoadingStrategyTests(unittest.TestCase):
    def run_node(self,body):
        script="const assert=require('node:assert/strict'),fs=require('node:fs');\n"+\
            "assert(fs.existsSync('./web_r4/loading-engine.js'),'shared loading engine missing');\n"+\
            "const E=require('./web_r4/loading-engine.js'),C=JSON.parse(fs.readFileSync('./web_r4/loading-data.json','utf8')),copy=x=>JSON.parse(JSON.stringify(x));\n"+body
        result=subprocess.run(['node','-e',script],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_actual_picks_composition_roles_and_unknowns(self):
        self.run_node(r'''
const a=E.exampleInput(C,0),first=E.analyze(a,C);
assert.equal(a.allies.length,5);assert.equal(a.enemies.length,5);
assert.equal(first.input.own_champion,'Caitlyn');
assert.equal(first.lane.opponent.id,'Kaisa');
assert.equal(first.summary.remember.length<=3,true);
assert(first.summary.our_plan.includes('케이틀린')||first.summary.my_role.includes('케이틀린'));
assert(first.teamfight.threats.some(x=>x.name==='노틸러스'||x.name==='제드'));
let enemyChange=copy(a);
enemyChange.enemies=[{champion:'Nasus',position:'TOP'},{champion:'Ivern',position:'JUNGLE'},{champion:'Ziggs',position:'MID'},{champion:'Jinx',position:'BOTTOM'},{champion:'Janna',position:'SUPPORT'}];
const different=E.analyze(enemyChange,C);
assert.notEqual(first.summary.enemy_plan,different.summary.enemy_plan);
assert.notEqual(first.summary.fight_key,different.summary.fight_key);
let ownChange=copy(a);ownChange.own_champion='Ornn';ownChange.own_position='TOP';
const front=E.analyze(ownChange,C);
assert.notEqual(first.summary.my_role,front.summary.my_role);
assert.notEqual(first.teamfight.role,front.teamfight.role);
assert(front.teamfight.actions.join(' ').includes('화염 돌진'));
let unknown=copy(a);unknown.opponent_mode='UNKNOWN';unknown.lane_opponent=null;unknown.patch=null;
const u=E.analyze(unknown,C);
assert.equal(u.lane.opponent,null);assert(u.lane.rows.every(x=>x.judgment.includes('미확인')));
assert(u.lane.rows.some(x=>x.evidence_ids.length));
assert.equal(u.evidence.patch_status,'UNKNOWN');
assert.equal(u.evidence.real_coaching_n,0);assert.equal(u.evidence.accuracy,null);
assert.equal(first.evidence.strategy_level,'DESIGN_HYPOTHESIS');
assert.deepEqual(first.evidence.lectures,[]);
assert(!Object.hasOwn(first.input,'economy'));
assert.deepEqual(a,E.exampleInput(C,0));
''')

    def test_search_validation_and_manual_pc_import_equivalence(self):
        self.run_node(r'''
for(const [query,id] of [['케이틀린','Caitlyn'],['caitlyn','Caitlyn'],['Kai\'Sa','Kaisa'],['유나라','Yunara'],['Wukong','MonkeyKing']])assert.equal(E.resolveChampion(query,C),id);
assert.equal(E.resolveChampion('모르는챔피언',C),null);
const a=E.exampleInput(C,0);
const draft={phase:'PRE_GAME',patch:a.patch,my_champion:a.own_champion,my_position:a.own_position,
 slots:[...a.allies.map((s,i)=>({side:'ALLY',slot:i+1,...s})),...a.enemies.map((s,i)=>({side:'ENEMY',slot:i+1,...s}))],
 riotId:'must-not-be-copied',puuid:'must-not-be-copied'};
const imported=E.fromDraft(draft,C);assert.deepEqual(E.analyze(imported,C).summary,E.analyze(a,C).summary);
assert(!JSON.stringify(imported).includes('must-not-be-copied'));
assert.throws(()=>E.fromDraft({...draft,phase:'UNKNOWN'},C));
for(const mutate of [x=>x.allies.pop(),x=>x.enemies[0].champion=x.allies[0].champion,x=>x.own_champion='Zed',x=>x.own_position='toString',x=>x.own_position=['BOTTOM'],x=>x.enemies[0].position='BOTTOM',x=>x.economy={},x=>x.opponent_mode='MANUAL',x=>x.patch='latest']){
 let bad=copy(a);mutate(bad);assert.throws(()=>E.analyze(bad,C));
}
let manual=copy(a);manual.opponent_mode='MANUAL';manual.lane_opponent='Nautilus';
assert.equal(E.analyze(manual,C).lane.opponent.id,'Nautilus');
''')

    def test_milestones_evidence_and_applicable_maps(self):
        self.run_node(r'''
for(const raw of [E.exampleInput(C,0),E.exampleInput(C,1)]){
 const out=E.analyze(raw,C);
 assert.deepEqual(out.lane.rows.map(r=>r.id),['LEVEL1','LEVEL2','LEVEL3_5','LEVEL6','FIRST_PURCHASE','FIRST_CORE']);
 for(const row of out.lane.rows){
  assert(row.why&&row.action&&row.changes.length);
  assert(!Object.hasOwn(row,'score'));
  assert(row.evidence_ids.every(id=>out.evidence.facts.some(f=>f.id===id)||out.evidence.statistics.some(s=>s.id===id)));
 }
 const ids=new Set(raw.allies.map(x=>x.champion));
 for(const map of [out.teamfight.map,...out.scenarios.map(s=>s.map)]){
  assert(map.caption.includes('전술 설명용 예시'));
  assert(map.entities.every(e=>e.team!=='ENEMY'&&ids.has(e.champion)));
  assert(map.entities.some(e=>e.self&&e.champion===raw.own_champion));
 }
 assert(out.teamfight.actions.length===3&&out.teamfight.exit.length&&out.gameplan.prepare.length&&out.gameplan.switch_when.length);
}
let a=E.exampleInput(C,0),b=copy(a);b.allies[3].champion='Yunara';b.own_champion='Yunara';
const yunara=E.analyze(b,C);assert.equal(yunara.scenarios.length,0);
assert(yunara.lane.rows.some(r=>r.why.includes(C.champions.Yunara.facts.find(f=>f.slot==='Q').name)));
let red=copy(a);red.side='RED';
assert.notDeepEqual(E.analyze(a,C).teamfight.map.entities[0].start,E.analyze(red,C).teamfight.map.entities[0].start);
''')

    def test_position_and_duo_context_are_not_generic_cs_instructions(self):
        self.run_node(r'''
const a=E.exampleInput(C,0),bot=E.analyze(a,C);
assert(bot.summary.lane_key.includes('럭스')&&bot.summary.lane_key.includes('노틸러스'));
let jungle=copy(a);jungle.own_champion='Sejuani';jungle.own_position='JUNGLE';
const j=E.analyze(jungle,C);assert(j.lane.rows[0].action.includes('정글 자원'));assert(!j.lane.rows[0].action.includes('CS'));
let support=copy(a);support.own_champion='Lux';support.own_position='SUPPORT';
const s=E.analyze(support,C);assert(s.lane.rows[0].action.includes('수급을 보조'));
''')

    def test_functional_skill_bindings_and_loading_patch_warning(self):
        self.run_node(r'''
const a=E.exampleInput(C,1),out=E.analyze(a,C);
const ashe=out.composition.allies.signals.filter(s=>s.champion==='Ashe');
assert(ashe.find(s=>s.kind==='PICK').means.includes('수정화살'));
assert(ashe.find(s=>s.kind==='PRESSURE').means.includes('일제 사격'));
assert(!ashe.some(s=>s.means==='매 날리기'));
let b=E.exampleInput(C,0);b.patch='16.19';
assert(E.analyze(b,C).summary.uncertainties.some(s=>s.includes('16.19')&&s.includes('16.20.1')));
b.own_champion='Sejuani';b.own_position='JUNGLE';assert.equal(E.analyze(b,C).lane.opponent,null);
const lee=E.analyze(b,C).composition.enemies.signals.find(s=>s.champion==='LeeSin'&&s.kind==='COVER');
assert(lee.means.includes('방호'));
''')

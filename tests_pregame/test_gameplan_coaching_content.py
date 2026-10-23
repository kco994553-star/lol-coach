"""Real report behavior: role changes, absent actors and unknown-state boundaries."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRELUDE = """
const assert=require('node:assert/strict'), E=require('./web_r4/loading-engine.js'),
 C=require('./web_r4/loading-coach.js'), P=require('./web_r4/loading-presentation.js'),
 catalog=require('./web_r4/loading-data.json');
function input(role='JUNGLE') {const x=E.exampleInput(catalog,1);
 x.own_position=role;x.own_champion=x.allies.find(p=>p.position===role).champion;return x;}
function run(x=input()){return E.analyze(x,catalog).coach.planboard;}
"""

class GameplanCoachingContentTests(unittest.TestCase):
    def node(self, body):
        p = subprocess.run(['node', '-e', PRELUDE + body], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr[-5000:])

    def test_graves_jungle_plan_connects_growth_side_and_central_defense(self):
        self.node(r"""
const b=run();assert.match(b.operation_headline,/사이드.*중앙/);
assert.match(b.action_summaries.lane.items[0].text,/캠프|성장/);
assert.match(b.operations.placement,/중앙/);assert.match(b.operations.connection,/피오라/);
assert.match(b.fight.start,/빨리 뽑기\(E\)/);
assert.match(b.fight.target,/진입|들어온/);
assert.equal(b.briefing_v2.items.find(x=>x.id==='my_role').text,b.composition.role);
assert(b.condition_responses.operations.some(x=>x.id==='SIDE_DRAWS_TWO'));
assert(b.condition_responses.lane.some(x=>x.id==='JUNGLE_OPPOSITE'));
assert(b.coaching_explanation.operations.length>=2);
const v=P.project(E.analyze(input(),catalog));assert.equal(v.cards[0].label,'초반 정글');
assert.deepEqual(v.cards[1].explanation,b.coaching_explanation.operations);
""")

    def test_fiora_and_graves_have_different_jobs_in_same_team_plan(self):
        self.node(r"""
const f=run(input('TOP')),g=run();assert.deepEqual(f.team_plan.rows,g.team_plan.rows);
assert.match(f.operation_headline,/사이드/);assert.notEqual(f.operations.placement,g.operations.placement);
assert.match(f.fight.start,/응수\(W\)/);
assert(f.condition_responses.operations.some(x=>x.id==='SIDE_DEFENDER_LEAVES'));
assert.match(f.coaching_explanation.lane.join(' '),/공격 속도/);
for(const b of [f,g])for(const area of ['lane','operations','fight'])assert.equal(b.action_summaries[area].items.length,5);
assert.match(g.team_plan.theirs.opening,/말파이트.*자르반/);
assert.match(g.team_plan.theirs.damage,/오리아나.*징크스/);
""")

    def test_removed_champions_are_not_mentioned_by_new_rules(self):
        self.node(r"""
const x=input();x.allies[0].champion='Ornn';x.enemies[0].champion='Garen';
x.enemies[1].champion='Ivern';x.enemies[2].champion='Viktor';x.enemies[3].champion='Ezreal';
const b=run(x),text=JSON.stringify([b.coaching_explanation,b.team_plan,b.operations,b.fight,b.reminders]);
for(const absent of ['피오라','말파이트','자르반','오리아나','징크스'])assert(!text.includes(absent),absent);
assert(!b.condition_responses.operations.some(x=>x.id==='SIDE_DRAWS_TWO'));
assert.match(b.operation_headline,/성장/);
""")

    def test_missing_patch_and_wrong_role_do_not_gain_supported_coaching(self):
        self.node(r"""
let x=input();x.patch='1.1';assert(!run(x).coaching_explanation);
x=input();x.allies.find(p=>p.position==='JUNGLE').position='TOP';x.allies[0].position='JUNGLE';x.own_position='TOP';
assert(!run(x).coaching_explanation?.lane?.join(' ').includes('정글 캠프'));
""")

    def test_new_advice_does_not_promote_matchup_strength_or_live_state(self):
        self.node(r"""
const x=input(),r=E.analyze(x,catalog),b=r.coach.planboard;
assert.equal(b.coverage.status,'UNSUPPORTED');assert.equal(b.fight.kill,'UNDETERMINED');
for(const area of ['lane','operations','fight'])for(const c of b.condition_responses[area]){
 assert.equal(c.observation,false);assert(c.trigger&&c.action&&c.stop);
}
const f=E.analyze(input('TOP'),catalog);
const low=C.evaluate(f,catalog,{standard:'lane-standard-v1',overrides:{resources:'LOW'}},'LEVEL6').planboard;
assert.match(low.action_summaries.lane.items[0].text,/체력|회복/);
assert.match(low.action_summaries.lane.items[2].text,/교환.*줄|공격.*강제|무리/);
const lowJ=C.evaluate(r,catalog,{standard:'lane-standard-v1',overrides:{resources:'LOW'}},'LEVEL6').planboard;
assert.match(lowJ.action_summaries.lane.items[2].text,/회복|구매/);
""")

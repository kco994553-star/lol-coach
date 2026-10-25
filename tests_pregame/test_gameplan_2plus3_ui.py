"""2+3 delivery projection/replay checks; no tactical efficacy claim."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRE = """const assert=require('node:assert/strict'),E=require('./web_r4/loading-engine.js'),P=require('./web_r4/loading-presentation.js'),C=require('./web_r4/loading-data.json');C.coaching_knowledge=require('./web_r4/loading-knowledge.json');const oldInput=E.exampleInput(C,0),S=require('./web_r4/loading-situation.js');const r=E.analyze({...oldInput,schema_version:'lol-coach-loading-input-v5',preferences:{risk:'BALANCED'},scenario:{standard:'lane-standard-v1',overrides:{}},planning:{basis:'loading-plan-example-v1',overrides:{}},situation:S.defaultState()},C);"""

class Gameplan23UITests(unittest.TestCase):
    def node(self, body):
        result = subprocess.run(['node', '-e', PRE + body], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr[-3500:])

    def test_overview_is_engine_projection_with_distinct_responsibilities(self):
        self.node("const v=P.project(r,{currentOnly:true});assert.equal(v.overview.length,2);assert.deepEqual(v.overview.map(x=>x.id),['teams','user']);assert(v.overview.every(x=>x.title&&x.paragraphs.length));assert.equal(new Set(v.overview.flatMap(x=>x.paragraphs)).size,v.overview.flatMap(x=>x.paragraphs).length);")

    def test_expanded_combat_label_preserves_visible_actions_and_prose(self):
        self.node("const v=P.project(r,{currentOnly:true});assert.equal(v.cards[2].label,'교전·한타');assert.equal(v.cards[2].coaching_heading,'교전·한타를 풀어가는 방법');for(const card of v.cards){assert.equal(card.actions,r.coach.planboard.gp23.phases[card.id].actions);assert.equal(card.explanation,r.coach.planboard.gp23.phases[card.id].paragraphs);}")

    def test_v5_situation_roundtrips_without_old_link_migration(self):
        self.node("const input={...r.input,schema_version:'lol-coach-loading-input-v5',scenario:{standard:'lane-standard-v1',overrides:{}},planning:{basis:'loading-plan-example-v1',overrides:{}},situation:S.defaultState()};const hash=P.encode(input,'LEVEL2','fight');assert.deepEqual(P.decode(hash).input,input);assert.deepEqual(P.decode(P.encode(oldInput)).input,oldInput);assert.throws(()=>P.encode({...input,token:'private'}));")

if __name__ == '__main__':
    unittest.main()

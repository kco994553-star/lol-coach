"""Changed-only behavioral checks: learning prototype, never coaching accuracy."""
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DirectionsTests(unittest.TestCase):
    def test_official_image_assets_and_public_source_metadata_are_exact(self):
        source=json.loads((ROOT/'config/direction_asset_sources.json').read_text())
        catalog=json.loads((ROOT/'web_r4/directions-data.json').read_text())
        self.assertEqual({a['id'] for a in source['assets']},{'map11.png','Caitlyn.png','Fiora.png','Ornn.png'})
        public={a['id']:a for a in catalog['asset_sources']}
        for asset in source['assets']:
            raw=(ROOT/asset['local_path']).read_bytes()
            self.assertEqual(raw[:8],b'\x89PNG\r\n\x1a\n')
            self.assertEqual(hashlib.sha256(raw).hexdigest(),asset['sha256'])
            self.assertEqual(len(raw),asset['bytes'])
            self.assertEqual((int.from_bytes(raw[16:20],'big'),int.from_bytes(raw[20:24],'big')),(asset['width_px'],asset['height_px']))
            self.assertEqual(public[asset['id']]['sha256'],asset['sha256'])
            self.assertEqual(public[asset['id']]['requested_url'],asset['requested_url'])

    def test_decision_engine_counterfactuals_and_unknowns(self):
        script = r'''
const assert=require('node:assert/strict'), fs=require('node:fs');
const E=require('./web_r4/directions-engine.js');
const C=JSON.parse(fs.readFileSync('./web_r4/directions-data.json','utf8'));
const copy=x=>JSON.parse(JSON.stringify(x));
assert.equal(C.presets.length,6);
let plans=C.presets.map(p=>E.evaluate(p.input,C));
for(let n=0;n<6;n+=2){
 assert.deepEqual(plans[n].input.economy,plans[n+1].input.economy);
 assert.notEqual(plans[n].plan.id,plans[n+1].plan.id);
}
for(const p of C.presets){
 let i=copy(p.input),id=E.evaluate(i,C).plan.id;
 for(const state of ['AHEAD','BEHIND','EVEN','UNKNOWN']){
  for(const r of Object.keys(i.economy))i.economy[r]=state;
  assert.equal(E.evaluate(i,C).plan.id,id,'economy cannot force fight outcome');
 }
}
const side=copy(C.presets[2].input), roles=[];
for(const champion of ['Caitlyn','Fiora','Ornn']){
 side.champion=champion;const out=E.evaluate(side,C);roles.push(out.plan.id);
 assert(out.plan.steps.some(s=>s.text.includes({Caitlyn:'덫',Fiora:'응수',Ornn:'지형'}[champion])));
}
assert.equal(new Set(roles).size,3);
const unknown=E.evaluate(E.defaultInput(C),C);
assert(Object.values(unknown.input.economy).every(x=>x==='UNKNOWN'));
assert.equal(unknown.map.entities.filter(x=>x.team==='ENEMY').length,0);
assert(unknown.plan.alternative.steps.length>0);
for(const p of plans){
 assert.equal(p.evidence.level,'DESIGN_HYPOTHESIS');
 assert.deepEqual(p.evidence.statistics,[]);assert.deepEqual(p.evidence.expert_statements,[]);
 assert.equal(p.plan.steps.length,3);
 assert.deepEqual([...new Set(p.map.arrows.map(a=>a.step))].sort(),[1,2,3]);
 assert(p.map.arrows.every(a=>p.plan.steps.some(s=>s.number===a.step)));
 assert(p.map.arrows.every(a=>a.from.x!==a.to.x || a.from.y!==a.to.y));
 assert(p.plan.requirements.length && p.plan.switch_when.length && p.plan.why.length);
}
let blue=copy(C.presets[4].input),red=copy(blue);red.side='RED';
let b=E.evaluate(blue,C).map,r=E.evaluate(red,C).map;
assert.notDeepEqual(b.entities.find(e=>e.self).start,r.entities.find(e=>e.self).start);
assert.deepEqual(b.landmarks.find(x=>x.kind==='OBJECTIVE'),r.landmarks.find(x=>x.kind==='OBJECTIVE'));
let i=E.defaultInput(C);i.metrics.total_earned_difference=-400;i.metrics.purchased_value_difference=900;i.metrics.current_gold=700;
let m=E.evaluate(i,C).economy.metrics;
assert.deepEqual(m.map(x=>x.value),[-400,900,700]);assert(m.every(x=>x.observed_at===null));
assert.equal(E.evaluate(i,C).input.economy.BOTTOM,'UNKNOWN');
assert.equal(unknown.map.landmarks.filter(x=>x.kind==='WAVE').length,0);
for(const mutate of [x=>x.review_mode='IN_GAME',x=>x.review_mode='toString',x=>x.role='constructor',x=>x.role=['BOTTOM'],x=>x.review_mode=['PRE_GAME_LEARNING'],x=>x.economy.TOP=['UNKNOWN'],x=>x.conditions.wave=['UNKNOWN'],x=>x.economy.TOP='SAFE',x=>x.champion='Unknown',x=>x.metrics.current_gold=-1,x=>x.metrics.current_gold=NaN,x=>x.extra=true,x=>x.phase='POST_LANE']){
 const bad=E.defaultInput(C);mutate(bad);assert.throws(()=>E.evaluate(bad,C));
}
assert.deepEqual(C.presets.map(p=>p.input),C.presets.map(p=>E.evaluate(p.input,C).input));
process.stdout.write(JSON.stringify({passed:true,scenes:6,coaching_accuracy:null}));
'''
        result = subprocess.run(['node', '-e', script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)['passed'])

    def test_official_fact_excerpts_are_existing_exact_source_fields(self):
        catalog = json.loads((ROOT/'web_r4/directions-data.json').read_text())
        for champion in catalog['champions']:
            for fact in champion['official_facts']:
                p = ROOT/fact['local_source']
                self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),fact['sha256'])
                body=json.loads(p.read_text())['data'][champion['id']]
                actual=body['passive']['description'] if fact['slot']=='P' else body['spells']['QWER'.index(fact['slot'])]['description']
                self.assertEqual(fact['excerpt'],actual)
                self.assertEqual(fact['version'],'16.20.1')
                self.assertTrue(fact['url'].startswith('https://ddragon.leagueoflegends.com/'))


if __name__ == '__main__':
    unittest.main()

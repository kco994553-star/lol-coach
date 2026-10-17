"""Changed PC display surfaces only; no API, storage or collection work."""
import json
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SkillPcDisplayTests(unittest.TestCase):
    def test_shared_names_load_before_each_pc_renderer(self):
        for page, renderer in [('pc', 'pc.js'), ('pregame', 'official_reference.js'),
                               ('review_queue', 'official_reference.js')]:
            with self.subTest(page=page):
                html = (ROOT / 'web_r4' / (page + '.html')).read_text()
                scripts = re.findall(r'<script\b([^>]+)>', html)
                names = [re.search(r'src="([^"]+)"', tag).group(1).lstrip('/')
                         for tag in scripts if 'src=' in tag]
                self.assertIn('skill-data.js', names)
                self.assertIn('skill-display.js', names)
                self.assertLess(names.index('skill-data.js'), names.index('skill-display.js'))
                self.assertLess(names.index('skill-display.js'), names.index(renderer))
                self.assertTrue(all('defer' in tag for tag in scripts))

    def test_real_display_helpers_keep_owners_and_raw_data_separate(self):
        # Evaluate the actual pure adapters, leaving auth/DOM/request handlers unexecuted.
        script = r'''
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const SkillDisplay=require('./web_r4/skill-display.js');
const input={my_champion:'Caitlyn',slots:[{champion:'Caitlyn',side:'ALLY',position:'BOTTOM'},
 {champion:'Lux',side:'ALLY',position:'SUPPORT'},{champion:'Kaisa',side:'ENEMY',position:'BOTTOM'},
 {champion:'Jax',side:'ENEMY',position:'TOP'},{champion:'Ahri',side:'ENEMY',position:'MID'},
 {champion:'Fiddlesticks',side:'ENEMY',position:'JUNGLE'}]};
const source=fs.readFileSync('web_r4/pc.js','utf8');
const code=source.slice(source.indexOf('  function skillOptions('),source.indexOf('  const local ='));
const pc=vm.runInNewContext(code+';({cardText,prose})',{window:{SkillDisplay},currentInput:input});
const owned={champion:'Caitlyn',evidence_level:'HYPOTHESIS'};
assert.equal(pc.cardText('덫과 투망',owned),'케이틀린의 요들잡이 덫(W)과 케이틀린의 90구경 투망(E)');
assert.equal(pc.cardText('Q와 덫은 미확인',{evidence_level:'AUTO_VERIFIED'}),'Q와 덫은 미확인');
assert.equal(pc.cardText('럭스 Q',{evidence_level:'USER'}),'럭스의 빛의 속박(Q)');
assert.equal(pc.prose('상대 반격과 매혹, 공포에 대비하며 준비합니다.'),'상대 반격과 매혹, 공포에 대비하며 준비합니다.');
const official={champion:'Lux',evidence_level:'OFFICIAL'};
const original='빛의 속박: 원문 Q와 덫은 그대로 보존합니다.';
assert.equal(pc.cardText(original,official),'럭스의 빛의 속박(Q): 원문 Q와 덫은 그대로 보존합니다.');
assert.equal(original,'빛의 속박: 원문 Q와 덫은 그대로 보존합니다.');
const before=JSON.stringify(input),pgSource=fs.readFileSync('web_r4/pregame.js','utf8');
const pgCode=pgSource.slice(pgSource.indexOf('  function skillOptions('),pgSource.indexOf('  const manual ='));
const pg=vm.runInNewContext(pgCode+';({cooldownName,prose})',{window:{SkillDisplay},plan:{input}});
const item={name:'빛의 속박',spell_kind:'ABILITY',side:'ALLY',position:'SUPPORT'},plan={input};
assert.equal(pg.cooldownName(item,plan),'럭스의 빛의 속박(Q)');
assert.equal(pg.cooldownName({...item,name:'빛의 속박(Q)'},plan),'럭스의 빛의 속박(Q)');
assert.equal(pg.cooldownName({...item,name:'빛의 속박(W)'},plan),'빛의 속박(W)');
assert.equal(pg.cooldownName({...item,name:'Q'},plan),'Q');
assert.equal(pg.cooldownName({...item,spell_kind:'SUMMONER'},plan),'빛의 속박');
const duplicate={input:{...input,slots:[...input.slots,{champion:'Nautilus',side:'ALLY',position:'SUPPORT'}]}};
assert.equal(pg.cooldownName(item,duplicate),'빛의 속박');
assert.equal(pg.prose('럭스 Q와 케이틀린 W',plan),'럭스의 빛의 속박(Q)와 케이틀린의 요들잡이 덫(W)');
assert.equal(JSON.stringify(input),before);
const rqSource=fs.readFileSync('web_r4/review_queue.js','utf8');
const rqCode=rqSource.slice(rqSource.indexOf(' function prose('),rqSource.indexOf(' async function api('));
const current={claim:'럭스 Q'},rq=vm.runInNewContext(rqCode+';({prose})',
 {window:{SkillDisplay},current,queue:null,referenceData:{champions:[{champion:'Lux'}]}});
assert.equal(rq.prose(current.claim),'럭스의 빛의 속박(Q)');
assert.equal(current.claim,'럭스 Q');
console.log(JSON.stringify({api_calls:0,fixture_objects_unchanged:true,official_body_unchanged:true}));
'''
        result = subprocess.run(['node', '-e', script], cwd=ROOT,
                                text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        observed = json.loads(result.stdout)
        self.assertEqual(observed['api_calls'], 0)
        self.assertTrue(observed['fixture_objects_unchanged'])
        self.assertTrue(observed['official_body_unchanged'])


if __name__ == '__main__':
    unittest.main()

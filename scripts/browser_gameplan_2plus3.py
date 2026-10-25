"""Shipped 2+3 UI flow in isolated PC/public servers; no tactical accuracy claim."""
import argparse
import functools
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
JS = r'''
const assert=require('node:assert/strict'),fs=require('node:fs'),{chromium}=require('playwright');
(async()=>{const browser=await chromium.launch({executablePath:process.env.CHROMIUM_EXECUTABLE||'/usr/bin/chromium',args:['--no-sandbox']}),results=[];
try { for(const [name,width,height,base]of [['desktop',1440,1000,process.env.PC+'/loading'],['mobile',390,844,process.env.PUBLIC+'/lol-coach/loading.html'],['narrow',320,740,process.env.PUBLIC+'/lol-coach/loading.html']]){
 const page=await browser.newPage({viewport:{width,height},reducedMotion:'reduce'}),errors=[];page.on('pageerror',error=>errors.push(error.message));
 await page.goto(base);await page.locator('#analyze:enabled').waitFor();await page.locator('#example-0').click();await page.locator('#analyze').click();await page.locator('.plan-title').waitFor();
 assert.equal(await page.locator('[data-plan-overview]').count(),2,'two distinct upper cards');
 assert.equal(await page.locator('.plan-overview-comparison tbody tr').count(),4);
 const baseline=await page.locator('.plan-area-cards').innerText();
 for(const phase of ['lane','operations','fight']){
  assert.equal(await page.locator('[data-basic-phase='+phase+'] .plan-basic-actions li').count(),5);
  assert(await page.locator('[data-basic-coaching='+phase+'] p').count()>0);
  assert(await page.locator('[data-basic-phase='+phase+'] .plan-card-conditions > span').count()<=2);
  if(phase==='fight')assert(await page.locator('[data-gp23-decision=fight]').isVisible());
 }
 assert.match(await page.locator('[data-basic-phase=fight] h3').first().innerText(),/교전·한타/);
 const threatMeans=await page.evaluate(async()=>{const c=await(await fetch('./loading-data.json')).json();c.coaching_knowledge=await(await fetch('./loading-knowledge.json')).json();const fight=LoadingStrategy.analyze(LoadingPresentation.decode(location.hash).input,c).coach.planboard.gp23.phases.fight;return {means:(fight.threat_candidates||fight.threats).map(t=>t.means),scenarioEffect:fight.threat_priority.scenario_effect};});
 assert.equal(await page.locator('[data-gp23-threat-priority]').count(),1);assert.match(await page.locator('[data-gp23-threat-priority]').innerText(),/미확인/);const candidates=page.locator('[data-gp23-threat-candidates]');assert(!(await candidates.evaluate(n=>n.open)));await candidates.locator('summary').click();const threatText=await candidates.innerText();for(const means of threatMeans.means)assert(threatText.includes(means),'disclosed functional threat means: '+means);await candidates.locator('summary').click();assert((await page.locator('[data-gp23-decision=fight]').innerText()).includes(threatMeans.scenarioEffect),'current scenario threat constraint remains visible');

 assert.equal(await page.evaluate(()=>LoadingPresentation.decode(location.hash).input.schema_version),'lol-coach-loading-input-v5');
 const more=page.locator('[data-situation-controls] > summary');await more.focus();await page.keyboard.press('Enter');
 const jungle=page.locator('[data-situation-field=enemy_jungle]');await jungle.selectOption('NEAR');await page.waitForFunction(()=>document.querySelector('#loading-coach').getAttribute('aria-busy')==='false');
 assert.match(await page.locator('[data-situation-state]').first().innerText(),/가정/);
 const state=await page.evaluate(()=>LoadingPresentation.decode(location.hash).input.situation);assert.equal(state.fields.enemy_jungle.status,'assumed');assert.equal(state.fields.enemy_jungle.source,'user-scenario');assert.equal(state.fields.enemy_jungle.observed_at,null);
 const changed=await page.locator('.plan-area-cards').innerText(),shared=page.url();assert.match(await page.locator('[data-situation-status=assumed]').innerText(),/상대 정글.*가정/);
 await page.reload();await page.locator('[data-plan-overview]').first().waitFor();assert.equal(await page.locator('.plan-area-cards').innerText(),changed);
 const fresh=await browser.newPage({viewport:{width,height}});await fresh.goto(shared);await fresh.locator('.plan-title').waitFor();assert.equal(await fresh.locator('.plan-area-cards').innerText(),changed);await fresh.close();
 await page.locator('[data-plan-more=fight]').focus();await page.keyboard.press('Enter');await page.locator('.plan-detail-title').waitFor();await page.goBack();await page.locator('.plan-detail').waitFor({state:'hidden'});assert.equal(await page.locator('.plan-area-cards').innerText(),changed);
 await page.locator('[data-situation-controls] > summary').click();await page.locator('[data-situation-reset]').focus();await page.keyboard.press('Enter');await page.waitForFunction(()=>document.querySelector('#loading-coach').getAttribute('aria-busy')==='false');
 assert.equal(await page.locator('.plan-area-cards').innerText(),baseline);assert(await page.evaluate(()=>Object.values(LoadingPresentation.decode(location.hash).input.situation.fields).every(x=>x.status==='unknown')));
 const reviewed=await page.evaluate(()=>{const route=LoadingPresentation.decode(location.hash);route.input.situation=LoadingSituation.defaultState('REVIEW');route.input.situation.fields.enemy_jungle={status:'stale',value:'NEAR',source:'isolated-replay-fixture',observed_at:'2026-10-24T12:00:00Z'};return location.pathname+LoadingPresentation.encode(route.input,route.period,null);});
 await page.goto(new URL(reviewed,base).href);await page.locator('.plan-title').waitFor();assert.match(await page.locator('[data-situation-state]').innerText(),/오래된 정보/);assert.match(await page.locator('[data-situation-state]').innerText(),/isolated-replay-fixture/);assert.match(await page.locator('[data-situation-state]').innerText(),/과거/);
 await page.locator('[data-situation-controls] > summary').click();assert(await page.locator('[data-situation-field=enemy_jungle]').isDisabled());await page.locator('[data-situation-reset]').click();await page.waitForFunction(()=>document.querySelector('#loading-coach').getAttribute('aria-busy')==='false');assert.equal(await page.locator('[data-situation-status=stale]').count(),0);assert.equal(await page.locator('.plan-area-cards').innerText(),baseline);
 const learn=page.locator('[data-gameplan-learning]').first();assert(await learn.isVisible());const learningURL=await learn.getAttribute('href');assert.match(learningURL,/learning\.html#learn=/);assert(!learningURL.includes('allies')&&!learningURL.includes('scenario'));const sharedClaim=new URLSearchParams(learningURL.split('#learn=')[1]).get('claim');const currentClaims=await page.evaluate(async()=>{const c=await(await fetch('./loading-data.json')).json();c.coaching_knowledge=await(await fetch('./loading-knowledge.json')).json();return LoadingStrategy.analyze(LoadingPresentation.decode(location.hash).input,c).coach.planboard.gp23.phases.lane.actions.flatMap(a=>a.claim_ids||[]);});assert(!sharedClaim||currentClaims.includes(sharedClaim),'learning link claim belongs to current decision');
 for(const zoom of [false,true]){await page.evaluate(on=>document.documentElement.style.fontSize=on?'200%':'',zoom);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'no page overflow at '+width+' zoom '+zoom);for(const selector of ['[data-plan-overview]','.plan-basic-actions','[data-basic-coaching]'])assert(await page.locator(selector).evaluateAll(nodes=>nodes.every(n=>n.getBoundingClientRect().right<=innerWidth+1)),'no clipped core '+selector);await page.screenshot({path:process.env.OUT+'/'+name+(zoom?'-200':'')+'.png',fullPage:false});}
 await page.evaluate(()=>document.documentElement.style.fontSize='');
 await page.locator('[data-plan-edit]').click();await page.locator('#own-champion').selectOption('Ornn');await page.locator('#own-position').selectOption('TOP');await page.locator('#analyze').click();await page.locator('.plan-title').waitFor();assert.equal(await page.locator('.plan-coverage[data-coverage=GENERAL_ONLY]').count(),3);assert.equal(await page.locator('.plan-card-conditions [data-tag-kind=ACTION]').count(),0,'unsupported plans show scope status instead of actionable tags');
 await page.locator('[data-plan-edit]').click();await page.locator('#pick-ALLY-0').fill('');assert(await page.locator('#loading-results').isHidden());
 const archived=await page.evaluate(()=>{const saved=JSON.parse(decodeURIComponent(sessionStorage.getItem('lol-coach-loading-plan-v1').slice(6))).input;delete saved.situation;delete saved.scenario;delete saved.planning;saved.schema_version='lol-coach-loading-input-v2';return location.pathname+LoadingPresentation.encode(saved,'LEVEL1','lane');});
 await page.goto(new URL(archived,base).href);await page.locator('.plan-detail-title').waitFor();assert.equal(await page.locator('[data-plan-overview]').count(),0,'archived report remains on original contract');await page.locator('details[id$="-conditions"] > summary').click();await page.locator('[data-coach-focus=condition-resources]').selectOption('LOW');await page.waitForFunction(()=>document.querySelector('#loading-coach').getAttribute('aria-busy')==='false');assert.equal(await page.evaluate(()=>LoadingPresentation.decode(location.hash).input.schema_version),'lol-coach-loading-input-v4');assert.equal(await page.locator('[data-coach-focus=condition-resources]').count(),1,'legacy controls keep their semantics');
 assert.deepEqual(errors,[]);results.push({name,width,top2:true,phaseActions:15,hypothetical:true,reset:true,share:true,reload:true,back:true,keyboard:true,text200:true,unsupported:true,partialStaleHidden:true,errors});await page.close();
 } }finally{await browser.close();}
 fs.writeFileSync(process.env.OUT+'/result.json',JSON.stringify({passed:true,results,real_coaching_n:0},null,2));console.log(JSON.stringify({passed:true,results}));
})().catch(error=>{console.error(error.stack);process.exitCode=1;});
'''

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    from scripts.build_directions_web import build
    from scripts.launch_pc import create_server
    with tempfile.TemporaryDirectory(prefix='gp23-browser-') as temp:
        folder = Path(temp)
        build(folder/'public'/'lol-coach')
        pc = create_server(folder/'private', port=0)
        public = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(folder/'public')))
        for server in (pc, public):
            threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            probe = out/'probe.cjs'
            probe.write_text(JS)
            env = dict(os.environ, NODE_PATH=os.environ.get('NODE_PATH', '/opt/codex/cua_node/lib/node_modules'), PC='http://127.0.0.1:'+str(pc.server_port), PUBLIC='http://127.0.0.1:'+str(public.server_port), OUT=str(out))
            result = subprocess.run(['node', str(probe)], cwd=ROOT, env=env, text=True, capture_output=True, timeout=180)
            (out/'browser.log').write_text(result.stdout+result.stderr)
            sources = ['web_r4/'+name for name in ('loading.html','loading.js','loading-coach-view.js','loading-presentation.js','loading-presentation.css','loading-situation.js','loading-planboard.js','loading-engine.js')]
            receipt = {'passed': result.returncode == 0, 'source_commit': subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(), 'source_sha256': {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sources if (ROOT/name).exists()}, 'real_coaching_n':0}
            (out/'runner.json').write_text(json.dumps(receipt, indent=2)+'\n')
            print(json.dumps({'passed':receipt['passed'], 'output':str(out)}))
            if result.returncode:
                print(result.stderr[-4500:])
            return result.returncode
        finally:
            for server in (pc, public):
                server.shutdown()
                server.server_close()

if __name__ == '__main__':
    raise SystemExit(main())

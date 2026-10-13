"""Isolated Chromium queue proof. Simulated decisions never write USER_WEB.

Run from repository root. Only synthetic candidate read/propose/later state is
persisted; browser interception models decisions in an in-memory fixture.
"""
import hashlib
import json
import os
from pathlib import Path
import secrets
import sqlite3
import subprocess
import sys
import tempfile
import threading

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

BROWSER=r'''
const {chromium}=require('playwright');const fs=require('fs');const assert=require('node:assert/strict');
(async()=>{
 const fixture=JSON.parse(fs.readFileSync(process.env.RQ_FIXTURE));let view=fixture;let decisions=0;let userEvents=0;const checks=[];const errors=[];
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_EXECUTABLE,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 page.on('pageerror',e=>errors.push(String(e)));const token=fs.readFileSync(process.env.WORKBENCH_TOKEN_FILE,'utf8').trim();
 const base=process.env.WORKBENCH_URL;
 for(const c of fixture.candidates){
  c.sources=[{url:'https://example.org/synthetic',title:'SYNTHETIC archived excerpt',locator:'fixture.only',patch:'SYNTHETIC-1',excerpt:'SYNTHETIC source excerpt: recorded condition only. '.repeat(45),excerpt_status:'SYNTHETIC_FIXTURE'}];
  c.conditions.source_conditions=['SYNTHETIC declared circumstance'];
  c.statistics={status:'DESCRIPTIVE_ONLY',comparisons:[{champion:'Caitlyn',position:'BOTTOM',patch:'SYNTHETIC-1',tier:'CHALLENGER',comparison:'MATCHUP',unit:'gold delta',sample_kind:'SYNTHETIC',points:[{minute:10,n:2,mean:100,ci95:{low:90,high:110}}]}],limitations:['SYNTHETIC descriptive fixture; not tactical proof']};
 }

 try{
  await page.goto(base+'/review-queue');await page.fill('#rq-token',token);await page.click('#rq-connect');await page.waitForSelector('#rq-card:visible');
  checks.push('normal-queue-authenticated');
  await page.evaluate(()=>{document.querySelector('#rq-approve').click();document.querySelector('#rq-reject').click();});
  assert.equal(decisions,0);checks.push('untrusted-click-no-decisions');
  const denied=await page.request.post(base+'/dev/v1/knowledge/proposals/'+view.candidates[0].candidate_id+'/decisions',{headers:{Authorization:'Bearer '+token},data:{selected_version:view.candidates[0].selected_version,expected_version:view.candidates[0].selected_version,decision:'REVIEWED',patch_range:'SYNTHETIC-1',applicability:view.candidates[0].proposal.applicability}});
  assert.equal(denied.status(),403);checks.push('normal-automation-decision403');
  await page.route('**/dev/v1/pregame/review-queue',route=>route.fulfill({json:view}));
  await page.click('#rq-refresh');await page.waitForFunction(()=>document.querySelector('#rq-sources').textContent.includes('SYNTHETIC archived excerpt'));
  for(const width of [1280,1600]){
   await page.setViewportSize({width,height:844});await page.evaluate(()=>window.scrollTo(0,0));
   const geometry=await page.evaluate(()=>{
    const box=id=>{const r=document.querySelector(id).getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,bottom:r.bottom};};
    return {card:box('#rq-card'),conditions:box('#rq-conditions'),sources:box('#rq-sources'),statistics:box('#rq-statistics'),viewport:innerHeight,scroll:document.documentElement.scrollWidth,width:innerWidth,statisticsTable:box('#rq-statistics table'),sourceExcerpt:box('#rq-sources blockquote'),closedEvidence:document.querySelectorAll('#rq-sources details:not([open])').length};
   });
   assert(geometry.card.width>=width-100,'PC candidate must use the available desktop width');
   assert(geometry.conditions.x<geometry.sources.x&&geometry.sources.x<geometry.statistics.x,'conditions, source excerpt and statistics must be adjacent desktop columns');
   assert(Math.abs(geometry.conditions.y-geometry.sources.y)<30&&Math.abs(geometry.sources.y-geometry.statistics.y)<30,'all evidence starts in the same desktop row');
   assert(geometry.sources.y+80<geometry.viewport&&geometry.statistics.y+80<geometry.viewport,'source excerpt and comparison are immediately in view');
   assert(geometry.statisticsTable.bottom<=geometry.viewport,'first comparison table must be in the initial desktop viewport');assert(geometry.sourceExcerpt.y+28<=geometry.viewport,'first source excerpt line must be immediately visible');assert.equal(geometry.closedEvidence,0);assert(geometry.scroll<=geometry.width);checks.push('pc-visible-evidence-grid-'+width);if(process.env.RQ_BROWSER_SCREENSHOTS)await page.screenshot({path:process.env.RQ_BROWSER_SCREENSHOTS+'/desktop-'+width+'.png',fullPage:true});
  }
  await page.setViewportSize({width:390,height:844});const mobile=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));assert(mobile.scroll<=mobile.width);checks.push('mobile-rich-evidence-no-overflow');if(process.env.RQ_BROWSER_SCREENSHOTS)await page.screenshot({path:process.env.RQ_BROWSER_SCREENSHOTS+'/mobile-390.png',fullPage:true});
  await page.setViewportSize({width:1440,height:1000});
  await page.route('**/dev/v1/knowledge/proposals/*/decisions',async route=>{
   const b=route.request().postDataJSON();const current=view.candidates[0];assert.equal(b.selected_version,current.selected_version);assert.equal(b.expected_version,current.selected_version);
   decisions++;const saved={...current.proposal,version:'fixture-decision-'+decisions,review_state:b.decision,review_decision:{actor:'TEST_FIXTURE',selected_version:b.selected_version}};
   view={...view,candidates:view.candidates.slice(1),progress:{...view.progress,ready:view.progress.ready-1,pending:view.progress.pending-1,[b.decision==='REVIEWED'?'reviewed':'rejected']:view.progress[b.decision==='REVIEWED'?'reviewed':'rejected']+1}};
   await route.fulfill({status:201,json:saved});
  });
  await page.route('**/dev/v1/pregame/candidates',async route=>{
   const body=route.request().postDataJSON();const old=view.candidates[0];assert.equal(body.expected_version,old.selected_version);assert.equal(body.rule_id,old.candidate_id);
   const response=await route.fetch();assert.equal(response.status(),201);const saved=await response.json();
   view={...view,candidates:[{...old,proposal:saved.proposal,spec:saved.spec,selected_version:saved.proposal.version,claim:saved.proposal.claim,patch_range:saved.proposal.patch_range},...view.candidates.slice(1)]};
   await route.fulfill({response});
  });
  page.on('dialog',dialog=>dialog.accept());
  for(let i=0;i<10;i++){
   const selected=view.candidates[0].selected_version;
   const response=page.waitForResponse(r=>r.url().endsWith('/decisions')&&r.request().method()==='POST');
   if(i===4){await page.click('#rq-editor summary');await page.fill('#rq-edit-claim','SYNTHETIC edited fixture claim');await page.click('#rq-edit-approve');}
   else await page.click(i%2?'#rq-reject':'#rq-approve');await response;userEvents++;
   await page.waitForFunction(v=>!document.querySelector('#rq-card').dataset.version||document.querySelector('#rq-card').dataset.version!==v,selected);
  }
  assert.equal(decisions,10);assert.equal(userEvents,10);assert.equal(view.candidates.length,0);checks.push('ten-sequential-native-fixture-decisions-and-requery','edit-approve-preserves-proposal-lineage');
  await page.reload();await page.waitForSelector('#rq-workspace:visible');assert.match(await page.locator('#rq-empty').innerText(),/검토/);checks.push('requery-empty-state');
  await page.unroute('**/dev/v1/pregame/review-queue');await page.unroute('**/dev/v1/knowledge/proposals/*/decisions');await page.click('#rq-refresh');await page.waitForSelector('#rq-card:visible');
  const revision=await page.locator('#rq-card').getAttribute('data-version');await page.click('#rq-later');await page.waitForFunction(v=>document.querySelector('#rq-card').dataset.version!==v,revision);
  await page.reload();await page.waitForSelector('#rq-card:visible');await page.check('#rq-show-later');await page.waitForFunction(v=>document.querySelector('#rq-card').dataset.version===v,revision);checks.push('later-persists-and-revisitable');
  await page.uncheck('#rq-show-later');await page.click('#rq-later');await page.check('#rq-show-later');await page.waitForFunction(()=>document.querySelector('#rq-progress').textContent.includes('나중에 2'));
  const firstDeferred=await page.locator('#rq-card').getAttribute('data-version');await page.click('#rq-next');const secondDeferred=await page.locator('#rq-card').getAttribute('data-version');assert.notEqual(secondDeferred,firstDeferred);await page.click('#rq-previous');assert.equal(await page.locator('#rq-card').getAttribute('data-version'),firstDeferred);checks.push('multiple-deferred-navigation');
  await page.click('#rq-later');await page.waitForFunction(v=>document.querySelector('#rq-card').dataset.version!==v,firstDeferred);assert.equal(await page.locator('#rq-card').getAttribute('data-version'),secondDeferred);checks.push('later-on-deferred-rotates');
  await page.uncheck('#rq-show-later');
  let releaseHeld,heldReady;const gate=new Promise(r=>releaseHeld=r),ready=new Promise(r=>heldReady=r);let requests=0;
  const stale={...fixture,candidates:[{...fixture.candidates[0],claim:'RQ stale response'}]},fresh={...fixture,candidates:[{...fixture.candidates[0],claim:'RQ newest response'}]};
  await page.route('**/dev/v1/pregame/review-queue',async route=>{requests++;if(requests===1){heldReady();await gate;await route.fulfill({json:stale});}else await route.fulfill({json:fresh});});
  await page.click('#rq-refresh');await ready;await page.click('#rq-refresh');await page.waitForFunction(()=>document.querySelector('#rq-claim').textContent==='RQ newest response');
  const released=page.waitForResponse(r=>r.url().endsWith('/review-queue'));releaseHeld();await released;await page.waitForLoadState('networkidle');await page.check('#rq-show-later');await page.uncheck('#rq-show-later');assert.equal(await page.locator('#rq-claim').innerText(),'RQ newest response');checks.push('held-old-refresh-cannot-replace-new-queue');
  await page.unroute('**/dev/v1/pregame/review-queue');await page.click('#rq-refresh');await page.waitForLoadState('networkidle');
  const auth={Authorization:'Bearer '+token};
  for(let i=0;i<19;i++){
   const spec=structuredClone(fixture.candidates[0].spec);spec.rule_id='RQ-SYNTHETIC-PAGE-'+i;spec.output.text='SYNTHETIC page fixture '+i;
   const saved=await page.request.post(base+'/dev/v1/pregame/candidates',{headers:auth,data:{spec}});assert.equal(saved.status(),201);const proposal=(await saved.json()).proposal;
   const deferred=await page.request.post(base+'/dev/v1/pregame/review-queue/later',{headers:auth,data:{candidate_id:proposal.rule_id,selected_version:proposal.version}});assert.equal(deferred.status(),200);
  }
  const actualQueue=await (await page.request.get(base+'/dev/v1/pregame/review-queue',{headers:auth})).json();assert.equal(actualQueue.progress.deferred,21);assert.equal(actualQueue.pagination.later_pages,2);
  const refreshed=page.waitForResponse(r=>r.url().endsWith('/review-queue'));await page.click('#rq-refresh');await refreshed;await page.waitForFunction(()=>document.querySelector('#rq-progress').textContent.includes('나중에 21'));await page.check('#rq-show-later');assert.match(await page.locator('#rq-page-position').innerText(),/1 \/ 2/);
  const pageResponse=page.waitForResponse(r=>r.url().endsWith('/review-queue/page'));await page.click('#rq-page-next');await pageResponse;await page.waitForFunction(()=>document.querySelector('#rq-page-position').textContent.startsWith('2 / 2'));assert.match(await page.locator('#rq-position').innerText(),/1 \/ 1/);
  const backResponse=page.waitForResponse(r=>r.url().endsWith('/review-queue'));await page.click('#rq-page-previous');await backResponse;await page.waitForFunction(()=>document.querySelector('#rq-page-position').textContent.startsWith('1 / 2'));checks.push('twenty-first-deferred-candidate-page-navigation');
  for(const width of [390,1280]){await page.setViewportSize({width,height:844});const geometry=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));assert(geometry.scroll<=geometry.width);checks.push('layout-'+width);}
  await page.click('#rq-export');const exported=await page.locator('#rq-export-text').inputValue();assert(!exported.includes('resource_id'));assert(!exported.includes(token));checks.push('safe-text-export');
  assert.equal(await page.evaluate(()=>sessionStorage.getItem('lol-coach-dev-token')),token,'review login must share the app session token');
  await page.evaluate(t=>sessionStorage.setItem('pregame-token',t),token);
  await page.unroute('**/dev/v1/pregame/candidates');await page.goto(base+'/pregame');await page.waitForSelector('#pg-workspace:visible');checks.push('review-login-shared-pregame-autoauth');
  await page.click('#pg-logout');await page.waitForSelector('#pg-auth:visible');assert.equal(await page.evaluate(()=>sessionStorage.getItem('lol-coach-dev-token')),null);
  await page.goto(base+'/review-queue');await page.waitForLoadState('networkidle');assert(await page.locator('#rq-auth').isVisible());assert(!(await page.locator('#rq-workspace').isVisible()));
  assert.equal(await page.evaluate(()=>sessionStorage.getItem('pregame-token')),null);assert.equal(await page.evaluate(()=>sessionStorage.getItem('lol-coach-dev-token')),null);checks.push('pregame-logout-clears-review-auth-and-legacy-token');
  assert.equal(errors.length,0);checks.push('no-page-errors');
  process.stdout.write(JSON.stringify({passed:true,checks,decision_requests:decisions,simulated_actor:'TEST_FIXTURE',actual_user_web_decisions:0})+'\n');
 }catch(e){process.stderr.write(JSON.stringify({notice:await page.locator('#rq-notice').textContent(),errors})+'\n');throw e;}finally{await browser.close();}
})().catch(e=>{process.stderr.write(String(e.stack||e));process.exitCode=1;});
'''


def main():
    from datetime import datetime,timezone
    from scripts.browser_pregame import hashes as pregame_hashes
    def source_hashes():
        result=pregame_hashes()
        for path in (ROOT/'config').glob('*.json'):result[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
        return result
    before=source_hashes()
    output=ROOT/'evidence/queue/v20'/('review-browser-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    output.mkdir(parents=True)
    from coach_v1 import pregame_server as module
    from coach_v1.pregame_contract import parse_rule,proposal_rule
    from coach_v1.review_queue import queue_response
    from coach_v1.server import Limits
    from tests_pregame.test_contract import rule
    with tempfile.TemporaryDirectory(prefix='rq-v20-synthetic-') as td:
        private=Path(td);token=secrets.token_urlsafe(32);tokenfile=private/'token';tokenfile.write_text(token);tokenfile.chmod(0o600)
        server=module.PregameWorkbench(private/'work.sqlite',token,Limits(1_000_000,100,100,100,100,10))
        original=module.candidate_specs;module.candidate_specs=lambda:[]
        try:
            for i in range(10):
                spec=rule();spec['rule_id']='RQ-SYNTHETIC-'+str(i);spec['output']['text']='SYNTHETIC queue fixture '+str(i);spec=parse_rule(spec).model_dump(mode='json')
                source=server.research.add('RAW_DIAGNOSTIC','SYNTHETIC queue fixture',dict(schema_version='pregame.rule-source.v1',spec=spec))
                note=server.research.put_note(source['id'],'overview',dict(known='SYNTHETIC',intention='UI test only',alternative='',outcome='No approval'),0)
                server.research.propose(proposal_rule(spec),dict(resource_id=source['id'],anchor='overview',note_revision=note['revision']),max_bytes=1_000_000)
            fixture=private/'fixture.json';fixture.write_text(json.dumps(queue_response(server)))
            script=private/'browser.cjs';script.write_text(BROWSER)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            env=dict(os.environ,RQ_BROWSER_SCREENSHOTS=str(output),RQ_FIXTURE=str(fixture),WORKBENCH_TOKEN_FILE=str(tokenfile),WORKBENCH_URL='http://127.0.0.1:'+str(server.server_port),NODE_PATH=os.environ.get('NODE_PATH','/opt/codex/cua_node/lib/node_modules'),CHROMIUM_EXECUTABLE=os.environ.get('CHROMIUM_EXECUTABLE','/usr/bin/chromium'))
            result=subprocess.run(['node',str(script)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=120)
            with server.research._db() as db:
                rows=db.execute('SELECT payload FROM knowledge_rules').fetchall()
            actual=sum(json.loads(row[0]).get('schema_version')=='knowledge-decision.v1' for row in rows)
            receipt=json.loads(result.stdout.strip() or '{}');receipt['actual_user_web_decisions']=actual
            receipt['source_sha256']=source_hashes();receipt['sources_unchanged']=before==receipt['source_sha256']
            receipt['passed']=bool(receipt.get('passed')) and result.returncode==0 and actual==0 and receipt['sources_unchanged']
            receipt['git_head']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
            receipt['github_binding']={k:os.environ.get(k) for k in ('GITHUB_SHA','GITHUB_RUN_ID','GITHUB_REPOSITORY')}
            receipt['scope']='SYNTHETIC simulated TEST_FIXTURE decisions only; actual USER_WEB0; not coaching accuracy'
            receipt['coaching_accuracy']=None
            (output/'runner.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
            (output/'browser.log').write_text((result.stdout+result.stderr).replace(token,'[REDACTED]'))
            print(json.dumps(dict(passed=receipt['passed'],evidence_directory=str(output))))
            if result.stderr:print(result.stderr.replace(token,'[REDACTED]'),file=sys.stderr)
            if actual:raise RuntimeError('Synthetic browser must not write USER_WEB decision records')
            return 0 if receipt['passed'] else 1
        finally:
            server.shutdown();server.server_close();module.candidate_specs=original


if __name__=='__main__':raise SystemExit(main())

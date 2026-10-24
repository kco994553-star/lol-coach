"""Actual shipped DOM, separate from historical widget regression fixtures."""
import json,subprocess
from pathlib import Path
JS=r'''
const fs=require('fs'),assert=require('node:assert/strict'),{chromium}=require('playwright');
(async()=>{
const b=await chromium.launch({executablePath:process.env.CHROMIUM_EXECUTABLE,args:['--no-sandbox']}),results=[];
for(const [device,url,width,height] of [['desktop',process.env.LOADING_PC+'/loading',1440,1000],['mobile',process.env.LOADING_WEB+'/lol-coach/loading.html',390,844]]){
 const p=await b.newPage({viewport:{width,height},reducedMotion:'reduce'}),errors=[];p.on('pageerror',e=>errors.push(e.message));
 await p.goto(url);await p.locator('#analyze:enabled').waitFor();assert.equal(await p.locator('body').getAttribute('data-gameplan-view'),'current');
 await p.locator('#example-0').click();await p.locator('#analyze').click();await p.locator('.plan-title').waitFor();
 assert.equal(await p.locator('#loading-legacy-details,#loading-summary,#lane-table,#scenario-content').count(),0);
 assert.equal(await p.locator('.plan-overview-comparison tbody tr').count(),4);
 for(const phase of ['lane','operations','fight']){
  assert.equal(await p.locator('[data-basic-phase='+phase+'] .plan-basic-actions li').count(),5);
  assert(await p.locator('[data-basic-coaching='+phase+'] p').count()>0);
  await p.locator('[data-plan-more='+phase+']').click();
  assert.equal(await p.locator('.plan-retained,[data-coach-focus=legacy-open]').count(),0);
  assert.equal(await p.locator('[data-action-summary='+phase+'] li').count(),5);
  await p.locator('[data-coach-focus=close-detail]').click();await p.locator('.plan-detail').waitFor({state:'hidden'});
 }
 const baseline=await p.locator('[data-basic-phase=lane]').textContent();
 await p.locator('[data-plan-more=lane]').click();await p.locator('details[id$="-conditions"] > summary').click();
 assert.equal(await p.locator('[data-coach-focus="risk-LOSS_LIMIT"]').count(),1);
 await p.locator('[data-coach-focus="risk-LOSS_LIMIT"]').click();assert.match(p.url(),/LOSS_LIMIT/);await p.locator('[data-coach-focus="risk-BALANCED"]').click();
 await p.locator('[data-coach-focus=planning-income]').selectOption('LOSING');
 assert.match(p.url(),/LOSING/);assert.notEqual(await p.locator('[data-basic-phase=lane]').textContent(),baseline);await p.locator('[data-coach-focus=reset-scenario]').click();assert(!p.url().includes('LOSING'));assert.equal(await p.locator('[data-basic-phase=lane]').textContent(),baseline);
 await p.locator('[data-coach-focus=current-period]').selectOption('LEVEL2');
 assert.equal(await p.locator('.plan-layout').getAttribute('data-period'),'LEVEL2');
 const shared=p.url(),saved=await p.locator('[data-basic-phase=lane]').textContent();const fresh=await b.newPage({viewport:{width,height}});await fresh.goto(shared);await fresh.locator('.plan-detail').waitFor();assert.equal(await fresh.locator('[data-basic-phase=lane]').textContent(),saved);await fresh.close();
 await p.reload();await p.locator('.plan-detail').waitFor();assert.equal(await p.locator('.plan-layout').getAttribute('data-period'),'LEVEL2');
 await p.locator('[data-coach-focus=close-detail]').click();await p.locator('.plan-detail').waitFor({state:'hidden'});
 await p.screenshot({path:process.env.LOADING_OUT+'/'+device+'-current-gameplan.png'});
 assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
 await p.locator('[data-plan-edit]').click();await p.locator('#own-champion').selectOption('Sejuani');await p.locator('#own-position').selectOption('JUNGLE');await p.locator('#analyze').click();
 assert.match(await p.locator('[data-basic-phase=lane] h3').innerText(),/초반 정글/);
 assert.match(await p.locator('[data-basic-phase=operations] h3').innerText(),/중반 운영/);
 await p.locator('[data-plan-edit]').click();await p.locator('#pick-ALLY-0').fill('');assert(await p.locator('#loading-results').isHidden());
 assert.deepEqual(errors,[]);results.push({device,currentDOM:true,fiveActions:true,conditionsReset:true,periodRestore:true,jungleLabels:true,staleHidden:true,errors});await p.close();
}
await b.close();console.log(JSON.stringify({passed:true,results,real_coaching_n:0}));
})().catch(e=>{console.error(e);process.exit(1)});
'''
def run(env,out):
    probe=Path(out)/'current-gameplan.cjs';probe.write_text(JS)
    r=subprocess.run(['node',str(probe)],env=env,text=True,capture_output=True,timeout=90)
    (Path(out)/'current-gameplan.log').write_text(r.stdout+r.stderr)
    if r.returncode:raise AssertionError(r.stderr[-5000:])
    result=json.loads(r.stdout);assert result['passed'];return result

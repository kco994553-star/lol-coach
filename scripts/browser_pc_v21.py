"""Isolated synthetic input → real HTTP evaluator → actual Chromium PC UI proof."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

BROWSER=r'''
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {chromium}=require('playwright');
const token=fs.readFileSync(process.env.PC_TOKEN_FILE,'utf8').trim();
const base=process.env.PC_URL, output=process.env.PC_OUTPUT;
const fixture=JSON.parse(fs.readFileSync(process.env.PC_FIXTURE,'utf8'));
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_EXECUTABLE||'/usr/bin/chromium',args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 const errors=[],checks=[],timings=[];let previews=0,objections=0;
 let connection={status:'MANUAL_FALLBACK',reason:'SYNTHETIC_NO_GAME_CLIENT',phase:null,revision:0,input:null};
 page.on('pageerror',e=>errors.push(e.message));
 page.on('request',request=>{assert(!request.url().includes(token),'token must never enter request URL');if(request.url().endsWith('/pc-preview'))previews++;if(request.url().endsWith('/pc-objection'))objections++;});
 await page.route('**/dev/v1/pregame/pc-status',async route=>{
   assert.equal(route.request().headers().authorization,'Bearer '+token);
   await route.fulfill({json:{connection,review_summary:fixture.review_summary,weekly_report:fixture.weekly_report}});
 });
 async function waitStage(stage){await page.waitForFunction(s=>document.querySelector('#pc-stage').textContent===s,stage);}
 async function measuredInput(selector,value,stage){
   await page.evaluate(()=>{
     const target=document.querySelector('#pc-cards');window.pcMeasurement={start:null,end:null};
     const handler=()=>{window.pcMeasurement.start=performance.now();document.querySelector('#pc-draft').removeEventListener('input',handler,true);};
     document.querySelector('#pc-draft').addEventListener('input',handler,true);
     const observer=new MutationObserver(()=>{if(target.children.length && window.pcMeasurement.start!==null){requestAnimationFrame(()=>{window.pcMeasurement.end=performance.now();});observer.disconnect();}});
     observer.observe(target,{childList:true,subtree:true});
   });
   await page.fill(selector,value);await waitStage(stage);
   await page.waitForFunction(()=>window.pcMeasurement.end!==null);
   timings.push({input:selector,stage,input_to_card_ms:await page.evaluate(()=>Number((pcMeasurement.end-pcMeasurement.start).toFixed(2)))});
 }
 try{
   await page.goto(base+'/pc#token='+encodeURIComponent(token));
   await page.waitForSelector('#pc-workspace:visible');assert.equal(new URL(page.url()).hash,'');assert(!page.url().includes(token));checks.push('fragment-consumed-before-http-and-authenticated');
   await page.selectOption('#pc-position','BOTTOM');await page.fill('#pc-patch','16.20');
   await measuredInput('#pc-own','Caitlyn','내 픽');
   await measuredInput('#pc-laner','Ezreal','상대 라인');
   await measuredInput('#pc-jungler','LeeSin','적 정글');
   await page.locator('#pc-composition summary').click();
   for(const [side,role,champion] of [['ALLY','TOP','Ornn'],['ALLY','JUNGLE','Sejuani'],['ALLY','MID','Ahri'],['ALLY','SUPPORT','Lux'],['ENEMY','TOP','Fiora'],['ENEMY','MID','Zed']])await page.fill('#pc-team-'+side+'-'+role,champion);
   await measuredInput('#pc-team-ENEMY-SUPPORT','Nautilus','조합');checks.push('strict-partial-ten-slot-own-laner-jungle-composition');
   assert(await page.locator('.coach-card').count()>0);
   assert.equal(await page.locator('.coach-card details[open]').count(),0);
   assert(await page.locator('.evidence.AUTO_VERIFIED').count()>0);
   assert(await page.locator('.evidence.OFFICIAL').count()>0);
   assert(await page.locator('.coach-card').evaluateAll(cards=>cards.every(c=>c.querySelectorAll('.card-lines p').length<=3 && c.querySelector('.evidence'))));
   assert(await page.locator('.card-lines p').evaluateAll(lines=>lines.every(line=>line.getBoundingClientRect().height<=parseFloat(getComputedStyle(line).lineHeight)+1)),'preview entries must each occupy at most one visible line');
   await page.locator('.coach-card details summary').first().click();
   assert(await page.locator('.coach-card details[open] a').count()>0);
   assert(await page.locator('.sources a').evaluateAll(links=>links.every(a=>a.protocol==='https:' && a.rel.includes('noopener') && !new URL(a.href).username)));
   assert.equal(await page.locator('#pc-cards > .coach-card .evidence.AUTO_VERIFIED').count(),3);
   assert.equal(await page.locator('#pc-cards > .coach-card [data-card-id]').count(),0);
   assert.equal(await page.locator('#pc-cards > .coach-card[data-card-id="official-Caitlyn"]').count(),1);
   assert.equal(await page.locator('.more-cards:not([open])').count(),1);
   assert(await page.locator('.more-cards .coach-card').count()>0);
   await page.locator('.more-cards > summary').click();assert(await page.locator('.more-cards .coach-card').first().isVisible());await page.locator('.more-cards > summary').click();
   await page.locator('#pc-weekly > summary').click();
   assert.equal(await page.locator('#pc-weekly-items li').count(),fixture.weekly_report.items.length);
   for(const item of fixture.weekly_report.items)assert((await page.locator('#pc-weekly-items').innerText()).includes(item.summary));
   await page.locator('#pc-weekly > summary').click();
   assert(!(await page.locator('#pc-workspace').innerText()).includes('MATCHING_ARCHIVE'));
   checks.push('three-line-evidence-first-expandable-safe-sources','three-relevant-tactics-own-reference-and-discoverable-other-cards','actual-weekly-report-summaries-up-to-five-and-korean-statuses');
   const objectionButton=page.locator('.objection').first();const candidate=await objectionButton.evaluate(b=>b.closest('[data-candidate-id]').dataset.candidateId);
   await objectionButton.evaluate(b=>b.click());assert.equal(objections,0);checks.push('programmatic-click-cannot-object');
   page.once('dialog',dialog=>dialog.accept('SYNTHETIC TEST_FIXTURE objection; not a real user decision'));
   await objectionButton.click();
   await page.waitForFunction(id=>![...document.querySelectorAll('[data-candidate-id]')].some(c=>c.dataset.candidateId===id),candidate);
   await waitStage('조합');assert.equal(objections,1);checks.push('native-click-objection-real-local-post-immediate-exclusion');
   const stored=await page.request.post(base+'/dev/v1/pregame/pc-preview',{headers:{Authorization:'Bearer '+token},data:{input:fixture.input,draft_revision:100}});
   assert.equal(stored.status(),200);assert(!(await stored.json()).cards.some(c=>c.candidate_id===candidate));checks.push('objection-persists-in-new-projection');
   // Observe response supersession while the earlier real server result is held.
   let release,ready;const gate=new Promise(r=>release=r),started=new Promise(r=>ready=r);let held=false;
   await page.route('**/dev/v1/pregame/pc-preview',async route=>{
     if(!held){held=true;const response=await route.fetch();const result=await response.json();result.cards=result.cards.map(c=>({...c,title:'STALE_RESPONSE_SENTINEL'}));ready();await gate;try{await route.fulfill({response,json:result});}catch(_){} }
     else await route.continue();
   });
   await page.fill('#pc-own','Annie');await started;
   await page.fill('#pc-own','Caitlyn');await waitStage('조합');
   release();await page.waitForTimeout(150);assert(!(await page.locator('#pc-cards').innerText()).includes('STALE_RESPONSE_SENTINEL'));
   await page.unroute('**/dev/v1/pregame/pc-preview');checks.push('held-old-response-cannot-overwrite-edits');
   // LCU status is explicitly synthetic; previews continue through the real API.
   connection={status:'CONNECTED',reason:null,phase:'ChampSelect',revision:1,input:structuredClone(fixture.input)};
   connection.input.patch=null;connection.input.my_champion='Annie';connection.input.slots.find(s=>s.side==='ALLY'&&s.slot===4).champion='Annie';
   await page.check('#pc-auto');await page.waitForSelector('[data-card-id="official-Annie"]');
   assert.match(await page.locator('#pc-input-mode').innerText(),/패치는 수동 미검증/);
   const beforeSameRevision=previews;await page.waitForTimeout(1150);assert.equal(previews,beforeSameRevision);checks.push('same-lcu-revision-does-not-request-preview-and-manual-patch-preserved');
   connection={...connection,revision:2,input:structuredClone(fixture.input)};
   await page.waitForSelector('[data-card-id="official-Caitlyn"]');assert.equal(await page.locator('#pc-own').inputValue(),'Caitlyn');
   connection={status:'MANUAL_FALLBACK',reason:'PHASE_CHANGED',phase:'UNKNOWN',revision:3,input:null};
   await page.waitForFunction(()=>document.querySelector('#pc-cards').children.length===0);
   assert.equal(await page.locator('#pc-own').inputValue(),'Caitlyn');assert.equal(await page.locator('#pc-patch').inputValue(),'16.20');checks.push('lcu-unknown-clears-cards-preserves-manual-form');
   await page.uncheck('#pc-auto');await waitStage('조합');
   connection={status:'MANUAL_FALLBACK',reason:'NOT_CHAMP_SELECT',phase:'InProgress',revision:4,input:null};
   await page.waitForFunction(()=>document.querySelector('#pc-cards').children.length===0);await page.click('#pc-refresh');
   await page.waitForTimeout(150);assert.equal(await page.locator('.coach-card').count(),0);checks.push('game-start-clears-and-blocks-dynamic-cards');
   connection={status:'MANUAL_FALLBACK',reason:'SYNTHETIC_NO_GAME_CLIENT',phase:null,revision:5,input:null};
   await page.waitForTimeout(650);await page.uncheck('#pc-pregame');await page.waitForFunction(()=>document.querySelector('#pc-phase').textContent==='단계 미확인');
   assert.equal(await page.locator('.evidence.AUTO_VERIFIED,.evidence.HYPOTHESIS,.evidence.USER,.evidence.STATISTICS').count(),0);checks.push('manual-unknown-phase-hides-tactics');
   await page.check('#pc-pregame');await waitStage('조합');
   for(const width of [1440,1280,390]){
     await page.setViewportSize({width,height:1000});
     assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
     await page.screenshot({path:output+'/pc-'+width+'.png',fullPage:true});checks.push('layout-no-overflow-'+width);
   }
   // A pending preview must not restore content after logout.
   let logoutRelease,logoutReady;const logoutGate=new Promise(r=>logoutRelease=r),logoutStarted=new Promise(r=>logoutReady=r);
   await page.route('**/dev/v1/pregame/pc-preview',async route=>{const response=await route.fetch();logoutReady();await logoutGate;try{await route.fulfill({response});}catch(_){} });
   await page.fill('#pc-own','Ashe');await logoutStarted;await page.click('#pc-logout');logoutRelease();
   await page.waitForTimeout(150);assert(await page.locator('#pc-auth').isVisible());assert.equal(await page.locator('.coach-card').count(),0);
   assert.equal(await page.evaluate(()=>sessionStorage.getItem('lol-coach-dev-token')),null);checks.push('logout-invalidates-pending-preview-and-clears-key');
   assert.equal(errors.length,0);checks.push('no-browser-errors');
   process.stdout.write(JSON.stringify({passed:true,checks,timings,preview_requests:previews,objection_requests:objections,scope:'SYNTHETIC input and LCU fixture; real local HTTP evaluator and Chromium rendering; no actual Windows or League client proof',actual_user_approvals_created:0})+'\n');
 }catch(error){process.stderr.write(JSON.stringify({errors,notice:await page.locator('#pc-notice').textContent(),stage:await page.locator('#pc-stage').textContent()})+'\n');throw error;}finally{await browser.close();}
})().catch(error=>{process.stderr.write(String(error.stack||error));process.exitCode=1;});
'''


def main():
    from scripts.launch_pc import create_server
    from tests_pregame.test_pc_coach import draft
    from coach_v1.pc_coach import preview
    from coach_v1.pc_runtime import pc_status
    output=ROOT/'evidence/queue/v21'/('pc-browser-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    output.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix='pc-v21-synthetic-') as temporary:
        private=Path(temporary)
        server=create_server(private,port=0)
        try:
            sample=draft();fixture=preview(server,dict(input=sample,draft_revision=0))
            (private/'fixture.json').write_text(json.dumps(dict(input=sample,review_summary=fixture['review_summary'],weekly_report=pc_status(server)['weekly_report'])),encoding='utf-8')
            (private/'browser.cjs').write_text(BROWSER,encoding='utf-8')
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            env=dict(os.environ,PC_TOKEN_FILE=str(private/'access-token'),PC_FIXTURE=str(private/'fixture.json'),PC_OUTPUT=str(output),PC_URL='http://127.0.0.1:'+str(server.server_port),NODE_PATH=os.environ.get('NODE_PATH','/opt/codex/cua_node/lib/node_modules'))
            result=subprocess.run(['node',str(private/'browser.cjs')],cwd=ROOT,env=env,capture_output=True,text=True,timeout=120)
            receipt=json.loads(result.stdout.strip() or '{}')
            receipt['passed']=bool(receipt.get('passed')) and result.returncode==0
            receipt['actual_windows_lcu']='BLOCKED_EXTERNAL'
            receipt['source_sha256']={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in [ROOT/'web_r4'/name for name in ('pc.html','pc.js','pc.css')]}
            receipt['git_head']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
            receipt['actual_user_approvals_created']=len(server.research.list())
            if receipt['actual_user_approvals_created']:receipt['passed']=False
            (output/'runner.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            (output/'browser.log').write_text((result.stdout+result.stderr).replace(server.token,'[REDACTED]'),encoding='utf-8')
            print(json.dumps(dict(passed=receipt['passed'],evidence_directory=str(output))))
            if result.stderr:print(result.stderr.replace(server.token,'[REDACTED]'),file=sys.stderr)
            return 0 if receipt['passed'] else 1
        finally:
            server.shutdown();server.server_close()


if __name__=='__main__':
    raise SystemExit(main())

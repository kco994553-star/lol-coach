'use strict';
// Chromium executes the production UI. Intercepted API responses control the
// transport ordering; fixtures are isolated and send no review decisions.
const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const root=path.resolve(__dirname,'..');
const roles=['TOP','JUNGLE','MID','BOTTOM','SUPPORT'];
const deferred=()=>{let resolve;const promise=new Promise(r=>{resolve=r});return {promise,resolve};};
const cell=key=>({key,title:key,status:'UNKNOWN',texts:[],reasons:['NO_APPLICABLE_REVIEWED_RULE'],rules:[],outlook:null,cooldowns:[]});
const copy=value=>JSON.parse(JSON.stringify(value));
const hash=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
async function scenario(browser,name,{heldRead=false,revertRole=false,ambiguous=false}={}){
  const context=await browser.newContext();
  try{
    const page=await context.newPage();page.setDefaultTimeout(5000);
    const errors=[],calls=[],writeReceived=deferred(),readReceived=deferred();
    let saved=null,storedPlan=null,putRoute=null,held=null;
    page.on('pageerror',e=>errors.push(e.message));
    await page.route('http://localhost/**',async route=>{
      const req=route.request(),url=new URL(req.url()),pathname=url.pathname;
      const asset=pathname==='/pregame'?'pregame.html':path.basename(pathname);
      if(['pregame.html','pregame.js','pregame.css','pregame-icon.svg'].includes(asset))return route.fulfill({contentType:asset.endsWith('.html')?'text/html':asset.endsWith('.js')?'text/javascript':asset.endsWith('.css')?'text/css':'image/svg+xml',body:fs.readFileSync(path.join(root,'web_r4',asset),'utf8')});
      const method=req.method(),body=req.postDataJSON();calls.push({path:pathname,method,body});
      let data=[];
      if(pathname.endsWith('/status'))data={mode:'PRE_GAME',automatic_collection:'UNAVAILABLE',current_patch:null,knowledge_count:0,accuracy:null};
      if(pathname.endsWith('/roster'))data={static_version:null,champions:[]};
      if(pathname.endsWith('/inputs')&&method==='POST')data=saved={schema_version:'pregame.input.v1',id:'b'.repeat(32),session_id:'a'.repeat(32),revision:1,parent_id:null,created_at:'2026-10-11T00:00:00Z',input:body.input,input_sha256:'c'.repeat(64)};
      else if(pathname.endsWith('/inputs'))data=saved?[{session_id:saved.session_id,title:saved.input.title,revision:saved.revision,input_sha256:saved.input_sha256}]:[];
      if(pathname==='/dev/v1/pregame/inputs/'+'a'.repeat(32)&&method==='PUT'){
        putRoute={route,body,request:req};writeReceived.resolve();
        if(ambiguous){await route.abort('failed');return;}
        return; // Release from the test after the overlapping history click.
      }
      if(pathname.endsWith('/history'))data=saved?[saved]:[];
      if(pathname.endsWith('/plans')&&method==='POST')data=storedPlan={schema_version:'pregame.plan.v1',mode:'PRE_GAME',id:'d'.repeat(32),session_id:saved.session_id,revision:1,input_revision:1,input_sha256:saved.input_sha256,created_at:'2026-10-11T00:00:00Z',validity:'CURRENT',expiry_reasons:[],input:copy(saved.input),common:{map:roles.map(cell),jungle:cell('JUNGLE'),composition:cell('COMPOSITION')},personal:{role:cell('ROLE'),lane:cell('LANE'),fight:cell('FIGHT')},changes:cell('CHANGES'),evaluations:[],knowledge_fingerprint:'e'.repeat(64),coaching_accuracy:null,real_match_validation:'NOT_EVALUATED'};
      else if(pathname.endsWith('/plans'))data=storedPlan?[{...storedPlan,validity:saved.revision===1?'CURRENT':'EXPIRED',expiry_reasons:saved.revision===1?[]:['INPUT_REVISION_CHANGED']}]:[];
      if(pathname==='/dev/v1/pregame/plans/'+'d'.repeat(32)){
        const snapshot=copy(storedPlan);
        readReceived.resolve('READ_STARTED');
        if(heldRead){held={route,snapshot,request:req};return;}
        data=snapshot;
      }
      await route.fulfill({contentType:'application/json',body:JSON.stringify(data)});
    });
    await page.goto('http://localhost/pregame');
    await page.fill('#pg-token','isolated-race-fixture-only');await page.click('#pg-login');
    await page.waitForSelector('#pg-workspace:visible');await page.click('#pg-golden');
    await page.click('#pg-save');await page.waitForFunction(()=>!document.getElementById('pg-create-plan').disabled);
    await page.click('#pg-create-plan');await page.waitForSelector('#pg-plan-panel:visible');
    await page.waitForFunction(()=>!document.getElementById('pg-save').disabled);
    await page.getByText('입력·계획 이력',{exact:true}).click();
    const baselineInput=await page.textContent('#pg-input-json');
    await page.click('#pg-save');await writeReceived.promise;
    if(ambiguous)await page.waitForSelector('#pg-retry-save:visible');
    if(revertRole){await page.selectOption('#pg-my-position','TOP');await page.selectOption('#pg-my-position','BOTTOM');}
    const sameBaseline=await page.textContent('#pg-input-json')===baselineInput;
    await page.locator('#pg-plan-list button').click();
    const historyOutcome=await Promise.race([
      readReceived.promise,
      page.waitForFunction(()=>document.getElementById('pg-notice').textContent.includes('진행 중')).then(()=> 'READ_BLOCKED')
    ]);
    if(historyOutcome==='READ_STARTED'&&!heldRead)await page.waitForSelector('#pg-plan-panel:visible');
    const visibleBeforeAck=await page.isVisible('#pg-plan-panel');
    if(!ambiguous){
      saved={...saved,id:'f'.repeat(32),parent_id:saved.id,revision:2,input:copy(putRoute.body.input)};
      await putRoute.route.fulfill({contentType:'application/json',body:JSON.stringify(saved)});
      await page.waitForFunction(()=>document.getElementById('pg-current').textContent.includes('v2')&&!document.getElementById('pg-save').disabled);
    }
    if(held){await held.route.fulfill({contentType:'application/json',body:JSON.stringify(held.snapshot)});const response=await held.request.response();if(response)await response.finished();}
    await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
    const visibleAfterAck=await page.isVisible('#pg-plan-panel');
    const displayed=visibleAfterAck?JSON.parse(await page.textContent('#pg-plan-json')):null;
    const historyRequests=calls.filter(c=>c.path.startsWith('/dev/v1/pregame/plans/')).length;
    const result={name,same_baseline:sameBaseline,write_expected_revision:putRoute.body.expected_revision,write_position:putRoute.body.input.my_position,history_outcome:historyOutcome,held_snapshot_before_ack:held?{input_revision:held.snapshot.input_revision,validity:held.snapshot.validity}:null,visible_before_ack:visibleBeforeAck,visible_after_ack:visibleAfterAck,displayed_after_ack:displayed?{input_revision:displayed.input_revision,validity:displayed.validity}:null,history_requests:historyRequests,acknowledged_revision:ambiguous?1:2,ambiguous_save_retry_available:ambiguous?await page.isVisible('#pg-retry-save'):null,page_errors:errors,decisions_sent:calls.some(c=>c.path.endsWith('/decisions'))};
    result.passed=sameBaseline&&historyOutcome==='READ_BLOCKED'&&!visibleBeforeAck&&!visibleAfterAck&&historyRequests===0&&errors.length===0&&!result.decisions_sent;
    return result;
  }finally{await context.close();}
}
(async()=>{
  const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_EXECUTABLE||'/usr/bin/chromium',args:['--no-sandbox']});
  let results;
  try{results=await Promise.all([
    scenario(browser,'unchanged input: history click during pending PUT'),
    scenario(browser,'role changes then returns to baseline: held history read released after PUT ACK',{revertRole:true,heldRead:true}),
    scenario(browser,'unchanged input: ambiguous save still requires identical-operation retry',{ambiguous:true})
  ]);}finally{await browser.close();}
  const phase=process.env.UI_RACE_PHASE||'check',stamp=new Date().toISOString().replace(/[:.]/g,'-');
  const receipt={executed_at:new Date().toISOString(),phase,scope:'Production UI in Chromium with intercepted isolated API responses; three pending/ambiguous-save races; no server/database changes or approvals',source_sha256:hash(path.join(root,'web_r4/pregame.js')),test_sha256:hash(__filename),passed:results.every(r=>r.passed),results};
  const output=path.join(root,'evidence/queue','ui-save-race-'+stamp+'-'+phase+'.json');
  fs.writeFileSync(output,JSON.stringify(receipt,null,2)+'\n');
  console.log(JSON.stringify({evidence:path.relative(root,output),...receipt}));
  if(!receipt.passed)process.exitCode=1;
})().catch(error=>{console.error(error);process.exitCode=1});

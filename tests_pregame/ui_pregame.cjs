'use strict';
// Local browser contract checks with intercepted API fixtures, not server integration.
const {chromium} = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const position = ['TOP','JUNGLE','MID','BOTTOM','SUPPORT'];
const spec={schema_version:'pregame.rule.v1',rule_id:'ui-fixture-only',version:'1',scope:'COMMON',positions:[],patches:[],sources:[{url:'https://example.org/synthetic-ui-only',title:'Isolated synthetic UI fixture',locator:'fixture',patch:null,sha256:null,kind:'SYNTHETIC'}],required_fields:[],conditions:[],counterconditions:[],stop_conditions:[],counterexamples:['SYNTHETIC: not coaching knowledge'],limitations:['UI test only'],output:{section:'COMPOSITION',target:'GLOBAL',outlook:null,text:'Fixture only',alternatives:[],change_conditions:[]},profile:null,cooldowns:[]};
const unknown = (key) => ({key,title:key,status:'UNKNOWN',texts:[],reasons:['NO_REVIEWED_RULE'],rules:[],cooldowns:[],outlook:null});
(async () => {
  const html = fs.readFileSync(path.join(root,'web_r4/pregame.html'),'utf8');
  const browser = await chromium.launch({headless:true, executablePath:process.env.CHROMIUM_EXECUTABLE || '/usr/bin/chromium',args:['--no-sandbox']});
  try {
    const page = await browser.newPage({viewport:{width:1280,height:900}});
    const errors=[], calls=[]; let saved=null, failSave=true, delayed=null, imported=null;
    page.on('dialog',d=>d.accept());
    page.on('pageerror', e=>errors.push(e.message));
    await page.route('http://localhost/**', async route => {
      const request=route.request(), pathname=new URL(request.url()).pathname;
      if(pathname==='/pregame')return route.fulfill({contentType:'text/html',body:html});
      if(pathname.endsWith('.svg'))return route.fulfill({contentType:'image/svg+xml',body:fs.readFileSync(path.join(root,'web_r4',path.basename(pathname)),'utf8')});
      if(pathname.endsWith('.js')||pathname.endsWith('.css'))return route.fulfill({contentType:pathname.endsWith('.js')?'application/javascript':'text/css',body:fs.readFileSync(path.join(root,'web_r4',path.basename(pathname)),'utf8')});
      const body=request.postDataJSON(); calls.push({path:pathname,method:request.method(),body,key:request.headers()['idempotency-key']});
      let data=[];
      if(pathname.endsWith('/status'))data={mode:'PRE_GAME',automatic_collection:'UNAVAILABLE',current_patch:null,knowledge_count:0,accuracy:null};
      if(pathname.endsWith('/candidates')){data=request.method()==='POST'?(imported={proposal:{rule_id:spec.rule_id,version:1,review_state:'EXPLORATORY',patch_range:body.spec.patches.join(','),applicability:{champion:'TYPE_BASED',role:'ALL',matchup:'STRUCTURED_CONDITIONS',level:'PRE_GAME_CONDITIONAL',context:'PRE_GAME'}},spec:body.spec}):[spec];}
      if(pathname.endsWith('/knowledge'))data=imported?[imported]:[];
      if(pathname.endsWith('/draft-captures'))data=[{id:'f'.repeat(32),session_id:'1'.repeat(32),revision:1,capture:{title:'Legacy draft'}}];
      if(pathname.endsWith('/review-priority'))data=[{rank:1,candidate_id:'fixture-priority',title:'Isolated priority fixture',reason:'Synthetic readonly reason',source_urls:[spec.sources[0].url],patch_range:'UNKNOWN',counterexamples:['UI only'],review_state:'EXPLORATORY'}];
      if(pathname.endsWith('/roster'))data={static_version:null,champions:[]};
      if(pathname.endsWith('/inputs')&&request.method()==='POST') {
        if(failSave){failSave=false;return route.abort('failed');}
        saved={schema_version:'pregame.input.v1',id:'b'.repeat(32),session_id:'a'.repeat(32),revision:1,parent_id:null,created_at:'2026-10-11T00:00:00Z',input:body.input,input_sha256:'c'.repeat(64)};data=saved;
      } else if(pathname.endsWith('/inputs'))data=saved?[{session_id:saved.session_id,title:saved.input.title,revision:1,input_sha256:saved.input_sha256}]:[];
      if(pathname.endsWith('/plans')&&request.method()==='POST') {
        const p={schema_version:'pregame.plan.v1',mode:'PRE_GAME',id:'d'.repeat(32),session_id:saved.session_id,revision:1,input_revision:1,input_sha256:saved.input_sha256,created_at:'2026-10-11T00:00:00Z',validity:'CURRENT',expiry_reasons:[],input:saved.input,common:{map:position.map(unknown),jungle:unknown('JUNGLE'),composition:unknown('COMPOSITION')},personal:{role:unknown('ROLE'),lane:unknown('LANE'),fight:unknown('FIGHT')},changes:unknown('CHANGES'),evaluations:[],knowledge_fingerprint:'e'.repeat(64),coaching_accuracy:null,real_match_validation:'NOT_EVALUATED'};
        if(delayed) return delayed(route,p);
        data=p;
      }
      await route.fulfill({contentType:'application/json',body:JSON.stringify(data)});
    });
    await page.goto('http://localhost/pregame');
    assert.equal(await page.locator('link[rel="icon"]').getAttribute('href'),'/pregame-icon.svg');
    await page.fill('#pg-token','fixture-only'); await page.click('#pg-login');
    await page.waitForSelector('#pg-workspace:visible');
    assert.equal(await page.locator('.pg-slot').count(),10);
    assert.match(await page.textContent('#pg-review-priority'),/Synthetic readonly reason/);
    assert.equal(await page.inputValue('#pg-patch'),'');
    assert.equal(await page.inputValue('#pg-phase'),'UNKNOWN');
    assert.equal(await page.locator('#pg-draft-select option').nth(1).getAttribute('value'),'1'.repeat(32));
    await page.click('#pg-golden');
    assert.equal(await page.inputValue('#pg-phase'),'PRE_GAME');
    assert.equal(await page.inputValue('#pg-ally-1-champion'),'Ornn');
    assert.equal(await page.inputValue('#pg-enemy-5-champion'),'Nautilus');
    await page.click('#pg-save');await page.waitForSelector('#pg-retry-save:visible');
    await page.fill('#pg-title','Edit after ambiguous save');
    await page.click('#pg-retry-save');
    await page.waitForFunction(()=>document.getElementById('pg-current').textContent.includes('v1'));
    assert.equal(await page.inputValue('#pg-title'),'Edit after ambiguous save');
    const writes=calls.filter(c=>c.path.endsWith('/inputs')&&c.method==='POST');
    assert.equal(writes.length,2);assert.deepEqual(writes[0].body,writes[1].body);assert.equal(writes[0].key,writes[1].key);
    assert.equal(writes[0].body.input.patch,null);
    assert.equal(await page.isDisabled('#pg-create-plan'),true);
    await page.fill('#pg-title',saved.input.title);
    await page.click('#pg-create-plan'); await page.waitForSelector('#pg-plan-panel:visible');
    assert.equal(await page.locator('#pg-cards > article').count(),9);
    assert.equal(await page.locator('#pg-card-map .pg-map-row').count(),5);
    assert.equal(await page.locator('#pg-card-map .selected').count(),1);
    assert.match(await page.textContent('#pg-cards'),/NO_REVIEWED_RULE/);
    await page.locator('#pg-card-map summary').click();
    assert.match(await page.textContent('#pg-card-map pre'),/input_sha256/);
    await page.setViewportSize({width:390,height:844});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
    await page.screenshot({path:path.join(root,'evidence/queue/ui-mobile.png'),fullPage:true});
    await page.setViewportSize({width:1280,height:900});
    await page.locator('#pg-candidate-list button').click();
    assert.equal(await page.isDisabled('#pg-approve'),true);
    assert.match(await page.textContent('#pg-knowledge-json'),/counterexamples/);
    assert.equal(await page.locator('#pg-knowledge-sources a').getAttribute('href'),spec.sources[0].url);
    const edited={...spec,patches:['SYNTHETIC-UI-ONLY']};
    await page.fill('#pg-spec-json',JSON.stringify(edited));
    assert.equal(await page.isDisabled('#pg-import-candidate'),true);
    await page.click('#pg-preview-spec');
    await page.click('#pg-import-candidate');
    await page.waitForSelector('#pg-knowledge-list button');
    await page.locator('#pg-knowledge-list button').click();
    assert.equal(await page.isDisabled('#pg-approve'),false);
    await page.evaluate(()=>document.getElementById('pg-approve').click());
    assert.equal(calls.some(c=>c.path.endsWith('/decisions')),false);
    assert.deepEqual(calls.find(c=>c.path.endsWith('/candidates')&&c.method==='POST').body.spec.patches,['SYNTHETIC-UI-ONLY']);
    await page.fill('#pg-patch','changed');
    assert.equal(await page.isVisible('#pg-plan-panel'),false);
    await page.fill('#pg-patch','');
    let release; delayed=(route,p)=>new Promise(resolve=>{release=async()=>{await route.fulfill({contentType:'application/json',body:JSON.stringify(p)});resolve();};});
    await page.click('#pg-create-plan');
    await page.waitForFunction(()=>document.getElementById('pg-create-plan').disabled);
    await page.click('#pg-logout');await release();
    assert.equal(await page.isVisible('#pg-workspace'),false);
    assert.equal(await page.isVisible('#pg-plan-panel'),false);
    assert.equal(calls.some(c=>c.path.endsWith('/decisions')),false);
    await page.setViewportSize({width:390,height:844});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
    assert.deepEqual(errors,[]);
    const evidence={executed_at:new Date().toISOString(),source_sha256:require('node:crypto').createHash('sha256').update(fs.readFileSync(path.join(root,'web_r4/pregame.js'))).digest('hex'),scope:'Local Chromium + intercepted synthetic API fixtures; no server integration or approval decisions',checks:['10 structured slots','explicit UNKNOWN/PRE_GAME phase','legacy selector uses session ID','null patch Golden input only','ambiguous save identical retry key/body','later edits preserved','plan acknowledged revision gate','7 cards/5 map rows','unknown reasons/full detail','edit hides plan','logout suppresses late plan','editable full spec preview before EXPLORATORY import','sources link','same-origin SVG favicon declaration','readonly priority source list and reasons','untrusted approval click blocked; no decisions sent','390px authenticated view no overflow'],passed:true,page_errors:errors};
    fs.writeFileSync(path.join(root,'evidence/queue/ui-local.json'),JSON.stringify(evidence,null,2)+'\n');
    console.log(JSON.stringify(evidence));
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});

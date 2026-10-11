'use strict';
const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const output=process.env.PREGAME_V13_EVIDENCE_DIR;
const mode=process.env.PREGAME_V13_MODE || process.env.PREGAME_BROWSER_MODE;
if(!output || !['actual','synthetic'].includes(mode))throw new Error('Use scripts/browser_v13.py');
const token=fs.readFileSync(process.env.WORKBENCH_TOKEN_FILE,'utf8').trim();
const roles=['TOP','JUNGLE','MID','BOTTOM','SUPPORT'],champions=['Ornn','Sejuani','Ahri','Caitlyn','Lux'];
const roleChecks=['nine-cards','common-identity','guard-state','operations-state','movement-state','five-mini-graphs','lane-graph','dirty-hides'];
const expected=['connected','legacy-input-shape',...roles.flatMap(r=>roleChecks.map(c=>r+'-'+c)),
  'explicit-pick-metadata','metadata-reopen','power-renderer-ci-gaps','power-markers','power-synthetic-gates',
  'power-fallback-labels','power-late-dirty','power-late-logout','no-decisions','no-browser-errors'];
const checks=[],errors=[],snapshots=[];let browser,page,firstFailure=null,decisions=0;
function check(id,passed,actual){checks.push({id,passed:Boolean(passed),actual});if(!passed)throw new Error('Failed check: '+id);}
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
async function ready(){await page.waitForFunction(()=>!document.getElementById('pg-workspace').hidden&&!document.getElementById('pg-login').disabled&&document.getElementById('pg-notice').textContent.includes('연결'));await page.waitForLoadState('networkidle');}
async function save(){const pending=page.waitForResponse(r=>/\/pregame\/inputs(?:\/[a-f0-9]+)?$/.test(r.url())&&['POST','PUT'].includes(r.request().method()));await page.locator('#pg-save').click();const r=await pending;if(!r.ok())throw new Error('Save '+r.status());await page.waitForFunction(()=>!document.getElementById('pg-create-plan').disabled);return r.json();}
async function generate(waitPower=true){const pending=page.waitForResponse(r=>/\/inputs\/[a-f0-9]+\/plans$/.test(r.url())&&r.request().method()==='POST');await page.locator('#pg-create-plan').click();const r=await pending;if(!r.ok())throw new Error('Plan '+r.status());await page.locator('#pg-plan-panel').waitFor({state:'visible'});if(waitPower)await page.waitForLoadState('networkidle');return JSON.parse(await page.locator('#pg-plan-json').textContent());}
(async()=>{try{
 browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_EXECUTABLE,args:['--no-sandbox','--disable-dev-shm-usage']});
 const context=await browser.newContext({viewport:{width:1280,height:960}});page=await context.newPage();
 page.on('pageerror',e=>errors.push(String(e).split(token).join('[REDACTED]')));
 page.on('console',m=>{if(m.type()==='error')errors.push(m.text().split(token).join('[REDACTED]'));});
 page.on('request',r=>{if(/\/decisions$/.test(r.url()))decisions++;});page.on('dialog',d=>d.dismiss());
 await page.goto(process.env.WORKBENCH_URL);await page.locator('#pg-token').fill(token);await page.locator('#pg-login').click();await ready();
 check('connected',await page.locator('#pg-workspace').isVisible(),{mode});
 await page.locator('#pg-golden').click();const raw=JSON.parse(await page.locator('#pg-input-json').textContent());
 check('legacy-input-shape',!('schema_version' in raw)&&!('my_pick_state' in raw)&&!('frequent_champions' in raw),{keys:Object.keys(raw)});
 if(mode==='synthetic')await page.locator('#pg-patch').fill('SYNTHETIC-1');
 let common=null;
 for(const [i,role]of roles.entries()){
  await page.locator('#pg-my-position').selectOption(role);await page.locator('#pg-my-champion').fill(champions[i]);await page.locator('#pg-my-slot').selectOption(String(i+1));await save();const p=await generate();snapshots.push(p);
  check(role+'-nine-cards',await page.locator('#pg-cards > article').count()===9,{count:await page.locator('#pg-cards > article').count()});
  check(role+'-common-identity',common===null||same(common,p.common),{position:role});common=p.common;
  const guardText=await page.locator('#pg-card-role .pg-guard').allTextContents();
  check(role+'-guard-state',mode==='synthetic'?guardText.some(t=>t.includes('SYNTHETIC prerequisite')&&t.includes('SYNTHETIC invalidation')&&t.includes('SYNTHETIC alternative')):guardText.length>0&&guardText.every(t=>t.includes('UNKNOWN')),{guardText});
  const operations=await page.locator('#pg-card-operations').textContent();
  check(role+'-operations-state',mode==='synthetic'?operations.includes('SYNTHETIC request')&&operations.includes('SYNTHETIC required play'):operations.includes('UNKNOWN')&&!operations.includes('SYNTHETIC'),{operations});
  const movement=await page.locator('#pg-card-movement').textContent();
  check(role+'-movement-state',mode==='synthetic'?movement.includes('EARLY')&&movement.includes('MID')&&movement.includes('LATE')&&movement.includes('SYNTHETIC'):movement.includes('UNKNOWN'),{movement});
  check(role+'-five-mini-graphs',await page.locator('#pg-card-map .pg-power').count()===5,{count:await page.locator('#pg-card-map .pg-power').count()});
  check(role+'-lane-graph',await page.locator('#pg-card-lane .pg-power').count()===1,{count:await page.locator('#pg-card-lane .pg-power').count()});
  await page.locator('#pg-title').fill('v1.3 '+role+' edit');check(role+'-dirty-hides',!await page.locator('#pg-plan-panel').isVisible(),{});
 }
 await page.locator('#pg-pick-metadata > summary').click();await page.locator('#pg-my-pick-state').selectOption('PICKED');await page.locator('#pg-frequent-champions').fill('Ornn, Sejuani');const record=await save();
 check('explicit-pick-metadata',record.input.schema_version==='pregame.input-draft.v2'&&record.input.my_pick_state==='PICKED'&&same(record.input.frequent_champions,['Ornn','Sejuani']),record.input);
 await page.reload();await ready();await page.locator('#pg-input-list button').first().click();await page.waitForFunction(()=>!document.getElementById('pg-create-plan').disabled);
 check('metadata-reopen',await page.locator('#pg-my-pick-state').inputValue()==='PICKED'&&(await page.locator('#pg-frequent-champions').inputValue()).includes('Sejuani'),{});
 // Isolated renderer fixture does not alter server knowledge, saved plans or approvals.
 const renderer=await page.evaluate(()=>{
  const host=document.createElement('div');host.id='renderer-test';document.body.append(host);
  const point=(minute,mean,low,high,comparison='MATCHUP')=>({minute,n:30,mean,ci95:{low,high},visible:true,omission_reason:null,comparison,metric:'gold_delta'});
  const marker={kind:'LEVEL',level:6,n:30,median_minute:6,q1_minute:5,q3_minute:7,label:'DESCRIPTIVE_NON_CAUSAL'};
  const view={status:'KNOWN',metric:'gold_delta',source:{sample_kind:'SYNTHETIC',patch:'SYNTHETIC-1',tier:'TEST',precision_policy:{kind:'TEST'},limitations:['TEST sampling bias']},dataset_digest:'fixture-digest',points:[point(1,10,5,15),point(2,1,-2,4),{minute:3,n:1,mean:null,ci95:null,visible:false,omission_reason:'INSUFFICIENT_SAMPLES',comparison:null},point(4,-10,-15,-5,'ROLE_POPULATION'),point(5,-9,-14,-4,'ROLE_POPULATION')],markers:[marker]};
  const response={view,opponent_view:{...view,markers:[{...marker,kind:'ITEM',item_id:1,item_order:1}]},test_mode:true};
  window.PregamePower.render(host,response,{testMode:true,champion:'Ornn',opponent:'Fiora'});
  const first={ci:host.querySelectorAll('.pg-power-ci').length,lines:host.querySelectorAll('.pg-power-line').length,zero:host.querySelectorAll('.pg-power-zero').length,text:host.textContent,metricOptions:host.querySelectorAll('.pg-power-metric option').length,own:host.querySelectorAll('[data-owner="own"]').length,opponent:host.querySelectorAll('[data-owner="opponent"]').length};
  window.PregamePower.render(host,response,{testMode:false});const blocked=host.textContent;
  window.PregamePower.render(host,{...response,test_mode:false},{testMode:true});const blockedResponse=host.textContent;
  return {first,blocked,blockedResponse};
 });
 check('power-renderer-ci-gaps',renderer.first.metricOptions===3&&renderer.first.ci===2&&renderer.first.lines===2&&renderer.first.zero===1&&renderer.first.text.includes('강함')&&renderer.first.text.includes('약함')&&renderer.first.text.includes('비슷함'),renderer.first);
 check('power-markers',renderer.first.own>0&&renderer.first.opponent>0&&renderer.first.text.includes('IQR')&&renderer.first.text.includes('비인과')&&renderer.first.text.includes('빌드'),renderer.first);
 check('power-synthetic-gates',renderer.first.text.includes('TEST')&&renderer.blocked.includes('UNKNOWN')&&renderer.blockedResponse.includes('UNKNOWN'),{blocked:renderer.blocked,blockedResponse:renderer.blockedResponse});
 check('power-fallback-labels',renderer.first.text.includes('동일 포지션 전체')&&renderer.first.text.includes('n=30')&&renderer.first.text.includes('INSUFFICIENT_SAMPLES'),renderer.first);
 await page.locator('#renderer-test').evaluate(n=>n.remove());
 if(mode==='actual'){await page.locator('#pg-patch').fill('14.1');await save();}
 let releases=[],heldResolve;const allHeld=()=>new Promise(resolve=>{heldResolve=resolve;});await page.route('**/pregame/power-view',async route=>{await new Promise(resolve=>{releases.push(resolve);if(releases.length===6&&heldResolve)heldResolve();});await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({view:{status:'UNKNOWN',points:[],markers:[]},opponent_view:null,test_mode:false})});});
 const lateDirty=allHeld();await generate(false);await lateDirty;await page.waitForFunction(()=>document.querySelectorAll('.pg-power').length===6);await page.locator('#pg-title').fill('dirty power request');releases.splice(0).forEach(r=>r());await page.waitForLoadState('networkidle');
 check('power-late-dirty',!await page.locator('#pg-plan-panel').isVisible()&&await page.locator('#pg-cards > article').count()===0,{});
 await save();const lateLogout=allHeld();await generate(false);await lateLogout;await page.locator('#pg-logout').click();releases.splice(0).forEach(r=>r());await page.waitForLoadState('networkidle');
 check('power-late-logout',!await page.locator('#pg-workspace').isVisible()&&await page.locator('#pg-cards > article').count()===0&&await page.locator('#pg-plan-json').textContent()==='',{});
 check('no-decisions',decisions===0,{decisions});check('no-browser-errors',errors.length===0,{errors});
 }catch(e){firstFailure=String(e.stack||e).split(token).join('[REDACTED]');}finally{
 if(browser)await browser.close();const passed=!firstFailure&&same(checks.map(c=>c.id),expected)&&checks.every(c=>c.passed);fs.mkdirSync(output,{recursive:true});
 fs.writeFileSync(path.join(output,'receipt.json'),JSON.stringify({evidence_kind:'FRESH_BROWSER_EXECUTION',mode,passed,expected_check_ids:expected,checks,first_failure:firstFailure,page_errors:errors,decision_requests:decisions,coaching_accuracy:null,real_match_validation:'NOT_EVALUATED',tested_at:new Date().toISOString()},null,2)+'\n');
 fs.writeFileSync(path.join(output,'plans.json'),JSON.stringify(snapshots,null,2)+'\n');process.stdout.write(JSON.stringify({passed,mode,checks:checks.length,first_failure:firstFailure})+'\n');process.exitCode=passed?0:1;
 }} )();

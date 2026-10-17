"""Affected loading flow in real Chromium, PC routes and repository-subpath export."""
from datetime import datetime,timezone
import functools,hashlib,json,os
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import subprocess,sys,tempfile,threading

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
SOURCES=['web_r4/'+p for p in ['loading-exploration.js','loading-interactive.js','loading.html','loading.js','loading.css','loading-engine.js','loading-map.js','loading-data.json','skill-data.js','skill-display.js','directions-engine.js','directions.js']]+['coach_v1/pregame_server.py','scripts/build_directions_web.py','scripts/browser_loading.py']

def affected():
    event_path=os.environ.get('GITHUB_EVENT_PATH')
    if not event_path:return True
    event=json.loads(Path(event_path).read_text());before=event.get('pull_request',{}).get('base',{}).get('sha') or event.get('before')
    if not before or set(before)=={'0'}:return True
    changed=set(subprocess.check_output(['git','diff','--name-only',before,'HEAD'],cwd=ROOT,text=True).splitlines())
    return bool(changed&set(SOURCES) or any(p.startswith('web_r4/loading-assets/') for p in changed))

JS=r'''
const fs=require('node:fs'),assert=require('node:assert/strict'),{chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_EXECUTABLE?{executablePath:process.env.CHROMIUM_EXECUTABLE}:{}),args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1440,height:1000},hasTouch:true,reducedMotion:'reduce'}),errors=[],bad=[],requests=[];
 page.on('pageerror',e=>errors.push(e.message));
 page.on('request',r=>{requests.push(r.url());assert([process.env.LOADING_PC,process.env.LOADING_WEB].some(b=>r.url().startsWith(b+'/')),'unexpected external request');assert.equal(r.method(),'GET');});
 page.on('response',r=>{if(r.status()>=400)bad.push({path:new URL(r.url()).pathname,status:r.status()});});
 const ready=async url=>{await page.goto(url);await page.waitForSelector('#analyze:enabled');};
 const analyze=async()=>{await page.locator('#analyze').click();await page.waitForSelector('#loading-results:visible');};
 const example=async i=>{await page.locator('#input-panel').evaluate(e=>e.open=true);await page.locator('#example-'+i).click();await analyze();};
 const capture=async(selector,file)=>page.locator(selector).screenshot({path:process.env.LOADING_OUT+'/'+file});
 const summary=async()=>page.locator('#loading-summary').innerText();
 const interactiveFlow=async(label)=>{
  const flow=page.locator('#interactive-flow');await flow.waitFor({state:'visible'});
  const selected=async()=>flow.getAttribute('data-selected-plan');
  assert.equal(await selected(),'PREPARE_WINDOW');await page.locator('#risk-OPPORTUNITY').check();assert.equal(await selected(),'PREPARE_WINDOW');assert.match(await page.locator('#exploration-summary').innerText(),/현재 조건에서는 선택이 같습니다/);assert(await page.locator('#preview-SHORT_FOLLOW').isDisabled());
  await page.locator('#assumptions-ready').click();assert.equal(await selected(),'SHORT_FOLLOW');assert.equal(await page.locator('#active-plan').getAttribute('data-plan'),'SHORT_FOLLOW');
  const shortCosts=await flow.locator('[data-plan-id="SHORT_FOLLOW"]').innerText(),receiveCosts=await flow.locator('[data-plan-id="RECEIVE_WITH_LUX"]').innerText();assert.match(shortCosts,/소모|전진 노출/);assert.match(receiveCosts,/CS|주도권|미니언/);
  const beforePath=await page.locator('#active-plan .strategy-map').innerHTML();await page.locator('#risk-LOSS_LIMIT').check();assert.equal(await selected(),'RECEIVE_WITH_LUX');assert.equal(await page.locator('#active-plan').getAttribute('data-plan'),'RECEIVE_WITH_LUX');assert.notEqual(await page.locator('#active-plan .strategy-map').innerHTML(),beforePath);assert.match(await page.locator('#selected-action').innerText(),/포기할 미니언/);
  await page.locator('#risk-OPPORTUNITY').check();assert.equal(await selected(),'SHORT_FOLLOW');
  const map=page.locator('#active-plan .scenario-grid');await map.locator('[data-map-step="ALL"]').click();await map.locator('[data-map-action="3"]').first().focus();await page.keyboard.press('Enter');assert.equal(await map.locator('.strategy-map').getAttribute('data-active-step'),'3');assert.equal(await page.locator('#selected-action').getAttribute('data-step'),'3');
  await map.locator('.scenario-steps [data-step="2"] button').click();assert.equal(await map.locator('.strategy-map').getAttribute('data-active-step'),'2');assert.equal(await page.locator('#selected-action').getAttribute('data-step'),'2');
  await map.locator('.map-header button').click();await page.waitForSelector('#loading-map-dialog[open]');await page.locator('#zoom-step-controls [data-map-step="ALL"]').click();await page.locator('#zoom-map [data-map-action="1"]').first().focus();await page.keyboard.press(' ');assert.equal(await map.locator('.strategy-map').getAttribute('data-active-step'),'1');assert.equal(await page.locator('#selected-action').getAttribute('data-step'),'1');assert.match(await page.locator('#zoom-selected-action').innerText(),/럭스의 빛의 속박\(Q\)/);await page.locator('#map-scale').fill('200');await page.locator('#map-scale').dispatchEvent('input');assert(await page.locator('#map-zoom-stage').evaluate(e=>e.scrollWidth>e.clientWidth));await page.keyboard.press('Escape');
  if(label==='mobile'){await map.locator('[data-map-step="ALL"]').click();const target=await map.locator('[data-map-action="2"] circle').first().boundingBox();await page.touchscreen.tap(target.x+target.width/2,target.y+target.height/2);assert.equal(await page.locator('#selected-action').getAttribute('data-step'),'2');}
  await page.locator('#assumption-binding').selectOption('MISS');assert.equal(await selected(),'RECEIVE_WITH_LUX');assert.equal(await page.locator('#condition-change').getAttribute('data-action-changed'),'true');assert(await page.locator('#preview-SHORT_FOLLOW').isDisabled());
  await page.locator('#assumption-binding').selectOption('UNKNOWN');assert.equal(await selected(),'RECEIVE_WITH_LUX');assert(await page.locator('#preview-SHORT_FOLLOW').isDisabled());
  await page.locator('#assumption-exit_cover').selectOption('UNKNOWN');assert.equal(await selected(),'PREPARE_WINDOW');assert.equal(await page.locator('#active-plan .strategy-map path[marker-end]').count(),0);assert.equal(await page.locator('#active-plan [data-team="ENEMY"]').count(),0);
  await page.locator('#assumptions-ready').click();await page.locator('#why-SHORT_FOLLOW > summary').click();assert.match(await page.locator('#why-SHORT_FOLLOW').innerText(),/설계 가설|조건부/);assert(await page.locator('#why-SHORT_FOLLOW a[href^="https:"]').count()>=5);assert.match(await page.locator('#why-SHORT_FOLLOW').innerText(),/DUO-L2/);
  await capture('#active-plan',label+'-interactive-plan.png');await capture('#plan-comparison',label+'-interactive-comparison.png');
  await page.locator('#period-LEVEL6').click();assert.equal(await selected(),'UNSUPPORTED');assert.match(await page.locator('#selected-lane-row').innerText(),/폭뢰\(R\)/);assert.equal(await flow.locator('#active-plan').count(),0);
  await page.locator('#explore-tab-OPERATIONS').click();assert.match(await flow.innerText(),/운영 기본안/);await page.locator('#explore-tab-FIGHT').click();assert.match(await flow.innerText(),/한타에서 내 역할/);await page.locator('#explore-tab-LANE').click();await page.locator('#period-LEVEL2').click();await page.locator('#assumptions-reset').click();assert.equal(await selected(),'PREPARE_WINDOW');assert.equal(await page.locator('#assumption-followup').inputValue(),'UNKNOWN');
  await page.locator('#risk-BALANCED').check();await page.locator('#input-panel').evaluate(e=>e.open=true);await page.locator('#pick-ALLY-0').fill('Malphite');assert(await page.locator('#loading-results').isHidden());assert.equal(await flow.locator('.strategy-map').count(),0);await analyze();assert.match(await page.locator('#fight-content').innerText(),/말파이트/);await example(0);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'interactive horizontal overflow');
 };
 const skillPresentation=async()=>{
  const row=id=>page.locator('[data-milestone="'+id+'"]'),cell=(id,index)=>row(id).locator('td').nth(index);
  assert.match(await summary(),/럭스의 빛의 속박\(Q\)/);assert.match(await summary(),/케이틀린의 요들잡이 덫\(W\)/);
  assert.match(await page.locator('#lane-key').innerText(),/설치·발동·후속 거리/);
  assert.match(await page.locator('#remember li').first().innerText(),/케이틀린의 요들잡이 덫\(W\) 후속이 확정되지는/);
  assert.match(await cell('LEVEL1',0).innerText(),/케이틀린의 필트오버 피스메이커\(Q\).*럭스의 광휘의 특이점\(E\)/);
  assert.match(await cell('LEVEL1',2).innerText(),/노틸러스가 닻줄 견인\(Q\)로/);
  assert.match(await cell('LEVEL1',2).innerText(),/카이사가.*카이사의 이케시아 폭우\(Q\) 피해/);
  assert.match(await cell('LEVEL2',2).innerText(),/케이틀린의 요들잡이 덫\(W\)와 짧은/);
  assert.match(await cell('LEVEL2',2).innerText(),/노틸러스의 닻줄 견인\(Q\) 접근/);
  assert.match(await cell('LEVEL3_5',1).innerText(),/럭스의 광휘의 특이점\(E\)의 원문/);
  assert.match(await cell('LEVEL3_5',0).innerText(),/럭스의 프리즘 보호막\(W\)을 배운 가정/);
  assert.match(await cell('LEVEL3_5',1).innerText(),/아군에게 보호막을 줍니다/);
  assert.match(await cell('LEVEL3_5',2).innerText(),/케이틀린의 90구경 투망\(E\)를 단순/);
  assert.match(await cell('LEVEL3_5',2).innerText(),/케이틀린의 90구경 투망\(E\)가 없거나/);
  assert.match(await cell('LEVEL3_5',2).innerText(),/럭스의 광휘의 특이점\(E\)로 보지 못한/);
  assert.match(await cell('LEVEL3_5',2).innerText(),/또는 럭스의 프리즘 보호막\(W\) 하나/);
  assert.match(await cell('LEVEL3_5',2).innerText(),/럭스의 프리즘 보호막\(W\)이 닿지/);
  assert.match(await cell('LEVEL3_5',3).innerText(),/케이틀린의 90구경 투망\(E\)를 소모하거나 럭스의 프리즘 보호막\(W\) 보호/);
  assert.match(await cell('LEVEL6',2).innerText(),/카이사의 사냥본능\(R\) 후속/);
  assert.match(await row('FIRST_PURCHASE').innerText(),/노틸러스의 닻줄 견인\(Q\).*노틸러스의 강력한 일격\(P\)/);
  assert.match(await cell('FIRST_PURCHASE',2).innerText(),/노틸러스의 닻줄 견인\(Q\)을 피하거나/);
  assert.match(await row('FIRST_CORE').innerText(),/설계 가설/);
  assert.match(await page.locator('#lane-context .fight-link-list').first().innerText(),/럭스의 빛의 속박\(Q\)/);
  assert.match(await page.locator('#fight-content').innerText(),/케이틀린의 90구경 투망\(E\)/);
  assert.match(await page.locator('#scenario-content').innerText(),/케이틀린의 요들잡이 덫\(W\)/);
  assert.match(await page.locator('#scenario-content').innerText(),/케이틀린의 90구경 투망\(E\)/);
  const originalFact=JSON.parse(fs.readFileSync('web_r4/loading-data.json','utf8')).champions.Caitlyn.facts.find(f=>f.slot==='W');
  const fact=page.locator('[data-fact-id="official:Caitlyn:W"]');assert.equal(await fact.locator('blockquote').first().textContent(),originalFact.text);
  assert.equal(await fact.locator('h4').textContent(),'케이틀린의 요들잡이 덫(W)');
  assert(await page.evaluate(()=>{
    const opts={champions:['Caitlyn','Lux','Nautilus','Kaisa'],own:'Caitlyn'},alias={...opts,aliases:[{text:'덫',champion:'Caitlyn',slot:'W'}]};
    const sample='럭스 Q와 내 W, 케이틀린의 90구경 투망(E)',once=SkillDisplay.format(sample,opts),trap=SkillDisplay.format('덫 연결',alias);
    const generic='교전 준비 · 상대 반격/매혹/공포',genericOptions={champions:['Katarina','Jax','Ahri','Fiddlesticks']};
    return SkillDisplay.format(once,opts)===once&&SkillDisplay.format(trap,alias)===trap&&SkillDisplay.format('Q·E',opts)==='Q·E'&&SkillDisplay.format('덫 연결',opts)==='덫 연결'&&SkillDisplay.format(generic,genericOptions)===generic;
  }));
 };
 const mapSkillPresentation=async()=>{
  // A display-only fixture checks fields absent from the retained maps' generic labels.
  await page.evaluate(catalog=>{
   const input=LoadingStrategy.exampleInput(catalog,0),fixture={id:'recall-crash',map:{landmarks:[{step:1,label:'럭스 E',x:50,y:50}],caption:'케이틀린 E',notes:['럭스 Q'],entities:[]},plan:{steps:[{number:1,text:'덫 / 투망'}]}};
   const host=document.createElement('div');host.id='skill-map-probe';host.append(LoadingMap.create(fixture,catalog,input));document.querySelector('main').append(host);
  },JSON.parse(fs.readFileSync('web_r4/loading-data.json','utf8')));
  const probe=page.locator('#skill-map-probe');
  assert.equal(await probe.locator('.map-caption').innerText(),'케이틀린의 90구경 투망(E)');
  assert.equal(await probe.locator('.map-label').textContent(),'럭스의 광휘의 특이점(E)');
  assert.match(await probe.locator('.scenario-steps').innerText(),/케이틀린의 요들잡이 덫\(W\) \/ 케이틀린의 90구경 투망\(E\)/);
  await probe.locator('.map-header button').click();await page.waitForSelector('#loading-map-dialog[open]');
  assert.equal(await page.locator('#zoom-map .map-label').textContent(),'럭스의 광휘의 특이점(E)');
  await page.locator('#map-close').click();await probe.evaluate(element=>element.remove());
 };
 const snapshots=[];
 try{
  await ready(process.env.LOADING_PC+'/loading');
  assert.equal(await page.locator('[id^="economy-"]').count(),0);
  assert.equal(requests.filter(u=>u.includes('/dev/')).length,0);
  // Actual manual input uses both Korean and English; no economy/vision/wave fields.
  const teams=[['오른','Sejuani','아리','caitlyn','럭스'],['Fiora','리 신','Zed',"Kai\'Sa",'노틸러스']],roles=['TOP','JUNGLE','MID','BOTTOM','SUPPORT'];
  for(let t=0;t<2;t++)for(let i=0;i<5;i++){
   const team=t?'ENEMY':'ALLY';await page.locator('#pick-'+team+'-'+i).fill(teams[t][i]);await page.locator('#position-'+team+'-'+i).selectOption(roles[i]);
  }
  await page.locator('#own-champion').selectOption('Caitlyn');await page.locator('#own-position').selectOption('BOTTOM');
  await page.locator('.optional-settings').evaluate(e=>e.open=true);await page.locator('#patch').fill('16.20');await analyze();
  const original=await summary();assert.match(original,/케이틀린/);assert.match(original,/카이사/);assert.match(original,/노틸러스/);
  assert.equal(await page.locator('#report-teams .roster-pick').count(),10);assert.equal(await page.locator('#lane-table tbody tr').count(),6);
  assert.match(await page.locator('[data-milestone="LEVEL1"]').innerText(),/케이틀린의 필트오버 피스메이커\(Q\)/);
  assert.match(await page.locator('[data-milestone="LEVEL1"]').innerText(),/럭스의 광휘의 특이점\(E\)/);
  assert.equal(await page.locator('#scenario-content [data-scenario]').count(),2);
  assert.equal(await page.locator('[data-team="ENEMY"][data-entity]').count(),0);
  await skillPresentation();
  await interactiveFlow('desktop');
  await mapSkillPresentation();
  await capture('#loading-summary','desktop-summary.png');await capture('#loading-lane','desktop-lane.png');await capture('#teamfight','desktop-teamfight.png');
  snapshots.push({input:'example-0 manual Korean/English',summary:original,lane_rows:await page.locator('#lane-table tbody').innerText()});
  // Context meaning fixed in contract before implementation, exercised through real controls.
  const baseLane=await page.locator('#lane-table tbody').innerText();
  const level2=await page.locator('[data-milestone="LEVEL2"]').innerText();
  assert.match(level2,/럭스의 빛의 속박\(Q\)/);assert(!/오른|세주아니/.test(baseLane));
  assert.match(baseLane,/상대 대응 가정/);assert.match(baseLane,/그때의 대안/);assert.match(baseLane,/실제 상태 미관측/);
  assert.match(await page.locator('#fight-content').innerText(),/기본 유형·역할/);
  const beforeMap=await page.locator('#scenario-content [data-entity] title').allTextContents();
  assert(beforeMap.every(t=>!/오른|세주아니/.test(t)));
  await page.locator('#input-panel').evaluate(e=>e.open=true);
  for(let t=0;t<2;t++)for(let i=0;i<5;i++){
    const team=t?'ENEMY':'ALLY',from=4-i;await page.locator('#pick-'+team+'-'+i).fill(teams[t][from]);await page.locator('#position-'+team+'-'+i).selectOption(roles[from]);
  }
  await page.locator('#own-champion').selectOption('Caitlyn');await page.locator('#own-position').selectOption('BOTTOM');await analyze();
  assert.equal(await summary(),original);assert.equal(await page.locator('#lane-table tbody').innerText(),baseLane);
  await page.locator('#input-panel').evaluate(e=>e.open=true);await page.locator('#pick-ALLY-0').fill('Malphite');await analyze();
  assert.equal(await page.locator('#lane-table tbody').innerText(),baseLane);
  assert.match(await page.locator('#fight-content').innerText(),/말파이트/);
  await page.locator('#input-panel').evaluate(e=>e.open=true);await page.locator('#pick-ALLY-4').fill('Janna');await analyze();
  assert(!/빛의 속박/.test(await page.locator('#lane-table tbody').innerText()));assert.match(await page.locator('#lane-table tbody').innerText(),/잔나/);
  await example(0);await page.locator('#input-panel').evaluate(e=>e.open=true);await page.locator('#pick-ENEMY-4').fill('Lulu');await analyze();
  assert(!/노틸러스|닻줄 견인/.test(await page.locator('#lane-table tbody').innerText()));assert.match(await page.locator('#lane-table tbody').innerText(),/룰루/);
  await example(0);await page.locator('#input-panel').evaluate(e=>e.open=true);await page.locator('#position-ENEMY-4').selectOption('');await analyze();
  assert.match(await page.locator('#lane-context').innerText(),/배치 미확인/);assert(!/럭스 Q·내 W를 배운 가정/.test(await page.locator('#lane-table tbody').innerText()));
  await example(0);await page.locator('#input-panel').evaluate(e=>e.open=true);await page.locator('#position-ENEMY-3').selectOption('');await analyze();
  assert.match(await page.locator('#lane-context').innerText(),/노틸러스/);assert.match(await page.locator('#lane-opponent-copy').innerText(),/미확인/);
  await example(0);await page.locator('#input-panel').evaluate(e=>e.open=true);await page.locator('#position-ENEMY-3').selectOption('SUPPORT');await page.locator('#position-ENEMY-4').selectOption('BOTTOM');await analyze();
  assert.match(await page.locator('#lane-opponent-copy').innerText(),/노틸러스/);assert(!/럭스 Q·내 W를 배운 가정/.test(await page.locator('#lane-table tbody').innerText()));
  await example(0);await page.locator('#input-panel').evaluate(e=>e.open=true);
  for(const [i,id] of [[0,'Gangplank'],[1,'Kindred'],[2,'Hwei'],[4,'Teemo']])await page.locator('#pick-ALLY-'+i).fill(id);
  await analyze();const unknownControl=await page.locator('#fight-content .scenario-steps [data-step="2"]').innerText();
  assert.match(unknownControl,/제어 연결은 미확인/);assert.match(unknownControl,/90구경 투망/);assert(!unknownControl.includes('제어가 적중'));
  await example(0);
  await page.locator('.detail-nav a[href="#loading-lane"]').click();assert.equal(await page.evaluate(()=>location.hash),'#loading-lane');
  await page.locator('#input-panel').evaluate(e=>e.open=true);await page.locator('#own-champion').selectOption('Ornn');await page.locator('#own-position').selectOption('TOP');await analyze();
  assert.notEqual(await summary(),original);assert.match(await page.locator('#my-role').innerText(),/오른/);assert.match(await page.locator('#fight-content').innerText(),/화염 돌진/);
  assert.equal(await page.locator('[data-scenario="objective-connected"]').count(),1);
  await example(1);const second=await summary();assert.notEqual(second,original);assert.match(second,/피오라/);
  assert.equal(await page.locator('[data-scenario="side-connected"]').count(),1);await capture('#loading-summary','desktop-alternative.png');
  await page.locator('[data-scenario="side-connected"] a').click();await page.waitForSelector('#result:visible');
  assert.equal(await page.locator('#direction-app').getAttribute('data-plan-id'),'SIDE_PRESSURE');
  await ready(process.env.LOADING_PC+'/loading');await example(0);
  // Unknown/incorrect inputs never become a balanced matchup or a stale new report.
  await page.locator('#input-panel').evaluate(e=>e.open=true);await page.locator('.optional-settings').evaluate(e=>e.open=true);
  await page.locator('#opponent-mode').selectOption('UNKNOWN');await page.locator('#patch').fill('16.19');await analyze();
  assert.match(await page.locator('#lane-opponent-copy').innerText(),/미확인/);assert.match(await page.locator('#uncertainties').innerText(),/16.19.*16.20.1/);
  await page.locator('#input-panel').evaluate(e=>e.open=true);await page.locator('#pick-ENEMY-0').fill('Caitlyn');await page.locator('#analyze').click();
  assert.match(await page.locator('#loading-message').innerText(),/겹치지/);assert(await page.locator('#loading-results').isHidden());
  await example(0);
  // Cached PC snapshot import is explicit, authenticated, ChampSelect only; identities discarded.
  await page.locator('#input-panel').evaluate(e=>e.open=true);const before=requests.filter(u=>u.includes('/dev/')).length;
  await page.locator('#pc-import').click();assert.equal(requests.filter(u=>u.includes('/dev/')).length,before);
  const token=fs.readFileSync(process.env.LOADING_TOKEN,'utf8').trim();await page.evaluate(t=>sessionStorage.setItem('lol-coach-dev-token',t),token);
  await page.locator('#pc-import').click();await page.waitForFunction(()=>document.querySelector('#loading-message').textContent.startsWith('입력한'));
  assert.equal(await summary(),original);assert(!(await page.locator('body').innerText()).includes('synthetic-private-identity'));
  const state=JSON.parse(fs.readFileSync(process.env.LOADING_STATE,'utf8'));state.phase='InProgress';fs.writeFileSync(process.env.LOADING_STATE,JSON.stringify(state));
  await page.locator('#input-panel').evaluate(e=>e.open=true);await page.locator('#pc-import').click();await page.waitForFunction(()=>document.querySelector('#loading-message').textContent.includes('직접 입력'));
  assert.match(await page.locator('#loading-message').innerText(),/직접 입력/);
  // The exact public allowlist works under /lol-coach/, with mobile steps/zoom/details.
  await page.setViewportSize({width:390,height:844});await ready(process.env.LOADING_WEB+'/lol-coach/index.html');await example(0);
  await interactiveFlow('mobile');
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await skillPresentation();
  await mapSkillPresentation();
  const map=page.locator('#fight-content .scenario-grid').first();await map.locator('.scenario-steps [data-step="2"] button').click();
  assert.equal(await map.locator('.strategy-map').getAttribute('data-active-step'),'2');
  await map.locator('.map-header button').click();await page.waitForSelector('#loading-map-dialog[open]');
  await page.locator('#zoom-step-controls [data-map-step="3"]').click();assert.equal(await map.locator('.strategy-map').getAttribute('data-active-step'),'3');
  await page.locator('#map-scale').fill('200');await page.locator('#map-scale').dispatchEvent('input');
  assert(await page.locator('#map-zoom-stage').evaluate(e=>e.scrollWidth>e.clientWidth));
  await page.screenshot({path:process.env.LOADING_OUT+'/mobile-zoom.png'});await page.keyboard.press('Escape');
  await capture('#loading-summary','mobile-summary.png');await capture('#loading-lane','mobile-lane.png');
  await page.locator('.site-header nav a[aria-current]').click();await page.waitForSelector('#analyze:enabled');
  await page.locator('.site-header nav a[href="./directions.html"]').click();await page.waitForSelector('#result:visible');
  await page.goto(process.env.LOADING_WEB+'/lol-coach/status.html');await page.waitForSelector('#status-items section');
  assert.equal(errors.length,0,JSON.stringify(errors));assert.equal(bad.length,0,JSON.stringify(bad));
  process.stdout.write(JSON.stringify({passed:true,snapshots,checks:['context lane/jungle/fight actor separation','25 engine permutations and real form array reversal','distant ally preserves lane; own/enemy support changes mechanisms','six hypothetical decisions with reply/alternative and source boundary','base vs proposed role','missing support assignment does not fabricate duo','known support survives missing carry; swapped enemy roles disable duo template','unbound allied control removes concrete trap-follow action','true manual ten picks Korean/English','no economy required','actual composition and own role counterfactual','six milestone table','relevant legacy scenes and hash selection','unknown opponent and patch mismatch','invalid input hides stale report','explicit authenticated sanitized PC import and manual fallback','public repository subpath navigation','desktop1440/mobile390 no overflow','card/main/zoom step synchronization','mobile200percent zoom','public status'],browser_errors:errors,http_errors:bad,provider_requests:0,real_windows_connection:'BLOCKED_EXTERNAL',real_coaching_n:0,coaching_accuracy:null})+'\n');
 }finally{await browser.close();}
})().catch(e=>{process.stderr.write(String(e.stack||e));process.exitCode=1;});
'''

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass

class CachedDraft:
    def __init__(self,path):self.path=path
    def snapshot(self):return json.loads(self.path.read_text())

def main():
    if not affected():print(json.dumps(dict(status='UNCHANGED_LOADING_BROWSER_REUSED')));return 0
    from scripts.launch_pc import create_server
    from scripts.build_directions_web import build
    out=ROOT/'evidence/actual-evidence/loading'/('browser-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix='loading-browser-') as temp:
        p=Path(temp);build(p/'public'/'lol-coach');pc=create_server(p/'private',port=0)
        example=json.loads(subprocess.check_output(['node','-e',"const E=require('./web_r4/loading-engine.js'),C=require('./web_r4/loading-data.json');console.log(JSON.stringify(E.exampleInput(C,0)));"],cwd=ROOT,text=True))
        draft=dict(phase='PRE_GAME',patch=example['patch'],my_champion=example['own_champion'],my_position=example['own_position'],slots=[dict(side=side,slot=i+1,**pick) for side,key in [('ALLY','allies'),('ENEMY','enemies')] for i,pick in enumerate(example[key])])
        draft['riotId']='synthetic-private-identity';state=p/'cached-draft.json';state.write_text(json.dumps(dict(status='CONNECTED',phase='ChampSelect',revision=1,input=draft)));pc.pc_services=CachedDraft(state)
        public=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(p/'public')))
        try:
            for server in (pc,public):threading.Thread(target=server.serve_forever,daemon=True).start()
            (p/'probe.cjs').write_text(JS)
            env=dict(os.environ,NODE_PATH=os.environ.get('NODE_PATH','/opt/codex/cua_node/lib/node_modules'),LOADING_PC='http://127.0.0.1:'+str(pc.server_port),LOADING_WEB='http://127.0.0.1:'+str(public.server_port),LOADING_OUT=str(out),LOADING_TOKEN=str(p/'private/access-token'),LOADING_STATE=str(state))
            if 'CHROMIUM_EXECUTABLE' not in env and Path('/usr/bin/chromium').exists():env['CHROMIUM_EXECUTABLE']='/usr/bin/chromium'
            r=subprocess.run(['node',str(p/'probe.cjs')],cwd=ROOT,env=env,text=True,capture_output=True,timeout=150)
            (out/'browser.log').write_text(r.stdout+r.stderr)
            receipt=json.loads(r.stdout or '{}');receipt['passed']=bool(receipt.get('passed')) and r.returncode==0
            receipt['source_sha256']={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES}
            receipt['user_decisions_created']=len(pc.research.list())
            (out/'runner.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
            print(json.dumps(dict(passed=receipt['passed'],evidence_directory=str(out))))
            if not receipt['passed']:print(r.stderr,file=sys.stderr)
            return 0 if receipt['passed'] else 1
        finally:
            for server in (pc,public):server.shutdown();server.server_close()

if __name__=='__main__':raise SystemExit(main())

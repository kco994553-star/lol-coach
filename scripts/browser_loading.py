"""Affected loading flow in real Chromium, PC routes and repository-subpath export."""
from datetime import datetime,timezone
import functools,hashlib,json,os
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import subprocess,sys,tempfile,threading

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
SOURCES=['web_r4/home-assets/AsheBase.jpg', 'web_r4/home-assets/AsheSkin17.jpg', 'web_r4/home-assets/KaisaBase.jpg', 'web_r4/home-assets/KaisaSkin14.jpg', 'web_r4/home-assets/JinxBase.jpg', 'web_r4/home-assets/JinxSkin4.jpg', 'web_r4/home-assets/EzrealBase.jpg', 'web_r4/home-assets/EzrealSkin21.jpg', 'web_r4/home-assets/LuxBase.jpg', 'web_r4/home-assets/LuxSkin17.jpg', 'web_r4/home-assets/YasuoBase.jpg', 'web_r4/home-assets/YasuoSkin9.jpg', 'web_r4/home-assets/YoneBase.jpg', 'web_r4/home-assets/YoneSkin1.jpg', 'web_r4/home-assets/IreliaBase.jpg', 'web_r4/home-assets/IreliaSkin37.jpg', 'web_r4/home-assets/VayneBase.jpg', 'web_r4/home-assets/VayneSkin25.jpg', 'web_r4/home-assets/LeonaBase.jpg', 'web_r4/home-assets/LeonaSkin10.jpg', 'web_r4/home-assets/game-lane.webp', 'web_r4/home-assets/game-operations.webp', 'web_r4/home-assets/game-fight.webp']+['web_r4/coach-theme.css','web_r4/coach-shell.js','web_r4/hero-art.json','web_r4/home-assets/strategy-panels.webp']+['web_r4/home-assets/'+p for p in ('Ahri.jpg','Caitlyn.jpg','AhriSkin27.jpg','LuxSkin7.jpg','Moonlit.webp','strategy-objectives.webp','lane.jpg','fight.jpg')]+['web_r4/'+p for p in ['loading-coach.js', 'loading-coach-view.js', 'loading-coach.css', 'loading-knowledge.json', 'loading-study.js','loading-exchange.js','loading-exchange-view.js','loading-engagement.js','loading-engagement-view.js','dashboard.html','dashboard.js','dashboard.css','pro-dashboard.json','loading-wave.js','loading-wave-view.js','loading-exploration.js','loading-interactive.js','loading.html','loading.js','loading.css','loading-engine.js','loading-map.js','loading-data.json','skill-data.js','skill-display.js','directions-engine.js','directions.js']]+['coach_v1/pregame_server.py','scripts/build_directions_web.py','scripts/browser_loading.py']

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
 page.on('request',r=>{requests.push(r.url());assert([process.env.LOADING_PC,process.env.LOADING_WEB].some(b=>r.url().startsWith(b+'/')),'unexpected external request');assert.equal(r.method(),r.url().endsWith('/dev/v1/account/lookup')?'POST':'GET');});
 page.on('response',r=>{if(r.status()>=400)bad.push({path:new URL(r.url()).pathname,status:r.status()});});
 const ready=async url=>{await page.goto(url);await page.waitForSelector('#analyze:enabled');};
 const analyze=async()=>{await page.locator('#analyze').click();await page.waitForSelector('#loading-results:visible');await page.locator('#loading-legacy-details').evaluate(e=>e.open=true);};
 const example=async i=>{await page.locator('#input-panel').evaluate(e=>e.open=true);await page.locator('#example-'+i).click();await analyze();};
 const capture=async(selector,file)=>page.locator(selector).screenshot({path:process.env.LOADING_OUT+'/'+file});
 const summary=async()=>page.locator('#loading-summary').innerText();
 const interactiveFlow=async(label)=>{
  const flow=page.locator('#interactive-flow');await flow.waitFor({state:'visible'});await page.locator('#wave-skill-means').evaluate(e=>e.open=true);
  const selected=async()=>flow.getAttribute('data-selected-plan');
  assert.equal(await selected(),'PREPARE_WINDOW');await page.locator('#risk-OPPORTUNITY').check();assert.equal(await selected(),'PREPARE_WINDOW');assert.match(await page.locator('#exploration-summary').innerText(),/현재 조건에서는 선택이 같습니다/);assert(await page.locator('#preview-SHORT_FOLLOW').isDisabled());
  await page.locator('#assumptions-ready').click();assert.equal(await selected(),'SHORT_FOLLOW');assert.equal(await page.locator('#active-plan').getAttribute('data-plan'),'SHORT_FOLLOW');
  await page.locator('#risk-BALANCED').check();assert.equal(await selected(),'SHORT_FOLLOW');assert.match(await page.locator('#exploration-summary').innerText(),/현재 조건에서는 선택이 같습니다/);await page.locator('#risk-OPPORTUNITY').check();assert.equal(await selected(),'SHORT_FOLLOW');assert.match(await page.locator('#exploration-summary').innerText(),/현재 조건에서는 선택이 같습니다/);
  const shortCosts=await flow.locator('[data-plan-id="SHORT_FOLLOW"]').innerText(),receiveCosts=await flow.locator('[data-plan-id="RECEIVE_WITH_LUX"]').innerText();assert.match(shortCosts,/소모|전진 노출/);assert.match(receiveCosts,/CS|주도권|미니언/);
  const beforePath=await page.locator('#active-plan .strategy-map').innerHTML();await page.locator('#risk-LOSS_LIMIT').check();assert.equal(await selected(),'RECEIVE_WITH_LUX');assert.equal(await page.locator('#active-plan').getAttribute('data-plan'),'RECEIVE_WITH_LUX');assert.notEqual(await page.locator('#active-plan .strategy-map').innerHTML(),beforePath);assert.match(await page.locator('#selected-action').innerText(),/포기할 미니언/);
  await page.locator('#risk-OPPORTUNITY').check();assert.equal(await selected(),'SHORT_FOLLOW');
  const map=page.locator('#active-plan .scenario-grid');await map.locator('[data-map-step="ALL"]').click();await map.locator('[data-map-action="3"]').first().focus();await page.keyboard.press('Enter');assert.equal(await map.locator('.strategy-map').getAttribute('data-active-step'),'3');assert.equal(await page.locator('#selected-action').getAttribute('data-step'),'3');assert.match(await page.locator('#selected-action').innerText(),/케이틀린의 요들잡이 덫\(W\)/);
  await map.locator('.scenario-steps [data-step="2"] button').click();assert.equal(await map.locator('.strategy-map').getAttribute('data-active-step'),'2');assert.equal(await page.locator('#selected-action').getAttribute('data-step'),'2');
  await map.locator('.map-header button').click();await page.waitForSelector('#loading-map-dialog[open]');await page.locator('#zoom-step-controls [data-map-step="ALL"]').click();await page.locator('#zoom-map [data-map-action="1"]').first().focus();await page.keyboard.press(' ');assert.equal(await map.locator('.strategy-map').getAttribute('data-active-step'),'1');assert.equal(await page.locator('#selected-action').getAttribute('data-step'),'1');assert.match(await page.locator('#zoom-selected-action').innerText(),/럭스의 빛의 속박\(Q\)/);await page.locator('#zoom-step-controls [data-map-step="3"]').click();assert.match(await page.locator('#zoom-selected-action').innerText(),/케이틀린의 요들잡이 덫\(W\)/);await page.locator('#zoom-step-controls [data-map-step="1"]').click();await page.locator('#map-scale').fill('200');await page.locator('#map-scale').dispatchEvent('input');assert(await page.locator('#map-zoom-stage').evaluate(e=>e.scrollWidth>e.clientWidth));await page.keyboard.press('Escape');
  if(label==='mobile'){await map.locator('[data-map-step="ALL"]').click();const target=await map.locator('[data-map-action="2"] circle').first().boundingBox();await page.touchscreen.tap(target.x+target.width/2,target.y+target.height/2);assert.equal(await page.locator('#selected-action').getAttribute('data-step'),'2');}
  await page.locator('#assumption-binding').selectOption('MISS');assert.equal(await selected(),'RECEIVE_WITH_LUX');assert.equal(await page.locator('#condition-change').getAttribute('data-action-changed'),'true');assert(await page.locator('#preview-SHORT_FOLLOW').isDisabled());
  await page.locator('#assumption-binding').selectOption('UNKNOWN');assert.equal(await selected(),'RECEIVE_WITH_LUX');assert(await page.locator('#preview-SHORT_FOLLOW').isDisabled());
  await page.locator('#assumption-exit_cover').selectOption('UNKNOWN');assert.equal(await selected(),'PREPARE_WINDOW');assert.equal(await page.locator('#active-plan .strategy-map path[marker-end]').count(),0);assert.equal(await page.locator('#active-plan [data-team="ENEMY"]').count(),0);
  await page.locator('#assumptions-ready').click();await page.locator('#why-SHORT_FOLLOW > summary').click();assert.match(await page.locator('#why-SHORT_FOLLOW').innerText(),/설계 가설|조건부/);assert(await page.locator('#why-SHORT_FOLLOW a[href^="https:"]').count()>=5);assert.match(await page.locator('#why-SHORT_FOLLOW').innerText(),/DUO-L2/);
  await capture('#active-plan',label+'-interactive-plan.png');await capture('#plan-comparison',label+'-interactive-comparison.png');
  await page.locator('#period-LEVEL6').click();await page.locator('#wave-skill-means').evaluate(e=>e.open=true);assert.equal(await selected(),'UNSUPPORTED');assert.match(await page.locator('#selected-lane-row').innerText(),/폭뢰\(R\)/);assert.equal(await flow.locator('#active-plan').count(),0);
  await page.locator('#explore-tab-OPERATIONS').click();assert.match(await flow.innerText(),/운영 기본안/);await page.locator('#explore-tab-FIGHT').click();assert.match(await flow.innerText(),/한타에서 내 역할/);await page.locator('#explore-tab-LANE').click();await page.locator('#period-LEVEL2').click();await page.locator('#assumptions-reset').click();assert.equal(await selected(),'PREPARE_WINDOW');assert.equal(await page.locator('#assumption-followup').inputValue(),'UNKNOWN');
  await page.locator('#risk-BALANCED').check();await page.locator('#input-panel').evaluate(e=>e.open=true);await page.locator('#pick-ALLY-0').fill('Malphite');assert(await page.locator('#loading-results').isHidden());assert.equal(await flow.locator('.strategy-map').count(),0);await analyze();assert.match(await page.locator('#fight-content').innerText(),/말파이트/);await example(0);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'interactive horizontal overflow');
 };
 const waveFlow=async(label)=>{
  await example(0);const wave=page.locator('#wave-flow');const selected=async()=>wave.getAttribute('data-wave-plan');
  assert.equal(await selected(),'CHECK_WAVE');assert(await page.locator('#wave-skill-means').evaluate(e=>!e.open));
  assert.match(await page.locator('#lane-key').innerText(),/웨이브/);
  await page.locator('#wave-example').click();assert.equal(await selected(),'SLOW_PUSH');
  await page.locator('#risk-OPPORTUNITY').check();assert.equal(await selected(),'FAST_PUSH');assert.match(await page.locator('#wave-choice').innerText(),/소모|노출/);
  await page.locator('#wave-preview-SLOW_PUSH').click();await page.locator('#wave-macro').evaluate(e=>e.open=true);assert.match(await page.locator('#wave-macro .scenario-steps-column > p').innerText(),/아군 잔여/);assert.equal(await page.locator('#wave-diagram [data-wave-direction]').getAttribute('data-wave-direction'),'TOWARD_ENEMY');await page.locator('#wave-preview-FAST_PUSH').click();await page.locator('#wave-macro').evaluate(e=>e.open=true);assert.match(await page.locator('#wave-macro .scenario-steps-column > p').innerText(),/처리 시간/);await page.locator('#wave-macro').evaluate(e=>e.open=false);

  await page.locator('#wave-skill-means').evaluate(e=>e.open=true);await page.locator('#assumptions-ready').click();assert.equal(await wave.getAttribute('data-follow-allowed'),'true');assert.match(await page.locator('#lane-key').innerText(),/가상 웨이브 목표/);
  await page.locator('#wave-purpose').selectOption('RESET');assert.equal(await selected(),'FAST_PUSH');assert.equal(await wave.getAttribute('data-follow-allowed'),'false');assert(await page.locator('#preview-SHORT_FOLLOW').isDisabled());assert.equal(await page.locator('#active-plan .strategy-map').count(),0);assert.match(await page.locator('#wave-choice').innerText(),/현재 조건에서는 선택이 같습니다/);
  await page.locator('#wave-punishment > summary').click();assert.match(await page.locator('#wave-punishment').innerText(),/공격보다|기본 행동으로 선택하지|처리/);
  assert.match(await page.locator('#wave-active').innerText(),/포탑 도착|Crash 완료/);await page.locator('#wave-crash').selectOption('READY');assert.equal(await selected(),'CRASH');
  await page.locator('#wave-flow').screenshot({path:process.env.LOADING_OUT+'/'+label+'-wave-crash.png'});
  await page.locator('#wave-flow').evaluate(e=>e.scrollIntoView());await page.locator('#wave-flow #wave-macro').evaluate(e=>e.open=true);
  await page.locator('#wave-step-2').click();assert.equal(await page.locator('#wave-selected-action').getAttribute('data-step'),'2');assert.equal(await page.locator('#wave-active .strategy-map').getAttribute('data-active-step'),'2');
  await page.locator('#wave-diagram .wave-diagram-control[data-wave-step="3"]').focus();await page.keyboard.press('Enter');assert.equal(await page.locator('#wave-selected-action').getAttribute('data-step'),'3');
  await page.locator('#wave-line-open').click();await page.locator('#wave-line-scale').fill('200');await page.locator('#wave-line-scale').dispatchEvent('input');assert(await page.locator('.wave-line-scroll').evaluate(e=>e.scrollWidth>e.clientWidth));assert.match(await page.locator('#wave-line-dialog').innerText(),/실제 관측 없음/);
  await page.keyboard.press('Escape');await page.locator('#wave-flow #wave-macro .map-step-controls [data-map-step="1"]').click();assert.equal(await page.locator('#wave-selected-action').getAttribute('data-step'),'1');
  await page.locator('#wave-flow #wave-macro').evaluate(e=>e.open=false);
  await page.locator('#wave-flow').screenshot({path:process.env.LOADING_OUT+'/'+label+'-wave-plan.png'});
  await page.locator('#wave-flow #wave-why').evaluate(e=>e.open=true);assert.match(await page.locator('#wave-why').innerText(),/기술의 성질만|원문/);assert.equal(await page.locator('#wave-why a[href^="https:"]').count(),7);
  await page.locator('#wave-flow').evaluate(e=>e.scrollIntoView());await page.locator('#wave-flow #wave-why').evaluate(e=>e.open=false);
  await page.locator('#wave-crash').selectOption('UNKNOWN');
  await page.locator('#wave-condition-flow').selectOption('INCOMING');await page.locator('#wave-access').selectOption('DENIED');assert.equal(await selected(),'TRIM_RECEIVE');
  await page.locator('#risk-LOSS_LIMIT').check();assert.equal(await selected(),'TRIM_RECEIVE');await page.locator('#risk-OPPORTUNITY').check();assert.equal(await selected(),'TRIM_RECEIVE');
  await page.locator('#wave-response').selectOption('UNKNOWN');assert.equal(await selected(),'CHECK_WAVE');assert(await page.locator('#wave-preview-FAST_PUSH').isDisabled());assert(await page.locator('#wave-preview-FREEZE').isDisabled());
  await page.locator('#wave-reset').click();assert.equal(await selected(),'CHECK_WAVE');assert.equal(await page.locator('#wave-purpose').inputValue(),'UNKNOWN');
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await example(0);
 };


 const engagementFlow=async(label)=>{
  await example(0);const g=page.locator('#engagement-flow'),wave=page.locator('#wave-flow');assert.equal(await g.getAttribute('data-advantage'),'UNKNOWN');
  await page.locator('#wave-example').click();assert.equal(await wave.getAttribute('data-wave-plan'),'SLOW_PUSH');
  const open=async()=>page.locator('#engagement-conditions').evaluate(e=>e.open=true);
  const set=async(key,value)=>{await open();await page.locator('#engagement-'+key).selectOption(value);};
  await set('resources','LOW');assert.equal(await page.locator('#wave-access').inputValue(),'READY');assert.equal(await wave.getAttribute('data-wave-plan'),'CHECK_WAVE');assert.equal(await g.getAttribute('data-wave-constraint'),'LIMIT_EXPOSURE');
  await set('window','ALL_READY');assert.match(await page.locator('#engagement-status').innerText(),/성립하지/);assert.equal(await wave.getAttribute('data-wave-plan'),'CHECK_WAVE');
  await page.locator('#engagement-reset').click();assert.equal(await wave.getAttribute('data-wave-plan'),'SLOW_PUSH');await page.locator('#wave-purpose').selectOption('RESET');assert.equal(await wave.getAttribute('data-wave-plan'),'FAST_PUSH');assert.match(await g.innerText(),/귀환 준비라/);await page.locator('#wave-reset').click();
  await page.locator('#input-panel').evaluate(e=>e.open=true);await page.locator('#pick-ALLY-3').fill('유나라');await page.locator('#pick-ALLY-4').fill('Lulu');await page.locator('#pick-ENEMY-3').fill('Lucian');await page.locator('#own-champion').selectOption('Yunara');await analyze();
  assert.equal(await g.getAttribute('data-advantage'),'UNKNOWN');assert.match(await wave.innerText(),/미지원|지원하지|지원은/);
  await page.locator('#period-LEVEL3_5').click();await page.locator('#engagement-type').selectOption('ALL_IN');await set('window','ALL_READY');assert.match(await page.locator('#engagement-status').innerText(),/궁극기/);assert.equal(await page.locator('#engagement-why blockquote').filter({hasText:'초월 상태에 돌입'}).count(),0);
  await page.locator('#period-LEVEL6').click();assert.match(await page.locator('#engagement-status').innerText(),/자기 초월\(R\)/);assert.match(await page.locator('#engagement-status').innerText(),/급성장\(R\)/);assert.equal(await g.getAttribute('data-advantage'),'UNKNOWN');assert.equal(await g.locator('[data-engagement-action="ALL_IN"]').count(),0);
  await set('window','ENEMY_Q_SPENT');for(const [key,value] of Object.entries({resources:'READY',followup:'BOTH',space:'PLAYABLE',intervention:'DUO_ONLY',growth:'COMPARABLE',spells:'BOTH_READY',initiator:'ALLY',hit:'ALLY_HIT'}))await set(key,value);
  await page.locator('#engagement-type').selectOption('SHORT');await page.locator('#risk-LOSS_LIMIT').check();assert.equal(await g.getAttribute('data-action'),'PRESERVE_INTAKE');await page.locator('#risk-OPPORTUNITY').check();assert.equal(await g.getAttribute('data-action'),'SHORT_WINDOW');assert.equal(await g.getAttribute('data-advantage'),'UNKNOWN');assert.match(await page.locator('#engagement-actions').innerText(),/확산|웨이브/);
  await page.locator('#engagement-table').evaluate(e=>e.open=true);assert.equal(await page.locator('#engagement-table tbody tr').count(),5);await page.locator('#engagement-why').evaluate(e=>e.open=true);assert.match(await page.locator('#engagement-why').innerText(),/사용자 제시 검토 가설/);assert(await page.locator('#engagement-why a[href^="https:"]').count()>=20);await page.locator('#engagement-why').evaluate(e=>e.open=false);
  await g.screenshot({path:process.env.LOADING_OUT+'/'+label+'-engagement.png'});
  await set('hit','ENEMY_HIT');assert.equal(await g.getAttribute('data-action'),'PRESERVE_INTAKE');assert.equal(await g.getAttribute('data-wave-constraint'),'LIMIT_EXPOSURE');await set('hit','UNKNOWN');assert.equal(await g.getAttribute('data-action'),'CS_WINDOW');await set('followup','UNKNOWN');assert.equal(await g.getAttribute('data-action'),'PRESERVE_INTAKE');assert.equal(await g.getAttribute('data-advantage'),'UNKNOWN');
  await page.locator('#engagement-type').focus();await page.keyboard.press('ArrowDown');await page.keyboard.press('Enter');assert.equal(await g.getAttribute('data-advantage'),'UNKNOWN');
  await page.locator('#period-FIRST_PURCHASE').click();assert.match(await page.locator('#engagement-status').innerText(),/6레벨 여부/);assert.equal(await page.locator('#engagement-why blockquote').filter({hasText:'초월 상태에 돌입'}).count(),0);await set('level_stage','POST6');assert.match(await page.locator('#engagement-status').innerText(),/자기 초월\(R\)/);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await example(0);
 };

 const exchangeFlow=async(label)=>{
  const neutral=await page.evaluate(async()=>{const C=await(await fetch(new URL('loading-data.json',location.href))).json(),a=LoadingStrategy.exampleInput(C,0);a.enemies.find(p=>p.position==='BOTTOM').champion='Jinx';const r=LoadingStrategy.analyze(a,C),g=LoadingEngagement.evaluate(r,C,LoadingEngagement.defaultState()),x=LoadingExchange.evaluate(r,C,g),n=LoadingExchangeView.create({result:x,report:r,catalog:C,engagement:g,onChange:()=>{},onReset:()=>{}});return {text:n.textContent,controls:n.querySelectorAll('select').length};});assert(!/카이사|케이틀린/.test(neutral.text));assert.equal(neutral.controls,0);
  await example(0);await page.locator('#input-panel').evaluate(e=>e.open=true);await page.locator('#pick-ALLY-3').fill('Yunara');await page.locator('#pick-ALLY-4').fill('Lulu');await page.locator('#pick-ENEMY-3').fill('Lucian');await page.locator('#own-champion').selectOption('Yunara');await analyze();await page.locator('#period-LEVEL6').click();
  const flow=page.locator('#exchange-flow'),ours=page.locator('#exchange-ours'),theirs=page.locator('#exchange-theirs');assert.equal(await ours.getAttribute('data-classification'),'UNKNOWN');
  for(const [key,value] of Object.entries({window:'ENEMY_Q_SPENT',resources:'READY',followup:'BOTH',space:'PLAYABLE',intervention:'DUO_ONLY',growth:'COMPARABLE',spells:'BOTH_READY',initiator:'ALLY',hit:'ALLY_HIT'})){await page.locator('#engagement-conditions').evaluate(e=>e.open=true);await page.locator('#engagement-'+key).selectOption(value);}
  const set=async(side,key,value)=>{await page.locator('#exchange-conditions').evaluate(e=>e.open=true);await page.locator('#exchange-'+side+'-'+key).selectOption(value);};
  for(const [side,values] of Object.entries({ours:{window:'REPEAT_ACTIVE',cover:'ACTIVE',contact:'CONNECTED'},theirs:{window:'HIT_WINDOW',cover:'ACTIVE',contact:'CONNECTED'}}))for(const [key,value] of Object.entries(values))await set(side,key,value);
  assert.equal(await ours.getAttribute('data-mode'),'REPEATED');assert.equal(await theirs.getAttribute('data-mode'),'SHORT');assert.match(await ours.innerText(),/유나라의 영혼 단련\(Q\)/);assert.match(await ours.innerText(),/룰루의 도와줘, 픽스!\(E\)/);assert.match(await ours.innerText(),/공격 순서/);assert.match(await theirs.innerText(),/노틸러스 자신/);assert.equal(await page.locator('#engagement-flow').getAttribute('data-advantage'),'UNKNOWN');
  const before=await ours.innerText();await page.locator('#risk-LOSS_LIMIT').check();assert.equal(await ours.innerText(),before);await page.locator('#risk-OPPORTUNITY').check();assert.equal(await ours.innerText(),before);assert.equal(await page.locator('#engagement-flow').getAttribute('data-action'),'SHORT_WINDOW');
  await page.locator('#exchange-periods').evaluate(e=>e.open=true);assert.equal(await page.locator('#exchange-periods tbody tr').count(),6);await page.locator('#exchange-periods').evaluate(e=>e.open=false);await page.locator('#exchange-conditions').evaluate(e=>e.open=false);
  snapshots.push({kind:'generated-exchange-repeat',device:label,ours:before,theirs:await theirs.innerText(),actual_advantage:await page.locator('#exchange-actual-advantage').innerText()});await flow.screenshot({path:process.env.LOADING_OUT+'/'+label+'-exchange-repeat.png'});
  await set('ours','cover','ENDING');assert.equal(await ours.getAttribute('data-mode'),'SHORT');assert.match(await ours.innerText(),/추가 공격을 시작하지/);assert.equal(await flow.getAttribute('data-attack-gate'),'NO_ADDITIONAL_ATTACK');assert.notEqual(await page.locator('#engagement-flow').getAttribute('data-action'),'SHORT_WINDOW');assert.equal(await page.locator('#engagement-actions [data-engagement-action="SHORT_WINDOW"]').count(),0);assert.equal(await page.locator('#engagement-flow').getAttribute('data-advantage'),'UNKNOWN');
  snapshots.push({kind:'generated-exchange-stop',device:label,ours:await ours.innerText(),wave:await page.locator('#exchange-wave').innerText()});await page.locator('#exchange-conditions').evaluate(e=>e.open=false);await flow.screenshot({path:process.env.LOADING_OUT+'/'+label+'-exchange-stop.png'});
  await set('theirs','window','REPEAT_ACTIVE');assert.equal(await theirs.getAttribute('data-mode'),'REPEATED');assert.match(await theirs.innerText(),/재사용 대기시간을 임의 계산/);
  await set('ours','cover','UNKNOWN');assert.equal(await ours.getAttribute('data-classification'),'UNKNOWN');assert.equal(await ours.getAttribute('data-mode'),'UNKNOWN');
  await page.locator('#exchange-reset').click();assert.equal(await ours.getAttribute('data-classification'),'UNKNOWN');assert.equal(await page.locator('#exchange-ours-window').inputValue(),'UNKNOWN');
  await page.locator('#period-LEVEL1').click();assert.equal(await ours.getAttribute('data-classification'),'UNKNOWN');assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await example(0);await page.locator('#wave-example').click();await page.locator('#wave-purpose').selectOption('RESET');assert.equal(await page.locator('#exchange-wave').getAttribute('data-adoption'),'WITHHELD_FOR_RESET');assert.match(await page.locator('#exchange-wave').innerText(),/처리·이탈 자원/);
  await page.locator('#wave-purpose').selectOption('SPACE');await page.locator('#wave-skill-means').evaluate(e=>e.open=true);await page.locator('#assumptions-ready').click();assert.equal(await page.locator('#interactive-flow').getAttribute('data-selected-plan'),'SHORT_FOLLOW');assert(!(await page.locator('#preview-SHORT_FOLLOW').isDisabled()));
  await set('ours','cover','ENDING');await page.locator('#wave-skill-means').evaluate(e=>e.open=true);assert.equal(await page.locator('#interactive-flow').getAttribute('data-selected-plan'),'SHORT_FOLLOW');assert.equal(await page.locator('#interactive-flow').getAttribute('data-adopted-plan'),'NO_ADDITIONAL_ATTACK');assert(await page.locator('#preview-SHORT_FOLLOW').isDisabled());assert.equal(await page.locator('#active-plan .strategy-map').count(),0);assert.match(await page.locator('#condition-change').innerText(),/추가 공격을 제외/);
  await page.locator('#input-panel').evaluate(e=>e.open=true);await page.locator('#pick-ALLY-0').fill('Malphite');assert(await page.locator('#loading-results').isHidden());await analyze();assert.equal(await page.locator('#exchange-ours').getAttribute('data-classification'),'UNKNOWN');await example(0);
 };

 const coachFlow=async(label)=>{
  const base=process.env.LOADING_WEB+'/lol-coach/';await ready(base+'loading.html');
  await page.locator('#example-0').click();await page.locator('#analyze').click();await page.waitForSelector('#loading-coach .coach-matrix');
  const host=page.locator('#loading-coach'),view=host.locator('.loading-coach');
  const button=key=>host.locator('[data-coach-focus="'+key+'"]');
  const condition=async(key,value)=>{await host.locator('details[id$="-conditions"]').evaluate(e=>e.open=true);await button('condition-'+key).selectOption(value);await page.waitForFunction(()=>document.querySelector('#loading-coach').getAttribute('aria-busy')==='false');};
  assert.equal(await page.locator('#loading-legacy-details').evaluate(e=>e.open),false);assert.equal(await host.locator('details[id$="-conditions"]').evaluate(e=>e.open),false);
  assert.equal(await view.getAttribute('data-matchup'),'A');assert.equal(await host.locator('.coach-matrix tbody tr').count(),6);assert.equal(await host.locator('.coach-matrix tbody tr').first().locator('td[data-assessment="ALLY"]').count(),2);
  assert.match(await host.locator('.coach-overview').innerText(),/ウェイ|웨이브/);assert(await host.locator('.coach-execution-steps').isVisible());assert.equal(await host.locator('.coach-line').first().getAttribute('data-plan'),'SLOW_PUSH');
  await page.screenshot({path:process.env.LOADING_OUT+'/'+label+'-coach-default.png'});
  const grid=await host.locator('.coach-matrix').innerText();await button('risk-LOSS_LIMIT').click();assert.equal(await view.getAttribute('data-selected-action'),'CONTROL_WAVE');const loss=await host.locator('.coach-execution-steps').innerText();await button('risk-OPPORTUNITY').click();assert.equal(await view.getAttribute('data-selected-action'),'SHORT_POKE');assert.notEqual(await host.locator('.coach-execution-steps').innerText(),loss);assert.equal(await host.locator('.coach-matrix').innerText(),grid);assert(await host.locator('.coach-choice-comparison').isVisible());
  await button('card-step-2').click();assert.equal(await host.locator('.coach-line').first().getAttribute('data-step'),'2');await button('open-zoom').click();assert(await host.locator('.coach-zoom').evaluate(e=>e.open));await button('zoom-step-3').click();assert.equal(await host.locator('.coach-line').first().getAttribute('data-step'),'3');await page.keyboard.press('Escape');assert.equal(await button('open-zoom').evaluate(e=>e===document.activeElement),true);
  const why=host.locator('details[id$="-why-wave"]');await why.evaluate(e=>e.open=true);assert(await why.locator('blockquote').count()>0);assert(await why.locator('a[href^="https://"]').count()>0);await why.evaluate(e=>e.open=false);
  await condition('resources','LOW');assert.equal(await view.getAttribute('data-selected-action'),'RECEIVE');assert.equal(await host.locator('.coach-line').first().getAttribute('data-plan'),'TRIM_RECEIVE');await button('risk-LOSS_LIMIT').click();assert.equal(await view.getAttribute('data-selected-action'),'RECEIVE');assert.match(await host.locator('.coach-preferences').innerText(),/현재 조건에서는.*같습니다/);
  snapshots.push({kind:'coach-low',device:label,text:await host.locator('.coach-execution-steps').innerText(),comparison:await host.locator('.coach-choice-comparison').innerText()});
  await condition('wave','UNKNOWN');assert.equal(await view.getAttribute('data-selected-action'),'CHECK_WAVE');assert.equal(await host.locator('.coach-line').count(),0);assert.equal(await host.locator('.coach-matrix tbody tr').first().locator('td').first().getAttribute('data-assessment'),'INSUFFICIENT');
  await button('reset-scenario').click();assert.equal(await button('condition-resources').inputValue(),'SUFFICIENT');assert.equal(await host.locator('.coach-line').first().getAttribute('data-plan'),'SLOW_PUSH');
  await button('period-LEVEL6').focus();await page.keyboard.press('Enter');assert.equal(await view.getAttribute('data-period'),'LEVEL6');assert.equal(await host.locator('.coach-matrix tbody tr').nth(3).locator('td').nth(1).getAttribute('data-assessment'),'INSUFFICIENT');
  await button('tab-operations').click();assert.match(await host.locator('[role=tabpanel]').innerText(),/기본 계획/);await button('tab-operations').focus();await page.keyboard.press('ArrowRight');assert.equal(await button('tab-fight').getAttribute('aria-selected'),'true');assert.match(await host.locator('[role=tabpanel]').innerText(),/내 역할/);await button('tab-lane').click();
  await page.locator('#input-panel').evaluate(e=>e.open=true);await page.locator('#example-2').click();await page.locator('#analyze').click();assert.equal(await view.getAttribute('data-matchup'),'B');await button('period-LEVEL3_5').click();await condition('engage','THEIRS');assert.equal(await view.getAttribute('data-selected-action'),'COUNTER_FOCUS_ADC');assert.match(await host.locator('.coach-execution-steps').innerText(),/카이사/);await condition('resources','LOW');assert.notEqual(await view.getAttribute('data-selected-action'),'COUNTER_FOCUS_ADC');
  await page.locator('#input-panel').evaluate(e=>e.open=true);await page.locator('#example-3').click();await page.locator('#analyze').click();assert.equal(await view.getAttribute('data-matchup'),'C');await condition('start_skill','Q');assert.match(await host.locator('.coach-execution-steps').innerText(),/바깥날/);assert(!/평타·.*마비의 일격/.test(await host.locator('.coach-execution-steps').innerText()));
  await page.locator('#input-panel').evaluate(e=>e.open=true);await page.locator('#example-4').click();await page.locator('#analyze').click();assert.equal(await view.getAttribute('data-matchup'),'D');await button('growth-KAISA_EVOLVED_ACCESS').click();assert.match(await host.locator('.coach-growth-detail').innerText(),/고정 3코어.*아니다/);assert.match(await host.locator('.coach-growth-detail').innerText(),/견제/);await page.screenshot({path:process.env.LOADING_OUT+'/'+label+'-coach-growth.png'});
  await page.locator('#input-panel').evaluate(e=>e.open=true);await page.locator('#example-1').click();await page.locator('#analyze').click();assert.equal(await view.getAttribute('data-matchup'),'UNSUPPORTED');assert.equal(await host.locator('.coach-line').count(),0);assert(!/신비한 화살|비전 이동/.test(await host.locator('.coach-execution-steps').innerText()));
  await page.locator('#input-panel').evaluate(e=>e.open=true);await page.locator('#pick-ALLY-0').fill('Darius');assert(await page.locator('#loading-results').isHidden());assert.equal(await host.locator('.loading-coach').count(),0);
  await page.locator('#example-0').click();await page.locator('.optional-settings').evaluate(e=>e.open=true);await page.locator('#patch').fill('1.1');await page.locator('#analyze').click();assert.match(await host.locator('.coach-overview').innerText(),/버전 차이/);assert.equal(await host.locator('.coach-line').count(),0);assert.equal(await view.getAttribute('data-selected-action'),'CHECK_WAVE');assert.equal(await host.locator('.coach-matrix td[data-assessment=ALLY]').count(),0);
  await page.goto(base+'directions.html#coach-lesson-B');await page.waitForSelector('#coach-lesson-B');assert.match(await page.locator('#coach-lesson-B').innerText(),/유나라.*룰루/);assert(await page.locator('#coach-lesson-B a[href^="https://"]').count()>0);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 };
 const homeDesignFlow=async(label)=>{
  const base=process.env.LOADING_WEB+'/lol-coach/';await page.goto(base+'index.html');await page.waitForSelector('#hero-cycle:enabled');assert.equal(await page.locator('.strategy-entry').count(),3);const source=await page.locator('#hero-art').getAttribute('src');await page.locator('#hero-cycle').click();assert.notEqual(await page.locator('#hero-art').getAttribute('src'),source);assert.equal(await page.locator('#riot-id').inputValue(),'');await page.locator('#hero-cycle').click();
  await page.locator('#hero-art').evaluate(e=>e.decode());for(const image of await page.locator('.entry-art>img').all())await image.evaluate(e=>e.decode());  assert(await page.locator('#hero-art').evaluate(e=>e.complete&&e.naturalWidth>0));assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:process.env.LOADING_OUT+'/'+label+'-home.png'});
  for(const [area,target,title] of [['lane','loading-coach','라인전'],['operations','loading-coach','운영'],['fight','loading-coach','한타']]){
   await page.goto(base+'index.html');const link=page.locator('[data-strategy-entry="'+area+'"]');if(area==='lane'){await link.focus();await page.keyboard.press('Enter');}else await link.click();await page.waitForSelector('#analyze:enabled');assert(await page.locator('#loading-results').isHidden());assert.match(await page.locator('#loading-message').innerText(),new RegExp(title));assert.equal(await page.locator('#pick-ALLY-3').inputValue(),'');
   await example(0);assert.equal(await page.locator('#loading-results').getAttribute('data-entry-target'),area);assert.equal(await page.evaluate(()=>document.activeElement.id),target);assert.equal(await page.locator('#report-teams .roster-pick').count(),10);assert.equal(await page.locator('#own-champion').inputValue(),'Caitlyn');await page.screenshot({path:process.env.LOADING_OUT+'/'+label+'-entry-'+area+'.png'});
  }
 };
 const sharedThemeFlow=async(label)=>{
  const base=process.env.LOADING_WEB+'/lol-coach/';await page.goto(base+'index.html');await page.waitForSelector('#coach-nav',{timeout:3000,state:'attached'});
  await page.context().addInitScript(()=>{const seed=sessionStorage.getItem('coach-test-random');if(seed) Math.random=()=>Number(seed);});
  await page.evaluate(()=>{sessionStorage.removeItem('lol-coach-hero-v1');sessionStorage.setItem('coach-test-random','0');});const seen=[];const onHero=r=>{if(/home-assets\//.test(r.url())&&!/strategy-|game-/.test(r.url()))seen.push(new URL(r.url()).pathname);};page.on('request',onHero);await page.reload();await page.waitForFunction(()=>document.querySelector('#hero-art')?.dataset.art==='Ahri');await page.locator('#hero-art').evaluate(e=>e.decode());assert.equal(new Set(seen).size,1);assert(seen.every(x=>x.endsWith('/Ahri.jpg')));
  await page.locator('#riot-id').fill('keep#KR1');await page.locator('#riot-id').focus();await page.evaluate(()=>scrollTo(0,0));const y=await page.evaluate(()=>scrollY),rect=await page.locator('#account-form').boundingBox();if(label==='mobile')await page.locator('#hero-cycle').tap();else await page.locator('#hero-cycle').click();await page.waitForFunction(()=>document.querySelector('#hero-art').dataset.art==='Caitlyn');assert.equal(await page.locator('#riot-id').inputValue(),'keep#KR1');assert.equal(await page.evaluate(()=>document.activeElement.id),'riot-id');assert.equal(await page.evaluate(()=>scrollY),y);assert.deepEqual(await page.locator('#account-form').boundingBox(),rect);if(label==='mobile'){const art=await page.locator('#hero-art').boundingBox(),head=await page.locator('.coach-mobile-header').boundingBox();assert(art.y>=head.y+head.height);assert(art.height<=300);}await page.locator('#hero-cycle').focus();const heroIds=await page.evaluate(async()=>{const c=await(await fetch('./hero-art.json')).json();return c.assets.map(x=>x.id);});assert.equal(heroIds.length,25);for(const id of heroIds.slice(2).concat(heroIds.slice(0,2))){await page.keyboard.press('Enter');await page.waitForFunction(id=>document.querySelector('#hero-art').dataset.art===id,id);await page.locator('#hero-art').evaluate(e=>e.decode());assert.equal(await page.evaluate(()=>document.activeElement.id),'hero-cycle');assert.equal(await page.locator('#riot-id').inputValue(),'keep#KR1');assert.equal(await page.evaluate(()=>scrollY),y);if(['AsheSkin17','KaisaBase','LuxSkin17','LeonaSkin10','Moonlit'].includes(id))await page.screenshot({path:process.env.LOADING_OUT+'/'+label+'-hero-'+id+'.png'});}assert.equal(await page.locator('.art-label').count(),0);for(const area of ['lane','operations','fight']){const im=page.locator('[data-strategy-entry="'+area+'"] .entry-art>img');assert.equal(await im.getAttribute('src'),'./home-assets/game-'+area+'.webp');await im.evaluate(e=>e.decode());}assert(!/AI 일러스트|AI로 만든/.test(await page.locator('body').innerText()));
  await page.evaluate(()=>sessionStorage.setItem('coach-test-random','0'));await page.reload();await page.waitForFunction(()=>document.querySelector('#hero-art')?.dataset.art==='Caitlyn');await page.evaluate(()=>{sessionStorage.removeItem('lol-coach-hero-v1');sessionStorage.setItem('coach-test-random','.99');});await page.reload();await page.waitForFunction(()=>document.querySelector('#hero-art')?.dataset.art==='LeonaSkin10');page.off('request',onHero);
  await page.route('**/home-assets/*',r=>/strategy-|game-/.test(r.request().url())?r.continue():r.abort());await page.reload();await page.waitForFunction(()=>document.querySelector('#hero-status')?.dataset.state==='ERROR');await page.locator('#riot-id').fill('keep#KR1');await page.locator('#account-submit').click();await page.waitForFunction(()=>document.querySelector('#account-status').dataset.state==='API_UNAVAILABLE');assert.equal(await page.locator('#account-status').getAttribute('data-state'),'API_UNAVAILABLE');assert(await page.locator('#account-retry').isVisible());await page.locator('#account-retry').click();await page.waitForFunction(()=>document.querySelector('#account-status').dataset.state==='API_UNAVAILABLE');assert.equal(await page.locator('#account-status').getAttribute('data-state'),'API_UNAVAILABLE');assert(await page.locator('#guest-entry').isEnabled());await page.unroute('**/home-assets/*');
  await page.route('**/hero-art.json',r=>r.fulfill({contentType:'application/json',body:JSON.stringify({format:'lol-coach-hero-art-v1',assets:[]})}));await page.reload();await page.waitForFunction(()=>document.querySelector('#hero-status')?.dataset.state==='EMPTY');assert(await page.locator('#guest-entry').isEnabled());assert.match(await page.locator('#hero-status').innerText(),/목록|일러스트/);await page.unroute('**/hero-art.json');
  const styles=[];for(const [file,current] of [['index.html','home'],['loading.html','prepare'],['directions.html','practice'],['status.html','status']]){await page.goto(base+file);await page.waitForSelector('#coach-nav',{state:'attached'});assert.equal(await page.locator('#coach-nav [aria-current]').getAttribute('data-page'),current);styles.push(await page.evaluate(()=>({bg:getComputedStyle(document.body).backgroundColor,font:getComputedStyle(document.body).fontFamily,accent:getComputedStyle(document.documentElement).getPropertyValue('--accent').trim()})));assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));if(file==='index.html'){for(const image of await page.locator('.entry-art>img').all())await image.evaluate(e=>e.decode());}await page.screenshot({path:process.env.LOADING_OUT+'/'+label+'-shared-'+current+'.png'});}assert(styles.every(x=>JSON.stringify(x)===JSON.stringify(styles[0])));
  await page.goto(base+'index.html');await page.waitForSelector('#hero-cycle');await page.locator('#guest-entry').click();assert.equal(await page.locator('#account-status').getAttribute('data-state'),'GUEST');assert.equal(await page.locator('#coach-nav').getAttribute('data-current'),'dashboard');await page.screenshot({path:process.env.LOADING_OUT+'/'+label+'-shared-dashboard.png'});await page.locator('#prepare-main').click();await page.waitForSelector('#analyze:enabled');await example(0);assert.equal(await page.locator('#report-teams .roster-pick').count(),10);const radio=await page.locator('#risk-BALANCED').boundingBox();assert(radio.width<30&&radio.height<30);await page.locator('#period-LEVEL6').click();assert.equal(await page.locator('#interactive-flow').getAttribute('data-period'),'LEVEL6');await page.screenshot({path:process.env.LOADING_OUT+'/'+label+'-shared-analysis.png'});
  if(label==='mobile'){await page.locator('#menu-toggle').click();assert.equal(await page.locator('#menu-toggle').getAttribute('aria-expanded'),'true');await page.keyboard.press('Escape');assert.equal(await page.locator('#menu-toggle').getAttribute('aria-expanded'),'false');await page.locator('#menu-toggle').click();}await page.locator('#coach-nav [data-page="practice"]').click();await page.waitForSelector('#result:visible');await page.locator('#map-zoom').click();await page.waitForSelector('#map-dialog[open]');await page.keyboard.press('Escape');assert(await page.locator('#map-dialog').isHidden());
  await page.evaluate(()=>{document.documentElement.style.fontSize='200%';});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.evaluate(()=>{sessionStorage.removeItem('coach-test-random');document.documentElement.style.fontSize='';});
 };
 const desktopCompositionFlow=async()=>{
  const measurements=[];
  for(const [width,height] of [[980,800],[980,1800],[952,688],[1440,900],[1920,1080],[701,900],[390,844],[282,690]]){
   await page.setViewportSize({width,height});await page.goto(process.env.LOADING_WEB+'/lol-coach/index.html');await page.evaluate(()=>sessionStorage.setItem('lol-coach-hero-v1','Ahri'));await page.reload();await page.waitForSelector('#hero-cycle:enabled');await page.locator('#hero-art').evaluate(e=>e.decode());for(const im of await page.locator('.entry-art>img').all())await im.evaluate(e=>e.decode());
   const data=await page.evaluate(()=>{const box=s=>{const r=document.querySelector(s).getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height,right:r.right,bottom:r.bottom};};return {width:innerWidth,height:innerHeight,stage:box('.home-stage'),cards:box('.strategy-entries'),entries:['lane','operations','fight'].map(a=>box('[data-strategy-entry='+a+']')),input:box('#riot-id'),region:box('#region'),submit:box('#account-submit'),guestInPanel:!!document.querySelector('.search-panel #guest-entry'),overflow:document.documentElement.scrollWidth>innerWidth};});
   assert(!data.overflow);assert(!data.guestInPanel);assert.equal(await page.locator('.coach-brand svg').first().getAttribute('data-icon'),'brand');assert.equal(await page.locator('[data-strategy-entry=operations] .entry-icon svg').getAttribute('data-icon'),'operations');
   if(width>700){assert(data.stage.h<1050,'no viewport-height-driven blank area');for(const b of [data.region,data.submit]){assert(Math.abs(b.y-data.input.y)<1);assert(Math.abs(b.h-data.input.h)<1);}for(let i=0;i<3;i++){const b=data.entries[i];assert(b.right<=data.cards.right+1);if(i<2)assert(b.right+8<=data.entries[i+1].x,'cards must have visible gutters, no clipping');}if(width===952)assert(data.entries[2].bottom<=height,'reference desktop frame must contain all three cards');}
   measurements.push(data);if([980,952,1440,390].includes(width))await page.screenshot({path:process.env.LOADING_OUT+'/composition-'+width+'x'+height+'.png'});
   if(width===980&&height===1800){await page.locator('#account-submit').click();await page.waitForFunction(()=>document.querySelector('#account-status').dataset.state==='INPUT_ERROR');assert(await page.locator('#account-status').isVisible());const boxes=await page.evaluate(()=>{const a=document.querySelector('#account-status').getBoundingClientRect(),b=document.querySelector('#guest-entry').getBoundingClientRect();return {status:a.bottom,guest:b.top};});assert(boxes.guest>=boxes.status);}
  }
  assert(Math.abs(measurements[0].stage.h-measurements[1].stage.h)<1,'same desktop width must keep composition across tall/landscape windows');
  snapshots.push({kind:'desktop-reference-composition',measurements});
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
  await waveFlow('desktop');
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
  await page.setViewportSize({width:390,height:844});await ready(process.env.LOADING_WEB+'/lol-coach/loading.html');await example(0);
  await waveFlow('mobile');
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
  await page.locator('#menu-toggle').click();await page.locator('#coach-nav [data-page=prepare]').click();await page.waitForSelector('#analyze:enabled');
  await page.locator('#menu-toggle').click();await page.locator('#coach-nav [data-page=practice]').click();await page.waitForSelector('#result:visible');

  // New account entry: real service/projection against isolated protocol fixture only.
  await page.setViewportSize({width:1440,height:1000});await page.goto(process.env.LOADING_PC+'/index.html');await page.waitForSelector('#account-submit');
  await page.evaluate(()=>sessionStorage.removeItem('lol-coach-dev-token'));await page.locator('#riot-id').fill('synthetic-fixture#KR1');await page.locator('#account-submit').click();assert.equal(await page.locator('#account-status').getAttribute('data-state'),'AUTH_REQUIRED');
  await page.evaluate(t=>sessionStorage.setItem('lol-coach-dev-token',t),token);await page.locator('#riot-id').fill('missing#KR1');await page.locator('#account-submit').click();await page.waitForFunction(()=>document.querySelector('#account-status').dataset.state==='ACCOUNT_NOT_FOUND');
  await page.locator('#riot-id').fill('synthetic-fixture#KR1');await page.locator('#account-submit').click();await page.waitForFunction(()=>document.querySelector('#account-status').dataset.state==='CONNECTED');assert(await page.locator('#pro-entry').isHidden());assert.match(await page.locator('#profile-scope').innerText(),/1경기/);assert.match(await page.locator('#profile-rank').innerText(),/골드 II/);assert.equal(await page.locator('#recent-matches .match-row').count(),1);assert.match(await page.locator('#coaching-notes').innerText(),/별개|아직 없습니다/);
  await page.locator('#guest-entry').click();assert.equal(await page.locator('#account-status').getAttribute('data-state'),'GUEST');assert(await page.locator('#pro-entry').isVisible());assert.match(await page.locator('#profile-name').innerText(),/연결 전/);
  await page.locator('#riot-id').fill('slow#KR1');await page.locator('#account-submit').click();assert.equal(await page.locator('#account-status').getAttribute('data-state'),'LOADING');await page.locator('#guest-entry').click();assert.equal(await page.locator('#account-status').getAttribute('data-state'),'GUEST');assert(await page.locator('#account-submit').isEnabled());
  await page.locator('#riot-id').fill('edited#KR1');assert.match(await page.locator('#profile-name').innerText(),/연결 전/);assert.equal(await page.locator('#recent-matches .match-row').count(),0);
  // Public artifact knows it has no private backend, even under localhost test server.
  await page.goto(process.env.LOADING_WEB+'/lol-coach/index.html');await page.waitForSelector('#account-submit');
  assert.equal(await page.locator('body').getAttribute('data-account-backend'),'PUBLIC_STATIC');const accountBefore=requests.filter(u=>u.includes('/dev/v1/account')).length;
  await page.locator('#riot-id').fill('bad');await page.locator('#account-submit').click();assert.equal(await page.locator('#account-status').getAttribute('data-state'),'INPUT_ERROR');
  await page.locator('#riot-id').fill('synthetic-fixture#KR1');await page.locator('#account-submit').click();await page.waitForFunction(()=>document.querySelector('#account-status').dataset.state==='API_UNAVAILABLE');assert.equal(requests.filter(u=>u.includes('/dev/v1/account')).length,accountBefore);assert.match(await page.locator('#pro-records').innerText(),/확인된 LCK/);
  await capture('#account-search','desktop-account-entry.png');await capture('#dashboard','desktop-dashboard.png');
  await page.setViewportSize({width:390,height:844});await page.locator('#menu-toggle').click();assert.equal(await page.locator('#menu-toggle').getAttribute('aria-expanded'),'true');await page.locator('#menu-toggle').click();assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await capture('#account-search','mobile-account-entry.png');await capture('#dashboard','mobile-dashboard.png');
  await page.locator('#guest-entry').click();await page.locator('#prepare-main').click();await page.waitForSelector('#analyze:enabled');await example(0);assert.equal(await page.locator('#report-teams .roster-pick').count(),10);assert.equal(await page.locator('#wave-flow').getAttribute('data-wave-plan'),'CHECK_WAVE');

  // Separate display fixture: pro records reuse real projection shape, never adopted as actual data.
  const fixtureProfile={format:'lol-coach-account-profile-v1',riot_id:'synthetic-reference#KR1',region:'KR',retrieved_at:'2026-10-17T00:00:00Z',rank:null,recent_matches:[{champion:'Caitlyn',won:true,kills:2,deaths:1,assists:3,started_at:1792194000000,queue_id:420}],champions:[{champion:'Caitlyn',sample_n:1,win_rate:100,kda:5}],statistics:{sample_n:1,window_start:1792194000000,window_end:1792194000000,queue_id:420,win_rate:100,kda:5},omitted_matches:0};
  await page.route('**/pro-dashboard.json',route=>route.fulfill({json:{format:'lol-coach-pro-dashboard-v1',queue_id:420,status:'READY',profiles:[{player:'Synthetic reference',team:'Fixture',position:'MID',roster_status:'CURRENT_LCK_FIRST_TEAM_VERIFIED',account_status:'VERIFIED',account_checked_at:'2026-10-17',profile:fixtureProfile}]}}));
  await page.goto(process.env.LOADING_WEB+'/lol-coach/index.html');await page.locator('#pro-records details > summary').click();assert.equal(await page.locator('[data-pro-recent] .match-row').count(),1);assert.match(await page.locator('[data-pro-recent]').innerText(),/Caitlyn.*승리/);assert.match(await page.locator('[data-pro-champions]').innerText(),/Caitlyn.*1경기/);assert.match(await page.locator('#profile-name').innerText(),/연결 전/);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.unroute('**/pro-dashboard.json');
  await ready(process.env.LOADING_PC+'/loading');await engagementFlow('desktop');await page.setViewportSize({width:390,height:844});await ready(process.env.LOADING_WEB+'/lol-coach/loading.html');await engagementFlow('mobile');
  await ready(process.env.LOADING_PC+'/loading');await exchangeFlow('desktop');await page.setViewportSize({width:390,height:844});await ready(process.env.LOADING_WEB+'/lol-coach/loading.html');await exchangeFlow('mobile');await homeDesignFlow('mobile');await page.setViewportSize({width:1440,height:1000});await homeDesignFlow('desktop');await sharedThemeFlow('desktop');await page.setViewportSize({width:390,height:844});await sharedThemeFlow('mobile');await desktopCompositionFlow();
  await page.setViewportSize({width:1440,height:1000});await coachFlow('desktop');await page.setViewportSize({width:390,height:844});await coachFlow('mobile');
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
        from coach_v1.account_dashboard import AccountDashboardService
        def account_fixture(url,headers,timeout):
            # Isolated protocol fixture, never published as a real player or provider result.
            if '/accounts/by-riot-id/' in url:
                if '/missing/' in url:return 404,{},b'{}'
                if '/slow/' in url:__import__('time').sleep(.4)
                data={'puuid':'synthetic-own-puuid'}
            elif '/entries/by-puuid/' in url:data=[{'queueType':'RANKED_SOLO_5x5','tier':'GOLD','rank':'II','leaguePoints':30}]
            elif '/ids?' in url:data=['KR_111']
            else:data={'info':{'queueId':420,'gameStartTimestamp':1792195200000,'gameDuration':1800,'participants':[{'puuid':'synthetic-own-puuid','championName':'Caitlyn','win':True,'kills':4,'deaths':2,'assists':3}]}}
            return 200,{},json.dumps(data).encode()
        pc.account_dashboard_service=AccountDashboardService(api_key='RGAPI-'+'00000000-0000-0000-0000-000000000000',transport=account_fixture)
        public=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(p/'public')))
        try:
            for server in (pc,public):threading.Thread(target=server.serve_forever,daemon=True).start()
            (p/'probe.cjs').write_text(JS)
            env=dict(os.environ,NODE_PATH=os.environ.get('NODE_PATH','/opt/codex/cua_node/lib/node_modules'),LOADING_PC='http://127.0.0.1:'+str(pc.server_port),LOADING_WEB='http://127.0.0.1:'+str(public.server_port),LOADING_OUT=str(out),LOADING_TOKEN=str(p/'private/access-token'),LOADING_STATE=str(state))
            if 'CHROMIUM_EXECUTABLE' not in env and Path('/usr/bin/chromium').exists():env['CHROMIUM_EXECUTABLE']='/usr/bin/chromium'
            r=subprocess.run(['node',str(p/'probe.cjs')],cwd=ROOT,env=env,text=True,capture_output=True,timeout=300)
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

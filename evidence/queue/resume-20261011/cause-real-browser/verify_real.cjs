'use strict';
const {chromium}=require('playwright');
const fs=require('node:fs'),path=require('node:path');
const output=process.env.REAL_EVIDENCE_DIR;
const binding=JSON.parse(fs.readFileSync(path.join(output,'input-binding.json'),'utf8'));
const token=fs.readFileSync(process.env.WORKBENCH_TOKEN_FILE,'utf8').trim();
const checks=[],errors=[],consoleErrors=[],httpErrors=[],requests=[],responses=[];
let browser,page,firstFailure=null;
const check=(id,ok,detail)=>{checks.push({id,passed:!!ok,detail});if(!ok)throw new Error(id+': '+JSON.stringify(detail));};
const canonical=x=>JSON.stringify(x && typeof x==='object' ? Array.isArray(x)?x.map(y=>JSON.parse(canonical(y))):Object.fromEntries(Object.keys(x).sort().map(k=>[k,JSON.parse(canonical(x[k]))])):x);
const lane=()=>page.locator('#pg-card-lane .pg-power');
async function settled(){await page.waitForFunction(()=>document.querySelectorAll('#pg-cards>article').length===9 && [...document.querySelectorAll('.pg-power,.pg-outcome-view')].every(n=>!n.textContent.includes('불러오는 중')),{},{timeout:30000});await page.waitForLoadState('networkidle');}
async function savePlan(){const saved=page.waitForResponse(r=>/\/pregame\/inputs(?:\/[0-9a-f]+)?$/.test(new URL(r.url()).pathname)&&['POST','PUT'].includes(r.request().method()));await page.locator('#pg-save').click();const r=await saved;if(!r.ok())throw new Error('Input save '+r.status()+': '+await r.text());await page.waitForFunction(()=>!document.getElementById('pg-create-plan').disabled);const created=page.waitForResponse(r=>/\/inputs\/[0-9a-f]+\/plans$/.test(new URL(r.url()).pathname)&&r.request().method()==='POST');await page.locator('#pg-create-plan').click();const p=await created;if(!p.ok())throw new Error('Plan create '+p.status()+': '+await p.text());await settled();await page.waitForFunction(()=>!document.getElementById('pg-create-plan').disabled);return JSON.parse(await page.locator('#pg-plan-json').textContent());}
const selectedResponse=opponent=>responses.filter(r=>r.body.champion===binding.selection.champion&&r.body.position===binding.selection.position&&r.body.patch===binding.selection.patch&&r.body.opponent_champion===opponent).at(-1);
(async()=>{
 try{
  check('real-datasets',Object.values(binding.datasets).every(d=>d.source.sample_kind==='REAL'&&d.source.tier==='CHALLENGER'&&d.samples?.synthetic_matches===0),Object.fromEntries(Object.entries(binding.datasets).map(([k,d])=>[k,{digest:d.dataset_digest,status:d.status,samples:d.samples}])));
  browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_EXECUTABLE});page=await browser.newPage({viewport:{width:1440,height:1000}});
  page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text());});
  page.on('request',r=>{if(r.url().includes('/dev/v1/'))requests.push({path:new URL(r.url()).pathname,method:r.method(),body:r.postDataJSON()});});
  page.on('response',async r=>{if(r.status()>=400)httpErrors.push({path:new URL(r.url()).pathname,status:r.status()});if(r.url().endsWith('/power-view')){try{responses.push({body:r.request().postDataJSON(),reply:await r.json()});}catch(e){errors.push(e.message);}}});
  await page.goto(process.env.WORKBENCH_URL);await page.locator('#pg-token').fill(token);await page.locator('#pg-login').click();await page.waitForFunction(()=>!document.getElementById('pg-workspace').hidden&&!document.getElementById('pg-login').disabled&&document.getElementById('pg-notice').textContent.includes('연결'));await page.waitForLoadState('networkidle');
  const status=await page.evaluate(async()=>{const r=await fetch('/dev/v1/pregame/status',{headers:{Authorization:'Bearer '+sessionStorage.getItem('lol-coach-dev-token')}});return r.json();});
  check('production-auth',status.test_mode===false&&status.power_tiers.includes('CHALLENGER'),{test_mode:status.test_mode,power_tiers:status.power_tiers});
  const s=binding.selection,roles=['TOP','JUNGLE','MID','BOTTOM','SUPPORT'],slot=roles.indexOf(s.position)+1;
  await page.locator('#pg-title').fill('REAL aggregate browser verification · manually authored draft');await page.locator('#pg-phase').selectOption('PRE_GAME');await page.locator('#pg-patch').fill(s.patch);await page.locator('#pg-my-position').selectOption(s.position);await page.locator('#pg-my-champion').fill(s.champion);await page.locator('#pg-my-slot').selectOption(String(slot));
  for(const side of ['ally','enemy'])for(let i=0;i<roles.length;i++){await page.locator(`#pg-${side}-${i+1}-position`).selectOption(roles[i]);await page.locator(`#pg-${side}-${i+1}-uncertainty`).fill('Browser-authored draft; not observed current lobby');}
  await page.locator(`#pg-ally-${slot}-champion`).fill(s.champion);if(s.opponent_champion)await page.locator(`#pg-enemy-${slot}-champion`).fill(s.opponent_champion);
  const plan=await savePlan();
  check('manual-default-roles',plan.input.slots.every(p=>p.position===roles[p.slot-1]&&p.runes.status==='UNKNOWN'&&p.summoners.status==='UNKNOWN'),{draft:'manual, not actual lobby',role:s.position,champion:s.champion,opponent:s.opponent_champion});
  check('saved-current-plan',plan.validity==='CURRENT'&&plan.input.patch===s.patch&&await page.locator('#pg-cards>article').count()===9,{validity:plan.validity,patch:plan.input.patch});
  await page.locator('#pg-power-tier').selectOption('CHALLENGER');await settled();
  check('challenger-tier',await page.locator('#pg-power-tier').inputValue()==='CHALLENGER','Explicit CHALLENGER selection');
  const observed=selectedResponse(s.opponent_champion);
  check('source-bound-view',observed?.reply.test_mode===false&&canonical(observed.reply.view)===canonical(binding.expected.observed),observed?.reply);
  const rawGold=observed.reply.view.points.filter(p=>p.metric==='gold_delta'),rateDisplay=rawGold.some(p=>p.comparison==='ROLE_POPULATION');
  const eligibleGold=rawGold.filter(p=>p.visible===true&&(!rateDisplay||p.comparison!=='MATCHUP'||p.minute>0)),svgCount=await lane().locator('svg').count(),laneText=await lane().textContent();
  check('honest-precision-rendering',eligibleGold.length?svgCount===1&&await lane().locator('.pg-power-point').count()===eligibleGold.length:svgCount===0&&laneText.includes('UNKNOWN'),{gold_points:eligibleGold.length,view_status:observed.reply.view.status,reasons:observed.reply.view.reasons,svg_count:svgCount,ci_shades:await lane().locator('.pg-power-ci').count(),rate_display:rateDisplay,withheld_zero_minute:rawGold.length-eligibleGold.length});
  let hover={withheld:true,reason:'No eligible gold points; no fabricated CI or hover'};
  if(eligibleGold.length){const point=lane().locator('.pg-power-point').first();await point.focus();await point.hover();hover={withheld:false,label:await point.getAttribute('aria-label'),title:await point.locator('title').textContent()};}
  check('point-hover-or-withheld',eligibleGold.length?hover.label.includes('n=')&&hover.label.includes('95% CI')&&hover.title===hover.label:svgCount===0,hover);
  const source=lane().locator('.pg-power-source');await source.locator('summary').click();const sourceText=await source.textContent();
  check('real-source-details',sourceText.includes('REAL')&&sourceText.includes(binding.datasets.power.dataset_digest)&&sourceText.includes(s.patch)&&sourceText.includes('CHALLENGER')&&sourceText.includes('정밀도'),sourceText);
  await lane().screenshot({path:path.join(output,'observed-source.png')});
  await page.locator(`#pg-enemy-${slot}-champion`).fill('');await savePlan();const fallback=selectedResponse(null);
  check('unknown-opponent-fallback',fallback?.reply.test_mode===false&&canonical(fallback.reply.view)===canonical(binding.expected.fallback)&&fallback.reply.view.points.every(p=>p.comparison==='ROLE_POPULATION')&&(fallback.reply.view.status==='UNKNOWN'||(await lane().textContent()).includes('역할 평균 대비 분당')),fallback?.reply);
  await lane().screenshot({path:path.join(output,'unknown-opponent.png')});
  await page.locator('#pg-patch').fill('');const powerBefore=requests.filter(r=>r.path.endsWith('/power-view')).length;await savePlan();
  check('explicit-missing-patch',requests.filter(r=>r.path.endsWith('/power-view')).length===powerBefore&&(await lane().textContent()).includes('챔피언·포지션·정확한 패치 필요')&&await lane().locator('svg').count()===0,await lane().textContent());
  await lane().screenshot({path:path.join(output,'explicit-missing-patch.png')});
  check('no-synthetic-rendering',responses.every(r=>r.reply.view.source?.sample_kind==='REAL'&&r.reply.view.samples?.synthetic_matches===0)&&await page.locator('.pg-power-test,.pg-outcome-test').count()===0,{responses:responses.length,test_labels:await page.locator('.pg-power-test,.pg-outcome-test').count()});
  check('no-review-writes',requests.every(r=>!r.path.includes('/decisions')&&!r.path.includes('/knowledge/import')&&!r.path.includes('/experts/import')),requests.map(r=>({path:r.path,method:r.method})));
  check('clean-browser',errors.length===0&&consoleErrors.length===0&&httpErrors.length===0,{errors,consoleErrors,httpErrors});
 }catch(e){firstFailure={message:e.message,stack:e.stack};if(page)await page.screenshot({path:path.join(output,'failure.png'),fullPage:true}).catch(()=>{});}
 const receipt={evidence_kind:'FRESH_REAL_AGGREGATE_BROWSER_EXECUTION',passed:!firstFailure&&checks.length===binding.expected_check_ids.length,expected_check_ids:binding.expected_check_ids,checks,first_failure:firstFailure,page_errors:errors,console_errors:consoleErrors,http_errors:httpErrors,browser_version:browser?.version(),source_sha256:binding.source_sha256,scope:'Manual PRE_GAME draft over acquired REAL anonymous aggregates; no live lobby, gameplay accuracy or approval claim'};
 fs.writeFileSync(path.join(output,'receipt.json'),JSON.stringify(receipt,null,2)+'\n');if(browser)await browser.close();console.log(JSON.stringify({passed:receipt.passed,checks:checks.length,first_failure:firstFailure?.message}));process.exitCode=receipt.passed?0:1;
})();

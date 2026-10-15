"""Real archived anonymous datasets, real Chromium; no provider requests or live game input."""
from pathlib import Path
import sys,tempfile,threading,subprocess,os,json,hashlib
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.launch_pc import create_server
from coach_v1.pc_runtime import load_pc_default_datasets
from coach_v1.recall_pc import load_datasets
OUT=ROOT/'evidence/queue/v23'/('actual-browser-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));OUT.mkdir(parents=True)
BROWSER=r'''
const fs=require('node:fs'), assert=require('node:assert/strict');
const {chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_EXECUTABLE?{executablePath:process.env.CHROMIUM_EXECUTABLE}:{}),args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1600,height:1000}}),errors=[],timings=[],requests=[];let writes=0;
 const token=fs.readFileSync(process.env.PC_TOKEN_FILE,'utf8').trim(),base=process.env.PC_URL;
 page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{assert(!r.url().includes(token));if(r.method()!=='GET'&&!r.url().endsWith('/pc-preview'))writes++;});
 page.on('response',async r=>{if(r.url().endsWith('/pc-preview')&&r.ok())requests.push(await r.json());});
 async function measure(selector,value,label){
  await page.evaluate(()=>{window.actualMeasure={start:null,end:null};const host=document.querySelector('#pc-cards');const handler=()=>{actualMeasure.start=performance.now();document.querySelector('#pc-draft').removeEventListener('input',handler,true);};document.querySelector('#pc-draft').addEventListener('input',handler,true);const obs=new MutationObserver(()=>{if(actualMeasure.start!==null&&host.querySelector('.coach-card')){requestAnimationFrame(()=>actualMeasure.end=performance.now());obs.disconnect();}});obs.observe(host,{subtree:true,childList:true});});
  await page.fill(selector,value);await page.waitForFunction(()=>actualMeasure.end!==null);await page.waitForFunction(()=>document.querySelector('#pc-notice').textContent==='입력에 맞는 근거를 표시했습니다.');
  timings.push({label,input_to_card_ms:await page.evaluate(()=>Number((actualMeasure.end-actualMeasure.start).toFixed(2)))});
 }
 try{
  await page.goto(base+'/pc#token='+encodeURIComponent(token));await page.waitForSelector('#pc-workspace:visible');
  await page.selectOption('#pc-position','BOTTOM');await page.fill('#pc-patch','16.20');
  await measure('#pc-own','Caitlyn','REAL anonymous datasets: own pick');
  await page.locator('.more-cards > summary').click();
  await measure('#pc-laner','Ezreal','REAL anonymous datasets: opponent pick');
  const ref=await page.request.post(base+'/dev/v1/pregame/recall-reference',{headers:{Authorization:'Bearer '+token},data:{champion:'Caitlyn',position:'BOTTOM',patch:'16.20',opponent_champion:'Ezreal'}});
  assert.equal(ref.status(),200);const data=await ref.json();fs.writeFileSync(process.env.PC_OUTPUT+'/reference-response.json',JSON.stringify(data,null,2));
  assert(data.own.some(v=>v.status==='AVAILABLE'),'real recall distribution required');
  const cards=page.locator('.coach-card[data-section="RECALL"]');assert(await cards.count()>0);
  const stat=cards.filter({has:page.locator('.evidence.STATISTICS')}).first();assert(await stat.isVisible());
  await stat.locator('details > summary').click();assert((await stat.innerText()).includes('끝 구간'));
  assert(await stat.locator('.sources a').count()>0);await page.screenshot({path:process.env.PC_OUTPUT+'/actual-recall-1600.png',fullPage:true});
  assert.equal(errors.length,0);assert.equal(writes,0);
  fs.writeFileSync(process.env.PC_OUTPUT+'/preview-projections.json',JSON.stringify(requests,null,2));
  process.stdout.write(JSON.stringify({passed:true,goal_under_1000ms:timings.every(t=>t.input_to_card_ms<1000),timings,browser_version:browser.version(),browser_errors:errors,unexpected_writes:writes,recall_population_status:data.own.map(v=>({population:v.population,status:v.status,scope:v.scope,sample:v.sample})),scope:'Synthetic manual champion picks; REAL anonymous source-bound recall and Q15 datasets; actual Chromium and local HTTP; no game-PC or coaching-accuracy proof'})+'\n');
 }finally{await browser.close();}
})().catch(e=>{process.stderr.write(String(e.stack||e));process.exitCode=1;});
'''
with tempfile.TemporaryDirectory(prefix='v23-actual-data-') as temporary:
 p=Path(temporary);server=create_server(p,port=0)
 try:
  load_pc_default_datasets(server);loaded=load_datasets(server)
  if set(server.recall_datasets)!={'CHALLENGER','PRO_REFERENCE'}:raise SystemExit('BOTH_ACTUAL_RECALL_DATASETS_REQUIRED')
  threading.Thread(target=server.serve_forever,daemon=True).start()
  (p/'browser.cjs').write_text(BROWSER)
  env=dict(os.environ,NODE_PATH=os.environ.get('NODE_PATH','/opt/codex/cua_node/lib/node_modules'),PC_URL='http://127.0.0.1:'+str(server.server_port),PC_TOKEN_FILE=str(p/'access-token'),PC_OUTPUT=str(OUT))
  if 'CHROMIUM_EXECUTABLE' not in env and Path('/usr/bin/chromium').exists():env['CHROMIUM_EXECUTABLE']='/usr/bin/chromium'
  r=subprocess.run(['node',str(p/'browser.cjs')],cwd=ROOT,env=env,text=True,capture_output=True,timeout=120)
  (OUT/'browser.log').write_text((r.stdout+r.stderr).replace(server.token,'[REDACTED]'))
  receipt=json.loads(r.stdout.strip() or '{}');receipt['passed']=bool(receipt.get('passed')) and r.returncode==0
  receipt['source_sha256']={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('coach_v1/recall_pc.py','coach_v1/recall_stats.py','coach_v1/pc_runtime.py','coach_v1/pregame_server.py','scripts/browser_recall_actual_v23.py','web_r4/pc.js','web_r4/pc.css')}
  receipt['dataset_sha256']={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in (ROOT/'data/recall/2026-10-15').glob('*/recall-data.json')}
  receipt['actual_user_decisions_created']=len(server.research.list());receipt['loaded_populations']=loaded
  (OUT/'runner.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
  print(json.dumps({'passed':receipt['passed'],'goal_under_1000ms':receipt.get('goal_under_1000ms'),'timings':receipt.get('timings'),'evidence_directory':str(OUT)}))
  if not receipt['passed']:print(r.stderr.replace(server.token,'[REDACTED]'),file=sys.stderr)
  raise SystemExit(0 if receipt['passed'] else 1)
 finally:server.shutdown();server.server_close()

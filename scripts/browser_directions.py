"""Changed prototype acceptance in actual Chromium, against PC and mobile export."""
from datetime import datetime,timezone
import functools
import hashlib
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import json,os
from pathlib import Path
import subprocess,sys,tempfile,threading

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
SOURCES=['web_r4/coach-theme.css','web_r4/coach-shell.js','web_r4/directions.html','web_r4/directions.js','web_r4/directions.css',
    'web_r4/skill-data.js','web_r4/skill-display.js',
    'web_r4/directions-engine.js','web_r4/directions-data.json','web_r4/status.html',
    'web_r4/directions-status.js','web_r4/directions-status.json','coach_v1/pregame_server.py',
    'scripts/build_directions_web.py','scripts/browser_directions.py']


def affected():
    event_path=os.environ.get('GITHUB_EVENT_PATH')
    if not event_path:return True
    event=json.loads(Path(event_path).read_text());before=event.get('pull_request',{}).get('base',{}).get('sha') or event.get('before')
    if not before or set(before)=={'0'}:return True
    changed=set(subprocess.check_output(['git','diff','--name-only',before,'HEAD'],cwd=ROOT,text=True).splitlines())
    return bool(changed & set(SOURCES) or any(p.startswith('web_r4/direction-assets/') for p in changed))


JS=r'''
const fs=require('node:fs'),assert=require('node:assert/strict'),{chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_EXECUTABLE?{executablePath:process.env.CHROMIUM_EXECUTABLE}:{}),args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1600,height:1100}}),errors=[],requests=[],bad=[];
 page.on('pageerror',e=>errors.push(e.message));
 page.on('request',r=>{requests.push(r.url());assert([process.env.DIRECTION_PC_URL,process.env.DIRECTION_WEB_URL].some(base=>r.url().startsWith(base+'/')),'unexpected external request '+r.url());assert.equal(r.method(),'GET');});
 page.on('response',r=>{if(r.status()>=400&&!r.url().endsWith('/build-info.json'))bad.push({url:r.url(),status:r.status()});});
 const plan=()=>page.locator('#direction-app').getAttribute('data-plan-id');
  const displayedArrows=selector=>page.locator(selector+' [data-kind]').evaluateAll(nodes=>nodes.filter(e=>getComputedStyle(e).display!=='none').map(e=>e.dataset.step));
 const scene=async id=>{await page.click('#scene-'+id);await page.waitForFunction(()=>!!document.querySelector('#direction-app').dataset.planId);};
 const capture=async file=>{await page.locator('#main-plan').screenshot({path:process.env.DIRECTION_OUTPUT+'/'+file});};
 const sceneSkills=async id=>{
  const copy=await page.locator('#plan-steps').innerText(),aria=await page.locator('#plan-steps button').evaluateAll(buttons=>buttons.map(button=>button.getAttribute('aria-label')).join(' '));
  const expected=id.startsWith('recall-')?['케이틀린의 요들잡이 덫(W)','케이틀린의 90구경 투망(E)']:id==='side-connected'?['피오라의 찌르기(Q)','피오라의 응수(W)']:id==='side-exit-lost'?['피오라의 응수(W)']:id==='objective-connected'?['오른의 화염 돌진(E)']:[];
  expected.forEach(label=>{assert(copy.includes(label),label);assert(aria.includes(label),label+' accessible text');});
  assert(await page.evaluate(()=>{const own=document.querySelector('#champion').value,options={champions:[own],own,owner:own,aliases:own==='Caitlyn'?[{text:'덫',champion:own,slot:'W'},{text:'투망',champion:own,slot:'E'}]:[]};const copy=document.querySelector('#plan-steps').textContent;return SkillDisplay.format(copy,options)===copy;}));
 };
 const snapshots=[];
 try{
  await page.goto(process.env.DIRECTION_PC_URL+'/directions');await page.waitForSelector('#result:visible');
  assert.equal(await plan(),'INFORMATION_RESET');assert.equal(await page.locator('#map [data-team="ENEMY"]').count(),0);
  assert.equal(await page.locator('#map [data-landmark="wave"]').count(),0);
  for(const r of ['TOP','JUNGLE','MID','BOTTOM','SUPPORT'])assert.equal(await page.inputValue('#economy-'+r),'UNKNOWN');
  const scenes=['recall-crash','recall-incoming','side-connected','side-exit-lost','objective-connected','objective-short'];
  const expected=['RESET_AFTER_CRASH','RECEIVE_WAVE','SIDE_PRESSURE','SAFE_REGROUP','OBJECTIVE_SETUP','TRADE_KNOWN_RESOURCE'];
  for(let n=0;n<scenes.length;n++){
   await scene(scenes[n]);assert.equal(await plan(),expected[n]);assert.equal(await page.locator('#plan-steps > li').count(),3);
   for(const step of [1,2,3])assert(await page.locator('#map [data-kind][data-step="'+step+'"]').count());
   await sceneSkills(scenes[n]);
   assert.equal(await page.locator('#map [data-self="true"]').count(),1);
   snapshots.push({scene:scenes[n],plan:await plan(),title:await page.locator('#plan-title').innerText(),steps:await page.locator('#plan-steps > li').allInnerTexts()});
   await capture('scene-'+scenes[n]+'.png');
  }
  await scene('side-connected');await page.selectOption('#champion','Caitlyn');
  assert.match(await page.locator('#plan-steps').innerText(),/케이틀린의 요들잡이 덫\(W\)/);
  assert.match(await page.locator('#plan-steps button').nth(1).getAttribute('aria-label'),/케이틀린의 요들잡이 덫\(W\)/);
  await scene('recall-crash');
  const originalFacts=JSON.parse(fs.readFileSync('web_r4/directions-data.json','utf8')).champions.find(champion=>champion.id==='Caitlyn').official_facts;
  for(let index=0;index<originalFacts.length;index++){
   const fact=page.locator('#official-facts .fact-card').nth(index);assert.equal(await fact.locator('blockquote').textContent(),originalFacts[index].excerpt);
   assert.match(await fact.locator('h4').textContent(),/케이틀린의 .+\([WE]\)/);
   assert((await fact.locator('code').allTextContents()).some(value=>value==='SHA-256 · '+originalFacts[index].sha256));
  }
  await scene('recall-crash');await page.selectOption('#condition-wave','INCOMING_LARGE');assert.equal(await plan(),'RECEIVE_WAVE');
  for(const state of ['AHEAD','BEHIND','UNKNOWN']){await page.selectOption('#economy-BOTTOM',state);assert.equal(await plan(),'RECEIVE_WAVE');}
  await page.selectOption('#role','SUPPORT');assert.match(await page.locator('#current-role').innerText(),/연결자/);
  await scene('side-connected');const championPlans=[];
  for(const [champion,word] of [['Caitlyn','덫'],['Fiora','응수'],['Ornn','지형']]){
   await page.selectOption('#champion',champion);championPlans.push(await plan());assert.match(await page.locator('#plan-steps').innerText(),new RegExp(word));
  }
  assert.equal(new Set(championPlans).size,3);
  await scene('objective-connected');const blue=await page.locator('#map [data-self="true"] circle').first().getAttribute('cx');
  const objective=await page.locator('#map [data-landmark="dragon"]').innerHTML();
  await page.selectOption('#side','RED');assert.notEqual(await page.locator('#map [data-self="true"] circle').first().getAttribute('cx'),blue);
  assert.equal(await page.locator('#map [data-landmark="dragon"]').innerHTML(),objective);
  await page.selectOption('#condition-enemy_visible','VISIBLE_EXAMPLE');assert.equal(await page.locator('#map [data-team="ENEMY"]').count(),1);
  await page.selectOption('#condition-enemy_visible','UNKNOWN');assert.equal(await page.locator('#map [data-team="ENEMY"]').count(),0);
  await page.locator('.optional-inputs summary').click();
  for(const [key,value] of [['total_earned_difference','-400'],['purchased_value_difference','900'],['current_gold','700']]){
   await page.fill('#metric-'+key,value);await page.locator('#metric-'+key).dispatchEvent('change');
  }
  await page.locator('.economy-summary summary').click();
  assert.match(await page.locator('[data-metric="total_earned_difference"]').innerText(),/-400/);
  assert.match(await page.locator('[data-metric="purchased_value_difference"]').innerText(),/900/);
  assert.match(await page.locator('[data-metric="current_gold"]').innerText(),/700/);
  await page.locator('#evidence > summary').click();assert.match(await page.locator('#evidence').innerText(),/16.20.1/);
  assert.match(await page.locator('#statistics-status').innerText(),/없음/);assert.match(await page.locator('#expert-status').innerText(),/없음/);
  await capture('red-objective-unknown-enemy.png');
  await page.goto(process.env.DIRECTION_PC_URL+'/pc');assert(await page.locator('#pc-auth').isVisible());
  await page.locator('a[href="/directions"]').click();await page.waitForSelector('#result:visible');
  // The same exported code must work at a repository subpath, as GitHub Pages does.
  await page.setViewportSize({width:390,height:844});
  await page.goto(process.env.DIRECTION_WEB_URL+'/lol-coach/directions.html');await page.waitForSelector('#result:visible');
  assert.equal(await page.locator('#manual-settings').getAttribute('open'),null);
  assert.equal(await page.locator('#map').getAttribute('data-active-step'),'1');
  for(const id of scenes){await scene(id);await sceneSkills(id);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));}
  await page.locator('#plan-steps [data-step="2"] button').click();
  assert.deepEqual(await displayedArrows('#map'),['2']);
  await page.locator('#map-step-ALL').click();assert.deepEqual(await displayedArrows('#map'),['1','2','3']);
  await page.locator('#map-step-1').click();
  await page.screenshot({path:process.env.DIRECTION_OUTPUT+'/mobile-390.png',fullPage:true});
  await page.locator('#map-zoom').click();await page.waitForSelector('#map-dialog[open]');
  await page.locator('#zoom-step-3').click();
  assert.equal(await page.locator('#map').getAttribute('data-active-step'),'3');
  assert.equal(await page.locator('#map-detail').getAttribute('data-active-step'),'3');
  assert.deepEqual(await displayedArrows('#map-detail'),['3']);
  assert.equal(await page.locator('#plan-steps [data-step="3"] button').getAttribute('aria-pressed'),'true');
  await page.locator('#zoom-range').fill('200');await page.locator('#zoom-range').dispatchEvent('input');
  assert(await page.locator('#map-zoom-stage').evaluate(e=>e.scrollWidth>e.clientWidth));
  await page.screenshot({path:process.env.DIRECTION_OUTPUT+'/mobile-zoom-200.png'});
  await page.locator('#map-close').click();assert(await page.locator('#map-zoom').evaluate(e=>document.activeElement===e));
  await page.goto(process.env.DIRECTION_WEB_URL+'/lol-coach/status.html');await page.waitForSelector('#status-items section');
  assert.match(await page.locator('#status-time').innerText(),/KST/);assert.match(await page.locator('#status-items').innerText(),/実行|실행/);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  assert.equal(errors.length,0,JSON.stringify(errors));assert.equal(bad.length,0,JSON.stringify(bad));
  process.stdout.write(JSON.stringify({passed:true,scenes:snapshots,checks:['same-economy condition counterfactual','economy state reuse','champion unique methods','support role distinction','unknown economy/enemy/wave','RED anchors and fixed objective','numbered steps/maps','card-main-zoom visible step synchronization','separate gold metrics','source levels','PC link and retained login','public repository-subpath export','mobile390/no overflow','200percent zoom and keyboard focus','dated status snapshot','local GET-only requests'],browser_errors:errors,http_errors:bad,request_count:requests.length,provider_requests:0,live_game_connection:false,windows_lcu:'BLOCKED_EXTERNAL',coaching_accuracy:null})+'\n');
 }finally{await browser.close();}
})().catch(e=>{process.stderr.write(String(e.stack||e));process.exitCode=1;});
'''


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass


def main():
    if not affected():print(json.dumps(dict(status='UNCHANGED_DIRECTIONS_BROWSER_REUSED')));return 0
    from scripts.launch_pc import create_server
    from scripts.build_directions_web import build
    out=ROOT/'evidence/actual-evidence/directions'/('browser-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix='directions-browser-') as temp:
        p=Path(temp);build(p/'public'/'lol-coach');pc=create_server(p/'private',port=0)
        public=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(p/'public')))
        try:
            for server in (pc,public):threading.Thread(target=server.serve_forever,daemon=True).start()
            (p/'probe.cjs').write_text(JS)
            env=dict(os.environ,NODE_PATH=os.environ.get('NODE_PATH','/opt/codex/cua_node/lib/node_modules'),DIRECTION_PC_URL='http://127.0.0.1:'+str(pc.server_port),DIRECTION_WEB_URL='http://127.0.0.1:'+str(public.server_port),DIRECTION_OUTPUT=str(out))
            if 'CHROMIUM_EXECUTABLE' not in env and Path('/usr/bin/chromium').exists():env['CHROMIUM_EXECUTABLE']='/usr/bin/chromium'
            r=subprocess.run(['node',str(p/'probe.cjs')],cwd=ROOT,env=env,text=True,capture_output=True,timeout=120)
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

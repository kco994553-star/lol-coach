"""Learning-room Chromium QA on the PC host and exported repository subpath.

run(env,out) uses the existing LOADING_PC/LOADING_WEB harness contract. All requests
are constrained to its loopback origins; video links are inspected without fetching.
"""
import argparse
from datetime import datetime, timezone
import functools
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
ROOT = Path(__file__).resolve().parents[1]
JS = r'''
const assert=require('node:assert/strict'),fs=require('node:fs'),{chromium}=require('playwright');
(async()=>{
const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_EXECUTABLE?{executablePath:process.env.CHROMIUM_EXECUTABLE}:{}),args:['--no-sandbox']});
const result={passed:false,checks:[],screenshots:[],browser_errors:[],http_errors:[],external_requests:[],provider_requests:0,new_visual_review_n:0,actual_user_approvals_created:0,synthetic_segment_checks:0};
const origins=[process.env.LOADING_PC,process.env.LOADING_WEB],check=n=>result.checks.push(n);
async function page(width=1440,height=1000){const context=await browser.newContext({viewport:{width,height},reducedMotion:'reduce'}),p=await context.newPage();p.setDefaultTimeout(12000);p.on('pageerror',e=>result.browser_errors.push(e.message));p.on('response',r=>{if(r.status()>=400&&!p.expectedFailure)result.http_errors.push({url:r.url(),status:r.status()});});await context.route('**/*',route=>{const u=route.request().url();if(origins.some(o=>u.startsWith(o+'/')))return route.continue();result.external_requests.push(u);return route.abort();});return p;}
async function ready(p){await p.locator('body[data-learning-ready="true"]').waitFor();}
async function overflow(p,label){const geometry=await p.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));assert(geometry.scroll<=geometry.width+1,label+' overflow '+JSON.stringify(geometry));const skip=await p.locator('.skip-link').first().evaluate(n=>({bottom:n.getBoundingClientRect().bottom,focused:document.activeElement===n}));assert(skip.focused||skip.bottom<=0,label+' inactive skip link must stay above viewport');check(label+' no horizontal overflow');}
async function capture(p,name){await p.evaluate(()=>scrollTo(0,0));await p.screenshot({path:process.env.LEARNING_OUT+'/'+name+'.png'});result.screenshots.push(name+'.png');}
try{
 for(const [mode,base,prefix] of [['pc',process.env.LOADING_PC,''],['public',process.env.LOADING_WEB,'/lol-coach']]){
  const p=await page(),url=base+prefix+'/learning.html';await p.goto(url);await ready(p);
  assert.equal(await p.locator('#coach-nav a[data-page]').count(),6);assert.match(await p.locator('#coach-nav a[aria-current]').innerText(),/학습실/);
  const all=await p.locator('.lesson-card').count();assert.equal(all,29);assert.equal(await p.locator('.candidate-card').count(),8);assert.equal(await p.locator('.lesson-card').first().locator('.lesson-fields dt').count(),11);
  assert.equal(await p.locator('#learning-group option').count(),5);assert.equal(await p.locator('#learning-topic option').count(),21);assert.equal(await p.locator('#learning-leaf option').count(),82);
  assert.match(await p.locator('#learning-status').innerText(),/80개는 분류 수/);check(mode+' six menus, real 29 claims/8 link-only candidates, 80 taxonomy independent of content, eleven fields');
  await p.locator('#learning-group').selectOption('topic:1');assert.equal(await p.locator('#learning-topic option').count(),6);assert.equal(await p.locator('#learning-leaf option').count(),22);
  await p.locator('#learning-topic').selectOption('topic:1.1');assert.equal(await p.locator('#learning-leaf option').count(),6);await p.locator('#learning-leaf').selectOption('topic:1.1.1');assert(await p.locator('.lesson-card').count()>0);assert(p.url().includes('#learn='));assert(p.url().includes('topic%3A1.1.1'));
  const filtered=await p.locator('#lesson-grid').innerText();await p.reload();await ready(p);assert.equal(await p.locator('#lesson-grid').innerText(),filtered);await p.locator('#reset-learning').click();assert.equal(await p.locator('.lesson-card').count(),all);await p.goBack();assert.equal(await p.locator('#learning-leaf').inputValue(),'topic:1.1.1');check(mode+' 4→20→80 hierarchy URL, refresh and Back roundtrip');
  await p.locator('#reset-learning').click();await p.locator('#learning-search').fill('케이틀린');assert(await p.locator('.lesson-card').count()>0);assert(await p.locator('.lesson-card').count()<all);await p.locator('#learning-search').fill('missing-learning-zzzz');assert(await p.locator('#learning-empty').isVisible());await p.locator('#clear-empty').click();assert.equal(await p.locator('.lesson-card').count(),all);
  await p.locator('#learning-role').selectOption('BOTTOM');assert(await p.locator('.lesson-card').count()>0);await p.locator('#learning-opponent').selectOption('Kaisa');assert(await p.locator('.lesson-card').count()>0);await p.locator('#learning-patch_state').selectOption('MISMATCH');assert(await p.locator('#learning-empty').isVisible());await p.locator('#learning-patch_state').selectOption('UNKNOWN');assert.equal(await p.locator('.lesson-card').count(),3,'unknown patch is a distinct existing state, not mismatch');await p.locator('#learning-patch_state').selectOption('');check(mode+' title, name, role, opponent and honest patch filters; empty/reset');
  await p.locator('#reset-learning').click();await p.locator('#learning-search').fill('조건 케이틀린');assert(await p.locator('.lesson-card').count()>0);await p.locator('#reset-learning').click();await p.locator('#learning-patch').selectOption('12.1 / Season 12');assert(await p.locator('.lesson-card').count()>0);assert(p.url().includes('Season'));await p.reload();await ready(p);assert.equal(await p.locator('#learning-patch').inputValue(),'12.1 / Season 12');await p.locator('#reset-learning').click();await p.locator('#learning-evidence').selectOption('LINK_ONLY');assert.equal(await p.locator('.lesson-card').count(),0);assert.equal(await p.locator('.candidate-card').count(),8);assert.match(await p.locator('.candidate-card').first().innerText(),/学習|학습 본문 없음/);assert.equal(await p.locator('.candidate-card a[href*="t="]').count(),0);check(mode+' link-only candidates unavailable, no invented lesson or timestamp');
  await p.locator('#reset-learning').click();const first=p.locator('.lesson-card').first();await first.locator('.lesson-evidence > summary').click();assert.match(await first.innerText(),/자막 발언: 미확보/);assert.match(await first.innerText(),/장면: 미검증/);assert.match(await first.innerText(),/SHA-256/);assert.match(await first.innerText(),/전술 승인|사용자 승인/);
  await first.locator('.lesson-fields button').click();assert(await first.locator('.lesson-practice').getAttribute('open')!==null);await first.locator('textarea').fill('조건 하나를 바꿔 다시 확인한다.');await first.locator('.lesson-practice button').click();assert.match(await first.locator('.lesson-practice').innerText(),/자동 채점·정답 생성 없음/);assert.equal(await first.locator('textarea').inputValue(),'조건 하나를 바꿔 다시 확인한다.');check(mode+' registry refs, unknown fields, source/hash/patch boundaries and condition-change reflection without grading');
  await overflow(p,mode+' desktop');await p.goto(url+'#learn=leaf=topic%3A1.1.1');await ready(p);await capture(p,mode+'-desktop');
  const contextLink=await p.evaluate(()=>window.LearningRoom.createLearningURL({champion:'Caitlyn',role:'BOTTOM',opponent:'Kaisa',claim:'A-WAVE'},{storage:sessionStorage,returnURL:location.pathname.replace('learning.html','loading.html')+'#plan=private-sensitive-state'}));assert(!contextLink.includes('private-sensitive-state'));await p.goto(new URL(contextLink,url).href);await ready(p);assert.match(await p.locator('#learning-context').innerText(),/A-WAVE/);assert((await p.locator('#return-gameplan').getAttribute('href')).endsWith('#plan=private-sensitive-state'));const share=p.url(),fresh=await page();await fresh.goto(share);await ready(fresh);assert(await fresh.locator('#return-gameplan').isHidden());await fresh.close();check(mode+' public bounded context and session-only opaque private return, independent session cannot restore');
  await p.goto(url+'#learn=group=evil&claim=private-match&role=FAKE&redirect=javascript%3Aalert(1)');await ready(p);await p.waitForFunction(()=>!location.href.includes('private-match'));assert(!p.url().includes('private-match'));assert.equal(await p.locator('#learning-role').inputValue(),'');assert.equal(await p.locator('.lesson-card').count(),0);check(mode+' malformed private claim discarded; safe unknown taxonomy returns empty');
  await p.goto(url+'#learn=champion=caitlyn');await p.waitForFunction(()=>document.querySelector('#learning-champion').value==='Caitlyn');assert.equal(await p.locator('.lesson-card').count(),8);await p.goto(url+'#learn=patch=DECLARED_UNVERIFIED');await p.waitForFunction(()=>document.querySelector('#learning-patch').value==='DECLARED_UNVERIFIED');assert.equal(await p.locator('.lesson-card').count(),0);check(mode+' lowercase URL identity canonicalized and unknown literal sourcepatch returns empty');
  for(const invalidContext of [{role:'FAKE'},{champion:'../../x'},{claim:'unknown'}]){const invalidLink=await p.evaluate(context=>window.LearningRoom.createLearningURL(context,{storage:sessionStorage,returnURL:location.pathname.replace('learning.html','loading.html')+'#plan=private-sensitive-state'}),invalidContext);await p.goto(new URL(invalidLink,url).href);await p.locator('#learning-invalid').waitFor({state:'visible'});await p.waitForFunction(()=>location.hash.includes('invalid=context'));assert.equal(await p.locator('.lesson-card,.candidate-card').count(),0);assert.match(await p.locator('#learning-status').innerText(),/연결 조건 오류/);assert((await p.locator('#return-gameplan').getAttribute('href')).endsWith('#plan=private-sensitive-state'));assert(!p.url().includes('private-sensitive-state'));await p.reload();await ready(p);assert(await p.locator('#learning-invalid').isVisible());assert.equal(await p.locator('.lesson-card,.candidate-card').count(),0);}
  await p.locator('#reset-learning').click();assert(await p.locator('#learning-invalid').isHidden());assert.equal(await p.locator('.lesson-card').count(),29);assert.equal(await p.locator('.candidate-card').count(),8);assert(await p.locator('#return-gameplan').isVisible());check(mode+' invalid role/champion/claim fail closed across serialization and refresh; reset restores all with session return');await p.close();
 }
 for(const [label,width,height,font] of [['tablet',768,1024,100],['mobile390',390,844,100],['mobile320',320,780,100],['desktop200',720,900,100],['mobile320-text200',320,780,200]]){const p=await page(width,height);await p.goto(process.env.LOADING_WEB+'/lol-coach/learning.html#learn=leaf=topic%3A1.1.1');await ready(p);if(font===200)await p.evaluate(()=>document.documentElement.style.fontSize='200%');await overflow(p,label);await capture(p,label);await p.keyboard.press('Tab');await p.keyboard.press('Tab');assert(await p.evaluate(()=>!!document.activeElement&&document.activeElement!==document.body));check(label+' keyboard focus');await p.close();}
 // Delayed/error fixtures affect only the local JSON response, never a provider.
 const failure=await page();failure.expectedFailure=true;let fail=true;await failure.route('**/learning-room.json',async route=>{if(fail)return route.fulfill({status:503,contentType:'application/json',body:'{}'});return route.continue();});await failure.goto(process.env.LOADING_WEB+'/lol-coach/learning.html');await failure.locator('#learning-error').waitFor({state:'visible'});assert.match(await failure.locator('#learning-status').innerText(),/오류/);fail=false;await failure.locator('#retry-learning').click();await ready(failure);check('source error/retry recovers actual JSON');await failure.close();
 const delayed=await page();let release;const gate=new Promise(resolve=>release=resolve);await delayed.route('**/learning-room.json',async route=>{await gate;await route.continue();});await delayed.goto(process.env.LOADING_WEB+'/lol-coach/learning.html',{waitUntil:'domcontentloaded'});assert.match(await delayed.locator('#learning-status').innerText(),/불러오고/);assert.equal(await delayed.locator('#learning-results').getAttribute('aria-busy'),'true');release();await ready(delayed);check('delayed source explicit loading state');await delayed.close();
 // Timestamp behavior uses an explicitly synthetic segment; actual acquisition N remains zero.
 const synthetic=await page();await synthetic.route('**/learning-room.json',async route=>{const response=await route.fetch(),data=await response.json();data.videos.push({video_id:'abcdefghijk',canonical_url:'https://www.youtube.com/watch?v=abcdefghijk'});data.segments.push({segment_id:'synthetic-segment',video_id:'abcdefghijk',video_start_ms:32000,video_end_ms:45000,timestamp_state:'VALIDATED',access_state:'PERMITTED',license_or_access_state:'PERMITTED',evidence_kind:'TRANSCRIPT',transcript_cue_ids:['synthetic-cue'],source_hash:'a'.repeat(64),game_clock_ms:null,scene_verified:false,viewer_perspective:'UNKNOWN'});data.lessons[0].segment_ids=['synthetic-segment'];return route.fulfill({json:data});});await synthetic.goto(process.env.LOADING_WEB+'/lol-coach/learning.html');await ready(synthetic);await synthetic.locator('.lesson-evidence > summary').first().click();const segment=synthetic.locator('a').filter({hasText:'검증된 영상 구간 열기'});assert.equal(await segment.count(),1);assert.equal(new URL(await segment.getAttribute('href')).searchParams.get('t'),'32s');assert.match(await synthetic.locator('.lesson-card').first().innerText(),/게임 내 시각: 미확인/);assert.match(await synthetic.locator('.lesson-card').first().innerText(),/자막 발언: 권한 확인된 구간 참조/);assert.match(await synthetic.locator('.lesson-card').first().innerText(),/육안 장면: 미검증/);result.synthetic_segment_checks=1;check('synthetic validated video timestamp stays separate from unknown game clock, no media fetched');await synthetic.close();
 assert.deepEqual(result.browser_errors,[]);assert.deepEqual(result.http_errors,[]);assert.deepEqual(result.external_requests,[]);result.passed=true;
}finally{fs.writeFileSync(process.env.LEARNING_OUT+'/learning-browser.json',JSON.stringify(result,null,2));await browser.close();}
console.log(JSON.stringify(result));
})().catch(e=>{console.error(e.stack||e);process.exitCode=1;});
'''

def run(env, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    probe = out / 'learning.cjs'
    probe.write_text(JS)
    browser_env = dict(env, LEARNING_OUT=str(out))
    completed = subprocess.run(['node',str(probe)],cwd=ROOT,env=browser_env,text=True,capture_output=True,timeout=180)
    (out/'learning.log').write_text(completed.stdout+completed.stderr)
    if completed.returncode:
        raise AssertionError(completed.stderr[-6000:])
    result = json.loads((out/'learning-browser.json').read_text())
    assert result['passed']
    return result

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):
        pass
    def copyfile(self, source, outputfile):
        try:
            super().copyfile(source, outputfile)
        except (BrokenPipeError, ConnectionResetError):
            pass

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    sys.path.insert(0,str(ROOT))
    from scripts.build_directions_web import build
    from scripts.launch_pc import create_server
    output=(args.output or ROOT/'evidence/actual-evidence/learning-room'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')).resolve()
    output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='learning-browser-') as temporary:
        temp=Path(temporary);build(temp/'public/lol-coach');pc=create_server(temp/'private',port=0)
        public=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(temp/'public')))
        try:
            for server in (pc,public):
                threading.Thread(target=server.serve_forever,daemon=True).start()
            env=dict(os.environ,LOADING_PC='http://127.0.0.1:'+str(pc.server_port),LOADING_WEB='http://127.0.0.1:'+str(public.server_port),NODE_PATH=os.environ.get('NODE_PATH','/opt/codex/cua_node/lib/node_modules'))
            if 'CHROMIUM_EXECUTABLE' not in env and Path('/usr/bin/chromium').exists():
                env['CHROMIUM_EXECUTABLE']='/usr/bin/chromium'
            result=run(env,output)
            result['source_sha256']={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('web_r4/learning.html','web_r4/learning.css','web_r4/learning-engine.js','web_r4/learning.js','web_r4/learning-room.json','web_r4/loading-knowledge.json')}
            result['actual_user_approvals_created']=len(pc.research.list())
            (output/'learning-browser.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
            print(json.dumps({'passed':result['passed'],'output':str(output),'checks':len(result['checks'])}))
            return 0
        finally:
            for server in (pc,public):
                server.shutdown();server.server_close()

if __name__=='__main__':
    raise SystemExit(main())

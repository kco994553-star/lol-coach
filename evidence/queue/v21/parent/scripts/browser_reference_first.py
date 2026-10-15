"""Browser -> real API -> verified archive, without any knowledge approval."""
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import threading
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
BROWSER=r'''
const {chromium}=require('playwright'),fs=require('fs'),assert=require('node:assert/strict');
(async()=>{
 const token=fs.readFileSync(process.env.REFERENCE_TOKEN_FILE,'utf8');
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_EXECUTABLE,args:['--no-sandbox']});
 const page=await browser.newPage();page.setDefaultTimeout(8000);const errors=[];page.on('pageerror',e=>errors.push(String(e)));const checks=[];
 try{
  const base=process.env.REFERENCE_URL;
  await page.goto(base+'/review-queue');await page.fill('#rq-token',token);await page.click('#rq-connect');
  await page.waitForSelector('#rq-reference .official-fact');
  assert.equal(await page.locator('#rq-reference .official-fact').count(),15);checks.push('korean-official-facts-visible-without-approval');
  const auth={Authorization:'Bearer '+token};
  const focused=await(await page.request.get(base+'/dev/v1/pregame/review-queue',{headers:auth})).json();
  assert(focused.candidates.length<=5);assert.equal(focused.progress.reviewed,0);assert.equal(focused.progress.example_card_filled,0);
  assert((await page.locator('#rq-progress').textContent()).includes('선택 검토'));checks.push('five-optional-tactics-no-backlog-obligation');
  await page.check('#rq-show-archive');await page.waitForFunction(()=>document.querySelector('#rq-page-position').textContent.startsWith('1 / 2'));
  await page.click('#rq-page-next');await page.waitForFunction(()=>document.querySelector('#rq-page-position').textContent.startsWith('2 / 2'));checks.push('all-thirty-preserved-in-optional-archive');
  await page.uncheck('#rq-show-archive');await page.waitForFunction(()=>document.querySelector('#rq-page-position').textContent.startsWith('1 / 1'));
  for(const width of [390,1440]){
   await page.setViewportSize({width,height:900});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   await page.screenshot({path:process.env.REFERENCE_OUTPUT+'/review-'+width+'.png',fullPage:true});
  }
  checks.push('pc-and-mobile-reference-no-overflow');
  await page.goto(base+'/pregame');await page.waitForSelector('#pg-workspace:visible');await page.waitForLoadState('networkidle');
  await page.locator('#pg-input-list button').first().click();await page.waitForFunction(()=>!document.querySelector('#pg-create-plan').disabled);
  await page.click('#pg-create-plan');await page.waitForSelector('#pg-reference .official-fact');
  assert((await page.locator('#pg-reference').textContent()).includes('공식 자료'));
  assert.equal(await page.locator('#pg-cards > article').count(),9);checks.push('pregame-reference-available-with-zero-reviewed-knowledge');
  const facts=await(await page.request.post(base+'/dev/v1/pregame/official-facts',{headers:auth,data:{champions:['Caitlyn'],patch:'16.21'}})).json();
  assert.equal(facts.champions[0].patch_status,'GAME_PATCH_MISMATCH');assert.equal(facts.approval_required,false);checks.push('patch-mismatch-kept-separate');
  const knowledge=await(await page.request.get(base+'/dev/v1/pregame/knowledge',{headers:auth})).json();assert.equal(knowledge.length,0);checks.push('no-user-decisions-created');
  assert.equal(errors.length,0);checks.push('no-page-errors');
  process.stdout.write(JSON.stringify({passed:true,checks,actual_user_decisions:0,official_source_fact_count:65}));
 }finally{await browser.close();}
})().catch(e=>{process.stderr.write(String(e.stack||e));process.exitCode=1;});
'''


def main():
    from coach_v1.pregame_server import PregameWorkbench,current_knowledge
    from coach_v1.server import Limits
    from tests_pregame.test_contract import golden
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output=ROOT/'evidence/queue/reference-first'/('browser-'+stamp);output.mkdir(parents=True)
    with tempfile.TemporaryDirectory() as folder:
        private=Path(folder);token=secrets.token_hex(32);tokenfile=private/'token';tokenfile.write_text(token);tokenfile.chmod(0o600)
        script=private/'browser.cjs';script.write_text(BROWSER)
        server=PregameWorkbench(private/'work.sqlite',token,Limits(1_000_000,100,100,100,100,10))
        server.pregame.save(golden('BOTTOM',patch='16.20'),None,0,'example-pick-fixture')
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        env=dict(os.environ,REFERENCE_TOKEN_FILE=str(tokenfile),REFERENCE_URL=f'http://127.0.0.1:{server.server_port}',REFERENCE_OUTPUT=str(output),NODE_PATH=os.environ.get('NODE_PATH','/opt/codex/cua_node/lib/node_modules'),CHROMIUM_EXECUTABLE=os.environ.get('CHROMIUM_EXECUTABLE','/usr/bin/chromium'))
        try:
            result=subprocess.run(['node',str(script)],cwd=ROOT,env=env,capture_output=True,text=True,timeout=90)
            receipt=json.loads(result.stdout or '{}');receipt['actual_user_decisions']=sum(r['proposal']['review_state']!='EXPLORATORY' for r in current_knowledge(server.research))
            receipt['passed']=bool(receipt.get('passed')) and result.returncode==0 and receipt['actual_user_decisions']==0
            receipt['scope']='Example pick fixture; actual official source files; no approval clicks or GitHub writes'
            (output/'browser.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
            if result.stderr:(output/'browser.stderr').write_text(result.stderr)
            print(json.dumps(dict(passed=receipt['passed'],evidence_directory=str(output)),ensure_ascii=False))
            if not receipt['passed']:raise SystemExit(1)
        finally:server.shutdown();server.server_close();thread.join(timeout=5)


if __name__=='__main__':main()

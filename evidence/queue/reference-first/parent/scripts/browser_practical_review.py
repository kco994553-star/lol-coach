"""Actual 30-advice browser projection; GitHub reads use empty test pages.

No approval clicks, USER decisions, or GitHub writes. Separate actual remote
read receipt records the real user decision count.
"""
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import threading
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
BROWSER=r'''
const {chromium}=require('playwright'),fs=require('fs'),assert=require('node:assert/strict');
(async()=>{
 const token=fs.readFileSync(process.env.REVIEW_TOKEN_FILE,'utf8');
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_EXECUTABLE,args:['--no-sandbox']});
 const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(String(e)));
 try{
  const base=process.env.REVIEW_URL;
  await page.goto(base+'/review-queue');await page.fill('#rq-token',token);await page.click('#rq-connect');await page.waitForSelector('#rq-card:visible');
  const labels=['상황','할 것','하지 말 것','상대 권리','무효 조건','근거','패치'];
  for(const label of labels)assert((await page.locator('#rq-claim').textContent()).includes(label+':'));
  assert((await page.locator('#rq-priority').textContent()).includes('기존 후보 Q05-I-'));
  assert.equal(await page.locator('#rq-approve').isDisabled(),true);
  const auth={Authorization:'Bearer '+token};
  let queue=await(await page.request.get(base+'/dev/v1/pregame/review-queue',{headers:auth})).json();
  assert.equal(queue.progress.total,30);assert.equal(queue.progress.reviewed,0);assert.equal(queue.progress.example_card_filled,0);
  const response=page.waitForResponse(r=>r.url().endsWith('/review-queue/github-sync'));
  await page.click('#rq-github-sync');const synced=await response;assert.equal(synced.status(),200);assert.equal((await synced.json()).applied,0);
  await page.waitForFunction(()=>document.querySelector('#rq-notice').textContent.includes('사용자 결정 0개 반영'));
  const changed=page.waitForResponse(r=>r.url().endsWith('/review-queue/page'));
  await page.click('#rq-page-next');await changed;await page.waitForFunction(()=>document.querySelector('#rq-page-position').textContent.startsWith('2 / 2'));
  for(const width of [390,1440]){
   await page.setViewportSize({width,height:900});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   await page.screenshot({path:process.env.REVIEW_OUTPUT+'/practical-'+width+'.png',fullPage:true});
  }
  assert.equal(errors.length,0);
  process.stdout.write(JSON.stringify({passed:true,checks:['seven-korean-fields','original-id-link','no-automatic-approval','30-actual-catalog-rows','local-sync-route-empty-github-fixture','second-page','mobile-and-pc-no-overflow','no-page-errors'],actual_user_decisions:0}));
 }finally{await browser.close();}
})().catch(e=>{process.stderr.write(String(e.stack||e));process.exitCode=1;});
'''


def main():
    from coach_v1.pregame_server import PregameWorkbench,current_knowledge
    from coach_v1.server import Limits
    output=ROOT/'evidence/queue/practical-review-20261014'
    output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as folder:
        private=Path(folder);token=secrets.token_hex(32);tokenfile=private/'token';tokenfile.write_text(token);tokenfile.chmod(0o600)
        script=private/'browser.cjs';script.write_text(BROWSER)
        server=PregameWorkbench(private/'work.sqlite',token,Limits(1_000_000,100,100,100,100,10))
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        env=dict(os.environ,REVIEW_TOKEN_FILE=str(tokenfile),REVIEW_URL=f'http://127.0.0.1:{server.server_port}',REVIEW_OUTPUT=str(output),NODE_PATH=os.environ.get('NODE_PATH','/opt/codex/cua_node/lib/node_modules'),CHROMIUM_EXECUTABLE=os.environ.get('CHROMIUM_EXECUTABLE','/usr/bin/chromium'))
        try:
            # Preserve node subprocess execution; substitute only gh GET reads.
            original=subprocess.run
            def run(args,*a,**kw):
                if args[:4]==['gh','api','--method','GET']:return SimpleNamespace(stdout='[]')
                return original(args,*a,**kw)
            with patch('subprocess.run',run):
                result=subprocess.run(['node',str(script)],cwd=ROOT,env=env,capture_output=True,text=True,timeout=90)
            receipt=json.loads(result.stdout or '{}');receipt['actual_user_decisions']=sum(r['proposal']['review_state']!='EXPLORATORY' for r in current_knowledge(server.research))
            receipt['passed']=receipt.get('passed') and result.returncode==0 and receipt['actual_user_decisions']==0
            receipt['github_scope']='empty response fixture; actual remote read recorded separately'
            (output/'browser.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
            if result.stderr:(output/'browser.stderr').write_text(result.stderr)
            print(json.dumps(receipt,ensure_ascii=False))
            if not receipt['passed']:raise SystemExit(1)
        finally:server.shutdown();server.server_close();thread.join(timeout=5)


if __name__=='__main__':main()

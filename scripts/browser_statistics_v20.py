"""Isolated Chromium tier/progress verification; no provider calls or approvals."""
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
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))

BROWSER=r"""
'use strict';
const {chromium}=require(process.env.PLAYWRIGHT_MODULE),fs=require('fs'),path=require('path');
const out=process.env.STATS_EVIDENCE_DIR,checks=[],errors=[];
function check(id,passed){checks.push({id,passed:!!passed});if(!passed)throw Error(id);}
(async()=>{let browser;try{
 browser=await chromium.launch({executablePath:process.env.CHROMIUM_EXECUTABLE||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1280,height:900}});page.on('pageerror',e=>errors.push(e.message));
 await page.goto(process.env.WORKBENCH_URL+'/statistics');await page.locator('#stats-token').fill(fs.readFileSync(process.env.WORKBENCH_TOKEN_FILE,'utf8').trim());await page.locator('#stats-login button').click();await page.waitForSelector('#stats-body:not([hidden])');await page.waitForLoadState('networkidle');
 check('no-own-tier-or-comparison-selector',await page.locator('#stats-own,#stats-high').count()===0);
 await page.locator('#stats-role').selectOption('TOP');await page.locator('#stats-champion').selectOption('Champion');await page.waitForFunction(()=>document.querySelector('#stats-summary h2')?.textContent==='Champion · TOP · 16.19');
 fs.writeFileSync(path.join(out,'initial-state.json'),JSON.stringify(await page.evaluate(()=>({notice:document.querySelector('#stats-notice').textContent,summary:document.querySelector('#stats-summary')?.textContent,graphs:document.querySelector('#stats-graphs')?.textContent}))));
 await page.screenshot({path:path.join(out,'initial-state.png'),fullPage:true});
 check('three-resource-graphs',await page.locator('.stats-metric svg').count()===3);
 check('primary-and-insufficient-only-auxiliary-labeled',await page.locator('#stats-summary').innerText().then(t=>t.includes('CHALLENGER')&&t.includes('GRANDMASTER')&&t.includes('보조')));
 check('exact-primary-point-count',await page.locator('.stats-point[data-origin="PRIMARY"]').count()===6);
 check('only-inadequate-minutes-get-auxiliary',await page.locator('.stats-point[data-origin="AUXILIARY"]').count()===3);
 check('both-provenance-maps',await page.locator('#stats-primary-source').innerText().then(t=>t.includes('CHALLENGER'))&&await page.locator('#stats-auxiliary-source').innerText().then(t=>t.includes('GRANDMASTER')));
 check('remaining-is-honest-unknown',await page.locator('#stats-summary').innerText().then(t=>t.includes('UNKNOWN')));
 check('pc-graphs-side-by-side',await page.evaluate(()=>{const r=[...document.querySelectorAll('.stats-metric')].map(n=>n.getBoundingClientRect());return r.length===3&&r.every(n=>Math.abs(n.top-r[0].top)<2)&&r[1].left>r[0].left;}));
 let release,announce,holdNext=true;const held=new Promise(resolve=>announce=resolve);
 await page.route('**/pregame/challenger-reference',async route=>{if(!holdNext){await route.continue();return;}holdNext=false;await new Promise(resolve=>{release=resolve;announce();});await route.abort('failed');});
 await page.locator('#stats-role').selectOption('MID');await held;await page.locator('#stats-role').selectOption('TOP');await page.waitForFunction(()=>document.querySelectorAll('.stats-metric svg').length===3);release();await page.waitForLoadState('networkidle');
 check('stale-error-does-not-clear-current-reference',await page.locator('.stats-point[data-origin="PRIMARY"]').count()===6);await page.unroute('**/pregame/challenger-reference');
 await page.screenshot({path:path.join(out,'desktop.png'),fullPage:true});
 await page.setViewportSize({width:390,height:844});check('mobile-no-overflow',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:path.join(out,'mobile.png'),fullPage:true});
 await page.locator('#stats-role').selectOption('MID');await page.waitForFunction(()=>document.querySelector('#stats-summary h2')?.textContent==='Champion · MID · 16.19');check('unavailable-exact-cohort-unknown',await page.locator('#stats-summary').innerText().then(t=>t.includes('UNKNOWN')));
 await page.locator('#stats-logout').click();check('logout-clears-reference',await page.locator('#stats-body').isHidden()&&await page.locator('.stats-point').count()===0);check('no-browser-errors',errors.length===0);
 fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify({passed:true,checks,errors,coaching_accuracy:null}));
 }catch(e){fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify({passed:false,checks,errors,error:e.message}));process.exitCode=1;}finally{if(browser)await browser.close();}})();
"""

def main():
    from coach_v1.pregame_server import PregameWorkbench
    from coach_v1.server import Limits
    from coach_v1.power_stats import build_power_dataset
    from tests_pregame.test_power_stats import pair,source
    output=ROOT/'evidence/queue/v20'/('statistics-browser-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    output.mkdir(parents=True)
    names=['coach_v1/pregame_server.py','coach_v1/power_stats.py','coach_v1/collection_progress.py','coach_v1/challenger_reference.py','web_r4/statistics.html','web_r4/statistics.js','web_r4/statistics.css','scripts/browser_statistics_v20.py','tests_pregame/test_challenger_reference.py']
    hashes=lambda:{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names}
    before=hashes()
    with tempfile.TemporaryDirectory(prefix='stats-browser-v20-') as tmp:
        token=secrets.token_urlsafe(32);path=Path(tmp);tokenfile=path/'token';tokenfile.write_text(token);tokenfile.chmod(0o600)
        server=PregameWorkbench(path/'work.sqlite',token,Limits(1000000,1000,100,100,100,10));server.test_mode=True
        for tier in ['CHALLENGER','GRANDMASTER']:
            src=source();src['tier']=tier
            server.power_datasets[('16.19',tier)]=build_power_dataset([pair(i,100+i*10,minutes=(1,3) if tier=='CHALLENGER' and i<23 else (1,2,3)) for i in range(24)],source=src)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        playwright=subprocess.check_output(['node','-p','require.resolve("playwright")'],cwd=ROOT,text=True).strip()
        env=dict(os.environ,WORKBENCH_TOKEN_FILE=str(tokenfile),WORKBENCH_URL=f'http://127.0.0.1:{server.server_port}',STATS_EVIDENCE_DIR=str(output),PLAYWRIGHT_MODULE=playwright)
        browser_script=path/'statistics-check.cjs';browser_script.write_text(BROWSER)
        try:
            run=subprocess.run(['node',str(browser_script)],cwd=ROOT,env=env,capture_output=True,text=True,timeout=120)
            (output/'browser.log').write_text(run.stdout+run.stderr)
        finally:server.shutdown();thread.join();server.server_close()
    browser=json.loads((output/'browser.json').read_text()) if (output/'browser.json').exists() else dict(passed=False,error='NO_RECEIPT')
    receipt=dict(passed=run.returncode==0 and browser.get('passed') and before==hashes(),browser=browser,source_sha256=hashes(),sources_unchanged=before==hashes(),git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),github_binding={k:os.environ.get(k) for k in ('GITHUB_SHA','GITHUB_RUN_ID','GITHUB_REPOSITORY')},scope='SYNTHETIC only; no real matches/provider requests/user approvals',coaching_accuracy=None)
    (output/'runner.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(passed=receipt['passed'],evidence_directory=str(output))));return 0 if receipt['passed'] else 1
if __name__=='__main__':raise SystemExit(main())

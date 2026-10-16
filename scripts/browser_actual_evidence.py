"""Changed PC resource projection in actual Chromium; no client/skill-effect claim."""
from datetime import datetime,timezone
import hashlib,json,os
from pathlib import Path
import subprocess,sys,tempfile,threading
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.verify_actual_evidence import affected_browser_changed
JS=r'''
const fs=require('node:fs'),assert=require('node:assert/strict'),{chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_EXECUTABLE?{executablePath:process.env.CHROMIUM_EXECUTABLE}:{}),args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1600,height:1000}}),errors=[];let writes=0,latency=null;
 const token=fs.readFileSync(process.env.PC_TOKEN_FILE,'utf8').trim(),base=process.env.PC_URL,cohort=JSON.parse(process.env.RESOURCE_COHORT);
 page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{assert(!r.url().includes(token));if(r.method()!=='GET'&&!r.url().endsWith('/pc-preview'))writes++;});
 try{
  await page.goto(base+'/pc#token='+encodeURIComponent(token));await page.waitForSelector('#pc-workspace:visible');
  await page.selectOption('#pc-position',cohort?.position||'BOTTOM');await page.fill('#pc-patch',cohort?.patch||'16.20');
  await page.fill('#pc-own',cohort?.champion||'Caitlyn');
  const start=performance.now();await page.fill('#pc-laner',cohort?.opponent_champion||'Ezreal');
  const card=page.locator('[data-card-id="resource-observed-matchup"]');
  if(cohort){
   await card.waitFor({state:'attached'});latency=performance.now()-start;
   const more=page.locator('.more-cards');if(await more.count()&&!await more.getAttribute('open'))await more.locator('> summary').click();
   assert.match(await card.locator('.evidence').innerText(),/통계|미확인/);
   await card.locator('details > summary').click();const text=await card.innerText();
   assert.match(text,/10분 구간/);assert.match(text,/실제 관측 시각/);assert.match(text,/경험치/);assert.match(text,/유효/);assert.match(text,/누락/);assert.match(text,/정확히 10분/);assert.match(text,/보간하지 않습니다/);
   assert.equal(await card.locator('.objection').count(),0);
   await page.screenshot({path:process.env.PC_OUTPUT+'/observed-resource-1600.png',fullPage:true});
   await page.fill('#pc-patch','16.99');await page.waitForFunction(()=>!document.querySelector('[data-card-id="resource-observed-matchup"]'));
   await page.fill('#pc-patch',cohort.patch);await card.waitFor({state:'attached'});
  }else{await page.waitForTimeout(500);assert.equal(await card.count(),0);}
  assert.equal(await page.locator('#pc-own').isEnabled(),true);
  await page.uncheck('#pc-pregame');await page.waitForFunction(()=>!document.querySelector('[data-card-id="resource-observed-matchup"]'));
  assert.equal(errors.length,0);assert.equal(writes,0);
  process.stdout.write(JSON.stringify({passed:true,resource_report_available:!!cohort,resource_card_checked:!!cohort,input_to_card_ms:latency,under_one_second:latency===null?null:latency<1000,cases:['access token auto connection','manual pick fallback retained',...(cohort?['actual source-bound observed-time card','patch mismatch exclusion']:['missing dataset preserves existing UI']),'nonpregame suppression'],browser_errors:errors,unexpected_writes:writes,windows_lcu:'BLOCKED_EXTERNAL',coaching_accuracy:null})+'\n');
 }finally{await browser.close();}
})().catch(e=>{process.stderr.write(String(e.stack||e));process.exitCode=1;});
'''

def main():
    if not affected_browser_changed():
        print(json.dumps(dict(status='UNCHANGED_EVIDENCE_BROWSER_REUSED',coaching_accuracy=None)));return 0
    from scripts.launch_pc import create_server
    from coach_v1.resource_recovery import load_bound_report
    directory=ROOT/'data/resource_recovery/2026-10-16';cohort=None
    if (directory/'resources.json').exists():
        report,_=load_bound_report(directory)
        available=[c for c in report['cohorts'] if c['opponent_champion'] and c['position']!='UNKNOWN']
        cohort=next((c for c in available if c['champion']=='Caitlyn' and c['patch']=='16.20'),available[0] if available else None)
    out=ROOT/'evidence/actual-evidence'/('browser-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix='evidence-browser-') as temp:
        p=Path(temp);server=create_server(p,port=0)
        try:
            threading.Thread(target=server.serve_forever,daemon=True).start();(p/'probe.cjs').write_text(JS)
            env=dict(os.environ,NODE_PATH=os.environ.get('NODE_PATH','/opt/codex/cua_node/lib/node_modules'),PC_URL='http://127.0.0.1:'+str(server.server_port),PC_TOKEN_FILE=str(p/'access-token'),PC_OUTPUT=str(out),RESOURCE_COHORT=json.dumps(cohort))
            if 'CHROMIUM_EXECUTABLE' not in env and Path('/usr/bin/chromium').exists():env['CHROMIUM_EXECUTABLE']='/usr/bin/chromium'
            result=subprocess.run(['node',str(p/'probe.cjs')],cwd=ROOT,env=env,text=True,capture_output=True,timeout=120)
            (out/'browser.log').write_text((result.stdout+result.stderr).replace(server.token,'[REDACTED]'))
            receipt=json.loads(result.stdout or '{}');receipt['passed']=bool(receipt.get('passed')) and result.returncode==0
            receipt['user_decisions_created']=len(server.research.list())
            receipt['source_sha256']={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('coach_v1/pc_coach.py','coach_v1/resource_view.py','scripts/browser_actual_evidence.py')}
            (out/'runner.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
            print(json.dumps(dict(passed=receipt['passed'],evidence_directory=str(out))))
            if not receipt['passed']:print(result.stderr.replace(server.token,'[REDACTED]'),file=sys.stderr)
            return 0 if receipt['passed'] else 1
        finally:server.shutdown();server.server_close()

if __name__=='__main__':raise SystemExit(main())

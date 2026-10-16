"""Real browser for changed revision/topic flow only; no provider or USER write."""
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.verify_quality_pilot import affected_code_changed

JS=r'''
const fs=require('node:fs'),assert=require('node:assert/strict'),{chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_EXECUTABLE?{executablePath:process.env.CHROMIUM_EXECUTABLE}:{}),args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1600,height:1000}}),errors=[];let writes=0;
 const token=fs.readFileSync(process.env.PC_TOKEN_FILE,'utf8').trim(),base=process.env.PC_URL;
 page.on('pageerror',e=>errors.push(e.message));
 page.on('request',r=>{assert(!r.url().includes(token));if(r.method()!=='GET'&&!r.url().endsWith('/pc-preview'))writes++;});
 try{
  await page.goto(base+'/pc#token='+encodeURIComponent(token));await page.waitForSelector('#pc-workspace:visible');
  await page.selectOption('#pc-position','BOTTOM');await page.fill('#pc-patch','16.20');await page.fill('#pc-own','Caitlyn');
  await page.fill('#pc-laner','Ezreal');await page.locator('#pc-composition > summary').click();
  await page.fill('#pc-team-ENEMY-SUPPORT','Nautilus');
  const revision=page.locator('[data-card-id="QP-20261016-KR-008-v2"]');await revision.waitFor({state:'attached'});
  const more=page.locator('.more-cards');if(await more.count() && !await more.getAttribute('open'))await more.locator('> summary').click();
  assert.match(await revision.locator('.topic').innerText(),/스킬 상호작용/);
  assert.match(await revision.locator('.evidence').innerText(),/미검토 가설/);
  assert.equal(await revision.locator('.objection').count(),0);
  assert.equal(await page.locator('[data-card-id="advice-KR-008"]').count(),0);
  assert.equal(await page.locator('[data-card-id="advice-KR-009"]').count(),1);
  await revision.locator('details > summary').click();
  const detail=await revision.innerText();assert.match(detail,/선택 조건\(모두\)/);assert.match(detail,/중단 조건\(하나라도\)/);assert.match(detail,/불확실할 때/);assert.match(detail,/긴급 방어/);
  assert.match(detail,/기존 자동 검토나 사용자 승인을 승계하지 않습니다/);
  await page.screenshot({path:process.env.PC_OUTPUT+'/revised-caitlyn-1600.png',fullPage:true});
  await page.fill('#pc-own','Ashe');await page.fill('#pc-jungler','LeeSin');
  const scout=page.locator('[data-card-id="QP-20261016-KR-026-v2"]');await scout.waitFor({state:'attached'});
  assert.equal(await page.locator('[data-card-id="advice-KR-026"]').count(),0);
  await page.uncheck('#pc-pregame');await page.waitForFunction(()=>!document.querySelector('[data-card-id^="QP-"]'));
  assert.equal(await page.locator('.evidence.AUTO_VERIFIED').count(),0);
  assert.equal(errors.length,0);assert.equal(writes,0);
  process.stdout.write(JSON.stringify({passed:true,cases:['Caitlyn revision and independent topic','unchanged legacy advice preserved','Ashe scout alternatives','nonpregame suppression'],browser_errors:errors,unexpected_writes:writes,scope:'Synthetic manual picks and actual local HTTP/browser; no real gameplay-effect validation'})+'\n');
 }finally{await browser.close();}
})().catch(e=>{process.stderr.write(String(e.stack||e));process.exitCode=1;});
'''


def main():
    if not affected_code_changed():
        print(json.dumps(dict(status='UNCHANGED_PILOT_BROWSER_EVIDENCE_REUSED',coaching_accuracy=None)));return 0
    from scripts.launch_pc import create_server
    out=ROOT/'evidence/quality-pilot'/('browser-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix='quality-browser-') as temp:
        p=Path(temp);server=create_server(p,port=0)
        try:
            threading.Thread(target=server.serve_forever,daemon=True).start();(p/'probe.cjs').write_text(JS)
            env=dict(os.environ,NODE_PATH=os.environ.get('NODE_PATH','/opt/codex/cua_node/lib/node_modules'),PC_URL='http://127.0.0.1:'+str(server.server_port),PC_TOKEN_FILE=str(p/'access-token'),PC_OUTPUT=str(out))
            if 'CHROMIUM_EXECUTABLE' not in env and Path('/usr/bin/chromium').exists():env['CHROMIUM_EXECUTABLE']='/usr/bin/chromium'
            result=subprocess.run(['node',str(p/'probe.cjs')],cwd=ROOT,env=env,text=True,capture_output=True,timeout=120)
            (out/'browser.log').write_text((result.stdout+result.stderr).replace(server.token,'[REDACTED]'))
            receipt=json.loads(result.stdout or '{}');receipt['passed']=bool(receipt.get('passed')) and result.returncode==0
            receipt['user_decisions_created']=len(server.research.list());receipt['coaching_accuracy']=None
            receipt['source_sha256']={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('coach_v1/pilot_advice.py','coach_v1/pc_coach.py','web_r4/pc.js','knowledge_candidates/coaching-quality-pilot.json','scripts/browser_quality_pilot.py')}
            (out/'runner.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
            print(json.dumps(dict(passed=receipt['passed'],evidence_directory=str(out))))
            if not receipt['passed']:print(result.stderr.replace(server.token,'[REDACTED]'),file=sys.stderr)
            return 0 if receipt['passed'] else 1
        finally:server.shutdown();server.server_close()


if __name__=='__main__':raise SystemExit(main())

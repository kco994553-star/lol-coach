"""Changed manual item workflow only; fixtures never certify a real game client."""
import functools,json,os,subprocess,tempfile,threading,hashlib,sys
from pathlib import Path
from datetime import datetime,timezone
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
SOURCES=['web_r4/'+x for x in ['game-info.html','game-info.js','game-info-engine.js','game-info.css','game-info-items.json']]+['coach_v1/game_info.py','scripts/browser_game_info.py','scripts/build_game_info_catalog.py','scripts/build_directions_web.py']
def affected():
 p=os.environ.get('GITHUB_EVENT_PATH')
 if not p:return True
 e=json.loads(Path(p).read_text());base=e.get('pull_request',{}).get('base',{}).get('sha')or e.get('before')
 if not base or set(base)=={'0'}:return True
 return bool(set(subprocess.check_output(['git','diff','--name-only',base,'HEAD'],cwd=ROOT,text=True).splitlines())&set(SOURCES))
JS=r'''const fs=require('fs'),assert=require('assert/strict'),{chromium}=require('playwright');(async()=>{const b=await chromium.launch({executablePath:process.env.CHROMIUM_EXECUTABLE||'/usr/bin/chromium',args:['--no-sandbox']}),p=await b.newPage({reducedMotion:'reduce'}),errors=[],requests=[];p.on('pageerror',e=>errors.push(e.message));p.on('request',r=>requests.push(r.url()));const records=[];for(const [device,width,height]of[['desktop',1440,1000],['mobile',390,844]]){await p.setViewportSize({width,height});const response=await p.goto(process.env.INFO_WEB+'/lol-coach/game-info.html');assert.equal(response.status(),200,'manual comparison page missing');await p.waitForSelector('#compare-items:enabled');assert.equal(await p.locator('#local-game-read').isDisabled(),true);await p.locator('#item-example').click();await p.locator('#compare-items').click();assert.match(await p.locator('#comparison-result').innerText(),/100/);assert.match(await p.locator('#cash-value').innerText(),/미확인/);assert.match(await p.locator('#earned-value').innerText(),/미확인/);assert(!/승률|확정 승리/.test(await p.locator('#comparison-result').innerText()));await p.locator('#item-patch').fill('16.19');await p.locator('#compare-items').click();assert.match(await p.locator('#comparison-result').innerText(),/미확인/);await p.locator('#item-patch').fill('16.20');await p.locator('#ours-0').fill('999999');await p.locator('#compare-items').click();assert.match(await p.locator('#comparison-result').innerText(),/미확인/);await p.locator('#item-example').click();await p.locator('#compare-items').focus();await p.keyboard.press('Enter');assert.match(await p.locator('#comparison-result').innerText(),/100/);assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await p.screenshot({path:process.env.INFO_OUT+'/'+device+'.png',fullPage:true});records.push({device,result:await p.locator('#comparison-result').innerText(),timers:await p.locator('#timer-capabilities').innerText()});}assert.equal(errors.length,0,errors.join('\n'));assert(!requests.some(x=>x.includes('/dev/')||x.includes(':2999')||x.includes('api.riotgames')));fs.writeFileSync(process.env.INFO_OUT+'/result.json',JSON.stringify({passed:true,records,external_provider_requests:0,real_client_verified:false},null,2));await b.close();})().catch(e=>{console.error(e);process.exit(1)});'''
def main():
 if not affected():print('UNCHANGED_GAME_INFO_BROWSER_REUSED');return 0
 from scripts.build_directions_web import build
 out=ROOT/'evidence/actual-evidence/game-info'/('browser-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir(parents=True)
 class Quiet(SimpleHTTPRequestHandler):
  def log_message(self,*a):pass
 with tempfile.TemporaryDirectory()as t:
  build(Path(t)/'lol-coach');server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=t));threading.Thread(target=server.serve_forever,daemon=True).start();script=Path(t)/'probe.cjs';script.write_text(JS)
  try:
   env={**os.environ,'NODE_PATH':os.environ.get('NODE_PATH','/opt/codex/cua_node/lib/node_modules'),'INFO_WEB':'http://127.0.0.1:'+str(server.server_port),'INFO_OUT':str(out)};r=subprocess.run(['node',str(script)],env=env,capture_output=True,text=True,timeout=90);(out/'browser.log').write_text(r.stdout+r.stderr);result=json.loads((out/'result.json').read_text())if(out/'result.json').exists()else{'passed':False};result['passed']=r.returncode==0 and result['passed'];result['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in SOURCES if(ROOT/p).exists()};(out/'runner.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'evidence_directory':str(out)}));print(r.stderr[-1600:]if r.returncode else'');return 0 if result['passed']else 1
  finally:server.shutdown();server.server_close()
if __name__=='__main__':raise SystemExit(main())

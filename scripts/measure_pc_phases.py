"""Offline, isolated PC timing observations; never an acceptance or accuracy test.

Each repeat starts a fresh Python server and Chromium context with the same local
archives and picks. The server uses the launcher's create_server and local data
loaders, but deliberately does not start LCU or reference-refresh services.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import http.client
import json
import os
from pathlib import Path
import platform
import selectors
import statistics
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]

JS = r'''
const fs=require('node:fs'),assert=require('node:assert/strict');
const {performance}=require('node:perf_hooks'),{chromium}=require('playwright');
(async()=>{
 const preset=JSON.parse(fs.readFileSync(process.env.PC_PRESET,'utf8'));
 const token=fs.readFileSync(process.env.PC_TOKEN_FILE,'utf8').trim();
 const base=process.env.PC_URL, records=[], errors=[], blocked=[];
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_EXECUTABLE,args:['--no-sandbox']});
 const context=await browser.newContext({viewport:{width:1600,height:1000}});
 const page=await context.newPage();let eventOrigin=performance.now();
 const offset=()=>performance.now()-eventOrigin;
 await context.route('**/*',route=>{
  if(new URL(route.request().url()).origin!==base){blocked.push('non-loopback request');return route.abort();}
  return route.continue();
 });
 await page.addInitScript(preset=>{
  window.__pcMeasurement={presetApplied:false,events:[]};
  const apply=()=>{
   if(window.__pcMeasurement.presetApplied || !document.querySelector('#pc-pregame'))return;
   for(const [id,value] of Object.entries(preset.fields))document.getElementById(id).value=value;
   document.querySelector('#pc-auto').checked=false;
   window.__pcMeasurement.presetApplied=true;
   window.__pcMeasurement.presetAt=performance.now();
  };
  new MutationObserver(()=>{
   apply();
   const card=document.querySelector('#pc-cards > article.coach-card');
   const title=card?.querySelector('h3')?.textContent;
   const resource=document.querySelector('[data-card-id="resource-observed-matchup"] h3')?.textContent;
   const notice=document.querySelector('#pc-notice')?.textContent;
   if(title && notice==='입력에 맞는 근거를 표시했습니다.'){
    const events=window.__pcMeasurement.events,previous=events.at(-1);
    if(!previous || previous.title!==title || previous.resource!==resource)
     events.push({at:performance.now(),title,resource,notice,own:document.querySelector('#pc-own').value});
   }
  }).observe(document,{childList:true,subtree:true,characterData:true});
  apply();
 },preset);
 page.on('pageerror',e=>errors.push(e.message));
 page.on('request',request=>{
  const url=new URL(request.url());
  assert(!url.search && !url.hash,'no token in request URL');
  if(request.method()!=='GET' && !url.pathname.endsWith('/pc-preview'))throw Error('unexpected browser write');
  if(url.pathname.endsWith('/pc-preview')){
   const body=request.postDataJSON();
   records.push({kind:'request',at_ms:offset(),revision:body.draft_revision,input:body.input});
  }
 });
 page.on('requestfailed',request=>{
  if(new URL(request.url()).pathname.endsWith('/pc-preview'))records.push({kind:'requestfailed',at_ms:offset(),reason:request.failure()?.errorText});
 });
 page.on('response',async response=>{
  if(!new URL(response.url()).pathname.endsWith('/pc-preview'))return;
  const request=response.request(),body=request.postDataJSON();
  try {
   const result=await response.json();
   records.push({kind:'response',at_ms:offset(),status:response.status(),revision:body.draft_revision,
    returned_revision:result.draft_revision,input:body.input,cards:result.cards?.map(c=>({id:c.id,title:c.title,sources:c.sources}))});
  }catch(error){records.push({kind:'response-body-failure',at_ms:offset(),reason:error.name});}
 });
 function matchingResponse(own){return records.findLast(r=>r.kind==='response'&&r.status===200&&
  r.input.my_champion===own&&r.input.patch===preset.patch&&r.input.my_position===preset.position&&
  r.input.slots.some(s=>s.side==='ENEMY'&&s.position===preset.position&&s.champion===preset.opponent)&&
  r.revision===r.returned_revision&&r.cards?.some(c=>c.id==='resource-observed-matchup'&&
   c.title===`프로 참고 자원 · ${own} 대 ${preset.opponent}`&&c.sources?.some(s=>s.sha256===preset.report_sha256)));}
 async function complete(own,after){
  await page.waitForFunction(({own,opponent,after})=>{
   const events=window.__pcMeasurement?.events||[];
   return events.some(e=>e.at>=after&&e.own===own&&e.resource===`프로 참고 자원 · ${own} 대 ${opponent}`);
  },{own,opponent:preset.opponent,after},{timeout:120000});
  // Response body consumption may finish after the DOM observer callback.
  for(let i=0;i<100&&!matchingResponse(own);i++)await page.waitForTimeout(10);
  const response=matchingResponse(own);assert(response,'matching final response revision/source/picks');
  const state=await page.evaluate(()=>window.__pcMeasurement);
  const event=state.events.find(e=>e.at>=after&&e.own===own&&e.resource===`프로 참고 자원 · ${own} 대 ${preset.opponent}`);
  const first=await page.locator('#pc-cards > article.coach-card').first().locator('h3').innerText();
  assert(response.cards.some(c=>c.title===first),'first visible card belongs to matched response');
  assert.equal(await page.locator('#pc-own').inputValue(),own);
  assert.equal(await page.locator('#pc-patch').inputValue(),preset.patch);
  return {event,response,state,first};
 }
 let result;
 try {
  eventOrigin=performance.now();
  await page.goto(base+'/pc#token='+encodeURIComponent(token),{waitUntil:'domcontentloaded',timeout:120000});
  const entry=await complete(preset.initial,0);
  assert(entry.state.presetApplied,'isolated preset applied');
  const firstRequest=records.find(r=>r.kind==='request');
  assert.equal(firstRequest.input.my_champion,preset.initial,'first preview already has preset');
  const navigation=await page.evaluate(()=>performance.getEntriesByType('navigation')[0].toJSON());
  const entry_ms=entry.event.at; // performance time origin is navigation start.
  await page.waitForTimeout(250); // same brief settling interval before each single-field change.
  const changeStart=await page.evaluate(()=>performance.now());
  const changeNodeStart=offset();
  await page.fill('#pc-own',preset.changed);
  const refreshed=await complete(preset.changed,changeStart);
  const changedRequest=records.find(r=>r.kind==='request'&&r.input.my_champion===preset.changed);
  assert(changedRequest.revision>firstRequest.revision,'new revision after actual input');
  assert.equal(errors.length,0);assert.equal(blocked.length,0);
  result={passed:true,browser_version:browser.version(),node_version:process.version,
   entry_to_matching_card_ms:entry_ms,pick_change_to_matching_card_ms:refreshed.event.at-changeStart,
   change_boundary:'page performance.now immediately before Playwright fill; includes driver/action/debounce',
   entry_first_card:entry.first,changed_first_card:refreshed.first,
   initial_revision:entry.response.revision,changed_revision:refreshed.response.revision,
   preset_applied_at_ms:entry.state.presetAt,navigation,
   changed_request_after_action_start_ms:changedRequest.at_ms-changeNodeStart,
   dom_events:refreshed.state.events,preview_records:records,browser_errors:errors,blocked_requests:blocked};
 }catch(error){result={passed:false,error:String(error.stack||error),preview_records:records,browser_errors:errors,blocked_requests:blocked};}
 finally {await browser.close();}
 process.stdout.write(JSON.stringify(result)+'\n');if(!result.passed)process.exitCode=1;
})().catch(error=>{process.stdout.write(JSON.stringify({passed:false,error:String(error.stack||error)})+'\n');process.exitCode=1;});
'''


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def serve(directory):
    sys.path.insert(0, str(ROOT))
    from scripts.launch_pc import create_server
    server = create_server(directory, port=0)
    from coach_v1.pc_runtime import load_pc_default_datasets
    from coach_v1.recall_pc import load_datasets
    load_pc_default_datasets(server)
    statuses = load_datasets(server)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=120)
    connection.request('GET', '/dev/v1/pregame/pc-status', headers={'Authorization': 'Bearer '+server.token})
    response = connection.getresponse()
    status = response.status
    response.read()
    connection.close()
    if status != 200:
        raise RuntimeError('Authenticated local readiness failed')
    print(json.dumps(dict(ready=True, port=server.server_port, recall_status=statuses,
                          power_dataset_count=len(server.power_datasets))), flush=True)
    try:
        sys.stdin.read()
    finally:
        server.shutdown()
        server.server_close()


def run(args):
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    targets = [output.with_suffix(suffix) for suffix in ('.json', '.md', '.log')]
    if any(path.exists() for path in targets):
        raise ValueError('Refusing to overwrite existing evidence')
    report_path = ROOT/'data/resource_recovery/2026-10-16/resources.json'
    report = json.loads(report_path.read_text())
    cohorts = [c for c in report['cohorts'] if c['patch']=='16.20' and c['position']=='BOTTOM' and c['opponent_champion']=='Aphelios']
    assert all(any(c['champion']==own for c in cohorts) for own in ('Draven', 'Kalista'))
    preset = dict(initial='Draven', changed='Kalista', opponent='Aphelios', patch='16.20', position='BOTTOM',
                  report_sha256=sha(report_path), fields={'pc-own':'Draven','pc-laner':'Aphelios','pc-position':'BOTTOM','pc-patch':'16.20'})
    source_names = ['scripts/measure_pc_phases.py','scripts/launch_pc.py','coach_v1/pc_runtime.py',
                    'coach_v1/pc_coach.py','coach_v1/resource_view.py','web_r4/pc.js','web_r4/pc.html']
    data_paths = [report_path, report_path.with_name('source-binding.json')]
    data_paths += sorted((ROOT/'data/riot/2026-10-13').glob('power-*'))
    data_paths += sorted((ROOT/'data/recall/2026-10-15').glob('*/recall-data.json'))
    files = {str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size, sha256=sha(p)) for p in data_paths}
    cpu = next((line.split(':',1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')), None)
    result = dict(schema_version='pc-phase-measurement.v1', at=datetime.now(timezone.utc).isoformat(),
                  environment=dict(os=platform.platform(),python=sys.version.split()[0],cpu=cpu,
                                   logical_cpu_count=os.cpu_count(),chromium_executable=args.chromium,
                                   cpu_limit=Path('/sys/fs/cgroup/cpu.max').read_text().strip() if Path('/sys/fs/cgroup/cpu.max').exists() else None),
                  preset=preset, data_files=files, source_sha256={name:sha(ROOT/name) for name in source_names},
                  boundaries=dict(startup='parent monotonic immediately before Popen fresh Python -> child confirms authenticated GET /pc-status HTTP 200 fully read after create_server and local dataset loads; includes process/import/DB/local loaders/readiness request',
                                  entry='ready server + new empty Chromium context; navigation time origin -> MutationObserver sees first visible card and success notice plus matching resource card title; final response revision/picks/report hash also required',
                                  change='same loaded page, 250ms settled; page monotonic immediately before single Draven -> Kalista fill -> same semantic DOM condition with new revision; includes browser action and 100ms input debounce'),
                  cache=dict(server='new Python process and isolated SQLite each repeat; no preview warmup before first entry; authenticated status readiness warms status/assessment path',
                             browser='fresh Chromium process/context each repeat; no cookies/session/local storage/HTTP cache from prior repeats; all local replies no-store',
                             operating_system='filesystem/page cache not flushed; repeated trials may benefit; no machine reboot',
                             change='same server/browser/page after first render; local in-process caches warm'),
                  limitations=['Linux headless Chromium; not Windows/game PC launcher end-to-end',
                               'No PCServices/LCU adapter or background reference maintenance; no provider/API collection',
                               'Browser process launch is excluded from entry phase; OS scheduling and shared machine load uncontrolled',
                               'Isolated manual JSON preset injected before first preview; production PC has no persisted manual draft loader',
                               'No comparable baseline collected; historic 0.5–0.9s values are not a regression comparison',
                               'No LCU connectivity, gameplay accuracy, or user approval claim'], trials=[])
    logs=[]
    for index in range(args.repeats):
        with tempfile.TemporaryDirectory(prefix='pc-phase-') as temporary:
            folder=Path(temporary)
            (folder/'preset.json').write_text(json.dumps(preset))
            (folder/'probe.cjs').write_text(JS)
            server=None
            trial=dict(index=index+1)
            try:
                start=time.perf_counter()
                server=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--serve',str(folder/'private')],cwd=ROOT,
                                        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                selector=selectors.DefaultSelector()
                selector.register(server.stdout,selectors.EVENT_READ)
                if not selector.select(timeout=180):
                    raise TimeoutError('server readiness timeout')
                line=server.stdout.readline()
                trial['server_start_to_ready_ms']=(time.perf_counter()-start)*1000
                ready=json.loads(line)
                assert ready.get('ready')
                trial['server_ready']=ready
                env=dict(os.environ,NODE_PATH=os.environ.get('NODE_PATH','/opt/codex/cua_node/lib/node_modules'),
                         PC_URL=f"http://127.0.0.1:{ready['port']}",PC_TOKEN_FILE=str(folder/'private/access-token'),
                         PC_PRESET=str(folder/'preset.json'),CHROMIUM_EXECUTABLE=args.chromium)
                browser=subprocess.run(['node',str(folder/'probe.cjs')],cwd=ROOT,env=env,capture_output=True,text=True,timeout=300)
                token=(folder/'private/access-token').read_text().strip()
                logs.append(f"trial {index+1} browser returncode={browser.returncode}\n"+(browser.stdout+browser.stderr).replace(token,'[REDACTED]'))
                trial['browser']=json.loads(browser.stdout)
                trial['passed']=browser.returncode==0 and trial['browser'].get('passed') is True
            except Exception as error:
                trial.update(passed=False,error=type(error).__name__+': '+str(error))
            finally:
                if server:
                    try:
                        _,stderr=server.communicate('',timeout=15)
                    except subprocess.TimeoutExpired:
                        server.kill()
                        _,stderr=server.communicate()
                    logs.append(f"trial {index+1} server stderr\n"+stderr)
            result['trials'].append(trial)
            print(json.dumps(dict(trial=index+1,passed=trial['passed'],startup_ms=trial.get('server_start_to_ready_ms'),
                                  entry_ms=trial.get('browser',{}).get('entry_to_matching_card_ms'),
                                  change_ms=trial.get('browser',{}).get('pick_change_to_matching_card_ms'))),flush=True)
    result['passed']=all(t['passed'] for t in result['trials']) and len(result['trials'])>=3
    summary={}
    for name,getter in [('server_start_to_ready_ms',lambda t:t.get('server_start_to_ready_ms')),
                        ('entry_to_matching_card_ms',lambda t:t.get('browser',{}).get('entry_to_matching_card_ms')),
                        ('pick_change_to_matching_card_ms',lambda t:t.get('browser',{}).get('pick_change_to_matching_card_ms'))]:
        values=[getter(t) for t in result['trials'] if t['passed']]
        summary[name]=dict(n=len(values),values=values,median=statistics.median(values) if values else None,
                           minimum=min(values) if values else None,maximum=max(values) if values else None)
    result['summary']=summary
    result['source_files_unchanged_during_measurement']=all(sha(ROOT/name)==value for name,value in result['source_sha256'].items())
    result['data_files_unchanged_during_measurement']=all(sha(ROOT/name)==value['sha256'] for name,value in files.items())
    result['passed']=result['passed'] and result['source_files_unchanged_during_measurement'] and result['data_files_unchanged_during_measurement']
    output.with_suffix('.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    output.with_suffix('.log').write_text('\n'.join(logs))
    lines=['# Isolated PC phase timing observations','',f"Successful matched trials: {sum(t['passed'] for t in result['trials'])}/{len(result['trials'])}.",'',
           '| Phase | Values (ms) | Median (ms) | Range (ms) |','|---|---|---|---|']
    for name,row in summary.items():
        values=', '.join(f'{v:.1f}' for v in row['values'])
        lines.append(f"| {name} | {values} | {row['median']:.1f} | {row['minimum']:.1f}–{row['maximum']:.1f} |" if row['n'] else f'| {name} | No successful trials | — | — |')
    lines+=['','Same local data hashes and Draven → Kalista / BOTTOM / Aphelios / 16.20 picks in every repeat. Each first preview starts with the isolated JSON preset. Timing completion requires a matching preview response revision, input, report SHA256 and semantic DOM card set; an old card or merely attached card cannot finish the trial.','',
            'The entry completion is the coherent rendered card set: first visible briefing card plus the matching resource card (which can be inside collapsed “more” details). It is not a promise that every resource card is visible without expanding details.','',
            'Boundaries:']+[f'- {name}: {text}' for name,text in result['boundaries'].items()]
    lines+=['','Cache conditions:']+[f'- {name}: {text}' for name,text in result['cache'].items()]
    lines+=['','Limitations:']+['- '+text for text in result['limitations']]
    lines+=['','Environment, browser versions, source/data hashes, per-request revision/timing records and failures are retained in the companion JSON/log. No existing browser acceptance suite was run.']
    output.with_suffix('.md').write_text('\n'.join(lines)+'\n')
    return 0 if result['passed'] else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serve',type=Path)
    parser.add_argument('--repeats',type=int,default=3)
    parser.add_argument('--chromium',default='/usr/bin/chromium')
    parser.add_argument('--output',default='evidence/actual-evidence/gemini-diagnostic/pc-phases-20261017')
    args=parser.parse_args()
    if args.serve:
        serve(args.serve)
        return 0
    if args.repeats<3:
        parser.error('at least three matched repeats required')
    return run(args)


if __name__=='__main__':
    raise SystemExit(main())

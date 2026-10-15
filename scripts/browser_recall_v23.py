"""New v2.3 evidence: synthetic raw inputs through real HTTP and Chromium.

This runner does not execute completed v2.1 checks. Only the LCU feed and raw
matches are synthetic; no preview/status HTTP response is intercepted or forged.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def place_events_in_received_frames(timeline):
    """Keep synthetic event batches inside their actual received interval."""
    frames = timeline['info']['frames']
    events = [event for frame in frames for event in frame['events']]
    for frame in frames:
        frame['events'] = []
    for event in events:
        enclosing = next(frame for frame in frames if frame['timestamp'] >= event['timestamp'])
        enclosing['events'].append(event)


def synthetic_datasets():
    from tests_pregame.test_recall_stats_v23 import fixture, event
    from coach_v1.recall_stats import extract_match, build_dataset
    from coach_v1.power_stats import build_power_dataset
    observations, pairs = [], []
    positions = ['BOTTOM', 'TOP', 'JUNGLE', 'MID', 'SUPPORT']
    teams = {100: ['Caitlyn', 'Ornn', 'Sejuani', 'Ahri', 'Lux'],
             200: ['Ezreal', 'Fiora', 'LeeSin', 'Zed', 'Nautilus']}
    for number in range(1, 6):
        match, timeline = fixture(number)
        match['info'].update(gameMode='CLASSIC', gameStartTimestamp=100000, gameDuration=600)
        match['info']['participants'] = [
            dict(participantId=index + 1 + (0 if team == 100 else 5),
                 teamId=team, championName=champion, teamPosition=positions[index])
            for team, champions in teams.items() for index, champion in enumerate(champions)]
        timeline['info']['frameInterval'] = 60000
        for frame in timeline['info']['frames']:
            minute = frame['timestamp'] / 60000
            frame['participantFrames'] = {
                str(player['participantId']): dict(
                    currentGold=900 + minute * 60,
                    totalGold=500 + minute * 100 + (100 if player['teamId'] == 100 else 0),
                    xp=minute * 200 + (100 if player['teamId'] == 100 else 0),
                    minionsKilled=minute * 5, jungleMinionsKilled=0, level=1 + int(minute),
                    championStats=dict(health=200 if minute == 3 else 1000, healthMax=1000),
                    position=dict(x=11000, y=1800))
                for player in match['info']['participants']}
            # A real insufficient Q15 minute, rather than an invented graph gap.
            if minute == 5 and number > 1:
                frame['participantFrames']['1'].pop('totalGold')
        event(timeline, 'ITEM_PURCHASED', 200000 + number * 1000, participantId=1, itemId=1001)
        event(timeline, 'ITEM_PURCHASED', 250000 + number * 1000, participantId=6, itemId=1001)
        event(timeline, 'CHAMPION_KILL', 220000, victimId=4, killerId=8,
              assistingParticipantIds=[6], position=dict(x=1000, y=8000))
        place_events_in_received_frames(timeline)
        observations.append(extract_match(match, timeline, population='CHALLENGER'))
        pairs.append(dict(match=match, timeline=timeline))
    recall = build_dataset(observations, population='CHALLENGER', retrieved_at='2026-10-15T00:00:00Z')
    source = dict(provider='SYNTHETIC', platform='KR', regional='ASIA', queue_id=420,
                  map_id=11, tier='CHALLENGER', patch='16.20', window_start=1,
                  window_end=2000000000, retrieved_at='2026-10-15T00:00:00Z',
                  sample_kind='SYNTHETIC', endpoints=['MATCH_V5_MATCH', 'MATCH_V5_TIMELINE'])
    return recall, build_power_dataset(pairs, source=source)


def synthetic_postgame():
    """Reuse the raw fixture constructor, without running any previous checks."""
    from copy import deepcopy
    from tests_pregame.test_v20_postgame import body
    sample = body()
    sample['match']['info'].update(gameVersion='16.20.1', gameDuration=600)
    sample['match']['info']['participants'][8]['championName'] = 'Ezreal'
    baseline = sample['timeline']['info']['frames'][0]['participantFrames']
    frames = []
    for minute in range(11):
        participants = deepcopy(baseline)
        for pid, participant in participants.items():
            participant.update(totalGold=500 + 100 * minute + int(pid), xp=60 * minute,
                               minionsKilled=5 * minute, jungleMinionsKilled=minute,
                               level=min(18, minute + 1), currentGold=0 if minute == 0 else 900 + 60 * minute,
                               championStats=dict(health=200 if pid == '4' and minute == 3 else 1000,
                                                  healthMax=1000),
                               position=dict(x=11000, y=1800))
        frames.append(dict(timestamp=minute * 60000, participantFrames=participants, events=[]))
    frames[-1]['events'] = [
        dict(type='ITEM_PURCHASED', timestamp=130000, participantId=4, itemId=1001),
        dict(type='ITEM_PURCHASED', timestamp=250000, participantId=9, itemId=1001),
        dict(type='CHAMPION_KILL', timestamp=260000, victimId=4, killerId=9,
             position=dict(x=11000, y=1800))]
    sample['timeline']['info']['frames'] = frames
    place_events_in_received_frames(sample['timeline'])
    return sample


BROWSER = r'''
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {chromium}=require('playwright');
const base=process.env.PC_URL, output=process.env.PC_OUTPUT;
const token=fs.readFileSync(process.env.PC_TOKEN_FILE,'utf8').trim();
const connectionFile=process.env.PC_CONNECTION_FILE;
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_EXECUTABLE||'/usr/bin/chromium',args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1440,height:1100}});
 const checks=[],timings=[],errors=[],responses=[],postgameResponses=[];let previewRequests=0,writeRequests=0,postgameImports=0;
 page.on('pageerror',error=>errors.push(error.message));
 page.on('request',request=>{
   assert(!request.url().includes(token));
   if(request.url().endsWith('/pc-preview'))previewRequests++;
   else if(request.url().endsWith('/postgame/import'))postgameImports++;
   else if(request.method()!=='GET')writeRequests++;
 });
 page.on('response',response=>{
   if(response.url().endsWith('/pc-preview'))responses.push(response.json());
   if(/\/postgame\/matches\/[a-f0-9]{64}$/.test(response.url()))postgameResponses.push(response.json());
 });
 const recall=()=>page.locator('[data-section="RECALL"]');
 const low=()=>page.locator('[data-section="LOW_HEALTH"]');
 async function settled(){await page.waitForFunction(()=>document.querySelector('#pc-notice').textContent==='입력에 맞는 근거를 표시했습니다.');}
 async function change(selector,value,label){
   await page.evaluate(selector=>{
     window.recallTiming={start:null,end:null};
     document.querySelector(selector).addEventListener('input',()=>{window.recallTiming.start=performance.now();},{once:true});
     const observer=new MutationObserver(()=>{
       const cards=[...document.querySelectorAll('[data-section="RECALL"]')];
       if(window.recallTiming.start!==null && cards.some(card=>card.getBoundingClientRect().height>0)){
         requestAnimationFrame(()=>{window.recallTiming.end=performance.now();});observer.disconnect();
       }
     });
     observer.observe(document.querySelector('#pc-cards'),{childList:true,subtree:true});
   },selector);
   await page.fill(selector,value);await settled();
   await page.waitForFunction(()=>window.recallTiming.end!==null);
   const ms=await page.evaluate(()=>Number((recallTiming.end-recallTiming.start).toFixed(2)));
   timings.push({input:selector,case:label,input_to_visible_recall_card_ms:ms});assert(ms<1000,'new recall input-to-visible-card target <1s: '+ms);
 }
 try{
   await page.goto(base+'/pc#token='+encodeURIComponent(token));
   await page.waitForSelector('#pc-workspace:visible');
   await page.selectOption('#pc-position','BOTTOM');await page.fill('#pc-patch','16.20');await page.fill('#pc-own','Caitlyn');await settled();
   await page.locator('.more-cards > summary').click();
   await change('#pc-laner','Ezreal','matching-patch-own-and-opponent');
   assert(await recall().count()>=2);assert(await low().count()>0);
   assert.equal(await page.locator('#pc-cards > [data-section="RECALL"],#pc-cards > [data-section="LOW_HEALTH"]').count(),0);
   assert.equal(await page.locator('.resource-graph svg').count(),0,'graphs are created only when card details expand');
   const known=recall().filter({has:page.locator('.evidence.STATISTICS')}).first();
   assert(await known.count()>0);
   await known.locator('details > summary').click();
   const text=await known.innerText();assert(text.includes('SHA256'));assert(text.includes('입력 패치와 일치'));
   assert(await known.locator('.sources a').count()>0);
   assert(await known.locator('.sources a').evaluateAll(links=>links.every(link=>link.protocol==='https:' && link.rel.includes('noopener'))));
   checks.push('real-preview-new-recall-low-health-cards-with-source-patch-and-detail-only-graphs');
   const hypotheses=page.locator('[data-section="RECALL"] .evidence.HYPOTHESIS,[data-section="LOW_HEALTH"] .evidence.HYPOTHESIS');
   assert(await hypotheses.count()>0);assert((await hypotheses.first().textContent()).includes('미검토 가설'));
   checks.push('new-recall-tactics-explicit-unreviewed-hypothesis');
   let graph=page.locator('.resource-graph').first();
   if(!await graph.count()){
     // Locate the actual graph-bearing card from the real response, never replace it.
     const projection=(await Promise.all(responses)).at(-1);
     const card=projection.cards.find(card=>card.graph && card.graph.points.some(point=>Number.isFinite(point.value)));
     assert(card,'real Q15 projection includes graph');
     const article=page.locator('[data-card-id="'+card.id+'"]');
     await article.locator('details > summary').click();graph=article.locator('.resource-graph');
   }
   await graph.waitFor({state:'visible'});
   assert((await graph.innerText()).includes('골드/분'));
   assert(await graph.locator('svg[role="img"] title').count()>0);
   const labels=await graph.locator('.graph-label').allTextContents();assert(labels.some(label=>label.includes('분')));assert(labels.some(label=>label.includes('골드')));
   const opponent=graph.locator('.graph-marker.opponent');assert(await opponent.count()>0);
   assert((await opponent.first().getAttribute('aria-label')).includes('맞라이너'));
   assert(await opponent.first().locator('title').textContent());
   assert(await graph.locator('svg').evaluate(svg=>![...svg.querySelectorAll('*')].some(element=>[...element.attributes].some(attribute=>/NaN|Infinity/.test(attribute.value)))));
   const paths=await graph.locator('.graph-line').evaluateAll(lines=>lines.map(line=>line.getAttribute('points')));
   assert(paths.length>=2,'insufficient real minute splits line into segments');
   checks.push('real-q15-rate-axis-finite-svg-with-gap-and-opponent-recall-tooltip');
   await page.screenshot({path:output+'/recall-expanded-1440.png',fullPage:true});
   await change('#pc-patch','16.19','patch-mismatch-unknown');
   assert(await recall().locator('.evidence.UNKNOWN').count()>0);
   const unknown=recall().filter({has:page.locator('.evidence.UNKNOWN')}).first();
   if(!await unknown.locator('details').evaluate(detail=>detail.open))await unknown.locator('details > summary').click();
   const unknownText=await unknown.innerText();assert(/미확인|UNKNOWN|부족|없|일치/.test(unknownText));
   assert(unknownText.includes('게임 패치와 다름'),'mismatched source patch must visibly warn');
   assert.equal(await page.locator('.resource-graph svg').count(),0,'wrong patch cannot reuse resource graph');
   checks.push('patch-separated-recall-unknown-and-no-stale-resource-graph');
   await change('#pc-patch','16.20','matching-patch-restored');
   await page.setViewportSize({width:390,height:1000});
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   await page.screenshot({path:output+'/recall-mobile-390.png',fullPage:true});
   checks.push('new-recall-cards-mobile-without-horizontal-overflow');
   fs.writeFileSync(connectionFile,JSON.stringify({status:'MANUAL_FALLBACK',reason:'NOT_CHAMP_SELECT',phase:'InProgress',revision:1,input:null}));
   await page.waitForFunction(()=>document.querySelector('#pc-connection').textContent==='게임 진행 중');
   assert.equal(await recall().count(),0);assert.equal(await low().count(),0);
   const result=await page.request.post(base+'/dev/v1/pregame/pc-preview',{headers:{Authorization:'Bearer '+token},data:{input:JSON.parse(fs.readFileSync(process.env.PC_INPUT_FILE,'utf8')),draft_revision:999}});
   assert.equal(result.status(),200);const suppressed=await result.json();
   assert.equal(suppressed.phase,'UNKNOWN');assert(!suppressed.cards.some(card=>['RECALL','LOW_HEALTH'].includes(card.section)));
   checks.push('synthetic-lcu-live-phase-suppresses-new-ui-and-real-server-preview');
   // New V6 private contexts only: the ordinary file upload and real store/API.
   await page.setViewportSize({width:1280,height:1000});
   await page.goto(base+'/postgame');await page.click('#pm-connect');
   await page.waitForSelector('#pm-workspace:visible');
   await page.locator('#pm-personal > summary').click();
   await page.locator('#pm-match-file').setInputFiles(process.env.PC_POSTGAME_MATCH_FILE);
   await page.selectOption('#pm-participant','4');
   await page.locator('#pm-timeline-file').setInputFiles(process.env.PC_POSTGAME_TIMELINE_FILE);
   await page.selectOption('#pm-source','SYNTHETIC');
   const started=performance.now();
   await page.click('#pm-import-button');
   await page.waitForFunction(()=>document.querySelectorAll('.recall-context').length===2);
   timings.push({case:'private-postgame-import-to-two-visible-contexts',import_to_visible_recall_context_ms:Number((performance.now()-started).toFixed(2))});
   const positive=(await Promise.all(postgameResponses)).at(-1);
   assert.equal(positive.source,'SYNTHETIC');assert.equal(positive.champion,'Caitlyn');
   assert.equal(positive.recall_contexts.status,'OBSERVED');
   assert.deepEqual(positive.recall_contexts.signals.map(signal=>signal.type),['FIRST_RECALL_PRIORITY_GAP','LOW_HEALTH_STAY_DEATH']);
   assert(positive.recall_contexts.signals.every(signal=>signal.inference==='OBSERVED_CONTEXT_NOT_MISTAKE'));
   assert.equal(positive.recall_contexts.low_health.action,'STAY');
   assert.equal(positive.recall_contexts.low_health.outcomes.self_deaths.value,1);
   assert(await page.locator('.recall-context').evaluateAll(cards=>cards.every(card=>card.getBoundingClientRect().height>0)));
   const contexts=await page.locator('.recall-context').allTextContents();
   assert(contexts.every(text=>text.includes('관측된 맥락')));
   assert(contexts.some(text=>text.includes('원인이라는 판정은 아닙니다')));
   assert((await page.locator('#pm-contexts').innerText()).includes('마지막 수신 프레임 이전까지만 집계하며 끝 구간은 제외합니다.'));
   assert(!contexts.some(text=>/AUTO_VERIFIED|자동 검토됨|사용자 승인|확정 실수|CHALLENGER|PRO_REFERENCE/.test(text)));
   assert(!JSON.stringify(positive).includes('PRIVATE_PUUID'));
   checks.push('new-private-postgame-real-import-two-positive-observation-contexts-without-wrong-labels');
   await page.locator('#pm-contexts').screenshot({path:output+'/postgame-recall-contexts.png'});
   // Selecting the opposite owner must not inherit the first player's signals.
   await page.selectOption('#pm-participant','9');
   const responsePending=page.waitForResponse(response=>/\/postgame\/matches\/[a-f0-9]{64}$/.test(response.url()));
   await page.click('#pm-import-button');const ownerResponse=await responsePending;
   const negative=await ownerResponse.json();
   await page.waitForFunction(()=>document.querySelector('#pm-title').textContent.startsWith('Ezreal') && document.querySelectorAll('.recall-context').length===0);
   assert.equal(negative.champion,'Ezreal');assert.equal(negative.recall_contexts.signals.length,0);
   assert.equal(negative.recall_contexts.first_recall.priority_gap.status,'NOT_EARLIER');
   assert.equal(negative.recall_contexts.low_health.reason,'NO_LOW_HEALTH_FRAME');
   assert.equal(postgameImports,2);
   checks.push('new-private-postgame-selected-owner-excludes-opponent-signals-and-unsupported-verdicts');
   assert.equal(writeRequests,0);assert.equal(errors.length,0);
   const projections=await Promise.all(responses);
   fs.writeFileSync(output+'/preview-projections.json',JSON.stringify(projections,null,2)+'\n');
   fs.writeFileSync(output+'/postgame-projections.json',JSON.stringify([positive,negative],null,2)+'\n');
   process.stdout.write(JSON.stringify({passed:true,checks,timings,browser_version:browser.version(),preview_requests:previewRequests,synthetic_private_postgame_imports:postgameImports,non_preview_write_requests:writeRequests+postgameImports,unexpected_write_requests:writeRequests,browser_errors:errors,scope:'SYNTHETIC Match-V5 raw fixtures and LCU feed; real local HTTP pc-status/pc-preview/private postgame import/store and Chromium rendering; no intercepted HTTP responses; not actual Windows/LCU gameplay evidence'})+'\n');
 }catch(error){process.stderr.write(JSON.stringify({errors,notice:await page.locator('#pc-notice,#pm-status').textContent(),cards:await page.locator('#pc-cards,#pm-contexts').innerText()})+'\n');throw error;}
 finally{await browser.close();}
})().catch(error=>{process.stderr.write(String(error.stack||error));process.exitCode=1;});
'''


def main():
    from scripts.launch_pc import create_server
    from tests_pregame.test_pc_coach import draft
    output = ROOT / 'evidence/queue/v23' / ('browser-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    output.mkdir(parents=True)
    recall, power = synthetic_datasets()
    with tempfile.TemporaryDirectory(prefix='recall-v23-synthetic-') as temporary:
        private = Path(temporary)
        connection_file = private / 'connection.json'
        connection_file.write_text(json.dumps(dict(status='MANUAL_FALLBACK', reason='SYNTHETIC_NO_GAME_CLIENT', phase=None, revision=0, input=None)))

        class SyntheticLCU:
            def snapshot(self):
                return json.loads(connection_file.read_text())

        server = create_server(private, port=0)
        server.test_mode = True
        server.recall_datasets = {'CHALLENGER': recall}
        server.power_datasets = {('16.20', 'CHALLENGER'): power}
        server.pc_services = SyntheticLCU()
        sample = draft()
        sample['slots'][8]['champion'] = 'Ezreal'
        (private / 'input.json').write_text(json.dumps(sample))
        postgame = synthetic_postgame()
        (private / 'postgame-match.json').write_text(json.dumps(postgame['match']))
        (private / 'postgame-timeline.json').write_text(json.dumps(postgame['timeline']))
        (private / 'browser.cjs').write_text(BROWSER)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        before_user_rows = len(server.research.list())
        try:
            env = dict(os.environ, PC_TOKEN_FILE=str(private/'access-token'),
                       PC_CONNECTION_FILE=str(connection_file), PC_INPUT_FILE=str(private/'input.json'),
                       PC_POSTGAME_MATCH_FILE=str(private/'postgame-match.json'),
                       PC_POSTGAME_TIMELINE_FILE=str(private/'postgame-timeline.json'),
                       PC_OUTPUT=str(output), PC_URL='http://127.0.0.1:'+str(server.server_port),
                       NODE_PATH=os.environ.get('NODE_PATH', '/opt/codex/cua_node/lib/node_modules'))
            result = subprocess.run(['node', str(private/'browser.cjs')], cwd=ROOT, env=env,
                                    capture_output=True, text=True, timeout=120)
            receipt = json.loads(result.stdout.strip() or '{}')
            receipt['passed'] = bool(receipt.get('passed')) and result.returncode == 0
            receipt['actual_windows_lcu'] = 'BLOCKED_EXTERNAL'
            receipt['actual_user_rows_before'] = before_user_rows
            receipt['actual_user_rows_after'] = len(server.research.list())
            receipt['actual_user_approvals_created'] = receipt['actual_user_rows_after'] - before_user_rows
            if receipt['actual_user_approvals_created']:
                receipt['passed'] = False
            source_paths = ['web_r4/pc.html', 'web_r4/pc.js', 'web_r4/pc.css',
                            'web_r4/postgame.html', 'web_r4/postgame.js', 'coach_v1/postgame_match.py',
                            'coach_v1/pc_coach.py', 'coach_v1/recall_stats.py',
                            'coach_v1/recall_pc.py', 'coach_v1/recall_candidates.py',
                            'coach_v1/pregame_server.py', 'coach_v1/official_items.py',
                            'coach_v1/power_stats.py', 'scripts/launch_pc.py',
                            'knowledge_candidates/recall-v23.json',
                            'tests_pregame/test_recall_stats_v23.py', 'scripts/browser_recall_v23.py']
            receipt['source_sha256'] = {path: hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
                                        for path in source_paths if (ROOT/path).is_file()}
            receipt['synthetic_input_sha256'] = {name: hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
                                                for name, data in [('recall', recall), ('power', power), ('private_postgame_fixture', postgame)]}
            from coach_v1.recall_stats import POLICY
            receipt['tested_coverage_guard'] = POLICY.get('coverage_guard')
            receipt['private_postgame_fixture_coverage'] = dict(
                first_received_frame_ms=postgame['timeline']['info']['frames'][0]['timestamp'],
                penultimate_received_frame_ms=postgame['timeline']['info']['frames'][-2]['timestamp'],
                last_received_frame_ms=postgame['timeline']['info']['frames'][-1]['timestamp'],
                last_interior_signal_event_ms=260000, positive_low_health_window_end_ms=300000,
                final_frame_event_count=len(postgame['timeline']['info']['frames'][-1]['events']))
            receipt['git_head'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
            (output/'runner.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n')
            (output/'browser.log').write_text((result.stdout+result.stderr).replace(server.token, '[REDACTED]'))
            print(json.dumps(dict(passed=receipt['passed'], evidence_directory=str(output))))
            if result.stderr:
                print(result.stderr.replace(server.token, '[REDACTED]'), file=sys.stderr)
            return 0 if receipt['passed'] else 1
        finally:
            server.shutdown()
            server.server_close()


if __name__ == '__main__':
    raise SystemExit(main())

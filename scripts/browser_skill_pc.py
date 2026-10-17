"""Changed PC renderers in Chromium using static files and in-memory fixtures.

Uses the existing CI Node Playwright installation. No application server, login,
API, source refresh, decision write, or provider is used. Renderer accessors are
injected into test copies of the real scripts only.
"""
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]

JS = r'''
const fs=require('node:fs'),assert=require('node:assert/strict'),path=require('node:path');
const {chromium}=require('playwright'),web=path.resolve('web_r4');
const read=name=>fs.readFileSync(path.join(web,name),'utf8');
(async()=>{
 const facts=JSON.parse(read('loading-data.json')).champions;
 const official={champion:'Lux',name:'럭스',source_patch:'16.20.1',patch_status:'MATCHING_ARCHIVE',
  facts:facts.Lux.facts.map(f=>({name:f.name,text:f.text,source:{url:f.url,locator:f.locator,sha256:f.sha256,patch:f.patch}}))};
 const q='럭스의 빛의 속박(Q)',trap='케이틀린의 요들잡이 덫(W)',net='케이틀린의 90구경 투망(E)';
 const input={my_champion:'Caitlyn',my_position:'BOTTOM',slots:[
  ['Caitlyn','ALLY','BOTTOM'],['Lux','ALLY','SUPPORT'],['Kaisa','ENEMY','BOTTOM'],['Nautilus','ENEMY','SUPPORT']
 ].map(([champion,side,position])=>({champion,side,position}))};
 const cards={phase:'PRE_GAME',stage:'COMPOSITION',cards:[
  {id:'owned',champion:'Caitlyn',evidence_level:'HYPOTHESIS',title:'덫과 투망',
   lines:['덫과 투망을 확인합니다.'],details:'럭스 Q도 확인합니다.',sources:[]},
  {id:'unowned',evidence_level:'AUTO_VERIFIED',title:'소유자 미확인',
   lines:['Q와 덫은 소유자를 추정하지 않습니다.'],details:'럭스 Q를 확인합니다.',
   candidate_id:'isolated-fixture',candidate_sha256:'a'.repeat(64),sources:[]},
  {id:'official',champion:'Lux',evidence_level:'OFFICIAL',title:'럭스 기술 설명',
   lines:official.facts.slice(0,3).map(f=>f.name+': '+f.text),
   details:official.facts.map(f=>f.name+': '+f.text).join('\n'),
   sources:official.facts.map(f=>f.source),patch_status:'MATCHING_ARCHIVE'}]};
 const browser=await chromium.launch({headless:true,
  ...(process.env.CHROMIUM_EXECUTABLE?{executablePath:process.env.CHROMIUM_EXECUTABLE}:{}),args:['--no-sandbox']});
 const apiCalls=[],external=[],observations=[];
 try{
  for(const width of [1440,390]){
   const context=await browser.newContext({viewport:{width,height:1000}}),page=await context.newPage(),errors=[];
   page.on('pageerror',e=>errors.push(e.message));
   const assertFit=async selector=>{
    assert(await page.locator(selector).isVisible(),selector);
    assert(await page.locator(selector).evaluate(node=>{const box=node.getBoundingClientRect();
     return box.left>=-1&&box.right<=innerWidth+1&&node.scrollWidth<=Math.ceil(box.width)+1;}),width+' '+selector);
   };
   // Original production HTML and deferred scripts boot without auth or API access.
   await page.route('**/*',async route=>{
    const pathname=new URL(route.request().url()).pathname,asset=pathname==='/pc'?'pc.html':pathname.slice(1);
    if(!['pc.html','pc.js','pc.css','skill-data.js','skill-display.js'].includes(asset)){
     external.push(route.request().url());return route.abort();
    }
    await route.fulfill({contentType:asset.endsWith('.html')?'text/html':asset.endsWith('.css')?'text/css':'text/javascript',body:read(asset)});
   });
   await page.goto('http://localhost/pc');
   assert(await page.locator('#pc-auth').isVisible());
   assert.equal(await page.locator('#pc-team-inputs input').count(),10);
   assert.equal(await page.evaluate(()=>SkillDisplay.label('Lux','Q')),q);
   assert.equal(await page.evaluate(()=>Object.keys(LoLSkillNames.champions).length),173);
   const load=async(stem,exports)=>{
    const html=read(stem+'.html').replace(/<script\b[^>]*>[\s\S]*?<\/script>/g,'').replace(/<link\b[^>]*>/g,'');
    await page.unrouteAll({behavior:'wait'});
    await page.route('**/*',async route=>{
     if(route.request().url()==='http://localhost/skill-fixture')return route.fulfill({contentType:'text/html',body:html});
     external.push(route.request().url());return route.abort();
    });
    await page.goto('http://localhost/skill-fixture');
    await page.evaluate(()=>{sessionStorage.clear();window.__apiCalls=[];
     window.fetch=(...args)=>{__apiCalls.push(String(args[0]));return Promise.reject(new Error('API prohibited in display fixture'));};});
    for(const name of ['skill-data.js','skill-display.js','official_reference.js'])await page.addScriptTag({path:path.join(web,name)});
    if(fs.existsSync(path.join(web,stem+'.css')))await page.addStyleTag({path:path.join(web,stem+'.css')});
    const source=read(stem+'.js'),stop=source.lastIndexOf('})();');assert(stop>=0);
    await page.addScriptTag({content:source.slice(0,stop)+exports+source.slice(stop)});
   };
   await load('pc','window.__fixture={render,renderCatalog,input:value=>{currentInput=value;},catalog:value=>{catalog=value;}};');
   await page.evaluate(data=>{window.__input=data.input;window.__cards=data.cards;window.__before=JSON.stringify(data);
    __fixture.input(__input);__fixture.render(__cards);__fixture.catalog([data.official]);__fixture.renderCatalog();
    document.getElementById('pc-workspace').hidden=false;document.getElementById('pc-auth').hidden=true;
   },{input,cards,official});
   assert((await page.locator('[data-card-id="owned"]').innerText()).includes(trap));
   assert((await page.locator('[data-card-id="owned"]').innerText()).includes(net));
   await assertFit('[data-card-id="owned"] .card-lines');
   assert((await page.locator('[data-card-id="unowned"]').innerText()).includes('Q와 덫은 소유자를 추정하지 않습니다.'));
   assert((await page.locator('[data-card-id="unowned"]').textContent()).includes(q));
   assert((await page.locator('#pc-reference-list').textContent()).includes(q));
   for(const f of official.facts){
    assert((await page.locator('[data-card-id="official"]').textContent()).includes(f.text));
    assert((await page.locator('#pc-reference-list').textContent()).includes(f.text));
   }
   assert(await page.evaluate(official=>__before===JSON.stringify({input:__input,cards:__cards,official}),official));
   apiCalls.push(...await page.evaluate(()=>__apiCalls));

   await load('pregame','window.__fixture={cellContent,cooldowns,detail};');
   const plan={validity:'CURRENT',input,evaluations:[]};
   const cell={key:'LANE',status:'KNOWN',texts:['럭스 Q 뒤 케이틀린 W를 확인합니다.'],rules:[],reasons:[],cooldowns:[
    {name:'빛의 속박',side:'ALLY',position:'SUPPORT',spell_kind:'ABILITY'},
    {name:'Q',side:'ALLY',position:'SUPPORT',spell_kind:'ABILITY'},
    {name:'빛의 속박',side:'ALLY',position:'SUPPORT',spell_kind:'SUMMONER'}]};
   await page.evaluate(data=>{window.__plan=data.plan;window.__cell=data.cell;window.__before=JSON.stringify(data);
    const host=document.getElementById('pg-cards');__fixture.cellContent(host,__cell,__plan);__fixture.detail(host,__plan,[__cell]);
    OfficialReference.render(document.getElementById('pg-reference'),data.official);
    document.getElementById('pg-workspace').hidden=false;document.getElementById('pg-plan-panel').hidden=false;
    document.getElementById('pg-auth').hidden=true;
   },{plan,cell,official:{champions:[official]}});
   assert((await page.locator('#pg-cards').textContent()).includes(q));
   assert((await page.locator('#pg-cards').textContent()).includes(trap));await assertFit('#pg-cards');
   assert.deepEqual((await page.locator('#pg-cards .cooldown > p:first-child').allTextContents()).slice(0,3),
    [q+' · 미확인','Q · 미확인','빛의 속박 · 미확인']);
   assert((await page.locator('#pg-reference strong').allTextContents()).includes(q));
   assert.deepEqual(await page.locator('#pg-reference .official-fact p').allTextContents(),official.facts.map(f=>f.text));
   const raw=JSON.parse(await page.locator('#pg-cards pre').textContent());
   assert.deepEqual(raw.cells[0].texts,cell.texts);assert.deepEqual(raw.cells[0].cooldowns,cell.cooldowns);
   assert(await page.evaluate(official=>__before===JSON.stringify({plan:__plan,cell:__cell,official}),{champions:[official]}));
   await page.evaluate(()=>{const p=structuredClone(__plan);p.input.slots.push({champion:'Nautilus',side:'ALLY',position:'SUPPORT'});
    const host=document.getElementById('pg-cards');host.replaceChildren();__fixture.cooldowns(host,[__cell.cooldowns[0]],p);});
   assert.equal(await page.locator('#pg-cards .cooldown > p:first-child').textContent(),'빛의 속박 · 미확인');
   apiCalls.push(...await page.evaluate(()=>__apiCalls));

   await load('review_queue','window.__fixture={set:value=>{queue=value;render();},current:()=>current};');
   const candidate={candidate_id:'fixture',selected_version:1,claim:'럭스 Q 뒤 케이틀린 W를 확인합니다.',
    priority:{reason:'fixture',observed_frequency:0},conditions:{applicability:{champion:'TYPE_BASED'}},patch_range:'UNKNOWN',
    sources:[{title:'원문',locator:'data.Lux.spells.0.description',patch:'16.20.1',excerpt:'원문 Q와 덫은 변경하지 않습니다.'}],
    counterexamples:['럭스 Q가 없으면 중단합니다.'],statistics:{status:'UNKNOWN',comparisons:[],limitations:[]},
    preview:{text:'럭스 Q를 확인합니다.',reasons:[]}};
   const queue={progress:{ready:1,optional_archive:0,deferred:0,reviewed:0,rejected:0,example_card_filled:0,example_card_total:5},
    candidates:[candidate],deferred_candidates:[],page_limit:20,official_reference:{champions:[official]}};
   await page.evaluate(data=>{window.__queue=data;window.__before=JSON.stringify(data);__fixture.set(data);
    document.getElementById('rq-workspace').hidden=false;document.getElementById('rq-auth').hidden=true;},queue);
   assert((await page.locator('#rq-claim').textContent()).includes(q));
   assert((await page.locator('#rq-claim').textContent()).includes(trap));await assertFit('#rq-claim');
   assert((await page.locator('#rq-preview').textContent()).includes(q));
   assert.equal(await page.locator('#rq-edit-claim').inputValue(),candidate.claim);
   assert.equal(await page.locator('#rq-sources blockquote').textContent(),candidate.sources[0].excerpt);
   assert(await page.evaluate(()=>__before===JSON.stringify(__queue)));
   apiCalls.push(...await page.evaluate(()=>__apiCalls));assert.deepEqual(errors,[]);
   observations.push({width,original_pc_script_load:true,pc:true,pregame:true,review_queue:true,
    labels_fit_viewport:true,official_source_bodies:true,unchanged_fixture_data:true});
   await context.close();
  }
  assert.deepEqual(apiCalls,[]);assert.deepEqual(external,[]);
  process.stdout.write(JSON.stringify({viewports:[1440,390],observations,api_calls:0,external_requests:0,
   fixture_objects_unchanged:true,official_bodies_and_source_quotes_unchanged:true,
   evidence_scope:'SYNTHETIC_DISPLAY_FIXTURES_NOT_WINDOWS_OR_STRATEGY_VALIDATION'})+'\n');
 }finally{await browser.close();}
})().catch(e=>{process.stderr.write(String(e.stack||e)+'\n');process.exitCode=1;});
'''


def main():
    env = dict(os.environ, NODE_PATH=os.environ.get('NODE_PATH', '/opt/codex/cua_node/lib/node_modules'))
    if 'CHROMIUM_EXECUTABLE' not in env and Path('/usr/bin/chromium').exists():
        env['CHROMIUM_EXECUTABLE'] = '/usr/bin/chromium'
    return subprocess.run(['node', '-e', JS], cwd=ROOT, env=env, timeout=90).returncode


if __name__ == '__main__':
    raise SystemExit(main())

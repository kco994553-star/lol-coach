"""Independent Chromium QA of shipped champion DOM on PC and /lol-coach/ export.

Uses the Node Playwright installed in CI, never the Python Playwright package.
All browser requests are constrained to the two isolated loopback servers.
"""
from datetime import datetime, timezone
import argparse
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
sys.path.insert(0, str(ROOT))

BROWSER = r'''
const assert=require('node:assert/strict'),fs=require('node:fs'),{chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_EXECUTABLE?{executablePath:process.env.CHROMIUM_EXECUTABLE}:{}),args:['--no-sandbox']});
 const result={passed:false,checks:[],screenshots:[],browser_errors:[],console_errors:[],http_errors:[],external_requests:[],provider_requests:0,actual_user_approvals_created:0};
 const origins=[process.env.CHAMPION_PC,process.env.CHAMPION_WEB];
 const check=(name)=>result.checks.push(name);
 async function makePage(width,height){
  const context=await browser.newContext({viewport:{width,height},hasTouch:true,reducedMotion:'reduce'});
  const page=await context.newPage();page.setDefaultTimeout(10000);
  page.on('pageerror',e=>result.browser_errors.push({url:page.url(),message:e.message}));page.on('console',message=>{if(message.type()==='error')result.console_errors.push({url:page.url(),message:message.text()});});
  page.on('response',r=>{if(r.status()>=400)result.http_errors.push({url:r.url(),status:r.status()});});
  await context.route('**/*',route=>{const url=route.request().url();if(origins.some(o=>url.startsWith(o+'/')))return route.continue();result.external_requests.push(url);return route.abort();});
  return page;
 }
 async function noOverflow(page,label){const overflow=await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,nodes:[...document.querySelectorAll('body *')].filter(n=>{const r=n.getBoundingClientRect();return r.width>0&&(r.right>innerWidth+1||r.left< -1);}).slice(0,12).map(n=>({tag:n.tagName,id:n.id,cls:n.className,width:n.getBoundingClientRect().width,right:n.getBoundingClientRect().right}))}));assert(overflow.scrollWidth<=overflow.width+1,label+' horizontal overflow '+JSON.stringify(overflow));check(label+' no horizontal overflow');}
 async function capture(page,name){await page.evaluate(()=>document.fonts.ready);await page.screenshot({path:process.env.CHAMPION_OUT+'/'+name+'.png',fullPage:true});result.screenshots.push({file:name+'.png',url:page.url(),viewport:page.viewportSize()});}
 const state=(champion='Caitlyn',position='BOTTOM')=>'#state='+encodeURIComponent(JSON.stringify({champion,position}));
 try{

  for(const [mode,base,prefix] of [['pc',process.env.CHAMPION_PC,''],['public',process.env.CHAMPION_WEB,'/lol-coach']]){
   const page=await makePage(1440,1000),url=(name)=>base+prefix+'/'+name;
   if(process.env.CHAMPION_SCREENS_ONLY!=='1'){
    await page.goto(url('champions.html'));await page.locator('#champion-grid .champion-card').first().waitFor();
    assert.equal(await page.locator('#coach-nav a[data-page]').count(),6);check(mode+' six menus');
    const allCount=await page.locator('#champion-grid .champion-card').count();assert(allCount>=170);
    await page.goto(url('champion.html')+state('Caitlyn',''));await page.locator('#champion-detail').waitFor({state:'visible'});assert.equal(await page.locator('#own-position').inputValue(),'','ALL without a chosen role requires explicit selection');assert(await page.locator('#gameplan-own').isDisabled());await page.goto(url('champions.html'));await page.locator('#champion-grid .champion-card').first().waitFor();
    await page.locator('#champion-search').fill('Caitlyn');assert.equal(await page.locator('#champion-grid .champion-card[data-champion="Caitlyn"]').count(),1);
    await page.locator('#champion-search').fill('케이틀린');assert.equal(await page.locator('#champion-grid .champion-card').count(),1);
    await page.locator('#champion-search').fill('zzzz-no-such-champion');await page.locator('#empty-results').waitFor({state:'visible'});assert.equal(await page.locator('#champion-grid .champion-card').count(),0);
    await page.locator('#reset-search').click();assert.equal(await page.locator('#champion-grid .champion-card').count(),allCount);
    await page.locator('#position-filter').selectOption('BOTTOM');
    const stats=await page.evaluate(async()=>await(await fetch('./champion-stats.json')).json());
    const observed=await page.locator('#champion-grid .champion-card').evaluateAll(nodes=>nodes.map(n=>n.dataset.champion));
    assert.deepEqual(observed.slice().sort(),Object.entries(stats.champions).filter(([id,c])=>c.observed_positions.some(r=>r.position==='BOTTOM'&&r.matches>0)).map(([id])=>id).sort());
    await page.locator('#champion-search').fill('Caitlyn');const filteredHref=await page.locator('#champion-grid [data-champion="Caitlyn"]').getAttribute('href');assert.equal(JSON.parse(decodeURIComponent(new URL(filteredHref,page.url()).hash.slice(7))).position,'BOTTOM');await page.locator('#champion-grid [data-champion="Caitlyn"]').click();await page.locator('#champion-detail').waitFor({state:'visible'});
    assert.equal(await page.locator('#own-position').inputValue(),'BOTTOM','explicitly chosen position filter carries the reference role');
    assert(await page.locator('#gameplan-own').isEnabled());
    await page.locator('#own-position').selectOption('BOTTOM');
    await page.locator('#context-opponent').selectOption('Ezreal');await page.locator('#opponent-position').selectOption('BOTTOM');await page.locator('#ally-support').selectOption('Lux');await page.locator('#enemy-support').selectOption('Nautilus');
    const baselineHash=new URL(page.url()).hash,baselineTitle=await page.locator('#champion-name').innerText();
    await page.locator('#change-champion').click();await page.locator('#champion-dialog[open]').waitFor();await page.locator('#dialog-position').selectOption('ALL');await page.locator('#dialog-search').fill('zzzz-no-such-champion');assert.equal(await page.locator('#dialog-grid .champion-card').count(),0);
    await page.locator('#dialog-search').fill('Ahri');await page.locator('#dialog-grid [data-champion="Ahri"]').click();
    assert.equal(await page.locator('#champion-name').innerText(),baselineTitle);assert.equal(new URL(page.url()).hash,baselineHash);
    await page.locator('#dialog-cancel').click();assert.equal(await page.locator('#champion-name').innerText(),baselineTitle);assert.equal(new URL(page.url()).hash,baselineHash);
    assert.equal(await page.evaluate(()=>document.activeElement.id),'change-champion');
    await page.locator('#change-champion').click();await page.locator('#dialog-search').fill('Ahri');await page.locator('#dialog-grid [data-champion="Ahri"]').click();await page.keyboard.press('Escape');
    assert.equal(new URL(page.url()).hash,baselineHash);assert.equal(await page.evaluate(()=>document.activeElement.id),'change-champion');
    await page.locator('#change-champion').click();await page.locator('#dialog-search').fill('Ahri');await page.locator('#dialog-grid [data-champion="Ahri"]').click();await page.locator('#dialog-apply').click();
    assert.equal(await page.locator('#own-position').inputValue(),'BOTTOM');assert.match(await page.locator('#champion-name').innerText(),/아리/);for(const [id,value]of [['context-opponent','Ezreal'],['opponent-position','BOTTOM'],['ally-support','Lux'],['enemy-support','Nautilus']])assert.equal(await page.locator('#'+id).inputValue(),value);
    await page.reload();await page.locator('#champion-detail').waitFor({state:'visible'});assert.match(await page.locator('#champion-name').innerText(),/아리/);assert.equal(await page.locator('#own-position').inputValue(),'BOTTOM');
    await page.locator('#back-to-champions').click();await page.locator('#recent-section').waitFor({state:'visible'});assert(await page.locator('#recent-champions [data-champion="Ahri"]').count());
    await page.locator('#position-filter').selectOption('MID');const recentRole=page.locator('#recent-champions [data-champion="Ahri"][data-position="BOTTOM"]');assert.equal(await recentRole.count(),1);const recentHref=await recentRole.getAttribute('href');assert.equal(JSON.parse(decodeURIComponent(new URL(recentHref,page.url()).hash.slice(7))).position,'BOTTOM');await recentRole.click();await page.locator('#champion-detail').waitFor({state:'visible'});assert.equal(await page.locator('#own-position').inputValue(),'BOTTOM');await page.locator('#back-to-champions').click();await page.locator('body[data-champion-ready="true"]').waitFor();check(mode+' explicit-role href and recent champion-role pair survive a different filter');
    check(mode+' Korean English search, no results, observed filter, explicit role, recent, modal cancel apply Escape focus and refresh');
    await page.goto(url('champion.html')+state());await page.locator('#champion-detail').waitFor({state:'visible'});
    const expected=stats.champions.Caitlyn.positions.BOTTOM;
    assert(stats.growth_source,'retained real growth source is required');{
     const growth=expected.growth;assert(growth&&growth.points.length);assert.notEqual(stats.growth_source.dataset_digest,stats.source.dataset_digest);
     assert((await page.locator('#growth-source').innerText()).includes(stats.growth_source.matches+'경기'));assert((await page.locator('#growth-provenance').textContent()).includes(stats.growth_source.dataset_digest));
     const growthRows=await page.locator('#growth-table tr').evaluateAll(nodes=>nodes.map(n=>({...n.dataset})));
     assert.equal(growthRows.length,growth.points.length);
     for(const row of growthRows){const point=growth.points.find(p=>p.metric===row.metric&&p.minute===Number(row.minute));assert(point);assert.equal(Number(row.n),point.n);assert.equal(Number(row.championN),point.champion_n);assert.equal(Number(row.referenceN),point.reference_n);assert.equal(row.visible,String(point.visible));if(point.visible){assert.equal(Number(row.championMean),point.champion_mean);assert.equal(Number(row.referenceMean),point.reference_mean);assert.equal(Number(row.meanDelta),point.mean_delta);}else{assert.equal(row.championMean,undefined);assert.equal(row.referenceMean,undefined);assert.equal(row.meanDelta,undefined);}}
     const growthMarks=page.locator('#growth-markers [data-kind]');assert.equal(await growthMarks.count(),growth.markers.length);for(let i=0;i<growth.markers.length;i++){assert.equal(Number(await growthMarks.nth(i).getAttribute('data-n')),growth.markers[i].n);assert.match(await growthMarks.nth(i).innerText(),/관측|후보/);}
     assert((await page.locator('#growth table caption').textContent()).includes('기준 챔피언 평균의 신뢰구간이 아닙니다'));
     assert.equal(await page.locator('#growth-charts [data-growth-series="champion"]').count(),growth.points.filter(p=>p.visible).length);
     check(mode+' independent real growth source exact means N and observed markers, delta uncertainty labeled separately');
    }

    const headline=page.locator('#headline-stats [data-n]').first();assert.equal(Number(await headline.getAttribute('data-n')),expected.summary.n);assert.equal(Number(await headline.getAttribute('data-wins')),expected.summary.wins);
    assert((await page.locator('#statistics-source').innerText()).includes(stats.source.patch));
    assert((await page.locator('#statistics-provenance').textContent()).includes(stats.source.dataset_digest));
    const allRows=page.locator('#power-table tr[data-series="all"]');assert.equal(await allRows.count(),expected.duration.length);
    for(let i=0;i<expected.duration.length;i++){assert.equal(Number(await allRows.nth(i).getAttribute('data-n')),expected.duration[i].n);assert.equal(Number(await allRows.nth(i).getAttribute('data-wins')),expected.duration[i].wins);const bin=expected.duration[i],text=await allRows.nth(i).textContent();if(bin.win_rate_pct!==null)assert(text.includes(bin.win_rate_pct.toFixed(1)+'%'));if(bin.ci_low_pct!==null)assert(text.includes(bin.ci_low_pct.toFixed(1)+'%')&&text.includes(bin.ci_high_pct.toFixed(1)+'%'));}
    const opponent=Object.keys(expected.opponents)[0];assert(opponent);
    const records=await page.locator('#opponent-table-body tr').evaluateAll(nodes=>nodes.map(n=>({id:n.dataset.champion,n:Number(n.dataset.n),wins:Number(n.dataset.wins),perspective:n.dataset.perspective})));
    assert.equal(records.length,Object.keys(expected.opponents).length);
    for(const [i,row]of records.entries()){assert.equal(row.n,expected.opponents[row.id].summary.n);assert.equal(row.wins,expected.opponents[row.id].summary.wins);assert.equal(row.perspective,'A');if(i)assert(records[i-1].n>=row.n);}
    await page.locator('#opponent-search').fill('zzzz-no-such-opponent');assert.equal(await page.locator('#opponent-table-body tr').count(),0);await page.locator('#opponent-empty').waitFor({state:'visible'});
    await page.locator('#opponent-search').fill('');await page.locator('#opponent-sort').selectOption('rate-asc');await page.locator('#opponent-sort-warning').waitFor({state:'visible'});
    const rates=await page.locator('#opponent-table-body tr').evaluateAll(nodes=>nodes.map(n=>Number(n.dataset.wins)/Number(n.dataset.n)));for(let i=1;i<rates.length;i++)assert(rates[i]>=rates[i-1]);
    await page.locator('#opponent-sort').selectOption('rate-desc');const reversedRates=await page.locator('#opponent-table-body tr').evaluateAll(nodes=>nodes.map(n=>Number(n.dataset.wins)/Number(n.dataset.n)));for(let i=1;i<reversedRates.length;i++)assert(reversedRates[i]<=reversedRates[i-1]);
    await page.locator('#opponent-sort').selectOption('sample');await page.locator('#opponent-table-body button[data-champion="'+opponent+'"]').click();assert.equal(await page.locator('#context-opponent').inputValue(),opponent);assert.equal(await page.locator('#opponent-position').inputValue(),'BOTTOM');
    for(const phase of ['lane','operations','fight']){const text=await page.locator('[data-matchup-phase='+phase+']').innerText();for(const word of ['자료 부족','이유','행동','재검토 조건'])assert(text.includes(word));}
    check(mode+' actual opponent records, sample and winrate sorting warning, noresults, selection sync and three honest matchup phase cards');

    await page.locator('#context-opponent').selectOption(opponent);await page.locator('#opponent-position').selectOption('BOTTOM');
    const opponentRows=page.locator('#power-table tr[data-series="opponent"]');assert.equal(await opponentRows.count(),expected.opponents[opponent].duration.length);
    for(let i=0;i<expected.opponents[opponent].duration.length;i++){assert.equal(Number(await opponentRows.nth(i).getAttribute('data-wins')),expected.opponents[opponent].duration[i].wins);}
    assert.equal(await page.locator('#power-chart [data-n]').evaluateAll(nodes=>nodes.filter(n=>Number(n.dataset.n)<100).length),0);
    if(expected.duration.every(b=>!b.drawable))assert.equal(await page.locator('#power-chart polyline,#power-chart path[data-series]').count(),0,'insufficient bins cannot become a curve');
    assert.match(await page.locator('#baseline-note').innerText(),/REFERENCE_ONLY|작성된/);assert((await page.locator('#official-skills').innerText()).includes('Q'));
    check(mode+' real patch digest exact N wins duration opponent A-perspective and insufficient curves');
    await page.locator('#ally-support').selectOption('Lux');await page.locator('#enemy-support').selectOption('Nautilus');await page.locator('#gameplan-context').click();await page.locator('#handoff-preview').waitFor({state:'visible'});const contextIntent=await page.evaluate(()=>JSON.parse(decodeURIComponent(location.hash.slice(9))));assert.equal(contextIntent.champion,'Caitlyn');assert.equal(contextIntent.position,'BOTTOM');assert.equal(contextIntent.opponent,opponent);assert.equal(contextIntent.opponent_position,'BOTTOM');assert.equal(contextIntent.ally_support,'Lux');assert.equal(contextIntent.enemy_support,'Nautilus');const back=await page.locator('#handoff-return').getAttribute('href');const returnState=JSON.parse(decodeURIComponent(new URL(back,page.url()).hash.slice(7)));assert.equal(returnState.champion,'Caitlyn');assert.equal(returnState.opponent,opponent);await page.locator('#handoff-return').click();await page.locator('#champion-detail').waitFor({state:'visible'});assert.equal(await page.locator('#context-opponent').inputValue(),opponent);assert.equal(await page.locator('#ally-support').inputValue(),'Lux');check(mode+' real context CTA retains own opponent roles and supports and returns to detail');
    await page.evaluate(()=>{localStorage.setItem('lol-coach-champion-recent-v1','{corrupt');sessionStorage.setItem('lol-coach-gameplan-draft-v1','{corrupt');});
    await page.goto(url('champions.html')+'#state=%ZZ');await page.locator('#champion-grid .champion-card').first().waitFor();assert(await page.locator('#recent-section').isHidden());
    check(mode+' malformed hash and corrupt storage recover');
    // An existing ten-pick plan is read first; opening/canceling is read-only.
    await page.goto(url('loading.html'));await page.locator('#analyze:enabled').waitFor();await page.locator('#example-0').click();await page.locator('#analyze').click();await page.locator('.plan-title').waitFor();
    const oldHash=new URL(page.url()).hash,oldInput=await page.evaluate(()=>JSON.parse(decodeURIComponent(location.hash.slice(6))).input);
    const oldStored=await page.evaluate(()=>sessionStorage.getItem('lol-coach-loading-plan-v1'));
    const intent={champion:'Malphite',position:'TOP',return_state:{target:'champion.html',champion:'Malphite',position:'TOP'}};
    const handoff=url('loading.html')+'#handoff='+encodeURIComponent(JSON.stringify(intent));
    await page.goto(handoff);await page.locator('#handoff-preview').waitFor({state:'visible'});
    assert.equal(await page.evaluate(()=>sessionStorage.getItem('lol-coach-loading-plan-v1')),oldStored);
    await page.locator('#handoff-cancel').click();assert.equal(new URL(page.url()).hash,new URL(handoff).hash);assert.equal(await page.evaluate(()=>sessionStorage.getItem('lol-coach-loading-plan-v1')),oldStored);
    await page.goto(handoff);await page.locator('#handoff-preview').waitFor({state:'visible'});
    await page.locator('input[data-handoff-replace]').check();await page.locator('#handoff-apply').click();await page.locator('.plan-title').waitFor();
    assert(new URL(page.url()).hash.startsWith('#plan='));
    const applied=await page.evaluate(()=>JSON.parse(decodeURIComponent(location.hash.slice(6))).input);
    assert.equal(applied.own_champion,'Malphite');assert.equal(applied.own_position,'TOP');
    for(const team of ['allies','enemies'])for(let i=0;i<5;i++){if(team==='allies'&&i===0)assert.deepEqual(applied[team][i],{champion:'Malphite',position:'TOP'});else assert.deepEqual(applied[team][i],oldInput[team][i]);}
    for(const key of ['scenario','planning','preferences','side','patch'])assert.deepEqual(applied[key],oldInput[key]);
    const appliedHash=new URL(page.url()).hash;await page.reload();await page.locator('.plan-title').waitFor();assert.equal(new URL(page.url()).hash,appliedHash);
    for(const phase of ['lane','operations','fight']){assert.equal(await page.locator('[data-basic-phase='+phase+'] .plan-basic-actions li').count(),5);assert(await page.locator('[data-basic-coaching='+phase+'] p').count()>0);}
    check(mode+' explicit preview cancel, confirmed one-slot replacement preserves nine other picks and planning, complete hash refresh three phases five actions prose');
    // A fresh shared #plan must seed persistence before a full champion-page roundtrip.
    const restoredPage=await makePage(1440,1000);await restoredPage.goto(url('loading.html')+oldHash);await restoredPage.locator('.plan-title').waitFor();
    await restoredPage.goto(url('champion.html')+state('Ezreal','BOTTOM'));await restoredPage.locator('#champion-detail').waitFor({state:'visible'});await restoredPage.locator('#gameplan-own').click();await restoredPage.locator('#handoff-preview').waitFor({state:'visible'});
    assert.equal(await restoredPage.locator('select[data-handoff-target]').count(),0);const restored=await restoredPage.evaluate(()=>JSON.parse(decodeURIComponent(sessionStorage.getItem('lol-coach-gameplan-draft-v1').slice(7))));assert.deepEqual(restored.input,oldInput);
    const cancellationSnapshot=await restoredPage.evaluate(()=>({url:location.href,plan:sessionStorage.getItem('lol-coach-loading-plan-v1'),draft:sessionStorage.getItem('lol-coach-gameplan-draft-v1')}));await restoredPage.locator('#handoff-cancel').click();assert.deepEqual(await restoredPage.evaluate(()=>({url:location.href,plan:sessionStorage.getItem('lol-coach-loading-plan-v1'),draft:sessionStorage.getItem('lol-coach-gameplan-draft-v1')})),cancellationSnapshot);
    await restoredPage.goto(url('loading.html')+oldHash);await restoredPage.locator('.plan-title').waitFor();await restoredPage.locator('[data-plan-area="lane"]').click();await restoredPage.locator('summary').filter({hasText:'상황 바꾸기'}).click();await restoredPage.locator('[data-coach-focus="quick-KEY_SPENT"]').click();
    await restoredPage.waitForFunction(()=>JSON.parse(decodeURIComponent(location.hash.slice(6))).input.scenario?.overrides.enemy_key==='SPENT');await restoredPage.goBack();await restoredPage.waitForFunction(()=>JSON.parse(decodeURIComponent(location.hash.slice(6))).detail===null);
    assert.equal(await restoredPage.evaluate(()=>JSON.parse(decodeURIComponent(location.hash.slice(6))).input.scenario.overrides.enemy_key),'SPENT');await restoredPage.close();
    check(mode+' fresh shared plan survives champion CTA and cancel; Back retains newly edited scenario');

    await page.evaluate(()=>{sessionStorage.removeItem('lol-coach-loading-plan-v1');sessionStorage.removeItem('lol-coach-gameplan-draft-v1');});
    await page.goto(url('champions.html'));await page.locator('#champion-grid .champion-card').first().waitFor();
    await page.goto(handoff);await page.locator('#handoff-preview').waitFor({state:'visible'});
    await page.locator('select[data-handoff-target]').selectOption('allies:0');await page.locator('#handoff-apply').click();
    assert(new URL(page.url()).hash.startsWith('#draft='));assert(await page.locator('#loading-results').isHidden());
    await page.reload();await page.locator('#analyze:enabled').waitFor();assert.match(await page.locator('#pick-ALLY-0').inputValue(),/Malphite|말파이트/);const restoredDraft=await page.evaluate(()=>JSON.parse(decodeURIComponent(location.hash.slice(7))));assert.equal(restoredDraft.input.allies[0].champion,'Malphite');assert(await page.locator('#loading-results').isHidden());
    for(const id of ['#pick-ALLY-1','#pick-ALLY-2','#pick-ALLY-3','#pick-ALLY-4','#pick-ENEMY-0','#pick-ENEMY-1','#pick-ENEMY-2','#pick-ENEMY-3','#pick-ENEMY-4'])assert.equal(await page.locator(id).inputValue(),'');
    check(mode+' explicit empty-draft target persists partial without fabricating missing picks');
   }
   await page.close();
   if(mode==='pc'&&process.env.CHAMPION_SCREENS_ONLY!=='1'){
    const fixture=JSON.parse(fs.readFileSync(process.env.CHAMPION_PC_FIXTURE,'utf8'));
    const blocked=await makePage(1440,1000);await blocked.addInitScript(()=>{Storage.prototype.getItem=function(key){return key==='lol-coach-dev-token'?'isolated-protocol-fixture':null;};Storage.prototype.setItem=function(){throw Error('isolated storage denial');};});
    await blocked.route('**/dev/v1/pregame/pc-status',route=>route.fulfill({json:fixture}));await blocked.goto(url('loading.html')+'#handoff='+encodeURIComponent(JSON.stringify({champion:'Caitlyn',position:'BOTTOM'})));await blocked.locator('#handoff-preview').waitFor({state:'visible'});await blocked.locator('select[data-handoff-target]').selectOption('allies:3');await blocked.locator('#pc-import').click();await blocked.waitForFunction(()=>location.hash.startsWith('#plan='));
    assert(await blocked.locator('#handoff-preview').isHidden());const importedHash=new URL(blocked.url()).hash;await blocked.locator('#handoff-apply').evaluate(el=>el.click());assert.equal(new URL(blocked.url()).hash,importedHash);assert.match(await blocked.locator('#pick-ALLY-0').inputValue(),/Fiora|피오라/);assert.match(await blocked.locator('#pick-ENEMY-0').inputValue(),/Malphite|말파이트/);await blocked.close();
    const late=await makePage(1440,1000);await late.addInitScript(()=>sessionStorage.setItem('lol-coach-dev-token','isolated-protocol-fixture'));let held,announce;const pending=new Promise(resolve=>announce=resolve);await late.route('**/dev/v1/pregame/pc-status',route=>{held=route;announce();});await late.goto(url('loading.html'));await late.locator('#analyze:enabled').waitFor();await late.locator('#pc-import').click();await pending;await late.locator('#example-0').click();const newer=await late.locator('#pick-ALLY-0').inputValue();await held.fulfill({json:fixture});await late.locator('#pc-import:enabled').waitFor();assert.equal(await late.locator('#pick-ALLY-0').inputValue(),newer);assert(!new URL(late.url()).hash.startsWith('#plan='));await late.close();
    check('PC isolated protocol import invalidates old preview with denied storage; late import cannot overwrite newer picks');
    const account=await makePage(1440,1000);await account.addInitScript(()=>sessionStorage.setItem('lol-coach-dev-token','isolated-account-protocol-fixture'));
    const profileFixture={format:'lol-coach-account-profile-v1',riot_id:'isolated-fixture#KR1',region:'KR',retrieved_at:'2026-10-25T00:00:00Z',rank:null,recent_matches:[],champions:[{champion:'Caitlyn',sample_n:7,win_rate:71.4,kda:3},{champion:'케이틀린',sample_n:1,win_rate:100,kda:2}],statistics:{sample_n:8,queue_id:420,win_rate:75,kda:3,window_start:1,window_end:2},omitted_matches:0};
    await account.route('**/dev/v1/account/lookup',route=>route.fulfill({json:{status:'CONNECTED',profile:profileFixture}}));await account.goto(url('index.html'));await account.locator('#account-submit').waitFor();await account.locator('#riot-id').fill('isolated-fixture#KR1');await account.locator('#account-submit').click();await account.locator('.record-champion-link').first().waitFor({state:'visible'});
    const links=await account.locator('.record-champion-link').evaluateAll(nodes=>nodes.map(n=>n.href));assert.equal(links.length,2);assert.deepEqual(JSON.parse(decodeURIComponent(new URL(links[0]).hash.slice(7))),{champion:'Caitlyn'});assert.deepEqual(JSON.parse(decodeURIComponent(new URL(links[1]).hash.slice(7))),{query:'케이틀린'});assert(new URL(links[1]).pathname.endsWith('/champions.html'));
    await account.locator('.record-champion-link').first().click();await account.locator('#champion-detail').waitFor({state:'visible'});assert.equal(await account.locator('#own-position').inputValue(),'');assert(!account.url().includes('isolated-fixture'));await account.locator('#own-position').selectOption('BOTTOM');const commonN=await account.locator('#headline-stats [data-n]').first().getAttribute('data-n');const commonStats=await account.evaluate(async()=>await(await fetch('./champion-stats.json')).json());assert.equal(Number(commonN),commonStats.champions.Caitlyn.positions.BOTTOM.summary.n);assert.notEqual(Number(commonN),profileFixture.champions[0].sample_n);await account.close();
    check('PC isolated account DOM link hands off champion identity only, requires own role, keeps personal sample separate from common statistics');

   }
  }
  // Real public artifacts: eight page states plus the change dialog, desktop/mobile.
  for(const [device,width,height] of [['mobile',390,844],['desktop',1440,1000]]){
   const page=await makePage(width,height),base=process.env.CHAMPION_WEB+'/lol-coach/';
   for(const [name,route,ready] of [['index','index.html','#account-submit'],['champions','champions.html','#champion-grid .champion-card'],['champion','champion.html'+state(),'#champion-detail'],['loading','loading.html','#analyze:enabled'],['game-info','game-info.html','#compare-items:enabled'],['review','index.html#review-card','#review-card'],['directions','directions.html','#result'],['status','status.html','#status-items section']]){
    await page.goto(base+route);await page.locator(ready).first().waitFor({state:'visible'});
    if(name==='loading'){await page.locator('#example-0').click();await page.locator('#analyze').click();await page.locator('.plan-title').waitFor();}
    await noOverflow(page,device+' '+name);await capture(page,device+'-'+name);
    if(device==='mobile'){await page.setViewportSize({width:320,height:740});await noOverflow(page,'320 '+name);await page.setViewportSize({width,height});}
   }
   await page.goto(base+'champion.html'+state());await page.locator('#champion-detail').waitFor({state:'visible'});await page.locator('#change-champion').click();await page.locator('#champion-dialog[open]').waitFor();await page.locator('#dialog-search').fill('아리');
   await noOverflow(page,device+' dialog');await capture(page,device+'-champion-dialog');
   const card=page.locator('#dialog-grid [data-champion="Ahri"]');await card.focus();await page.keyboard.press('Enter');assert.equal(await card.getAttribute('aria-pressed'),'true');
   assert(await page.locator('#champion-dialog').evaluate(dialog=>dialog.contains(document.activeElement)));
   await page.locator('#dialog-apply').focus();await page.keyboard.press('Tab');assert.equal(await page.evaluate(()=>document.activeElement.id),'dialog-close');await page.keyboard.press('Shift+Tab');assert.equal(await page.evaluate(()=>document.activeElement.id),'dialog-apply');
   if(device==='mobile'){await page.setViewportSize({width:320,height:740});await noOverflow(page,'320 dialog');await page.setViewportSize({width,height});}
   if(device==='mobile'){const box=await page.locator('#dialog-cancel').boundingBox();await page.touchscreen.tap(box.x+box.width/2,box.y+box.height/2);}else await page.keyboard.press('Escape');
   assert.equal(await page.evaluate(()=>document.activeElement.id),'change-champion');
   check(device+' dialog keyboard/touch selection focus restore');
   if(device==='desktop'){await page.evaluate(()=>document.documentElement.style.zoom='2');await noOverflow(page,'desktop 200 percent content zoom');await page.locator('#change-champion').click();await page.locator('#champion-dialog[open]').waitFor();await noOverflow(page,'desktop 200 percent dialog');await page.keyboard.press('Escape');}
   await page.close();
  }

  assert.equal(result.screenshots.length,18,'eight pages plus dialog on desktop and mobile');
  assert.deepEqual(result.external_requests,[],'outgoing requests are forbidden');
  assert.deepEqual(result.browser_errors,[],'JavaScript errors');
  assert.deepEqual(result.console_errors,[],'browser console errors');
  assert.deepEqual(result.http_errors,[],'HTTP errors');
  result.passed=true;
 }catch(error){result.failure=String(error.stack||error);result.failure_context=[];for(const context of browser.contexts())for(const page of context.pages())result.failure_context.push({url:page.url(),body:await page.locator('body').innerText().catch(()=>'<unavailable>')});throw error;}
 finally{await browser.close();fs.writeFileSync(process.env.CHAMPION_OUT+'/browser-result.json',JSON.stringify(result,null,2));}
})().catch(e=>{console.error(e.stack||e);process.exitCode=1});
'''


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def copyfile(self, source, outputfile):
        try:
            super().copyfile(source, outputfile)
        except (BrokenPipeError, ConnectionResetError):
            # Deliberate page navigation may cancel an in-flight local sprite fetch.
            pass


def source_hashes():
    """Bind receipts to every public input and relevant runner/server source."""
    from scripts.build_directions_web import FILES
    names = {'web_r4/' + name for name in FILES}
    names.update(('scripts/browser_champions.py', 'scripts/build_directions_web.py',
                  'scripts/launch_pc.py', 'coach_v1/pregame_server.py',
                  'tests_pregame/test_champion_publication.py', 'contracts/information-architecture-v1.md'))
    matrix = 'docs/gameplan-content/frontend-v2-feature-matrix.json'
    if (ROOT / matrix).is_file():
        names.add(matrix)
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(names)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--screens-only', action='store_true', help='Capture 18 real shipped UI states; skip interactive regression flows')
    args = parser.parse_args(argv)
    output = (args.output or ROOT / 'evidence/actual-evidence/frontend-v2' /
              ('browser-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))).resolve()
    output.mkdir(parents=True, exist_ok=True)
    from scripts.build_directions_web import build
    from scripts.launch_pc import create_server
    before = source_hashes()
    receipt = {'passed': False, 'mode': 'screens-only' if args.screens_only else 'full',
               'started_at': datetime.now(timezone.utc).isoformat(),
               'source_sha256': before,
               'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
               'scope': 'Real shipped Chromium DOM on isolated PC and public subpath; PC import protocol fixtures only; no actual player, Windows LCU, deployment, or provider proof'}
    with tempfile.TemporaryDirectory(prefix='champion-browser-') as temp:
        temporary = Path(temp)
        manifest = build(temporary / 'public/lol-coach')
        pc = create_server(temporary / 'private', port=0)
        public = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(temporary / 'public')))
        servers = [pc, public]
        try:
            for server in servers:
                threading.Thread(target=server.serve_forever, daemon=True).start()
            example = json.loads(subprocess.check_output(['node', '-e',
                "const E=require('./web_r4/loading-engine.js'),C=require('./web_r4/loading-data.json');console.log(JSON.stringify(E.exampleInput(C,1)))"], cwd=ROOT, text=True))
            pc_input = dict(phase='PRE_GAME', my_champion=example['own_champion'],
                            my_position=example['own_position'], patch=example['patch'],
                            slots=[dict(side=side, slot=index + 1, **pick)
                                   for side, team in [('ALLY', 'allies'), ('ENEMY', 'enemies')]
                                   for index, pick in enumerate(example[team])])
            fixture = temporary / 'isolated-pc-protocol.json'
            fixture.write_text(json.dumps(dict(connection=dict(status='CONNECTED', phase='ChampSelect', input=pc_input))))
            (output / 'browser-result.json').unlink(missing_ok=True)
            script = temporary / 'champions.cjs'
            script.write_text(BROWSER, encoding='utf-8')
            env = dict(os.environ, CHAMPION_PC='http://127.0.0.1:' + str(pc.server_port),
                       CHAMPION_WEB='http://127.0.0.1:' + str(public.server_port),
                       CHAMPION_OUT=str(output), CHAMPION_PC_FIXTURE=str(fixture), CHAMPION_SCREENS_ONLY=str(int(args.screens_only)),
                       NODE_PATH=os.environ.get('NODE_PATH', '/opt/codex/cua_node/lib/node_modules'))
            if 'CHROMIUM_EXECUTABLE' not in env and Path('/usr/bin/chromium').exists():
                env['CHROMIUM_EXECUTABLE'] = '/usr/bin/chromium'
            run = subprocess.run(['node', str(script)], cwd=ROOT, env=env, text=True, capture_output=True, timeout=300)
            (output / 'browser.log').write_text(run.stdout + run.stderr, encoding='utf-8')
            if (output / 'browser-result.json').exists():
                receipt.update(json.loads((output / 'browser-result.json').read_text()))
            receipt['export_sha256'] = manifest['sha256']
            receipt['actual_user_approvals_created'] = len(pc.research.list())
            receipt['source_unchanged_during_run'] = before == source_hashes()
            receipt['passed'] = bool(receipt.get('passed')) and run.returncode == 0 and receipt['source_unchanged_during_run'] and receipt['actual_user_approvals_created'] == 0
            receipt['screenshot_sha256'] = {item['file']: hashlib.sha256((output / item['file']).read_bytes()).hexdigest() for item in receipt.get('screenshots', [])}
            receipt['finished_at'] = datetime.now(timezone.utc).isoformat()
            (output / 'runner.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            print(json.dumps({'passed': receipt['passed'], 'evidence_directory': str(output), 'screenshots': len(receipt['screenshot_sha256'])}))
            if not receipt['passed']:
                print(run.stderr, file=sys.stderr)
                if not receipt['source_unchanged_during_run']:
                    print('Source changed during run; repeat after edits settle.', file=sys.stderr)
            return 0 if receipt['passed'] else 1
        finally:
            for server in servers:
                server.shutdown()
                server.server_close()


if __name__ == '__main__':
    raise SystemExit(main())

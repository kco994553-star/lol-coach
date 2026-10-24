
const fs=require('node:fs'),assert=require('node:assert/strict'),{chromium}=require('playwright');
(async()=>{
 const E=require(process.cwd()+'/web_r4/loading-engine.js'),P=require(process.cwd()+'/web_r4/loading-presentation.js'),c=require(process.cwd()+'/web_r4/loading-data.json');c.coaching_knowledge=require(process.cwd()+'/web_r4/loading-knowledge.json');
 const x=E.exampleInput(c,0),roles=['TOP','JUNGLE','MID','BOTTOM','SUPPORT'];x.allies=['Ornn','Vi','Ahri','Kaisa','Nautilus'].map((champion,i)=>({champion,position:roles[i]}));x.enemies=['Renekton','Graves','Orianna','Ziggs','Karma'].map((champion,i)=>({champion,position:roles[i]}));x.own_champion='Kaisa';x.own_position='BOTTOM';
 const expected=P.project(E.analyze(x,c)),errors=[],results=[];
 const b=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_EXECUTABLE||'/usr/bin/chromium',args:['--no-sandbox'],...(process.env.PUBLIC_PROXY?{proxy:{server:process.env.PUBLIC_PROXY}}:{})});
 for(const width of [1440,390,320]){
  const p=await b.newPage({viewport:{width,height:950},reducedMotion:'reduce'});p.on('pageerror',e=>errors.push(e.message));await p.goto(process.env.ROOT+'/lol-coach/loading.html'+P.encode(x));await p.locator('.plan-title').waitFor();
  for(const area of ['lane','operations','fight']){
   const base=p.locator('[data-basic-phase='+area+']'),prose=base.locator('[data-basic-coaching]');
   assert.equal(await base.locator('[data-basic-action-kind]').count(),5);assert.deepEqual(await prose.locator('p').allTextContents(),expected.cards.find(a=>a.id===area).explanation);
   assert.equal(await prose.locator('h4').innerText(),{lane:'라인전을 풀어가는 방법',operations:'운영을 풀어가는 방법',fight:'한타를 풀어가는 방법'}[area]);
   const style=await prose.locator('p').first().evaluate(n=>{const s=getComputedStyle(n);return {size:parseFloat(s.fontSize),line:parseFloat(s.lineHeight),color:s.color}});assert(style.size>=16&&style.line>=28);assert.equal(style.color,'rgb(237, 242, 250)');
   await base.screenshot({path:process.env.OUT+'/narrative-'+width+'-'+area+'.png'});await prose.locator('h4').scrollIntoViewIfNeeded();await p.evaluate(()=>document.activeElement?.blur());await p.screenshot({path:process.env.OUT+'/viewport-'+width+'-'+area+'.png'});
   const more=base.locator('[data-plan-more]');assert(await more.isVisible());await more.focus();await p.keyboard.press('Enter');await p.locator('.plan-detail-title').waitFor();
   assert.deepEqual(await p.locator('.plan-detail [data-coaching-explanation] p').allTextContents(),expected.cards.find(a=>a.id===area).explanation);
   await p.locator('details[id$="-other-conditions-'+area+'"]>summary').click();assert(await p.locator('[data-condition-response=WINDOW_MISSED]').isVisible());
   assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await p.reload();await p.locator('.plan-detail-title').waitFor();await p.locator('[data-coach-focus=close-detail]').click();
  }
  results.push({width,defaultActions:15,paragraphsMatch:true,keyboardDisclosure:true,reload:true,readable:true,overflow:false});await p.close();
 }
 assert.deepEqual(errors,[]);fs.writeFileSync(process.env.OUT+'/narrative-result.json',JSON.stringify({results,errors,input:x},null,2));await b.close();
})().catch(e=>{console.error(e);process.exit(1)});

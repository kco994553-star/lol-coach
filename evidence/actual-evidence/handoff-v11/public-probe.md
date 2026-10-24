
const fs=require('node:fs'),assert=require('node:assert/strict'),{chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,proxy:{server:process.env.HTTPS_PROXY||'http://proxy:8080'},executablePath:process.env.CHROMIUM_EXECUTABLE||'/usr/bin/chromium',args:['--no-sandbox']});
 const results=[],errors=[];
 for(const width of [1440,390,320]){
  const p=await browser.newPage({viewport:{width,height:950},reducedMotion:'reduce'});p.on('pageerror',e=>errors.push(e.message));
  await p.goto(process.env.ROOT+'/lol-coach/loading.html');await p.locator('#analyze:enabled').waitFor();await p.locator('#example-0').click();await p.locator('#analyze').click();await p.locator('.plan-title').waitFor();
  assert.equal(await p.locator('.plan-overview-comparison tbody tr').count(),4,'four basic comparison criteria without disclosure');
  for(const area of ['lane','operations','fight']){
   const basic=p.locator('[data-basic-phase='+area+']');assert(await basic.isVisible(),area+' basic visible');assert.equal(await basic.locator('[data-basic-action-kind]').count(),5);
   assert(await basic.locator('.plan-coaching-explanation p').count()>0);assert(await basic.locator('.plan-coaching-explanation').isVisible());
   const text=await basic.locator('.plan-basic-action-text').allTextContents();
   await basic.locator('[data-plan-area]').focus();await p.keyboard.press('Enter');await p.locator('.plan-detail-title').waitFor();
   const titleBox=await p.locator('.plan-detail-title').boundingBox();assert(titleBox.y>=0&&titleBox.y+titleBox.height<=950,'focused detail heading is in viewport');
   assert.deepEqual(await p.locator('.plan-detail .coach-action-text').evaluateAll(ns=>ns.map(n=>Array.from(n.childNodes).filter(c=>c.nodeType===3).map(c=>c.textContent).join(''))),text);
   assert.deepEqual(await p.locator('.plan-detail .plan-coaching-explanation p').allTextContents(),await basic.locator('.plan-coaching-explanation p').allTextContents());
   await p.locator('[data-coach-focus=close-detail]').click();assert.equal(await p.evaluate(()=>document.activeElement.dataset.planArea),area);
  }
  const boxes=await p.locator('.plan-basic-phase').evaluateAll(ns=>ns.map(n=>{const r=n.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width};}));
  if(width===1440){assert(Math.abs(boxes[0].y-boxes[2].y)<2);assert(boxes[2].x>boxes[1].x&&boxes[1].x>boxes[0].x);}else assert(boxes[2].y>boxes[1].y&&boxes[1].y>boxes[0].y);
  assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  await p.locator('[data-plan-area=lane]').click();await p.locator('.plan-detail details.coach-details[id$="-conditions"]').evaluate(e=>e.open=true);
  await p.locator('[data-coach-focus=planning-ally_followup]').selectOption('UNAVAILABLE');
  await p.waitForFunction(()=>document.querySelector('#loading-coach').getAttribute('aria-busy')==='false');
  assert.match(await p.locator('.plan-detail [data-action-kind=TRADE]').innerText(),/호응/);
  assert.equal(await p.locator('.plan-detail .coach-action-text').nth(2).textContent(),await p.locator('[data-basic-phase=lane] .plan-basic-action-text').nth(2).textContent());
  await p.reload();await p.locator('.plan-detail-title').waitFor();assert.match(await p.locator('.plan-detail [data-action-kind=TRADE]').innerText(),/호응/);
  await p.locator('.plan-detail details.coach-details[id$="-conditions"]').evaluate(e=>e.open=true);await p.locator('[data-coach-focus=reset-scenario]').click();await p.waitForFunction(()=>document.querySelector('#loading-coach').getAttribute('aria-busy')==='false');
  assert.equal(await p.locator('[data-coach-focus=planning-ally_followup]').inputValue(),'UNCONFIRMED');await p.locator('[data-coach-focus=close-detail]').click();
  const before=await p.locator('.plan-overview-comparison').innerText();await p.reload();await p.locator('.plan-title').waitFor();assert.equal(await p.locator('.plan-overview-comparison').innerText(),before);
  await p.screenshot({path:process.env.OUT+'/v11-'+width+'.png',fullPage:true});results.push({width,basicPhases:3,actions:15,comparison:4,keyboardDetails:true,refresh:true});await p.close();
 }
 assert.deepEqual(errors,[]);fs.writeFileSync(process.env.OUT+'/v11-result.json',JSON.stringify({results,errors},null,2));await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});

'use strict';
const {chromium}=require('playwright'),fs=require('fs'),path=require('path');
const out=process.env.STATS_EVIDENCE_DIR,checks=[],errors=[];
function check(id,passed){checks.push({id,passed:!!passed});if(!passed)throw Error(id);}
(async()=>{let browser;try{
 browser=await chromium.launch({executablePath:process.env.CHROMIUM_EXECUTABLE||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1280,height:900}});page.on('pageerror',e=>errors.push(e.message));
 await page.goto(process.env.WORKBENCH_URL+'/statistics');await page.locator('#stats-token').fill(fs.readFileSync(process.env.WORKBENCH_TOKEN_FILE,'utf8').trim());await page.locator('#stats-login button').click();await page.waitForSelector('#stats-body:not([hidden])');await page.waitForLoadState('networkidle');
 check('high-default',await page.locator('#stats-high').inputValue()==='CHALLENGER');
 await page.locator('#stats-own').selectOption('GOLD');await page.waitForLoadState('networkidle');
 await page.screenshot({path:path.join(out,'before-graph-check.png'),fullPage:true}); const graphDetails={high:await page.locator('#stats-high-graph').innerText(),own:await page.locator('#stats-own-graph').innerText(),counts:[await page.locator('#stats-high-graph svg').count(),await page.locator('#stats-own-graph svg').count()]}; fs.writeFileSync(path.join(out,'graph-details.json'),JSON.stringify(graphDetails)); check('two-tier-graphs',graphDetails.counts.every(n=>n===1));
 check('sample-progress',await page.locator('#stats-high-progress').innerText().then(s=>s.includes('CHALLENGER')&&s.includes('실제 0경기')&&s.includes('합성 24경기 TEST')));
 let heldResolve,releaseOld,holdNext=true;const held=new Promise(resolve=>{heldResolve=resolve;});
 await page.route('**/pregame/power-view',async route=>{if(!holdNext){await route.continue();return;}holdNext=false;await new Promise(resolve=>{releaseOld=resolve;heldResolve();});await route.abort('failed');});
 await page.locator('#stats-own').selectOption('');await held;await page.locator('#stats-own').selectOption('GOLD');await page.waitForFunction(()=>document.querySelectorAll('#stats-own-graph svg').length===1);releaseOld();await page.waitForLoadState('networkidle');check('stale-failure-preserves-current-graphs',await page.locator('#stats-own-graph svg').count()===1);await page.unroute('**/pregame/power-view');
 await page.screenshot({path:path.join(out,'desktop.png'),fullPage:true});
 await page.setViewportSize({width:390,height:844});await page.screenshot({path:path.join(out,'mobile-before-check.png'),fullPage:true});fs.writeFileSync(path.join(out,'overflow.json'),JSON.stringify(await page.evaluate(()=>[...document.querySelectorAll('body *')].filter(n=>n.getBoundingClientRect().right>window.innerWidth+1).slice(0,15).map(n=>({tag:n.tagName,id:n.id,class:n.className?.baseVal||n.className,right:n.getBoundingClientRect().right,text:n.textContent.slice(0,80)})))));const viewportInfo=await page.evaluate(()=>({scroll:document.documentElement.scrollWidth,inner:window.innerWidth,client:document.documentElement.clientWidth,body:document.body.scrollWidth}));fs.writeFileSync(path.join(out,'viewport.json'),JSON.stringify(viewportInfo));check('mobile-no-overflow',viewportInfo.scroll<=viewportInfo.inner);
 await page.screenshot({path:path.join(out,'mobile.png'),fullPage:true});
 await page.locator('#stats-own').selectOption('');await page.waitForLoadState('networkidle');check('missing-user-tier-unknown',await page.locator('#stats-own-graph').innerText().then(s=>s.includes('UNKNOWN')));
 await page.locator('#stats-logout').click();check('logout-hides-data',await page.locator('#stats-body').isHidden());check('no-browser-errors',errors.length===0);
 fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify({passed:true,checks,errors,coaching_accuracy:null}));
 }catch(e){fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify({passed:false,checks,errors,error:e.message}));process.exitCode=1;}finally{if(browser)await browser.close();}})();

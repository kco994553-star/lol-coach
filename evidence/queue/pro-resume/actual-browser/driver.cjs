const {chromium}=require('playwright'),fs=require('fs');
const token=fs.readFileSync('/workspace/scratch/pro-production/private/token.txt','utf8').trim();
const out='/workspace/scratch/pro-production',checks=[],errors=[];
function check(id,value,detail){checks.push({id,passed:!!value,detail});if(!value)throw Error(id);}
(async()=>{let browser;try{
 browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1600,height:1000}});page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8137/statistics');await page.locator('#stats-token').fill(token);await page.locator('#stats-login button').click();
 await page.waitForFunction(()=>document.querySelectorAll('.stats-baseline-role svg').length===15,{},{timeout:90000});
 check('actual-five-roles-15-basic-curves',await page.locator('.stats-baseline-role').count()===5&&await page.locator('.stats-baseline-role svg').count()===15);
 check('actual-495-eligible-basic-points',await page.locator('.stats-baseline-point').count()===495);
 check('actual-late-gaps-withheld',await page.locator('.stats-baseline-gap').count()===120&&await page.locator('.stats-baseline-point[data-minute="34"]').count()===0);
 check('actual-patch16.20-default',await page.locator('#stats-patch').inputValue()==='16.20');
 await page.locator('#stats-role').selectOption('BOTTOM');await page.locator('#stats-champion').selectOption('Caitlyn');
 await page.waitForFunction(()=>document.querySelector('#stats-summary h2')?.textContent==='Caitlyn · BOTTOM · 16.20',{},{timeout:90000});
 check('actual-champion-three-resource-graphs',await page.locator('#stats-graphs svg').count()===3);
 check('actual-challenger-visible-points',await page.locator('.stats-point[data-origin="PRIMARY"]').count()>0);
 await page.screenshot({path:out+'/statistics-pc.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});check('actual-statistics-mobile-no-overflow',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 await page.setViewportSize({width:1600,height:1000});await page.goto('http://127.0.0.1:8137/postgame');
 await page.locator('#pm-token').fill('');const sharedTokenFallback=await page.locator('#pm-token').inputValue()==='';await page.locator('#pm-connect').click();await page.waitForFunction(()=>document.querySelectorAll('.reference-stage').length===3,{},{timeout:90000});
 check('actual-no-own-input-or-identity',await page.locator('#pm-personal').evaluate(e=>!e.open)&&sharedTokenFallback&&await page.locator('#pm-match-file').inputValue()==='');
 check('actual-87-match-real-reference',await page.locator('#pm-cases-state').innerText().then(t=>t.includes('REAL')&&t.includes('87')));
 check('actual-reference16.20-default',await page.locator('#pm-case-patch').inputValue()==='16.20');
 for(const role of ['TOP','JUNGLE','MID','BOTTOM','SUPPORT']){
  await page.locator('#pm-case-role').selectOption(role);
  check('actual-'+role+'-three-stages',await page.locator('.reference-stage').count()===3);
  check('actual-'+role+'-position-grid-and-signals',await page.locator('.reference-region').count()===27&&await page.locator('.reference-signal').count()>0);
 }
 await page.locator('#pm-case-role').selectOption('BOTTOM');await page.screenshot({path:out+'/postgame-pc.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});check('actual-postgame-mobile-no-overflow',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:out+'/postgame-mobile.png',fullPage:true});
 check('actual-browser-errors-zero',errors.length===0);
 fs.writeFileSync(out+'/actual-browser.json',JSON.stringify({passed:true,evidence_kind:'ACTUAL_REAL_ANONYMOUS_DATA_BROWSER',checks,errors,browser_version:browser.version(),own_match_count:0,USER_WEB_decisions:0,coaching_accuracy:null},null,2));
}catch(e){fs.writeFileSync(out+'/actual-browser.json',JSON.stringify({passed:false,checks,errors,error:e.message},null,2));process.exitCode=1;}finally{if(browser)await browser.close();}})();

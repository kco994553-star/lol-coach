'use strict';
// Independent DOM tests: no server, knowledge edits, approvals or credentials.
const {chromium}=require('playwright');
const fs=require('node:fs');const path=require('node:path');const crypto=require('node:crypto');
const expected=['auxiliary-table','mobile-table-access','uncertainty-n-one','test-source-provenance','ui-gate','server-gate','unrecognized-source','actual-source','unknown-without-table'];
const sources=['web_r4/pregame_outcome.js','tests_pregame/browser_outcome.cjs'];
const hashes=()=>Object.fromEntries(sources.map(name=>[name,crypto.createHash('sha256').update(fs.readFileSync(path.resolve(__dirname,'..',name))).digest('hex')]));
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_EXECUTABLE,args:['--no-sandbox']});
 try{
  const page=await browser.newPage({viewport:{width:375,height:800}});await page.setContent('<div id="host"></div>');
  const renderer=path.resolve(__dirname,'../web_r4/pregame_outcome.js');
  if(!fs.existsSync(renderer))throw new Error('Outcome table renderer is not implemented');
  await page.addScriptTag({path:renderer});
  const results=await page.evaluate(()=>{
   const host=document.getElementById('host');
   const source={sample_kind:'SYNTHETIC',provider:'SYNTHETIC',patch:'16.19',tier:'GOLD',formula_version:'WILSON_SCORE_95.v1',duration_bin_policy:{kind:'ENDING_GAME_DURATION_FLOOR_MINUTE',width_seconds:60,unit:'SECONDS'},limitations:['N_ONE_COMPUTABLE_NOT_SAMPLE_SUFFICIENCY']};
   const view={status:'KNOWN',schema_version:'pregame.outcome-data.v1',dataset_digest:'a'.repeat(64),source,samples:{synthetic_matches:1,real_matches:0},points:[{minute:30,n:1,wins:1,win_rate:1,ci95:{low:0.20654931437723745,high:1},input_match_hashes:['b'.repeat(64)],comparison:'CHAMPION_ROLE',opponent_champion:null}]};
   const response={view,test_mode:true};const result=[];
   const test=(id,passed,actual)=>result.push({id,passed,actual});
   window.PregameOutcome.render(host,response,{testMode:true});let text=host.textContent;
   test('auxiliary-table',host.querySelectorAll('table').length===1&&host.querySelectorAll('svg,canvas').length===0&&host.querySelectorAll('tbody tr').length===1&&text.includes('30–31')&&text.includes('20.65%')&&text.includes('100%'),text);
   test('mobile-table-access',document.documentElement.scrollWidth<=375&&!!host.querySelector('[role=region][tabindex]'),{scrollWidth:document.documentElement.scrollWidth});
   test('uncertainty-n-one',text.includes('n=1')&&text.includes('승리 1')&&text.includes('충분한 표본을 뜻하지')&&text.includes('진행 중 경기의 강함')&&text.includes('상대 전체'),text);
   test('test-source-provenance',text.includes('TEST')&&text.includes(view.dataset_digest)&&text.includes('WILSON_SCORE_95.v1')&&text.includes('N_ONE_COMPUTABLE_NOT_SAMPLE_SUFFICIENCY'),text);
   for(const [name,reply,options]of [['ui-gate',response,{testMode:false}],['server-gate',{...response,test_mode:false},{testMode:true}],['unrecognized-source',{...response,view:{...view,source:{sample_kind:'UNKNOWN'}}},{testMode:true}]]){window.PregameOutcome.render(host,reply,options);test(name,host.textContent.includes('UNKNOWN')&&!host.querySelector('table'),host.textContent);}
   window.PregameOutcome.render(host,{...response,view:{...view,source:{...source,sample_kind:'REAL',provider:'RIOT_API'},samples:{real_matches:1,synthetic_matches:0}},test_mode:false},{testMode:false});test('actual-source',!!host.querySelector('table')&&!host.textContent.includes('TEST'),host.textContent);
   window.PregameOutcome.render(host,{...response,view:{...view,status:'UNKNOWN',points:[],reasons:['NO_MATCHING_COHORT']}},{testMode:true});test('unknown-without-table',!host.querySelector('table')&&host.textContent.includes('NO_MATCHING_COHORT'),host.textContent);
   return result;
  });
  const passed=results.every(r=>r.passed)&&JSON.stringify(results.map(r=>r.id))===JSON.stringify(expected);process.stdout.write(JSON.stringify({evidence_kind:'FRESH_BROWSER_EXECUTION',scope:'ISOLATED_DOM_FIXTURES_NO_MATCH_ACQUISITION',real_match_validation:'NOT_EVALUATED',coaching_accuracy:null,passed,expected_check_ids:expected,checks:results,browser_version:browser.version(),source_sha256:hashes(),tested_at:new Date().toISOString()})+'\n');if(!passed)process.exitCode=1;
 }catch(e){process.stdout.write(JSON.stringify({passed:false,first_failure:String(e)})+'\n');process.exitCode=1;}finally{await browser.close();}
})();

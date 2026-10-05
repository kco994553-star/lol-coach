'use strict';
// Retry-key ownership test for production draft.js. Synthetic service replies;
// actual HTTP/SQLite/browser response-loss coverage is separate.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),harnessPath=path.join(root,'tests_mvp/ui_draft_capture.cjs');
const harnessBytes=fs.readFileSync(harnessPath),prefix=harnessBytes.toString('utf8').split('async function run(){')[0];
if(!prefix.includes('async function ready('))throw Error('Existing harness interface changed');
const digest=value=>crypto.createHash('sha256').update(value).digest('hex');
const context=vm.createContext({require,process,__dirname:path.dirname(harnessPath),__filename:harnessPath,console,setTimeout,clearTimeout});
vm.runInContext(prefix,context,{filename:harnessPath});

async function runRetry(){
 const h=await ready(),results=[];
 async function check(id,task){try{const actual=await task();results.push({id,passed:Object.values(actual.checks).every(Boolean),...actual});}catch(error){results.push({id,passed:false,error:error.message});}}
 await check('DRAFT-RETRY-NETWORK-LOSS-REUSES-EXACT-REQUEST-THEN-ROTATES-KEY',async()=>{
  h.edit('title','first submitted draft α');
  const firstSave=h.save(),first={body:clone(h.saveQueue[0].body),key:h.saveQueue[0].idem};
  h.saveQueue[0].queued.reject(new TypeError('synthetic response lost'));
  await firstSave;
  h.edit('title','later editor draft 한글 😀');
  const beforeRetry=h.state(),retrySave=h.save(),retry={body:clone(h.saveQueue[1].body),key:h.saveQueue[1].idem};
  h.acceptSave(1);await retrySave;
  const afterRetry=h.state(),nextSave=h.save(),next={body:clone(h.saveQueue[2].body),key:h.saveQueue[2].idem};
  h.acceptSave(2);await nextSave;
  return {checks:{first_key_is_nonempty:typeof first.key==='string'&&first.key.length>0,
    retry_reuses_exact_key:first.key===retry.key,
    retry_reuses_exact_body:same(first.body,retry.body),
    later_editor_survives_original_ack:same(afterRetry.values,beforeRetry.values)&&afterRetry.dirty,
    next_save_rotates_key:next.key!==retry.key,
    next_save_uses_acknowledged_cas:next.body.expected_revision===2,
    next_save_contains_later_edit:next.body.capture.title==='later editor draft 한글 😀'},
    first,retry,beforeRetry,afterRetry,next,calls:h.calls};
 });
 return {scope:'Manual draft retry attempt key/body ownership after an ambiguous network failure',
  verifier:'Node VM production script with synthetic DOM/service; not actual browser/HTTP/SQLite/game evidence',
  executed_at:new Date().toISOString(),node_version:process.version,source_sha256:hash(source),
  passed:results.filter(result=>result.passed).length,total:1,results};
}

vm.runInContext('('+runRetry.toString()+')()',context).then(receipt=>{
 receipt.harness_sha256=digest(harnessBytes);receipt.test_sha256=digest(fs.readFileSync(__filename));
 const output=path.resolve(process.argv[2]||path.join(root,'evidence/mvp/draft-retry-after.json'));
 fs.mkdirSync(path.dirname(output),{recursive:true});fs.writeFileSync(output,JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});
 console.log(JSON.stringify({passed:receipt.passed,total:receipt.total,source_sha256:receipt.source_sha256,results:receipt.results.map(({id,passed})=>({id,passed}))}));
 process.exitCode=receipt.passed===receipt.total?0:1;
}).catch(error=>{console.error(error);process.exitCode=1;});

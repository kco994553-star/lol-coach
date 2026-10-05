'use strict';
// Synthetic DOM/service replies isolate three Knowledge deletion UI races.
// No real source, HTTP, SQLite, coaching validation or source authentication.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),source=fs.readFileSync(path.resolve(process.argv[3]||path.join(root,'web_r4/knowledge.js')),'utf8');
const hash=value=>crypto.createHash('sha256').update(value).digest('hex');
function deferred(){let resolve;const promise=new Promise(done=>resolve=done);return {promise,resolve};}
const ruleId='1'.repeat(32),versions={A:'a'.repeat(32),C:'c'.repeat(32),D:'d'.repeat(32)};
const base={schema_version:'knowledge-proposal.v1',rule_id:ruleId,patch_range:'UNKNOWN',applicability:{champion:'UNKNOWN',role:'UNKNOWN',matchup:'UNKNOWN',level:'UNKNOWN',context:'UNKNOWN'},required_fields:['UNKNOWN'],mechanism:'UNKNOWN',counterexamples:['UNKNOWN'],author:'synthetic test',limitations:['UNKNOWN'],review_state:'EXPLORATORY',coaching_enabled:false};
const ref=id=>({resource_id:id,anchor:'overview',note_revision:1});
const A={...base,version:versions.A,claim:'preserved ancestor A',source_refs:[ref('source1')],supersedes:null};
const C={...base,version:versions.C,claim:'DELETED-C-SENTINEL',source_refs:[ref('source3')],supersedes:'b'.repeat(32)};
const D={...C,version:versions.D,claim:'DELETED-D-HELD-ACK',supersedes:versions.C};
function harness(mode){
 const elements=new Map(),sourceRead=deferred(),latestRead=deferred(),post=deferred(),calls=[];
 function el(id){if(!elements.has(id))elements.set(id,{value:'',disabled:false,hidden:false,textContent:'',dataset:{},listeners:{},addEventListener(type,fn){this.listeners[type]=fn;},replaceChildren(){},append(){}});return elements.get(id);}
 function notFound(){const error=new Error('KNOWLEDGE_RULE_NOT_FOUND');error.status=404;throw error;}
 const context=vm.createContext({$:el,node:()=>({dataset:{},addEventListener(){}}),document:{addEventListener(){}},confirm:()=>true,error(){},console,
  api:async(route,method='GET')=>{
   calls.push({route,method});
   if(route==='/knowledge/proposals'&&method==='POST')return post.promise;
   if(route==='/knowledge/proposals/'+ruleId)return mode==='held-ack'?latestRead.promise:A;
   if(route.startsWith('/knowledge/proposals/'+ruleId+'/versions/'))return notFound();
   if(route==='/research/source3')return mode==='new-source'?sourceRead.promise:{id:'source3'};
   if(route==='/research/source4')return {id:'source4'};
   if(route==='/knowledge/proposals')return [A];
   throw Error('Unexpected synthetic service route '+route);
  }});
 vm.runInContext(source,context,{filename:'web_r4/knowledge.js'});
 vm.runInContext('kRecord='+JSON.stringify(C)+';kLatest=kRecord.version;kSource=kBoundSource(kRecord);kApplyRule(kRecord);kSourceLabel();kCurrentLabel()',context);
 const evaluate=code=>vm.runInContext(code,context);
 const state=()=>JSON.parse(evaluate('JSON.stringify({record:kRecord&&kRecord.version,latest:kLatest,source:kSource&&kSource.resource_id,claim:$("k-claim").value,dirty:kDirty,download_disabled:$("k-download").disabled,notice:$("k-notice").textContent})'));
 return {evaluate,state,sourceRead,latestRead,post,calls};
}
async function run(){const results=[];
 async function check(id,task){try{const actual=await task();results.push({id,passed:Object.values(actual.checks).every(value=>value===true),...actual});}catch(error){results.push({id,passed:false,error:error.message});}}
 await check('KNOWLEDGE-DELETED-DISPLAYED-DESCENDANT-CLEARED-WITH-ANCESTOR-SURVIVING',async()=>{
  const h=harness('middle'),before=h.state();await h.evaluate('kAfterSourceDeletion()');const after=h.state();
  return {checks:{deleted_saved_state_cleared:after.record===null,deleted_content_cleared:after.claim==='',deleted_download_blocked:after.download_disabled===true},before,after,calls:h.calls};
 });
 await check('KNOWLEDGE-LATE-DELETION-READ-CANNOT-CLEAR-NEW-INDEPENDENT-SOURCE-DRAFT',async()=>{
  const h=harness('new-source'),reconciliation=h.evaluate('kAfterSourceDeletion()');
  h.evaluate('kSource={resource_id:"source4",anchor:"overview",note_revision:1};kEdit++;kDirty=true;$("k-claim").value="NEW-INDEPENDENT-DRAFT";kSourceLabel()');const before=h.state();
  h.sourceRead.resolve(null);await reconciliation;const after=h.state();
  return {checks:{independent_new_draft_retained:after.claim===before.claim&&after.dirty===true,independent_source_retained:after.source==='source4',deleted_saved_record_detached:after.record===null&&after.download_disabled===true},before,after,calls:h.calls};
 });
 await check('KNOWLEDGE-HELD-CREATED-ACK-CANNOT-RESURRECT-CASCADED-DESCENDANT',async()=>{
  const h=harness('held-ack');h.evaluate('kDirty=true;kEdit++;$("k-claim").value="DELETED-D-HELD-ACK"');
  const saving=h.evaluate('kSave()'),reconciliation=h.evaluate('kAfterSourceDeletion()');h.post.resolve(D);
  await new Promise(resolve=>setTimeout(resolve,0));h.latestRead.resolve(A);
  await Promise.all([saving,reconciliation]);const after=h.state();
  return {checks:{removed_ack_not_displayed:after.record===null,removed_payload_not_rendered:after.claim==='',removed_download_blocked:after.download_disabled===true},after,calls:h.calls};
 });
 return {scope:'Knowledge deletion reconciliation/ack races only',verifier:'Node VM synthetic DOM/service replies; not actual browser/HTTP/SQLite/game evidence',
  executed_at:new Date().toISOString(),node_version:process.version,source_sha256:hash(source),test_sha256:hash(fs.readFileSync(__filename)),
  fixture_sha256:hash(JSON.stringify({A,C,D})),passed:results.filter(result=>result.passed).length,total:results.length,results};
}
run().then(receipt=>{const out=path.resolve(process.argv[2]||path.join(root,'evidence/mvp/knowledge-ui-after.json'));fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({passed:receipt.passed,total:receipt.total,source_sha256:receipt.source_sha256,results:receipt.results.map(({id,passed})=>({id,passed}))}));process.exitCode=receipt.passed===receipt.total?0:1;}).catch(error=>{console.error(error);process.exitCode=1;});

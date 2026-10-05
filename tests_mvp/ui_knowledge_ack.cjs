'use strict';
// Synthetic deferred exact-read response: a preserved ancestor and independent
// draft survive while a cached 200 for a deleted descendant must not be applied.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),source=fs.readFileSync(path.resolve(process.argv[3]||path.join(root,'web_r4/knowledge.js')),'utf8');
const hash=value=>crypto.createHash('sha256').update(value).digest('hex');
function deferred(){let resolve;const promise=new Promise(done=>resolve=done);return {promise,resolve};}
const id='1'.repeat(32),a='a'.repeat(32),c='c'.repeat(32),d='d'.repeat(32),claim='NEW-INDEPENDENT-D-DRAFT';
const base={schema_version:'knowledge-proposal.v1',rule_id:id,patch_range:'UNKNOWN',applicability:{champion:'UNKNOWN',role:'UNKNOWN',matchup:'UNKNOWN',level:'UNKNOWN',context:'UNKNOWN'},required_fields:['UNKNOWN'],mechanism:'UNKNOWN',counterexamples:['UNKNOWN'],author:'synthetic test',limitations:['UNKNOWN'],review_state:'EXPLORATORY',coaching_enabled:false};
const A={...base,version:a,claim:'preserved A',source_refs:[{resource_id:'source1',anchor:'overview',note_revision:1}],supersedes:null};
const D={...base,version:d,claim,source_refs:[{resource_id:'source3',anchor:'overview',note_revision:1}],supersedes:c};
async function run(){const elements=new Map(),listeners={},verificationReady=deferred(),oldVerification=deferred(),calls=[];let exactReads=0;
 function el(key){if(!elements.has(key))elements.set(key,{value:'',disabled:false,hidden:false,textContent:'',dataset:{},addEventListener(){},replaceChildren(){},append(){}});return elements.get(key);}
 const context=vm.createContext({$:el,node:()=>({dataset:{},addEventListener(){}}),document:{addEventListener(type,fn){listeners[type]=fn;}},confirm:()=>true,error(){},console,
  api:async(route,method='GET')=>{
   calls.push({route,method});
   if(route==='/knowledge/proposals'&&method==='POST')return D;
   if(route==='/knowledge/proposals/'+id+'/versions/'+d){exactReads++;if(exactReads===1){verificationReady.resolve();return oldVerification.promise;}const error=new Error('KNOWLEDGE_RULE_NOT_FOUND');error.status=404;throw error;}
   if(route==='/knowledge/proposals/'+id+'/versions/'+a)return A;
   if(route==='/knowledge/proposals/'+id)return A;
   if(route==='/research/source3')return {id:'source3'};
   if(route==='/knowledge/proposals')return [A];
   throw Error('Unexpected synthetic service route '+route);
  }});
 vm.runInContext(source,context,{filename:'web_r4/knowledge.js'});
 vm.runInContext('kRecord='+JSON.stringify(A)+';kLatest="'+c+'";kSource={resource_id:"source3",anchor:"overview",note_revision:1};kApplyRule(kRecord);$("k-claim").value="'+claim+'";kDirty=true;kEdit++;kSourceLabel();kCurrentLabel()',context);
 const state=()=>JSON.parse(vm.runInContext('JSON.stringify({record:kRecord&&kRecord.version,latest:kLatest,source:kSource&&kSource.resource_id,claim:$("k-claim").value,dirty:kDirty,notice:$("k-notice").textContent})',context));
 const saving=vm.runInContext('kSave()',context);await verificationReady.promise;
 await listeners['research-resource-deleted']({detail:{id:'source2'}});const afterDeletion=state();
 oldVerification.resolve(D);await saving;const afterOldVerification=state();
 const checks={preserved_ancestor_not_replaced:afterOldVerification.record===a,postdeletion_latest_preserved:afterOldVerification.latest===a,
  independent_draft_retained:afterOldVerification.claim===claim&&afterOldVerification.source==='source3'&&afterOldVerification.dirty===true,
  postdeletion_exact_revalidation:exactReads===2};
 return {scope:'Cached exact-read acknowledgment across middle-source deletion only',verifier:'Node VM synthetic DOM/service replies; not actual browser/HTTP/SQLite/game evidence',
  executed_at:new Date().toISOString(),node_version:process.version,source_sha256:hash(source),test_sha256:hash(fs.readFileSync(__filename)),fixture_sha256:hash(JSON.stringify({A,D})),
  passed:Object.values(checks).every(value=>value===true)?1:0,total:1,results:[{id:'KNOWLEDGE-CACHED-EXACT-ACK-CANNOT-REAPPLY-DELETED-DESCENDANT',passed:Object.values(checks).every(value=>value===true),checks,exactReads,afterDeletion,afterOldVerification,calls}]};
}
run().then(receipt=>{const out=path.resolve(process.argv[2]||path.join(root,'evidence/mvp/knowledge-ui-ack-after.json'));fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({passed:receipt.passed,total:receipt.total,source_sha256:receipt.source_sha256,results:receipt.results.map(({id,passed})=>({id,passed}))}));process.exitCode=receipt.passed===receipt.total?0:1;}).catch(error=>{console.error(error);process.exitCode=1;});

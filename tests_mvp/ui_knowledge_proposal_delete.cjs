'use strict';
// Synthetic successful proposal DELETE replies spanning a same-rule open or a
// new independent draft. These fixtures do not establish HTTP or game evidence.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),source=fs.readFileSync(path.resolve(process.argv[3]||path.join(root,'web_r4/knowledge.js')),'utf8');
const hash=value=>crypto.createHash('sha256').update(value).digest('hex');
function deferred(){let resolve;const promise=new Promise(done=>resolve=done);return {promise,resolve};}
const id='1'.repeat(32),a='a'.repeat(32),c='c'.repeat(32),draft='new independent draft';
const base={schema_version:'knowledge-proposal.v1',rule_id:id,patch_range:'UNKNOWN',applicability:{champion:'UNKNOWN',role:'UNKNOWN',matchup:'UNKNOWN',level:'UNKNOWN',context:'UNKNOWN'},required_fields:['UNKNOWN'],mechanism:'UNKNOWN',counterexamples:['UNKNOWN'],author:'synthetic test',limitations:['UNKNOWN'],review_state:'EXPLORATORY',coaching_enabled:false};
const A={...base,version:a,claim:'deleted A',source_refs:[{resource_id:'source1',anchor:'overview',note_revision:1}],supersedes:null};
const C={...base,version:c,claim:'deleted C',source_refs:[{resource_id:'source3',anchor:'overview',note_revision:1}],supersedes:a};
function setup(service){
 const elements=new Map(),calls=[];
 function element(key){if(!elements.has(key))elements.set(key,{value:'',disabled:false,hidden:false,textContent:'',dataset:{},children:[],addEventListener(){},replaceChildren(...children){this.children=[...children];},append(child){this.children.push(child);}});return elements.get(key);}
 const context=vm.createContext({$:element,node:(tag,text)=>({tag,textContent:text,dataset:{},addEventListener(){}}),document:{addEventListener(){}},confirm:()=>true,error(){},console,
  api:async(route,method='GET')=>{const call={route,method};calls.push(call);try{const value=await service(route,method);call.status=method==='DELETE'?200:200;return value;}catch(error){call.status=error.status||500;throw error;}}});
 vm.runInContext(source,context,{filename:'web_r4/knowledge.js'});
 vm.runInContext('kRecord='+JSON.stringify(A)+';kLatest="'+c+'";kSource=kBoundSource(kRecord);kValidatedDeletion=kDeletionEpoch;kApplyRule(kRecord);kSourceLabel();kCurrentLabel()',context);
 const state=()=>JSON.parse(vm.runInContext('JSON.stringify({record:kRecord&&kRecord.version,latest:kLatest,source:kSource&&kSource.resource_id,claim:$("k-claim").value,dirty:kDirty,downloadDisabled:$("k-download").disabled,deleteDisabled:$("k-delete").disabled,notice:$("k-notice").textContent})',context));
 return {context,state,calls};
}
function notFound(){const error=new Error('KNOWLEDGE_RULE_NOT_FOUND');error.status=404;throw error;}
async function sameRuleOpen(){
 const deleteReady=deferred(),heldDelete=deferred(),latestReady=deferred(),heldLatest=deferred();let exists=true,latestReads=0;
 const rig=setup(async(route,method)=>{
  if(route==='/knowledge/proposals/'+id&&method==='DELETE'){deleteReady.resolve();return heldDelete.promise;}
  if(route==='/knowledge/proposals/'+id){latestReads++;if(!exists)return notFound();if(latestReads===1){latestReady.resolve();return heldLatest.promise;}return C;}
  if(route==='/knowledge/proposals/'+id+'/versions/'+a||route==='/knowledge/proposals/'+id+'/versions/'+c){if(!exists)return notFound();return route.endsWith('/'+a)?A:C;}
  if(route==='/knowledge/proposals')return exists?[A,C]:[];
  if(route==='/research/source1'||route==='/research/source3')return {id:route.split('/').at(-1)};
  throw Error('Unexpected synthetic service route '+route);
 });
 const deleting=vm.runInContext('kDelete()',rig.context);await deleteReady.promise;
 const opening=vm.runInContext('kUi(()=>kOpen("'+id+'","'+c+'"))',rig.context);await latestReady.promise;
 exists=false;heldDelete.resolve({status:'DELETED',receipt_id:'e'.repeat(32),deleted_versions:2});await deleting;const afterDelete=rig.state();
 heldLatest.resolve(C);await opening;const afterCachedRead=rig.state();
 const exact404=rig.calls.some(call=>call.route.includes('/versions/')&&call.status===404);
 return {afterDelete,afterCachedRead,calls:rig.calls,checks:{deleted_descendant_not_displayed:afterCachedRead.record!==c&&afterCachedRead.claim!==C.claim,
  deleted_current_record_purged:afterCachedRead.record===null&&afterCachedRead.latest===null,
  deleted_record_download_and_delete_blocked:afterCachedRead.downloadDisabled===true&&afterCachedRead.deleteDisabled===true,
  postcommit_exact_revalidation_observed:exact404}};
}
async function independentDraft(){
 const deleteReady=deferred(),heldDelete=deferred();let exists=true;
 const rig=setup(async(route,method)=>{
  if(route==='/knowledge/proposals/'+id&&method==='DELETE'){deleteReady.resolve();return heldDelete.promise;}
  if(route==='/knowledge/proposals/'+id||route.includes('/versions/')){if(!exists)return notFound();return A;}
  if(route==='/knowledge/proposals')return exists?[A]:[];
  if(route==='/research/independent-source')return {id:'independent-source'};
  throw Error('Unexpected synthetic service route '+route);
 });
 const deleting=vm.runInContext('kDelete()',rig.context);await deleteReady.promise;
 vm.runInContext('kClear();kSource={resource_id:"independent-source",anchor:"overview",note_revision:1};$("k-claim").value="'+draft+'";kEdit++;kDirty=true;kSourceLabel();kCurrentLabel()',rig.context);
 const beforeCommit=rig.state();exists=false;heldDelete.resolve({status:'DELETED',receipt_id:'f'.repeat(32),deleted_versions:2});await deleting;const afterCommit=rig.state();
 return {beforeCommit,afterCommit,calls:rig.calls,checks:{independent_new_draft_preserved:afterCommit.record===null&&afterCommit.source==='independent-source'&&afterCommit.claim===draft&&afterCommit.dirty===true,
  independent_draft_download_remains_blocked:afterCommit.downloadDisabled===true}};
}
async function run(){
 const sameRule=await sameRuleOpen(),independent=await independentDraft(),checks={...sameRule.checks,...independent.checks},passed=Object.values(checks).every(value=>value===true);
 return {scope:'Successful proposal deletion across same-rule cached open and independent new draft only',verifier:'Node VM synthetic DOM/service transactions; not actual browser/HTTP/SQLite/game evidence',executed_at:new Date().toISOString(),node_version:process.version,source_sha256:hash(source),test_sha256:hash(fs.readFileSync(__filename)),fixture_sha256:hash(JSON.stringify({A,C,draft})),passed:passed?1:0,total:1,results:[{id:'KNOWLEDGE-PROPOSAL-DELETE-CANNOT-RESURRECT-SAME-RULE-CACHED-OPEN',passed,checks,sameRule,independent}]};
}
run().then(receipt=>{const out=path.resolve(process.argv[2]||path.join(root,'evidence/mvp/knowledge-ui-proposal-delete-after.json'));fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({passed:receipt.passed,total:receipt.total,source_sha256:receipt.source_sha256,results:receipt.results.map(({id,passed})=>({id,passed}))}));process.exitCode=receipt.passed===receipt.total?0:1;}).catch(error=>{console.error(error);process.exitCode=1;});

'use strict';
// Synthetic cached open/list replies spanning a middle-source deletion. These
// fixtures verify UI ownership only, never actual browser/HTTP/game evidence.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),source=fs.readFileSync(path.resolve(process.argv[3]||path.join(root,'web_r4/knowledge.js')),'utf8');
const hash=value=>crypto.createHash('sha256').update(value).digest('hex');
function deferred(){let resolve;const promise=new Promise(done=>resolve=done);return {promise,resolve};}
const id='1'.repeat(32),a='a'.repeat(32),c='c'.repeat(32);
const base={schema_version:'knowledge-proposal.v1',rule_id:id,patch_range:'UNKNOWN',applicability:{champion:'UNKNOWN',role:'UNKNOWN',matchup:'UNKNOWN',level:'UNKNOWN',context:'UNKNOWN'},required_fields:['UNKNOWN'],mechanism:'UNKNOWN',counterexamples:['UNKNOWN'],author:'synthetic test',limitations:['UNKNOWN'],review_state:'EXPLORATORY',coaching_enabled:false};
const A={...base,version:a,claim:'preserved A',source_refs:[{resource_id:'source1',anchor:'overview',note_revision:1}],supersedes:null};
const C={...base,version:c,claim:'deleted C',source_refs:[{resource_id:'source3',anchor:'overview',note_revision:1}],supersedes:'b'.repeat(32)};
const rows=records=>records.map(record=>({rule_id:record.rule_id,version:record.version,claim:record.claim,author:record.author,review_state:record.review_state,supersedes:record.supersedes,current:record.version===a}));
function setup(service){
 const elements=new Map(),listeners={},calls=[];
 function element(key){if(!elements.has(key))elements.set(key,{value:'',disabled:false,hidden:false,textContent:'',dataset:{},children:[],addEventListener(){},replaceChildren(...children){this.children=[...children];},append(child){this.children.push(child);}});return elements.get(key);}
 const context=vm.createContext({$:element,node:(tag,text)=>({tag,textContent:text,dataset:{},addEventListener(){}}),document:{addEventListener(type,fn){listeners[type]=fn;}},confirm:()=>true,error(){},console,
  api:async(route,method='GET')=>{calls.push({route,method});return service(route,method);}});
 vm.runInContext(source,context,{filename:'web_r4/knowledge.js'});
 vm.runInContext('kRecord='+JSON.stringify(A)+';kLatest="'+c+'";kSource=kBoundSource(kRecord);kApplyRule(kRecord);kSourceLabel();kCurrentLabel()',context);
 const state=()=>({...JSON.parse(vm.runInContext('JSON.stringify({record:kRecord&&kRecord.version,latest:kLatest,source:kSource&&kSource.resource_id,claim:$("k-claim").value,dirty:kDirty,downloadDisabled:$("k-download").disabled,deleteDisabled:$("k-delete").disabled,notice:$("k-notice").textContent})',context)),listVersions:element('k-list').children.filter(child=>child.dataset&&child.dataset.versionId).map(child=>child.dataset.versionId)});
 return {context,listeners,state,calls};
}
function notFound(){const error=new Error('KNOWLEDGE_RULE_NOT_FOUND');error.status=404;throw error;}
async function cachedOpen(){
 const ready=deferred(),held=deferred();let exactCReads=0;
 const rig=setup(async route=>{
  if(route==='/knowledge/proposals/'+id+'/versions/'+c){exactCReads++;if(exactCReads===1){ready.resolve();return held.promise;}return notFound();}
  if(route==='/knowledge/proposals/'+id+'/versions/'+a||route==='/knowledge/proposals/'+id)return A;
  if(route==='/research/source1')return {id:'source1'};
  if(route==='/knowledge/proposals')return rows([A]);
  throw Error('Unexpected synthetic service route '+route);
 });
 const opening=vm.runInContext('kUi(()=>kOpen("'+id+'","'+c+'"))',rig.context);await ready.promise;
 await rig.listeners['research-resource-deleted']({detail:{id:'source2'}});const afterDeletion=rig.state();
 held.resolve(C);await opening;const afterCachedRead=rig.state();
 const checks={surviving_ancestor_remains_displayed:afterCachedRead.record===a&&afterCachedRead.claim===A.claim,
  latest_and_bound_source_remain_ancestor:afterCachedRead.latest===a&&afterCachedRead.source==='source1',
  deleted_descendant_never_downloadable:afterCachedRead.record!==c&&afterCachedRead.downloadDisabled===false,
  cached_exact_reply_revalidated:exactCReads===2};
 return {id:'KNOWLEDGE-CACHED-OPEN-CANNOT-DISPLAY-DELETED-DESCENDANT',passed:Object.values(checks).every(value=>value===true),checks,exactCReads,afterDeletion,afterCachedRead,calls:rig.calls};
}
async function cachedList(){
 const ready=deferred(),held=deferred();let listReads=0;
 const rig=setup(async route=>{
  if(route==='/knowledge/proposals'){listReads++;if(listReads===1){ready.resolve();return held.promise;}return rows([A]);}
  if(route==='/knowledge/proposals/'+id+'/versions/'+a||route==='/knowledge/proposals/'+id)return A;
  if(route==='/research/source1')return {id:'source1'};
  throw Error('Unexpected synthetic service route '+route);
 });
 const refreshing=vm.runInContext('kUi(()=>kRefresh())',rig.context);await ready.promise;
 await rig.listeners['research-resource-deleted']({detail:{id:'source2'}});const afterDeletion=rig.state();
 held.resolve(rows([A,C]));await refreshing;const afterCachedRead=rig.state();
 const checks={fresh_deletion_list_contains_only_ancestor:afterDeletion.listVersions.length===1&&afterDeletion.listVersions[0]===a,
  cached_list_does_not_restore_deleted_descendant:afterCachedRead.listVersions.length===1&&afterCachedRead.listVersions[0]===a,
  surviving_display_and_source_preserved:afterCachedRead.record===a&&afterCachedRead.source==='source1'&&afterCachedRead.claim===A.claim};
 return {id:'KNOWLEDGE-CACHED-LIST-CANNOT-RESTORE-DELETED-DESCENDANT',passed:Object.values(checks).every(value=>value===true),checks,listReads,afterDeletion,afterCachedRead,calls:rig.calls};
}
async function run(){
 const results=[await cachedOpen(),await cachedList()];
 return {scope:'Cached exact open/list reads across middle-source deletion only',verifier:'Node VM synthetic DOM/service replies; not actual browser/HTTP/SQLite/game evidence',executed_at:new Date().toISOString(),node_version:process.version,source_sha256:hash(source),test_sha256:hash(fs.readFileSync(__filename)),fixture_sha256:hash(JSON.stringify({A,C})),passed:results.filter(result=>result.passed).length,total:2,results};
}
run().then(receipt=>{const out=path.resolve(process.argv[2]||path.join(root,'evidence/mvp/knowledge-ui-read-after.json'));fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({passed:receipt.passed,total:receipt.total,source_sha256:receipt.source_sha256,results:receipt.results.map(({id,passed})=>({id,passed}))}));process.exitCode=receipt.passed===receipt.total?0:1;}).catch(error=>{console.error(error);process.exitCode=1;});

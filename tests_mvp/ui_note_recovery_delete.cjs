'use strict';
// Actual production Research script in a synthetic DOM/service harness.
// Deferred replies model delivery order, not actual browser/HTTP/game evidence.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),source=fs.readFileSync(path.resolve(process.argv[3]||path.join(root,'web_r4/research.js')),'utf8');
const hash=value=>crypto.createHash('sha256').update(value).digest('hex');
const fields=['known','intention','alternative','outcome'];
const aOverview={known:'삭제할 A 전체 저장 메모',intention:'A 원래 의도',alternative:'A 원래 대안',outcome:'A 원래 결과'};
const aAnchor={known:'PRIVATE_DELETED_A_OTHER_ANCHOR 한글·😀',intention:'A 구간 의도',alternative:'A 구간 대안',outcome:'A 구간 결과'};
const bOverview={known:'보존할 B 저장 메모 日本語·👀',intention:'B 의도',alternative:'B 대안',outcome:'B 결과'};
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function deferred(){let resolve;const promise=new Promise(done=>resolve=done);return {promise,resolve};}
function harness({holdAnchor=false,holdB=false}={}){
 const elements=new Map(),calls=[],events=[],downloads=[],documentListeners=new Map();
 const deletion=deferred(),anchorRead=deferred(),bRead=deferred();
 const el=id=>{if(!elements.has(id))elements.set(id,{value:'',files:[],disabled:false,hidden:false,textContent:'',dataset:{},listeners:{},addEventListener(type,fn){this.listeners[type]=fn;},replaceChildren(){},append(){},click(){}});return elements.get(id);};
 const note=(id,anchor,revision,values)=>({resource_id:id,anchor,revision,...values});
 const resource=id=>({id,title:'Synthetic resource '+id,kind:'RAW_DIAGNOSTIC',report:{declared_source_kind:'UNVERIFIED_IMPORT',sections:{},issues:[]}});
 const context=vm.createContext({$:el,node:()=>el(Symbol()),Blob,URL:{createObjectURL(blob){downloads.push(blob);return 'blob:synthetic-'+downloads.length;},revokeObjectURL(){}},setTimeout(){},confirm:()=>true,error(){},console,
  CustomEvent:class {constructor(type,options){this.type=type;this.detail=options.detail;}},
  document:{querySelector:()=>el('filter-label'),addEventListener(type,fn){if(!documentListeners.has(type))documentListeners.set(type,[]);documentListeners.get(type).push(fn);},dispatchEvent(event){events.push({type:event.type,detail:JSON.parse(JSON.stringify(event.detail))});for(const listener of documentListeners.get(event.type)||[])listener(event);return true;}},
  api:async(route,method='GET',body)=>{calls.push({route,method,...(body===undefined?{}:{body:JSON.parse(JSON.stringify(body))})});
   if(method==='DELETE'&&route==='/research/A')return deletion.promise;
   if(method!=='GET')throw Error('Unexpected synthetic method '+method+' '+route);
   if(route==='/research')return [];
   if(route==='/research/A')return resource('A');
   if(route==='/research/B')return holdB?bRead.promise:resource('B');
   if(route==='/research/A/notes/overview')return note('A','overview',1,aOverview);
   if(route==='/research/A/notes/1')return holdAnchor?anchorRead.promise:note('A','1',2,aAnchor);
   if(route==='/research/B/notes/overview')return note('B','overview',3,bOverview);
   throw Error('Unexpected synthetic route '+method+' '+route);
  }});
 vm.runInContext(source,context,{filename:'web_r4/research.js'});
 const evaluate=code=>vm.runInContext(code,context);
 const state=()=>JSON.parse(evaluate('JSON.stringify({resource:rResource&&rResource.id,note:rNote,dirty:rDirty,edit:rEdit,epoch:rEpoch,values:Object.fromEntries(rFields.map(f=>[f,$("r-"+f).value])),detail_hidden:$("r-detail").hidden,save_disabled:$("r-save").disabled,history_preview:rHistoryPreview,history_owner:rHistoryOwner,recover_disabled:$("r-history-recover").disabled})'));
 return {el,calls,events,evaluate,state,
  open:id=>evaluate('rOpen('+JSON.stringify(id)+')'),openAnchor:()=>evaluate('rOpenNote("1")'),remove:()=>el('r-delete').listeners.click(),
  commitDelete:()=>deletion.resolve({id:'A',status:'DELETED',deleted_versions:0}),
  deliverAnchor:()=>anchorRead.resolve(note('A','1',2,aAnchor)),deliverB:()=>bRead.resolve(resource('B')),
  async download(){const before=downloads.length;el('r-download').listeners.click();return downloads.length===before?null:JSON.parse(await downloads.at(-1).text());}};
}
const purged=state=>state.resource===null&&state.note===null&&state.detail_hidden&&fields.every(field=>state.values[field]==='')&&state.history_preview===null&&state.history_owner===null&&state.recover_disabled;
async function run(){const results=[];async function check(id,task){try{const actual=await task();results.push({id,passed:Object.values(actual.checks).every(Boolean),...actual});}catch(error){results.push({id,passed:false,error:error.message});}}
 await check('NOTE-DELETE-READY-SAME-RESOURCE-OTHER-ANCHOR-PURGES-SAVED-EXPORT',async()=>{
  const h=harness();await h.open('A');const deleting=h.remove();await h.openAnchor();const before=h.state();h.commitDelete();await deleting;const after=h.state(),download=await h.download();
  return {checks:{genuine_delete_event:h.events.length===1&&h.events[0].detail.id==='A',other_anchor_loaded_before_delete:before.note.anchor==='1'&&same(before.values,aAnchor),deleted_resource_and_note_purged:purged(after),deleted_saved_note_not_exportable:download===null},before,after,download,events:h.events,calls:h.calls};
 });
 await check('NOTE-DELETE-PENDING-SAME-RESOURCE-READ-CANNOT-REVIVE-DELETED-NOTE',async()=>{
  const h=harness({holdAnchor:true});await h.open('A');const deleting=h.remove(),opening=h.openAnchor();const before=h.state();h.commitDelete();await deleting;const afterDelete=h.state(),downloadAfterDelete=await h.download();h.deliverAnchor();await opening;const afterRead=h.state(),downloadAfterRead=await h.download();
  return {checks:{exact_same_resource_read_dispatched:h.calls.some(call=>call.route==='/research/A/notes/1'),cache_purged_at_delete:purged(afterDelete),no_export_while_old_read_pending:downloadAfterDelete===null,late_predelete_reply_cannot_revive:purged(afterRead),no_export_after_late_reply:downloadAfterRead===null},before,afterDelete,downloadAfterDelete,afterRead,downloadAfterRead,events:h.events,calls:h.calls};
 });
 await check('NOTE-DELETE-PENDING-DIFFERENT-RESOURCE-LOAD-SURVIVES-DELETED-CACHE-PURGE',async()=>{
  const h=harness({holdB:true});await h.open('A');const deleting=h.remove(),opening=h.open('B');const before=h.state();h.commitDelete();await deleting;const afterDelete=h.state(),downloadAfterDelete=await h.download();h.deliverB();await opening;const afterRead=h.state(),downloadAfterRead=await h.download();
  return {checks:{different_resource_read_dispatched:h.calls.some(call=>call.route==='/research/B'),old_deleted_cache_purged:purged(afterDelete),no_deleted_export_while_B_pending:downloadAfterDelete===null,pending_B_epoch_preserved:afterDelete.epoch===before.epoch,B_successful_load_preserved:afterRead.resource==='B'&&afterRead.note.resource_id==='B'&&same(afterRead.values,bOverview)&&!afterRead.detail_hidden&&!afterRead.save_disabled,B_export_only:downloadAfterRead!==null&&downloadAfterRead.resource.id==='B'&&downloadAfterRead.saved_note.resource_id==='B'&&same(Object.fromEntries(fields.map(field=>[field,downloadAfterRead.saved_note[field]])),bOverview)},before,afterDelete,downloadAfterDelete,afterRead,downloadAfterRead,events:h.events,calls:h.calls};
 });
 return {scope:'Resource deletion across same-resource anchor and pending resource reads',verifier:'Node VM actual production Research script with synthetic DOM/service reply scheduling; not actual browser/HTTP/SQLite/game evidence',executed_at:new Date().toISOString(),node_version:process.version,source_sha256:hash(source),test_sha256:hash(fs.readFileSync(__filename)),fixture_sha256:hash(JSON.stringify({aOverview,aAnchor,bOverview})),passed:results.filter(result=>result.passed).length,total:3,results};
}
run().then(receipt=>{const out=path.resolve(process.argv[2]||path.join(root,'evidence/mvp/note-recovery-delete-after.json'));fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({passed:receipt.passed,total:receipt.total,source_sha256:receipt.source_sha256,test_sha256:receipt.test_sha256,results:receipt.results.map(({id,passed})=>({id,passed}))}));process.exitCode=receipt.passed===receipt.total?0:1;}).catch(error=>{console.error(error);process.exitCode=1;});

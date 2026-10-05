'use strict';
// Production Research script in a synthetic DOM/service harness. These cases
// verify draft/CAS ownership, not actual browser, HTTP, authentication or gameplay.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),source=fs.readFileSync(path.resolve(process.argv[3]||path.join(root,'web_r4/research.js')),'utf8');
const hash=value=>crypto.createHash('sha256').update(value).digest('hex');
const fields=['known','intention','alternative','outcome'];
const v1={known:'과거 근거 한글·日本語·😀\n"정확한 인용"',intention:'의도 α',alternative:'대안 👀 <조건>',outcome:'사후 결과는 분리'};
const v3={known:'현재 저장된 v3',intention:'현재 의도',alternative:'현재 대안',outcome:'현재 결과'};
const currentDraft={known:'복구 전에 작성한 초안',intention:'초안 의도',alternative:'초안 대안',outcome:'초안 사후 메모'};
function deferred(){let resolve;const promise=new Promise(done=>resolve=done);return {promise,resolve};}
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function harness(){const elements=new Map(),calls=[],confirmations=[],save=deferred();let decision=true;
 const el=id=>{if(!elements.has(id))elements.set(id,{value:'',files:[],disabled:false,hidden:false,textContent:'',dataset:{},listeners:{},addEventListener(type,fn){this.listeners[type]=fn;},replaceChildren(){},append(){}});return elements.get(id);};
 const note=(id,revision,values)=>({resource_id:id,anchor:'overview',revision,...values});
 const context=vm.createContext({$:el,node:()=>el(Symbol()),document:{querySelector:()=>el('filter-label')},confirm:message=>{confirmations.push({message,accepted:decision});return decision;},error(){},console,
  api:async(route,method='GET',body)=>{calls.push({route,method,...(body===undefined?{}:{body:JSON.parse(JSON.stringify(body))})});
   if(method==='DELETE')return {id:'A',status:'DELETED'};
   if(method==='PUT')return save.promise;
   if(route==='/research')return [];
   if(route==='/research/A'||route==='/research/B')return {id:route.endsWith('A')?'A':'B',title:'synthetic resource',kind:'RAW_DIAGNOSTIC',report:{declared_source_kind:'UNVERIFIED_IMPORT',sections:{},issues:[]}};
   if(route==='/research/A/notes/overview')return note('A',3,v3);
   if(route==='/research/B/notes/overview')return note('B',0,Object.fromEntries(fields.map(field=>[field,''])));
   if(route==='/research/A/notes/overview/revisions/1')return {resource_id:'A',anchor:'overview',revision:1,current_revision:3,note:{...v1},read_only:true};
   throw Error('Unexpected synthetic service route '+method+' '+route);
  }});
 vm.runInContext(source,context,{filename:'web_r4/research.js'});
 const evaluate=code=>vm.runInContext(code,context);
 const state=()=>JSON.parse(evaluate('JSON.stringify({note:rNote,resource:rResource&&rResource.id,dirty:rDirty,edit:rEdit,epoch:rEpoch,values:Object.fromEntries(rFields.map(f=>[f,$("r-"+f).value])),note_state:$("r-note-state").textContent,notice:$("r-notice").textContent,preview:rHistoryPreview,history_state:$("r-history-state").textContent,recover_disabled:$("r-history-recover").disabled,save_disabled:$("r-save").disabled,detail_hidden:$("r-detail").hidden,workspace_hidden:$("workspace").hidden,research_hidden:$("research-view").hidden})'));
 const draft=values=>{for(const field of fields){el('r-'+field).value=values[field];el('r-'+field).listeners.input();}};
 return {el,evaluate,state,calls,confirmations,save,setDecision:value=>{decision=value;},draft,
  open:()=>evaluate('rOpen("A")'),preview:()=>{el('r-history-revision').value='1';return evaluate('rHistoryOpen()');},recover:()=>evaluate('rHistoryRecover()'),saved:values=>save.resolve(note('A',4,values))};
}
async function ready(){const h=harness();await h.open();await h.preview();return h;}
async function run(){const results=[];async function check(id,task){try{const actual=await task();results.push({id,passed:Object.values(actual.checks).every(Boolean),...actual});}catch(error){results.push({id,passed:false,error:error.message});}}
 await check('NOTE-RECOVERY-EXACT-UNICODE-DRAFT-KEEPS-CURRENT-CAS-NO-PUT',async()=>{const h=await ready(),before=h.state();h.recover();const after=h.state();return {checks:{exact_four_unicode_fields:same(after.values,v1),current_saved_note_preserved:same(after.note,before.note)&&after.note.revision===3,dirty_edit_advanced:after.dirty&&after.edit>before.edit,save_enabled:!after.save_disabled,no_write:h.calls.every(call=>call.method==='GET'),unsaved_notice:after.note_state.includes('미저장')||after.notice.includes('미저장')},before,after,calls:h.calls};});
 await check('NOTE-RECOVERY-NATIVE-CANCEL-LEAVES-DIRTY-EDITOR-UNCHANGED',async()=>{const h=await ready();h.draft(currentDraft);h.setDecision(false);const before=h.state();h.recover();const after=h.state();return {checks:{confirmation_requested:h.confirmations.length===1&&!h.confirmations[0].accepted,exact_state_unchanged:same(after,before),no_put:h.calls.every(call=>call.method==='GET')},before,after,confirmations:h.confirmations};});
 await check('NOTE-RECOVERY-LOADING-AND-PENDING-SAVE-HANDLER-BLOCKED',async()=>{const loading=await ready();loading.evaluate('rReading(true)');const loadingBefore=loading.state();loading.recover();const loadingAfter=loading.state();const saving=await ready();saving.draft(currentDraft);const pending=saving.evaluate('rSave()'),saveBefore=saving.state();saving.recover();const saveAfter=saving.state();saving.saved(currentDraft);await pending;return {checks:{loading_control_disabled:loadingBefore.recover_disabled,loading_direct_handler_no_change:same(loadingAfter,loadingBefore),save_control_disabled:saveBefore.recover_disabled,pending_save_direct_handler_no_change:same(saveAfter,saveBefore),sole_put_original_current_draft:saving.calls.filter(call=>call.method==='PUT').length===1&&same(saving.calls.find(call=>call.method==='PUT').body.note,currentDraft)},loadingBefore,loadingAfter,saveBefore,saveAfter,calls:saving.calls};});
 await check('NOTE-RECOVERY-NAVIGATION-VIEW-LOGOUT-DELETION-PREVIEW-BLOCKED',async()=>{const states=[];for(const action of ['navigation','view','logout','delete']){const h=await ready();if(action==='navigation')await h.evaluate('rOpen("B")');if(action==='view')h.el('show-synthetic').listeners.click();if(action==='logout')h.el('logout').listeners.click();if(action==='delete')await h.el('r-delete').listeners.click();const before=h.state();h.recover();const after=h.state();states.push({action,before,after,unchanged:same(before,after),disabled:before.recover_disabled});}return {checks:{all_invalidated:states.every(state=>state.disabled),all_direct_handlers_blocked:states.every(state=>state.unchanged)},states};});
 await check('NOTE-RECOVERY-NEXT-SAVE-USES-LOADED-LATEST-NOT-HISTORICAL-REVISION',async()=>{const h=await ready();h.recover();const saving=h.evaluate('rSave()'),request=h.calls.find(call=>call.method==='PUT');h.saved(v1);await saving;const after=h.state();return {checks:{current_latest_cas:request.body.expected_revision===3,exact_recovered_payload:same(request.body.note,v1),new_revision_four:after.note.revision===4&&!after.dirty&&same(after.values,v1),old_preview_fixture_preserved:v1.known==='과거 근거 한글·日本語·😀\n"정확한 인용"'},request,after};});
 return {scope:'History to editable draft recovery only',verifier:'Node VM production Research script with synthetic DOM/service replies; not actual browser/HTTP/SQLite/game evidence',executed_at:new Date().toISOString(),node_version:process.version,source_sha256:hash(source),test_sha256:hash(fs.readFileSync(__filename)),fixture_sha256:hash(JSON.stringify({v1,v3,currentDraft})),passed:results.filter(result=>result.passed).length,total:5,results};
}
run().then(receipt=>{const out=path.resolve(process.argv[2]||path.join(root,'evidence/mvp/note-recovery-after.json'));fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({passed:receipt.passed,total:receipt.total,source_sha256:receipt.source_sha256,results:receipt.results.map(({id,passed})=>({id,passed}))}));process.exitCode=receipt.passed===receipt.total?0:1;}).catch(error=>{console.error(error);process.exitCode=1;});

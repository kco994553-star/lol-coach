'use strict';
const fs=require('node:fs'),vm=require('node:vm'),crypto=require('node:crypto');
const sourcePath='/workspace/scratch/b091e55de8cd/lol-coach/web_r4/research.js';
const source=fs.readFileSync(sourcePath,'utf8'),elements=new Map();
const hash=value=>crypto.createHash('sha256').update(value).digest('hex');
const el=id=>{if(!elements.has(id))elements.set(id,{value:'',disabled:false,hidden:false,textContent:'',files:[],dataset:{},listeners:{},addEventListener(type,fn){this.listeners[type]=fn;},replaceChildren(){},append(){}});return elements.get(id);};
function deferred(){let resolve;const promise=new Promise(done=>resolve=done);return {promise,resolve};}
const refreshStarted=deferred(),refresh=deferred(),heldPreview=deferred();
const context=vm.createContext({$:el,node:()=>el(Symbol()),document:{querySelector:()=>el('label')},confirm:()=>true,error(){},api:async(route,method='GET')=>{if(method==='DELETE')return {id:'A',status:'DELETED'};if(route==='/research'){refreshStarted.resolve();return refresh.promise;}if(route==='/research/A/notes/overview/revisions/1')return heldPreview.promise;throw Error('Unexpected synthetic service route '+route);}});
vm.runInContext(source,context,{filename:sourcePath});
vm.runInContext('rResource={id:"A"};rNote={resource_id:"A",anchor:"overview",revision:1,known:"saved",intention:"",alternative:"",outcome:""};$("r-known").value="saved";$("r-notice").textContent="저장된 자료를 열었습니다.";$("r-history-revision").value="1"',context);
const read=()=>JSON.parse(vm.runInContext('JSON.stringify({resource:rResource,note:rNote,epoch:rEpoch,dirty:rDirty,values:Object.fromEntries(rFields.map(f=>[f,$("r-"+f).value])),notice:$("r-notice").textContent,detail_hidden:$("r-detail").hidden,preview:rHistoryPreview,owner:rHistoryOwner,history_state:$("r-history-state").textContent,recover_disabled:$("r-history-recover").disabled})',context));
(async()=>{
 const history=vm.runInContext('rHistoryOpen()',context),deleting=el('r-delete').listeners.click();
 await refreshStarted.promise;const beforeRefreshCompletion=read();
 refresh.resolve([]);await deleting;const afterFullDeletion=read();
 heldPreview.resolve({resource_id:'A',anchor:'overview',revision:1,current_revision:1,note:{known:'saved',intention:'',alternative:'',outcome:''},read_only:true});
 await history;vm.runInContext('rHistoryRecover()',context);const afterLatePreviewAndRecovery=read();
 const changedKeys=Object.keys(beforeRefreshCompletion).filter(key=>JSON.stringify(beforeRefreshCompletion[key])!==JSON.stringify(afterFullDeletion[key]));
 const checks={early_resource_note_predicate_true:beforeRefreshCompletion.resource===null&&beforeRefreshCompletion.note===null,only_notice_changes_on_legitimate_completion:JSON.stringify(changedKeys)==='["notice"]',final_notice_is_success:afterFullDeletion.notice==='자료와 노트를 삭제했습니다.',late_preview_and_recovery_cannot_change_complete_state:JSON.stringify(afterFullDeletion)===JSON.stringify(afterLatePreviewAndRecovery)};
 const result={scope:'Independent Node VM reproduction of actual production Research handler scheduling; synthetic DOM/service replies, not actual browser/HTTP/SQLite evidence',executed_at:new Date().toISOString(),command:'node /tmp/lol-note-recovery-delete-order-20261005T0613.cjs',source_path:sourcePath,source_sha256:hash(source),reproducer_sha256:hash(fs.readFileSync(__filename)),checks,changedKeys,beforeRefreshCompletion,afterFullDeletion,afterLatePreviewAndRecovery};
 const out='/tmp/lol-note-recovery-delete-order-20261005T0613.json';fs.writeFileSync(out,JSON.stringify(result,null,2)+'\n',{flag:'wx'});
 console.log(JSON.stringify({output_path:out,output_sha256:hash(fs.readFileSync(out)),...result},null,2));
 process.exitCode=Object.values(checks).every(Boolean)?0:1;
})().catch(error=>{console.error(error);process.exitCode=1;});

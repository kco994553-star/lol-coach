'use strict';
// Manual proposals and explicit user review decisions. A saved source note is a provenance link,
// never verified player state, accepted knowledge, or automatic coaching input.
let kRecord=null,kLatest=null,kSource=null,kEpoch=0,kEdit=0,kDeletionEpoch=0,kValidatedDeletion=-1,kDirty=false,kSaving=false;
const kText={patch_range:'patch',champion:'champion',role:'role',matchup:'matchup',level:'level',context:'context',claim:'claim',mechanism:'mechanism',author:'author'};
const kLists={required_fields:'required',counterexamples:'counterexamples',limitations:'limitations'};
const kInputs=[...Object.values(kText),...Object.values(kLists)];
function kNotice(message){$('k-notice').textContent=message;}
function kLeave(){return !kDirty||confirm('저장하지 않은 지식 제안 변경을 버리고 이동할까요?');}
function kError(e){kNotice('처리하지 못했습니다: '+e.message);if(e.status===401){kClear();if(typeof rClear==='function')rClear();error(e);}}
function kUi(action){const pending=action(),mark=kEpoch;return Promise.resolve(pending).catch(e=>{if(mark===kEpoch)kError(e);});}
function kSourceLabel(){
 $('k-source').textContent=kSource?'저장된 자료 '+kSource.resource_id+' · 구간 '+kSource.anchor+' · 노트 버전 '+kSource.note_revision:'연결된 저장 노트가 없습니다.';
}
function kReviewControls(){
 for(const id of ['k-review','k-reject'])if($(id))$(id).disabled=!kRecord||kSaving||$('k-save').disabled||kValidatedDeletion!==kDeletionEpoch;
}
function kCurrentLabel(){
 $('k-current').textContent=kRecord?kRecord.review_state+' · '+kRecord.rule_id+' · 조회 버전 '+kRecord.version+' · 다음 저장 기준 '+kLatest:'새 EXPLORATORY(탐색 제안) · 코칭 입력으로 사용하지 않습니다.';
 $('k-download').disabled=!kRecord||kValidatedDeletion!==kDeletionEpoch;$('k-delete').disabled=!kRecord;kReviewControls();
}
function kReadRule(){
 const rule={patch_range:$('k-patch').value,applicability:{}};
 for(const field of ['champion','role','matchup','level','context'])rule.applicability[field]=$('k-'+kText[field]).value;
 for(const field of ['claim','mechanism','author'])rule[field]=$('k-'+kText[field]).value;
 for(const [field,id] of Object.entries(kLists))rule[field]=$('k-'+id).value.split(/\r?\n/).map(x=>x.trim()).filter(Boolean);
 return rule;
}
function kApplyRule(rule){
 $('k-patch').value=rule.patch_range;
 for(const field of ['champion','role','matchup','level','context'])$('k-'+kText[field]).value=rule.applicability[field];
 for(const field of ['claim','mechanism','author'])$('k-'+kText[field]).value=rule[field];
 for(const [field,id] of Object.entries(kLists))$('k-'+id).value=rule[field].join('\n');
}
function kClear(){
 kEpoch++;kEdit=0;kDirty=false;kSaving=false;kRecord=null;kLatest=null;kSource=null;kValidatedDeletion=-1;
 for(const id of kInputs){$('k-'+id).disabled=false;$('k-'+id).value=['claim','author'].includes(id)?'':'UNKNOWN';}
 $('k-save').disabled=false;$('k-use-note').disabled=false;$('k-list').replaceChildren();
 kSourceLabel();kCurrentLabel();kNotice('');
}
function kReading(b){for(const id of kInputs)$('k-'+id).disabled=b;$('k-save').disabled=b;$('k-use-note').disabled=b;$('k-delete').disabled=b||!kRecord;kReviewControls();}
function kBoundSource(record){const ref=record.source_refs[0];return {resource_id:ref.resource_id,anchor:ref.anchor,note_revision:ref.note_revision};}
async function kRefresh(){
 const mark=kEpoch;let rows,deletion;
 do{
  deletion=kDeletionEpoch;
  try{rows=await api('/knowledge/proposals');}
  catch(e){if(mark!==kEpoch)return;if(deletion!==kDeletionEpoch)continue;throw e;}
  if(mark!==kEpoch)return;
 }while(deletion!==kDeletionEpoch);
 $('k-list').replaceChildren();if(!rows.length)$('k-list').append(node('p','저장된 탐색 제안이 없습니다.','small'));
 for(const row of rows){
  const button=node('button',row.claim+' · '+row.version);
  button.textContent+=' · '+row.review_state;
  button.dataset.ruleId=row.rule_id;button.dataset.versionId=row.version;
  button.addEventListener('click',()=>kUi(()=>kOpen(row.rule_id,row.version)));$('k-list').append(button);
 }
}
async function kOpen(id,version){
 if(!kLeave())return;const mark=++kEpoch;kSaving=false;kReading(true);
 try{
  let record,latest,deletion;
  do{
   deletion=kDeletionEpoch;
   try{
    record=await api('/knowledge/proposals/'+id+'/versions/'+version);
    latest=await api('/knowledge/proposals/'+id);
   }catch(e){if(mark!==kEpoch)return;if(deletion!==kDeletionEpoch)continue;throw e;}
   if(mark!==kEpoch)return;
  }while(deletion!==kDeletionEpoch);
  kRecord=record;kLatest=latest.version;kSource=kBoundSource(record);kEdit=0;kDirty=false;kSaving=false;
  kValidatedDeletion=deletion;
  kApplyRule(record);kSourceLabel();kCurrentLabel();kNotice('저장된 탐색 제안을 열었습니다. 이전 버전은 그대로 보존됩니다.');
 }finally{if(mark===kEpoch)kReading(false);}
}
function kUseNote(){
 if($('k-use-note').disabled)return;
 if(!rResource||!rNote||rNote.resource_id!==rResource.id||!Number.isSafeInteger(rNote.revision)||rNote.revision<1||rDirty||$('r-known').disabled){
  kNotice('자료·복기 노트에서 노트를 먼저 저장하고, 저장하지 않은 변경을 정리하세요.');return;
 }
 const source={resource_id:rResource.id,anchor:rNote.anchor,note_revision:rNote.revision};
 if(kSource&&JSON.stringify(kSource)===JSON.stringify(source)){kNotice('현재 연결은 같은 저장 노트입니다.');return;}
 if(kSource&&kDirty&&!confirm('이 초안에 연결된 출처를 현재 저장 노트로 바꿀까요? 제안 내용은 유지됩니다.'))return;
 kSource=source;kEdit++;kDirty=true;kSourceLabel();kNotice('저장된 노트를 출처로 연결했습니다. 내용 검증 상태는 EXPLORATORY로 유지됩니다.');
}
async function kSave(){
 if(kSaving||$('k-save').disabled)return;
 if(!kSource){kNotice('저장된 복기 노트를 출처로 연결한 후 저장하세요.');return;}
 const mark=kEpoch,edit=kEdit,rule=kReadRule(),source={...kSource};
 const body={rule,source,rule_id:kRecord?kRecord.rule_id:null,expected_version:kRecord?kLatest:null};
 kSaving=true;$('k-save').disabled=true;kReviewControls();
 try{
  const received=await api('/knowledge/proposals','POST',body);if(mark!==kEpoch)return;
  let saved,observedDeletion;
  try{
   do{
    observedDeletion=kDeletionEpoch;
    saved=await api('/knowledge/proposals/'+received.rule_id+'/versions/'+received.version);
    if(mark!==kEpoch)return;
   }while(observedDeletion!==kDeletionEpoch);
  }
  catch(e){
   if(mark!==kEpoch)return;
   if(e.status===404){await kAfterSourceDeletion();if(mark===kEpoch)kNotice('저장 응답에 해당하는 버전이 삭제되어 화면에 적용하지 않았습니다.');return;}
   throw e;
  }
  if(mark!==kEpoch)return;
  kRecord=saved;kLatest=saved.version;kValidatedDeletion=observedDeletion;
  if(edit===kEdit){kApplyRule(saved);kSource=kBoundSource(saved);kDirty=false;}
  kSourceLabel();kCurrentLabel();await kRefresh();if(mark!==kEpoch)return;
  kNotice(edit===kEdit?'탐색 제안을 새 버전으로 저장했습니다. 자동 코칭에는 사용되지 않습니다.':'요청한 버전은 저장했습니다. 저장 중 작성한 새 초안과 출처는 그대로 남아 있습니다.');
 }catch(e){if(mark===kEpoch)kError(e);}
 finally{if(mark===kEpoch){kSaving=false;$('k-save').disabled=false;kReviewControls();}}
}
async function kDelete(){
 if($('k-delete').disabled||!kRecord||!confirm('이 제안과 모든 버전·연결된 후속 제안을 삭제할까요?'))return;
 let mark=kEpoch,cleared=false;const id=kRecord.rule_id;
 const current=()=>mark===kEpoch&&(cleared?kRecord===null:kRecord&&kRecord.rule_id===id);
 try{
  await api('/knowledge/proposals/'+id,'DELETE',{expected_version:kLatest});
  kDeletionEpoch++;$('k-download').disabled=true;
  if(!current()){if(!$('workspace').hidden)await kAfterSourceDeletion();return;}
  kClear();mark=kEpoch;cleared=true;await kRefresh();if(current())kNotice('제안과 연결된 버전을 삭제했습니다.');
 }catch(e){if(current())kError(e);}
}
async function kAfterSourceDeletion(){
 let mark=kEpoch;const id=kRecord&&kRecord.rule_id,version=kRecord&&kRecord.version,edit=kEdit,deletion=kDeletionEpoch,source=kSource&&{...kSource},bound=kRecord&&kBoundSource(kRecord);
 const changed=()=>edit!==kEdit||deletion!==kDeletionEpoch||JSON.stringify(source)!==JSON.stringify(kSource)||(kRecord&&kRecord.version)!==version;
 const read=async route=>{try{return await api(route);}catch(e){if(e.status===404)return null;throw e;}};
 try{
 const [latest,displayed,resource]=await Promise.all([id?read('/knowledge/proposals/'+id):Promise.resolve(undefined),id?read('/knowledge/proposals/'+id+'/versions/'+version):Promise.resolve(undefined),source?read('/research/'+source.resource_id):Promise.resolve(undefined)]);
 if(mark!==kEpoch)return;
 // Reconcile the actual current edit/source after a late read instead of
 // clearing a newer independent draft using an earlier deleted-source result.
 if(changed())return kAfterSourceDeletion();
 if(resource===null||(id&&(latest===null||displayed===null))){
  if(kDirty&&source&&resource!==null&&bound&&JSON.stringify(source)!==JSON.stringify(bound)){kEpoch++;kSaving=false;kRecord=null;kLatest=null;$('k-save').disabled=false;kCurrentLabel();kNotice('삭제된 저장 제안의 연결을 해제했습니다. 다른 자료에 연결된 미저장 초안은 유지됩니다.');}
  else{kClear();kNotice('출처 삭제로 연결된 제안과 화면 내용을 지웠습니다.');}
 }else if(id&&latest){kLatest=latest.version;kValidatedDeletion=deletion;}
 mark=kEpoch;
 kCurrentLabel();await kRefresh();
 }catch(e){if(mark!==kEpoch)return;if(changed())return kAfterSourceDeletion();kError(e);}
}
$('show-knowledge').addEventListener('click',()=>{if(typeof rHistoryClear==='function')rHistoryClear();$('synthetic-view').hidden=true;$('research-view').hidden=true;$('knowledge-view').hidden=false;kUi(()=>kRefresh());});
$('k-new').addEventListener('click',()=>{if(!kLeave())return;kClear();kUi(()=>kRefresh());});
$('k-refresh').addEventListener('click',()=>kUi(()=>kRefresh()));
$('k-use-note').addEventListener('click',kUseNote);
$('k-save').addEventListener('click',kSave);
$('k-delete').addEventListener('click',kDelete);
$('k-download').addEventListener('click',()=>{
 if(!kRecord||$('k-download').disabled||kValidatedDeletion!==kDeletionEpoch)return;
 const url=URL.createObjectURL(new Blob([JSON.stringify(kRecord,null,2)],{type:'application/json'})),link=node('a');
 link.href=url;link.download='lol-coach-knowledge-'+kRecord.version+'.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
for(const id of kInputs)$('k-'+id).addEventListener('input',()=>{kEdit++;kDirty=true;kNotice('저장하지 않은 탐색 제안 변경이 있습니다.');});
$('logout').addEventListener('click',kClear);
document.addEventListener('research-resource-deleted',()=>{kDeletionEpoch++;$('k-download').disabled=true;if(!$('workspace').hidden)return kUi(()=>kAfterSourceDeletion());});
kClear();

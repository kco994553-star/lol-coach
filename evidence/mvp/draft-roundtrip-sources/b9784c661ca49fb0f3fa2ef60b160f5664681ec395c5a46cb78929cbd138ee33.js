'use strict';
// Operator-declared input only; neither verified state nor automatic coaching.
let dRecord=null,dLatest=0,dEpoch=0,dEdit=0,dDirty=false,dSaving=false,dPendingCapture=null,dPreview=null,dPreviewOwner=null,dHistoryEpoch=0;
const dDeletedIds=new Set(),dDeletingIds=new Set();
const dSlots=[];for(const side of ['ALLY','ENEMY'])for(let slot=1;slot<=5;slot++)dSlots.push({side,slot,key:side+'-'+slot});
const dInputs=['title','patch','phase','observed','author','perspective','source',...dSlots.flatMap(({key})=>['pick','ban','role','uncertainty'].map(field=>field+'-'+key))];
function dNotice(message){$('d-notice').textContent=message;}
function dNullable(value){return value.trim()?value:null;}
function dReadCapture(){
 const visible_picks=[],visible_bans=[],role_assignments=[];
 for(const {side,slot,key} of dSlots){
  const champion=dNullable($('d-pick-'+key).value),ban=dNullable($('d-ban-'+key).value),role=dNullable($('d-role-'+key).value),uncertainty=$('d-uncertainty-'+key).value;
  if(champion!==null)visible_picks.push({side,slot,champion});
  if(ban!==null)visible_bans.push({side,slot,champion:ban});
  if(champion!==null||role!==null||uncertainty!=='UNKNOWN')role_assignments.push({side,slot,role,uncertainty});
 }
 return {title:$('d-title').value,phase:dNullable($('d-phase').value),patch:dNullable($('d-patch').value),observed_at:dNullable($('d-observed').value),visible_picks,visible_bans,role_assignments,source:{author:$('d-author').value,perspective:$('d-perspective').value,description:$('d-source').value}};
}
function dBlank(){
 for(const id of dInputs)$('d-'+id).value=id==='perspective'||id.startsWith('uncertainty-')?'UNKNOWN':'';
}
function dApplyCapture(capture){
 dBlank();for(const id of ['title','phase','patch'])$('d-'+id).value=capture[id]===null?'':capture[id];
 $('d-observed').value=capture.observed_at===null?'':capture.observed_at;
 $('d-author').value=capture.source.author;$('d-perspective').value=capture.source.perspective;$('d-source').value=capture.source.description;
 for(const [name,field] of [['visible_picks','pick'],['visible_bans','ban']])for(const row of capture[name])$('d-'+field+'-'+row.side+'-'+row.slot).value=row.champion===null?'':row.champion;
 for(const row of capture.role_assignments){$('d-role-'+row.side+'-'+row.slot).value=row.role===null?'':row.role;$('d-uncertainty-'+row.side+'-'+row.slot).value=row.uncertainty;}
}
function dHistoryClear(){
 dHistoryEpoch++;dPreview=null;dPreviewOwner=null;$('d-history-revision').replaceChildren();$('d-history-revision').disabled=true;$('d-history-preview').hidden=true;$('d-history-preview').textContent='';$('d-history-download').disabled=true;$('d-history-state').textContent='';
}
function dControls(reading=false){
 const dead=dRecord&&(dDeletedIds.has(dRecord.session_id)||dDeletingIds.has(dRecord.session_id));
 for(const id of dInputs)$('d-'+id).disabled=reading;
 $('d-save').disabled=reading||dSaving||Boolean(dead);
 $('d-download').disabled=reading||!dRecord||Boolean(dead);
 $('d-delete').disabled=reading||dSaving||!dRecord||Boolean(dead);
 $('d-history-load').disabled=reading||!dRecord||Boolean(dead);
}
function dCurrent(){
 $('d-current').textContent=dRecord?'UNVERIFIED(미검증) · 조회 버전 '+dRecord.revision+' · 다음 저장 기준 '+dLatest+' · 관찰 시각 '+(dRecord.capture.observed_at||'미확인')+' · 저장 시각 '+dRecord.received_at+(dDirty?' · 미저장 변경 있음':''):'새 기록 · 아직 저장하지 않았습니다.';
}
function dClear(){
 dEpoch++;dEdit=0;dDirty=false;dSaving=false;dPendingCapture=null;dRecord=null;dLatest=0;dBlank();dHistoryClear();$('d-list').replaceChildren();$('d-detail').hidden=true;dControls();dCurrent();dNotice('');
}
function dError(e){dNotice('처리하지 못했습니다: '+e.message);if(e.status===401){dClear();if(typeof rClear==='function')rClear();if(typeof kClear==='function')kClear();error(e);}}
function dLeave(){return !dDirty||confirm('저장하지 않은 픽창 기록 변경을 버리고 이동할까요?');}
function dUi(action){const pending=action(),mark=dEpoch;return Promise.resolve(pending).catch(e=>{if(mark===dEpoch)dError(e);});}
function dNew(){if(!dLeave())return;dClear();$('d-detail').hidden=false;dNotice('새 수동 기록을 작성하세요. 알지 못한 값은 빈칸으로 남겨주세요.');}
async function dRefresh(){
 const mark=dEpoch,rows=await api('/draft-captures');if(mark!==dEpoch)return;
 $('d-list').replaceChildren();const currentRows=rows.filter(row=>!dDeletedIds.has(row.session_id));
 if(!currentRows.length)$('d-list').append(node('p','저장한 픽창 기록이 없습니다.','small'));
 for(const row of currentRows){const b=node('button',row.capture.title+' · v'+row.revision);b.dataset.captureId=row.session_id;b.addEventListener('click',()=>dUi(()=>dOpen(row.session_id)));$('d-list').append(b);}
}
async function dOpen(cid,revision){
 if(!dLeave()||dDeletedIds.has(cid))return;
 const mark=++dEpoch;dPendingCapture=cid;dSaving=false;dHistoryClear();dControls(true);
 try{
  const record=await api('/draft-captures/'+cid+(revision===undefined?'':'/revisions/'+revision));
  const latest=revision===undefined?record:await api('/draft-captures/'+cid);
  if(mark!==dEpoch||dDeletedIds.has(cid))return;
  dRecord=record;dLatest=latest.revision;dEdit=0;dDirty=false;dApplyCapture(record.capture);$('d-detail').hidden=false;dCurrent();dNotice('저장된 수동 기록을 열었습니다. 내용 검증 상태는 바뀌지 않습니다.');
 }catch(e){if(mark===dEpoch&&!dDeletedIds.has(cid))dError(e);}
 finally{if(mark===dEpoch){dPendingCapture=null;dControls();}}
}
async function dSave(){
 if($('d-save').disabled||dSaving)return;
 const capture=dReadCapture(),mark=dEpoch,edit=dEdit,cid=dRecord&&dRecord.session_id,expected=dLatest;
 if(cid&&(dDeletedIds.has(cid)||dDeletingIds.has(cid)))return;
 dSaving=true;dControls();
 try{
  const record=await api('/draft-captures'+(cid?'/'+cid:''),cid?'PUT':'POST',cid?{capture,expected_revision:expected}:{capture});
  if(mark!==dEpoch||dDeletedIds.has(record.session_id)||(cid&&(!dRecord||dRecord.session_id!==cid)))return;
  dHistoryClear();dRecord=record;dLatest=record.revision;
  if(edit===dEdit){dApplyCapture(record.capture);dDirty=false;}
  $('d-detail').hidden=false;dCurrent();
  dNotice(dDirty?'요청한 기록은 저장했습니다. 저장 중 수정한 초안은 그대로 남아 있습니다.':'수동 기록을 새 버전으로 저장했습니다.');
  await dRefresh();
 }catch(e){if(mark===dEpoch&&(!cid||(dRecord&&dRecord.session_id===cid&&!dDeletedIds.has(cid))))dError(e);}
 finally{if(mark===dEpoch){dSaving=false;dControls();}}
}
function dHistoryCurrent(owner,mark){return Boolean(owner&&mark===dHistoryEpoch&&owner.epoch===dEpoch&&dRecord&&dRecord.session_id===owner.id&&!dDeletedIds.has(owner.id)&&!dDeletingIds.has(owner.id)&&!$('workspace').hidden&&!$('draft-view').hidden);}
async function dHistoryLoad(){
 if($('d-history-load').disabled||!dRecord)return;
 const owner={id:dRecord.session_id,epoch:dEpoch};dHistoryClear();const mark=dHistoryEpoch;
 try{const result=await api('/draft-captures/'+owner.id+'/history');if(!dHistoryCurrent(owner,mark))return;
  const select=$('d-history-revision');select.replaceChildren();const blank=node('option','조회할 버전 선택');blank.value='';select.append(blank);for(const revision of result.revisions){const item=node('option','버전 '+revision);item.value=String(revision);select.append(item);}select.disabled=false;$('d-history-state').textContent='저장 버전 '+result.revision_count+'개 · 편집 중 내용과 저장 기준은 바뀌지 않습니다.';
 }catch(e){if(dHistoryCurrent(owner,mark))dError(e);}
}
async function dHistoryOpen(){
 const value=$('d-history-revision').value;if(!value||!dRecord)return;
 const owner={id:dRecord.session_id,epoch:dEpoch},mark=++dHistoryEpoch;
 dPreview=null;dPreviewOwner=null;$('d-history-preview').textContent='';$('d-history-preview').hidden=true;$('d-history-download').disabled=true;
 try{const preview=await api('/draft-captures/'+owner.id+'/revisions/'+value);if(!dHistoryCurrent(owner,mark))return;
  dPreview=preview;dPreviewOwner={owner,mark};$('d-history-preview').textContent=JSON.stringify(preview,null,2);$('d-history-preview').hidden=false;$('d-history-download').disabled=false;
 }catch(e){if(dHistoryCurrent(owner,mark))dError(e);}
}
async function dDelete(){
 if($('d-delete').disabled||!dRecord||!confirm('이 픽창 기록과 모든 저장 버전을 삭제할까요?'))return;
 const cid=dRecord.session_id,expected=dLatest,mark=dEpoch;dDeletingIds.add(cid);dControls(Boolean(dPendingCapture));
 try{
  await api('/draft-captures/'+cid,'DELETE',{expected_revision:expected});
  dDeletedIds.add(cid);
  // Successful deletion belongs to the resource, even after navigation.
  // Purge inactive A without cancelling the independently pending B read.
  if(dRecord&&dRecord.session_id===cid){
   if(dPendingCapture&&dPendingCapture!==cid){
    dRecord=null;dLatest=0;dEdit=0;dDirty=false;dBlank();dHistoryClear();$('d-detail').hidden=true;dControls(true);dCurrent();
   }else{
    dClear();const cleared=dEpoch;await dRefresh();if(cleared===dEpoch&&!dRecord)dNotice('픽창 기록과 모든 버전을 삭제했습니다.');return;
   }
  }else if(dPendingCapture===cid){
   dEpoch++;dPendingCapture=null;dSaving=false;dHistoryClear();dControls();dNotice('열려던 픽창 기록이 삭제됐습니다. 기존 다른 기록은 유지됩니다.');
  }
  await dUi(dRefresh);
 }catch(e){if(mark===dEpoch&&dRecord&&dRecord.session_id===cid)dError(e);}
 finally{dDeletingIds.delete(cid);dControls(Boolean(dPendingCapture));}
}
function dDownload(record,filename){
 if(!record||$('workspace').hidden||$('draft-view').hidden||dDeletedIds.has(record.session_id)||dDeletingIds.has(record.session_id))return;
 const url=URL.createObjectURL(new Blob([JSON.stringify(record,null,2)],{type:'application/json'})),a=node('a');a.href=url;a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
for(const id of dInputs)$('d-'+id).addEventListener('input',()=>{dEdit++;dDirty=true;dCurrent();});
$('d-new').addEventListener('click',dNew);$('d-refresh').addEventListener('click',()=>dUi(dRefresh));$('d-save').addEventListener('click',dSave);$('d-delete').addEventListener('click',dDelete);
$('d-history-load').addEventListener('click',dHistoryLoad);$('d-history-revision').addEventListener('change',dHistoryOpen);
$('d-download').addEventListener('click',()=>{if(!$('d-download').disabled)dDownload(dRecord,'lol-coach-draft-v'+dRecord.revision+'.json');});
$('d-history-download').addEventListener('click',()=>{if(dPreviewOwner&&dHistoryCurrent(dPreviewOwner.owner,dPreviewOwner.mark))dDownload(dPreview,'lol-coach-draft-v'+dPreview.revision+'.json');});
$('show-draft').addEventListener('click',()=>{$('synthetic-view').hidden=true;$('research-view').hidden=true;$('knowledge-view').hidden=true;$('draft-view').hidden=false;if(!dRecord)$('d-detail').hidden=false;if(typeof rHistoryClear==='function')rHistoryClear();dUi(dRefresh);});
for(const id of ['show-synthetic','show-research','show-knowledge'])$(id).addEventListener('click',()=>{$('draft-view').hidden=true;dEpoch++;dPendingCapture=null;dSaving=false;dHistoryClear();dControls();});
$('logout').addEventListener('click',dClear);
dBlank();dControls();dCurrent();


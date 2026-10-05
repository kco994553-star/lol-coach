'use strict';
let rResource=null,rNote=null,rEpoch=0,rEdit=0,rDirty=false,rFileRead=0;
const rFields=['known','intention','alternative','outcome'];
const rLabels={ROAM:'로밍',WAVE:'웨이브',JUNGLE:'정글',VISION:'시야',TRADE:'교환'};
function rNotice(s){$('r-notice').textContent=s;}
function rError(e){rNotice('처리하지 못했습니다: '+e.message);if(e.status===401){rClear();error(e);}}
function rClear(){rHistoryClear();rEpoch++;rFileRead++;rReading(false);rResource=null;rNote=null;rDirty=false;rEdit=0;$('r-list').replaceChildren();$('r-candidates').replaceChildren();$('r-diagnostic').replaceChildren();$('r-detail').hidden=true;for(const f of rFields)$('r-'+f).value='';}
function rReading(b){if(b)rHistoryClear();$('r-history-load').disabled=b;for(const f of rFields)$('r-'+f).disabled=b;$('r-save').disabled=b;$('r-delete').disabled=b;}
function rLeave(){return !rDirty||confirm('저장하지 않은 노트 변경을 버리고 이동할까요?');}
function rApply(note){rNote=note;for(const f of rFields)$('r-'+f).value=note[f];rDirty=false;$('r-save').disabled=false;$('r-note-state').textContent='저장 버전 '+note.revision+' · 자동 검증 상태는 바뀌지 않습니다.';}
async function rRefresh(){const mark=rEpoch;const rows=await api('/research');if(mark!==rEpoch)return;$('r-list').replaceChildren();if(!rows.length)$('r-list').append(node('p','저장한 자료가 없습니다.','small'));for(const row of rows){const b=node('button',row.title);b.dataset.resourceId=row.id;b.addEventListener('click',()=>rOpen(row.id).catch(rError));$('r-list').append(b);}}
async function rOpen(id){if(!rLeave())return;const mark=++rEpoch;rReading(true);try{const resource=await api('/research/'+id);const note=await api('/research/'+id+'/notes/overview');if(mark!==rEpoch)return;rResource=resource;rEdit=0;$('r-detail').hidden=false;$('r-title').textContent=resource.title;$('r-filter').value='ALL';rRender();rApply(note);$('r-note-title').textContent='자료 전체 복기';rNotice('저장된 자료를 열었습니다.');}finally{if(mark===rEpoch)rReading(false);}}
function rRender(){const p=rResource.report;$('r-diagnostic').replaceChildren();const video=rResource.kind==='VIDEO';$('r-filter').hidden=!video;document.querySelector('label[for="r-filter"]').hidden=!video;
 if(video){$('r-summary').textContent='자동자막 '+p.cue_count+'구간 · 주제 후보 '+p.candidates.length+'개 · 화면 검증 전';$('r-diagnostic').append(node('p','영상 시간과 게임 시간은 다릅니다. 해설 주장을 관찰 사실로 사용하지 않습니다.','callout'));}
 else{$('r-summary').textContent=(p.declared_source_kind==='DOCUMENTATION_SAMPLE'?'공식 문서 예제':'출처 미검증 입력')+' · 코칭 비활성';for(const [name,state] of Object.entries(p.sections))$('r-diagnostic').append(node('p',name+' · '+({PRESENT:'있음',MISSING:'누락',NULL:'빈 값',WRONG_TYPE:'형식 오류'}[state]||state)));$('r-diagnostic').append(node('p','확인 필요: '+(p.issues.join(', ')||'구조 문제 없음. 실제 의미 검증은 별도입니다.')));}
 rCandidates();}
function rCandidates(){const box=$('r-candidates');box.replaceChildren();if(!rResource||rResource.kind!=='VIDEO')return;const p=rResource.report;const table=node('table');const head=node('tr');for(const h of ['영상 시점','주제','복기'])head.append(node('th',h));table.append(head);
 for(const c of p.candidates){if($('r-filter').value!=='ALL'&&!c.topics.includes($('r-filter').value))continue;const sec=c.video_time_ms/1000;const tr=node('tr'),time=node('td'),a=node('a',String(Math.floor(sec/60)).padStart(2,'0')+':'+String(sec%60).padStart(2,'0')+' ↗');a.href='https://www.youtube.com/watch?v='+encodeURIComponent(p.video_id)+'&t='+sec+'s';a.target='_blank';a.rel='noopener noreferrer';time.append(a);tr.append(time,node('td',c.topics.map(t=>rLabels[t]||t).join(', ')));const cell=node('td'),b=node('button','노트 열기','secondary');b.dataset.anchor=String(c.cue_index);b.addEventListener('click',()=>rOpenNote(String(c.cue_index)).catch(rError));cell.append(b);tr.append(cell);table.append(tr);}box.append(table);}
async function rOpenNote(anchor){if(!rResource||!rLeave())return;const mark=++rEpoch,id=rResource.id;rReading(true);try{const note=await api('/research/'+id+'/notes/'+anchor);if(mark!==rEpoch)return;rEdit=0;rApply(note);$('r-note-title').textContent=anchor==='overview'?'자료 전체 복기':'영상 자막 구간 #'+anchor+' 복기';}finally{if(mark===rEpoch)rReading(false);}}
async function rAdd(body,eligible=()=>true){
 if(!rLeave())return;let mark=++rEpoch;rReading(true);
 try{
  const resource=await api('/research','POST',body);if(mark!==rEpoch||!eligible())return;
  rDirty=false;await rRefresh();if(mark!==rEpoch||!eligible())return;
  const opening=rOpen(resource.id);mark=rEpoch;await opening;
 }catch(e){if(mark===rEpoch&&eligible())rError(e);}
 finally{if(mark===rEpoch)rReading(false);}
}
async function rSave(){if(!rResource||!rNote)return;const mark=rEpoch,edit=rEdit,id=rResource.id,anchor=rNote.anchor;const note=Object.fromEntries(rFields.map(f=>[f,$('r-'+f).value]));$('r-save').disabled=true;
 try{const saved=await api('/research/'+id+'/notes/'+anchor,'PUT',{note,expected_revision:rNote.revision});if(mark!==rEpoch)return;rHistoryClear();rNote=saved;if(edit===rEdit)rApply(saved);else{$('r-note-state').textContent='버전 '+saved.revision+' 저장 완료 · 이후 수정은 아직 저장되지 않았습니다.';}rNotice('복기 노트를 저장했습니다.');}
 finally{if(mark===rEpoch)$('r-save').disabled=false;}}
$('show-research').addEventListener('click',()=>{$('synthetic-view').hidden=true;$('research-view').hidden=false;rRefresh().catch(rError);});
$('show-synthetic').addEventListener('click',()=>{rHistoryClear();$('research-view').hidden=true;$('synthetic-view').hidden=false;});
$('r-refresh').addEventListener('click',()=>rRefresh().catch(rError));
$('r-sample').addEventListener('click',()=>rAdd({source_type:'official_sample',title:'공식 응답 예제'}).catch(rError));
$('r-video').addEventListener('click',()=>rAdd({source_type:'video_example',title:'공개 영상 · 해설 후보'}).catch(rError));
$('r-filter').addEventListener('change',rCandidates);
$('r-overview').addEventListener('click',()=>rOpenNote('overview').catch(rError));
$('r-save').addEventListener('click',()=>rSave().catch(rError));
for(const f of rFields)$('r-'+f).addEventListener('input',()=>{rEdit++;rDirty=true;$('r-note-state').textContent='저장하지 않은 변경이 있습니다.';});
$('r-file').addEventListener('change',async()=>{
 const read=++rFileRead,mark=rEpoch,file=$('r-file').files[0],kind=$('r-kind').value,videoId=$('r-video-id').value;
 const current=()=>mark===rEpoch&&read===rFileRead&&$('r-file').files[0]===file;
 try{
  if(!file)return;
  if(!limits||file.size>limits.body_bytes/2)throw Error('파일 크기가 허용 범위를 초과했습니다.');
  const bytes=await file.arrayBuffer();
  if(!current())return;
  let raw;
  // Preserve the BOM in raw_text so UTF-8 re-encoding binds the original bytes.
  // Fatal decoding rejects corruption instead of silently replacing characters.
  try{raw=new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(bytes);}
  catch{throw Error('UTF-8 파일 형식이 올바르지 않습니다.');}
  const body={source_type:kind,title:file.name,raw_text:raw};if(kind==='transcript')body.video_id=videoId;
  await rAdd(body,()=>read===rFileRead&&$('r-file').files[0]===file);
 }catch(e){if(current())rError(e);}
 finally{if($('r-file').files[0]===file)$('r-file').value='';}
});
$('r-delete').addEventListener('click',async()=>{
 if($('r-delete').disabled||!rResource||!confirm('이 자료와 모든 복기 노트를 삭제할까요?'))return;
 let mark=rEpoch,cleared=false;const id=rResource.id;
 const current=()=>mark===rEpoch&&(cleared?rResource===null:rResource&&rResource.id===id);
 try{
  await api('/research/'+id,'DELETE');if(!current())return;
  rClear();mark=rEpoch;cleared=true;
  await rRefresh();if(current())rNotice('자료와 노트를 삭제했습니다.');
 }catch(e){if(current())rError(e);}
});
$('r-download').addEventListener('click',()=>{if(!rResource||!rNote)return;const data={resource:rResource,saved_note:rNote,unsaved_changes_not_included:rDirty};const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=node('a');a.href=url;a.download='lol-coach-research-note.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
$('logout').addEventListener('click',rClear);

// Saved-history preview owns its own request generation and never changes rNote
// or editable fields. A navigation/save/history reload invalidates stale preview work.
let rHistoryEpoch=0,rHistoryPreview=null;
function rHistoryClear(){rHistoryEpoch++;rHistoryPreview=null;$('r-history-revision').replaceChildren();$('r-history-revision').disabled=true;$('r-history-preview').textContent='';$('r-history-preview').hidden=true;$('r-history-download').disabled=true;$('r-history-state').textContent='';}
function rHistoryIdentity(){return rResource&&rNote?{id:rResource.id,anchor:rNote.anchor,epoch:rEpoch}:null;}
function rHistoryCurrent(identity,mark){return mark===rHistoryEpoch&&identity&&identity.epoch===rEpoch&&rResource&&rNote&&rResource.id===identity.id&&rNote.anchor===identity.anchor;}
function rHistoryError(e){$('r-history-state').textContent='처리하지 못했습니다: '+e.message;if(e.status===401)rError(e);}
async function rHistoryLoad(){
 if($('r-history-load').disabled)return;const identity=rHistoryIdentity();if(!identity)return;
 rHistoryClear();const mark=rHistoryEpoch;$('r-history-state').textContent='저장 버전 목록을 불러오는 중입니다.';
 try{
  const history=await api('/research/'+identity.id+'/notes/'+identity.anchor+'/history');if(!rHistoryCurrent(identity,mark))return;
  const select=$('r-history-revision');const placeholder=node('option',history.revision_count?'버전을 선택하세요':'저장된 버전이 없습니다.');placeholder.value='';select.append(placeholder);
  for(const revision of history.revisions){const option=node('option','저장 버전 '+revision);option.value=String(revision);select.append(option);}
  select.value='';select.disabled=!history.revision_count;$('r-history-state').textContent='저장된 버전 '+history.revision_count+'개 · 최신 저장 버전 '+history.current_revision;
 }catch(e){if(rHistoryCurrent(identity,mark))rHistoryError(e);}
}
async function rHistoryOpen(){
 const identity=rHistoryIdentity(),revision=$('r-history-revision').value;const mark=++rHistoryEpoch;
 rHistoryPreview=null;$('r-history-download').disabled=true;$('r-history-preview').hidden=true;$('r-history-preview').textContent='';
 if(!identity||!revision){$('r-history-state').textContent='조회할 저장 버전을 선택하세요.';return;}
 $('r-history-state').textContent='저장 버전 '+revision+' 조회 중입니다.';
 try{
  const preview=await api('/research/'+identity.id+'/notes/'+identity.anchor+'/revisions/'+revision);if(!rHistoryCurrent(identity,mark))return;
  rHistoryPreview=preview;$('r-history-preview').textContent=JSON.stringify(preview,null,2);$('r-history-preview').hidden=false;$('r-history-download').disabled=false;
  $('r-history-state').textContent='저장 버전 '+preview.revision+' 조회 중 · 조회 시 최신 버전 '+preview.current_revision;
 }catch(e){if(rHistoryCurrent(identity,mark))rHistoryError(e);}
}
$('r-history-load').addEventListener('click',rHistoryLoad);
$('r-history-revision').addEventListener('change',rHistoryOpen);
$('r-history-download').addEventListener('click',()=>{
 if(!rHistoryPreview||$('r-history-download').disabled)return;
 const url=URL.createObjectURL(new Blob([JSON.stringify(rHistoryPreview,null,2)],{type:'application/json'}));const a=node('a');a.href=url;a.download='lol-coach-note-v'+rHistoryPreview.revision+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});

'use strict';
const $=id=>document.getElementById(id);
let token=sessionStorage.getItem('lol-coach-dev-token')||'';
let current=null,jobId=null,report=null,pollTimer=null,epoch=0,selectionEpoch=0,limits=null;
let savedEditor='',saveAttempt=null,reviewAttempt=null;
const labels={KNOWN:'확인됨',UNKNOWN:'미확인',CONDITIONAL:'조건부',CONFLICTING:'근거 충돌',STALE:'유효성 만료',SUFFICIENT:'정보 충분',INSUFFICIENT:'정보 부족',FAVORABLE:'유리',UNFAVORABLE:'불리',CONTESTED:'경합',UNDETERMINED:'판단 보류',POSSIBLE:'실행 가능',IMPOSSIBLE:'실행 불가',WAIT:'대기',DISENGAGE:'후퇴',SHORT_TRADE:'짧은 교환'};
const text=v=>v===null||v===undefined?'—':typeof v==='object'?JSON.stringify(v):String(v);
function node(tag,value,cls){const n=document.createElement(tag);if(value!==undefined)n.textContent=text(value);if(cls)n.className=cls;return n;}
function notice(message,error=false){$('notice').textContent=message;$('notice').className=error?'error':'';}
function clearPoll(){if(pollTimer)clearTimeout(pollTimer);pollTimer=null;}
function hideReport(){report=null;$('report-panel').hidden=true;}
function reset(){epoch++;selectionEpoch++;clearPoll();current=null;jobId=null;saveAttempt=null;reviewAttempt=null;savedEditor='';hideReport();$('current').textContent='아직 선택한 사례가 없습니다.';$('analyze').disabled=true;$('cancel').disabled=true;$('session-actions').hidden=true;}
function confirmDraftReplacement(){return !$('case-json').value.trim()||$('case-json').value===savedEditor||confirm('저장하지 않은 수정 내용이 있습니다. 다른 입력을 열면 이 초안이 사라집니다. 계속 열까요?');}
async function api(path,method='GET',body,idem){
  const headers={Authorization:'Bearer '+token};if(body!==undefined)headers['Content-Type']='application/json';if(idem)headers['Idempotency-Key']=idem;
  const response=await fetch('/dev/v1'+path,{method,headers,body:body===undefined?undefined:JSON.stringify(body),cache:'no-store'});
  const data=await response.json();if(!response.ok){const err=new Error(data.error_code||'REQUEST_FAILED');err.status=response.status;throw err;}return data;
}
function error(e){if(e.status===401){sessionStorage.removeItem('lol-coach-dev-token');token='';$('auth-panel').hidden=false;$('workspace').hidden=true;reset();}notice('처리하지 못했습니다: '+e.message,true);}
async function connect(){const mark=epoch;const data=await api('/status');if(mark!==epoch)return;limits=data.limits;$('auth-panel').hidden=true;$('workspace').hidden=false;sessionStorage.setItem('lol-coach-dev-token',token);$('token').value='';await refresh();notice('연결됐습니다. 합성 사례를 불러와 시작하세요.');}
async function refresh(){const mark=epoch;const rows=await api('/sessions');if(mark!==epoch)return;$('sessions').replaceChildren();if(!rows.length)$('sessions').append(node('p','저장한 사례가 없습니다.','small'));for(const s of rows){const b=node('button',s.title+' · v'+s.revision,current&&s.id===current.id?'active':'');b.type='button';b.addEventListener('click',()=>openSession(s.id).catch(error));$('sessions').append(b);}}
async function openSession(id){if(!confirmDraftReplacement())return;reset();const mark=epoch;const s=await api('/sessions/'+id);const entry=s.revision?await api('/sessions/'+id+'/case'):null;const jobs=await api('/sessions/'+id+'/reviews');const done=jobs.find(j=>j.status==='COMPLETED');const result=done?await api('/reviews/'+done.result_ref):null;if(mark!==epoch)return;current=s;$('title').value=s.title;$('case-json').value=entry?JSON.stringify(entry.case,null,2):'';savedEditor=$('case-json').value;$('current').textContent=s.title+' · 저장 버전 '+s.revision;$('analyze').disabled=!entry;$('session-actions').hidden=false;if(result)render(result);await refresh();if(mark===epoch)notice(result?'저장한 입력과 복기 결과를 열었습니다.':'저장한 사례를 열었습니다.');}
function assignSession(payload,id){payload.snapshot_request.session_id=id;for(const o of payload.observations)o.session_id=id;return payload;}
async function loadExample(){if(!confirmDraftReplacement())return;reset();const mark=epoch;const data=await api('/examples/'+$('example').value);if(mark!==epoch)return;$('case-json').value=JSON.stringify(data,null,2);$('title').value=$('example').selectedOptions[0].textContent;notice('합성 예시를 불러왔습니다. 사례 저장 후 분석하세요.');}
async function save(){
  const selection=selectionEpoch,editorAtStart=$('case-json').value;const payload=JSON.parse(editorAtStart);if(payload.mode!=='TEST'||payload.evidence_kind!=='SYNTHETIC')throw new Error('합성 TEST 사례만 저장할 수 있습니다.');
  $('save-case').disabled=true;
  try{
    if(!current){const created=await api('/sessions','POST',{title:$('title').value,patch:payload.snapshot_request.patch,mode:'TEST'});if(selection!==selectionEpoch)return;current=created;}
    const sid=current.id;
    assignSession(payload,current.id);
    const body={case:payload,expected_revision:current.revision};const fingerprint=JSON.stringify(body);
    if(!saveAttempt||saveAttempt.fingerprint!==fingerprint)saveAttempt={fingerprint,key:crypto.randomUUID()};
    const result=await api('/sessions/'+sid+'/case','PUT',body,saveAttempt.key);
    if(selection!==selectionEpoch||!current||current.id!==sid)return;current.revision=result.revision;saveAttempt=null;reviewAttempt=null;savedEditor=JSON.stringify(result.case,null,2);if($('case-json').value===editorAtStart)$('case-json').value=savedEditor;hideReport();
    $('current').textContent=current.title+' · 저장 버전 '+current.revision;$('analyze').disabled=$('case-json').value!==savedEditor;$('session-actions').hidden=false;
    await refresh();if(selection===selectionEpoch&&current&&current.id===sid)notice($('case-json').value===savedEditor?'입력을 저장했습니다. 분석 실행으로 이어가세요.':'요청한 입력은 저장했습니다. 저장 중 수정한 초안은 그대로 남아 있으니 추가 저장하세요.');
  }finally{$('save-case').disabled=false;}
}
async function analyze(){
  if(!current)throw new Error('먼저 사례를 저장하세요.');
  if($('case-json').value!==savedEditor)throw new Error('수정한 입력을 먼저 저장하세요.');
  hideReport();const mark=++epoch;clearPoll();$('analyze').disabled=true;
  try{if(!reviewAttempt||reviewAttempt.revision!==current.revision)reviewAttempt={revision:current.revision,key:crypto.randomUUID()};
    const job=await api('/sessions/'+current.id+'/reviews','POST',{expected_revision:current.revision},reviewAttempt.key);if(mark!==epoch)return;jobId=job.id;$('cancel').disabled=false;notice('분석 작업을 시작했습니다.');await poll(mark);
  }catch(e){$('analyze').disabled=false;throw e;}
}
async function poll(mark){if(mark!==epoch||!jobId)return;const job=await api('/jobs/'+jobId);if(mark!==epoch)return;
  if(job.status==='COMPLETED'){const result=await api('/reviews/'+job.result_ref);if(mark!==epoch)return;render(result);$('cancel').disabled=true;$('analyze').disabled=false;reviewAttempt=null;notice(result.stale?'이 결과는 이전 입력 버전의 결과입니다. 다시 분석하세요.':'복기 결과를 저장했습니다.');return;}
  if(['FAILED','CANCELLED'].includes(job.status)){$('cancel').disabled=true;$('analyze').disabled=false;reviewAttempt=null;notice(job.status==='CANCELLED'?'작업을 취소했습니다.':'분석 실패: '+(job.error||'UNKNOWN'),job.status==='FAILED');return;}
  pollTimer=setTimeout(()=>poll(mark).catch(error),250);
}
function render(wrapper){report=wrapper;$('report-panel').hidden=false;$('report-state').textContent=wrapper.stale?'이전 버전 결과':'합성 검증 결과';const r=wrapper.result;$('objective').textContent=r.objective;
  $('evaluations').replaceChildren();for(const a of r.evaluations){const card=node('article',undefined,'card');card.append(node('h3',labels[a.action_type]||a.action_type));const badges=node('div',undefined,'badges');for(const s of [a.sufficiency,a.assessment])badges.append(node('span',labels[s]||s,'badge'));card.append(badges);card.append(node('p',a.missing_fields.length?'부족한 정보: '+a.missing_fields.join(', '):'명시한 필수 정보가 확보된 합성 조건입니다.'));card.append(node('p',a.expired?'판단 마감 또는 중단 조건 발생':'종료 조건: '+a.contract.exit_condition));card.append(node('p','검토 후보: '+(r.alternatives.includes(a.action_id)?'유지':'제외·만료·실행 미확인')));$('evaluations').append(card);}
  $('evidence').replaceChildren();for(const f of r.snapshot.fields){const tr=node('tr');tr.append(node('td',f.key),node('td',labels[f.state]||f.state),node('td',text(f.value)+(f.reasons.length?' / '+f.reasons.join(', '):'')));$('evidence').append(tr);}
  $('questions').replaceChildren();if(!r.information_requests.length)$('questions').append(node('p','현재 활성화된 추가 확인 요청이 없습니다.'));for(const q of r.information_requests)$('questions').append(node('p',q.minimum_observation+' · 대기 비용: '+q.waiting_cost));for(const q of r.deferred_information)$('questions').append(node('p','보류: '+q.minimum_observation+' / '+q.reason,'small'));
  $('reflection').textContent='당시 의도: '+(r.intention.state==='UNKNOWN'?'미확인':r.intention.text)+' · 사후 결과: '+(r.outcome.text||'입력 없음')+' · 결과는 당시 판단 평가에 사용하지 않았습니다.';
  $('report-json').textContent=JSON.stringify(wrapper,null,2);
}
$('login-form').addEventListener('submit',e=>{e.preventDefault();token=$('token').value.trim();connect().catch(error);});
$('logout').addEventListener('click',()=>{sessionStorage.removeItem('lol-coach-dev-token');token='';reset();$('case-json').value='';$('report-json').textContent='';$('sessions').replaceChildren();$('workspace').hidden=true;$('auth-panel').hidden=false;notice('연결을 해제했습니다.');});
$('refresh').addEventListener('click',()=>refresh().catch(error));
$('load-example').addEventListener('click',()=>loadExample().catch(error));
$('save-case').addEventListener('click',()=>save().catch(error));
$('analyze').addEventListener('click',()=>analyze().catch(error));
$('cancel').addEventListener('click',()=>{if(jobId)api('/jobs/'+jobId+'/cancel','POST',{}).then(()=>notice('취소 요청을 처리했습니다.')).catch(error);});
$('case-json').addEventListener('input',()=>{epoch++;clearPoll();$('cancel').disabled=true;$('analyze').disabled=!current||$('case-json').value!==savedEditor;hideReport();});
$('import-file').addEventListener('change',async()=>{const mark=epoch;const selected=$('import-file').files[0];try{const file=$('import-file').files[0];if(!file)return;if(!limits||file.size>limits.body_bytes)throw new Error('허용된 파일 크기를 초과했습니다.');const data=JSON.parse(await file.text());if(mark!==epoch)return;if(data.mode!=='TEST'||data.evidence_kind!=='SYNTHETIC')throw new Error('합성 TEST JSON만 사용할 수 있습니다.');if(!confirmDraftReplacement())return;reset();$('case-json').value=JSON.stringify(data,null,2);notice('합성 입력 파일을 불러왔습니다.');}catch(e){error(e);}finally{if($('import-file').files[0]===selected)$('import-file').value='';}});
$('delete-session').addEventListener('click',async()=>{if(!current||!confirm('이 사례의 입력과 모든 복기 결과를 삭제할까요?'))return;const mark=epoch,sid=current.id;try{await api('/sessions/'+sid,'DELETE');if(mark!==epoch||!current||current.id!==sid)return;reset();$('case-json').value='';await refresh();notice('사례와 결과를 삭제했습니다.');}catch(e){error(e);}});
$('download').addEventListener('click',()=>{if(!report)return;const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'}));const a=node('a');a.href=url;a.download='lol-coach-synthetic-review.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
if(token)connect().catch(error);

'use strict';
// Authority starts at a trusted browser button event. No review function is
// exported for AI/automatic proposal code. Browser control is a trusted boundary.
(()=>{
 let busy=false;
 async function decide(event,decision){
  if(!event.isTrusted||!navigator.userActivation.isActive||busy||kSaving||event.currentTarget.disabled||!kRecord)return;
  const rule=kReadRule(),scope=rule.applicability,selected=kRecord;
  const sameSource=JSON.stringify(kSource)===JSON.stringify(kBoundSource(selected));
  const unchanged=['claim','mechanism','author','required_fields','counterexamples','limitations'].every(key=>JSON.stringify(rule[key])===JSON.stringify(selected[key]));
  if(!sameSource||!unchanged){kNotice('후보 내용·출처 변경을 새 버전으로 저장한 뒤 결정하세요.');return;}
  if(decision==='REVIEWED'&&[rule.patch_range,...Object.values(scope)].some(value=>!value.trim()||['UNKNOWN','미확인'].includes(value.trim().toUpperCase()))){
   kNotice('승인하려면 패치 범위와 모든 적용 조건을 입력하세요. 빈 값·UNKNOWN·미확인은 승인할 수 없습니다.');return;
  }
  if(!confirm('조회 버전 '+selected.version+'을 '+(decision==='REVIEWED'?'승인':'거절')+'할까요? 결정은 새 버전으로 보존됩니다.'))return;
  const body={selected_version:selected.version,expected_version:kLatest,decision,patch_range:rule.patch_range,applicability:scope};
  const mark=++kEpoch;busy=true;kReading(true);$('k-review').disabled=true;$('k-reject').disabled=true;
  try{
   const response=await fetch('/dev/v1/knowledge/proposals/'+selected.rule_id+'/decisions',{
    method:'POST',mode:'same-origin',headers:{Authorization:'Bearer '+token,'Content-Type':'application/json'},body:JSON.stringify(body)});
   const received=await response.json();if(mark!==kEpoch)return;
   if(!response.ok){const e=new Error(received.error_code||'결정 저장 실패');e.status=response.status;throw e;}
   let saved,latest,deletion;
   try{
    do{
     deletion=kDeletionEpoch;
     saved=await api('/knowledge/proposals/'+received.rule_id+'/versions/'+received.version);
     latest=await api('/knowledge/proposals/'+received.rule_id);
     if(mark!==kEpoch)return;
    }while(deletion!==kDeletionEpoch);
   }catch(e){
    if(mark!==kEpoch)return;
    if(e.status===404){await kAfterSourceDeletion();return;}
    throw e;
   }
   if(mark!==kEpoch)return;
   kRecord=saved;kLatest=latest.version;kSource=kBoundSource(saved);kDirty=false;
   kValidatedDeletion=deletion;kApplyRule(saved);kSourceLabel();kCurrentLabel();
   await kRefresh();if(mark!==kEpoch)return;
   kNotice(decision==='REVIEWED'?'승인 결정을 저장했습니다. 게임플랜 생성은 아직 제공하지 않습니다.':'거절 결정을 저장했습니다. 이전 버전은 보존됩니다.');
  }catch(e){if(mark===kEpoch)kError(e);}
  finally{busy=false;if(mark===kEpoch)kReading(false);kReviewControls();}
 }
 $('k-review').addEventListener('click',event=>decide(event,'REVIEWED'));
 $('k-reject').addEventListener('click',event=>decide(event,'REJECTED'));
})();

'use strict';
(() => {
  // Authority exists only inside trusted human click handlers, never in an exported decision function.
  function attach(options){
    const approve=document.getElementById('ex-approve'),reject=document.getElementById('ex-reject');
    const unchanged=state=>{try{return JSON.stringify(JSON.parse(document.getElementById('ex-proposal-json').textContent))===JSON.stringify(state.record)&&JSON.stringify(state.record.source_refs)===JSON.stringify(state.boundSources);}catch(_){return false;}};
    const complete=scope=>[scope.patch_range,...Object.values(scope.applicability)].every(v=>v.trim()&&!['UNKNOWN','미확인'].includes(v.trim().toUpperCase()));
    function update(){const state=options.snapshot(),blocked=!state||state.busy||state.record.version!==state.latest||!unchanged(state);approve.disabled=blocked||!complete(options.readScope());reject.disabled=blocked;}
    async function decide(event,decision){
      if(!event.isTrusted||!navigator.userActivation.isActive||event.currentTarget.disabled)return;
      const state=options.snapshot();if(!state||state.busy||state.record.version!==state.latest||!unchanged(state)){options.notice('저장 버전과 출처를 다시 열고 확인하세요.',true);update();return;}
      const scope=options.readScope();if(decision==='REVIEWED'&&!complete(scope)){options.notice('패치와 모든 적용 범위를 직접 확인하세요.',true);update();return;}
      if(!confirm('조회 버전 '+state.record.version+'을 '+(decision==='REVIEWED'?'승인':'거절')+'할까요? 내용·출처·반례·한계를 확인한 결정은 새 버전으로 보존됩니다. 실행 명세는 연결되지 않습니다.'))return;
      const mark=options.context();options.busy(true);update();
      try{await options.request('/knowledge/proposals/'+state.record.rule_id+'/decisions','POST',{selected_version:state.record.version,expected_version:state.latest,decision,...scope});if(!options.alive(mark))return;await options.refresh();if(options.alive(mark))options.notice('직접 검토 결정을 저장했습니다. 실행 명세는 미연결입니다.');}
      catch(e){if(options.alive(mark))options.error(e);}
      finally{if(options.alive(mark)){options.busy(false);update();}}
    }
    approve.addEventListener('click',event=>decide(event,'REVIEWED'));reject.addEventListener('click',event=>decide(event,'REJECTED'));return {update};
  }
  window.ExpertReview={attach};
})();

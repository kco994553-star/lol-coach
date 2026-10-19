/* Presentation only. No matchup rules, scores, provider calls or example prose. */
(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.LoadingPresentation=factory();})(typeof window!=='undefined'?window:globalThis,function(){
  'use strict';
  const areas=['lane','operations','fight'];
  const inputKeys=new Set(['schema_version','allies','enemies','own_champion','own_position','side','patch','opponent_mode','lane_opponent','preferences','scenario','planning']);
  function project(report){
    const b=report.coach?.planboard||{}, summaries=b.loading_summary?.items||[];
    return {schema_version:'lol-coach-presentation-v1',own:{champion:report.input.own_champion,position:report.input.own_position},teams:{allies:report.input.allies,enemies:report.input.enemies},
      title:b.headline||report.summary?.my_role||'이 조합의 분석을 확인해 주세요.',support:b.composition?.role||report.summary?.my_role||'',
      cards:areas.map(id=>{const s=summaries.find(x=>x.id===id)||{};return {id,label:{lane:'라인전',operations:'운영',fight:'한타'}[id],title:s.conclusion||b.brief?.[id]||'이 영역의 자료가 부족합니다.',text:s.support||'',perspectives:b.area_context?.[id]||{},actions:b.action_summaries?.[id]?.items||[],judgment:b.action_summaries?.[id]?.judgment,source_paths:['loading_summary.items.'+id,'area_context.'+id,'action_summaries.'+id]};}),
      remember:(b.loading_summary?.changes||b.reminders||[]).slice(0,3),origin:b.context?.origin||'ANALYSIS_ASSUMPTIONS_NOT_OBSERVATION'};
  }
  function validate(value){
    if(!value||value.version!==1||!value.input||typeof value.input!=='object'||Array.isArray(value.input))throw Error('공유한 게임플랜 형식을 읽을 수 없습니다.');
    if(Object.keys(value.input).some(k=>!inputKeys.has(k)))throw Error('공유할 수 없는 입력 필드가 있습니다.');
    if(!Array.isArray(value.input.allies)||!Array.isArray(value.input.enemies)||value.input.allies.length!==5||value.input.enemies.length!==5)throw Error('공유한 조합의 10픽을 확인해 주세요.');
    if(value.detail!==null&&!areas.includes(value.detail))throw Error('상세 화면 경로를 읽을 수 없습니다.');
    if(typeof value.period!=='string'||!/^[A-Z0-9_]{1,60}$/.test(value.period))throw Error('선택한 구간을 읽을 수 없습니다.');
    return value;
  }
  function encode(input,period='LEVEL1',detail=null){const value=validate({version:1,input,period,detail}),hash='#plan='+encodeURIComponent(JSON.stringify(value));if(hash.length>20000)throw Error('공유할 입력이 너무 깁니다.');return hash;}
  function decode(hash){if(!String(hash).startsWith('#plan='))return null;if(hash.length>20000)throw Error('공유할 입력이 너무 깁니다.');try{return validate(JSON.parse(decodeURIComponent(hash.slice(6))));}catch(e){throw Error('게임플랜 링크를 읽을 수 없습니다. 조합을 다시 입력해 주세요.');}}
  return Object.freeze({project,encode,decode});
});

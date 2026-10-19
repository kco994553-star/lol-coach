/* Presentation only. No matchup rules, scores, provider calls or example prose. */
(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.LoadingPresentation=factory();})(typeof window!=='undefined'?window:globalThis,function(){
  'use strict';
  const areas=['lane','operations','fight'];
  const inputKeys=new Set(['schema_version','allies','enemies','own_champion','own_position','side','patch','opponent_mode','lane_opponent','preferences','scenario','planning']);
  // Short names for decisions already selected by the engine; never choose a plan here.
  const waveNames={ACQUIRE_PUSH:['먼저 밀고, 견제할 공간 만들기','먼저 밀어 견제할 공간을 만드세요'],CHECK_WAVE:['미니언을 챙기며 다음 기회 준비','성장을 지키며 다음 행동을 준비하세요'],SLOW_PUSH:['천천히 쌓아 다음 선택 준비','미니언을 쌓아 다음 선택을 준비하세요'],TRIM_RECEIVE:['상대 미니언을 줄이며 받아먹기','위험한 전진을 줄이고 미니언을 챙기세요'],TOWER_CS:['포탑 아래에서 성장 지키기','포탑 가까이에서 성장을 지키세요'],RETURNING:['돌아오는 미니언을 안전하게 받기','돌아오는 미니언으로 다음 기회를 준비하세요'],FAST_PUSH:['빠르게 밀고 포탑 도달 확인','빠르게 밀고 다음 행동을 준비하세요']};
  const operationNames={GROUP_CONNECTED:'중앙에서 아군과 함께 압박',SIDE_RETURN:'사이드 압박을 아군과 연결',FRONT_CONNECT:'가까운 라인에서 아군과 연결'};
  function project(report){
    const b=report.coach?.planboard||{}, summaries=b.loading_summary?.items||[];
    return {schema_version:'lol-coach-presentation-v1',own:{champion:report.input.own_champion,position:report.input.own_position},teams:{allies:report.input.allies,enemies:report.input.enemies},
      hero_title:b.operation_headline||waveNames[b.wave?.plan_id]?.[1]||b.headline||report.summary?.my_role||'이 조합의 분석을 확인해 주세요.',
      title:b.headline||report.summary?.my_role||'이 조합의 분석을 확인해 주세요.',support:b.composition?.role||report.summary?.my_role||'',
      cards:areas.map(id=>{const s=summaries.find(x=>x.id===id)||{};return {id,concept:id==='lane'?(b.lane?.concept?.plan_id===b.wave?.plan_id?b.lane.concept.text:waveNames[b.wave?.plan_id]?.[0]||s.conclusion):id==='operations'?(b.operations?.concept||operationNames[b.operations?.mode]||s.conclusion):(b.fight?.concept||b.fight?.role||s.conclusion),conditions:id==='lane'?[report.coach?.selected?.metrics?.SHORT?.assessment==='ALLY'?'짧은 교환 우세':null,b.wave?.conditions?.enemy_jungle==='UNKNOWN'?'정글 위치 미확인':null].filter(Boolean):[],explanation:b.coaching_explanation?.[id]||[],label:{lane:report.input.own_position==='JUNGLE'?'초반 정글':'라인전',operations:'운영',fight:'한타'}[id],title:s.conclusion||b.brief?.[id]||'이 영역의 자료가 부족합니다.',text:s.support||'',focus:id==='operations'?b.operations?.awareness?.watch:id==='fight'?b.fight?.awareness?.danger:null,perspectives:b.area_context?.[id]||{},actions:b.action_summaries?.[id]?.items||[],condition_responses:b.condition_responses?.[id]||[],judgment:b.action_summaries?.[id]?.judgment,source_paths:['loading_summary.items.'+id,'area_context.'+id,'action_summaries.'+id,'condition_responses.'+id]};}),
      team_plan:b.team_plan||null,remember:(b.team_plan?b.reminders:(b.loading_summary?.changes||b.reminders||[])).slice(0,3),origin:b.context?.origin||'ANALYSIS_ASSUMPTIONS_NOT_OBSERVATION'};
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

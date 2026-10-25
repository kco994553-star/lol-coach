/* Explicit review/scenario information. No IO, clock, observed-current inference or tactics. */
(function(root,factory){
  if(typeof module==='object'&&module.exports)module.exports=factory();
  else root.LoadingSituation=factory();
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const definitions=[
    ['ally_jungle','아군 정글 정보',{NEAR:'가까운 지역',AWAY:'다른 지역'}],
    ['enemy_jungle','상대 정글 정보',{NEAR:'가까운 지역',AWAY:'다른 지역'}],
    ['wave_direction','웨이브 방향',{EVEN:'중앙에서 만남',BUILDING:'아군 잔여가 쌓이며 전진',INCOMING:'상대 웨이브가 들어옴',UNDER_TOWER:'아군 포탑에 도착',RETURNING:'밀어 넣은 뒤 돌아옴'}],
    ['wave_size','상대 웨이브 압박',{NORMAL:'감당할 규모',LARGE:'크게 누적된 웨이브'}],
    ['wave_access','웨이브 조작 가능성',{READY:'처리·반격 대응과 퇴로를 남길 수 있음',DENIED:'나가서 처리할 여건 없음'}],
    ['wave_crash','포탑까지 밀어 넣을 여건',{READY:'도달·상대 처리·추가 웨이브 조건을 비교함',BLOCKED:'도달 조건이 부족함'}],
    ['resources','처리·교전 뒤 남길 자원',{SUFFICIENT:'관련 체력·마나·기술 예산을 남길 수 있음',LOW:'남길 자원이 부족함'}],
    ['ally_followup','아군 호응',{AVAILABLE:'같은 적에게 호응할 수 있음',UNAVAILABLE:'호응할 수 없음'}],
    ['combat_context','교전 문맥',{DUEL:'1대1',DUO:'2대2',GANK:'갱',COUNTERGANK:'역갱',RIVER_JUNGLE:'강·정글 싸움',PICK_CHASE:'잘라먹기·추격',OBJECTIVE:'오브젝트 전투',TEAMFIGHT:'팀 단위 한타'}],
    ['ally_contribution','아군의 실제 기여',{READY:'공격·보호에 기여할 수 있음',LIMITED:'기여가 제한됨',UNAVAILABLE:'기여할 수 없음'}],
    ['enemy_contribution','상대의 실제 기여',{READY:'공격·보호에 기여할 수 있음',LIMITED:'기여가 제한됨',UNAVAILABLE:'기여할 수 없음'}],
    ['arrival_order','합류 순서',{ALLY_FIRST:'아군이 먼저',EVEN:'비슷한 순서',ENEMY_FIRST:'상대가 먼저'}],
    ['threat_reach','대응할 위협의 도달성',{REACHABLE:'나 또는 보호 대상에 닿을 수 있음',UNREACHABLE:'이번 위치에 닿기 어려움'}],
    ['ally_carry_risk','아군 딜러 보호 필요',{THREATENED:'아군 딜러가 위협받음',COVERED:'아군 딜러 보호가 연결됨'}],
    ['enemy_carry_access','상대 딜러 방해 가능성',{DISRUPTABLE:'아군과 연결해 공격을 방해할 수 있음',UNREACHABLE:'연결해서 방해할 위치가 아님'}],
    ['combat_space','교전 지형·퇴로',{OPEN:'행동과 퇴로를 함께 확보할 수 있음',RESTRICTED:'지형·퇴로로 행동이 제한됨'}],
    ['key_skill','이번 행동의 핵심 기술',{AVAILABLE:'배웠고 행동에 남길 수 있음',SPENT:'이번 행동에 남길 수 없음'}]
  ];
  const fields=definitions.map(([key,label,options])=>Object.freeze({key,label,options:Object.freeze(options)}));
  const clone=x=>JSON.parse(JSON.stringify(x));
  const text=x=>typeof x==='string'&&x.trim().length>0&&x.length<=240;
  const object=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
  const exact=(x,keys)=>object(x)&&Object.keys(x).sort().join('|')===[...keys].sort().join('|');
  const fail=()=>{throw Error('SITUATION_INVALID: 상황 정보의 상태·값·출처·관측 시각을 확인해 주세요.');};
  function defaultState(mode='PRE_GAME'){
    if(!['PRE_GAME','REVIEW'].includes(mode))fail();
    return {schema_version:'lol-coach-situation-v1',mode,fields:Object.fromEntries(fields.map(f=>[f.key,{status:'unknown',value:null,source:null,observed_at:null}]))};
  }
  function validTime(x){return typeof x==='string'&&/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?Z$/.test(x)&&Number.isFinite(Date.parse(x))&&new Date(x).toISOString().slice(0,19)===x.slice(0,19);}
  function validate(raw){
    if(!exact(raw,['schema_version','mode','fields'])||raw.schema_version!=='lol-coach-situation-v1'||!['PRE_GAME','REVIEW'].includes(raw.mode)||!exact(raw.fields,fields.map(f=>f.key)))fail();
    for(const field of fields){
      const info=raw.fields[field.key];
      if(!exact(info,['status','value','source','observed_at'])||!['observed','assumed','unknown','stale'].includes(info.status))fail();
      if(info.status==='unknown'){if(info.value!==null||info.source!==null||info.observed_at!==null)fail();continue;}
      if(!Object.hasOwn(field.options,info.value)||!text(info.source))fail();
      if(info.status==='assumed'){if(info.observed_at!==null)fail();}
      else if(raw.mode!=='REVIEW'||!validTime(info.observed_at))fail();
    }
    return clone(raw);
  }
  // Historical evidence has unverified per-datum freshness. Only explicit
  // scenario assumptions can supply executable hypothetical values in v1.
  function effective(info){return info?.status==='assumed'?info.value:null;}
  function project(raw){
    const state=validate(raw),out={};
    for(const field of fields){const info=state.fields[field.key];out[field.key]={...info,effective:effective(info),label:field.label,freshness:['observed','stale'].includes(info.status)?'UNVERIFIED_HISTORICAL':'NOT_APPLICABLE'};}
    return {schema_version:'lol-coach-situation-projection-v1',mode:state.mode,label:state.mode==='REVIEW'?'과거 자료 복기 · 현재 관측 아님':'경기 전 선택 가정 · 실제 관측 아님',live_coaching_enabled:false,fields:out};
  }
  return Object.freeze({fields:Object.freeze(fields),defaultState,validate,effective,project});
});

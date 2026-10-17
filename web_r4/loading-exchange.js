/* Relative trade-length candidates from preserved properties, never matchup-win models. */
(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.LoadingExchange=factory();})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 const classifications={SHORT_ADVANTAGE:'짧은 교환 우세',SUSTAINED_ADVANTAGE:'지속 교전 우세',CONDITIONAL:'조건부',UNKNOWN:'미확인'};
 const defs=[{key:'window',label:'공격 효과·다음 수단 가정',options:{UNKNOWN:'미확인',HIT_WINDOW:'단발 적중·발동 기회가 열린 가정',REPEAT_ACTIVE:'관련 강화·반복 후속 수단이 남은 가정',ENDED:'이번 효과·사용할 기회가 끝난 가정'}},{key:'cover',label:'보호 효과 가정',options:{UNKNOWN:'미확인',ACTIVE:'지정한 대상에 보호 효과가 적용 중인 가정',ENDING:'그 보호 효과가 끝나는 순간 가정',SPENT:'보호 효과를 이번 교환에 남길 수 없는 가정'}},{key:'contact',label:'공격 거리·연결 가정',options:{UNKNOWN:'미확인',CONNECTED:'공격·동료 연결과 이탈을 계속 비교할 여건',BREAKING:'더 붙거나 후속을 이을 조건이 끊기는 순간'}}];
 const defaultState=()=>({ours:Object.fromEntries(defs.map(d=>[d.key,'UNKNOWN'])),theirs:Object.fromEntries(defs.map(d=>[d.key,'UNKNOWN']))});
 function stateOf(raw){const s=raw||defaultState();if(!s||Object.keys(s).sort().join('|')!=='ours|theirs')throw Error('양쪽 교환 길이 가정을 확인해 주세요.');for(const side of ['ours','theirs']){if(!s[side]||Object.keys(s[side]).sort().join('|')!=='contact|cover|window')throw Error('교환 효과·보호·거리 가정을 확인해 주세요.');for(const d of defs)if(!Object.hasOwn(d.options,s[side][d.key]))throw Error('교환 길이 가정은 목록 또는 미확인만 지원합니다.');}return JSON.parse(JSON.stringify(s));}
 function evaluate(report,catalog,g,raw){
  const state=stateOf(raw),supported=g.supported===true,yunara=g.matchup==='Yunara_Lulu__Lucian_Nautilus',early=['LEVEL1','LEVEL2'].includes(g.state.milestone),valid=g.scenario_valid!==false;
  if(!supported){
   const neutral=()=>({evidence_ids:[],classification:'UNKNOWN',label:classifications.UNKNOWN,mode:'UNKNOWN',preferred_exchange:'미확인 · 이 조합의 교환 길이 비교는 미지원',reason:'이 조합·배치·패치에 연결된 비교 규칙이 없습니다. 다른 조합의 선호나 공격 절차를 대신 쓰지 않습니다.',start_conditions:[],attack_order:[],end:[],continue_if:[],reply_alternative:'관련 조합의 근거와 실행 조건이 필요합니다.',cover_owner:null,cover_target:null,intent:'UNKNOWN',short_may_only_limit_loss:false,mechanism_inference:'UNSUPPORTED',actual_relative_superiority:'UNVERIFIED',actual_matchup_advantage:g.advantage});
   return {schema_version:'exchange-preference-v1',supported:false,state,observation:'HYPOTHETICAL',milestone:g.state.milestone,ours:neutral(),theirs:neutral(),actual_matchup_advantage:g.advantage,all_in_supported:false,chase_supported:false,attack_gate:'UNCHANGED',wave:{adoption:'UNSUPPORTED',cost:'교환 길이를 근거로 현재 웨이브 계획을 바꾸지 않습니다.',minion_effect:'미확인',avoid_opponent_pattern:'미확인'},evidence:{grade:'UNSUPPORTED',facts:[],matchup_comparisons:0,scope:'관련 조합의 비교 규칙과 직접 근거가 필요합니다.',question_ids:[],coaching_n:0}};
  }
  const fn=(champ,slot)=>{const f=catalog.champions[champ]?.facts.find(f=>f.slot===slot);return f?catalog.champions[champ].name+'의 '+f.name+'('+slot+')':'공식 수단 미확인';};
  const ourCarry=yunara?'Yunara':'Caitlyn',ourSupport=yunara?'Lulu':'Lux',enemyCarry=yunara?'Lucian':'Kaisa';
  const explicitStop=state.ours.window==='ENDED'||['ENDING','SPENT'].includes(state.ours.cover)||state.ours.contact==='BREAKING';
  const attackGate=supported&&explicitStop?'NO_ADDITIONAL_ATTACK':'UNCHANGED';
  function sidePlan(side){
   const s=state[side],ours=side==='ours',carry=ours?ourCarry:enemyCarry,coverOwner=ours?ourSupport:'Nautilus';
   const cover=ours?fn(ourSupport,yunara?'E':'W'):fn('Nautilus','W');
   const negative=ours&&g.wave_constraint==='LIMIT_EXPOSURE',ending=s.window==='ENDED'||['ENDING','SPENT'].includes(s.cover)||s.contact==='BREAKING'||negative;
   let mode='UNKNOWN',classification='UNKNOWN';
   if(supported&&valid&&!early&&s.window!=='UNKNOWN'){
    if(ending)mode='SHORT';
    else if(s.window==='HIT_WINDOW'&&s.contact==='CONNECTED')mode='SHORT';
    else if(s.window==='REPEAT_ACTIVE'&&s.cover==='ACTIVE'&&s.contact==='CONNECTED'&&(!ours||yunara))mode='REPEATED';
    if(mode!=='UNKNOWN')classification='CONDITIONAL';
   }
   const ownReasons=yunara?[
    fn('Yunara','Q')+'에는 공격 속도·적중 추가 피해·주변 확산이 있고, '+fn('Lulu','P')+'는 따라가는 대상의 공격에 반응합니다. '+cover+'의 보호가 남는 동안 반복 공격을 비교할 기전은 있습니다.',
    fn('Lulu','W')+'를 아군 강화에 쓰는 선택과 상대의 공격·시전을 제한하는 선택은 나눠야 합니다. 이 성질만으로 상대보다 지속 피해가 높다고 판정하지 않습니다.'
   ]:[
    fn('Caitlyn','P')+'는 '+fn('Caitlyn','W')+' 또는 '+fn('Caitlyn','E')+' 조건에 반응하며, '+fn('Lux','P')+'도 기술 적중 뒤 별도 기본 공격 조건이 있습니다.',
    '이 발동 기회를 제한된 후속으로 쓰는 후보와, 계속 기본 공격을 누적하는 선택은 다릅니다. 기본 공격을 반복할 수 있다는 사실만으로 지속 교전 선호를 확정하지 않습니다.'
   ];
   const enemyReasons=yunara?[
    fn('Lucian','P')+'는 스킬 뒤 다음 공격을 강화합니다. 한 번의 기술→공격 창으로 끊을 수도 있고, 다음 기술이 실제 남아 있으면 다시 기술→공격을 연결할 수도 있습니다.',
    fn('Lucian','E')+'는 지속 효과 공격으로 재사용 대기시간이 줄어드는 성질이지 즉시 다시 이동할 수 있다는 증거는 아닙니다. '+fn('Nautilus','W')+'의 보호 대상은 노틸러스 자신이며 루시안이 아닙니다.'
   ]:[
    fn('Kaisa','P')+'는 반복 공격·아군 이동 불가에 중첩이 쌓이고, '+fn('Kaisa','E')+'는 이동 속도 뒤 공격 속도가 증가합니다. 이 상태와 후속이 남으면 반복 공격을 원하는 후보가 됩니다.',
    fn('Nautilus','W')+'는 노틸러스 자신의 보호막과 그동안의 공격 효과입니다. 카이사의 보호막으로 합치거나 중첩만으로 올인 피해를 확정하지 않습니다.'
   ];
   let reason=(ours?ownReasons:enemyReasons).join(' ');
   if(ending)reason+=' 선택한 종료 사건 뒤 길게 붙는 대신 이미 시작한 교환을 끊는 후보입니다. 두 방식 모두 불리하고 짧게 끝내는 편이 손실을 덜 남길 가능성도 있으며, 그 크기는 검증하지 않았습니다.';
   if(mode==='SHORT'&&!ending)reason+=' 이번 가정은 한 적중·발동 기회이며 다음 반복까지 보장하지 않아, 그 기회 뒤 끊는 후보를 비교합니다.';
   if(mode==='UNKNOWN')reason+=(early?' 이 구간의 실제 기술 투자 조합을 확인하지 않아 길이 선호는 미확인입니다.':' 효과·보호·거리 가정 또는 직접 비교 근거가 부족해 상대적으로 나은 길이는 아직 미확인입니다.');
   const start=[ours?'관련 기술을 실제 배워 가용하고 양쪽 남은 반격·우리 자원·동료 후속·미니언/포탑 노출·외부 개입과 퇴로를 비교한 가정에서만 후보를 실행합니다.':'상대가 관련 기술·자원과 후속 거리를 남겨 둔 경우의 가능성입니다. 상대 실제 의도·체력/마나·다음 가용 수단은 미확인입니다.',cover+'의 적용 대상과 남은 효과를 구분합니다. 보호 종료나 강화 종료를 실제 게임 관측으로 기록하지 않습니다.'];
   let order;
   if(ending){order=[ours?'추가 공격을 시작하지 않고 이미 시작한 교환을 마무리합니다.':'다음 공격을 자동으로 잇는다고 가정하지 않고, 상대가 연결을 끊거나 다른 수단으로 바꿀 가능성을 봅니다.',ours?'공격에 쓴 수단을 이탈에 다시 세지 말고 남은 이동·보호와 동료 거리를 확인합니다.':'보호가 끝나도 기본 공격·다른 기술은 남을 수 있습니다. 효과 종료를 상대 무력화로 읽지 않습니다.',ours?'현재 받을 수급·웨이브 처리 범위로 목표를 바꿉니다. 무리하게 붙는 대신 잃을 CS·공간과 회복/귀환을 비교합니다.':'상대가 물러나면 추격 대신 우리 CS·처리 공간을 비교합니다. 실제 위치·미니언·추가 인원이 맞는지는 별도입니다.'];}
   else if(ours&&yunara){order=[fn('Lulu','E')+'의 아군 보호가 닿아 남는지 보고, '+fn('Lulu','W')+'는 아군 강화와 상대 제약 중 어느 용도로 남길지 나눕니다.',mode==='SHORT'?fn('Yunara','W')+' 등의 적중 뒤 이번에 닿는 공격 기회만 비교하고 다음 반복을 자동으로 시작하지 않습니다. '+fn('Yunara','Q')+' 강화 반복은 별도 조건입니다.':fn('Yunara','Q')+' 강화와 후속 거리·처리/대응 예산이 남는 동안, 닿는 대상의 기본 공격을 반복할 후보를 비교합니다. 누구를 이기는지는 미확인입니다.',fn('Yunara','E')+' 등 남길 이동 수단과 룰루 연결을 지키고, 확산 공격이 원래 웨이브 목표를 깨면 추가 공격 대신 처리량·대상을 바꿉니다.'];}
   else if(ours){order=[fn('Lux','Q')+' 실제 적중 뒤 '+fn('Caitlyn','W')+' 설치·발동과 후속 거리가 맞는 경우를 따로 확인합니다. 적중만으로 덫 후속이 확정되지 않습니다.',fn('Caitlyn','W')+' 또는 '+fn('Caitlyn','E')+'가 만든 조건의 '+fn('Caitlyn','P')+' 공격 후보를 비교합니다. '+fn('Lux','P')+' 추가 공격은 럭스가 실제로 들어갔다 나올 수 있을 때만 비교합니다.',fn('Caitlyn','E')+'를 이미 공격에 썼다면 다시 이탈 수단으로 세지 않습니다. 남은 동료 연결과 받을 수급 범위로 바꾸며, 다음 발동을 기다리겠다고 추격하지 않습니다.'];}
   else if(yunara){order=[fn('Lucian','Q')+' 등 배워 가용한 기술 뒤 '+fn('Lucian','P')+' 공격을 잇는 가능성을 비교합니다. 실제 적중·노출 비용은 별도입니다.',mode==='REPEATED'?'다음 기술과 자원이 실제 남아 있을 때만 다시 기술→강화 공격을 연결할 후보입니다. 재사용 대기시간을 임의 계산해 순서를 보장하지 않습니다.':'이번 강화 공격 창을 사용한 뒤 다음 기술·자원이 남았는지 다시 봅니다. 공격 뒤 아무 피해도 없다고 가정하지 않습니다.',fn('Lucian','E')+'를 앞으로 썼다면 즉시 이탈에 다시 쓰는 것으로 세지 않습니다. '+fn('Nautilus','P')+' 등 남은 반격과 동료 거리를 별도로 봅니다.'];}
   else{order=[fn('Kaisa','E')+'의 실제 상태와 '+fn('Kaisa','P')+' 중첩·후속 기회가 남는 조건을 비교합니다. 이동 속도 구간과 공격 속도 구간을 같다고 보지 않습니다.',fn('Kaisa','Q')+'·'+fn('Kaisa','W')+' 뒤 추가 기본 공격 또는 다음 수단이 남는지 봅니다. 발동 횟수·처치 피해·가용 시각은 만들지 않습니다.',fn('Nautilus','W')+'의 자기 보호가 끝나거나 카이사와 연결이 끊기면 상대 계획도 바뀔 수 있습니다. 물러나는 상대를 쫓을 허가는 아닙니다.'];}
   if(!valid||early)order=['이 구간의 기술 투자·가용 조합이 확인되지 않아 구체적인 공격 순서를 채택하지 않습니다. 실제 배운 수단과 양쪽 후속·퇴로를 확인한 뒤 해당 구간의 후보를 다시 비교합니다.'];
   const end=[carry==='Yunara'?fn('Yunara','Q')+' 강화가 종료되거나 보호 효과·후속/공격 거리가 끊기면 이번 반복을 끝내고 다시 비교합니다.':'선택한 공격 발동 기회가 소모되거나 다음 가용 수단이 없고 보호·후속 거리가 끊기면 이번 교환을 끝내고 다시 비교합니다.',cover+'의 종료, 남은 상대 제어가 열림, 미니언/포탑 노출·증원 또는 처리/이탈 자원 부족은 전환 사건입니다. 공통 초 수로 정하지 않습니다.'];
   const extend=['다음 공격·강화·보호 수단이 실제 남고 양쪽 후속·퇴로·자원·미니언/포탑 노출이 다시 맞을 때만 추가 교환을 비교합니다.','이어서 공격할 수 있다는 조건은 올인·추격 승리 또는 전체 피해 우위가 아닙니다.'];
   const alternative=ours?'상대가 접근·제어·맞견제로 끊으면 추가 공격 대신 남은 보호·이동을 수급 복귀에 남깁니다. 상대 반격 창이 살아 있는 동안 무리하게 붙지 않고, 상대가 CS를 먹는 동안 얻을 처리·공간과 포기할 자원을 비교합니다.':'상대가 원하는 기술→공격 또는 중첩 연속을 끊을 수 있는 거리·동료 연결을 먼저 비교합니다. 그 조건이 없으면 공격을 유도하러 전진하지 않고 CS 처리·자원 보존으로 바꿉니다. 미니언만으로 접근이 막힌다고 단정하지 않습니다.';
   const evidenceIds=(ours?(yunara?['Yunara:Q','Yunara:W','Yunara:E','Lulu:P','Lulu:W','Lulu:E']:['Caitlyn:P','Caitlyn:W','Caitlyn:E','Lux:P','Lux:Q','Lux:W','Lux:E']):(yunara?['Lucian:P','Lucian:Q','Lucian:E','Nautilus:P','Nautilus:W']:['Kaisa:P','Kaisa:Q','Kaisa:W','Kaisa:E','Nautilus:W'])).map(id=>'official:'+id);
   return {evidence_ids:evidenceIds,classification,label:classifications[classification],mode,preferred_exchange:classification==='CONDITIONAL'?(mode==='REPEATED'?'조건부 · 효과가 남는 동안 반복 공격 후보':'조건부 · 한 기회만 쓰거나 이미 시작한 교환을 짧게 끝내는 후보'):'미확인 · 교전 길이 우위를 정하지 않음',reason,start_conditions:start,attack_order:order,end,continue_if:extend,reply_alternative:alternative,cover_owner:coverOwner,cover_target:ours?ourCarry:'Nautilus',intent:'UNKNOWN',short_may_only_limit_loss:mode==='SHORT'&&ending,mechanism_inference:'DESIGN_HYPOTHESIS',actual_relative_superiority:'UNVERIFIED',actual_matchup_advantage:g.advantage};
  }
  const ours=sidePlan('ours'),theirs=sidePlan('theirs');
  const minions=yunara?fn('Yunara','Q')+'는 주변 확산으로 웨이브 처리량을 바꿀 수 있습니다. '+fn('Lulu','P')+'의 광선은 다른 유닛이 대신 맞을 수 있어 실제 닿는 피해를 확인해야 합니다.':fn('Lux','E')+' 등 처리 수단을 교환에 쓰면 원래 처리·방어 예산이 바뀝니다. 상대 미니언과 포탑의 실제 영향은 분포·위치·대상 없이는 정하지 않습니다.';
  const reset=g.wave_goal==='RESET';
  return {schema_version:'exchange-preference-v1',supported,state,observation:'HYPOTHETICAL',milestone:g.state.milestone,ours,theirs,actual_matchup_advantage:g.advantage,all_in_supported:false,chase_supported:false,attack_gate:attackGate,wave:{adoption:reset?'WITHHELD_FOR_RESET':attackGate==='NO_ADDITIONAL_ATTACK'?'NO_ADDITIONAL_ATTACK':'KEEP_EXISTING_GATES',cost:reset?'상대보다 교환이 유리하더라도 귀환을 위한 처리·이탈 자원과 밀어 넣을 시간을 잃으면 이번 공격을 채택하지 않습니다. 상대적 길이 후보와 실행 선택은 다릅니다.':'교환에 쓰는 기술·마나·앞으로 나가는 노출과 웨이브 처리·복귀 비용을 함께 비교합니다. 처리 속도와 포탑 도착 완료는 별도입니다.',minion_effect:minions,avoid_opponent_pattern:theirs.mode==='REPEATED'?'상대 중첩·다음 강화 공격이 이어지는 거리에 계속 머물지 않을 조건을 비교합니다. 동료·퇴로가 없으면 이를 끊으려 무리하게 전진하지 않습니다.':'상대 기술→추가 공격 창이 열린 동안 같은 길이의 교환을 강요하지 않습니다. 다음 수단이 실제 소모된 뒤 남은 반격과 CS·처리 공간을 다시 비교합니다.'},evidence:{grade:'DESIGN_HYPOTHESIS',facts:supported?g.evidence.facts.filter(f=>new Set([...ours.evidence_ids,...theirs.evidence_ids]).has(f.id)):[],matchup_comparisons:0,scope:'공식 기전에서 만든 조건부 계획. 실제 매치업의 짧은/지속 우열·피해 공백 길이·승리 조건 근거는 미연결.',question_ids:g.evidence.question_ids,coaching_n:0}};
 }
 function constrainEngagement(g,x){if(x.attack_gate!=='NO_ADDITIONAL_ATTACK')return g;const next=JSON.parse(JSON.stringify(g));next.actions=next.actions.filter(p=>p.id!=='SHORT_WINDOW');if(next.selected_action_id==='SHORT_WINDOW')next.selected_action_id=next.actions.find(p=>p.id==='CS_WINDOW')?.id||next.actions[0].id;next.exchange_gate=x.attack_gate;next.selection_reason+=' 교환 종료 가정 때문에 추가 공격 후보를 제외하고 남은 수급·처리 후보를 비교합니다.';return next;}
 function waveMeans(means,x){return x.attack_gate==='NO_ADDITIONAL_ATTACK'?{...means,selected_plan_id:'PREPARE_WINDOW'}:means;}
 return {classifications,defs,defaultState,evaluate,constrainEngagement,waveMeans};
});

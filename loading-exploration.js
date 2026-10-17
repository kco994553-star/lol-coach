/* Future-condition decisions. A user's preference is not an observation or evidence. */
(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.LoadingExploration=factory();})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const clone=x=>JSON.parse(JSON.stringify(x));
  const riskNames={LOSS_LIMIT:'손실 제한 우선',BALANCED:'균형',OPPORTUNITY:'기회 추구 우선'};
  const milestones=['LEVEL1','LEVEL2','LEVEL3_5','LEVEL6','FIRST_PURCHASE','FIRST_CORE'];
  const dimensions=['survival_exposure','resources','growth','position_wave','time_objectives','options'];
  const dimensionNames={survival_exposure:'생존·노출',resources:'체력·마나·스킬',growth:'골드·경험치',position_wave:'위치·웨이브',time_objectives:'시간·목표물',options:'남는 선택권'};
  const conditionDefs=[
    {key:'binding',label:'럭스의 빛의 속박(Q) 결과 가정',options:{UNKNOWN:'미확인',HIT:'적 챔피언 적중',MISS:'빗나감 / 가용성 상실'}},
    {key:'followup',label:'덫 후속 실행 조건 가정',note:'스킬 습득·가용성, 설치·발동·공격 거리, 체력·자원·웨이브를 함께 확인한 가정',options:{UNKNOWN:'미확인',READY:'모두 충족',UNAVAILABLE:'하나 이상 불충족'}},
    {key:'exit_cover',label:'동료 연결·상대 대응·퇴로 가정',note:'럭스와 연결되고 노틸러스·카이사의 대응을 감당할 이탈 공간이 있는 가정',options:{UNKNOWN:'미확인',AVAILABLE:'연결·퇴로 충족',BROKEN:'연결 또는 퇴로 끊김'}}
  ];
  const neededFacts=['official:Lux:Q','official:Caitlyn:W','official:Nautilus:Q','official:Nautilus:P','official:Kaisa:Q'];
  const defaultState=()=>({milestone:'LEVEL2',assumptions:{binding:'UNKNOWN',followup:'UNKNOWN',exit_cover:'UNKNOWN'}});
  function stateOf(raw){
    const s=raw||defaultState();
    if(!s||Object.keys(s).sort().join('|')!=='assumptions|milestone'||!milestones.includes(s.milestone)||!s.assumptions||Object.keys(s.assumptions).sort().join('|')!=='binding|exit_cover|followup')throw Error('탐색 구간과 가상 조건을 확인해 주세요.');
    for(const def of conditionDefs)if(!Object.hasOwn(def.options,s.assumptions[def.key]))throw Error('가상 조건은 미확인 또는 목록의 값으로 선택해 주세요.');
    return clone(s);
  }
  function mapFor(input,plan){
    const mirror=p=>input.side==='BLUE'?p:{x:p.y,y:p.x};
    const home={x:77,y:83},meeting={x:80,y:78},resource={x:70,y:84},ally={x:73,y:79};
    const end=plan.id==='SHORT_FOLLOW'?meeting:plan.id==='RECEIVE_WITH_LUX'?resource:home;
    const steps=plan.steps,attack=plan.id==='SHORT_FOLLOW',receive=plan.id==='RECEIVE_WITH_LUX';
    const arrows=attack?[{step:2,kind:'PRESSURE',from:mirror(home),to:mirror(meeting)},{step:3,kind:'RETREAT',from:mirror(meeting),to:mirror(resource)}]:receive?[{step:2,kind:'MOVE',from:mirror(home),to:mirror(resource)}]:[];
    const landmarks=attack?[{id:'check',label:'1 적중·연결 점검 예시',...mirror(home),step:1}]:receive?[{id:'receiving',label:'1 받을 위치 후보 · 실제 웨이브 미확인',...mirror(resource),step:1},{id:'reassess',label:'3 다음 연결 재비교',...mirror(ally),step:3}]:[{id:'check',label:'1 화면 정보 점검',...mirror(home),step:1},{id:'resource',label:'2 받을 위치 후보 비교 · 이동 지시 아님',...mirror(resource),step:2},{id:'reassess',label:'3 연결·회복 재비교',...mirror(ally),step:3}];
    return {plan:{id:plan.id,direction:plan.objective,steps},map:{context:'LANE',asset:'direction-assets/map11.png',caption:'전술 설명용 예시 · 케이틀린·럭스 레벨 2 · 전 위치는 가정이며 현재 관측 아님',entities:[{id:'self',team:'ALLY',self:true,champion:'Caitlyn',start:mirror(home),target:plan.id==='PREPARE_WINDOW'?null:mirror(end)},{id:'lane-peer',team:'ALLY',self:false,champion:'Lux',start:mirror(ally),target:null}],arrows,landmarks,notes:['적 위치는 미확인이므로 적 초상화를 표시하지 않습니다.','숫자는 행동 순서입니다. 점검 표시는 이동 지시가 아닙니다. 화살표는 안전 경로·정확한 스킬 사거리나 전술 효과의 검증이 아닙니다.','이 배치는 대표 매치업의 조건부 선택을 설명하는 설계 가설입니다.']}};
  }

  function candidates(a){
    const positive=a.binding==='HIT'&&a.followup==='READY'&&a.exit_cover==='AVAILABLE';
    const negative=a.binding==='MISS'||a.followup==='UNAVAILABLE'||a.exit_cover==='BROKEN';
    const shared={evidence_ids:neededFacts,opponent_response:['노틸러스의 닻줄 견인(Q) 또는 기본 공격 속박과 카이사 후속이 열리면 전진을 끝내고 받을 위치를 바꿉니다.'],next_if_unknown:['실제 적중·스킬 가용성·동료 거리·상대 대응을 화면에서 다시 보고, 확인하려고 혼자 앞으로 나가지 않습니다.'],scope:'HYPOTHETICAL_NOT_OBSERVED',level:'DESIGN_HYPOTHESIS'};
    const make=(id,title,objective,steps,requirements,abort,costs,dim,feasibility)=>({...clone(shared),id,title,objective,gain:objective,steps:steps.map((s,i)=>({number:i+1,action_id:s[0],text:s[1]})),requirements,abort,costs,dimensions:Object.fromEntries(dimensions.map((k,i)=>[k,{text:dim[i],evidence_ids:neededFacts,level:'DESIGN_HYPOTHESIS'}])),feasibility});
    return [
      make('SHORT_FOLLOW','짧은 후속 공격','적중한 제어를 제한된 공격 기회로 바꾸기',[
        ['OBSERVE_BIND_AND_EXIT','럭스의 빛의 속박(Q) 실제 적중과 럭스 연결·상대 두 명의 대응·퇴로를 함께 봅니다.'],
        ['SET_TRAP_FOLLOW','케이틀린의 요들잡이 덫(W) 설치 위치·발동·공격 거리가 맞는 경우만 짧은 후속을 잇습니다.'],
        ['END_FOLLOW','덫 연결·동료 거리·퇴로가 끊기면 추격을 접고 럭스 쪽 받을 위치로 돌아옵니다.']
      ],['속박이 적 챔피언에게 적중한 가정','덫 습득·가용성·설치·발동·거리·자원·웨이브가 맞는 가정','상대 대응을 감당할 동료 연결·퇴로가 있는 가정'],['속박 빗나감·덫 발동 불명확','노틸러스 접근·카이사 후속 또는 추가 인원','럭스 연결이나 퇴로 상실'],['덫과 공격 시간·자원을 소모하며 전진 노출이 생깁니다.','교환하는 동안 미니언·복귀 기회를 놓칠 수 있고 피해 우열은 모릅니다.'],['전진 노출과 상대 역대응 가능; 생존 보장 없음','덫과 후속 공격 자원 소모','CS 손실과 교환 이득 크기는 미확인','전진 뒤 동료 연결·복귀선 필요','추격으로 시간/목표물을 더 잃을 수 있음','덫 소모 후 다른 접근 대응 선택권 감소'],positive?'POSSIBLE':negative?'IMPOSSIBLE':'UNKNOWN'),
      make('RECEIVE_WITH_LUX','동료와 수급선 유지','교환을 늘리기보다 접근 가능한 자원과 다음 연결을 남기기',[
        ['LIMIT_RESOURCE_TARGET','럭스와 연결되는 받을 위치를 고르고 이번에 포기할 미니언을 정합니다.'],
        ['CLAIM_NEAR_RESOURCE','상대 둘의 대응·자원을 보며 접근 가능한 미니언만 받고 억지 견제나 전진은 하지 않습니다.'],
        ['REASSESS_NEXT_WINDOW','상대 기술 사용·동료 연결·웨이브가 달라지면 다음 후속 또는 귀환 조건을 다시 비교합니다.']
      ],['럭스 연결과 상대 대응을 감당할 받을 위치·퇴로가 있는 가정'],['노틸러스가 수급선에 접근하거나 동료/퇴로 연결이 끊김','체력·자원/웨이브 변화로 같은 자리에서 받을 수 없음'],['속박 적중 기회를 공격으로 바꾸지 못할 수 있습니다.','상대에게 공간·웨이브 주도권을 내주거나 일부 CS를 잃을 수 있습니다.'],['전진은 줄이지만 수급선도 안전 보장 없음','공격용 스킬 소모를 줄이는 선택; 회복량 미확인','일부 미니언과 교환 기회를 포기할 수 있음','럭스와 같은 수급선 필요; 무조건 뒤로 걷는 지시 아님','상대가 이동/준비할 시간을 가질 수 있음','다음 연결에 쓸 기술/복귀 선택권을 남김'],a.exit_cover==='AVAILABLE'?'POSSIBLE':a.exit_cover==='BROKEN'?'IMPOSSIBLE':'UNKNOWN'),
      make('PREPARE_WINDOW','조건 확인·수급 목표 조정','불확실한 교환 대신 다음에 확인할 정보와 받을 자원 범위를 정하기',[
        ['CHECK_OBSERVABLE_WINDOW','실제 속박 적중·덫 가용성·럭스 거리·상대 대응 중 모르는 항목을 화면에서 구분합니다.'],
        ['REDUCE_RESOURCE_TARGET','모르는 구역으로 확인하러 가지 않고 보이는 아군 쪽 받을 위치와 포기할 자원을 비교합니다.'],
        ['REOPEN_OR_RESET','후속·퇴로 조건이 확인되면 다시 비교하고, 불충족이면 위치·회복·귀환 준비로 목표를 바꿉니다.']
      ],['확인 계획이며 이동/교환 성공을 전제하지 않음'],['정보가 더 없거나 추가 적 접근이 드러나면 같은 수급 위치를 고집하지 않음'],['기다리는 동안 CS·압박 기회와 시간을 잃을 수 있습니다.','대기·후퇴 자체도 상대 접근·다이브를 막는다는 보장은 없습니다.'],['미확인 공간에 직접 진입하지 않음; 현재 자리 안전 미확인','교환 자원 소모를 미루되 체력 손실 가능','지연 중 CS/경험치 포기 가능','현재 위치 고정이 아니라 관측 가능한 받을 위치 재비교','지연 중 상대 이동/목표 준비 가능','교환·수급·회복 선택을 다시 열기 위한 정보 확보'], 'POSSIBLE')
    ];
  }
  function choose(plans,risk){
    const possible=id=>plans.find(p=>p.id===id&&p.feasibility==='POSSIBLE');
    if(possible('SHORT_FOLLOW'))return risk==='LOSS_LIMIT'&&possible('RECEIVE_WITH_LUX')?'RECEIVE_WITH_LUX':'SHORT_FOLLOW';
    return possible('RECEIVE_WITH_LUX')?'RECEIVE_WITH_LUX':'PREPARE_WINDOW';
  }
  function evaluate(report,catalog,raw){
    const state=stateOf(raw),row=report.lane.rows.find(r=>r.id===state.milestone),risk=report.input.preferences?.risk||'BALANCED';
    if(!Object.hasOwn(riskNames,risk))throw Error('리스크 성향을 목록에서 선택해 주세요.');
    const factIds=new Set(Object.values(catalog.champions).flatMap(c=>c.facts).map(f=>f.id));
    const sourceMatch=report.input.patch&&report.input.patch.split('.').slice(0,2).join('.')===catalog.source_patch.split('.').slice(0,2).join('.');
    const supported=report.lane.matchup_id==='Caitlyn_Lux__Kaisa_Nautilus_v2'&&state.milestone==='LEVEL2'&&Boolean(sourceMatch)&&neededFacts.every(id=>factIds.has(id));
    const reason=state.milestone!=='LEVEL2'?'이 구간은 기존 설명 탐색만 지원합니다. 행동 간 실행 조건·비용 비교와 지도 규칙은 아직 연결하지 않았습니다.':!sourceMatch?'입력 패치가 미확인 또는 공식 자료와 다릅니다. 행동 비교를 실행 가능으로 제시하지 않습니다.':report.lane.matchup_id!=='Caitlyn_Lux__Kaisa_Nautilus_v2'?'이 상호작용은 케이틀린·럭스 대 카이사·노틸러스의 확정 포지션 예시만 지원합니다.':'필요한 공식 사실 연결이 없어 행동 비교를 지원하지 않습니다.';
    const plans=supported?candidates(state.assumptions):[],selected=plans.length?choose(plans,risk):null;
    const same=!supported||new Set(Object.keys(riskNames).map(r=>choose(plans,r))).size===1;
    const selection_reason=same?'현재 조건에서는 선택이 같습니다. '+(!supported?reason:selected==='PREPARE_WINDOW'?'후속·수급의 필수 조건이 미확인/불충족이라 성향으로 실행 가능하게 바꾸지 않습니다.':'실행 조건이 맞는 후속이 없어 동료와 수급선을 다시 보는 선택을 유지합니다.'):'두 안의 실행 조건을 충족한 가정입니다. '+(risk==='LOSS_LIMIT'?'공격 기회 일부를 포기하고 수급·남는 기술 선택권을 먼저 남깁니다.':'전진 노출·덫 소모를 감수하는 짧은 후속을 먼저 살펴봅니다. 최적 행동으로 검증된 것은 아닙니다.');
    const selectedPlan=plans.find(p=>p.id===selected);
    return {schema_version:'loading-exploration-v1',supported,unsupported_reason:supported?null:reason,state,row,preference:{risk,label:riskNames[risk],source:'USER_PREFERENCE'},assumption_status:'NOT_OBSERVED',plans,selected_plan_id:selected,selection_reason,same_choice_across_preferences:same,required_checks:[...conditionDefs.filter(d=>state.assumptions[d.key]==='UNKNOWN').map(d=>d.label),'실행 전에 가정한 기술·거리·자원을 실제 화면에서 다시 확인해야 합니다.'],unchanged_conditions:['상대 둘의 대응·내 체력/자원·웨이브와 추가 인원을 함께 확인해야 합니다.','성향·가상 조건 선택은 실제 관측이나 전략 검증이 아닙니다.'],evidence:{level:'DESIGN_HYPOTHESIS',sufficiency:supported?'CONDITIONAL':'INSUFFICIENT',assessment:'UNDETERMINED',official_scope:row?.fact_scope||'공식 기술의 성질만 확인된 범위입니다.',question_id:report.lane.matchup_id!=='Caitlyn_Lux__Kaisa_Nautilus_v2'?null:state.milestone==='LEVEL2'?'DUO-L2':state.milestone==='LEVEL3_5'?'DUO-L3_5':state.milestone==='LEVEL6'?'DUO-L6':null,counterexamples:report.lane.matchup_id==='Caitlyn_Lux__Kaisa_Nautilus_v2'&&state.milestone==='LEVEL2'?['속박은 맞아도 덫 발동 전에 벗어나거나 노틸러스 역대응 때문에 후속이 끊길 수 있습니다.','수급선 유지도 동료 연결·퇴로가 없으면 안전한 대안이 아닙니다.']:['가정한 기술·거리·자원이 다르면 기존 계획을 적용할 수 없습니다. 해당 구간의 실제 반례 장면은 아직 확보하지 않았습니다.'],real_coaching_n:0,accuracy:null},map_scenario:selectedPlan?mapFor(report.input,selectedPlan):null};
  }
  return Object.freeze({defaultState,evaluate,mapFor,riskNames,dimensionNames,conditionDefs});
});

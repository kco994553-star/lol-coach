/* Wave plans are explicit future hypotheses, never observed priority or simulations. */
(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.LoadingWave=factory();})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const clone=x=>JSON.parse(JSON.stringify(x));
  const periods=['LEVEL1','LEVEL2','LEVEL3_5','LEVEL6','FIRST_PURCHASE','FIRST_CORE'];
  const conditionDefs=[
    {key:'flow',label:'웨이브 흐름 가정',options:{UNKNOWN:'미확인',BUILDING:'아군 잔여가 유지되며 천천히 전진하는 흐름',INCOMING:'상대 웨이브가 우리 쪽으로 오는 중',UNDER_TOWER:'우리 포탑에 도착함',RETURNING:'밀어 넣은 뒤 돌아오는 흐름'}},
    {key:'access',label:'전진 처리 여건·자원 비용 가정',note:'양쪽 미니언 체력·위치, 내 체력·마나·가용 기술과 동료 거리, 방어에 남길 자원을 비교한 가정. 선푸시 우위 판정은 아님',options:{UNKNOWN:'미확인',READY:'처리와 대응 자원을 함께 남길 수 있음',DENIED:'앞으로 나가 처리할 여건 부족'}},
    {key:'response',label:'상대 방해를 감당할 수급·처리 공간 가정',note:'맞밀기·견제·진입에 따라 처리량·위치를 바꿀 여건과 퇴로가 있는지. 안전 보장은 아님',options:{UNKNOWN:'미확인',MANAGEABLE:'현재 계획의 처리·이탈 여건 있음',DISRUPTS:'방해로 유지가 어려움'}},
    {key:'purpose',label:'이번 웨이브 뒤 얻으려는 것',options:{UNKNOWN:'미확인',SPACE:'라인 공간과 다음 선택권 비교',RESET:'귀환 준비',STAY:'자원 수급과 라인 유지'}},
    {key:'crash',label:'상대 포탑까지 도달할 여건 가정',note:'잔여 미니언·상대 처리·증원·거리·시간을 별도로 확인한 가정. 빠른 처리만으로 충족되지 않음',options:{UNKNOWN:'미확인',READY:'모두 확인한 가정',BLOCKED:'하나 이상 부족'}}
  ];
  const defaultState=()=>({milestone:'LEVEL2',assumptions:Object.fromEntries(conditionDefs.map(d=>[d.key,'UNKNOWN']))});
  const preset=()=>({flow:'BUILDING',access:'READY',response:'MANAGEABLE',purpose:'SPACE',crash:'UNKNOWN'});
  const factIds=['official:Caitlyn:Q','official:Caitlyn:W','official:Lux:Q','official:Lux:E','official:Nautilus:Q','official:Nautilus:P','official:Kaisa:Q'];
  const periodFacts={LEVEL3_5:['official:Caitlyn:E','official:Lux:W'],LEVEL6:['official:Nautilus:R','official:Kaisa:R','official:Kaisa:P','official:Caitlyn:E']};
  const notes={
    LEVEL1:'레벨 1은 처리 수단을 점검하는 시점입니다. 케이틀린의 필트오버 피스메이커(Q)·럭스의 광휘의 특이점(E)를 배워 가용한 가정에서만 처리 비용을 비교합니다. 광역 기술만으로 먼저 밀거나 선레벨을 확정하지 않습니다.',
    LEVEL2:'레벨 2 자체가 푸시 우위는 아닙니다. 럭스의 빛의 속박(Q)·케이틀린의 요들잡이 덫(W)를 배운 경우에도, 후속에 쓰는 시간·자원이 웨이브 처리와 퇴로를 깨는지 먼저 봅니다.',
    LEVEL3_5:'케이틀린의 90구경 투망(E)·럭스의 프리즘 보호막(W)를 실제 배워 가용하면 처리 중 남길 대응 수단으로 비교합니다. 공격에 소모해 상대 진입을 감당하지 못하면 처리 목표부터 줄입니다.',
    LEVEL6:'노틸러스의 폭뢰(R)·카이사의 사냥본능(R)이 실제 가용하고 조건이 맞는 경우 접근 대응을 다시 봅니다. 큰 아군 웨이브나 케이틀린의 90구경 투망(E)만으로 제어가 사라진다고 가정하지 않습니다.',
    FIRST_PURCHASE:'첫 귀환은 실제 구매·회복·양쪽 복귀와 다음 웨이브를 확인한 뒤 처리 비용을 재비교하는 시점입니다. 구매 이름만으로 푸시 우위·최적 귀환을 확정하지 않습니다.',
    FIRST_CORE:'첫 핵심 아이템이 완성돼도 상대 구매·체력·인원·동료 연결을 다시 봅니다. 아이템 완성이 밀기나 합류의 자동 허가는 아닙니다.'
  };
  function stateOf(raw){
    const s=raw||defaultState();
    if(!s||Object.keys(s).sort().join('|')!=='assumptions|milestone'||!periods.includes(s.milestone)||!s.assumptions||Object.keys(s.assumptions).sort().join('|')!==conditionDefs.map(d=>d.key).sort().join('|'))throw Error('웨이브 구간과 가정 필드를 확인해 주세요.');
    for(const d of conditionDefs)if(!Object.hasOwn(d.options,s.assumptions[d.key]))throw Error('웨이브 가정은 미확인 또는 목록의 값으로 선택해 주세요.');
    return clone(s);
  }
  function punishment(plan,follow){
    const reset=plan.id==='FAST_PUSH'||plan.id==='CRASH';
    return [
      {trigger:'상대가 막타를 먹으러 나올 때',goal:reset?'처리 시간을 확보하고 귀환 준비 자원을 남기기':'수급 공간을 확보하되 웨이브 목표를 지키기',means:follow?'럭스의 빛의 속박(Q) 적중·덫 발동·후속 거리와 퇴로가 모두 맞는 가정에서만 케이틀린의 요들잡이 덫(W) 후속을 짧게 비교합니다.':'공격을 강제하지 않고 접근 가능한 미니언 처리나 현재 수급 공간을 먼저 사용합니다.',reply:'노틸러스의 닻줄 견인(Q)·기본 공격 속박과 카이사 후속이 열릴 수 있습니다.',end:'상대 접근·동료 연결 상실 또는 처리에 남길 자원이 줄면 교환을 끝냅니다.',wave_effect:reset?'추가 공격 때문에 잔여 처리·밀어 넣기가 늦어지면 응징보다 웨이브 처리를 우선합니다.':'견제가 미니언까지 맞아 원치 않게 빨리 밀리면 대상·처리량을 줄입니다.'},
      {trigger:'상대가 웨이브 처리에 핵심 기술을 쓴 것을 보았을 때',goal:'상대 의도가 아니라 실제 생긴 처리·수급 여유를 사용하기',means:'기술이 빠진 사실만으로 진입하지 않습니다. 남은 상대 수단·거리와 내 처리 예산이 맞으면 미니언 처리 또는 공간 확보를 비교합니다.',reply:'다른 기술·기본 공격·동료 후속으로 반격하거나 맞밀 수 있습니다. 재사용 시간은 임의로 계산하지 않습니다.',end:'반격 수단이나 추가 인원이 확인되거나 여유가 사라지면 전진을 중단합니다.',wave_effect:'교환보다 이번 계획에 필요한 처리·방어 자원을 남깁니다.'},
      {trigger:'상대가 우리 웨이브를 줄이거나 밀어 넣기를 막을 때',goal:'완료 불가능한 밀기를 고집하지 않고 손실을 줄이기',means:'남은 양쪽 미니언 체력·위치와 상대 처리 속도를 다시 보고, 감당할 처리만 하거나 아군 쪽 받을 위치로 목표를 바꿉니다.',reply:'상대가 맞밀기·견제·진입으로 전진 시간을 늘릴 수 있습니다.',end:'자원·동료 거리·퇴로가 부족하면 쌓기나 밀어 넣기 시도를 접습니다.',wave_effect:'상대 포탑 도착이 확인되기 전에는 Crash(밀어 넣기) 완료나 자유로운 귀환·이동으로 기록하지 않습니다.'},
      {trigger:'상대가 공간·주도권을 행사하지 않는 것이 확인될 때',goal:'싸움 없이 접근 가능한 CS·공간 또는 자원을 남기기',means:'현재 보이는 범위에서 받을 자원을 확보하거나 계획에 필요한 미니언만 처리합니다. 상대가 안 보인다는 이유로 빈 공간으로 나가지는 않습니다.',reply:'상대가 지연해 진입하거나 다른 인원과 돌아올 가능성은 미확인입니다.',end:'상대가 다시 전진하거나 시야·처리 여건이 바뀌면 공간 확보를 멈추고 재비교합니다.',wave_effect:'불필요한 기술 소모를 줄이고 다음 처리·복귀 선택을 남깁니다.'}
    ];
  }
  function plansFor(a){
    const ready=a.access==='READY'&&a.response==='MANAGEABLE',building=a.flow==='BUILDING',knownPurpose=a.purpose!=='UNKNOWN';
    const status=(yes,blocked)=>yes?'POSSIBLE':blocked?'IMPOSSIBLE':'UNKNOWN';
    const specs=[
      ['SLOW_PUSH','천천히 쌓아 밀기',ready&&building&&['SPACE','STAY'].includes(a.purpose),a.flow!=='UNKNOWN'&&!building,
       '아군 잔여를 유지하며 이후 처리·공간 선택을 남기기','아군 잔여가 살아남아 전진하는 흐름과 처리·대응 예산을 확인한 가정',
       '막타 중심으로 처리하되 양쪽 잔여 미니언 체력·위치와 감소 방향을 봅니다. 아군 잔여가 사라지면 처리량을 무작정 늘려 쌓기라고 부르지 않습니다.',
       '케이틀린의 필트오버 피스메이커(Q)·럭스의 광휘의 특이점(E)를 배워 가용해도 매번 웨이브에 쓰지 않습니다. 원치 않는 동시 피해와 방어 자원 소모를 피하는 가설입니다.',
       '상대가 줄이거나 맞밀 때 아군 잔여와 동료 연결을 계속 비교합니다. 유지가 안 되면 쌓기 계획을 바꿉니다.',
       '의도한 잔여·전진 흐름을 확인하면 다음 빠른 처리나 유지 선택을 재비교합니다. 포탑 도착은 별도 완료 조건입니다.',
       '상대 처리로 잔여가 사라짐·견제 손실·추가 인원으로 전진 여건 상실','쌓기 실패 시 무리한 교환 대신 받을 위치·자원 목표를 줄여 다시 비교',
       ['기다리는 동안 상대가 잔여를 줄이거나 공간을 사용할 수 있습니다.','완료·귀환 시각을 보장하지 않으며 방어·마나 예산을 계속 남겨야 합니다.']],
      ['FAST_PUSH','빠르게 처리하기',ready&&building&&['SPACE','RESET'].includes(a.purpose),a.access==='DENIED'||a.response==='DISRUPTS',
       '현재 잔여 처리 시간을 줄여 공간·귀환 준비를 비교하기','가용 기술·자원과 상대 방해를 감당하며 처리할 수 있는 가정',
       '양쪽 미니언 체력·위치에 맞춰 처리 대상을 고르고, 실제 잔여 감소와 상대 맞처리를 보며 처리량을 조절합니다. 원거리 기술은 배워 가용한 경우만 비교합니다.',
       '케이틀린의 필트오버 피스메이커(Q)·럭스의 광휘의 특이점(E)를 처리에 쓸 경우 체력·마나·대응 기술의 남는 예산을 봅니다. 견제와 처리에 같은 자원을 두 번 계산하지 않습니다.',
       '상대가 버티거나 새 웨이브가 만나면 다시 비교합니다. 빠른 처리 능력과 먼저 미는 우위는 다릅니다.',
       '정한 잔여 처리 완료를 실제 확인합니다. 상대 포탑 도착이나 Crash 완료는 아직 미확인입니다.',
       '딜교환 소모로 잔여를 처리하지 못함·상대 맞처리·동료 연결 상실','포탑까지 못 넣으면 자동 귀환하지 않고 잔여·복귀 손실에 따라 처리 연장 또는 받기로 전환',
       ['체력·마나·가용 기술과 전진 시간이 듭니다.','상대가 밖에서 웨이브를 잡으면 귀환 준비가 끝나지 않고 다음 방어 선택이 줄 수 있습니다.']],
      ['CRASH','상대 포탑까지 밀어 넣기',ready&&building&&a.purpose==='RESET'&&a.crash==='READY',a.crash==='BLOCKED'||a.response==='DISRUPTS',
       '상대 포탑 도착을 확인한 뒤 귀환·다음 준비 시간을 비교하기','빠른 처리 외에 잔여 도달·상대 처리·추가 웨이브·시간 여건까지 따로 확인한 가정',
       '막는 잔여를 처리할 수 있는지 보고 아군 웨이브의 실제 포탑 도착까지 확인합니다. 도중에 멈추면 완료로 부르지 않습니다.',
       '처리용 기술과 상대 접근 대응에 남길 기술을 나눕니다. 교환 소모로 끝까지 못 넣는다면 공격을 줄이거나 계획을 취소합니다.',
       '새 웨이브·상대 방해·증원으로 도달이 끊기지 않는지 계속 확인합니다.',
       '아군 웨이브가 상대 포탑에 실제 도착한 것을 본 경우만 완료. 현재는 가정이므로 완료 미관측입니다.',
       '포탑 밖에서 멈춤·처리 예산 고갈·상대 접근으로 전진 불가','밀어 넣기 실패를 인정하고 남은 자원·웨이브 손실을 비교해 받기 또는 귀환 준비 수정',
       ['끝까지 넣으려는 전진 시간과 자원·상대 대응 노출이 필요합니다.','완료를 확인해도 시야·귀환 완료·합류 도착과 아군 준비가 따로 필요합니다.']],
      ['TRIM_RECEIVE','일부 줄이며 당겨 받기',a.flow==='INCOMING'&&a.response==='MANAGEABLE',a.flow!=='UNKNOWN'&&a.flow!=='INCOMING',
       '오는 웨이브의 압박을 조절하며 접근 가능한 자원 받기','상대 웨이브가 오는 흐름과 현재 받을 위치·대응 여건을 확인한 가정',
       '받을 위치에서 감당하지 못할 미니언 압박을 줄이되, 어느 쪽으로 움직이는지 보며 필요한 대상만 처리합니다. 상대 수량·체력에 따른 정확한 처리량은 미확인입니다.',
       '배워 가용한 처리 기술도 필요한 잔여에 한정해 비교합니다. 케이틀린의 필트오버 피스메이커(Q)·럭스의 광휘의 특이점(E)가 함께 맞아 흐름을 반대로 바꾸면 처리량을 줄입니다.',
       '현재 수급 공간과 체력·동료 연결을 재확인합니다. 고정 위치를 계속 유지하는 프리징과 같지 않습니다.',
       '목표로 삼은 자원을 실제 받았거나 포탑에 도착하면 포탑 아래 수급으로 재비교합니다.',
       '줄이는 동안 견제·진입을 감당 못함·원치 않게 반대로 밀림','일부 CS를 포기하고 포탑 수급·회복 후보를 비교하되 포탑도 안전 보장은 아님',
       ['CS·공간·먼저 움직일 기회를 일부 포기할 수 있습니다.','줄이기 자체도 자원·체력을 쓰며 상대 다이브나 로밍을 막는다는 보장은 없습니다.']],
      ['TOWER_CS','포탑 아래 수급',a.flow==='UNDER_TOWER'&&a.response==='MANAGEABLE',a.flow!=='UNKNOWN'&&a.flow!=='UNDER_TOWER',
       '도착한 웨이브에서 감당할 자원을 확보하기','포탑 도착과 상대 접근·동료 연결을 확인한 가정',
       '실제 미니언 체력·포탑 공격 대상·내 공격 가능 거리를 보고 받을 대상을 고릅니다. 고정 타수나 전부 수급을 약속하지 않습니다.',
       '가용 처리 기술은 받을 자원과 다이브 대응 예산을 함께 비교합니다. 무리한 막타보다 포기할 자원을 구분합니다.',
       '상대 접근·추가 인원과 내 체력 때문에 수급 공간이 사라지는지 봅니다.',
       '도착 잔여 처리 또는 포기한 자원이 정해지면 다음 웨이브·회복을 비교합니다.',
       '다이브·체력 부족·퇴로 상실로 현재 위치 수급 불가','완전 수급을 포기하고 회복·이탈 후보를 재비교하며 정글 도움은 실제 도착 가능 조건이 있을 때 별도 검토',
       ['일부 CS·포탑 체력·이동 기회를 잃을 수 있습니다.','포탑은 다이브·제어를 없애지 않으며 정해진 CS 획득량도 보장하지 않습니다.']],
      ['RETURNING','밀어 넣은 뒤 돌아오는 웨이브 받기',a.flow==='RETURNING'&&a.response==='MANAGEABLE',a.flow!=='UNKNOWN'&&a.flow!=='RETURNING',
       '이전 밀어 넣기 뒤 돌아오는 흐름에 복귀·수급 맞추기','이전 포탑 도착과 현재 돌아오는 흐름을 확인한 미래 가정',
       '현재 만나는 위치·잔여 체력을 먼저 보고 받을 자원을 고릅니다. 이전 Crash만으로 지금 흐름·손실을 확정하지 않습니다.',
       '복귀한 실제 아이템·체력·가용 기술로 처리량을 다시 비교합니다. 필요 없는 광역 처리로 반대 방향으로 바꾸지 않습니다.',
       '상대가 흐름을 바꾸거나 복귀가 늦으면 수급 목표를 낮춥니다.',
       '돌아온 자원 처리 또는 손실을 확인하면 다음 유지·밀기 계획을 새로 고릅니다.',
       '복귀 어긋남·상대 빠른 처리·추가 인원으로 예상과 다른 흐름','이전 계획을 버리고 현재 흐름에서 받기·회복 재비교',
       ['복귀 지연으로 CS·경험치·공간을 잃을 수 있습니다.','이전 포탑 도착은 현재 안전·원하는 반사 흐름·완전 수급을 보장하지 않습니다.']],
      ['FREEZE','유리한 위치에 유지하기 · 프리징',false,false,
       '유리한 위치에 웨이브를 계속 유지하려는 후보','유지 위치·양쪽 종류/체력·상대 방해 조건의 검증 근거 필요',
       '현재 자료로 이 매치업의 유지 처리량을 정하지 않습니다. 임의 미니언 수나 고정 타수는 제시하지 않습니다.',
       '유지에 필요한 기술·체력 예산이 확인되지 않아 실행안으로 선택하지 않습니다.',
       '당겨 받기와 프리징은 별개이며 정확한 지속 유지 기준은 미지원입니다.',
       '유리한 위치가 유지됐다는 실제 연속 관측이 필요합니다. 현재 미판정입니다.',
       '상대가 깨는 방식과 유지 실패 지점의 자료 부족','우선 실제 흐름에서 당겨 받기·포탑 수급의 조건을 비교',
       ['상대가 깨거나 개입하면 자원·체력 손실 가능; 현재 기준으로 이 비용을 비교 확정할 수 없습니다.']],
      ['CHECK_WAVE','흐름 확인·수급 목표 정하기',true,false,
       '모르는 조건을 분리하고 감당할 수급·회복 선택 남기기','실행 판단에 필요한 정보가 없거나 기존 가정이 깨짐',
       '현재 보이는 미니언 체력·위치·이동과 상대 처리·내 자원 중 모르는 항목을 나눕니다. 확인하려고 미확인 공간에 들어가지 않습니다.',
       '처리·대응에 필요한 기술 예산을 구분하고 확실하지 않은 CS는 목표에서 줄입니다. 광역 기술이 있다고 처리 우위를 채우지 않습니다.',
       '정보가 생기면 밀기·받기 후보를 다시 비교하며 현재 위치를 안전하다고 고정하지 않습니다.',
       '흐름·처리·상대 대응 조건을 확인했을 때만 다음 계획을 선택합니다.',
       '추가 정보가 없거나 상대 접근으로 현재 수급 공간 상실','자원 목표를 줄이거나 회복·이탈 후보를 비교; 정글·시야 도움은 따로 가능한 조건 필요',
       ['기다리는 동안 CS·시간·공간·귀환 기회를 잃을 수 있습니다.','정보 확인이나 후퇴도 생존·수급을 보장하지 않습니다.']]
    ];
    return specs.map(([id,title,ok,blocked,objective,start,processing,skills,maintenance,completion,failure,next,costs])=>({id,title,objective,start,processing,skills,maintenance,completion,failure,next,costs,
      feasibility:id==='FREEZE'?'UNSUPPORTED':status(ok,blocked),level:'DESIGN_HYPOTHESIS',evidence_ids:factIds,
      opponent_goal:'카이사·노틸러스는 맞처리·견제·접근으로 아군 잔여를 줄이거나 수급 위치를 제한할 수 있습니다. 원하는 웨이브와 실제 의도는 미확인입니다.',
      conversion:'귀환은 잔여·포탑 도착·복귀 손실을 확인한 뒤 비교합니다. 시야·합류는 실제 위치 정보·이동과 복귀 시간·아군 준비가 맞는 별도 조건이며, 밀었다고 즉시 가능하지 않습니다.',
      steps:[{number:1,text:objective+' · '+start},{number:2,text:processing+' '+skills},{number:3,text:'상대 방해·응징을 재비교: '+failure+'이면 '+next}],punishment:[]}));
  }
  function choose(plans,a,risk){
    const can=id=>plans.find(p=>p.id===id&&p.feasibility==='POSSIBLE');
    for(const id of ['TRIM_RECEIVE','TOWER_CS','RETURNING','CRASH'])if(can(id))return id;
    if(a.purpose==='RESET'&&can('FAST_PUSH'))return 'FAST_PUSH';
    if(risk==='OPPORTUNITY'&&can('FAST_PUSH'))return 'FAST_PUSH';
    return can('SLOW_PUSH')?'SLOW_PUSH':can('FAST_PUSH')?'FAST_PUSH':'CHECK_WAVE';
  }
  function mapFor(input,plan){
    const mirror=p=>input.side==='RED'?{x:p.y,y:p.x}:p,here={x:75,y:82};
    return {plan:{id:plan.id,direction:plan.objective,steps:plan.steps},map:{caption:'모든 위치는 전술 설명용 가정 · 웨이브 처리 도식은 별도 표시',entities:[{id:'wave-self',team:'ALLY',self:true,champion:'Caitlyn',start:mirror(here)},{id:'wave-peer',team:'ALLY',champion:'Lux',start:mirror({x:72,y:80})}],arrows:[],landmarks:[{id:'wave',step:1,label:'1 라인 흐름·처리 여건',...mirror(here)},{id:'budget',step:2,label:'2 웨이브 처리·대응 예산',...mirror({x:80,y:80})},{id:'convert',step:3,label:'3 귀환·합류는 별도 조건',...mirror({x:64,y:76})}],notes:['정글 개입·귀환·합류는 위치·도착·복귀 손실과 동료 준비가 확인될 때만 별도로 비교합니다.','현재 지도는 조건 연결 위치를 설명하며 이동 경로·안전·이득 달성을 확정하지 않습니다.','적 위치는 미확인이므로 표시하지 않습니다.']}};
  }
  function evaluate(report,catalog,raw,means){
    const s=stateOf(raw),a=s.assumptions,risk=report.input.preferences?.risk||'BALANCED';
    if(!['LOSS_LIMIT','BALANCED','OPPORTUNITY'].includes(risk))throw Error('성향을 확인해 주세요.');
    const patch=report.input.patch&&report.input.patch.split('.').slice(0,2).join('.')===catalog.source_patch.split('.').slice(0,2).join('.');
    const ids=new Set(Object.values(catalog.champions).flatMap(c=>c.facts).map(f=>f.id));
    const requiredFacts=[...new Set([...factIds,...(periodFacts[s.milestone]||[])])];
    const supported=report.lane.matchup_id==='Caitlyn_Lux__Kaisa_Nautilus_v2'&&Boolean(patch)&&requiredFacts.every(id=>ids.has(id));
    const plans=supported?plansFor(a):[],selectedId=supported?choose(plans,a,risk):null,selected=plans.find(p=>p.id===selectedId)||null;
    const follow=Boolean(supported&&s.milestone==='LEVEL2'&&['SLOW_PUSH','FAST_PUSH'].includes(selectedId)&&a.purpose==='SPACE'&&a.access==='READY'&&a.response==='MANAGEABLE'&&means?.supported&&means?.selected_plan_id==='SHORT_FOLLOW');
    for(const p of plans){p.evidence_ids=requiredFacts;p.punishment=punishment(p,follow&&p.id===selectedId);}
    const same=!supported||new Set(['LOSS_LIMIT','BALANCED','OPPORTUNITY'].map(r=>choose(plans,a,r))).size===1;
    const reason=!supported?'대표 바텀 매치업·포지션·패치·공식 사실 연결 조건 밖입니다. 웨이브 전략과 도식은 미지원입니다.':selectedId==='CHECK_WAVE'?'처리 여건·흐름·목적 또는 상대 방해 대응이 미확인/부족합니다. 성향으로 이 조건을 통과시키지 않습니다.':same?'현재 조건에서는 선택이 같습니다. 웨이브 흐름·실행 여건·목적이 선택을 먼저 제한하므로 성향에 맞춰 억지로 바꾸지 않습니다.':risk==='OPPORTUNITY'?'가정이 맞으면 처리 자원·노출 비용을 감수해 공간을 더 빨리 비교하는 안을 강조합니다. 최적 선택 검증은 아닙니다.':'처리 여건이 맞아도 기술 소모·전진 시간을 줄여 잔여와 다음 선택을 남기는 안을 강조합니다. 상대가 깨면 유지하지 않습니다.';
    return {schema_version:'loading-wave-v1',supported,unsupported_reason:supported?null:reason,state:s,preference:risk,observation:'NOT_OBSERVED',plans,selected,selected_plan_id:selectedId,selection_reason:reason,same_choice_across_preferences:same,first_push:{status:'UNKNOWN',conditional_access:a.access,reason:'실제 선푸시는 상대 맞처리·잔여 체력·도달을 측정하지 않아 미확인입니다. 광역 기술 보유나 레벨만으로 채우지 않습니다.'},should_push:a.purpose==='RESET'?'귀환 목적상 빠른 처리·도달 여건을 따로 비교합니다. 실행 조건이 없으면 밀기를 강제하지 않습니다.':a.purpose==='SPACE'?'공간 확보와 상대 방해 비용을 비교하는 가정입니다. 먼저 밀기가 무조건 유리하지 않습니다.':'라인 유지 목적 또는 목적 미확인입니다. 밀기 자체를 목표로 정하지 않습니다.',crash_completion:'NOT_OBSERVED',period_note:notes[s.milestone],question_ids:supported?['DUO-L2','DUO-L3_5','DUO-L6']:[],punishment_follow_allowed:follow,punishment_reason:follow?'웨이브 목표·처리 예산을 깨지 않는 가정에서만 기존 스킬 후속을 하위 수단으로 비교합니다.':'처리·퇴로 예산 또는 스킬 후속 조건이 부족하거나 귀환 준비가 목적입니다. 공격 대신 웨이브 처리·공간·자원 보존을 우선 비교합니다.',counterexamples:supported?['견제 기술이 미니언까지 맞아 천천히 쌓기·당겨 받기 목표와 반대로 흐름이 바뀜','딜교환에 마나·기술을 소모해 잔여 처리나 밀어 넣기를 못 함','상대 맞밀기·진입 또는 추가 인원 때문에 가정한 처리·이탈 여건이 깨짐','빨리 처리했지만 상대 포탑 밖에서 멈춰 귀환 손실이 커짐']:[],evidence:{level:'DESIGN_HYPOTHESIS',official_scope:'연결된 공식 자료는 기술의 성질만 지지합니다. 웨이브 처리량·선푸시 우위·최적 계획·응징 성과는 검증되지 않았습니다.',sufficiency:supported?'CONDITIONAL':'INSUFFICIENT',real_coaching_n:0,accuracy:null},diagram:selected?{plan_id:selectedId,observation:'HYPOTHETICAL',counts:'SYMBOLS_NOT_QUANTITIES',after:'DESIRED_NOT_PREDICTED'}:null,map_scenario:selected?mapFor(report.input,selected):null};
  }
  return Object.freeze({defaultState,preset,conditionDefs,evaluate,mapFor});
});

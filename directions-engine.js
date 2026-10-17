/* Pure manual learning engine, shared by the PC page and public mobile export. */
(function(root, factory) {
  const engine = factory();
  if (typeof module === 'object' && module.exports) module.exports = engine;
  else root.DirectionEngine = engine;
})(typeof globalThis !== 'undefined' ? globalThis : this, function() {
  'use strict';
  const clone = value => JSON.parse(JSON.stringify(value));
  const roles = ['TOP','JUNGLE','MID','BOTTOM','SUPPORT'];
  const validEnum = (values,value) => typeof value === 'string' && Object.hasOwn(values,value);
  function exact(object, keys) {
    if (!object || Array.isArray(object) || typeof object !== 'object' ||
        Object.keys(object).sort().join('|') !== [...keys].sort().join('|')) throw Error('입력 필드를 확인해 주세요.');
  }
  function defaultInput(catalog) { return clone(catalog.default_input); }
  function validate(input, catalog) {
    exact(input, Object.keys(catalog.default_input));
    if (!validEnum(catalog.labels.phases,input.phase) || !validEnum(catalog.labels.positions,input.role) ||
        !validEnum(catalog.labels.review_modes,input.review_mode) || !['BLUE','RED'].includes(input.side) ||
        !catalog.champions.some(c => c.id === input.champion) ||
        !catalog.decisions.some(d => d.id === input.decision && d.phase === input.phase)) throw Error('지원하는 학습 장면을 선택해 주세요.');
    if (input.patch !== null && (typeof input.patch !== 'string' || !/^\d{1,3}\.\d{1,3}(?:\.\d{1,3})?$/.test(input.patch))) throw Error('패치를 숫자.숫자 형식으로 입력해 주세요.');
    exact(input.economy, roles);
    for (const role of roles) if (!validEnum(catalog.labels.economy,input.economy[role])) throw Error('경제 상태를 확인해 주세요.');
    exact(input.conditions,catalog.inputs.conditions.map(c => c.key));
    for (const c of catalog.inputs.conditions) if (!validEnum(c.options,input.conditions[c.key])) throw Error('상황 조건을 확인해 주세요.');
    exact(input.metrics,['total_earned_difference','purchased_value_difference','current_gold','observed_at']);
    for (const key of ['total_earned_difference','purchased_value_difference','current_gold']) {
      const v = input.metrics[key];
      if (v !== null && (!Number.isSafeInteger(v) || (key === 'current_gold' && v < 0))) throw Error('골드 지표는 확인한 정수 또는 미확인으로 입력해 주세요.');
    }
    if (input.metrics.observed_at !== null && (typeof input.metrics.observed_at !== 'string' || input.metrics.observed_at.length > 80 || !input.metrics.observed_at.trim())) throw Error('관측 시각을 확인해 주세요.');
    return clone(input);
  }
  function choose(input) {
    const c = input.conditions;
    if (input.decision === 'RECALL') {
      if (c.health === 'READY' && c.wave === 'CRASHED' && c.purchase === 'READY') return 'RESET_AFTER_CRASH';
      if (c.health === 'READY' && c.wave === 'INCOMING_LARGE') return 'RECEIVE_WAVE';
      return 'INFORMATION_RESET';
    }
    if (input.decision === 'SIDE_GROUP') {
      if (c.side_exit !== 'AVAILABLE' || c.ally_ready !== 'READY' || c.vision !== 'OBSERVED_ROUTE' || c.health !== 'READY' || c.level_items !== 'READY') return 'SAFE_REGROUP';
      if (input.champion === 'Fiora' && !['JUNGLE','SUPPORT'].includes(input.role)) return 'SIDE_PRESSURE';
      return input.champion === 'Ornn' ? 'FRONT_CONNECT' : 'GROUP_SETUP';
    }
    return c.objective === 'AVAILABLE' && c.numbers === 'ENOUGH' && c.vision === 'OBSERVED_ROUTE' &&
      c.ally_ready === 'READY' && c.health === 'READY' && c.level_items === 'READY' ? 'OBJECTIVE_SETUP' : 'TRADE_KNOWN_RESOURCE';
  }
  // Hand-authored approximate image anchors, never world coordinates or inferred positions.
  function anchors(input) {
    const blue = input.side === 'BLUE';
    const lane = input.role === 'TOP' ? 'TOP' : ['BOTTOM','SUPPORT'].includes(input.role) ? 'BOTTOM' : 'MID';
    const lanes = blue ? {
      TOP: {home:[16,60],safe:[14,72],forward:[16,29],enemy:[32,15]},
      BOTTOM:{home:[60,84],safe:[43,85],forward:[80,73],enemy:[85,59]},
      MID:{home:[43,57],safe:[35,65],forward:[54,46],enemy:[61,39]}
    } : {
      TOP:{home:[40,16],safe:[58,15],forward:[25,17],enemy:[15,33]},
      BOTTOM:{home:[85,40],safe:[86,28],forward:[85,68],enemy:[69,84]},
      MID:{home:[57,43],safe:[65,35],forward:[46,54],enemy:[39,61]}
    };
    const l = lanes[lane], pt = xy => ({x:xy[0],y:xy[1]});
    return {base:pt(blue?[18,81]:[81,18]),lane_home:pt(l.home),lane_safe:pt(l.safe),lane_forward:pt(l.forward),enemy:pt(l.enemy),
      lane_pressure:pt([l.forward[0]+(blue?2:-2),l.forward[1]+(blue?-5:5)]),
      mid_home:pt(blue?[43,57]:[57,43]),mid_front:pt(blue?[49,51]:[51,49]),mid_pressure:pt(blue?[52,48]:[48,52]),
      objective:pt([67,70]),objective_approach:pt(blue?[56,67]:[70,57]),objective_edge:pt(blue?[62,70]:[70,65]),vision:pt(blue?[57,62]:[73,59])};
  }
  function mapFor(input, plan, catalog) {
    const a = anchors(input), layout = catalog.layouts[plan.layout];
    const path = layout.path.map(k => a[k]);
    const self = {id:'self',team:'ALLY',self:true,champion:input.champion,portrait:'direction-assets/'+input.champion+'.png',start:a[layout.start],target:a[layout.target]};
    const entities = [self];
    if (input.phase === 'POST_LANE') {
      const ally = input.champion === 'Ornn' ? 'Caitlyn' : 'Ornn';
      entities.push({id:'ally',team:'ALLY',self:false,champion:ally,portrait:'direction-assets/'+ally+'.png',start:{x:a.mid_home.x+4,y:a.mid_home.y+5},target:null});
    }
    if (input.conditions.enemy_visible === 'VISIBLE_EXAMPLE') {
      const enemy = input.champion === 'Fiora' ? 'Caitlyn' : 'Fiora';
      entities.push({id:'enemy-example',team:'ENEMY',self:false,champion:enemy,portrait:'direction-assets/'+enemy+'.png',start:a.enemy,target:null});
    }
    // Each numbered arrow refers to its card step. The skill-check step uses a small
    // illustrative pressure direction, not an instruction to cast or an exact range.
    const starts = [a[layout.start],path[0],path[1]];
    const arrows = path.map((to,i) => ({step:i+1,kind:layout.kinds[i],from:starts[i],to,
      label:i===1?'2 · 수단을 검토할 위치':'행동 '+(i+1)}));
    const landmarks = [{id:'friendly-tower',kind:'TOWER',label:'아군 포탑 예시',...a.lane_home,step:1}];
    if (input.conditions.wave!=='UNKNOWN') landmarks.push(
      {id:'wave',kind:'WAVE',label:input.conditions.wave==='CRASHED'?'도착한 웨이브 예시':'들어오는 웨이브 예시',
       ...(input.conditions.wave==='CRASHED'?a.enemy:a.lane_home),step:1});
    if (input.phase === 'POST_LANE') landmarks.push({id:'vision',kind:'VISION',label:input.conditions.vision==='OBSERVED_ROUTE'?'접근 정보 확인 방향 예시':'정보가 필요한 방향 · 미확인',...a.vision,step:1});
    if (input.decision === 'OBJECTIVE') landmarks.push({id:'dragon',kind:'OBJECTIVE',label:'용 위치 예시 · 생성 시각 미사용',...a.objective,step:3});
    return {asset:'direction-assets/map11.png',caption:'전술 설명용 예시 · 실제 위치 추적 아님',entities,arrows,landmarks,
      notes:['선명한 초상화: 예시 시작 · 반투명 초상화: 목표 배치',
        '화살표는 행동 방향이며 안전 경로나 정확한 기술 사거리가 아닙니다. 귀환 방향은 도보 경로가 아닙니다.',
        '좌표·웨이브·포탑·시야 표시는 개략적인 설명 위치입니다. 지도 자산 16.20.1의 최신 지형 일치 여부는 별도입니다.',
        input.conditions.enemy_visible==='UNKNOWN'?'적 위치 미확인: 적 초상화를 배치하지 않았습니다.':'적 1명은 사용자가 선택한 가상 관측 예시이며 실제 적 위치가 아닙니다.']};
  }
  function evaluate(rawInput,catalog) {
    const input = validate(rawInput,catalog), id = choose(input), original = catalog.plans[id];
    const champion = clone(catalog.champions.find(c => c.id === input.champion));
    const kitKey = input.decision === 'RECALL' ? 'RECALL' : id;
    const objectiveRole = {Caitlyn:'아군 뒤에서 접근 공간을 제한할 사람',Fiora:'고립되지 않는 옆 위치에서 아군과 연결할 사람',Ornn:'아군이 따라올 전방 공간을 준비할 사람'}[input.champion];
    const plan = clone(original);
    plan.id = id;
    plan.role = plan.role.replace('{objective_role}',objectiveRole);
    plan.steps = plan.steps.map((text,i) => ({number:i+1,text:text.replace('{kit}',catalog.methods[input.champion][kitKey])}));
    if (['JUNGLE','SUPPORT'].includes(input.role) && id === 'RECEIVE_WAVE') {
      plan.role = '라이너와 수급·귀환 순서를 맞출 연결자';
      plan.steps[2].text = '라이너가 받을 자원을 대신 가져온다고 가정하지 않습니다. 위험을 감당하며 웨이브를 지키기보다 내 회복·구매와 다음 합류 위치를 맞춥니다.';
      plan.requirements.push('정글·서포터의 기여를 골드 차이나 웨이브 수급량만으로 판단하지 않음');
    }
    const decision = catalog.decisions.find(d => d.id === input.decision);
    plan.why = decision.condition_keys.filter(k=>k!=='enemy_visible').map(key=>{
      const c=catalog.inputs.conditions.find(x=>x.key===key);return c.label+': '+c.options[input.conditions[key]]+' (수동 입력)';
    });
    const known = roles.filter(r => input.economy[r]!=='UNKNOWN');
    plan.why.push('경제 입력: '+(known.length?known.map(r=>catalog.labels.positions[r]+' '+catalog.labels.economy[input.economy[r]]).join(' · '):'전 포지션 미확인')+'. 경제 상태만으로 교전 승리·이동 가능성을 판정하지 않습니다.');
    if (known.length < 5) plan.why.push('미확인 경제 상태 '+(5-known.length)+'개는 비슷으로 바꾸지 않았습니다.');
    const ownState = input.economy[input.role];
    if (ownState === 'AHEAD') plan.requirements.push('내 경제 우세가 있어도 체력·인원·기술·경로 조건이 부족하면 전진 폭을 늘리지 않기');
    if (ownState === 'BEHIND') plan.requirements.push('내 경제 열세에서 잃을 자원과 회복 필요를 비교하되 아군 연결·기술 활용 역할까지 없다고 단정하지 않기');
    if (['JUNGLE','SUPPORT'].includes(input.role)) plan.why.push('정글·서포터 역할은 아군 연결·수단·자원 상태를 함께 보며 골드만으로 평가하지 않습니다.');
    const metricNames = {total_earned_difference:'총 획득 골드 차이',purchased_value_difference:'구매한 아이템 가치 차이',current_gold:'현재 보유 골드'};
    const metrics = Object.entries(metricNames).map(([key,label]) => ({key,label,value:input.metrics[key],unit:'골드',source:'사용자 수동 입력 · 미검증',observed_at:input.metrics.observed_at,missing:input.metrics[key]===null,
      limit:'자동 계산·분류하지 않음. 다른 골드 지표를 대신하지 않음. '+(input.metrics.observed_at?'관측 시각도 사용자 입력입니다.':'관측 시각 미확인입니다.')}));
    const samePatch = input.patch && input.patch.split('.').slice(0,2).join('.')===catalog.source_version.split('.').slice(0,2).join('.');
    const evidence = {level:'DESIGN_HYPOTHESIS',label:'설계 가설 · 신규 전략 미검증',official_facts:champion.official_facts,statistics:[],expert_statements:[],
      limits:[...catalog.limitations,input.patch===null?'게임 패치 미확인 · 공식 원문은 16.20.1 참고 자료입니다.':samePatch?'게임 패치와 공식 원문의 주 패치가 같습니다. 전술 검증을 뜻하지 않습니다.':'입력 패치와 공식 원문 버전이 다릅니다. 적용을 확정하지 마세요.']};
    return {schema_version:'lol-coach-directions-output-v1',input,plan,champion,economy:{states:clone(input.economy),metrics,note:'골드 차이는 경제 상태입니다. 교전 승리 판정이나 정글·서포터 기여 점수가 아닙니다.'},evidence,map:mapFor(input,plan,catalog)};
  }
  return {defaultInput,evaluate};
});

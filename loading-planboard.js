/* Pure decision projection. No observations, IO, strength scores or source promotions. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./loading-formation.js'));
  else root.LoadingPlanboard = factory(root.LoadingFormation);
})(typeof globalThis !== 'undefined' ? globalThis : this, function (formation) {
  'use strict';
  const clone = x => JSON.parse(JSON.stringify(x));
  const ENUMS = {
    enemy_support: ['PRESENT', 'ABSENT', 'UNKNOWN'], enemy_jungle: ['UNKNOWN', 'AWAY', 'NEAR'],
    ally_jungle: ['UNCONFIRMED', 'AVAILABLE'], goal: ['AUTO', 'PRESSURE', 'FARM', 'RECALL'],
    clear_window: ['UNCONFIRMED', 'OPEN'], ally_followup: ['UNCONFIRMED','AVAILABLE','UNAVAILABLE']
  };
  const defaults = () => ({ basis: 'loading-plan-example-v1', overrides: {} });
  function validate(value) {
    if (!value || Array.isArray(value) || typeof value !== 'object' || Object.keys(value).sort().join('|') !== 'basis|overrides' || value.basis !== 'loading-plan-example-v1' || !value.overrides || Array.isArray(value.overrides) || typeof value.overrides !== 'object') throw Error('작전 예시의 형식을 확인해 주세요.');
    for (const [key, v] of Object.entries(value.overrides)) if (!ENUMS[key]?.includes(v)) throw Error('지원하는 작전 가정만 선택해 주세요.');
    return clone(value);
  }
  const roleNames = { TOP: '탑', MID: '미드', BOTTOM: '바텀' };
  // Authored strategy display only. Never apply to quotes, official descriptions or traces.
  function plainLanguage(value) {
    let text=String(value??'');
    const phrases=[
      ['접근·처리 선택권을 만든다','상대에게 다가갈 기회와 미니언을 먼저 잡을 여유를 만든다'],['아군 제어와 연결해','아군의 속박·기절에 맞춰 움직여'],['아군 제어가 적중하고','아군의 속박·기절이 맞고'],['사이드 CS·포탑 압박을 얻되 본대가 버틸 수 없는 싸움은 미리 접는다.','다른 라인에서 미니언을 잡고 포탑을 압박하되, 아군이 버티기 어려운 싸움이 열리면 더 깊게 밀지 않는다.'],['피오라는 응수(W)로 받아낼 수단과 복귀 경로를 정한 뒤 접근한다.','피오라는 응수(W)로 막을 기술과 빠져나올 길을 정한 뒤 접근한다.'],
      ['측면 진입·동료 후속 단절이면 교환 종료.','상대가 옆으로 들어오거나 동료가 함께 공격할 수 없으면 교환을 끝낸다.'],['정글 개입·후속 단절이면 전진 폭을 줄인다.','정글러가 개입하거나 아군이 함께 공격할 수 없으면 더 앞으로 나가지 않는다.'],['상대 서포터 복귀·정글 개입·동료 후속 단절이면 압박을 접는다.','상대 서포터가 돌아오거나 정글러가 개입하거나 동료가 함께 공격할 수 없으면 압박을 멈춘다.'],['수급 아이템','미니언을 잡기 좋은 아이템'],['처리·회복 수단','미니언을 잡거나 체력을 회복할 수단'],['본대 합류를','아군이 모인 곳으로 이동하는지를'],['기본 수급을','미니언을 잡으며 성장하기를'],['수급을 기본으로 기회 압박','미니언을 잡으며 성장하고, 기회가 생기면 압박'],['동료 후속','동료의 추가 공격'],
      ['후속 거리가 끊기면','아군이 함께 공격할 수 없으면'],['수급할','미니언을 잡을'],['수급하는','미니언을 잡는'],['수급하며','미니언을 잡으며'],['처리할','미니언을 잡을'],['처리하는','미니언을 잡는'],['처리한다','미니언을 잡는다'],['처리하면','미니언을 잡으면'],['처리해야','미니언을 잡아야'],['수급을 잇는다','미니언을 계속 잡는다'],['수급을 이어','미니언을 계속 잡아'],['수급하고','미니언을 잡아 골드·경험치를 얻고'],['수급한다','미니언을 잡아 골드·경험치를 얻는다'],
      ['수급 공간','미니언을 잡을 자리'],['수급 위치','미니언을 잡을 위치'],['수급선','미니언을 잡고 돌아올 위치'],['수급 거리','미니언을 잡고 돌아올 거리'],['수급 자원','미니언을 잡는 데 쓸 체력·마나·기술'],['수급 목표','챙길 미니언과 경험치'],['수급 손실','놓치는 미니언 골드·경험치'],['수급 보존','골드·경험치 챙기기'],['수급 유지','미니언을 계속 잡기'],['수급 접근','미니언에 다가가기'],
      ['중앙 수급','중앙 라인에서 미니언 잡기'],['포탑 아래 수급','포탑 아래에서 미니언 잡기'],['포탑 수급','포탑 아래에서 미니언 잡기'],
      ['처리·교환·대응 자원','미니언 잡기·견제·방어에 쓸 체력·마나·기술'],['처리 자원','미니언을 잡는 데 쓸 마나·기술'],['처리 수단','미니언을 잡을 기술'],['처리 기술','미니언을 잡는 기술'],['처리 능력','미니언을 잡는 능력'],['처리 우위','상대보다 미니언을 먼저 잡을 여유'],['처리 여유','미니언을 먼저 잡고 움직일 시간'],['처리 선택권','미니언을 빨리 잡거나 막타만 칠 선택'],['처리 시간','미니언을 잡을 시간'],['처리량','미니언을 잡는 속도'],['처리 방향','미니언이 어느 쪽으로 밀리는지'],['처리 방식','미니언을 잡는 방법'],['처리 속도','미니언을 잡는 속도'],['빠른 처리','미니언을 빠르게 잡기'],['선처리 경쟁','미니언을 먼저 잡는 경쟁'],['선처리','상대보다 먼저 미니언 잡기'],
      ['후속이 끊기면','추가 공격이 이어지지 않으면'],['후속 단절','추가 공격을 이어갈 수 없음'],['후속 거리','같이 공격할 수 있는 거리'],['카이사 후속','카이사의 추가 공격'],['아군 후속','아군의 추가 공격'],['동료 후속','동료의 추가 공격'],
      ['본대와 연결한다','아군이 모인 곳에 합류할 준비를 한다'],['본대와 연결','아군이 모인 곳에 합류할 준비'],['본대 복귀 경로','아군이 모인 곳으로 돌아갈 길'],['본대 합류','아군이 모인 곳에 합류'],['본대 후속','아군이 함께 공격할 수 있는'],['본대','아군이 모인 곳'],['보호 연결','아군 보호 기술이 닿는 거리'],['동료 연결','함께 싸울 아군과의 거리'],
      ['사이드 자원','사이드 라인의 미니언·포탑'],['가까운 자원','가까이서 얻을 골드·경험치'],['남길 자원','아껴둘 체력·마나·기술'],['성장 자원','골드·경험치'],['대응 자원','반격·방어에 쓸 체력·마나·기술'],['이탈 자원','빠져나올 기술'],
      ['아군 제어가 맞으면','아군의 속박·기절이 맞으면'],['제어 적중','속박·기절 적중'],['제어 뒤','적을 묶은 뒤'],['CS 접근','미니언 막타를 칠 자리'],['교전 우열','싸울 때 어느 쪽이 강한지'],['강약세','강한 구간과 약한 구간']
    ];
    const replacePhrase=(from,to)=>{const re=new RegExp(from.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'(으로|로|을|를|이|가|은|는|과|와)?','g');text=text.replace(re,(_,particle)=>{if(!particle)return to;const n=to.charCodeAt(to.length-1)-0xAC00;if(n<0||n>11171)return to+particle;const end=n%28,pairs=[['을','를'],['이','가'],['은','는'],['과','와']];if(particle==='으로'||particle==='로')return to+(end&&end!==8?'으로':'로');const pair=pairs.find(p=>p.includes(particle));return to+(pair?pair[end?0:1]:particle);});};
    for(const [from,to]of phrases.sort((a,b)=>b[0].length-a[0].length))replacePhrase(from,to);
    text=text.replace(/수급을/g,'미니언을 잡아 골드·경험치를 얻는 일을').replace(/수급이/g,'미니언을 잡는 일이').replace(/수급에/g,'미니언을 잡는 데').replace(/수급으로/g,'미니언을 잡는 쪽으로').replace(/수급/g,'미니언 잡기');
    text=text.replace(/처리하고/g,'미니언을 잡고').replace(/처리에/g,'미니언을 잡는 데').replace(/처리를/g,'미니언을 잡는 일을').replace(/처리가/g,'미니언 잡기가').replace(/처리/g,'미니언 잡기');
    return text;
  }
  function actionSummaries(b,coach,report) {
    const sentence=value=>{const text=plainLanguage(value||'').trim().split(/(?<=[.!?])\s+/)[0];return text?(/[.!?]$/.test(text)?text:text+'.'):'공격을 강제하지 않고 닿는 미니언과 경험치를 챙긴다.';};
    const assessments=Object.fromEntries(Object.entries(coach.selected.metrics).map(([k,v])=>[k,v.assessment]));
    const app=coach.knowledge_application,override=coach.context.assumptions.scenario?.overrides||{};
    const conditional=Object.values(override).some(v=>['LOW','UNKNOWN','THEIRS'].includes(v));
    let kind=b.coverage.status==='UNSUPPORTED'?'KNOWLEDGE_GAP':app?.active&&app?.reference_plan?'EXECUTION_DEPENDENT':'CONDITION_DEPENDENT';
    if(kind!=='KNOWLEDGE_GAP'&&!conditional&&Object.values(assessments).some(v=>['ALLY','ENEMY'].includes(v)))kind='CLEAR_IN_SCOPE';
    const labels={CLEAR_IN_SCOPE:'일부 구간·교전 방식의 우열 근거 있음',CONDITION_DEPENDENT:'보호·거리·남은 수단에 따라 행동이 달라짐',EXECUTION_DEPENDENT:'접근·적중·이탈 실행에 따라 기회가 달라짐',KNOWLEDGE_GAP:'매치업 판단 부족 · 적용 가능한 일반 원칙'};
    const laneJudgment={kind,label:labels[kind],axis_assessments:assessments,outcome:'UNDETERMINED',scope:'행동 계획과 개별 축의 판단이며 전체 승패·반반 판정이 아닙니다.',missing_axes:Object.keys(assessments).filter(k=>assessments[k]==='INSUFFICIENT')};
    const contextConditions=[coach.context.assumptions.label,coach.selected.label+'의 비교 가정이며 실제 상태를 관측하지 않았습니다.'];
    const phaseLabel=area=>area==='fight'?'라인전 이후, 6레벨 이상으로 관련 기술을 배워 사용할 수 있다는 한타 가정입니다.':'라인전 이후의 배치·합류 가정이며 실제 위치를 관측하지 않았습니다.';
    const make=(area,kind,label,value,paths,target,extra={})=>({kind,label,text:sentence(value),source_paths:paths,detail_target:target,conditions:[...(area==='lane'?contextConditions:[phaseLabel(area)]),...(area==='lane'?(coach.actions.find(a=>a.id===coach.selection.id)?.requirements||[]):(report.roles?.proposed?.conditions||[]))],applicability:{champion:report.input.own_champion,position:report.input.own_position,patch:coach.context.patch.status,...(area==='lane'?{period:coach.selected_period}:{phase:area==='fight'?'POST_LANE_LEARNED_KIT':'POST_LANE_ASSUMPTION',lane_reference_period:coach.selected_period}),scenario:coach.context.assumptions.scenario,planning:b.context.planning},provenance_scope:'LINKED_CONTEXT_AND_RULE_NOT_TACTICAL_PROOF',judgment:area==='lane'?laneJudgment:{kind:'CONDITION_DEPENDENT',label:'입력한 조합의 수단을 적용한 조건부 계획',outcome:'UNDETERMINED'},knowledge_state:b.coverage.status==='UNSUPPORTED'?'GENERAL_PRINCIPLE':'SOURCE_SCOPE_LIMITED',basis:'DESIGN_HYPOTHESIS',claim_ids:[...(b[area]?.claim_ids||b.wave.claim_ids||[])],rule_ids:['player-planboard-v1',...paths.map(p=>'projection:'+p)],observation:false,...extra});
    const support=report.input.enemies.find(p=>p.position==='SUPPORT')?.champion;
    const counterpart=report.input.enemies.find(p=>p.position===report.input.own_position)?.champion;
    // A context example, never a global importance ranking; preserve all actual candidates in details.
    const candidates=[b.fight.threats.filter(t=>t.champion===support),b.fight.threats.filter(t=>t.champion===counterpart),b.fight.threats];
    const group=candidates.find(ts=>ts.length)||[];
    const example=group.find(t=>t.slot==='R')||group[0];
    const awareness=b.fight.awareness?.actors?.every(id=>b.fight.threats.some(t=>t.champion===id))?b.fight.awareness:null;
    const threatText=awareness?.danger||(example?example.label+' · '+plainLanguage(example.action):b.fight.stop);
    return {schema_version:'lol-coach-action-summaries-v1',origin:'ANALYSIS_ASSUMPTIONS_NOT_OBSERVATION',standard:coach.context.assumptions.label,
      lane:{judgment:laneJudgment,items:[
        make('lane','GOAL','이번 라인전 목표',b.lane.milestone.goal,['lane.milestone.goal'],'lane-goal'),
        make('lane','WAVE','기본 웨이브 방향',b.wave.handling,['wave.handling'],'lane-methods'),
        make('lane','TRADE','교환·응징 방법',b.wave.combat,['wave.combat'],'lane-methods'),
        make('lane','CAUTION','조심할 상황',b.matchup_playbook.ours.avoid,['matchup_playbook.ours.avoid'],'lane-counterplay'),
        make('lane','SWITCH','계획을 바꿀 조건',b.wave.change_if,['wave.change_if'],'lane-methods')
      ]},operations:{assumption:phaseLabel('operations'),items:[
        make('operations','POSITION','기본 활동 위치',b.operations.placement,['operations.placement'],'operations-plan'),
        make('operations','PARTNER','연결할 아군',b.operations.connection,['operations.connection'],'operations-plan'),
        make('operations','GAIN','우선할 이득',b.operations.priority,['operations.priority'],'operations-plan'),
        make('operations','AVOID','피할 행동',b.operations.concede,['operations.concede'],'operations-methods'),
        make('operations','FALLBACK','막히거나 불리할 때',b.operations.fallback,['operations.fallback'],'operations-plan')
      ]},fight:{assumption:phaseLabel('fight'),items:[
        make('fight','ROLE_POSITION','내 역할·기본 위치',b.fight.setup,['fight.role','fight.setup'],'fight-methods',{role:b.fight.role}),
        make('fight','START','공격 시작 조건',b.fight.start,['fight.start'],'fight-plan'),
        make('fight','TARGET','우선 공격 대상',b.fight.target,['fight.target'],'fight-methods'),
        make('fight','THREAT','대응할 위협',threatText,awareness?['fight.awareness.danger']:example?['fight.threats']:['fight.stop'],example?'fight-threats':'fight-plan',{threat_ids:awareness?awareness.mechanism_ids:example?[example.id]:[],conditions:example?[phaseLabel('fight'),example.condition]:[phaseLabel('fight')],selection_scope:awareness?awareness.scope:example?'조합에서 실제 연결된 위협 수단 예시 · 전체 중요도 순위 아님':'연결된 위협 자료 없음 · 기존 이탈 원칙만 제공'}),
        make('fight','EXIT','이탈·재배치 조건',b.fight.stop,['fight.stop'],'fight-plan')
      ]}
    };
  }
  function evaluate(report, catalog, coach, supplied, knowledge) {
    const input = report.input, planning = validate(supplied || input.planning || defaults());
    const p = { enemy_support: 'PRESENT', enemy_jungle: 'UNKNOWN', ally_jungle: 'UNCONFIRMED', goal: 'AUTO', clear_window: 'UNCONFIRMED', ...planning.overrides };
    const s = { wave: 'EVEN', resources: 'SUFFICIENT', enemy_key: 'AVAILABLE', engage: 'NONE', start_skill: 'W', ...coach.context.assumptions.scenario.overrides };
    const reverse = input.own_champion === 'Kaisa' && input.own_position === 'BOTTOM' && input.opponent_mode === 'ASSIGNED' && input.allies.some(p=>p.position==='SUPPORT'&&p.champion==='Alistar') && input.enemies.some(p=>p.position==='BOTTOM'&&p.champion==='Yunara') && input.enemies.some(p=>p.position==='SUPPORT'&&p.champion==='Lulu') && coach.context.patch.status !== 'MISMATCH';
    const id = reverse ? 'BR' : coach.matchup_id, period = coach.selected_period, early = ['LEVEL1', 'LEVEL2', 'LEVEL3_5'].includes(period);
    const valid = coach.supported === true, usable = valid || reverse, low = s.resources === 'LOW', unknown = !usable || s.resources === 'UNKNOWN' || s.wave === 'UNKNOWN';
    const slot = (team, position) => input[team].find(r => r.position === position)?.champion || null;
    const name = c => catalog.champions[c]?.name || c || '배치 미확인';
    const fact = (c, k) => catalog.champions[c]?.facts.find(f => f.slot === k);
    const skill = (c, k) => fact(c, k) ? name(c) + '의 ' + fact(c, k).name + '(' + k + ')' : name(c) + '의 기술(키 미확인)';
    const self = input.own_champion, role = report.roles?.proposed?.id || report.roles?.base?.id;
    const sideRole = role === 'SIDE_RETURN', bottom = input.own_position === 'BOTTOM';
    const supportCase = usable && bottom && ['A', 'B', 'BR'].includes(id) && !!slot('allies', 'SUPPORT') && !!slot('enemies', 'SUPPORT');
    const absent = supportCase && p.enemy_support === 'ABSENT';
    const jungleNear = p.enemy_jungle === 'NEAR',noFollowup=p.ally_followup==='UNAVAILABLE';
    const claims = id === 'A' ? ['A-WAVE', 'A-SHORT', 'A-RECALL', 'A-WAVE-SPACE',...(coach.knowledge_application?.supported?['A-INITIAL-ORDER-v1']:[])] : reverse ? ['B-ALI-RESOURCE','B-ALI-POLY'] : coach.evidence.claim_ids;
    const growth = coach.growth.find(g => g.id === period) || null;
    const reference=valid?coach.source_plan:null;
    const laneGoals = {
      E:reference?.overall_goal,
      BR: '체력을 보존해 CS·경험치를 받고, 알리스타 접근과 카이사 후속을 함께 쓸 여건을 남긴다.',
      A: early ? '럭스와 멀리서 견제해 카이사의 막타를 방해하고, 밀어 넣을 기회를 만든다.' : '받을 CS와 퇴로를 지키며 아군 제어 뒤 짧게 공격한다.',
      B: '유나라의 강화 공격과 룰루 지원이 겹치는 교환을 만들고 성장 자원을 남긴다.',
      C: '가까운 막타 자리를 압박하고, 상대 이탈을 쫓는 대신 CS·공간을 얻는다.',
      D: '장거리 견제로 수급을 잇되, 성장 후 고립된 맞딜을 허용하지 않는다.'
    };
    let overallGoal = usable ? laneGoals[id] : '확인된 수단으로 CS·경험치를 확보하고 복귀 선택권을 남긴다.';
    let milestoneGoal = reference?.selected?.purpose || (growth ? growth.after : id === 'C' ? coach.selected.action : overallGoal);
    if(reverse)milestoneGoal = period==='LEVEL1' ? '알리스타에게 아직 연속 진입 수단이 없는 구간: 체력·경험치와 닿는 CS를 지킨다.' : period==='LEVEL2' ? '알리스타가 박치기(W)·분쇄(Q)를 배웠다면 접근·후속 창이 생긴다. 체력을 써 선레벨 경쟁부터 강제하지 않는다.' : '룰루의 보호·변이와 유나라 강화 창을 피하고, 아군 후속이 닿는 교환만 비교한다.';
    if(noFollowup)overallGoal=milestoneGoal='아군 호응 없이 전진을 강제하지 않고, 받을 자원·지원·귀환을 비교한다.';
    if (low) milestoneGoal = '처리에 쓸 체력·마나를 남기며 받을 CS·경험치를 확보한다.';
    if (coach.context.patch.status === 'MISMATCH') overallGoal = milestoneGoal = '자료 버전이 달라 우세 적용을 제한하고 수급·복귀 계획부터 세운다.';
    const recallOpen = valid && !noFollowup && !low && !unknown && p.goal === 'RECALL' && p.clear_window === 'OPEN' && !jungleNear && ['EVEN', 'BUILDING'].includes(s.wave);
    let planId = noFollowup || unknown ? 'CHECK_WAVE' : low ? 'TRIM_RECEIVE' : valid && coach.knowledge_application?.supported && id==='A' && s.engage==='NONE' && early && s.wave==='EVEN' && !['FARM','RECALL'].includes(p.goal) ? 'ACQUIRE_PUSH' : ({ INCOMING: 'TRIM_RECEIVE', UNDER_TOWER: 'TOWER_CS', RETURNING: 'RETURNING' })[s.wave] || (p.goal === 'FARM' || reference || reverse || id === 'A' && !early ? 'TRIM_RECEIVE' : 'SLOW_PUSH');
    if (recallOpen) planId = 'FAST_PUSH';
    const labels = { ACQUIRE_PUSH:'선푸시 확보 후 처리량 조절', CHECK_WAVE: '수급 거리에서 처리 방향 파악', SLOW_PUSH: '막타 중심으로 천천히 쌓기', TRIM_RECEIVE: '필요한 만큼 줄이며 받기', TOWER_CS: '포탑 아래 수급', RETURNING: '돌아오는 웨이브 받기', FAST_PUSH: '빠른 처리 후 포탑 도달 확인' };
    let handling = {
      ACQUIRE_PUSH:'막타만 기다리지 않고 미니언에 평타를 보태 처리 우위를 만든다. 케이틀린의 필트오버 피스메이커(Q)·럭스의 광휘의 특이점(E)를 필요할 때 처리에 배분하고 진입 대응 자원을 남긴다.',
      CHECK_WAVE: '닿는 막타·경험치를 받으며 양쪽 처리 방향을 파악한다. 미확인인 채로 유지·크래시 성공을 가정하지 않는다.',
      SLOW_PUSH: '막타를 우선하고, 상대가 줄이는 속도보다 조금 더 처리할 여유가 있을 때만 쌓는다.',
      TRIM_RECEIVE: '안전한 막타를 받고 과하게 쌓이는 상대 미니언만 일부 줄인다. 프리징이나 당겨지는 결과를 보장하지 않는다.',
      TOWER_CS: '포탑 공격과 내 공격으로 받을 수 있는 막타를 고른다. 받을 수 없는 CS를 위해 퇴로까지 포기하지 않는다.',
      RETURNING: '이전 크래시가 완료됐다는 예시에서 돌아오는 미니언을 아군 쪽에서 받는다. 상대가 유지하면 더 나가지 않는다.',
      FAST_PUSH: '귀환 전 남긴 처리 자원을 써 현재 웨이브를 줄인다. 다음 웨이브에 막히면 포탑 도달·귀환 창을 얻었다고 보지 않는다.'
    }[planId];
    if(reference&&planId==='TRIM_RECEIVE'&&!low&&!unknown)handling='막타 중심으로 수급하고, 상대가 밀어올 때만 과도한 미니언을 일부 줄인다. 억지로 프리징을 만들기 위해 체력을 내주지 않는다.';
    const purpose = p.goal === 'RECALL' ? recallOpen ? '처리 여유를 귀환·구매 시간으로 바꾼다.' : '귀환 전 잃을 자원을 줄이고 밀어 넣을 여유를 마련한다.' : p.goal === 'FARM' || low ? '교환보다 CS·경험치와 다음 수급 자원을 확보한다.' : milestoneGoal;
    const reserve = coach.wave.selected.reserve[0];
    const pace = { id: planId === 'ACQUIRE_PUSH' ? 'ACQUIRE_THEN_MODULATE' : planId === 'FAST_PUSH' ? 'FAST' : planId === 'SLOW_PUSH' ? 'LAST_HIT_PLUS' : planId === 'CHECK_WAVE' ? 'OBSERVE_FROM_ACCESS' : 'SELECTIVE_CLEAR', label: labels[planId] };
    const pressure = { id: jungleNear || low || unknown || p.goal === 'FARM' || p.goal === 'RECALL' ? 'LIMITED' : absent ? 'CS_SPACE' : 'CS_EDGE', label: jungleNear ? '줄이기 · CS 자리 밖 추격 금지' : absent ? '남은 원딜의 막타 접근 제한' : '닿는 막타 자리만 압박' };
    const exposure = { id: jungleNear ? 'HOME_CONNECTED' : 'ALLY_CONNECTED', label: jungleNear ? '아군 쪽 퇴로에 붙기' : '동료·미니언과 연결된 자리' };
    // Preview and applied scenario use the same precedence (resources, intervention, goal, unknowns).
    const combatFor = enemyKey => {
      let combat = coach.selection.id === 'SHORT_POKE' ? coach.selected.action : id === 'A' ? '상대가 막타에 접근하면 사거리 끝 짧은 공격으로 공간을 지키고, 물러나면 CS·처리 시간을 얻는다.' : coach.selected.action;
      if(planId==='ACQUIRE_PUSH')combat='카이사가 막타를 치러 나오면 노틸러스의 위치를 보고 평타를 넣은 뒤, 럭스 쪽으로 거리를 벌린다. 견제 때문에 미니언 잡기가 늦어지면 견제를 멈추고, 남긴 기술로 진입에 대응한다. '+coach.selected.action;
      if(reverse)combat = period==='LEVEL1' ? skill('Kaisa','Q')+'로 받을 수 있는 CS를 확보하고 동료와 연결한다. 아직 배우지 않은 알리스타의 연속 진입을 전제하지 않는다.' : '배운 '+skill('Alistar','W')+'·'+skill('Alistar','Q')+'에 '+skill('Kaisa','P')+' 후속이 닿을 때만 교환을 비교한다. 룰루의 보호·변이가 남으면 연장을 강제하지 않는다.';
      if (valid && id === 'A' && enemyKey === 'SPENT') combat = early ? '럭스와 함께 앞으로 나와 카이사의 막타를 방해하고, 상대가 물러나면 미니언을 먼저 잡는다. 카이사를 쫓아붙기보다 견제할 공간을 넓힌다.' : '럭스와 함께 공격할 수 있는 자리에서 카이사의 막타를 방해한다. '+skill('Nautilus','R')+'를 배웠고 사용할 수 있다면, 닻을 빗맞혔어도 앞으로 깊게 나가지 않는다.';
      if (absent) combat = name(slot('enemies', 'BOTTOM')) + '의 막타 접근과 웨이브만 제한적으로 압박한다. 서포터 부재를 추격·다이브 허가로 쓰지 않는다.';
      if (jungleNear) combat = '앞으로 나가는 교환 폭은 줄이고 막타·처리 선택권을 지킨다. 상대의 전진이 지원군과 연결됐을 가능성도 다시 본다.';
      if (low || p.goal === 'FARM') combat = '남는 자원으로 수급 공간을 지킨다. 상대가 물러나 주는 CS·처리 시간까지 포기하지 않는다.';
      if (recallOpen) combat = '추가 교환보다 귀환용 처리·이탈 자원을 남긴다. 상대가 처리를 막으면 밀어 넣기를 중단한다.';
      if(id==='A'&&s.engage!=='NONE'&&!low&&!unknown)combat='이미 교전을 시작한 가정에서는 선처리 경쟁보다 남은 동료 후속·제어·퇴로를 먼저 비교한다. 반격과 연결이 남으면 대응하고, 끊기면 교환을 끝낸 뒤 처리 계획을 다시 고른다.';
      if (unknown) combat = '막타·경험치 접근부터 확보한다. 모르는 상대 위치를 확인하러 깊게 나가지 않는다.';
      if (id === 'C' && !low && !unknown && !jungleNear && !recallOpen) combat = coach.selected.action;
      if(noFollowup)combat='아군 호응이 불가능하면 함께 전진하는 교환을 강제하지 않는다. 받을 막타·경험치와 퇴로·지원·귀환을 비교한다.';
      return combat;
    };
    const combat = combatFor(s.enemy_key);
    const position = reference&&!jungleNear&&!unknown?'앞 급소에 닿고 걸어서 돌아올 자리에서 CS를 받는다. '+skill('Malphite','Q')+' 뒤 이동 속도 차이로 퇴로가 길어지면 전진 폭을 줄인다.':jungleNear ? '아군 쪽 퇴로와 후속이 닿는 자리에 서고, 웨이브를 따라 깊게 전진하지 않는다.' : '아군 후속과 걸어서 돌아올 거리가 남는 쪽에 선다. 미니언은 일부 투사체 대응 수단이며 전체 안전선이 아니다.';
    const nextWave = planId==='ACQUIRE_PUSH' ? '처리 우위를 얻었으면 막타 중심으로 낮춰 쌓고 상대의 CS 접근을 압박한다. 맞밀기에 밀리면 더 전진하지 않고 일부 줄이며 받는다. 선레벨·크래시는 별도다. 상대 쪽에 웨이브가 멈추면 다음 수급의 전진 부담도 다시 본다.' : recallOpen ? '웨이브가 실제 상대 포탑에 닿은 뒤 귀환·구매를 비교한다. 도달하지 못하면 다음 웨이브에 더 노출될 부담을 먼저 줄인다.' : planId === 'TOWER_CS' ? '받은 뒤 체력·구매와 다음 웨이브 복귀를 비교한다. 다이브 인원·퇴로가 나쁘면 경험치·생존을 우선한다.' : planId === 'RETURNING' ? '돌아오는 웨이브가 멈추면 다시 처리량을 조절한다. 멀리 나가 상대 쪽에 묶이지 않는다.' : '상대 쪽에 웨이브가 멈추면 다음 수급에 더 나가야 한다. 자원·지원이 끊기면 추가 쌓기를 접고 일부 정리·귀환을 비교한다.';
    const changeIf = absent ? '상대 서포터 복귀·정글 개입·동료 후속 단절이면 압박을 접는다.' : jungleNear ? '상대 쪽에서 웨이브가 멈추거나 퇴로가 끊기면 추가 전진을 끝낸다.' : p.goal === 'RECALL' ? '처리를 방해받거나 포탑 도달 여유가 사라지면 귀환 계획을 바꾼다.' : coach.trade.ours.end[0];
    const choiceId = reverse ? 'PRESERVE_FOLLOWUP' : recallOpen ? 'PROCESS_FOR_RECALL' : p.goal === 'FARM' ? 'FARM_ACCESS' : coach.selection.id;
    const choice = { id: choiceId, same_across_preferences: reverse || recallOpen || low || unknown || p.goal === 'FARM' || coach.selection.same_across_preferences,
      cost: reverse ? '일부 즉시 압박과 선처리 기회를 양보하고 체력·후속 자원을 남긴다.' : recallOpen ? '지금의 견제·킬 기회를 일부 포기하고 처리·구매 시간을 얻는다.' : coach.actions.find(a => a.id === coach.selection.id)?.costs[0] || '앞으로 선 자리와 처리 자원이 비용이다.',
      reserve, reason: reverse ? '이 조건부 참고에서는 성향을 바꿔도 선택이 같습니다. 새로운 공격 후보의 실행 근거가 필요합니다.' : recallOpen || p.goal === 'FARM' ? '현재 목적에서는 성향을 바꿔도 선택이 같습니다. 필요한 수급·처리 조건이 우선입니다.' : coach.selection.reason };
    const wave = { plan_id: planId, label: labels[planId], purpose, handling, position, combat, next_wave: nextWave, change_if: changeIf, completed: false,
      state: { position: s.wave, minion_size: 'UNOBSERVED', reinforcements: 'UNOBSERVED', origin: 'HYPOTHETICAL_LOADING_EXAMPLE' },
      conditions: { resources: s.resources, enemy_key: s.enemy_key, enemy_jungle: p.enemy_jungle, clear_window: p.clear_window },
      axes: { pace, pressure, exposure, resources: { id: recallOpen ? 'PROCESS_AND_EXIT' : 'RESERVE_RESPONSE', label: '처리·교환·대응 자원을 따로 남김', reserve } },
      steps: [{ number: 1, text: handling }, { number: 2, text: combat }, { number: 3, text: nextWave }], claim_ids: claims, basis: 'DESIGN_HYPOTHESIS' };
    wave.diagram = { ...clone(coach.diagram), plan_id: planId, steps: wave.steps, supported: coach.diagram.supported && !unknown };
    if (absent) wave.diagram.enemies = wave.diagram.enemies.filter(c => c !== slot('enemies', 'SUPPORT'));
    if(usable && id==='A'){wave.opponent_response='노틸러스는 선처리를 노려도 진입 공간이 사라질 만큼 빨리 밀지 않을 수 있다. 상대의 느린 처리를 처리 능력 부족으로 단정하지 않는다.';wave.success='사거리·자원·퇴로를 남긴 채 CS 접근과 다음 처리 선택권을 얻는 것. 킬·선레벨·크래시 보장은 아니다.';}
    if(reference){wave.opponent_response=reference.opponent.means;wave.success='체력·마나와 다음 막타 접근을 남기며 급소·수급 공간을 얻는 것. 강제 선푸시·처치가 성공 조건은 아니다.';}
    const allKnowledge = knowledge || { matchups: [], sources: [] };
    const knownMatches = allKnowledge.matchups.filter(m => slot('allies', m.role) === m.allies[0] && slot('enemies', m.role) === m.enemies[0] && (m.role !== 'BOTTOM' || m.carry_only || slot('allies', 'SUPPORT') === m.allies[1] && slot('enemies', 'SUPPORT') === m.enemies[1]));
    const lanes = ['TOP', 'MID', 'BOTTOM'].map(position => {
      const match = knownMatches.find(m => m.role === position), ownLane = position === input.own_position;
      const sourcePush = early && match?.id === 'A' && coach.context.patch.status !== 'MISMATCH';
      return { position, label: roleNames[position], allies: [slot('allies', position), ...(position === 'BOTTOM' ? [slot('allies', 'SUPPORT')] : [])].filter(Boolean), enemies: [slot('enemies', position), ...(position === 'BOTTOM' ? [slot('enemies', 'SUPPORT')] : [])].filter(Boolean), priority: ownLane ? coach.selected.metrics.PUSH.assessment : sourcePush ? 'ALLY' : 'INSUFFICIENT', reason: ownLane ? coach.selected.metrics.PUSH.reason : sourcePush ? '정확히 연결된 바텀 공략의 초반 접근 강점 · 선레벨 보장 아님' : '이 라인의 푸시 상성 근거가 연결되지 않았다.', claim_ids: sourcePush ? ['A-WAVE'] : ownLane ? coach.selected.metrics.PUSH.claim_ids : [] };
    });
    const jungler = slot('allies', 'JUNGLE');
    const linkSlots = { Ornn: 'Q', Ahri: 'E', Lux: period === 'LEVEL1' ? 'E' : 'Q', Lulu: 'W', Darius: 'E', Ashe: 'R', Janna: 'Q', Ziggs: 'W' };
    const jungleLinks = lanes.filter(l => jungler && l.allies.length).map(l => {
      const link = l.allies.map(c => ({ champion: c, key: linkSlots[c] })).find(c => c.key && (c.key !== 'R' || !early));
      return { position: l.position, jungler, allies: l.allies, means: link ? skill(link.champion, link.key) : null,
        condition: link ? '해당 기술 습득·적중과 정글의 실제 후속 거리가 맞을 때의 후보' : '연결할 제어·후속 기술의 근거를 더 확인해야 함',
        available_example: p.ally_jungle === 'AVAILABLE', observed_route: false, basis: 'DESIGN_HYPOTHESIS' };
    });
    const threats = [];
    const addThreat = (champion, key, response, action, condition) => {
      if (!input.enemies.some(v => v.champion === champion) || !fact(champion, key)) return;
      threats.push({ id: champion + ':' + key, champion, slot: key, label: skill(champion, key), mechanism: fact(champion, key).text,
        response_kind: response, action, condition, basis: 'DESIGN_HYPOTHESIS', mechanism_basis: 'OFFICIAL_MECHANISM', evidence_ids: ['official:' + champion + ':' + key] });
    };
    addThreat('Nautilus', 'Q', 'BLOCK_LINE', '미니언으로 훅 선을 가리되 측면·지형 접근을 함께 존중한다. 소모 뒤에는 CS·처리 공간부터 얻는다.', '맞힐 선과 남은 평타 제어·후속이 따로 있음');
    addThreat('Nautilus', 'R', 'EXPOSURE_AND_FOLLOWUP', '6레벨 이후 대상 노출과 진입 후 후속 거리를 관리한다. 맞으면 동료 보호·제어로 추가 공격 연결을 끊는 선택을 비교한다.', '대상 추적형 수단이며 미니언 뒤가 전체 안전을 보장하지 않음');
    addThreat('Alistar', 'W', 'EXPOSURE_AND_FOLLOWUP', id === 'B' && valid ? skill('Alistar', 'W') + ' 뒤에도 ' + skill('Alistar', 'Q') + '와 카이사 후속을 따로 본다. 룰루가 자유롭고 카이사에게 닿을 때만 원딜 집중 반격을 비교한다.' : '접근 뒤 남은 제어와 상대 후속을 따로 본다. 아군 보호·퇴로가 연결될 때만 반격을 비교한다.', '알리스타 기술 하나의 소모가 전체 교전 승리 아님');
    addThreat('LeeSin', 'R', 'EXPOSURE_AND_FOLLOWUP', '리 신이 옆이나 뒤로 붙으면 공격을 더 잇기보다 아군 쪽으로 거리를 벌린다. 밀려난 뒤에도 상대의 추가 공격을 끊을 아군과 연결한다.', '6레벨 이후 배운 궁극기 가정; Q를 피했어도 다른 접근까지 사라진 것은 아님');
    addThreat('Kaisa', 'R', 'MARK_AND_ACCESS', '플라즈마 표식·접근이 겹치면 고립을 피하고 이탈·아군 연결을 남긴다.', '6레벨 이후 가용·접근 조건이 맞는 한타 예시');
    addThreat('Zed', 'R', 'RESERVE_AND_FOLLOWUP', '6레벨 이후 측면 노출을 줄이고 대응 자원을 남긴다. 진입 뒤에도 남은 후속을 끊을 동료와 연결한다.', '실제 로밍·위치·사용 가능은 관측하지 않음');
    addThreat('LeeSin', 'Q', 'BLOCK_LINE', '투사체 적중 선과 적중 뒤 접근을 나눠 대응한다. 미니언 대응만으로 다른 접근까지 끝났다고 보지 않는다.', '정글 위치·다른 접근 수단과 구분');
    addThreat('Malphite', 'R', 'EXPOSURE_AND_FOLLOWUP', '6레벨 이후 뭉친 배치·접근 노출을 줄이고, 맞은 뒤 상대 후속과 분리될 대응을 남긴다.', '반응 회피만을 전제로 하지 않는 한타 예시');
    addThreat('Ambessa', 'Q', 'CONTACT_AND_EXIT', '끝거리 견제와 붙은 교전을 구분하고, 첫 돌진만 보고 남은 이탈이 끝났다고 추격하지 않는다.', '가까운 CS 자리 압박과 처치·추격 승패는 별개');
    threats.sort((a, b) => a.id.localeCompare(b.id));
    const protectors = report.contexts.teamfight.partners.filter(p => p.kinds.includes('COVER')).map(p => p.champion).sort();
    const controllers = report.contexts.teamfight.partners.filter(p => p.kinds.includes('PICK')).map(p => p.champion).sort();
    const fight = {
      role: report.roles.proposed.label, partners: [...new Set([...protectors, ...controllers])].sort(), threats,
      target: sideRole ? '본대와 떨어진 추격 대신 연결 가능한 가까운 상대를 고른다.' : '보호·퇴로를 잃지 않고 닿는 상대부터 공격한다. 뒤의 원딜만 잡으러 들어가지 않는다.',
      start: self === 'Caitlyn' ? '아군 제어가 적중하고 후속 거리가 맞으면 사거리 끝에서 공격한다. ' + skill('Caitlyn', 'W') + ' 연계는 설치·발동 여유가 있을 때만 잇는다.' : self === 'Ezreal' ? skill('Ezreal', 'Q') + '로 접근 전에 체력을 깎고, 배운 ' + skill('Ezreal', 'E') + '를 남긴 채 닿는 대상을 공격한다.' : self === 'Yunara' ? skill('Yunara', 'Q') + ' 강화와 ' + (slot('allies', 'SUPPORT') === 'Lulu' ? '룰루 지원' : '아군 후속') + '이 함께 닿는 창에서 공격한다. 피격 뒤에도 남은 보호·후속으로 반격할 수 있는지 따로 본다.' : self === 'Fiora' ? '피오라는 ' + skill('Fiora', 'W') + '로 받아낼 수단과 복귀 경로를 정한 뒤 접근한다. 사이드 압박을 깊은 추격으로 바꾸지 않는다.' : self === 'Darius' ? '가까운 대상에게 걸어서 닿을 때 공격하고, 배운 ' + skill('Darius', 'E') + '를 상대 이탈에 쓸지 남긴다.' : '내가 배운 공격·제어와 아군 후속이 같은 대상에 닿는 범위에서 시작한다.',
      setup: sideRole ? '시작 전 사이드 자원과 본대 복귀 거리를 맞춘다. 숨은 진입이 유리하다는 별도 판정은 하지 않는다.' : protectors.length ? '보호가 닿는 아군 뒤·옆에서 시작하고, 전방 제어가 닿은 대상과 연결한다.' : '확인된 아군 후속과 내 퇴로가 함께 남는 배치에서 시작한다.',
      stop: '보호·후속이 끊기거나 상대 접근에 내 퇴로가 닫히면 공격 대상·위치를 바꾼다. 적 체력이 낮다는 이유만으로 추격하지 않는다.',
      after: '교전 뒤 남은 인원·체력·웨이브로 닿는 포탑·목표물 또는 귀환을 고른다.', kill: 'UNDETERMINED', chase: 'UNDETERMINED', basis: 'DESIGN_HYPOTHESIS', claim_ids: claims
    };
    const ownSupport = slot('allies', 'SUPPORT');
    const operations = {
      mode: sideRole ? 'SIDE_RETURN' : input.own_position === 'BOTTOM' ? 'GROUP_CONNECTED' : 'FRONT_CONNECT',
      placement: sideRole ? '피오라가 복귀 경로를 남긴 사이드 자원을 맡고, 본대는 합류 전 강제 교전을 피하는 예시다.' : input.own_position === 'BOTTOM' ? '내가 아군과 연결된 중앙 수급을 맡고, 사이드는 복귀 가능한 아군이 받는 예시다.' : name(self) + '는 가까운 라인 자원과 본대 후속 거리를 연결하는 예시다.',
      priority: sideRole ? '사이드 CS·포탑 압박을 얻되 본대가 버틸 수 없는 싸움은 미리 접는다.' : '놓칠 웨이브를 먼저 정리하고 아군 제어와 연결해 포탑·목표물 접근 시간을 얻는다.',
      connection: sideRole ? '본대의 대기·복귀 수단이 사라지면 압박을 접고 가까운 안전한 수급으로 목표를 낮춘다.' : ownSupport && ownSupport !== self ? name(ownSupport) + '의 보호·제어가 닿는 거리와 전방 아군의 후속을 연결한다.' : '현재 역할의 후속 아군과 내 복귀 선택권을 연결한다.',
      concede: '합류까지 멀고 수급 손실이 큰 싸움은 억지로 따라가지 않는다. 대신 닿는 웨이브·구매 시간을 확보한다.',
      deny: '상대의 이동에 계속 늦게 반응해 웨이브와 목표물 접근을 함께 내주는 흐름을 줄인다.',
      fallback: sideRole ? '퇴로·본대 대기가 사라지면 더 깊은 포탑 압박 대신 합류·아군 쪽 수급으로 바꾼다.' : '정면 연결이 막히면 아군 쪽 웨이브·회복·구매를 확보하고 다시 모일 조건을 만든다.',
      growth: growth ? growth.label + ' · ' + growth.trigger + ' ' + growth.change + ' ' + growth.after : id === 'D' ? '카이사의 실제 진화·접근 또는 무라마나 변신을 따로 본다. 고정 3코어 전체 역전을 가정하지 않는다.' : '레벨·실제 구매 뒤 수단이 달라지면 역할을 재검토한다. 같은 코어 수를 같은 성장으로 세지 않는다.',
      steps: sideRole ? ['돌아올 수 있는 사이드 자원을 고른다.', '본대 대기·퇴로가 남는 만큼만 압박한다.', '연결이 끊기면 합류·수급으로 바꾼다.'] : ['먼저 받을 웨이브와 아군 연결 위치를 정한다.', '제어·보호가 연결되면 포탑·목표물 접근으로 바꾼다.', '연결이 끊기면 가까운 자원·구매로 재정비한다.'], basis: 'DESIGN_HYPOTHESIS', claim_ids: claims
    };
    // Reviewed official mechanics identify relevant actors; these action plans remain scoped inference.
    // This is a flank-exposure selection for a backline carry, not a universal danger ranking.
    const backline = bottom && report.roles.base.id==='FOLLOW_DAMAGE' && coach.context.patch.status!=='MISMATCH';
    const flankThreats = backline ? threats.filter(t=>(t.champion==='Zed'||t.champion==='LeeSin')&&t.slot==='R') : [];
    const flankActors = flankThreats.map(t=>t.champion).sort(), flankNames=flankActors.map(name).join('·');
    const flankSubject=flankNames+((flankNames.charCodeAt(flankNames.length-1)-0xAC00)%28?'이':'가');
    const frontActors = input.allies.filter(a=>a.champion!==self&&catalog.champions[a.champion]?.official_tags?.includes('Tank')).map(a=>a.champion).sort();
    const frontNames=frontActors.length?frontActors.map(name).join('·'):'앞을 지켜 주는 아군';
    const coverNames=protectors.length?protectors.map(name).join('·'):'도와줄 수 있는 아군';
    if(flankActors.length){
      const awareness={actors:flankActors,mechanism_ids:flankThreats.flatMap(t=>t.evidence_ids),
        scope:'후방 딜러의 측면 접근·고립 위험에 관한 후보; 다른 적의 위협이 없다는 뜻이 아니다.',
        basis:'DESIGN_HYPOTHESIS',observation:false,actual_positions:null,phase:'POST_LANE_ASSUMPTION',
        watch:flankNames+'의 마지막으로 보인 위치와 접근할 길을 기준으로 포탑을 더 때릴지, 어느 길로 이동할지 정한다.',
        missing:flankSubject+' 보이지 않으면 혼자 포탑을 계속 때리거나 어두운 강·정글을 가로지르지 않는다. 시야가 있는 아군 쪽에서 미니언을 챙기고 함께 이동한다.',
        visible:'다른 쪽에 보인 위치가 아직 유효하고 주변 인원·퇴로도 확보됐다면, 미니언을 밀고 아군과 포탑·목표물 압박을 늘린다.',
        keep:'적 위치를 찾으러 혼자 들어가지 않는다. 상대가 안 보여도 아군 가까이에서 얻을 미니언과 공간까지 포기하지 않는다.',
        stop:'마지막으로 본 정보가 오래됐거나 아군이 흩어지면, 더 깊은 포탑 공격·추격을 멈추고 함께 움직일 위치로 바꾼다.'};
      operations.awareness=awareness;
      operations.late_join=operations.concede;
      operations.concept='포탑 압박과 이동 전에, 측면 위협부터';
      operations.placement='중앙에서 '+coverNames+'와 함께 미니언을 잡고, 혼자 긴 사이드 라인 깊숙이 가지 않는다.';
      operations.connection=coverNames+'와 함께 움직이고, 앞을 지키는 아군이 시야를 확보한 길로 이동한다.';
      operations.priority='미드 미니언을 먼저 잡아 움직일 시간을 만들고, 아군과 드래곤·바론 주변에 먼저 자리 잡는다.';
      operations.concede=awareness.missing;
      operations.fallback='앞으로 나가기 어렵거나 뒤처졌다면 아군 포탑 가까이에서 미니언을 챙기고, 함께 움직일 인원과 구매를 갖춘 뒤 다시 압박한다.';
      operations.steps=[operations.priority,awareness.watch,awareness.missing];
      fight.role='앞라인 뒤에서 공격하며 측면 진입에 대응하는 원거리 딜러';
      fight.combo=fight.start; // CC/trap execution remains accessible as a secondary tip.
      const reserve=self==='Caitlyn'?skill('Caitlyn','E')+'은 단순 견제에 쓰지 말고, 접근하는 적과 거리를 벌릴 때 남긴다.':self==='Ezreal'?skill('Ezreal','E')+'은 더 때리러 들어가기보다 빠져나올 때 쓸 수 있게 남긴다.':'앞으로 나가 공격하는 데 방어·이탈 수단을 모두 쓰지 않는다.';
      fight.awareness={...awareness,phase:'POST_LANE_LEARNED_KIT',reserve,
        entered:flankSubject+' 옆으로 들어오면 앞의 적 추격을 멈추고 '+coverNames+' 쪽으로 이동해, 나에게 들어온 적부터 함께 공격한다.',
        danger:flankNames+'의 측면 진입에 대비해 '+(['Caitlyn','Ezreal'].includes(self)?skill(self,'E'):'빠져나올 수단')+'을 남기고, 들어오면 '+coverNames+' 쪽으로 이동해 함께 반격한다.',
        opening:'측면의 적이 다른 아군에게 진입했고 나에게 닿을 다른 수단이 없다면, 아군 앞라인을 넘지 않는 범위에서 닿는 적을 계속 공격한다.'};
      fight.concept='앞의 적을 때리되, 옆으로 들어오는 적에 대응';
      fight.setup=frontNames+' 뒤에서 '+coverNames+'의 도움을 받을 수 있는 거리를 유지한다.';
      fight.start='아군 앞라인 뒤에서 닿는 적부터 공격한다. '+flankSubject+' 안 보여도 보호받는 자리의 공격은 이어가되, 적을 따라 앞으로 걸어나가지는 않는다.';
      const enemyCarry=slot('enemies','BOTTOM');
      fight.target=(enemyCarry?name(enemyCarry)+'를 잡으러 적진으로 걸어가기보다, ':'')+'현재 닿는 적이나 나에게 들어온 적을 먼저 공격한다.';
      fight.stop='옆에서 적이 접근하거나 앞라인이 멀어지면 평타를 더 치려 하지 말고 '+coverNames+' 쪽으로 위치를 바꾼다.';
      fight.awareness.stop=fight.stop;
    }
    // Role-specific plans use verified own kit; they do not assert lane superiority.
    const roleKit=coach.context.patch.status!=='MISMATCH'&&
      ((self==='Ahri'&&input.own_position==='MID'&&fact(self,'Q')&&fact(self,'E')&&fact(self,'R'))||
       (self==='Sejuani'&&input.own_position==='JUNGLE'&&fact(self,'Q')&&fact(self,'E')&&fact(self,'R')));
    if(roleKit&&self==='Ahri'){
      operations.concept='미니언을 먼저 잡고, 정글과 함께 움직일 시간 만들기';
      operations.placement='라인 미니언을 먼저 잡은 뒤, 돌아올 길이 보이는 쪽에서 아군 정글러와 움직인다.';
      operations.connection=name(slot('allies','JUNGLE'))+'와 같은 적에게 닿을 거리에서 움직이고, 혼자 어두운 강을 건너 상대를 따라가지 않는다.';
      operations.priority='미니언을 밀어 넣어 만든 시간을 시야·바텀 지원·목표물 주변 자리로 바꾼다.';
      operations.concede='상대가 먼저 사라졌다면 보이지 않는 길로 따라가지 말고, 위험을 알린 뒤 남은 미니언과 안전한 합류 길을 비교한다.';
      operations.fallback='미니언을 밀거나 먼저 합류할 수 없다면 라인에서 골드·경험치를 챙기고, 가까운 아군에게 오는 적을 끊는다.';
      fight.concept='잡을 적을 찾되, 돌아올 길을 남기기';
      fight.role='매혹으로 공격 기회를 만들고 가까운 아군의 진입을 끊는 역할';
      fight.setup='아군에게 돌아올 길이 보이는 옆쪽에서 각을 잡고, 혼자 적 뒤로 깊게 돌지 않는다.';
      fight.start=skill('Ahri','E')+'이 닿고 아군도 함께 공격할 수 있을 때 연결한다. '+skill('Ahri','R')+'을 배웠다면 남은 이동을 복귀에 쓸 수 있는지 먼저 본다.';
      fight.target='아군과 함께 닿는 적을 노리고, 적 딜러에게 닿으려고 보호받는 적진을 혼자 가로지르지 않는다.';
      fight.stop='매혹이 빗나가거나 아군이 멀어지면 더 깊게 들어가지 않고, 남은 이동으로 아군 쪽에 돌아온다.';
    }else if(roleKit&&self==='Sejuani'){
      operations.concept='밀어 넣는 라인을 돕고, 함께 들어갈 시야 만들기';
      operations.placement='아군이 먼저 움직일 수 있는 라인 쪽에서 캠프·지원·목표물 준비를 연결한다.';
      operations.connection='라인 아군이 미니언을 놓치지 않고 따라올 수 있을 때 강과 정글에 함께 들어간다.';
      operations.priority='아군의 밀어 넣기를 도와 귀환·이동 시간을 만들고, 인원과 체력이 갖춰지면 목표물 주변 시야를 잡는다.';
      operations.concede='라인 아군이 포탑에 묶여 있으면 혼자 강 싸움이나 상대 정글 침입을 시작하지 않는다.';
      operations.fallback='라인 지원이 늦거나 체력이 부족하면 가까운 캠프를 챙기고, 상대가 아군 쪽으로 들어오는 길을 지키며 다음 합류를 준비한다.';
      fight.concept='진입할지, 뒤의 딜러를 지킬지 먼저 나누기';
      fight.role='아군 공격이 닿는 진입과 후방 보호 사이를 선택하는 역할';
      fight.setup='아군 딜러와 너무 멀어지지 않는 앞쪽에서 시작하고, 다른 앞라인이 진입하면 후방 보호가 남는지 본다.';
      fight.start=skill('Sejuani','R')+'을 배웠고 아군 공격이 닿는다면 적을 묶어 시작한다. 아군 딜러에게 적이 접근하면 진입보다 '+skill('Sejuani','Q')+'를 보호에 남기고, 서리가 최대로 중첩된 적에게 배운 '+skill('Sejuani','E')+'를 쓴다.';
      fight.target='혼자 적 딜러를 쫓기보다 아군이 함께 때릴 적이나 아군 딜러에게 붙은 적을 먼저 묶는다.';
      fight.stop='아군이 따라오지 못하거나 뒤의 딜러가 물리면 더 깊게 진입하지 않고 아군 쪽으로 돌아와 접근한 적을 끊는다.';
    }
    if(roleKit)operations.steps=[operations.priority,operations.connection,operations.fallback];
    // Paired plans describe possibilities under the same explicit period/wave assumptions.
    // Guide-backed mechanics do not certify this complete tactical interpretation.
    const ours = { purpose, means: combat, look_for: '상대 막타 접근과 처리 기술 소모를 CS·공간 이득으로 바꾼다.', avoid: position + ' ' + reserve, switch_when: changeIf };
    let theirs = { purpose: '상대의 구체적인 매치업 계획은 자료 부족이다.', means: '대표 매치업의 대응 문장을 다른 조합에 옮기지 않는다.', look_for: '연결할 매치업 공략·조건이 필요하다.', avoid: '상대 의도를 실제 관측으로 취급하지 않기', switch_when: '지원 근거를 확보하면 다시 판단한다.' };
    if (valid && id === 'A') {
      ours.means = early ? skill('Caitlyn', 'Q') + '와 배운 ' + skill('Lux', 'E') + '로 접근·처리 선택권을 만든다. 견제가 미니언까지 맞아 원치 않게 밀리지 않도록 처리량을 조절한다.' : '배운 ' + skill('Lux', 'Q') + ' 적중 뒤 짧게 잇고, ' + skill('Caitlyn', 'E') + '를 접근 대응에 남긴다. 구매만으로 올인 우세를 가정하지 않는다.';
      ours.look_for = s.enemy_key === 'SPENT' ? skill('Nautilus', 'Q') + ' 소모 뒤 남은 평타 제어·카이사 후속 밖에서 CS 접근·짧은 교환을 얻는다.' : '상대가 막타·처리에 집중할 때 사거리 끝 공간을 얻는다. 일부러 훅을 맞아 유도하지 않는다.';
      ours.avoid = '견제에 다음 처리·이탈 자원을 모두 쓰거나 미니언 뒤를 절대 안전선으로 여기지 않는다.';
      theirs = { purpose: '사거리 견제를 오래 받기보다 접근과 원딜 후속이 겹치는 교환을 만든다. 진입할 거리가 사라질 만큼 과하게 밀지 않는 선택도 있다.', means: skill('Nautilus', 'Q') + '·' + skill('Nautilus', 'P') + '로 접근·제어하고, 배운 ' + skill('Kaisa', 'Q') + '와 ' + skill('Kaisa', 'P') + ' 후속을 잇는 후보.', look_for: '상대 처리 기술·이탈 소모 또는 두 동료가 벌어진 순간을 노린다. 실제 적중·후속 거리는 별도다.', avoid: '후속 없이 긴 견제를 받거나 웨이브·포탑 안쪽까지 깊게 추격하지 않는다.', switch_when: absent ? '서포터 부재 예시이므로 남은 원딜은 깊은 맞교환 대신 받을 CS·퇴로를 확보한다.' : '접근이 막히거나 원딜 후속이 끊기면 수급·재정비로 바꾼다.' };
    } else if (valid && id === 'B') {
      ours.means = skill('Yunara', 'Q') + ' 강화와 룰루의 배운 보호·제어를 겹친다. 상대 선진입 뒤에도 룰루가 자유롭고 카이사에게 닿을 때만 집중 반격을 비교한다.';
      ours.look_for = '상대 제어 소모 뒤에도 강화·보호·후속이 남는 창을 본다. 피격만으로 후퇴나 반격 승리를 고정하지 않는다.';
      theirs = { purpose: '보호·강화가 연결되기 전에 한 대상을 접근·후속으로 압박하는 후보.', means: (period === 'LEVEL1' ? skill('Alistar', 'Q') : skill('Alistar', 'W') + '·' + skill('Alistar', 'Q')) + '와 카이사의 ' + skill('Kaisa', 'P') + ' 후속을 연결한다.', look_for: '룰루가 행동할 수 없거나 원딜과 분리된 경우. 실제 거리·기술·자원 확인이 필요하다.', avoid: '진입만 하고 카이사 후속이 닿지 않는 교환을 지속하지 않는다.', switch_when: '룰루 보호·유나라 강화가 겹쳐 반격하면 이탈 가능성과 남은 수급을 비교한다.' };
    } else if (valid && id === 'C') {
      ours.means = coach.selected.action;
      ours.look_for = '상대가 막타를 위해 가까이 오거나 돌진 뒤 공격·이탈 창이 갈릴 때 CS 자리를 얻는다.';
      theirs = { purpose: '붙은 장기전을 강요받기보다 끝거리 교환과 남은 이동 수단을 활용하는 후보.', means: skill('Ambessa', 'Q') + '와 ' + skill('Ambessa', 'P') + '의 공격·이동 연결. 다리우스의 실제 시작 기술에 따라 거리 계획을 바꾼다.', look_for: '다리우스가 처리·공격에 기술을 쓴 뒤 남은 접근·이탈을 비교한다.', avoid: '남은 돌진이 불명확한데 처치 가능한 싸움이라고 고정하지 않는다.', switch_when: '이탈 자원·후속이 끊기면 가까운 지속 교환 대신 막타·거리 회복을 선택한다.' };
    } else if (valid && id === 'D') {
      ours.means = skill('Ezreal', 'Q') + '로 견제·막타를 잇는다.' + (period === 'LEVEL1' ? ' 이 구간에는 걸어서 돌아올 거리와 동료 연결을 남긴다.' : ' 배운 ' + skill('Ezreal', 'E') + '를 접근 대응에 남긴다.');
      ours.look_for = '카이사가 접근할 표식·고립·진화 조건을 얻기 전에 닿는 견제·처리 시간을 얻는다.';
      theirs = { purpose: '진화·표식과 접근이 겹치는 고립된 교환 기회를 찾는 후보.', means: '카이사의 실제 진화 상태·' + skill('Kaisa', 'P') + ' 표식' + (early ? '을 만드는 공격·후속을 비교한다. 이 구간에는 궁극기 접근을 전제하지 않는다.' : '과 배운 ' + skill('Kaisa', 'R') + ' 접근을 비교한다.'), look_for: period === 'LEVEL1' ? '이즈리얼이 걸어서 돌아갈 거리·동료 연결을 잃는 고립. 미습득 이동기 소모를 기다리지 않는다.' : skill('Ezreal', 'E') + ' 소모·고립. 고정 3코어 전체 역전과는 다르다.', avoid: '견제만 받으면서 조건 없는 추격·올인을 강제하지 않는다.', switch_when: '상대 이탈·보호가 남거나 진입 후 후속이 끊기면 수급·정비로 바꾼다.' };
    }
    if(reverse){ours.means=combat;ours.purpose=purpose;ours.look_for='상대가 막타 자리를 양보하면 수급·공간을 얻는다. 룰루 지원이 끊긴 기회는 남은 강화·퇴로까지 비교한다.';ours.avoid='레벨 경쟁에 진입에 쓸 체력을 모두 소모하거나 원딜 후속 없는 진입을 강제하지 않는다.';theirs={purpose:'유나라 강화와 룰루 지원을 겹쳐 아군의 수급 접근을 압박하는 후보.',means:skill('Yunara','Q')+' 강화와 룰루의 배운 보호·제어를 함께 쓴다.',look_for:'알리스타의 접근과 카이사 후속이 갈라지거나 자원이 부족한 순간을 비교한다.',avoid:'서포터 제어만 보고 카이사의 남은 후속까지 사라졌다고 생각하지 않는다.',switch_when:'강화·보호가 끊기거나 진입 후 반격이 닿으면 교환 길이·위치를 바꾼다.'};}
    if (valid && id === 'A' && s.enemy_key === 'SPENT') { theirs.means = skill('Nautilus', 'P') + '와 카이사의 남은 후속은 있지만, 훅으로 여는 계획은 다시 사용 가능해질 때까지 미룬다.'; theirs.look_for = '상대가 스스로 평타 제어·카이사 후속 거리로 들어오는 경우만 비교한다. 훅 소모를 새 진입 수단으로 쓰지 않는다.'; }
    if (low || unknown || p.goal === 'FARM' || recallOpen) {
      ours.purpose = purpose; ours.means = combat;
      ours.look_for = low || unknown ? '닿는 막타·경험치와 걸어서 돌아올 공간을 얻는다.' : recallOpen ? '상대가 처리를 방해하지 않는 여유를 구매 시간으로 바꾼다.' : '상대가 양보한 CS·처리 시간을 얻는다.';
      ours.switch_when = changeIf;
    }
    if(reference){Object.assign(ours,{purpose,means:combat,look_for:'말파이트의 마나 부족·반격 기술 소모와 닿는 급소를 CS·공간 이득으로 바꾼다.',avoid:reference.selected.reserve,switch_when:changeIf});theirs=clone(reference.selected.opponent||reference.opponent);theirs.purpose=theirs.purpose.replace(/^Q 견제/,skill('Malphite','Q')+' 견제');}
    if (absent) {
      ours.means = combat;
      theirs.means = name(slot('enemies', 'BOTTOM')) + '만 남은 부재 예시다. 지원 없는 진입 대신 닿는 막타와 퇴로를 확보한다.';
      theirs.look_for = '상대 처리·견제가 닿지 않는 수급 창을 이용한다.';
    }
    if (jungleNear) { ours.means = combat; ours.look_for = '전진 압박은 낮추되 가까운 CS·처리 선택권을 남긴다.'; }
    const playbook = { supported: usable, ours, theirs, claim_ids: claims, basis: 'DESIGN_HYPOTHESIS', enemy_intent: 'POSSIBLE_PLAN_NOT_OBSERVED' };
    const coverage = { status: !usable ? 'UNSUPPORTED' : id === 'A' ? 'BASIC_PLAN_CONDITIONAL' : 'CONDITIONAL_REFERENCE', matchup: id,
      plan_scope: usable ? '조건부 기본 목적·웨이브·양쪽 상대법 연결' : '일반 역할만 제공 · 개별 상대법 미지원',
      gaps: reference?'공략 기반 수급·대응과 조건부 견제 판단. 전체 올인·동일 골드 빌드별 역전·누적 유지력 우열은 자료 부족.':id === 'A' && valid ? '초반 사거리·푸시 공략 범위. 지속 교전·올인·후반 전체 우열 자료 부족.' : usable ? '기전·조건부 참고. 전체 2대2/근접 지속 교전 승패는 미확인.' : '이 조합의 구간별 공략 근거가 연결되지 않았다.', effect_sample: 0 };
    const quick = [];
    if(valid && id === 'A')quick.push({id:'KEY_SPENT',label:'노틸러스 핵심 기술 소모',scenario:{enemy_key:'SPENT'},planning:{},reason:'남은 평타 제어·카이사 후속은 유지하고 CS 접근·짧은 교환 창만 비교'});
    if(reference&&period!=='LEVEL1')quick.push({id:'KEY_SPENT',label:skill('Malphite','E')+' 소모',scenario:{enemy_key:'SPENT'},planning:{},reason:'공격 속도 감소 창은 줄지만 Q·강화 공격·궁극기와 마나는 별도로 남음. 올인 승리로 바꾸지 않음'});
    if(supportCase)quick.push({id:'SUPPORT_ABSENT',label:'상대 서포터 부재',scenario:{},planning:{enemy_support:'ABSENT'},reason:'남은 원딜·정글·복귀 위험을 고려한 제한적 압박'});
    const reverseClaims = reverse ? allKnowledge.matchups.find(m=>m.id==='B')?.claims.filter(c=>claims.includes(c.id)) || [] : [];
    const allClaims = [...knownMatches.flatMap(m => m.claims),...reverseClaims], sourceIds = new Set(allClaims.flatMap(c => c.source_ids));
    // Loading conclusions are not the execution procedure. Keep detailed wave axes intact.
    const laneConclusion = unknown ? '받을 자원을 확보하며 기본 계획을 적용할 상황을 좁힌다.' : low ? '체력·마나를 남기며 받을 CS·경험치를 확보한다.' : ['RECALL','FARM'].includes(p.goal) ? purpose : s.engage!=='NONE' ? '남은 동료 후속과 퇴로 안에서 교환을 정리하고 수급을 잇는다.' : ['UNDER_TOWER','INCOMING','RETURNING'].includes(s.wave) ? '받아올 자원을 지키고 다음 압박·구매 선택권을 남긴다.' : p.goal==='PRESSURE'?'닿는 막타 자리에서 공간과 처리 선택권을 얻는다.':reference?'체력·마나를 남기며 수급하고 닿는 급소만 압박한다.':overallGoal;
    const laneSupport=unknown?'깊은 압박을 확정하지 않고 닿는 수급·복귀 자원을 남긴다.':low?'추가 교환보다 다음 수급과 대응에 쓸 자원을 확보한다.':p.goal==='RECALL'?'추가 교환보다 구매 시간과 복귀할 자원을 얻는 것이 목적이다.':p.goal==='FARM'?'상대가 양보하는 공간은 얻되 수급 자원을 교환에 모두 쓰지 않는다.':s.engage!=='NONE'?'선처리 경쟁보다 남은 반격·동료 연결·복귀를 비교한다.':['UNDER_TOWER','INCOMING','RETURNING'].includes(s.wave)?'상대 미니언을 필요한 만큼 줄이고 깊은 수급으로 생길 부담을 낮춘다.':id==='E'?'걸어서 돌아올 공간을 남긴다.':id==='A'&&early?'먼저 처리 여유를 만든 뒤 사거리 견제로 상대 수급을 제한한다.':id==='C'?'상대가 이탈하면 추격 대신 가까운 막타 자리와 공간을 얻는다.':id==='D'?'장거리 견제로 수급을 잇고, 고립된 맞딜은 강제하지 않는다.':'동료의 후속과 남은 보호가 함께 닿는 교환을 고른다.';
    const growthCopy = {
      A: '초반 사거리·짧은 견제를 활용하되, 이후 지속 교전·올인 우세는 별도다.',
      B: '유나라의 강화 공격과 룰루 지원이 겹치는 창을 활용한다.',
      BR: '알리스타의 접근과 카이사 후속이 함께 가능한 성장 구간을 기다린다.',
      C: period==='LEVEL1'&&coach.selected.metrics.EXTENDED.assessment==='ALLY' ? 'Lv1 근접 지속 교전 우세를 CS 자리 압박으로 바꾼다.' : '시작 기술·접촉 거리가 달라지면 Lv1 근접 우세를 이어 쓰지 않는다.',
      D: '실제 진화·접근 수단과 무라마나 변신 때 교환 거리를 다시 잡는다.',
      E: '말파이트 방어 구매 뒤에는 처리·성장으로 전환한다.'
    };
    const growthConclusion = usable ? growth ? growth.change : growthCopy[id] : '구간별 우열을 정할 매치업 자료가 아직 없다.';
    const loadingSummary = {
      schema_version:'lol-coach-loading-direction-v1',
      items:[
        {id:'lane',title:'라인전 목적과 기본 방식',conclusion:laneConclusion,support:laneSupport},
        {id:'growth',title:'강한 구간과 성장 전환',conclusion:growthConclusion,support:usable?(growth?'전체 상성 역전과 특정 접근·위치의 위험 증가는 다르다.':id==='E'?'방어 구매 전 저마나에서 압박 기회를 더 본다.':'교환 방식의 강점을 처치·추격 가능으로 확대하지 않는다.'):'자료 부족을 동률이나 안전으로 대신하지 않는다.'},
        {id:'operations',title:'운영 방향',conclusion:sideRole?'복귀 가능한 사이드 자원을 맡고 본대와 연결한다.':bottom?'아군과 연결된 중앙 수급을 포탑·목표물 접근으로 바꾼다.':'가까운 자원과 본대 후속 거리를 연결한다.',support:sideRole?'본대 합류와 돌아올 자원을 함께 남긴다.':'먼 싸움의 합류 손실과 가까운 자원을 비교한다.'},
        {id:'fight',title:'한타 역할과 공격 시작',conclusion:self==='Caitlyn'?'아군 제어가 맞으면 보호 연결 안에서 닿는 대상을 공격한다.':self==='Ezreal'?'접근 전 견제하고 이탈 수단을 남긴 채 공격한다.':self==='Fiora'?'받아칠 수단과 본대 복귀 경로를 정한 뒤 접근한다.':self==='Yunara'?'강화 공격과 아군 지원이 같은 대상에 닿을 때 공격한다.':self==='Darius'?'걸어서 닿는 가까운 대상을 아군 후속과 함께 공격한다.':'보호·후속과 퇴로가 연결된 자리에서 닿는 대상을 공격한다.',support:'닿는 대상부터 아군 후속과 함께 공격한다.'}
      ],
      changes:[id==='E'&&period==='LEVEL1'&&!low&&!unknown?skill('Malphite','Q')+' 뒤 퇴로가 길어지면 교환 종료.':id==='A'&&!low&&!unknown?'측면 진입·동료 후속 단절이면 교환 종료.':changeIf,low?'수급에 쓸 자원까지 줄면 귀환·구매를 비교한다.':id==='E'?'방어 구매 뒤에는 압박보다 처리·구매를 우선한다.':'교환으로 다음 처리·대응 자원이 부족해지면 수급으로 바꾼다.',jungleNear?'개입 후속과 퇴로가 겹치면 깊은 전진을 끝낸다.':'정글 개입·후속 단절이면 전진 폭을 줄인다.'],
      origin:'ANALYSIS_ASSUMPTIONS_NOT_OBSERVATION',method_label:'방법 보기'
    };
    // Explain opposing plans from the same exact lane and ten-pick capabilities.
    // A capability is not a measured matchup winner or an observed player intention.
    const ownLaneName=[self,...(bottom?[slot('allies','SUPPORT')]:[])].filter(Boolean).map(name).join('·');
    const enemyLaneName=[slot('enemies',input.own_position),...(bottom?[slot('enemies','SUPPORT')]:[])].filter(Boolean).map(name).join('·')||'상대 배치 미확인';
    const laneViews={
      A:['케이틀린·럭스는 멀리서 공격해 상대가 미니언에 다가오기 어렵게 만드는 조합이다.','카이사·노틸러스는 거리를 좁혀 두 명이 함께 공격할 기회를 노릴 수 있다.','먼 거리의 짧은 견제와 접근 후 함께 때리는 싸움이 맞붙는 라인이다.'],
      B:['유나라·룰루는 강화 공격에 보호·지원 기술을 겹치는 방식으로 싸운다.','카이사·알리스타는 한 명에게 접근해 두 명이 함께 공격할 기회를 노릴 수 있다.','누가 먼저 맞았는지만이 아니라 강화·보호와 원딜의 추가 공격이 남는지가 중요하다.'],
      BR:['카이사·알리스타는 체력을 아껴 미니언을 잡고, 접근과 원딜 공격을 함께 쓸 기회를 만든다.','유나라·룰루는 강화 공격과 보호 기술을 함께 써서 가까이 오는 상대를 압박할 수 있다.','상대 강화·보호가 겹친 싸움과 알리스타 접근 뒤 카이사 공격이 닿는 싸움을 나눠 본다.'],
      C:['다리우스는 가까이 붙은 싸움에서 계속 공격할 수 있는지를 본다.','암베사는 기술 끝거리에서 공격하거나 남은 이동 수단으로 거리를 벌릴 수 있다.','Lv1 시작 기술과 붙어 있을 수 있는지가 핵심이며, 상대가 빠져나간 뒤의 추격은 별도다.'],
      D:['이즈리얼은 멀리서 공격하고 상대가 다가올 때 빠져나올 수단을 남기는 방식이다.','카이사는 표식·진화와 접근 수단이 갖춰진 뒤 가까운 싸움을 노릴 수 있다.','견제가 닿는 거리와 카이사가 접근한 뒤의 싸움은 다르며, 서포터에 따른 2대2 우열은 별도다.'],
      E:['피오라는 닿는 급소를 짧게 공격하면서 미니언 골드·경험치를 놓치지 않는 것이 기본이다.','말파이트는 원거리 견제로 급소·미니언에 다가오는 피오라의 체력을 깎고 거리를 벌릴 수 있다.','급소에 닿고 빠지는 피오라와 멀리서 견제하는 말파이트가 맞붙는 라인이다.']
    };
    const view=usable?laneViews[id]?.slice():null;
    if(view&&id==='C'&&period!=='LEVEL1')view[2]='이 구간의 교환 우열은 자료가 부족하므로 Lv1 판단을 그대로 적용하지 않고 남은 기술과 이탈 가능성을 다시 본다.';
    const signals=side=>(report.composition?.[side]?.signals||[]).filter(v=>v.evidence_ids?.length).slice().sort((a,b)=>(a.champion+':'+a.kind).localeCompare(b.champion+':'+b.kind));
    const oursSignals=signals('allies'),theirSignals=signals('enemies');
    const has=(rows,k)=>rows.some(v=>v.kind===k);
    const group=(rows,k)=>rows.filter(v=>v.kind===k).map(v=>({champion:v.champion,name:name(v.champion),skills:v.evidence_ids.map(ref=>{const [,c,key]=ref.split(':');return skill(c,key);}),fact_ids:v.evidence_ids}));
    let ourStyle=has(oursSignals,'PICK')?(has(oursSignals,'COVER')?'적을 묶는 기술과 아군을 지키는 기술을 함께 쓸 수 있다.':'적을 묶고 같은 대상을 함께 공격할 기회를 만들 수 있다.'):has(oursSignals,'PRESSURE')?'적이 다가오기 전에 견제로 체력을 깎을 수 있다.':'확인된 공격 수단과 아군이 함께 공격할 거리를 먼저 맞춘다.';
    const theirStyle=has(theirSignals,'ACCESS')?'상대는 거리를 좁혀 떨어진 아군을 먼저 공격할 수 있다.':has(theirSignals,'PRESSURE')?'상대는 멀리서 체력을 깎아 우리를 물러나게 할 수 있다.':'상대가 싸움을 여는 주된 방법은 현재 자료에서 분명하지 않다.';
    if(usable&&id==='A')ourStyle='케이틀린의 먼 거리 공격을 럭스의 속박·보호와 함께 쓰는 조합이다.';
    if(usable&&id==='E')ourStyle=oursSignals.some(v=>v.champion!==self&&['COVER','PICK'].includes(v.kind))?'피오라는 다른 라인에서 포탑을 압박하고, 나머지 아군은 보호·방해 기술로 합류할 시간을 버는 계획이다.':'피오라는 다른 라인에서 포탑을 압박할 수 있지만, 아군이 싸움을 피하며 기다릴 수 있는지는 따로 봐야 한다.';
    if(usable&&id==='B')ourStyle='유나라가 강화 공격을 이어갈 동안 룰루가 보호·방해 기술로 돕는 조합이다.';
    const accessNames=[...new Set(theirSignals.filter(v=>v.kind==='ACCESS').map(v=>v.champion))].map(name).join('·');
    const opposingStyle=accessNames?accessNames+'처럼 거리를 좁히는 상대가 떨어진 아군을 먼저 잡는 싸움을 노릴 수 있다.':theirStyle;
    const means={ours:Object.fromEntries(['PICK','COVER','PRESSURE','ACCESS'].map(k=>[k,group(oursSignals,k)])),theirs:Object.fromEntries(['PICK','COVER','PRESSURE','ACCESS'].map(k=>[k,group(theirSignals,k)]))};
    const macroMatchup=sideRole?(has(theirSignals,'ACCESS')?'우리의 사이드 압박과 상대의 강제 교전이 충돌하므로, 따로 미는 동안 아군이 먼저 잡히지 않을 거리가 중요하다.':'사이드에서 얻는 골드·포탑과 아군이 함께 싸울 수 있는 시간을 맞추는 구도다.'):(has(theirSignals,'ACCESS')?'아군이 함께 때릴 수 있는 거리와 상대가 뛰어들 거리가 부딪히는 구도다.':'먼저 미니언을 밀고 움직일 시간과 상대의 견제를 버틸 체력이 중요한 구도다.');
    const fightMatchup=has(theirSignals,'ACCESS')?(has(oursSignals,'COVER')?'상대가 뛰어든 뒤 아군 보호가 닿고 같은 대상을 함께 때릴 수 있는지가 공격 기회를 만든다.':'상대가 다가올 때 빠져나올 길과 아군이 함께 공격할 거리가 중요하다.'):'먼 거리의 공격으로 체력을 깎는 동안 누가 먼저 적을 묶거나 가까워질 수 있는지가 중요하다.';
    const areaContext={
      lane:{ours:view?.[0]||ownLaneName+'의 공격·방어 수단을 같은 라인 안에서 비교한다.',theirs:view?.[1]||enemyLaneName+'의 이 매치업 계획은 아직 자료가 부족하다.',matchup:view?.[2]||'구체적인 상성 근거가 없는 상대에게 기존 예시의 유리·불리 판단을 옮기지 않는다.',action:ours.means,basis:usable?'CONDITIONAL_REFERENCE':'INSUFFICIENT',claim_ids:claims,winner:'UNDETERMINED'},
      operations:{ours:ourStyle,theirs:opposingStyle,matchup:macroMatchup,action:operations.priority,basis:'DESIGN_HYPOTHESIS',means,claim_ids:claims,winner:'UNDETERMINED'},
      fight:{ours:ourStyle,theirs:opposingStyle,matchup:fightMatchup,action:fight.start,basis:'DESIGN_HYPOTHESIS',means,claim_ids:claims,winner:'UNDETERMINED'},
      origin:'ANALYSIS_ASSUMPTIONS_NOT_OBSERVATION'
    };
    loadingSummary.items[0].support=unknown||low||s.engage!=='NONE'||!['EVEN','BUILDING'].includes(s.wave)||p.goal!=='AUTO'?laneSupport:areaContext.lane.matchup;
    loadingSummary.items[2].support=sideRole&&has(theirSignals,'ACCESS')?'내가 다른 라인을 미는 동안 상대가 아군에게 먼저 싸움을 걸 수 있다.':'함께 공격할 아군과 상대의 접근·견제를 함께 고려한다.';
    loadingSummary.items[3].support=fightMatchup;
    const summary=loadingSummary.items;
    if(!unknown&&!low&&p.goal==='AUTO'&&s.engage==='NONE'&&['EVEN','BUILDING'].includes(s.wave)){
      if(id==='E')summary[0].conclusion='체력을 아끼며 미니언을 잡고, 닿는 급소만 짧게 공격한다.';
      if(id==='A'&&early)summary[0].conclusion='멀리서 견제해 상대의 막타를 방해하고 먼저 움직일 기회를 만든다.';
    }
    if(usable&&id==='E')summary[1]={...summary[1],conclusion:'말파이트가 방어 아이템을 사면 무리한 공격보다 내 아이템을 갖춘다.',support:'방어 아이템이 없고 마나도 적을 때는 급소를 공격할 기회를 본다.'};
    summary[2].conclusion=sideRole?'사이드 라인에서 미니언을 잡고 포탑을 압박하되, 아군에게 합류할 길을 남긴다.':bottom?'아군 가까이에서 미니언을 잡고, 함께 포탑·드래곤·바론을 노린다.':'가까운 라인에서 성장하고 아군이 싸울 때 함께 공격할 거리를 유지한다.';
    if(self==='Fiora')summary[3].conclusion='피오라의 응수(W)로 막을 기술과 빠져나올 길을 정한 뒤 접근한다.';
    if(self==='Caitlyn')summary[3].conclusion='아군의 속박·기절이 맞으면 보호받을 거리에서 닿는 적을 공격한다.';
    if(operations.awareness){summary[2].conclusion=operations.priority;summary[2].support=operations.awareness.watch;summary[3].conclusion=fight.start.split('. ')[0]+'.';summary[3].support=fight.awareness.danger;areaContext.operations.action=operations.priority;areaContext.fight.action=fight.start;}
    const sentence=value=>{const text=plainLanguage(value).trim().split(/(?<=[.!?])\s+/)[0]||'이 조건의 자료가 부족합니다.';return /[.!?]$/.test(text)?text:text+'.';};
    const briefing={schema_version:'lol-coach-loading-brief-v2',origin:'ANALYSIS_ASSUMPTIONS_NOT_OBSERVATION',basis:'DESIGN_HYPOTHESIS',items:[
      {id:'our_plan',title:'우리 팀의 승리 방식',text:sentence(!sideRole&&has(oursSignals,'PICK')&&has(oursSignals,'COVER')?'아군이 적을 묶으면 보호받는 거리에서 함께 공격하고, 포탑·목표물을 노린다.':ourStyle),target:'operations'},
      {id:'enemy_plan',title:'상대 팀의 가능한 승리 방식',text:sentence(theirStyle),target:'operations'},
      {id:'my_role',title:'이번 판의 내 역할',text:sentence(summary[3].conclusion),target:'fight'},
      {id:'key_change',title:'가장 중요한 변경 조건',text:sentence(loadingSummary.changes[0]),target:'lane'}
    ],limits:'실제 관측이 아닌 비교용 조건입니다. 개별 매치업의 근거 범위는 상세에서 구분합니다.'};
    const application=coach.knowledge_application;
    const evidenceBridge=application?.supported?{
      schema_version:'lol-coach-counterplay-evidence-bridge-v1',
      statistics:{matchup:application.statistics||null,tactical_confirmation:false,calculation:'PRESERVED_ARCHIVE_PROJECTION_NOT_TACTICAL_VALIDATION',role:'추세·반례 점검 자료이며 개별 교전 우세나 최적 행동의 증명은 아니다.'},
      expert:{plan:application.recommended_plan,reason:application.reason,source_ids:application.direct_sources.map(s=>s.source_id),sources:clone(application.direct_sources),conditions:clone(application.conditions),exceptions:clone(application.exceptions)},
      counterplay:{purpose:ours.purpose,opponent_goal:theirs.purpose,wave_plan:wave.label,trade:ours.means,punish:ours.look_for,growth:loadingSummary.items[1].conclusion},
      inference:clone(application.inference),application_active:application.active,real_effect:'NOT_MEASURED_N0'
    }:null;
    const result = {
      schema_version: 'lol-coach-player-planboard-v1', context: { origin: 'HYPOTHETICAL_LOADING_EXAMPLE', planning, actual_enemy_positions: null, standard: coach.context.assumptions.label, patch: coach.context.patch.label },
      brief: { lane: labels[planId] + ' · ' + (id==='C'&&coach.selected.metrics.EXTENDED.assessment==='ALLY'?'근접 지속 교전 우세 추론':valid ? coach.trade.ours.label : '교전 자료 부족'), operations: sideRole ? '복귀할 수 있는 사이드 압박을 맡고 본대와 연결한다.' : bottom ? '중앙 수급을 아군과 잇고 제어 뒤 목표물로 전환한다.' : '가까운 자원과 본대 후속 거리를 연결한다.', fight: self === 'Caitlyn' ? '아군 제어가 맞으면 보호 연결 안에서 닿는 대상을 공격한다.' : self === 'Ezreal' ? '접근 전 견제하고 이탈 수단을 남긴 채 공격한다.' : self === 'Fiora' ? '사이드 복귀와 받아칠 수단을 정한 뒤 접근한다.' : self === 'Yunara' ? '강화·아군 지원이 함께 닿을 때 공격하고 후속이 끊기면 바꾼다.' : fight.start },
      loading_summary:loadingSummary, briefing_v2:briefing, evidence_bridge:evidenceBridge, area_context:areaContext,
      composition: {ours:report.summary?.our_plan?.split('. ')[0],theirs:report.summary?.enemy_plan?.split('. ')[0],ours_full:report.summary?.our_plan,theirs_full:report.summary?.enemy_plan,role:report.summary?.my_role,basis:'DESIGN_HYPOTHESIS'},
      headline: usable ? overallGoal : '확인된 수단으로 수급·연결부터 준비한다.',
      lane: { concept:valid&&id==='A'&&planId==='ACQUIRE_PUSH'?{plan_id:planId,text:'럭스와 함께 압박해, 미니언을 먼저 잡을 공간 만들기'}:null, overall_goal: overallGoal, milestone: { id: period, label: coach.selected.label, goal: milestoneGoal }, can_push: coach.wave.can_push, should_push: coach.wave.should_push,
        strong_fight: id==='C'&&coach.selected.metrics.EXTENDED.assessment==='ALLY' ? '근접 지속 교전 우세 추론 · 접촉 유지 조건' : reverse ? '상대 강화·보호가 겹치지 않는 조건부 후속 창 · 전체 우열 미확인' : valid ? coach.trade.ours.label : '개별 매치업 자료 부족', avoid: id === 'A' ? '사거리 안쪽에 붙은 장기전·올인 승리는 별도 판단' : '처치·추격을 교환 선호와 동일시하지 않기',
        induce: absent ? '남은 상대가 막타에 접근할 때 제한적 압박' : '상대의 막타 접근·처리 기술 사용을 짧은 공간 이득으로 연결', gain: 'CS 접근·처리 시간·귀환 선택권', basis: usable ? id === 'A' && early ? 'GUIDE_BASED' : 'CONDITIONAL' : 'INSUFFICIENT', claim_ids: claims },
      overall: { lanes, jungle_links: jungleLinks, risk: [slot('enemies', 'JUNGLE'), slot('enemies', 'MID')].filter(Boolean).map(name).join('·') + '의 개입 가능성을 전진 비용에 포함한다. 실제 로밍·정글 동선은 미관측이다.', route_prediction: false },
      operations, fight: {...fight,formations:formation?.evaluate(input,{...catalog,coaching_knowledge:allKnowledge})}, wave, choice, growth, matchup_playbook: playbook, coverage,
      reminders: [valid && id === 'A' ? '측면 진입·럭스 후속 단절이면 교환 종료.' : changeIf, p.goal === 'RECALL' ? '빠른 처리와 실제 포탑 도달은 별개다.' : '교환에 다음 처리·대응 자원을 모두 쓰지 않는다.', growth ? '성장 후에도 남는 견제·연결 수단을 활용한다.' : '정글 미확인은 전진 폭을 조절할 이유이며 모든 처리·교전 금지가 아니다.'],
      quick_scenarios: quick,
      evidence: { claims: allClaims, sources: allKnowledge.sources.filter(s => sourceIds.has(s.id)), official_facts: threats.map(t => ({ ...fact(t.champion, t.slot), champion: t.champion })) }
    };
    if(fight.awareness){result.brief.fight=summary[3].conclusion;result.composition.role=name(self)+': '+fight.role+'.';}
    const roleFacts=roleKit?['Q','E','R'].map(k=>'official:'+self+':'+k):[];
    if(roleKit){
      summary[2].conclusion=operations.priority;summary[2].support=operations.concede;
      summary[3].conclusion=fight.start.split('. ')[0]+'.';summary[3].support=fight.stop;
      areaContext.operations.action=operations.priority;areaContext.fight.action=fight.start;
      result.composition.role=name(self)+': '+fight.role+'.';result.brief.fight=summary[3].conclusion;
      if(self==='Ahri'){
        areaContext.lane.ours='아리는 미니언을 잡을 체력·마나를 남기고, 먼저 밀어 넣을 수 있을 때 정글과 움직일 시간을 만든다.';
        areaContext.lane.action='상대가 미니언에 기술을 썼다면 견제와 미니언 잡기 중 이득을 고른다. 매혹을 놓쳤다면 재진입보다 거리부터 회복한다.';
        areaContext.lane.basis='ROLE_PRINCIPLE_NOT_MATCHUP_ADVANTAGE';
      }
    }
    // Six independent dimensions, never one composition score. Only source-linked signals participate.
    const teamSide=(rows,team)=>{
      // Explicit effect-linked additions for the current content scope. Unknown
      // profile classifications are not evidence that a champion lacks a means.
      rows=rows.slice();
      for(const [id,key,kind,effect] of [['Vi','R','PICK',/공중/],['Vi','Q','ACCESS',/돌진/],['Renekton','E','ACCESS',/돌격/],['Karma','Q','PRESSURE',/폭발/],['Karma','W','PICK',/묶/],['Karma','E','COVER',/보호막/]]){
        const f=fact(id,key);
        if(input[team].some(p=>p.champion===id)&&f&&effect.test(f.text)&&!rows.some(r=>r.champion===id&&r.kind===kind))rows.push({champion:id,kind,evidence_ids:[f.id]});
      }
      const people=k=>[...new Set(rows.filter(r=>r.kind===k).map(r=>r.champion))];
      const names=k=>people(k).map(name).join('·');
      const pressure=people('PRESSURE'),pick=people('PICK'),access=people('ACCESS'),cover=people('COVER');
      const front=input[team].filter(x=>catalog.champions[x.champion]?.official_tags?.includes('Tank')).map(x=>x.champion);
      const side=input[team].some(x=>x.champion==='Fiora')&&fact('Fiora','Q')&&fact('Fiora','W')?'Fiora':null;
      const rearCover=cover.filter(champion=>input[team].some(p=>p.champion===champion&&['SUPPORT','MID'].includes(p.position)));
      const prepared=!!(pressure.length>=2&&pick.length&&rearCover.length);
      return {actors:{pressure,pick,access,cover,rearCover,front,side:side?[side]:[]},
        win:prepared?'먼저 자리 잡고 견제해 접근을 어렵게 만든 뒤, 닿는 적을 함께 공격해 포탑·목표물로 바꾼다.':access.length?'아군이 같은 대상에 닿는 방향에서 접근해 떨어진 적을 노리고, 교전 뒤 포탑·목표물을 얻는다.':'확인된 공격 수단을 함께 쓸 거리를 만들고, 밀 수 있는 라인에서 이동 시간을 얻는다.',
        field:prepared?'아군과 시야를 먼저 확보한 포탑·목표물 주변에서 정면 거리를 유지한다.':access.length?'옆으로 접근할 길이 있는 전장에서 고립된 적을 노린다. 어두운 길이 접근하는 쪽에도 안전하다는 뜻은 아니다.':'퇴로와 아군의 공격이 이어지는 전장을 고른다.',
        opening:pick.length?names('PICK')+'의 방해 기술로 공격 기회를 만들되, 아군이 닿지 못하면 진입을 이어가지 않는다.':pressure.length?names('PRESSURE')+'의 견제로 체력을 깎으며 접근할 기회를 만든다.':'교전을 열 수단의 지식이 부족하므로 선진입 성공을 전제하지 않는다.',
        damage:rearCover.length?rearCover.map(name).join('·')+'의 보호가 실제로 닿는 동안 공격을 이어간다. '+(front.length?'앞라인이 모두 멀리 진입하면 뒤의 딜러 보호는 사라질 수 있다.':'보호 기술 하나가 모든 접근을 막지는 않는다.'):access.length?names('ACCESS')+'의 접근을 같은 대상에 맞춰 공격을 집중한다. '+(cover.length?names('COVER')+'의 보호가 닿는지와 남은 수단은 별도로 확인한다.':'현재 연결된 후방 보호 자료가 없어, 접근 뒤 돌아갈 길을 남긴다.'):'서로 같은 적을 공격할 거리를 유지한다. 현재 연결된 보호 기술 자료가 없어 아군 수만으로 보호를 보장하지 않는다.',
        macro:side?name(side)+'의 사이드 압박과 중앙 움직임을 맞춘다. 사이드로 인원이 빠지면 중앙의 부족한 인원으로 교전을 강제하지 않는다.':prepared?'중앙 미니언을 먼저 잡고 함께 이동해 포탑·목표물 주변을 선점한다. 사이드 미니언을 받을 아군도 따로 정한다.':'밀어 넣을 라인과 함께 움직일 아군을 정하고, 상대가 갈라졌을 때 가까운 포탑·목표물을 노린다.',
        avoid:prepared?'진형이 갈라진 채 어두운 지역을 추격하거나, 앞라인과 뒤의 딜러가 서로 도울 수 없게 벌어지지 않는다.':access.length?'먼 거리 견제를 계속 맞으며 좁은 입구로 따로 진입하지 않는다.':'도와줄 아군보다 먼저 깊게 들어가지 않는다.',
        evidence_ids:[...new Set(rows.flatMap(r=>r.evidence_ids).concat(side?['official:Fiora:Q','official:Fiora:W']:[]))],
        basis:'MECHANISM_LINKED_INFERENCE',prepared};
    };
    const teamOurs=teamSide(oursSignals,'allies'),teamTheirs=teamSide(theirSignals,'enemies');
    result.team_plan={schema_version:'lol-coach-team-plan-v1',observation:false,basis:'MECHANISM_LINKED_INFERENCE',
      assumptions:'비슷한 성장과 배운 기술을 사용할 수 있는 기본 구도. 실제 위치·스킬 가용성은 관측하지 않았습니다.',
      scope:'확인된 기술 기능을 조합한 참고 계획이며 전체 조합 우열·교전 승리를 검증한 판정이 아닙니다.',
      rows:[['win','승리 방식'],['field','원하는 전장·접근 방향'],['opening','싸움을 여는 방식'],['damage','공격·보호 구조'],['macro','운영 방향'],['avoid','피해야 할 상황']].map(([id,label])=>({id,label,ours:teamOurs[id],theirs:teamTheirs[id]})),
      ours:teamOurs,theirs:teamTheirs,rule_ids:['source-linked-team-dimensions-v1'],
      phases:[{id:'early',label:'초반',text:'각 라인은 미니언을 밀거나 받아야 할 조건을 확인하고, 정글은 먼저 움직일 수 있는 아군과 지원을 연결한다. 개별 라인 우열은 해당 매치업 근거가 있는 범위에서 판단한다.'},
        {id:'mid',label:'중반',text:teamOurs.macro},
        {id:'objective',label:'목표물 교전',text:teamOurs.prepared?'아군과 먼저 자리를 잡고 상대가 접근하게 만든다. 진입하는 아군과 뒤의 딜러를 지킬 아군을 나누되, 사이드 방어로 인원이 줄면 시작을 늦춘다.':teamOurs.field+' '+teamOurs.damage}]};
    if(coach.context.patch.status==='MISMATCH')result.team_plan=null;
    if(result.team_plan){
      result.composition.ours=teamOurs.win;result.composition.theirs=teamTheirs.win;
      result.composition.ours_full=teamOurs.win+' '+teamOurs.macro;result.composition.theirs_full=teamTheirs.win+' '+teamTheirs.macro;
      areaContext.operations.ours=teamOurs.macro;areaContext.operations.theirs=teamTheirs.macro;
      areaContext.fight.ours=teamOurs.damage;areaContext.fight.theirs=teamTheirs.opening;
      result.operation_headline=backline&&teamOurs.prepared?'라인에서 만든 압박을 중앙 포탑과 목표물로 옮기세요':roleKit&&self==='Ahri'?'라인에서 만든 시간을 정글·다른 라인 지원에 쓰세요':roleKit?'아군이 함께 싸울 자리부터 만들고, 진입과 보호를 나누세요':null;
      if(backline)result.reminders=[slot('enemies','SUPPORT')?name(slot('enemies','SUPPORT'))+'가 나에게 접근할 길이 열려 있나?':'상대가 나에게 접근할 길이 열려 있나?',flankActors.length?flankNames+'의 마지막 위치와 지금 접근할 길은 어디인가?':'보이지 않는 상대가 옆으로 접근할 수 있나?','내가 공격받으면 바로 도와줄 아군이 옆에 있나?'];
      if(roleKit)result.reminders=self==='Ahri'?['지금 움직이면 라인 미니언을 얼마나 놓치나?','매혹이 맞아도 아군이 함께 공격할 수 있나?','남은 이동으로 아군에게 돌아올 수 있나?']:['라인 아군이 먼저 움직일 수 있나?','내가 들어가면 아군 공격이 닿나?','다른 앞라인이 진입했을 때 뒤의 딜러는 누가 지키나?'];
    }
    result.action_summaries=actionSummaries(result,coach,report);
    if(roleKit&&self==='Ahri'){
      const a=result.action_summaries.lane.items;
      const values=[areaContext.lane.ours,'체력·마나를 남긴 채 미니언을 먼저 잡을 여유를 만들고, 밀어 넣기 전에는 무조건 합류하러 떠나지 않는다.',areaContext.lane.action,'매혹이 없는 동안 상대에게 다가갈 때는 남은 방어·이탈 수단과 돌아올 거리를 남긴다.','상대가 먼저 사라지거나 미니언을 밀 수 없으면 따라가기보다 위험을 알리고 라인 손실을 줄인다.'];
      a.forEach((x,i)=>{x.text=values[i];x.basis='ROLE_PRINCIPLE';x.knowledge_state='GENERAL_PRINCIPLE';x.rule_ids.push('Ahri-mid-methods-v1');x.evidence_ids=roleFacts;x.source_paths=['area_context.lane','role_principles'];});
      result.role_principles={lane:values,basis:'ROLE_PRINCIPLE_NOT_MATCHUP_ADVANTAGE',evidence_ids:roleFacts};
      summary[0].conclusion=values[0];summary[0].support='밀어 넣고 움직일 시간과 매혹 적중·복귀 경로를 비교한다. 매치업 우열은 별도 자료가 필요하다.';
    }
    if(roleKit&&self==='Sejuani'){
      const values=['아군이 미니언을 잃지 않고 함께 싸울 수 있는 라인을 지원한다.','아군이 밀어 넣기를 요청하고 함께 마무리할 수 있다면 돕되, 유지하려는 미니언을 임의로 밀지 않는다.','아군 공격이 닿을 때 접근하고, 지원이 끊기면 상대를 끝까지 쫓지 않는다.','상대 정글 위치를 모른다면 라인 아군이 먼저 움직일 수 있는지부터 보고 강에 들어간다.','갱킹 각이 없으면 근처 캠프로 돌아가 성장하고 다음 지원 시간을 만든다.'];
      result.role_principles={lane:values,basis:'JUNGLE_SUPPORT_NOT_LANE_MATCHUP',evidence_ids:roleFacts};
      summary[0].conclusion=values[0];summary[0].support='정글 사용자는 라인별 지원·합류 조건을 본다. 라인 미니언을 임의로 밀지 않는다.';
      result.action_summaries.lane.items.forEach((x,i)=>{x.text=values[i];x.basis='ROLE_PRINCIPLE';x.knowledge_state='GENERAL_PRINCIPLE';x.rule_ids.push('Sejuani-jungle-support-v1');x.evidence_ids=roleFacts;x.source_paths=['role_principles.lane'];});
    }

    if(roleKit){
      const dangerActors=threats.filter(x=>['Zed','LeeSin'].includes(x.champion)&&x.slot==='R');
      const actorNames=dangerActors.map(x=>name(x.champion)).join('·');
      const danger=self==='Ahri'?(actorNames?actorNames+'의 측면 접근이 가능한 동안에는 복귀할 이동을 남기고, 매혹이 없을 때 고립된 옆각을 만들지 않는다.':'매혹이 없거나 돌아올 이동이 부족하면 혼자 옆으로 깊게 돌지 않는다.'):(actorNames?actorNames+'이 아군 딜러에게 접근하면 남긴 방해 기술을 보호에 쓰고, 이미 들어간 적을 쫓지 않는다.':'아군 딜러가 공격받으면 남긴 방해 기술을 보호에 쓰고, 혼자 적 뒤를 쫓지 않는다.');
      result.fight.role_danger=danger;
      const item=result.action_summaries.fight.items[3];item.text=danger;item.source_paths=['fight.role_danger'];item.threat_ids=dangerActors.flatMap(x=>x.evidence_ids);item.selection_scope='현재 조합에서 확인한 접근 수단에 대한 역할별 조건부 대응';
    }
    const condition = (area,key,trigger,action,keep,stop,paths,actors=[],extra={}) => ({
      id:key,trigger,action,keep,stop,actors:actors.filter(Boolean),
      basis:'DESIGN_HYPOTHESIS',observation:false,provenance_scope:'LINKED_CONTEXT_AND_RULE_NOT_TACTICAL_PROOF',
      phase:area==='lane'?period:'POST_LANE_LEARNED_KIT',
      knowledge_state:area==='lane'&&!usable?'GENERAL_PRINCIPLE':'SOURCE_SCOPE_LIMITED',
      source_paths:paths,rule_ids:['player-planboard-v1','condition-response:'+key],
      claim_ids:[...claims],...extra
    });
    const laneChange = valid&&id==='A' ? condition('lane','ENEMY_KEY_SPENT',
      skill('Nautilus','Q')+'이 빗나갔다면',combatFor('SPENT'),
      skill('Nautilus','P')+'와 카이사의 추가 공격은 남아 있다. 럭스가 함께 공격할 거리와 빠져나올 기술을 남긴다.',
      '노틸러스가 다시 다가오거나 럭스가 함께 공격할 수 없으면 교환을 끝낸다. 상대 기술을 다시 쓸 수 있으면 이 기회도 끝난다.',
      ['wave.combat','wave.conditions','wave.change_if','fight.threats'],['Nautilus'],
      {scenario_patch:{enemy_key:'SPENT'},applied:s.enemy_key==='SPENT',
       conditions:['해당 기술을 배웠고 빗맞혀 소모했다는 가정이다.','체력·마나, 웨이브, 정글 개입, 귀환 목적 등 나머지 선택 조건은 그대로 적용한다.'],
       evidence_ids:['official:Nautilus:Q','official:Nautilus:P']}) : condition('lane','LANE_PLAN_CHANGE',
      '이 조건이면 현재 계획을 바꾼다',changeIf,position,combat,
      ['wave.change_if','wave.position','wave.combat'],[slot('enemies',input.own_position)],
      {conditions:[coach.context.assumptions.label],limits:'특정 기술 소모 후의 대응이 없는 매치업은 기존 계획의 변경 기준만 제공한다.'});
    result.condition_responses={schema_version:'lol-coach-condition-responses-v1',origin:'HYPOTHETICAL_LOADING_EXAMPLE',
      lane:[laneChange],
      operations:[sideRole ? condition('operations','SIDE_RETURN_BLOCKED',
        '사이드에서 돌아갈 길이 막히거나 아군이 버티기 어렵다면',operations.fallback,
        operations.priority,operations.connection,
        ['operations.fallback','operations.priority','operations.connection'],[self]) : condition('operations','LATE_JOIN',
        '합류가 늦고 미니언도 많이 놓친다면',operations.late_join||operations.concede,
        operations.connection,operations.fallback,
        [operations.late_join?'operations.late_join':'operations.concede','operations.connection','operations.fallback'],[self,ownSupport!==self?ownSupport:null])],
      fight:[condition('fight','FOLLOWUP_WINDOW',self==='Caitlyn'&&controllers.length?'아군이 묶은 적에게 함께 공격할 수 있다면':'아군과 같은 대상을 공격할 수 있다면',
        fight.start,fight.target,fight.stop,['fight.start','fight.target','fight.stop'],[self]),
        condition('fight','CONNECTION_LOST','아군 보호가 멀어지거나 옆에서 적이 접근한다면',
        fight.stop,fight.setup,'아군 보호와 퇴로가 다시 이어지기 전에는 낮은 체력의 적을 쫓지 않는다.',['fight.stop','fight.setup','fight.target'],[self])]
    };
    if(operations.awareness){
      const a=operations.awareness,f=fight.awareness;
      result.condition_responses.operations.unshift(condition('operations','FLANK_UNSEEN',
        flankSubject+' 보이지 않는다면',a.missing,a.keep,a.stop,
        ['operations.awareness.missing','operations.awareness.keep','operations.awareness.stop'],flankActors,
        {evidence_ids:a.mechanism_ids,conditions:[a.scope,'실제 위치를 읽지 않는 운영 참고 계획이다.']}));
      result.condition_responses.operations.push(condition('operations','FLANK_SEEN_ELSEWHERE',
        flankSubject+' 다른 쪽에 보인다면',a.visible,a.keep,a.stop,
        ['operations.awareness.visible','operations.awareness.keep','operations.awareness.stop'],flankActors));
      result.condition_responses.fight.unshift(condition('fight','FLANK_ENTRY',
        flankSubject+' 옆에서 들어온다면',f.entered,f.reserve,f.stop,
        ['fight.awareness.entered','fight.awareness.reserve','fight.stop'],flankActors,
        {evidence_ids:[...f.mechanism_ids,...(self==='Caitlyn'?['official:Caitlyn:E']:self==='Ezreal'?['official:Ezreal:E']:[])],conditions:[f.scope,'6레벨 이후 해당 기술을 배운 한타 예시; 실제 위치·가용 여부는 관측하지 않았다.']}));
      result.condition_responses.fight.push(condition('fight','FLANK_COMMITTED',
        '측면의 적이 다른 아군에게 진입했다면',f.opening,f.reserve,f.stop,
        ['fight.awareness.opening','fight.awareness.reserve','fight.stop'],flankActors));
      // Existing follow-up case remains an execution tip, not the first tactical priority.
      const combo=result.condition_responses.fight.find(x=>x.id==='FOLLOWUP_WINDOW');
      combo.action=fight.combo;combo.source_paths[0]='fight.combo';
    }
    const scenario=(area,key,trigger,action,reason,exception,actors,evidence)=>condition(area,key,trigger,action,reason,exception,
      ['condition_responses.'+area+'.'+key],actors,{reason,evidence_ids:evidence,conditions:['조건을 직접 확인했을 때의 참고 안내이며 현재 관측이 아니다.'],priority:'CONTEXTUAL',rule_ids:['situation-rule:'+key]});
    if(valid&&id==='A'){
      result.condition_responses.lane.push(
        scenario('lane','LUX_BIND_HIT',skill('Lux','Q')+'이 적중했다면',
          '배운 '+skill('Caitlyn','W')+'를 대상 발밑에 연결하고 닿는 거리에서 공격한다.',
          '속박된 위치에 덫을 놓을 기회다. 덫 설치·발동 시간과 아군 공격 거리가 필요하다.',
          '노틸러스에게 잡힐 위치까지 걸어가야 하거나 덫을 배우지 않았다면 연결을 강제하지 않는다.',['Lux','Caitlyn'],['official:Lux:Q','official:Caitlyn:W']),
        scenario('lane','LUX_BIND_MISSED',skill('Lux','Q')+'이 빗나가고 '+skill('Nautilus','Q')+'이 남았다면',
          '카이사를 더 때리러 전진하지 말고, 럭스와 거리를 맞춘 채 닿는 미니언을 잡는다.',
          '럭스의 즉시 속박이 없는 동안 노틸러스가 접근할 기회를 줄인다.',
          '상대가 물러나 주는 미니언과 공간까지 포기하지 않는다. 상대 접근 수단과 아군 지원이 바뀌면 다시 전진을 비교한다.',['Lux','Nautilus'],['official:Lux:Q','official:Nautilus:Q']));
    }
    if(backline&&frontActors.length>=2){
      result.condition_responses.fight.push(scenario('fight','FRONT_DEEP',frontNames+'이 모두 멀리 진입했다면',
        '자동으로 따라가지 말고 '+coverNames+' 쪽에서 닿는 적을 공격한다. 다른 아군도 도울 수 없다면 퇴로 쪽으로 거리를 벌린다.',
        '앞라인 인원 수와 지금 나를 보호할 수 있는 거리는 다르다.',
        '측면 접근이 막혔고 아군 보호가 다시 닿을 때만 전진 폭을 늘린다.',frontActors,oursSignals.filter(x=>frontActors.includes(x.champion)).flatMap(x=>x.evidence_ids)));
    }
    if(backline&&teamTheirs.actors.side.length){
      result.condition_responses.operations.push(scenario('operations','SIDE_PRESSURE','피오라가 사이드 포탑을 압박한다면',
        '혼자 긴 사이드로 가서 막기보다 방어할 아군을 정하고 중앙에서 얻을 포탑·미니언을 고른다.',
        '사이드 방어로 인원이 빠졌는데 다섯 명이 모인 것처럼 교전하면 중앙과 사이드를 함께 잃을 수 있다.',
        '방어할 아군이 없거나 포탑 손실이 더 크면 중앙 공격을 접고 함께 방어한다.',['Fiora'],['official:Fiora:Q','official:Fiora:W']));
    }
    if(roleKit){
      result.condition_responses.fight.unshift(scenario('fight','ROLE_PLAN_BREAKS',self==='Ahri'?'매혹이 빗나가거나 아군 공격이 닿지 않는다면':'다른 앞라인이 진입하고 아군 딜러가 공격받는다면',
        fight.stop,self==='Ahri'?'적중해도 아군과 떨어진 깊은 위치에서는 공격을 이어가기 어렵다.':'진입 기술을 모두 공격에 쓰면 뒤의 딜러에게 접근한 적을 끊을 수단이 줄어든다.',fight.setup,[self],roleFacts));
    }
    enrichCoaching(result,report,catalog,coach);
    attachWaitingDecision(result,report,catalog,coach);
    composeNarrative(result,report,catalog,coach);
    // Team descriptions always use the user's fixed team perspective. These are
    // authored tactics, never source quotations or observed facts.
    if(result.team_plan){
      const other=result.team_plan.theirs;
      for(const key of ['win','field','opening','damage','macro','avoid'])other[key]=other[key].replaceAll('아군','상대 팀원');
      result.team_plan.rows.forEach(row=>{row.theirs=other[row.id];});
      result.composition.theirs=other.win;result.composition.theirs_full=other.win+' '+other.macro;
      result.area_context.operations.theirs=other.macro;result.area_context.fight.theirs=other.opening;
    }
    return result;
  }

  // Waiting has an opportunity cost even when a fight is unavailable. This is
  // a conditional role principle, not a matchup advantage or an observed state.
  function attachWaitingDecision(b,report,catalog,coach){
    const input=report.input,pos=input.own_position,opts=coach.context.assumptions.scenario.overrides,
      planning=b.context.planning.overrides,team=key=>input[key],at=(key,role)=>team(key).find(p=>p.position===role)?.champion,
      name=id=>catalog.champions[id]?.name||'배치 미확인',fact=(id,key)=>catalog.champions[id]?.facts?.find(f=>f.slot===key),
      skill=(id,key)=>name(id)+'의 '+fact(id,key).name+'('+key+')';
    const support=at('allies','SUPPORT'),enemySupport=at('enemies','SUPPORT'),opponent=input.opponent_mode==='MANUAL'?input.lane_opponent:input.opponent_mode==='ASSIGNED'?at('enemies',pos==='SUPPORT'?'BOTTOM':pos):null;
    const duo=['BOTTOM','SUPPORT'].includes(pos),supportName=name(support),enemySupportName=name(enemySupport),opponentName=opponent?name(opponent):'맞상대 미확인';
    const patchOK=!['MISMATCH','UNKNOWN'].includes(coach.context.patch.status),low=opts.resources==='LOW',unconfirmed=opts.resources==='UNKNOWN'||opts.wave==='UNKNOWN';
    const mode=!patchOK?'SOURCE_REVIEW_REQUIRED':low||planning.ally_followup==='UNAVAILABLE'?'LIMIT_LOSS':unconfirmed?'CHECK_CONDITIONS':'CONDITIONAL_WINDOW';
    const w={schema_version:'lol-coach-waiting-cost-v1',rule_id:'waiting-cost-role-v1',mode,observation:false,basis:'DESIGN_HYPOTHESIS',outcome:'UNDETERMINED',
      actors:duo?[at('allies','BOTTOM'),support,opponent,enemySupport].filter(Boolean):[input.own_champion,opponent].filter(Boolean),
      conditions:{period:coach.selected_period,resources:opts.resources||'SUFFICIENT',wave:opts.wave||'EVEN',enemy_key:opts.enemy_key||'AVAILABLE',ally_followup:planning.ally_followup||'UNCONFIRMED',patch:coach.context.patch.status},evidence_ids:[],
      source_patch:catalog.source_patch,review_state:'TACTICAL_UNREVIEWED',source_paths:['waiting'],
      scope:'포지션 기본 판단과 제한된 기술 사례입니다. 픽만으로 현재 체력·스킬 습득·가용성·웨이브·동료 호응을 알 수 없으며, 전술 정확도나 교환 승리를 검증한 결과가 아닙니다.'};
    if(pos==='JUNGLE'){
      w.loss='갱킹 각이 없는데 기다리면 캠프 성장·경험치와 다음 지원 시간이 늦어진다. 반대로 라인을 떠나면 아군이 다이브나 큰 웨이브 손실을 받을 수도 있어 두 비용을 비교한다.';
      w.window='아군이 먼저 움직일 수 있고 배운 제어·후속 공격이 함께 닿으며 내 체력·레벨·퇴로가 남을 때 개입을 비교한다. 상대 정글의 위치는 관측한 범위만 사용한다.';
      w.fallback='호응이나 자원이 없으면 캠프·귀환으로 다음 개입을 준비한다. 아군이 다이브 위협을 받는다면 도착 가능 시간을 확인해 방어·역갱과 반대편 이득을 비교한다.';
      w.switch='상대 정글 목격, 라인 웨이브·체력, 아군 호응 또는 목표물 준비가 바뀌면 동선을 바꾼다. 고정 동선과 늦은 추격을 강제하지 않는다.';
    }else{
      w.loss=pos==='SUPPORT'?'함께 물러서기만 하면 아군 원딜의 CS·경험치, 체력과 웨이브 처리 여유·주도권을 잃을 수 있다. 개인 막타보다 아군의 수급과 견제를 막을 자리를 함께 지킨다.':'CS만 기다려도 경험치 범위에서 밀려나거나 체력·미니언·포탑 체력과 주도권을 잃을 수 있다. 상대가 밀어 넣고 귀환·로밍할 시간을 주는 비용도 비교한다.';
      w.window=duo?supportName+'와 함께 '+opponentName+'·'+enemySupportName+'의 견제·반격을 비교한다. 배운 기술과 레벨·체력·마나가 받쳐 주고, 적 미니언이 너무 많지 않으며 동료가 함께 공격할 거리일 때 짧은 교환부터 비교한다.':opponentName+'의 견제와 내 반격·이탈 수단을 비교한다. 배운 기술·레벨·자원과 미니언 수가 허용할 때 교환해 막타 공간을 만들고, 반격할 수 없다면 억지로 진입하지 않는다.';
      w.fallback=pos==='SUPPORT'?'교환 조건이 없으면 아군의 막타·경험치 접근을 보호하고, 웨이브 정리 지원·함께 귀환·시야 확보를 비교한다. 아군을 혼자 남겨도 되는 웨이브와 상대 진입 위험이 확인될 때만 로밍한다.':'교환 조건이 없으면 받을 경험치와 포기할 CS를 정하고, 배운 기술로 미니언을 줄일 여유·정글 지원·귀환을 비교한다. 포탑 아래에서도 견제·다이브 비용을 확인한다.';
      w.switch='웨이브 크기·진행 방향, 양쪽 레벨·구매·체력·마나, 핵심 기술의 사용 여부와 동료 호응이 바뀌면 교환·정리·귀환 중 다시 고른다. 기술 하나 소모만으로 올인 승리를 단정하지 않는다.';
      if(duo&&patchOK){
        // Explicit contextual examples, gated by retained official effects.
        // Other supports retain the general plan rather than a guessed key.
        const examples={
          Alistar:['Q',/공중/,'공중에 띄우는 수단에 함께 공격할 거리가 필요하다. 접근할 수 없으면 진입을 기다리지 말고 미니언·체력을 지킬 자리를 바꾼다.'],
          Lux:['Q',/속박/,'속박이 맞고 후속 공격이 닿을 때 짧게 공격한다. 빗나가면 다시 묶을 수 있는 것처럼 앞으로 나가지 않는다.'],
          Lulu:['E',/보호막/,'보호막과 아군 공격이 겹치는 동안 짧은 교환을 비교한다. 보호막이 끝나거나 상대 진입을 끊을 수 없으면 추가 공격을 줄인다.']
        };
        const example=examples[support];
        if(example&&fact(support,example[0])&&example[1].test(fact(support,example[0]).text)){
          w.window+=' '+skill(support,example[0])+'를 배워 쓸 수 있을 때 '+example[2];w.evidence_ids.push(fact(support,example[0]).id);
        }
        const counters={
          Nautilus:['Q',/당겨|끌려/,'의 접근이 남아 있으면 전진 뒤의 퇴로를 먼저 남긴다. 빗나가도 다른 제어와 동료 후속이 남아 있는지 확인한다.'],
          Lulu:['W',/기본 공격.*스킬/,'로 기본 공격·스킬이 막힐 수 있어 보호받는 상대를 끝까지 쫓지 않는다. 이 기술이 소모돼도 다른 보호와 반격을 다시 확인한다.'],
          Lux:['Q',/속박/,'에 함께 묶이지 않게 간격을 벌린다. 빗나갔을 때만 후속 공격 거리와 남은 보호막을 확인해 짧은 교환을 비교한다.']
        };
        const counter=counters[enemySupport];
        if(counter&&fact(enemySupport,counter[0])&&counter[1].test(fact(enemySupport,counter[0]).text)){
          w.window+=' '+skill(enemySupport,counter[0])+counter[2];w.evidence_ids.push(fact(enemySupport,counter[0]).id);
        }
        if(opponent==='Ziggs'&&fact(opponent,'W')&&/밀려|밀어/.test(fact(opponent,'W').text)){
          w.window+=' '+skill(opponent,'W')+'의 밀쳐내기는 접근을 끊을 수 있으므로 소모 여부와 남은 퇴로를 확인한다. 소모됐어도 '+enemySupportName+'의 반격과 적 미니언을 무시하지 않는다.';w.evidence_ids.push(fact(opponent,'W').id);
        }
      }
    }
    if(mode==='SOURCE_REVIEW_REQUIRED')w.window='패치가 미확인 또는 자료와 달라 상세 교환 조건을 확정하지 않는다. 양쪽 기술·레벨·자원·웨이브를 확인하고 포지션 기본 계획으로 제한한다.';
    else if(mode==='LIMIT_LOSS')w.window='자원이나 아군 호응이 부족하면 교환·진입을 강제하지 않는다. '+(pos==='JUNGLE'?'회복·구매를 먼저 비교하고 다음 캠프와 개입에 쓸 자원을 남긴다.':pos==='SUPPORT'?'아군 보호와 견제 대응에 쓸 자원을 남긴다.':'다음 반격이나 미니언 정리에 쓸 자원을 남긴다.');
    else if(mode==='CHECK_CONDITIONS')w.window='자원·웨이브가 미확인이면 공격 기회가 있다고 확정하지 않는다. 보이는 정보와 동료 호응부터 확인한다.';
    if(planning.ally_followup==='UNAVAILABLE'||['LIMIT_LOSS','CHECK_CONDITIONS'].includes(mode)&&pos==='JUNGLE'){
      const action=b.action_summaries.lane.items[2];
      action.text=pos==='JUNGLE'?(mode==='CHECK_CONDITIONS'?'자원·웨이브·동료 호응이 미확인이면 개입을 강제하지 않고 실행 조건부터 확인한다.':w.window):b.wave.combat;
      action.source_paths=['waiting.window','wave.combat'];b.wave.combat=action.text;
      if(b.wave.steps[1])b.wave.steps[1].text=action.text;
      b.area_context.lane.action=action.text;
      for(const response of b.condition_responses.lane)if(response.id!=='LANE_PLAN_CHANGE'){response.action=action.text;response.stop=w.switch;response.source_paths=['waiting.window','waiting.switch'];}
    }
    b.waiting=w;
    b.action_summaries.lane.items.forEach(item=>item.rule_ids.push(w.rule_id));

    // Keep exactly five actions and role-appropriate alternatives even outside
    // the individually authored matchup corpus.
    if(pos==='SUPPORT'){
      const values=['아군의 CS·경험치 접근을 보호하며 견제받는 자리를 줄인다.','아군의 귀환·성장 목적을 확인해 미니언 정리를 돕고, 유지하려는 웨이브를 임의로 밀지 않는다.',mode==='CONDITIONAL_WINDOW'?'아군이 함께 공격할 거리에서 배운 견제·제어를 쓰고, 호응이 끊기면 끝낸다.':'자원·호응이 없거나 미확인이면 진입을 강제하지 않고 아군의 접근을 보호한다.','상대 바텀 두 명의 진입·후속 공격을 따로 보고 아군을 혼자 두지 않는다.','아군 귀환·웨이브와 상대 진입 위험이 바뀌면 보호·시야·로밍 중 다시 고른다.'];
      b.action_summaries.lane.items.forEach((item,i)=>Object.assign(item,{text:values[i],basis:'ROLE_PRINCIPLE',source_paths:['waiting','action_summaries.lane']}));
    }else if(pos==='JUNGLE'&&!b.role_principles?.lane){
      const values=['캠프 성장과 라인 손실을 비교해 개입할 시간을 정한다.','먼저 움직일 아군과 연결되는 캠프를 택하고, 상대 동선을 단정하지 않는다.',mode==='CONDITIONAL_WINDOW'?'배운 기술과 아군 호응·자원이 맞을 때 개입하고, 각이 없으면 오래 기다리지 않는다.':'자원·호응이 부족하거나 미확인이면 무리한 갱킹을 강제하지 않는다.','라인 지원 없이 침입하거나 적을 끝까지 추격하지 않는다.','목격·웨이브·목표물 준비가 바뀌면 방어·역갱·반대편 교환을 비교한다.'];
      b.action_summaries.lane.items.forEach((item,i)=>Object.assign(item,{text:values[i],basis:'ROLE_PRINCIPLE',source_paths:['waiting','action_summaries.lane']}));
    }
  }

  // A small causal plan over retained facts. Decisions are made here; views only
  // project their paragraphs. This is authored interpretation, never observation.
  function composeNarrative(b,report,catalog,coach){
    const x=report.input,pos=x.own_position,w=b.waiting;
    if(!b.team_plan||!w||w.mode==='SOURCE_REVIEW_REQUIRED')return;
    const at=(side,role)=>x[side].find(p=>p.position===role)?.champion;
    const name=id=>catalog.champions[id]?.name||'확인할 아군';
    const fact=(id,key)=>catalog.champions[id]?.facts?.find(f=>f.slot===key);
    const refs=new Set(),used=new Set(),phaseRefs={lane:new Set(),operations:new Set(),fight:new Set()};let phase='lane';
    const skill=(id,key)=>{const f=fact(id,key);if(!f)return null;refs.add(f.id);phaseRefs[phase].add(f.id);used.add(id);return name(id)+'의 '+f.name+'('+key+')';};
    const has=(side,id,keys)=>x[side].some(p=>p.champion===id)&&keys.every(k=>fact(id,k));
    // Keep authored Fiora/Graves and other role plans; waiting is a decision in
    // details, not four independent paragraphs appended to their explanation.
    if(pos!=='BOTTOM'){
      if(b.coaching_explanation?.lane){
        b.coaching_explanation.lane.push(pos==='JUNGLE'?
          '개입을 기다리는 동안 놓칠 캠프와, 떠났을 때 아군이 잃을 미니언·포탑을 함께 본다. '+(w.mode==='CONDITIONAL_WINDOW'?'아군과 공격할 수 없는 길이라면 다음 캠프로 움직이되, 다이브 위험이 큰 라인은 도착할 시간을 비교해 방어한다.':w.window):
          pos==='SUPPORT'?'상대에게 자리를 모두 내주면 원딜이 막타뿐 아니라 경험치에도 접근하기 어려워진다. 함께 공격할 여건이 없다면 아군 곁에서 견제를 막고 미니언 정리와 귀환을 도와 다음 교환에 쓸 체력을 남긴다.':
          '막타를 기다리는 동안에도 상대 견제로 체력을 잃거나 경험치 범위에서 밀려날 수 있다. 반격에 필요한 자원이 없다면 받을 미니언과 포기할 막타를 정하고 귀환이나 정글 지원으로 다음 웨이브의 접근 여건을 바꾼다.');
      }return;
    }
    const support=at('allies','SUPPORT'),enemy=at('enemies','BOTTOM'),es=at('enemies','SUPPORT'),self=x.own_champion;
    if(x.opponent_mode!=='ASSIGNED'&&!(x.opponent_mode==='MANUAL'&&x.lane_opponent===enemy)){
      b.coaching_explanation.lane=[b.matchup_playbook.ours.means,w.loss+' '+w.fallback];
      b.coaching_scope.limitation='수동 맞상대 또는 미지정 상태에는 바텀 2대2 상세 코칭을 적용하지 않습니다. 기존 지정 상대의 기본 계획만 제공합니다.';return;
    }
    const previousLane=b.coaching_explanation.lane.slice();
    // Scope is explicit: a supported interaction, not every champion matchup.
    const supportKinds={Nautilus:['Q','P'],Lux:['Q','W'],Lulu:['E','W'],Alistar:['Q','W']};
    if(!supportKinds[support]?.every(k=>fact(support,k))){
      b.coaching_explanation={lane:['이 바텀 두 명의 구체적인 교환 순서는 아직 연결되지 않았다. '+w.loss+' '+w.fallback],operations:[b.operations.placement+' '+b.operations.fallback],fight:[b.fight.setup+' '+b.fight.stop]};
      b.coaching_scope.limitation='포지션 기본 계획만 제공하며 이 조합의 개별 코칭은 미지원입니다.';return;
    }
    [self,support,enemy,es].filter(Boolean).forEach(id=>used.add(id));
    const sn=name(support),en=name(enemy),esn=name(es),s=coach.context.assumptions.scenario.overrides,p=b.context.planning.overrides;
    const constrained=p.enemy_jungle==='NEAR'||['FARM','RECALL'].includes(p.goal)||(s.engage&&s.engage!=='NONE')||['INCOMING','UNDER_TOWER','RETURNING','UNKNOWN'].includes(s.wave);
    const limited=w.mode!=='CONDITIONAL_WINDOW'||constrained,sourceLimited=b.coverage.status==='UNSUPPORTED';
    let response,shortResponse,reset;
    if(support==='Nautilus'){
      response=sn+'가 앞으로 움직일 때 그 뒤에서 같은 적에게 기본 공격이 닿을 거리를 맞춘다. '+skill(support,'Q')+'으로 당겨도 혼자만 접근하면 교환을 이어갈 수 없으므로, 적 미니언을 지나며 받을 공격까지 보고 함께 전진한다.';
      shortResponse='노틸러스와 같은 적을 공격할 거리에서 호응하고, 혼자 들어간 노틸러스를 뒤늦게 따라가지 않는다.';
      reset='닻이 빗나가거나 노틸러스와 공격 거리가 벌어지면 추격 대신 미니언 쪽으로 돌아온다.';
    }else if(support==='Lux'){
      response=skill(support,'Q')+'의 속박이 맞은 적에게 럭스와 함께 공격할 거리를 잡는다. 먼저 적진으로 들어가 속박을 기다리기보다, 럭스의 견제에 상대가 피하는 방향을 보고 닿는 적에게 짧게 공격한다.';
      shortResponse='럭스의 속박 적중과 후속 공격 거리를 확인하고 짧게 공격한다.';reset='속박이 빗나가면 앞으로 더 쫓지 않고 '+skill(support,'W')+'의 보호를 받을 쪽으로 돌아온다.';
    }else if(support==='Lulu'){
      response=skill(support,'E')+'의 보호막과 함께 공격할 시간을 맞추고 룰루 곁에서 짧게 교환한다. 상대가 들어오면 '+skill(support,'W')+'를 적에게 쓸 수 있는지도 확인해야 하므로, 룰루가 먼저 적진을 뚫어 줄 것처럼 앞서가지 않는다.';
      shortResponse='룰루의 보호막과 함께 짧게 교환하고 변이로 막을 수 없는 깊이까지 쫓지 않는다.';reset='보호막이 끝나거나 룰루의 방해 수단이 없으면 함께 뒤로 물러나 다음 교환을 준비한다.';
    }else{
      response=skill(support,'W')+'와 '+skill(support,'Q')+'를 배워 함께 쓸 수 있는 구간에 알리스타의 접근과 내 공격 거리를 맞춘다. 아직 필요한 기술을 배우지 않았거나 거리가 멀다면 진입 연계를 기대하며 먼저 체력을 쓰지 않는다.';
      shortResponse='알리스타가 배운 진입 기술과 내 공격이 함께 닿을 때 호응한다.';reset='알리스타의 진입이 끝나도 공격 거리가 이어지지 않으면 더 깊이 따라가지 않는다.';
    }
    const pressure=has('enemies','Ziggs',['Q','W'])&&enemy==='Ziggs'?
      skill('Ziggs','Q')+'으로 미니언을 잡으려는 자리를 견제하면서 웨이브를 밀어 넣을 수 있다.'+
      (es==='Karma'&&has('enemies','Karma',['Q','E','W'])?' 여기에 '+skill('Karma','Q')+'의 폭발까지 겹치면, 막타를 치러 갈 때 두 사람의 공격을 한꺼번에 받을 수 있다.':' '+esn+'가 함께 공격할 수 있는 자리에서는 직스만 보고 앞으로 걷지 않는다.'):
      en+'에게 막타를 치는 순간 공격받지 않도록 '+esn+'의 호응 거리까지 함께 본다. 이 두 챔피언의 밀기·교환 우열을 확정할 자료는 없으므로, 먼저 미니언을 잡을 수 있는지는 실제 웨이브로 확인한다.';
    const counter=[];
    if(enemy==='Ziggs'&&has('enemies','Ziggs',['W','E']))counter.push(skill('Ziggs','W')+'의 밀쳐내기와 '+skill('Ziggs','E')+'의 둔화는 접근과 퇴로를 끊을 수 있다');
    if(es==='Karma'&&has('enemies','Karma',['E','W']))counter.push(skill('Karma','E')+'의 보호막·이동 속도 때문에 상대가 거리를 벌릴 수 있고, '+skill('Karma','W')+'의 연결을 끊지 못하면 속박될 수 있다');
    else if(es==='Lulu'&&has('enemies','Lulu',['W']))counter.push(skill('Lulu','W')+'가 남아 있으면 공격과 기술이 막힐 수 있다');
    else if(es==='Nautilus'&&has('enemies','Nautilus',['Q']))counter.push(skill('Nautilus','Q')+'의 역진입이 남아 있으면 퇴로를 막힐 수 있다');
    else counter.push(esn+'의 남은 보호·반격 수단은 실제 사용 여부를 확인해야 한다');
    response='관련 기술을 배워 사용할 수 있는 구간에는 '+response;
    const lane={title:'함께 공격할 거리를 만들어, 막타를 칠 자리를 되찾기',pressure,
      cost:'계속 뒤로만 물러서면 CS와 경험치에 접근할 공간을 잃고, 포탑 아래에서도 견제를 받아 다음 웨이브를 버틸 체력이 줄 수 있다. 그렇다고 큰 적 웨이브 속으로 들어가면 미니언 공격과 상대 반격 때문에 다음 막타까지 더 많이 놓친다.',
      response:constrained?b.wave.combat+' '+(p.goal==='RECALL'?'귀환을 선택했다면 교환을 늘려 구매 시간을 늦추지 않는다.':p.goal==='FARM'?'성장을 우선한 만큼 미니언과 경험치를 놓칠 추격은 줄인다.':'상대 개입·웨이브·선진입 가정을 먼저 처리해야 다음 교환을 준비할 수 있다.'):limited?'지금 설정한 가정에서는 '+(w.mode==='CHECK_CONDITIONS'?'체력·웨이브가 미확인이므로 호응 가능 여부부터 확인한다.':'자원이나 아군 호응이 부족하므로 먼저 교전 여건을 바꾼다.')+' '+w.fallback:response,
      payoff:'상대를 물러나게 하거나 방어 기술을 쓰게 했다면 킬을 끝까지 쫓기보다 CS에 접근할 자리와 웨이브를 정리할 시간을 얻는다. 밀어 넣을 수 있으면 귀환 시간을 만들고, 체력이 부족하면 다음 웨이브까지 버티려 하지 말고 귀환과 지원을 비교한다.',
      fallback:reset+' 레벨·체력·마나가 부족하거나 아군 호응이 없으면 경험치를 받을 자리를 지키며 정리 지원과 귀환을 요청한다. 아군이 합류하거나 상대 견제 수단이 빠져 같은 적을 함께 공격할 수 있게 되면 다시 전진할 폭을 넓힌다.',
      counter:counter.join('. ')+'. 하나가 소모됐다는 이유만으로 남은 수단과 미니언을 무시하지 않는다.'};
    if(self==='Kaisa'&&fact(self,'P'))lane.response+=(limited?' 다음 기회에는 ':' ')+skill(self,'P')+'는 아군의 이동 불가로도 플라즈마가 쌓이므로, 동료가 묶은 적에게 내 공격까지 이어지는 것이 중요하다.';
    phase='operations';
    const openingSkills={Ornn:['R',/공중/],Vi:['R',/공중/],Nautilus:['Q',/당겨/],Sejuani:['R',/기절/],Ahri:['E',/홀립|홀린/],Lux:['Q',/속박/],Alistar:['Q',/공중/]};
    const initiators=x.allies.map(p=>p.champion).filter(id=>openingSkills[id]&&fact(id,openingSkills[id][0])&&openingSkills[id][1].test(fact(id,openingSkills[id][0]).text));
    const starters=initiators.length?initiators.map(name).join('·'):sn;
    const nearby=['Vi',support].filter((id,i,a)=>a.indexOf(id)===i&&x.allies.some(p=>p.champion===id));
    const partners=nearby.map(name).join('·');
    const join=has('allies','Ahri',['E'])?'아리가 미니언을 정리해 합류할 수 있다면 '+skill('Ahri','E')+'에 맞춰 같은 적을 공격할 길도 생긴다. 아리가 사이드에 묶여 있으면 아리의 공격까지 합쳐 교전을 시작하지 않는다.':'다른 라인 아군이 웨이브를 놓치지 않고 합류할 수 있는지 먼저 확인한다.';
    const op={title:enemy==='Ziggs'?'직스 앞의 긴 대치를 끊고, 아군과 함께 접근하기':'웨이브를 정리한 시간을 아군과의 공격 기회로 바꾸기',
      pressure:enemy==='Ziggs'?'직스 앞에서 같은 자리에 오래 대치하면 견제를 피하며 미니언을 잡는 데 체력과 시간이 소모된다. 체력이 깎인 뒤에야 진입하면 접근 도중 반격까지 버티기 어려워진다.':en+'와 정면에서 대치하는 동안 사이드 미니언과 먼저 이동할 시간을 놓칠 수 있다. 대치 자체가 이득인지는 아군이 다른 곳에서 얻는 것까지 함께 본다.',
      cost:'이동만 서두르다 웨이브를 버리면 성장도 잃고, 아군보다 먼저 어두운 길에 들어가면 함께 싸울 수도 없다.',
      response:partners+'와 중앙 미니언을 정리한 뒤, 아군이 확인한 시야 안에서 같은 적에게 닿을 경로를 잡는다. '+(has('allies','Vi',['R'])?skill('Vi','R')+'이 적을 띄워도 내 공격이 닿지 않으면 바이만 적진에 남으므로, 진입 전에 따라갈 거리부터 맞춘다.':'제어가 맞아도 내 공격이 닿지 않으면 묶은 시간을 이득으로 쓰기 어렵다.')+' '+join,
      payoff:'상대가 물러난 시간에는 가까운 포탑을 치거나 목표물 주변 시야를 확보한다. 다른 곳의 미니언을 받을 아군과 합류 시간을 정해, 한쪽이 귀환하는데 나머지만 교전을 시작하지 않게 한다.',
      fallback:'함께 들어갈 경로가 없으면 같은 입구에서 견제를 계속 맞지 말고 가까운 웨이브를 받은 뒤 구매·회복을 맞춘다. '+sn+'와 다른 입구의 시야를 확보하되 혼자 어두운 강을 건너지 않는다. 이미 아군 진입이 끝나 상대가 물러났다면 뒤늦게 쫓지 말고 다음 웨이브와 목표물 준비로 돌아간다.'};
    phase='fight';
    initiators.forEach(id=>skill(id,openingSkills[id][0]));
    let danger=[];
    if(has('enemies','Renekton',['E','W']))danger.push(skill('Renekton','E')+'를 이용한 접근 뒤 '+skill('Renekton','W')+'로 묶일 수 있으므로, 레넥톤이 들어올 측면과 뒤로 물러날 길을 함께 본다.');
    if(has('enemies','Orianna',['Q','E','R']))danger.push('오리아나의 공은 '+skill('Orianna','Q')+'에 따라 이동하거나 '+skill('Orianna','E')+'로 상대 팀원을 따라간다. '+skill('Orianna','R')+'에 함께 끌려가지 않도록 공 주변으로 아군과 겹쳐 들어가지 않는다.');
    if(!danger.length)danger=[b.fight.awareness?.danger||b.fight.stop];
    const fight={title:'진입한 아군과 같은 적을 공격하되, 고립되는 진입은 보류하기',pressure:danger.join(' '),
      cost:'먼 딜러에게 다가가는 동안 가까운 적에게 공격받거나 아군의 도움이 끊기면, 진입에 성공해도 지속해서 피해를 줄 시간이 사라진다.',
      response:starters+'가 적을 묶을 때 바로 공격을 이어갈 수 있도록 아군 뒤나 옆에서 출발한다. 탱커가 멀리 들어갔다는 사실만으로 안전해지는 것은 아니므로, 함께 닿는 가까운 적부터 공격하며 아군과 거리를 유지한다.',
      payoff:'첫 제어에 공격을 맞추고 상대가 물러나면 무리하게 따라붙기보다 다시 공격할 위치를 확보한다. 들어온 적을 함께 밀어내는 것도 뒤의 딜러를 쫓는 것만큼 유효한 선택이다.',
      fallback:self==='Kaisa'&&fact(self,'R')?skill(self,'R')+'을 이용한 후속 진입을 검토할 때는 도착할 자리에서 아군이 계속 도울 수 있는지 먼저 본다. 진입자만 멀리 있고 상대 반격이 남았다면 궁극기를 써 따라가지 않는다. 공격 기회를 이미 놓쳤으면 가까운 적과 퇴로 쪽으로 대상을 바꿔 다음 공격을 준비한다.':sn+'의 도움이 닿지 않는 깊이까지 따라가지 않는다. 아군 제어가 끝났거나 상대가 거리를 벌렸다면 가까운 적을 공격하며 다시 모인다.'};
    b.narrative_decisions={};
    for(const [area,d]of Object.entries({lane,operations:op,fight})){
      Object.assign(d,{rule_id:'causal-coaching-v1:'+area,actors:[...new Set([...x.allies,...x.enemies].filter(p=>Object.values(d).some(t=>typeof t==='string'&&t.includes(name(p.champion)))).map(p=>p.champion))],evidence_ids:[...phaseRefs[area]],observation:false,basis:'MECHANISM_LINKED_INFERENCE',outcome:'UNDETERMINED',review_state:'TACTICAL_UNREVIEWED'});b.narrative_decisions[area]=d;
    }
    if(!sourceLimited){
      lane.pressure=b.area_context.lane.theirs;lane.response=previousLane[0];lane.fallback=b.wave.change_if;
      lane.evidence_ids=[...new Set(b.action_summaries.lane.items.flatMap(i=>i.evidence_ids||[]))];
      lane.counter='지금 선택한 구간의 기술 습득과 웨이브 가정을 우선한다. 이후의 보호·진입 수단이 이미 준비됐다고 보고 교환을 늘리지 않는다.';
    }
    b.coaching_explanation={lane:[lane.pressure+' '+lane.cost,lane.response,lane.counter+' '+lane.payoff,lane.fallback],operations:[op.pressure+' '+op.cost,op.response,op.payoff+' '+op.fallback],fight:[fight.response+' '+fight.cost,fight.pressure,fight.fallback+' '+fight.payoff]};
    b.coaching_scope={...b.coaching_scope,rule_id:'causal-coaching-v1',evidence_ids:[...refs],limitation:'저장된 기술 기전에서 도출한 조건부 코칭입니다. 현재 상태·상성 우열·전술 정확도는 검증하지 않았습니다. 구간별 미지원은 그대로입니다.'};
    // Preserve reviewed matchup decisions. For role-only inputs, close the old
    // summary/detail gap using this very same causal decision, not another plan.
    if(sourceLimited){
      b.lane.concept={plan_id:b.wave.plan_id,text:lane.title};
      const laneActions=['상대에게 막타 자리를 모두 내주지 않되, 교환 뒤에도 다음 웨이브를 받을 체력을 남긴다.','큰 적 웨이브에는 깊게 들어가지 말고, 동료와 함께 줄인 뒤 막타에 접근한다.',limited?lane.response.split('. ')[0]+'.':shortResponse,'상대 두 명의 남은 반격과 퇴로를 보고, 한 기술이 빠졌다고 끝까지 추격하지 않는다.',reset];
      if(constrained){laneActions[1]=b.wave.handling;laneActions[2]=b.wave.combat;laneActions[4]=b.wave.change_if;}
      laneActions.forEach((text,i)=>b.action_summaries.lane.items[i].text=text);
      b.wave.combat=laneActions[2];b.wave.change_if=laneActions[4];b.wave.handling=laneActions[1];b.wave.steps=b.wave.steps.map((step,i)=>({...step,text:laneActions[[1,2,4][i]??4]}));
      if(b.wave.diagram?.steps)b.wave.diagram.steps=b.wave.steps.map(step=>({...step}));
      b.matchup_playbook.ours.means=lane.response;b.matchup_playbook.ours.avoid=lane.counter;
      b.area_context.lane={...b.area_context.lane,ours:lane.response,theirs:lane.pressure,action:laneActions[2],matchup:lane.cost};
      Object.assign(b.operations,{concept:op.title,placement:'중앙에서 '+partners+'와 움직이며 같은 적에게 닿을 거리를 맞춘다.',connection:(has('allies','Vi',['R'])?'바이의 진입에 닿을 경로를 잡고, ':'')+sn+'의 '+(['Nautilus','Alistar'].includes(support)?'제어':'보호·방해')+'가 닿는 거리를 유지한다.',priority:'웨이브를 정리한 시간을 가까운 포탑·목표물 주변 시야로 바꾼다.',concede:op.cost,fallback:op.fallback});
      Object.assign(b.fight,{concept:fight.title,setup:starters+'의 뒤나 옆에서 시작해 같은 적을 공격할 거리를 유지한다.',start:'아군 제어와 내 공격이 함께 닿을 때 공격하고, 멀어진 진입자를 혼자 따라가지 않는다.',target:'함께 닿는 가까운 적부터 공격하며 아군을 지킬 거리를 남긴다.',stop:fight.fallback});
      b.operations.steps=[b.operations.placement,b.operations.priority,b.operations.fallback];
      for(const [area,values]of Object.entries({operations:[b.operations.placement,b.operations.connection,b.operations.priority,b.operations.concede,b.operations.fallback],fight:[b.fight.setup,b.fight.start,b.fight.target,fight.pressure,b.fight.stop]})){
        values.forEach((text,i)=>b.action_summaries[area].items[i].text=text.split('. ')[0]+(text.includes('. ')?'.':''));
        b.area_context[area].action=area==='operations'?b.operations.priority:b.fight.start;
      }
      for(const area of ['lane','operations','fight']){
        const d=b.narrative_decisions[area],summary=b.loading_summary.items.find(i=>i.id===area);summary.conclusion=d.title;summary.support=d.payoff;
        b.condition_responses[area]=[{id:area==='lane'&&limited?'PREPARE_WINDOW':'PLAN_WINDOW',trigger:area==='lane'&&limited?'싸울 필요가 있어도 자원·호응 여건이 부족하거나 미확인이라면':'아군과 공격할 거리·자원·경로가 모두 맞는다면',action:area==='lane'?(limited?lane.response:shortResponse):d.response,keep:d.payoff,reason:d.cost,stop:d.fallback,actors:d.actors,evidence_ids:d.evidence_ids,observation:false,basis:d.basis,rule_ids:[d.rule_id]},
          {id:'WINDOW_MISSED',trigger:'아군 공격이 끝났거나 후속 거리가 끊겼다면',action:d.fallback,keep:'뒤늦은 진입으로 다음 웨이브와 체력까지 잃지 않는다.',stop:'아군과 다시 모여 자원·거리·남은 수단을 확인할 때 다시 기회를 찾는다.',actors:d.actors,evidence_ids:d.evidence_ids,observation:false,basis:d.basis,rule_ids:[d.rule_id]},
          {id:'WAIT_FOR_HELP',trigger:'웨이브를 받을 수 있고 합류·구매가 곧 준비된다면',action:area==='lane'?'동료 곁에서 경험치와 닿는 막타를 받고 체력·기술을 남긴다.':'아군의 합류와 구매를 맞추며 다음 공격 위치를 준비한다.',keep:'기다리는 손실이 작고 실제로 좋아질 조건이 있을 때 시간을 쓴다.',stop:'견제나 포탑 손실이 커지면 같은 자리에서 기다리지 않고 지원·귀환·다른 경로를 선택한다.',actors:d.actors,evidence_ids:d.evidence_ids,observation:false,basis:d.basis,rule_ids:[d.rule_id]}];
      }
      for(const area of ['lane','operations','fight'])for(const c of b.condition_responses[area]){
        c.conditions=['게임 전 가정이며 실제 체력·기술 가용성·위치를 관측하지 않았습니다.'];
        c.limits=b.coaching_scope.limitation;c.source_paths=['narrative_decisions.'+area];
      }
    }
  }

  // Authored, conditional coaching over retained mechanisms. This does not change
  // matchup assessments, observations, knowledge adoption, or the wave decision.
  function enrichCoaching(b,report,catalog,coach){
    if(coach.context.patch.status==='MISMATCH'||!b.team_plan)return;
    const input=report.input,self=input.own_champion,pos=input.own_position;
    const name=id=>catalog.champions[id]?.name||id;
    const fact=(id,k)=>catalog.champions[id]?.facts?.find(f=>f.slot===k);
    const has=(team,id,keys=[])=>input[team].some(p=>p.champion===id)&&keys.every(k=>fact(id,k));
    const skill=(id,k)=>name(id)+'의 '+fact(id,k).name+'('+k+')';
    const at=(team,position)=>input[team].find(p=>p.position===position)?.champion;
    const sources=(id,keys)=>keys.filter(k=>fact(id,k)).map(k=>'official:'+id+':'+k);
    const join=ids=>ids.map(name).join('·');
    const side=input.allies.find(p=>p.champion==='Fiora'&&['TOP','MID'].includes(p.position)&&has('allies','Fiora',['Q','W']))?.champion;
    const initiators=team=>['Malphite','JarvanIV'].filter(id=>has(team,id,['R']));
    const enemyEntry=initiators('enemies'),entryNames=join(enemyEntry);
    const ownSupport=at('allies','SUPPORT'),enemyJungle=at('enemies','JUNGLE');
    const team=b.team_plan;
    for(const [key,roster] of [['ours','allies'],['theirs','enemies']]){
      const t=team[key],entry=initiators(roster),names=join(entry);
      if(entry.length>=2){
        t.win='강제 교전으로 상대 진형을 묶고, 뒤의 딜러가 같은 대상에게 공격을 집중한다.';
        t.field='좁은 입구나 여러 적이 모인 위치에서 진입을 연결한다. 아군 딜러가 따라올 수 없는 깊은 진입은 피한다.';
        t.opening=names+'의 진입을 연결해 교전을 열되, 두 진입을 한 번에 소비할지 나눌지 아군 공격 거리를 보고 정한다.';
        const follow=['Orianna','Jinx'].filter(id=>has(roster,id,[id==='Orianna'?'R':'P']));
        t.damage=(follow.length?join(follow)+'의 후속 공격을 진입한 아군과 연결한다. ':'뒤의 딜러가 안전하게 공격할 거리를 남긴다. ')+(has(roster,'Lulu',['E','R'])?'룰루가 실제로 보호할 수 있는 대상과 거리를 확인한다.':'보호가 닿기 전에 진입자만 고립되지 않게 한다.');
        t.avoid='진입과 후속 공격이 따로 들어가거나, 견제를 계속 맞은 뒤 건강한 상대에게 교전을 강제하지 않는다.';
        t.evidence_ids=[...new Set([...t.evidence_ids,...entry.flatMap(id=>sources(id,['R'])),...follow.flatMap(id=>sources(id,id==='Orianna'?['E','R']:['P'])),...(has(roster,'Lulu',['E','R'])?sources('Lulu',['E','R']):[])])];
      }
    }
    if(side){
      team.ours.win=team.ours.prepared?'피오라가 사이드 포탑을 위협하고, 중앙 아군은 웨이브 정리와 견제로 상대를 나눠 대응하게 만든다.':'피오라의 사이드 압박과 중앙의 움직임을 맞춰 상대 대응을 나눈다. 중앙이 버틸 수 없다면 먼저 모여 가까운 이득을 찾는다.';
      team.ours.macro='피오라의 사이드 압박과 중앙의 전진 시간을 맞춘다. 중앙이 물리기 쉽거나 합류할 수 없다면 사이드를 덜 밀고 먼저 모인다.';
      team.ours.avoid='중앙이 귀환하거나 물러나는 동안 피오라 혼자 깊게 전진하지 않는다. 네 명이 버틸 수 있다고 가정하지 않는다.';
    }
    team.rows.forEach(row=>{row.ours=team.ours[row.id];row.theirs=team.theirs[row.id];});
    team.phases.find(x=>x.id==='mid').text=team.ours.macro;
    if(enemyEntry.length>=2)team.phases.find(x=>x.id==='objective').text='미니언을 정리하고 먼저 시야를 확보해 견제할 시간을 만든다. '+entryNames+'의 진입이 가능한데 목표물을 치며 좁은 곳에 뭉치지 않는다. 상대 인원·체력·남은 기술을 확인한 뒤 시작한다.';
    b.composition.ours=team.ours.win;b.composition.theirs=team.theirs.win;
    b.composition.ours_full=team.ours.win+' '+team.ours.macro;b.composition.theirs_full=team.theirs.win+' '+team.theirs.macro;
    b.area_context.operations.ours=team.ours.macro;b.area_context.operations.theirs=team.theirs.macro;
    b.area_context.fight.ours=team.ours.damage;b.area_context.fight.theirs=team.theirs.opening;
    const graves=self==='Graves'&&pos==='JUNGLE'&&has('allies',self,['P','Q','W','E']);
    const fiora=self==='Fiora'&&['TOP','MID'].includes(pos)&&has('allies',self,['P','Q','W','R']);
    const explain={lane:[],operations:[],fight:[]};
    let laneValues=null,roleEvidence=[];
    const add=(area,id,trigger,action,reason,stop,actors,evidence)=>b.condition_responses[area].push({
      id,trigger,action,reason,keep:reason,stop,actors,evidence_ids:evidence,claim_ids:[],
      conditions:['게임 시작 전의 조건부 계획입니다. 실제 위치·체력·기술 사용 여부를 직접 확인한 뒤 적용하세요.'],
      phase:area==='lane'?coach.selected_period:'POST_LANE_LEARNED_KIT',basis:'DESIGN_HYPOTHESIS',observation:false,
      knowledge_state:'GENERAL_PRINCIPLE',provenance_scope:'MECHANISMS_NOT_TACTICAL_VALIDATION',
      rule_ids:['gameplan-coaching-content-v1',id],source_paths:['coaching_explanation.'+area]});
    if(graves){
      roleEvidence=sources(self,['P','Q','W','E']);
      b.operation_headline=side?'사이드 압박과 중앙 수비를 연결하며 성장하세요':'성장 동선과 아군 지원을 연결하세요';
      laneValues=['캠프 성장을 유지하면서 상대 정글의 개입이 큰 손해로 이어지지 않게 돕는다.',
        '아군이 먼저 움직일 수 있는 라인 쪽에서 캠프와 지원을 연결한다. 탑 챔피언만 보고 시작 동선을 고정하지 않는다.',
        '상대가 깊게 들어오거나 아군이 묶은 적에게 함께 닿을 때 개입한다. 잡을 각이 없으면 오래 기다리지 않는다.',
        '라인 지원이 없는데 상대 정글을 쫓아 들어가지 않는다. 장전과 퇴로를 확인하고 배운 '+skill(self,'E')+'를 전진에 모두 쓰지 않는다.',
        '도와줄 수 없는 반대편에서 상대 정글이 보이면 가까운 캠프·갱킹·목표물 중 안전한 이득으로 교환한다.'];
      Object.assign(b.operations,{
        concept:side?'사이드 압박과 중앙 수비를 연결하기':'성장 동선과 라인 지원을 연결하기',
        placement:side?'피오라가 미는 사이드와 중앙 사이에서 움직이며, 먼저 무너질 위험이 있는 쪽에 가까이 선다.':'아군이 먼저 움직일 수 있는 라인 쪽 캠프를 연결하고, 중앙이 물릴 위험이 크면 먼저 지원한다.',
        connection:side?'피오라에게 접근로 시야와 퇴로를 마련해 주고, 중앙 아군이 물리지 않도록 돌아올 거리를 남긴다.':'라인 아군이 미니언을 놓치지 않고 움직일 수 있을 때 함께 시야를 확보한다.',
        priority:side?'피오라에게 상대 인원이 이동하면 중앙 포탑·정글·목표물 중 확보할 수 있는 이득을 고른다.':'캠프 성장과 아군 지원을 포탑·시야·목표물 이득으로 연결한다.',
        concede:side?'피오라와 함께 너무 깊이 들어가 중앙 아군을 상대의 강제 교전에 노출하지 않는다.':'라인 아군이 포탑에 묶여 있으면 혼자 강 싸움이나 상대 정글 침입을 시작하지 않는다.',
        fallback:'중앙이 버티지 못하면 압박을 줄이고 먼저 중앙을 안정시킨다. 싸울 여건이 없으면 가까운 캠프와 구매로 다음 기회를 준비한다.'});
      Object.assign(b.fight,{
        concept:'진입을 피하고, 아군과 가까운 적부터 공격하기',role:'성장한 화력을 아군과 연결하고 후속 공격을 방해하는 정글러',
        setup:'아군 딜러의 옆이나 조금 앞에서 시작하되 한 번에 함께 묶이지 않게 간격을 둔다. 내가 모든 진입을 받아내는 탱커라고 생각하지 않는다.',
        start:'견제로 적이 약해지거나 상대 진입 뒤 안전한 공격 틈이 생기면 전진한다. '+skill(self,'E')+'는 첫 전진보다 회피·재배치에 쓸 여유를 남긴다.',
        target:'아군을 물러 들어온 적이나 함께 닿는 대상부터 공격한다. 보호받는 적 원딜을 잡으러 혼자 적진을 가로지르지 않는다.',
        stop:'아군이 멀어지거나 측면 진입이 보이면 추격을 멈추고 아군 쪽으로 위치를 바꾼다.'});
      explain.lane=['개입은 도착 후 실제로 적에게 닿을 수 있는지부터 판단한다. 아군의 제어·체력·웨이브가 맞지 않으면 기다리는 시간만 늘어 성장도 늦어진다.',
        (enemyJungle?name(enemyJungle)+'의 반대편 등장이 보여도':'상대 정글이 반대편에 보여도')+' 목표물 확보가 자동으로 안전해지는 것은 아니다. 가까운 라인이 먼저 움직일 수 있는지와 처리할 체력·시간을 확인한다.'];
      explain.operations=[side?'피오라를 지원한다는 것은 옆에 계속 붙어 있는 것이 아니다. 접근로를 밝히고 퇴로를 마련한 뒤 중앙에서 이득을 만들어야 상대를 나눌 수 있다.':'아군이 먼저 움직일 수 있을 때 상대 정글과 강을 압박한다. 라인 지원이 없으면 내 캠프와 역갱 기회로 성장한다.',
        '아군이 귀환 중이거나 중앙에서 밀리고 있다면 깊은 침입을 줄인다. 중앙과 사이드가 동시에 압박할 때 상대가 대응하기 어려워진다.'];
      explain.fight=[skill(self,'W')+'는 접근 가능한 적 후속 딜러의 시야를 방해하는 데 쓴다. 연막을 맞히려고 혼자 깊이 들어가거나, 연막 하나로 궁극기 연계가 차단된다고 기대하지 않는다.',
        '첫 진입을 버틴 뒤 아군과 함께 공격할 틈을 찾는다. 장전 중에도 무리하게 적에게 붙어 있지 말고 퇴로와 다음 공격 위치를 확보한다.'];
      add('lane','JUNGLE_OPPOSITE','상대 정글이 도와주기 어려운 반대편에 보인다면',laneValues[4],
        '늦게 따라가 아무것도 얻지 못하는 대신 가까운 확실한 이득을 찾는다.','주변 라인 지원이나 체력이 부족하면 목표물을 강제하지 않고 캠프·귀환을 고른다.',enemyJungle?[enemyJungle]:[],roleEvidence);
      add('lane','NO_GANK_WINDOW','상대가 안전한 포탑 아래에 있고 아군 연계가 어렵다면','갱킹을 오래 기다리지 말고 캠프를 연결하거나 반대편 지원으로 전환한다.',
        '상대를 잡을 조건이 없는 대기는 성장 시간을 잃게 한다.','아군이 밀어 넣지 못하거나 다이브 위협이 있다면 떠나기 전 안전하게 웨이브를 넣도록 돕는다.',[self],roleEvidence);
      b.reminders=['상대 정글이 지금 개입하면 어느 라인이 가장 크게 손해를 보나?',side?'피오라에게 상대가 움직였을 때 나는 무엇을 얻을 수 있나?':'아군이 먼저 움직일 수 있는 라인은 어디인가?','지금 앞으로 가면 아군과 함께 싸우나, 나만 들어가나?'];
    }
    if(fiora){
      roleEvidence=sources(self,['P','Q','W','R']);
      b.operation_headline='사이드를 압박하되, 아군이 버틸 수 있는 시간에 맞추세요';
      Object.assign(b.operations,{
        concept:'사이드 압박 시간을 중앙과 맞추기',placement:'다음 목표물과 합류 수단에 맞춰 사이드를 고른다. 순간이동이 없다면 걸어서 합류할 수 있는 쪽에서 활동한다.',
        connection:(at('allies','JUNGLE')?name(at('allies','JUNGLE'))+'와 ':'아군과 ')+'접근로 시야를 확보하고, 중앙 아군이 전진할 때 함께 포탑을 위협한다.',
        priority:'상대 한 명을 사이드에 묶고 미니언·포탑 이득을 쌓는다. 추가 인원이 오면 포위되기 전에 물러나 중앙의 이득을 요청한다.',
        concede:'아군이 귀환하거나 중앙에서 물러나는 동안 혼자 적 포탑까지 깊게 들어가지 않는다.',
        fallback:'중앙이 버티지 못하거나 돌아갈 길이 없으면 더 깊이 밀지 않고 먼저 합류하거나 가까운 안전한 웨이브를 받는다.'});
      Object.assign(b.fight,{
        concept:'진입을 받아치거나, 고립된 적에게 접근하기',role:'사이드로 상대를 나누고 교전에서는 함께 닿는 적을 공격하는 역할',
        setup:'정면에서 모든 공격을 받지 말고 아군과 연결되는 옆쪽에 선다. 급소를 돌 공간과 퇴로가 없는 깊은 진입은 피한다.',
        start:'상대 주요 진입이 빠졌거나 아군이 묶은 대상에게 함께 닿을 때 접근한다. '+skill(self,'W')+'로 막을 기술을 미리 정한다.',
        target:'고립된 적 또는 아군에게 들어온 적 중 함께 공격할 대상을 고른다. 보호받는 적 원딜만을 끝까지 쫓지 않는다.',
        stop:'아군이 따라올 수 없거나 급소를 돌 공간이 없으면 더 깊게 들어가지 않고 아군 쪽으로 돌아온다.'});
      explain.lane=['접근하기 쉬운 급소를 치고 빠지는 교환부터 비교한다. 적 미니언이 많거나 급소가 뒤에 있으면 무리하게 돌아가지 않는다.',
        skill(self,'W')+'는 단독 교환과 정글 개입 상황에서 남길 가치가 다르다. 가까운 거리의 진입을 매번 반응해서 막는 것을 기본 계획으로 삼지 않는다.'];
      const counterpart=input.opponent_mode==='MANUAL'?input.lane_opponent:input.opponent_mode==='ASSIGNED'?at('enemies',pos):null;
      if(counterpart==='Malphite'&&has('enemies','Malphite',['P','E'])){
        explain.lane.push('말파이트는 보호막으로 교환을 흡수하고 '+skill('Malphite','E')+'로 공격 속도를 낮춘다. 탱커라는 이유만으로 계속 붙어 싸우지 말고, 급소·미니언·남은 기술을 함께 본다.');
        add('lane','MALPHITE_SLOW','배운 '+skill('Malphite','E')+'를 맞아 공격 속도가 감소했다면','공격 속도가 느린 동안 긴 맞딜을 강제하지 않고 거리를 회복한다.',
          '급소를 이용한 교환과 제자리에서 오래 때리는 교전은 다르다.','효과가 끝나고 급소·체력·웨이브가 유리하면 다시 접근을 비교한다.',['Malphite','Fiora'],[...roleEvidence,...sources('Malphite',['P','E'])]);
      }
      explain.operations=['사이드는 깊이보다 타이밍이 중요하다. 중앙 아군이 미니언을 밀거나 견제하는 순간에 포탑을 위협해야 상대의 대응을 나눌 수 있다.',
        '상대가 나를 두고 중앙으로 떠나면 바로 위험을 알린다. 포탑을 더 때릴지 합류할지는 얻을 포탑과 아군 손실, 이동 시간·순간이동을 비교해 정한다.'];
      explain.fight=[skill(self,'R')+'는 적 원딜에게만 쓰지 않는다. 아군과 함께 잡을 수 있는 진입자에게 사용해 회복 구역을 만들 기회도 본다.',
        '회복은 네 급소를 모두 치거나 급소를 하나 이상 친 대상이 죽어야 생긴다. 단순히 궁을 썼다고 아군이 보호받는 것은 아니다.'];
      add('operations','SIDE_DEFENDER_LEAVES','나를 막던 상대가 중앙으로 사라졌다면','즉시 위험 신호를 보내고 포탑 압박과 선이동·순간이동을 비교한다.',
        '상대가 사이드를 비웠다는 사실은 중앙에서 교전을 열 기회도 얻었다는 뜻이다.','합류가 늦고 아군이 이미 빠질 수 있다면 무리하게 따라가지 않고 확실한 포탑·웨이브 이득을 챙긴다.',[self],roleEvidence);
      b.reminders=['지금 사이드를 밀 때 중앙 아군은 버틸 수 있나?','나를 막던 상대가 중앙으로 이동했나?','내 압박이 포탑이나 상대 인원 분산으로 이어지고 있나?'];
      // Preserve the actual matchup/wave decision, including low-resource gates.
      if(coach.context.assumptions.scenario.overrides.resources==='LOW'){
        b.action_summaries.lane.items[0].text='체력·마나를 회복할 길을 남기고 안전한 미니언·경험치부터 챙긴다.';
        b.action_summaries.lane.items[2].text='급소가 보여도 무리한 교환을 줄이고, 받을 미니언과 퇴로를 지킨다.';
      }
    }
    if(graves||fiora){
      if(graves&&coach.context.assumptions.scenario.overrides.resources==='LOW'){
        laneValues[0]='체력·마나 회복과 구매를 우선해 다음 캠프와 지원을 이어갈 상태를 만든다.';
        laneValues[2]='체력·마나가 부족하면 무리한 갱킹보다 회복·구매를 먼저 하고, 아군에게 위험을 알린다.';
      }
      b.operations.steps=[b.operations.priority,b.operations.connection,b.operations.fallback];
      b.composition.role=name(self)+': '+b.fight.role+'.';
      const briefValues={our_plan:team.ours.win,enemy_plan:team.theirs.win,my_role:b.composition.role,key_change:b.operations.fallback};
      b.briefing_v2.items.forEach(item=>{item.text=briefValues[item.id].split('. ')[0].replace(/\.$/,'')+'.';});
      b.area_context.operations.action=b.operations.priority;b.area_context.fight.action=b.fight.start;
      if(laneValues){
        b.loading_summary.items.find(x=>x.id==='lane').title='초반 정글 목표와 개입 방식';
        b.lane.concept={plan_id:b.wave.plan_id,text:'성장 동선과 개입할 라인 연결하기'};
        b.area_context.lane.ours=laneValues[0];b.area_context.lane.action=laneValues[2];
        b.area_context.lane.theirs=enemyJungle?name(enemyJungle)+'의 실제 동선을 단정하지 않고, 아군이 깊이 전진하거나 체력이 낮을 때의 개입을 대비한다.':'상대 정글 배치를 확인한 뒤 개입 위협을 비교한다.';
        laneValues.forEach((text,i)=>Object.assign(b.action_summaries.lane.items[i],{text,evidence_ids:roleEvidence,basis:'ROLE_PRINCIPLE',knowledge_state:'GENERAL_PRINCIPLE',source_paths:['role_principles.lane']}));
        b.action_summaries.lane.items.forEach((x,i)=>x.label=['이번 정글 목표','기본 성장·지원 동선','개입·응징 방법','조심할 상황','계획을 바꿀 조건'][i]);
        b.role_principles={lane:laneValues,basis:'JUNGLE_SUPPORT_NOT_LANE_MATCHUP',evidence_ids:roleEvidence};
      }
      const danger=enemyEntry.length?entryNames+'의 진입에 함께 묶이지 않게 간격을 벌리고, 아군과 함께 닿는 진입자부터 공격한다.':'상대 진입에 혼자 고립되지 않게 아군과 거리를 맞춘다.';
      const values={operations:[b.operations.placement,b.operations.connection,b.operations.priority,b.operations.concede,b.operations.fallback],fight:[b.fight.setup,b.fight.start,b.fight.target,danger,b.fight.stop]};
      for(const area of ['operations','fight'])values[area].forEach((text,i)=>Object.assign(b.action_summaries[area].items[i],{text,evidence_ids:[...roleEvidence,...enemyEntry.flatMap(id=>sources(id,['R']))],basis:'ROLE_PRINCIPLE',knowledge_state:'GENERAL_PRINCIPLE',source_paths:[area]}));
      for(const area of ['lane','operations','fight']){
        const s=b.loading_summary.items.find(x=>x.id===area);
        const text=area==='lane'?(laneValues?.[0]||b.action_summaries.lane.items[0].text):area==='operations'?b.operations.priority:b.fight.start;
        if(s){s.conclusion=text.split('. ')[0].replace(/\.$/,'')+'.';s.support=area==='lane'?explain.lane[0]:area==='operations'?b.operations.fallback:b.fight.stop;}
        b.brief[area]=text;
      }
      for(const item of b.condition_responses.fight){
        if(item.id==='FOLLOWUP_WINDOW'){item.action=b.fight.start;item.keep=b.fight.target;item.stop=b.fight.stop;}
        if(item.id==='CONNECTION_LOST'){item.action=b.fight.stop;item.keep=b.fight.setup;}
      }
      if(side)add('operations','SIDE_DRAWS_TWO','피오라에게 상대 두 명 이상이 이동한다면',
        fiora?'포위되기 전에 물러나고 중앙에서 이득을 얻도록 신호를 보낸다.':'피오라에게 후퇴 신호를 주고 중앙 포탑·정글·목표물 중 안전한 이득을 고른다.',
        '사이드에 상대 인원이 묶인 시간을 다른 곳의 이득으로 바꾼다.','상대 위치가 다시 사라지거나 중앙 아군도 움직일 수 없다면 깊은 전진을 멈춘다.',['Fiora',...(graves?[self]:[])],sources('Fiora',['Q','W']));
      if(graves)add('fight','SMOKE_FOLLOWUP','적 후속 딜러가 안전하게 연막 사거리 안에 있다면',skill(self,'W')+'로 시야를 방해하고, 아군과 함께 접근한 적을 공격한다.',
        '진입자와 후속 딜러의 공격을 한 번에 받는 상황을 줄이기 위한 선택이다.','연막을 던지려다 혼자 적진으로 들어가야 한다면 가까운 적과 퇴로를 우선한다.',[self],sources(self,['W','E']));
    }
    // Other roles retain their actual selected plan; explanation is projected,
    // never copied from Fiora/Graves or used to invent a supported matchup.
    for(const area of ['lane','operations','fight'])if(!explain[area].length){
      explain[area]=area==='lane'?[b.matchup_playbook.ours.means,b.wave.change_if].filter(Boolean):area==='operations'?
        [b.operations.mode==='SIDE_RETURN'?'사이드에서 얻는 골드·경험치만큼 중앙에서 빠진 인원의 비용도 생긴다. 상대가 사이드에 대응한 시간을 아군이 다른 곳의 이득으로 바꿀 수 있어야 압박의 가치가 커진다.':'미니언을 먼저 잡아야 상대보다 먼저 움직일 시간을 얻는다. 그 시간을 포탑 공격이나 목표물 주변 시야 확보에 써야 단순한 이동을 이득으로 바꿀 수 있다.',
         '아군이 귀환하거나 인원이 부족한데 같은 압박을 유지하면 함께 싸울 수 없는 위치가 된다. 다음 웨이브·구매 뒤 다시 모일 시간과 지금 얻을 이득을 비교해 전진 폭을 정한다.']:
        [pos==='SUPPORT'?'진입과 보호에 같은 기술이 필요하면 먼저 쓴 쪽의 기회를 다른 쪽에서 잃는다. 적을 묶는 이득과 뒤의 아군을 도울 수단을 남기는 가치를 함께 비교한다.':'먼 대상에게 접근하는 동안 가까운 적에게 받는 공격과 아군 후속이 끊기는 비용도 생긴다. 아군과 함께 공격할 수 있는 대상을 먼저 고르면 고립되는 상황을 줄일 수 있다.',
         '공격할 수 있는 시간은 상대의 진입·반격 수단과 아군 보호가 닿는 거리에 따라 달라진다. 상대가 물러나면 끝까지 추격하기보다 다음 공격 위치와 돌아올 길을 먼저 확보한다.'];
    }
    b.coaching_explanation=explain;
    b.coaching_scope={basis:'MECHANISM_LINKED_INFERENCE',observation:false,rule_id:'gameplan-coaching-content-v1',evidence_ids:roleEvidence,
      limitation:'조합과 기술에서 도출한 조건부 계획입니다. 실제 경기 관측이나 승리 보장이 아니며, 개별 매치업 우열은 기존 자료 범위를 따릅니다.'};
  }
  return Object.freeze({ evaluate, validate, defaults, plainLanguage, actionSummaries });
});

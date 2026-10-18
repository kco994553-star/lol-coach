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
    clear_window: ['UNCONFIRMED', 'OPEN']
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
    const threatText=example?example.label+' · '+plainLanguage(example.action):b.fight.stop;
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
        make('fight','THREAT','대응할 위협',threatText,example?['fight.threats']:['fight.stop'],example?'fight-threats':'fight-plan',{threat_ids:example?[example.id]:[],conditions:example?[phaseLabel('fight'),example.condition]:[phaseLabel('fight')],selection_scope:example?'조합에서 실제 연결된 위협 수단 예시 · 전체 중요도 순위 아님':'연결된 위협 자료 없음 · 기존 이탈 원칙만 제공'}),
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
    const jungleNear = p.enemy_jungle === 'NEAR';
    const claims = id === 'A' ? ['A-WAVE', 'A-SHORT', 'A-RECALL', 'A-WAVE-SPACE',...(coach.knowledge_application?.supported?['A-INITIAL-ORDER-v1']:[])] : reverse ? ['B-ALI-RESOURCE','B-ALI-POLY'] : coach.evidence.claim_ids;
    const growth = coach.growth.find(g => g.id === period) || null;
    const reference=valid?coach.source_plan:null;
    const laneGoals = {
      E:reference?.overall_goal,
      BR: '체력을 보존해 CS·경험치를 받고, 알리스타 접근과 카이사 후속을 함께 쓸 여건을 남긴다.',
      A: early ? '사거리 견제로 막타 접근을 늦추고 웨이브·공간 선택권을 만든다.' : '받을 CS와 퇴로를 지키며 아군 제어 뒤 짧게 공격한다.',
      B: '유나라의 강화 공격과 룰루 지원이 겹치는 교환을 만들고 성장 자원을 남긴다.',
      C: '가까운 막타 자리를 압박하고, 상대 이탈을 쫓는 대신 CS·공간을 얻는다.',
      D: '장거리 견제로 수급을 잇되, 성장 후 고립된 맞딜을 허용하지 않는다.'
    };
    let overallGoal = usable ? laneGoals[id] : '확인된 수단으로 CS·경험치를 확보하고 복귀 선택권을 남긴다.';
    let milestoneGoal = reference?.selected?.purpose || (growth ? growth.after : id === 'C' ? coach.selected.action : overallGoal);
    if(reverse)milestoneGoal = period==='LEVEL1' ? '알리스타에게 아직 연속 진입 수단이 없는 구간: 체력·경험치와 닿는 CS를 지킨다.' : period==='LEVEL2' ? '알리스타가 박치기(W)·분쇄(Q)를 배웠다면 접근·후속 창이 생긴다. 체력을 써 선레벨 경쟁부터 강제하지 않는다.' : '룰루의 보호·변이와 유나라 강화 창을 피하고, 아군 후속이 닿는 교환만 비교한다.';
    if (low) milestoneGoal = '처리에 쓸 체력·마나를 남기며 받을 CS·경험치를 확보한다.';
    if (coach.context.patch.status === 'MISMATCH') overallGoal = milestoneGoal = '자료 버전이 달라 우세 적용을 제한하고 수급·복귀 계획부터 세운다.';
    const recallOpen = valid && !low && !unknown && p.goal === 'RECALL' && p.clear_window === 'OPEN' && !jungleNear && ['EVEN', 'BUILDING'].includes(s.wave);
    let planId = unknown ? 'CHECK_WAVE' : low ? 'TRIM_RECEIVE' : valid && coach.knowledge_application?.supported && id==='A' && s.engage==='NONE' && early && s.wave==='EVEN' && !['FARM','RECALL'].includes(p.goal) ? 'ACQUIRE_PUSH' : ({ INCOMING: 'TRIM_RECEIVE', UNDER_TOWER: 'TOWER_CS', RETURNING: 'RETURNING' })[s.wave] || (p.goal === 'FARM' || reference || reverse || id === 'A' && !early ? 'TRIM_RECEIVE' : 'SLOW_PUSH');
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
    let combat = coach.selection.id === 'SHORT_POKE' ? coach.selected.action : id === 'A' ? '상대가 막타에 접근하면 사거리 끝 짧은 공격으로 공간을 지키고, 물러나면 CS·처리 시간을 얻는다.' : coach.selected.action;
    if(planId==='ACQUIRE_PUSH')combat='미니언을 먼저 잡는 흐름을 유지하면서, 상대가 막타를 치러 나오면 사거리 끝에서 짧게 견제한다. 견제 때문에 미니언 잡기가 늦어지면 견제를 멈추고, 남긴 기술로 진입에 대응한다. '+coach.selected.action;
    if(reverse)combat = period==='LEVEL1' ? skill('Kaisa','Q')+'로 받을 수 있는 CS를 확보하고 동료와 연결한다. 아직 배우지 않은 알리스타의 연속 진입을 전제하지 않는다.' : '배운 '+skill('Alistar','W')+'·'+skill('Alistar','Q')+'에 '+skill('Kaisa','P')+' 후속이 닿을 때만 교환을 비교한다. 룰루의 보호·변이가 남으면 연장을 강제하지 않는다.';
    if (valid && id === 'A' && s.enemy_key === 'SPENT') combat = skill('Nautilus', 'Q') + ' 소모 뒤 막타 자리로 접근하거나 짧게 공격한다. ' + skill('Nautilus', 'P') + '와 카이사의 후속은 남아 있으므로 붙어서 추격하지 않는다.';
    if (absent) combat = name(slot('enemies', 'BOTTOM')) + '의 막타 접근과 웨이브만 제한적으로 압박한다. 서포터 부재를 추격·다이브 허가로 쓰지 않는다.';
    if (jungleNear) combat = '앞으로 나가는 교환 폭은 줄이고 막타·처리 선택권을 지킨다. 상대의 전진이 지원군과 연결됐을 가능성도 다시 본다.';
    if (low || p.goal === 'FARM') combat = '남는 자원으로 수급 공간을 지킨다. 상대가 물러나 주는 CS·처리 시간까지 포기하지 않는다.';
    if (recallOpen) combat = '추가 교환보다 귀환용 처리·이탈 자원을 남긴다. 상대가 처리를 막으면 밀어 넣기를 중단한다.';
    if(id==='A'&&s.engage!=='NONE'&&!low&&!unknown)combat='이미 교전을 시작한 가정에서는 선처리 경쟁보다 남은 동료 후속·제어·퇴로를 먼저 비교한다. 반격과 연결이 남으면 대응하고, 끊기면 교환을 끝낸 뒤 처리 계획을 다시 고른다.';
    if (unknown) combat = '막타·경험치 접근부터 확보한다. 모르는 상대 위치를 확인하러 깊게 나가지 않는다.';
    if (id === 'C' && !low && !unknown && !jungleNear && !recallOpen) combat = coach.selected.action;
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
      lane: { overall_goal: overallGoal, milestone: { id: period, label: coach.selected.label, goal: milestoneGoal }, can_push: coach.wave.can_push, should_push: coach.wave.should_push,
        strong_fight: id==='C'&&coach.selected.metrics.EXTENDED.assessment==='ALLY' ? '근접 지속 교전 우세 추론 · 접촉 유지 조건' : reverse ? '상대 강화·보호가 겹치지 않는 조건부 후속 창 · 전체 우열 미확인' : valid ? coach.trade.ours.label : '개별 매치업 자료 부족', avoid: id === 'A' ? '사거리 안쪽에 붙은 장기전·올인 승리는 별도 판단' : '처치·추격을 교환 선호와 동일시하지 않기',
        induce: absent ? '남은 상대가 막타에 접근할 때 제한적 압박' : '상대의 막타 접근·처리 기술 사용을 짧은 공간 이득으로 연결', gain: 'CS 접근·처리 시간·귀환 선택권', basis: usable ? id === 'A' && early ? 'GUIDE_BASED' : 'CONDITIONAL' : 'INSUFFICIENT', claim_ids: claims },
      overall: { lanes, jungle_links: jungleLinks, risk: [slot('enemies', 'JUNGLE'), slot('enemies', 'MID')].filter(Boolean).map(name).join('·') + '의 개입 가능성을 전진 비용에 포함한다. 실제 로밍·정글 동선은 미관측이다.', route_prediction: false },
      operations, fight: {...fight,formations:formation?.evaluate(input,{...catalog,coaching_knowledge:allKnowledge})}, wave, choice, growth, matchup_playbook: playbook, coverage,
      reminders: [valid && id === 'A' ? '측면 진입·럭스 후속 단절이면 교환 종료.' : changeIf, p.goal === 'RECALL' ? '빠른 처리와 실제 포탑 도달은 별개다.' : '교환에 다음 처리·대응 자원을 모두 쓰지 않는다.', growth ? '성장 후에도 남는 견제·연결 수단을 활용한다.' : '정글 미확인은 전진 폭을 조절할 이유이며 모든 처리·교전 금지가 아니다.'],
      quick_scenarios: quick,
      evidence: { claims: allClaims, sources: allKnowledge.sources.filter(s => sourceIds.has(s.id)), official_facts: threats.map(t => ({ ...fact(t.champion, t.slot), champion: t.champion })) }
    };
    result.action_summaries=actionSummaries(result,coach,report);return result;
  }
  return Object.freeze({ evaluate, validate, defaults, plainLanguage, actionSummaries });
});

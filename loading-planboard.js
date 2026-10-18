/* Pure decision projection. No observations, IO, strength scores or source promotions. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.LoadingPlanboard = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
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
  function evaluate(report, catalog, coach, supplied, knowledge) {
    const input = report.input, planning = validate(supplied || input.planning || defaults());
    const p = { enemy_support: 'PRESENT', enemy_jungle: 'UNKNOWN', ally_jungle: 'UNCONFIRMED', goal: 'AUTO', clear_window: 'UNCONFIRMED', ...planning.overrides };
    const s = { wave: 'EVEN', resources: 'SUFFICIENT', enemy_key: 'AVAILABLE', engage: 'NONE', start_skill: 'W', ...coach.context.assumptions.scenario.overrides };
    const id = coach.matchup_id, period = coach.selected_period, early = ['LEVEL1', 'LEVEL2', 'LEVEL3_5'].includes(period);
    const valid = coach.supported === true, low = s.resources === 'LOW', unknown = !valid || s.resources === 'UNKNOWN' || s.wave === 'UNKNOWN';
    const slot = (team, position) => input[team].find(r => r.position === position)?.champion || null;
    const name = c => catalog.champions[c]?.name || c || '배치 미확인';
    const fact = (c, k) => catalog.champions[c]?.facts.find(f => f.slot === k);
    const skill = (c, k) => fact(c, k) ? name(c) + '의 ' + fact(c, k).name + '(' + k + ')' : name(c) + '의 기술(키 미확인)';
    const self = input.own_champion, role = report.roles?.proposed?.id || report.roles?.base?.id;
    const sideRole = role === 'SIDE_RETURN', bottom = input.own_position === 'BOTTOM';
    const supportCase = valid && bottom && ['A', 'B'].includes(id) && !!slot('allies', 'SUPPORT') && !!slot('enemies', 'SUPPORT');
    const absent = supportCase && p.enemy_support === 'ABSENT';
    const jungleNear = p.enemy_jungle === 'NEAR';
    const claims = id === 'A' ? ['A-WAVE', 'A-SHORT', 'A-RECALL'] : coach.evidence.claim_ids;
    const growth = coach.growth.find(g => g.id === period) || null;
    const laneGoals = {
      A: early ? '사거리 견제로 막타 접근을 늦추고 웨이브·공간 선택권을 만든다.' : '받을 CS와 퇴로를 지키며 아군 제어 뒤 짧게 공격한다.',
      B: '유나라의 강화 공격과 룰루 지원이 겹치는 교환을 만들고 성장 자원을 남긴다.',
      C: '가까운 막타 자리를 압박하고, 상대 이탈을 쫓는 대신 CS·공간을 얻는다.',
      D: '장거리 견제로 수급을 잇되, 성장 후 고립된 맞딜을 허용하지 않는다.'
    };
    let overallGoal = valid ? laneGoals[id] : '확인된 수단으로 CS·경험치를 확보하고 복귀 선택권을 남긴다.';
    let milestoneGoal = growth ? growth.after : id === 'C' ? coach.selected.action : overallGoal;
    if (low) milestoneGoal = '처리에 쓸 체력·마나를 남기며 받을 CS·경험치를 확보한다.';
    if (coach.context.patch.status === 'MISMATCH') overallGoal = milestoneGoal = '자료 버전이 달라 우세 적용을 제한하고 수급·복귀 계획부터 세운다.';
    const recallOpen = valid && !low && !unknown && p.goal === 'RECALL' && p.clear_window === 'OPEN' && !jungleNear && ['EVEN', 'BUILDING'].includes(s.wave);
    let planId = unknown ? 'CHECK_WAVE' : low ? 'TRIM_RECEIVE' : ({ INCOMING: 'TRIM_RECEIVE', UNDER_TOWER: 'TOWER_CS', RETURNING: 'RETURNING' })[s.wave] || (p.goal === 'FARM' || id === 'A' && !early ? 'TRIM_RECEIVE' : 'SLOW_PUSH');
    if (recallOpen) planId = 'FAST_PUSH';
    const labels = { CHECK_WAVE: '수급 거리에서 처리 방향 파악', SLOW_PUSH: '막타 중심으로 천천히 쌓기', TRIM_RECEIVE: '필요한 만큼 줄이며 받기', TOWER_CS: '포탑 아래 수급', RETURNING: '돌아오는 웨이브 받기', FAST_PUSH: '빠른 처리 후 포탑 도달 확인' };
    const handling = {
      CHECK_WAVE: '닿는 막타·경험치를 받으며 양쪽 처리 방향을 파악한다. 미확인인 채로 유지·크래시 성공을 가정하지 않는다.',
      SLOW_PUSH: '막타를 우선하고, 상대가 줄이는 속도보다 조금 더 처리할 여유가 있을 때만 쌓는다.',
      TRIM_RECEIVE: '안전한 막타를 받고 과하게 쌓이는 상대 미니언만 일부 줄인다. 프리징이나 당겨지는 결과를 보장하지 않는다.',
      TOWER_CS: '포탑 공격과 내 공격으로 받을 수 있는 막타를 고른다. 받을 수 없는 CS를 위해 퇴로까지 포기하지 않는다.',
      RETURNING: '이전 크래시가 완료됐다는 예시에서 돌아오는 미니언을 아군 쪽에서 받는다. 상대가 유지하면 더 나가지 않는다.',
      FAST_PUSH: '귀환 전 남긴 처리 자원을 써 현재 웨이브를 줄인다. 다음 웨이브에 막히면 포탑 도달·귀환 창을 얻었다고 보지 않는다.'
    }[planId];
    const purpose = p.goal === 'RECALL' ? recallOpen ? '처리 여유를 귀환·구매 시간으로 바꾼다.' : '귀환 전 잃을 자원을 줄이고 밀어 넣을 여유를 마련한다.' : p.goal === 'FARM' || low ? '교환보다 CS·경험치와 다음 수급 자원을 확보한다.' : milestoneGoal;
    const reserve = coach.wave.selected.reserve[0];
    const pace = { id: planId === 'FAST_PUSH' ? 'FAST' : planId === 'SLOW_PUSH' ? 'LAST_HIT_PLUS' : planId === 'CHECK_WAVE' ? 'OBSERVE_FROM_ACCESS' : 'SELECTIVE_CLEAR', label: labels[planId] };
    const pressure = { id: jungleNear || low || unknown || p.goal === 'FARM' || p.goal === 'RECALL' ? 'LIMITED' : absent ? 'CS_SPACE' : 'CS_EDGE', label: jungleNear ? '줄이기 · CS 자리 밖 추격 금지' : absent ? '남은 원딜의 막타 접근 제한' : '닿는 막타 자리만 압박' };
    const exposure = { id: jungleNear ? 'HOME_CONNECTED' : 'ALLY_CONNECTED', label: jungleNear ? '아군 쪽 퇴로에 붙기' : '동료·미니언과 연결된 자리' };
    let combat = coach.selection.id === 'SHORT_POKE' ? coach.selected.action : id === 'A' ? '상대가 막타에 접근하면 사거리 끝 짧은 공격으로 공간을 지키고, 물러나면 CS·처리 시간을 얻는다.' : coach.selected.action;
    if (valid && id === 'A' && s.enemy_key === 'SPENT') combat = skill('Nautilus', 'Q') + ' 소모 뒤 막타 자리로 접근하거나 짧게 공격한다. ' + skill('Nautilus', 'P') + '와 카이사의 후속은 남아 있으므로 붙어서 추격하지 않는다.';
    if (absent) combat = name(slot('enemies', 'BOTTOM')) + '의 막타 접근과 웨이브만 제한적으로 압박한다. 서포터 부재를 추격·다이브 허가로 쓰지 않는다.';
    if (jungleNear) combat = '앞으로 나가는 교환 폭은 줄이고 막타·처리 선택권을 지킨다. 상대의 전진이 지원군과 연결됐을 가능성도 다시 본다.';
    if (low || p.goal === 'FARM') combat = '남는 자원으로 수급 공간을 지킨다. 상대가 물러나 주는 CS·처리 시간까지 포기하지 않는다.';
    if (recallOpen) combat = '추가 교환보다 귀환용 처리·이탈 자원을 남긴다. 상대가 처리를 막으면 밀어 넣기를 중단한다.';
    if (unknown) combat = '막타·경험치 접근부터 확보한다. 모르는 상대 위치를 확인하러 깊게 나가지 않는다.';
    if (id === 'C' && !low && !unknown && !jungleNear && !recallOpen) combat = coach.selected.action;
    const position = jungleNear ? '아군 쪽 퇴로와 후속이 닿는 자리에 서고, 웨이브를 따라 깊게 전진하지 않는다.' : '아군 후속과 걸어서 돌아올 거리가 남는 쪽에 선다. 미니언은 일부 투사체 대응 수단이며 전체 안전선이 아니다.';
    const nextWave = recallOpen ? '웨이브가 실제 상대 포탑에 닿은 뒤 귀환·구매를 비교한다. 도달하지 못하면 다음 웨이브에 더 노출될 부담을 먼저 줄인다.' : planId === 'TOWER_CS' ? '받은 뒤 체력·구매와 다음 웨이브 복귀를 비교한다. 다이브 인원·퇴로가 나쁘면 경험치·생존을 우선한다.' : planId === 'RETURNING' ? '돌아오는 웨이브가 멈추면 다시 처리량을 조절한다. 멀리 나가 상대 쪽에 묶이지 않는다.' : '상대 쪽에 웨이브가 멈추면 다음 수급에 더 나가야 한다. 자원·지원이 끊기면 추가 쌓기를 접고 일부 정리·귀환을 비교한다.';
    const changeIf = absent ? '상대 서포터 복귀·정글 개입·동료 후속 단절이면 압박을 접는다.' : jungleNear ? '상대 쪽에서 웨이브가 멈추거나 퇴로가 끊기면 추가 전진을 끝낸다.' : p.goal === 'RECALL' ? '처리를 방해받거나 포탑 도달 여유가 사라지면 귀환 계획을 바꾼다.' : coach.trade.ours.end[0];
    const choiceId = recallOpen ? 'PROCESS_FOR_RECALL' : p.goal === 'FARM' ? 'FARM_ACCESS' : coach.selection.id;
    const choice = { id: choiceId, same_across_preferences: recallOpen || low || unknown || p.goal === 'FARM' || coach.selection.same_across_preferences,
      cost: recallOpen ? '지금의 견제·킬 기회를 일부 포기하고 처리·구매 시간을 얻는다.' : coach.actions.find(a => a.id === coach.selection.id)?.costs[0] || '앞으로 선 자리와 처리 자원이 비용이다.',
      reserve, reason: recallOpen || p.goal === 'FARM' ? '현재 목적에서는 성향을 바꿔도 선택이 같습니다. 필요한 수급·처리 조건이 우선입니다.' : coach.selection.reason };
    const wave = { plan_id: planId, label: labels[planId], purpose, handling, position, combat, next_wave: nextWave, change_if: changeIf, completed: false,
      state: { position: s.wave, minion_size: 'UNOBSERVED', reinforcements: 'UNOBSERVED', origin: 'HYPOTHETICAL_LOADING_EXAMPLE' },
      conditions: { resources: s.resources, enemy_key: s.enemy_key, enemy_jungle: p.enemy_jungle, clear_window: p.clear_window },
      axes: { pace, pressure, exposure, resources: { id: recallOpen ? 'PROCESS_AND_EXIT' : 'RESERVE_RESPONSE', label: '처리·교환·대응 자원을 따로 남김', reserve } },
      steps: [{ number: 1, text: handling }, { number: 2, text: combat }, { number: 3, text: nextWave }], claim_ids: claims, basis: 'DESIGN_HYPOTHESIS' };
    wave.diagram = { ...clone(coach.diagram), plan_id: planId, steps: wave.steps, supported: coach.diagram.supported && !unknown };
    if (absent) wave.diagram.enemies = wave.diagram.enemies.filter(c => c !== slot('enemies', 'SUPPORT'));
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
      theirs = { purpose: '사거리 견제를 오래 받기보다 접근과 원딜 후속이 겹치는 교환을 만든다.', means: skill('Nautilus', 'Q') + '·' + skill('Nautilus', 'P') + '로 접근·제어하고, 배운 ' + skill('Kaisa', 'Q') + '와 ' + skill('Kaisa', 'P') + ' 후속을 잇는 후보.', look_for: '상대 처리 기술·이탈 소모 또는 두 동료가 벌어진 순간을 노린다. 실제 적중·후속 거리는 별도다.', avoid: '후속 없이 긴 견제를 받거나 웨이브·포탑 안쪽까지 깊게 추격하지 않는다.', switch_when: absent ? '서포터 부재 예시이므로 남은 원딜은 깊은 맞교환 대신 받을 CS·퇴로를 확보한다.' : '접근이 막히거나 원딜 후속이 끊기면 수급·재정비로 바꾼다.' };
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
    if (valid && id === 'A' && s.enemy_key === 'SPENT') { theirs.means = skill('Nautilus', 'P') + '와 카이사의 남은 후속은 있지만, 훅으로 여는 계획은 다시 사용 가능해질 때까지 미룬다.'; theirs.look_for = '상대가 스스로 평타 제어·카이사 후속 거리로 들어오는 경우만 비교한다. 훅 소모를 새 진입 수단으로 쓰지 않는다.'; }
    if (low || unknown || p.goal === 'FARM' || recallOpen) {
      ours.purpose = purpose; ours.means = combat;
      ours.look_for = low || unknown ? '닿는 막타·경험치와 걸어서 돌아올 공간을 얻는다.' : recallOpen ? '상대가 처리를 방해하지 않는 여유를 구매 시간으로 바꾼다.' : '상대가 양보한 CS·처리 시간을 얻는다.';
      ours.switch_when = changeIf;
    }
    if (absent) {
      ours.means = combat;
      theirs.means = name(slot('enemies', 'BOTTOM')) + '만 남은 부재 예시다. 지원 없는 진입 대신 닿는 막타와 퇴로를 확보한다.';
      theirs.look_for = '상대 처리·견제가 닿지 않는 수급 창을 이용한다.';
    }
    if (jungleNear) { ours.means = combat; ours.look_for = '전진 압박은 낮추되 가까운 CS·처리 선택권을 남긴다.'; }
    const playbook = { supported: valid, ours, theirs, claim_ids: claims, basis: 'DESIGN_HYPOTHESIS', enemy_intent: 'POSSIBLE_PLAN_NOT_OBSERVED' };
    const coverage = { status: !valid ? 'UNSUPPORTED' : id === 'A' ? 'BASIC_PLAN_CONDITIONAL' : 'CONDITIONAL_REFERENCE', matchup: id,
      plan_scope: valid ? '조건부 기본 목적·웨이브·양쪽 상대법 연결' : '일반 역할만 제공 · 개별 상대법 미지원',
      gaps: id === 'A' && valid ? '초반 사거리·푸시 공략 범위. 지속 교전·올인·후반 전체 우열 자료 부족.' : valid ? '기전·조건부 참고. 전체 2대2/근접 지속 교전 승패는 미확인.' : '이 조합의 구간별 공략 근거가 연결되지 않았다.', effect_sample: 0 };
    const quick = [];
    if(valid && id === 'A')quick.push({id:'KEY_SPENT',label:'노틸러스 핵심 기술 소모',scenario:{enemy_key:'SPENT'},planning:{},reason:'남은 평타 제어·카이사 후속은 유지하고 CS 접근·짧은 교환 창만 비교'});
    if(supportCase)quick.push({id:'SUPPORT_ABSENT',label:'상대 서포터 부재',scenario:{},planning:{enemy_support:'ABSENT'},reason:'남은 원딜·정글·복귀 위험을 고려한 제한적 압박'});
    const allClaims = knownMatches.flatMap(m => m.claims), sourceIds = new Set(allClaims.flatMap(c => c.source_ids));
    return {
      schema_version: 'lol-coach-player-planboard-v1', context: { origin: 'HYPOTHETICAL_LOADING_EXAMPLE', planning, actual_enemy_positions: null, standard: coach.context.assumptions.label, patch: coach.context.patch.label },
      brief: { lane: labels[planId] + ' · ' + (valid ? coach.trade.ours.label : '교전 자료 부족'), operations: sideRole ? '복귀할 수 있는 사이드 압박을 맡고 본대와 연결한다.' : bottom ? '중앙 수급을 아군과 잇고 제어 뒤 목표물로 전환한다.' : '가까운 자원과 본대 후속 거리를 연결한다.', fight: self === 'Caitlyn' ? '아군 제어가 맞으면 보호 연결 안에서 닿는 대상을 공격한다.' : self === 'Ezreal' ? '접근 전 견제하고 이탈 수단을 남긴 채 공격한다.' : self === 'Fiora' ? '사이드 복귀와 받아칠 수단을 정한 뒤 접근한다.' : self === 'Yunara' ? '강화·아군 지원이 함께 닿을 때 공격하고 후속이 끊기면 바꾼다.' : fight.start },
      headline: valid ? overallGoal : '확인된 수단으로 수급·연결부터 준비한다.',
      lane: { overall_goal: overallGoal, milestone: { id: period, label: coach.selected.label, goal: milestoneGoal }, can_push: coach.wave.can_push, should_push: coach.wave.should_push,
        strong_fight: valid ? coach.trade.ours.label : '개별 매치업 자료 부족', avoid: id === 'A' ? '사거리 안쪽에 붙은 장기전·올인 승리는 별도 판단' : '처치·추격을 교환 선호와 동일시하지 않기',
        induce: absent ? '남은 상대가 막타에 접근할 때 제한적 압박' : '상대의 막타 접근·처리 기술 사용을 짧은 공간 이득으로 연결', gain: 'CS 접근·처리 시간·귀환 선택권', basis: valid ? id === 'A' && early ? 'GUIDE_BASED' : 'CONDITIONAL' : 'INSUFFICIENT', claim_ids: claims },
      overall: { lanes, jungle_links: jungleLinks, risk: [slot('enemies', 'JUNGLE'), slot('enemies', 'MID')].filter(Boolean).map(name).join('·') + '의 개입 가능성을 전진 비용에 포함한다. 실제 로밍·정글 동선은 미관측이다.', route_prediction: false },
      operations, fight, wave, choice, growth, matchup_playbook: playbook, coverage,
      reminders: [valid && id === 'A' ? '측면 진입·럭스 후속 단절이면 교환 종료.' : changeIf, p.goal === 'RECALL' ? '빠른 처리와 실제 포탑 도달은 별개다.' : '교환에 다음 처리·대응 자원을 모두 쓰지 않는다.', growth ? '성장 후에도 남는 견제·연결 수단을 활용한다.' : '정글 미확인은 전진 폭을 조절할 이유이며 모든 처리·교전 금지가 아니다.'],
      quick_scenarios: quick,
      evidence: { claims: allClaims, sources: allKnowledge.sources.filter(s => sourceIds.has(s.id)), official_facts: threats.map(t => ({ ...fact(t.champion, t.slot), champion: t.champion })) }
    };
  }
  return Object.freeze({ evaluate, validate, defaults });
});

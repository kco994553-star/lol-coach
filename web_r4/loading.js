/* Shared pure analysis, manual picks, and an explicitly requested loopback import. */
(function () {
  'use strict';
  const roles = { TOP: '탑', JUNGLE: '정글', MID: '미드', BOTTOM: '바텀', SUPPORT: '서포터' };
  const $ = id => document.getElementById(id);
  const node = (tag, cls, value, options) => { const el = document.createElement(tag); if (cls) el.className = cls; if (value != null) el.textContent = tag === 'code' || tag === 'blockquote' ? String(value) : display(value, options); return el; };
  const entries = value => Array.isArray(value) ? value : value == null ? [] : [value];
  const caitlynAliases = [{ text: '덫', champion: 'Caitlyn', slot: 'W' }, { text: '투망', champion: 'Caitlyn', slot: 'E' }];
  // These bindings belong to the authored decision and field, not a guessed nearby owner.
  const laneSkillBindings = {
    RECEIVE_WITH_SPACE: {
      judgment: [{ text: 'Q', champion: 'Caitlyn', slot: 'Q' }, { text: 'E', champion: 'Lux', slot: 'E' }],
      action: [{ text: 'Q로 받을', champion: 'Caitlyn', slot: 'Q', prefix: true }, { text: 'Q 조준', champion: 'Caitlyn', slot: 'Q', prefix: true }],
      opponent_response: [{ text: 'Q로 당기거나', champion: 'Nautilus', slot: 'Q', prefix: true }, { text: 'Q 피해', champion: 'Kaisa', slot: 'Q', prefix: true }],
      changes: [{ text: 'Q 적중', champion: 'Nautilus', slot: 'Q', prefix: true }]
    },
    FOLLOW_BIND_WITH_EXIT: {
      action: [{ text: 'W와 짧은', champion: 'Caitlyn', slot: 'W', prefix: true }],
      opponent_response: [{ text: 'Q 접근', champion: 'Nautilus', slot: 'Q', prefix: true }]
    },
    KEEP_ESCAPE_VS_REENGAGE: {
      judgment: [{ text: '보호막', champion: 'Lux', slot: 'W' }],
      why: [{ text: 'E의 원문', champion: 'Lux', slot: 'E', prefix: true }],
      action: [{ text: 'E를 단순', champion: 'Caitlyn', slot: 'E', prefix: true }],
      opponent_response: [{ text: 'Q로 재접근', champion: 'Nautilus', slot: 'Q', prefix: true }, { text: 'W 적중', champion: 'Kaisa', slot: 'W', prefix: true }, { text: '보호막', champion: 'Lux', slot: 'W' }],
      alternative: [{ text: 'E가 없거나', champion: 'Caitlyn', slot: 'E', prefix: true }, { text: 'E로 보지 못한', champion: 'Lux', slot: 'E', prefix: true }, { text: '보호막', champion: 'Lux', slot: 'W' }],
      changes: [{ text: 'E를 소모하거나', champion: 'Caitlyn', slot: 'E', prefix: true }, { text: 'W 보호', champion: 'Lux', slot: 'W', prefix: true }]
    },
    RESPECT_TARGETED_CONTROL: { opponent_response: [{ text: 'R 후속', champion: 'Kaisa', slot: 'R', prefix: true }] },
    REASSESS_PURCHASE_AND_RETURN: { alternative: [{ text: '닻', champion: 'Nautilus', slot: 'Q' }] }, KEEP_FOLLOWUP_AFTER_CORE: {}
  };
  let catalog = null;
  let report = null;
  let filling = false;
  let importing = false;

  function display(value, options) {
    const input = report && report.input || {};
    return window.SkillDisplay ? window.SkillDisplay.format(String(value), { champions: [...entries(input.allies), ...entries(input.enemies)].map(pick => pick.champion), own: input.own_champion, ...options }) : String(value);
  }
  function laneFieldOptions(row, field) {
    const fields = laneSkillBindings[row.decision_id];
    return fields ? { bindings: fields[field] || [], aliases: caitlynAliases } : {};
  }
  function meansOptions(owner, value) {
    const who = champion(owner), names = String(value || '').split('·');
    return { owner, skillNames: Boolean(who && names.length && names.every(value => who.facts.some(fact => fact.name === value))) };
  }
  function ownActionOptions(value) {
    // Only kitAction's authored second action interpolates these own skill names.
    const own = report.input.own_champion, who = champion(own);
    return { bindings: entries(who && who.facts).filter(fact => String(value).includes(fact.name)).map(fact => ({ text: fact.name, champion: own, slot: fact.slot })) };
  }
  function fightActions() {
    return entries(report.teamfight && report.teamfight.actions).map((action, index) => index === 1 ? display(readable(action), ownActionOptions(readable(action))) : readable(action));
  }
  function laneFieldValue(row, field, value) {
    if (row.decision_id || !['why', 'action', 'assumptions'].includes(field)) return value;
    const own = report.input.own_champion, who = champion(own);
    const fact = entries(who && who.facts).find(fact => String(row.why).startsWith(fact.name + ': '));
    if (!fact || !window.SkillDisplay) return value;
    const qualify = value => String(value).startsWith(fact.name) ? window.SkillDisplay.label(own, fact.slot) + String(value).slice(fact.name.length) : value;
    return Array.isArray(value) ? value.map(qualify) : qualify(value);
  }
  function readable(value) {
    if (value == null) return '';
    if (typeof value === 'string' || typeof value === 'number') return String(value);
    if (Array.isArray(value)) return value.map(readable).filter(Boolean).join(' · ');
    return ['text', 'description', 'message', 'label', 'name', 'role', 'status', 'reason', 'note', 'summary'].map(key => value[key]).filter(v => typeof v === 'string').join(' · ');
  }
  function message(value, state) {
    $('loading-message').textContent = display(value);
    $('loading-message').classList.toggle('is-error', state === 'error');
    $('loading-message').classList.toggle('is-stale', state === 'stale');
  }
  function resolve(value) { return catalog ? window.LoadingStrategy.resolveChampion(value, catalog) : null; }
  function champion(value) { return catalog && catalog.champions[resolve(value) || value] || null; }
  function name(value) { const item = champion(value); return item ? item.name : String(value || '미확인'); }
  function text(id, value, options) { $(id).textContent = display(readable(value), options); }
  function list(items, cls, ordered, options) {
    const ul = node(ordered ? 'ol' : 'ul', cls);
    entries(items).forEach(item => { const copy = readable(item); if (copy) ul.append(node('li', '', copy, options)); });
    return ul;
  }
  function block(title, value, cls, options) {
    const wrap = node('div', 'copy-block' + (cls ? ' ' + cls : ''));
    wrap.append(node('h4', '', title));
    if (Array.isArray(value)) wrap.append(list(value, '', false, options));
    else wrap.append(node('p', '', readable(value) || '자료 미확인', options));
    return wrap;
  }
  function details(title, content) {
    const el = node('details', 'evidence-details'), body = node('div');
    el.append(node('summary', '', title)); body.append(content); el.append(body); return el;
  }
  function options(select, values, placeholder, current) {
    const items = [node('option', '', placeholder)]; items[0].value = '';
    values.forEach(value => { const option = node('option', '', name(value)); option.value = value; items.push(option); });
    select.replaceChildren(...items); select.value = values.includes(current) ? current : '';
  }
  function buildPicks() {
    ['ALLY', 'ENEMY'].forEach(team => {
      const target = $(team === 'ALLY' ? 'allied-picks' : 'enemy-picks');
      for (let index = 0; index < 5; index += 1) {
        const row = node('div', 'pick-row'); row.dataset.team = team; row.dataset.slot = index;
        const image = window.LoadingMap.portrait(null); image.id = 'portrait-' + team + '-' + index;
        const pickLabel = node('label'), input = node('input');
        input.type = 'text'; input.id = 'pick-' + team + '-' + index; input.setAttribute('list', 'champion-names'); input.setAttribute('aria-label', (team === 'ALLY' ? '아군 ' : '적군 ') + (index + 1) + ' 챔피언'); input.placeholder = '챔피언 이름'; input.required = true; input.maxLength = 80; input.autocomplete = 'off'; input.spellcheck = false;
        pickLabel.append(input);
        const positionLabel = node('label'), select = node('select'); select.id = 'position-' + team + '-' + index; select.setAttribute('aria-label', (team === 'ALLY' ? '아군 ' : '적군 ') + (index + 1) + ' 포지션');
        const unknown = node('option', '', '미확인'); unknown.value = ''; select.append(unknown);
        Object.entries(roles).forEach(([key, label]) => { const option = node('option', '', label); option.value = key; select.append(option); }); positionLabel.append(select); row.append(image, pickLabel, positionLabel); target.append(row);
      }
    });
  }
  function updateRosterOptions() {
    if (!catalog) return;
    const ids = team => [...Array(5)].map((_, i) => resolve($('pick-' + team + '-' + i).value)).filter(Boolean);
    const allies = [...new Set(ids('ALLY'))], enemies = [...new Set(ids('ENEMY'))];
    options($('own-champion'), allies, '아군 픽에서 선택', $('own-champion').value);
    $('own-champion').disabled = !allies.length;
    options($('lane-opponent'), enemies, '적군 픽에서 선택', $('lane-opponent').value);
    $('lane-opponent').disabled = $('opponent-mode').value !== 'MANUAL';
    $('lane-opponent').required = $('opponent-mode').value === 'MANUAL';
    ['ALLY', 'ENEMY'].forEach(team => {
      for (let index = 0; index < 5; index += 1) {
        const pick = champion($('pick-' + team + '-' + index).value), own = team === 'ALLY' && pick && pick.id === $('own-champion').value;
        const image = window.LoadingMap.portrait(pick, own); image.id = 'portrait-' + team + '-' + index; $('portrait-' + team + '-' + index).replaceWith(image);
      }
    });
    const complete = allies.length === 5 && enemies.length === 5;
    $('input-state').textContent = complete ? '10개 픽 입력됨 · 포지션은 선택 입력' : '아군 ' + allies.length + '/5 · 적군 ' + enemies.length + '/5';
  }
  function fillForm(input) {
    filling = true;
    ['ALLY', 'ENEMY'].forEach(team => entries(team === 'ALLY' ? input.allies : input.enemies).slice(0, 5).forEach((pick, index) => {
      $('pick-' + team + '-' + index).value = name(pick.champion);
      $('position-' + team + '-' + index).value = pick.position || '';
      $('pick-' + team + '-' + index).removeAttribute('aria-invalid');
    }));
    updateRosterOptions();
    $('own-champion').value = input.own_champion || '';
    $('own-position').value = input.own_position || '';
    $('side').value = input.side || 'BLUE';
    $('patch').value = input.patch || '';
    $('opponent-mode').value = input.opponent_mode || 'ASSIGNED';
    $('lane-opponent').value = input.lane_opponent || '';
    updateRosterOptions(); filling = false;
  }
  function readInput() {
    const picks = team => [...Array(5)].map((_, index) => ({ champion: $('pick-' + team + '-' + index).value.trim(), position: $('position-' + team + '-' + index).value || null }));
    return { allies: picks('ALLY'), enemies: picks('ENEMY'), own_champion: $('own-champion').value, own_position: $('own-position').value, side: $('side').value, patch: $('patch').value.trim() || null, opponent_mode: $('opponent-mode').value, lane_opponent: $('opponent-mode').value === 'MANUAL' ? $('lane-opponent').value || null : null };
  }
  function stale() {
    if (filling) return;
    updateRosterOptions();
    if (report) message('입력이 바뀌었습니다. ‘이번 판 방향 보기’를 눌러 새 픽과 조건을 반영하세요.', 'stale');
    else message('10개 픽과 내 챔피언·포지션을 선택하면 분석할 수 있습니다.');
  }
  function roster(picks, enemy, own) {
    const wrap = node('div', 'report-team' + (enemy ? ' enemy' : ''));
    wrap.append(node('span', '', enemy ? '적군' : '아군'));
    const row = node('div', 'team-roster');
    picks.forEach(pick => {
      const self = !enemy && pick.champion === own, item = node('div', 'roster-pick' + (self ? ' is-self' : ''));
      item.title = display(name(pick.champion) + ' · ' + (roles[pick.position] || '포지션 미확인') + (self ? ' · 나' : ''));
      item.append(window.LoadingMap.portrait(champion(pick.champion), self), node('span', '', (self ? '나 · ' : '') + name(pick.champion))); row.append(item);
    });
    wrap.append(row); return wrap;
  }
  function renderComposition() {
    const target = $('composition-content'); target.replaceChildren();
    [['allies', '우리 팀', false], ['enemies', '상대 팀', true]].forEach(([key, title, enemy]) => {
      const item = report.composition[key] || {}, card = node('article', 'panel composition-card' + (enemy ? ' enemy' : ''));
      card.append(node('h3', '', title), block('활용할 강점', item.strengths || []), block('조심할 빈틈', item.weaknesses || []), block('이 조건이 갖춰져야', item.conditions || [], 'is-conditions'));
      const signals = entries(item.signals);
      if (signals.length) {
        const detail = node('details', 'evidence-details'), body = node('div'); detail.append(node('summary', '', '이 해석에 연결한 실제 픽'));
        signals.forEach(signal => {
          const signalName = typeof signal === 'string' ? '' : name(signal.champion || signal.champion_id);
          const copy = typeof signal === 'string' ? signal : [display(readable(signal.means), meansOptions(signal.champion || signal.champion_id, signal.means)), readable(signal.condition)].filter(Boolean).join(' · ');
          const p = node('p', 'source-note', [signalName !== '미확인' ? signalName : '', copy].filter(Boolean).join(' · '));
          if (signal.evidence_ids) p.append(node('code', 'fact-hash', '자료 식별자 · ' + entries(signal.evidence_ids).join(' · ')));
          body.append(p);
        }); detail.append(body); card.append(detail);
      }
      target.append(card);
    });
  }
  function renderGameplan() {
    const plan = report.gameplan || {}, target = $('gameplan-content'); target.replaceChildren();
    target.append(node('p', 'lead-copy', readable(plan.base)));
    const grid = node('div', 'content-grid'); grid.append(block('싸움 전에 준비', plan.prepare || []), block('조건이 부족하면', plan.fallback), block('이때 방향을 바꿔요', plan.switch_when || []), block('사이드와 합류의 선택', plan.side_vs_group)); target.append(grid);
    if (entries(plan.stages).length) {
      const stages = node('ol', 'stage-list');
      entries(plan.stages).forEach(stage => { const item = node('li'); const label = { LANE: '라인전', EARLY: '초반', MID: '중반', LATE: '후반', TRANSITION: '라인전 이후', TEAMFIGHT: '한타', OBJECTIVE: '목표 경합' }[stage.stage] || stage.stage; item.append(node('h4', '', label), node('p', '', readable(stage.role)), list(stage.conditions || [])); stages.append(item); }); target.append(stages);
    }
    target.append(block('목표물 경합', plan.objectives), block('교전 뒤 이득으로 연결', plan.conversion));
    const context = report.contexts && report.contexts.operations;
    if (context) {
      target.append(block('운영에서 연결할 픽과 조건', context.selection_note || '아래 연결은 픽의 기술을 바탕으로 한 조건부 설계 가설입니다.'));
      target.append(connectionColumns(context, '운영을 함께 연결할 아군', '운영 전환을 끊을 상대'));
    }
  }
  function renderLane() {
    const lane = report.lane || {};
    const status = typeof lane.status === 'string' ? ({ UNKNOWN: '상대 미확인', ASSIGNED: '포지션 기준 상대', MANUAL: '직접 지정한 상대', KNOWN: '상대 지정됨' }[lane.status] || lane.status) : readable(lane.status);
    text('lane-status', status);
    text('lane-opponent-copy', lane.opponent ? '내 챔피언 ' + name(report.input.own_champion) + ' · 상대 ' + (lane.opponent.name || name(lane.opponent.id)) + (lane.opponent.position ? ' · ' + (roles[lane.opponent.position] || '포지션 미확인') : '') : '라인 상대 미확인 · 확정할 수 있는 기술의 성질과, 상대가 정해져야 판단할 내용을 구분합니다.');
    const tbody = $('lane-table').querySelector('tbody'); tbody.replaceChildren();
    entries(lane.rows).forEach(row => {
      const tr = node('tr'); tr.dataset.milestone = row.id;
      const th = node('th', '', row.period); th.scope = 'row';
      const level = typeof row.level === 'string' ? ({ UNKNOWN: '상성 미확인', OFFICIAL_FACT: '공식 기술 참고', DESIGN_HYPOTHESIS: '조건부 해석', EXPLORATORY: '탐색 해석' }[row.level] || '') : '';
      if (level) th.append(node('span', 'lane-level', level)); tr.append(th);
      [['판단', 'judgment'], ['이유', 'why'], ['내 행동', 'action'], ['달라지는 조건', 'changes']].forEach(([label, field]) => {
        const td = node('td'), body = node('div'); td.dataset.label = label;
        const value = laneFieldValue(row, field, row[field]), options = laneFieldOptions(row, field);
        body.append(Array.isArray(value) ? list(value, '', false, options) : node('span', '', readable(value), options));
        if (label === '이유') {
          if (entries(row.assumptions).length) body.append(block('가정한 기술·상황 · 실제 상태 미관측', laneFieldValue(row, 'assumptions', row.assumptions), '', laneFieldOptions(row, 'assumptions')));
          if (row.fact_scope) body.append(node('p', 'source-note', '공식 사실과 설계 가설의 경계 · ' + readable(row.fact_scope)));
        }
        if (label === '내 행동') {
          if (row.opponent_response) body.append(block('상대 대응 가정', row.opponent_response, '', laneFieldOptions(row, 'opponent_response')));
          if (row.alternative) body.append(block('그때의 대안', row.alternative, '', laneFieldOptions(row, 'alternative')));
        }
        td.append(body); tr.append(td);
      });
      if (entries(row.evidence_ids).length) tr.dataset.evidenceIds = row.evidence_ids.join(' ');
      tbody.append(tr);
    });
    const target = $('lane-context'); target.replaceChildren();
    const grid = node('div', 'content-grid'); grid.append(block('미니언 흐름', lane.wave), block('정글과의 연결', lane.jungle), block('귀환과 다른 라인 이동', lane.reset_roam), block('어려워졌을 때 복구', lane.recovery)); target.append(grid);
    if (entries(lane.interactions).length) target.append(block('맞부딪히는 기술과 조건', lane.interactions));
    const contexts = report.contexts || {}, laneContext = contexts.lane, jungle = contexts.jungle;
    if (laneContext) {
      const label = { DUO: '바텀·서포터의 라인 연결', DUO_INCOMPLETE: '바텀·서포터 연결 · 일부 배치 미확인', SOLO: '단독 라인의 연결', SOLO_UNKNOWN: '라인 상대 미확인 상태의 연결', JUNGLE: '정글 · 고정 라인 상대 없음', MANUAL_COMPARISON: '직접 지정한 상대와 비교' }[laneContext.kind] || '라인에서 연결할 픽과 조건';
      target.append(block(label, laneContext.selection_note || '라인 상대와 함께 서는 아군을 구분해 읽는 조건부 설계 가설입니다.'));
      target.append(connectionColumns(laneContext, '라인에서 함께 연결할 아군', '라인에서 대응할 상대'));
      if (entries(laneContext.limits).length) target.append(block('라인 연결의 미확인 범위', laneContext.limits));
    }
    if (jungle) {
      target.append(block('정글 개입 · 현재 위치 미관측', '아군·적 정글러의 현재 위치와 이동 경로는 관측하지 않았습니다. 아래 개입은 조건이 확인된 경우만 가정합니다.'));
      target.append(connectionColumns(jungle, '개입을 연결할 아군', '개입을 경계할 상대'));
      if (entries(jungle.conditions).length) target.append(block('정글 개입을 가정하기 전 확인', jungle.conditions));
    }
  }
  function fightConnections(items, threats, reasonRequired) {
    const ul = node('ul', 'fight-link-list' + (threats ? ' threats' : ''));
    entries(items).forEach(item => {
      const li = node('li');
      if (typeof item === 'string') {
        const body = node('div'); body.append(node('p', '', item));
        if (reasonRequired) body.append(node('small', '', '선정 이유 · 추가 근거 미확인'));
        li.append(body);
      }
      else {
        const who = champion(item.champion || item.id), body = node('div');
        const options = { owner: item.champion || item.id };
        li.append(window.LoadingMap.portrait(who)); body.append(node('strong', '', item.name || (who && who.name) || name(item.champion)), node('p', '', readable(item.means), meansOptions(item.champion || item.id, item.means)));
        const reasons = entries(item.reasons).map(readable).filter(Boolean);
        if (reasons.length) reasons.forEach(reason => body.append(node('small', '', '선정 이유 · ' + reason, options)));
        else if (reasonRequired || item.context) body.append(node('small', '', '선정 이유 · 추가 근거 미확인'));
        if (item.condition) body.append(node('small', '', '조건 · ' + readable(item.condition), options)); li.append(body);
      }
      ul.append(li);
    }); return ul;
  }
  function connectionColumns(context, partnerTitle, threatTitle, reasonRequired = true) {
    const columns = node('div', 'fight-columns');
    [[context.partners, partnerTitle, false], [context.threats, threatTitle, true]].forEach(([items, title, threats]) => {
      const column = node('div', 'copy-block'); column.append(node('h4', '', title));
      column.append(entries(items).length ? fightConnections(items, threats, reasonRequired) : node('p', 'source-note', '이 맥락에 연결할 후보 미확인 · 해당 능력이 없다는 뜻은 아닙니다.'));
      columns.append(column);
    });
    return columns;
  }
  function renderFight() {
    const fight = report.teamfight || {}, target = $('fight-content'); target.replaceChildren(node('p', 'lead-copy', readable(fight.role)));
    const role = report.roles;
    if (role) {
      const roleGrid = node('div', 'content-grid'), proposed = role.proposed || {};
      const base = block('기본 유형·역할', readable(role.base) || '기본 유형 미확인');
      const proposal = block('이번 계획에서 맡을 역할 제안', readable(proposed) || '역할 제안 미확인', 'is-conditions');
      if (typeof role.changed === 'boolean') proposal.append(node('p', 'source-note', role.changed ? '조합과 조건에 따라 기본 유형에서 역할을 바꾼 제안입니다.' : '이번 계획에서도 기본 유형의 역할을 제안합니다.'));
      if (entries(proposed.reasons).length) proposal.append(block('이 역할을 제안한 이유', proposed.reasons));
      if (entries(proposed.conditions).length) proposal.append(block('이 조건이 갖춰져야', proposed.conditions));
      if (entries(proposed.limits).length) proposal.append(block('역할 제안의 한계', proposed.limits));
      roleGrid.append(base, proposal); target.append(roleGrid);
    }
    const context = report.contexts && report.contexts.teamfight;
    if (context && context.selection_note) target.append(node('p', 'source-note', readable(context.selection_note)));
    target.append(connectionColumns(context || fight, '함께 연결할 아군', '내 행동을 끊을 상대', Boolean(context)));
    if (fight.map) {
      const scenario = { map: fight.map, plan: { steps: fightActions().map((action, i) => ({ number: i + 1, text: action })) } };
      target.append(window.LoadingMap.create(scenario, catalog, report.input));
    }
    const grid = node('div', 'content-grid'); grid.append(block('진입 전 점검', fight.setup || []));
    if (!fight.map) grid.append(block('싸움 중 순서', fightActions()));
    grid.append(block('역할을 바꿀 조건', fight.switch_when || []), block('퇴로와 이탈 기준', fight.exit || []), block('교전이 끝난 뒤', fight.after || [])); target.append(grid);
  }
  function renderScenarios() {
    const target = $('scenario-content'); target.replaceChildren();
    if (!entries(report.scenarios).length) { target.append(node('p', 'empty-state', '현재 내 챔피언과 역할에 바로 연결할 기존 지도 장면이 없습니다. 위의 조합·라인전·한타 조건부터 확인하세요. 다른 챔피언으로 바꾼 지도를 대신 표시하지 않습니다.')); return; }
    report.scenarios.forEach((scenario, index) => {
      const options = { aliases: report.input.own_champion === 'Caitlyn' ? caitlynAliases : [] };
      const card = node('article', 'panel scenario-card'); card.dataset.scenario = scenario.id;
      const heading = node('div', 'scenario-heading'); heading.append(node('h3', '', String(index + 1).padStart(2, '0') + ' · ' + scenario.title, options));
      const link = node('a', '', '기존 상황 연습에서 열기 ↗'); link.href = './directions.html#scene=' + encodeURIComponent(scenario.id); heading.append(link); card.append(heading);
      const assumptions = node('div', 'scenario-conditions'); assumptions.append(node('h4', '', '앞으로 이 조건이 갖춰진 상황을 가정합니다'), list(scenario.assumptions || [], '', false, options)); card.append(assumptions);
      card.append(window.LoadingMap.create(scenario, catalog, report.input));
      const lower = node('div', 'content-grid'); lower.append(block('먼저 확인할 전제', scenario.requirements || [], '', options), block('이때는 적용하지 않아요', scenario.exceptions || [], '', options)); card.append(lower); target.append(card);
    });
  }
  function officialFacts(facts) {
    const wrap = node('div');
    entries(facts).forEach(fact => {
      const article = node('article', 'fact-card'); article.dataset.factId = fact.id || '';
      const who = fact.champion || fact.champion_id || (typeof fact.id === 'string' && !fact.id.startsWith('official-item:') ? fact.id.split(':')[1] : null);
      const factTitle = window.SkillDisplay && who ? window.SkillDisplay.factLabel(who, fact) : [who ? name(who) : '', fact.slot === 'P' ? '기본 지속 효과' : fact.slot === 'ITEM' ? '아이템' : fact.slot, fact.name].filter(Boolean).join(' · ');
      const heading = node('h4'); heading.textContent = factTitle;
      article.append(heading, node('blockquote', '', fact.text || fact.raw_excerpt || fact.excerpt));
      const meta = node('div', 'fact-meta'); meta.append(node('span', '', '공식 자료 패치 · ' + (fact.patch || catalog.source_patch || '미확인')));
      try { const url = new URL(fact.url); if (url.protocol === 'https:') { const link = node('a', '', '공식 원문 ↗'); link.href = url.href; link.target = '_blank'; link.rel = 'noopener noreferrer'; meta.append(link); } } catch (_) { /* Source data stays inert if its URL is malformed. */ }
      article.append(meta);
      if (String(fact.scope || '').includes('UNEVALUATED_TEMPLATE')) article.append(node('p', 'source-note', '보관 원문의 템플릿 수치는 미평가입니다. 실제 피해량·사거리·재사용 시간을 계산한 값이 아닙니다.'));
      if (String(fact.scope || '').includes('NOT_BUILD_OR_MATCHUP')) article.append(node('p', 'source-note', '아이템 속성 참고이며 권장 빌드·구매 시점·매치업 우열의 근거가 아닙니다.'));
      if (fact.raw_excerpt && fact.raw_excerpt !== fact.text) { const raw = node('details', 'evidence-details'); raw.append(node('summary', '', '보관한 원문 발췌'), node('blockquote', '', fact.raw_excerpt)); article.append(raw); }
      if (fact.id) article.append(node('code', 'fact-hash', '자료 식별자 · ' + fact.id));
      if (fact.sha256) article.append(node('code', 'fact-hash', 'SHA-256 · ' + fact.sha256));
      if (fact.local_source || fact.locator) article.append(node('code', 'fact-hash', '보관 위치 · ' + [fact.local_source, readable(fact.locator)].filter(Boolean).join(' · ')));
      wrap.append(article);
    });
    if (!wrap.childNodes.length) wrap.append(node('p', 'source-note', '연결된 공식 기술 자료가 없습니다.'));
    return wrap;
  }
  function renderEvidence() {
    const evidence = report.evidence || {}, target = $('evidence-content'); target.replaceChildren();
    target.append(node('p', 'evidence-intro', '공식 원문은 기술의 성질을 확인하는 참고 자료입니다. 조합 해석과 행동 제안은 조건부 설계 가설이며 전술 효과 검증이나 사용자 승인을 뜻하지 않습니다.'));
    const status = readable(evidence.patch_status);
    if (status) target.append(node('p', 'source-note', '패치 적용 범위 · ' + ({ UNKNOWN: '입력 패치 미확인', MATCH: '공식 자료와 주 패치 일치 · 전술 검증과 별개', SOURCE_MAJOR_MATCH: '공식 자료와 주 패치 일치 · 전술 검증과 별개', MISMATCH: '입력 패치와 공식 자료 버전이 다름' }[status] || status)));
    target.append(details('공식 챔피언 기술 원문 · 출처와 해시', officialFacts(evidence.facts)));
    const ruleWrap = node('div'); ruleWrap.append(node('p', 'source-note', '기존 규칙은 탐색 단계입니다. 빈 분류는 해당 능력이 없다는 뜻이 아니며, 모든 조합 상호작용을 분류한 자료가 아닙니다.'));
    const ruleList = node('ul', 'rules-list');
    entries(evidence.rules).forEach(rule => { const li = node('li'); if (typeof rule === 'string') li.append(node('code', 'fact-hash', rule)); else { li.append(node('strong', '', rule.interpretation || readable(rule) || rule.id || '기존 탐색 규칙')); if (rule.id || rule.version) li.append(node('code', 'fact-hash', '규칙 식별자 / 버전 · ' + [rule.id, rule.version].filter(Boolean).join(' / '))); if (rule.sha256) li.append(node('code', 'fact-hash', 'SHA-256 · ' + rule.sha256)); if (rule.local_source) li.append(node('code', 'fact-hash', '보관 위치 · ' + rule.local_source)); if (entries(rule.limitations).length) li.append(list(rule.limitations)); if (entries(rule.counterexamples).length) li.append(list(rule.counterexamples)); } ruleList.append(li); });
    ruleWrap.append(ruleList); target.append(details('조합 해석에 사용한 탐색 규칙 · 분류 미완성', ruleWrap));
    const stats = node('div');
    if (!entries(evidence.statistics).length) stats.append(node('p', 'source-note', '이 입력에 연결된 통계 근거가 없습니다. 승률·상성 점수·효과를 추정하지 않습니다.'));
    else {
      stats.append(node('p', 'source-note', '기존 익명 표본의 관찰 정보입니다. 표본의 패치·포지션·상대 범위와 누락을 함께 읽어야 하며, 라인 상성이나 다음 교전 승률로 바꾸지 않습니다.'));
      entries(evidence.statistics).forEach(stat => {
        const item = node('article', 'fact-card'); item.append(node('h4', '', typeof stat === 'string' ? stat : readable(stat) || '기존 익명 통계'));
        if (typeof stat === 'object') {
          const population = { PRO_REFERENCE: '프로 참고 표본 · 선택된 참가자', CHALLENGER: '챌린저 시드 경기 표본 · 모든 참가자의 등급을 뜻하지 않음' }[stat.population] || '범위 미확인';
          const fields = [['패치', stat.patch], ['챔피언', stat.champion ? name(stat.champion) : null], ['포지션', roles[stat.position]], ['표본 범위', population], ['경기 / 참가자 관측', [stat.matches, stat.participant_observations].filter(v => v != null).join(' / ')], ['상대 범위', stat.opponent ? name(stat.opponent) : '상대 챔피언별 통계 아님']];
          fields.forEach(([label, value]) => { const copy = readable(value); if (copy) item.append(node('p', 'source-note', label + ' · ' + copy)); });
          const recall = stat.first_recall || {};
          [['timing', '첫 구매 기반 귀환 시각'], ['current_gold', '구매 직전 관측 골드']].forEach(([key, title]) => {
            const metric = recall[key]; if (!metric) return;
            const format = value => key === 'timing' ? (Math.round(value / 1000) / 60).toFixed(1) + '분' : Math.round(value) + '골드';
            const value = metric.status === 'AVAILABLE' && Number.isFinite(metric.median) ? '중앙값 ' + format(metric.median) + (Number.isFinite(metric.q1) && Number.isFinite(metric.q3) ? ' · 중간 50% ' + format(metric.q1) + '–' + format(metric.q3) : '') : '미확인 · 유효 경기 부족 또는 결측';
            item.append(node('p', 'source-note', title + ' · ' + value + ' · 유효 경기 ' + (metric.match_n ?? '미확인') + ' / 관측 ' + (metric.n ?? '미확인') + ' · 누락 ' + (metric.missing_n ?? '미확인')));
          });
          item.append(node('p', 'source-note', '구매 기록으로 추정하므로 구매 없는 귀환·정확한 귀환 시작과 완료·당시 미니언 흐름과 의도는 모릅니다. 시각·금액은 권장값이 아니며, 경기 표본이 겹칠 수 있습니다.'));
          if (stat.source) item.append(node('code', 'fact-hash', '보관 위치 · ' + stat.source.local_source), node('code', 'fact-hash', 'SHA-256 · ' + stat.source.sha256));
          if (stat.id) item.append(node('code', 'fact-hash', '자료 식별자 · ' + stat.id));
        }
        stats.append(item);
      });
    }
    target.append(details('기존 익명 통계 · 적용 범위와 한계', stats));
    const unknowns = node('div'); unknowns.append(block('아직 모르는 것', evidence.unknowns || []), block('이 안내의 한계', evidence.limits || []), node('p', 'source-note', '현재 체력·마나·아이템·기술 사용 가능 여부·적의 의도는 입력된 픽에서 추론하지 않습니다. 레벨 점검 시점이 기술 습득이나 준비 완료를 보장하지 않습니다.'));
    target.append(details('미확인 정보와 적용 한계', unknowns));
    const assets = node('div'); assets.append(node('p', 'source-note', '챔피언 초상화와 지도는 로컬에 보관한 Riot Games 공식 자료입니다.'));
    entries(catalog.assets).forEach(asset => { const item = node('div', 'fact-card'); item.append(node('p', 'source-note', readable(asset.path || asset.local_path || asset.id || asset.name)), node('code', 'fact-hash', '원본 URL · ' + (asset.url || asset.source_url || asset.requested_url || '자료 목록 참조')), node('code', 'fact-hash', 'SHA-256 · ' + (asset.sha256 || '미확인'))); assets.append(item); });
    target.append(details('지도·초상화 자산의 자료 기록', assets));
  }
  function renderReport() {
    const summary = report.summary || {};
    const representative = report.lane && report.lane.matchup_id === 'Caitlyn_Lux__Kaisa_Nautilus_v2';
    const representativeAliases = representative ? { aliases: [{ text: '덫', champion: 'Caitlyn', slot: 'W' }] } : {};
    ['our_plan', 'enemy_plan', 'collision', 'my_role', 'lane_key', 'fight_key'].forEach(key => text(key.replaceAll('_', '-'), summary[key], key === 'lane_key' ? representativeAliases : {}));
    $('remember').replaceChildren(...entries(summary.remember).slice(0, 3).map((item, index) => node('li', '', readable(item), index === 0 ? representativeAliases : {})));
    const uncertainties = [...entries(summary.uncertainties)];
    if (!uncertainties.some(item => /체력|준비|사용 가능/.test(readable(item)))) uncertainties.push('현재 체력·자원과 기술 사용 가능 여부는 경기 안에서 별도 확인하세요.');
    $('uncertainties').replaceChildren(...uncertainties.map(item => node('li', '', readable(item))));
    text('report-patch', '입력 패치 ' + (report.input.patch || '미확인') + ' · 자료 ' + catalog.source_patch);
    $('report-teams').replaceChildren(roster(report.input.allies, false, report.input.own_champion), roster(report.input.enemies, true));
    renderComposition(); renderGameplan(); renderLane(); renderFight(); renderScenarios(); renderEvidence();
    $('loading-results').hidden = false;
  }
  function analyze() {
    try {
      document.querySelectorAll('[id^="pick-"]').forEach(input => input.removeAttribute('aria-invalid'));
      const input = readInput();
      ['ALLY', 'ENEMY'].forEach(team => { for (let i = 0; i < 5; i += 1) { const el = $('pick-' + team + '-' + i); if (!resolve(el.value)) el.setAttribute('aria-invalid', 'true'); } });
      const next = window.LoadingStrategy.analyze(input, catalog);
      report = next; fillForm(next.input); renderReport(); $('input-panel').open = false;
      message('입력한 10개 픽을 반영했습니다. 먼저 핵심 요약과 미확인 조건을 읽어보세요.');
      $('loading-summary').focus({ preventScroll: true }); $('loading-summary').scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
    } catch (error) {
      $('loading-results').hidden = true;
      $('input-panel').open = true;
      message((error && error.message) || '픽과 포지션 입력을 확인해 주세요.', 'error');
      const invalid = document.querySelector('#loading-form [aria-invalid="true"]');
      if (invalid) invalid.focus();
    }
  }
  function localImportAvailable() { return location.protocol === 'http:' && ['localhost', '127.0.0.1', '::1', '[::1]'].includes(location.hostname); }
  async function importDraft() {
    if (!localImportAvailable() || importing) return;
    importing = true; $('pc-import').disabled = true;
    try {
      let token = '';
      try { token = sessionStorage.getItem('lol-coach-dev-token') || ''; } catch (_) { /* Manual input remains available. */ }
      if (!token) throw new Error('기존 PC 연결 인증이 없습니다. PC 화면에서 연결한 뒤 가져오거나 직접 입력해 주세요.');
      const response = await fetch('/dev/v1/pregame/pc-status', { method: 'GET', headers: { Authorization: 'Bearer ' + token }, cache: 'no-store', credentials: 'same-origin', redirect: 'error' });
      token = '';
      if (!response.ok) throw new Error('기존 PC 연결을 확인할 수 없습니다. 직접 입력해 주세요.');
      const data = await response.json(), connection = data && data.connection;
      if (!connection || connection.status !== 'CONNECTED' || connection.phase !== 'ChampSelect' || !connection.input) throw new Error('챔피언 선택 중인 연결된 PC 픽이 없습니다. 직접 입력해 주세요.');
      const input = window.LoadingStrategy.fromDraft(connection.input, catalog);
      fillForm(input); $('input-panel').open = true;
      if (!$('loading-form').checkValidity()) { message('PC 픽을 가져왔습니다. 빈 픽과 내 챔피언·포지션을 확인한 뒤 방향을 살펴보세요.'); return; }
      analyze();
    } catch (error) { message(error && error.message || 'PC 픽 가져오기를 완료하지 못했습니다. 직접 입력해 주세요.', 'error'); }
    finally { importing = false; $('pc-import').disabled = false; }
  }
  async function init() {
    buildPicks(); window.LoadingMap.init();
    $('loading-form').addEventListener('submit', event => { event.preventDefault(); analyze(); });
    $('loading-form').addEventListener('input', stale);
    $('loading-form').addEventListener('change', stale);
    $('pc-import').hidden = !localImportAvailable(); $('pc-import').addEventListener('click', importDraft);
    try {
      const response = await fetch('./loading-data.json', { cache: 'no-store', credentials: 'same-origin', redirect: 'error' });
      if (!response.ok) throw new Error('자료 응답을 확인할 수 없습니다.');
      catalog = await response.json();
      if (!catalog || !catalog.champions || Array.isArray(catalog.champions) || !window.LoadingStrategy) throw new Error('챔피언 자료와 분석 엔진을 함께 불러오지 못했습니다.');
      const values = new Set();
      const searchOptions = [];
      Object.values(catalog.champions).sort((a, b) => a.name.localeCompare(b.name, 'ko')).forEach(item => [item.name, item.id, ...entries(item.aliases)].forEach(alias => { if (typeof alias !== 'string' || values.has(alias)) return; values.add(alias); const option = node('option'); option.value = alias; option.label = item.name + ' · ' + item.id; searchOptions.push(option); }));
      $('champion-names').replaceChildren(...searchOptions);
      [0, 1].forEach(index => { const button = $('example-' + index); button.disabled = false; button.addEventListener('click', () => { fillForm(window.LoadingStrategy.exampleInput(catalog, index)); $('input-panel').open = true; if (report) message('예시 픽을 입력했습니다. ‘이번 판 방향 보기’를 누르면 요약이 바뀝니다.', 'stale'); else message('예시 픽을 입력했습니다. 내 챔피언과 포지션을 확인하고 ‘이번 판 방향 보기’를 눌러보세요.'); }); });
      $('analyze').disabled = false; updateRosterOptions(); message('10개 픽과 내 챔피언·포지션을 선택하세요. 예시를 바꿔 조합별 방향을 비교할 수도 있습니다.');
    } catch (error) { message('자료를 불러오지 못했습니다. 페이지를 새로고침해 주세요. ' + (error && error.message || ''), 'error'); }
  }
  init();
})();

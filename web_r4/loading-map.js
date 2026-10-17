/* Local sprite portraits and illustrative maps. No live positions or network adapters. */
(function (root) {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg';
  const styles = { MOVE: { color: '#90d7ee', label: '이동' }, PRESSURE: { color: '#f3bf69', dash: '24 17', label: '압박' }, RETREAT: { color: '#d3a4ee', dash: '5 17', label: '후퇴' } };
  let sequence = 0;
  let activeZoom = null;
  const display = (text, options) => root.SkillDisplay ? root.SkillDisplay.format(String(text), { champions: [], ...options }) : String(text);
  const node = (tag, cls, text, options) => { const el = document.createElement(tag); if (cls) el.className = cls; if (text != null) el.textContent = display(text, options); return el; };
  function svg(tag, attrs, text, options) {
    const el = document.createElementNS(NS, tag);
    Object.entries(attrs || {}).forEach(([key, value]) => { if (value != null) el.setAttribute(key, key === 'aria-label' || key === 'title' ? display(value, options) : String(value)); });
    if (text != null) el.textContent = display(text, options);
    return el;
  }
  function sprite(champion) {
    const p = champion && champion.portrait;
    if (!p || !/^loading-assets\/[A-Za-z0-9_.-]+\.png$/.test(p.sprite || '') || ![p.x, p.y, p.w, p.h].every(Number.isFinite) || p.w <= 0 || p.h <= 0) return null;
    const view = svg('svg', { viewBox: [p.x, p.y, p.w, p.h].join(' '), class: 'champion-sprite', preserveAspectRatio: 'xMidYMid slice', role: 'img', 'aria-label': champion.name + ' 공식 초상화' });
    view.append(svg('image', { href: './' + p.sprite, x: 0, y: 0, width: p.sheet_width || 480, height: p.sheet_height || 144 }));
    return view;
  }
  function portrait(champion, self) {
    const wrap = node('span', 'pick-portrait' + (self ? ' is-self' : ''));
    const image = sprite(champion);
    if (image) wrap.append(image);
    else { wrap.textContent = champion ? champion.name.slice(0, 1) : '+'; wrap.setAttribute('aria-hidden', 'true'); }
    return wrap;
  }
  const point = value => ({ x: Math.min(100, Math.max(0, Number(value && value.x) || 0)) * 10, y: Math.min(100, Math.max(0, Number(value && value.y) || 0)) * 10 });
  const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
  function draw(map, catalog, input, prefix, options) {
    const result = svg('svg', { class: 'strategy-map', viewBox: '0 0 1000 1000', role: 'img', 'aria-labelledby': prefix + '-title ' + prefix + '-desc' });
    result.append(svg('title', { id: prefix + '-title' }, '내 시작과 목표 배치 · 설명용 예시'), svg('desc', { id: prefix + '-desc' }, '금색 테두리는 내 시작점, 반투명 점선은 목표점입니다. 번호별 화살표는 행동 카드와 대응하며 실제 위치·안전 경로가 아닙니다. 적 위치는 표시하지 않습니다.'));
    const defs = svg('defs');
    Object.entries(styles).forEach(([key, style]) => {
      const marker = svg('marker', { id: prefix + '-' + key, viewBox: '0 0 10 10', refX: 8, refY: 5, markerWidth: 3.5, markerHeight: 3.5, orient: 'auto-start-reverse' });
      marker.append(svg('path', { d: 'M 0 0 L 10 5 L 0 10 Z', fill: style.color })); defs.append(marker);
    });
    result.append(defs, svg('image', { href: './direction-assets/map11.png', x: 0, y: 0, width: 1000, height: 1000 }), svg('rect', { x: 0, y: 0, width: 1000, height: 1000, fill: '#09141e', 'fill-opacity': '.2' }));
    (map.landmarks || []).forEach(landmark => {
      const p = point(landmark);
      const group = svg('g', { class: 'map-step', 'data-step': landmark.step || 1 });
      group.append(svg('circle', { cx: p.x, cy: p.y, r: 15, fill: '#12202a', stroke: '#e3c081', 'stroke-width': 4 }), svg('text', { x: clamp(p.x, 180, 820), y: clamp(p.y - 78, 35, 960), class: 'map-label', 'text-anchor': 'middle' }, landmark.label || '설명 위치', options));
      result.append(group);
    });
    const badgeLocations = [];
    const alliedIds = new Set(input.allies.map(pick => pick.champion));
    const entityLocations = (map.entities || []).filter(e => e.team === 'ALLY' && alliedIds.has(e.champion)).flatMap(e => [point(e.start), ...(e.target ? [point(e.target)] : [])]);
    (map.arrows || []).forEach((arrow, index) => {
      const style = styles[arrow.kind] || styles.MOVE, a = point(arrow.from), b = point(arrow.to), step = arrow.step || index + 1;
      const group = svg('g', { class: 'map-step', 'data-step': step });
      group.append(svg('title', {}, step + '단계 · ' + style.label + ' 방향 예시', options));
      const d = 'M ' + a.x + ' ' + a.y + ' L ' + b.x + ' ' + b.y;
      group.append(svg('path', { d, stroke: '#07121b', 'stroke-width': 22, fill: 'none', 'stroke-linecap': 'round' }), svg('path', { d, stroke: style.color, 'stroke-width': 11, 'stroke-dasharray': style.dash, fill: 'none', 'stroke-linecap': 'round', 'marker-end': 'url(#' + prefix + '-' + (styles[arrow.kind] ? arrow.kind : 'MOVE') + ')' }));
      const dx = b.x - a.x, dy = b.y - a.y, length = Math.hypot(dx, dy) || 1;
      const candidates = [67, -67, 100, -100].map(offset => ({ x: clamp(a.x + dx * .56 - dy / length * offset, 32, 968), y: clamp(a.y + dy * .56 + dx / length * offset, 32, 968) }));
      const clearance = p => Math.min(...[...entityLocations, ...badgeLocations].map(q => Math.hypot(q.x - p.x, q.y - p.y)), 1000);
      const p = candidates.find(p => clearance(p) > 78) || candidates.sort((a, b) => clearance(b) - clearance(a))[0]; badgeLocations.push(p);
      group.append(svg('circle', { cx: p.x, cy: p.y, r: 25, fill: '#f1e5c7', stroke: '#25323b', 'stroke-width': 4 }), svg('text', { x: p.x, y: p.y, class: 'map-number' }, step)); result.append(group);
    });
    // Show only actual allied picks in the supplied illustrative geometry.
    // No enemy location is observed or inferred by this loading report.
    (map.entities || []).filter(entity => entity.team === 'ALLY' && alliedIds.has(entity.champion) && (!entity.self || entity.champion === input.own_champion)).forEach(entity => {
      const champion = catalog.champions[entity.champion], start = point(entity.start);
      const addPortrait = (p, target) => {
        const group = svg('g', target ? { 'data-entity-target': entity.id } : { 'data-entity': entity.id, 'data-self': String(Boolean(entity.self)), 'data-team': 'ALLY' });
        group.append(svg('title', {}, (target ? '내 목표 배치 예시 · ' : entity.self ? '내 시작 예시 · ' : '아군 배치 예시 · 현재 위치 미확인 · ') + (champion ? champion.name : ''), options));
        group.append(svg('circle', { cx: p.x, cy: p.y, r: target ? 35 : entity.self ? 34 : 27, fill: '#152333', 'fill-opacity': target ? .5 : 1, stroke: target || !entity.self ? '#80c4f5' : '#e3c081', 'stroke-width': target ? 4 : entity.self ? 6 : 5, 'stroke-dasharray': target ? '10 8' : null }));
        const image = sprite(champion);
        if (image) { const size = entity.self ? 52 : 43; image.setAttribute('class', 'map-sprite'); image.setAttribute('x', p.x - size / 2); image.setAttribute('y', p.y - size / 2); image.setAttribute('width', size); image.setAttribute('height', size); if (target) image.setAttribute('opacity', '.4'); group.append(image); }
        const right = !entity.self && p.x < 800;
        group.append(svg('text', { x: p.x + (right ? 42 : -46), y: p.y + 8, 'text-anchor': right ? 'start' : 'end', class: 'map-label' }, target ? '목표 예시' : entity.self ? '내 시작 예시' : (champion ? champion.name : '') + ' 예시', options));
        result.append(group);
      };
      if (entity.self && entity.target) addPortrait(point(entity.target), true);
      addPortrait(start, false);
    });
    return result;
  }
  function controls(select) {
    const wrap = node('div', 'map-step-controls'); wrap.setAttribute('role', 'group'); wrap.setAttribute('aria-label', '지도에 표시할 행동 단계'); wrap.append(node('span', '', '단계 보기'));
    ['ALL', '1', '2', '3'].forEach(step => { const button = node('button', '', step === 'ALL' ? '전체' : step); button.type = 'button'; button.dataset.mapStep = step; button.setAttribute('aria-pressed', 'false'); button.setAttribute('aria-label', step === 'ALL' ? '전체 단계 표시' : step + '단계만 표시'); button.addEventListener('click', () => select(step)); wrap.append(button); });
    return wrap;
  }
  function create(scenario, catalog, input) {
    const options = { champions: [...input.allies, ...input.enemies].map(pick => pick.champion), own: input.own_champion, owner: scenario.id ? input.own_champion : undefined, aliases: scenario.id && input.own_champion === 'Caitlyn' ? [{ text: '덫', champion: 'Caitlyn', slot: 'W' }, { text: '투망', champion: 'Caitlyn', slot: 'E' }] : [] };
    const wrap = node('div', 'scenario-grid'), left = node('div', 'scenario-map-column'), right = node('div', 'scenario-steps-column');
    const heading = node('div', 'map-header'); heading.append(node('h4', '', '움직임 지도'));
    const zoom = node('button', '', '⤢ 크게 보기'); zoom.type = 'button'; heading.append(zoom); left.append(heading);
    const prefix = 'loading-map-' + (++sequence), map = draw(scenario.map || {}, catalog, input, prefix, options);
    let selected = root.matchMedia('(max-width: 560px)').matches ? '1' : 'ALL';
    const steps = node('ol', 'scenario-steps');
    const items = scenario.plan && scenario.plan.steps || [];
    const select = step => {
      selected = step;
      map.dataset.activeStep = step;
      [control, activeZoom && activeZoom.owner === prefix ? activeZoom.controls : null].filter(Boolean).forEach(group => group.querySelectorAll('button').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.mapStep === step))));
      if (activeZoom && activeZoom.owner === prefix) activeZoom.map.dataset.activeStep = step;
      steps.querySelectorAll('li').forEach(item => { const match = item.dataset.step === step; item.classList.toggle('is-selected', match); item.querySelector('button').setAttribute('aria-pressed', String(match)); });
    };
    const control = controls(select); left.append(control);
    const frame = node('div', 'map-frame'); frame.append(map); left.append(frame);
    const legend = node('div', 'map-legend'); legend.append(node('span', 'gold', '● 내 시작 예시'), node('span', 'blue', '◌ 목표 / 이동'), node('span', 'gold', '⇢ 압박'), node('span', 'purple', '⇢ 후퇴')); left.append(legend, node('p', 'map-caption', scenario.map && scenario.map.caption || '설명용 예시 · 실제 위치 추적 없음', options), node('p', 'map-note', '화살표는 행동 방향입니다. 안전한 경로·정확한 기술 사거리·실제 적 위치를 나타내지 않습니다.'));
    (scenario.map && scenario.map.notes || []).forEach(note => left.append(node('p', 'map-note', note, options)));
    right.append(node('h4', '', '번호를 눌러 한 단계씩 확인'));
    items.forEach((step, index) => {
      const number = typeof step === 'string' ? index + 1 : step.number || index + 1, value = typeof step === 'string' ? step : step.text;
      const preset = catalog.directions && catalog.directions.presets.find(preset => preset.id === scenario.id);
      const methodKey = preset && preset.input.decision === 'RECALL' ? 'RECALL' : scenario.plan && scenario.plan.id;
      const method = preset && catalog.directions.methods[input.own_champion] && catalog.directions.methods[input.own_champion][methodKey];
      const bindings = number === 2 && typeof method === 'string' && value === method ? catalog.champions[input.own_champion].facts.filter(fact => method.includes(fact.name)).map(fact => ({ text: fact.name, champion: input.own_champion, slot: fact.slot })) : [];
      const item = node('li'); item.dataset.step = number; const button = node('button'); button.type = 'button';
      button.append(node('span', '', number), node('span', '', value, { ...options, bindings }));
      button.addEventListener('click', () => select(String(number))); item.append(button); steps.append(item);
    });
    right.append(steps);
    if (scenario.plan && scenario.plan.direction) right.append(node('p', 'map-note', scenario.plan.direction, options));
    zoom.addEventListener('click', () => {
      const dialog = document.getElementById('loading-map-dialog');
      const zoomMap = draw(scenario.map || {}, catalog, input, prefix + '-zoom-' + (++sequence), options), zoomControls = controls(select);
      activeZoom = { owner: prefix, map: zoomMap, controls: zoomControls };
      document.getElementById('zoom-map').replaceChildren(zoomMap); document.getElementById('zoom-step-controls').replaceChildren(zoomControls);
      document.getElementById('map-scale').value = '100'; document.getElementById('map-scale-value').textContent = '100%';
      const stage = document.getElementById('map-zoom-stage'); stage.dataset.zoom = '100'; stage.scrollTop = 0; stage.scrollLeft = 0;
      select(selected); dialog.showModal();
    });
    wrap.append(left, right); select(selected); return wrap;
  }
  function init() {
    const dialog = document.getElementById('loading-map-dialog');
    document.getElementById('map-close').addEventListener('click', () => dialog.close());
    dialog.addEventListener('close', () => { activeZoom = null; });
    document.getElementById('map-scale').addEventListener('input', event => { document.getElementById('map-zoom-stage').dataset.zoom = event.target.value; document.getElementById('map-scale-value').textContent = event.target.value + '%'; });
  }
  root.LoadingMap = { portrait, create, init };
})(window);

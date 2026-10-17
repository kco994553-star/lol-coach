/* Public, manual learning UI. The only data request is the local curated catalog. */
(function () {
  'use strict';

  const NS = 'http://www.w3.org/2000/svg';
  const roles = ['TOP', 'JUNGLE', 'MID', 'BOTTOM', 'SUPPORT'];
  const metricKeys = ['total_earned_difference', 'purchased_value_difference', 'current_gold'];
  const portraits = { Caitlyn: './direction-assets/Caitlyn.png', Fiora: './direction-assets/Fiora.png', Ornn: './direction-assets/Ornn.png' };
  const arrowStyles = {
    MOVE: { color: '#90d7ee', dash: null, label: '이동' },
    PRESSURE: { color: '#f3bf69', dash: '24 17', label: '압박' },
    RETREAT: { color: '#d3a4ee', dash: '5 17', label: '후퇴' }
  };
  let catalog;
  let input;
  let result;
  let activeScene = null;
  let selectedStep = window.matchMedia('(max-width: 640px)').matches ? '1' : 'ALL';
  const $ = id => document.getElementById(id);
  const clone = value => JSON.parse(JSON.stringify(value));

  function node(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined && text !== null) element.textContent = String(text);
    return element;
  }

  function svgNode(tag, attributes, text) {
    const element = document.createElementNS(NS, tag);
    Object.entries(attributes || {}).forEach(([key, value]) => {
      if (value !== undefined && value !== null) element.setAttribute(key, String(value));
    });
    if (text !== undefined) element.textContent = String(text);
    return element;
  }

  function text(id, value) { $(id).textContent = value == null ? '' : String(value); }

  function options(select, entries, value) {
    select.replaceChildren(...Object.entries(entries).map(([key, label]) => {
      const option = node('option', '', label);
      option.value = key;
      return option;
    }));
    select.value = value;
  }

  function list(id, items) {
    $(id).replaceChildren(...(items || []).map(item => node('li', '', typeof item === 'string' ? item : item.text)));
  }

  function message(value, isError) {
    text('app-message', value);
    $('app-message').classList.toggle('is-error', Boolean(isError));
  }

  function renderScenes() {
    $('scenes').replaceChildren(...catalog.presets.map((preset, index) => {
      const button = node('button', 'scene-card');
      button.type = 'button';
      button.id = 'scene-' + preset.id;
      button.dataset.scene = preset.id;
      button.setAttribute('aria-pressed', 'false');
      const number = node('span', 'scene-number', String(index + 1).padStart(2, '0'));
      number.setAttribute('aria-hidden', 'true');
      const copy = node('span', 'scene-text');
      copy.append(node('strong', '', preset.title), node('small', '', preset.description));
      button.append(number, copy);
      button.addEventListener('click', () => {
        input = clone(preset.input);
        activeScene = preset.id;
        renderForm();
        evaluate();
      });
      return button;
    }));
  }

  function renderForm() {
    document.querySelectorAll('#phase [data-phase]').forEach(button => {
      const selected = button.dataset.phase === input.phase;
      button.setAttribute('aria-selected', String(selected));
      button.tabIndex = selected ? 0 : -1;
    });
    options($('decision'), Object.fromEntries(catalog.decisions.filter(decision => decision.phase === input.phase).map(decision => [decision.id, decision.title])), input.decision);
    options($('champion'), Object.fromEntries(catalog.champions.map(champion => [champion.id, champion.name])), input.champion);
    options($('role'), catalog.labels.positions, input.role);
    options($('review-mode'), catalog.labels.review_modes, input.review_mode);
    $('side').value = input.side;
    $('economy-inputs').replaceChildren(...roles.map(role => {
      const label = node('label', 'economy-field');
      label.htmlFor = 'economy-' + role;
      label.append(node('span', '', catalog.labels.positions[role]));
      const select = node('select');
      select.id = 'economy-' + role;
      select.dataset.economyRole = role;
      select.setAttribute('aria-label', catalog.labels.positions[role] + ' 경제 상태');
      options(select, catalog.labels.economy, input.economy[role]);
      select.dataset.value = input.economy[role];
      label.append(select);
      return label;
    }));
    const decision = catalog.decisions.find(item => item.id === input.decision);
    $('condition-inputs').replaceChildren(...decision.condition_keys.map(key => {
      const condition = catalog.inputs.conditions.find(item => item.key === key);
      const label = node('label', '', condition.label);
      label.htmlFor = 'condition-' + key;
      const select = node('select');
      select.id = 'condition-' + key;
      select.dataset.condition = key;
      options(select, condition.options, input.conditions[key]);
      label.append(select);
      return label;
    }));
    metricKeys.forEach(key => { $('metric-' + key).value = input.metrics[key] == null ? '' : input.metrics[key]; });
    $('observed-at').value = input.metrics.observed_at || '';
    $('patch').value = input.patch || '';
    updateSceneSelection();
  }

  function updateSceneSelection() {
    document.querySelectorAll('[data-scene]').forEach(button => {
      button.setAttribute('aria-pressed', String(button.dataset.scene === activeScene));
    });
  }

  function evaluate() {
    try {
      result = window.DirectionEngine.evaluate(input, catalog);
      message('', false);
      renderResult();
      $('result').hidden = false;
      $('direction-app').dataset.planId = result.plan.id;
    } catch (error) {
      $('result').hidden = true;
      delete $('direction-app').dataset.planId;
      message(error.message || '입력 조건을 확인해 주세요.', true);
    }
  }

  function renderResult() {
    const plan = result.plan;
    $('main-plan').dataset.planId = plan.id;
    text('mode-label', catalog.labels.review_modes[input.review_mode]);
    text('champion-name', result.champion.name);
    $('champion-portrait').src = portraits[result.champion.id];
    $('champion-portrait').alt = result.champion.name + ' 초상화';
    const typeLabel = value => (catalog.labels.types && catalog.labels.types[value]) || value;
    text('champion-type', '일반 유형 · ' + [result.champion.primary_type, ...result.champion.secondary_types].map(typeLabel).join(' / '));
    text('current-role', plan.role);
    text('plan-title', plan.title);
    text('direction', plan.direction);
    $('plan-steps').replaceChildren(...plan.steps.map(step => {
      const item = node('li');
      item.dataset.step = step.number;
      const button = node('button', 'step-card-button');
      button.type = 'button';
      button.setAttribute('aria-label', step.number + '단계를 지도에 표시. ' + step.text);
      const number = node('span', 'step-badge', step.number);
      number.setAttribute('aria-hidden', 'true');
      const copy = node('span', 'step-copy', step.text);
      copy.append(node('span', 'selected-step-label', '지도에 표시 중'));
      button.append(number, copy);
      item.append(button);
      button.addEventListener('click', () => selectStep(String(step.number)));
      item.addEventListener('mouseenter', () => highlightStep(step.number));
      item.addEventListener('mouseleave', () => highlightStep(null));
      button.addEventListener('focus', () => highlightStep(step.number));
      button.addEventListener('blur', () => highlightStep(null));
      return item;
    }));
    list('plan-why', plan.why);
    list('plan-requirements', plan.requirements);
    text('alternative-title', plan.alternative.title);
    text('alternative-when', plan.alternative.when);
    list('alternative-steps', plan.alternative.steps);
    list('switch-when', plan.switch_when);
    renderMap($('map'), 'main');
    text('map-caption', result.map.caption);
    list('map-notes', result.map.notes);
    renderEconomy();
    renderEvidence();
    if ($('map-dialog').open) renderZoomMap();
    selectStep(selectedStep);
  }

  function selectStep(step) {
    selectedStep = step === 'ALL' || result.plan.steps.some(item => String(item.number) === step) ? step : 'ALL';
    document.querySelectorAll('[data-map-step]').forEach(button => {
      button.setAttribute('aria-pressed', String(button.dataset.mapStep === selectedStep));
    });
    document.querySelectorAll('#map, #map-detail').forEach(svg => {
      svg.dataset.activeStep = selectedStep;
    });
    document.querySelectorAll('#plan-steps > li').forEach(item => {
      const selected = item.dataset.step === selectedStep;
      item.classList.toggle('is-selected-step', selected);
      item.querySelector('button').setAttribute('aria-pressed', String(selected));
    });
    const label = selectedStep === 'ALL' ? '전체 방향을 함께 봅니다. 번호를 고르면 해당 단계만 표시합니다.' : selectedStep + '단계만 지도에 표시 중 · 같은 번호의 행동 카드를 확인하세요.';
    text('map-step-status', label);
    text('zoom-step-status', label);
  }

  function highlightStep(number) {
    document.querySelectorAll('#plan-steps [data-step], #map [data-step], #zoom-map [data-step]').forEach(element => {
      element.classList.toggle('is-step-active', number !== null && element.dataset.step === String(number));
    });
  }

  function renderEconomy() {
    $('economy-states').replaceChildren(...roles.map(role => {
      const state = result.economy.states[role];
      const chip = node('span', 'economy-state', catalog.labels.positions[role]);
      chip.dataset.state = state;
      chip.append(node('strong', '', catalog.labels.economy[state]));
      return chip;
    }));
    $('economy-metrics').replaceChildren(...result.economy.metrics.map(metric => {
      const card = node('article', 'metric-card');
      card.dataset.metric = metric.key;
      const value = metric.missing || metric.value === null ? '미입력' : Number(metric.value).toLocaleString('ko-KR') + ' ' + metric.unit;
      const observed = metric.observed_at ? '관찰 시각 · ' + metric.observed_at : '관찰 시각 · 미확인';
      card.append(node('h4', '', metric.label), node('strong', '', value), node('p', '', metric.source + ' / ' + observed), node('p', '', metric.limit));
      return card;
    }));
    text('economy-note', result.economy.note);
  }

  function renderEvidence() {
    const evidence = result.evidence;
    $('evidence').dataset.level = evidence.level;
    text('evidence-label', evidence.label);
    $('official-facts').replaceChildren(...evidence.official_facts.map(fact => {
      const article = node('article', 'fact-card');
      article.append(node('h4', '', '공식 사실 · ' + fact.slot + ' ' + fact.name), node('blockquote', '', fact.excerpt));
      const source = node('div', 'fact-source');
      source.append(node('span', '', '자료 버전 ' + fact.version));
      try {
        const url = new URL(fact.url);
        if (url.protocol === 'https:') {
          const link = node('a', '', '공식 원문 확인 ↗');
          link.href = url.href;
          link.target = '_blank';
          link.rel = 'noopener noreferrer';
          source.append(link);
        }
      } catch (_) { /* An invalid source is displayed as text, never as an executable URL. */ }
      article.append(source, node('code', 'fact-hash', 'URL · ' + fact.url), node('code', 'fact-hash', 'SHA-256 · ' + fact.sha256));
      return article;
    }));
    if (!evidence.official_facts.length) $('official-facts').append(node('p', 'small-copy', '이 장면에 연결된 공식 사실 자료가 없습니다.'));
    text('statistics-status', evidence.statistics.length ? '제공된 자료 ' + evidence.statistics.length + '개 · 아래 한계를 함께 확인하세요.' : '제공된 통계 없음 · 승률이나 효과를 추정하지 않습니다.');
    text('expert-status', evidence.expert_statements.length ? '제공된 발언 ' + evidence.expert_statements.length + '개 · 아래 한계를 함께 확인하세요.' : '제공된 전문가 발언 없음 · 전문가 승인으로 표시하지 않습니다.');
    list('evidence-limits', evidence.limits);
    $('asset-sources').replaceChildren(...(catalog.asset_sources || []).map(asset => {
      const article = node('article', 'asset-source');
      const name = node('h4', '', asset.id === 'map11.png' ? '소환사의 협곡 지도 · map11.png' : '챔피언 초상화 · ' + asset.id);
      article.append(name, node('p', 'small-copy', '자료 버전 ' + asset.source_build + ' · ' + asset.copyright_holder));
      const localAssets = ['map11.png', 'Caitlyn.png', 'Fiora.png', 'Ornn.png'];
      if (localAssets.includes(asset.id)) {
        const link = node('a', 'asset-link', '화면에 사용한 로컬 자료 보기 ↗');
        link.href = './direction-assets/' + asset.id;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        article.append(link);
      }
      article.append(node('code', 'fact-hash', '원본 URL · ' + asset.requested_url), node('code', 'fact-hash', 'SHA-256 · ' + asset.sha256), node('p', 'asset-license', asset.license_note));
      return article;
    }));
  }

  function point(value) { return { x: Number(value.x) * 10, y: Number(value.y) * 10 }; }
  function clamp(value, low, high) { return Math.min(high, Math.max(low, value)); }

  function renderMap(svg, prefix) {
    svg.replaceChildren();
    svg.append(svgNode('title', { id: prefix + '-map-title' }, '전술 설명용 예시 지도 · ' + result.plan.title));
    svg.append(svgNode('desc', { id: prefix + '-map-description' }, '선명한 파랑 테두리와 금색 강조는 내 시작 예시, 반투명 표시는 목표 배치입니다. 선택한 단계 번호는 행동 카드와 대응합니다. 화살표는 방향이며 안전한 경로 또는 사거리가 아닙니다.'));
    svg.setAttribute('aria-labelledby', prefix + '-map-title ' + prefix + '-map-description');
    svg.dataset.planId = result.plan.id;
    svg.dataset.activeStep = selectedStep;
    const defs = svgNode('defs');
    Object.entries(arrowStyles).forEach(([kind, style]) => {
      const marker = svgNode('marker', { id: prefix + '-arrow-' + kind, viewBox: '0 0 10 10', refX: '8', refY: '5', markerWidth: '3.5', markerHeight: '3.5', orient: 'auto-start-reverse' });
      marker.append(svgNode('path', { d: 'M 0 0 L 10 5 L 0 10 Z', fill: style.color }));
      defs.append(marker);
    });
    svg.append(defs, svgNode('image', { href: './direction-assets/map11.png', x: '0', y: '0', width: '1000', height: '1000', preserveAspectRatio: 'xMidYMid meet' }));
    svg.append(svgNode('rect', { x: '0', y: '0', width: '1000', height: '1000', fill: '#09141e', 'fill-opacity': '.18' }));

    result.map.landmarks.forEach(landmark => {
      const location = point(landmark);
      const group = svgNode('g', { class: 'map-step', 'data-landmark': landmark.id, 'data-step': landmark.step });
      const color = landmark.kind === 'OBJECTIVE' ? '#e3c081' : '#cedbc4';
      const labelY = clamp(location.y + (landmark.kind === 'TOWER' ? -79 : landmark.kind === 'VISION' ? -90 : 102), 34, 966);
      const labelX = clamp(location.x, 180, 820);
      group.append(svgNode('circle', { cx: location.x, cy: location.y, r: '16', fill: '#12202a', stroke: color, 'stroke-width': '4' }));
      group.append(svgNode('text', { x: labelX, y: labelY, class: 'map-label', 'text-anchor': 'middle' }, landmark.label));
      svg.append(group);
    });

    result.map.arrows.forEach(arrow => {
      const from = point(arrow.from);
      const to = point(arrow.to);
      const style = arrowStyles[arrow.kind];
      if (!style) return;
      const group = svgNode('g', { class: 'map-step', 'data-step': arrow.step, 'data-kind': arrow.kind });
      group.append(svgNode('title', {}, arrow.step + '단계 · ' + style.label + ' 방향 예시'));
      group.append(svgNode('path', { d: 'M ' + from.x + ' ' + from.y + ' L ' + to.x + ' ' + to.y, stroke: '#07121b', 'stroke-opacity': '.9', 'stroke-width': '21', fill: 'none', 'stroke-linecap': 'round' }));
      group.append(svgNode('path', { d: 'M ' + from.x + ' ' + from.y + ' L ' + to.x + ' ' + to.y, stroke: style.color, 'stroke-width': '11', 'stroke-dasharray': style.dash, fill: 'none', 'stroke-linecap': 'round', 'marker-end': 'url(#' + prefix + '-arrow-' + arrow.kind + ')' }));
      svg.append(group);
    });

    const badgeLocations = [];
    const portraitLocations = result.map.entities.flatMap(entity => [point(entity.start), ...(entity.target ? [point(entity.target)] : [])]);
    result.map.arrows.forEach(arrow => {
      const from = point(arrow.from);
      const to = point(arrow.to);
      const dx = to.x - from.x;
      const dy = to.y - from.y;
      const length = Math.hypot(dx, dy) || 1;
      const midpoint = { x: from.x + dx * .56, y: from.y + dy * .56 };
      const candidates = [64, -64, 94, -94].map(offset => ({
        x: clamp(midpoint.x - dy / length * offset, 32, 968),
        y: clamp(midpoint.y + dx / length * offset, 32, 968)
      }));
      const clearance = candidate => Math.min(...[...portraitLocations, ...badgeLocations].map(location => Math.hypot(location.x - candidate.x, location.y - candidate.y)));
      const location = candidates.find(candidate => clearance(candidate) >= 76) || candidates.sort((a, b) => clearance(b) - clearance(a))[0];
      const { x, y } = location;
      badgeLocations.push(location);
      const group = svgNode('g', { class: 'map-step', 'data-step': arrow.step, 'aria-label': arrow.step + '단계' });
      group.append(svgNode('circle', { cx: x, cy: y, r: '24', fill: '#f1e5c7', stroke: '#25323b', 'stroke-width': '4' }));
      group.append(svgNode('text', { x, y, class: 'step-number' }, arrow.step));
      svg.append(group);
    });
    result.map.entities.slice().sort((a, b) => Number(a.self) - Number(b.self)).forEach((entity, index) => {
      const start = point(entity.start);
      const enemy = entity.team === 'ENEMY';
      const color = enemy ? '#f08d8d' : '#80c4f5';
      const portrait = portraits[entity.champion];
      const name = (catalog.champions.find(champion => champion.id === entity.champion) || {}).name || entity.champion;
      if (entity.target) {
        const target = point(entity.target);
        const targetGroup = svgNode('g', { 'data-entity-target': entity.id });
        targetGroup.append(svgNode('title', {}, (entity.self ? '내' : name) + ' 목표 배치 · 전술 설명용 예시'));
        targetGroup.append(svgNode('circle', { cx: target.x, cy: target.y, r: '40', fill: color, 'fill-opacity': '.17', stroke: color, 'stroke-width': '5', 'stroke-dasharray': '10 8' }));
        if (portrait) {
          const clipId = prefix + '-target-' + index;
          const clip = svgNode('clipPath', { id: clipId });
          clip.append(svgNode('circle', { cx: target.x, cy: target.y, r: '34' }));
          defs.append(clip);
          targetGroup.append(svgNode('image', { href: portrait, x: target.x - 34, y: target.y - 34, width: '68', height: '68', opacity: '.35', 'clip-path': 'url(#' + clipId + ')' }));
        }
        const targetRight = target.x < 230 || (target.x < 770 && target.x >= start.x);
        const targetDirection = targetRight ? 1 : -1;
        targetGroup.append(svgNode('path', { d: 'M ' + (target.x + targetDirection * 41) + ' ' + target.y + ' L ' + (target.x + targetDirection * 53) + ' ' + target.y, stroke: color, 'stroke-opacity': '.7', 'stroke-width': '3', fill: 'none' }));
        targetGroup.append(svgNode('text', { x: target.x + targetDirection * 60, y: target.y + 9, 'text-anchor': targetRight ? 'start' : 'end', class: 'map-label entity-label' }, '목표 예시'));
        svg.append(targetGroup);
      }
      const group = svgNode('g', { 'data-entity': entity.id, 'data-team': entity.team, 'data-self': String(entity.self) });
      group.append(svgNode('title', {}, (entity.self ? '내 시작 예시 · ' : enemy ? '관측한 적 예시 · ' : '아군 예시 · ') + name + ' · 전술 설명용 예시'));
      if (entity.self) group.append(svgNode('circle', { cx: start.x, cy: start.y, r: '45', fill: '#152333', stroke: '#e3c081', 'stroke-width': '7' }));
      group.append(svgNode('circle', { cx: start.x, cy: start.y, r: '38', fill: '#172936', stroke: color, 'stroke-width': entity.self ? '7' : '6' }));
      if (portrait) {
        const clipId = prefix + '-portrait-' + index;
        const clip = svgNode('clipPath', { id: clipId });
        clip.append(svgNode('circle', { cx: start.x, cy: start.y, r: '32' }));
        defs.append(clip);
        group.append(svgNode('image', { href: portrait, x: start.x - 32, y: start.y - 32, width: '64', height: '64', 'clip-path': 'url(#' + clipId + ')' }));
      }
      if (entity.self) {
        const targetX = entity.target ? point(entity.target).x : start.x;
        const right = start.x < 230 || (start.x < 770 && targetX <= start.x);
        const direction = right ? 1 : -1;
        group.append(svgNode('path', { d: 'M ' + (start.x + direction * 46) + ' ' + start.y + ' L ' + (start.x + direction * 59) + ' ' + start.y, stroke: '#80c4f5', 'stroke-width': '4', fill: 'none' }));
        group.append(svgNode('text', { x: start.x + direction * 66, y: start.y + 9, 'text-anchor': right ? 'start' : 'end', class: 'map-label entity-label' }, '내 시작 예시'));
      } else {
        group.append(svgNode('text', { x: clamp(start.x, 110, 890), y: start.y > 860 ? start.y - 58 : start.y + 66, 'text-anchor': 'middle', class: 'map-label entity-label' }, (enemy ? '적' : '아군') + ' 예시'));
      }
      svg.append(group);
    });
  }

  function renderZoomMap() {
    const svg = svgNode('svg', { viewBox: '0 0 1000 1000', role: 'img', id: 'map-detail' });
    renderMap(svg, 'zoom');
    $('zoom-map').replaceChildren(svg);
    selectStep(selectedStep);
  }

  function bindEvents() {
    document.querySelectorAll('[data-map-step]').forEach(button => {
      button.addEventListener('click', () => selectStep(button.dataset.mapStep));
    });
    $('scenario-form').addEventListener('submit', event => event.preventDefault());
    $('scenario-form').addEventListener('change', event => {
      const field = event.target;
      if (!(field instanceof HTMLInputElement || field instanceof HTMLSelectElement)) return;
      activeScene = null;
      if (field.dataset.economyRole) {
        input.economy[field.dataset.economyRole] = field.value;
        field.dataset.value = field.value;
      } else if (field.dataset.condition) input.conditions[field.dataset.condition] = field.value;
      else if (metricKeys.includes(field.name)) input.metrics[field.name] = field.value.trim() === '' ? null : Number(field.value);
      else if (field.id === 'observed-at') input.metrics.observed_at = field.value.trim() || null;
      else if (field.id === 'patch') input.patch = field.value.trim() || null;
      else if (['decision', 'champion', 'role', 'side', 'review_mode'].includes(field.name)) {
        input[field.name] = field.value;
        if (field.id === 'decision') renderForm();
      }
      updateSceneSelection();
      evaluate();
    });
    const tabs = Array.from(document.querySelectorAll('#phase [data-phase]'));
    function choosePhase(button) {
      activeScene = null;
      input.phase = button.dataset.phase;
      input.decision = catalog.decisions.find(decision => decision.phase === input.phase).id;
      renderForm();
      evaluate();
    }
    tabs.forEach((button, index) => {
      button.addEventListener('click', () => choosePhase(button));
      button.addEventListener('keydown', event => {
        if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
        event.preventDefault();
        const next = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : (index + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
        choosePhase(tabs[next]);
        tabs[next].focus();
      });
    });
    $('map-zoom').addEventListener('click', () => {
      renderZoomMap();
      $('zoom-range').value = '100';
      text('zoom-value', '100%');
      $('map-zoom-stage').dataset.zoom = '100';
      $('map-zoom-stage').scrollTop = 0;
      $('map-zoom-stage').scrollLeft = 0;
      $('map-dialog').showModal();
    });
    $('map-close').addEventListener('click', () => $('map-dialog').close());
    $('map-dialog').addEventListener('click', event => { if (event.target === $('map-dialog')) $('map-dialog').close(); });
    $('map-dialog').addEventListener('close', () => $('map-zoom').focus());
    $('zoom-range').addEventListener('input', event => {
      $('map-zoom-stage').dataset.zoom = event.target.value;
      text('zoom-value', event.target.value + '%');
    });
  }

  async function init() {
    try {
      if (!window.DirectionEngine) throw new Error('학습 엔진을 불러오지 못했습니다. 페이지를 새로고침해 주세요.');
      const response = await fetch('./directions-data.json', { credentials: 'omit' });
      if (!response.ok) throw new Error('학습 장면을 불러오지 못했습니다. 페이지를 새로고침해 주세요.');
      catalog = await response.json();
      input = window.DirectionEngine.defaultInput(catalog);
      renderScenes();
      renderForm();
      bindEvents();
      if (window.matchMedia('(max-width: 640px)').matches) $('manual-settings').open = false;
      evaluate();
    } catch (error) {
      message(error.message || '학습 화면을 준비하지 못했습니다.', true);
    }
  }

  init();
})();

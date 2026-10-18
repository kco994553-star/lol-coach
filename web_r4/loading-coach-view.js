/* Consumer only: judgments, conditions and action selection come from report.coach. */
(function (root) {
  'use strict';
  let instance = 0;
  const metrics = [['PUSH', '밀기'], ['SHORT', '짧은 교환'], ['EXTENDED', '지속 교전'], ['ALLIN', '올인'], ['ATTRITION', '소모전']];
  const assessments = { ALLY: '우리 우세', ENEMY: '상대 우세', CONTESTED: '조건 경합', INSUFFICIENT: '근거 부족' };
  const risks = { LOSS_LIMIT: '손실 제한', BALANCED: '균형', OPPORTUNITY: '기회 추구' };
  const basis = { GUIDE_BASED: '가이드 원문 검토', DESIGN_HYPOTHESIS: 'AI 해석 가설', OFFICIAL_MECHANISM: '공식 기전' };
  const arr = value => Array.isArray(value) ? value : value == null || value === '' ? [] : [value];
  function plain(value) {
    if (value == null) return '';
    if (typeof value === 'boolean') return value ? '가능' : '불가';
    if (typeof value !== 'object') return String(value);
    return [value.label || value.text || value.name || value.goal || value.description || value.role || value.summary, value.reason].filter(Boolean).join(' · ');
  }
  function mount({ host, report, catalog, onChange }) {
    if (!host || typeof host.replaceChildren !== 'function') throw new TypeError('LoadingCoachView host is required');
    const prefix = 'coach-' + (++instance), state = { tab: 'lane', step: 1, zoom: false, scale: 100, busy: false, error: '' };
    let current = report, destroyed = false, request = 0, zoomOpener = null;
    let focusHint = null;
    function coach() { return current && current.coach || {}; }
    function format(value) {
      const text = plain(value), input = current && current.input || {};
      return root.SkillDisplay ? root.SkillDisplay.format(text, { champions: [...arr(input.allies), ...arr(input.enemies)].map(p => p.champion), own: input.own_champion }) : text;
    }
    function el(tag, text, cls) { const n = document.createElement(tag); if (text != null) n.textContent = format(text); if (cls) n.className = cls; return n; }
    function button(text, key, fn) { const n = el('button', text); n.type = 'button'; if (key) n.dataset.coachFocus = key; n.addEventListener('click', fn); return n; }
    function list(values, ordered) { const n = el(ordered ? 'ol' : 'ul', null, 'coach-list'); arr(values).filter(v => plain(v)).forEach(v => n.append(el('li', v))); return n; }
    function block(title, value, cls) { const n = el('div', null, cls || 'coach-block'); if (!arr(value).some(v => plain(v))) return n; n.append(el('h4', title), Array.isArray(value) ? list(value) : el('p', value)); return n; }
    function card(title) { const n = el('article', null, 'coach-card'); if (title) n.append(el('h3', title)); return n; }
    function details(key, title) { const n = el('details', null, 'coach-details'); n.id = prefix + '-' + key; n.append(el('summary', title)); return n; }
    function urlLink(text, url) { if (!/^https?:\/\//i.test(url || '')) return null; const n = el('a', text); n.href = url; n.target = '_blank'; n.rel = 'noopener noreferrer'; return n; }
    function scenario() {
      const supplied = coach().context?.assumptions?.scenario || current?.input?.scenario;
      return { standard: supplied?.standard || 'lane-standard-v1', overrides: { ...(supplied?.overrides || {}) } };
    }
    function change(patch) {
      if (state.busy || destroyed || typeof onChange !== 'function') return;
      const payload = { scenario: scenario(), period: coach().selected_period || 'LEVEL1', preference: coach().context?.preferences?.risk || 'BALANCED', ...patch };
      focusHint = document.activeElement?.dataset?.coachFocus || null;
      const seq = ++request; state.busy = true; state.error = ''; syncBusy();
      try {
        Promise.resolve(onChange(payload)).then(next => {
          if (destroyed || seq !== request) return;
          state.busy = false;
          if (next) { current = next; render(); } else syncBusy();
        }, error => { if (destroyed || seq !== request) return; state.busy = false; state.error = error?.message || '비교를 바꾸지 못했습니다. 다시 시도해 주세요.'; render(); });
      } catch (error) { state.busy = false; state.error = error?.message || '비교를 바꾸지 못했습니다.'; render(); }
    }
    function syncBusy() {
      host.setAttribute('aria-busy', String(state.busy));
      host.querySelectorAll('[data-coach-change]').forEach(n => { n.disabled = state.busy || typeof onChange !== 'function'; });
      const n = host.querySelector('.coach-live'); if (n) n.textContent = state.busy ? '비교 갱신 중' : state.error;
    }
    function why(ids, key, title) {
      const c = coach(), evidence = c.evidence || {}, claims = arr(evidence.claims).filter(claim => arr(ids).includes(claim.id));
      const wrap = details('why-' + key, title || '왜? · 출처와 적용 조건');
      wrap.append(el('p', '가이드 원문 검토는 인용·적용 범위의 확인입니다. AI 해석 가설은 원문에서 확장한 설명이며, 실제 효과 검증과 구분합니다.', 'coach-muted'));
      if (!claims.length) wrap.append(el('p', '이 항목에 연결된 주장 근거가 아직 없습니다.', 'coach-muted'));
      claims.forEach((claim, index) => {
        const section = el('section', null, 'coach-claim');
        section.append(el('span', basis[claim.basis] || '근거 범위 미확인', 'coach-badge'), el('p', claim.text));
        if (claim.review) section.append(block('검토 범위', claim.review==='SOURCE_SCOPE_CHECKED_CONDITIONAL'?'원문과 적용 범위 확인 · 실전 효과 미검증':claim.review));
        section.append(block('적용 조건', claim.conditions), block('반례 · 적용을 멈출 조건', claim.counterexamples), block('패치 한계', claim.patch_limits));
        arr(evidence.sources).filter(source => arr(claim.source_ids).includes(source.id)).forEach(source => {
          const quote = el('div', null, 'coach-source'), link = urlLink(source.title || '원문 보기 ↗', source.url);
          quote.append(link || el('p', source.title || '출처 URL 미확인'));
          const expertise=typeof source.expertise==='string'?source.expertise:[source.expertise?.self_claimed,source.expertise?.evidence,source.expertise?.details,source.expertise?.verified_evidence,typeof source.expertise?.verified==='string'?source.expertise.verified:null].filter(Boolean).join(' · ');
          quote.append(el('p',[source.author,'작성·수정일: '+(source.date||'미확인'),'공략 표기 패치: '+(source.patch||'미확인')].filter(Boolean).join(' · '),'coach-muted'));
          if(expertise)quote.append(block('작성자·전문성 확인 범위',expertise));
          if(source.date_note)quote.append(block('날짜 확인 한계',source.date_note));
          if(arr(source.limits).length)quote.append(block('출처 한계',source.limits));
          arr(source.excerpts).forEach(excerpt => { const raw=el('blockquote');raw.textContent=excerpt.text;quote.append(raw); if (excerpt.locator) quote.append(el('p', excerpt.locator, 'coach-muted')); });
          section.append(quote);
        });
        const trace = details('claim-trace-' + key + '-' + index, '자료 식별 · Trace');
        const pre = el('pre'); pre.textContent = JSON.stringify({ id: claim.id, basis: claim.basis, review: claim.review, sources: arr(evidence.sources).filter(s => arr(claim.source_ids).includes(s.id)).map(s => ({ id: s.id, url: s.url, excerpts: arr(s.excerpts).map(e => ({ id: e.id, sha256: e.sha256 })) })) }, null, 2); trace.append(pre); section.append(trace); wrap.append(section);
      });
      if (/^[ABCD]$/.test(c.matchup_id)) { const a = el('a', '같은 근거로 학습하기 →'); a.href = './directions.html#coach-lesson-' + c.matchup_id; wrap.append(a); }
      return wrap;
    }
    function conditions() {
      const c = coach(), wrap = details('conditions', '상황 바꾸기');
      wrap.append(el('p', '가상의 조건을 바꿔 비교합니다. 현재 게임에서 관측한 정보가 아닙니다.', 'coach-muted'));
      const fields = el('div', null, 'coach-controls');
      arr(c.exceptions).forEach(def => {
        if (!def.id || !def.options || typeof def.options !== 'object') return;
        const label = el('label'), select = el('select'); select.id = prefix + '-condition-' + def.id; select.dataset.coachFocus = 'condition-' + def.id; select.dataset.coachChange = '';
        Object.entries(def.options).forEach(([value, text]) => { const option = el('option', text); option.value = value; select.append(option); });
        select.value = def.value; select.addEventListener('change', () => { const next = scenario(); next.overrides[def.id] = select.value; change({ scenario: next }); });
        label.append(el('span', def.label), select); fields.append(label);
      });
      const reset=button('기본 비교로 되돌리기','reset-scenario',()=>change({scenario:{standard:'lane-standard-v1',overrides:{}}}));reset.dataset.coachChange='';wrap.append(reset);
      wrap.append(fields, block(c.context?.assumptions?.label || '표준 비교 가정', c.context?.assumptions?.details), block('패치 · 자료 범위', [c.context?.patch?.label, ...arr(c.context?.patch?.limits)].filter(Boolean)));
      return wrap;
    }
    function preferences() {
      const c = coach(), field = el('fieldset', null, 'coach-preferences'); field.append(el('legend', '어떤 비용을 먼저 감수할까?'));
      const controls = el('div', null, 'coach-risk-options'); Object.entries(risks).forEach(([value, text]) => {
        const b = button(text, 'risk-' + value, () => change({ preference: value })); b.dataset.coachChange = ''; b.setAttribute('aria-pressed', String((c.context?.preferences?.risk || 'BALANCED') === value)); controls.append(b);
      });
      const chosen=arr(c.actions).find(a=>a.id===c.selection?.id), alternative=arr(c.actions).find(a=>a.id!==chosen?.id&&a.feasible==='POSSIBLE');
      const comparison=el('div',null,'coach-choice-comparison');
      [[chosen,'기본 선택'],[alternative,'가능한 대안']].forEach(([action,title])=>{if(!action)return;const box=el('section',null,'coach-choice');box.append(el('h4',title+' · '+action.label),block('얻을 것',action.goal),block('비용',action.costs),block('성립 조건',action.requirements),block('중단',action.abort));comparison.append(box);});
      field.append(comparison);
      field.append(controls, el('p', c.selection?.reason || '성향은 가능한 행동 후보의 선택에만 적용됩니다.', 'coach-muted'), el('p', '성향을 바꿔도 매치업 우열·실행 조건·근거는 바뀌지 않습니다.', 'coach-muted'));
      return field;
    }
    function matrix() {
      const c = coach(), wrap = el('div', null, 'coach-matrix-scroll'); wrap.tabIndex = 0; wrap.dataset.coachScroll = 'matrix'; wrap.setAttribute('role', 'region'); wrap.setAttribute('aria-label', '구간별 비교표 · 좌우로 스크롤');
      const table = el('table', null, 'coach-matrix'), caption = el('caption', '동일한 표준 조건의 구간별 비교 · 실제 시간이나 승률이 아닙니다.'); table.append(caption);
      const head = el('thead'), tr = el('tr'); tr.append(el('th', '구간')); metrics.forEach(([, label]) => { const th = el('th', label); th.scope = 'col'; tr.append(th); }); head.append(tr); table.append(head);
      const body = el('tbody'); arr(c.periods).forEach(row => { const r = el('tr'); r.dataset.selected = String(row.id === c.selected_period); const th = el('th'); th.scope = 'row'; const b = button(row.label, 'period-' + row.id, () => change({ period: row.id })); b.dataset.coachChange = ''; b.setAttribute('aria-pressed', String(row.id === c.selected_period)); th.append(b); r.append(th); metrics.forEach(([key]) => { const metric = row.metrics?.[key] || {}, td = el('td', assessments[metric.assessment] || assessments.INSUFFICIENT); td.dataset.assessment = metric.assessment || 'INSUFFICIENT'; if (metric.scope || metric.reason) td.title = format([metric.scope, metric.reason].filter(Boolean).join(' · ')); r.append(td); }); body.append(r); }); table.append(body); wrap.append(table); return wrap;
    }
    function growth() {
      const wrap = el('div', null, 'coach-growth'); arr(coach().growth).forEach(event => {
        const b = button(event.label, 'growth-' + event.id, () => change({ period: event.id })); b.dataset.coachChange = ''; b.setAttribute('aria-pressed', String(event.id === coach().selected_period)); wrap.append(b);
        if (event.id === coach().selected_period) { const card = el('div', null, 'coach-growth-detail'); card.append(block('변화가 생기는 조건', event.trigger), block('무엇이 달라지나', event.change), block('변화 전', event.before), block('변화 후', event.after), block('상대에게 남은 강점', event.remaining_strength), block('위치에 따른 응징 위험', event.positional_punish_risk==='INCREASED_CONDITIONAL'?'조건부 증가': '미확인'), block('예외', event.exceptions)); if (event.global_reversal != null) card.append(block('전체 구도 역전', typeof event.global_reversal === 'boolean' ? (event.global_reversal ? '근거가 제시된 범위에서 역전' : '전체 구도 역전으로 해석하지 않습니다.') : event.global_reversal==='UNDETERMINED'?'미확인':event.global_reversal)); card.append(why(event.claim_ids, 'growth-' + event.id)); wrap.append(card); }
      }); return wrap;
    }
    function selected() {
      const c = coach(), row = c.selected || arr(c.periods).find(p => p.id === c.selected_period) || {}, wrap = card(row.label || '선택한 구간');
      wrap.append(block('이유', row.reason), block('지금의 행동', row.action), block('예외', row.exception));
      const grid = el('div', null, 'coach-metric-notes'); metrics.forEach(([key, label]) => { const metric = row.metrics?.[key]; if (!metric) return; const section = el('section'); section.append(el('h4', label + ' · ' + (assessments[metric.assessment] || assessments.INSUFFICIENT)), el('p', metric.scope, 'coach-muted'), el('p', metric.reason), why(metric.claim_ids, 'metric-' + key)); grid.append(section); });
      const more = details('selected-metrics', '다섯 비교의 이유 · 적용 범위'); more.append(grid); wrap.append(more);
      if (arr(row.engagements).length) { const types = details('engagements', '교전 방식별 시작 · 순서 · 종료'); arr(row.engagements).forEach((e, index) => { const n = card(e.label); n.append(el('p', e.advantage_label || assessments[e.advantage] || '근거 부족'), block('이유', e.reason), block('시작', e.start), block('순서', e.order), block('종료', e.end), block('이어갈 조건', e.continue_if), block('예외', e.exceptions), block('허용 범위', e.allowed), block('처치', e.kill==='UNDETERMINED'?'판정하지 않음':e.kill), block('추격', e.chase==='UNDETERMINED'?'판정하지 않음':e.chase)); types.append(n); }); wrap.append(types); }
      return wrap;
    }
    function stepControls(where) {
      const group = el('div', null, 'coach-step-controls'); group.setAttribute('role', 'group'); group.setAttribute('aria-label', '같은 실행의 단계 선택');
      arr(coach().diagram?.steps).forEach((step, index) => { const number = Number(step.number) || index + 1, b = button(String(number) + '단계', where + '-step-' + number, () => selectStep(number)); b.dataset.coachStep = number; b.setAttribute('aria-pressed', String(state.step === number)); b.addEventListener('keydown', event => { if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return; event.preventDefault(); const buttons = Array.from(group.children), at = buttons.indexOf(b), target = event.key === 'Home' ? 0 : event.key === 'End' ? buttons.length - 1 : (at + (event.key === 'ArrowRight' ? 1 : -1) + buttons.length) % buttons.length; buttons[target].click(); buttons[target].focus(); }); group.append(b); }); return group;
    }
    function selectStep(number) { state.step = number; syncSteps(); }
    function syncSteps() {
      const steps = arr(coach().diagram?.steps), step = steps.find(s => Number(s.number) === state.step) || steps[0];
      host.querySelectorAll('[data-coach-step]').forEach(n => { const selected = Number(n.dataset.coachStep) === state.step; if (n.tagName === 'BUTTON') n.setAttribute('aria-pressed', String(selected)); else n.dataset.active = String(selected); });
      host.querySelectorAll('.coach-step-copy').forEach(n => { n.textContent = step ? format(String(step.number) + '. ' + step.text) : ''; });
      host.querySelectorAll('.coach-line').forEach(n => { n.dataset.step = String(state.step); });
    }
    function lineDiagram(zoom) {
      const c = coach(), d = c.diagram || {}, wrap = el('div', null, 'coach-line-wrap');
      if (!d.supported || d.kind !== 'LINE') { wrap.append(el('p', '현재 조건에 연결된 라인 도식이 없습니다.', 'coach-muted')); return wrap; }
      const line = el('div', null, 'coach-line'); line.dataset.plan = d.plan_id || ''; line.dataset.step = state.step; line.setAttribute('role', 'img'); line.setAttribute('aria-label', '선택된 웨이브 계획의 상징 도식. 적 위치는 모두 가상이며 실제 거리·사거리·시간을 나타내지 않습니다.');
      const terrain = el('div', null, 'coach-lane-track'); line.append(terrain, el('span', '아군 방향', 'coach-line-home'), el('span', '상대 방향', 'coach-line-away'));
      const symbol = el('span', ({ SLOW_PUSH: '→', FAST_PUSH: '⇉', CRASH: '→│', TRIM_RECEIVE: '←', TOWER_CS: '│', RETURNING: '⇇', FREEZE: '↔', CHECK_WAVE: '?' })[d.plan_id] || '?', 'coach-wave-symbol'); symbol.setAttribute('aria-hidden', 'true'); line.append(symbol);
      const geometry = {
        SLOW_PUSH: [34, 43, 54, 63], FAST_PUSH: [36, 45, 57, 66], CRASH: [51, 61, 74, 83], TRIM_RECEIVE: [24, 34, 45, 55], TOWER_CS: [17, 26, 37, 46], RETURNING: [30, 40, 54, 64], FREEZE: [24, 33, 44, 53], CHECK_WAVE: [35, 44, 56, 65]
      }[d.plan_id] || [35, 44, 56, 65];
      geometry.forEach((x, i) => { const group = el('span', '● ● ●', 'coach-minions ' + (i < 2 ? 'coach-minions-ally' : 'coach-minions-enemy')); group.style.left = x + '%'; group.style.top = (i % 2 ? 57 : 44) + '%'; group.setAttribute('aria-hidden', 'true'); line.append(group); });
      const own = d.own || current?.input?.own_champion;
      [['ALLY', Array.from(new Set([own, ...arr(d.allies)].filter(Boolean))), 22], ['ENEMY', Array.from(new Set(arr(d.enemies))), 78]].forEach(([team, ids, x]) => { ids.forEach((id, i) => { const unit = el('span', null, 'coach-line-unit ' + (team === 'ALLY' ? 'coach-line-ally' : 'coach-line-enemy')); unit.style.left = (ids.length > 2 ? 15 + i * 70 / (ids.length - 1) : x) + '%'; unit.style.top = (ids.length > 2 ? team === 'ALLY' ? 12 : 78 : ids.length > 1 ? i % 2 ? 78 : 12 : 12) + '%'; const champion = catalog?.champions?.[id]; if (root.LoadingMap?.portrait) unit.append(root.LoadingMap.portrait(champion, id === own)); else unit.append(el('span', champion?.name?.slice(0, 1) || '?')); unit.title = (champion?.name || id) + (team === 'ENEMY' ? ' · 가상 적 위치' : ' · 설명용 아군 위치'); line.append(unit); }); });
      const steps = arr(d.steps); steps.forEach((s, index) => { const n = el('span', String(s.number || index + 1), 'coach-line-number'); n.style.left = (28 + index * 22) + '%'; n.dataset.coachStep = s.number || index + 1; n.setAttribute('aria-hidden', 'true'); line.append(n); });
      let touchX = null; line.addEventListener('pointerdown', event => { touchX = event.clientX; }); line.addEventListener('pointerup', event => { if (touchX == null || Math.abs(event.clientX - touchX) < 45) return; const at = steps.findIndex(s => Number(s.number) === state.step), next = Math.max(0, Math.min(steps.length - 1, at + (event.clientX < touchX ? 1 : -1))); if (steps[next]) selectStep(Number(steps[next].number)); touchX = null; });
      wrap.append(line, el('p', '초상화: 공식 자료 · 미니언: 상징 묶음 · 모든 적 위치는 가상 예시', 'coach-muted'), stepControls(zoom ? 'zoom' : 'line'), el('p', '', 'coach-step-copy'));
      return wrap;
    }
    function wave() {
      const c = coach(), w = c.wave || {}, plan = w.selected, section = card('웨이브 · 실행');
      section.append(block('밀 수 있는가', w.can_push), block('밀어야 하는가', w.should_push));
      if (!plan) { section.append(el('p', '현재 조건에서 연결된 실행 계획이 없습니다.', 'coach-muted')); return section; }
      section.append(el('p','웨이브 절차 · 조건부 설계 가설','coach-badge'),el('h4', plan.label), block('목표', plan.goal));
      const steps = el('ol', null, 'coach-execution-steps'); arr(c.diagram?.supported ? c.diagram.steps : plan.steps).forEach((step, index) => { const li = el('li'), number = Number(step.number) || index + 1; li.dataset.coachStep = number; const b = button(step.text, 'card-step-' + number, () => selectStep(number)); b.dataset.coachStep = number; li.append(b); steps.append(li); }); section.append(steps);
      section.append(lineDiagram(false));
      if (c.diagram?.supported) { const b = button('도식 크게 보기', 'open-zoom', () => openZoom(b)); section.append(b); }
      const procedure = details('wave-procedure', '시작 · 처리 · 남길 자원 · 중단과 다음 행동');
      [['시작 조건', 'start'], ['처리 방식', 'processing'], ['기술 사용', 'skills'], ['남길 자원', 'reserve'], ['완료 확인', 'complete'], ['중단 조건', 'abort'], ['다음 행동', 'next'], ['상대의 응징', 'punishment'], ['이득 전환', 'conversion'], ['비용', 'costs']].forEach(([label, key]) => procedure.append(block(label, plan[key])));
      section.append(procedure, why(plan.claim_ids, 'wave'));
      const alternatives = details('wave-alternatives', '다른 웨이브 계획의 지원 범위'); arr(w.plans).forEach(p => { alternatives.append(block(p.label || '계획', [p.goal, p.reason, p.feasible === 'UNKNOWN' ? '실행 여건 미확인' : p.feasible === 'IMPOSSIBLE' ? '현재 조건에서 실행 불가' : ''].filter(Boolean))); }); section.append(alternatives);
      return section;
    }
    function trade() {
      const t = coach().trade || {}, section = card('교환 길이 · 상대의 남은 대응'); section.append(block('실제 매치업 우열', t.actual_advantage));
      [['ours', '우리의 선호'], ['theirs', '상대의 가능한 선호']].forEach(([key, title]) => { const side = t[key] || {}, n = el('section', null, 'coach-trade-side'); n.append(el('h4', title + (side.label ? ' · ' + side.label : '')), block('이유', side.reason)); const d = details('trade-' + key, '시작 · 공격 순서 · 종료 조건'); [['시작', 'start'], ['공격 순서', 'order'], ['종료', 'end'], ['이어갈 조건', 'continue_if'], ['대안', 'alternative']].forEach(([label, field]) => d.append(block(label, side[field]))); n.append(d); section.append(n); }); return section;
    }
    function sustain() {
      const s = coach().sustain || {}, section = card('유지력 · 피해를 버티는 방식'); section.append(el('p', s.summary));
      arr(s.actors).forEach(actor => { const d = details('sustain-' + actor.champion, actor.name || catalog?.champions?.[actor.champion]?.name || '각 챔피언'); [['교전 중 회복', 'in_fight_heal'], ['교환 사이 회복', 'between_trade'], ['피해 방지 · 보호막', 'shield'], ['자원', 'resources'], ['수급 · 행동 공백', 'downtime'], ['위험', 'risks']].forEach(([label, key]) => d.append(block(label, actor[key]))); section.append(d); }); section.append(block('재정비', s.reset), block('한계', s.limits)); return section;
    }
    function lane() {
      const n = el('div', null, 'coach-lane-panel'); n.append(matrix(), growth(), selected(), preferences()); const grid = el('div', null, 'coach-execution-grid'); grid.append(wave(), trade(), sustain()); n.append(grid);
      if (arr(coach().actions).length) { const d = details('actions', '행동 후보 · 비용과 실행 조건'); arr(coach().actions).forEach(action => { const a = card(action.label); a.append(el('p', ({ POSSIBLE: '조건 내 실행 후보', UNKNOWN: '실행 여건 미확인', IMPOSSIBLE: '현재 조건에서 실행 불가' })[action.feasible] || '실행 여건 미확인', 'coach-badge'), block('목표', action.goal), block('필요 조건', action.requirements), block('비용', action.costs), block('중단', action.abort), block('대안', action.alternative), why(action.claim_ids, 'action-' + action.id)); d.append(a); }); n.append(d); } return n;
    }
    function operations() {
      const g = current?.gameplan || {}, n = card('운영 · 다음 이득으로 연결');
      [['기본 계획', 'base'], ['준비', 'prepare'], ['대안', 'fallback'], ['전환 조건', 'switch_when'], ['사이드와 합류', 'side_vs_group'], ['오브젝트', 'objectives'], ['이득 전환', 'conversion']].forEach(([label, key]) => n.append(block(label, g[key])));
      arr(g.stages).forEach(stage => { const section = el('section'); section.append(block(stage.label || stage.stage || '단계', stage.role), block('조건', stage.conditions)); n.append(section); }); return n;
    }
    function fight() {
      const f = current?.teamfight || {}, n = card('한타 · 내 역할과 전환');
      [['내 역할', 'role'], ['전투 전 배치', 'setup'], ['행동 순서', 'actions'], ['전환 조건', 'switch_when'], ['이탈', 'exit'], ['전투 후', 'after']].forEach(([label, key]) => n.append(block(label, f[key])));
      if (f.map && root.LoadingMap?.create && current.input) { const d = details('fight-map', '전체 지도 · 실제 픽의 역할 배치 예시'); try { const steps = arr(f.actions).slice(0, 3).map((text, i) => ({ number: i + 1, text: plain(text) })); d.append(root.LoadingMap.create({ map: f.map, plan: { steps } }, catalog, current.input)); n.append(d); } catch (_) { d.append(el('p', '이 보고서의 지도 표시는 지원되지 않습니다.', 'coach-muted')); n.append(d); } }
      return n;
    }
    function officialFacts() {
      const facts = arr(coach().evidence?.official_facts), d = details('official-facts', '공식 기전 · 비교에 연결된 사실');
      if (!facts.length) return el('div');
      facts.forEach((fact, index) => {
        const section = el('section', null, 'coach-claim');
        const label = root.SkillDisplay?.factLabel ? root.SkillDisplay.factLabel(fact.champion, fact) : fact.name;
        section.append(el('h4', label), el('p', fact.text));
        const link = urlLink('공식 출처 ↗', fact.url); if (link) section.append(link);
        const trace = details('official-trace-' + index, '자료 식별 · Trace'), pre = el('pre'); pre.textContent = JSON.stringify({ id: fact.id, sha256: fact.sha256 }, null, 2); trace.append(pre); section.append(trace); d.append(section);
      }); return d;
    }
    function lesson() {
      const c = coach(), l = c.lesson; if (!l) return el('div'); const d = details('lesson', '한 가지 확인 · 같은 지식으로 학습'); d.append(el('p', [l.role, l.type, l.plan].filter(Boolean).join(' → '), 'coach-muted'), el('h3', l.question));
      arr(l.options).forEach((option, index) => { const b = button(option, 'lesson-' + index, () => { const answer = d.querySelector('.coach-answer'); answer.hidden = false; answer.textContent = format((index === l.answer ? '맞습니다. ' : '이 선택을 다시 살펴보세요. ') + plain(l.explanation)); }); d.append(b); }); const answer = el('p', '', 'coach-answer'); answer.setAttribute('role', 'status'); answer.hidden = true; d.append(answer);
      if (/^[ABCD]$/.test(c.matchup_id)) { const a = el('a', '학습 페이지에서 계속 →'); a.href = './directions.html#coach-lesson-' + c.matchup_id; d.append(a); } return d;
    }
    function openZoom(opener) { zoomOpener = opener; state.zoom = true; const d = host.querySelector('.coach-zoom'); if (d && !d.open) { d.showModal(); d.querySelector('button')?.focus(); } }
    function zoomDialog() {
      const d = el('dialog', null, 'coach-zoom'); d.id = prefix + '-zoom'; d.setAttribute('aria-labelledby', prefix + '-zoom-title');
      const header = el('div', null, 'coach-zoom-header'), h = el('h2', '웨이브 실행 · 크게 보기'); h.id = prefix + '-zoom-title'; const close = button('닫기', 'close-zoom', () => d.close()); header.append(h, close); d.append(header);
      const label = el('label', null, 'coach-scale'), range = el('input'), value = el('output', state.scale + '%'); range.type = 'range'; range.min = '100'; range.max = '200'; range.step = '25'; range.value = state.scale; range.setAttribute('aria-label', '도식 확대'); label.append(el('span', '확대'), range, value); d.append(label);
      const stage = el('div', null, 'coach-zoom-stage'), diagram = lineDiagram(true); stage.append(diagram); d.append(stage); diagram.style.width = state.scale + '%'; range.addEventListener('input', () => { state.scale = Number(range.value); value.textContent = state.scale + '%'; diagram.style.width = state.scale + '%'; });
      d.addEventListener('close', () => { state.zoom = false; const opener = zoomOpener?.isConnected ? zoomOpener : host.querySelector('[data-coach-focus="open-zoom"]'); opener?.focus({ preventScroll: true }); }); return d;
    }
    function render() {
      if (destroyed) return;
      const open = new Set(Array.from(host.querySelectorAll('details[open]'), n => n.id));
      const focused = focusHint || (host.contains(document.activeElement) ? document.activeElement?.dataset?.coachFocus : null); focusHint = null;
      const scroll = Array.from(host.querySelectorAll('[data-coach-scroll]'), n => [n.dataset.coachScroll, n.scrollLeft, n.scrollTop]);
      const pageX = root.scrollX, pageY = root.scrollY;
      const c = coach(), container = el('section', null, 'loading-coach'); container.id = prefix;container.dataset.matchup=c.matchup_id||'UNSUPPORTED';container.dataset.selectedAction=c.selection?.id||'';container.dataset.period=c.selected_period||''; container.setAttribute('aria-label', '로딩 코치 · 표준 비교');
      const hero = el('div', null, 'coach-overview'), eyebrow = el('p', '표준 조건으로 먼저 보는 계획', 'coach-eyebrow'); hero.append(eyebrow, el('h2', c.title || '로딩 코치'));
      hero.append(el('p', c.summary?.our_plan || '현재 보고서에 연결된 비교 계획이 없습니다.', 'coach-main-plan'));
      const overview = el('dl', null, 'coach-overview-facts'); [['상대 계획', c.summary?.enemy_plan], ['강한 구간', c.summary?.strong_phase], ['내 역할', c.summary?.role], ['라인전 기본',c.summary?.lane], ['한타 핵심',c.summary?.fight]].forEach(([title, value]) => { if (plain(value)) overview.append(el('dt', title), el('dd', value)); }); hero.append(overview);
      if (arr(c.summary?.exceptions).length) hero.append(block('먼저 볼 예외', arr(c.summary.exceptions).slice(0, 3), 'coach-summary-exceptions'));
      hero.append(el('p', [c.context?.observations?.label, c.context?.assumptions?.label].filter(Boolean).join(' · '), 'coach-muted')); container.append(hero, conditions());
      const deep = el('section', null, 'coach-execution'), tabs = el('div', null, 'coach-tabs'); deep.setAttribute('aria-label', '구간별 실행'); tabs.setAttribute('role', 'tablist'); tabs.setAttribute('aria-label', '실행 영역');
      [['lane', '라인'], ['operations', '운영'], ['fight', '한타']].forEach(([key, label]) => { const b = button(label, 'tab-' + key, () => { state.tab = key; render(); }); b.id = prefix + '-tab-' + key; b.setAttribute('role', 'tab'); b.setAttribute('aria-selected', String(state.tab === key)); b.setAttribute('aria-controls', prefix + '-panel'); b.tabIndex = state.tab === key ? 0 : -1; b.addEventListener('keydown', event => { const keys = ['lane', 'operations', 'fight']; if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return; event.preventDefault(); const at = keys.indexOf(key), next = event.key === 'Home' ? 0 : event.key === 'End' ? 2 : (at + (event.key === 'ArrowRight' ? 1 : -1) + 3) % 3; state.tab = keys[next]; render(); host.querySelector('[data-coach-focus="tab-' + state.tab + '"]')?.focus({ preventScroll: true }); }); tabs.append(b); });
      const panel = el('div', null, 'coach-panel'); panel.id = prefix + '-panel'; panel.setAttribute('role', 'tabpanel'); panel.setAttribute('aria-labelledby', prefix + '-tab-' + state.tab); panel.append(state.tab === 'lane' ? lane() : state.tab === 'operations' ? operations() : fight()); deep.append(tabs, panel); container.append(deep, officialFacts(), lesson());
      const trace = details('trace', '자료 범위 · 개발 Trace'); trace.append(block('자료 한계', c.evidence?.limits), block('연결된 질문', c.evidence?.questions)); const pre = el('pre'); pre.textContent = JSON.stringify({ schema_version: c.schema_version, supported: c.supported, matchup_id: c.matchup_id, selected_period: c.selected_period, selection: c.selection, claims: c.evidence?.claim_ids }, null, 2); trace.append(pre); container.append(trace);
      const live = el('p', state.error, 'coach-live'); live.setAttribute('role', 'status'); live.setAttribute('aria-live', 'polite'); container.append(live, zoomDialog());
      host.replaceChildren(container); open.forEach(id => { const n = document.getElementById(id); if (n && host.contains(n)) n.open = true; });
      scroll.forEach(([key, left, top]) => { const n = host.querySelector('[data-coach-scroll="' + key + '"]'); if (n) { n.scrollLeft = left; n.scrollTop = top; } });
      if (focused) Array.from(host.querySelectorAll('[data-coach-focus]')).find(n => n.dataset.coachFocus === focused)?.focus({ preventScroll: true });
      if (state.zoom) { const d = host.querySelector('.coach-zoom'); if (d && !d.open) d.showModal(); }
      syncSteps(); syncBusy(); if (Number.isFinite(pageY) && typeof root.scrollTo === 'function') root.scrollTo(pageX, pageY);
    }
    render();
    return { update(next) { if (!destroyed) { current = next; render(); } }, setPanel(panel) { if (['lane','operations','fight'].includes(panel)) { state.tab=panel; render(); } }, destroy() { destroyed = true; request++; host.replaceChildren(); host.removeAttribute('aria-busy'); } };
  }
  root.LoadingCoachView = Object.freeze({ mount });
})(typeof window !== 'undefined' ? window : globalThis);

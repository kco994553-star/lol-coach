/* Consumer only: judgments, conditions and action selection come from report.coach. */
(function (root) {
  'use strict';
  let instance = 0;
  const metrics = [['PUSH', '밀기'], ['SHORT', '짧은 교환'], ['EXTENDED', '지속 교전'], ['ALLIN', '올인'], ['ATTRITION', '소모전']];
  const assessments = { ALLY: '우리 우세', ENEMY: '상대 우세', CONTESTED: '조건 경합', INSUFFICIENT: '근거 부족' };
  const risks = { LOSS_LIMIT: '손실 제한', BALANCED: '균형', OPPORTUNITY: '기회 추구' };
  const basis = { GUIDE_BASED: '가이드 원문 검토', DESIGN_HYPOTHESIS: 'AI 해석 가설', OFFICIAL_MECHANISM: '공식 기전', MECHANISM_INFERENCE:'기전·공략 종합 추론', STATISTICAL_TREND:'관측 통계', EXPERT_JUDGMENT:'공략 판단 기반' };
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
    function board() { return coach().planboard || {}; }
    function planning() { return board().context?.planning || {basis:'loading-plan-example-v1',overrides:{}}; }
    function diagramData() { return board().wave?.diagram || coach().diagram || {}; }
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
      const payload = { planning: planning(), scenario: scenario(), period: coach().selected_period || 'LEVEL1', preference: coach().context?.preferences?.risk || 'BALANCED', ...patch };
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
      const c = coach(), evidence = { claims:[...new Map([...arr(c.evidence?.claims),...arr(board().evidence?.claims)].map(x=>[x.id,x])).values()], sources:[...new Map([...arr(c.evidence?.sources),...arr(board().evidence?.sources)].map(x=>[x.id,x])).values()] }, claims = arr(evidence.claims).filter(claim => arr(ids).includes(claim.id));
      const wrap = details('why-' + key, title || '왜? · 출처와 적용 조건');
      wrap.append(el('p', '가이드 원문 검토는 인용·적용 범위의 확인입니다. AI 해석 가설은 원문에서 확장한 설명이며, 실제 효과 검증과 구분합니다.', 'coach-muted'));
      if (!claims.length) wrap.append(el('p', '이 항목에 연결된 주장 근거가 아직 없습니다.', 'coach-muted'));
      claims.forEach((claim, index) => {
        const section = el('section', null, 'coach-claim');
        section.append(el('span', basis[claim.basis] || '근거 범위 미확인', 'coach-badge'), el('p', claim.display_text || claim.text));
        if (claim.review) section.append(block('검토 범위', claim.review==='SOURCE_SCOPE_CHECKED_CONDITIONAL'?'원문과 적용 범위 확인 · 실전 효과 미검증':claim.review==='TYPE_SCOPED_ADOPTION_NOT_USER_OR_AUTO'?'출처 범위에 맞춰 채택 · 사용자 승인·자동 검토 등급과 별도':claim.review));
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
      if (/^[ABCDE]$/.test(c.matchup_id)) { const a = el('a', '같은 근거로 학습하기 →'); a.href = './directions.html#coach-lesson-' + c.matchup_id; wrap.append(a); }
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
      const reset=button('기본 비교로 되돌리기','reset-scenario',()=>change({scenario:{standard:'lane-standard-v1',overrides:{}},planning:{basis:'loading-plan-example-v1',overrides:{}}}));reset.dataset.coachChange='';wrap.append(reset);
      const extra=[['enemy_jungle','상대 정글',{UNKNOWN:'미확인',AWAY:'반대편 확인 가정',NEAR:'가까운 개입 가정'}],['goal','이번 웨이브 목적',{AUTO:'구간 기본 목적',PRESSURE:'CS·공간 압박',FARM:'수급 보존',RECALL:'귀환 준비'}],['clear_window','포탑 도달 여유',{UNCONFIRMED:'미확인',OPEN:'다음 웨이브까지 처리·도달 여유 가정'}]];
      if(c.supported&&['A','B'].includes(c.matchup_id))extra.push(['enemy_support','상대 서포터',{PRESENT:'함께 있는 예시',ABSENT:'부재 가정',UNKNOWN:'미확인'}]);
      extra.forEach(([key,title,options])=>{const label=el('label'),select=el('select');select.dataset.coachFocus='planning-'+key;select.dataset.coachChange='';Object.entries(options).forEach(([value,text])=>{const o=el('option',text);o.value=value;select.append(o);});select.value=planning().overrides[key]||Object.keys(options)[0];select.addEventListener('change',()=>change({planning:{...planning(),overrides:{...planning().overrides,[key]:select.value}}}));label.append(el('span',title),select);fields.append(label);});
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
      if(board().choice?.id===c.selection?.id)field.append(comparison);else field.append(block('목적에 맞춘 선택',board().wave?.purpose),block('비용',board().choice?.cost),block('남길 자원',board().choice?.reserve));
      field.append(controls, el('p', board().choice?.reason || c.selection?.reason || '성향은 가능한 행동 후보의 선택에만 적용됩니다.', 'coach-muted'), el('p', '성향을 바꿔도 매치업 우열·실행 조건·근거는 바뀌지 않습니다.', 'coach-muted'));
      return field;
    }
    function matrix() {
      const c = coach(), reference=!!c.source_plan,wrap = el('div', null, 'coach-matrix-scroll'); wrap.tabIndex = 0; wrap.dataset.coachScroll = 'matrix'; wrap.setAttribute('role', 'region'); wrap.setAttribute('aria-label', '구간별 비교표 · 우리/상대는 조건부 우세, 부족은 자료 부족');
      const table = el('table', null, 'coach-matrix'), caption = el('caption', '동일한 표준 조건의 구간별 비교 · 실제 시간이나 승률이 아닙니다.'); table.append(caption);
      const head = el('thead'), tr = el('tr'); tr.append(el('th', '구간')); metrics.forEach(([, label]) => { const th = el('th', label); th.scope = 'col'; tr.append(th); }); head.append(tr); table.append(head);
      const body = el('tbody'); arr(c.periods).forEach(row => { const r = el('tr'); r.dataset.selected = String(row.id === c.selected_period); const th = el('th'); th.scope = 'row'; const b = reference?el('span',row.label):button(row.label, 'period-' + row.id, () => change({ period: row.id })); b.dataset.coachChange = ''; b.setAttribute('aria-pressed', String(row.id === c.selected_period)); th.append(b); r.append(th); metrics.forEach(([key]) => { const metric = row.metrics?.[key] || {}, td = el('td', ({ALLY:'우리',ENEMY:'상대',CONTESTED:'경합',INSUFFICIENT:'부족'})[metric.assessment] || '부족'); if(metric.evidence_kind==='MECHANISM_INFERENCE')td.textContent+=' · '+(metric.qualifier||'조건부')+' 추론';td.dataset.assessment = metric.assessment || 'INSUFFICIENT'; if (metric.scope || metric.reason) td.title = format([metric.scope, metric.reason].filter(Boolean).join(' · ')); r.append(td); }); body.append(r); }); table.append(body); wrap.append(table);
      if(reference){const section=el('section',null,'coach-phase-plans');section.append(el('h3','구간별 기본 계획'),el('p','공략에서 채택한 계획입니다. 교환 우열은 조건·견해 차이가 있어 별도로 남겼습니다.','coach-muted'));const t=el('table',null,'coach-stat-table'),h=el('tr');['구간','기본 목적'].forEach(x=>h.append(el('th',x)));t.append(h);for(const row of arr(c.periods)){const r=el('tr'),head=el('th');r.dataset.selected=String(row.id===c.selected_period);const b=button(row.label,'period-'+row.id,()=>change({period:row.id}));b.dataset.coachChange='';b.setAttribute('aria-pressed',String(row.id===c.selected_period));head.append(b);r.append(head,el('td',c.source_plan.periods[row.id]?.purpose||row.action));t.append(r);}section.append(t);const raw=details('strength-data','교전 우열 표 · 아직 확정하지 않은 부분');raw.append(wrap);section.append(raw);return section;}return wrap;
    }
    function growth() {
      const wrap = el('div', null, 'coach-growth'); arr(coach().growth).forEach(event => {
        const b = button(event.label, 'growth-' + event.id, () => change({ period: event.id })); b.dataset.coachChange = ''; b.setAttribute('aria-pressed', String(event.id === coach().selected_period)); wrap.append(b);
        if (event.id === coach().selected_period) { const card = el('div', null, 'coach-growth-detail'); card.append(block('변화가 생기는 조건', event.trigger), block('무엇이 달라지나', event.change), block('변화 전', event.before), block('변화 후', event.after), block('우리에게 남는 강점', event.remaining_strength), block('위치에 따른 응징 위험', event.positional_punish_risk==='INCREASED_CONDITIONAL'?'조건부 증가': '미확인'), block('예외', event.exceptions)); if (event.global_reversal != null) card.append(block('전체 구도 역전', typeof event.global_reversal === 'boolean' ? (event.global_reversal ? '근거가 제시된 범위에서 역전' : '전체 구도 역전으로 해석하지 않습니다.') : event.global_reversal==='UNDETERMINED'?'미확인':event.global_reversal)); card.append(why(event.claim_ids, 'growth-' + event.id)); wrap.append(card); }
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
      arr(diagramData().steps).forEach((step, index) => { const number = Number(step.number) || index + 1, b = button(String(number) + '단계', where + '-step-' + number, () => selectStep(number)); b.dataset.coachStep = number; b.setAttribute('aria-pressed', String(state.step === number)); b.addEventListener('keydown', event => { if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return; event.preventDefault(); const buttons = Array.from(group.children), at = buttons.indexOf(b), target = event.key === 'Home' ? 0 : event.key === 'End' ? buttons.length - 1 : (at + (event.key === 'ArrowRight' ? 1 : -1) + buttons.length) % buttons.length; buttons[target].click(); buttons[target].focus(); }); group.append(b); }); return group;
    }
    function selectStep(number) { state.step = number; syncSteps(); }
    function syncSteps() {
      const steps = arr(diagramData().steps), step = steps.find(s => Number(s.number) === state.step) || steps[0];
      host.querySelectorAll('[data-coach-step]').forEach(n => { const selected = Number(n.dataset.coachStep) === state.step; if (n.tagName === 'BUTTON') n.setAttribute('aria-pressed', String(selected)); else n.dataset.active = String(selected); });
      host.querySelectorAll('.coach-step-copy').forEach(n => { n.textContent = step ? format(String(step.number) + '. ' + step.text) : ''; });
      host.querySelectorAll('.coach-line').forEach(n => { n.dataset.step = String(state.step); });
    }
    function lineDiagram(zoom) {
      const c = coach(), d = diagramData(), wrap = el('div', null, 'coach-line-wrap');
      if (!d.supported || d.kind !== 'LINE') { wrap.append(el('p', '현재 조건에 연결된 라인 도식이 없습니다.', 'coach-muted')); return wrap; }
      const line = el('div', null, 'coach-line'); line.dataset.plan = d.plan_id || ''; line.dataset.step = state.step; line.setAttribute('role', 'group'); line.setAttribute('aria-label', '선택된 웨이브 계획의 상징 도식. 적 위치는 모두 가상이며 실제 거리·사거리·시간을 나타내지 않습니다.');
      const terrain = el('div', null, 'coach-lane-track'); line.append(terrain, el('span', '아군 방향', 'coach-line-home'), el('span', '상대 방향', 'coach-line-away'));
      const symbol = el('span', ({ ACQUIRE_PUSH: '⇢', SLOW_PUSH: '→', FAST_PUSH: '⇉', CRASH: '→│', TRIM_RECEIVE: '←', TOWER_CS: '│', RETURNING: '⇇', FREEZE: '↔', CHECK_WAVE: '?' })[d.plan_id] || '?', 'coach-wave-symbol'); symbol.setAttribute('aria-hidden', 'true'); line.append(symbol);
      const geometry = {
        ACQUIRE_PUSH: [32, 41, 54, 63], SLOW_PUSH: [34, 43, 54, 63], FAST_PUSH: [36, 45, 57, 66], CRASH: [51, 61, 74, 83], TRIM_RECEIVE: [24, 34, 45, 55], TOWER_CS: [17, 26, 37, 46], RETURNING: [30, 40, 54, 64], FREEZE: [24, 33, 44, 53], CHECK_WAVE: [35, 44, 56, 65]
      }[d.plan_id] || [35, 44, 56, 65];
      geometry.forEach((x, i) => { const group = el('span', '● ● ●', 'coach-minions ' + (i < 2 ? 'coach-minions-ally' : 'coach-minions-enemy')); group.style.left = x + '%'; group.style.top = (i % 2 ? 57 : 44) + '%'; group.setAttribute('aria-hidden', 'true'); line.append(group); });
      const own = d.own || current?.input?.own_champion;
      [['ALLY', Array.from(new Set([own, ...arr(d.allies)].filter(Boolean))), 22], ['ENEMY', Array.from(new Set(arr(d.enemies))), 78]].forEach(([team, ids, x]) => { ids.forEach((id, i) => { const unit = el('span', null, 'coach-line-unit ' + (team === 'ALLY' ? 'coach-line-ally' : 'coach-line-enemy')); unit.style.left = (ids.length > 2 ? 15 + i * 70 / (ids.length - 1) : x) + '%'; unit.style.top = (ids.length > 2 ? team === 'ALLY' ? 12 : 72 : ids.length > 1 ? i % 2 ? 72 : 12 : 12) + '%'; const champion = catalog?.champions?.[id]; if (root.LoadingMap?.portrait) unit.append(root.LoadingMap.portrait(champion, id === own)); else unit.append(el('span', champion?.name?.slice(0, 1) || '?')); unit.title = (champion?.name || id) + (team === 'ENEMY' ? ' · 가상 적 위치' : ' · 설명용 아군 위치'); line.append(unit); }); });
      const steps = arr(d.steps); steps.forEach((s, index) => { const n = button(String(s.number || index + 1),'map-step-'+(s.number||index+1),()=>selectStep(s.number||index+1)); n.className='coach-line-number'; n.style.left = (28 + index * 22) + '%'; n.dataset.coachStep = s.number || index + 1; n.setAttribute('aria-label',(s.number||index+1)+'단계 행동 보기'); line.append(n); });
      let touchX = null; line.addEventListener('pointerdown', event => { touchX = event.clientX; }); line.addEventListener('pointerup', event => { if (touchX == null || Math.abs(event.clientX - touchX) < 45) return; const at = steps.findIndex(s => Number(s.number) === state.step), next = Math.max(0, Math.min(steps.length - 1, at + (event.clientX < touchX ? 1 : -1))); if (steps[next]) selectStep(Number(steps[next].number)); touchX = null; });
      wrap.append(line, el('p', '초상화: 공식 자료 · 미니언: 상징 묶음 · 모든 적 위치는 가상 예시', 'coach-muted'), stepControls(zoom ? 'zoom' : 'line'), el('p', '', 'coach-step-copy'));
      return wrap;
    }
    function wave() {
      const c=coach(), w=board().wave, legacy=c.wave?.selected, section=card('이번 웨이브 · 상황별 참고 계획');
      if(!w)return section;
      section.dataset.boardPlan=w.plan_id;
      const copy=el('dl',null,'coach-wave-four');
      [['목적',w.purpose],['처리',w.handling],['위치·교전',w.position+' '+w.combat],['다음 웨이브 / 변경',w.next_wave+' '+w.change_if]].forEach(([key,value])=>copy.append(el('dt',key),el('dd',value)));
      section.append(copy);
      const axes=el('div',null,'coach-axes');Object.entries(w.axes).forEach(([key,value])=>{const chip=el('span',value.label);chip.dataset.axis=key;axes.append(chip);});section.append(axes);
      const steps=el('ol',null,'coach-execution-steps');arr(w.steps).forEach(step=>{const li=el('li'),b=button(step.number+' · '+step.text,'card-step-'+step.number,()=>selectStep(step.number));li.dataset.coachStep=step.number;b.dataset.coachStep=step.number;li.append(b);steps.append(li);});
      const d=details('execution-steps','처리 → 응징 → 다음 선택');d.append(steps);section.append(d,lineDiagram(false));
      if(diagramData().supported){const b=button('도식 크게 보기','open-zoom',()=>openZoom(b));section.append(b);}
      const procedure=details('wave-procedure','밀 수 있는가 / 밀어야 하는가 · 원리와 중단');
      procedure.append(block('상대의 웨이브 대응',w.opponent_response),block('이번 목적의 성공 기준',w.success),block('밀 수 있는가',board().lane?.can_push),block('밀어야 하는가',board().lane?.should_push));
      if(legacy)[['시작 조건','start'],['처리 방식','processing'],['기술 사용','skills'],['남길 자원','reserve'],['완료 확인','complete'],['중단 조건','abort'],['다음 행동','next'],['상대 접근에 대한 우리 대응','punishment'],['이득 전환','conversion'],['비용','costs']].forEach(([label,key])=>procedure.append(block(label,legacy[key])));
      section.append(procedure,why(w.claim_ids,'wave'));return section;
    }
    function counterplans(){
      const p=board().matchup_playbook,section=card('양쪽 상대법');
      if(!p)return section;
      section.append(el('p',p.supported?'같은 구간·웨이브 가정의 조건부 계획 · 상대 의도를 관측한 정보가 아닙니다.':'이 매치업의 개별 상대법은 아직 지원하지 않습니다.','coach-muted'));
      const grid=el('div',null,'coach-counterplans');
      [['ours','우리의 상대법'],['theirs','상대의 가능한 상대법']].forEach(([key,title])=>{const n=el('section');n.dataset.counterplan=key;n.append(el('h4',title));[['목적','purpose'],['수단','means'],['노릴 행동','look_for'],['피할 행동','avoid'],['계획 변경','switch_when']].forEach(([label,field])=>n.append(block(label,p[key][field])));grid.append(n);});section.append(grid,why(p.claim_ids,'counterplans'));return section;
    }
    function trade() {
      const t = coach().trade || {}, section = card('교환 길이 · 상대의 남은 대응'); section.append(block('실제 매치업 우열', t.actual_advantage));
      [['ours', '우리의 선호'], ['theirs', '상대의 가능한 선호']].forEach(([key, title]) => { const side = t[key] || {}, n = el('section', null, 'coach-trade-side'); n.append(el('h4', title + (side.label ? ' · ' + side.label : '')), block('이유', side.reason)); const d = details('trade-' + key, '시작 · 공격 순서 · 종료 조건'); [['시작', 'start'], ['공격 순서', 'order'], ['종료', 'end'], ['이어갈 조건', 'continue_if'], ['대안', 'alternative']].forEach(([label, field]) => d.append(block(label, side[field]))); n.append(d); section.append(n); }); return section;
    }
    function sustain() {
      const s = coach().sustain || {}, section = card('유지력 · 피해를 버티는 방식'); section.append(el('p', s.summary));
      arr(s.actors).forEach(actor => { const d = details('sustain-' + actor.champion, actor.name || catalog?.champions?.[actor.champion]?.name || '각 챔피언'); [['교전 중 회복', 'in_fight_heal'], ['교환 사이 회복', 'between_trade'], ['피해 방지 · 보호막', 'shield'], ['자원', 'resources'], ['수급 · 행동 공백', 'downtime'], ['위험', 'risks']].forEach(([label, key]) => d.append(block(label, actor[key]))); section.append(d); }); section.append(block('재정비', s.reset), block('한계', s.limits)); return section;
    }
    function application() {
      const a=coach().knowledge_application,wrap=details('knowledge-application','이 기본 판단을 채택한 이유');
      if(!a?.supported)return wrap;
      wrap.append(block(a.active?'추천 기본 계획':'기본 구도 참고 · 현재 조건에는 미적용',a.recommended_plan),block('판단 이유',a.reason),block('현재 적용',a.active?'선택한 구간·가정에서 적용':'이 구간·가정에는 기본 분기를 그대로 적용하지 않습니다.'),block('적용 조건',a.conditions),block('계획을 바꿀 예외',a.exceptions),block('자료를 넘어선 제한적 추론',a.inference),block('남은 핵심 질문',a.open_questions));
      for(const ref of arr(a.direct_sources)){const source=arr(coach().evidence?.sources).find(s=>s.id===ref.source_id);if(source){wrap.append(urlLink(source.title,source.url),el('p',ref.locator+' · '+ref.supports));}}
      wrap.append(why([a.id],'application'));return wrap;
    }
    function evidenceBridge(){
      const b=board().evidence_bridge,d=details('evidence-bridge','통계 → 공략 판단 → 이번 상대법');
      if(!b){d.append(el('p','이 매치업의 종합 근거가 아직 연결되지 않았습니다.'));return d;}
      d.dataset.evidenceBridge='';const s=b.statistics.matchup;
      if(s){const points=s.matchup.points,counts=[...new Set(points.map(p=>p.n))];d.append(block('① Riot 경기 관측',points.length?`10·15분 맞상대 자원 관측 ${counts.join('/')}경기 · 세부 지표·누락은 아래 통계에서 확인합니다.`:'10·15분 맞상대 자원 집계 없음 · 일반 포지션 통계로 대신하지 않습니다.'));
        const data=s.datasets;d.append(el('p',`패치 ${data.power.patch} · ${data.power.platform} · queue 420 · 챌린저 시드 모집단(모든 참가자의 티어 보장 아님)`,'coach-muted'),el('p',`자원 집계 ${data.power.matches}경기 ${data.power.window_start.slice(0,10)}~${data.power.window_end.slice(0,10)} / 결과 집계 ${data.outcome.matches}경기 ${data.outcome.window_start.slice(0,10)}~${data.outcome.window_end.slice(0,10)} · 서로 합산하지 않음`,'coach-muted'));
        d.append(block('전체 경기 결과',s.outcome.n?`${s.outcome.wins}승 / ${s.outcome.n}경기 · 라인전·교전 승률이 아닙니다.`:'일치하는 경기 결과 집계 없음'),el('p',b.statistics.role,'coach-muted'));}
      else d.append(block('① Riot 경기 관측','연결된 집계 없음 · 공략의 정성적 기본 계획과 별도로 관리합니다.'));
      d.append(block(b.application_active?'② 전문가 공략의 판단':'② 공략의 기본 판단 · 현재 조건에는 미적용',b.expert.plan),block('조건·견해 차이',b.expert.reason),block('적용 조건',b.expert.conditions),block('대표 반례',b.expert.exceptions));
      b.expert.sources.forEach(ref=>{const src=arr(coach().evidence.sources).find(s=>s.id===ref.source_id);if(src){d.append(urlLink(src.author+' · '+src.title,src.url),el('p',ref.locator+' · '+ref.supports),el('p','공략 패치: '+src.patch+' · 문단 개별 수정일은 미확인','coach-muted'));}});
      const c=b.counterplay;d.append(block(b.application_active?'③ 현재 구간의 상대법':'③ 현재 조건에 제한된 상대법',[c.purpose,c.opponent_goal,c.wave_plan,c.trade,c.punish,c.growth]),block('자료를 넘어선 해석',b.inference),el('p','통계는 전문가 계획의 승리 증명이 아닙니다. 원문·조건·반례를 종합한 기본 계획이며 실전 효과는 미측정입니다.','coach-muted'));return d;
    }
    function statistics() {
      const s=coach().knowledge_application?.statistics,wrap=details('statistical-context','기존 경기 통계 · 매치업과 일반 참고 구분');
      if(!s){wrap.append(el('p','연결된 통계가 없습니다. 다른 포지션·조합의 수치로 채우지 않습니다.'));return wrap;}
      wrap.dataset.statisticalScope=s.matchup.comparison;
      wrap.append(el('p','원딜 상대 또는 솔로 라인 관측이며 서포터 포함 2대2 증거가 아닙니다. 자원 차이와 전체 승률은 교전 승률이 아닙니다.'));
      const meta=(key,title)=>{const d=s.datasets[key];wrap.append(block(title,`패치 ${d.patch} · ${d.platform} · 솔로/듀오 랭크 · 챌린저 시드 모집단 ${d.matches}경기 · ${d.window_start.slice(0,10)}~${d.window_end.slice(0,10)} · 조회 ${d.retrieved_at.slice(0,10)}. 모든 참가자가 챌린저였다는 뜻은 아닙니다.`));};
      const table=(title,points,role)=>{wrap.append(el('h4',title));if(!points.length){wrap.append(el('p','일치하는 집계 없음 · 일반 포지션 자료로 대체하지 않음'));return;}
        const scroll=el('div',null,'coach-matrix-scroll');scroll.tabIndex=0;scroll.setAttribute('role','region');scroll.setAttribute('aria-label',title);const t=el('table',null,'coach-stat-table'),h=el('tr');['시점','지표','유효 표본','평균 차이 · 95% 구간'].forEach(x=>h.append(el('th',x)));t.append(h);
        for(const p of points){const row=el('tr');row.dataset.statVisible=String(p.legacy_visible);const metric=({gold_delta:'총 획득 골드',xp_delta:'경험치',cs_delta:'미니언+정글 CS'})[p.metric],n=role?`챔피언 ${p.champion_n}관측 / 대조 ${p.reference_n}관측 (${p.n}경기)`:`${p.n}경기`,value=p.mean==null?`${p.omission_reason==='N_LT_2'?'단일 표본':'추정 범위 넓음'} · 기존 정밀도 기준에 따라 수치 보류`:`${p.mean.toFixed(1)} ${p.unit} (${p.ci95.low.toFixed(1)}~${p.ci95.high.toFixed(1)})`;
          for(const x of [p.minute+'분',metric,n,value])row.append(el('td',x));t.append(row);}
        scroll.append(t);wrap.append(scroll);};
      meta('power','시간대별 자원 집계');table('선택한 챔피언 대 맞상대 · 해당 포지션',s.matchup.points,false);
      const general=details('general-statistics','일반 포지션 참고 — 매치업 근거와 별도'); // General population stays explicitly separate.
      general.append(el('p','전체 같은 포지션의 분당 자원 평균과 비교합니다. 총량 차이나 특정 상대와의 2대2 우위가 아닙니다.'));
      wrap.append(general);const count=wrap.childNodes.length;table('일반 포지션 분당 차이',s.role_context.points,true);while(wrap.childNodes.length>count)general.append(wrap.childNodes[count]);
      meta('outcome','전체 경기 결과 집계');const o=s.outcome;wrap.append(block('선택한 맞상대 전체 결과',o.n?`${o.wins}승 / ${o.n}경기 · 표본 승률 ${(100*o.win_rate).toFixed(1)}% · 95% 구간 ${(100*o.ci95.low).toFixed(1)}~${(100*o.ci95.high).toFixed(1)}%. 작은 표본의 기술 통계이며 안정적 상성 판단이 아닙니다.`:'일치하는 결과 집계 없음'));
      wrap.append(el('p','집계 기간과 분모가 다른 자료를 합치지 않았습니다. 이 수치로 기본 교전 우세를 변경하지 않습니다.'));const trace=details('statistics-lineage','통계 출처 · 계산식 · 추적');const pre=el('pre');pre.textContent=JSON.stringify(s.datasets,null,2);trace.append(pre);wrap.append(trace);return wrap;
    }
    function lane() {
      const n=el('div',null,'coach-lane-panel');n.append(matrix(),growth());
      const purpose=card(board().lane?.milestone?.label||'선택 구간');purpose.append(block('이번 구간 목적',board().lane?.milestone?.goal));
      const whyPeriod=details('selected-reason','이 구간의 이유 · 교전 유형별 판단');whyPeriod.append(selected());purpose.append(whyPeriod);n.append(purpose);const methods=details('methods','방법 보기 · 웨이브·교환·양쪽 상대법');methods.append(wave(),counterplans(),preferences());n.append(methods,evidenceBridge(),application(),statistics());
      const comparison=details('trade-sustain','교환 길이 · 반복 교환과 유지력');comparison.append(trade(),sustain());n.append(comparison);return n;
    }
    function operations() {
      const g=board().operations,n=card('운영 · 어디에서 무엇을 얻는가');
      [['기본 계획','placement'],['우선할 이득','priority'],['누구와 연결','connection'],['양보와 교환','concede'],['막히면','fallback'],['성장 후 변화','growth']].forEach(([label,key])=>n.append(block(label,g?.[key])));
      n.append(list(g?.steps,true),why(g?.claim_ids,'operations'));
      // No independent geometry exists for this projected macro plan. Do not relabel a teamfight map.
      n.append(el('p','이 운영 배치의 전체 지도는 미지원입니다. 아래 한타 탭의 역할 배치와 구분합니다.','coach-muted'));return n;
    }
    function fight() {
      const f=board().fight,n=card('한타 · 내 공격 시작 기준');
      [['내 역할','role'],['공격할 대상','target'],['공격 시작','start'],['시작 전 배치','setup'],['중단·위치 변경','stop'],['교전 뒤','after']].forEach(([label,key])=>n.append(block(label,f?.[key])));
      const threats=details('fight-threats','행동을 바꾸는 접근 수단 · 유형별 후보');arr(f?.threats).forEach(t=>{const d=el('section');d.append(block(t.label,t.action),block('조건',t.condition));threats.append(d);});n.append(threats);
      const map=current?.teamfight?.map;
      if(map&&root.LoadingMap?.create){const d=details('fight-map','전체 지도 · 실제 픽의 역할 배치 예시');try{const steps=[f.setup,f.start,f.stop].map((text,i)=>({number:i+1,text}));d.append(root.LoadingMap.create({map,plan:{steps}},catalog,current.input,{selectedStep:String(state.step),onSelect:step=>{if(step!=='ALL'){state.step=Number(step);syncSteps();}}}));}catch(_){d.append(el('p','이 보고서의 지도 표시는 지원되지 않습니다.','coach-muted'));}n.append(d);}
      n.append(why(f?.claim_ids,'fight'));return n;
    }
    function officialFacts() {
      const facts = [...new Map([...arr(coach().evidence?.official_facts),...arr(board().evidence?.official_facts)].map(f=>[f.champion+':'+f.slot,f])).values()], d = details('official-facts', '공식 기전 · 비교에 연결된 사실');
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
      if (/^[ABCDE]$/.test(c.matchup_id)) { const a = el('a', '학습 페이지에서 계속 →'); a.href = './directions.html#coach-lesson-' + c.matchup_id; d.append(a); } return d;
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
      const b=board(),hero=el('div',null,'coach-overview coach-board');hero.append(el('p','이번 판 작전판 · 운영·한타는 가설','coach-eyebrow'));
      const matchup=el('div',null,'coach-matchup-portraits');
      const rosterLane=arr(b.overall?.lanes).find(l=>l.position===current.input.own_position);
      [['우리',rosterLane?.allies],['상대',rosterLane?.enemies]].forEach(([label,ids])=>{const team=el('div',null,'coach-board-team');team.append(el('span',label));arr(ids).forEach(id=>{if(root.LoadingMap?.portrait)team.append(root.LoadingMap.portrait(catalog.champions[id],id===current.input.own_champion));team.append(el('span',catalog.champions[id]?.name||id));});matchup.append(team);});hero.append(matchup,el('h2','이번 판의 방향','sr-only'));
      const applied=c.knowledge_application;if(applied?.supported)hero.append(el('p',applied.active?(applied.display_label||(c.matchup_id==='C'?'기전·공략 종합 추론 · 근접 접촉 유지 조건':'공략 판단 기반 · 확보 전 처리 / 확보 후 쌓기')):'조건 변경으로 기본 근거 적용 범위 제한','coach-evidence-kind'));
      const tiles=el('div',null,'coach-board-tiles');
      const compact=item=>{const tile=button('', 'board-'+item.id,()=>{state.tab=item.id==='growth'?'lane':item.id;render();if(item.id==='growth')host.querySelector('.coach-matrix,.coach-phase-plans')?.scrollIntoView({block:'start',behavior:'instant'});else host.querySelector('[role=tabpanel]')?.scrollIntoView({block:'start',behavior:'instant'});});tile.className='coach-board-tile';tile.dataset.loadingDecision=item.id;tile.setAttribute('aria-label',item.title+' 상세');tile.append(el('span',item.title,'coach-tile-label'),el('span',item.conclusion,'coach-tile-copy'),el('span',item.support,'coach-tile-support'),el('span','↗','coach-tile-arrow'));tiles.append(tile);};
      arr(b.loading_summary?.items).forEach(compact);hero.append(tiles);
      const overallDetails=details('overall-plan','기본 가정 · 전체 구도 · 지원 범위');overallDetails.append(block('우리 계획',b.composition?.ours_full),block('상대의 가능한 계획',b.composition?.theirs_full),block('내 역할',b.composition?.role));arr(b.overall?.lanes).forEach(l=>overallDetails.append(block(l.label,l.reason)));overallDetails.append(el('p',b.overall?.risk));arr(b.overall?.jungle_links).forEach(l=>overallDetails.append(block(({TOP:'탑',MID:'미드',BOTTOM:'바텀'})[l.position]+' 연계 후보',l.means?l.means+' · '+l.condition:l.condition)));hero.append(overallDetails);
      hero.append(block('계획을 바꾸는 조건',b.loading_summary?.changes,'coach-summary-exceptions'));
      const quick=el('div',null,'coach-quick');arr(b.quick_scenarios).forEach(q=>{const n=button(q.label,'quick-'+q.id,()=>change({scenario:{...scenario(),overrides:{...scenario().overrides,...q.scenario}},planning:{...planning(),overrides:{...planning().overrides,...q.planning}}}));n.dataset.coachChange='';quick.append(n);});

      hero.append(el('p','비교용 기본 가정 · '+c.context?.patch?.label,'coach-muted'));
      const scope=overallDetails;scope.append(el('p',b.coverage?.plan_scope),el('p',b.coverage?.gaps),block(c.context?.assumptions?.label,c.context?.assumptions?.details));container.dataset.boardChoice=b.choice?.id||'';const optional=conditions();optional.insertBefore(quick,optional.children[1]||null);container.append(hero,optional);
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

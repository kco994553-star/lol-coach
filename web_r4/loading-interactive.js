/* One synchronous future-scenario state. Preferences, assumptions and viewing stay distinct. */
(function(root){
  'use strict';
  function describeSelection(result, previous) {
    const sameChange = previous && previous.risk !== result.preference.risk && previous.plan === result.selected_plan_id;
    if (sameChange && !result.selection_reason.startsWith('현재 조건에서는 선택이 같습니다')) {
      return '현재 조건에서는 선택이 같습니다. 두 성향 모두 명시한 가정에서 실행 가능한 같은 안을 먼저 살펴보도록 연결되어 있습니다. 조건·비용·중단 기준은 그대로입니다.';
    }
    return result.selection_reason;
  }
  function waveAllowsMeans(wave,id){
    if(id==='PREPARE_WINDOW')return true;
    if(!wave?.supported)return false;
    if(id==='SHORT_FOLLOW')return wave.punishment_follow_allowed===true;
    return id==='RECEIVE_WITH_LUX'&&['TRIM_RECEIVE','TOWER_CS','RETURNING'].includes(wave.selected_plan_id);
  }
  function mount({report:initial,catalog,host,onPreference}){
    const X=root.LoadingExploration,S=root.SkillDisplay,W=root.LoadingWave,G=root.LoadingEngagement;
    let report=initial,state=X.defaultState(),panel='LANE',step='1',preview=null,result=null,destroyed=false,last=null;
    let engagementState=G.defaultState(),engagementResult=null,engagementOpen=false;
    let waveState=W.defaultState(),waveResult=null,wavePreview=null,waveStep='1',legacyOpen=false;
    const fmt=v=>S.format(String(v),{champions:report.input.allies.concat(report.input.enemies).map(p=>p.champion),own:report.input.own_champion,aliases:report.lane.matchup_id==='Caitlyn_Lux__Kaisa_Nautilus_v2'?[{text:'덫',champion:'Caitlyn',slot:'W'}]:[]});
    const el=(tag,text,cls)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!=null)n.textContent=['code','blockquote'].includes(tag)?String(text):fmt(text);return n;};
    const button=(text,id,fn)=>{const n=el('button',text);n.type='button';if(id)n.id=id;n.addEventListener('click',fn);return n;};
    const list=(values,ordered=false)=>{const n=el(ordered?'ol':'ul');(values||[]).forEach(v=>n.append(el('li',v)));return n;};
    const block=(title,value)=>{const n=el('div',null,'interactive-block');n.append(el('h4',title),Array.isArray(value)?list(value):el('p',value));return n;};
    const closeZoom=()=>{const d=document.getElementById('loading-map-dialog');if(d?.open)d.close();};
    function evidenceFor(plan){
      const why=el('details',null,'interactive-why');why.id=plan?'why-'+plan.id:'row-why';why.append(el('summary','왜? · 관련 근거·예외·반례'));
      why.append(block('공식 사실이 지지하는 범위',result.evidence.official_scope),block('행동 해석의 수준','설계 가설 · 조건부 근거 · 유불리/최적 행동은 미판정. 성향 선택은 근거 수준을 올리지 않습니다.'),block('적용 가정',plan?.requirements||result.row.assumptions||[]),block('중단·예외',plan?.abort||result.row.changes||[]),block('수정이 필요한 반례',result.evidence.counterexamples));
      const ids=new Set(plan?.evidence_ids||result.row.evidence_ids||[]),facts=report.evidence.facts.filter(f=>ids.has(f.id));
      const factsArea=el('div',null,'interactive-facts');
      facts.forEach(f=>{
        const article=el('article',null,'fact-card'),owner=f.id.split(':')[1],heading=S.factLabel(owner,f);
        article.append(el('h4',heading),el('p',f.text));
        const quote=el('details');quote.append(el('summary','보존된 출처 원문'),el('blockquote',f.raw_excerpt||f.text));article.append(quote);
        const a=el('a','공식 출처 ↗');a.href=f.url;a.target='_blank';a.rel='noopener noreferrer';article.append(a,el('p','자료 패치 '+f.patch,'source-note'));
        const trace=el('details');trace.append(el('summary','출처·버전·Trace 상세'),el('code',JSON.stringify({id:f.id,patch:f.patch,sha256:f.sha256,locator:f.locator,local_source:f.local_source},null,2)));article.append(trace);factsArea.append(article);
      });
      if(!facts.length)factsArea.append(el('p','이 조언에 연결된 공식 사실이 없습니다. 행동 근거는 미확인입니다.'));
      why.append(factsArea,block('강의 설명·관측 통계','이 행동 선택을 직접 지지하는 강의 구간·매치업 통계는 아직 연결하지 않았습니다. '+(result.evidence.question_id?'대기 질문 '+result.evidence.question_id:'이 구간의 추가 근거가 필요합니다.')));
      return why;
    }
    function apply(next,reason){
      if(destroyed)return;
      const focused=host.contains(document.activeElement)?document.activeElement.id:null;
      const before=result,oldPlan=before?.selected_plan_id;
      state=next;result=X.evaluate(report,catalog,state);preview=result.selected_plan_id;step='1';
      last={reason,previous:oldPlan,current:result.selected_plan_id,previous_choice:before?{risk:before.preference.risk,plan:oldPlan}:null,action_changed:Boolean(before&&oldPlan!==result.selected_plan_id)};
      waveState={...waveState,milestone:state.milestone};engagementState={...engagementState,milestone:state.milestone};engagementResult=G.evaluate(report,catalog,engagementState,waveState.assumptions.purpose);waveResult=G.constrainWave(report,catalog,waveState,result,engagementResult,W);wavePreview=waveResult.selected_plan_id;waveStep='1';
      closeZoom();render();
      if(focused)host.querySelector('#'+CSS.escape(focused))?.focus({preventScroll:true});
    }
    function render(){
      host.querySelector('#wave-line-dialog')?.close();host.replaceChildren();host.dataset.selectedPlan=result.selected_plan_id||'UNSUPPORTED';host.dataset.period=state.milestone;host.dataset.risk=result.preference.risk;
      host.append(el('h2','조건을 바꿔, 다음 선택 살펴보기'),el('p','앞으로 이런 상황이라면 · 모든 조건과 지도 위치는 가상입니다. 현재 게임을 관측하지 않습니다.','source-note'));
      const preference=el('fieldset',null,'risk-options');preference.append(el('legend','내 선호 · 실행 가능성과 근거 수준은 별도'));
      for(const [risk,name] of Object.entries(X.riskNames)){
        const label=el('label'),input=el('input');input.type='radio';input.name='risk';input.id='risk-'+risk;input.value=risk;input.checked=result.preference.risk===risk;
        input.addEventListener('change',()=>{if(!input.checked)return;try{report=onPreference(risk);apply(state,'사용자 선호 변경');}catch(e){showError(e);}});label.append(input,el('span',name));preference.append(label);
      }
      host.append(preference);
      const status=el('div',null,'interactive-status');status.id='exploration-summary';status.setAttribute('role','status');
      const preferred=result.plans.find(p=>p.id===result.selected_plan_id);
      status.append(el('strong','가상 '+result.row.period+' 선택: '+(preferred?.title||'기존 구간 설명만 지원')),el('p',describeSelection(result,last?.previous_choice)),el('small','사용자 선호: '+result.preference.label+' / 근거: 설계 가설 · '+(result.supported?'조건부':'자료/비교 규칙 부족')+' / 현재 관측: 없음'));status.hidden=true;host.append(status);
      const tabs=el('div',null,'interactive-tabs');tabs.setAttribute('role','group');tabs.setAttribute('aria-label','빠른 분석 전환');
      for(const [id,name] of [['LANE','라인전'],['OPERATIONS','운영'],['FIGHT','한타']]){const b=button(name,'explore-tab-'+id,()=>{panel=id;render();host.querySelector('#explore-tab-'+id).focus({preventScroll:true});});b.setAttribute('aria-pressed',String(panel===id));tabs.append(b);}host.append(tabs);
      if(panel!=='LANE'){
        const isFight=panel==='FIGHT';host.append(block(isFight?'한타에서 내 역할':'운영 기본안',isFight?report.teamfight.role:report.gameplan.base),block('필요한 준비',isFight?report.teamfight.setup:report.gameplan.prepare),block('조건이 끊기면',isFight?report.teamfight.exit:report.gameplan.fallback));
        host.append(el('p','이 문맥은 기존 분석을 재사용합니다. 성향별 대안 비교는 대표 바텀 레벨 2에서만 지원합니다.','source-note'));
        const a=el('a',isFight?'전체 한타·기존 지도 보기':'전체 운영 분석 보기');a.href=isFight?'#teamfight':'#loading-gameplan';host.append(a);return;
      }
      const periods=el('div',null,'period-options');periods.setAttribute('role','group');periods.setAttribute('aria-label','라인전 구간 선택');
      report.lane.rows.forEach(row=>{const b=button(row.period,'period-'+row.id,()=>apply({...state,milestone:row.id},'라인전 구간 변경'));b.dataset.lanePeriod=row.id;b.setAttribute('aria-pressed',String(row.id===state.milestone));periods.append(b);});host.append(periods);
      const engagement=root.LoadingEngagementView.create({result:engagementResult,report,catalog,onChange:(key,value)=>{engagementState=key==='type'?{...engagementState,type:value}:{...engagementState,assumptions:{...engagementState.assumptions,[key]:value}};apply(state,'교전 가정 변경');},onReset:()=>{engagementState={...G.defaultState(),milestone:state.milestone};apply(state,'교전 가정 초기화');}});const ec=engagement.querySelector('#engagement-conditions');if(ec){ec.open=engagementOpen;ec.addEventListener('toggle',()=>engagementOpen=ec.open);}const encounterLink=el('a','교전 유형·올인 조건 비교로 이동');encounterLink.href='#engagement-flow';host.append(encounterLink);
      const wave=root.LoadingWaveView.create({result:waveResult,catalog,report,preview:wavePreview,step:waveStep,onAssumption:(key,value)=>{waveState={...waveState,assumptions:{...waveState.assumptions,[key]:value}};apply(state,'웨이브 가정 변경');},onPreset:assumptions=>{waveState={...waveState,assumptions};apply(state,'웨이브 가정 예시/초기화');},onPreview:id=>{wavePreview=id;waveStep='1';closeZoom();render();host.querySelector('#wave-preview-'+id)?.focus({preventScroll:true});},onStep:n=>{waveStep=n;}});host.append(wave,engagement);if(waveResult.engagement_constraint==='LIMIT_EXPOSURE'){const note=el('p','교전 조건으로 웨이브 실행을 제한했습니다. 원래 입력은 보존하지만 전진 처리·상대 방해를 감당한다는 가정을 그대로 실행에 쓰지 않습니다. '+engagementResult.wave_bridge,'interactive-status');note.id='wave-engagement-gate';wave.prepend(note);}
      host.dataset.wavePlan=waveResult.selected_plan_id||'UNSUPPORTED';
      const laneKey=document.getElementById('lane-key');if(laneKey)laneKey.textContent=fmt(waveResult.supported&&waveResult.selected_plan_id!=='CHECK_WAVE'?'가상 웨이브 목표: '+waveResult.selected.title+' / 전환: '+waveResult.selected.failure+' / 기회: 처리·퇴로 예산을 깨지 않을 때만 공간·미니언 처리·짧은 응징을 비교합니다.':report.summary.lane_key);
      const legacy=el('details');legacy.id='wave-skill-means';legacy.open=legacyOpen;legacy.append(el('summary','웨이브 계획의 하위 수단 · 기존 기술·딜교환 상세'));legacy.addEventListener('toggle',()=>legacyOpen=legacy.open);host.append(legacy);
      const row=el('article',null,'interactive-row');row.id='selected-lane-row';row.dataset.selectedMilestone=state.milestone;
      row.append(el('h3',result.row.period+' · '+result.row.judgment),block('행동과 이유',[result.row.action,result.row.why]),block('상대 대응',result.row.opponent_response||report.lane.interactions),block('조건이 부족할 때',result.row.alternative||report.lane.recovery),block('중단·전환',result.row.changes));
      // Reuse the same bounded owner bindings as the full table, supplied by its existing renderer.
      const fullRow=document.querySelector('#lane-table [data-milestone="'+state.milestone+'"]');
      if(fullRow){const cells=fullRow.querySelectorAll('td');row.replaceChildren(el('h3',result.row.period+' · 조건·행동·대응'));
        for(const [index,title] of [[0,'판단'],[1,'이유·가정'],[2,'행동·상대 대응·대안'],[3,'중단·전환']]){const box=el('div',null,'interactive-block');box.append(el('h4',title),cells[index].firstElementChild.cloneNode(true));row.append(box);}}
      row.append(evidenceFor(null));const full=el('a','전체 여섯 구간 표로 비교');full.href='#loading-lane';row.append(full);legacy.append(row);
      if(!result.supported){legacy.append(block('스킬 수단 비교·지도 미지원',result.unsupported_reason));return;}
      const conditions=el('fieldset',null,'hypothesis-inputs');conditions.append(el('legend','가정 한 가지 바꾸기 · 실제 관측 아님'));
      X.conditionDefs.forEach(def=>{const label=el('label'),select=el('select');select.id='assumption-'+def.key;for(const [value,name] of Object.entries(def.options)){const o=el('option',name);o.value=value;select.append(o);}select.value=state.assumptions[def.key];select.addEventListener('change',()=>apply({...state,assumptions:{...state.assumptions,[def.key]:select.value}},def.label));label.append(el('span',def.label),select);if(def.note)label.append(el('small',def.note));conditions.append(label);});
      const presets=el('div',null,'assumption-actions');presets.append(button('후속 가능 가정 예시','assumptions-ready',()=>apply({...state,assumptions:{binding:'HIT',followup:'READY',exit_cover:'AVAILABLE'}},'미래 조건 예시 불러오기')),button('기본 조건으로 되돌리기','assumptions-reset',()=>apply({...state,assumptions:X.defaultState().assumptions},'가상 조건 초기화')));conditions.append(presets);legacy.append(conditions);
      const diff=el('div',null,'condition-diff');diff.id='condition-change';diff.setAttribute('aria-live','polite');diff.dataset.actionChanged=String(Boolean(last?.action_changed));
      const title=id=>result.plans.find(p=>p.id===id)?.title||'미지원';diff.append(block('달라진 행동',last?.action_changed?title(last.previous)+' → '+title(last.current):'행동 선택 유지: '+title(result.selected_plan_id)),block('달라진 이유',describeSelection(result,last?.previous_choice)),block('그대로인 조건',result.unchanged_conditions),block('새로 필요한 확인',result.required_checks));legacy.append(diff);
      const comparison=el('div',null,'plan-comparison');comparison.id='plan-comparison';
      result.plans.forEach(plan=>{
        const card=el('article',null,'plan-option');card.dataset.planId=plan.id;card.dataset.feasibility=plan.feasibility;card.dataset.preferred=String(plan.id===result.selected_plan_id&&waveAllowsMeans(waveResult,plan.id));
        card.append(el('h3',plan.title+(waveAllowsMeans(waveResult,plan.id)?' · 웨이브 목표 안의 수단':' · 현재 웨이브 목표에 미채택')),el('p',plan.feasibility==='POSSIBLE'?'명시한 가정 안에서 검토 가능':plan.feasibility==='UNKNOWN'?'실행 조건 미확인 · 선택 불가':'가정상 실행 불가 · 선택 불가','source-note'),block('얻으려는 것',plan.objective),block('포기·소모·위험',plan.costs),block('필요한 조건',plan.requirements));
        const dims=el('details');dims.append(el('summary','비용 비교 · 여섯 관점'));Object.entries(plan.dimensions).forEach(([key,v])=>dims.append(block(X.dimensionNames[key],v.text)));card.append(dims);
        const pick=button('이 안의 행동·지도 살펴보기','preview-'+plan.id,()=>{preview=plan.id;step='1';renderMap();comparison.querySelectorAll('[data-plan-id]').forEach(c=>c.classList.toggle('is-preview',c.dataset.planId===preview));});pick.disabled=plan.feasibility!=='POSSIBLE'||!waveAllowsMeans(waveResult,plan.id);card.append(pick,evidenceFor(plan));comparison.append(card);
      });legacy.append(comparison);
      const active=el('div');active.id='active-plan';active.setAttribute('aria-live','polite');legacy.append(active);renderMap();
    }
    function renderMap(){
      const target=host.querySelector('#active-plan');if(!target)return;const plan=result.plans.find(p=>p.id===preview&&p.feasibility==='POSSIBLE'&&waveAllowsMeans(waveResult,p.id));target.replaceChildren();if(!plan){target.append(el('p','이 수단은 현재 웨이브 목표 또는 실행 조건에 맞지 않아 선택·실행 지도를 표시하지 않습니다. 기존 조언과 조건·비용은 보존합니다.'));return;}
      target.dataset.plan=plan.id;target.append(el('h3','살펴보는 안: '+plan.title),block('준비 → 실행 → 전환',plan.steps.map(s=>s.number+'. '+s.text)),block('상대 대응 시·중단 기준',plan.abort),block('불확실할 때의 다음 행동',plan.next_if_unknown));
      const action=el('p',null,'selected-action');action.id='selected-action';action.setAttribute('role','status');target.append(action);
      const select=n=>{step=n;action.textContent=fmt(n==='ALL'?'전체 단계 · 번호를 선택해 행동을 살펴보세요.':plan.steps.find(s=>String(s.number)===n)?.text||'');action.dataset.step=n;target.dataset.selectedStep=n;};
      const scenario=X.mapFor(report.input,plan);target.append(root.LoadingMap.create(scenario,catalog,report.input,{selectedStep:step,onSelect:select,skillAliases:[{text:'덫',champion:'Caitlyn',slot:'W'}]}));select(step);
    }
    function showError(error){closeZoom();host.replaceChildren(el('p','탐색을 완료하지 못했습니다. 픽을 다시 분석해 주세요. '+(error?.message||''),'is-error'));}
    result=X.evaluate(report,catalog,state);preview=result.selected_plan_id;engagementResult=G.evaluate(report,catalog,engagementState,waveState.assumptions.purpose);waveResult=G.constrainWave(report,catalog,waveState,result,engagementResult,W);wavePreview=waveResult.selected_plan_id;render();
    return {destroy(){destroyed=true;closeZoom();host.querySelector('#wave-line-dialog')?.close();host.replaceChildren();},snapshot(){return {state:JSON.parse(JSON.stringify(state)),panel,step,preview,result:result.selected_plan_id};}};
  }
  root.LoadingInteractive={mount,describeSelection,waveAllowsMeans};
})(window);

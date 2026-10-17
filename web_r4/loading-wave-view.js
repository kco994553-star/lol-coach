/* Wave-first presentation: same selected plan/step drives cards, line sketch and macro map. */
(function(root){
  'use strict';
  const NS='http://www.w3.org/2000/svg';
  function create({result:r,catalog,report,preview,step='1',onAssumption,onPreset,onPreview,onStep}){
    const fmt=t=>root.SkillDisplay.format(String(t),{champions:report.input.allies.concat(report.input.enemies).map(p=>p.champion),own:report.input.own_champion});
    const el=(tag,text,cls)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!=null)n.textContent=fmt(text);return n;};
    const list=vs=>{const n=el('ul');vs.forEach(v=>n.append(el('li',v)));return n;};
    const block=(title,v)=>{const n=el('div',null,'interactive-block');n.append(el('h4',title),Array.isArray(v)?list(v):el('p',v));return n;};
    const button=(text,id,fn)=>{const n=el('button',text);n.type='button';n.id=id;n.addEventListener('click',fn);return n;};
    const svg=(tag,attrs={},text)=>{const n=document.createElementNS(NS,tag);Object.entries(attrs).forEach(([k,v])=>n.setAttribute(k,String(v)));if(text!=null)n.textContent=fmt(text);return n;};
    const host=el('section',null,'wave-flow');host.id='wave-flow';host.dataset.wavePlan=r.selected_plan_id||'UNSUPPORTED';host.dataset.followAllowed=String(r.punishment_follow_allowed);
    host.append(el('h3','라인전 목표에서 웨이브 계획으로'),el('p','설계 가설 · 앞으로 이런 상황이라면 · 현재 게임 관측 없음','source-note'));
    if(!r.supported){host.append(block('이 매치업의 웨이브 판단 미지원',r.unsupported_reason));return host;}
    host.append(block('먼저 밀 수 있는가?',r.first_push.reason+' 전진 처리 여건 입력도 가정이며 실제 선푸시 우위를 확인한 값이 아닙니다.'),block('먼저 밀려고 해야 하는가?',r.should_push),block('선택한 구간의 점검',r.period_note));
    const goal=el('div',null,'interactive-status');goal.id='wave-goal-first';goal.append(el('strong','라인전 목표: '+r.selected.objective),el('p','기본 웨이브 계획: '+r.selected.title));host.insertBefore(goal,host.children[2]);
    const fields=el('fieldset',null,'hypothesis-inputs');fields.append(el('legend','웨이브 조건 가정 · 기본값은 미확인'));
    root.LoadingWave.conditionDefs.forEach(d=>{const label=el('label'),select=el('select');select.id=d.key==='flow'?'wave-condition-flow':'wave-'+d.key;Object.entries(d.options).forEach(([v,t])=>{const o=el('option',t);o.value=v;select.append(o);});select.value=r.state.assumptions[d.key];select.addEventListener('change',()=>onAssumption(d.key,select.value));label.append(el('span',d.label),select);if(d.note)label.append(el('small',d.note));fields.append(label);});
    fields.append(button('쌓기·처리 비교 가정 예시','wave-example',()=>onPreset(root.LoadingWave.preset())),button('웨이브 조건 초기화','wave-reset',()=>onPreset(root.LoadingWave.defaultState().assumptions)));host.append(fields);
    const status=el('div',null,'interactive-status');status.id='wave-choice';status.setAttribute('role','status');status.append(el('strong','웨이브 목표: '+r.selected.title),el('p',r.selection_reason),el('p','조건·성향 변경은 관측이나 검증이 아닙니다. '+r.punishment_reason));host.append(status);
    const choices=el('div',null,'wave-comparison');choices.id='wave-comparison';
    const primaryIds=new Set([r.selected_plan_id,...r.plans.filter(p=>p.feasibility==='POSSIBLE'&&p.id!==r.selected_plan_id&&p.id!=='CHECK_WAVE').map(p=>p.id)].slice(0,2));
    const otherChoices=el('details');otherChoices.id='wave-other-options';otherChoices.append(el('summary','다른 웨이브 후보·미지원 이유'));
    r.plans.forEach(p=>{const card=el('article',null,'plan-option');card.dataset.waveOption=p.id;card.dataset.feasibility=p.feasibility;card.dataset.preferred=String(p.id===r.selected_plan_id);card.append(el('h4',p.title+(p.id===r.selected_plan_id?' · 현재 강조':'')),el('p',p.feasibility==='POSSIBLE'?'명시한 미래 가정 안의 후보':p.feasibility==='UNSUPPORTED'?'미지원 · 유지 기준 근거 부족':'실행 조건 미확인 또는 불충족','source-note'),el('p',p.objective));
      const detail=el('details');detail.append(el('summary','조건·비용 비교'),block('시작 조건',p.start),block('포기·소모·위험',p.costs),block('실패하면',p.next));card.append(detail);
      const b=button('이 웨이브 계획 살펴보기','wave-preview-'+p.id,()=>onPreview(p.id));b.disabled=p.feasibility!=='POSSIBLE';b.setAttribute('aria-pressed',String((preview||r.selected_plan_id)===p.id));card.append(b);(primaryIds.has(p.id)?choices:otherChoices).append(card);
    });host.append(choices,otherChoices);
    const plan=r.plans.find(p=>p.id===(preview||r.selected_plan_id)&&p.feasibility==='POSSIBLE')||r.selected;
    const active=el('article',null,'wave-active');active.id='wave-active';active.dataset.plan=plan.id;
    active.append(el('h3','살펴보는 웨이브 계획: '+plan.title),block('목표와 이유',plan.objective),block('상대가 만들 수 있는 상태',plan.opponent_goal),block('시작 조건',plan.start),block('구체적인 미니언 처리',plan.processing),block('기술 사용·보존',plan.skills),block('유지 조건',plan.maintenance),block('완료 기준',plan.completion),block('귀환·시야·합류로 전환',plan.conversion),block('실패 조건',plan.failure),block('실패 시 다음 선택',plan.next));
    const punishment=el('details');punishment.id='wave-punishment';punishment.append(el('summary','이 웨이브 계획에서 응징·딜교환은 어떻게 쓰나?'));
    plan.punishment.forEach(q=>{const card=el('article');card.append(el('h4',q.trigger),block('얻으려는 것',q.goal),block('수단',q.means),block('상대 반격',q.reply),block('끝낼 조건',q.end),block('웨이브 목표에 미치는 영향',q.wave_effect));punishment.append(card);});
    punishment.append(block('기존 짧은 후속 공격',r.punishment_follow_allowed?'처리·퇴로 예산을 남긴 공간 확보 가정에서만 짧은 후속을 검토합니다. 속박 적중은 덫 발동·킬을 보장하지 않습니다.':'귀환 준비·수급·처리 예산이 우선이거나 실행 조건이 없어, 기존 짧은 후속 공격을 기본 행동으로 선택하지 않습니다.'),block('기존 동료 쪽 수급','오는 웨이브를 감당할 동료 연결이 있을 때 받기를 돕습니다. 반대로 끝까지 밀어 넣는 것이 목적이면 너무 일찍 물러나 잔여를 남길 수 있어, 도달·처리 손실을 보고 전환합니다. 받기 역시 프리징·안전·완전 CS를 보장하지 않습니다.'));
    active.append(punishment);host.append(active);
    let selected=String(step),macro=null,zoom=null;
    const action=el('p',null,'selected-action');action.id='wave-selected-action';action.setAttribute('role','status');
    const sync=n=>{selected=String(n);onStep(selected);action.dataset.step=selected;action.textContent=fmt(plan.steps.find(s=>String(s.number)===selected)?.text||'전체 단계');host.querySelectorAll('[data-wave-step]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.waveStep===selected)));host.querySelectorAll('.wave-line').forEach(s=>s.dataset.activeStep=selected);if(zoom)zoom.querySelector('.wave-zoom-action').textContent=action.textContent;};
    const changeStep=n=>{sync(n);const b=macro?.querySelector('.map-step-controls [data-map-step="'+n+'"]');if(b&&b.getAttribute('aria-pressed')!=='true')b.click();};
    const steps=el('div',null,'wave-steps');steps.setAttribute('role','group');steps.setAttribute('aria-label','웨이브 행동 단계');
    plan.steps.forEach(s=>{const b=button(s.number+'. '+s.text,'wave-step-'+s.number,()=>changeStep(String(s.number)));b.dataset.waveStep=String(s.number);steps.append(b);});active.append(steps,action);
    function diagram(){
      const view=svg('svg',{viewBox:'0 0 720 400',class:'wave-line',role:'img','aria-label':'처리 전 예시와 원하는 처리 후 상태 · 모든 위치와 개수는 설명용 가정'});
      const colors=report.input.side==='RED'?['#ed858f','#80c4f5']:['#80c4f5','#ed858f'];
      const targets={SLOW_PUSH:[360,470],FAST_PUSH:[460,540],CRASH:[585,625],TRIM_RECEIVE:[195,280],TOWER_CS:[95,165],RETURNING:[180,270],CHECK_WAVE:[300,420]};
      const after=targets[plan.id]||[300,420];
      for(const [row,y,xs,title] of [[0,115,[300,420],'처리 전 · 흐름을 확인하는 예시'],[1,300,after,plan.id==='CHECK_WAVE'?'목표 미확인 · 성공 상태 생성 안 함':'원하는 처리 후 · 달성 예측 아님']]){
        view.append(svg('rect',{x:8,y:y-73,width:704,height:155,rx:14,fill:'#10212d',stroke:'#45606b'}),svg('text',{x:22,y:y-45,class:'wave-label'},title),svg('path',{d:'M 62 '+y+' H 658',stroke:'#728a91','stroke-width':6}));
        for(const [i,x] of [55,665].entries()){view.append(svg('rect',{x:x-14,y:y-22,width:28,height:44,fill:colors[i],opacity:.65}),svg('text',{x:i?570:20,y:y+65,class:'wave-label'},i?'상대 포탑':'내 포탑'));}
        xs.forEach((x,i)=>{const g=svg('g',{'data-minion-team':i?'ENEMY':'ALLY'});for(const dx of [-12,0,12])g.append(svg('circle',{cx:x+dx,cy:y,r:5,fill:colors[i]}));g.append(svg('text',{x:x-27,y:y+30,class:'wave-label'},i?'적 묶음':'아군 묶음'));view.append(g);});
        if(row&&plan.id!=='CHECK_WAVE'){const dir=after[0]>300?1:-1;view.append(svg('path',{'data-wave-direction':dir>0?'TOWARD_ENEMY':'TOWARD_OWN',d:'M '+(after[0]-20*dir)+' '+(y-12)+' L '+after[0]+' '+y+' L '+(after[0]-20*dir)+' '+(y+12),stroke:colors[0],fill:'none','stroke-width':3}));}
        for(const [id,x,dy,i] of [['Caitlyn',180,-15,0],['Lux',225,-28,0],['Kaisa',515,-15,1],['Nautilus',560,-28,1]]){
          const g=svg('g');g.append(svg('title',{},catalog.champions[id].name+' · 가정 위치'),svg('circle',{cx:x,cy:y+dy,r:19,stroke:colors[i],fill:'#162732','stroke-width':3}));const portrait=root.LoadingMap.portrait(catalog.champions[id],id==='Caitlyn').querySelector('svg');if(portrait){portrait.setAttribute('x',x-15);portrait.setAttribute('y',y+dy-15);portrait.setAttribute('width',30);portrait.setAttribute('height',30);g.append(portrait);}view.append(g);
        }
      }
      for(const [n,x] of [[1,45],[2,350],[3,650]]){
        const g=svg('g',{tabindex:0,role:'button','data-wave-step':n,'aria-label':n+'단계 설명 선택',class:'wave-diagram-control'});g.append(svg('circle',{cx:x,cy:202,r:19,fill:'#244656',stroke:'#e3c081','stroke-width':2}),svg('text',{x,y:208,'text-anchor':'middle',class:'wave-label'},n));g.addEventListener('click',()=>changeStep(String(n)));g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();changeStep(String(n));}});view.append(g);
      }
      return view;
    }
    const line=el('section',null,'wave-diagram');line.id='wave-diagram';line.append(el('h4','확대 라인 도식 · 미니언 처리'),el('p','전술 설명용 가정 · 점은 미니언 묶음 기호이며 실제·필요 수량이 아닙니다. 내 포탑이 왼쪽인 개념도입니다. 초상화 위치도 가정이며, 화살표는 원하는 흐름일 뿐 성공·정확한 속도·안전 경로가 아닙니다.','source-note'));
    line.append(diagram(),button('라인 도식 확대','wave-line-open',()=>{zoom=el('dialog',null,'wave-line-dialog');zoom.id='wave-line-dialog';const close=button('닫기','wave-line-close',()=>zoom.close()),range=el('input');range.id='wave-line-scale';range.type='range';range.min=100;range.max=200;range.value=100;range.step=25;range.setAttribute('aria-label','라인 도식 확대 비율');const container=el('div',null,'wave-line-scroll');container.tabIndex=0;const image=diagram();container.append(image);range.addEventListener('input',()=>{image.style.width=range.value+'%';});const text=el('p',action.textContent,'wave-zoom-action');zoom.append(el('h3','설명용 라인 도식 · 실제 관측 없음'),close,text,range,container);zoom.addEventListener('close',()=>{zoom.remove();zoom=null;host.querySelector('#wave-line-open')?.focus();});host.append(zoom);zoom.showModal();sync(selected);}));active.append(line);
    const macroArea=el('details');macroArea.id='wave-macro';macroArea.append(el('summary','전체 미니맵 · 귀환·정글·합류의 조건 연결'));
    macro=root.LoadingMap.create(root.LoadingWave.mapFor(report.input,plan),catalog,report.input,{selectedStep:selected,onSelect:sync});macroArea.append(macro);active.append(macroArea);
    const why=el('details');why.id='wave-why';why.append(el('summary','왜? · 웨이브 근거와 미확인'),block('공식 사실이 지지하는 범위',r.evidence.official_scope),block('설계 가설의 반례',r.counterexamples),block('하위 질문 · 원문·보류 이력 보존',r.question_ids.map(q=>q+' · 해당 웨이브의 스킬/대응 조건 보완 · 강의 구간 미연결')));
    const ids=new Set(plan.evidence_ids);report.evidence.facts.filter(f=>ids.has(f.id)).forEach(f=>{const item=el('details'),a=el('a','공식 출처 ↗');a.href=f.url;a.target='_blank';a.rel='noopener noreferrer';item.append(el('summary',root.SkillDisplay.factLabel(f.id.split(':')[1],f)),el('p',f.text),a,el('p','자료 '+f.patch));const raw=el('blockquote');raw.textContent=f.raw_excerpt||f.text;item.append(raw);why.append(item);});
    active.append(why);sync(selected);return host;
  }
  root.LoadingWaveView={create};
})(window);

/* Generated preference/sequence output; controls are future hypotheses, not observations. */
(function(root){
 'use strict';
 function create({result:r,report,catalog,engagement,onChange,onReset}){
  const T=root.LoadingExchange,G=root.LoadingEngagement,skill=(id,slot)=>{const f=catalog.champions[id]?.facts.find(f=>f.slot===slot);return f?root.SkillDisplay.factLabel(id,f):'공식 수단 미확인';},el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!=null)n.textContent=text;if(cls)n.className=cls;return n;},list=(vs,ordered=false)=>{const n=el(ordered?'ol':'ul');vs.forEach(v=>n.append(el('li',v)));return n;},block=(title,value)=>{const n=el('div',null,'interactive-block');n.append(el('h5',title),Array.isArray(value)?list(value):el('p',value));return n;};
  const host=el('section',null,'exchange-flow');host.id='exchange-flow';host.dataset.ourMode=r.ours.mode;host.dataset.theirMode=r.theirs.mode;host.dataset.attackGate=r.attack_gate;
  host.append(el('h4','짧게 끊을까, 공격을 이어갈까?'),el('p','상대적으로 나은 교환 방식의 후보와 실제 교전 우세는 별도입니다. 실제 매치업 비교 없음 · 기전에서 만든 설계 가설','source-note'));
  const status=el('p','실제 상대보다 유리한가: '+engagement.advantage_label+' · 올인·추격 허용으로 바뀌지 않습니다.','interactive-status');status.id='exchange-actual-advantage';host.append(status);if(!r.supported){host.append(el('p','이 조합의 교환 길이·공격 순서·미니언 영향은 미지원입니다. 다른 조합의 기술 가정을 대신 표시하지 않습니다.'));return host;}
  const grid=el('div',null,'exchange-grid');
  for(const [side,title] of [['ours','우리의 교환 길이'],['theirs','상대가 선호할 수 있는 길이']]){
   const p=r[side],card=el('article',null,'plan-option');card.id='exchange-'+side;card.dataset.classification=p.classification;card.dataset.mode=p.mode;card.append(el('h4',title+' · '+p.preferred_exchange),block('이유',p.reason));
   if(side==='theirs')card.append(el('p','상대 플레이어의 실제 의도는 미확인입니다.','source-note'));
   const body=el(p.classification==='UNKNOWN'?'details':'div');if(p.classification==='UNKNOWN')body.append(el('summary','미채택 조건부 절차와 필요한 확인 보기'));
   body.append(block('시작 조건',p.start_conditions),block('공격 순서',p.attack_order),block('끝낼 시점',p.end),block('더 이어갈 조건',p.continue_if),block('상대 대응 시 대안',p.reply_alternative));card.append(body);
   const why=el('details');why.id='exchange-why-'+side;why.append(el('summary','왜? · 이 후보의 공식 기전과 한계'),el('p',r.evidence.scope));
   for(const f of r.evidence.facts.filter(f=>p.evidence_ids.includes(f.id))){const owner=f.id.split(':')[1],quote=el('details');quote.append(el('summary',root.SkillDisplay.factLabel(owner,f)),el('blockquote',f.raw_excerpt||f.text));const a=el('a','공식 출처 ↗');a.href=f.url;a.target='_blank';a.rel='noopener noreferrer';quote.append(a,el('p','자료 '+f.patch,'source-note'));why.append(quote);}why.append(el('p','직접 비교가 필요한 기존 질문: '+r.evidence.question_ids.join(' / ')));card.append(why);grid.append(card);
  }host.append(grid);
  const wave=el('div',null,'interactive-status');wave.id='exchange-wave';wave.dataset.adoption=r.wave.adoption;wave.append(block('현재 웨이브 목표와 비용',r.wave.cost),block('미니언·처리 방식의 영향',r.wave.minion_effect),block('상대 방식에 그대로 맞춰 싸우지 않으려면',r.wave.avoid_opponent_pattern));if(r.attack_gate==='NO_ADDITIONAL_ATTACK')wave.append(el('p','종료 가정 때문에 추가 공격 후보·후속 공격 지도를 제외합니다. 수급·처리 후보가 자동으로 없어지는 것은 아닙니다.'));host.append(wave);
  const controls=el('details');controls.id='exchange-conditions';controls.append(el('summary','강화·보호·연결이 달라진다면 · 가정 바꾸기'));
  for(const [side,title] of [['ours','우리'],['theirs','상대']]){const fields=el('fieldset',null,'hypothesis-inputs');fields.append(el('legend',title+' · 현재 게임 관측 아님'));
   for(const def of T.defs){const label=el('label'),select=el('select');select.id='exchange-'+side+'-'+def.key;for(const [value,name] of Object.entries(def.options)){const o=el('option',name);o.value=value;select.append(o);}select.value=r.state[side][def.key];select.addEventListener('change',()=>onChange(side,def.key,select.value));label.append(el('span',def.label),select);
    if(def.key==='cover'){const owner=r[side].cover_owner,slot=side==='ours'?(owner==='Lulu'?'E':'W'):'W',f=catalog.champions[owner]?.facts.find(f=>f.slot===slot);label.append(el('small',f?root.SkillDisplay.factLabel(owner,f)+' · 대상 '+catalog.champions[r[side].cover_target].name:'보호 적용 대상 미확인'));}
    if(def.key==='window')label.append(el('small',side==='ours'?(r.ours.cover_target==='Yunara'?'반복 가정은 '+skill('Yunara','Q')+' 등 관련 수단의 실제 강화·가용을 가정합니다. 초월 상태·지속시간을 자동 추정하지 않습니다.':skill('Caitlyn','W')+'·'+skill('Caitlyn','E')+' 조건의 '+skill('Caitlyn','P')+' 기회와 기본 공격 누적은 다릅니다. 지속 교전 선호는 미검증입니다.'):(r.theirs.cover_target==='Nautilus'&&engagement.matchup.startsWith('Yunara')?'루시안의 기술→'+skill('Lucian','P')+' 한 창과 다음 기술이 남는 반복을 구분합니다.':skill('Kaisa','P')+'·'+skill('Kaisa','E')+' 상태를 가정합니다. 중첩 발동 수·피해량은 미확인입니다.')));fields.append(label);
   }controls.append(fields);
  }
  const reset=el('button','교환 길이 가정 초기화');reset.id='exchange-reset';reset.type='button';reset.addEventListener('click',onReset);controls.append(reset);host.append(controls);
  const compare=el('details');compare.id='exchange-periods';compare.append(el('summary','여섯 구간의 교환 길이 후보 비교'));
  const wrap=el('div',null,'table-scroll');wrap.tabIndex=0;wrap.setAttribute('role','region');wrap.setAttribute('aria-label','구간별 양쪽 교환 선호 · 좌우 스크롤');const table=el('table'),head=el('thead'),hr=el('tr');['구간','우리의 상대적 방식','상대의 가능한 방식','실제 교전 우세','근거'].forEach(t=>hr.append(el('th',t)));head.append(hr);table.append(head);const body=el('tbody');
  for(const row of report.lane.rows){const g=G.evaluate(report,catalog,{...engagement.state,milestone:row.id},engagement.wave_goal),x=T.evaluate(report,catalog,g,r.state),tr=el('tr');tr.dataset.exchangePeriod=row.id;[row.period,x.ours.preferred_exchange,x.theirs.preferred_exchange,g.advantage_label,'공식 기전 / 조건부 해석 · 매치업 비교 없음'].forEach(t=>tr.append(el('td',t)));body.append(tr);}table.append(body);wrap.append(table);compare.append(wrap,el('p','같은 가정을 다른 구간에 적용해 비교한 표입니다. 레벨만으로 교환 길이나 상대 우세를 정하지 않습니다.','source-note'));host.append(compare);
  return host;
 }
 root.LoadingExchangeView={create};
})(window);

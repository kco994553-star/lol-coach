/* Study reuses the exact reviewed claim registry; it does not invent another lesson corpus. */
(async function(){
  'use strict';
  const host=document.getElementById('coach-lessons');if(!host)return;
  let skillScope=[];
  const el=(tag,text)=>{const n=document.createElement(tag);if(text)n.textContent=window.SkillDisplay?window.SkillDisplay.format(text,{champions:skillScope}):text;return n;};
  try{
    const responses=await Promise.all([fetch('./loading-knowledge.json'),fetch('./loading-data.json')]);
    if(responses.some(r=>!r.ok))throw Error('공통 근거 자료를 불러오지 못했습니다.');
    const [knowledge,catalog]=await Promise.all(responses.map(r=>r.json()));
    for(const m of knowledge.matchups){
      skillScope=[...m.allies,...m.enemies];
      const section=el('article');section.id='coach-lesson-'+m.id;section.className='coach-card';
      section.append(el('h3',m.title),el('p',(m.role==='TOP'?'탑의 자리·CS 역할':'원딜·서포터의 교환·지원 역할')+' → 유형별 수단 → 기본 계획 → 조건·반례'));
      for(const claim of m.claims){
        const detail=el('details');detail.className='coach-details';detail.append(el('summary',claim.display_text||claim.text));
        detail.append(el('p',claim.basis==='DESIGN_HYPOTHESIS'?'공식 기전·공략을 적용한 해석 가설':'공략 기반 판단 · 원문·적용 범위 검토'));
        const conditions=el('ul');for(const text of [...claim.conditions,...claim.counterexamples])conditions.append(el('li',text));detail.append(conditions);
        for(const source of knowledge.sources.filter(s=>claim.source_ids.includes(s.id))){const a=el('a',source.title+' ↗');a.href=source.url;a.target='_blank';a.rel='noopener noreferrer';detail.append(a);}
        section.append(detail);
      }
      const q=el('details');q.className='coach-details';q.append(el('summary','선택 질문 · 교전 강점을 얻으면 끝까지 추격해야 할까요?'),el('p','아니요. CS·공간·웨이브 처리도 이득입니다. 처치와 추격에는 남은 반격·이탈·후속 근거가 따로 필요합니다.'));
      section.append(q);const link=el('a','10픽 전략에서 조건 비교하기 →');link.href='./loading.html';section.append(link);host.append(section);
    }
    const target=document.getElementById(location.hash.slice(1));if(target&&host.contains(target))target.scrollIntoView({block:'start',behavior:'auto'});
  }catch(error){host.append(el('p',error.message+' 기존 6장면 연습은 아래에서 계속 사용할 수 있습니다.'));}
})();

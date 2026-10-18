/* Study reuses the exact reviewed claim registry; it does not invent another lesson corpus. */
(async function(){
  'use strict';
  const host=document.getElementById('coach-lessons');if(!host)return;
  let skillScope=[];
  const el=(tag,text)=>{const n=document.createElement(tag);if(text){const readable=window.LoadingPlanboard?.plainLanguage?window.LoadingPlanboard.plainLanguage(text):text;n.textContent=window.SkillDisplay?window.SkillDisplay.format(readable,{champions:skillScope}):readable;}return n;};
  try{
    const responses=await Promise.all([fetch('./loading-knowledge.json'),fetch('./loading-data.json')]);
    if(responses.some(r=>!r.ok))throw Error('공통 근거 자료를 불러오지 못했습니다.');
    const [knowledge,catalog]=await Promise.all(responses.map(r=>r.json()));
    const formationHost=document.getElementById('formation-study');
    if(formationHost&&window.LoadingFormation){
      const input={patch:catalog.source_patch,own_champion:'Caitlyn',own_position:'BOTTOM',allies:[['Ornn','TOP'],['Sejuani','JUNGLE'],['Ahri','MID'],['Caitlyn','BOTTOM'],['Lux','SUPPORT']].map(([champion,position])=>({champion,position})),enemies:[['Fiora','TOP'],['LeeSin','JUNGLE'],['Zed','MID'],['Kaisa','BOTTOM'],['Nautilus','SUPPORT']].map(([champion,position])=>({champion,position}))};
      const model=window.LoadingFormation.evaluate(input,{...catalog,coaching_knowledge:knowledge});formationHost.append(window.LoadingFormation.create(model,catalog));
      const why=document.getElementById('formation-study-why');if(why){why.append(el('p',model.evidence?.scope||model.reason));for(const s of model.evidence?.sources||[]){const a=el('a',s.author+' · '+s.title+' ↗');a.href=s.url;a.target='_blank';a.rel='noopener noreferrer';why.append(a,el('p','공략 표기 패치: '+(s.patch||'미확인')+' · 작성·수정일: '+(s.date||s.research_metadata?.updated_at||'미확인')),el('p','공략의 적용 한계: '+(Array.isArray(s.limits)?s.limits.join(' '):s.limits||'미확인')));}}
    }
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
    if(knowledge.lecture_candidates?.length){const d=el('details');d.className='coach-details';d.append(el('summary','사용자 제공 강의 후보 · 본문·관련 구간 검토 전'),el('p','영상 제목·설명만으로 전술 근거를 채택하지 않습니다. 아래 후보는 기존 영상 원장·진단 순서를 통과한 뒤 검토합니다.'));knowledge.lecture_candidates.forEach((v,i)=>{const p=el('p'),a=el('a','강의 후보 '+(i+1)+' ↗');a.href=v.url;a.target='_blank';a.rel='noopener noreferrer';p.append(a);d.append(p);});host.append(d);}
    const openLesson=()=>{const target=document.getElementById(location.hash.slice(1));if(target&&(target===host||host.contains(target))){for(let n=target.parentElement;n;n=n.parentElement)if(n.tagName==='DETAILS')n.open=true;target.scrollIntoView({block:'start',behavior:'auto'});}};window.addEventListener('hashchange',openLesson);openLesson();
  }catch(error){host.append(el('p',error.message+' 기존 6장면 연습은 아래에서 계속 사용할 수 있습니다.'));}
})();

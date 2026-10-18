/* Shared illustrative teamfight geometry. Source-bound threat references, no live positions or win model. */
(function(root,factory){
  if(typeof module==='object'&&module.exports)module.exports=factory(require('./formation-ranges.js'));
  else root.LoadingFormation=factory(root.FormationRanges);
})(typeof globalThis!=='undefined'?globalThis:this,function(rangeData){
  'use strict';
  const order={TOP:0,JUNGLE:1,MID:2,BOTTOM:3,SUPPORT:4};
  const sorted=rows=>[...rows].sort((a,b)=>(order[a.position]??9)-(order[b.position]??9)||a.champion.localeCompare(b.champion));
  function evaluate(input,catalog){
    const no=reason=>({version:'teamfight-formation-v1',supported:false,reason,scenes:[],origin:'ILLUSTRATIVE_HYPOTHESIS',actual_enemy_positions:null});
    const gameplayPatch=p=>typeof p==='string'&&/^\d+\.\d+(?:\.\d+)?$/.test(p)?p.split('.').slice(0,2).join('.'):null;
    if(!gameplayPatch(input.patch)||gameplayPatch(input.patch)!==gameplayPatch(catalog.source_patch))return no('입력 패치와 기술 자료가 다르거나 패치를 확인할 수 없습니다.');
    const sides={ALLY:sorted(input.allies||[]),ENEMY:sorted(input.enemies||[])};
    if(Object.values(sides).some(s=>s.length!==5||s.some(p=>!catalog.champions[p.champion])))return no('양 팀의 다섯 챔피언을 확인해야 배치를 비교할 수 있습니다.');
    const sideOf=id=>Object.keys(sides).find(t=>sides[t].some(p=>p.champion===id));
    const cait=sideOf('Caitlyn'),kai=sideOf('Kaisa');
    if(!cait||!kai||cait===kai)return no('현재 비교는 케이틀린과 카이사가 상대 팀에 있는 구도부터 지원합니다.');
    const profile=id=>catalog.champions[id]?.profile||{};
    const front=id=>(profile(id).protection||[]).includes('FRONTLINE');
    const access=id=>(catalog.champions[id]?.official_tags||[]).some(t=>t==='Assassin'||t==='Fighter');
    const cFront=sides[cait].filter(p=>front(p.champion));
    const kFront=sides[kai].filter(p=>front(p.champion));
    if(!cFront.length||!kFront.length)return no('양 팀 전방을 맡을 수단이 확인되지 않아 이 배치 예시를 적용하지 않습니다.');
    if(!sides[cait].some(p=>(profile(p.champion).protection||[]).includes('PEEL')))return no('케이틀린과 연결할 아군 보호 수단이 확인되지 않아 이 배치 예시를 적용하지 않습니다.');
    const name=id=>catalog.champions[id].name;
    const key=(id,slot)=>{const f=catalog.champions[id].facts.find(f=>f.slot===slot);return name(id)+'의 '+(f?.name||'기술 미확인')+'('+slot+')';};
    const cPositions=[[20,50],[15,17],[15,83],[40,31],[40,70]];
    const kPositions=[[82,50],[85,17],[85,83],[60,31],[60,70]];
    function roster(team,carry,positions){
      const picks=sides[team],back=picks.filter(p=>p.champion!==carry&&!front(p.champion)),ahead=picks.filter(p=>front(p.champion));
      return [{...picks.find(p=>p.champion===carry),role:'후방 연결 후보'},...back.map(p=>({...p,role:'후방 연결 후보'})),...ahead.map(p=>({...p,role:'전방 연결 후보'}))].map((p,i)=>({champion:p.champion,name:name(p.champion),team,position:p.position,self:team==='ALLY'&&p.champion===input.own_champion,role:p.role,positions:Array.from({length:3},()=>({x:positions[i][0],y:positions[i][1]}))}));
    }
    const base=[...roster(cait,'Caitlyn',cPositions),...roster(kai,'Kaisa',kPositions)];
    const commonConditions=['양 팀이 모두 합류하고 해당 기술을 배워 사용할 수 있다는 비교 가정입니다.','체력·아이템·지형과 적중 여부에 따라 결과가 바뀝니다.'];
    const frontal={id:'FRONT_CONNECTED',title:'정면 대형 · 전방 뒤에서 함께 공격',favored_champion:'Caitlyn',favored_team:cait,basis:'DESIGN_HYPOTHESIS',winner:'UNDETERMINED',actors:base,
      goal:'케이틀린은 전방·보호 뒤에서 닿는 적부터 공격한다.',
      reason:'정면을 유지하며 사거리를 쓰는 예시다. 정면 5대5의 승리를 뜻하지 않으며, 붙어 서거나 전방이 끊기면 계획을 바꾼다.',
      conditions:[...commonConditions,'전방·보호 기술이 케이틀린과 연결되고 측면 접근을 함께 막을 수 있어야 합니다.'],
      failure:['아군이 한 점에 뭉쳐 광역 진입을 허용하거나 전방·보호가 끊기면 정면 배치도 불리해질 수 있습니다.','측면에서 들어온 상대를 무시하고 앞의 적만 계속 공격하지 않습니다.'],
      steps:[{title:'① 준비 배치',action:'전방과 후방을 나누되 보호가 닿을 만큼 연결한다. 같은 지점에 겹쳐 서지 않는다.'},{title:'② 공격 시작',action:'아군이 적을 묶고 함께 공격할 수 있으면 케이틀린이 닿는 적부터 친다. '+key('Caitlyn','W')+'는 설치·발동할 여유가 있을 때 잇는다.'},{title:'③ 다시 연결',action:'측면 접근으로 보호가 끊기면 전방 뒤의 다른 자리로 옮긴다. '+key('Caitlyn','E')+'를 썼다는 이유만으로 모든 접근을 피했다고 보지 않는다.'}]};
    const flankActors=JSON.parse(JSON.stringify(base));
    const kaiActor=flankActors.find(a=>a.champion==='Kaisa'),target=flankActors.find(a=>a.champion==='Caitlyn');
    kaiActor.role='연결된 진입·후속 후보';kaiActor.positions=[{x:77,y:84},{x:34,y:52},{x:77,y:84}];
    const flankers=flankActors.filter(a=>a.team===kai&&a.champion!=='Kaisa'&&!front(a.champion)&&access(a.champion));
    const flankPoints=[[[48,10],[35,12],[48,10]],[[80,20],[85,30],[80,20]],[[85,52],[85,55],[85,52]]];
    flankers.forEach((a,i)=>{a.role='측면 진입 후보';a.positions=flankPoints[i].map(([x,y])=>({x,y}));});
    target.positions=[{x:20,y:50},{x:18,y:38},{x:23,y:48}];
    // Protection being unavailable is a scenario assumption, never inferred from distance alone.
    const separated=flankActors.filter(a=>a.team===cait&&a.champion!=='Caitlyn');
    [[17,82],[44,84],[63,18],[59,62]].forEach(([x,y],i)=>separated[i].positions[1]={x,y});
    const kFrontActor=flankActors.find(a=>a.team===kai&&front(a.champion));kFrontActor.positions=[{x:64,y:60},{x:82,y:82},{x:63,y:61}];
    const flank={id:'FLANK_ISOLATE',title:'측면 구도 · 고립된 대상에 후속',favored_champion:'Kaisa',favored_team:kai,basis:'DESIGN_HYPOTHESIS',winner:'UNDETERMINED',actors:flankActors,
      goal:'카이사는 아군의 진입에 맞춰 고립된 대상을 함께 공격한다.',
      reason:key('Kaisa','R')+'과 아군 제어를 연결하는 예시다. 흩어져 있는 것만으로 유리해지지 않는다.',
      conditions:[...commonConditions,'카이사에게 진입 가능한 표식과 사냥본능(R)이 있고, 아군 후속이 같은 대상에 닿아야 합니다.','서로 다른 각도로 움직여도 아군끼리 지원이 끊기지 않고, 남은 보호·반격과 빠져나올 길을 감당할 수 있어야 합니다.'],
      failure:['산개한 아군이 먼저 분리되어 잡히거나 카이사의 후속이 끊기면 포위를 접습니다.','상대 보호가 남아 있거나 고립되지 않았다면 억지로 뛰지 않고 아군과 연결해 닿는 적을 공격합니다.'],
      steps:[{title:'① 준비 배치',action:'접근 수단이 있는 아군이 측면 각도를 만든다는 가정이다. 혼자 먼저 들어가거나 실제 적 위치를 안다고 가정하지 않는다.'},{title:'② 공격 시작',action:'대상이 보호에서 떨어지고 표식·아군 공격이 연결될 때만 '+key('Kaisa','R')+' 진입을 비교한다. 남은 보호·반격이 있으면 진입을 강제하지 않는다.'},{title:'③ 다시 연결',action:'상대 보호가 닿거나 아군과 떨어지면 진입·추격을 끝내고 아군 쪽으로 연결한다. 진입 이후 빠져나올 수 있다는 보장은 없다.'}]};
    // A selected attack/reposition changes the illustrative layout, never the combat verdict.
    frontal.actors.find(a=>a.champion==='Caitlyn').positions[2]={x:25,y:60};
    frontal.actors.find(a=>a.champion==='Caitlyn').positions[1]={x:31,y:50};
    frontal.actors.find(a=>a.team===kai&&front(a.champion)).positions[1]={x:59,y:50};
    // Keep carry examples fixed; resolve other portrait collisions as display geometry only.
    for(const scene of [frontal,flank])for(let step=0;step<3;step++){
      const placed=[];
      const actors=[...scene.actors].sort((a,b)=>Number(['Caitlyn','Kaisa'].includes(b.champion))-Number(['Caitlyn','Kaisa'].includes(a.champion)));
      for(const a of actors){
        const wanted=a.positions[step],clear=p=>placed.every(q=>Math.hypot(p.x-q.x,p.y-q.y)>=18);
        if(!clear(wanted)){
          const points=[];for(let x=12;x<=88;x+=19)for(let y=12;y<=88;y+=19)points.push({x,y});
          const free=points.filter(clear).sort((p,q)=>Math.hypot(p.x-wanted.x,p.y-wanted.y)-Math.hypot(q.x-wanted.x,q.y-wanted.y)||p.x-q.x||p.y-q.y);
          if(free.length)a.positions[step]=free[0];
        }
        placed.push(a.positions[step]);
      }
    }
    const scale=2000;
    for(const s of [frontal,flank])s.cohesion=[0,1,2].map(step=>{
      const nearest=s.actors.map(a=>{const peers=s.actors.filter(b=>b.team===a.team&&b.champion!==a.champion).map(b=>({champion:b.champion,distance:Math.hypot(a.positions[step].x-b.positions[step].x,a.positions[step].y-b.positions[step].y)})).sort((a,b)=>a.distance-b.distance||a.champion.localeCompare(b.champion)),p=peers[0];return {champion:a.champion,team:a.team,ally:p.champion,distance_game_units:Math.round(p.distance*scale/100),origin:'ILLUSTRATIVE_GEOMETRY'};});
      const links=[...new Map(nearest.map(n=>[[n.team,...[n.champion,n.ally].sort()].join(':'),{team:n.team,from:n.champion,to:n.ally}])).values()];
      return {nearest,links,tactical_isolation:'NOT_INFERRED',label:s.id==='FRONT_CONNECTED'?'전방·후방 연결을 남기는 배치 예시':'여러 각도에서 접근하는 배치 예시 · 고립 여부는 보호·후속 단절 조건이 별도'};
    });
    const threats=Object.fromEntries(base.map(a=>[a.champion,rangeData?.source_patch===catalog.source_patch?rangeData.champions[a.champion]?.threat:null]));
    const extents=[frontal,flank].flatMap(s=>s.actors.flatMap(a=>a.positions.map(p=>{const t=threats[a.champion],radius=Math.max(t?.direct?.radius||0,t?.approach?.radius||0);return {x:p.x*scale/100,y:p.y*scale/100,radius};})));
    const minX=Math.min(...extents.map(p=>p.x-p.radius)),maxX=Math.max(...extents.map(p=>p.x+p.radius)),minY=Math.min(...extents.map(p=>p.y-p.radius)),maxY=Math.max(...extents.map(p=>p.y+p.radius)),width=Math.max(maxX-minX,maxY-minY)*1.1;
    const threatReference={champions:threats,risk_verdict:'NOT_COMPUTED',origin:'ILLUSTRATIVE_MECHANISM_REFERENCE',view:{x:(minX+maxX-width)/2,y:(minY+maxY-width)/2,width},layout_width_game_units:scale,
      scope:'1차는 현재 자리에서 쓸 대표 수단, 2차는 접근 수단까지 쓰는 조건부 위협입니다. 원 밖의 다른 기술과 실제 피해·승패는 별도입니다.'};
    const sourceIds=new Set(['A:S3','D:S1']);
    const ranges=rangeData?.source_patch===catalog.source_patch?Object.fromEntries(base.map(a=>[a.champion,rangeData.champions[a.champion]])):{};
    return {version:'teamfight-formation-v1',supported:true,origin:'ILLUSTRATIVE_HYPOTHESIS',actual_enemy_positions:null,default_scene:input.own_champion==='Kaisa'?'FLANK_ISOLATE':'FRONT_CONNECTED',scenes:[frontal,flank],threat_reference:threatReference,range_reference:{origin:'ILLUSTRATIVE_SCALE',board_width_game_units:scale,champions:ranges,limits:rangeData?.limits||['공식 기본 공격 거리 자료가 없어 원을 표시하지 않습니다.']},
      evidence:{official:[...['Caitlyn:W','Caitlyn:E','Kaisa:R'].map(ref=>{const [champion,slot]=ref.split(':');return {champion,...catalog.champions[champion].facts.find(f=>f.slot===slot)};}),{...catalog.champions.Kaisa.facts.find(f=>f.slot==='R'),champion:'Kaisa',locator:'data.Kaisa.spells.3.tooltip',text:'플라즈마 표식이 남은 적 챔피언 근처로 빠르게 돌진',raw_excerpt:'카이사가 <keywordMajor>플라즈마</keywordMajor> 표식이 남은 적 챔피언 근처로 빠르게 돌진하며,'}],sources:(catalog.coaching_knowledge?.sources||[]).filter(s=>sourceIds.has(s.id)),
        scope:'공식 기술은 수단을, 기존 공략은 거리·접근 조건을 뒷받침합니다. 열 명의 좌표·순서와 어느 대형을 선호하는지는 설명용 해석 가설이며 검토된 승패 판정이 아닙니다.'}};
  }
  let nextId=0;
  function create(model,catalog){
    const doc=document,prefix='formation-'+(++nextId),root=doc.createElement('section');root.className='formation-explorer';
    const el=(tag,text,cls)=>{const n=doc.createElement(tag);if(text)n.textContent=text;if(cls)n.className=cls;return n;};
    if(!model?.supported){root.append(el('p',model?.reason||'이 조합의 한타 배치 비교는 아직 지원하지 않습니다.','coach-muted'));return root;}
    let scene=model.default_scene,step=0,actor=null,rangeMode='ALL',showLinks=true,viewMode='OVERVIEW',pickerOpen=false;
    const main=el('div'),dialog=el('dialog',null,'formation-dialog'),stage=el('div'),close=el('button','닫기');close.type='button';close.addEventListener('click',()=>dialog.close());dialog.append(close,stage);root.append(main,dialog);
    dialog.setAttribute('aria-label','한타 구도 확대');let zoomOpener=null;
    dialog.addEventListener('close',()=>{const opener=main.querySelector('[data-formation-zoom]')||zoomOpener;opener?.focus({preventScroll:true});});
    function render(target,isZoom){
      const focus=target.contains(doc.activeElement)?doc.activeElement.dataset.formationControl:null;
      target.replaceChildren();const s=model.scenes.find(s=>s.id===scene);const frame=viewMode==='OVERVIEW'?model.threat_reference.view:{x:0,y:0,width:model.threat_reference.layout_width_game_units};const project=p=>({x:(p.x*model.threat_reference.layout_width_game_units/100-frame.x)/frame.width*100,y:(p.y*model.threat_reference.layout_width_game_units/100-frame.y)/frame.width*100});
      const controls=el('div',null,'formation-controls');controls.setAttribute('role','group');controls.setAttribute('aria-label','비교할 한타 구도');
      const btn=(label,key,selected,fn)=>{const b=el('button',label);b.type='button';b.dataset.formationControl=key;b.setAttribute('aria-pressed',String(selected));b.addEventListener('click',fn);return b;};
      model.scenes.forEach(s=>controls.append(btn(s.favored_champion==='Caitlyn'?'정면 대형':'측면·고립',s.id,s.id===scene,()=>{scene=s.id;step=0;actor=null;refresh();})));target.append(controls,el('h4',s.goal),el('p',s.reason));
      const rangeControls=el('div',null,'formation-controls');rangeControls.classList.add('formation-range-controls');rangeControls.setAttribute('role','group');rangeControls.setAttribute('aria-label','위협 범위와 동료 연결 표시');[['ALL','전체 10명 원'],['SELECTED','선택한 챔피언 원'],['OFF','원 숨기기']].forEach(([v,label])=>rangeControls.append(btn(label,'range-'+v,rangeMode===v,()=>{rangeMode=v;refresh();})));rangeControls.append(btn('동료 연결선','links',showLinks,()=>{showLinks=!showLinks;refresh();}));target.append(rangeControls);
      const steps=el('div',null,'formation-controls');steps.setAttribute('role','group');steps.setAttribute('aria-label','한타 행동 단계');s.steps.forEach((v,i)=>steps.append(btn(v.title,'step-'+i,i===step,()=>{step=i;actor=null;refresh();})));target.append(steps);const views=el('div',null,'formation-controls');views.setAttribute('role','group');views.setAttribute('aria-label','배치와 전체 위협 범위 보기');[['OVERVIEW','전체 범위 보기'],['LAYOUT','배치 확대']].forEach(([v,label])=>views.append(btn(label,'view-'+v,viewMode===v,()=>{viewMode=v;refresh();})));target.append(views);
      const arena=el('div',null,'formation-arena');arena.dataset.formationScene=s.id;arena.dataset.formationStep=step;arena.setAttribute('aria-label','가정한 양 팀 열 명의 배치');
      const line=el('div',null,'formation-contact');line.setAttribute('aria-hidden','true');arena.append(line);
      const ns='http://www.w3.org/2000/svg',overlay=doc.createElementNS(ns,'svg');overlay.setAttribute('viewBox','0 0 100 100');overlay.classList.add('formation-ranges');overlay.setAttribute('aria-hidden','true');
      if(showLinks)for(const link of s.cohesion[step].links){const a=s.actors.find(a=>a.champion===link.from),b=s.actors.find(a=>a.champion===link.to),l=doc.createElementNS(ns,'line');for(const [k,v]of Object.entries({x1:project(a.positions[step]).x,y1:project(a.positions[step]).y,x2:project(b.positions[step]).x,y2:project(b.positions[step]).y}))l.setAttribute(k,v);l.setAttribute('class','formation-connection '+link.team.toLowerCase());overlay.append(l);}
      for(const a of s.actors){
        const profile=model.threat_reference.champions[a.champion],selected=actor?a.team+':'+a.champion===actor:a.self;
        if(rangeMode==='OFF'||rangeMode==='SELECTED'&&!selected)continue;
        for(const [tier,ref]of [['COMMITTED',profile?.approach],['DIRECT',profile?.direct]]){
          if(!(ref?.radius>0))continue;const p=project(a.positions[step]),circle=doc.createElementNS(ns,'circle');
          for(const [k,v]of Object.entries({cx:p.x,cy:p.y,r:ref.radius/frame.width*100,'data-range-champion':a.champion,'data-range-tier':tier,'data-range-value':ref.radius}))circle.setAttribute(k,v);
          circle.setAttribute('class','formation-range '+a.team.toLowerCase()+' '+tier.toLowerCase()+(a.self?' is-self':'')+(actor&&!selected?' is-muted':'')+(selected&&actor?' is-selected':'')+(profile.status==='BASIC_ONLY'?' is-partial':''));
          const title=doc.createElementNS(ns,'title');title.textContent=ref.label+' · '+ref.radius+' · '+(tier==='DIRECT'?'1차 대표 위협':'2차 조건부 접근');circle.append(title);overlay.append(circle);
        }
      }
      arena.append(overlay);
      if(step){
        const arrowScale=model.threat_reference.layout_width_game_units/frame.width;
        const ns='http://www.w3.org/2000/svg',svg=doc.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 100 100');svg.setAttribute('preserveAspectRatio','none');svg.setAttribute('aria-hidden','true');svg.classList.add('formation-arrows');
        for(const a of s.actors){const from=project(a.positions[step-1]),to=project(a.positions[step]),dx=to.x-from.x,dy=to.y-from.y,len=Math.hypot(dx,dy);if(len<8*arrowScale)continue;const path=doc.createElementNS(ns,'path');path.setAttribute('d',`M ${from.x} ${from.y} L ${to.x-dx/len*6*arrowScale} ${to.y-dy/len*6*arrowScale}`);path.setAttribute('class',a.team.toLowerCase());svg.append(path);const tip=doc.createElementNS(ns,'path'),x=to.x-dx/len*5*arrowScale,y=to.y-dy/len*5*arrowScale;tip.setAttribute('d',`M ${x-dx/len*3*arrowScale+dy/len*2*arrowScale} ${y-dy/len*3*arrowScale-dx/len*2*arrowScale} L ${x} ${y} L ${x-dx/len*3*arrowScale-dy/len*2*arrowScale} ${y-dy/len*3*arrowScale+dx/len*2*arrowScale}`);tip.setAttribute('class',a.team.toLowerCase());svg.append(tip);}
        arena.append(svg);
      }
      for(const a of s.actors){
        const token=btn('',a.team+':'+a.champion,actor===a.team+':'+a.champion,()=>{actor=a.team+':'+a.champion;refresh();});token.className='formation-actor '+a.team.toLowerCase()+(a.self?' is-self':'');token.style.left=project(a.positions[step]).x+'%';token.style.top=project(a.positions[step]).y+'%';token.dataset.formationChampion=a.champion;token.dataset.team=a.team;token.setAttribute('aria-label',(a.team==='ALLY'?'아군 ':'상대 ')+a.name+' · '+a.role+' · 가정 위치');
        const p=catalog.champions[a.champion]?.portrait,portrait=el('span',null,'formation-portrait');portrait.setAttribute('aria-hidden','true');
        if(p){portrait.style.backgroundImage='url("./'+p.sprite+'")';portrait.style.backgroundSize=(p.sheet_width/p.w*100)+'% '+(p.sheet_height/p.h*100)+'%';portrait.style.backgroundPosition=(p.x/(p.sheet_width-p.w)*100)+'% '+(p.y/(p.sheet_height-p.h)*100)+'%';}else portrait.textContent=a.name.slice(0,1);
        token.append(portrait,el('span',a.name,'formation-name'));arena.append(token);
      }
      target.append(arena,el('p','파랑: 아군 · 빨강: 상대 · 금색: 나 | 실선: 1차 대표 위협 · 점선 원: 2차 접근 위협 · 직선 점선: 동료 연결','formation-legend'),el('p','1차: 매우 위험하게 볼 대표 수단 · 2차: 상대도 진입 비용·반격 위험을 감수하는 조건부 범위','formation-legend'),el('p',model.threat_reference.scope+' 가정 배치이며 관련 기술을 배워 사용할 수 있다는 전제입니다.','formation-legend'));
      const focused=s.actors.find(a=>actor?a.team+':'+a.champion===actor:a.self),near=s.cohesion[step].nearest.find(n=>n.champion===focused?.champion),chosen=model.threat_reference.champions[focused?.champion];
      if(near)target.append(el('p',focused.name+'의 가장 가까운 동료: '+catalog.champions[near.ally].name+' · 예시 거리 '+near.distance_game_units+' 게임 단위 (실제 관측 아님)','formation-cohesion'));
      if(chosen){
        const ref=el('div',null,'formation-threat-summary');ref.setAttribute('aria-live','polite');ref.append(el('h4',focused.name+'의 원 기준'),el('p','1차 · '+(chosen.direct?chosen.direct.label+' '+chosen.direct.radius:'미확인')));
        if(chosen.approach)ref.append(el('p','2차 · '+chosen.approach.label+' '+chosen.approach.radius),el('p',chosen.approach.cost),el('p',chosen.approach.conditions.join(' · ')));
        else ref.append(el('p','2차 미확인 · '+chosen.approach_missing_reason));
        if(chosen.additional.length)ref.append(el('p','원 외에도 남는 위협: '+chosen.additional.map(v=>v.label+' '+v.radius).join(' · ')));
        ref.append(el('p',chosen.scope,'coach-muted'));target.append(ref);
      }
      const roster=el('details',null,'coach-details formation-roster');roster.append(el('summary','10명 선택 · 작은 초상화 대신 이름으로 선택'));roster.open=pickerOpen;const picks=el('div',null,'formation-roster-buttons');
      for(const a of s.actors)picks.append(btn((a.team==='ALLY'?'아군 ':'상대 ')+a.name,'pick-'+a.team+':'+a.champion,actor===a.team+':'+a.champion,()=>{actor=a.team+':'+a.champion;refresh();}));roster.append(picks);target.append(roster);
      const action=el('p',s.steps[step].action,'formation-action');action.setAttribute('aria-live','polite');target.append(action);
      if(actor){const a=s.actors.find(a=>a.team+':'+a.champion===actor);target.append(el('p',a.name+' · '+a.role+' · '+s.steps[step].action,'formation-actor-detail'));}
      const limits=el('details',null,'coach-details');limits.append(el('summary','성립 조건 · 실패하면 바꾸는 법'));const ul=el('ul');[...s.conditions,...s.failure].forEach(v=>ul.append(el('li',v)));limits.append(ul);target.append(limits);
      const rangeWhy=el('details',null,'coach-details');rangeWhy.append(el('summary','원 기준·공식 출처·위험 판단의 한계'));const caveats=el('ul');['선택한 대표 기술의 시전 사거리 참고이며 전체 위협·실제 적중·확정 피해 판정은 아닙니다.','2차 합산은 방향·기술 가용·대상·이동 경로가 맞을 때의 상한 참고입니다. 두 기술을 더했다는 이유로 공격 성공을 보장하지 않습니다.','궁극기는 첫 스킬 레벨, 모든 수단을 배워 사용할 수 있다는 가정입니다. 실제 쿨타임·표식·적중은 관측하지 않습니다.','점선 연결은 가까운 동료 관계이며 거리만으로 보호 가능·전술적 고립을 확정하지 않습니다.','전체 범위는 원이 잘리지 않는 공통 척도이고 배치 확대에서는 원이 화면 밖까지 이어질 수 있습니다.'].forEach(v=>caveats.append(el('li',v)));rangeWhy.append(caveats);
      const sourceRows=[chosen?.direct,chosen?.approach,...(chosen?.additional||[])].filter(Boolean);for(const source of [...new Map(sourceRows.flatMap(r=>r.sources).map(s=>[s.url+':'+s.locator,s])).values()]){const link=el('a','공식 '+source.patch+' · '+source.locator);link.href=source.url;link.target='_blank';link.rel='noopener noreferrer';rangeWhy.append(link);}target.append(rangeWhy);
      if(!isZoom){const zoom=el('button','배치 크게 보기');zoom.type='button';zoom.dataset.formationZoom='';zoom.addEventListener('click',()=>{zoomOpener=zoom;render(stage,true);dialog.showModal();});target.append(zoom);}
      if(focus)Array.from(target.querySelectorAll('[data-formation-control]')).find(n=>n.dataset.formationControl===focus)?.focus({preventScroll:true});
    }
    function refresh(){const old=(dialog.open?stage:main).querySelector('.formation-roster');if(old)pickerOpen=old.open;render(main,false);if(dialog.open)render(stage,true);}
    refresh();return root;
  }
  return Object.freeze({evaluate,create});
});

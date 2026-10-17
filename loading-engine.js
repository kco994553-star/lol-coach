/* Shared PC/mobile pre-game analysis. Source facts and tactical hypotheses differ. */
(function(root,factory){
  if(typeof module==='object'&&module.exports)module.exports=factory(require('./directions-engine.js'));
  else root.LoadingStrategy=factory(root.DirectionEngine);
})(typeof globalThis!=='undefined'?globalThis:this,function(DirectionEngine){
  'use strict';
  const POSITIONS=['TOP','JUNGLE','MID','BOTTOM','SUPPORT'];
  const POSITION_NAMES={TOP:'탑',JUNGLE:'정글',MID:'미드',BOTTOM:'바텀',SUPPORT:'서포터'};
  const clone=x=>JSON.parse(JSON.stringify(x));
  const norm=s=>typeof s==='string'?s.normalize('NFKC').toLowerCase().replace(/[^a-z0-9가-힣]/g,''):'';
  const indexes=new WeakMap();
  function resolveChampion(query,catalog){
    if(typeof query!=='string'||query.length>100)return null;
    if(!indexes.has(catalog)){
      const index=new Map();
      for(const row of Object.values(catalog.champions))for(const alias of [row.id,row.name,...row.aliases]){
        const key=norm(alias);if(key)index.set(key,index.has(key)&&index.get(key)!==row.id?null:row.id);
      }
      indexes.set(catalog,index);
    }
    return indexes.get(catalog).get(norm(query))||null;
  }
  function exact(value,keys){
    if(!value||Array.isArray(value)||typeof value!=='object'||Object.keys(value).sort().join('|')!==[...keys].sort().join('|'))throw Error('입력 항목을 확인해 주세요.');
  }
  function validate(raw,catalog){
    exact(raw,['allies','enemies','own_champion','own_position','side','patch','opponent_mode','lane_opponent']);
    const out={};
    for(const side of ['allies','enemies']){
      if(!Array.isArray(raw[side])||raw[side].length!==5)throw Error('아군과 상대 챔피언을 각각 5명 입력해 주세요.');
      out[side]=raw[side].map(s=>{
        exact(s,['champion','position']);
        const champion=resolveChampion(s.champion,catalog);
        if(!champion)throw Error('챔피언 이름을 검색 목록에서 확인해 주세요.');
        if(s.position!==null&&!POSITIONS.includes(s.position))throw Error('포지션은 미확인 또는 목록에서 선택해 주세요.');
        return {champion,position:s.position};
      });
      const roles=out[side].map(s=>s.position).filter(Boolean);
      if(new Set(roles).size!==roles.length)throw Error('같은 팀의 확정 포지션이 겹칩니다. 모르는 배치는 미확인으로 바꿔 주세요.');
    }
    if(new Set([...out.allies,...out.enemies].map(s=>s.champion)).size!==10)throw Error('10명의 챔피언이 겹치지 않도록 입력해 주세요.');
    out.own_champion=resolveChampion(raw.own_champion,catalog);
    if(!out.own_champion||!out.allies.some(s=>s.champion===out.own_champion))throw Error('내 챔피언을 아군 5명 중에서 선택해 주세요.');
    if(!POSITIONS.includes(raw.own_position))throw Error('내 포지션을 선택해 주세요.');
    out.own_position=raw.own_position;
    const self=out.allies.find(s=>s.champion===out.own_champion);
    if(self.position&&self.position!==out.own_position||out.allies.some(s=>s.champion!==out.own_champion&&s.position===out.own_position))throw Error('내 포지션과 아군 배치를 맞춰 주세요. 미확인 배치는 비워 둘 수 있습니다.');
    if(!['BLUE','RED'].includes(raw.side))throw Error('미니맵의 예시 진영을 선택해 주세요.');
    out.side=raw.side;
    if(raw.patch!==null&&(typeof raw.patch!=='string'||!/^\d{1,3}\.\d{1,3}(?:\.\d{1,3})?$/.test(raw.patch)))throw Error('패치는 숫자.숫자 형식 또는 미확인으로 입력해 주세요.');
    out.patch=raw.patch;
    if(!['ASSIGNED','UNKNOWN','MANUAL'].includes(raw.opponent_mode))throw Error('라인 상대의 확인 방법을 선택해 주세요.');
    out.opponent_mode=raw.opponent_mode;
    out.lane_opponent=raw.lane_opponent===null?null:resolveChampion(raw.lane_opponent,catalog);
    if(raw.opponent_mode==='MANUAL'){
      if(!out.lane_opponent||!out.enemies.some(s=>s.champion===out.lane_opponent))throw Error('직접 고른 라인 상대는 상대 5명 중에서 선택해 주세요.');
    }else if(raw.lane_opponent!==null)throw Error('라인 상대 직접 선택 값과 선택 방법을 맞춰 주세요.');
    return out;
  }
  function exampleInput(catalog,index=0){
    const teams=index===1?[
      ['Fiora','Graves','Ziggs','Ashe','Janna'],['Malphite','JarvanIV','Orianna','Jinx','Lulu']
    ]:[['Ornn','Sejuani','Ahri','Caitlyn','Lux'],['Fiora','LeeSin','Zed','Kaisa','Nautilus']];
    return {allies:teams[0].map((champion,i)=>({champion,position:POSITIONS[i]})),enemies:teams[1].map((champion,i)=>({champion,position:POSITIONS[i]})),own_champion:index===1?'Fiora':'Caitlyn',own_position:index===1?'TOP':'BOTTOM',side:'BLUE',patch:'16.20',opponent_mode:'ASSIGNED',lane_opponent:null};
  }
  function fromDraft(draft,catalog){
    if(!draft||draft.phase!=='PRE_GAME'||!Array.isArray(draft.slots)||draft.slots.length!==10)throw Error('완료된 경기 전 10픽만 가져올 수 있습니다. 수동 입력을 사용할 수 있습니다.');
    const teams={ALLY:[],ENEMY:[]};
    for(const side of ['ALLY','ENEMY']){
      const rows=draft.slots.filter(s=>s&&s.side===side).sort((a,b)=>a.slot-b.slot);
      if(rows.length!==5||rows.some((s,i)=>s.slot!==i+1))throw Error('픽창의 슬롯 구성을 확인하지 못했습니다.');
      teams[side]=rows.map(s=>({champion:s.champion,position:s.position}));
    }
    return validate({allies:teams.ALLY,enemies:teams.ENEMY,own_champion:draft.my_champion,own_position:draft.my_position,side:'BLUE',patch:draft.patch,opponent_mode:'ASSIGNED',lane_opponent:null},catalog);
  }
  const values=(hero,key)=>hero.profile?.[key]||[];
  const has=(hero,key,label)=>values(hero,key).includes(label);
  const fact=(hero,slot)=>hero.facts.find(f=>f.slot===slot);
  const preferred={Caitlyn:['W','E'],Ornn:['E','R'],Fiora:['W','Q'],Ashe:['R','W'],Kaisa:['R','E'],Yunara:['E','R']};
  // A multi-function candidate rule's source list is not a function→skill map.
  // These bounded bindings were checked against the retained official descriptions.
  // Unlisted functions remain champion-level exploratory candidates, without a skill claim.
  const functionalSlots={
    Caitlyn:{PICK:'W',PRESSURE:'Q'},Ornn:{PICK:'R',ACCESS:'E',PRESSURE:'Q'},Fiora:{ACCESS:'Q',PICK:'W'},
    Sejuani:{ACCESS:'Q',PICK:'R'},Ahri:{PICK:'E',ACCESS:'R',ASSASSIN:'R',PRESSURE:'Q'},
    Lux:{PICK:'Q',PRESSURE:'E',COVER:'W'},LeeSin:{ACCESS:'Q',COVER:'W',PICK:'R',PRESSURE:'Q'},
    Zed:{ACCESS:'R',ASSASSIN:'R',PRESSURE:'Q'},Kaisa:{ACCESS:'R',PRESSURE:'W'},Nautilus:{PICK:'Q',ACCESS:'Q'},
    Graves:{ACCESS:'E',PRESSURE:'Q'},Ziggs:{PRESSURE:'Q',PICK:'W'},Ashe:{PICK:'R',PRESSURE:'W'},
    Janna:{COVER:'E',PICK:'Q',PRESSURE:'W'},Malphite:{ACCESS:'R',PICK:'R',PRESSURE:'Q'},
    JarvanIV:{ACCESS:'R',PICK:'Q'},Orianna:{COVER:'E',PICK:'R',PRESSURE:'Q'},Jinx:{PRESSURE:'W',PICK:'E'},
    Lulu:{COVER:'E',PICK:'W',PRESSURE:'Q'},Yunara:{PRESSURE:'W'}
  };
  function signature(hero,kind){
    if(kind)return fact(hero,functionalSlots[hero.id]?.[kind])||null;
    return fact(hero,(preferred[hero.id]||['Q'])[0])||hero.facts[0];
  }
  const meansFor=(f,kind)=>f?f.name:kind==='FRONT'?'전방 역할 후보(탐색 분류·특정 기술 효과 미확인)':'챔피언 단위 후보(기능별 기술 연결 미확인)';
  function signalsFor(rows,catalog){
    const signals=[];
    for(const row of rows){
      const h=catalog.champions[row.champion];
      for(const [kind,key,label] of [['PICK','threats','GRAB_PICK'],['ACCESS','threats','DIVE'],['ASSASSIN','threats','ASSASSINATION'],['PRESSURE','threats','POKE'],['FRONT','protection','FRONTLINE'],['COVER','protection','PEEL']]){
        if(!has(h,key,label))continue;
        const f=signature(h,kind);
        signals.push({champion:h.id,name:h.name,kind,means:meansFor(f,kind),evidence_ids:f?[f.id]:[],level:'EXISTING_RULE',review_state:'EXPLORATORY',condition:'배운 기술·가용성·발동/적중 조건·아군 연결을 확인한 경우에만',rule_ids:(h.profile?.rule_refs||[]).filter(r=>(r.fields?.[key]||[]).includes(label)).map(r=>r.id)});
      }
    }
    return signals;
  }
  const kinds=(signals,...selected)=>signals.filter(s=>selected.includes(s.kind));
  const brief=rows=>[...new Set(rows.map(r=>r.name))].slice(0,2).join('·');
  function composition(rows,catalog){
    const signals=signalsFor(rows,catalog),strengths=[];
    const patterns=[['PICK','제어 적중을 후속 공격으로 연결할 후보'],['ACCESS','상대에게 접근해 연결할 후보'],['PRESSURE','접근 전 공간을 압박할 후보'],['COVER','아군 행동을 보호하며 이어 줄 후보'],['FRONT','아군과 전방 거리를 맞출 후보']];
    for(const [kind,label] of patterns){const found=kinds(signals,kind);if(found.length)strengths.push(brief(found)+': '+found.map(s=>s.means).slice(0,2).join('·')+' — '+label+'입니다. 기술 준비·적중·후속 연결이 조건입니다.');}
    const empty=rows.filter(r=>!signals.some(s=>s.champion===r.champion)).map(r=>catalog.champions[r.champion].name);
    return {strengths:strengths.length?strengths:['확인된 유형만으로 조합의 주된 시작 수단은 미확인입니다. 아래 공식 기술과 조건부터 비교합니다.'],weaknesses:[kinds(signals,'FRONT','COVER').length?'앞 공간과 보호 수단이 있어도 아군 거리가 벌어지면 연결이 끊깁니다.':'확인된 분류만으로 전방 유지·보호 수단을 보장할 수 없습니다. 미부여 분류는 수단 부재가 아닙니다.',...(empty.length?[empty.join('·')+'의 전략 분류는 부분적이거나 미확인입니다. 약한 챔피언이라는 뜻이 아닙니다.']:[])],conditions:['픽만으로 스킬 습득·가용성·체력·인원·시야·웨이브를 알 수 없습니다.','상대가 아래 계획을 실제로 선택한다고 단정하지 않습니다.'],signals};
  }
  function roleFor(input,hero){
    if(input.own_position==='SUPPORT')return has(hero,'protection','PEEL')?'PROTECT':has(hero,'protection','FRONTLINE')?'FRONT_CONNECT':has(hero,'threats','GRAB_PICK')?'PICK_LINK':'SUPPORT_CONNECT';
    if(input.own_position==='JUNGLE')return has(hero,'protection','FRONTLINE')?'FRONT_CONNECT':has(hero,'threats','ASSASSINATION')?'PICK_FOLLOW':'JUNGLE_CONNECT';
    if(hero.id==='Fiora'&&['TOP','MID'].includes(input.own_position))return 'SIDE_RETURN';
    if(hero.official_tags.includes('Marksman'))return 'FOLLOW_DAMAGE';
    if(has(hero,'protection','FRONTLINE'))return 'FRONT_CONNECT';
    if(has(hero,'threats','ASSASSINATION'))return 'PICK_FOLLOW';
    if(has(hero,'protection','PEEL'))return 'PROTECT';
    if(has(hero,'threats','POKE'))return 'SPACE_CONTROL';
    if(has(hero,'threats','GRAB_PICK'))return 'PICK_LINK';
    return 'CONDITIONAL_LINK';
  }
  const roleNames={PROTECT:'아군의 공격·이탈을 이어 주는 보호',FRONT_CONNECT:'후속 아군이 닿는 전방 연결',PICK_LINK:'제어 적중 뒤 후속 연결',SUPPORT_CONNECT:'아군 수급·귀환·교전 연결',JUNGLE_CONNECT:'라인과 목표물 사이의 연결',SIDE_RETURN:'복귀 조건을 남긴 사이드·본대 전환',FOLLOW_DAMAGE:'아군 제어 뒤 연결되는 지속 공격',PICK_FOLLOW:'노출된 대상에 조건부 후속 진입',SPACE_CONTROL:'아군과 압박선·공간 조정',CONDITIONAL_LINK:'확인된 기술에 맞춘 조건부 연결'};
  function selectPartners(input,catalog,role){
    const available=input.allies.filter(r=>r.champion!==input.own_champion);
    const ranked=available.map(row=>{
      const h=catalog.champions[row.champion];
      const follow=role==='FRONT_CONNECT'||role==='PROTECT';
      const priority=follow?(h.official_tags.includes('Marksman')?0:has(h,'threats','GRAB_PICK')?1:3):(has(h,'protection','FRONTLINE')?0:has(h,'protection','PEEL')?1:has(h,'threats','GRAB_PICK')?2:4);
      return {h,priority};
    }).filter(x=>x.priority<3).sort((a,b)=>a.priority-b.priority).slice(0,2);
    return ranked.map(({h})=>{const f=signature(h,has(h,'protection','FRONTLINE')?'FRONT':has(h,'protection','PEEL')?'COVER':'PICK');return {champion:h.id,name:h.name,means:meansFor(f,has(h,'protection','FRONTLINE')?'FRONT':has(h,'protection','PEEL')?'COVER':'PICK'),condition:'배운 기술과 후속 거리·체력·가용성이 맞을 때 연결 후보. 분류만으로 실제 준비를 확인하지 않음.',evidence_ids:f?[f.id]:[]};});
  }
  function threatsFor(input,catalog,enemySignals){
    const ids=[...new Set([...kinds(enemySignals,'ASSASSIN'),...kinds(enemySignals,'ACCESS'),...kinds(enemySignals,'PICK'),...kinds(enemySignals,'PRESSURE')].map(s=>s.champion))];
    return ids.map(id=>{const h=catalog.champions[id],s=enemySignals.find(x=>x.champion===id),f=signature(h,s.kind);return {champion:id,name:h.name,means:meansFor(f,s.kind),condition:'보유 기술의 조건이 맞으면 위협 후보입니다. 실제 의도·위치·현재 사용 가능 여부는 미확인입니다.',evidence_ids:f?[f.id]:[]};});
  }
  function kitAction(hero,role,partner,threat){
    const f=signature(hero),second=fact(hero,(preferred[hero.id]||['Q','E'])[1])||fact(hero,'E');
    if(hero.id==='Caitlyn')return `아군 ${partner}의 연결이 있고 덫을 설치할 위치에 접근 가능한 경우 ${fact(hero,'W').name}을 검토합니다. ${threat}의 접근이 남아 있으면 설치하려고 혼자 전진하지 않고 ${fact(hero,'E').name}의 사용 가능 여부와 뒤쪽 공간을 남깁니다.`;
    if(hero.id==='Ornn')return `${fact(hero,'E').name}은 지형 충돌이 띄우기의 조건입니다. 실제 지형·기술 가용성과 ${partner}의 후속 거리가 함께 맞을 때 전방 제어를 검토하고, 하나가 부족하면 진입보다 아군 쪽으로 거리를 줄입니다.`;
    if(hero.id==='Fiora')return `${fact(hero,'W').name}로 받아낼 상대 수단을 먼저 정하고 ${fact(hero,'Q').name}의 전진 폭을 남깁니다. ${partner}와 연결되지 않거나 ${threat}의 추가 접근이 보이면 결투를 만들기보다 압박을 접습니다.`;
    if(hero.id==='Kaisa')return `${fact(hero,'R').name}의 대상·사용 조건과 도착 지점의 아군 연결을 먼저 확인합니다. ${partner}의 후속이 끊기거나 ${threat}의 대응이 남으면 이동 수단만 보고 깊이 들어가지 않고 현재 위치에서 공격을 이어갈 대상을 바꿉니다.`;
    if(role==='FRONT_CONNECT')return `${f.name}의 발동 조건을 확인하고 ${partner}가 닿는 위치에서만 전방을 좁힙니다. 기술을 쓴 뒤 아군이 멀어지면 추가 추격 대신 연결 위치로 물러납니다.`;
    if(role==='PROTECT'||role==='SUPPORT_CONNECT')return `${partner}와 사용할 ${f.name}의 대상·발동 조건을 맞춥니다. ${threat}가 접근할 수 있는 동안 보호에 필요한 기술을 먼저 소모하지 않고, 연결이 끊기면 보호 위치를 아군 쪽으로 바꿉니다.`;
    return `${f.name}의 설명상 발동·적중 조건이 맞고 ${partner}가 연결할 수 있을 때만 행동 범위를 넓힙니다. ${threat}의 접근이나 아군 이탈이 확인되면 ${second.name}의 실제 사용 가능 여부를 따로 보고 대상·위치를 바꿉니다.`;
  }
  function basicMap(input,catalog,role,partners){
    const blue=input.side==='BLUE',own=catalog.champions[input.own_champion];
    const home=blue?{x:40,y:61}:{x:60,y:39},front=blue?{x:48,y:53}:{x:52,y:47},back=blue?{x:33,y:68}:{x:67,y:32};
    const target=role==='FRONT_CONNECT'?front:role==='PICK_FOLLOW'||role==='SIDE_RETURN'?(blue?{x:37,y:54}:{x:63,y:46}):role==='PROTECT'?home:back;
    const entities=[{id:'self',self:true,team:'ALLY',champion:own.id,portrait:own.portrait,start:home,target}];
    for(const [i,p] of partners.entries())entities.push({id:'partner-'+i,self:false,team:'ALLY',champion:p.champion,portrait:catalog.champions[p.champion].portrait,start:blue?{x:46+i*7,y:59-i*8}:{x:54-i*7,y:41+i*8},target:null});
    const arrows=role==='CONDITIONAL_LINK'?[]:[{step:1,kind:'MOVE',from:home,to:target},{step:2,kind:'PRESSURE',from:target,to:{x:target.x+(blue?4:-4),y:target.y+(blue?-4:4)}},{step:3,kind:'RETREAT',from:target,to:blue?{x:28,y:73}:{x:72,y:27}}];
    return {asset:'direction-assets/map11.png',caption:'전술 설명용 예시 · 로딩 시점의 실제 위치가 아닙니다.',entities,arrows,landmarks:[],notes:[`이번 조합에서 ${roleNames[role]} 역할을 검토하는 경우의 가상 배치입니다.`,`함께 배치한 ${partners.map(p=>p.name).join('·')||'아군 없음'}은 실제 10픽에서 연결 수단이 있는 후보만 골랐습니다. 현재 위치·준비 여부는 미확인입니다.`,'상대 5명의 챔피언은 알지만 위치는 모르므로 지도에 적 초상화를 배치하지 않습니다.','화살표는 안전 경로나 기술 사거리가 아닙니다. 표시된 연결 조건이 깨지면 전진 대신 위치를 바꿉니다.']};
  }
  function scenarioLinks(input,catalog,partners){
    let decision=null;
    if(input.own_champion==='Caitlyn'&&input.own_position==='BOTTOM')decision='RECALL';
    if(input.own_champion==='Fiora'&&['TOP','MID'].includes(input.own_position)&&partners.length)decision='SIDE_GROUP';
    if(input.own_champion==='Ornn'&&['TOP','JUNGLE','SUPPORT'].includes(input.own_position)&&partners.length)decision='OBJECTIVE';
    if(!decision||!DirectionEngine||!catalog.directions)return [];
    return catalog.directions.presets.filter(p=>p.input.decision===decision).map(p=>{
      const state=clone(p.input);state.role=input.own_position;state.side=input.side;state.patch=input.patch;state.economy=Object.fromEntries(POSITIONS.map(r=>[r,'UNKNOWN']));
      const old=DirectionEngine.evaluate(state,catalog.directions);
      old.map.entities=old.map.entities.filter(e=>e.self||partners.length).map(e=>e.self?{...e,portrait:catalog.champions[e.champion].portrait}:{...e,champion:partners[0].champion,portrait:catalog.champions[partners[0].champion].portrait});
      const assumptions=catalog.directions.decisions.find(d=>d.id===decision).condition_keys.filter(k=>k!=='enemy_visible').map(k=>{const c=catalog.directions.inputs.conditions.find(x=>x.key===k);return c.label+'：'+c.options[state.conditions[k]]+'라는 미래 가정';});
      return {id:p.id,title:p.title,assumptions,requirements:[...old.plan.requirements,partners.length?'실제 픽 '+partners[0].name+'의 '+partners[0].means+'과 연결할 수 있는 경우에만 예시 아군으로 배치':'내 챔피언·바텀 포지션의 귀환 판단에만 연결'],exceptions:[...old.plan.switch_when,'경제 상태는 선택 입력 전까지 전 포지션 미확인입니다.'],plan:old.plan,map:old.map,level:'DESIGN_HYPOTHESIS'};
    });
  }
  function analyze(raw,catalog){
    const input=validate(raw,catalog),own=catalog.champions[input.own_champion],role=roleFor(input,own);
    const allies=composition(input.allies,catalog),enemies=composition(input.enemies,catalog),partners=selectPartners(input,catalog,role),threats=threatsFor(input,catalog,enemies.signals);
    const allyLink=brief(partners)||'연결 가능한 아군',threatName=brief(threats)||'상대의 확인되지 않은 대응';
    const opponentRow=input.opponent_mode==='UNKNOWN'?null:input.opponent_mode==='MANUAL'?input.enemies.find(r=>r.champion===input.lane_opponent):input.own_position==='JUNGLE'?null:input.enemies.find(r=>r.position===input.own_position);
    const opponent=opponentRow?catalog.champions[opponentRow.champion]:null;
    const laneTool=h=>{const slots=functionalSlots[h.id]||{};return fact(h,[slots.PICK,slots.PRESSURE,'Q'].find(s=>s&&s!=='R'));};
    const ownQ=fact(own,'Q'),ownTool=signature(own),ownR=fact(own,'R'),enemyTool=opponent?laneTool(opponent):null;
    const enemyAccess=kinds(enemies.signals,'ASSASSIN','ACCESS'),enemyPoke=kinds(enemies.signals,'PRESSURE'),ourPoke=kinds(allies.signals,'PRESSURE'),ourControl=kinds(allies.signals,'PICK','FRONT');
    const attackPlan=ourPoke.length?`${brief(ourPoke)}의 압박 수단으로 공간을 만들고 ${brief(ourControl)||'연결할 아군'}의 후속이 닿을 때 목표물·포탑 압박을 검토합니다.`:`${brief(ourControl)||'기술 조건을 확인한 아군'}의 행동에 후속 거리를 맞춰 라인 자원·목표물 이득으로 연결하는 방안을 검토합니다.`;
    const enemyPlan=enemyAccess.length?`상대는 ${brief(enemyAccess)}의 접근 수단을 연결해 떨어진 대상을 노릴 가능성이 있습니다. 적중·아군 거리·가용성이 조건이며 실제 의도는 미확인입니다.`:enemyPoke.length?`상대는 ${brief(enemyPoke)}의 압박으로 먼저 체력·공간을 바꾸려 할 가능성이 있습니다. 실제 의도와 기술 가용성은 미확인입니다.`:'확인된 분류만으로 상대의 주된 계획은 미확인입니다. 10픽의 공식 기술과 접근·제어 조건부터 비교합니다.';
    const laneStatus=opponent?'조건부 대응 가능 · 매치업 우열 미확인':'상대 미확인 · 상성 우열 미확인';
    const duoPosition=input.own_position==='BOTTOM'?'SUPPORT':input.own_position==='SUPPORT'?'BOTTOM':null;
    const allyDuo=duoPosition?input.allies.find(r=>r.position===duoPosition):null;
    const enemyDuo=duoPosition?input.enemies.find(r=>r.position===duoPosition):null;
    const duoText=duoPosition?` 아군 ${allyDuo?catalog.champions[allyDuo.champion].name:'함께 설 아군 미확인'}·상대 ${enemyDuo?catalog.champions[enemyDuo.champion].name:'다른 라인 상대 미확인'}의 연결도 함께 봅니다.`:'';
    const resource=input.own_position==='JUNGLE'?'정글 자원':input.own_position==='SUPPORT'?'아군 수급 보조':'CS';
    const laneKey=(opponent?`${opponent.name}의 ${enemyTool.name} 대응과 ${ownTool.name} 사용 조건이 맞을 때만 ${resource} 접근·교환 폭을 넓힙니다.`:`상대가 미확인입니다. ${ownQ.name}을 배운 경우의 ${resource}·교환 조건부터 준비합니다.`)+duoText;
    const kit=kitAction(own,role,allyLink,threatName);
    const fightKey=enemyAccess.length?`${threatName}의 접근에 ${allyLink}와 거리를 맞춘 뒤 ${ownTool.name}의 사용 조건을 고릅니다. 고립되면 추격 대신 연결 회복입니다.`:`${allyLink}와 압박선을 맞춰 ${ownTool.name}의 조건을 준비합니다. ${brief(enemyPoke)||'상대'}의 견제·아군 이탈로 조건이 깨지면 목표·위치를 바꿉니다.`;
    const uncertainties=[...(input.patch&&input.patch.split('.').slice(0,2).join('.')!==catalog.source_patch.split('.').slice(0,2).join('.')?['입력 패치 '+input.patch+'와 공식 자료 '+catalog.source_patch+'가 다릅니다. 기술 변경 여부를 확인하기 전 행동 해석 적용에 제한이 있습니다.']:[]),...(opponent?[]:['맞라이너 미확인']),...(input.patch?[]:['게임 패치 미확인']),...(input.opponent_mode==='MANUAL'?['라인 상대는 직접 고른 가정이며 실제 배치 미확인']:[]),'기술 습득·가용성·체력·웨이브·적 정글 위치는 로딩에서 미확인'];
    const summary={our_plan:attackPlan,enemy_plan:enemyPlan,collision:`${threatName}의 접근·압박과 ${allyLink}의 연결이 만나는 순간이 핵심입니다. 먼저 닿는 쪽을 픽만으로 확정할 수 없습니다.`,my_role:`${POSITION_NAMES[input.own_position]} ${own.name}: ${roleNames[role]}. ${allyLink}와 연결할 수 있는지를 기준으로 역할을 바꿉니다.`,lane_key:laneKey,fight_key:fightKey,remember:[`상대 ${opponent?.name||'맞라이너'}의 대응과 내 ${ownTool.name} 조건을 함께 보기`,`${allyLink}와 후속 거리가 끊기면 전진 폭 줄이기`,'보이지 않는 적을 없다고 보거나 미니언만으로 안전을 확정하지 않기'],uncertainties};
    const relevantStats=(catalog.statistics||[]).filter(s=>s.champion===own.id&&s.position===input.own_position&&input.patch&&s.patch===input.patch.split('.').slice(0,2).join('.'));
    const quote=f=>`${f.name}: ${f.text}`;
    const duoFact=enemyDuo?signature(catalog.champions[enemyDuo.champion]):null;
    const context=(opponent?`상대 ${quote(enemyTool)}. `:'맞라이너의 대응 기술은 미확인입니다. ')+(duoFact?`함께 서는 상대 ${catalog.champions[enemyDuo.champion].name}의 ${duoFact.name} 조건도 별도입니다. `:'');
    const change=['상대 라인·보조 챔피언의 실제 배치가 바뀔 때','체력·배운 기술·가용성·정글 개입·웨이브가 달라질 때'];
    const laneRows=[
      {id:'LEVEL1',period:'레벨 1',why:`${quote(ownQ)}. ${opponent?'상대의 '+quote(fact(opponent,'Q'))+'도 실제로 배운 경우의 대응 후보입니다. ':context}처음 배운 기술은 픽만으로 알 수 없습니다.`,action:`이 기술을 배웠고 상대 대응을 감당할 위치가 있을 때만 다음 CS로 접근합니다. 조건이 없으면 현재 위치에서 받을 자원을 고르고 불필요한 맞교환을 줄입니다.`,facts:[ownQ,opponent?fact(opponent,'Q'):null]},
      {id:'LEVEL2',period:'레벨 2',why:`${quote(ownTool)}. ${allyLink}의 두 번째 기술 습득과 상대 선행 레벨은 미확인입니다.`,action:`새로 배운 기술과 아군 연결을 확인한 뒤 교환 폭을 바꿉니다. 레벨 2라는 이유만으로 들어가지 않고, 연결이 없으면 미니언 수급과 귀환 자원을 준비합니다.`,facts:[ownTool,enemyTool]},
      {id:'LEVEL3_5',period:'레벨 3~5',why:`${context}${quote(fact(own,'E'))}. 기술 투자 순서·재사용 상태는 따로 확인해야 합니다.`,action:`상대 대응이 이미 사용됐거나 회피·방어 수단이 확인됐을 때만 교환 후 빠질 위치를 남깁니다. 정글 위치가 불명확하면 시야 밖으로 따라가지 않고 가까운 자원과 아군 연결로 목표를 낮춥니다.`,facts:[fact(own,'E'),enemyTool]},
      {id:'LEVEL6',period:'레벨 6',why:`${quote(ownR)}. ${opponent?'상대의 '+quote(fact(opponent,'R'))+'도 실제 습득·가용성을 따로 확인합니다. ':''}이 레벨에 궁극기를 배웠거나 사용할 수 있다고 자동 가정하지 않습니다.`,action:`실제 습득·사용 조건을 확인한 경우 ${allyLink}의 후속과 함께 사용할지, 상대 접근에 남길지 고릅니다. 적의 대응이 남거나 고립되면 기술만 보고 진입하지 않습니다.`,facts:[ownR,opponent?fact(opponent,'R'):null]},
      {id:'FIRST_PURCHASE',period:'첫 귀환·구매 이후',why:relevantStats.length?'같은 챔피언·포지션·패치의 첫 구매 기반 귀환 관측·누락 기록이 있습니다. 지표가 표본 부족이면 미확인을 유지하며, 상대별 비교·최적 시점·금액을 뜻하지 않습니다.':`확인 가능한 ${own.name}·${POSITION_NAMES[input.own_position]}·입력 패치의 구매 관측은 미확인입니다. 구매만으로 상성 우열을 바꾸지 않습니다.`,action:`구매한 실제 아이템·체력 회복·다음 웨이브·상대 구매를 비교합니다. 회복이 필요하면 가까운 자원을 포기할 수 있고, 로밍은 받은 자원과 복귀 손실·아군 연결을 함께 보고 고릅니다.`,facts:[ownTool]},
      {id:'FIRST_CORE',period:'첫 핵심 아이템 이후',why:'이번 판의 첫 핵심 아이템 선택·완성 시각·상대 아이템은 미확인입니다. 스킬 설명만으로 피해량 역전이나 최적 빌드를 확정하지 않습니다.',action:`완성한 실제 아이템과 레벨·체력·인원을 확인해 ${roleNames[role]}의 전진 폭을 다시 정합니다. 본대와 떨어지면 아이템 완성만 믿고 싸우기보다 수급·합류 순서를 바꿉니다.`,facts:[ownTool,ownR]}
    ].map(r=>({id:r.id,period:r.period,judgment:laneStatus,why:r.why,action:r.action,changes:[...change,...(r.id==='FIRST_PURCHASE'||r.id==='FIRST_CORE'?['실제 구매·완성 아이템을 확인했을 때']:['실제로 배운 기술·상대 대응을 확인했을 때'])],evidence_ids:[...r.facts.filter(Boolean).map(f=>f.id),...(duoFact&&r.id==='LEVEL1'?[duoFact.id]:[]),...(r.id==='FIRST_PURCHASE'?relevantStats.map(s=>s.id):[])],level:'DESIGN_HYPOTHESIS'}));
    if(input.own_position==='JUNGLE'){
      for(const row of laneRows)row.action=row.action.replaceAll('CS','정글 자원').replaceAll('미니언 수급','정글 자원 수급');
      laneRows[0].action='배운 기술·체력과 정글 자원을 받을 동선을 확인합니다. 적 정글 위치를 상상해 침투하지 않고, 아군이 연결할 수 있는 입구·가까운 자원·귀환을 비교합니다.';
    }
    if(input.own_position==='SUPPORT'){
      for(const row of laneRows)row.action=row.action.replaceAll('다음 CS','아군과 연결되는 위치').replaceAll('미니언 수급','아군 수급 보조');
      laneRows[0].action=`${allyDuo?catalog.champions[allyDuo.champion].name:'바텀 아군'}의 수급을 보조할 위치와 배운 기술의 연결을 맞춥니다. 상대 대응이 남으면 무리하게 견제하지 않고 아군이 받을 공간을 남깁니다. 아군 CS를 대신 가져오라는 뜻은 아닙니다.`;
    }
    const lane={opponent:opponent?{id:opponent.id,name:opponent.name,position:opponentRow.position}:null,status:laneStatus,rows:laneRows,interactions:[quote(ownTool),...(enemyTool?[`상대의 실제 수단: ${quote(enemyTool)}`]:[]),kit],wave:'모인 미니언은 수급·밀기·귀환 시간을 만들 후보지만, 체력·적 합류·상대 광역기 조건을 함께 봅니다. 미니언 충돌이 공식 설명에 없는 기술을 미니언만으로 막는다고 가정하지 않습니다.',jungle:`적 정글 ${input.enemies.find(s=>s.position==='JUNGLE')?catalog.champions[input.enemies.find(s=>s.position==='JUNGLE').champion].name:'챔피언/배치 미확인'}의 현재 위치는 모릅니다. 확인된 위치·경로 정보가 생기기 전에는 라인 밖 추격보다 가까운 수급·아군 쪽 복귀를 대안으로 둡니다. 첫 갱 시점을 추정하지 않습니다.`,reset_roam:'웨이브를 실제로 밀어 넣었고 체력·구매·목표물 일정이 맞으면 귀환 후보입니다. 이동·로밍은 합류 가치와 놓칠 자원·복귀 수단이 함께 맞을 때만 검토하며, 안 맞으면 라인 수급·회복을 택합니다.',recovery:'불리해지면 받을 수 있는 웨이브·체력 회복·아군과 만날 위치를 먼저 정합니다. 포탑 아래도 안전하다고 단정하지 않으며, 받을 수 없는 자원을 지키려 고립되지 않습니다.'};
    const gameplan={base:attackPlan,prepare:[`${allyLink}와 먼저 움직일 라인·후속 위치를 맞춥니다.`,`${threatName}의 접근에 쓸 기술과 이탈할 방향을 정합니다.`, '웨이브·체력·아이템·시야가 실제로 확인된 뒤 목표물 시작 여부를 고릅니다.'],fallback:'연결이 성립하지 않으면 먼 경합을 강행하지 않고 아군 쪽의 보이는 웨이브·회복·구매로 목표를 낮춥니다. 반대편이 비었다고 가정하지 않습니다.',switch_when:['아군 후속 거리 또는 내 이탈 수단이 사라질 때','상대 증원·접근이나 체력·인원 손실을 확인했을 때','웨이브·목표물·구매 조건이 바뀔 때'],stages:[{stage:'초반',role:`${POSITION_NAMES[input.own_position]}의 자원·기술 조건을 준비하고 상대 대응을 확인`,conditions:['라인 배치·배운 기술·정글 위치가 확인되는 만큼만 전진']},{stage:'중반',role:role==='SIDE_RETURN'?'본대가 대기하고 복귀 수단이 있을 때만 사이드 압박, 아니면 합류 거리 축소':`${allyLink}와 ${roleNames[role]}을 연결`,conditions:['웨이브 수급·아군 준비·접근 정보·복귀 손실을 함께 비교']},{stage:'후반',role:'기술·인원 연결을 유지하며 교전 후 실제 남은 자원으로 이득 전환',conditions:['사망 손실이 큰 상황인지 별도 확인','유리한 아이템만으로 재진입을 결정하지 않기']}],side_vs_group:`${own.name}의 사이드 여부는 대기할 본대·보이는 자원·복귀 수단이 모두 맞는 경우에 검토합니다. ${threatName}의 접근이나 아군 선교전이 확인되면 더 깊은 압박보다 연결 회복을 우선 비교합니다.`,objectives:'현재 존재하는 목표물과 웨이브·체력·인원·접근 정보를 확인한 뒤 경합을 준비합니다. 생성 시각은 공식 패치 근거를 연결하지 않아 제시하지 않습니다.',conversion:'교전 뒤 살아 있는 인원·체력·웨이브와 실제로 접근 가능한 목표물을 확인해 포탑·목표물·귀환 중 하나를 고릅니다. 킬만 얻었다고 모든 이득을 함께 가져갈 수 있다고 보지 않습니다.'};
    const teamfight={role:`${own.name}: ${roleNames[role]} — ${allyLink}의 수단과 내 ${ownTool.name}을 연결하는 조건부 역할입니다.`,partners,threats,setup:[`${allyLink}의 후속 위치와 내 이탈 방향을 먼저 맞춥니다.`,'적 위치는 로딩에서 미확인입니다. 미니맵 배치는 전술 설명용 가정입니다.'],actions:[`${allyLink}가 연결할 수 있고 내 기술·체력 조건이 맞는 위치까지 이동합니다. 확인되지 않은 진입 경로를 안전하다고 보지 않습니다.`,kit,`${threatName}의 접근·아군 이탈·체력 손실로 연결이 끊기면 대상을 바꾸거나 아군 쪽으로 이탈합니다.`],switch_when:['선교전 아군에게 즉시 닿을 수 없으면 무리한 후속 대신 가까운 아군 보호·거리 조정','내 진입 수단을 쓰면 이탈이 사라지는 경우 역할을 후속·보호로 변경'],exit:['아군 후속·체력·기술 조건이 끊기거나 새 적 접근이 확인되면 추가 추격 중단','퇴로 정보가 사라지면 보이지 않는 길로 상대를 따라가지 않기'],after:[gameplan.conversion],map:basicMap(input,catalog,role,partners)};
    const selected=new Map();
    const add=f=>{if(f)selected.set(f.id,f);};
    for(const f of own.facts)add(f);
    for(const row of [...input.allies,...input.enemies]){const h=catalog.champions[row.champion];add(signature(h));}
    for(const s of [...allies.signals,...enemies.signals,...partners,...threats])for(const id of s.evidence_ids)for(const h of Object.values(catalog.champions)){const f=h.facts.find(f=>f.id===id);if(f)add(f);}
    if(opponent)for(const f of opponent.facts)add(f);
    if(enemyTool)add(enemyTool);
    const rules=[...new Map([...input.allies,...input.enemies].flatMap(r=>catalog.champions[r.champion].profile?.rule_refs||[]).map(r=>[r.id,{...r,level:'EXISTING_RULE',review_state:'EXPLORATORY',interpretation:'기존 조건부 분류를 참고하며 승인·실전 효과를 승계하지 않습니다.'}])).values()];
    const patch_status=input.patch===null?'UNKNOWN':input.patch.split('.').slice(0,2).join('.')===catalog.source_patch.split('.').slice(0,2).join('.')?'SOURCE_MAJOR_MATCH':'MISMATCH';
    const evidence={facts:[...selected.values()],rules,statistics:relevantStats,lectures:[],unknowns:[...uncertainties,'레벨별 매치업 우열·스킬 투자·아이템 완성 후 교전 승리','부여하지 않은 유형·상대 플레이어의 의도·시야 밖 적 위치'],limits:['공식 기술 설명은 메커니즘 사실이며 이 전략의 최적성·성공을 검증하지 않습니다.','기존 분류 규칙은 EXPLORATORY(검토 전 후보)이며 누락 유형은 능력 부재가 아닙니다.','라인전·조합·한타 해석은 신규 설계 가설입니다. 기존 AUTO/USER 승인을 승계하지 않습니다.','구매 통계는 챔피언·포지션 참고이며 상대별 상성·권장 시각·권장 금액의 근거가 아닙니다.','게임 로딩 전 계획·경기 후 복기용입니다. 실시간 판단·게임 조작·비공개 정보 접근은 하지 않습니다.'],patch_status,strategy_level:'DESIGN_HYPOTHESIS',real_coaching_n:0,accuracy:null};
    return {schema_version:'lol-coach-loading-report-v1',input,summary,composition:{allies,enemies},gameplan,lane,teamfight,scenarios:scenarioLinks(input,catalog,partners),evidence};
  }
  return {resolveChampion,exampleInput,fromDraft,analyze};
});

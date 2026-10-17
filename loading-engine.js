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
  // Canonical display order only; never an importance or advantage ranking.
  const byId=(a,b)=>a.champion<b.champion?-1:a.champion>b.champion?1:0;
  const sortedRows=rows=>[...rows].sort((a,b)=>(POSITIONS.indexOf(a.position)<0?5:POSITIONS.indexOf(a.position))-(POSITIONS.indexOf(b.position)<0?5:POSITIONS.indexOf(b.position))||byId(a,b));
  const names=rows=>[...new Map([...rows].sort(byId).map(r=>[r.champion,r.name])).values()].join('·');
  const kindNames={PICK:'제어 연결',ACCESS:'접근',ASSASSIN:'고립 대상 위협',PRESSURE:'견제·공간',COVER:'보호',FRONT:'전방 연결 후보',DAMAGE:'후속 공격',UNKNOWN:'수단 미확인'};
  function composition(rows,catalog){
    const signals=signalsFor(sortedRows(rows),catalog).sort((a,b)=>byId(a,b)||(a.kind<b.kind?-1:1));
    const strengths=[];
    for(const kind of ['PICK','ACCESS','PRESSURE','COVER','FRONT']){
      const found=kinds(signals,kind);if(found.length)strengths.push(`${kindNames[kind]} 후보 ${names(found)}: ${found.map(s=>s.name+'의 '+s.means).join(' / ')}. 습득·가용성·발동 조건과 후속 거리가 맞는 경우의 탐색 해석입니다.`);
    }
    const empty=sortedRows(rows).filter(r=>!signals.some(s=>s.champion===r.champion)).map(r=>catalog.champions[r.champion].name);
    return {signals,strengths:strengths.length?strengths:['확인한 분류만으로 주된 시작 수단은 미확인입니다.'],weaknesses:['제어·보호 후보가 있어도 실제 습득·가용성과 아군 연결은 별도 조건입니다.',...(empty.length?[empty.join('·')+'의 분류는 부분적/미확인입니다. 능력 부재나 약세가 아닙니다.']:[])],conditions:['이름의 표시 순서는 중요도 순위가 아닙니다. 알려진 유형별 후보를 모두 보존합니다.','픽만으로 현재 위치·합류·체력·기술 상태와 상대 의도를 알 수 없습니다.']};
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
  const pickTypes=h=>[['PICK','threats','GRAB_PICK'],['ACCESS','threats','DIVE'],['ASSASSIN','threats','ASSASSINATION'],['PRESSURE','threats','POKE'],['COVER','protection','PEEL'],['FRONT','protection','FRONTLINE']].filter(([,key,label])=>has(h,key,label)).map(([kind])=>kind);
  function candidate(row,catalog,context,reason,allowed){
    const h=catalog.champions[row.champion],all=[...new Set([...pickTypes(h),...Object.keys(functionalSlots[h.id]||{})])],selected=allowed?all.filter(k=>allowed.includes(k)):all;
    const fs=[...new Map(selected.map(k=>signature(h,k)).filter(Boolean).map(f=>[f.id,f])).values()];
    if(context==='LANE'||context==='JUNGLE_INTERVENTION')for(const f of h.facts)if(!fs.some(x=>x.id===f.id))fs.push(f);
    return {champion:h.id,name:h.name,context,kinds:selected.length?selected:['UNKNOWN'],means:fs.length?fs.map(f=>f.name).join('·'):'기능별 기술 연결 미확인' ,reasons:[reason,...(selected.length?['기존 탐색 분류/기술별 기능 후보: '+selected.map(k=>kindNames[k]).join('·')]:['이 문맥의 기능 연결 근거가 부족합니다. 능력이 없다는 뜻이 아닙니다.'])],condition:'해당 기술을 배웠고 사용할 수 있으며 실제 거리·체력·발동 조건이 맞는 경우의 후보. 위치·합류·가용성은 미관측.',evidence_ids:fs.map(f=>f.id).sort(),eligible:fs.length>0};
  }
  function laneContext(input,catalog){
    const duo=['BOTTOM','SUPPORT'].includes(input.own_position),peerPosition=input.own_position==='BOTTOM'?'SUPPORT':'BOTTOM';
    const peer=duo?input.allies.find(p=>p.position===peerPosition&&p.champion!==input.own_champion):null;
    let opponent=null,enemies=[];
    if(input.opponent_mode==='MANUAL')opponent=input.enemies.find(p=>p.champion===input.lane_opponent);
    else if(input.opponent_mode==='ASSIGNED'&&input.own_position!=='JUNGLE')opponent=input.enemies.find(p=>p.position===input.own_position);
    const manualMismatch=opponent&&input.opponent_mode==='MANUAL'&&(!duo||!['BOTTOM','SUPPORT'].includes(opponent.position));
    if(duo&&input.opponent_mode==='ASSIGNED')enemies=input.enemies.filter(p=>['BOTTOM','SUPPORT'].includes(p.position));
    else if(opponent)enemies=duo&&!manualMismatch?input.enemies.filter(p=>['BOTTOM','SUPPORT'].includes(p.position)):[opponent];
    const kind=input.own_position==='JUNGLE'&&input.opponent_mode!=='MANUAL'?'JUNGLE':manualMismatch?'MANUAL_COMPARISON':duo?(peer&&enemies.length===2?'DUO':'DUO_INCOMPLETE'):(opponent?'SOLO':'SOLO_UNKNOWN');
    const partners=peer?[candidate(peer,catalog,'LANE',`입력한 ${POSITION_NAMES[peerPosition]} 배치가 내 ${POSITION_NAMES[input.own_position]}와 같은 바텀 라인인 경우의 동료. 다른 라인의 합류를 가정하지 않음.`)]:[];
    const threats=[...enemies].sort(byId).map(p=>candidate(p,catalog,'LANE','입력한 라인 배치 또는 직접 비교 대상으로 지정한 상대. 현재 같은 위치에 있다는 관측은 아님.'));
    return {kind,opponent:opponent?{id:opponent.champion,name:catalog.champions[opponent.champion].name,position:opponent.position}:null,partners,threats,selection_note:'라인은 포지션/직접 지정으로만 연결합니다. 목록 정렬은 표시용이며 중요도 순위가 아닙니다.',limits:[...(duo&&!peer?['함께 설 바텀 아군 배치 미확인']:[]),...(duo&&enemies.length<2?['상대 바텀 두 명의 배치가 모두 확인되지 않았습니다. 빈칸을 조합 유형으로 채우지 않습니다.']:[]),...(input.opponent_mode==='MANUAL'?['직접 고른 비교 대상이며 실제 라인 배치는 별도 확인']:[]),'로딩에서는 현재 위치·실제 합류·스킬 습득/가용성을 관측하지 않습니다.']};
  }
  function contextCandidates(input,catalog,base,context){
    const preferredKinds=context==='OPERATIONS'?['PRESSURE','PICK','COVER','FRONT']:['FRONT_CONNECT','PROTECT'].includes(base)?['PRESSURE','PICK','COVER']:['PICK','COVER','FRONT'];
    const partners=input.allies.filter(p=>p.champion!==input.own_champion).sort(byId).map(p=>{
      const h=catalog.champions[p.champion],allow=[...preferredKinds];
      const c=candidate(p,catalog,context,context==='OPERATIONS'?'웨이브·목표물·복귀 계획을 연결할 실제 아군 후보. 같은 위치/합류는 가정하지 않음.':'내 기본 역할과 제어·보호·후속 기능을 연결할 실제 아군 후보. 현재 거리와 기술 준비는 별도 조건.',allow);
      if(['FRONT_CONNECT','PROTECT'].includes(base)&&h.official_tags.includes('Marksman')){c.kinds=[...new Set([...c.kinds.filter(k=>k!=='UNKNOWN'),'DAMAGE'])];c.eligible=true;c.reasons.push('공식 원거리 딜러 분류를 후속 공격 역할 후보로 참고. 피해량·현재 준비를 검증한 것은 아님.');}
      return c;
    });
    const threats=input.enemies.map(p=>candidate(p,catalog,context,'실제 상대 픽의 알려진 접근·제어·견제 등 대응 후보를 보존합니다. 중요도·현재 위치·사용 가능 여부는 미확인.')).sort(byId);
    return {partners,threats,selection_note:'유형별 후보이며 중요도 순위가 아닙니다. 모든 실제 픽을 보존하고 기능 미확인은 따로 표시합니다. 요약의 생략은 위협 부재가 아닙니다.'};
  }
  function proposeRole(base,own,fight,catalog){
    const relevant=fight.partners.flatMap(p=>p.kinds.map(kind=>({p,kind,f:signature(catalog.champions[p.champion],kind)})));
    const control=relevant.filter(x=>x.kind==='PICK'&&x.f),cover=relevant.filter(x=>x.kind==='COVER'&&x.f);
    const baseInfo={id:base,label:roleNames[base],types:[...own.official_tags],scope:'챔피언·포지션의 기본 분류 · 전술 효과 미검증'};
    let proposed={id:base,label:roleNames[base],reasons:['분류를 바꿀 만큼 확인된 조합 기능 연결 근거가 없어 기본 역할을 유지합니다.'],conditions:['실제 기술·체력·거리와 상대 대응을 확인한 만큼만 실행'],limits:['미확인 분류를 수단 부재로 바꾸지 않습니다.'],action_ids:['KEEP_BASE_ROLE','KEEP_SELF_EXIT']};
    if(base==='FOLLOW_DAMAGE'&&control.length){
      proposed={id:cover.length?'CONTROL_WITH_COVER':'CONTROL_WITH_SELF_EXIT',label:cover.length?'보호 연결을 남긴 제어 후속 공격':'내 이탈 수단을 남긴 조건부 제어 후속',reasons:['제어 수단 후보: '+control.map(x=>x.p.name+' '+x.f.name).join(' / '),...(cover.length?['보호 수단 후보: '+cover.map(x=>x.p.name+' '+x.f.name).join(' / ')]:['확인된 기능 연결에서 보호를 보장할 수 없어, 내 이탈과 후속 거리 조건을 더 좁힙니다.'])],conditions:[cover.length?'보호가 실제로 닿는 위치와 제어 적중이 함께 확인된 경우':'내 이탈 수단과 아군 제어 적중·후속 거리까지 확인된 경우','상대의 접근·제어가 남아 있으면 공격 폭을 줄이고 접근 가능한 대상을 선택'],limits:['조합만으로 현재 보호/제어 가용성·교전 승리를 확인하지 않습니다.','기본 유형은 바뀌지 않으며 이번 계획은 설계 가설입니다.'],action_ids:['FOLLOW_CONFIRMED_CONTROL',cover.length?'KEEP_COVER_CONNECTION':'KEEP_SELF_EXIT','CHANGE_TARGET_IF_ACCESS_OPENS']};
    }else if(base==='FOLLOW_DAMAGE'&&cover.length){
      proposed={id:'COVERED_RESOURCE',label:'보호 범위에서 자원·공격 연결 유지',reasons:['보호 수단은 연결되지만 확정할 제어 후속 근거가 부족합니다.'],conditions:['실제로 보호가 닿고 공격 가능한 대상과 퇴로가 있는 경우'],limits:['확인 못 한 제어가 없다고 단정하지 않습니다.'],action_ids:['RECEIVE_WITH_COVER','KEEP_COVER_CONNECTION','KEEP_SELF_EXIT']};
    }
    const entry=fight.threats.filter(p=>p.kinds.some(k=>['ACCESS','ASSASSIN'].includes(k)&&signature(catalog.champions[p.champion],k)));
    proposed.conditions.push(entry.length?'상대 '+names(entry)+'의 확인된 접근 수단이 남으면 공격을 짧게 나누고 보호/내 이탈을 먼저 남김':'파악한 원거리 제어·견제와 체력 손실을 보고 공격선을 조정하며, 연결되지 않은 접근 수단은 미확인으로 유지');
    proposed.action_ids.push(entry.length?'RESPECT_CONFIRMED_ENTRY':'REASSESS_UNMAPPED_ENTRY');
    return {base:baseInfo,proposed,changed:proposed.id!==base};
  }
  function kitAction(hero,role,partner,threat,controlNames){
    const f=signature(hero),second=fact(hero,(preferred[hero.id]||['Q','E'])[1])||fact(hero,'E');
    if(hero.id==='Caitlyn'&&!controlNames)return `아군 제어 연결은 미확인입니다. 현재 공격 가능한 대상과 뒤쪽 공간을 함께 고르고 ${fact(hero,'E').name}을 접근 대응과 이탈에 남길지 비교합니다. 혼자 전진해 덫 연계를 만들지 않고 확인하지 못한 경로로 추격하지 않습니다.`;
    if(hero.id==='Caitlyn')return `아군 ${controlNames}의 제어가 적중했고 덫 설치 위치·발동 조건과 후속 거리가 맞는 경우 ${fact(hero,'W').name} 후속을 검토합니다. 명중만으로 덫 연계가 보장되지는 않습니다. ${threat} 대응이 남으면 혼자 덫을 설치하러 나가지 않고 ${fact(hero,'E').name}과 뒤쪽 공간을 남깁니다.`;
    if(hero.id==='Ornn')return `${fact(hero,'E').name}의 띄우기는 지형 충돌이 조건입니다. 지형·기술 가용성과 ${partner}의 후속 거리가 맞을 때만 전방 제어를 검토하고, 부족하면 아군 쪽으로 거리를 줄입니다.`;
    if(hero.id==='Fiora')return `${fact(hero,'W').name}로 받아낼 수단을 먼저 정하고 ${fact(hero,'Q').name}의 전진 폭을 남깁니다. ${partner}의 연결·복귀 조건이 깨지면 압박을 접습니다.`;
    if(hero.id==='Kaisa')return `${fact(hero,'R').name}의 플라즈마 표식 대상 조건과 도착 지점의 아군 연결을 확인합니다. 후속이 끊기거나 상대 대응이 남으면 현재 위치에서 공격할 대상을 바꿉니다.`;
    if(role==='PROTECT'||role==='SUPPORT_CONNECT')return `${partner}와 ${f.name}의 실제 대상·발동 조건을 맞춥니다. 상대 접근 대응에 필요한 수단을 먼저 소모하지 않고 연결이 끊기면 아군 쪽으로 위치를 바꿉니다.`;
    return `${f.name}의 발동·적중 조건과 ${partner}의 후속이 맞을 때만 전진 폭을 넓힙니다. 상대 대응이나 아군 이탈이 확인되면 ${second.name}의 실제 가용성을 보고 대상·위치를 바꿉니다.`;
  }
  function basicMap(input,catalog,role,partners){
    const blue=input.side==='BLUE',own=catalog.champions[input.own_champion],eligible=partners.filter(p=>p.eligible);
    const home=blue?{x:40,y:61}:{x:60,y:39},front=blue?{x:48,y:53}:{x:52,y:47},back=blue?{x:33,y:68}:{x:67,y:32};
    const target=role==='FRONT_CONNECT'?front:role==='PICK_FOLLOW'||role==='SIDE_RETURN'?(blue?{x:37,y:54}:{x:63,y:46}):role==='PROTECT'?home:back;
    const entities=[{id:'self',self:true,team:'ALLY',champion:own.id,portrait:own.portrait,start:home,target}];
    eligible.forEach((p,i)=>entities.push({id:'partner-'+p.champion,self:false,team:'ALLY',champion:p.champion,portrait:catalog.champions[p.champion].portrait,start:blue?{x:46+i*7,y:59-i*8}:{x:54-i*7,y:41+i*8},target:null}));
    const arrows=role==='CONDITIONAL_LINK'?[]:[{step:1,kind:'MOVE',from:home,to:target},{step:2,kind:'PRESSURE',from:target,to:{x:target.x+(blue?4:-4),y:target.y+(blue?-4:4)}},{step:3,kind:'RETREAT',from:target,to:blue?{x:28,y:73}:{x:72,y:27}}];
    return {context:'TEAMFIGHT',asset:'direction-assets/map11.png',caption:'전술 설명용 예시 · 한타 문맥 · 실제 위치/합류 관측 아님',entities,arrows,landmarks:[],notes:[`기본 역할 ${roleNames[role]}을 검토하는 경우의 가상 배치입니다.`,`표시한 아군 ${names(eligible)||'없음'}은 조건부 연결 후보이며 위치·준비는 미관측입니다. 후보 표시 순서는 중요도가 아닙니다.`,'상대 위치는 모르므로 적 초상화를 배치하지 않습니다. 화살표는 안전 경로나 기술 사거리가 아닙니다.']};
  }
  function scenarioLinks(input,catalog,contexts){
    let decision=null,context='OPERATIONS';
    if(input.own_champion==='Caitlyn'&&input.own_position==='BOTTOM'){decision='RECALL';context='LANE';}
    const partners=(context==='LANE'?contexts.lane.partners:contexts.operations.partners).filter(p=>p.eligible);
    if(input.own_champion==='Fiora'&&['TOP','MID'].includes(input.own_position)&&partners.length)decision='SIDE_GROUP';
    if(input.own_champion==='Ornn'&&['TOP','JUNGLE','SUPPORT'].includes(input.own_position)&&partners.length)decision='OBJECTIVE';
    if(!decision||!DirectionEngine||!catalog.directions)return [];
    return catalog.directions.presets.filter(p=>p.input.decision===decision).map(p=>{
      const state=clone(p.input);state.role=input.own_position;state.side=input.side;state.patch=input.patch;state.economy=Object.fromEntries(POSITIONS.map(r=>[r,'UNKNOWN']));
      const old=DirectionEngine.evaluate(state,catalog.directions),self=old.map.entities.find(e=>e.self),otherStart=old.map.entities.find(e=>!e.self)?.start;
      old.map.entities=[self,...partners.map((p,i)=>({id:'context-'+p.champion,self:false,team:'ALLY',champion:p.champion,portrait:catalog.champions[p.champion].portrait,start:otherStart?{x:otherStart.x+i*6,y:otherStart.y-i*6}:{x:self.start.x+(input.side==='BLUE'?5:-5),y:self.start.y+(input.side==='BLUE'?-4:4)},target:null}))];
      old.map.context=context;old.map.notes.push(`문맥 ${context==='LANE'?'바텀 라인전':'라인전 이후 운영'}: ${names(partners)||'연결 동료 미확인'}. 현재 합류·위치·인원은 관측하지 않은 예시입니다.`);
      old.plan.why=old.plan.why.map(x=>x.replaceAll('(수동 입력)','(미래 조건 가정 · 현재 관측 아님)'));
      const assumptions=catalog.directions.decisions.find(d=>d.id===decision).condition_keys.filter(k=>k!=='enemy_visible').map(k=>{const c=catalog.directions.inputs.conditions.find(x=>x.key===k);return c.label+'：'+c.options[state.conditions[k]]+'라는 미래 가정';});
      return {id:p.id,title:p.title,context,assumption_status:'NOT_OBSERVED',assumptions,requirements:[...old.plan.requirements,`${names(partners)||'동료 미확인'}의 ${context==='LANE'?'같은 라인 연결':'운영 연결'}이 실제로 성립하는 경우만 적용`],exceptions:[...old.plan.switch_when,'경제·적 위치·실제 합류는 로딩에서 미확인입니다.'],plan:old.plan,map:old.map,level:'DESIGN_HYPOTHESIS'};
    });
  }
  function representativeDuoRows(input,catalog,lane){
    if(input.own_champion!=='Caitlyn'||input.own_position!=='BOTTOM'||input.opponent_mode!=='ASSIGNED'||lane.kind!=='DUO'||lane.partners[0]?.champion!=='Lux'||input.enemies.find(p=>p.position==='BOTTOM')?.champion!=='Kaisa'||input.enemies.find(p=>p.position==='SUPPORT')?.champion!=='Nautilus')return null;
    const actors={self:'Caitlyn',ally:'Lux',enemies:['Kaisa','Nautilus']};
    const data=[
      {id:'LEVEL1',period:'레벨 1',decision_id:'RECEIVE_WITH_SPACE',judgment:'Q·E를 배운 가정: 수급 위치와 포착 각을 나누기',assumptions:['케이틀린 Q·럭스 E를 배웠고 사용할 수 있음','양쪽 바텀 두 명만 라인에 있고 웨이브·체력·거리를 확인한 미래 상황'],why:'케이틀린 Q는 조준 뒤 관통 피해, 럭스 E는 지역 둔화/폭발 수단입니다. 노틸러스 Q의 적중 시 당김과 기본 공격 속박 때문에, 스킬로 미니언을 받는 위치와 상대가 접근할 각을 함께 비교하는 계획입니다.',action:'럭스 E를 사용할 범위와 내 Q로 받을 미니언을 먼저 맞춥니다. 노틸러스의 접근을 감당할 거리·뒤쪽 공간이 있을 때만 그 위치로 옮겨 짧게 수급/교환합니다. Q 조준 때문에 대응이 늦을 수 있는 위치까지 따라 나가지는 않습니다.',opponent_response:'노틸러스가 Q로 당기거나 가까워져 기본 공격 속박을 노리고, 카이사가 근처 대상에 Q 피해를 연결할 가능성이 있습니다. 실제 기술 선택·피해 우열은 미확인입니다.',alternative:'거리·체력 또는 럭스 E 연결이 부족하면 견제를 강제로 만들지 않고 다음 미니언을 받을 위치를 아군 쪽으로 바꿉니다. 상대가 실제로 전진/기술을 쓰는지 보며 수급 목표를 줄입니다.',changes:['노틸러스가 Q 적중을 노릴 위치로 좁혀 올 때','럭스 E를 배웠거나 쓸 수 있다는 가정이 틀릴 때','보이지 않던 추가 인원이 확인될 때'],evidence_ids:['official:Caitlyn:Q','official:Lux:E','official:Nautilus:Q','official:Nautilus:P','official:Kaisa:Q'],action_ids:['MATCH_LUX_AREA','RECEIVE_SHORT_TRADE','CHANGE_RECEIVE_POSITION']},
      {id:'LEVEL2',period:'레벨 2',decision_id:'FOLLOW_BIND_WITH_EXIT',judgment:'럭스 Q·내 W를 배운 가정: 속박 적중 뒤 제한된 후속',assumptions:['럭스 Q와 케이틀린 W가 실제로 배워져 가용함','양쪽 실제 레벨·거리·체력을 확인했으며 노틸러스의 대응을 감당할 퇴로가 있음'],why:'럭스 Q는 최대 두 적 유닛을 속박하고 케이틀린 W는 발동해야 적 챔피언을 묶습니다. 둘을 배운 경우에만 제어 후속이라는 선택지가 생깁니다. 레벨 2 도달만으로 이 스킬 조합·선점·유리함이 확인되지는 않습니다.',action:'럭스 Q의 실제 챔피언 적중을 본 뒤, 설치 위치·덫 발동과 후속 거리까지 맞는 경우 W와 짧은 공격을 검토합니다. 속박을 보았다는 이유만으로 덫 발동이나 확정 연계/킬을 가정하지 않습니다.',opponent_response:'노틸러스는 럭스 Q가 빠진 틈에 Q 접근 또는 기본 공격 속박으로 역대응할 수 있습니다. 카이사도 계속 공격할 권리가 있으므로 한 명의 속박만으로 상대 둘의 대응이 사라지지는 않습니다.',alternative:'럭스 Q가 빗나가거나 덫 연결이 불명확하면 추가 전진을 접고 럭스와 같은 수급선으로 돌아옵니다. 상대가 기술을 쓰도록 억지로 몸을 내주는 행동은 권하지 않습니다.',changes:['럭스 Q 빗나감/가용성 상실','노틸러스 접근·카이사 후속이 열림','추가 인원·레벨 또는 웨이브 조건이 바뀜'],evidence_ids:['official:Lux:Q','official:Caitlyn:W','official:Nautilus:Q','official:Nautilus:P','official:Kaisa:Q'],action_ids:['OBSERVE_BIND_HIT','CONDITIONAL_TRAP_FOLLOW','END_ADVANCE_AFTER_MISS']},
      {id:'LEVEL3_5',period:'레벨 3~5',decision_id:'KEEP_ESCAPE_VS_REENGAGE',judgment:'투망·보호막을 배운 가정: 공격과 이탈 자원을 나누기',assumptions:['케이틀린 E·럭스 W/E가 배워져 있고 현재 가용성을 확인함','현재 웨이브·상대 두 명의 접근 각과 자원을 확인한 미래 상황'],why:'케이틀린 E는 둔화와 뒤로 밀리는 수단이고, 럭스 W는 마법봉에 닿는 아군에게 보호막을 줍니다. E의 원문에는 지역 시야 제공도 있습니다. 이 수단을 함께 남길 수 있는지에 따라 견제와 수급 위치를 다르게 잡는 가설입니다.',action:'노틸러스의 접근 대응이 남으면 E를 단순 견제에 모두 쓰기보다 이탈에 남기는 선택을 비교합니다. 럭스 W가 닿을 위치를 맞추고, 럭스 E로 확인한 범위의 정보만 사용해 다음 수급 위치를 옮깁니다.',opponent_response:'노틸러스는 가까운 거리의 기본 공격 속박이나 Q로 재접근을 노릴 수 있고, 카이사는 W 적중으로 플라즈마를 쌓을 수 있습니다. 투망 또는 보호막 하나로 이 대응을 모두 무효화한다고 보지 않습니다.',alternative:'E가 없거나 보호막이 닿지 않으면 교환을 더 이어가지 않고 아군 쪽 받을 자원과 회복을 고릅니다. E로 보지 못한 구역은 계속 미확인이며, 정보 확인을 위해 혼자 그곳으로 이동하지 않습니다.',changes:['E를 소모하거나 W 보호 연결이 끊김','노틸러스가 거리를 좁힘/카이사 W 적중','지역 시야 밖 정보나 추가 인원이 문제됨'],evidence_ids:['official:Caitlyn:E','official:Lux:W','official-detail:Lux:W','official-detail:Lux:E','official:Nautilus:Q','official:Nautilus:P','official:Kaisa:W'],action_ids:['KEEP_E_FOR_EXIT','MATCH_SHIELD_CONTACT','LIMIT_TO_OBSERVED_AREA','RESET_IF_ESCAPE_LOST']},
      {id:'LEVEL6',period:'레벨 6',decision_id:'RESPECT_TARGETED_CONTROL',judgment:'궁극기를 배운 가정: 표식·추적 제어까지 포함해 배치 변경',assumptions:['해당 궁극기를 실제로 배웠고 가용성을 확인한 상황','카이사의 플라즈마 표식과 후속 거리·내 체력/보호 연결을 확인할 수 있음'],why:'노틸러스 R은 대상을 추적해 띄우고 기절시키며, 카이사 R 상세 원문은 플라즈마 표식 대상 근처 돌진을 요구합니다. 카이사 P에는 아군 이동 불가 효과도 표식을 더한다는 설명이 있습니다. 미니언이나 거리만으로 이 연결이 사라진다고 가정하지 않는 계획입니다.',action:'추적 제어와 표식 후속이 열릴 경우 럭스 W가 닿을 거리와 이탈 공간부터 맞춥니다. 케이틀린 R은 적 챔피언이 대신 막을 수 있으므로 마무리가 보장된다고 추격하지 않습니다. 투망으로 노틸러스 R을 취소할 수 있다고 가정하지 않습니다.',opponent_response:'노틸러스의 이동 불가 효과가 카이사의 표식·R 후속 조건과 연결될 가능성이 있습니다. 실제 가용성·표식·아군 거리와 별개로 자동 연계가 완성된다고 단정하지 않습니다.',alternative:'상대 궁극기 상태나 표식이 불명확하면 새로운 마무리 추격보다 럭스와 받을 공간을 좁혀 연결을 유지합니다. 표식/접근이 생기면 공격 대상을 바꾸고 아군 쪽으로 전진 폭을 줄입니다.',changes:['표식·추적 제어·카이사 후속 거리가 확인됨','럭스 보호 연결이나 내 이탈 자원 상실','상대 궁극기 가용성이 달라짐'],evidence_ids:['official:Nautilus:R','official:Kaisa:P','official-detail:Kaisa:R','official:Caitlyn:R','official:Caitlyn:E','official-detail:Lux:W'],action_ids:['CHECK_PLASMA_ACCESS','KEEP_LUX_COVER','NO_ASSUMED_R_CANCEL','STOP_FINISH_CHASE']},
      {id:'FIRST_PURCHASE',period:'첫 귀환·구매 이후',decision_id:'REASSESS_PURCHASE_AND_RETURN',judgment:'실제 구매가 확인된 가정: 이동·공격 자원과 복귀 손실 재비교',assumptions:['실제로 구매한 아이템과 체력·마나 회복을 확인한 미래 상황','상대 두 명의 구매/복귀와 다음 웨이브는 확인한 범위만 사용'],why:'공식 장화의 이동 속도와 롱소드의 공격력 속성은 서로 다른 변화입니다. 실제 구매 효과를 확인한 경우에만 접근/공격 조건을 재비교합니다. 어느 것을 샀는지, 최적 첫 구매와 이 매치업의 피해 우열은 로딩에서 미확인입니다.',action:'내 구매가 이동·공격 중 무엇을 바꾸었는지 확인하고 럭스의 자원/복귀와 다음 웨이브를 함께 맞춥니다. 상대 구매가 불명확하면 이전과 같은 교환이 이긴다고 가정하지 않고 짧은 수급·교환부터 다시 비교합니다.',opponent_response:'노틸러스 Q/P의 제어와 카이사의 표식 후속 조건은 단순 아이템 구매만으로 없어진다고 보지 않습니다. 상대도 구매·회복 후 돌아올 수 있습니다.',alternative:'복귀가 어긋나 1명만 먼저 라인에 서거나 큰 손실이 예상되면 압박보다 받을 위치·자원을 줄이고 회복/동시 복귀를 비교합니다. 구매 아이템 하나로 닻을 피하거나 맞교환을 이긴다고 보지 않습니다.',changes:['실제 아이템 속성·상대 구매가 확인됨','럭스와 복귀/자원 연결이 어긋남','웨이브·체력/마나·인원이 바뀜'],evidence_ids:['official-item:1001','official-item:1036','official:Nautilus:Q','official:Nautilus:P','official:Kaisa:P'],action_ids:['COMPARE_ACTUAL_PURCHASE_PROPERTY','MATCH_RETURN_RESOURCES','LIMIT_SOLO_RECEIVE']},
      {id:'FIRST_CORE',period:'첫 핵심 아이템 이후',decision_id:'KEEP_FOLLOWUP_AFTER_CORE',judgment:'핵심 아이템 완성 가정: 후속 지속/회복 계획을 다시 선택',assumptions:['내 실제 완성 아이템과 상대 아이템·레벨·체력/인원을 확인함','럭스의 제어/보호와 내 이탈 수단이 연결되는지 확인할 수 있는 미래 상황'],why:'완성 아이템에 따른 실제 피해량·상성 역전 근거는 없습니다. 따라서 아이템 완성 자체를 진입 허가로 쓰지 않고, 럭스 제어 적중과 노틸러스의 남은 제어·카이사 후속을 함께 비교하는 계획입니다.',action:'럭스 제어가 적중하고 남은 상대 대응·후속 거리까지 감당할 때만 접근 가능한 대상에 공격을 이어갑니다. 이 조건이 없으면 라인 자원 확보→회복/구매 또는 다음 합류 준비 중 손실이 작은 쪽을 고릅니다. 새 아이템을 이유로 혼자 추격하지 않습니다.',opponent_response:'노틸러스의 남은 제어와 카이사의 표식·돌진은 여전히 계획 전환 조건입니다. 상대 아이템·지원 인원 변화도 기존 교환 계획을 무효화할 수 있습니다.',alternative:'내 이탈이나 럭스 연결이 끊기면 짧게 공격한 뒤 자원 수급/회복으로 돌아옵니다. 사이드 이동·합류는 추가 인원·웨이브·복귀 손실이 확인된 별도 운영 계획에서만 비교합니다.',changes:['상대 아이템/지원 인원 또는 남은 제어가 달라짐','럭스 연결이나 내 이탈이 사라짐','라인 유지와 다음 합류의 자원 손실 조건이 바뀜'],evidence_ids:['official:Lux:Q','official-detail:Lux:W','official:Caitlyn:E','official:Nautilus:R','official-detail:Kaisa:R'],action_ids:['FOLLOW_CONFIRMED_CONTROL','KEEP_SELF_EXIT','CONVERT_TO_RESOURCE_OR_RECOVERY']}
    ];
    return data.map(row=>({...row,actors:clone(actors),assumption_status:'NOT_OBSERVED',fact_scope:'공식: 연결된 기술/아이템의 명시한 성질. 가정: 위 스킬·자원·인원 조건을 갖춘 미래 장면. 행동 선택·연계 타이밍·우열은 설계 가설이며 실전 검증 없음.',level:'DESIGN_HYPOTHESIS'}));
  }
  function genericLaneRows(input,catalog,lane,own,relevantStats){
    const ownQ=fact(own,'Q'),ownR=fact(own,'R'),ownE=fact(own,'E'),slots=functionalSlots[own.id]||{},tool=fact(own,[slots.PICK,slots.PRESSURE,'Q'].find(s=>s&&s!=='R'));
    const peer=names(lane.partners)||'같은 라인 동료 미확인',enemy=names(lane.threats)||'맞라이너 미확인',resource=input.own_position==='JUNGLE'?'정글 자원':input.own_position==='SUPPORT'?'아군 수급 보조':'CS';
    const ids=[...new Set([ownQ.id,tool.id,ownR.id,ownE.id,...lane.partners.flatMap(p=>p.evidence_ids),...lane.threats.flatMap(p=>p.evidence_ids)])].sort();
    return [['LEVEL1','레벨 1',ownQ,'배운 기본 기술로 받을 자원과 상대 대응 위치를 나누기'],['LEVEL2','레벨 2',tool,'새 기술이 연결되는 경우만 교환 폭 바꾸기'],['LEVEL3_5','레벨 3~5',ownE,'이탈·보호 자원을 남길지 재비교'],['LEVEL6','레벨 6',ownR,'궁극기 대상·후속·이탈 조건 추가'],['FIRST_PURCHASE','첫 귀환·구매 이후',tool,'실제 구매·회복·복귀 손실 비교'],['FIRST_CORE','첫 핵심 아이템 이후',tool,'완성 아이템과 남은 제어를 따로 비교']].map(([id,period,f,decision])=>({id,period,judgment:decision+' · 매치업 우열 미확인',why:`${f.name}: ${f.text} 같은 라인 동료는 ${peer}, 상대는 ${enemy}입니다. ${id==='FIRST_PURCHASE'&&relevantStats.length?'기존 챔피언·포지션 구매 관측은 상대별 상성·권장 시점 근거가 아닙니다.':''}`,action:input.own_position==='SUPPORT'&&id==='LEVEL1'?`${peer}의 수급을 보조할 위치와 배운 기술의 연결을 맞춥니다. 아군 CS를 대신 가져오라는 뜻이 아닙니다.`:`${f.name}을 실제로 배웠고 상대 대응과 후속/이탈 조건이 맞는 경우에만 ${resource}와 교환 범위를 넓힙니다. 부족하면 받을 자원·회복·같은 라인 연결 위치를 다시 고릅니다.`,assumptions:[`${f.name}이 실제로 배워져 가용하고 상대 대응·자원·웨이브를 확인한 미래 상황`],opponent_response:`${enemy}의 실제 습득·가용성과 대응은 별도 확인합니다. 한 스킬의 설명만으로 매치업 우열을 확정하지 않습니다.`,alternative:`연결이 없으면 ${resource}를 받을 위치와 회복/복귀 손실을 비교합니다. 다른 라인의 아군이 이미 와 있다고 보지 않습니다.`,changes:['같은 라인 기술·자원·웨이브·실제 인원이 바뀔 때','상대 배치/구매가 확인되거나 수정될 때'],evidence_ids:[...ids,...(id==='FIRST_PURCHASE'?relevantStats.map(s=>s.id):[])],assumption_status:'NOT_OBSERVED',fact_scope:'공식 기술의 성질과 조건부 행동 해석을 구분합니다. 현재 스킬 습득·우열은 미확인입니다.',level:'DESIGN_HYPOTHESIS'}));
  }
  function analyze(raw,catalog){
    const validated=validate(raw,catalog),input={...validated,allies:sortedRows(validated.allies),enemies:sortedRows(validated.enemies)},own=catalog.champions[input.own_champion],base=roleFor(input,own);
    const allies=composition(input.allies,catalog),enemies=composition(input.enemies,catalog),laneCtx=laneContext(input,catalog);
    const operations=contextCandidates(input,catalog,base,'OPERATIONS'),fight=contextCandidates(input,catalog,base,'TEAMFIGHT');
    const junglers=(side)=>input[side].filter(p=>p.position==='JUNGLE'&&p.champion!==input.own_champion).sort(byId).map(p=>candidate(p,catalog,'JUNGLE_INTERVENTION','입력'+'한 정글 배치의 개입 후보. 실제 위치·합류 시점은 관측하지 않았으며 기본 라인 인원에 합치지 않음.'));
    const contexts={lane:laneCtx,jungle:{partners:junglers('allies'),threats:junglers('enemies'),conditions:['정글러 위치·실제 접근 경로와 라이너 자원이 확인된 경우에만 개입 장면을 별도로 비교','미확인 정글 위치를 안전이나 확정 갱으로 바꾸지 않기'],observation:'NOT_OBSERVED'},operations,teamfight:fight};
    const roles=proposeRole(base,own,fight,catalog),peer=names(laneCtx.partners)||'같은 라인 동료 미확인',laneEnemies=names(laneCtx.threats)||'맞라이너 미확인';
    const allyFunctions=[...new Set(fight.partners.flatMap(p=>p.kinds).filter(k=>k!=='UNKNOWN'))].sort(),enemyFunctions=[...new Set(fight.threats.flatMap(p=>p.kinds).filter(k=>k!=='UNKNOWN'))].sort();
    const allyFunctionText=allyFunctions.map(k=>kindNames[k]).join('·')||'기능 연결 미확인',enemyFunctionText=enemyFunctions.map(k=>kindNames[k]).join('·')||'대응 기능 미확인';
    const control=fight.partners.filter(p=>p.kinds.includes('PICK')&&p.evidence_ids.length),cover=fight.partners.filter(p=>p.kinds.includes('COVER')&&p.evidence_ids.length),partners=names(fight.partners.filter(p=>p.eligible))||'기술 연결이 확인되는 아군',threatName='상대의 접근·제어·견제';
    const relevantStats=(catalog.statistics||[]).filter(s=>s.champion===own.id&&s.position===input.own_position&&input.patch&&s.patch===input.patch.split('.').slice(0,2).join('.')).sort((a,b)=>a.id<b.id?-1:1);
    const special=representativeDuoRows(input,catalog,laneCtx),rows=special||genericLaneRows(input,catalog,laneCtx,own,relevantStats);
    const laneStatus=laneCtx.opponent?'조건부 계획 · 매치업 우열 미확인':'상대 미확인 · 조건부 준비 계획';
    const lane={opponent:laneCtx.opponent,status:laneStatus,matchup_id:special?'Caitlyn_Lux__Kaisa_Nautilus_v2':null,rows,interactions:special?['럭스 Q 적중→케이틀린 W 후속은 설치·발동·거리 조건이 필요하며 확정 연계가 아닙니다.','노틸러스의 이동 불가 수단과 카이사의 플라즈마/궁극기 후속을 함께 봅니다.','럭스 Q는 최대 두 유닛에 적용됩니다. 노틸러스 Q의 미니언 충돌 규칙은 이 원문에서 확인하지 않았으므로 웨이브 뒤면 안전하다고 단정하지 않습니다.']:[`같은 라인 동료 ${peer}와 상대 ${laneEnemies}의 실제 기술 조건만 이 표에 연결합니다.`],wave:'미니언은 수급·밀기·귀환 조건입니다. 특정 기술의 충돌/관통 규칙이 확인되지 않았으면 미니언만으로 진입을 막는다고 가정하지 않습니다.',jungle:'정글 개입은 아래 별도 조건부 항목입니다. 로딩에서는 위치·실제 도착·갱 시점을 모르며 기본 라인 인원에 합치지 않습니다.',reset_roam:'웨이브 도착·체력/마나·실제 구매와 동료 복귀가 확인된 뒤 귀환 후보를 비교합니다. 이동/합류는 복귀 손실과 아군 준비가 맞는 별도 운영 조건입니다.',recovery:'같은 라인 연결·퇴로가 끊기면 받을 자원과 회복/복귀를 다시 고릅니다. 포탑 아래라는 이유만으로 안전을 보장하지 않습니다.'};
    if(input.own_position==='JUNGLE')rows[0].action='배운 기술·체력과 정글 자원을 받을 동선을 확인합니다. 적 정글 위치를 상상해 침투하지 않고, 아군과 실제 연결 가능한 입구·가까운 자원·귀환을 비교합니다.';
    const patch_status=input.patch===null?'UNKNOWN':input.patch.split('.').slice(0,2).join('.')===catalog.source_patch.split('.').slice(0,2).join('.')?'SOURCE_MAJOR_MATCH':'MISMATCH';
    const uncertainty=[...(laneCtx.opponent?[]:['맞라이너 미확인']),...(patch_status==='MISMATCH'?['입력 패치 '+input.patch+'와 공식 자료 '+catalog.source_patch+'가 다릅니다. 적용 범위 재확인이 필요합니다.']:[]),...(!input.patch?['게임 패치 미확인']:[]),'스킬 습득·가용성·체력·웨이브·현재 위치/실제 합류는 로딩에서 미관측','요약은 유형별 계획입니다. 상세의 다른 후보 생략을 위협 부재나 중요도 순위로 읽지 마세요.'];
    const attackPlan=control.length?`아군 ${names(control)}의 제어가 적중하고 ${cover.length?names(cover)+'의 보호가 닿는 거리':'내 이탈과 후속 거리'}가 맞으면 ${own.name}의 공격을 잇습니다. 상대 대응으로 연결이 끊기면 추격을 접고 남은 인원·웨이브로 포탑·목표물 압박과 귀환을 비교합니다.`:`${own.name}의 기본 역할은 ${roles.base.label}입니다. 현재 연결할 수단이 부족하면 공격 가능한 대상·가까운 자원과 내 이탈 공간부터 고르고, 실제 연결이 확인될 때만 계획을 넓힙니다.`;
    const laneKey=special?'럭스 Q가 적중하고 덫 발동·후속 거리까지 맞으면 케이틀린 W 후속을 검토합니다. 노틸러스 Q/기본 공격 속박과 카이사 후속이 남으면 짧게 끝내고 럭스 쪽 수급선으로 돌아옵니다.':`${peer}와 ${laneEnemies}의 기술을 함께 비교합니다. 실제 습득·가용성과 수급/이탈 조건이 맞는 경우만 교환 폭을 바꿉니다.`;
    const roleAttack=roles.proposed.action_ids.includes('KEEP_COVER_CONNECTION')?`보호 후보 ${names(cover)}가 실제로 닿는 거리에서, 제어 후보 ${names(control)||'미확인'}의 적중 뒤 접근 가능한 대상을 공격합니다.`:roles.proposed.action_ids.includes('FOLLOW_CONFIRMED_CONTROL')?`제어 후보 ${names(control)}의 적중·후속 거리와 내 이탈이 함께 맞을 때만 공격을 잇습니다.`:'기본 역할을 유지하되 확인한 기술과 가까운 자원·후속/퇴로 조건부터 준비합니다.';
    const entry=fight.threats.filter(p=>p.kinds.some(k=>['ACCESS','ASSASSIN'].includes(k)&&signature(catalog.champions[p.champion],k)));
    const ranged=fight.threats.filter(p=>p.kinds.some(k=>['PICK','PRESSURE'].includes(k)));
    const enemyPlan=special?'라인에서는 노틸러스의 제어 뒤 카이사가 공격을 잇는 계획이 가능합니다. 한타에서는 다른 접근 후보도 함께 보되, 표식·실제 거리·기술 가용성이 조건이며 상대의 실제 의도는 미확인입니다.':entry.length?`상대 접근 후보 ${names(entry)}가 공격·이탈 연결을 끊으려 할 가능성이 있습니다. 실제 기술·후속 거리·현재 위치는 미확인이며 유형별 전체 후보는 상세에서 비교합니다.`:ranged.length?`상대 제어·견제 후보 ${names(ranged)}가 공간·체력을 먼저 바꾸려 할 가능성이 있습니다. 연결하지 못한 접근 수단은 미확인이며, 실제 거리·가용성과 의도는 별도입니다.`:'확인한 기능만으로 상대의 주된 계획은 미확인입니다. 공식 기술과 조건이 확인된 범위에서 대응을 준비합니다.';
    const summary={our_plan:attackPlan,enemy_plan:enemyPlan,collision:'우리의 제어·보호·후속 거리가 상대의 접근·제어·견제에 끊기는지가 핵심입니다. 라인전 상대와 한타 후보는 상세에서 구분합니다.',my_role:`${POSITION_NAMES[input.own_position]} ${own.name}: 기본 ${roles.base.label} / 이번 계획 ${roles.proposed.label}.`,lane_key:laneKey,fight_key:roleAttack+' '+roles.proposed.conditions.at(-1)+'. 연결이 끊기면 추격 대신 공격 대상·위치를 바꿉니다.',remember:[special?'럭스 Q 적중만으로 확정 덫 연계는 아님; 노틸러스와 카이사의 남은 대응을 함께 보기':`${laneEnemies}의 대응과 내 기술·같은 라인 연결을 함께 보기`,roles.proposed.conditions[0],'보이지 않는 적·실제 합류·미니언 차단 효과를 임의로 확정하지 않기'],uncertainties:uncertainty};
    const gameplan={base:attackPlan,prepare:[`운영 연결 후보 ${names(operations.partners.filter(p=>p.eligible))||'미확인'}의 실제 웨이브·접근 거리·기술 상태를 확인한 뒤 움직일 순서를 맞춥니다.`,'상대의 유형별 대응과 내 이탈/회복 수단을 함께 확인합니다.','목표물·시야·인원이 확인된 후 경합 또는 가까운 자원 교환을 비교합니다.'],fallback:'연결이 부족하면 보이지 않는 반대편이 비었다고 가정하지 않고 아군 쪽 보이는 자원·회복·구매로 목표를 낮춥니다.',switch_when:['아군 후속 또는 내 이탈/보호 조건이 사라짐','상대 증원·체력 손실·남은 제어가 확인됨','웨이브·구매·목표물 조건이 달라짐'],stages:[{stage:'초반',role:`${POSITION_NAMES[input.own_position]} ${own.name}의 라인/정글 자원과 기술 조건 준비`,conditions:['같은 라인 동료와 직접 상대만 기본 문맥에 연결','정글 개입은 따로 관측될 때 비교']},{stage:'중반',role:base==='SIDE_RETURN'?'본대의 대기·복귀 수단이 맞을 때 사이드 압박, 아니면 합류 거리 축소':roles.proposed.label,conditions:['웨이브·합류 자원 손실·아군 실제 준비를 함께 확인']},{stage:'후반',role:'남은 기술·인원과 귀환/목표물 이득 전환 비교',conditions:['아이템 완성만으로 재진입하지 않기','현재 위치·기술을 확인한 후보만 연결']}],side_vs_group:'사이드/본대 선택은 보이는 자원·복귀 수단·본대의 대기와 상대 접근이 함께 확인된 경우 비교합니다. 유형별 후보가 있다고 실제 합류를 가정하지 않습니다.',objectives:'실제로 존재하는 목표물과 웨이브·체력·인원·접근 정보를 확인한 뒤 경합을 준비합니다. 미연결 생성 시각·승률을 만들지 않습니다.',conversion:'교전 뒤 실제 남은 인원·체력·웨이브와 접근 가능한 목표물을 보고 포탑·목표물·귀환 중 이득을 고릅니다. 킬이 모든 이득을 보장하지 않습니다.'};
    const teamfight={role:`${own.name}: ${roles.proposed.label}. ${roleAttack}`,partners:fight.partners,threats:fight.threats,setup:[roles.proposed.conditions[0],'유형별 후보는 현재 배치가 아닙니다. 실제 위치·준비를 확인한 후보만 연결합니다.'],actions:[`${partners} 중 실제 후속/보호가 연결될 아군과 내 이탈 방향을 먼저 맞춥니다. 로딩에서 이미 모여 있다고 보지 않습니다.`,kitAction(own,base,partners,threatName,names(control)),`${threatName}로 연결이 끊기면 공격 대상·위치를 바꾸거나 아군 쪽으로 이탈합니다.`],switch_when:['아군 선교전에 닿지 못하면 억지 후속 대신 가까운 연결/보호로 변경','내 이동 수단 사용 후 퇴로가 사라지면 추격 중단'],exit:['보호·후속·내 이탈 자원이 끊기거나 새 적 접근이 확인됨','퇴로 정보가 없으면 보이지 않는 길로 추격하지 않기'],after:[gameplan.conversion],map:basicMap(input,catalog,base,fight.partners)};
    const facts=input.allies.concat(input.enemies).flatMap(p=>catalog.champions[p.champion].facts);
    const usedIds=new Set(rows.flatMap(r=>r.evidence_ids));
    for(const f of catalog.context_facts||[])if(usedIds.has(f.id)||(f.id==='official-detail:Kaisa:R'&&input.own_champion==='Kaisa'))facts.push(f);
    const rules=[...new Map(input.allies.concat(input.enemies).flatMap(p=>catalog.champions[p.champion].profile?.rule_refs||[]).map(r=>[r.id,{...r,level:'EXISTING_RULE',review_state:'EXPLORATORY',interpretation:'기존 탐색 분류를 문맥별로 참고하며 전략 승인/실전 효과를 승계하지 않습니다.'}])).values()].sort((a,b)=>a.id<b.id?-1:1);
    const evidence={facts:[...new Map(facts.map(f=>[f.id,f])).values()].sort((a,b)=>a.id<b.id?-1:1),rules,statistics:relevantStats,lectures:[],unknowns:[...uncertainty,'레벨별 매치업 우열·피해량·최적 스킬/구매·미확인 충돌 규칙'],limits:['공식 기술/아이템 사실과 신규 조건부 전략 해석은 별도입니다.','기존 유형 분류는 EXPLORATORY이며 미부여 유형은 능력 부재가 아닙니다.','라인전/운영/한타 대상은 문맥별 후보로 선정합니다. 배열 표시 순서가 중요도를 뜻하지 않습니다.','상황 가정은 실제 습득·위치·합류·아이템 관측이 아닙니다.','귀환 통계는 챔피언/포지션 관측이며 매치업/최적 시점 근거가 아닙니다.','경기 전 학습/경기 후 복기용. 실시간 지시·비공개 정보·게임 조작 없음.'],patch_status,strategy_level:'DESIGN_HYPOTHESIS',real_coaching_n:0,accuracy:null};
    return {schema_version:'lol-coach-loading-report-v2',input,summary,composition:{allies,enemies},roles,contexts,gameplan,lane,teamfight,scenarios:scenarioLinks(input,catalog,contexts),evidence};
  }
  return {resolveChampion,exampleInput,fromDraft,analyze};
});

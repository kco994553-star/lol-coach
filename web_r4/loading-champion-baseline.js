/* Standalone champion lookup. Retained prose is not a complete/actionable plan. */
(function(root,factory){
  if(typeof module==='object'&&module.exports)module.exports=factory(require('./loading-direction-profiles.js'));
  else root.LoadingChampionBaseline=factory(root.LoadingDirectionProfiles);
})(typeof globalThis!=='undefined'?globalThis:this,function(defaultProfiles){
  'use strict';
  const VERSION='champion-baseline-backend-v1';
  const POSITIONS=['TOP','JUNGLE','MID','BOTTOM','SUPPORT'];
  const PHASES=['lane','operations','fight'];
  const SOURCE='web_r4/loading-direction-profiles.js';
  const own=(x,k)=>x!==null&&typeof x==='object'&&Object.hasOwn(x,k);
  const object=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
  const text=x=>typeof x==='string'&&x.trim().length>0;
  const clone=x=>JSON.parse(JSON.stringify(x));
  const normalize=x=>x.normalize('NFKC').toLowerCase().replace(/[^a-z0-9가-힣]/g,'');
  const compare=(a,b)=>a<b?-1:a>b?1:0; // Stable across machines/locales.
  const patch=x=>typeof x==='string'&&/^\d{1,3}\.\d{1,3}(?:\.\d{1,3})?$/.test(x);
  function fail(code){const error=new Error(code);error.code=code;throw error;}
  function keys(value,allowed){
    if(!object(value)||Object.keys(value).some(k=>!allowed.includes(k)))fail('INPUT_INVALID');
  }
  function createService(rawCatalog,rawProfiles=defaultProfiles){
    if(!object(rawCatalog)||rawCatalog.format!=='lol-coach-loading-v1'||!patch(rawCatalog.source_patch)||
      !object(rawCatalog.champions)||!Object.keys(rawCatalog.champions).length)fail('CATALOG_INVALID');
    const heroes=new Map(),aliases=new Map();
    for(const [id,raw] of Object.entries(rawCatalog.champions)){
      if(!/^[A-Za-z][A-Za-z0-9]{0,59}$/.test(id)||!object(raw)||raw.id!==id||!text(raw.name)||
        !Array.isArray(raw.aliases)||!raw.aliases.every(a=>text(a)&&a.length<=100))fail('CATALOG_INVALID');
      const row=clone(raw),terms=[...new Set([id,row.name,...row.aliases].map(normalize))].filter(Boolean);
      heroes.set(id,{...row,terms});
      for(const term of terms){if(!aliases.has(term))aliases.set(term,[]);aliases.get(term).push(id);}
    }
    // Capture the publication once. No per-query network, mutable shared cache or AI.
    const dataPatch=rawCatalog.source_patch;
    const sourceBindings=clone(Array.isArray(rawCatalog.source_bindings)?rawCatalog.source_bindings:[]);
    const profiles=rawProfiles==null?null:clone(rawProfiles);
    const bundleValid=object(profiles)&&profiles.schema_version==='gameplan-direction-profiles-v1'&&
      text(profiles.version)&&patch(profiles.source_patch)&&profiles.review_state==='TACTICAL_UNREVIEWED'&&object(profiles.champions);
    const profileFor=id=>bundleValid&&own(profiles.champions,id)?profiles.champions[id]:null;
    function resolve(query){
      if(!text(query)||query.length>100)fail('INPUT_INVALID');
      // Selection carries an exact canonical ID; ambiguous search terms remain unselected.
      if(heroes.has(query))return query;
      const found=aliases.get(normalize(query))||[];
      if(!found.length)fail('CHAMPION_NOT_FOUND');
      if(found.length!==1)fail('CHAMPION_AMBIGUOUS');
      return found[0];
    }
    function selection(raw){
      keys(raw,['champion','position','patch','game','mode']);
      const position=raw.position??null,requestedPatch=raw.patch??null;
      if(position!==null&&!POSITIONS.includes(position)||requestedPatch!==null&&!patch(requestedPatch)||
        own(raw,'game')&&raw.game!=='LOL'||own(raw,'mode')&&raw.mode!=='SUMMONERS_RIFT')fail('INPUT_INVALID');
      return {game:'LOL',mode:'SUMMONERS_RIFT',champion:resolve(raw.champion),position,patch:requestedPatch};
    }
    function blankPhase(phase,position,status,reason){
      return {label:phase==='lane'?(position==='JUNGLE'?'초반 정글':'라인전'):phase==='operations'?'운영':'한타',
        status,reason_codes:[reason],reference:null,delivery:null,tags:[]};
    }
    function getBaseline(raw){
      const input=selection(raw),entry=profileFor(input.champion),hero=heroes.get(input.champion);
      // A two-component request compares the game patch; a three-component request is exact.
      const patchStatus=input.patch===null?'NOT_CONFIRMED':
        (input.patch.split('.').length===2?dataPatch.split('.').slice(0,2).join('.')===input.patch:dataPatch===input.patch)?'MATCH':'MISMATCH';
      const output={schema_version:'gameplan-champion-baseline-v1',view_mode:'BASELINE',input,
        versions:{backend:VERSION,normalization:'champion-name-nfkc-v1',data:'lol-coach-loading-v1',source_patch:dataPatch,
          direction_data:bundleValid?profiles.version:null},
        composition:null,observation:false,tactical_validation:'UNREVIEWED',patch_status:patchStatus,
        status:null,profile:null,phases:{},limitations:[
          '작성된 기본 방향 참고 자료입니다. 전술 효과와 현재 경기 상태를 검증한 결과가 아닙니다.',
          '5개 행동·행동 태그는 아직 작성되지 않았습니다. 조합별 승패나 최적 행동을 판단하지 않습니다.',
          ...(input.patch===null?['적용할 경기 패치는 미확인입니다. 표시된 자료 패치를 확인하세요.']:[])]};
      let blocked=null,reason=null;
      if(!input.position){blocked='POSITION_REQUIRED';reason='POSITION_NOT_SELECTED';}
      else if(!bundleValid){blocked='SOURCE_REVIEW_REQUIRED';reason='PROFILE_BUNDLE_INVALID';}
      else if(!own(profiles.champions,input.champion)){blocked='NO_PROFILE';reason='CHAMPION_PROFILE_MISSING';}
      else if(!object(entry)||!POSITIONS.includes(entry.role)){blocked='SOURCE_REVIEW_REQUIRED';reason='PROFILE_INVALID';}
      else if(entry.role!==input.position){blocked='UNSUPPORTED_POSITION';reason='POSITION_PROFILE_MISSING';}
      else if(profiles.source_patch!==dataPatch||patchStatus==='MISMATCH'){blocked='SOURCE_REVIEW_REQUIRED';reason='PATCH_MISMATCH';}
      else if(!Array.isArray(entry.required_slots)||!entry.required_slots.length||
        new Set(entry.required_slots).size!==entry.required_slots.length||!entry.required_slots.every(s=>['P','Q','W','E','R'].includes(s))){
        blocked='SOURCE_REVIEW_REQUIRED';reason='PROFILE_INVALID';
      }
      if(blocked){
        output.status=blocked;
        for(const phase of PHASES)output.phases[phase]=blankPhase(phase,input.position,blocked,reason);
        return output;
      }
      output.profile={id:input.position.toLowerCase()+'-direction:'+input.champion,version:profiles.version,
        source_path:SOURCE,source_patch:profiles.source_patch,review_state:profiles.review_state};
      for(const phase of PHASES){
        const p=object(entry.phases)&&own(entry.phases,phase)?entry.phases[phase]:null;
        let result=blankPhase(phase,input.position,'SOURCE_REVIEW_REQUIRED','PHASE_CONTENT_INVALID');
        output.phases[phase]=result;
        if(p===null){result.status='NO_PHASE_CONTENT';result.reason_codes=['PHASE_CONTENT_MISSING'];continue;}
        if(!object(p)||!['gain','method','explanation'].every(k=>text(p[k]))||!Array.isArray(p.keys)||!p.keys.length||
          new Set(p.keys).size!==p.keys.length||!p.keys.every(k=>entry.required_slots.includes(k)))continue;
        const templates=[p.gain,p.method,p.explanation];
        if(templates.some(s=>s.replace(/\{[PQWER]\}/g,'').match(/[{}]/)||
          [...s.matchAll(/\{([PQWER])\}/g)].some(m=>!p.keys.includes(m[1]))))continue;
        const facts=[];
        for(const slot of p.keys){
          const matches=(Array.isArray(hero.facts)?hero.facts:[]).filter(f=>object(f)&&f.slot===slot);
          if(matches.length!==1)break;
          const f=matches[0];
          if(f.id!==`official:${input.champion}:${slot}`||!text(f.name)||!text(f.url)||!text(f.locator)||
            f.patch!==dataPatch||!/^[a-f0-9]{64}$/.test(f.sha256||'')||
            !sourceBindings.some(b=>object(b)&&b.local_source===f.local_source&&b.sha256===f.sha256))break;
          facts.push({id:f.id,slot:f.slot,name:f.name,patch:f.patch,sha256:f.sha256,url:f.url,local_source:f.local_source,locator:f.locator});
        }
        if(facts.length!==p.keys.length){result.reason_codes=['MECHANISM_SOURCE_MISSING_OR_MISMATCH'];continue;}
        const render=s=>s.replace(/\{([PQWER])\}/g,(_,slot)=>facts.find(f=>f.slot===slot).name+'('+slot+')');
        result.status='REFERENCE_ONLY';result.reason_codes=['FIVE_ACTION_CONTENT_NOT_AUTHORED'];
        result.reference={headline:render(p.gain),methods:[render(p.method)],paragraphs:[render(p.explanation)],
          source_path:SOURCE,locator:`champions.${input.champion}.phases.${phase}`,profile_version:profiles.version,
          source_patch:profiles.source_patch,review_state:profiles.review_state,evidence:facts,
          mechanism_evidence_is_tactical_validation:false};
      }
      const states=Object.values(output.phases).map(p=>p.status);
      output.status=states.every(s=>s==='REFERENCE_ONLY')?'REFERENCE_ONLY':states.includes('REFERENCE_ONLY')?'PARTIAL':
        states.every(s=>s==='NO_PHASE_CONTENT')?'NO_PHASE_CONTENT':'SOURCE_REVIEW_REQUIRED';
      return output;
    }
    function search(options={}){
      keys(options,['query','position','limit']);
      const query=options.query??'',position=options.position??null,limit=options.limit??20;
      if(typeof query!=='string'||query.length>100||position!==null&&!POSITIONS.includes(position)||
        !Number.isInteger(limit)||limit<1||limit>200)fail('INPUT_INVALID');
      const q=normalize(query),items=[];
      for(const hero of heroes.values()){
        const entry=profileFor(hero.id),roles=object(entry)&&POSITIONS.includes(entry.role)?[entry.role]:[];
        if(position&&!roles.includes(position)||query.trim()&&!q)continue;
        const rank=!q?3:hero.terms.includes(q)?0:hero.terms.some(t=>t.startsWith(q))?1:hero.terms.some(t=>t.includes(q))?2:4;
        if(rank===4)continue;
        items.push({id:hero.id,name:hero.name,aliases:clone(hero.aliases),portrait:hero.portrait?clone(hero.portrait):null,
          authored_positions:roles,selectable_positions:[...POSITIONS],
          baseline_status:!bundleValid||own(profiles.champions,hero.id)&&!roles.length?'SOURCE_REVIEW_REQUIRED':roles.length?getBaseline({champion:hero.id,position:roles[0]}).status:'NO_PROFILE',
          match:['EXACT','PREFIX','CONTAINS','ALL'][rank],rank});
      }
      items.sort((a,b)=>a.rank-b.rank||compare(a.name,b.name)||compare(a.id,b.id));
      return {schema_version:'gameplan-champion-search-v1',status:items.length?'RESULTS':'NO_RESULTS',
        query,position,source_patch:dataPatch,total:items.length,selection:null,
        items:items.slice(0,limit).map(({rank,...row})=>row)};
    }
    function prepareHandoff(raw,draft=null){
      keys(raw,['champion','position']);const selected=selection(raw);
      if(!selected.position)fail('INPUT_INVALID');
      const intent={own_champion:selected.champion,own_position:selected.position};
      const conflicts=[];
      if(draft!==null){
        if(!object(draft)||!['allies','enemies'].every(team=>Array.isArray(draft[team])&&draft[team].length<=5))fail('DRAFT_INVALID');
        const allSeen=new Set();
        for(const team of ['allies','enemies']){
          const roles=new Set();
          draft[team].forEach((row,index)=>{
            if(!object(row)||row.position!=null&&row.position!==''&&!POSITIONS.includes(row.position))fail('DRAFT_INVALID');
            let champion=null;
            if(row.champion!=null&&row.champion!==''){
              try{champion=resolve(row.champion);}catch(_){fail('DRAFT_INVALID');}
            }
            if(champion&&allSeen.has(champion)||row.position&&roles.has(row.position)){
              conflicts.push({code:'EXISTING_DRAFT_CONFLICT',team,index});
            }
            if(champion)allSeen.add(champion);if(row.position)roles.add(row.position);
            if(champion===selected.champion){
              if(team==='enemies')conflicts.push({code:'CHAMPION_ON_ENEMY_TEAM',team,index});
              else if(!row.position)conflicts.push({code:'POSITION_UNCONFIRMED',team,index});
              else if(row.position!==selected.position)conflicts.push({code:'CHAMPION_IN_OTHER_SLOT',team,index});
            }
            if(team==='allies'&&row.position===selected.position&&champion&&champion!==selected.champion)
              conflicts.push({code:'SLOT_OCCUPIED',team,index,previous_champion:champion});
          });
        }
        if(!draft.allies.some(row=>row.position===selected.position)&&draft.allies.some(row=>row.champion&&!row.position))
          conflicts.push({code:'POSITION_UNCONFIRMED',team:'allies',index:null});
      }
      return {schema_version:'gameplan-handoff-intent-v1',status:conflicts.some(c=>['CHAMPION_ON_ENEMY_TEAM','EXISTING_DRAFT_CONFLICT'].includes(c.code))?
        'BLOCKED':conflicts.length?'CONFIRMATION_REQUIRED':'READY',intent,conflicts,draft:draft===null?null:clone(draft),
        apply_automatically:false,composition_ready:false};
    }
    return Object.freeze({search,getBaseline,prepareHandoff});
  }
  return Object.freeze({createService,VERSION});
});

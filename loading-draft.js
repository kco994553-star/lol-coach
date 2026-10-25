/* Partial input storage and explicit champion handoff. Never analyzes or invents picks. */
(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory(require('./loading-coach.js'));else root.LoadingDraft=factory(root.LoadingCoach);})(typeof globalThis!=='undefined'?globalThis:this,function(Coach){
  'use strict';
  const SESSION_KEY='lol-coach-gameplan-draft-v1', ROLES=['TOP','JUNGLE','MID','BOTTOM','SUPPORT'];
  const inputKeys=['schema_version','allies','enemies','own_champion','own_position','side','patch','opponent_mode','lane_opponent','preferences','scenario','planning'];
  const fail=code=>{throw Error(code);};
  const object=x=>x!==null&&typeof x==='object'&&!Array.isArray(x)&&[Object.prototype,null].includes(Object.getPrototypeOf(x));
  function safe(value,depth=0){
    if(depth>18)fail('INPUT_INVALID');
    if(value===null||typeof value==='string'||typeof value==='boolean'||typeof value==='number'&&Number.isFinite(value))return;
    if(Array.isArray(value)){if(value.length>300)fail('INPUT_INVALID');value.forEach(v=>safe(v,depth+1));return;}
    if(!object(value))fail('INPUT_INVALID');
    for(const key of Object.keys(value)){if(['__proto__','prototype','constructor'].includes(key))fail('INPUT_INVALID');safe(value[key],depth+1);}
  }
  function copy(x){safe(x);const text=JSON.stringify(x);if(text.length>18000)fail('INPUT_TOO_LONG');return JSON.parse(text);}
  function freeze(x){if(x&&typeof x==='object'){Object.values(x).forEach(freeze);Object.freeze(x);}return x;}
  function keys(x,allowed){if(!object(x)||Object.keys(x).some(k=>!allowed.includes(k)))fail('INPUT_INVALID');safe(x);}
  function champion(x,nullable=false){if(nullable&&(x===null||x===undefined||x===''))return null;if(typeof x!=='string'||!/^[A-Za-z][A-Za-z0-9]{0,59}$/.test(x)||['constructor','prototype'].includes(x))fail('CHAMPION_INVALID');return x;}
  function role(x,nullable=false){if(nullable&&(x==null||x===''))return null;if(!ROLES.includes(x))fail('POSITION_INVALID');return x;}
  function createIntent(raw){
    keys(raw,['champion','position','opponent','opponent_position','ally_support','enemy_support','reference','return_state']);
    const out={champion:champion(raw.champion),position:role(raw.position)};
    for(const key of ['opponent','ally_support','enemy_support'])if(raw[key]!=null&&raw[key]!=='')out[key]=champion(raw[key]);
    if(raw.opponent_position!=null){if(!out.opponent)fail('OPPONENT_REQUIRED');out.opponent_position=role(raw.opponent_position);}
    if(out.opponent&&!out.opponent_position)fail('OPPONENT_POSITION_REQUIRED');
    if(raw.reference!=null){if(typeof raw.reference!=='string'||raw.reference.length>300)fail('REFERENCE_INVALID');out.reference=raw.reference;}
    if(raw.return_state!=null){
      if(!object(raw.return_state))fail('RETURN_STATE_INVALID');
      keys(raw.return_state,['detail_scroll','section','target','query','filter','scroll','champion','position','opponent','opponent_position','ally_support','enemy_support']);
      const state=copy(raw.return_state);
      if(state.detail_scroll!=null&&(!Number.isFinite(state.detail_scroll)||state.detail_scroll<0||state.detail_scroll>100000))fail('RETURN_STATE_INVALID');
      if(state.section!=null&&!['overview','power','baseline','skills','matchup'].includes(state.section))fail('RETURN_STATE_INVALID');
      if(state.query!=null&&(typeof state.query!=='string'||state.query.length>100))fail('RETURN_STATE_INVALID');
      if(state.scroll!=null&&(!Number.isFinite(state.scroll)||state.scroll<0||state.scroll>100000))fail('RETURN_STATE_INVALID');
      if(state.filter!=null&&!['ALL','UNCLASSIFIED',...ROLES].includes(state.filter))fail('RETURN_STATE_INVALID');
      for(const key of ['champion','opponent','ally_support','enemy_support'])if(state[key]!=null)champion(state[key],true);
      for(const key of ['position','opponent_position'])if(state[key]!=null)role(state[key],true);
      if(state.target!=null&&!['champions.html','champion.html','./champions.html','./champion.html'].includes(state.target))fail('RETURN_TARGET_INVALID');
      out.return_state=state;
    }
    const selected=[out.champion,out.opponent,out.ally_support,out.enemy_support].filter(Boolean);
    if(new Set(selected).size!==selected.length)fail('DUPLICATE_CHAMPION');
    return freeze(copy(out));
  }
  function fromInput(raw={},revision=0){
    keys(raw,inputKeys);if(!Number.isSafeInteger(revision)||revision<0)fail('REVISION_INVALID');
    const input=copy(raw);
    for(const team of ['allies','enemies']){
      if(input[team]!=null&&(!Array.isArray(input[team])||input[team].length>5))fail('DRAFT_INVALID');
      input[team]=Array.from({length:5},(_,i)=>{const pick=(input[team]||[])[i];if(pick==null)return {champion:null,position:null};keys(pick,['champion','position']);return {champion:champion(pick.champion,true),position:role(pick.position,true)};});
    }
    input.own_champion=champion(input.own_champion,true);input.own_position=role(input.own_position,true);
    input.side=input.side||'BLUE';if(!['BLUE','RED'].includes(input.side))fail('SIDE_INVALID');
    input.patch=input.patch||null;if(input.patch!==null&&(typeof input.patch!=='string'||!/^\d{1,3}\.\d{1,3}(?:\.\d{1,3})?$/.test(input.patch)))fail('PATCH_INVALID');
    input.opponent_mode=input.opponent_mode||'ASSIGNED';if(!['ASSIGNED','UNKNOWN','MANUAL'].includes(input.opponent_mode))fail('OPPONENT_MODE_INVALID');
    input.lane_opponent=champion(input.lane_opponent,true);
    input.preferences=input.preferences||{risk:'BALANCED'};keys(input.preferences,['risk']);if(!['LOSS_LIMIT','BALANCED','OPPORTUNITY'].includes(input.preferences.risk))fail('PREFERENCE_INVALID');
    input.schema_version=input.schema_version||(input.planning?'lol-coach-loading-input-v4':input.scenario?'lol-coach-loading-input-v3':'lol-coach-loading-input-v2');
    if(!['lol-coach-loading-input-v2','lol-coach-loading-input-v3','lol-coach-loading-input-v4'].includes(input.schema_version))fail('SCHEMA_INVALID');
    const v3=input.schema_version==='lol-coach-loading-input-v3',v4=input.schema_version==='lol-coach-loading-input-v4';
    if((v3||v4)!==Object.hasOwn(input,'scenario')||v4!==Object.hasOwn(input,'planning'))fail('SCHEMA_INVALID');
    if(v3||v4){if(!Coach)fail('SCENARIO_VALIDATOR_UNAVAILABLE');input.scenario=Coach.validateScenario(input.scenario);}
    if(v4)input.planning=Coach.validatePlanning(input.planning);
    return freeze({schema_version:'lol-coach-gameplan-draft-v1',revision,input});
  }
  function draft(value){if(value&&value.schema_version==='lol-coach-gameplan-draft-v1'){keys(value,['schema_version','revision','input']);return fromInput(value.input,value.revision);}return fromInput(value||{});}
  function slot(target){if(typeof target!=='string'||!/^(allies|enemies):[0-4]$/.test(target))fail('TARGET_INVALID');const [team,index]=target.split(':');return {team,index:Number(index)};}
  function issues(input){
    const found=[],seen=new Set();
    for(const team of ['allies','enemies']){const roles=new Set();for(const [index,pick] of input[team].entries()){
      if(pick.champion){if(seen.has(pick.champion))found.push({code:'DUPLICATE_CHAMPION',target:team+':'+index});seen.add(pick.champion);}
      if(pick.position){if(roles.has(pick.position))found.push({code:'DUPLICATE_POSITION',target:team+':'+index});roles.add(pick.position);}
    }}return found;
  }
  function previewTransfer(raw,value){
    const intent=createIntent(raw),current=draft(value),input=current.input;
    const wants=[['own','allies',intent.champion,intent.position],['opponent','enemies',intent.opponent,intent.opponent_position],['ally_support','allies',intent.ally_support,'SUPPORT'],['enemy_support','enemies',intent.enemy_support,'SUPPORT']].filter(x=>x[2]);
    const conflicts=issues(input),changes=wants.map(([key,team,id,position])=>{
      const exact=input[team].map((row,i)=>({row,i})).filter(x=>x.row.position===position);
      const existing=input[team].map((row,i)=>({row,i})).find(x=>x.row.champion===id);
      // An unconfirmed role always needs a visible slot choice, including a new empty draft.
      const chosen=exact.length===1?exact[0]:existing&&existing.row.position===position?existing:null;
      const target=chosen?team+':'+chosen.i:null;
      for(const other of ['allies','enemies'])for(const [i,row] of input[other].entries())if(row.champion===id&&(other!==team||target&&target!==other+':'+i))conflicts.push({code:'DUPLICATE_CHAMPION',target:other+':'+i});
      return {key,team,target,candidates:input[team].map((row,i)=>({target:team+':'+i,previous:row})).filter(x=>!x.previous.position||x.previous.position===position),previous:chosen?chosen.row:null,next:{champion:id,position}};
    });
    return freeze({schema_version:'lol-coach-transfer-preview-v1',intent,draft:current,revision:current.revision,changes,conflicts,status:conflicts.length?'BLOCKED':changes.some(c=>!c.target||c.previous.champion&&c.previous.champion!==c.next.champion)?'CONFIRMATION_REQUIRED':'READY'});
  }
  function applyTransfer(preview,choices={},expectedRevision){
    if(!preview||preview.schema_version!=='lol-coach-transfer-preview-v1')fail('PREVIEW_INVALID');
    const p=previewTransfer(preview.intent,preview.draft);
    if(expectedRevision!==p.revision)fail('STALE_REVISION');
    if(p.conflicts.length)fail(p.conflicts[0].code);
    keys(choices,['replacements','targets']);const targets=choices.targets||{};keys(targets,p.changes.map(c=>c.key));
    const replacements=choices.replacements||[];if(!Array.isArray(replacements)||replacements.some(x=>typeof x!=='string'))fail('REPLACEMENTS_INVALID');
    const input=copy(p.draft.input),used=new Set();
    for(const c of p.changes){
      const target=targets[c.key]||c.target;if(!target)fail('TARGET_REQUIRED');
      const {team,index}=slot(target);if(team!==c.team||c.target&&target!==c.target||!c.candidates.some(x=>x.target===target))fail('TARGET_INVALID');
      if(used.has(target))fail('DUPLICATE_TARGET');used.add(target);
      const previous=input[team][index];if(previous.champion&&previous.champion!==c.next.champion&&!replacements.includes(target))fail('REPLACEMENT_REQUIRED');
      input[team][index]=copy(c.next);
    }
    const conflicts=issues(input);if(conflicts.length)fail(conflicts[0].code);
    input.own_champion=p.intent.champion;input.own_position=p.intent.position;
    return fromInput(input,p.revision+1);
  }
  function toCompleteInput(value){const d=draft(value),i=d.input;if([...i.allies,...i.enemies].some(p=>!p.champion)||!i.own_champion||!i.own_position)return null;const errors=issues(i);if(errors.length)fail(errors[0].code);return copy(i);}
  function encode(prefix,value){return prefix+encodeURIComponent(JSON.stringify(value));}
  function decode(hash,prefix){if(typeof hash!=='string'||!hash.startsWith(prefix)||hash.length>60000)fail('ROUTE_INVALID');try{return JSON.parse(decodeURIComponent(hash.slice(prefix.length)));}catch(_){fail('ROUTE_INVALID');}}
  const encodeIntent=intent=>encode('#handoff=',createIntent(intent));
  const decodeIntent=hash=>createIntent(decode(hash,'#handoff='));
  const encodeDraft=value=>encode('#draft=',draft(value));
  function decodeDraft(hash){const value=decode(hash,'#draft=');if(!object(value)||value.schema_version!=='lol-coach-gameplan-draft-v1')fail('ROUTE_INVALID');return draft(value);}
  function saveDraft(storage,value){try{storage.setItem(SESSION_KEY,encodeDraft(value));return {ok:true};}catch(_){return {ok:false,error:'STORAGE_UNAVAILABLE'};}}
  function loadDraft(storage){try{const value=storage.getItem(SESSION_KEY);return value?decodeDraft(value):null;}catch(_){return null;}}
  function returnLink(raw){const intent=createIntent(raw),state=intent.return_state;if(!state)return null;const target=state.target||'champion.html';return './'+target.replace(/^\.\//,'')+'#state='+encodeURIComponent(JSON.stringify(state));}
  return Object.freeze({SESSION_KEY,createIntent,fromInput,previewTransfer,applyTransfer,toCompleteInput,encodeIntent,decodeIntent,encodeDraft,decodeDraft,saveDraft,loadDraft,returnLink});
});

/* Read-only learning index. Tactical prose remains in the shared claim registry. */
(function(root,factory){'use strict';const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.LearningRoom=api;})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 const ROLES=['TOP','JUNGLE','MID','BOTTOM','SUPPORT'];
 const KEYS=['q','group','topic','leaf','champion','role','opponent','evidence','patch','patch_state','situation','claim','lesson','return','invalid'];
 const REF_FIELDS=['text','display_text','conditions','counterexamples','patch_limits','extension','alternative_or_recovery'];
 const FIELDS=['phase','goal','threat','action','reason','required_conditions','stop_or_switch','waiting_cost','alternative_or_recovery'];
 const HOSTS=['youtube.com','www.youtube.com','youtu.be','www.mobafire.com','mobafire.com','dignitas.gg','www.reddit.com','reddit.com','docs.google.com','ddragon.leagueoflegends.com','www.leagueoflegends.com','leagueoflegends.com'];
 const array=v=>Array.isArray(v)?v:[];
 const id=v=>typeof v==='string'&&/^[A-Za-z0-9][A-Za-z0-9:_.-]{0,99}$/.test(v)?v:'';
 const text=v=>typeof v==='string'?v.replace(/[\u0000-\u001f\u007f]/g,'').trim().slice(0,100):'';
 const norm=v=>String(v||'').normalize('NFKC').toLocaleLowerCase().replace(/ß/g,'ss').replace(/ς/g,'σ').trim();
 function taxonomy(data){return array(data?.taxonomy?.groups).flatMap(g=>array(g.topics).flatMap(t=>array(t.leaves).map(l=>({...l,group_id:g.id,group_label:g.label,topic_id:t.id,topic_label:t.label}))));}
 function claimMap(knowledge){const map=new Map();for(const m of array(knowledge?.matchups))for(const c of array(m.claims))map.set(c.id,c);return map;}
 function resolveRef(ref,knowledge){if(!ref||typeof ref!=='object'||!REF_FIELDS.includes(ref.field))return null;const claim=claimMap(knowledge).get(ref.claim_id);if(!claim||!Object.hasOwn(claim,ref.field))return null;const value=claim[ref.field];return typeof value==='string'||Array.isArray(value)&&value.every(x=>typeof x==='string')?value:null;}
 function clean(input,data,knowledge){
  const s=Object.fromEntries(KEYS.map(k=>[k,'']));
  for(const k of KEYS){if(['q','situation','patch'].includes(k))s[k]=text(input[k]);else if(k==='return')s[k]=typeof input[k]==='string'&&/^[a-f0-9]{32}$/.test(input[k])?input[k]:'';else s[k]=id(input[k]);}
  s.invalid=input.invalid?'context':'';
  const supplied=key=>input[key]!==undefined&&input[key]!==null&&input[key]!=='';
  s.role=s.role.toUpperCase();if(!ROLES.includes(s.role))s.role='';
  for(const key of ['champion','opponent'])if(!/^[A-Za-z][A-Za-z0-9]{0,29}$/.test(s[key]))s[key]='';
  for(const key of ['group','topic','leaf','champion','role','opponent','evidence','patch','patch_state','situation','claim','lesson'])if(supplied(key)&&!s[key])s.invalid='context';
  if(data){
   const groups=array(data.taxonomy?.groups),leaves=taxonomy(data);
   if(s.topic){const parent=groups.find(g=>array(g.topics).some(t=>t.id===s.topic));if(parent)s.group=parent.id;}
   if(s.leaf&&s.leaf!=='UNCLASSIFIED'){const leaf=leaves.find(l=>l.id===s.leaf);if(leaf){s.topic=leaf.topic_id;s.group=leaf.group_id;}}
   if(!array(data.lessons).some(l=>l.lesson_id===s.lesson))s.lesson='';
   const champs=[...new Set([...array(data.champion_ids),...array(data.lessons).flatMap(l=>[...array(l.champions),...array(l.opponents)])])];
   for(const key of ['champion','opponent'])s[key]=champs.find(c=>norm(c)===norm(s[key]))||s[key];
   for(const [key,values] of [['evidence',array(data.lessons).map(l=>l.evidence_state)],['patch_state',array(data.lessons).map(l=>l.patch_state)],['patch',array(data.lessons).flatMap(l=>array(l.source_patches))],['situation',array(data.lessons).flatMap(l=>array(l.situation_tags))]])s[key]=values.find(v=>norm(v)===norm(s[key]))||s[key];
  }
  if(knowledge)s.claim=[...claimMap(knowledge).keys()].find(c=>norm(c)===norm(s.claim))||'';
  for(const key of ['group','topic','leaf','champion','role','opponent','evidence','patch','patch_state','situation','claim','lesson'])if(supplied(key)&&!s[key])s.invalid='context';
  return s;
 }
 function stateFromURL(search,data,knowledge){let params;try{params=new URLSearchParams(String(search||'').slice(0,10000).replace(/^(?:\?|#learn=)/,''));}catch(_){params=new URLSearchParams();}return clean(Object.fromEntries(KEYS.map(k=>[k,params.get(k)||''])),data,knowledge);}
 function stateToSearch(state){const s=clean(state||{}),p=new URLSearchParams();for(const key of KEYS)if(s[key])p.set(key,s[key]);return p.size?'?'+p.toString():'';}
 function filterLessons(data,knowledge,state){const s=clean(state||{},data,knowledge);if(s.invalid)return [];const leaves=taxonomy(data),claims=claimMap(knowledge);return array(data?.lessons).filter(l=>{
  const related=[l.primary_topic_id,...array(l.secondary_topic_ids)],leaf=leaves.find(t=>t.id===l.primary_topic_id);
  if(s.group&&!related.some(t=>leaves.some(x=>x.id===t&&x.group_id===s.group)))return false;
  if(s.topic&&!related.some(t=>leaves.some(x=>x.id===t&&x.topic_id===s.topic)))return false;
  if(s.leaf&&(s.leaf==='UNCLASSIFIED'?!!leaf:!related.includes(s.leaf)))return false;
  for(const [k,list] of [['champion','champions'],['role','roles'],['opponent','opponents'],['situation','situation_tags'],['claim','claim_ids']])if(s[k]&&!array(l[list]).some(value=>norm(value)===norm(s[k])))return false;
  if(s.evidence&&norm(l.evidence_state)!==norm(s.evidence))return false;if(s.patch_state&&norm(l.patch_state)!==norm(s.patch_state))return false;if(s.patch&&!array(l.source_patches).some(p=>norm(p)===norm(s.patch)))return false;
  if(s.q){const topics=leaves.filter(t=>related.includes(t.id));const corpus=[l.title,l.lesson_id,...array(l.claim_ids),l.question,...array(l.champions),...array(l.roles),...array(l.opponents),...array(l.situation_tags),...topics.flatMap(t=>[t.label,t.topic_label,t.group_label]),...[...FIELDS,'patch_limits'].map(f=>resolveRef(l[f],knowledge)),...array(l.claim_ids).flatMap(c=>{const claim=claims.get(c);return claim?[claim.text,claim.display_text,...array(claim.conditions),...array(claim.counterexamples)]:[];})].flat(Infinity).join(' ');if(!norm(s.q).split(/\s+/).every(term=>norm(corpus).includes(term)))return false;}return true;
 });}
 function safeSourceURL(value){if(typeof value!=='string'||value.length>2048||/[\u0000-\u0020\\]/.test(value))return null;try{const u=new URL(value);if(u.protocol!=='https:'||u.username||u.password||u.port||!HOSTS.includes(u.hostname))return null;return u.href;}catch(_){return null;}}
 function segmentURL(video,segment){const url=safeSourceURL(video?.canonical_url||video?.url),start=segment?.video_start_ms,end=segment?.video_end_ms,clock=segment?.game_clock_ms;
  if(!url||segment?.timestamp_state!=='VALIDATED'||segment.access_state!=='PERMITTED'||segment.license_or_access_state!=='PERMITTED'||!Number.isSafeInteger(start)||start<0||!Number.isSafeInteger(end)||end<=start||clock!=null&&(!Number.isSafeInteger(clock)||clock<0))return null;
  if(!/^[A-Za-z0-9_-]{11}$/.test(video?.video_id||'')||segment.video_id!==video.video_id||!/^[a-f0-9]{64}$/i.test(segment.source_hash||'')||!['TRANSCRIPT','VISUAL','AI_INTERPRETATION'].includes(segment.evidence_kind))return null;
  if(segment.evidence_kind==='VISUAL'&&segment.scene_verified!==true)return null;if(segment.evidence_kind==='TRANSCRIPT'&&(!array(segment.transcript_cue_ids).length||!segment.transcript_cue_ids.every(v=>typeof v==='string'&&v.length>0)))return null;
  const u=new URL(url);if(u.hostname!=='www.youtube.com'||u.pathname!=='/watch'||u.searchParams.get('v')!==video.video_id)return null;u.searchParams.delete('start');u.searchParams.set('t',String(Math.floor(start/1000))+'s');return u.href;
 }
 function safeReturn(url){return typeof url==='string'&&url.length<=32768&&!/[\u0000-\u0020\\]/.test(url)&&/^(?:\.\/|\/(?:lol-coach\/)?)?(?:loading(?:\.html)?|champion\.html|champions\.html|index\.html|directions(?:\.html)?|review\.html|dashboard\.html)(?:[?#]|$)/.test(url)?url:null;}
 function storeReturn(url,storage){if(!safeReturn(url)||!storage)return null;try{const bytes=new Uint8Array(16);if(!globalThis.crypto?.getRandomValues)return null;globalThis.crypto.getRandomValues(bytes);const token=Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');storage.setItem('lol-coach-learning-return:'+token,JSON.stringify({url,expires:Date.now()+8*60*60*1000}));return token;}catch(_){return null;}}
 function restoreReturn(token,storage){if(!/^[a-f0-9]{32}$/.test(token||'')||!storage)return null;try{const item=JSON.parse(storage.getItem('lol-coach-learning-return:'+token)||'null');return item&&item.expires>Date.now()?safeReturn(item.url):null;}catch(_){return null;}}
 function createLearningURL(context,options){const s=clean(context||{}),opts=options||{};const token=storeReturn(opts.returnURL,opts.storage);if(token)s.return=token;const query=stateToSearch(s);return './learning.html'+(query?'#learn='+query.slice(1):'');}
 return Object.freeze({ROLES,KEYS,FIELDS,taxonomy,claimMap,resolveRef,stateFromURL,stateToSearch,filterLessons,safeSourceURL,segmentURL,storeReturn,restoreReturn,createLearningURL});
});

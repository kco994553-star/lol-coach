/* Reproducible actual-engine evidence. Never edits or substitutes engine prose. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),cp=require('node:child_process');
const ROOT=path.resolve(__dirname,'..'),WEB=path.join(ROOT,'web_r4');
const ROLES=['TOP','JUNGLE','MID','BOTTOM','SUPPORT'],DEFAULT_SEED=20261025;
const clone=value=>JSON.parse(JSON.stringify(value));
const sha256=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
function catalog(){
  const c=JSON.parse(fs.readFileSync(path.join(WEB,'loading-data.json')));
  c.coaching_knowledge=JSON.parse(fs.readFileSync(path.join(WEB,'loading-knowledge.json')));
  return c;
}
// xorshift32, Fisher-Yates; sorted catalog IDs make selection independent of object order.
function random(seed){let state=seed>>>0;if(!state)throw Error('SEED_MUST_BE_NONZERO_UINT32');return ()=>{state^=state<<13;state^=state>>>17;state^=state<<5;return (state>>>0)/4294967296;};}
function shuffle(values,next){const result=[...values];for(let i=result.length-1;i>0;i--){const j=Math.floor(next()*(i+1));[result[i],result[j]]=[result[j],result[i]];}return result;}
function tankFacts(hero){return hero.facts.filter(f=>/둔화|속박|기절|공중으로 띄/.test(f.text));}
function selectInputs(c,seed=DEFAULT_SEED){
  const S=require(path.join(WEB,'loading-situation.js'));
  const next=random(seed),ids=Object.keys(c.champions).sort();
  const tanks=ids.filter(id=>c.champions[id].official_tags.includes('Tank')&&tankFacts(c.champions[id]).length);
  if(!tanks.length)throw Error('NO_OFFICIAL_TANK_WITH_CONTROL_FACT');
  return ROLES.map((role,index)=>{
    let roster=shuffle(ids,next).slice(0,10),basis={kind:'SEEDED_CATALOG_DRAW',role_assignment:'Synthetic positions, not an assertion of champion suitability'};
    if(index===0){
      const tank=tanks[Math.floor(next()*tanks.length)];roster=[tank,...shuffle(ids.filter(id=>id!==tank),next).slice(0,9)];
      basis={kind:'OFFICIAL_TANK_TAG_AND_CONTROL_FACT',role_assignment:'Synthetic TOP assignment, not a matchup strength claim',official_tags:c.champions[tank].official_tags,mechanism_facts:tankFacts(c.champions[tank]).map(clone)};
    }
    const situation=S.defaultState();situation.fields.ally_followup={status:'assumed',value:'AVAILABLE',source:'user-scenario',observed_at:null};
    const input={schema_version:'lol-coach-loading-input-v5',allies:ROLES.map((position,i)=>({champion:roster[i],position})),enemies:ROLES.map((position,i)=>({champion:roster[i+5],position})),own_champion:roster[index],own_position:role,side:'BLUE',patch:c.source_patch,opponent_mode:'ASSIGNED',lane_opponent:null,preferences:{risk:'BALANCED'},scenario:{standard:'lane-standard-v1',overrides:{}},planning:{basis:'loading-plan-example-v1',overrides:{}},situation};
    return {id:String(index+1).padStart(2,'0')+'-'+role.toLowerCase(),selection_basis:basis,input};
  });
}
function pointer(key){return String(key).replace(/~/g,'~0').replace(/\//g,'~1');}
function differences(a,b,base=''){
  if(JSON.stringify(a)===JSON.stringify(b))return [];
  if(a===null||b===null||typeof a!=='object'||typeof b!=='object')return [base];
  return [...new Set([...Object.keys(a),...Object.keys(b)])].flatMap(key=>differences(a[key],b[key],base+'/'+pointer(key)));
}
function conditionPair(input){
  const changed=clone(input);changed.situation.fields.ally_followup.value='UNAVAILABLE';
  return {input:changed,changed_path:'/situation/fields/ally_followup/value',condition:'User-scenario ally followup assumption AVAILABLE → UNAVAILABLE; all other fields unchanged; no live observation'};
}
function strings(value,base=''){
  if(typeof value==='string')return [{path:base,text:value}];
  if(!value||typeof value!=='object')return [];
  return Object.entries(value).flatMap(([key,item])=>strings(item,base+'/'+pointer(key)));
}
function sourceBinding(root,files){
  const git=(...args)=>cp.execFileSync('git',['-C',root,...args],{encoding:'utf8',maxBuffer:32*1024*1024}).trim();
  const head=git('rev-parse','HEAD'),hashes=Object.fromEntries([...new Set(files)].sort().map(file=>[file,sha256(fs.readFileSync(path.join(root,file)))]));
  const tracked=new Set(git('ls-tree','-r','--name-only',head,'--',...Object.keys(hashes)).split('\n'));
  const changed=git('diff','--name-only',head,'--',...Object.keys(hashes)).split('\n').filter(Boolean);
  const untracked=Object.keys(hashes).filter(file=>!tracked.has(file));
  const exact=!changed.length&&!untracked.length;
  return {status:exact?'EXACT_COMMIT':'WORKTREE_SNAPSHOT',source_commit:exact?head:null,base_commit:head,changed_source_files:changed,untracked_source_files:untracked,sha256:hashes};
}
function sourceFiles(c,samples){
  const files=fs.readdirSync(WEB).filter(file=>/^(loading-|directions-).*\.(js|json)$/.test(file)).map(file=>'web_r4/'+file);
  files.push('scripts/export_gameplan_2plus3.js',`data/official_catalog/versions/${c.source_patch}/champion.ko_KR.json`);
  for(const sample of samples)for(const pick of [...sample.input.allies,...sample.input.enemies])for(const fact of c.champions[pick.champion].facts)if(fact.local_source)files.push(fact.local_source);
  return [...new Set(files)].sort();
}
function execute(input,c,E,P){
  const supplied=clone(input),report=E.analyze(clone(input),c),view=P.project(report,{currentOnly:true});
  return {input:supplied,report,view,screen:strings(view),support_limits:{coach_supported:report.coach.supported,coaching_scope:report.coach.planboard.coaching_scope??null,evidence_limits:report.evidence.limits,real_coaching_n:report.evidence.real_coaching_n,accuracy:report.evidence.accuracy,card_coverage:view.cards.map(card=>({id:card.id,coverage:card.coverage}))}};
}
function exportExamples({output,seed=DEFAULT_SEED,requireBound=false}={}){
  const c=catalog(),samples=selectInputs(c,seed),source=sourceBinding(ROOT,sourceFiles(c,samples));
  if(requireBound&&source.status!=='EXACT_COMMIT')throw Error('EXACT_SOURCE_COMMIT_REQUIRED: '+JSON.stringify({changed:source.changed_source_files,untracked:source.untracked_source_files}));
  const E=require(path.join(WEB,'loading-engine.js')),P=require(path.join(WEB,'loading-presentation.js'));
  const results=samples.map(sample=>{
    const pair=conditionPair(sample.input),inputChanges=differences(sample.input,pair.input);
    if(inputChanges.length!==1||inputChanges[0]!==pair.changed_path)throw Error('PAIR_MUST_CHANGE_EXACTLY_ONE_INPUT_LEAF');
    const baseline=execute(sample.input,c,E,P),changed=execute(pair.input,c,E,P);
    return {...sample,baseline,changed,comparison:{condition:pair.condition,changed_path:pair.changed_path,input_changes:inputChanges,view_changes:differences(baseline.view,changed.view),decision_changes:differences(baseline.report.coach.planboard,changed.report.coach.planboard)}};
  });
  // Refuse to bind a snapshot if another worker changed a runtime source mid-run.
  const after=sourceBinding(ROOT,sourceFiles(c,samples));
  if(JSON.stringify(source)!==JSON.stringify(after))throw Error('SOURCE_CHANGED_DURING_EXPORT');
  const dir=path.resolve(output||path.join(ROOT,'evidence/actual-evidence/gameplan-2plus3-20261025/examples'));
  fs.mkdirSync(dir,{recursive:true});
  const manifest={format:'gameplan-2plus3-actual-evidence-v1',seed,selection:{algorithm:'xorshift32/Fisher-Yates over sorted catalog IDs; 5 draws, one per fixed role; TOP draw constrained to official Tank tag plus retained control mechanic',quality_filter:false,redraw_after_analysis:false,role_suitability:'UNMEASURED_SYNTHETIC_ASSIGNMENTS'},source,patch:c.source_patch,real_coaching_n:0,real_coaching_effect:'UNMEASURED',evaluation_status:'INTERNAL_REVIEW_REQUIRED_NOT_LIVE_COACHING',cases:[]};
  for(const result of results){
    const file=result.id+'.json',bytes=JSON.stringify(result,null,2)+'\n';fs.writeFileSync(path.join(dir,file),bytes);
    manifest.cases.push({id:result.id,file,sha256:sha256(bytes),own_champion:result.input.own_champion,own_position:result.input.own_position,changed_path:result.comparison.changed_path});
    const lines=['# '+result.id,'',`Source status: ${source.status}; source commit: ${source.source_commit||'UNBOUND'}; base commit: ${source.base_commit}.`,'','The following JSON string values are extracted directly from P.project(E.analyze(input)). JSON escaping preserves original text. No prose has been corrected.',''];
    for(const variant of ['baseline','changed']){lines.push('## '+variant,'');for(const row of result[variant].screen)lines.push('### '+row.path,'','```json',JSON.stringify(row.text),'```','');}
    fs.writeFileSync(path.join(dir,result.id+'.md'),lines.join('\n')+'\n');
  }
  fs.writeFileSync(path.join(dir,'manifest.json'),JSON.stringify(manifest,null,2)+'\n');
  return manifest;
}
if(require.main===module){
  const args=process.argv.slice(2),options={};
  for(let i=0;i<args.length;i++){if(args[i]==='--output')options.output=args[++i];else if(args[i]==='--seed')options.seed=Number(args[++i]);else if(args[i]==='--require-bound')options.requireBound=true;else throw Error('UNKNOWN_ARGUMENT: '+args[i]);}
  if(options.seed!==undefined&&(!Number.isInteger(options.seed)||options.seed<=0||options.seed>0xffffffff))throw Error('SEED_MUST_BE_NONZERO_UINT32');
  const manifest=exportExamples(options);console.log(JSON.stringify({source_status:manifest.source.status,source_commit:manifest.source.source_commit,seed:manifest.seed,cases:manifest.cases.map(x=>({id:x.id,champion:x.own_champion}))},null,2));
}
module.exports={catalog,selectInputs,conditionPair,differences,strings,sourceBinding,exportExamples};

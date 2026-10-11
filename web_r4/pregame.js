'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const positions = ['TOP','JUNGLE','MID','BOTTOM','SUPPORT'];
  const roleNames = {TOP:'탑',JUNGLE:'정글',MID:'미드',BOTTOM:'원딜',SUPPORT:'서포터'};
  const labels = {KNOWN:'확인됨',UNKNOWN:'미확인',CONFLICTING:'근거 충돌',CURRENT:'현재 유효',EXPIRED:'만료된 이력',FAVORABLE:'유리',UNFAVORABLE:'불리',CONTESTED:'경합',REVIEWED:'사용자 검토됨',REJECTED:'거절됨',EXPLORATORY:'미검토 후보'};
  let token = sessionStorage.getItem('lol-coach-dev-token') || '';
  let authEpoch=0, navEpoch=0, editEpoch=0, listEpoch=0, knowledgeEpoch=0, fileEpoch=0;
  let connected=false, testMode=false, powerTiers=[], draftV2=false, current=null, baseline='', originalCapture=null, plan=null, planViewEpoch=0, previewedSpec='';
  let writeBusy=false, readBusy=false, planBusy=false, knowledgeBusy=false;
  let saveAttempt=null, planAttempt=null, selectedKnowledge=null;
  const json = value => JSON.stringify(value,null,2);
  const clone = value => JSON.parse(JSON.stringify(value));
  const fingerprint = value => JSON.stringify(value,(_key,v)=>v && typeof v==='object' && !Array.isArray(v)?Object.fromEntries(Object.keys(v).sort().map(k=>[k,v[k]])):v);
  const nullable = value => value.trim() || null;
  const node = (tag,text,className) => {const n=document.createElement(tag);if(text!==undefined)n.textContent=String(text);if(className)n.className=className;return n;};
  const context = () => ({auth:authEpoch,nav:navEpoch});
  const alive = mark => connected && mark.auth===authEpoch && mark.nav===navEpoch;
  const manual = reference => ({kind:'MANUAL',reference:reference || null,observed_at:null,verification:'UNVERIFIED'});
  const unknownSource = () => ({kind:'UNKNOWN',reference:null,observed_at:null,verification:'UNKNOWN'});
  function notice(text,bad=false){$('pg-notice').textContent=text;$('pg-notice').className=bad?'error':'';}
  function hidePlan(){planViewEpoch++;plan=null;$('pg-plan-panel').hidden=true;$('pg-cards').replaceChildren();$('pg-plan-json').textContent='';}
  function apiError(error,mark){if(mark && !alive(mark))return;if(error.status===401){logout();notice('토큰을 확인하고 다시 연결하세요.',true);return;}notice('처리하지 못했습니다: '+error.message,true);}
  async function api(path,method='GET',bodyString,key,legacy=false){
    const headers={Authorization:'Bearer '+token};
    if(bodyString!==undefined)headers['Content-Type']='application/json';
    if(key)headers['Idempotency-Key']=key;
    const response=await fetch((legacy?'/dev/v1':'/dev/v1/pregame')+path,{method,mode:'same-origin',headers,body:bodyString,cache:'no-store'});
    let data;try{data=await response.json();}catch(_){const e=new Error('응답을 확인할 수 없습니다');e.ambiguous=true;e.status=response.status;throw e;}
    if(!response.ok){const e=new Error(data.error_code||'REQUEST_FAILED');e.status=response.status;throw e;}return data;
  }
  function option(value,text){const n=node('option',text);n.value=value;return n;}
  function roleOptions(select){select.append(option('','미확인'));positions.forEach(p=>select.append(option(p,roleNames[p])));}
  function field(label,id,type='input',values){const l=node('label',label),n=node(type);n.id=id;if(type==='select'){values.forEach(v=>n.append(option(v[0],v[1])));}l.append(n);return l;}
  function sourceEditor(parent,prefix){
    const container=node('div',undefined,'provenance'),grid=node('div',undefined,'grid');
    grid.append(field('출처 종류',prefix+'-kind','select',[['UNKNOWN','미확인'],['MANUAL','수동 입력'],['AUTOMATIC','자동 자료']]),field('출처 참조',prefix+'-reference'),field('출처 관측 시각 · ISO + 시간대',prefix+'-observed-at'),field('검증 선언',prefix+'-verification','select',[['UNKNOWN','미확인'],['UNVERIFIED','미검증'],['SOURCE_VERIFIED','원본 출처 확인']]));
    container.append(grid);parent.append(container);
    const kind=grid.querySelector('select'),verification=grid.querySelectorAll('select')[1];
    kind.addEventListener('change',()=>{
      const verified=verification.querySelector('option[value="SOURCE_VERIFIED"]');
      verified.disabled=kind.value==='MANUAL';
      if(verified.disabled && verification.value==='SOURCE_VERIFIED')verification.value='UNVERIFIED';
    });
  }
  function readSource(prefix){return {kind:$(prefix+'-kind').value,reference:nullable($(prefix+'-reference').value),observed_at:nullable($(prefix+'-observed-at').value),verification:$(prefix+'-verification').value};}
  function putSource(prefix,s){$(prefix+'-kind').value=s.kind;$(prefix+'-reference').value=s.reference || '';$(prefix+'-observed-at').value=s.observed_at || '';$(prefix+'-verification').value=s.verification;$(prefix+'-verification').querySelector('option[value="SOURCE_VERIFIED"]').disabled=s.kind==='MANUAL';}
  function selectionEditor(parent,prefix,title){
    const d=node('details'),summary=node('summary',title+' · 완료 선언 및 출처');d.append(summary);
    const grid=node('div',undefined,'grid');grid.append(field('선택 상태',prefix+'-status','select',[['UNKNOWN','UNKNOWN · 미확인'],['PARTIAL','PARTIAL · 일부'],['FULL','FULL · 전체 선언']]),field('값 · 쉼표/줄바꿈 구분',prefix+'-values','textarea'));d.append(grid);
    sourceEditor(d,prefix+'-source');d.append(node('p','전체/일부 선언은 실제 게임 클라이언트 인증이 아닙니다. UNKNOWN은 값이 없어야 합니다.','small'));parent.append(d);
  }
  function readSelection(prefix){return {status:$(prefix+'-status').value,values:$(prefix+'-values').value.split(/[,\n]/).map(s=>s.trim()).filter(Boolean),source:readSource(prefix+'-source')};}
  function putSelection(prefix,s){$(prefix+'-status').value=s.status;$(prefix+'-values').value=s.values.join(', ');putSource(prefix+'-source',s.source);}
  function slotPrefix(side,slot){return 'pg-'+side.toLowerCase()+'-'+slot;}
  function buildForm(){
    roleOptions($('pg-my-position'));sourceEditor($('pg-input-source'),'pg-source');
    for(const side of ['ALLY','ENEMY'])for(let i=1;i<=5;i++){
      const prefix=slotPrefix(side,i),row=node('article',undefined,'pg-slot');row.id=prefix;row.append(node('h4',(side==='ALLY'?'아군 ':'적군 ')+i));
      const grid=node('div',undefined,'grid');const champ=field('챔피언 · 이름/ID',prefix+'-champion');champ.querySelector('input').setAttribute('list','pg-roster');champ.querySelector('input').maxLength=100;
      const role=field('확정 포지션',prefix+'-position','select',[]);roleOptions(role.querySelector('select'));
      grid.append(champ,role,field('불확실성·판단 근거',prefix+'-uncertainty'));row.append(grid);
      const candidateLabel=node('div'),checks=node('div',undefined,'candidate-checks');candidateLabel.append(node('p','미확정 포지션 후보 · 확정 포지션과 함께 지정할 수 없습니다.','small'));
      for(const p of positions){const l=node('label',roleNames[p]),c=node('input');c.type='checkbox';c.id=prefix+'-candidate-'+p;c.value=p;l.prepend(c);checks.append(l);}candidateLabel.append(checks);row.append(candidateLabel);
      const sources=node('details');sources.append(node('summary','챔피언·포지션 출처'));sources.append(node('h4','챔피언 출처'));sourceEditor(sources,prefix+'-champion-source');sources.append(node('h4','포지션 출처'));sourceEditor(sources,prefix+'-position-source');row.append(sources);
      selectionEditor(row,prefix+'-runes','룬');selectionEditor(row,prefix+'-summoners','소환사 주문');$('pg-'+side.toLowerCase()+'-slots').append(row);
    }
  }
  function emptyInput(){return {title:'경기 전 입력',patch:null,phase:'UNKNOWN',observed_at:null,my_position:null,my_champion:null,my_slot:null,slots:['ALLY','ENEMY'].flatMap(side=>[1,2,3,4,5].map(slot=>({side,slot,champion:null,position:null,position_candidates:[],uncertainty:'미확인',champion_source:unknownSource(),position_source:unknownSource(),runes:{status:'UNKNOWN',values:[],source:unknownSource()},summoners:{status:'UNKNOWN',values:[],source:unknownSource()}}))),source:unknownSource(),original_capture:null};}
  function readInput(){const input={title:$('pg-title').value.trim(),patch:nullable($('pg-patch').value),phase:$('pg-phase').value,observed_at:nullable($('pg-observed-at').value),my_position:$('pg-my-position').value || null,my_champion:nullable($('pg-my-champion').value),my_slot:$('pg-my-slot').value?Number($('pg-my-slot').value):null,
    slots:['ALLY','ENEMY'].flatMap(side=>[1,2,3,4,5].map(slot=>{const p=slotPrefix(side,slot);return {side,slot,champion:nullable($(p+'-champion').value),position:$(p+'-position').value || null,position_candidates:positions.filter(role=>$(p+'-candidate-'+role).checked),uncertainty:$(p+'-uncertainty').value,champion_source:readSource(p+'-champion-source'),position_source:readSource(p+'-position-source'),runes:readSelection(p+'-runes'),summoners:readSelection(p+'-summoners')};})),source:readSource('pg-source'),original_capture:originalCapture};
    const preferences=$('pg-frequent-champions').value.split(/[,\n]/).map(v=>v.trim()).filter(Boolean),pickState=$('pg-my-pick-state').value;
    if(draftV2 || pickState || preferences.length)Object.assign(input,{schema_version:'pregame.input-draft.v2',my_pick_state:pickState || 'UNKNOWN',frequent_champions:preferences});return input;}
  function putInput(input){
    draftV2=input.schema_version==='pregame.input-draft.v2';
    $('pg-my-pick-state').value=draftV2?input.my_pick_state:'';$('pg-frequent-champions').value=(input.frequent_champions || []).join(', ');
    originalCapture=input.original_capture===null?null:clone(input.original_capture);
    $('pg-phase').value=input.phase;$('pg-title').value=input.title;$('pg-patch').value=input.patch || '';$('pg-observed-at').value=input.observed_at || '';$('pg-my-position').value=input.my_position || '';$('pg-my-champion').value=input.my_champion || '';$('pg-my-slot').value=input.my_slot || '';putSource('pg-source',input.source);
    for(const s of input.slots){const p=slotPrefix(s.side,s.slot);$(p+'-champion').value=s.champion || '';$(p+'-position').value=s.position || '';$(p+'-uncertainty').value=s.uncertainty;for(const role of positions)$(p+'-candidate-'+role).checked=s.position_candidates.includes(role);putSource(p+'-champion-source',s.champion_source);putSource(p+'-position-source',s.position_source);putSelection(p+'-runes',s.runes);putSelection(p+'-summoners',s.summoners);}
    updateEditor();
  }
  function dirty(){return fingerprint(readInput())!==baseline;}
  function updateEditor(){
    const input=readInput();$('pg-input-json').textContent=json(input);
    $('pg-current').textContent=current?current.input.title+' · 저장 v'+current.revision+(dirty()?' · 미저장 수정 있음':''):'새 입력 · 아직 저장하지 않음';
    $('pg-create-plan').disabled=!connected || !current || dirty() || writeBusy || readBusy || planBusy || !!saveAttempt;
    $('pg-save').disabled=!connected || writeBusy || readBusy || !!saveAttempt;
    $('pg-retry-save').hidden=!saveAttempt;$('pg-retry-save').disabled=writeBusy || readBusy;
    knowledgeControls();
    $('pg-save-state').textContent=saveAttempt?'응답이 불확실합니다. 동일 키·본문으로 원래 저장 요청을 재시도한 뒤 현재 수정본을 추가 저장하세요.':dirty()?'수정본을 저장한 뒤 새 계획을 생성할 수 있습니다.':'현재 입력은 저장 버전과 같습니다.';
  }
  function validateInput(input){
    if(!input.title)throw new Error('제목을 입력하세요.');
    if(input.my_pick_state==='UNPICKED' && input.my_champion!==null)throw new Error('미선택 선언에는 내 챔피언을 비워 두세요.');
    if(input.my_pick_state==='PICKED' && input.my_champion===null)throw new Error('선택 완료 선언에는 내 챔피언이 필요합니다.');
    if(input.frequent_champions && new Set(input.frequent_champions).size!==input.frequent_champions.length)throw new Error('자주 하는 챔피언이 중복됩니다.');
    const checkSource=s=>{if(s.kind==='MANUAL'&&s.verification==='SOURCE_VERIFIED')throw new Error('수동 입력은 원본 검증으로 선언할 수 없습니다.');if(s.kind==='AUTOMATIC'&&!s.reference)throw new Error('자동 자료에는 출처 참조가 필요합니다.');if(s.observed_at&&!/([zZ]|[+-]\d{2}:\d{2})$/.test(s.observed_at))throw new Error('출처 시각에는 시간대가 필요합니다.');};
    checkSource(input.source);
    if(input.observed_at&&!/([zZ]|[+-]\d{2}:\d{2})$/.test(input.observed_at))throw new Error('입력 시각에는 시간대가 필요합니다.');
    for(const side of ['ALLY','ENEMY']){const seen=new Set();for(const s of input.slots.filter(s=>s.side===side)){if(s.position && s.position_candidates.length)throw new Error('확정 포지션과 포지션 후보를 함께 지정할 수 없습니다.');if(s.position&&seen.has(s.position))throw new Error('같은 팀의 확정 포지션이 중복됩니다.');seen.add(s.position);if(!s.uncertainty.trim())throw new Error('불확실성·판단 근거를 입력하세요.');checkSource(s.champion_source);checkSource(s.position_source);for(const selection of [s.runes,s.summoners]){checkSource(selection.source);if((selection.status==='UNKNOWN')!==!selection.values.length)throw new Error('룬·주문 UNKNOWN은 값 없이, FULL/PARTIAL은 값과 함께 지정하세요.');if(new Set(selection.values).size!==selection.values.length)throw new Error('룬·주문 값이 중복됩니다.');}}}
  }
  function replaceAllowed(){if(writeBusy || readBusy || planBusy){notice('진행 중인 요청이 끝난 뒤 다른 입력을 여세요.',true);return false;}if(saveAttempt && !confirm('응답을 확인하지 못한 저장 요청이 있습니다. 이 초안을 떠나면 동일 요청 재시도 정보를 잃습니다. 저장 이력을 다시 확인해야 합니다. 계속할까요?'))return false;return !dirty() || confirm('저장하지 않은 수정이 있습니다. 다른 입력으로 바꾸면 수정본이 사라집니다. 계속할까요?');}
  function resetNavigation(){navEpoch++;editEpoch++;fileEpoch++;knowledgeEpoch++;knowledgeBusy=false;selectedKnowledge=null;$('pg-knowledge-detail').hidden=true;current=null;saveAttempt=null;planAttempt=null;readBusy=false;planBusy=false;hidePlan();$('pg-history').replaceChildren();$('pg-plan-list').replaceChildren();}
  function newInput(input=emptyInput(),message='새 입력을 열었습니다.'){
    if(!replaceAllowed())return;resetNavigation();putInput(input);baseline=fingerprint(emptyInput());updateEditor();notice(message);
  }
  function golden(){
    const input=emptyInput(),teams=[['Ornn','Sejuani','Ahri','Caitlyn','Lux'],['Fiora','LeeSin','Zed','Ezreal','Nautilus']];
    input.phase='PRE_GAME';input.title='Golden10 · 수동 시연 입력';input.source=manual('Golden10 시연; 실제 클라이언트 미검증');
    for(const s of input.slots){s.champion=teams[s.side==='ALLY'?0:1][s.slot-1];s.position=positions[s.slot-1];s.uncertainty='수동 시연 지정; 실제 클라이언트 미검증';s.champion_source=manual('Golden10 테스트 입력');s.position_source=manual('Golden10 테스트 입력');s.runes.source=manual('선택 미확인');s.summoners.source=manual('선택 미확인');}
    input.my_position='BOTTOM';input.my_champion='Caitlyn';input.my_slot=4;
    newInput(input,'Golden10 시연 입력만 채웠습니다. 패치는 미확인이며 지식은 가져오거나 승인하지 않았습니다.');
  }
  async function refreshInputs(){const mark=context(),seq=++listEpoch;const rows=await api('/inputs');if(!alive(mark)||seq!==listEpoch)return;$('pg-input-list').replaceChildren();if(!rows.length)$('pg-input-list').append(node('p','저장한 입력이 없습니다.','small'));for(const r of rows){const b=node('button',r.title+' · v'+r.revision,current&&r.session_id===current.session_id?'active':'');b.addEventListener('click',()=>openInput(r.session_id).catch(e=>apiError(e,context())));$('pg-input-list').append(b);}}
  async function loadHistory(mark,sid){
    const results=await Promise.allSettled([api('/inputs/'+sid+'/history'),api('/inputs/'+sid+'/plan-history')]);if(!alive(mark)||!current||current.session_id!==sid)return;
    $('pg-history').replaceChildren();$('pg-plan-list').replaceChildren();
    if(results[0].status==='fulfilled')for(const record of results[0].value){const d=node('details');d.append(node('summary','입력 v'+record.revision+' · '+record.created_at),node('pre',json(record)));$('pg-history').append(d);}else $('pg-history').append(node('p','입력 이력 조회 실패: '+results[0].reason.message,'small'));
    if(results[1].status==='fulfilled')for(const p of results[1].value){const b=node('button','계획 · 입력 v'+p.input_revision+' · '+(labels[p.validity]||p.validity));b.addEventListener('click',()=>openPlan(p.id).catch(e=>apiError(e,context())));$('pg-plan-list').append(b);}else $('pg-plan-list').append(node('p','계획 이력 조회 실패: '+results[1].reason.message,'small'));
  }
  async function openInput(sid){
    if(!replaceAllowed())return;resetNavigation();const mark=context(),edit=editEpoch;readBusy=true;updateEditor();
    try{const record=await api('/inputs/'+sid);if(!alive(mark))return;if(edit!==editEpoch){notice('입력을 읽는 동안 만든 수정본을 보존했습니다. 다시 열거나 새 입력으로 저장하세요.');return;}current=record;putInput(record.input);baseline=fingerprint(readInput());updateEditor();await loadHistory(mark,sid);if(alive(mark))notice('저장한 현재 입력을 열었습니다.');}
    catch(e){apiError(e,mark);}finally{if(alive(mark)){readBusy=false;updateEditor();}}
  }
  async function importDraft(){
    const id=$('pg-draft-select').value;if(!id)throw new Error('기존 픽창 저장본을 선택하세요.');if(!replaceAllowed())return;resetNavigation();const mark=context(),edit=editEpoch;readBusy=true;updateEditor();
    try{const input=await api('/import-draft/'+id);if(!alive(mark)||edit!==editEpoch)return;putInput(input);baseline=fingerprint(emptyInput());notice('원본을 보존한 10슬롯 입력을 가져왔습니다. 내 포지션·챔피언·슬롯을 직접 지정한 뒤 저장하세요.');}
    catch(e){apiError(e,mark);}finally{if(alive(mark)){readBusy=false;updateEditor();}}
  }
  async function save(retry=false){
    if(writeBusy||readBusy)return;
    const mark=context();
    if(!retry){if(saveAttempt)return;const input=readInput();validateInput(input);saveAttempt={key:crypto.randomUUID(),method:current?'PUT':'POST',path:current?'/inputs/'+current.session_id:'/inputs',body:JSON.stringify(current?{input,expected_revision:current.revision}:{input}),editor:fingerprint(input)};}
    if(!saveAttempt)return;
    const op=saveAttempt;writeBusy=true;hidePlan();updateEditor();
    try{const record=await api(op.path,op.method,op.body,op.key);if(!alive(mark)||saveAttempt!==op)return;
      hidePlan();
      const editorNow=fingerprint(readInput());current=record;saveAttempt=null;planAttempt=null;baseline=fingerprint(record.input);
      if(editorNow===op.editor){putInput(record.input);baseline=fingerprint(readInput());}
      updateEditor();await refreshInputs();await loadHistory(mark,record.session_id);
      if(alive(mark))notice(dirty()?'요청한 입력은 저장됐습니다. 요청 이후의 수정본을 보존했으니 추가 저장하세요.':'입력을 저장했습니다. 이 버전으로 계획을 생성하세요.');
    }catch(e){if(!alive(mark))return;if(e.status && e.status<500 && !e.ambiguous){saveAttempt=null;if(e.status===409)notice('저장 버전이 바뀌었거나 요청 키가 충돌했습니다. 현재 수정본은 유지됩니다. 저장 목록에서 최신 버전과 비교하세요.',true);else apiError(e,mark);}else notice('저장 응답을 확인하지 못했습니다. 현재 수정본을 보존했습니다. 동일 저장 요청을 재시도하세요.',true);}
    finally{if(alive(mark)){writeBusy=false;updateEditor();}}
  }
  async function createPlan(){
    if(!current||dirty()||writeBusy||readBusy||planBusy||saveAttempt)throw new Error('수정 없는 저장 버전이 필요합니다.');
    const mark=context(),edit=editEpoch,sid=current.session_id,revision=current.revision;
    if(!planAttempt||planAttempt.sid!==sid||planAttempt.revision!==revision)planAttempt={sid,revision,key:crypto.randomUUID(),body:JSON.stringify({expected_revision:revision})};
    const op=planAttempt;planBusy=true;hidePlan();const view=planViewEpoch;updateEditor();
    try{const result=await api('/inputs/'+sid+'/plans','POST',op.body,op.key);if(!alive(mark)||edit!==editEpoch||view!==planViewEpoch||!current||current.session_id!==sid||current.revision!==revision)return;planAttempt=null;renderPlan(result);await loadHistory(mark,sid);if(alive(mark))notice('저장 버전의 경기 전 계획을 저장했습니다.');}
    catch(e){if(alive(mark)&&edit===editEpoch){if(e.status&&e.status<500&&!e.ambiguous)planAttempt=null;apiError(e,mark);}}
    finally{if(alive(mark)){planBusy=false;updateEditor();}}
  }
  async function openPlan(id){
    if(writeBusy||readBusy||planBusy||saveAttempt){notice('진행 중인 요청 또는 응답 미확인 저장이 있습니다. 저장·조회가 끝난 뒤 계획 이력을 확인하세요.',true);return;}
    if(dirty()){notice('수정본을 저장하거나 저장 입력을 다시 연 뒤 계획 이력을 확인하세요.',true);return;}
    const mark=context(),edit=editEpoch;hidePlan();const view=planViewEpoch,p=await api('/plans/'+id);if(!alive(mark)||edit!==editEpoch||view!==planViewEpoch)return;renderPlan(p);
  }
  function addSources(parent,sources){
    const list=node('ul',undefined,'sources');for(const s of sources || []){const item=node('li'),a=node('a',s.title || s.url);try{const u=new URL(s.url);if(u.protocol==='https:' && !u.username&&!u.password){a.href=u.href;a.target='_blank';a.rel='noopener noreferrer';}}catch(_){}item.append(a,node('span',' · '+(s.locator || '')+' · 패치 '+(s.patch || '미확인')+' · '+(s.kind || '')));if(s.sha256)item.append(node('div','원본 SHA256: '+s.sha256));list.append(item);}parent.append(list);
  }
  function cooldowns(parent,items){
    for(const item of items || []){const box=node('div',undefined,'cooldown');box.append(node('p',(item.name || '스킬')+' · '+(item.label || '미확인')));
      if(item.base_values && item.base_values.length)box.append(node('p','기준값: '+item.base_values.join(' / ')+'초','small'));
      if(item.conditional_values && item.conditional_values.length)box.append(node('p','계산/조건부: '+item.conditional_values.join(' / ')+'초','small'));
      if(item.linked_condition)box.append(node('p','연결 조건: '+item.linked_condition,'small'));
      for(const reason of item.reasons || [])box.append(node('p',reason,'small'));
      if(item.conditional?.source){box.append(node('p','계산/조건부 출처','small'));addSources(box,[item.conditional.source]);}
      for(const reason of item.conditional_reasons || [])box.append(node('p',reason,'small'));
      addSources(box,item.sources);parent.append(box);
    }
  }
  function cellContent(parent,cell,p){
    const currentPlan=p.validity==='CURRENT',usable=currentPlan && cell.status==='KNOWN';
    const names={ROLE:'내 역할',LANE:'라인·동선',FIGHT:'교전·생존',COMPOSITION:'조합',OPERATIONS:'운영·팀 의존',MOVEMENT:'이동 단계',CHANGES:'변화 조건'};
    const title=currentPlan?(roleNames[cell.key] || cell.title || cell.key):(roleNames[cell.key] || names[cell.key] || '보존된 카드');
    const head=node('div',undefined,'cell-head');head.append(node('h4',title),node('span',currentPlan?(labels[cell.status] || cell.status):'UNKNOWN · 만료된 이력','badge'));parent.append(head);
    if(usable){if(cell.outlook)parent.append(node('p',labels[cell.outlook] || cell.outlook,'outlook'));for(const text of cell.texts || [])parent.append(node('p',text));cooldowns(parent,cell.cooldowns);}
    else parent.append(node('p',currentPlan?'미확인 · 실행 내용은 보류합니다.':'만료된 이력 · 실행 내용과 수치는 보류합니다. 원본은 아래 이력에서 확인하세요.'));
    if(currentPlan){const reasons=node('ul');for(const reason of cell.reasons || [])reasons.append(node('li',reason));if(reasons.children.length)parent.append(reasons);}
    renderGuards(parent,cell,p);
  }
  const signalNames={ALLY_MINIMAP:'아군 미니맵',WAVE:'웨이브',SELF_HEALTH:'내 체력',SELF_RESOURCE:'내 자원',GAME_TIME:'게임 시간'};
  function usableGuard(p,cell,trace){return p.validity==='CURRENT' && cell.status==='KNOWN' && trace.status==='APPLIED' && trace.spec?.plan_guard;}
  function renderGuards(parent,cell,p){
    const traces=cell.rules || [],items=traces.length?traces:[null];
    for(const trace of items){const box=node('div',undefined,'pg-guard'),guard=trace && usableGuard(p,cell,trace);box.dataset.status=guard?'KNOWN':'UNKNOWN';
      if(!guard){box.append(node('p','실행 조건 UNKNOWN · 미확인','small'),node('p','전제조건 · 무효화 신호 · 대안: UNKNOWN','small'));}
      else{box.append(node('p','직접 확인할 실행 조건 · '+trace.rule_id,'small'));
        for(const [key,label] of [['preconditions','전제조건'],['invalidation_signals','무효화 신호']]){const list=node('ul');for(const signal of guard[key] || [])list.append(node('li',label+' · '+(signalNames[signal.field] || signal.field)+' · '+signal.text));box.append(list);}
        box.append(node('p','대안 · '+guard.alternative));
      }parent.append(box);
    }
  }
  function renderOperations(parent,p,cell){
    const dependency=p.team_dependencies;
    if(dependency){parent.append(node('p','팀 의존 정보 · '+(p.validity==='CURRENT'?(dependency.status || 'UNKNOWN'):'UNKNOWN'),'small'));
      if(p.validity==='CURRENT' && dependency.status==='KNOWN'){parent.append(node('p','시작 역할 의존 · '+(dependency.dependency_risk || 'UNKNOWN')+' · 시작 역할 수 '+(dependency.initiator_count ?? 'UNKNOWN'),'small'));
        for(const ally of dependency.allies || [])parent.append(node('p',(roleNames[ally.position] || ally.position)+' · '+ally.champion+' · '+((ally.initiative || []).join(', ') || 'UNKNOWN')+' · 필요 '+((ally.needs || []).join(', ') || 'UNKNOWN'),'small'));
      }
    }
    let shown=false;
    for(const trace of cell.rules || []){if(!usableGuard(p,cell,trace))continue;const ops=trace.spec?.output?.operations;if(!ops)continue;shown=true;
      for(const [key,title] of [['opening_allies','초반 함께 움직일 아군'],['pressure_allies','압박할 아군'],['win_condition_allies','승리 조건을 맡는 아군']])parent.append(node('p',title+' · '+((ops[key] || []).map(r=>roleNames[r] || r).join(', ') || 'UNKNOWN')));
      for(const d of ops.dependencies || [])parent.append(node('p','필요 행동 · '+(roleNames[d.position] || d.position)+' · '+d.required_play,'pg-dependency'));
      for(const m of ops.minimum_plays || []){const list=node('ul',undefined,'pg-minimum-plays');for(const play of m.plays || [])list.append(node('li',(roleNames[m.position] || m.position)+' · '+play));parent.append(list);}
      for(const text of ops.request_templates || [])parent.append(node('blockquote','요청 템플릿 · '+text,'pg-request-template'));
      parent.append(node('p','혼자 할 수 있는 대안 · '+ops.solo_alternative));
    }
    if(!shown)parent.append(node('p','운영 템플릿 UNKNOWN · 검토된 실행 조건과 연결 행동이 필요합니다.'));
    parent.append(node('p','요청은 검토된 원문을 표시합니다. 직접 확인하고 필요하면 직접 전달하세요.','small'));
    if(p.validity==='CURRENT' && p.input.my_pick_state==='UNPICKED')for(const warning of p.pick_warnings || []){
      if(warning.champion && !(p.input.frequent_champions || []).includes(warning.champion))continue;
      const item=node('div',undefined,'pg-pick-warning');item.append(node('p','검토된 선택 후보 · '+(warning.champion || '')+' · '+(warning.reason || warning.text || '')));const details=node('details');details.append(node('summary','선택 후보 승인 근거'),node('p','규칙 '+warning.rule_id+' · 버전 '+warning.version+' · 명세 SHA256 '+warning.spec_sha256,'small'));addSources(details,warning.sources);item.append(details);parent.append(item);
    }
  }
  function renderMovement(parent,p,cell){
    const locations={HOME_LANE:'내 기본 라인',JUNGLE:'정글',MAIN_GROUP:'본대',SIDE_LANE:'사이드 라인',OBJECTIVE_AREA:'오브젝트 주변'};
    const subjects={SELF:'나',ALLY:'아군',ENEMY:'적군'};
    const fields={LANING_ACTIVE:'라인전 진행',FIRST_TURRET_DESTROYED:'첫 포탑 파괴',MAJOR_OBJECTIVE_CONTEST:'주요 오브젝트 경합',LONG_RESPAWN_RISK:'긴 부활 시간 위험'};
    let shown=false;
    for(const trace of cell.rules || []){if(!usableGuard(p,cell,trace))continue;
      const rows=trace.output?.movement || trace.spec?.output?.movement || [];
      for(const row of rows){if(!row.statistics_ref?.dataset_sha256 || !row.statistics_ref?.cohort_id)continue;shown=true;
        const article=node('article',undefined,'pg-movement-row');article.dataset.stage=row.stage;
        article.append(node('h4',row.stage+' · '+row.layer+' · '+(subjects[row.subject] || row.subject)+' '+(roleNames[row.position] || row.position || '')));
        article.append(node('p','조건부 위치 · '+(locations[row.location] || row.location)),node('p','역할 · '+row.role),node('p','이유 · '+row.why));
        for(const condition of row.stage_conditions || [])article.append(node('p','구간 조건 · '+(fields[condition.field] || condition.field)+' · '+(condition.value?'참일 때':'거짓일 때'),'small'));
        for(const text of row.exceptions || [])article.append(node('p','예외 · '+text,'small'));
        const provenance=node('details');provenance.append(node('summary','이동 근거·통계 연결'),node('p','규칙 '+trace.rule_id+' · '+trace.version,'small'),node('p','통계 digest '+row.statistics_ref.dataset_sha256+' · cohort '+row.statistics_ref.cohort_id,'small'));
        if(row.overrides?.length)provenance.append(node('p','덮어쓰는 규칙 · '+row.overrides.join(', '),'small'));addSources(provenance,trace.spec?.sources || trace.sources);article.append(provenance);parent.append(article);
      }
    }
    if(!shown)parent.append(node('p','이동 단계 UNKNOWN · 검토된 근거와 검증된 위치 통계 연결이 필요합니다.'));
    parent.append(node('p','초반·중반·후반은 표시된 상황 조건으로 구분합니다. 현재 경기 상황을 감지하거나 분 단위로 확정하지 않습니다.','small'));
  }
  function phaseBands(p,position){
    const cell=p.movement;if(p.validity!=='CURRENT' || !cell || cell.status==='CONFLICTING')return [];
    const bands=[];
    for(const trace of cell.rules || []){if(trace.status!=='APPLIED' || !trace.spec?.plan_guard)continue;
      const support=trace.movement_statistics;if(!support)continue;
      for(const row of trace.output?.movement || []){if(row.position!==position || !(row.subject==='ALLY' || row.subject==='SELF' && p.input.my_position===position))continue;
        if(row.statistics_ref?.dataset_sha256!==support.dataset_sha256 || row.statistics_ref?.cohort_id!==support.cohort_id)continue;
        for(const point of support.points || [])if(point.visible===true && typeof point.minute==='number')bands.push({minute:point.minute,n:point.n,stage:row.stage,conditions:row.stage_conditions,dataset_digest:support.dataset_sha256,cohort_id:support.cohort_id});
      }
    }return bands;
  }
  function powerSlot(parent,p,position,compact){
    const host=node('div',undefined,'pg-power'+(compact?' pg-power-mini':''));host.dataset.position=position;host.append(node('p','통계 UNKNOWN · 불러오는 중','small'));parent.append(host);
    if(p.validity!=='CURRENT'){host.replaceChildren(node('p','통계 UNKNOWN · 현재 유효한 계획에서 확인하세요.','small'));return;}
    const own=p.input.slots.filter(s=>s.side==='ALLY' && s.position===position),enemy=p.input.slots.filter(s=>s.side==='ENEMY' && s.position===position);
    if(own.length!==1 || !own[0].champion || !p.input.patch){host.replaceChildren(node('p','통계 UNKNOWN · 챔피언·포지션·정확한 패치 필요','small'));return;}
    const champion=own[0].champion,opponent=enemy.length===1?enemy[0].champion:null,mark=context(),view=planViewEpoch;
    api('/power-view','POST',JSON.stringify({champion,position,patch:p.input.patch,tier:$('pg-power-tier').value || null,opponent_champion:opponent})).then(response=>{
      if(!alive(mark) || view!==planViewEpoch || plan!==p || !host.isConnected || dirty())return;
      window.PregamePower.render(host,response,{testMode,compact,champion,opponent,phaseBands:phaseBands(p,position)});
    }).catch(e=>{if(!alive(mark)||view!==planViewEpoch||plan!==p||!host.isConnected)return;if(e.status===401){apiError(e,mark);return;}host.replaceChildren(node('p','통계 UNKNOWN · 조회하지 못했습니다.','small'));});
  }
  function detail(parent,p,cells){
    const d=node('details');d.append(node('summary','저장 입력·규칙·출처·적용/제외 이유'));
    const applied=cells.flatMap(c=>c.rules || []);d.append(node('p','이 카드의 적용 규칙과 전체 평가 이력을 함께 확인합니다.','small'));
    for(const trace of [...applied,...(p.evaluations || [])]){d.append(node('p',(trace.rule_id || '규칙')+' · 버전 '+(trace.version || '')+' · '+(trace.status || '')+' · '+(trace.condition || ''),'small'));addSources(d,trace.sources || trace.spec?.sources);cooldowns(d,trace.cooldowns);}
    d.append(node('pre',json({saved_input:{session_id:p.session_id,input_revision:p.input_revision,input_sha256:p.input_sha256,input:p.input},cells,applied_rules:applied,evaluations:p.evaluations || []})));parent.append(d);
  }
  function renderPlan(p){
    planViewEpoch++;plan=p;$('pg-plan-panel').hidden=false;$('pg-plan-state').textContent=labels[p.validity] || p.validity;
    $('pg-plan-meta').textContent='입력 v'+p.input_revision+' · '+p.created_at+' · '+(p.input.my_position?roleNames[p.input.my_position]:'내 포지션 미확인')+(p.expiry_reasons?.length?' · 만료 근거: '+p.expiry_reasons.join(', '):'');$('pg-plan-json').textContent=json(p);$('pg-cards').replaceChildren();
    const unknownOperations={key:'OPERATIONS',title:'운영·의존',status:'UNKNOWN',texts:[],reasons:['LEGACY_OPERATIONS_UNAVAILABLE'],rules:[],cooldowns:[]};
    const sections=[['map','① 5개 포지션 지도',p.common.map],['jungle','② 정글 주도권',[p.common.jungle]],['composition','③ 조합 방향',[p.common.composition]],['role','④ 내 역할',[p.personal.role]],['lane','⑤ 라인·동선',[p.personal.lane]],['fight','⑥ 교전·생존',[p.personal.fight]],['operations','⑦ 운영·팀 의존',[p.operations || unknownOperations]],['movement','⑧ 이동 단계',[p.movement || {...unknownOperations,key:'MOVEMENT',title:'이동 단계',reasons:['MOVEMENT_UNAVAILABLE']}]],['changes','⑨ 변화 조건·미확인',[p.changes]]];
    for(const [id,title,cells] of sections){const card=node('article',undefined,'card');card.id='pg-card-'+id;card.append(node('h3',title));for(const c of cells){if(id==='map'){const row=node('div',undefined,'pg-map-row'+(c.key===p.input.my_position?' selected':''));row.dataset.position=c.key;cellContent(row,c,p);if(c.key===p.input.my_position)row.append(node('span','내 포지션','badge'));card.append(row);powerSlot(row,p,c.key,true);}else cellContent(card,c,p);}if(id==='operations')renderOperations(card,p,cells[0]);if(id==='movement')renderMovement(card,p,cells[0]);if(id==='lane')powerSlot(card,p,p.input.my_position,false);detail(card,p,cells);$('pg-cards').append(card);}
  }

  function knowledgeControls(){
    const item=selectedKnowledge,proposal=item?.proposal,spec=item?.spec;
    const blocked=!connected || knowledgeBusy || writeBusy || readBusy || planBusy;
    $('pg-import-candidate').disabled=blocked || !spec || !!proposal || $('pg-spec-json').value!==previewedSpec;
    $('pg-approve').disabled=blocked || !proposal || !spec || !spec.patches?.length;
    $('pg-reject').disabled=blocked || !proposal;
    $('pg-preview-spec').disabled=blocked;
  }
  function showKnowledge(item){
    if(knowledgeBusy)return;knowledgeEpoch++;selectedKnowledge=clone(item);if(!item.proposal){$('pg-spec-json').value=json(item.spec);previewedSpec=$('pg-spec-json').value;}else previewedSpec='';hidePlan();planAttempt=null;
    $('pg-knowledge-detail').hidden=false;const p=item.proposal,s=item.spec;
    $('pg-knowledge-state').textContent=(p?labels[p.review_state] || p.review_state:'EXPLORATORY 가져오기 전 미검토 후보')+' · '+(p?.rule_id || s?.rule_id || '')+' · 저장 버전 '+(p?.version || '없음')+' · 명세 버전 '+(s?.version || '미연결');
    $('pg-knowledge-sources').replaceChildren();addSources($('pg-knowledge-sources'),s?.sources || []);$('pg-knowledge-json').textContent=json(item);knowledgeControls();
  }
  async function refreshKnowledge(){
    const mark=context(),seq=++knowledgeEpoch;selectedKnowledge=null;knowledgeBusy=true;$('pg-knowledge-detail').hidden=true;hidePlan();planAttempt=null;knowledgeControls();
    try{const results=await Promise.allSettled([api('/knowledge'),api('/candidates'),api('/review-priority')]);if(!alive(mark)||seq!==knowledgeEpoch)return;
      $('pg-review-priority').replaceChildren();
      if(results[2].status==='fulfilled'){for(const row of (Array.isArray(results[2].value)?results[2].value:results[2].value?.recommended_review_order || [])){const d=node('details');d.append(node('summary',row.rank+'. '+row.title+' · '+row.candidate_id),node('p',row.reason),node('p','EXPLORATORY · 출처 후보 · 아직 실행 연결 없음','small'),node('p','출처 패치 범위: '+row.patch_range,'small'));addSources(d,(row.source_urls || []).map(url=>({url,title:url,locator:'원본 출처 후보',patch:null})));d.append(node('pre',json(row)));$('pg-review-priority').append(d);}}else $('pg-review-priority').append(node('p','검토 추천 목록을 불러오지 못했습니다.','small'));
      for(const [idx,id] of [[0,'pg-knowledge-list'],[1,'pg-candidate-list']]){const container=$(id);container.replaceChildren();if(results[idx].status==='rejected'){container.append(node('p','조회 실패: '+results[idx].reason.message,'small'));if(results[idx].reason.status===401)throw results[idx].reason;continue;}const rows=results[idx].value;if(!rows.length)container.append(node('p','현재 항목이 없습니다.','small'));for(const row of rows){const item=idx===0?row:{proposal:null,spec:row},p=item.proposal,s=item.spec,b=node('button',(p?.rule_id || s?.rule_id || '미연결')+' · '+(p?labels[p.review_state] || p.review_state:'EXPLORATORY')+' · '+(p?.version || s?.version || ''));b.addEventListener('click',()=>showKnowledge(item));container.append(b);}}
    }catch(e){if(alive(mark)&&seq===knowledgeEpoch)apiError(e,mark);}finally{if(alive(mark)&&seq===knowledgeEpoch){knowledgeBusy=false;knowledgeControls();}}
  }
  async function importCandidate(){
    knowledgeControls();if($('pg-import-candidate').disabled||knowledgeBusy||!selectedKnowledge?.spec||selectedKnowledge.proposal)return;
    const mark=context(),seq=knowledgeEpoch,spec=clone(selectedKnowledge.spec);knowledgeBusy=true;hidePlan();planAttempt=null;knowledgeControls();
    try{await api('/candidates','POST',JSON.stringify({spec}));if(!alive(mark)||seq!==knowledgeEpoch)return;knowledgeBusy=false;await refreshKnowledge();if(alive(mark))notice('EXPLORATORY 후보를 등록했습니다. 현재 버전을 열고 명세·출처를 검토하세요.');}
    catch(e){if(alive(mark)&&seq===knowledgeEpoch)apiError(e,mark);}finally{if(alive(mark)&&seq===knowledgeEpoch){knowledgeBusy=false;knowledgeControls();}}
  }
  // Review authority is accepted only in these direct trusted browser click handlers.
  async function decide(event,decision){
    knowledgeControls();if(!event.isTrusted || !navigator.userActivation.isActive || event.currentTarget.disabled || knowledgeBusy || !selectedKnowledge?.proposal)return;
    const p=clone(selectedKnowledge.proposal),spec=selectedKnowledge.spec;
    if(decision==='REVIEWED' && !spec?.patches?.length)return;
    if(!confirm('명세·출처·반례·한계를 확인했나요? '+p.rule_id+' 저장 버전 '+p.version+'을 '+(decision==='REVIEWED'?'승인':'거절')+'할까요? 이 결정은 새 버전으로 저장됩니다.'))return;
    const mark=context(),seq=knowledgeEpoch;knowledgeBusy=true;hidePlan();planAttempt=null;knowledgeControls();
    try{const response=await fetch('/dev/v1/knowledge/proposals/'+encodeURIComponent(p.rule_id)+'/decisions',{method:'POST',mode:'same-origin',cache:'no-store',headers:{Authorization:'Bearer '+token,'Content-Type':'application/json',Origin:location.origin},body:JSON.stringify({selected_version:p.version,expected_version:p.version,decision,patch_range:p.patch_range,applicability:p.applicability})});
      const result=await response.json();if(!alive(mark)||seq!==knowledgeEpoch)return;if(!response.ok){const e=new Error(result.error_code || 'DECISION_FAILED');e.status=response.status;throw e;}
      knowledgeBusy=false;await refreshKnowledge();if(alive(mark))notice('사용자의 '+(decision==='REVIEWED'?'승인':'거절')+' 결정을 저장했습니다. 새 현재 버전을 확인하세요.');
    }catch(e){if(alive(mark)&&seq===knowledgeEpoch)apiError(e,mark);}finally{if(alive(mark)&&seq===knowledgeEpoch){knowledgeBusy=false;knowledgeControls();}}
  }
  async function connect(){
    const auth=++authEpoch;navEpoch++;$('pg-login').disabled=true;
    try{const status=await api('/status');if(auth!==authEpoch)return;connected=true;testMode=status.test_mode===true;powerTiers=Array.isArray(status.power_tiers)?status.power_tiers:[];$('pg-power-tier').replaceChildren(option('','티어 미확인'));for(const tier of powerTiers)$('pg-power-tier').append(option(tier,tier));if(powerTiers.length)$('pg-power-tier').value=powerTiers[0];sessionStorage.setItem('lol-coach-dev-token',token);$('pg-token').value='';$('pg-auth').hidden=true;$('pg-workspace').hidden=false;$('pg-status').textContent='연결됨 · 자동 수집 미제공 · 패치 미확인';updateEditor();const mark=context();
      const results=await Promise.allSettled([refreshInputs(),refreshKnowledge(),api('/roster'),api('/draft-captures','GET',undefined,undefined,true)]);if(!alive(mark))return;
      for(const result of results)if(result.status==='rejected'){apiError(result.reason,mark);if(!connected)return;}
      if(results[2].status==='fulfilled'){const roster=results[2].value;$('pg-roster').replaceChildren();for(const c of roster.champions){const o=node('option');o.value=c.id;o.label=c.name+' · '+c.roles.map(r=>roleNames[r] || r).join(', ');$('pg-roster').append(o);}}
      if(results[3].status==='fulfilled'){$('pg-draft-select').replaceChildren(option('','저장본 선택'));for(const d of results[3].value)$('pg-draft-select').append(option(d.session_id || d.capture_id || d.id,(d.capture?.title || d.title || '픽창')+' · v'+d.revision));}
      notice('개인 경기 전 작업실에 연결됐습니다.');
    }catch(e){if(auth===authEpoch){sessionStorage.removeItem('lol-coach-dev-token');notice('연결 실패: '+e.message,true);}}
    finally{if(auth===authEpoch)$('pg-login').disabled=false;}
  }
  function logout(){
    authEpoch++;navEpoch++;editEpoch++;listEpoch++;knowledgeEpoch++;fileEpoch++;connected=false;testMode=false;powerTiers=[];$('pg-power-tier').replaceChildren(option('','티어 미확인'));token='';sessionStorage.removeItem('lol-coach-dev-token');current=null;saveAttempt=null;planAttempt=null;selectedKnowledge=null;writeBusy=false;readBusy=false;planBusy=false;knowledgeBusy=false;hidePlan();
    $('pg-auth').hidden=false;$('pg-workspace').hidden=true;$('pg-token').value='';$('pg-login').disabled=false;
    for(const id of ['pg-input-list','pg-history','pg-plan-list','pg-knowledge-list','pg-candidate-list','pg-knowledge-sources','pg-review-priority'])$(id).replaceChildren();$('pg-knowledge-detail').hidden=true;$('pg-knowledge-json').textContent='';$('pg-spec-json').value='';previewedSpec='';$('pg-restore').value='';putInput(emptyInput());baseline=fingerprint(readInput());updateEditor();knowledgeControls();notice('연결을 해제했습니다.');
  }
  function download(data,name){const url=URL.createObjectURL(new Blob([json(data)],{type:'application/json'})),a=node('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
  async function exportArchive(){const mark=context(),archive=await api('/export');if(!alive(mark))return;download(archive,'lol-coach-pregame-sidecar.json');notice('저장된 경기 전 입력·계획 이력을 내보냈습니다. 미저장 수정본은 포함되지 않습니다.');}
  async function restoreArchive(){
    const file=$('pg-restore').files[0];if(!file)return;const mark=context(),seq=++fileEpoch;
    try{if(file.size>1000000)throw new Error('복원 파일은 1MB 이하여야 합니다.');const archive=JSON.parse(await file.text());if(!alive(mark)||seq!==fileEpoch||$('pg-restore').files[0]!==file)return;if(!confirm('이 경기 전 sidecar를 빈 경기 전 DB에 복원할까요? 서버가 무결성과 빈 DB 조건을 확인합니다.'))return;await api('/restore','POST',JSON.stringify({archive}));if(!alive(mark)||seq!==fileEpoch)return;await refreshInputs();notice('경기 전 sidecar를 복원했습니다. 저장 목록에서 입력을 여세요.');}
    catch(e){if(alive(mark)&&seq===fileEpoch)apiError(e,mark);}finally{if(seq===fileEpoch&&$('pg-restore').files[0]===file)$('pg-restore').value='';}
  }
  function listen(id,event,handler){$(id).addEventListener(event,e=>{const mark=context();Promise.resolve().then(()=>handler(e)).catch(error=>apiError(error,mark));});}
  buildForm();putInput(emptyInput());baseline=fingerprint(readInput());updateEditor();knowledgeControls();
  $('pg-login-form').addEventListener('submit',e=>{e.preventDefault();token=$('pg-token').value.trim();connect();});
  $('pg-logout').addEventListener('click',logout);
  $('pg-input-form').addEventListener('submit',e=>{e.preventDefault();const mark=context();save().catch(error=>apiError(error,mark));});
  $('pg-input-form').addEventListener('input',()=>{editEpoch++;hidePlan();planAttempt=null;updateEditor();knowledgeControls();});
  $('pg-input-form').addEventListener('change',()=>{editEpoch++;hidePlan();planAttempt=null;updateEditor();knowledgeControls();});
  listen('pg-new','click',()=>newInput());listen('pg-golden','click',golden);listen('pg-refresh-inputs','click',refreshInputs);listen('pg-import-draft','click',importDraft);listen('pg-retry-save','click',()=>save(true));listen('pg-create-plan','click',createPlan);listen('pg-refresh-knowledge','click',refreshKnowledge);listen('pg-import-candidate','click',importCandidate);listen('pg-export','click',exportArchive);listen('pg-restore','change',restoreArchive);
  listen('pg-preview-spec','click',()=>{const spec=JSON.parse($('pg-spec-json').value);if(!['pregame.rule.v1','pregame.rule.v2','pregame.rule.v3'].includes(spec.schema_version))throw new Error('pregame.rule.v1/v2/v3 명세가 필요합니다.');showKnowledge({proposal:null,spec});});
  $('pg-power-tier').addEventListener('change',()=>{if(plan)renderPlan(plan);});
  $('pg-spec-json').addEventListener('input',()=>{knowledgeControls();});
  // Do not wrap these in a promise: active user gesture must be checked synchronously.
  $('pg-approve').addEventListener('click',event=>decide(event,'REVIEWED'));
  $('pg-reject').addEventListener('click',event=>decide(event,'REJECTED'));
  window.addEventListener('pagehide',()=>{authEpoch++;navEpoch++;knowledgeEpoch++;});
  if(token)connect();
})();

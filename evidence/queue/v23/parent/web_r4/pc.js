'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const roles = ['TOP', 'JUNGLE', 'MID', 'BOTTOM', 'SUPPORT'];
  const names = {TOP:'탑', JUNGLE:'정글', MID:'미드', BOTTOM:'원딜', SUPPORT:'서포터'};
  const stages = ['OWN', 'LANER', 'JUNGLE', 'COMPOSITION'];
  const node = (tag, text, cls) => {const n=document.createElement(tag);if(text!==undefined)n.textContent=String(text);if(cls)n.className=cls;return n;};
  const clone = value => JSON.parse(JSON.stringify(value));
  const unknown = () => ({kind:'UNKNOWN', reference:null, observed_at:null, verification:'UNKNOWN'});
  const manual = () => ({kind:'MANUAL', reference:'PC 수동 입력', observed_at:null, verification:'UNVERIFIED'});
  const selection = () => ({status:'UNKNOWN', values:[], source:unknown()});
  let token='', authenticated=false, authEpoch=0, revision=0, previewController=null, previewTimer=null;
  let automaticInput=null, lastConnectionRevision=null, wasAutomatic=false, inGame=false, catalog=[];
  let currentInput=null, renderedRevision=null, pollTimer=null, lastPhase=null;
  const expandedCards=new Set();let moreExpanded=false;
  const patchLabel=value=>({MATCHING_ARCHIVE:'입력 패치와 일치',GAME_PATCH_UNKNOWN:'게임 패치 미확인 · 참고용',GAME_PATCH_MISMATCH:'게임 패치와 다름 · 참고용'})[value] || '패치 미확인 · 참고용';
  const connectionReason=value=>({GAME_PC_NOT_CONNECTED:'로컬 클라이언트 연결을 기다립니다.',LCU_NOT_AVAILABLE:'클라이언트가 실행 중인지 확인하세요.',LOCAL_PAIRING_UNAVAILABLE:'로컬 연결 확인이 필요합니다. 수동 입력을 사용할 수 있습니다.',PHASE_CHANGED:'챔피언 선택 단계가 바뀌었습니다.',PHASE_UNKNOWN:'클라이언트 단계를 확인하지 못했습니다.',NOT_CHAMP_SELECT:'현재 챔피언 선택 단계가 아닙니다.',SESSION_CHANGED:'클라이언트 연결이 바뀌어 다시 확인합니다.',CERTIFICATE_PIN_MISMATCH:'클라이언트 인증서가 바뀌어 연결을 보류했습니다.',SCHEMA_UNSUPPORTED:'현재 클라이언트 형식을 확인하지 못했습니다.',LCU_REQUEST_FAILED:'클라이언트가 응답하지 않아 수동 입력을 사용합니다.',LOCKFILE_UNAVAILABLE:'클라이언트 연결 파일을 찾지 못했습니다.',LOCKFILE_INVALID:'클라이언트 연결 파일을 확인하지 못했습니다.'})[value] || '자동 연결을 확인하지 못해 수동 입력을 사용합니다.';
  const local = location.protocol==='http:' && ['127.0.0.1','localhost','[::1]'].includes(location.hostname);
  // Consume the fragment before any request; no token enters an HTTP request URL.
  const fragment = new URLSearchParams(location.hash.slice(1));
  const handedToken = fragment.get('token') || '';
  if(location.hash)history.replaceState(null,'',location.pathname+location.search);
  try {token=handedToken || sessionStorage.getItem('lol-coach-dev-token') || '';} catch (_) {token=handedToken;}

  function notice(message, bad=false) {$('pc-notice').textContent=message;$('pc-notice').className=bad?'error':'';}
  function empty(message='내 챔피언부터 알려 주세요') {
    $('pc-cards').replaceChildren();$('pc-empty').hidden=false;$('pc-empty').querySelector('h3').textContent=message;
    $('pc-stage').textContent='정보 대기';$('pc-review').textContent='';
    for(const li of document.querySelectorAll('[data-stage]'))li.classList.remove('active');
    renderedRevision=null;
  }
  function invalidate(message) {
    revision++;clearTimeout(previewTimer);previewController?.abort();previewController=null;
    empty(message);
  }
  async function api(path, method='GET', body, signal) {
    if(!local)throw new Error('LOCAL_ONLY');
    const response=await fetch('/dev/v1/pregame'+path,{method, mode:'same-origin', credentials:'same-origin', redirect:'error', cache:'no-store', signal,
      headers:{Authorization:'Bearer '+token,...(body===undefined?{}:{'Content-Type':'application/json'})},body:body===undefined?undefined:JSON.stringify(body)});
    const data=await response.json();
    if(!response.ok){const error=new Error(data.error_code || 'REQUEST_FAILED');error.status=response.status;throw error;}
    return data;
  }
  function errorMessage(error, epoch) {
    if(epoch!==authEpoch || error.name==='AbortError')return;
    if(error.status===401){logout();notice('접속키를 확인하고 다시 연결하세요.',true);return;}
    notice('로컬 응답을 확인하지 못했습니다. 수동 입력은 유지됩니다.',true);
  }
  function readManual() {
    const position=$('pc-position').value || null, own=$('pc-own').value.trim() || null;
    const ownIndex=position?roles.indexOf(position):0;
    const slots=['ALLY','ENEMY'].flatMap(side=>roles.map((role,index)=>({side,slot:index+1,champion:null,position:null,position_candidates:[],uncertainty:'미확인',champion_source:unknown(),position_source:unknown(),runes:selection(),summoners:selection()})));
    const put=(side,index,champion,position)=>{
      if(!champion)return;
      const slot=slots.find(s=>s.side===side && s.slot===index+1);
      Object.assign(slot,{champion,position,uncertainty:'수동 입력 · 미검증',champion_source:manual(),position_source:position?manual():unknown()});
    };
    for(const side of ['ALLY','ENEMY'])for(let i=0;i<roles.length;i++){
      const input=$('pc-team-'+side+'-'+roles[i]);
      if(!input.disabled)put(side,i,input.value.trim() || null,roles[i]);
    }
    put('ALLY',ownIndex,own,position);
    if(position && position!=='JUNGLE')put('ENEMY',ownIndex,$('pc-laner').value.trim() || null,position);
    if(!position)put('ENEMY',0,$('pc-laner').value.trim() || null,null);
    put('ENEMY',1,$('pc-jungler').value.trim() || null,'JUNGLE');
    return {title:'PC 경기 전 입력',patch:$('pc-patch').value.trim() || null,phase:$('pc-pregame').checked && !inGame?'PRE_GAME':'UNKNOWN',observed_at:null,my_position:position,my_champion:own,my_slot:own?ownIndex+1:null,slots,source:manual(),original_capture:null};
  }
  function updateComposition() {
    const position=$('pc-position').value;
    for(const side of ['ALLY','ENEMY'])for(const role of roles){
      const input=$('pc-team-'+side+'-'+role);
      input.disabled=side==='ALLY'?(role===(position || 'TOP')):(role==='JUNGLE' || role===(position || 'TOP'));
      input.parentElement.hidden=input.disabled;
    }
    $('pc-laner').disabled=position==='JUNGLE';
    if(position==='JUNGLE')$('pc-laner').value='';
  }
  function isAutomatic() {return $('pc-auto').checked && automaticInput && !inGame;}
  function schedulePreview(immediate=false) {
    invalidate(inGame?'게임이 시작되어 경기 전 카드를 숨겼습니다.':'입력에 맞는 정보를 확인합니다.');
    if(!authenticated || inGame)return;
    const capturedRevision=revision, epoch=authEpoch;
    previewTimer=setTimeout(()=>preview(capturedRevision,epoch),immediate?0:100);
  }
  async function preview(capturedRevision=revision, epoch=authEpoch) {
    if(!authenticated || capturedRevision!==revision || epoch!==authEpoch || inGame)return;
    const input=isAutomatic()?clone(automaticInput):readManual();
    const manualPatch=isAutomatic() && input.patch===null && $('pc-patch').value.trim();
    if(manualPatch){input.patch=manualPatch;input.source=manual();input.title='PC 자동 선택 · 패치 수동 입력';}
    currentInput=clone(input);
    const controller=new AbortController();previewController=controller;
    $('pc-input-mode').textContent=isAutomatic()?(manualPatch?'자동 선택 · 패치는 수동 미검증':'자동 · 클라이언트 선택 정보'):'수동 · 미검증';
    $('pc-phase').textContent=input.phase==='PRE_GAME'?(isAutomatic()?'챔피언 선택 · 자동':'챔피언 선택 · 수동'):'단계 미확인';
    try {
      const result=await api('/pc-preview','POST',{input,draft_revision:capturedRevision},controller.signal);
      if(!authenticated || epoch!==authEpoch || capturedRevision!==revision || result.draft_revision!==capturedRevision || inGame)return;
      render(result);renderedRevision=capturedRevision;
      notice('입력에 맞는 근거를 표시했습니다.');
    } catch(error){errorMessage(error,epoch);}
  }
  function sources(parent, list) {
    const ul=node('ul',undefined,'sources');
    for(const source of list || []){
      const row=node('li'), label=source.title || source.name || source.url || '출처';
      let url;try {url=new URL(source.url);}catch(_){}
      if(url && url.protocol==='https:' && !url.username && !url.password){const a=node('a',label);a.href=url.href;a.target='_blank';a.rel='noopener noreferrer';row.append(a);}
      else row.append(node('span',label+' · 안전한 링크 없음'));
      if(source.patch)row.append(node('div','자료 패치: '+source.patch));
      if(source.locator)row.append(node('div',source.locator));
      if(source.sha256)row.append(node('div','원문 SHA256: '+source.sha256));
      ul.append(row);
    }
    if(ul.children.length)parent.append(ul);
  }
  function render(result) {
    $('pc-cards').replaceChildren();
    const phase=result.phase==='PRE_GAME';
    const cards=Array.isArray(result.cards)?result.cards:[];
    const visible=cards.filter(card=>phase || ['OFFICIAL','OFFICIAL_FACT','OFFICIAL_REFERENCE'].includes(card.evidence_level));
    const tactical=visible.filter(card=>['USER','AUTO_VERIFIED','HYPOTHESIS','EXPLORATORY'].includes(card.evidence_level)).slice(0,3);
    const ownOfficial=visible.find(card=>card.evidence_level==='OFFICIAL' && card.champion===currentInput?.my_champion);
    const first=[...tactical,...(ownOfficial?[ownOfficial]:[])];
    if(!first.length && visible.length)first.push(visible[0]);
    const others=visible.filter(card=>!first.includes(card));
    const more=node('details',undefined,'more-cards');more.open=moreExpanded;more.append(node('summary','다른 준비 조언·공식 설명 '+others.length+'개'));
    const group=node('div',undefined,'card-group');more.append(group);more.addEventListener('toggle',()=>{moreExpanded=more.open;});
    for(const card of [...first,...others]){
      const article=node('article',undefined,'coach-card');article.dataset.cardId=card.id || '';
      if(card.candidate_id)article.dataset.candidateId=card.candidate_id;
      const hypothesis=['EXPLORATORY','HYPOTHESIS'].includes(card.evidence_level);
      const label=hypothesis?'미검토 가설(AI 작성, 근거 링크)':card.evidence_label || '근거 미확인';
      const reference=card.evidence_level==='OFFICIAL' && card.patch_status!=='MATCHING_ARCHIVE';
      article.append(node('span',label+(reference?' · 참고용':''),'evidence '+(card.evidence_level || '')));
      article.append(node('h3',card.title || '경기 전 참고'));
      const lines=node('div',undefined,'card-lines');for(const line of (card.lines || []).slice(0,3))lines.append(node('p',line));article.append(lines);
      const detail=node('details'),summary=node('summary','상세 설명 · 근거 보기');detail.open=expandedCards.has(card.id);detail.addEventListener('toggle',()=>{if(detail.open)expandedCards.add(card.id);else expandedCards.delete(card.id);});detail.append(summary);
      if(card.details)detail.append(node('p',card.details));
      detail.append(node('p',patchLabel(card.patch_status)));sources(detail,card.sources);article.append(detail);
      if(card.evidence_level==='AUTO_VERIFIED' && card.candidate_id && card.candidate_sha256){
        const button=node('button','이 자동 검토에 이의 제기','objection');button.type='button';
        button.addEventListener('click',event=>objection(event,card,button));article.append(button);
      }
      (first.includes(card)?$('pc-cards'):group).append(article);
    }
    if(others.length)$('pc-cards').append(more);
    $('pc-empty').hidden=visible.length>0;
    if(!visible.length)$('pc-empty').querySelector('h3').textContent=phase?'확인된 정보가 아직 없습니다.':'단계 미확인 · 경기 전 카드를 숨겼습니다.';
    const stage=stages.indexOf(result.stage);
    for(const li of document.querySelectorAll('[data-stage]'))li.classList.toggle('active',phase && stages.indexOf(li.dataset.stage)<=stage);
    $('pc-stage').textContent=({OWN:'내 픽',LANER:'상대 라인',JUNGLE:'적 정글',COMPOSITION:'조합',EMPTY:'입력 대기'})[result.stage] || '입력 대기';
    const review=result.review_summary || {};
    $('pc-review').textContent='자동 검토 통과 '+(review.passed || 0)+' · 보류 '+(review.held || 0)+' · 자동 검토는 사용자 승인과 별개입니다.';
  }
  async function objection(event, card, button) {
    // Only a native user event may open this write flow. No timer/automation calls it.
    if(!event.isTrusted || !authenticated || renderedRevision!==revision)return;
    const capturedRevision=revision, epoch=authEpoch;
    const reason=window.prompt('이의를 제기하는 이유를 적어 주세요. 해당 후보는 즉시 제외됩니다.');
    if(reason===null || !reason.trim())return;
    if(capturedRevision!==revision || epoch!==authEpoch)return;
    button.disabled=true;
    try {
      await api('/pc-objection','POST',{candidate_id:card.candidate_id,reason:reason.trim().slice(0,2000),candidate_sha256:card.candidate_sha256});
      if(epoch!==authEpoch || !authenticated)return;
      // Remove across the current projection before requesting the updated view.
      for(const article of $('pc-cards').querySelectorAll('[data-candidate-id]'))if(article.dataset.candidateId===card.candidate_id)article.remove();
      notice('이의를 기록하고 해당 후보를 제외했습니다.');schedulePreview(true);
    } catch(error){if(epoch===authEpoch)button.disabled=false;errorMessage(error,epoch);}
  }
  async function poll(epoch) {
    if(!authenticated || epoch!==authEpoch)return;
    try {
      const status=await api('/pc-status');
      if(!authenticated || epoch!==authEpoch)return;
      const connection=status.connection || {}, phase=connection.phase;
      const connected=connection.status==='CONNECTED';
      const liveGame=['GameStart','InProgress','Reconnect','GAME_START','IN_GAME','IN_PROGRESS'].includes(phase);
      const select=connected && ['ChampSelect','CHAMP_SELECT','PRE_GAME'].includes(phase) && connection.input?.phase==='PRE_GAME';
      $('pc-connection').textContent=select?'클라이언트 연결됨':liveGame?'게임 진행 중':'수동 입력 가능';
      $('pc-lcu-reason').textContent=select?'선택·확정·포지션·밴 정보만 반영합니다.':liveGame?'경기 전 정보는 게임 시작과 함께 숨깁니다.':connectionReason(connection.reason);
      if(liveGame){
        if(!inGame || lastPhase!==phase){inGame=true;automaticInput=null;invalidate('게임이 시작되어 경기 전 카드를 숨겼습니다.');}
      } else {
        if(inGame){inGame=false;invalidate('경기 전 정보를 다시 입력하세요.');}
        if(select){
          if(connection.revision!==lastConnectionRevision){
            lastConnectionRevision=connection.revision;automaticInput=clone(connection.input);
            if($('pc-auto').checked){wasAutomatic=true;schedulePreview(true);}
          }
        } else if(wasAutomatic || automaticInput){
          automaticInput=null;wasAutomatic=false;lastConnectionRevision=null;
          invalidate('클라이언트 단계가 바뀌어 카드를 숨겼습니다. 수동 입력은 유지됩니다.');
          $('pc-input-mode').textContent='수동 · 미검증';
        }
      }
      lastPhase=phase;
      const report=status.weekly_report;
      if(report){
        const week=/^(\d{4})-W(\d+)$/.exec(report.week || '');
        $('pc-weekly-title').textContent=(week?week[1]+'년 '+Number(week[2])+'주':'이번 주')+' 로컬 점검 · 검토 선택사항';
        $('pc-weekly-items').replaceChildren();
        for(const item of (report.items || []).slice(0,5))$('pc-weekly-items').append(node('li',item.summary || '자동 검토 기록'));
        if(!$('pc-weekly-items').children.length)$('pc-weekly-items').append(node('li','이번 주 점검 항목을 준비하고 있습니다.'));
      }
    } catch(error){
      if(epoch===authEpoch && authenticated){
        $('pc-connection').textContent='연결 응답 없음 · 수동 입력 가능';
        if(automaticInput || wasAutomatic){automaticInput=null;wasAutomatic=false;lastConnectionRevision=null;invalidate('자동 연결이 끊겼습니다. 수동 입력은 유지됩니다.');}
        errorMessage(error,epoch);
      }
    } finally {if(authenticated && epoch===authEpoch)pollTimer=setTimeout(()=>poll(epoch),500);}
  }
  function renderCatalog() {
    const filter=$('pc-reference-search').value.trim().toLocaleLowerCase();$('pc-reference-list').replaceChildren();
    const matches=catalog.filter(c=>[c.champion,c.name,c.champion_name].some(v=>String(v || '').toLocaleLowerCase().includes(filter)));
    for(const champion of matches){
      const item=node('details',undefined,'reference-item');item.append(node('summary',(champion.name || champion.champion_name || champion.champion)+' · '+champion.champion+' · '+patchLabel(champion.patch_status)));
      for(const fact of champion.facts || []){
        item.append(node('p',(fact.name || fact.ability || '')+(fact.text?' · '+fact.text:'')));
        if(fact.source)sources(item,[fact.source]);
      }
      $('pc-reference-list').append(item);
    }
    if(!matches.length)$('pc-reference-list').append(node('p',catalog.length?'검색 결과가 없습니다.':'저장된 공식 자료가 없습니다. 다음 갱신에서 다시 확인합니다.','small'));
  }
  async function loadCatalog(epoch) {
    try {
      const response=await api('/official-catalog');if(epoch!==authEpoch || !authenticated)return;
      catalog=response.champions || [];renderCatalog();
      $('pc-roster').replaceChildren();
      for(const champion of catalog){const option=node('option');option.value=champion.champion;option.label=champion.name || champion.champion_name || champion.champion;$('pc-roster').append(option);}
    } catch(error){if(epoch===authEpoch && authenticated)renderCatalog();}
  }
  async function login() {
    if(!local){notice('이 화면은 로컬 PC 주소에서만 연결할 수 있습니다.',true);return;}
    const value=$('pc-token').value.trim() || token;if(!value)return;
    token=value;const epoch=++authEpoch;notice('로컬 서버에 연결합니다.');
    try {
      await api('/pc-status');if(epoch!==authEpoch)return;
      authenticated=true;try {sessionStorage.setItem('lol-coach-dev-token',token);}catch(_){}
      $('pc-token').value='';$('pc-auth').hidden=true;$('pc-workspace').hidden=false;$('pc-logout').hidden=false;
      notice('연결되었습니다.');poll(epoch);loadCatalog(epoch);schedulePreview(true);
    } catch(error){errorMessage(error,epoch);}
  }
  function logout() {
    authEpoch++;authenticated=false;token='';automaticInput=null;currentInput=null;lastConnectionRevision=null;wasAutomatic=false;inGame=false;lastPhase=null;
    clearTimeout(pollTimer);invalidate();catalog=[];expandedCards.clear();moreExpanded=false;$('pc-reference-list').replaceChildren();$('pc-roster').replaceChildren();
    try {sessionStorage.removeItem('lol-coach-dev-token');sessionStorage.removeItem('pregame-token');}catch(_){}
    $('pc-auth').hidden=false;$('pc-workspace').hidden=true;$('pc-logout').hidden=true;$('pc-connection').textContent='연결 대기';notice('로컬 연결을 해제했습니다.');
  }
  for(const side of ['ALLY','ENEMY'])for(const role of roles){
    const label=node('label',(side==='ALLY'?'아군 ':'적군 ')+names[role]),input=node('input');
    input.id='pc-team-'+side+'-'+role;input.maxLength=100;input.setAttribute('list','pc-roster');label.append(input);$('pc-team-inputs').append(label);
  }
  updateComposition();
  $('pc-draft').addEventListener('submit',event=>event.preventDefault());
  $('pc-draft').addEventListener('input',()=>{
    $('pc-auto').checked=false;wasAutomatic=false;updateComposition();schedulePreview();
  });
  $('pc-auto').addEventListener('change',()=>{wasAutomatic=!!isAutomatic();schedulePreview(true);});
  $('pc-refresh').addEventListener('click',()=>schedulePreview(true));
  $('pc-login').addEventListener('submit',event=>{event.preventDefault();login();});
  $('pc-logout').addEventListener('click',logout);
  $('pc-reference-search').addEventListener('input',renderCatalog);
  window.addEventListener('storage',event=>{if(event.key==='lol-coach-dev-token' && !event.newValue && authenticated)logout();});
  if(token)login();
})();

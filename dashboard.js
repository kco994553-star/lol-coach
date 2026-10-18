/* Identity lookup is not login or current draft detection. No provider key in this client. */
(function(){
  'use strict';
  const $=id=>document.getElementById(id),local=['127.0.0.1','localhost'].includes(location.hostname)&&location.protocol==='http:'&&document.body.dataset.accountBackend!=='PUBLIC_STATIC';
  let generation=0,controller=null,profile=null,selectedReview=null;
  const positionNames={TOP:'탑',JUNGLE:'정글',MID:'미드',BOTTOM:'바텀',SUPPORT:'서포터'};
  const tierNames={IRON:'아이언',BRONZE:'브론즈',SILVER:'실버',GOLD:'골드',PLATINUM:'플래티넘',EMERALD:'에메랄드',DIAMOND:'다이아몬드',MASTER:'마스터',GRANDMASTER:'그랜드마스터',CHALLENGER:'챌린저'};
  const date=stamp=>stamp?new Date(stamp).toLocaleString('ko-KR'):'미확인';
  const rate=n=>typeof n==='number'&&Number.isFinite(n)?n.toFixed(1)+'%':'미확인';
  const ratio=n=>typeof n==='number'&&Number.isFinite(n)?n.toFixed(1):'미확인';
  const node=(tag,text,cls)=>{const n=document.createElement(tag);if(text!=null)n.textContent=text;if(cls)n.className=cls;return n;};
  const statuses={GUEST:'계정 연결 없이 준비 중입니다. 기록은 미연결이며 10픽 전략은 바로 사용할 수 있습니다.',READY:'입력한 Riot ID는 아직 조회하지 않았습니다.',LOADING:'계정을 조회 중입니다…',INPUT_ERROR:'게임 이름#태그를 확인해 주세요.',REGION_UNSUPPORTED:'이 지역의 안전한 조회 경로는 준비 중입니다. 계정 없이 경기 전 준비는 가능합니다.',ACCOUNT_NOT_FOUND:'해당 Riot ID를 찾지 못했습니다. 이름·태그·지역을 확인해 주세요.',API_UNAVAILABLE:'계정 API에 연결할 수 없습니다. 계정 없이 경기 전 준비를 계속할 수 있습니다.',AUTH_REQUIRED:'PC 연결 인증이 필요합니다. 기존 PC 실행기로 연결하거나 계정 없이 준비하세요.',CONNECTED:'계정 기록을 불러왔습니다. 기록 조회는 계정 소유권 인증이나 코칭 평가가 아닙니다.'};
  function route(){const key=location.hash==='#review-card'?'review':['#dashboard','#pro-records'].includes(location.hash)?'dashboard':'search';document.querySelectorAll('[data-account-view]').forEach(n=>n.hidden=n.dataset.accountView!==key);}
  window.addEventListener('hashchange',route);route();
  function clearReview(){selectedReview=null;$('review-selection').textContent='선택한 경기가 없습니다. 전적 검색의 최근 경기에서 골라 주세요.';$('review-selection').dataset.origin='NONE';}
  function reviewRow(m,origin,scope){const row=node('div',null,'match-row');row.append(node('span',m.champion+' · '+(m.won?'승리':'패배'),m.won?'record-win':'record-loss'),node('span',m.kills+' / '+m.deaths+' / '+m.assists),node('span',date(m.started_at)));const button=node('button','이 경기 복기 준비','secondary');button.type='button';button.dataset.reviewRecord=origin;button.addEventListener('click',()=>{selectedReview={champion:m.champion,won:m.won,kills:m.kills,deaths:m.deaths,assists:m.assists,started_at:m.started_at,origin,scope};const target=$('review-selection');target.dataset.origin=origin;target.replaceChildren(node('p',(origin==='PRO_REFERENCE'?'프로 참고 기록':'조회한 계정 기록')+' · '+scope),node('p',selectedReview.champion+' · '+(selectedReview.won?'승리':'패배')+' · '+selectedReview.kills+' / '+selectedReview.deaths+' / '+selectedReview.assists),node('p',date(selectedReview.started_at)));location.hash='#review-card';route();$('review-card').focus({preventScroll:true});});row.append(button);return row;}
  function status(code){$('account-retry').hidden=code!=='API_UNAVAILABLE';$('account-status').dataset.state=code;$('account-status').textContent=statuses[code]||statuses.API_UNAVAILABLE;$('account-status').classList.toggle('error',!['GUEST','READY','LOADING','CONNECTED'].includes(code));}
  function invalidate(){clearReview();generation++;controller?.abort();controller=null;$('account-submit').disabled=false;if(profile){profile=null;renderProfile(null);}status('READY');}
  function renderProfile(p){
    clearReview();profile=p;$('data-mode').textContent=p?'조회한 계정 기록 · 소유권 미인증':'계정 미연결';$('profile-name').textContent=p?p.riot_id:'계정 연결 전';$('profile-sub').textContent=p?p.region+' · 마지막 조회 '+date(p.retrieved_at):'기록을 불러오면 이곳에 표시합니다.';
    $('profile-rank').textContent=p?.rank?(tierNames[p.rank.tier]||p.rank.tier)+' '+p.rank.division+' · '+p.rank.lp+' LP':p?'랭크 미확인':'미연결';
    const s=p?.statistics;$('profile-winrate').textContent=s?.sample_n?ratio(s.win_rate)+'%':'미연결 / 유효 표본 없음';$('profile-kda').textContent=s?.sample_n&&s.kda!=null?ratio(s.kda):s?.sample_n?'미정의':'미연결';
    const scope=s?.sample_n?'솔로/듀오 랭크 '+s.sample_n+'경기 · '+date(s.window_start)+' ~ '+date(s.window_end)+' · 누락/제외 '+p.omitted_matches+'경기':'유효한 경기 표본이 없습니다. 승률·KDA·코칭 점수를 만들지 않습니다.';
    $('profile-scope').textContent=scope;$('recent-scope').textContent=scope;
    const recent=$('recent-matches');recent.replaceChildren();if(!p?.recent_matches?.length)recent.append(node('p','불러온 경기가 없습니다.'));
    (p?.recent_matches||[]).forEach(m=>recent.append(reviewRow(m,'USER_RECORD',scope)));
    const champs=$('champion-records');champs.replaceChildren();if(!p?.champions?.length)champs.append(node('p','유효한 챔피언별 표본이 없습니다.'));
    (p?.champions||[]).forEach(c=>{const row=node('div',null,'champion-row');row.append(node('span',c.champion+' · '+c.sample_n+'경기'),node('span',ratio(c.win_rate)+'% · KDA '+ratio(c.kda)));champs.append(row);});
    $('coaching-notes').textContent='기록 조회와 코칭 분석은 별개입니다. 근거가 연결된 개인 분석이 아직 없습니다.';
    document.querySelector('.pro-card').hidden=Boolean(p);$('pro-entry').hidden=Boolean(p);
  }
  $('account-form').addEventListener('submit',async e=>{
    e.preventDefault();const body={riot_id:$('riot-id').value,region:$('region').value};const parts=body.riot_id.split('#');
    if(parts.length!==2||!parts.every(s=>s.trim())||parts[0].length>100||parts[1].length>20||/[\x00-\x1f]/.test(body.riot_id)){status('INPUT_ERROR');return;}
    const own=++generation;controller?.abort();controller=new AbortController();$('account-submit').disabled=true;status('LOADING');
    try{
      if(body.region!=='KR'){status('REGION_UNSUPPORTED');return;}
      if(!local){await new Promise(resolve=>requestAnimationFrame(resolve));if(own===generation)status('API_UNAVAILABLE');return;}
      let token='';try{token=sessionStorage.getItem('lol-coach-dev-token')||'';}catch(_){}
      if(!token){status('AUTH_REQUIRED');return;}
      const response=await fetch('/dev/v1/account/lookup',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+token},body:JSON.stringify(body),signal:controller.signal,cache:'no-store',credentials:'same-origin',redirect:'error'});token='';
      if(own!==generation)return;if(!response.ok){status(response.status===401?'AUTH_REQUIRED':'API_UNAVAILABLE');return;}
      const data=await response.json();if(own!==generation)return;
      if(data.status==='CONNECTED'&&validProfile(data.profile)){renderProfile(data.profile);status('CONNECTED');location.hash='#dashboard';route();$('dashboard').focus({preventScroll:true});$('dashboard').scrollIntoView();}else status(data.status==='CONNECTED'?'API_UNAVAILABLE':data.status);
    }catch(error){if(own===generation&&error.name!=='AbortError')status('API_UNAVAILABLE');}finally{if(own===generation)$('account-submit').disabled=false;}
  });
  function validProfile(p){return p&&p.format==='lol-coach-account-profile-v1'&&typeof p.riot_id==='string'&&Array.isArray(p.recent_matches)&&p.recent_matches.every(m=>m.queue_id===420)&&p.statistics?.queue_id===420&&Array.isArray(p.champions)&&typeof p.omitted_matches==='number';}
  $('riot-id').addEventListener('input',invalidate);$('region').addEventListener('change',invalidate);
  $('guest-entry').addEventListener('click',()=>{generation++;controller?.abort();$('account-submit').disabled=false;renderProfile(null);status('GUEST');location.href='./loading.html';});
  $('account-retry').addEventListener('click',()=>$('account-form').requestSubmit());
  let heroes=[],heroIndex=-1,heroSerial=0;
  const heroStatus=(state,text)=>{$('hero-status').dataset.state=state;$('hero-status').textContent=text;};
  function showHero(index){
    heroIndex=index;const h=heroes[index],serial=++heroSerial,img=$('hero-art');img.hidden=false;img.dataset.art=h.id;$('hero-name').textContent=h.name;heroStatus('LOADING','');
    for(const [mode,keys] of [['desktop',['--hero-x','--hero-y']],['mobile',['--hero-mobile-x','--hero-mobile-y']]])h.crop[mode].forEach((v,i)=>img.style.setProperty(keys[i],v+'%'));
    img.onload=()=>{if(serial===heroSerial)heroStatus('READY','');};img.onerror=()=>{if(serial===heroSerial){img.hidden=true;heroStatus('ERROR','이미지 연결 불가 · 검색과 준비는 계속할 수 있습니다.');}};
    try{sessionStorage.setItem('lol-coach-hero-v1',h.id);}catch(_){}img.src=h.src;
  }
  $('hero-cycle').addEventListener('pointerdown',e=>{if(e.button===0&&$('account-form').contains(document.activeElement))e.preventDefault();});
  $('hero-cycle').addEventListener('click',()=>{if(heroes.length>1)showHero((heroIndex+1)%heroes.length);});
  fetch('./hero-art.json',{credentials:'same-origin',redirect:'error'}).then(r=>{if(!r.ok)throw Error();return r.json();}).then(data=>{
    if(data.format!=='lol-coach-hero-art-v1'||!Array.isArray(data.assets)||!data.assets.length)throw Error();
    const heroSources={"Ahri":"Ahri.jpg","Caitlyn":"Caitlyn.jpg","AhriSkin27":"AhriSkin27.jpg","LuxSkin7":"LuxSkin7.jpg","Moonlit":"Moonlit.webp","AsheBase":"AsheBase.jpg","AsheSkin17":"AsheSkin17.jpg","KaisaBase":"KaisaBase.jpg","KaisaSkin14":"KaisaSkin14.jpg","JinxBase":"JinxBase.jpg","JinxSkin4":"JinxSkin4.jpg","EzrealBase":"EzrealBase.jpg","EzrealSkin21":"EzrealSkin21.jpg","LuxBase":"LuxBase.jpg","LuxSkin17":"LuxSkin17.jpg","YasuoBase":"YasuoBase.jpg","YasuoSkin9":"YasuoSkin9.jpg","YoneBase":"YoneBase.jpg","YoneSkin1":"YoneSkin1.jpg","IreliaBase":"IreliaBase.jpg","IreliaSkin37":"IreliaSkin37.jpg","VayneBase":"VayneBase.jpg","VayneSkin25":"VayneSkin25.jpg","LeonaBase":"LeonaBase.jpg","LeonaSkin10":"LeonaSkin10.jpg"};
    const safe=data.assets.every(h=>Object.hasOwn(heroSources,h.id)&&h.src==='./home-assets/'+heroSources[h.id]&&typeof h.name==='string'&&h.crop&&['desktop','mobile'].every(mode=>Array.isArray(h.crop[mode])&&h.crop[mode].length===2&&h.crop[mode].every(v=>typeof v==='number'&&Number.isFinite(v)&&v>=0&&v<=100)));
    if(!safe||new Set(data.assets.map(h=>h.id)).size!==data.assets.length)throw Error();heroes=data.assets.filter(h=>['OFFICIAL_STATIC_SPLASH','OFFICIAL_SKIN_SPLASH'].includes(h.kind));if(!heroes.length)throw Error();let saved;try{saved=sessionStorage.getItem('lol-coach-hero-v1');}catch(_){}const i=heroes.findIndex(h=>h.id===saved);showHero(i>=0?i:Math.floor(Math.random()*heroes.length));$('hero-cycle').disabled=heroes.length<2;
  }).catch(()=>{$('hero-art').hidden=true;$('hero-cycle').disabled=true;$('hero-name').textContent='LoL Coach';heroStatus('EMPTY','일러스트 목록 연결 불가 · 검색과 준비는 가능합니다.');});
  if(local){$('review-local').hidden=false;$('review-note').textContent='PC의 인증된 복기 화면에서 경기 종료·실제 자료를 확인한 뒤 분석합니다.';}
  fetch('./pro-dashboard.json',{cache:'no-store',credentials:'same-origin',redirect:'error'}).then(r=>{if(!r.ok)throw Error();return r.json();}).then(data=>{
    const target=$('pro-records');target.replaceChildren();if(data.format!=='lol-coach-pro-dashboard-v1'||data.queue_id!==420||!Array.isArray(data.profiles))throw Error();
    if(data.refresh_status?.startsWith('FAILED'))target.append(node('p','최근 갱신 실패 · 마지막 성공 기록을 유지합니다. 시도 시각 '+date(data.last_attempt_at)));
    if(!data.profiles.length){if(data.status==='BLOCKED_EXTERNAL'){target.append(node('p','확인된 계정의 실제 기록 조회가 연결되지 않았습니다. 미연결 수치를 만들지 않습니다.'));return;}target.append(node('p','확인된 LCK 1군 계정의 프로 참고 기록이 아직 연결되지 않았습니다.'),node('p','미확인 선수·계정·다른 대회 기록으로 채우지 않습니다. 마지막 데이터 갱신: 미확인'));return;}
    data.profiles.forEach(p=>{if(p.roster_status!=='CURRENT_LCK_FIRST_TEAM_VERIFIED'||p.account_status!=='VERIFIED'||!validProfile(p.profile))return;const card=node('article',null,'pro-profile'),q=p.profile;card.append(node('h4',p.player+' · '+p.team+' · '+(positionNames[p.position]||'포지션 미확인')+' · 프로 참고 기록'),node('p',q.riot_id+' · 마지막 갱신 '+date(q.retrieved_at)),node('p',q.statistics.sample_n+'경기 · '+date(q.statistics.window_start)+' ~ '+date(q.statistics.window_end)),node('p',q.rank?(tierNames[q.rank.tier]||q.rank.tier)+' '+q.rank.division+' · '+q.rank.lp+' LP':'랭크 미확인'),node('p','표본 승률 '+rate(q.statistics.win_rate)+' · KDA '+ratio(q.statistics.kda)));card.append(node('p','소속·본인 계정 확인일 '+p.account_checked_at+' · 포지션은 선수 명단 기준, 표본은 조회한 솔로랭크 전체입니다.'));const records=node('details');records.append(node('summary','최근 경기·챔피언별 표본 보기'));
      const recent=node('div',null,'pro-recent');recent.dataset.proRecent='true';recent.append(node('h5','실제 조회한 최근 솔로랭크'));
      q.recent_matches.forEach(m=>recent.append(reviewRow(m,'PRO_REFERENCE',p.player+' · '+p.team+' · queue420 · 조회 '+date(q.retrieved_at))));
      if(!q.recent_matches.length)recent.append(node('p','유효한 최근 경기 표본이 없습니다.'));
      const champs=node('div',null,'pro-champions');champs.dataset.proChampions='true';champs.append(node('h5','같은 조회 표본의 챔피언 기록'));
      q.champions.forEach(c=>{const row=node('div',null,'champion-row');row.append(node('span',c.champion+' · '+c.sample_n+'경기'),node('span',rate(c.win_rate)+' · KDA '+ratio(c.kda)));champs.append(row);});
      if(!q.champions.length)champs.append(node('p','유효한 챔피언 표본이 없습니다.'));
      records.append(recent,champs,node('p','누락·제외 '+q.omitted_matches+'경기 · 최근 조회 표본이며 시즌 전체 기록이 아닙니다.'));card.append(records);target.append(card);});
    if(!target.childElementCount)target.append(node('p','출처·계정·솔로랭크 범위를 확인할 수 없어 참고 기록을 표시하지 않습니다.'));
  }).catch(()=>{$('pro-records').textContent='프로 참고 데이터 연결 불가 · 개인 수치를 대신 만들지 않습니다.';});
})();

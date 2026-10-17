'use strict';
(async()=>{
  const response=await fetch('./directions-status.json',{cache:'no-store'});
  if(!response.ok)throw Error('상태 기록을 불러오지 못했습니다.');
  const status=await response.json();
  document.querySelector('#status-time').textContent='상태 확인 시각: '+new Date(status.observed_at).toLocaleString('ko-KR',{timeZone:'Asia/Seoul'})+' KST';
  const root=document.querySelector('#status-items');
  for(const item of status.items){
    const section=document.createElement('section');section.className='panel';
    const h=document.createElement('h2'),state=document.createElement('p'),detail=document.createElement('p');
    h.textContent=item.name;state.textContent=item.state;detail.textContent=item.detail;
    section.append(h,state,detail);root.append(section);
  }
  const build=await fetch('./build-info.json',{cache:'no-store'});
  if(build.ok){const b=await build.json();document.querySelector('#status-build').textContent='공개 웹 빌드: '+b.source_commit.slice(0,12)+' · '+b.built_at+' (빌드 시각은 상태 재확인 시각이 아닙니다.)';}
})().catch(e=>{document.querySelector('#status-time').textContent=e.message;});

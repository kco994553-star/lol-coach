'use strict';
(()=>{
 const node=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
 function render(host,data){
  host.replaceChildren(node('h3','공식 자료 · 승인 없이 참고'));
  host.append(node('p','공식 한국어 스킬 설명입니다. 전술의 승패나 최적 선택을 판정하는 내용은 별도로 검토합니다.'));
  for(const [index,champion] of (data.champions||[]).entries()){
   const group=node('details');group.open=index===0;group.className='official-champion';group.dataset.champion=champion.champion;
   group.append(node('summary',champion.name+' · 스킬 설명 '+champion.facts.length+'개'));
   const state=champion.patch_status;
   group.append(node('p','공식 자료 버전 '+champion.source_patch+' · '+(state==='MATCHING_ARCHIVE'?'입력한 경기 패치와 같은 버전 계열':state==='GAME_PATCH_MISMATCH'?'입력한 경기 패치와 다릅니다. 보관 자료로만 참고하세요.':'현재 경기 패치는 미확인입니다. 보관 자료로 참고하세요.')));
   for(const fact of champion.facts){
    const item=node('div');item.className='official-fact';item.append(node('strong',window.SkillDisplay.factLabel(champion.champion,fact)),node('p',fact.text));
    try{const url=new URL(fact.source.url);if(url.protocol==='https:'&&url.hostname==='ddragon.leagueoflegends.com'){const link=node('a','공식 원문');link.href=url.href;link.target='_blank';link.rel='noopener noreferrer';item.append(link);}}catch{}
    group.append(item);
   }
   host.append(group);
  }
  if(!data.champions?.length)host.append(node('p','선택한 챔피언의 확인된 한국어 자료가 아직 없습니다. 근거 없는 설명으로 채우지 않습니다.'));
  if(data.unavailable?.length)host.append(node('p','일부 챔피언의 자료는 아직 확인하지 못했습니다.'));
 }
 window.OfficialReference=Object.freeze({render});
})();

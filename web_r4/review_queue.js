'use strict';
(()=>{
 const $=id=>document.getElementById(id),prefix='/dev/v1/pregame';
 sessionStorage.removeItem('pregame-token');
 let token=sessionStorage.getItem('lol-coach-dev-token')||'',queue=null,current=null,busy=false,epoch=0,selectionIndex=0,page=0,laterPage=0;
 const node=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
 const notice=text=>{$('rq-notice').textContent=text;};
 async function api(path,method='GET',body){const r=await fetch(path,{method,mode:'same-origin',headers:{Authorization:'Bearer '+token,...(body===undefined?{}:{'Content-Type':'application/json'})},...(body===undefined?{}:{body:JSON.stringify(body)})});const data=await r.json();if(!r.ok){const e=new Error(data.error_code||'요청 실패');e.status=r.status;throw e;}return data;}
 function controls(){for(const b of document.querySelectorAll('.decisions button'))b.disabled=busy||!current;$('rq-previous').disabled=busy||(($('rq-show-later').checked?queue?.deferred_candidates:queue?.candidates)?.length||0)<2;$('rq-next').disabled=$('rq-previous').disabled;const paging=queue?.pagination;const deferred=$('rq-show-later').checked;const activePage=deferred?laterPage:page;const pages=deferred?paging?.later_pages:paging?.ready_pages;$('rq-page-previous').disabled=busy||activePage<=0;$('rq-page-next').disabled=busy||activePage+1>=(pages||0);const p=current?.proposal;$('rq-approve').disabled=busy||!p;$('rq-reject').disabled=busy||!p;$('rq-edit-approve').disabled=busy||!p;$('rq-prepare').hidden=!!p;}
 function render(){
  const paging=queue.pagination;const deferred=$('rq-show-later').checked;const activePage=deferred?laterPage:page;const pages=deferred?paging?.later_pages:paging?.ready_pages;$('rq-page-position').textContent=pages?(activePage+1)+' / '+pages+' 묶음':'';const p=queue.progress;$('rq-progress').textContent=`검토 대기 ${p.ready} · 나중에 ${p.deferred} · 승인 ${p.reviewed} · 거절 ${p.rejected}`;
  $('rq-coverage').textContent=`Golden10 예시 · 5개 포지션 카드 ${p.example_card_filled}/${p.example_card_total} · 경기 패치 미확인: 적용 여부는 조건부입니다.`;
  const rows=$('rq-show-later').checked?queue.deferred_candidates:queue.candidates;selectionIndex=rows.length?((selectionIndex%rows.length)+rows.length)%rows.length:0;current=rows[selectionIndex]||null;$('rq-position').textContent=rows.length?(selectionIndex+1)+' / '+rows.length+' (현재 불러온 후보)':'';$('rq-previous').disabled=busy||rows.length<2;$('rq-next').disabled=busy||rows.length<2;$('rq-card').hidden=!current;$('rq-empty').hidden=!!current;$('rq-card').dataset.version=current?.selected_version||'';controls();if(!current)return;
  $('rq-priority').textContent=current.priority.reason+' · 관측 빈도 '+current.priority.observed_frequency;
  $('rq-claim').textContent=current.claim;$('rq-version').textContent='조회 버전 '+current.selected_version+' · '+(current.proposal?.review_state||'아직 저장하지 않은 후보');
  $('rq-conditions').replaceChildren();for(const [key,value] of Object.entries(current.conditions))$('rq-conditions').append(node('p',({patches:'경기 패치',applicability:'적용 범위',required_fields:'필수 확인값',predicates:'구조화 조건',counterconditions:'반대 조건',stop_conditions:'중단 조건',source_conditions:'출처에 기록된 상황 · 실행 조건 아님'}[key]||key)+': '+JSON.stringify(key==='required_fields'?value.filter(v=>!v.startsWith('EXECUTABLE_')):value)));
  $('rq-patch').textContent='경기 적용 패치: '+current.patch_range+' · 정적 출처 패치와 경기 패치는 별도입니다.';
  $('rq-sources').replaceChildren();for(const s of current.sources){const div=node('div');if(s.url){const a=node('a',s.title);a.href=s.url;a.target='_blank';a.rel='noopener noreferrer';div.append(a);}else div.append(node('p',s.title));div.append(node('p','출처 패치 '+(s.patch||'UNKNOWN')+' · '+s.locator),node('blockquote',s.excerpt||'원문 발췌 미확인: 공개 출처 링크에서 확인하세요.'));$('rq-sources').append(div);}if(!current.sources.length)$('rq-sources').append(node('p','구조화 출처 미확인'));
  $('rq-counterexamples').replaceChildren(...current.counterexamples.map(t=>node('li',t)));
  $('rq-statistics').replaceChildren(node('p',current.statistics.status==='UNKNOWN'?'이 주장과 비교할 표본은 미확인입니다.':'관측된 자원 차이의 기술적 비교입니다.'));
  for(const c of current.statistics.comparisons){$('rq-statistics').append(node('p',`${c.champion} · ${c.position} · ${c.patch} · ${c.tier} · ${c.comparison} · ${c.unit} · ${c.sample_kind}`));const table=node('table');const head=node('tr');for(const label of ['분','n','평균','95% CI'])head.append(node('th',label));table.append(head);for(const p of c.points){const row=node('tr');for(const value of [p.minute,p.n,p.mean,p.ci95?`${p.ci95.low} ~ ${p.ci95.high}`:'UNKNOWN'])row.append(node('td',String(value)));table.append(row);}$('rq-statistics').append(table);}
  for(const text of current.statistics.limitations)$('rq-statistics').append(node('p',text));$('rq-preview').textContent=current.preview.text;$('rq-preview-reasons').textContent='검토 미완료 · 실행 적용 전 미리보기 · '+current.preview.reasons.join(', ');
  $('rq-editor').open=false;$('rq-edit-claim').value=current.claim;$('rq-edit-patch').value=current.patch_range==='UNKNOWN'?'':current.patch_range;
  $('rq-scope').replaceChildren();for(const [key,value] of Object.entries(current.proposal?.applicability||current.conditions.applicability)){const label=node('label',key);const input=node('input');input.id='rq-scope-'+key;input.value=value;input.disabled=!!current.spec;label.append(input);$('rq-scope').append(label);}
 }
 async function refresh(){const mark=++epoch;const received=page||laterPage?await api(prefix+'/review-queue/page','POST',{page,later_page:laterPage}):await api(prefix+'/review-queue');if(mark!==epoch)return;queue=received;const paging=queue.pagination;if(paging&&(page>0&&page>=paging.ready_pages||laterPage>0&&laterPage>=paging.later_pages)){page=Math.max(0,Math.min(page,paging.ready_pages-1));laterPage=Math.max(0,Math.min(laterPage,paging.later_pages-1));return refresh();}render();$('rq-auth').hidden=true;$('rq-workspace').hidden=false;}
 function scope(){return Object.fromEntries(['champion','role','matchup','level','context'].map(k=>[k,$('rq-scope-'+k).value.trim()]));}
 async function action(event,kind){
  if(!event.isTrusted||!navigator.userActivation.isActive||busy||!current||event.currentTarget.disabled)return;
  const selected=current,mark=epoch;const claim=$('rq-edit-claim').value.trim();const patch=$('rq-edit-patch').value.trim();const applicability=scope();
  if(['approve','edit'].includes(kind)&&(!patch||[patch,...Object.values(applicability)].some(v=>!v||['UNKNOWN','미확인'].includes(v.toUpperCase())))){notice('승인하려면 확인한 경기 패치와 모든 적용 조건을 입력하세요.');$('rq-editor').open=true;return;}
  if(kind==='approve'&&(claim!==selected.claim||patch!==selected.patch_range||Object.entries(applicability).some(([k,v])=>v!==selected.proposal.applicability[k]))){notice('변경한 내용은 수정 후 승인 버튼으로 새 버전을 저장하세요.');return;}
  if(['approve','reject','edit'].includes(kind)&&!confirm('조회 버전 '+selected.selected_version+'을 '+(kind==='reject'?'거절':'승인')+'할까요?'))return;
  busy=true;controls();notice('저장 중…');
  try{
   if(kind==='later'){await api(prefix+'/review-queue/later','POST',{candidate_id:selected.candidate_id,selected_version:selected.selected_version});if($('rq-show-later').checked)selectionIndex++;}
   else if(kind==='prepare')await api(prefix+'/candidates','POST',{spec:selected.spec});
   else{
    let p=selected.proposal;
    if(kind==='edit'){
     const latest=await api('/dev/v1/knowledge/proposals/'+p.rule_id);if(latest.version!==selected.selected_version)throw new Error('REVISION_CONFLICT');
     if(selected.spec){const spec=structuredClone(selected.spec);spec.output.text=claim;spec.patches=patch.split(',').map(v=>v.trim()).filter(Boolean);const saved=await api(prefix+'/candidates','POST',{spec,rule_id:p.rule_id,expected_version:selected.selected_version});p=saved.proposal;}
     else{const fields=['claim','mechanism','author','required_fields','counterexamples','limitations','patch_range','applicability'];const rule=Object.fromEntries(fields.map(k=>[k,p[k]]));rule.claim=claim;rule.patch_range=patch;rule.applicability=applicability;const source=Object.fromEntries(['resource_id','anchor','note_revision'].map(k=>[k,p.source_refs[0][k]]));p=await api('/dev/v1/knowledge/proposals','POST',{rule,source,rule_id:p.rule_id,expected_version:p.version});}
    }
    await api('/dev/v1/knowledge/proposals/'+p.rule_id+'/decisions','POST',{selected_version:p.version,expected_version:p.version,decision:kind==='reject'?'REJECTED':'REVIEWED',patch_range:kind==='edit'?p.patch_range:selected.patch_range,applicability:kind==='edit'?p.applicability:selected.proposal.applicability});
   }
   if(mark!==epoch)return;await refresh();notice(kind==='later'?'나중에 볼 후보로 보존했습니다.':kind==='prepare'?'검토 후보를 저장했습니다. 근거 확인 후 직접 결정하세요.':'결정을 저장하고 다음 후보를 불러왔습니다.');
  }catch(e){if(mark===epoch){notice(e.message==='REVISION_CONFLICT'?'후보 버전이 바뀌었습니다. 최신 버전을 다시 확인하세요.':e.message);if(e.status===409)await refresh().catch(()=>{});}}
  finally{busy=false;controls();}
 }
 for(const [id,kind] of [['rq-approve','approve'],['rq-reject','reject'],['rq-edit-approve','edit'],['rq-later','later'],['rq-prepare','prepare']])$(id).addEventListener('click',e=>action(e,kind));
 $('rq-login').addEventListener('submit',async e=>{e.preventDefault();token=$('rq-token').value.trim();try{await refresh();sessionStorage.setItem('lol-coach-dev-token',token);$('rq-token').value='';notice('개인 작업실에 연결했습니다.');}catch(err){notice(err.message);}});
 $('rq-refresh').addEventListener('click',()=>{if(!busy)refresh().catch(e=>notice(e.message));});$('rq-show-later').addEventListener('change',()=>{if(!busy){selectionIndex=0;render();}});for(const [id,offset] of [['rq-previous',-1],['rq-next',1]])$(id).addEventListener('click',()=>{if(!busy&&queue){selectionIndex+=offset;render();}});
 for(const [id,offset] of [['rq-page-previous',-1],['rq-page-next',1]])$(id).addEventListener('click',()=>{if(!busy&&queue){if($('rq-show-later').checked)laterPage=Math.max(0,laterPage+offset);else page=Math.max(0,page+offset);selectionIndex=0;refresh().catch(e=>notice(e.message));}});
 $('rq-export').addEventListener('click',()=>{$('rq-export-panel').hidden=false;$('rq-export-text').value=queue?.export_text||'';});
 $('rq-download').addEventListener('click',()=>{const url=URL.createObjectURL(new Blob([$('rq-export-text').value],{type:'text/plain;charset=utf-8'}));const a=node('a');a.href=url;a.download='review-top20.txt';a.click();setTimeout(()=>URL.revokeObjectURL(url),0);});
 $('rq-logout').addEventListener('click',()=>{epoch++;token='';queue=current=null;sessionStorage.removeItem('lol-coach-dev-token');sessionStorage.removeItem('pregame-token');$('rq-workspace').hidden=true;$('rq-auth').hidden=false;$('rq-claim').textContent='';$('rq-export-text').value='';$('rq-sources').replaceChildren();notice('연결을 해제했습니다.');});
 if(token)refresh().catch(e=>notice(e.message));
})();

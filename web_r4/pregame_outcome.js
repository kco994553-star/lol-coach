'use strict';
(() => {
  const node=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=String(text);return n;};
  const finite=v=>typeof v==='number'&&Number.isFinite(v);
  const percent=v=>String(Math.round(v*10000)/100)+'%';
  function render(parent,response,options={}){
    parent.replaceChildren();
    parent.append(node('p','종료 시간별 승리 비율 · 보조 기술 통계'));
    parent.append(node('p','종료 시간이 같은 수집 경기의 결과입니다. 진행 중 경기의 강함·단계·전술을 뜻하지 않습니다. 95% 신뢰구간은 항상 불확실성을 포함하며, n=1에서 계산 가능해도 충분한 표본을 뜻하지 않습니다.'));
    const view=response?.view,source=view?.source,kind=source?.sample_kind;
    const allowed=kind==='REAL'||kind==='SYNTHETIC'&&options.testMode===true&&response?.test_mode===true;
    if(!allowed||view?.status!=='KNOWN'){
      parent.append(node('p','결과 통계 UNKNOWN · '+(!allowed?'실제 자료 또는 명시적으로 허용된 TEST 자료 필요':(view.reasons || ['표본 미확인']).join(', '))));return;
    }
    if(kind==='SYNTHETIC')parent.append(node('p','TEST · 합성 표본 · 실제 경기 결과 검증 아님'));
    const points=(view.points || []).filter(p=>Number.isInteger(p.minute)&&p.minute>=0&&Number.isInteger(p.n)&&p.n>=1&&Number.isInteger(p.wins)&&p.wins>=0&&p.wins<=p.n&&finite(p.win_rate)&&p.win_rate>=0&&p.win_rate<=1&&finite(p.ci95?.low)&&finite(p.ci95?.high)&&p.ci95.low>=0&&p.ci95.high<=1&&p.ci95.low<=p.ci95.high);
    if(!points.length){parent.append(node('p','결과 통계 UNKNOWN · 유효한 종료 구간 표본 없음'));return;}
    const table=node('table');table.style.fontSize='12px';table.style.borderSpacing='10px 6px';table.className='pg-outcome-table';table.append(node('caption','경기 종료 시점 [분, 다음 분) · Wilson 95% 신뢰구간'));
    const head=node('thead'),header=node('tr');for(const label of ['종료 구간','비교 집단','경기 수','승리 수','승리 비율','Wilson 95% CI']){const th=node('th',label);th.scope='col';header.append(th);}head.append(header);table.append(head);
    const body=node('tbody');for(const p of points){const row=node('tr');for(const value of [p.minute+'–'+(p.minute+1)+'분',p.comparison==='MATCHUP'?'동일 상대 '+(p.opponent_champion || 'UNKNOWN'):'챔피언·포지션 / 수집 표본의 상대 전체','n='+p.n,'승리 '+p.wins,percent(p.win_rate),percent(p.ci95.low)+'–'+percent(p.ci95.high)])row.append(node('td',value));body.append(row);}table.append(body);const scroll=node('div');scroll.setAttribute('role','region');scroll.setAttribute('aria-label','경기 종료 시간별 결과 표 · 좌우로 스크롤 가능');scroll.tabIndex=0;scroll.style.overflowX='auto';scroll.style.maxWidth='100%';scroll.append(table);parent.append(scroll);
    const detail=node('details');detail.append(node('summary','결과 통계 출처·표본 한계'));
    detail.append(node('p','데이터 버전 '+(view.schema_version || 'UNKNOWN')+' · digest '+(view.dataset_digest || 'UNKNOWN')));
    for(const [field,label] of [['provider','제공자'],['platform','플랫폼'],['regional','지역'],['queue_id','큐'],['map_id','맵'],['endpoints','공식 API 출처'],['sample_kind','자료 종류'],['patch','패치'],['tier','티어'],['window_start','수집 시작'],['window_end','수집 끝'],['retrieved_at','수집 시각'],['formula_version','계산식'],['duration_bin_policy','종료 구간 정책'],['mirror_policy','미러 제외 정책'],['result_policy','결과 검증 정책']]){const value=source[field];detail.append(node('p',label+' · '+(value===undefined?'UNKNOWN':value!==null&&typeof value==='object'?JSON.stringify(value):value)));}
    detail.append(node('p','집계 표본 · 실제 경기 '+(view.samples?.real_matches ?? 'UNKNOWN')+' · 합성 경기 '+(view.samples?.synthetic_matches ?? 'UNKNOWN')));
    for(const limitation of source.limitations || [])detail.append(node('p',limitation));
    detail.append(node('p','표본 선택·독립성·지역·시간 범위 편향과 조기 종료·리메이크 분류는 검증되지 않았습니다.'));parent.append(detail);
  }
  window.PregameOutcome={render};
})();

'use strict';
(() => {
  const namespace='http://www.w3.org/2000/svg';
  const metrics={gold_delta:'골드 차이',xp_delta:'경험치 차이',cs_delta:'CS 차이'};
  const element=(tag,text,className)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=String(text);if(className)n.className=className;return n;};
  const svgElement=(tag,attributes,text)=>{const n=document.createElementNS(namespace,tag);for(const [key,value] of Object.entries(attributes || {}))n.setAttribute(key,String(value));if(text!==undefined)n.textContent=String(text);return n;};
  const finite=value=>typeof value==='number' && Number.isFinite(value);
  const number=value=>finite(value)?String(Math.round(value*100)/100):'UNKNOWN';
  const comparison=value=>value==='MATCHUP'?'동일 상대 매치업':value==='ROLE_POPULATION'?'동일 포지션 전체':'비교 집단 UNKNOWN';
  const state=point=>point.ci95.low>0?'강함':point.ci95.high<0?'약함':'비슷함';
  function provenance(parent,view,source){
    const details=element('details',undefined,'pg-power-source');details.append(element('summary','통계 출처·정밀도·표본 한계'));
    details.append(element('p','데이터 버전 '+(view.schema_version || view.dataset_version || 'UNKNOWN')+' · digest '+(view.dataset_digest || 'UNKNOWN'),'small'));
    for(const [field,label] of [['provider','제공자'],['sample_kind','자료 종류'],['patch','패치'],['tier','티어'],['retrieved_at','수집 시각'],['formula_version','계산식 버전'],['precision_policy','정밀도 정책']]){
      const value=source[field];details.append(element('p',label+' · '+(value===undefined?'UNKNOWN':typeof value==='object'?JSON.stringify(value):value),'small'));
    }
    details.append(element('p','집계 표본 · 실제 경기 '+(view.samples?.real_matches ?? 'UNKNOWN')+' · 합성 경기 '+(view.samples?.synthetic_matches ?? 'UNKNOWN'),'small'));
    details.append(element('p','정밀도 기준은 추정 불확실성을 제한하기 위한 운영 정책입니다. 검증된 전술 판단 기준이 아닙니다.','small'));
    for(const limitation of source.limitations || [])details.append(element('p',limitation,'small'));
    details.append(element('p','표본 선택·지역·시간 범위 편향과 경기 간 독립성은 검증되지 않았습니다.','small'));parent.append(details);
  }
  function graph(parent,view,opponent,options){
    const points=Array.isArray(view.points)?view.points:[],metric=view.metric || 'gold_delta';
    const shown=points.filter(p=>p.visible===true && finite(p.minute) && finite(p.mean) && finite(p.ci95?.low) && finite(p.ci95?.high));
    const heading=element('p',(metrics[metric] || metric)+' · '+(options.champion || '내 챔피언')+(options.opponent?' / '+options.opponent:''),'pg-power-heading');parent.append(heading);
    parent.append(element('p','강함: 95% CI 전체가 0 위 · 약함: 전체가 0 아래 · 비슷함: 0 포함','small'));
    if(!shown.length)parent.append(element('p','통계 UNKNOWN · 정밀도 기준을 충족한 구간이 없습니다.','small'));
    else{
      const width=options.compact?420:640,height=options.compact?240:310,left=55,right=18,top=24,bottom=85;
      const markers=[...(view.markers || []),...(opponent?.markers || [])];
      const minutes=[...points.map(p=>p.minute),...markers.flatMap(m=>[m.q1_minute,m.median_minute,m.q3_minute])].filter(finite);
      const minMinute=Math.min(0,...minutes),maxMinute=Math.max(1,...minutes),maxY=Math.max(1,...shown.flatMap(p=>[Math.abs(p.ci95.low),Math.abs(p.ci95.high)]));
      const x=t=>left+(t-minMinute)/(maxMinute-minMinute)*(width-left-right),y=v=>top+(maxY-v)/(maxY*2)*(height-top-bottom);
      const svg=svgElement('svg',{viewBox:'0 0 '+width+' '+height,role:'img','aria-label':(metrics[metric] || metric)+' 시간별 평균과 95% 신뢰구간',class:'pg-power-svg'});
      svg.append(svgElement('title',{},'분별 '+(metrics[metric] || metric)+' · 음영 95% 신뢰구간 · 0 기준선'));
      svg.append(svgElement('line',{x1:left,x2:width-right,y1:y(0),y2:y(0),class:'pg-power-zero'}));
      for(const value of [-maxY,0,maxY])svg.append(svgElement('text',{x:left-6,y:y(value)+4,'text-anchor':'end',class:'pg-power-axis'},number(value)));
      svg.append(svgElement('text',{x:left,y:14,class:'pg-power-axis'},metrics[metric] || metric));
      for(const minute of [...new Set([minMinute,Math.round((minMinute+maxMinute)/2),maxMinute])])svg.append(svgElement('text',{x:x(minute),y:height-bottom+19,'text-anchor':'middle',class:'pg-power-axis'},number(minute)+'분'));
      let segments=[],segment=[];
      for(const point of points){if(!shown.includes(point)){if(segment.length)segments.push(segment);segment=[];continue;}if(segment.length && point.minute!==segment[segment.length-1].minute+1){segments.push(segment);segment=[];}segment.push(point);}if(segment.length)segments.push(segment);
      for(const values of segments){if(values.length>1){
        const area=[...values.map(p=>x(p.minute)+','+y(p.ci95.high)),...values.slice().reverse().map(p=>x(p.minute)+','+y(p.ci95.low))].join(' ');
        svg.append(svgElement('polygon',{points:area,class:'pg-power-ci'}));
        svg.append(svgElement('polyline',{points:values.map(p=>x(p.minute)+','+y(p.mean)).join(' '),class:'pg-power-line'}));
      }
      for(const p of values){const title=number(p.minute)+'분 · n='+p.n+' · 평균 '+number(p.mean)+' · 95% CI ['+number(p.ci95.low)+', '+number(p.ci95.high)+'] · '+state(p)+' · '+comparison(p.comparison);
        const circle=svgElement('circle',{cx:x(p.minute),cy:y(p.mean),r:4,tabindex:0,role:'img','aria-label':title,class:'pg-power-point'});circle.append(svgElement('title',{},title));svg.append(circle);
      }}
      for(const [owner,data] of [['own',view],['opponent',opponent]])for(const m of data?.markers || []){
        if(![m.q1_minute,m.median_minute,m.q3_minute].every(finite))continue;
        const yy=height-(owner==='own'?42:22),name=m.kind==='LEVEL'?'레벨 '+(m.level ?? 'UNKNOWN'):'완성 아이템 '+(m.item_order ?? 'UNKNOWN')+' · '+(m.item_id ?? 'UNKNOWN');
        const label=(owner==='own'?'내 챔피언':'상대 챔피언')+' · '+name+' · 중앙값 '+number(m.median_minute)+'분 · IQR '+number(m.q1_minute)+'–'+number(m.q3_minute)+'분 · n='+m.n+' · 비인과 기술 통계';
        const group=svgElement('g',{'data-owner':owner,tabindex:0,role:'img','aria-label':label,class:'pg-power-marker '+owner});group.append(svgElement('title',{},label),svgElement('line',{x1:x(m.q1_minute),x2:x(m.q3_minute),y1:yy,y2:yy,class:'pg-power-iqr'}),svgElement('line',{x1:x(m.median_minute),x2:x(m.median_minute),y1:yy-6,y2:yy+6}));svg.append(group);
      }
      parent.append(svg);
    }
    const data=element('details',undefined,'pg-power-points');data.append(element('summary','분별 표본·비교 집단·누락 구간'));
    for(const p of points){const good=shown.includes(p);data.append(element('p',number(p.minute)+'분 · n='+p.n+' · '+comparison(p.comparison)+' · '+(good?'평균 '+number(p.mean)+' · 95% CI ['+number(p.ci95.low)+', '+number(p.ci95.high)+'] · '+state(p):'UNKNOWN · '+(p.omission_reason || '정밀도 미충족')),'small'));}parent.append(data);
    for(const [owner,value] of [['own',view],['opponent',opponent]])for(const m of value?.markers || [])parent.append(element('p',(owner==='own'?'내 챔피언':'상대 챔피언')+' · '+(m.kind==='LEVEL'?'레벨 '+(m.level ?? 'UNKNOWN'):'완성 아이템 '+(m.item_order ?? 'UNKNOWN')+' · '+(m.item_id ?? 'UNKNOWN'))+' · 중앙값 '+number(m.median_minute)+'분 · IQR '+number(m.q1_minute)+'–'+number(m.q3_minute)+'분 · n='+m.n+' · 비인과 기술 통계','small pg-power-marker-label'));
    parent.append(element('p','골드·경험치·CS 차이는 전투력 전체가 아닙니다. 레벨·아이템 시점은 비인과 기술 통계이며 서로 다른 빌드를 비교할 수 있습니다. 관측 프레임 사이의 실제 발생 시점은 확정할 수 없습니다.','small'));
  }
  function render(parent,response,options={}){
    parent.replaceChildren();const view=response?.view,source=view?.source || {},kind=source.sample_kind;
    if(!view || view.status!=='KNOWN'){parent.append(element('p','통계 UNKNOWN · '+((view?.reasons || []).join(', ') || view?.reason || '자료가 없습니다.'),'small'));if(kind==='REAL' || (kind==='SYNTHETIC' && options.testMode===true && response.test_mode===true)){if(kind==='SYNTHETIC')parent.append(element('p','TEST · SYNTHETIC 합성 통계 · 실제 경기 자료 아님','pg-power-test'));provenance(parent,view,source);}return;}
    const synthetic=kind==='SYNTHETIC';
    if(kind!=='REAL' && !(synthetic && options.testMode===true && response.test_mode===true)){parent.append(element('p','통계 UNKNOWN · 실제 자료를 확인할 수 없습니다.','small'));return;}
    const opponent=response.opponent_view;
    const safeOpponent=opponent && (opponent.source?.sample_kind==='REAL' || (opponent.source?.sample_kind==='SYNTHETIC' && options.testMode===true && response.test_mode===true))?opponent:null;
    if(synthetic)parent.append(element('p','TEST · SYNTHETIC 합성 통계 · 실제 경기 자료 아님','pg-power-test'));
    const label=element('label','표시 통계'),select=element('select',undefined,'pg-power-metric');select.setAttribute('aria-label','표시 통계');
    for(const [key,name] of Object.entries(metrics)){const option=element('option',name);option.value=key;select.append(option);}select.value='gold_delta';label.append(select);parent.append(label);
    const body=element('div',undefined,'pg-power-plot');parent.append(body);
    function draw(){
      const metric=select.value;let points=(view.points || []).filter(p=>(p.metric || view.metric || 'gold_delta')===metric);
      for(const reason of view.reasons || []){const match=/^INSUFFICIENT_AT_MINUTE:([0-9.]+):(.+)$/.exec(reason);if(match && match[2]===metric && !points.some(p=>p.minute===Number(match[1])))points.push({minute:Number(match[1]),n:'UNKNOWN',visible:false,omission_reason:reason,comparison:null});}
      points.sort((a,b)=>a.minute-b.minute);body.replaceChildren();graph(body,{...view,metric,points},safeOpponent,options);
    }
    select.addEventListener('change',draw);draw();provenance(parent,view,source);
  }
  window.PregamePower=Object.freeze({render});
})();

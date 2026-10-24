/* Export actual production output without editorial rewriting. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),web=path.join(root,'web_r4');
const E=require(path.join(web,'loading-engine.js')),P=require(path.join(web,'loading-presentation.js'));
const c=JSON.parse(fs.readFileSync(path.join(web,'loading-data.json')));
c.coaching_knowledge=JSON.parse(fs.readFileSync(path.join(web,'loading-knowledge.json')));
// Fixed role-diverse selection, not ranked or selected by output quality.
const picks=[['Caitlyn',0,'BOTTOM'],['Fiora',1,'TOP'],['Graves',1,'JUNGLE'],['Ahri',0,'MID'],['Lux',0,'SUPPORT']];
const samples=picks.map(([champion,preset,position])=>{
 const input={...E.exampleInput(c,preset),own_champion:champion,own_position:position};
 const report=E.analyze(input,c);
 return {name:c.champions[champion].name,input,view:P.project(report,{currentOnly:true}),delivery:report.coach.planboard.delivery};
});
const hashes=Object.fromEntries(fs.readdirSync(web).filter(f=>/^loading-.*\.(js|json)$/.test(f)).sort().map(f=>[f,crypto.createHash('sha256').update(fs.readFileSync(path.join(web,f))).digest('hex')]));
const output=path.resolve(process.argv[2]||path.join(root,'docs/gameplan-content/five-examples'));
fs.mkdirSync(output,{recursive:true});
fs.writeFileSync(path.join(output,'raw.json'),JSON.stringify({patch:c.source_patch,selection:'Fixed five roles; no quality ranking',source_sha256:hashes,samples},null,2)+'\n');
const lines=['# 현재 게임플랜 생성 예시 5개','',`데이터 패치: ${c.source_patch}. 현재 생성기 출력이며 문구를 교정하지 않았다. 다섯 포지션을 고정 선택했으며 품질이 좋은 사례만 선별하지 않았다. 실경기 검증 N=0.`, '', '이 문서는 비교표·단계별 제목/태그·행동 5개·코칭 본문을 그대로 추출한다. 펼치기 상세와 화면에 투영한 구조화 결과는 같은 폴더의 raw.json에 포함한다.',''];
const team=rows=>rows.map(x=>`${x.position}: ${c.champions[x.champion].name}`).join(' / ');
for(const [i,s] of samples.entries()){
 lines.push(`## ${i+1}. ${s.name} · ${s.input.own_position}`,'',`아군: ${team(s.input.allies)}`,'',`상대: ${team(s.input.enemies)}`,'',`입력: ${s.input.side}, ${s.input.opponent_mode}; 사용자 조건 추가 없음.`, '',s.view.hero_title,'',s.view.title,'','| 비교 | 아군 | 상대 |','|---|---|---|');
 for(const row of s.view.comparison)lines.push(`| ${row.label} | ${row.ours} | ${row.theirs} |`);
 lines.push('',...s.view.overall_commentary.flatMap(t=>[t,'']));
 for(const a of s.view.cards){lines.push(`### ${a.label}`,'',a.title,'',a.conditions.join(' · '),'');for(const [j,item]of a.actions.entries())lines.push(`${j+1}. **${item.label}** ${item.text}`);lines.push('',a.coaching_heading,'',...a.explanation.flatMap(t=>[t,'']));}
 lines.push('실전에서 기억할 질문 3개','',...s.view.remember.map(t=>'- '+t),'');
}
fs.writeFileSync(path.join(output,'examples.md'),lines.join('\n')+'\n');
console.log(JSON.stringify({output,samples:samples.map(s=>({name:s.name,titles:s.view.cards.map(a=>({phase:a.label,title:a.title,tags:a.conditions}))}))},null,2));

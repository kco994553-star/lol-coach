/* Deterministic, offline presentation draft generated from the production engine. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),web=path.join(root,'web_r4');
const E=require(path.join(web,'loading-engine.js')),P=require(path.join(web,'loading-presentation.js'));
const catalog=JSON.parse(fs.readFileSync(path.join(web,'loading-data.json')));
catalog.coaching_knowledge=JSON.parse(fs.readFileSync(path.join(web,'loading-knowledge.json')));
const sources=fs.readdirSync(web).filter(x=>/^loading-.*\.js$/.test(x)).concat(['loading-data.json','loading-knowledge.json']).sort();
const hashes=Object.fromEntries(sources.map(x=>[x,crypto.createHash('sha256').update(fs.readFileSync(path.join(web,x))).digest('hex')]));
const presets=[['Graves',1,'JUNGLE'],['Fiora',1,'TOP'],['Caitlyn',0,'BOTTOM']].map(([id,n,role])=>{
 const input=E.exampleInput(catalog,n);input.own_champion=id;input.own_position=role;
 const report=E.analyze(input,catalog);return {id,name:catalog.champions[id].name,input,view:P.project(report)};
});
const ids=[...new Set(presets.flatMap(p=>[...p.input.allies,...p.input.enemies].map(x=>x.champion)))];
const champions=Object.fromEntries(ids.map(id=>{const c=catalog.champions[id],p=c.portrait;return [id,{name:c.name,portrait:p,sheet:'data:image/png;base64,'+fs.readFileSync(path.join(web,p.sprite)).toString('base64')}];}));
const payload={version:1,kind:'gameplan-presentation-draft',patch:catalog.patch,source_sha256:hashes,presets,champions};
const template=fs.readFileSync(path.join(__dirname,'gameplan-preview.html'),'utf8');
const html=template.replace('__PAYLOAD__',JSON.stringify(payload).replace(/</g,'\\u003c'));
const out=path.resolve(process.argv[2]||path.join(root,'build/gameplan-preview.html'));
fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,html);
console.log(JSON.stringify({path:out,bytes:Buffer.byteLength(html),sha256:crypto.createHash('sha256').update(html).digest('hex'),presets:presets.map(p=>p.id)}));

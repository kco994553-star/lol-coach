'use strict';
// Synthetic DOM and deferred Files; actual UTF-8 codecs plus existing Python
// diagnostic adapters. This is source-byte validation, never player gold.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const crypto=require('node:crypto'),{spawnSync}=require('node:child_process');
const root=path.resolve(__dirname,'..');
const sourcePath=path.resolve(process.argv[3]||path.join(root,'web_r4/research.js'));
const source=fs.readFileSync(sourcePath,'utf8');
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const bom=Buffer.from([239,187,191]);
const transcript=Buffer.from('YouTube transcript\nVideo ID: abcdefghijk\nLanguage: ko\nCaptions: manual\n[00:01] wave 한글\n');
const cases={
  bom_json:Buffer.concat([bom,Buffer.from('{"note":"한글"}')]),
  bom_transcript:Buffer.concat([bom,transcript]),
  valid:Buffer.from('{"note":"한글 😀 �"}'),
  invalid:Buffer.from([123,34,110,111,116,101,34,58,34,255,34,125]),
  truncated:Buffer.from([123,34,110,111,116,101,34,58,34,226,130,34,125]),
  empty:Buffer.from('{}')
};
function file(name,bytes){let done;const gate=new Promise(r=>{done=r;});return {
  file:{name,size:bytes.length,text:async()=>{await gate;return new TextDecoder().decode(bytes);},
    arrayBuffer:async()=>{await gate;return Uint8Array.from(bytes).buffer;}},finish:()=>done()};}
function harness(){const elements=new Map(),posts=[];let resource;
 function el(id){if(!elements.has(id))elements.set(id,{value:'',files:[],disabled:false,hidden:false,textContent:'',dataset:{},listeners:{},addEventListener(k,f){this.listeners[k]=f;},replaceChildren(){},append(){}});return elements.get(id);}
 const context=vm.createContext({$:el,TextDecoder,document:{querySelector:()=>el('filter-label')},node:()=>el(Symbol()),limits:{body_bytes:1000000},confirm:()=>true,error(){},console,
 api:async(route,method,body)=>{
   if(method==='POST'){
    posts.push({title:body.title,submitted_sha256:hash(Buffer.from(body.raw_text))});
    const python=spawnSync(process.env.PYTHON||'python3',['-c',"import sys,json; from coach_intake.audit import inspect; from coach_intake.video import index_transcript; raw=sys.stdin.buffer.read(); print(json.dumps(index_transcript(raw,'abcdefghijk') if sys.argv[1]=='transcript' else inspect(raw)))",body.source_type],{input:Buffer.from(body.raw_text),cwd:root});
    if(python.status!==0)throw Error('Diagnostic adapter rejected input');
    const report=JSON.parse(python.stdout);posts.at(-1).report_sha256=report.raw_sha256||report.transcript_sha256;
    resource={id:'test',title:body.title,kind:body.source_type==='transcript'?'VIDEO':'RAW_DIAGNOSTIC',report};return resource;
   }
   if(route==='/research')return [];
   if(route.endsWith('/notes/overview'))return {anchor:'overview',revision:0,known:'',intention:'',alternative:'',outcome:''};
   if(route==='/research/test')return resource;
   throw Error('Unexpected test route');
 }});
 vm.runInContext(source,context,{filename:'web_r4/research.js'});
 const evalCode=x=>vm.runInContext(x,context);
 el('r-kind').value='raw_json';el('r-video-id').value='abcdefghijk';
 evalCode("rResource={id:'old',title:'old'};rNote={anchor:'overview',revision:3};rDirty=true;rEdit=2");
 el('r-known').value='미저장 원본 노트';el('r-title').textContent='old';
 return {el,posts,select(f){el('r-file').files=f?[f]:[];return el('r-file').listeners.change();},
 state(){return JSON.parse(evalCode("JSON.stringify({id:rResource&&rResource.id,note:rNote,dirty:rDirty,edit:rEdit,known:$('r-known').value,title:$('r-title').textContent,notice:$('r-notice').textContent})"));}};
}
async function run(){const results=[];
 async function check(id,task){try{const actual=await task();results.push({id,passed:Object.values(actual.checks).every(x=>x===true),...actual});}catch(e){results.push({id,passed:false,error:e.message});}}
 for(const [id,key,kind] of [['RESEARCH-BOM-JSON','bom_json','raw_json'],['RESEARCH-BOM-TRANSCRIPT','bom_transcript','transcript'],['RESEARCH-VALID-MULTIBYTE','valid','raw_json']])await check(id,async()=>{
  const h=harness(),f=file(key,cases[key]);h.el('r-kind').value=kind;const p=h.select(f.file);f.finish();await p;
  const post=h.posts[0];return {checks:{single_post:h.posts.length===1,original_submission_hash:post?.submitted_sha256===hash(cases[key]),original_adapter_hash:post?.report_sha256===hash(cases[key])},original_sha256:hash(cases[key]),post};});
 for(const key of ['invalid','truncated'])await check('RESEARCH-REJECT-'+key.toUpperCase(),async()=>{
  const h=harness(),before=h.state(),f=file(key,cases[key]);const p=h.select(f.file);f.finish();await p;const after=h.state();
  return {checks:{no_post:h.posts.length===0,resource_preserved:after.id===before.id,dirty_note_preserved:after.known===before.known&&after.dirty===true&&after.note.revision===3,explicit_error:after.notice.includes('UTF-8')},before,after};});
 for(const order of ['A-FIRST','B-FIRST'])await check('RESEARCH-STALE-INVALID-'+order,async()=>{
  const h=harness(),a=file('old-invalid',cases.invalid),b=file('new-valid',cases.valid);const pa=h.select(a.file),pb=h.select(b.file);
  if(order==='A-FIRST'){a.finish();await pa;b.finish();await pb;}else{b.finish();await pb;a.finish();await pa;}
  const state=h.state();return {checks:{only_latest_post:h.posts.length===1&&h.posts[0].title==='new-valid',latest_display:state.title==='new-valid',no_stale_error:!state.notice.includes('처리하지 못했습니다')},posts:h.posts,state};});
 await check('RESEARCH-CLEARED-INVALID',async()=>{const h=harness(),before=h.state(),a=file('cleared',cases.invalid),p=h.select(a.file);await h.select(null);a.finish();await p;const after=h.state();return {checks:{no_post:h.posts.length===0,no_error:after.notice==='',old_note:after.known===before.known&&after.dirty===true},after};});
 await check('R6-LATEST-FILE-A-FIRST',async()=>{const h=harness(),a=file('A.json',cases.empty),b=file('B.json',cases.empty),pa=h.select(a.file),pb=h.select(b.file);a.finish();await pa;const postsAfterA=[...h.posts];b.finish();await pb;return {checks:{posts_after_a_empty:postsAfterA.length===0,only_b:h.posts.length===1&&h.posts[0].title==='B.json',display_b:h.state().title==='B.json',no_error:!h.state().notice.includes('처리하지 못했습니다')},postsAfterA,posts:h.posts};});
 const oldCase=results.find(r=>r.id==='R6-LATEST-FILE-A-FIRST');
 return {scope:'Source UTF-8 byte preservation and stale-read guards; synthetic data only',verifier:'Node VM DOM stub with native TextDecoder and unchanged Python adapters; not browser',executed_at:new Date().toISOString(),node_version:process.version,source_sha256:hash(source),test_sha256:hash(fs.readFileSync(__filename)),fixture_sha256:Object.fromEntries(Object.entries(cases).map(([k,b])=>[k,hash(b)])),passed:results.filter(r=>r.passed).length,total:results.length,results,fixed_result:{passed:oldCase.passed,actual:oldCase}};
}
if(process.argv[2]==='--run'){run().then(r=>{console.log(JSON.stringify(r));process.exitCode=r.passed===r.total?0:1;}).catch(e=>{console.error(e);process.exitCode=1;});}
else {const dest=path.resolve(process.argv[2]||path.join(root,'evidence/mvp/research-bytes-after.json'));const child=spawnSync(process.execPath,[__filename,'--run',sourcePath],{encoding:'utf8',timeout:30000});let result;try{result=JSON.parse(child.stdout);}catch{result={source_sha256:hash(source),runner_error:'No valid child receipt',results:[]};}result.process={exit_code:child.status,signal:child.signal,stdout:child.stdout,stderr:child.stderr};fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,JSON.stringify(result,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({passed:result.passed,total:result.total,exit_code:child.status,results:result.results.map(r=>({id:r.id,passed:r.passed}))}));process.exitCode=child.status===0?0:1;}

'use strict';
// Synthetic late 401 isolates error ownership; it does not claim real token expiry.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),source=fs.readFileSync(path.resolve(process.argv[3]||path.join(root,'web_r4/knowledge.js')),'utf8');
const hash=value=>crypto.createHash('sha256').update(value).digest('hex');
function deferred(){let resolve,reject;const promise=new Promise((yes,no)=>{resolve=yes;reject=no;});return {promise,resolve,reject};}
const record={schema_version:'knowledge-proposal.v1',rule_id:'1'.repeat(32),version:'c'.repeat(32),patch_range:'UNKNOWN',applicability:{champion:'UNKNOWN',role:'UNKNOWN',matchup:'UNKNOWN',level:'UNKNOWN',context:'UNKNOWN'},required_fields:['UNKNOWN'],claim:'old stored C',mechanism:'UNKNOWN',counterexamples:['UNKNOWN'],author:'synthetic test',limitations:['UNKNOWN'],source_refs:[{resource_id:'source3',anchor:'overview',note_revision:1}],review_state:'EXPLORATORY',coaching_enabled:false,supersedes:'b'.repeat(32)};
async function run(){const elements=new Map(),oldRead=deferred(),ready=deferred(),calls=[];let authClears=0,freshUnauthorized=false;
 function el(key){if(!elements.has(key))elements.set(key,{value:'',disabled:false,hidden:false,textContent:'',dataset:{},listeners:{},addEventListener(type,fn){this.listeners[type]=fn;},replaceChildren(){},append(){}});return elements.get(key);}
 const unauthorized=()=>{const error=new Error('synthetic expired request');error.status=401;return error;};
 const context=vm.createContext({$:el,node:()=>({dataset:{},addEventListener(){}}),document:{addEventListener(){}},confirm:()=>true,error(){authClears++;},rClear(){},rResource:{id:'source4'},rNote:{resource_id:'source4',anchor:'overview',revision:1},rDirty:false,
  api:async(route,method='GET')=>{calls.push({route,method});if(freshUnauthorized)throw unauthorized();
   if(route==='/research/source3'){ready.resolve();return oldRead.promise;}
   if(route==='/research/source4')return {id:'source4'};
   if(route==='/knowledge/proposals')return [record];
   if(route==='/knowledge/proposals/'+record.rule_id||route==='/knowledge/proposals/'+record.rule_id+'/versions/'+record.version)return record;
   throw Error('Unexpected synthetic service route '+route);
  }});
 vm.runInContext(source,context,{filename:'web_r4/knowledge.js'});
 vm.runInContext('kRecord='+JSON.stringify(record)+';kLatest=kRecord.version;kSource=kBoundSource(kRecord);kApplyRule(kRecord);kSourceLabel();kCurrentLabel()',context);
 const state=()=>JSON.parse(vm.runInContext('JSON.stringify({record:kRecord&&kRecord.version,source:kSource&&kSource.resource_id,claim:$("k-claim").value,dirty:kDirty,notice:$("k-notice").textContent})',context));
 const pending=vm.runInContext('kAfterSourceDeletion()',context);await ready.promise;
 vm.runInContext('kUseNote();$("k-claim").value="NEW-INDEPENDENT-DRAFT"',context);el('k-claim').listeners.input();const before=state();
 oldRead.reject(unauthorized());await pending;const after=state(),staleAuthClears=authClears;
 freshUnauthorized=true;await vm.runInContext('kAfterSourceDeletion()',context);const afterCurrent401=state();
 const checks={late_old_error_cannot_clear_new_draft:after.claim===before.claim&&after.source==='source4'&&after.dirty===true,
  late_old_error_cannot_reset_auth:staleAuthClears===0,late_old_error_cannot_replace_notice:after.notice===before.notice,
  fresh_current_401_still_clears_auth:authClears===1&&afterCurrent401.record===null&&afterCurrent401.source===null&&afterCurrent401.claim===''};
 return {scope:'Source-deletion reconciliation error ownership only',verifier:'Node VM synthetic DOM/service replies, explicitly synthetic 401; not actual browser/HTTP/auth-expiry evidence',executed_at:new Date().toISOString(),node_version:process.version,source_sha256:hash(source),test_sha256:hash(fs.readFileSync(__filename)),fixture_sha256:hash(JSON.stringify(record)),passed:Object.values(checks).every(Boolean)?1:0,total:1,results:[{id:'KNOWLEDGE-STALE-DELETION-ERROR-CANNOT-CLEAR-NEW-DRAFT-AUTH',passed:Object.values(checks).every(Boolean),checks,before,after,afterCurrent401,staleAuthClears,authClears,calls}]};
}
run().then(receipt=>{const out=path.resolve(process.argv[2]||path.join(root,'evidence/mvp/knowledge-ui-error-after.json'));fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({passed:receipt.passed,total:receipt.total,source_sha256:receipt.source_sha256,results:receipt.results.map(({id,passed})=>({id,passed}))}));process.exitCode=receipt.passed===receipt.total?0:1;}).catch(error=>{console.error(error);process.exitCode=1;});

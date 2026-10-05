'use strict';
// Narrow lossless-input regression using the unchanged synthetic DOM/service
// harness. This is not actual browser/HTTP/SQLite or game evidence.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),harnessPath=path.join(root,'tests_mvp/ui_draft_capture.cjs');
const harnessBytes=fs.readFileSync(harnessPath),prefix=harnessBytes.toString('utf8').split('async function run(){')[0];
if(!prefix.includes('async function ready('))throw Error('Existing harness interface changed');
const digest=value=>crypto.createHash('sha256').update(value).digest('hex');
const context=vm.createContext({require,process,__dirname:path.dirname(harnessPath),__filename:harnessPath,console,setTimeout,clearTimeout});
vm.runInContext(prefix,context,{filename:harnessPath});
async function runRoundtrip(){
 const rich={title:'Untouched operator declaration 한글 😀',phase:null,patch:null,observed_at:null,
  visible_picks:[{side:'ENEMY',slot:4,champion:null},{side:'ALLY',slot:1,champion:'Ashe'},{side:'ALLY',slot:3,champion:null}],
  visible_bans:[{side:'ENEMY',slot:2,champion:null},{side:'ALLY',slot:5,champion:'Lux'},{side:'ALLY',slot:1,champion:null}],
  role_assignments:[{side:'ENEMY',slot:4,role:null,uncertainty:'UNKNOWN'},{side:'ALLY',slot:5,role:'BOTTOM',uncertainty:'수동 선언 😀'},{side:'ENEMY',slot:1,role:null,uncertainty:'미확인 역할 α'}],
  source:{author:'Operator α',perspective:'UNKNOWN',description:'Synthetic declared input only; not verified Player POV'}};
 const original=record(A,1,rich),results=[];
 async function seeded(){fixtures.A1=clone(original);return ready();}
 async function check(id,task){try{const actual=await task();results.push({id,passed:Object.values(actual.checks).every(Boolean),...actual});}catch(error){results.push({id,passed:false,error:error.message});}}
 await check('DRAFT-ROUNDTRIP-UNTOUCHED-NULL-MEMBERSHIP-ORDER',async()=>{
  const h=await seeded(),before=h.state(),pending=h.save(),request=clone(h.saveQueue[0].body),saved=h.acceptSave(0);await pending;
  return {checks:{untouched_editor_not_dirty:before.dirty===false,entire_loaded_capture_exact:same(request.capture,rich),pick_null_membership_order_exact:same(request.capture.visible_picks,rich.visible_picks),ban_null_membership_order_exact:same(request.capture.visible_bans,rich.visible_bans),role_unknown_membership_order_exact:same(request.capture.role_assignments,rich.role_assignments),champion_does_not_manufacture_role:!request.capture.role_assignments.some(row=>row.side==='ALLY'&&row.slot===1),actual_ack_retains_exact_capture:same(h.state().record.capture,rich)&&saved.revision===2},before,request,after:h.state()};
 });
 await check('DRAFT-ROUNDTRIP-SELECTIVE-EDITS-PRESERVE-OTHER-ROWS',async()=>{
  const h=await seeded();h.edit('title','Explicit title correction β');h.edit('pick-ALLY-3','Ahri');h.edit('ban-ALLY-5','');h.edit('role-ALLY-5','SUPPORT');h.edit('uncertainty-ENEMY-4','알 수 없음 β');h.edit('ban-ALLY-2','Jinx');
  const expected=clone(rich);expected.title='Explicit title correction β';expected.visible_picks[2].champion='Ahri';expected.visible_bans[1].champion=null;expected.visible_bans.push({side:'ALLY',slot:2,champion:'Jinx'});expected.role_assignments[1].role='SUPPORT';expected.role_assignments[0].uncertainty='알 수 없음 β';
  const pending=h.save(),request=clone(h.saveQueue[0].body);h.acceptSave(0);await pending;
  return {checks:{only_declared_fields_changed:same(request.capture,expected),edited_existing_blank_row_remains_null:request.capture.visible_bans.some(row=>row.side==='ALLY'&&row.slot===5&&row.champion===null),old_array_order_retained:same(request.capture.visible_bans.slice(0,3),expected.visible_bans.slice(0,3)),new_declared_row_appended:request.capture.visible_bans.length===4&&same(request.capture.visible_bans[3],expected.visible_bans[3]),untouched_null_and_unknown_rows_retained:same(request.capture.visible_picks[0],rich.visible_picks[0])&&same(request.capture.role_assignments[2],rich.role_assignments[2]),no_new_role_from_pick:request.capture.role_assignments.length===rich.role_assignments.length},request,expected,after:h.state()};
 });
 await check('DRAFT-ROUNDTRIP-LATE-ACK-KEEPS-CAPTURED-DRAFT-BASE',async()=>{
  const h=await seeded();h.edit('pick-ALLY-3','First submitted pick α');h.edit('ban-ALLY-2','First submitted ban β');
  const submitted=clone(rich);submitted.visible_picks[2].champion='First submitted pick α';submitted.visible_bans.push({side:'ALLY',slot:2,champion:'First submitted ban β'});
  const pending=h.save(),firstRequest=clone(h.saveQueue[0].body);
  h.edit('title','Later editor title 😀');h.edit('role-ALLY-5','SUPPORT');h.edit('ban-ALLY-1','Later declared ban');
  const beforeAck=h.state();h.acceptSave(0);await pending;const afterAck=h.state();
  const next=h.save(),nextRequest=clone(h.saveQueue[1].body);h.acceptSave(1);await next;
  const expected=clone(submitted);expected.title='Later editor title 😀';expected.role_assignments[1].role='SUPPORT';expected.visible_bans[2].champion='Later declared ban';
  return {checks:{first_submitted_capture_exact:same(firstRequest.capture,submitted),later_editor_retained:same(afterAck.values,beforeAck.values)&&afterAck.dirty,acknowledged_latest_cas_advanced:afterAck.latest===2&&nextRequest.expected_revision===2,previously_submitted_edits_retained:same(nextRequest.capture,expected),untouched_rows_remain_exact:same(nextRequest.capture.visible_picks[0],rich.visible_picks[0])&&same(nextRequest.capture.role_assignments[0],rich.role_assignments[0]),next_save_capture_ack_exact:same(h.state().record.capture,expected)&&h.state().latest===3},firstRequest,beforeAck,afterAck,nextRequest,expected};
 });
 await check('DRAFT-ROUNDTRIP-NEW-INPUT-NO-INFERRED-ROLE-ROWS',async()=>{
  const h=await seeded();h.evaluate('dNew()');h.edit('title','New declared operator input');h.edit('author','Explicit author');h.edit('source','Explicit source');h.edit('pick-ALLY-1','Ahri');h.edit('ban-ENEMY-2','Lux');
  const pickOnly=JSON.parse(h.evaluate('JSON.stringify(dReadCapture())'));h.edit('uncertainty-ENEMY-3','Explicit unknown role 😀');
  const explicitRole=JSON.parse(h.evaluate('JSON.stringify(dReadCapture())'));
  return {checks:{new_champion_does_not_manufacture_role:pickOnly.role_assignments.length===0,only_declared_pick_and_ban_rows:pickOnly.visible_picks.length===1&&pickOnly.visible_bans.length===1,unknown_time_patch_phase_not_fabricated:pickOnly.phase===null&&pickOnly.patch===null&&pickOnly.observed_at===null,explicit_uncertainty_creates_only_declared_role:same(explicitRole.role_assignments,[{side:'ENEMY',slot:3,role:null,uncertainty:'Explicit unknown role 😀'}]),cleared_base_does_not_retain_old_arrays:!explicitRole.visible_picks.some(row=>row.side==='ENEMY'&&row.slot===4)&&!explicitRole.role_assignments.some(row=>row.side==='ALLY'&&row.slot===5),read_does_not_write:h.calls.every(call=>call.method==='GET')},pickOnly,explicitRole,calls:h.calls};
 });
 return {scope:'Loaded manual capture array membership/order/UNKNOWN and deferred-save draft-base fidelity',verifier:'Node VM real production script, synthetic DOM/service only; not actual browser/HTTP/SQLite/game evidence',executed_at:new Date().toISOString(),node_version:process.version,source_sha256:hash(source),fixture_sha256:hash(canonical({rich,original})),passed:results.filter(result=>result.passed).length,total:4,results};
}
vm.runInContext('('+runRoundtrip.toString()+')()',context).then(receipt=>{
 receipt.test_sha256=digest(fs.readFileSync(__filename));receipt.harness_sha256=digest(harnessBytes);
 const output=path.resolve(process.argv[2]||path.join(root,'evidence/mvp/draft-roundtrip-after.json'));fs.mkdirSync(path.dirname(output),{recursive:true});fs.writeFileSync(output,JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});
 console.log(JSON.stringify({passed:receipt.passed,total:receipt.total,source_sha256:receipt.source_sha256,test_sha256:receipt.test_sha256,fixture_sha256:receipt.fixture_sha256,results:receipt.results.map(({id,passed})=>({id,passed}))}));process.exitCode=receipt.passed===receipt.total?0:1;
}).catch(error=>{console.error(error);process.exitCode=1;});

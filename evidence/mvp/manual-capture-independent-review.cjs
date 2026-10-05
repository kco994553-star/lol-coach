'use strict';
const fs = require('node:fs'), vm = require('node:vm'), path = require('node:path');
const root = '/workspace/scratch/b091e55de8cd/lol-coach';
const filename = path.join(root, 'tests_mvp/ui_draft_capture.cjs');
const prefix = fs.readFileSync(filename, 'utf8').split('async function run(){')[0];
const context = vm.createContext({require, process, __dirname:path.dirname(filename),
  __filename:filename, console, setTimeout, clearTimeout});
vm.runInContext(prefix, context);
vm.runInContext(`(async()=>{
 fixtures.A1.capture.title='original\\r\\n title';
 fixtures.A1.capture.phase='phase\\noriginal';
 fixtures.A1.capture.source.author='author\\r\\noriginal';
 fixtures.A1.capture.source.description='description\\r\\noriginal';
 fixtures.A1.capture.visible_picks=[{side:'ENEMY',slot:4,champion:null},{side:'ALLY',slot:1,champion:'Ashe'}];
 fixtures.A1.capture.visible_bans=[{side:'ENEMY',slot:5,champion:null},{side:'ALLY',slot:2,champion:'Lux'}];
 fixtures.A1.capture.role_assignments=[];
 fixtures.A1.input_sha256=hash(canonical(fixtures.A1.capture));
 const h=await ready();
 for(const id of ['title','phase','author','source'])h.el('d-'+id).value=h.el('d-'+id).value.replace(/[\\r\\n]/g,'');
 h.edit('title','explicitly changed title');
 const titleOnly=h.evaluate('dReadCapture()');
 const titleOnlyExpected=clone(fixtures.A1.capture);titleOnlyExpected.title='explicitly changed title';
 const scalarScopeExact=same(titleOnly,titleOnlyExpected);
 h.edit('pick-ENEMY-4','Ahri');
 const saving=h.save();
 h.edit('pick-ENEMY-4','');
 h.edit('source','explicitly changed description');
 const futureBefore=h.evaluate('dReadCapture()');
 const ack=h.acceptSave(0);await saving;
 const futureAfter=h.evaluate('dReadCapture()');
 const next=h.save(),request=clone(h.saveQueue[1].body);h.acceptSave(1);await next;
 const expected=clone(fixtures.A1.capture);expected.title='explicitly changed title';expected.source.description='explicitly changed description';
 const checks={scalar_edit_changes_only_title:scalarScopeExact,
  late_editor_base_unchanged:same(futureBefore,futureAfter),
  next_cas_is_two:request.expected_revision===2,
  later_current_capture_exact:same(request.capture,expected),
  explicit_null_order_retained:same(request.capture.visible_picks,expected.visible_picks),
  no_manufactured_roles:request.capture.role_assignments.length===0,
  untouched_author_newlines_retained:request.capture.source.author===expected.source.author};
 const result={scope:'Production draft.js with synthetic DOM/service and simulated native normalization; not actual browser/HTTP/game evidence',
  source_sha256:hash(source),acknowledged_submitted_champion:ack.capture.visible_picks[0].champion,
  checks,passed:Object.values(checks).every(Boolean)};
 console.log(JSON.stringify(result,null,2));if(!result.passed)process.exitCode=1;
})().catch(error=>{console.error(error.stack);process.exitCode=1;});`,context);

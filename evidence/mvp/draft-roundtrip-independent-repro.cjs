'use strict';
// Independent synthetic-service counterexample; no browser or game claim.
const fs = require('node:fs'), vm = require('node:vm'), path = require('node:path');
const root = '/workspace/scratch/b091e55de8cd/lol-coach';
const testPath = path.join(root, 'tests_mvp/ui_draft_capture.cjs');
const harnessSource = fs.readFileSync(testPath, 'utf8').split('async function run(){')[0];
const context = vm.createContext({ require, process, __dirname: path.dirname(testPath),
  __filename: testPath, console, setTimeout, clearTimeout });
vm.runInContext(harnessSource, context, { filename: testPath });
vm.runInContext(`(async () => {
  fixtures.A1.capture.visible_picks = [{side:'ALLY',slot:1,champion:null}];
  fixtures.A1.capture.visible_bans = [{side:'ENEMY',slot:2,champion:null}];
  fixtures.A1.capture.role_assignments = [{side:'ALLY',slot:1,role:null,uncertainty:'UNKNOWN'}];
  fixtures.A1.input_sha256 = hash(canonical(fixtures.A1.capture));
  const h = await ready();
  const loaded = clone(h.state().record.capture), dirtyBeforeSave = h.state().dirty;
  const saving = h.save(), request = clone(h.saveQueue[0].body);
  const nextRecord = h.acceptSave(0);
  await saving;
  console.log(JSON.stringify({scope:'Production draft.js with synthetic DOM/service; no browser/HTTP/game claim',
    source_sha256:hash(source), dirty_before_save:dirtyBeforeSave, loaded_capture:loaded,
    submitted_capture:request.capture, expected_revision:request.expected_revision,
    acknowledged_revision:nextRecord.revision, exact_no_edit_roundtrip:same(loaded,request.capture)}, null, 2));
})().catch(error => { console.error(error.stack); process.exitCode = 1; });`, context);

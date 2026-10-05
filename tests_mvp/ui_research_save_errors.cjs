'use strict';
// Synthetic DOM and deferred Research save failures. These failures are explicit
// Node test inputs, not actual HTTP authentication, credential expiry or games.
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const crypto = require('node:crypto'), {spawnSync} = require('node:child_process');
const root = path.resolve(process.env.LOL_COACH_REPO || path.join(__dirname, '..'));
const sourcePath = path.resolve(process.argv[3] || path.join(root, 'web_r4/research.js'));
const source = fs.readFileSync(sourcePath, 'utf8');
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const fixtures = {
  A: {resource: {id: 'A', title: 'A', kind: 'RAW_DIAGNOSTIC', report: {sections: {}, issues: [], declared_source_kind: 'UNVERIFIED_IMPORT'}},
    note: {resource_id: 'A', anchor: 'overview', revision: 1, known: 'A saved', intention: '', alternative: '', outcome: ''}, draft: 'A exact current unsaved draft'},
  B: {resource: {id: 'B', title: 'B', kind: 'RAW_DIAGNOSTIC', report: {sections: {}, issues: [], declared_source_kind: 'UNVERIFIED_IMPORT'}},
    note: {resource_id: 'B', anchor: 'overview', revision: 2, known: 'B saved', intention: '', alternative: '', outcome: ''}, draft: 'B exact newer unsaved draft 😀'}
};
function deferred() {let resolve, reject; const promise = new Promise((yes, no) => {resolve = yes; reject = no;}); return {promise, resolve, reject};}
function harness() {
  const elements = new Map(), calls = [], globalErrors = [], saveReply = deferred();
  const el = id => {
    if (!elements.has(id)) elements.set(id, {value: '', files: [], disabled: false, hidden: false, textContent: '', dataset: {}, listeners: {},
      addEventListener(type, fn) {this.listeners[type] = fn;}, replaceChildren() {}, append() {}});
    return elements.get(id);
  };
  const context = vm.createContext({$: el, document: {querySelector: () => el('filter-label')}, node: () => el(Symbol()),
    confirm: () => true, error: error => globalErrors.push({message: error.message, status: error.status}), console,
    api: async (route, method = 'GET', body) => {
      calls.push({route, method, body});
      if (route === '/research/A/notes/overview' && method === 'PUT') return saveReply.promise;
      if (route === '/research/B') return JSON.parse(JSON.stringify(fixtures.B.resource));
      if (route === '/research/B/notes/overview') return JSON.parse(JSON.stringify(fixtures.B.note));
      throw new Error('Unexpected synthetic API route: ' + method + ' ' + route);
    }});
  vm.runInContext(source, context, {filename: 'web_r4/research.js'});
  context.__initial = JSON.parse(JSON.stringify(fixtures.A));
  vm.runInContext("rResource=__initial.resource;rNote=__initial.note;rDirty=true;rEdit=1", context);
  el('r-title').textContent = 'A'; el('r-detail').hidden = false;
  el('r-known').value = fixtures.A.draft; el('r-note-state').textContent = '저장하지 않은 변경이 있습니다.';
  const state = () => JSON.parse(vm.runInContext("JSON.stringify({id:rResource&&rResource.id,note:rNote,known:$('r-known').value,intention:$('r-intention').value,alternative:$('r-alternative').value,outcome:$('r-outcome').value,title:$('r-title').textContent,dirty:rDirty,edit:rEdit,epoch:rEpoch,hidden:$('r-detail').hidden,notice:$('r-notice').textContent,note_state:$('r-note-state').textContent,save_disabled:$('r-save').disabled})", context));
  return {el, calls, globalErrors, state,
    save: () => el('r-save').listeners.click(),
    async openBAndDraft() {
      await vm.runInContext("rOpen('B')", context);
      el('r-known').value = fixtures.B.draft; el('r-known').listeners.input();
    },
    failSave(status) {saveReply.reject(Object.assign(new Error(status === 401 ? 'AUTH_REQUIRED' : 'REVISION_CONFLICT'), {status}));}};
}
async function run() {
  const results = [];
  async function check(id, task) {
    try {const actual = await task(); results.push({id, passed: Object.values(actual.checks).every(value => value === true), ...actual});}
    catch (error) {results.push({id, passed: false, error: error.message});}
  }
  for (const status of [401, 409]) await check('RESEARCH-STALE-SAVE-' + status + '-AFTER-B-DRAFT', async () => {
    const h = harness(), saving = h.save(); await h.openBAndDraft(); const before = h.state();
    h.failSave(status); await saving; const after = h.state();
    return {checks: {save_target_and_cas_are_a: h.calls.some(call => call.route === '/research/A/notes/overview' && call.method === 'PUT' && call.body.expected_revision === 1 && call.body.note.known === fixtures.A.draft),
      exact_b_state_retained: JSON.stringify(after) === JSON.stringify(before),
      b_dirty_draft_retained: after.id === 'B' && after.known === fixtures.B.draft && after.dirty === true && after.note?.revision === 2,
      no_old_auth_delegation: h.globalErrors.length === 0}, before, after, globalErrors: h.globalErrors, calls: h.calls};
  });
  await check('RESEARCH-CURRENT-SAVE-409-SHOWS-ERROR-KEEPS-DRAFT', async () => {
    const h = harness(), before = h.state(), saving = h.save();
    h.failSave(409); await saving; const after = h.state();
    return {checks: {current_error_shown: after.notice === '처리하지 못했습니다: REVISION_CONFLICT',
      current_resource_note_and_draft_retained: after.id === before.id && JSON.stringify(after.note) === JSON.stringify(before.note) && after.known === before.known && after.dirty === true,
      save_reenabled: after.save_disabled === false, no_auth_delegation: h.globalErrors.length === 0}, before, after, globalErrors: h.globalErrors};
  });
  await check('RESEARCH-CURRENT-SAVE-401-SHOWS-ERROR-CLEARS-AUTH-CONTEXT', async () => {
    const h = harness(), saving = h.save(); h.failSave(401); await saving; const after = h.state();
    return {checks: {current_auth_error_shown: after.notice === '처리하지 못했습니다: AUTH_REQUIRED',
      research_context_cleared: after.id === null && after.note === null && after.known === '' && after.dirty === false && after.hidden === true,
      one_current_auth_delegation: h.globalErrors.length === 1 && h.globalErrors[0].status === 401 && h.globalErrors[0].message === 'AUTH_REQUIRED'}, after, globalErrors: h.globalErrors};
  });
  return {scope: 'Research current/stale save-error routing; synthetic API failures only',
    verifier: 'Node VM DOM stub and deferred 401/409 inputs; not browser E2E, actual HTTP auth or credential expiry',
    executed_at: new Date().toISOString(), node_version: process.version,
    source_sha256: hash(source), test_sha256: hash(fs.readFileSync(__filename)), fixture_sha256: hash(JSON.stringify(fixtures)),
    passed: results.filter(row => row.passed).length, total: results.length, results};
}
if (process.argv[2] === '--run') {
  run().then(result => {console.log(JSON.stringify(result)); process.exitCode = result.passed === result.total ? 0 : 1;})
    .catch(error => {console.error(error); process.exitCode = 1;});
} else {
  const destination = path.resolve(process.argv[2] || path.join(root, 'evidence/mvp/research-save-errors-after.json'));
  const child = spawnSync(process.execPath, [__filename, '--run', sourcePath], {encoding: 'utf8', timeout: 30000});
  let result;
  try {result = JSON.parse(child.stdout);} catch {result = {source_sha256: hash(source), runner_error: 'No valid child receipt', results: []};}
  result.process = {exit_code: child.status, signal: child.signal, stdout: child.stdout, stderr: child.stderr};
  fs.mkdirSync(path.dirname(destination), {recursive: true});
  fs.writeFileSync(destination, JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
  console.log(JSON.stringify({passed: result.passed, total: result.total, source_sha256: result.source_sha256, exit_code: child.status,
    results: result.results.map(row => ({id: row.id, passed: row.passed}))}));
  process.exitCode = child.status === 0 ? 0 : 1;
}

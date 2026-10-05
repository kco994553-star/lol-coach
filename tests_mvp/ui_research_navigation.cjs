'use strict';
// Deferred service replies exercise only Research navigation/delete UI logic.
// This DOM stub is not browser or real game evidence.
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm'), crypto = require('node:crypto');
const root = path.resolve(__dirname, '..');
const sourcePath = path.resolve(process.argv[3] || path.join(root, 'web_r4/research.js'));
const source = fs.readFileSync(sourcePath, 'utf8');
const hash = value => crypto.createHash('sha256').update(value).digest('hex');
function deferred() {let resolve, reject; const promise = new Promise((yes, no) => {resolve = yes; reject = no;}); return {promise, resolve, reject};}

function harness() {
  const elements = new Map(), calls = [], getB = deferred(), deleteA = deferred();
  const el = id => {
    if (!elements.has(id)) elements.set(id, {value: '', files: [], disabled: false, hidden: false, textContent: '', dataset: {}, listeners: {},
      addEventListener(type, fn) {this.listeners[type] = fn;}, replaceChildren() {}, append() {}});
    return elements.get(id);
  };
  const context = vm.createContext({$: el, document: {querySelector: () => el('filter-label')}, node: () => el(Symbol()),
    confirm: () => true, error() {}, console,
    api: async (route, method = 'GET') => {
      calls.push({route, method});
      if (route === '/research/B' && method === 'GET') return getB.promise;
      if (route === '/research/A' && method === 'DELETE') return deleteA.promise;
      if (route === '/research/B/notes/overview') return {resource_id: 'B', anchor: 'overview', revision: 0, known: '', intention: '', alternative: '', outcome: ''};
      if (route === '/research') return [];
      throw new Error('Unexpected synthetic service route: ' + method + ' ' + route);
    }});
  vm.runInContext(source, context, {filename: 'web_r4/research.js'});
  vm.runInContext("rResource={id:'A',title:'A'};rNote={resource_id:'A',anchor:'overview',revision:0};rDirty=false", context);
  el('r-title').textContent = 'A'; el('r-detail').hidden = false; el('r-known').value = 'A old note';
  const state = () => JSON.parse(vm.runInContext("JSON.stringify({id:rResource&&rResource.id,known:$('r-known').value,dirty:rDirty,epoch:rEpoch,hidden:$('r-detail').hidden,notice:$('r-notice').textContent,delete_disabled:$('r-delete').disabled})", context));
  const finishB = () => getB.resolve({id: 'B', title: 'B', kind: 'RAW_DIAGNOSTIC', report: {declared_source_kind: 'UNVERIFIED_IMPORT', sections: {}, issues: []}});
  return {el, calls, state, finishB, deleteA,
    openB: () => vm.runInContext("rOpen('B')", context),
    delete: () => el('r-delete').listeners.click(),
    draftB: () => {el('r-known').value = 'B exact unsaved draft'; el('r-known').listeners.input();}};
}

async function run() {
  const results = [];
  async function check(id, task) {
    try {const actual = await task(); results.push({id, passed: Object.values(actual.checks).every(value => value === true), ...actual});}
    catch (error) {results.push({id, passed: false, error: error.message});}
  }
  await check('RESEARCH-NAV-DELETE-DISABLED-NO-REQUEST', async () => {
    const h = harness(), opening = h.openB(), pending = h.state();
    const deletion = h.delete(), requestsWhileLoading = h.calls.filter(call => call.method === 'DELETE').length;
    h.finishB(); await opening;
    h.deleteA.resolve({id: 'A', status: 'DELETED'}); await deletion;
    return {checks: {delete_disabled: pending.delete_disabled === true, handler_no_request: requestsWhileLoading === 0}, pending, requestsWhileLoading};
  });
  await check('RESEARCH-NAV-LEGACY-DELETE-CANNOT-CLEAR-B-DRAFT', async () => {
    const h = harness(), opening = h.openB();
    // Adversarially reproduce the old enabled-control window to test the
    // callback identity guard independently of the preventive disabled UI.
    h.el('r-delete').disabled = false;
    const deletion = h.delete();
    h.finishB(); await opening; h.draftB(); const before = h.state();
    h.deleteA.resolve({id: 'A', status: 'DELETED'}); await deletion; const after = h.state();
    return {checks: {delete_target_a: h.calls.some(call => call.method === 'DELETE' && call.route === '/research/A'),
      exact_b_draft_retained: after.id === 'B' && after.known === before.known && after.dirty === true && !after.hidden,
      notice_retained: after.notice === before.notice}, before, after, calls: h.calls};
  });
  await check('RESEARCH-NAV-CURRENT-DELETE-CLEARS', async () => {
    const h = harness(), deletion = h.delete();
    h.deleteA.resolve({id: 'A', status: 'DELETED'}); await deletion; const after = h.state();
    return {checks: {current_deleted: h.calls.some(call => call.method === 'DELETE' && call.route === '/research/A'),
      notes_cleared: after.id === null && after.known === '' && after.dirty === false && after.hidden,
      success_notice: after.notice === '자료와 노트를 삭제했습니다.'}, after, calls: h.calls};
  });
  await check('RESEARCH-NAV-LATE-A-DELETE-ERROR-CANNOT-REPORT-ON-B', async () => {
    const h = harness(), deletion = h.delete(), opening = h.openB();
    h.finishB(); await opening; h.draftB(); const before = h.state();
    h.deleteA.reject(new Error('RESOURCE_NOT_FOUND')); await deletion; const after = h.state();
    return {checks: {b_draft_retained: after.id === 'B' && after.known === before.known && after.dirty === true,
      no_stale_error: after.notice === before.notice}, before, after};
  });
  return {scope: 'Research navigation and deletion identity only; no real game validation', verifier: 'Node VM synthetic DOM and deferred service replies; not browser',
    executed_at: new Date().toISOString(), source_sha256: hash(source), test_sha256: hash(fs.readFileSync(__filename)),
    passed: results.filter(result => result.passed).length, total: results.length, results};
}

run().then(result => {
  const destination = path.resolve(process.argv[2] || path.join(root, 'evidence/mvp/research-navigation-after.json'));
  fs.mkdirSync(path.dirname(destination), {recursive: true});
  fs.writeFileSync(destination, JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
  console.log(JSON.stringify({passed: result.passed, total: result.total, source_sha256: result.source_sha256,
    results: result.results.map(({id, passed}) => ({id, passed}))}));
  process.exitCode = result.passed === result.total ? 0 : 1;
}).catch(error => {console.error(error); process.exitCode = 1;});

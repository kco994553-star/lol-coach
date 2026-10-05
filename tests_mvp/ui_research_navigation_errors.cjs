'use strict';
// Actual Research event handlers in a synthetic DOM with deferred API errors.
// Explicit 401 inputs are not HTTP auth observations or credential-expiry claims.
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const crypto = require('node:crypto'), {spawnSync} = require('node:child_process');
const root = path.resolve(process.env.LOL_COACH_REPO || path.join(__dirname, '..'));
const sourcePath = path.resolve(process.argv[3] || path.join(root, 'web_r4/research.js'));
const source = fs.readFileSync(sourcePath, 'utf8');
const hash = value => crypto.createHash('sha256').update(value).digest('hex');
const aid = 'a'.repeat(64), bid = 'b'.repeat(64);
const fixtures = {
  A: {resource: {id: aid, title: 'A', kind: 'VIDEO', report: {video_id: 'abcdefghijk', cue_count: 1,
    candidates: [{cue_index: 2, topics: ['WAVE'], video_time_ms: 1000}]}},
    note: {resource_id: aid, anchor: 'overview', revision: 1, known: 'A saved', intention: '', alternative: '', outcome: ''}},
  B: {resource: {id: bid, title: 'B', kind: 'RAW_DIAGNOSTIC', report: {declared_source_kind: 'UNVERIFIED_IMPORT', sections: {}, issues: []}},
    note: {resource_id: bid, anchor: 'overview', revision: 2, known: 'B saved', intention: '', alternative: '', outcome: ''}},
  newDraft: 'B exact newer unsaved draft 😀'
};
const copy = value => JSON.parse(JSON.stringify(value));
function deferred() {let reject; const promise = new Promise((resolve, no) => {reject = no;}); return {promise, reject};}
function element(tag = 'div', text = '') {return {tagName: tag, value: '', files: [], disabled: false, hidden: false,
  textContent: text, dataset: {}, listeners: {}, children: [],
  addEventListener(type, fn) {this.listeners[type] = fn;}, replaceChildren() {this.children = [];},
  append(...items) {this.children.push(...items);}};}
function find(node, predicate) {if (predicate(node)) return node; for (const child of node.children || []) {const result = find(child, predicate); if (result) return result;} return null;}
async function harness(subject) {
  const elements = new Map(), calls = [], globalErrors = [], failure = deferred();
  let armed = false;
  const el = id => {if (!elements.has(id)) elements.set(id, element()); return elements.get(id);};
  const context = vm.createContext({$: el, document: {querySelector: () => el('filter-label')},
    node: (tag, text) => element(tag, text || ''), confirm: () => true,
    error: error => globalErrors.push({message: error.message, status: error.status}), console,
    api: async (route, method = 'GET') => {
      calls.push({route, method});
      if (armed && ((subject === 'resource' && route === '/research/' + aid) ||
        (subject === 'anchor' && route === '/research/' + aid + '/notes/2') ||
        (subject === 'list' && route === '/research'))) return failure.promise;
      if (route === '/research') return [fixtures.A.resource, fixtures.B.resource].map(({id, title, kind}) => ({id, title, kind}));
      if (route === '/research/' + bid) return copy(fixtures.B.resource);
      if (route === '/research/' + bid + '/notes/overview') return copy(fixtures.B.note);
      throw Error('Unexpected synthetic API route: ' + route);
    }});
  vm.runInContext(source, context, {filename: 'web_r4/research.js'});
  context.__fixture = copy(fixtures.A);
  vm.runInContext("rResource=__fixture.resource;rNote=__fixture.note;rDirty=false;rEdit=0", context);
  el('r-title').textContent = 'A'; el('r-detail').hidden = false; el('r-known').value = 'A saved';
  el('r-filter').value = 'ALL'; vm.runInContext('rRender()', context);
  await vm.runInContext('rRefresh()', context);
  armed = true;
  const resourceA = find(el('r-list'), node => node.dataset.resourceId === aid);
  const resourceB = find(el('r-list'), node => node.dataset.resourceId === bid);
  const anchorA = find(el('r-candidates'), node => node.dataset.anchor === '2');
  if (!resourceA || !resourceB || !anchorA) throw Error('Actual source-created event targets missing');
  const state = () => JSON.parse(vm.runInContext("JSON.stringify({id:rResource&&rResource.id,note:rNote,known:$('r-known').value,intention:$('r-intention').value,alternative:$('r-alternative').value,outcome:$('r-outcome').value,title:$('r-title').textContent,dirty:rDirty,edit:rEdit,epoch:rEpoch,hidden:$('r-detail').hidden,notice:$('r-notice').textContent,note_state:$('r-note-state').textContent,save_disabled:$('r-save').disabled})", context));
  return {state, calls, globalErrors,
    trigger() {return (subject === 'resource' ? resourceA : subject === 'anchor' ? anchorA : el('r-refresh')).listeners.click();},
    async openBAndDraft() {await resourceB.listeners.click(); el('r-known').value = fixtures.newDraft; el('r-known').listeners.input();},
    fail() {failure.reject(Object.assign(new Error('AUTH_REQUIRED'), {status: 401}));}};
}
async function run() {
  const results = [];
  async function check(id, task) {
    try {const actual = await task(); results.push({id, passed: Object.values(actual.checks).every(value => value === true), ...actual});}
    catch (error) {results.push({id, passed: false, error: error.message});}
  }
  for (const subject of ['resource', 'anchor', 'list']) {
    await check('RESEARCH-STALE-' + subject.toUpperCase() + '-ERROR-AFTER-B-DRAFT', async () => {
      const h = await harness(subject), pending = h.trigger(); await h.openBAndDraft(); const before = h.state();
      h.fail(); await pending; const after = h.state();
      return {checks: {exact_b_state_retained: JSON.stringify(after) === JSON.stringify(before),
        b_new_draft_retained: after.id === bid && after.known === fixtures.newDraft && after.dirty === true && after.note?.revision === 2,
        no_old_auth_delegation: h.globalErrors.length === 0}, before, after, globalErrors: h.globalErrors, calls: h.calls};
    });
    await check('RESEARCH-CURRENT-' + subject.toUpperCase() + '-ERROR-STILL-HANDLED', async () => {
      const h = await harness(subject), pending = h.trigger(); h.fail(); await pending; const after = h.state();
      return {checks: {current_auth_error_shown: after.notice === '처리하지 못했습니다: AUTH_REQUIRED',
        context_cleared: after.id === null && after.note === null && after.known === '' && after.dirty === false && after.hidden === true,
        one_current_auth_delegation: h.globalErrors.length === 1 && h.globalErrors[0].status === 401}, after, globalErrors: h.globalErrors, calls: h.calls};
    });
  }
  return {scope: 'Research resource/anchor/list UI error routing; explicit synthetic API errors only',
    verifier: 'Node VM synthetic DOM with actual source-created buttons/event callbacks; not browser E2E or actual HTTP auth',
    executed_at: new Date().toISOString(), node_version: process.version, source_sha256: hash(source),
    test_sha256: hash(fs.readFileSync(__filename)), fixture_sha256: hash(JSON.stringify(fixtures)),
    passed: results.filter(row => row.passed).length, total: results.length, results};
}
if (process.argv[2] === '--run') {
  run().then(result => {console.log(JSON.stringify(result)); process.exitCode = result.passed === result.total ? 0 : 1;})
    .catch(error => {console.error(error); process.exitCode = 1;});
} else {
  const destination = path.resolve(process.argv[2] || path.join(root, 'evidence/mvp/research-navigation-errors-after.json'));
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

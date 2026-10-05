'use strict';
// Synthetic DOM plus deferred research API failures. No server responses or real
// game evidence are claimed; this checks current versus superseded UI errors.
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const crypto = require('node:crypto'), {spawnSync} = require('node:child_process');
const root = path.resolve(__dirname, '..');
const sourcePath = path.resolve(process.argv[3] || path.join(root, 'web_r4/research.js'));
const source = fs.readFileSync(sourcePath, 'utf8');
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const fixture = Buffer.from('{"allPlayers":[],"note":"request failure fixture"}');
function deferred() {let resolve; const promise = new Promise(r => {resolve = r;}); return {promise, resolve};}
function file(name, held = false) {
  const gate = deferred(); if (!held) gate.resolve();
  return {file: {name, size: fixture.length,
    text: async () => {await gate.promise; return fixture.toString('utf8');},
    arrayBuffer: async () => {await gate.promise; return Uint8Array.from(fixture).buffer;}},
    finish: () => gate.resolve()};
}
function harness({failureStage = 'resource', heldFailure = false} = {}) {
  const elements = new Map(), requests = [], resources = new Map();
  const lookupEntered = deferred(), rejectLookup = deferred();
  function el(id) {
    if (!elements.has(id)) elements.set(id, {value: '', files: [], disabled: false,
      hidden: false, textContent: '', dataset: {}, listeners: {},
      addEventListener(k, fn) {this.listeners[k] = fn;}, replaceChildren() {}, append() {}});
    return elements.get(id);
  }
  const context = vm.createContext({$: el, TextDecoder, limits: {body_bytes: 1000000},
    document: {querySelector: () => el('filter-label')}, node: () => el(Symbol()),
    confirm: () => true, error() {}, console,
    api: async (route, method = 'GET', body) => {
      requests.push({route, method, title: body?.title || null});
      if (method === 'POST') {
        const id = body.title === 'A.json' ? 'resource-a' : 'resource-b';
        const resource = {id, title: body.title, kind: 'RAW_DIAGNOSTIC',
          report: {declared_source_kind: 'UNVERIFIED_IMPORT', sections: {}, issues: [], coaching_enabled: false}};
        resources.set(id, resource); return resource;
      }
      if (route === '/research') return [...resources.values()].map(({id, title, kind}) => ({id, title, kind}));
      const failRoute = '/research/resource-a' + (failureStage === 'note' ? '/notes/overview' : '');
      if (route === failRoute) {
        lookupEntered.resolve(); if (heldFailure) await rejectLookup.promise;
        throw Error(failureStage === 'note' ? 'CURRENT_NOTE_LOOKUP_FAILED' : 'CURRENT_RESOURCE_LOOKUP_FAILED');
      }
      if (route.endsWith('/notes/overview')) return {resource_id: route.split('/')[2], anchor: 'overview', revision: 0,
        known: '', intention: '', alternative: '', outcome: ''};
      const resource = resources.get(route.split('/')[2]); if (resource) return resource;
      throw Error('Unexpected test route: ' + route);
    }});
  vm.runInContext(source, context, {filename: 'web_r4/research.js'});
  const evaluate = code => vm.runInContext(code, context);
  el('r-kind').value = 'raw_json';
  evaluate("rResource={id:'old',title:'old'};rNote={resource_id:'old',anchor:'overview',revision:3};rDirty=false;rEdit=2");
  el('r-known').value = '보존할 원본 노트'; el('r-title').textContent = 'old';
  return {el, requests, lookupEntered: lookupEntered.promise, rejectLookup: () => rejectLookup.resolve(),
    select(selected) {el('r-file').files = selected ? [selected] : []; return el('r-file').listeners.change();},
    logout() {el('logout').listeners.click();},
    state() {return JSON.parse(evaluate("JSON.stringify({id:rResource&&rResource.id,note:rNote,dirty:rDirty,edit:rEdit,epoch:rEpoch,read:rFileRead,known:$('r-known').value,title:$('r-title').textContent,notice:$('r-notice').textContent,note_disabled:$('r-known').disabled,save_disabled:$('r-save').disabled})"));}};
}
async function run() {
  const results = [];
  async function check(id, task) {
    try {const actual = await task(); results.push({id, passed: Object.values(actual.checks).every(v => v === true), ...actual});}
    catch (error) {results.push({id, passed: false, error: error.message});}
  }
  for (const stage of ['resource', 'note']) await check('RESEARCH-CURRENT-' + stage.toUpperCase() + '-GET-ERROR', async () => {
    const h = harness({failureStage: stage}), before = h.state(), a = file('A.json');
    await h.select(a.file); const after = h.state();
    const expected = '처리하지 못했습니다: ' + (stage === 'note' ? 'CURRENT_NOTE_LOOKUP_FAILED' : 'CURRENT_RESOURCE_LOOKUP_FAILED');
    return {checks: {current_error_reported: after.notice === expected,
      old_resource_and_note_retained: after.id === before.id && after.known === before.known && JSON.stringify(after.note) === JSON.stringify(before.note),
      old_note_editable: after.note_disabled === false && after.save_disabled === false,
      own_open_epoch_reached: after.epoch === 2}, before, after, requests: h.requests};
  });
  await check('RESEARCH-STALE-GET-ERROR-AFTER-NEW-SELECTION', async () => {
    const h = harness({heldFailure: true}), a = file('A.json'), b = file('B.json', true);
    const pa = h.select(a.file); await h.lookupEntered; const beforeSelection = h.state();
    const pb = h.select(b.file); const beforeStale = h.state();
    h.rejectLookup(); await pa; const afterStale = h.state();
    const pendingBRetained = h.el('r-file').files[0] === b.file;
    const postsBeforeB = h.requests.filter(r => r.method === 'POST').map(r => r.title);
    b.finish(); await pb; const afterB = h.state();
    return {checks: {selection_changed_without_epoch_change: beforeStale.epoch === beforeSelection.epoch && beforeStale.read > beforeSelection.read,
      no_stale_error: afterStale.notice === beforeStale.notice,
      old_resource_and_note_retained_while_b_pending: afterStale.id === beforeStale.id && afterStale.known === beforeStale.known && JSON.stringify(afterStale.note) === JSON.stringify(beforeStale.note),
      newest_file_retained: pendingBRetained, only_original_post_before_b: JSON.stringify(postsBeforeB) === JSON.stringify(['A.json']),
      latest_b_opens: afterB.title === 'B.json' && afterB.id === 'resource-b' && afterB.notice === '저장된 자료를 열었습니다.'},
      beforeSelection, beforeStale, afterStale, afterB, requests: h.requests};
  });
  await check('RESEARCH-STALE-GET-ERROR-AFTER-LOGOUT', async () => {
    const h = harness({heldFailure: true}), a = file('A.json');
    const pa = h.select(a.file); await h.lookupEntered; h.logout(); const loggedOut = h.state();
    const count = h.requests.length; h.rejectLookup(); await pa; const after = h.state();
    return {checks: {exact_logged_out_state_retained: JSON.stringify(after) === JSON.stringify(loggedOut),
      cleared_resource_and_note: after.id === null && after.note === null,
      no_stale_error: after.notice === '', no_followup_requests: h.requests.length === count}, loggedOut, after, requests: h.requests};
  });
  return {scope: 'Research current and superseded API error routing; synthetic fixtures only',
    verifier: 'Node VM DOM stub and deferred API failures; not browser E2E or real server',
    executed_at: new Date().toISOString(), node_version: process.version,
    source_sha256: hash(source), test_sha256: hash(fs.readFileSync(__filename)), fixture_sha256: hash(fixture),
    passed: results.filter(row => row.passed).length, total: results.length, results};
}
if (process.argv[2] === '--run') {
  run().then(result => {console.log(JSON.stringify(result)); process.exitCode = result.passed === result.total ? 0 : 1;})
    .catch(error => {console.error(error); process.exitCode = 1;});
} else {
  const destination = path.resolve(process.argv[2] || path.join(root, 'evidence/mvp/research-request-after.json'));
  const child = spawnSync(process.execPath, [__filename, '--run', sourcePath], {encoding: 'utf8', timeout: 30000});
  let result;
  try {result = JSON.parse(child.stdout);} catch {result = {source_sha256: hash(source), runner_error: 'No valid child receipt', results: []};}
  result.process = {exit_code: child.status, signal: child.signal, stdout: child.stdout, stderr: child.stderr};
  fs.mkdirSync(path.dirname(destination), {recursive: true});
  fs.writeFileSync(destination, JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
  console.log(JSON.stringify({passed: result.passed, total: result.total, exit_code: child.status, results: result.results.map(row => ({id: row.id, passed: row.passed}))}));
  process.exitCode = child.status === 0 ? 0 : 1;
}

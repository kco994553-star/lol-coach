'use strict';
// Deterministic file-read ordering checks. The DOM/File objects are stubs, not
// browser E2E and never actual game evidence. Optional argv[3] selects preserved
// app bytes for the before-repair receipt; argv[2] selects the output receipt.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const { spawnSync } = require('node:child_process');
const root = path.resolve(__dirname, '..');
const sourcePath = path.resolve(process.argv[3] || path.join(root, 'web_r4/app.js'));
const source = fs.readFileSync(sourcePath, 'utf8');
const fixturePath = path.join(root, 'examples/r3/compare-wait-retreat.json');
const fixtureBytes = fs.readFileSync(fixturePath);
const baseFixture = JSON.parse(fixtureBytes);
const hash = value => crypto.createHash('sha256').update(value).digest('hex');
const clone = value => JSON.parse(JSON.stringify(value));
const checksPassed = checks => Object.values(checks).every(Boolean);

function fixture(id, objective) {
  const result = clone(baseFixture);
  result.objective = objective;
  result.snapshot_request.session_id = id;
  result.observations.forEach(row => { row.session_id = id; });
  return result;
}

function deferredFile(name, objective) {
  let resolve, reject;
  const body = JSON.stringify(fixture('import-fixture', objective));
  const promise = new Promise((done, fail) => { resolve = done; reject = fail; });
  return { file: { name, size: Buffer.byteLength(body), text: () => promise },
    body, finish: () => resolve(body), finishMalformed: () => resolve('{malformed'),
    rejectRead: () => reject(Error('Old file read failed')) };
}

function harness() {
  const elements = new Map(), confirmations = [], requests = [];
  let confirmationAnswer = true;
  function element(id) {
    if (!elements.has(id)) elements.set(id, {
      value: '', hidden: false, disabled: false, textContent: '', className: '',
      files: [], listeners: {}, children: [],
      addEventListener(type, callback) { this.listeners[type] = callback; },
      replaceChildren(...children) { this.children = children; },
      append(...children) { this.children.push(...children); }
    });
    return elements.get(id);
  }
  const sessions = new Map(['session-A', 'session-B'].map(id => [id, {
    session: { id, title: id, patch: 'SYNTHETIC-1', mode: 'TEST', revision: 1 },
    case: fixture(id, 'Saved ' + id)
  }]));
  const context = vm.createContext({
    document: { getElementById: element, createElement: () => element(Symbol()) },
    sessionStorage: { getItem: () => '', setItem() {}, removeItem() {} },
    confirm: message => { confirmations.push(message); return confirmationAnswer; },
    setTimeout, clearTimeout, console, crypto: { randomUUID: () => 'synthetic-test-key' },
    fetch: async (url, options) => {
      const route = url.replace(/^\/dev\/v1/, '');
      requests.push({ route, method: options.method });
      let data;
      if (route === '/sessions') data = [...sessions.values()].map(row => row.session);
      else {
        const match = /^\/sessions\/([^/]+)(?:\/(case|reviews))?$/.exec(route);
        if (!match || !sessions.has(match[1]) || options.method !== 'GET') throw Error('Unexpected request: ' + route);
        const record = sessions.get(match[1]);
        data = !match[2] ? record.session : match[2] === 'case' ? { case: record.case, revision: 1 } : [];
      }
      return { ok: true, status: 200, json: async () => clone(data) };
    }
  });
  vm.runInContext(source, context, { filename: 'web_r4/app.js' });
  const evaluate = code => vm.runInContext(code, context);
  evaluate('limits={body_bytes:1000000}');
  return {
    element, confirmations, requests, evaluate,
    open: id => evaluate('openSession(' + JSON.stringify(id) + ')'),
    state: () => JSON.parse(evaluate("JSON.stringify({current,editor:$('case-json').value,saved_editor:savedEditor,analyze_disabled:$('analyze').disabled,notice:$('notice').textContent})")),
    select(file) {
      element('import-file').files = file ? [file] : [];
      element('import-file').value = file ? file.name : '';
      return element('import-file').listeners.change();
    },
    edit(value) { element('case-json').value = value; element('case-json').listeners.input(); },
    cancelConfirmation() { confirmationAnswer = false; }
  };
}

function observed(h) {
  const state = h.state();
  let objective = null;
  try { objective = JSON.parse(state.editor).objective; } catch {}
  return { session_id: state.current && state.current.id, editor_objective: objective,
    editor_sha256: hash(state.editor), saved_editor_sha256: hash(state.saved_editor),
    selected_file: h.element('import-file').value, analyze_disabled: state.analyze_disabled,
    confirmations: [...h.confirmations], notice: state.notice };
}

async function latestSelectionWins(oldCompletesFirst) {
  const h = harness(), a = deferredFile('A.json', 'Older selected file A'), b = deferredFile('B.json', 'Latest selected file B');
  const pa = h.select(a.file), pb = h.select(b.file);
  let interim;
  if (oldCompletesFirst) {
    a.finish(); await pa;
    interim = observed(h);
    b.finish(); await pb;
  } else {
    b.finish(); await pb;
    interim = observed(h);
    a.finish(); await pa;
  }
  const state = h.state();
  const checks = {
    newest_selected_file_loaded: state.editor === JSON.stringify(JSON.parse(b.body), null, 2),
    imported_input_not_associated_with_prior_session: state.current === null,
    only_applied_file_selection_cleared: h.element('import-file').value === '',
    import_not_saved_automatically: h.requests.length === 0,
    no_unexpected_confirmation: h.confirmations.length === 0,
    old_completion_does_not_replace_latest_input: !oldCompletesFirst || interim.editor_objective === null,
    old_completion_preserves_new_file_selection: !oldCompletesFirst || interim.selected_file === 'B.json'
  };
  return { id: oldCompletesFirst ? 'MVP-IMPORT-A-FIRST-B-LATEST' : 'MVP-IMPORT-B-FIRST-B-LATEST',
    passed: checksPassed(checks), checks, actual: { interim, final: observed(h), latest_selection: 'B.json' } };
}

async function clearedSelectionInvalidatesRead() {
  const h = harness();
  await h.open('session-A');
  const before = h.state(), a = deferredFile('A.json', 'Abandoned file A');
  const pending = h.select(a.file);
  await h.select(null);
  a.finish(); await pending;
  const after = h.state();
  const checks = { cleared_selection_does_not_load_old_file: after.editor === before.editor,
    session_identity_retained: after.current && after.current.id === 'session-A',
    saved_baseline_retained: after.saved_editor === before.saved_editor,
    no_discard_confirmation_for_cleared_selection: h.confirmations.length === 0,
    cleared_file_input_stays_empty: h.element('import-file').value === '' };
  return { id: 'MVP-IMPORT-CLEARED-SELECTION', passed: checksPassed(checks), checks, actual: observed(h) };
}

async function sessionSwitchInvalidatesRead() {
  const h = harness();
  await h.open('session-A');
  const a = deferredFile('A.json', 'Old import while A selected'), pending = h.select(a.file);
  await h.open('session-B');
  const draft = JSON.stringify(fixture('session-B', 'Unsaved B after switch'), null, 4) + '\n';
  h.edit(draft);
  const before = h.state();
  a.finish(); await pending;
  const after = h.state();
  const checks = { new_session_identity_retained: after.current && after.current.id === 'session-B',
    exact_new_session_draft_retained: after.editor === draft,
    new_session_saved_baseline_retained: after.saved_editor === before.saved_editor,
    dirty_new_session_analysis_stays_disabled: after.analyze_disabled === true,
    no_spurious_discard_confirmation: h.confirmations.length === 0 };
  return { id: 'MVP-IMPORT-SESSION-SWITCH', passed: checksPassed(checks), checks, actual: observed(h) };
}

async function dirtyDraftCancellation() {
  const h = harness();
  await h.open('session-A');
  const draft = JSON.stringify(fixture('session-A', 'Dirty current draft'), null, 4) + '\n';
  h.edit(draft);
  const before = h.state(), a = deferredFile('A.json', 'Cancelled replacement import');
  h.cancelConfirmation();
  const pending = h.select(a.file);
  a.finish(); await pending;
  const after = h.state();
  const checks = { discard_confirmation_offered: h.confirmations.length === 1,
    cancellation_retains_current_identity: after.current && after.current.id === 'session-A',
    cancellation_retains_exact_draft: after.editor === draft,
    cancellation_retains_saved_baseline: after.saved_editor === before.saved_editor,
    cancellation_keeps_analysis_disabled: after.analyze_disabled === true };
  return { id: 'MVP-IMPORT-DIRTY-CANCEL', passed: checksPassed(checks), checks, actual: observed(h) };
}

async function staleFailureKeepsLatestNotice(readRejects) {
  const h = harness(), a = deferredFile('A.json', 'Abandoned erroneous file A'), b = deferredFile('B.json', 'Latest valid file B');
  const pa = h.select(a.file), pb = h.select(b.file);
  b.finish(); await pb;
  const before = h.state();
  if (readRejects) a.rejectRead();
  else a.finishMalformed();
  await pa;
  const after = h.state();
  const checks = { latest_successful_import_retained: after.editor === JSON.stringify(JSON.parse(b.body), null, 2),
    latest_successful_notice_retained: after.notice === before.notice && !after.notice.startsWith('처리하지 못했습니다'),
    no_spurious_discard_confirmation: h.confirmations.length === 0 };
  return { id: readRejects ? 'MVP-IMPORT-STALE-READ-ERROR' : 'MVP-IMPORT-STALE-PARSE-ERROR',
    passed: checksPassed(checks), checks, actual: { notice_before_old_failure: before.notice, final: observed(h) } };
}

async function run() {
  const tests = [() => latestSelectionWins(true), () => latestSelectionWins(false),
    clearedSelectionInvalidatesRead, sessionSwitchInvalidatesRead, dirtyDraftCancellation,
    () => staleFailureKeepsLatestNotice(false), () => staleFailureKeepsLatestNotice(true)];
  const results = [];
  for (const [index, test] of tests.entries()) {
    try { results.push(await test()); }
    catch (error) { results.push({ id: 'MVP-IMPORT-HARNESS-' + index, passed: false, harness_error: error.stack }); }
  }
  const evidence = { scope: 'Synthetic JSON import read ordering, selection invalidation, session transition, and dirty-draft cancellation only',
    verifier: 'Node VM DOM/File stubs with deferred file.text promises; not browser E2E or real LoL evidence',
    evidence_kind: 'FRESH_EXECUTION', executed_at: new Date().toISOString(), node_version: process.version,
    source_path: 'web_r4/app.js', loaded_source_path: sourcePath, source_sha256: hash(source),
    fixture_path: 'examples/r3/compare-wait-retreat.json', fixture_sha256: hash(fixtureBytes),
    test_path: 'tests_mvp/ui_import_races.cjs', test_sha256: hash(fs.readFileSync(__filename)),
    passed: results.filter(result => result.passed).length, total: results.length, results };
  console.log(JSON.stringify(evidence));
  process.exitCode = evidence.passed === evidence.total ? 0 : 1;
}

if (process.argv[2] === '--run') {
  run().catch(error => { console.error(error.stack); process.exitCode = 1; });
} else {
  const destination = path.resolve(process.argv[2] || path.join(root, 'evidence/mvp/import-race-after.json'));
  const initialReceipt = path.basename(destination) === 'import-race-before.json';
  if (initialReceipt && fs.existsSync(destination)) throw Error('Refusing to overwrite immutable initial failure receipt: ' + destination);
  const startedAt = new Date().toISOString();
  const child = spawnSync(process.execPath, [__filename, '--run', sourcePath], { encoding: 'utf8', timeout: 30000 });
  const finishedAt = new Date().toISOString();
  let evidence;
  try { evidence = JSON.parse(child.stdout); }
  catch { evidence = { results: [], source_sha256: hash(source), runner_error: 'Child output was not valid JSON' }; }
  evidence.process = { command: [process.execPath, 'tests_mvp/ui_import_races.cjs', '--run', sourcePath],
    started_at: startedAt, finished_at: finishedAt, exit_code: child.status, signal: child.signal,
    stdout: child.stdout, stderr: child.stderr, error: child.error ? child.error.message : null };
  fs.mkdirSync(path.dirname(destination), { recursive: true });
  fs.writeFileSync(destination, JSON.stringify(evidence, null, 2) + '\n', { flag: initialReceipt ? 'wx' : 'w' });
  console.log(JSON.stringify({ source_sha256: evidence.source_sha256, passed: evidence.passed, total: evidence.total,
    exit_code: child.status, results: evidence.results.map(result => ({ id: result.id, passed: result.passed,
      failed_checks: Object.entries(result.checks || {}).filter(([, passed]) => !passed).map(([id]) => id) })) }));
  process.exitCode = child.status === 0 ? 0 : 1;
}

'use strict';
// Deterministic Node VM + DOM stub regressions. These are not browser E2E tests.
// The stub server enforces revision preconditions and captures requests before
// response delivery. Each test uses the repository's synthetic TEST fixture.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const { spawnSync } = require('node:child_process');
const root = path.resolve(__dirname, '..');
const sourcePath = path.join(root, 'web_r4/app.js');
const source = fs.readFileSync(sourcePath, 'utf8');
const baseFixture = JSON.parse(fs.readFileSync(path.join(root, 'examples/r3/compare-wait-retreat.json'), 'utf8'));
const clone = value => JSON.parse(JSON.stringify(value));
const hash = value => crypto.createHash('sha256').update(value).digest('hex');

function fixture(sessionId, objective) {
  const value = clone(baseFixture);
  value.snapshot_request.session_id = sessionId;
  value.observations.forEach(observation => { observation.session_id = sessionId; });
  value.objective = objective;
  return value;
}

function deferred() {
  let resolve;
  const promise = new Promise(done => { resolve = done; });
  return { promise, resolve };
}

function harness() {
  const elements = new Map(), requests = [], confirmations = [], server = new Map();
  const gates = [];
  let createCounter = 0, keyCounter = 0, confirmAnswer = true;
  for (const id of ['session-A', 'session-B']) server.set(id, {
    session: { id, title: id, patch: 'SYNTHETIC-1', mode: 'TEST', revision: 1 },
    case: fixture(id, 'Saved ' + id)
  });
  function element(id) {
    if (!elements.has(id)) elements.set(id, {
      value: '', hidden: false, disabled: false, textContent: '', className: '',
      files: [], listeners: {}, children: [], selectedOptions: [{ textContent: 'Synthetic fixture' }],
      addEventListener(type, callback) { this.listeners[type] = callback; },
      replaceChildren(...children) { this.children = children; },
      append(...children) { this.children.push(...children); }
    });
    return elements.get(id);
  }
  function response(data, status = 200) {
    return { ok: status >= 200 && status < 300, status, json: async () => clone(data) };
  }
  function handle(request) {
    const { route, method, body } = request;
    if (route === '/sessions' && method === 'GET') return response([...server.values()].map(row => row.session));
    if (route === '/sessions' && method === 'POST') {
      const id = 'created-' + (++createCounter);
      const session = { id, title: body.title, patch: body.patch, mode: body.mode, revision: 0 };
      server.set(id, { session, case: null });
      return response(session, 201);
    }
    const match = /^\/sessions\/([^/]+)(?:\/(case|reviews))?$/.exec(route);
    if (!match || !server.has(match[1])) throw new Error('Unexpected request: ' + method + ' ' + route);
    const record = server.get(match[1]);
    if (method === 'GET' && !match[2]) return response(record.session);
    if (method === 'GET' && match[2] === 'reviews') return response([]);
    if (method === 'GET' && match[2] === 'case') return response({ revision: record.session.revision, case: record.case });
    if (method === 'PUT' && match[2] === 'case') {
      if (body.expected_revision !== record.session.revision) return response({ error_code: 'REVISION_CONFLICT' }, 409);
      if (body.case.mode !== 'TEST' || body.case.evidence_kind !== 'SYNTHETIC') throw new Error('Non-synthetic save fixture');
      if (body.case.snapshot_request.session_id !== match[1] || body.case.observations.some(row => row.session_id !== match[1])) throw new Error('Save fixture session mismatch');
      record.case = clone(body.case);
      record.session.revision++;
      return response({ revision: record.session.revision, case: record.case });
    }
    throw new Error('Unexpected request: ' + method + ' ' + route);
  }
  const context = vm.createContext({
    document: { getElementById: element, createElement: () => element(Symbol()) },
    sessionStorage: { getItem: () => '', setItem() {}, removeItem() {} },
    confirm: message => { confirmations.push(message); return confirmAnswer; },
    setTimeout, clearTimeout, console,
    crypto: { randomUUID: () => 'test-idempotency-' + (++keyCounter) },
    fetch: async (url, options) => {
      const request = { route: url.replace(/^\/dev\/v1/, ''), method: options.method,
        body: options.body === undefined ? undefined : JSON.parse(options.body),
        idempotency_key: options.headers['Idempotency-Key'] || null };
      requests.push(request);
      const reply = handle(request);
      const index = gates.findIndex(gate => gate.method === request.method && gate.route === request.route);
      if (index === -1) return reply;
      const gate = gates.splice(index, 1)[0];
      gate.requested.resolve(request);
      await gate.release.promise;
      return reply;
    }
  });
  vm.runInContext(source, context, { filename: 'web_r4/app.js' });
  const evaluate = code => vm.runInContext(code, context);
  return {
    element, requests, confirmations, server, evaluate,
    state: () => JSON.parse(evaluate("JSON.stringify({current,editor:$('case-json').value,saved_editor:savedEditor,analyze_disabled:$('analyze').disabled,save_disabled:$('save-case').disabled,current_label:$('current').textContent})")),
    open: id => evaluate('openSession(' + JSON.stringify(id) + ')'),
    save: () => evaluate('save()'),
    reset: () => evaluate('reset()'),
    edit(value) { element('case-json').value = value; element('case-json').listeners.input(); },
    cancelReopen() { confirmAnswer = false; },
    delay(method, route) {
      const gate = { method, route, requested: deferred(), release: deferred() };
      gates.push(gate);
      return { requested: gate.requested.promise, release: () => gate.release.resolve() };
    }
  };
}

function observation(h, expectedEditor) {
  const state = h.state();
  return { session_id: state.current && state.current.id, client_revision: state.current && state.current.revision,
    editor_objective: (() => { try { return JSON.parse(state.editor).objective; } catch { return null; } })(),
    exact_editor_retained: expectedEditor === undefined ? undefined : state.editor === expectedEditor,
    editor_sha256: hash(state.editor), saved_editor_sha256: hash(state.saved_editor),
    editor_equals_saved: state.editor === state.saved_editor, analyze_disabled: state.analyze_disabled,
    save_disabled: state.save_disabled, current_label: state.current_label };
}
const canonical = (h, id) => JSON.stringify(h.server.get(id).case, null, 2);
const checksPassed = checks => Object.values(checks).every(Boolean);

async function existingSaveWithTyping() {
  const h = harness();
  await h.open('session-A');
  h.edit(JSON.stringify(fixture('session-A', 'Submitted edit')));
  const gate = h.delay('PUT', '/sessions/session-A/case');
  const pending = h.save();
  await gate.requested;
  const draft = JSON.stringify(fixture('session-A', 'Typed while v2 PUT pending'), null, 4) + '\n';
  h.edit(draft);
  gate.release();
  await pending;
  const acknowledged = h.state(), firstActual = observation(h, draft);
  const firstServer = clone(h.server.get('session-A'));
  let nextError = null;
  try { await h.save(); } catch (error) { nextError = { message: error.message, status: error.status }; }
  const puts = h.requests.filter(request => request.method === 'PUT');
  const final = h.state();
  const checks = {
    server_saved_first_payload_as_v2: firstServer.session.revision === 2 && firstServer.case.objective === 'Submitted edit',
    acknowledged_v2: acknowledged.current && acknowledged.current.revision === 2,
    exact_draft_retained: acknowledged.editor === draft,
    canonical_saved_baseline_recorded: acknowledged.saved_editor === JSON.stringify(fixture('session-A', 'Submitted edit'), null, 2),
    analysis_disabled_for_dirty_draft: acknowledged.analyze_disabled === true,
    next_save_expected_revision_2: puts.length === 2 && puts[1].body.expected_revision === 2,
    next_save_succeeds_as_v3: nextError === null && final.current && final.current.revision === 3 && h.server.get('session-A').session.revision === 3,
    next_save_canonical_and_analyzable: final.editor === canonical(h, 'session-A') && final.saved_editor === final.editor && final.analyze_disabled === false
  };
  return { id: 'MVP-SAVE-TYPING-REVISION', passed: checksPassed(checks), checks,
    actual: { after_delayed_ack: firstActual, server_after_delayed_ack: { revision: firstServer.session.revision, saved_objective: firstServer.case.objective }, after_next_save: observation(h), next_save_error: nextError,
      put_expected_revisions: puts.map(request => request.body.expected_revision), server_revision: h.server.get('session-A').session.revision } };
}

async function unchangedEditorCanonicalSave() {
  const h = harness();
  await h.open('session-A');
  const submitted = JSON.stringify(fixture('unassigned-fixture', 'Canonical save'));
  h.edit(submitted);
  const gate = h.delay('PUT', '/sessions/session-A/case');
  const pending = h.save();
  await gate.requested;
  gate.release();
  await pending;
  const state = h.state(), expected = canonical(h, 'session-A');
  const checks = { revision_2_acknowledged: state.current.revision === 2,
    canonical_response_replaces_unchanged_editor: state.editor === expected && state.editor !== submitted,
    saved_baseline_matches_canonical: state.saved_editor === expected,
    analysis_enabled: state.analyze_disabled === false };
  return { id: 'MVP-SAVE-UNCHANGED-CANONICAL', passed: checksPassed(checks), checks,
    actual: { ...observation(h), server_revision: h.server.get('session-A').session.revision } };
}

async function createWithTyping() {
  const h = harness();
  h.element('title').value = 'Created case';
  h.edit(JSON.stringify(fixture('unassigned-fixture', 'Submitted new case')));
  const gate = h.delay('POST', '/sessions');
  const pending = h.save();
  await gate.requested;
  const draft = JSON.stringify(fixture('unassigned-fixture', 'Typed during create POST'), null, 4) + '\n';
  h.edit(draft);
  gate.release();
  await pending;
  const state = h.state(), record = h.server.get('created-1');
  const checks = { created_identity_acknowledged: state.current && state.current.id === 'created-1',
    created_case_saved_and_revision_acknowledged: record.session.revision === 1 && state.current && state.current.revision === 1,
    saved_original_submission: record.case && record.case.objective === 'Submitted new case',
    exact_later_draft_retained: state.editor === draft,
    saved_baseline_matches_created_case: record.case && state.saved_editor === canonical(h, 'created-1'),
    analysis_disabled_for_dirty_draft: state.analyze_disabled === true };
  return { id: 'MVP-CREATE-TYPING-ACK', passed: checksPassed(checks), checks,
    actual: { ...observation(h, draft), server_revision: record.session.revision,
      server_saved_objective: record.case && record.case.objective,
      case_put_expected_revisions: h.requests.filter(request => request.method === 'PUT').map(request => request.body.expected_revision) } };
}

async function oldSaveAfterSessionSwitch() {
  const h = harness();
  await h.open('session-A');
  h.edit(JSON.stringify(fixture('session-A', 'A save before switch')));
  const gate = h.delay('PUT', '/sessions/session-A/case');
  const pending = h.save();
  await gate.requested;
  h.reset();
  await h.open('session-B');
  const draft = JSON.stringify(fixture('session-B', 'Unsaved B after reset and switch'), null, 4) + '\n';
  h.edit(draft);
  const before = h.state();
  gate.release();
  await pending;
  const after = h.state();
  const checks = { b_identity_and_revision_preserved: after.current.id === 'session-B' && after.current.revision === 1,
    exact_b_draft_preserved: after.editor === draft,
    b_saved_baseline_preserved: after.saved_editor === before.saved_editor,
    b_current_label_preserved: after.current_label === before.current_label,
    b_analysis_stays_disabled: after.analyze_disabled === true,
    a_server_save_committed: h.server.get('session-A').session.revision === 2,
    b_server_revision_unchanged: h.server.get('session-B').session.revision === 1 };
  return { id: 'MVP-OLD-SAVE-RESET-SWITCH', passed: checksPassed(checks), checks, actual: observation(h, draft) };
}

async function cancelDirtyReopen(refreshedButton) {
  const h = harness();
  await h.open('session-A');
  const draft = JSON.stringify(fixture('session-A', 'Dirty draft before reopen'), null, 4) + '\n';
  h.edit(draft);
  const before = h.state();
  h.cancelReopen();
  if (refreshedButton) {
    await h.evaluate('refresh()');
    const button = h.element('sessions').children.find(row => row.textContent.startsWith('session-A ·'));
    if (!button) throw new Error('Refreshed session-A button not rendered by DOM stub');
    await button.listeners.click();
  } else await h.open('session-A');
  const state = h.state();
  const checks = { discard_confirmation_offered: h.confirmations.length === 1,
    cancellation_retains_identity_and_revision: state.current && state.current.id === 'session-A' && state.current.revision === 1,
    cancellation_retains_exact_draft: state.editor === draft,
    cancellation_retains_saved_baseline: state.saved_editor === before.saved_editor,
    cancellation_keeps_analysis_disabled: state.analyze_disabled === true };
  return { id: refreshedButton ? 'MVP-DIRTY-REFRESHED-REOPEN-CANCEL' : 'MVP-DIRTY-CURRENT-REOPEN-CANCEL',
    passed: checksPassed(checks), checks, actual: { ...observation(h, draft), confirmation_messages: h.confirmations } };
}

async function oldCreateAfterReset() {
  const h = harness();
  h.element('title').value = 'Old pending creation';
  h.edit(JSON.stringify(fixture('unassigned-fixture', 'Old creation submission')));
  const gate = h.delay('POST', '/sessions');
  const pending = h.save();
  await gate.requested;
  h.reset();
  const draft = JSON.stringify(fixture('unassigned-fixture', 'New draft after reset'), null, 4) + '\n';
  h.edit(draft);
  gate.release();
  await pending;
  const state = h.state();
  const checks = { old_create_not_associated: state.current === null,
    new_exact_draft_retained: state.editor === draft,
    no_case_save_for_abandoned_creation: h.requests.filter(request => request.method === 'PUT').length === 0,
    abandoned_server_session_has_no_saved_case: h.server.get('created-1').session.revision === 0 && h.server.get('created-1').case === null,
    analysis_stays_disabled: state.analyze_disabled === true };
  return { id: 'MVP-OLD-CREATE-AFTER-RESET', passed: checksPassed(checks), checks,
    actual: { ...observation(h, draft), abandoned_server_revision: h.server.get('created-1').session.revision } };
}

async function run() {
  const results = [];
  for (const test of [existingSaveWithTyping, unchangedEditorCanonicalSave, createWithTyping,
    oldSaveAfterSessionSwitch, () => cancelDirtyReopen(false), () => cancelDirtyReopen(true), oldCreateAfterReset]) {
    try { results.push(await test()); }
    catch (error) { results.push({ id: test.name || 'anonymous', passed: false, harness_error: error.stack }); }
  }
  const evidence = { scope: 'Synthetic session save acknowledgements, exact draft retention, revision preconditions, navigation cancellation, and stale responses only',
    verifier: 'Node VM DOM stub with deterministic deferred HTTP responses; not browser E2E or real LoL evidence',
    executed_at: new Date().toISOString(), node_version: process.version, source_path: 'web_r4/app.js',
    source_sha256: hash(source), fixture_path: 'examples/r3/compare-wait-retreat.json',
    fixture_sha256: hash(fs.readFileSync(path.join(root, 'examples/r3/compare-wait-retreat.json'))),
    evidence_kind: 'FRESH_EXECUTION', passed: results.filter(result => result.passed).length, total: results.length, results };
  console.log(JSON.stringify(evidence));
  process.exitCode = evidence.passed === evidence.total ? 0 : 1;
}

if (process.argv[2] === '--run') {
  run().catch(error => { console.error(error.stack); process.exitCode = 1; });
} else {
  const destination = path.resolve(process.argv[2] || path.join(root, 'evidence/mvp/save-race-after.json'));
  if (path.basename(destination) === 'save-race-before.json' && fs.existsSync(destination)) {
    throw new Error('Refusing to overwrite immutable initial failure receipt: ' + destination);
  }
  const startedAt = new Date().toISOString();
  const child = spawnSync(process.execPath, [__filename, '--run'], { encoding: 'utf8', timeout: 30000 });
  const finishedAt = new Date().toISOString();
  let evidence;
  try { evidence = JSON.parse(child.stdout); }
  catch { evidence = { verifier: 'Node VM DOM stub; not browser E2E', source_sha256: hash(source), results: [], runner_error: 'Child output was not valid JSON' }; }
  evidence.process = { command: [process.execPath, 'tests_mvp/ui_save_race.cjs', '--run'],
    started_at: startedAt, finished_at: finishedAt, exit_code: child.status, signal: child.signal,
    stdout: child.stdout, stderr: child.stderr, error: child.error ? child.error.message : null };
  fs.mkdirSync(path.dirname(destination), { recursive: true });
  fs.writeFileSync(destination, JSON.stringify(evidence, null, 2) + '\n', { flag: path.basename(destination) === 'save-race-before.json' ? 'wx' : 'w' });
  console.log(JSON.stringify({ source_sha256: evidence.source_sha256, passed: evidence.passed, total: evidence.total,
    exit_code: child.status, results: evidence.results.map(result => ({ id: result.id, passed: result.passed, failed_checks: Object.entries(result.checks || {}).filter(([, passed]) => !passed).map(([id]) => id) })) }));
  process.exitCode = child.status === 0 ? 0 : 1;
}

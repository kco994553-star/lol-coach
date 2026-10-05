'use strict';
// Actual Chromium + coach_v1.server test. route.fetch() commits the real PUT;
// only delivery of that response is held while a real textarea input is edited.
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const output = process.env.MVP_BROWSER_EVIDENCE_DIR;
if (!output || !process.env.WORKBENCH_URL || !process.env.WORKBENCH_TOKEN_FILE) throw new Error('Run through scripts/browser_mvp.py with an isolated server');
const token = fs.readFileSync(process.env.WORKBENCH_TOKEN_FILE, 'utf8').trim();
const redact = value => String(value).split(token).join('[REDACTED]');
const hash = value => crypto.createHash('sha256').update(value).digest('hex');
const sourcePaths = ['web_r4/app.js', 'web_r4/index.html', 'web_r4/styles.css', 'coach_v1/server.py', 'coach_v1/storage.py', 'examples/r3/compare-wait-retreat.json', 'tests_mvp/browser_save_race.cjs', 'scripts/browser_mvp.py'];
const sourceHashes = () => Object.fromEntries(sourcePaths.map(file => [file, hash(fs.readFileSync(path.join(root, file)))]));
const checks = [], pageErrors = [], dialogs = [], writes = [], snapshots = [], backendSnapshots = [];
const startedAt = new Date().toISOString();
const initialHashes = sourceHashes();
let browser, page, stage = 'browser-launch', firstFailure = null, releaseHeldResponse;

function check(id, passed, actual) {
  checks.push({ id, passed: Boolean(passed), actual });
  if (!passed) throw new Error('Failed check: ' + id);
}
function deferred() {
  let resolve, reject;
  const promise = new Promise((done, fail) => { resolve = done; reject = fail; });
  return { promise, resolve, reject };
}
async function withTimeout(promise, milliseconds, label) {
  let timer;
  try {
    return await Promise.race([promise, new Promise((_, reject) => {
      timer = setTimeout(() => reject(new Error(label + ' timed out after ' + milliseconds + 'ms')), milliseconds);
    })]);
  } finally { clearTimeout(timer); }
}
async function uiSnapshot(label, expectedEditor) {
  const state = await page.evaluate(() => ({
    current_label: document.getElementById('current').textContent,
    editor: document.getElementById('case-json').value,
    analyze_disabled: document.getElementById('analyze').disabled,
    save_disabled: document.getElementById('save-case').disabled,
    report_hidden: document.getElementById('report-panel').hidden,
    notice: document.getElementById('notice').textContent
  }));
  const recorded = { label, observed_at: new Date().toISOString(), current_label: state.current_label,
    editor_sha256: hash(state.editor), exact_editor_match: expectedEditor === undefined ? undefined : state.editor === expectedEditor,
    editor_objective: (() => { try { return JSON.parse(state.editor).objective; } catch { return null; } })(),
    analyze_disabled: state.analyze_disabled, save_disabled: state.save_disabled,
    report_hidden: state.report_hidden, notice: state.notice };
  snapshots.push(recorded);
  return state;
}
async function serverCase(id, label) {
  const response = await page.context().request.get(process.env.WORKBENCH_URL + '/dev/v1/sessions/' + id + '/case', {
    headers: { Authorization: 'Bearer ' + token }
  });
  const body = await response.json();
  backendSnapshots.push({ label, observed_at: new Date().toISOString(), http_status: response.status(),
    session_id: body.session_id, revision: body.revision, objective: body.case && body.case.objective,
    case_sha256: body.case ? hash(JSON.stringify(body.case)) : null });
  check(label + '-backend-200', response.status() === 200, { status: response.status() });
  return body;
}
async function cancelNativeDialog(label, action, draft, currentLabel) {
  stage = label;
  const dialogPromise = page.waitForEvent('dialog');
  const actionPromise = Promise.resolve().then(action);
  const actionFailure = actionPromise.then(() => new Promise(() => {}), error => { throw error; });
  const dialog = await Promise.race([dialogPromise, actionFailure]);
  const record = { action: label, type: dialog.type(), message: dialog.message(), response: 'dismiss' };
  dialogs.push(record);
  await dialog.dismiss();
  await actionPromise;
  const state = await uiSnapshot(label + '-after-cancel', draft);
  check(label + '-native-confirm', record.type === 'confirm', record);
  check(label + '-exact-draft-retained', state.editor === draft, { editor_sha256: hash(state.editor), expected_sha256: hash(draft) });
  check(label + '-current-session-retained', state.current_label === currentLabel, { current_label: state.current_label });
  check(label + '-analysis-disabled', state.analyze_disabled === true, { analyze_disabled: state.analyze_disabled });
}

async function run() {
  try {
    browser = await chromium.launch({ headless: true, executablePath: process.env.CHROMIUM_EXECUTABLE || undefined,
      args: ['--no-sandbox'] });
    page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    page.setDefaultTimeout(15000);
    page.on('pageerror', error => pageErrors.push(redact(error.message)));
    page.on('request', request => {
      if (!['POST', 'PUT', 'DELETE'].includes(request.method()) || !request.url().includes('/dev/v1/')) return;
      let body;
      try { body = request.postDataJSON(); } catch { body = null; }
      writes.push({ at: new Date().toISOString(), route: new URL(request.url()).pathname, method: request.method(),
        expected_revision: body && body.expected_revision, objective: body && body.case && body.case.objective,
        title: body && body.title });
    });
    stage = 'login-and-initial-v1-save';
    await page.goto(process.env.WORKBENCH_URL);
    await page.fill('#token', token);
    await page.click('#login-form button');
    await page.waitForSelector('#workspace:visible');
    await page.selectOption('#example', 'compare-wait-retreat');
    await page.click('#load-example');
    await page.waitForFunction(() => document.getElementById('case-json').value.length > 100);
    await page.locator('details').filter({ has: page.locator('#case-json') }).locator('summary').click();
    await page.fill('#title', 'MVP actual browser save race');
    const initialResponsePromise = page.waitForResponse(response => response.request().method() === 'PUT' && response.url().endsWith('/case'));
    await page.click('#save-case');
    const initialResponse = await initialResponsePromise;
    const initialResult = await initialResponse.json();
    const sid = initialResult.session_id;
    const matchingCaseIds = initialResult.case && initialResult.case.snapshot_request.session_id === sid &&
      initialResult.case.observations.every(observation => observation.session_id === sid);
    check('initial-real-save-v1', initialResponse.status() === 200 && initialResult.revision === 1 && Boolean(sid) && matchingCaseIds &&
      initialResult.case.mode === 'TEST' && initialResult.case.evidence_kind === 'SYNTHETIC', {
      http_status: initialResponse.status(), session_id: sid, revision: initialResult.revision,
      request_expected_revision: initialResponse.request().postDataJSON().expected_revision,
      snapshot_session_id: initialResult.case && initialResult.case.snapshot_request.session_id,
      all_observation_session_ids_match_actual_server_id: Boolean(matchingCaseIds) });
    await page.waitForFunction(() => document.getElementById('current').textContent.includes('저장 버전 1') && !document.getElementById('save-case').disabled);
    const initialStored = await serverCase(sid, 'initial-v1');
    check('initial-v1-independently-stored', initialStored.revision === 1, { revision: initialStored.revision });

    stage = 'real-v2-commit-with-held-response';
    const submitted = JSON.parse(await page.inputValue('#case-json'));
    submitted.objective = 'Browser submitted edit for v2';
    await page.fill('#case-json', JSON.stringify(submitted));
    const committed = deferred(), held = deferred();
    releaseHeldResponse = () => held.resolve();
    let intercepted = false;
    const routePattern = '**/dev/v1/sessions/' + sid + '/case';
    const intercept = async route => {
      if (route.request().method() !== 'PUT' || intercepted) return route.continue();
      intercepted = true;
      try {
        const backendResponse = await route.fetch();
        const body = await backendResponse.json();
        committed.resolve({ status: backendResponse.status(), body, request: route.request().postDataJSON() });
        await held.promise;
        await route.fulfill({ response: backendResponse });
      } catch (error) { committed.reject(error); await route.abort().catch(() => {}); }
    };
    await page.route(routePattern, intercept);
    await page.click('#save-case');
    const actualCommit = await withTimeout(committed.promise, 15000, 'Real backend PUT interception');
    check('held-put-actually-commits-v2', actualCommit.status === 200 && actualCommit.body.revision === 2 && actualCommit.request.expected_revision === 1,
      { http_status: actualCommit.status, committed_revision: actualCommit.body.revision, request_expected_revision: actualCommit.request.expected_revision });
    const serverWhileHeld = await serverCase(sid, 'backend-v2-before-browser-ack');
    check('backend-v2-visible-before-response-release', serverWhileHeld.revision === 2 && serverWhileHeld.case.objective === submitted.objective,
      { revision: serverWhileHeld.revision, objective: serverWhileHeld.case.objective });
    const newer = JSON.parse(JSON.stringify(submitted));
    newer.objective = 'Browser newer draft while v2 response held';
    const exactDraft = JSON.stringify(newer, null, 4) + '\n';
    await page.fill('#case-json', exactDraft);
    const beforeAck = await uiSnapshot('typed-draft-before-release', exactDraft);
    check('draft-entered-before-v2-ack', beforeAck.current_label.includes('저장 버전 1') && beforeAck.editor === exactDraft && beforeAck.save_disabled,
      { current_label: beforeAck.current_label, exact_draft: beforeAck.editor === exactDraft, save_disabled: beforeAck.save_disabled });
    releaseHeldResponse();
    await page.waitForFunction(() => document.getElementById('current').textContent.includes('저장 버전 2') && !document.getElementById('save-case').disabled);
    await page.unroute(routePattern, intercept);
    const afterAck = await uiSnapshot('after-real-v2-ack', exactDraft);
    check('real-v2-ack-exact-draft-retained', afterAck.editor === exactDraft, { exact_draft: afterAck.editor === exactDraft });
    check('real-v2-ack-analysis-disabled', afterAck.analyze_disabled === true, { analyze_disabled: afterAck.analyze_disabled });

    stage = 'next-real-save-v3';
    const nextResponsePromise = page.waitForResponse(response => response.request().method() === 'PUT' && response.url().endsWith('/sessions/' + sid + '/case'));
    await page.click('#save-case');
    const nextResponse = await nextResponsePromise;
    const nextResult = await nextResponse.json();
    const nextRequest = nextResponse.request().postDataJSON();
    check('next-real-put-expects-v2-and-saves-v3', nextRequest.expected_revision === 2 && nextResponse.status() === 200 && nextResult.revision === 3,
      { request_expected_revision: nextRequest.expected_revision, http_status: nextResponse.status(), committed_revision: nextResult.revision });
    await page.waitForFunction(() => document.getElementById('current').textContent.includes('저장 버전 3') && !document.getElementById('analyze').disabled);
    const canonicalV3 = JSON.stringify(nextResult.case, null, 2);
    const savedV3 = await uiSnapshot('after-v3-save', canonicalV3);
    check('v3-save-canonical-editor', savedV3.editor === canonicalV3 && savedV3.analyze_disabled === false,
      { exact_canonical: savedV3.editor === canonicalV3, analyze_disabled: savedV3.analyze_disabled });
    const storedV3 = await serverCase(sid, 'backend-after-v3');
    let storedCaseMatchesAck = true;
    try { assert.deepStrictEqual(storedV3.case, nextResult.case); } catch { storedCaseMatchesAck = false; }
    check('backend-v3-has-newer-draft', storedV3.revision === 3 && storedV3.case.objective === newer.objective && storedCaseMatchesAck,
      { revision: storedV3.revision, objective: storedV3.case.objective, stored_case_semantically_matches_ack: storedCaseMatchesAck });
    const canonicalStoredV3 = JSON.stringify(storedV3.case, null, 2);

    stage = 'reload-persisted-v3';
    await page.reload();
    await page.waitForSelector('#workspace:visible');
    await page.waitForSelector('#sessions button');
    await page.locator('#sessions button').first().click();
    await page.waitForFunction(() => document.getElementById('current').textContent.includes('저장 버전 3'));
    const reloaded = await uiSnapshot('reloaded-v3', canonicalStoredV3);
    check('reload-reopens-real-v3', reloaded.editor === canonicalStoredV3 && !reloaded.analyze_disabled && storedCaseMatchesAck,
      { exact_canonical_from_stored_get: reloaded.editor === canonicalStoredV3, current_label: reloaded.current_label,
        analyze_disabled: reloaded.analyze_disabled, stored_case_semantically_matches_ack: storedCaseMatchesAck,
        ack_editor_sha256: hash(canonicalV3), stored_get_editor_sha256: hash(canonicalStoredV3),
        reloaded_editor_sha256: hash(reloaded.editor) });

    stage = 'one-real-synthetic-analysis';
    const reviewPostPromise = page.waitForResponse(response => response.request().method() === 'POST' && response.url().endsWith('/sessions/' + sid + '/reviews'));
    await page.click('#analyze');
    const reviewResponse = await reviewPostPromise;
    const reviewJob = await reviewResponse.json();
    await page.waitForSelector('#report-panel:visible');
    const report = JSON.parse(await page.locator('#report-json').textContent());
    check('real-synthetic-analysis-of-v3', reviewResponse.status() === 202 && reviewJob.input_revision === 3 && report.input_revision === 3 && !report.stale && report.result.objective === newer.objective,
      { submission_status: reviewResponse.status(), job_id: reviewJob.id, job_input_revision: reviewJob.input_revision,
        report_input_revision: report.input_revision, stale: report.stale, objective: report.result.objective });
    await page.screenshot({ path: path.join(output, 'desktop-analysis.png'), fullPage: true });
    stage = '390px-overflow';
    await page.setViewportSize({ width: 390, height: 844 });
    const dimensions = await page.evaluate(() => ({ scroll_width: document.documentElement.scrollWidth, inner_width: innerWidth }));
    check('390px-no-horizontal-overflow', dimensions.scroll_width <= dimensions.inner_width, dimensions);
    await page.screenshot({ path: path.join(output, 'mobile-analysis.png'), fullPage: true });
    await page.setViewportSize({ width: 1280, height: 900 });

    stage = 'dirty-native-cancel-checks';
    await page.locator('details').filter({ has: page.locator('#case-json') }).locator('summary').click();
    const cancelCase = JSON.parse(canonicalStoredV3);
    cancelCase.objective = 'Browser dirty draft kept after native cancellation';
    const cancelDraft = JSON.stringify(cancelCase, null, 4) + '\n';
    await page.fill('#case-json', cancelDraft);
    const currentLabel = await page.locator('#current').textContent();
    const previousSessionButton = await page.locator('#sessions button').first().elementHandle();
    const refreshPromise = page.waitForResponse(response => response.request().method() === 'GET' && response.url().endsWith('/dev/v1/sessions'));
    await page.click('#refresh');
    await refreshPromise;
    await page.waitForFunction(button => !button.isConnected, previousSessionButton);
    await previousSessionButton.dispose();
    await page.waitForSelector('#sessions button');
    await cancelNativeDialog('dirty-refreshed-reopen-cancel', () => page.locator('#sessions button').first().click(), cancelDraft, currentLabel);
    await cancelNativeDialog('dirty-load-example-cancel', () => page.click('#load-example'), cancelDraft, currentLabel);
    const importCase = JSON.parse(canonicalStoredV3);
    importCase.objective = 'Imported replacement should be cancelled';
    await cancelNativeDialog('dirty-import-cancel', () => page.setInputFiles('#import-file', {
      name: 'synthetic-cancel.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(importCase))
    }), cancelDraft, currentLabel);
    await page.waitForFunction(() => document.getElementById('import-file').value === '');
    const finalStored = await serverCase(sid, 'backend-after-native-cancellations');
    check('native-cancellations-leave-backend-v3', finalStored.revision === 3 && finalStored.case.objective === newer.objective,
      { revision: finalStored.revision, objective: finalStored.case.objective });
    check('no-page-errors', pageErrors.length === 0, pageErrors);
    check('tested-source-unchanged-during-run', JSON.stringify(initialHashes) === JSON.stringify(sourceHashes()), sourceHashes());
  } catch (error) {
    firstFailure = { stage, observed_at: new Date().toISOString(), error: redact(error.stack || error.message) };
    if (page) {
      await uiSnapshot('first-failure-state').catch(() => {});
      await page.screenshot({ path: path.join(output, 'first-failure.png'), fullPage: true }).catch(() => {});
    }
  } finally {
    if (releaseHeldResponse) releaseHeldResponse();
    const receipt = { verifier: browser ? 'Actual Playwright Chromium browser with isolated coach_v1.server and SQLite; not Node VM' : 'Playwright Chromium launch attempt; browser did not start',
      scope: 'Affected synthetic save race, revision acknowledgement, exact draft retention, reload, native cancellation, one synthetic analysis, 390px overflow and page errors',
      evidence_kind: browser ? 'FRESH_BROWSER_EXECUTION' : 'BROWSER_LAUNCH_FAILURE', started_at: startedAt, finished_at: new Date().toISOString(),
      node_version: process.version, browser_version: browser ? browser.version() : null,
      source_sha256: initialHashes, passed: firstFailure === null && checks.every(item => item.passed),
      checks, backend_snapshots: backendSnapshots, ui_snapshots: snapshots, native_dialogs: dialogs,
      actual_browser_write_requests: writes, page_errors: pageErrors, first_failure: firstFailure };
    fs.writeFileSync(path.join(output, 'receipt.json'), redact(JSON.stringify(receipt, null, 2)) + '\n', { flag: 'wx' });
    console.log(JSON.stringify({ passed: receipt.passed, completed_checks: checks.length, browser_version: receipt.browser_version,
      first_failure: firstFailure, receipt_path: path.join(output, 'receipt.json') }));
    if (browser) await browser.close();
    process.exitCode = receipt.passed ? 0 : 1;
  }
}
run().catch(error => { console.error(redact(error.stack || error.message)); process.exitCode = 1; });

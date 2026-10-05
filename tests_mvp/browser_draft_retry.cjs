'use strict';
// Actual Chromium + HTTP + SQLite response-loss verification. The intercepted
// PUT is committed by the real server before its response is intentionally
// dropped; no response body or stored record is fabricated.
const crypto = require('node:crypto');

function deferred() {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}

async function bounded(promise, label) {
  let timer;
  try {
    return await Promise.race([promise, new Promise((_, reject) => {
      timer = setTimeout(() => reject(Error(label + ' timed out')), 15000);
    })]);
  } finally { clearTimeout(timer); }
}

module.exports = async function checkDraftRetry({ page, check, baseUrl, token }) {
  const unique = crypto.randomUUID();
  let directKey = 0;
  async function api(path, method = 'GET', data) {
    const headers = { Authorization: 'Bearer ' + token };
    if (method === 'POST' || method === 'PUT') headers['Idempotency-Key'] = 'browser-retry-fixture-' + (++directKey) + '-' + unique;
    const response = await page.context().request.fetch(baseUrl + '/dev/v1' + path,
      { method, headers, ...(data === undefined ? {} : { data }) });
    return { status: response.status(), body: await response.json() };
  }
  const capture = {
    title: 'Retry-safe browser draft ' + unique, phase: null, patch: null, observed_at: null,
    visible_picks: [{ side: 'ALLY', slot: 1, champion: 'Ahri' }], visible_bans: [], role_assignments: [],
    source: { author: 'Private browser operator', perspective: 'UNKNOWN',
      description: 'Committed response-loss retry test; still UNVERIFIED' }
  };
  const created = await api('/draft-captures', 'POST', { capture });
  if (created.status !== 201) throw Error('Retry fixture create failed: ' + created.status);

  await page.click('#show-draft');
  await page.click('#d-refresh');
  const selector = '#d-list button[data-capture-id="' + created.body.session_id + '"]';
  await page.waitForSelector(selector);
  await page.click(selector);
  await page.waitForFunction(id => dRecord && dRecord.session_id === id && dRecord.revision === 1,
    created.body.session_id);
  await page.fill('#d-title', 'Committed but response lost ' + unique);

  const path = '/dev/v1/draft-captures/' + created.body.session_id;
  const pattern = '**' + path;
  const committed = deferred();
  let intercepted = false;
  const handler = async route => {
    if (intercepted || route.request().method() !== 'PUT') return route.continue();
    intercepted = true;
    try {
      const request = route.request();
      const response = await route.fetch();
      const body = await response.json();
      committed.resolve({ status: response.status(), body, raw: request.postData(),
        key: request.headers()['idempotency-key'] || null });
      await route.abort('failed');
    } catch (error) {
      committed.reject(error);
      await route.abort('failed').catch(() => {});
    }
  };
  await page.route(pattern, handler);
  await page.click('#d-save');
  const first = await bounded(committed.promise, 'Committed response-loss PUT');
  await page.waitForFunction(() => document.getElementById('d-notice').textContent.includes('저장 응답을 받지 못했습니다') &&
    !document.getElementById('d-save').disabled);
  await page.unroute(pattern, handler);
  const afterLoss = await api('/draft-captures/' + created.body.session_id);
  const historyAfterLoss = await api('/draft-captures/' + created.body.session_id + '/history');
  const uiAfterLoss = await page.evaluate(() => ({ revision: dRecord.revision, dirty: dDirty,
    title: document.getElementById('d-title').value, notice: document.getElementById('d-notice').textContent }));
  check('draft-retry-actual-committed-response-loss-keeps-retryable-editor', first.status === 200 && first.key &&
    afterLoss.status === 200 && afterLoss.body.revision === 2 && historyAfterLoss.body.revision_count === 2 &&
    uiAfterLoss.revision === 1 && uiAfterLoss.dirty && uiAfterLoss.title === 'Committed but response lost ' + unique,
    { committed_status: first.status, backend_revision: afterLoss.body.revision,
      history_count: historyAfterLoss.body.revision_count, ui_loaded_revision: uiAfterLoss.revision,
      ui_dirty: uiAfterLoss.dirty, retry_key_present: Boolean(first.key) });

  const replayResponse = page.waitForResponse(response => response.request().method() === 'PUT' &&
    new URL(response.url()).pathname === path);
  await page.click('#d-save');
  const replay = await bounded(replayResponse, 'Idempotent browser replay');
  const replayBody = await replay.json();
  await page.waitForFunction(id => dRecord && dRecord.id === id && dRecord.revision === 2 && !dDirty,
    first.body.id);
  const replayRequest = replay.request();
  const historyAfterReplay = await api('/draft-captures/' + created.body.session_id + '/history');
  check('draft-retry-reuses-exact-key-and-body-without-extra-revision', replay.status() === 200 &&
    replayRequest.headers()['idempotency-key'] === first.key && replayRequest.postData() === first.raw &&
    replayBody.id === first.body.id && historyAfterReplay.body.revision_count === 2 &&
    historyAfterReplay.body.current_revision === 2,
    { replay_status: replay.status(), exact_key_reused: replayRequest.headers()['idempotency-key'] === first.key,
      exact_body_reused: replayRequest.postData() === first.raw, same_snapshot_id: replayBody.id === first.body.id,
      history_count: historyAfterReplay.body.revision_count });

  await page.fill('#d-title', 'Next acknowledged edit ' + unique);
  const nextResponse = page.waitForResponse(response => response.request().method() === 'PUT' &&
    new URL(response.url()).pathname === path);
  await page.click('#d-save');
  const next = await bounded(nextResponse, 'Next acknowledged browser save');
  const nextBody = await next.json();
  await page.waitForFunction(id => dRecord && dRecord.id === id && dRecord.revision === 3 && !dDirty,
    nextBody.id);
  const finalHistory = await api('/draft-captures/' + created.body.session_id + '/history');
  check('draft-retry-rotates-key-only-after-acknowledged-success', next.status() === 200 &&
    next.request().headers()['idempotency-key'] !== first.key && nextBody.revision === 3 &&
    finalHistory.body.revision_count === 3 && finalHistory.body.current_revision === 3,
    { next_status: next.status(), key_rotated: next.request().headers()['idempotency-key'] !== first.key,
      final_revision: nextBody.revision, history_count: finalHistory.body.revision_count });
};

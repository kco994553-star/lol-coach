'use strict';
// Genuine optimistic-write conflicts from coach_v1.server. An old HTTP 409 is
// fetched from the backend and its delivery held; no response or 401 is faked.
const crypto = require('node:crypto');
const fields = ['known', 'intention', 'alternative', 'outcome'];
function deferred() {let resolve, reject; const promise = new Promise((yes, no) => {resolve = yes; reject = no;}); return {promise, resolve, reject};}
async function bounded(promise, label) {
  let timer;
  try {return await Promise.race([promise, new Promise((_, reject) => {timer = setTimeout(() => reject(new Error(label + ' timed out')), 15000);})]);}
  finally {clearTimeout(timer);}
}
function same(a, b) {return JSON.stringify(a) === JSON.stringify(b);}

module.exports = async function checkResearchSaveErrors({page, check, baseUrl, token}) {
  const auth = {Authorization: 'Bearer ' + token}, writes = [];
  let a, b, heldRoute, releaseHeld;
  const track = request => {
    if (request.method() !== 'PUT') return;
    const route = new URL(request.url()).pathname;
    if (a && route === '/dev/v1/research/' + a + '/notes/overview') {
      const body = request.postDataJSON(); writes.push({route, expected_revision: body.expected_revision, note: body.note});
    }
  };
  page.on('request', track);
  async function api(route, method = 'GET', data) {
    const response = await page.context().request.fetch(baseUrl + '/dev/v1' + route, {method, headers: auth,
      ...(data === undefined ? {} : {data})});
    return {status: response.status(), body: await response.json()};
  }
  const noteRoute = id => '/research/' + id + '/notes/overview';
  async function snapshot() {
    return page.evaluate(fieldNames => ({
      resource_id: rResource && rResource.id, title: document.getElementById('r-title').textContent,
      note: rNote, edit: rEdit, dirty: rDirty, epoch: rEpoch,
      values: Object.fromEntries(fieldNames.map(field => [field, document.getElementById('r-' + field).value])),
      note_state: document.getElementById('r-note-state').textContent,
      notice: document.getElementById('r-notice').textContent,
      save_disabled: document.getElementById('r-save').disabled,
      note_disabled: document.getElementById('r-known').disabled,
      detail_hidden: document.getElementById('r-detail').hidden,
      history: {epoch: rHistoryEpoch, preview: rHistoryPreview,
        text: document.getElementById('r-history-preview').textContent,
        hidden: document.getElementById('r-history-preview').hidden,
        status: document.getElementById('r-history-state').textContent,
        selected: document.getElementById('r-history-revision').value,
        options: [...document.getElementById('r-history-revision').options].map(option => option.value),
        download_disabled: document.getElementById('r-history-download').disabled},
      authenticated: Boolean(sessionStorage.getItem('lol-coach-dev-token')),
      auth_panel_hidden: document.getElementById('auth-panel').hidden,
      workspace_hidden: document.getElementById('workspace').hidden,
      main_notice: document.getElementById('notice').textContent
    }), fields);
  }
  async function open(id, revision, discardDirty) {
    const button = '#r-list button[data-resource-id="' + id + '"]';
    let confirmation = null;
    if (discardDirty) {
      const dialogPending = page.waitForEvent('dialog'), clicked = page.click(button);
      const dialog = await bounded(dialogPending, 'Native unsaved-note navigation confirmation');
      confirmation = {type: dialog.type(), message: dialog.message(), response: 'accept'};
      await dialog.accept(); await clicked;
    } else await page.click(button);
    await page.waitForFunction(expected => rResource && rResource.id === expected.id && rNote &&
      rNote.resource_id === expected.id && rNote.anchor === 'overview' && rNote.revision === expected.revision &&
      !document.getElementById('r-known').disabled, {id, revision});
    return confirmation;
  }
  async function fillNote(note) {for (const field of fields) await page.fill('#r-' + field, note[field]);}
  const initialA = {known: 'A 최초 저장 근거', intention: 'A 최초 의도', alternative: 'A 최초 대안', outcome: 'A 최초 사후 기록'};
  const externalA2 = {known: 'A 다른 저장 경로의 v2 근거', intention: 'v2 의도', alternative: 'v2 대안', outcome: 'v2 사후 기록'};
  const externalA3 = {known: 'A 외부 갱신 v3 근거', intention: 'v3 의도', alternative: 'v3 대안', outcome: 'v3 사후 기록'};
  const staleDraftA = {known: 'A 오래된 expected1 초안 😀', intention: '오래된 A 의도', alternative: '오래된 A 대안', outcome: '오래된 A 결과'};
  const draftB = {known: 'B 새 미저장 근거\n늦은 A 오류가 지우면 안 됨', intention: 'B 새 의도 👀', alternative: 'B 조건부 대안', outcome: 'B 사후 결과는 별도'};
  const currentDraftA = {known: 'A 현재 expected2 초안\n409 후에도 그대로', intention: '현재 A 의도', alternative: '현재 A 대안 😀', outcome: '현재 A 사후 메모'};
  try {
    await page.reload();
    if (!(await page.evaluate(() => Boolean(sessionStorage.getItem('lol-coach-dev-token'))))) {
      await page.fill('#token', token); await page.click('#login-form button');
    }
    await page.waitForFunction(() => !document.getElementById('workspace').hidden &&
      document.getElementById('notice').textContent.startsWith('연결됐습니다.'));
    const unique = crypto.randomUUID();
    const sourceA = await api('/research', 'POST', {source_type: 'raw_json', title: 'Save error A ' + unique,
      raw_text: JSON.stringify({note: 'synthetic save-conflict A ' + unique})});
    const sourceB = await api('/research', 'POST', {source_type: 'raw_json', title: 'Save error B ' + unique,
      raw_text: JSON.stringify({note: 'synthetic save-conflict B ' + unique})});
    if (sourceA.status !== 201 || sourceB.status !== 201) throw new Error('Real save-conflict fixture creation failed');
    a = sourceA.body.id; b = sourceB.body.id;
    const first = await api(noteRoute(a), 'PUT', {note: initialA, expected_revision: 0});
    if (first.status !== 200 || first.body.revision !== 1) throw new Error('Real A v1 fixture save failed');
    await page.click('#show-research');
    await page.waitForSelector('#r-list button[data-resource-id="' + a + '"]');
    await open(a, 1, false); await fillNote(staleDraftA);
    const externallyAdvanced = await api(noteRoute(a), 'PUT', {note: externalA2, expected_revision: 1});
    if (externallyAdvanced.status !== 200 || externallyAdvanced.body.revision !== 2) throw new Error('Real external A v2 save failed');

    const fetched = deferred(), gate = deferred(), delivered = deferred();
    releaseHeld = () => gate.resolve();
    const pattern = '**/dev/v1' + noteRoute(a);
    const handler = async route => {
      if (route.request().method() !== 'PUT') return route.continue();
      try {
        const request = route.request().postDataJSON(), response = await route.fetch(), body = await response.json();
        fetched.resolve({status: response.status(), body, request});
        await gate.promise; await route.fulfill({response}); delivered.resolve();
      } catch (error) {fetched.reject(error); delivered.reject(error); await route.abort().catch(() => {});}
    };
    heldRoute = {pattern, handler}; await page.route(pattern, handler);
    await page.click('#r-save');
    const actualOldConflict = await bounded(fetched.promise, 'Actual stale A PUT conflict');
    const toBConfirmation = await open(b, 0, true); await fillNote(draftB);
    const beforeOldError = await snapshot();
    gate.resolve(); await bounded(delivered.promise, 'Actual stale A 409 delivery');
    await page.evaluate(() => new Promise(resolve => setTimeout(resolve, 0)));
    const afterOldError = await snapshot();
    await page.unroute(pattern, handler); heldRoute = null;
    const backendA2 = await api(noteRoute(a)), backendB0 = await api(noteRoute(b));
    check('research-save-old-real-409-cannot-overwrite-new-b-draft-notice-auth',
      actualOldConflict.status === 409 && actualOldConflict.body.error_code === 'REVISION_CONFLICT' &&
      actualOldConflict.request.expected_revision === 1 && fields.every(field => actualOldConflict.request.note[field] === staleDraftA[field]) &&
      toBConfirmation.type === 'confirm' && same(afterOldError, beforeOldError) && afterOldError.resource_id === b &&
      afterOldError.note.revision === 0 && afterOldError.dirty && same(afterOldError.values, draftB) &&
      afterOldError.authenticated && !afterOldError.workspace_hidden && !afterOldError.save_disabled &&
      backendA2.status === 200 && backendA2.body.revision === 2 && fields.every(field => backendA2.body[field] === externalA2[field]) &&
      backendB0.status === 200 && backendB0.body.revision === 0 && fields.every(field => backendB0.body[field] === '') &&
      writes.length === 1 && writes[0].expected_revision === 1,
      {actual_http_status: actualOldConflict.status, actual_error_code: actualOldConflict.body.error_code,
        submitted_expected_revision: actualOldConflict.request.expected_revision, native_navigation_confirmation: toBConfirmation,
        exact_b_ui_note_history_notice_auth_retained: same(afterOldError, beforeOldError), exact_b_draft_retained: same(afterOldError.values, draftB),
        backend_a_revision: backendA2.body.revision, backend_b_revision: backendB0.body.revision,
        actual_browser_put_count: writes.length, authenticated: afterOldError.authenticated});

    const backToAConfirmation = await open(a, 2, true);
    const externalThird = await api(noteRoute(a), 'PUT', {note: externalA3, expected_revision: 2});
    if (externalThird.status !== 200 || externalThird.body.revision !== 3) throw new Error('Real external A v3 save failed');
    await fillNote(currentDraftA); const beforeCurrentError = await snapshot();
    const responsePending = page.waitForResponse(response => response.request().method() === 'PUT' &&
      new URL(response.url()).pathname === '/dev/v1' + noteRoute(a));
    await page.click('#r-save');
    const currentResponse = await responsePending, currentBody = await currentResponse.json(), currentRequest = currentResponse.request().postDataJSON();
    await page.waitForFunction(() => document.getElementById('r-notice').textContent.includes('REVISION_CONFLICT') &&
      !document.getElementById('r-save').disabled);
    const afterCurrentError = await snapshot(), backendA3 = await api(noteRoute(a)), backendBStill0 = await api(noteRoute(b));
    const withoutNotice = value => {const result = {...value}; delete result.notice; return result;};
    check('research-save-current-real-409-visible-keeps-draft-and-save-enabled',
      currentResponse.status() === 409 && currentBody.error_code === 'REVISION_CONFLICT' && currentRequest.expected_revision === 2 &&
      fields.every(field => currentRequest.note[field] === currentDraftA[field]) && backToAConfirmation.type === 'confirm' &&
      afterCurrentError.notice === '처리하지 못했습니다: REVISION_CONFLICT' &&
      same(withoutNotice(afterCurrentError), withoutNotice(beforeCurrentError)) && same(afterCurrentError.values, currentDraftA) &&
      afterCurrentError.note.revision === 2 && afterCurrentError.dirty && !afterCurrentError.save_disabled &&
      !afterCurrentError.note_disabled && afterCurrentError.authenticated && !afterCurrentError.workspace_hidden &&
      backendA3.status === 200 && backendA3.body.revision === 3 && fields.every(field => backendA3.body[field] === externalA3[field]) &&
      backendBStill0.status === 200 && backendBStill0.body.revision === 0 && writes.length === 2 && writes[1].expected_revision === 2,
      {actual_http_status: currentResponse.status(), actual_error_code: currentBody.error_code,
        submitted_expected_revision: currentRequest.expected_revision, native_navigation_confirmation: backToAConfirmation,
        visible_current_error: afterCurrentError.notice, exact_current_draft_retained: same(afterCurrentError.values, currentDraftA),
        exact_other_ui_state_retained: same(withoutNotice(afterCurrentError), withoutNotice(beforeCurrentError)),
        save_enabled: !afterCurrentError.save_disabled, authenticated: afterCurrentError.authenticated,
        backend_a_revision: backendA3.body.revision, backend_b_revision: backendBStill0.body.revision,
        actual_browser_put_count: writes.length});
  } finally {
    if (releaseHeld) releaseHeld();
    if (heldRoute) await page.unroute(heldRoute.pattern, heldRoute.handler);
    page.off('request', track);
  }
};

'use strict';
// Actual browser + authenticated server + SQLite saved notes. Held replies are
// fetched from the real backend; no stored version or HTTP body is fabricated.
const crypto = require('node:crypto');
const fields = ['known', 'intention', 'alternative', 'outcome'];
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const canonical = value => JSON.stringify(value, Object.keys(value || {}).sort());
function equal(a, b) {
  if (a === null || b === null || typeof a !== 'object' || typeof b !== 'object') return Object.is(a, b);
  if (Array.isArray(a) || Array.isArray(b)) return Array.isArray(a) && Array.isArray(b) &&
    a.length === b.length && a.every((value, index) => equal(value, b[index]));
  const ak = Object.keys(a).sort(), bk = Object.keys(b).sort();
  return equal(ak, bk) && ak.every(key => equal(a[key], b[key]));
}
function deferred() {let resolve, reject; const promise = new Promise((yes, no) => {resolve = yes; reject = no;}); return {promise, resolve, reject};}
async function bounded(promise, label) {
  let timer;
  try {return await Promise.race([promise, new Promise((_, reject) => {timer = setTimeout(() => reject(new Error(label + ' timed out')), 15000);})]);}
  finally {clearTimeout(timer);}
}

module.exports = async function checkSavedNoteHistory({page, check, baseUrl, token}) {
  const auth = {Authorization: 'Bearer ' + token}, routes = [], uiWrites = [];
  let a, b;
  const track = request => {
    if (request.method() !== 'PUT') return;
    const route = new URL(request.url()).pathname;
    if (a && route.startsWith('/dev/v1/research/' + a + '/notes/')) {
      const payload = request.postDataJSON();
      uiWrites.push({route, expected_revision: payload.expected_revision, note: payload.note});
    }
  };
  page.on('request', track);
  async function api(route, method = 'GET', data) {
    const response = await page.context().request.fetch(baseUrl + '/dev/v1' + route, {method, headers: auth,
      ...(data === undefined ? {} : {data})});
    return {status: response.status(), body: await response.json()};
  }
  const noteRoute = (id, anchor = 'overview') => '/research/' + id + '/notes/' + anchor;
  async function reconnect() {
    await page.reload();
    if (!(await page.evaluate(() => Boolean(sessionStorage.getItem('lol-coach-dev-token'))))) {
      await page.fill('#token', token); await page.click('#login-form button');
    }
    await page.waitForFunction(() => !document.getElementById('workspace').hidden &&
      document.getElementById('notice').textContent.startsWith('연결됐습니다.'));
    await page.click('#show-research');
  }
  async function openResource(id) {
    await page.waitForSelector('#r-list button[data-resource-id="' + id + '"]');
    await page.click('#r-list button[data-resource-id="' + id + '"]');
    await page.waitForFunction(rid => rResource && rResource.id === rid && rNote && rNote.resource_id === rid &&
      rNote.anchor === 'overview' && !document.getElementById('r-known').disabled, id);
    const details = page.locator('details').filter({has: page.locator('#r-history-load')});
    if (!(await details.evaluate(element => element.open))) await details.locator('summary').click();
  }
  async function editable() {
    return page.evaluate(fieldNames => ({resource_id: rResource && rResource.id,
      anchor: rNote && rNote.anchor, revision: rNote && rNote.revision, dirty: rDirty,
      values: Object.fromEntries(fieldNames.map(field => [field, document.getElementById('r-' + field).value])),
      note_disabled: document.getElementById('r-known').disabled,
      note_state: document.getElementById('r-note-state').textContent}), fields);
  }
  async function historyState() {
    return page.evaluate(() => ({text: document.getElementById('r-history-preview').textContent,
      hidden: document.getElementById('r-history-preview').hidden,
      status: document.getElementById('r-history-state').textContent,
      selected: document.getElementById('r-history-revision').value,
      options: [...document.getElementById('r-history-revision').options].map(option => option.value),
      download_disabled: document.getElementById('r-history-download').disabled,
      workspace_hidden: document.getElementById('workspace').hidden}));
  }
  async function loadHistory(expectedCount) {
    await page.click('#r-history-load');
    await page.waitForFunction(count => !document.getElementById('r-history-revision').disabled &&
      document.getElementById('r-history-revision').options.length === count + 1, expectedCount);
  }
  async function previewVersion(revision) {
    await page.selectOption('#r-history-revision', String(revision));
    await page.waitForFunction(value => {
      const element = document.getElementById('r-history-preview');
      try {return !element.hidden && JSON.parse(element.textContent).revision === value &&
        !document.getElementById('r-history-download').disabled;} catch {return false;}
    }, revision);
    const state = await historyState();
    return {state, body: JSON.parse(state.text)};
  }
  async function holdActualRead(routePath, action, expectedStatus = 200) {
    const pattern = '**/dev/v1' + routePath;
    const fetched = deferred(), gate = deferred(), delivered = deferred();
    let active = true;
    const handler = async route => {
      if (!active || route.request().method() !== 'GET') return route.continue();
      active = false;
      try {
        const response = await route.fetch(), body = await response.json();
        fetched.resolve({status: response.status(), body});
        await gate.promise; await route.fulfill({response}); delivered.resolve();
      } catch (error) {fetched.reject(error); delivered.reject(error); await route.abort().catch(() => {});}
    };
    await page.route(pattern, handler);
    const record = {pattern, handler, release: () => gate.resolve()}; routes.push(record);
    await action();
    const actual = await bounded(fetched.promise, 'Real saved-version backend read');
    if (actual.status !== expectedStatus) throw new Error('Held saved version HTTP ' + actual.status);
    return {actual, release: async () => {
      gate.resolve(); await bounded(delivered.promise, 'Saved-version response delivery');
      await page.evaluate(() => new Promise(resolve => setTimeout(resolve, 0)));
      await page.unroute(pattern, handler);
    }};
  }
  async function holdPreview(id, anchor, revision, expectedStatus = 200) {
    return holdActualRead(noteRoute(id, anchor) + '/revisions/' + revision,
      () => page.selectOption('#r-history-revision', String(revision)), expectedStatus);
  }
  const v1 = {known: '버전 1: 한글·日本語·😀\n정확한 근거 "인용"', intention: '원래 의도 α', alternative: '대기 / 복귀 <노트>', outcome: '사후 결과는 당시 근거와 분리'};
  const v2 = {known: '버전 2: 수정된 근거 👀\n추가 줄', intention: '교환 이후 후퇴 계획 β', alternative: '짧은 교환·조건부 접근', outcome: '승패 결과는 판단 입력으로 사용하지 않음'};
  const v3 = {known: '버전 3: 최신 저장 근거', intention: '최신 의도 γ', alternative: '현재 대안', outcome: '현재 사후 기록'};
  const v4 = {known: '아직 저장하지 않은 v4 초안 😀\n이력 조회가 지우면 안 됨', intention: 'v4 새 의도 δ', alternative: '새로운 조건부 대안', outcome: '새 사후 메모: "정확히 보존"'};
  const anchorNote = {known: '별도 영상 구간 1 노트', intention: '', alternative: '', outcome: ''};
  try {
    await reconnect();
    const unique = crypto.randomUUID();
    const sourceA = await api('/research', 'POST', {source_type: 'transcript', title: 'Saved note history A ' + unique,
      video_id: 'CejHqSces8Q', raw_text: 'YouTube transcript\nVideo ID: CejHqSces8Q\nLanguage: en\nCaptions: manual\n\n[0:01] wave ' + unique + '\n[0:02] roam ' + unique});
    const sourceB = await api('/research', 'POST', {source_type: 'raw_json', title: 'Saved note history B ' + unique,
      raw_text: JSON.stringify({note: 'synthetic alternate resource ' + unique})});
    if (sourceA.status !== 201 || sourceB.status !== 201) throw new Error('Actual history fixture creation failed');
    a = sourceA.body.id; b = sourceB.body.id;
    for (const [index, note] of [v1, v2, v3].entries()) {
      const saved = await api(noteRoute(a), 'PUT', {note, expected_revision: index});
      if (saved.status !== 200 || saved.body.revision !== index + 1) throw new Error('Actual history fixture save failed');
    }
    if ((await api(noteRoute(a, '1'), 'PUT', {note: anchorNote, expected_revision: 0})).status !== 200) throw new Error('Actual anchor fixture save failed');
    await page.click('#r-refresh'); await openResource(a);
    for (const field of fields) await page.fill('#r-' + field, v4[field]);
    const dirtyV3 = await editable();
    await loadHistory(3);
    const index = await api(noteRoute(a) + '/history'), loadedIndex = await historyState();
    check('note-history-real-index-descending-versions', index.status === 200 && index.body.resource_id === a &&
      index.body.anchor === 'overview' && index.body.current_revision === 3 && index.body.revision_count === 3 &&
      equal(index.body.revisions, [3, 2, 1]) && index.body.read_only === true &&
      equal(loadedIndex.options, ['', '3', '2', '1']),
      {http_status: index.status, current_revision: index.body.current_revision,
        actual_revisions: index.body.revisions, visible_revision_options: loadedIndex.options, read_only: index.body.read_only});

    const first = await previewVersion(1), expectedFirst = await api(noteRoute(a) + '/revisions/1');
    const readonlyPre = await page.locator('#r-history-preview').evaluate(element => element.tagName === 'PRE' && !element.isContentEditable);
    check('note-history-v1-exact-unicode-readonly-dirty-v3-retained', expectedFirst.status === 200 &&
      equal(first.body, expectedFirst.body) && equal(first.body.note, v1) && first.body.read_only === true &&
      readonlyPre && equal(await editable(), dirtyV3),
      {exact_real_api_preview: equal(first.body, expectedFirst.body), exact_unicode_v1: equal(first.body.note, v1),
        readonly_pre: readonlyPre, exact_dirty_v3_editor_retained: equal(await editable(), dirtyV3)});

    const second = await previewVersion(2), expectedSecond = await api(noteRoute(a) + '/revisions/2');
    const downloadPending = page.waitForEvent('download');
    await page.click('#r-history-download');
    const downloaded = await bounded(downloadPending, 'Actual saved-version browser download');
    const stream = await downloaded.createReadStream();
    if (!stream) throw new Error('Browser download stream unavailable');
    const chunks = []; for await (const chunk of stream) chunks.push(chunk);
    const downloadedBytes = Buffer.concat(chunks), downloadedText = downloadedBytes.toString('utf8');
    const downloadedObject = JSON.parse(downloadedText);
    check('note-history-v2-authentic-download-exact-preview-bytes', expectedSecond.status === 200 &&
      equal(second.body, expectedSecond.body) && equal(second.body.note, v2) &&
      downloadedText === second.state.text && equal(downloadedObject, second.body) && equal(await editable(), dirtyV3),
      {exact_real_api_v2: equal(second.body, expectedSecond.body), exact_unicode_v2: equal(second.body.note, v2),
        genuine_browser_download_filename: downloaded.suggestedFilename(), downloaded_sha256: hash(downloadedBytes),
        preview_utf8_sha256: hash(Buffer.from(second.state.text)), exact_downloaded_bytes: downloadedText === second.state.text,
        exact_dirty_v3_editor_retained: equal(await editable(), dirtyV3)});

    const saveResponsePending = page.waitForResponse(response => response.request().method() === 'PUT' &&
      new URL(response.url()).pathname === '/dev/v1' + noteRoute(a));
    await page.click('#r-save');
    const saveResponse = await saveResponsePending, savedBody = await saveResponse.json(), savedRequest = saveResponse.request().postDataJSON();
    await page.waitForFunction(() => rNote && rNote.revision === 4 && !document.getElementById('r-save').disabled);
    const actualLatest = await api(noteRoute(a)), afterSave = await editable(), invalidated = await historyState();
    check('note-history-current-save-uses-v3-and-creates-v4', savedRequest.expected_revision === 3 &&
      equal(savedRequest.note, v4) && saveResponse.status() === 200 && savedBody.revision === 4 &&
      actualLatest.status === 200 && actualLatest.body.revision === 4 && fields.every(field => actualLatest.body[field] === v4[field]) &&
      equal(afterSave.values, v4) && afterSave.revision === 4 && !afterSave.dirty && invalidated.hidden &&
      invalidated.text === '' && invalidated.download_disabled,
      {actual_expected_revision: savedRequest.expected_revision, actual_saved_revision: savedBody.revision,
        backend_latest_revision: actualLatest.body.revision, exact_v4_note: equal(afterSave.values, v4),
        old_preview_invalidated: invalidated.hidden && invalidated.text === '' && invalidated.download_disabled});

    await loadHistory(4);
    const anchorHeld = await holdPreview(a, 'overview', 1);
    await page.click('#r-candidates button[data-anchor="1"]');
    await page.waitForFunction(() => rNote && rNote.anchor === '1' && !document.getElementById('r-known').disabled);
    const anchorBefore = await historyState(), anchorEditor = await editable();
    await anchorHeld.release(); const anchorAfter = await historyState();
    check('note-history-delayed-preview-cannot-follow-new-anchor', equal(anchorAfter, anchorBefore) &&
      anchorAfter.hidden && anchorAfter.text === '' && anchorAfter.download_disabled &&
      equal(await editable(), anchorEditor) && anchorEditor.anchor === '1',
      {held_real_status: anchorHeld.actual.status, new_anchor: anchorEditor.anchor,
        exact_new_anchor_state_retained: equal(anchorAfter, anchorBefore), no_stale_preview: anchorAfter.hidden && anchorAfter.text === ''});

    await page.click('#r-overview');
    await page.waitForFunction(() => rNote && rNote.anchor === 'overview' && !document.getElementById('r-known').disabled);
    await loadHistory(4); const resourceHeld = await holdPreview(a, 'overview', 1);
    await openResource(b); const resourceBefore = await historyState(), resourceEditor = await editable();
    await resourceHeld.release(); const resourceAfter = await historyState();
    check('note-history-delayed-preview-cannot-follow-new-resource', equal(resourceAfter, resourceBefore) &&
      resourceAfter.hidden && resourceAfter.text === '' && resourceAfter.download_disabled &&
      equal(await editable(), resourceEditor) && resourceEditor.resource_id === b,
      {held_real_status: resourceHeld.actual.status, alternate_resource_selected: resourceEditor.resource_id === b,
        exact_new_resource_state_retained: equal(resourceAfter, resourceBefore), no_stale_preview: resourceAfter.hidden && resourceAfter.text === ''});

    await openResource(a); await loadHistory(4); const logoutHeld = await holdPreview(a, 'overview', 1);
    await page.click('#show-synthetic'); await page.click('#logout');
    const logoutBefore = await historyState(), logoutEditor = await editable();
    await logoutHeld.release(); const logoutAfter = await historyState();
    check('note-history-delayed-preview-cannot-follow-logout', equal(logoutAfter, logoutBefore) &&
      logoutAfter.workspace_hidden && logoutAfter.hidden && logoutAfter.text === '' && logoutAfter.download_disabled &&
      equal(await editable(), logoutEditor) && logoutEditor.resource_id === null,
      {held_real_status: logoutHeld.actual.status, logged_out: logoutAfter.workspace_hidden,
        exact_logged_out_history_retained: equal(logoutAfter, logoutBefore), no_stale_preview: logoutAfter.hidden && logoutAfter.text === ''});

    await reconnect(); await openResource(a); await loadHistory(4);
    await page.fill('#r-known', '이력 오류가 지우면 안 되는 최신 미저장 노트');
    const errorEditor = await editable();
    // Adversarial selector input requests an actually absent revision. The
    // genuine server returns its genuine 404; no response is mocked.
    await page.locator('#r-history-revision').evaluate(select => {
      const option = document.createElement('option'); option.value = '999'; option.textContent = '없는 버전 검증'; select.append(option);
    });
    const missingResponsePending = page.waitForResponse(response => new URL(response.url()).pathname ===
      '/dev/v1' + noteRoute(a) + '/revisions/999');
    await page.selectOption('#r-history-revision', '999');
    const missingResponse = await missingResponsePending, missingBody = await missingResponse.json();
    await page.waitForFunction(() => document.getElementById('r-history-state').textContent.includes('NOTE_REVISION_NOT_FOUND'));
    const errorState = await historyState();
    check('note-history-current-real-404-visible-with-draft-intact', missingResponse.status() === 404 &&
      missingBody.error_code === 'NOTE_REVISION_NOT_FOUND' && errorState.status.includes('NOTE_REVISION_NOT_FOUND') &&
      errorState.hidden && errorState.text === '' && errorState.download_disabled && equal(await editable(), errorEditor),
      {adversarial_missing_revision: 999, actual_http_status: missingResponse.status(), actual_error_code: missingBody.error_code,
        visible_history_error: errorState.status, stale_download_disabled: errorState.download_disabled,
        exact_dirty_current_editor_retained: equal(await editable(), errorEditor)});

    const finalIndex = await api(noteRoute(a) + '/history'), finalVersions = [];
    for (const revision of [1, 2, 3, 4]) finalVersions.push(await api(noteRoute(a) + '/revisions/' + revision));
    const anchorLatest = await api(noteRoute(a, '1'));
    check('note-history-reads-preserve-all-saved-versions-and-anchors', finalIndex.status === 200 &&
      equal(finalIndex.body.revisions, [4, 3, 2, 1]) && finalIndex.body.current_revision === 4 &&
      finalVersions.every((result, index) => result.status === 200 && result.body.revision === index + 1 &&
        result.body.read_only === true && equal(result.body.note, [v1, v2, v3, v4][index])) &&
      anchorLatest.status === 200 && anchorLatest.body.revision === 1 && fields.every(field => anchorLatest.body[field] === anchorNote[field]) &&
      uiWrites.length === 1 && uiWrites[0].expected_revision === 3 && equal(uiWrites[0].note, v4),
      {final_actual_revisions: finalIndex.body.revisions, all_original_unicode_payloads_preserved: finalVersions.every((result, index) => equal(result.body.note, [v1, v2, v3, v4][index])),
        alternate_anchor_revision: anchorLatest.body.revision, actual_browser_note_writes: uiWrites.length,
        sole_write_expected_revision: uiWrites[0]?.expected_revision});

    const failedViewHeld = await holdPreview(a, 'overview', 999, 404);
    const beforeViewEditor = await editable();
    await page.click('#show-synthetic');
    const clearedViewHistory = await historyState();
    const authAndView = () => page.evaluate(() => ({
      authenticated: Boolean(sessionStorage.getItem('lol-coach-dev-token')),
      workspace_hidden: document.getElementById('workspace').hidden,
      auth_panel_hidden: document.getElementById('auth-panel').hidden,
      synthetic_hidden: document.getElementById('synthetic-view').hidden,
      research_hidden: document.getElementById('research-view').hidden,
      main_notice: document.getElementById('notice').textContent
    }));
    const beforeViewAuth = await authAndView();
    await failedViewHeld.release();
    const afterViewHistory = await historyState(), afterViewAuth = await authAndView();
    check('note-history-delayed-real-404-cannot-follow-synthetic-view-toggle',
      failedViewHeld.actual.status === 404 && failedViewHeld.actual.body.error_code === 'NOTE_REVISION_NOT_FOUND' &&
      equal(afterViewHistory, clearedViewHistory) && afterViewHistory.hidden && afterViewHistory.text === '' &&
      afterViewHistory.status === '' && afterViewHistory.download_disabled &&
      equal(await editable(), beforeViewEditor) && equal(afterViewAuth, beforeViewAuth) &&
      afterViewAuth.authenticated && !afterViewAuth.workspace_hidden && afterViewAuth.auth_panel_hidden &&
      !afterViewAuth.synthetic_hidden && afterViewAuth.research_hidden,
      {held_actual_http_status: failedViewHeld.actual.status, held_actual_error_code: failedViewHeld.actual.body.error_code,
        exact_cleared_history_retained: equal(afterViewHistory, clearedViewHistory),
        exact_dirty_editor_retained: equal(await editable(), beforeViewEditor),
        authentication_and_view_retained: equal(afterViewAuth, beforeViewAuth), authenticated: afterViewAuth.authenticated,
        stale_history_error_absent: afterViewHistory.status === ''});

    await page.click('#show-research');
    await page.waitForFunction(() => !document.getElementById('research-view').hidden &&
      !document.getElementById('r-history-load').disabled);
    const indexHeld = await holdActualRead(noteRoute(a) + '/history', () => page.click('#r-history-load'));
    const deletedResponsePending = page.waitForResponse(response => response.request().method() === 'DELETE' &&
      new URL(response.url()).pathname === '/dev/v1/research/' + a);
    const dialogPending = page.waitForEvent('dialog');
    const deleteClicked = page.click('#r-delete');
    const deleteDialog = await bounded(dialogPending, 'Native current-resource delete confirmation');
    const deletionConfirmation = {type: deleteDialog.type(), message: deleteDialog.message(), response: 'accept'};
    await deleteDialog.accept(); await deleteClicked;
    const deletedResponse = await deletedResponsePending, deletedBody = await deletedResponse.json();
    await page.waitForFunction(rid => rResource === null && rNote === null &&
      document.getElementById('r-detail').hidden && document.getElementById('r-known').value === '' &&
      document.getElementById('r-notice').textContent === '자료와 노트를 삭제했습니다.' &&
      !document.querySelector('#r-list button[data-resource-id="' + rid + '"]'), a);
    const afterDeletionHistory = await historyState(), afterDeletionEditor = await editable();
    await indexHeld.release();
    const afterLateIndex = await historyState(), missingResource = await api('/research/' + a);
    const missingHistory = await api(noteRoute(a) + '/history');
    check('note-history-delayed-real-index-cannot-follow-current-resource-deletion',
      indexHeld.actual.status === 200 && equal(indexHeld.actual.body.revisions, [4, 3, 2, 1]) &&
      deletedResponse.status() === 200 && deletedBody.id === a && deletionConfirmation.type === 'confirm' &&
      equal(afterLateIndex, afterDeletionHistory) && afterLateIndex.hidden && afterLateIndex.text === '' &&
      afterLateIndex.status === '' && afterLateIndex.options.length === 0 && afterLateIndex.download_disabled &&
      equal(await editable(), afterDeletionEditor) && afterDeletionEditor.resource_id === null &&
      afterDeletionEditor.revision === null && !afterDeletionEditor.dirty &&
      fields.every(field => afterDeletionEditor.values[field] === '') &&
      missingResource.status === 404 && missingHistory.status === 404,
      {held_actual_history_status: indexHeld.actual.status, held_actual_revisions: indexHeld.actual.body.revisions,
        actual_deleted_resource_status: deletedResponse.status(), native_confirmation: deletionConfirmation,
        exact_cleared_history_retained: equal(afterLateIndex, afterDeletionHistory), old_options_absent: afterLateIndex.options.length === 0,
        current_selection_cleared: afterDeletionEditor.resource_id === null, notes_cleared: fields.every(field => afterDeletionEditor.values[field] === ''),
        actual_deleted_resource_get_status: missingResource.status, actual_cascaded_history_get_status: missingHistory.status});
  } finally {
    for (const route of routes) route.release();
    for (const route of routes) await page.unroute(route.pattern, route.handler);
    page.off('request', track);
  }
};

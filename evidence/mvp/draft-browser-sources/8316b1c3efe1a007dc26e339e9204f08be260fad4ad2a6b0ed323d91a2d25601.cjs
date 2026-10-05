'use strict';
// Actual Chrome + authenticated HTTP + SQLite. Each held response is obtained
// with route.fetch from the real server and delivered without fabricating data.
// Native confirm dialogs and actual download streams are observed directly.
const crypto = require('node:crypto');
const hash = value => crypto.createHash('sha256').update(value).digest('hex');
function equal(a, b) {
  if (a === null || b === null || typeof a !== 'object' || typeof b !== 'object') return Object.is(a, b);
  const ak = Object.keys(a).sort(), bk = Object.keys(b).sort();
  return ak.length === bk.length && ak.every((key, index) => key === bk[index] && equal(a[key], b[key]));
}
function deferred() { let resolve, reject; const promise = new Promise((yes, no) => { resolve = yes; reject = no; }); return { promise, resolve, reject }; }
async function bounded(promise, label) {
  let timer;
  try { return await Promise.race([promise, new Promise((_, reject) => { timer = setTimeout(() => reject(Error(label + ' timed out')), 15000); })]); }
  finally { clearTimeout(timer); }
}

module.exports = async function checkManualDraftCapture({ page, check, baseUrl, token }) {
  const auth = { Authorization: 'Bearer ' + token }, held = [], writes = [], unique = crypto.randomUUID();
  const fields = ['title', 'patch', 'phase', 'observed', 'author', 'perspective', 'source'];
  const track = request => {
    const pathname = new URL(request.url()).pathname;
    if (pathname.startsWith('/dev/v1/draft-captures') && ['POST', 'PUT', 'DELETE'].includes(request.method())) {
      writes.push({ method: request.method(), path: pathname, body: request.postDataJSON() });
    }
  };
  page.on('request', track);
  async function api(route, method = 'GET', data) {
    const response = await page.context().request.fetch(baseUrl + '/dev/v1' + route,
      { method, headers: auth, ...(data === undefined ? {} : { data }) });
    return { status: response.status(), body: await response.json() };
  }
  function fixture(title) {
    return { title, phase: null, patch: null, observed_at: null,
      visible_picks: [{ side: 'ALLY', slot: 1, champion: 'Ahri' }], visible_bans: [],
      role_assignments: [{ side: 'ALLY', slot: 1, role: null, uncertainty: 'UNKNOWN' }],
      source: { author: 'Native browser operator', perspective: 'UNKNOWN', description: 'Explicit unverified manual input ' + unique } };
  }
  async function create(title) {
    const result = await api('/draft-captures', 'POST', { capture: fixture(title) });
    if (result.status !== 201) throw Error('Real manual fixture create failed: ' + result.status);
    return result.body;
  }
  const recordPath = record => '/draft-captures/' + record.session_id;
  const versionPath = record => recordPath(record) + '/revisions/' + record.revision;
  async function reconnect() {
    await page.reload();
    if (!(await page.evaluate(() => Boolean(sessionStorage.getItem('lol-coach-dev-token'))))) {
      await page.fill('#token', token); await page.click('#login-form button');
    }
    await page.waitForFunction(() => !document.getElementById('workspace').hidden && document.getElementById('notice').textContent.startsWith('연결됐습니다.'));
    await page.click('#show-draft');
    await page.waitForFunction(() => !document.getElementById('draft-view').hidden);
  }
  async function native(action, answer = 'accept') {
    const pending = page.waitForEvent('dialog'), clicked = action(), dialog = await bounded(pending, 'Native draft confirmation');
    const result = { type: dialog.type(), message: dialog.message(), response: answer };
    if (answer === 'accept') await dialog.accept(); else await dialog.dismiss();
    await clicked;
    return result;
  }
  async function state() {
    return page.evaluate(names => ({ record: dRecord, latest: dLatest, dirty: dDirty, edit: dEdit, epoch: dEpoch, preview: dPreview,
      values: Object.fromEntries(names.map(name => [name, document.getElementById('d-' + name).value])),
      pick_ally_1: document.getElementById('d-pick-ALLY-1').value,
      ban_ally_2: document.getElementById('d-ban-ALLY-2').value,
      pick_enemy_5: document.getElementById('d-pick-ENEMY-5').value,
      save_disabled: document.getElementById('d-save').disabled,
      download_disabled: document.getElementById('d-download').disabled,
      history_download_disabled: document.getElementById('d-history-download').disabled,
      history_text: document.getElementById('d-history-preview').textContent,
      notice: document.getElementById('d-notice').textContent,
      authenticated: Boolean(sessionStorage.getItem('lol-coach-dev-token')),
      workspace_hidden: document.getElementById('workspace').hidden }), fields);
  }
  async function unfoldSlotGroups() {
    for (const side of ['ALLY', 'ENEMY']) {
      const input = page.locator('#d-pick-' + side + '-1');
      const group = page.locator('#draft-view details').filter({ has: input });
      if (!(await group.evaluate(element => element.open))) await group.locator('summary').click();
      await input.waitFor({ state: 'visible' });
    }
  }
  async function open(record, answer = 'accept') {
    const selector = '#d-list button[data-capture-id="' + record.session_id + '"]';
    await page.waitForSelector(selector);
    const confirmation = await page.evaluate(() => dDirty) ? await native(() => page.click(selector), answer) : (await page.click(selector), null);
    if (answer === 'accept') {
      await page.waitForFunction(expected => dRecord && dRecord.session_id === expected.session_id &&
        dRecord.revision === expected.revision && !document.getElementById('d-title').disabled, record);
      await unfoldSlotGroups();
    }
    return confirmation;
  }
  async function save(method, path) {
    const pending = page.waitForResponse(response => response.request().method() === method && new URL(response.url()).pathname === '/dev/v1' + path);
    await page.click('#d-save');
    const response = await bounded(pending, 'Actual draft save response'), body = await response.json();
    const result = { status: response.status(), body, request: response.request().postDataJSON() };
    if (result.status < 300) await page.waitForFunction(expected => dRecord && dRecord.id === expected.id &&
      !document.getElementById('d-save').disabled, body);
    return result;
  }
  async function history(count) {
    const container = page.locator('details').filter({ has: page.locator('#d-history-load') });
    if (await container.count() && !(await container.first().evaluate(node => node.open))) await container.first().locator('summary').click();
    await page.click('#d-history-load');
    await page.waitForFunction(number => [...document.getElementById('d-history-revision').options]
      .filter(option => /^\d+$/.test(option.value)).length === number && !document.getElementById('d-history-revision').disabled, count);
  }
  async function preview(revision) {
    await page.selectOption('#d-history-revision', String(revision));
    await page.waitForFunction(number => dPreview && dPreview.revision === number && !document.getElementById('d-history-download').disabled, revision);
  }
  async function download(selector) {
    const pending = page.waitForEvent('download'); await page.click(selector);
    const result = await bounded(pending, 'Authentic draft download'), stream = await result.createReadStream();
    if (!stream) throw Error('Actual draft download has no byte stream');
    const chunks = []; for await (const chunk of stream) chunks.push(chunk);
    const bytes = Buffer.concat(chunks);
    return { bytes, text: bytes.toString('utf8'), filename: result.suggestedFilename() };
  }
  async function holdGet(path, action) {
    const pattern = '**/dev/v1' + path, fetched = deferred(), release = deferred(), delivered = deferred(); let active = true;
    const handler = async route => {
      if (!active || route.request().method() !== 'GET') return route.continue();
      active = false;
      try {
        const response = await route.fetch(), body = await response.json();
        fetched.resolve({ status: response.status(), body }); await release.promise;
        await route.fulfill({ response }); delivered.resolve();
      } catch (error) { fetched.reject(error); delivered.reject(error); await route.abort().catch(() => {}); }
    };
    await page.route(pattern, handler); held.push({ pattern, handler, release: () => release.resolve() });
    await action(); const actual = await bounded(fetched.promise, 'Genuine held draft GET');
    return { actual, release: async () => { release.resolve(); await bounded(delivered.promise, 'Actual draft GET delivery');
      await page.evaluate(() => new Promise(resolve => setTimeout(resolve, 0))); await page.unroute(pattern, handler); } };
  }
  try {
    await reconnect(); await page.click('#d-new');
    await page.fill('#d-title', 'Native manual capture ' + unique);
    await page.fill('#d-author', '개인 직접 기록 😀');
    await page.selectOption('#d-perspective', 'UNKNOWN');
    await page.fill('#d-source', 'Player 검증 전 · 직접 입력한 픽창 α');
    for (const id of ['patch', 'phase', 'observed']) await page.fill('#d-' + id, '');
    await unfoldSlotGroups();
    await page.fill('#d-pick-ALLY-1', '아리'); await page.fill('#d-ban-ALLY-2', 'Yasuo'); await page.fill('#d-pick-ENEMY-5', 'Lux');
    const unsaved = await state(), listBefore = await api('/draft-captures'), writesBefore = writes.length;
    check('draft-native-operator-input-does-not-auto-save', unsaved.record === null && unsaved.dirty && writesBefore === 0 &&
      listBefore.status === 200 && listBefore.body.length === 0, { actual_browser_writes: writesBefore, actual_saved_count: listBefore.body.length, dirty: unsaved.dirty });
    const first = await save('POST', '/draft-captures'), capture = first.body.capture;
    const pick = (side, slot) => capture.visible_picks.find(row => row.side === side && row.slot === slot);
    const ban = (side, slot) => capture.visible_bans.find(row => row.side === side && row.slot === slot);
    check('draft-native-partial-save-preserves-declared-null-and-unverified-state', first.status === 201 && capture.patch === null &&
      capture.phase === null && capture.observed_at === null && pick('ALLY', 1).champion === '아리' && pick('ENEMY', 5).champion === 'Lux' &&
      ban('ALLY', 2).champion === 'Yasuo' && capture.role_assignments.every(row => row.role === null && row.uncertainty.length > 0) &&
      capture.source.perspective === 'UNKNOWN' && capture.source.author === '개인 직접 기록 😀' && first.body.validation_state === 'UNVERIFIED' &&
      first.body.gameplan_status === 'NOT_GENERATED' && first.body.coaching_enabled === false && first.body.parent_id === null,
      { actual_status: first.status, declared_unknown_time: capture.observed_at, unknown_roles: capture.role_assignments.every(row => row.role === null), validation_state: first.body.validation_state, coaching_enabled: first.body.coaching_enabled });
    const list1 = await api('/draft-captures'), exact1 = await api(versionPath(first.body));
    check('draft-native-saved-list-and-exact-version-use-actual-record', list1.status === 200 && list1.body.length === 1 &&
      equal(list1.body[0], first.body) && exact1.status === 200 && equal(exact1.body, first.body), { actual_list_count: list1.body.length, exact_saved_version: equal(exact1.body, first.body) });
    await reconnect(); await open(first.body);
    const reopened = await state();
    check('draft-native-reload-restores-null-and-two-side-input', equal(reopened.record, first.body) && reopened.values.patch === '' &&
      reopened.values.observed === '' && reopened.pick_ally_1 === '아리' && reopened.pick_enemy_5 === 'Lux' && reopened.ban_ally_2 === 'Yasuo' && !reopened.dirty,
      { saved_revision: reopened.record.revision, unknown_time_editor: reopened.values.observed, exact_saved_record: equal(reopened.record, first.body), ally_pick: reopened.pick_ally_1, enemy_pick: reopened.pick_enemy_5 });
    await page.fill('#d-pick-ALLY-1', '정정된 Ahri');
    const second = await save('PUT', recordPath(first.body)), oldAfterCorrection = await api(versionPath(first.body));
    check('draft-native-explicit-correction-cas-creates-immutable-successor', second.status === 200 && second.request.expected_revision === 1 &&
      second.body.revision === 2 && second.body.parent_id === first.body.id && equal(oldAfterCorrection.body, first.body) && !((await state()).dirty),
      { actual_expected_revision: second.request.expected_revision, saved_revision: second.body.revision, prior_snapshot_preserved: equal(oldAfterCorrection.body, first.body) });
    await page.fill('#d-title', 'UNSAVED PRIVATE DRAFT ' + unique);
    const downloadBefore = await state(), savedDownload = await download('#d-download');
    check('draft-native-current-download-is-exact-saved-record-not-dirty-input', savedDownload.text === JSON.stringify(second.body, null, 2) &&
      equal(await state(), downloadBefore) && !savedDownload.text.includes('UNSAVED PRIVATE DRAFT'),
      { genuine_download_sha256: hash(savedDownload.bytes), exact_saved_bytes: savedDownload.text === JSON.stringify(second.body, null, 2), dirty_input_excluded: !savedDownload.text.includes('UNSAVED PRIVATE DRAFT') });
    await history(2); await preview(1);
    const historical = await state(), oldDownload = await download('#d-history-download'), oldGet = await api(versionPath(first.body));
    check('draft-native-old-preview-download-preserves-exact-immutable-input', equal(historical.preview, first.body) && equal(oldGet.body, first.body) &&
      oldDownload.text === JSON.stringify(oldGet.body, null, 2) && equal((await state()).values, downloadBefore.values) && (await state()).dirty,
      { original_revision: historical.preview.revision, actual_download_sha256: hash(oldDownload.bytes), exact_original_saved_bytes: oldDownload.text === JSON.stringify(oldGet.body, null, 2), current_unsaved_editor_retained: equal((await state()).values, downloadBefore.values) });
    const external = await api(recordPath(first.body), 'PUT', { capture: { ...second.body.capture, title: 'Actual external revision 3' }, expected_revision: 2 });
    if (external.status !== 200) throw Error('Genuine external CAS update failed');
    const conflictBefore = await state(), conflict = await save('PUT', recordPath(first.body));
    await page.waitForFunction(() => document.getElementById('d-notice').textContent.includes('REVISION_CONFLICT') && !document.getElementById('d-save').disabled);
    const conflictAfter = await state();
    check('draft-native-real-409-keeps-exact-dirty-input-and-loaded-cas', conflict.status === 409 && conflict.body.error_code === 'REVISION_CONFLICT' &&
      conflict.request.expected_revision === 2 && equal(conflictAfter.values, conflictBefore.values) && equal(conflictAfter.record, conflictBefore.record) &&
      conflictAfter.dirty && !conflictAfter.save_disabled && conflictAfter.authenticated && !conflictAfter.workspace_hidden,
      { actual_http_status: conflict.status, expected_revision_sent: conflict.request.expected_revision, loaded_revision: conflictAfter.record.revision, exact_dirty_editor_retained: equal(conflictAfter.values, conflictBefore.values) });
    const writesAtCancel = writes.length, beforeCancel = await state(), cancelNew = await native(() => page.click('#d-new'), 'dismiss');
    check('draft-native-cancel-new-keeps-dirty-input-without-write', cancelNew.type === 'confirm' && cancelNew.response === 'dismiss' &&
      equal(await state(), beforeCancel) && writes.length === writesAtCancel, { native_confirmation: cancelNew, actual_write_delta: writes.length - writesAtCancel, exact_editor_retained: equal(await state(), beforeCancel) });
    const reloadConfirm = await open(external.body);
    check('draft-native-confirmed-reopen-loads-current-external-revision', reloadConfirm.type === 'confirm' && reloadConfirm.response === 'accept' &&
      equal((await state()).record, external.body) && !(await state()).dirty && (await state()).values.title === 'Actual external revision 3',
      { native_confirmation: reloadConfirm, actual_current_revision: (await state()).record.revision });
    await history(3); await preview(1);
    const deleteBefore = await state(), cancelDelete = await native(() => page.click('#d-delete'), 'dismiss');
    check('draft-native-cancel-delete-preserves-current-and-old-preview', cancelDelete.type === 'confirm' && cancelDelete.response === 'dismiss' &&
      equal(await state(), deleteBefore) && (await api(recordPath(first.body))).status === 200,
      { native_confirmation: cancelDelete, exact_current_and_preview_retained: equal(await state(), deleteBefore), actual_backend_still_present: true });
    const heldOld = await holdGet(recordPath(first.body) + '/revisions/2', () => page.selectOption('#d-history-revision', '2'));
    const deletePending = page.waitForResponse(response => response.request().method() === 'DELETE' && new URL(response.url()).pathname === '/dev/v1' + recordPath(first.body));
    const deleteConfirm = await native(() => page.click('#d-delete')), deleteResponse = await deletePending, deleteBody = await deleteResponse.json();
    await page.waitForFunction(() => dRecord === null && document.getElementById('d-download').disabled && document.getElementById('d-history-download').disabled &&
      document.getElementById('d-notice').textContent === '픽창 기록과 모든 버전을 삭제했습니다.');
    const deleteState = await state(), removedCurrent = await api(recordPath(first.body)), removedHistory = await api(recordPath(first.body) + '/history');
    check('draft-native-real-delete-purges-current-history-and-downloads', deleteResponse.status() === 200 && deleteConfirm.type === 'confirm' &&
      deleteBody.deleted_snapshots === 3 && deleteState.record === null && deleteState.preview === null && deleteState.download_disabled &&
      deleteState.history_download_disabled && deleteState.values.title === '' && removedCurrent.status === 404 && removedHistory.status === 404,
      { actual_http_status: deleteResponse.status(), actual_deleted_snapshots: deleteBody.deleted_snapshots, backend_current_status: removedCurrent.status, backend_history_status: removedHistory.status, native_confirmation: deleteConfirm });
    await heldOld.release();
    const afterLateOld = await state();
    check('draft-native-late-real-history-get-cannot-resurrect-deleted-input', heldOld.actual.status === 200 && heldOld.actual.body.revision === 2 &&
      equal(afterLateOld, deleteState) && afterLateOld.preview === null && afterLateOld.history_download_disabled,
      { held_actual_http_status: heldOld.actual.status, held_deleted_revision: heldOld.actual.body.revision, exact_deleted_state_retained: equal(afterLateOld, deleteState) });
    await page.click('#d-refresh');
    await page.waitForFunction(() => document.querySelectorAll('#d-list button[data-capture-id]').length === 0);
    check('draft-native-empty-refresh-has-no-phantom-record', (await api('/draft-captures')).body.length === 0 &&
      (await state()).record === null && await page.locator('#d-list button[data-capture-id]').count() === 0,
      { actual_backend_count: 0, visible_capture_buttons: await page.locator('#d-list button[data-capture-id]').count() });
    const a = await create('Native late A ' + unique), b = await create('Native active B ' + unique);
    await page.click('#d-refresh'); await page.waitForSelector('#d-list button[data-capture-id="' + b.session_id + '"]');
    await open(b);
    const heldA = await holdGet(recordPath(a), () => page.click('#d-list button[data-capture-id="' + a.session_id + '"]'));
    await open(b); await page.fill('#d-title', 'B dirty input must survive stale A');
    const beforeLateA = await state(); await heldA.release();
    const afterLateA = await state();
    check('draft-native-late-real-capture-get-keeps-new-owner-draft', heldA.actual.status === 200 && heldA.actual.body.session_id === a.session_id &&
      equal(afterLateA, beforeLateA) && afterLateA.record.session_id === b.session_id && afterLateA.dirty,
      { held_actual_capture_id: heldA.actual.body.session_id, active_capture_id: afterLateA.record.session_id, exact_new_owner_draft_retained: equal(afterLateA, beforeLateA) });
    await page.setViewportSize({ width: 390, height: 844 });
    const mobile = await page.locator('#d-save').evaluate(element => { const rect = element.getBoundingClientRect(); return {
      viewport: innerWidth, document_width: document.documentElement.scrollWidth, left: rect.left, right: rect.right,
      width: rect.width, visible: Boolean(element.getClientRects().length), disabled: element.disabled }; });
    check('draft-native-mobile-390-save-usable-without-overflow', mobile.viewport === 390 && mobile.document_width <= 391 && mobile.visible &&
      !mobile.disabled && mobile.width > 0 && mobile.left >= 0 && mobile.right <= 391,
      { viewport_width: mobile.viewport, document_width: mobile.document_width, control_visible: mobile.visible, control_disabled: mobile.disabled, bounds: { left: mobile.left, right: mobile.right } });
    await native(() => page.click('#d-list button[data-capture-id="' + b.session_id + '"]'));
    await history(1);
    const heldLogout = await holdGet(recordPath(b) + '/revisions/1', () => page.selectOption('#d-history-revision', '1'));
    await page.click('#show-synthetic'); await page.click('#logout');
    const loggedOut = await state(); await heldLogout.release();
    const afterLogout = await state();
    check('draft-native-logout-clears-private-input-and-blocks-late-get', heldLogout.actual.status === 200 && !loggedOut.authenticated &&
      loggedOut.workspace_hidden && loggedOut.record === null && loggedOut.preview === null && fields.every(field => loggedOut.values[field] === '' || field === 'perspective') &&
      loggedOut.download_disabled && loggedOut.history_download_disabled && equal(afterLogout, loggedOut),
      { held_actual_http_status: heldLogout.actual.status, authenticated: loggedOut.authenticated, workspace_hidden: loggedOut.workspace_hidden, cached_record_cleared: loggedOut.record === null, exact_logout_state_retained: equal(afterLogout, loggedOut) });
    await reconnect();
    const finalA = await api(recordPath(a)), finalB = await api(recordPath(b)), status = await api('/status'), sessions = await api('/sessions');
    check('draft-native-capture-remains-separate-from-synthetic-engine-and-real-coach', finalA.status === 200 && finalB.status === 200 &&
      finalA.body.validation_state === 'UNVERIFIED' && finalB.body.coaching_enabled === false && status.body.mode === 'SYNTHETIC_ONLY' &&
      status.body.real_data_enabled === false && !sessions.body.some(row => row.id === a.session_id || row.id === b.session_id),
      { manual_records_survive_logout: finalA.status === 200 && finalB.status === 200, real_data_enabled: status.body.real_data_enabled, synthetic_mode: status.body.mode, draft_ids_absent_from_legacy_sessions: !sessions.body.some(row => row.id === a.session_id || row.id === b.session_id) });
    const typedCapture = {
      title: 'Exact typed no-edit roundtrip ' + unique + '\nsecond declared title line', phase: '사용자가 선언한 픽 단계 未確認', patch: '26.20-declared',
      observed_at: '2026-10-05T15:31:12.345678+09:00',
      visible_picks: [{ side: 'ENEMY', slot: 4, champion: null }, { side: 'ALLY', slot: 2, champion: 'Ahri' },
        { side: 'ENEMY', slot: 1, champion: 'Lux' }, { side: 'ALLY', slot: 5, champion: null }],
      visible_bans: [{ side: 'ENEMY', slot: 5, champion: 'Yasuo' }, { side: 'ALLY', slot: 4, champion: null },
        { side: 'ALLY', slot: 1, champion: 'Zed' }],
      role_assignments: [{ side: 'ENEMY', slot: 3, role: null, uncertainty: 'UNKNOWN' },
        { side: 'ALLY', slot: 4, role: null, uncertainty: '직접 입력한 미확인 사유' },
        { side: 'ENEMY', slot: 1, role: 'SUPPORT', uncertainty: '사용자가 선언한 후보' }],
      source: { author: 'Declared operator 😀\nsecond declared author line', perspective: 'PLAYER', description: '직접 입력한 출처 α\r\n관찰과 검증 상태는 별개' }
    };
    const typedCreated = await api('/draft-captures', 'POST', { capture: typedCapture });
    if (typedCreated.status !== 201) throw Error('Genuine typed null-member fixture creation failed: ' + typedCreated.status);
    await page.click('#d-refresh'); await open(typedCreated.body);
    const beforeNoEdit = await state(), noEditSaved = await save('PUT', recordPath(typedCreated.body));
    const oldTyped = await api(versionPath(typedCreated.body)), newTyped = await api(recordPath(typedCreated.body));
    check('draft-native-no-edit-roundtrip-keeps-null-order-membership-and-declared-provenance', typedCreated.status === 201 &&
      equal(typedCreated.body.capture, typedCapture) && !beforeNoEdit.dirty && beforeNoEdit.record.revision === 1 &&
      beforeNoEdit.values.title === 'Exact typed no-edit roundtrip ' + unique + 'second declared title line' &&
      beforeNoEdit.values.author === 'Declared operator 😀second declared author line' &&
      beforeNoEdit.values.source === '직접 입력한 출처 α\n관찰과 검증 상태는 별개' &&
      noEditSaved.status === 200 && noEditSaved.request.expected_revision === 1 && equal(noEditSaved.request.capture, typedCapture) &&
      noEditSaved.body.revision === 2 && noEditSaved.body.parent_id === typedCreated.body.id && newTyped.status === 200 &&
      equal(newTyped.body.capture, typedCapture) && oldTyped.status === 200 && equal(oldTyped.body, typedCreated.body) &&
      !newTyped.body.capture.role_assignments.some(row => row.side === 'ALLY' && row.slot === 2) &&
      newTyped.body.capture.observed_at === '2026-10-05T15:31:12.345678+09:00' &&
      equal(newTyped.body.capture.source, typedCapture.source) && newTyped.body.validation_state === 'UNVERIFIED' &&
      newTyped.body.coaching_enabled === false,
      { actual_create_status: typedCreated.status, actual_native_update_status: noEditSaved.status,
        input_was_not_edited: !beforeNoEdit.dirty, expected_revision_sent: noEditSaved.request.expected_revision,
        exact_submitted_input: equal(noEditSaved.request.capture, typedCapture), exact_saved_successor_input: equal(newTyped.body.capture, typedCapture),
        null_pick_members_and_unsorted_order_retained: equal(newTyped.body.capture.visible_picks, typedCapture.visible_picks),
        null_ban_members_and_unsorted_order_retained: equal(newTyped.body.capture.visible_bans, typedCapture.visible_bans),
        exact_role_membership_and_order_retained: equal(newTyped.body.capture.role_assignments, typedCapture.role_assignments),
        absent_known_pick_role_stays_absent: !newTyped.body.capture.role_assignments.some(row => row.side === 'ALLY' && row.slot === 2),
        native_title_and_author_remove_newlines: beforeNoEdit.values.title === 'Exact typed no-edit roundtrip ' + unique + 'second declared title line' &&
          beforeNoEdit.values.author === 'Declared operator 😀second declared author line',
        native_description_normalizes_crlf_to_lf: beforeNoEdit.values.source === '직접 입력한 출처 α\n관찰과 검증 상태는 별개',
        original_title_newline_retained: newTyped.body.capture.title === typedCapture.title,
        original_source_author_newline_retained: newTyped.body.capture.source.author === typedCapture.source.author,
        original_source_description_crlf_retained: newTyped.body.capture.source.description === typedCapture.source.description,
        declared_timestamp_retained: newTyped.body.capture.observed_at, declared_source_retained: equal(newTyped.body.capture.source, typedCapture.source),
        original_snapshot_immutable: equal(oldTyped.body, typedCreated.body), successor_revision: newTyped.body.revision,
        validation_state: newTyped.body.validation_state, coaching_enabled: newTyped.body.coaching_enabled });
  } finally {
    for (const route of held) { route.release(); await page.unroute(route.pattern, route.handler).catch(() => {}); }
    page.off('request', track);
  }
};

'use strict';
// Actual browser navigation and real SQLite deletion. route.fetch() performs
// the genuine GET/DELETE; only response delivery is held for the race.
const crypto = require('node:crypto');
function deferred() {let resolve, reject; const promise = new Promise((yes, no) => {resolve = yes; reject = no;}); return {promise, resolve, reject};}
async function bounded(promise, label) {
  let timer;
  try {return await Promise.race([promise, new Promise((_, reject) => {timer = setTimeout(() => reject(new Error(label + ' timed out')), 15000);})]);}
  finally {clearTimeout(timer);}
}

module.exports = async function checkResearchNavigation({page, check, baseUrl, token}) {
  const auth = {Authorization: 'Bearer ' + token};
  const routeCleanup = [];
  async function api(route, method = 'GET', data) {
    const response = await page.context().request.fetch(baseUrl + '/dev/v1' + route, {method, headers: auth, ...(data === undefined ? {} : {data})});
    return {status: response.status(), body: await response.json()};
  }
  async function snapshot() {
    return page.evaluate(() => ({id: rResource && rResource.id, note_id: rNote && rNote.resource_id,
      known: document.getElementById('r-known').value, dirty: rDirty,
      detail_hidden: document.getElementById('r-detail').hidden,
      note_disabled: document.getElementById('r-known').disabled,
      delete_disabled: document.getElementById('r-delete').disabled,
      notice: document.getElementById('r-notice').textContent}));
  }
  async function nativeDeleteConfirmation() {
    const dialogPending = page.waitForEvent('dialog');
    const clicked = page.click('#r-delete');
    const dialog = await bounded(dialogPending, 'Native delete confirmation');
    const record = {type: dialog.type(), message: dialog.message(), response: 'accept'};
    await dialog.accept(); await clicked; return record;
  }
  async function holdActual(routeSuffix, method) {
    const fetched = deferred(), gate = deferred(), delivered = deferred();
    const pattern = '**/dev/v1' + routeSuffix;
    const handler = async route => {
      if (route.request().method() !== method) return route.continue();
      try {
        const response = await route.fetch();
        const body = await response.json();
        fetched.resolve({status: response.status(), body});
        await gate.promise;
        await route.fulfill({response});
        delivered.resolve();
      } catch (error) {fetched.reject(error); delivered.reject(error); await route.abort().catch(() => {});}
    };
    await page.route(pattern, handler);
    routeCleanup.push({pattern, handler, release: () => gate.resolve()});
    return {fetched: fetched.promise, delivered: delivered.promise, release: () => gate.resolve()};
  }
  try {
    // The preceding byte-integrity module deliberately ends logged out.
    await page.reload();
    if (!(await page.evaluate(() => Boolean(sessionStorage.getItem('lol-coach-dev-token'))))) {
      await page.fill('#token', token); await page.click('#login-form button');
    }
    await page.waitForFunction(() => !document.getElementById('workspace').hidden &&
      document.getElementById('notice').textContent.startsWith('연결됐습니다.'));
    const runId = crypto.randomUUID();
    const addedA = await api('/research', 'POST', {source_type: 'raw_json', title: 'Navigation race A ' + runId,
      raw_text: JSON.stringify({note: 'synthetic navigation A ' + runId})});
    const addedB = await api('/research', 'POST', {source_type: 'raw_json', title: 'Navigation race B ' + runId,
      raw_text: JSON.stringify({note: 'synthetic navigation B ' + runId})});
    if (addedA.status !== 201 || addedB.status !== 201) throw new Error('Actual navigation fixture creation failed');
    const a = addedA.body.id, b = addedB.body.id;
    await page.click('#show-research');
    await page.waitForSelector('#r-list button[data-resource-id="' + a + '"]');
    await page.click('#r-list button[data-resource-id="' + a + '"]');
    await page.waitForFunction(id => rResource && rResource.id === id &&
      !document.getElementById('r-known').disabled, a);

    const getB = await holdActual('/research/' + b, 'GET');
    const deleteA = await holdActual('/research/' + a, 'DELETE');
    await page.click('#r-list button[data-resource-id="' + b + '"]');
    const actualBRead = await bounded(getB.fetched, 'Actual B GET');
    const loading = await snapshot();
    check('research-loading-disables-delete-button', actualBRead.status === 200 &&
      actualBRead.body.id === b && loading.id === a && loading.delete_disabled && loading.note_disabled,
      {actual_b_get_status: actualBRead.status, old_resource_still_displayed: loading.id === a,
        delete_disabled: loading.delete_disabled, note_disabled: loading.note_disabled});

    // Recreate the legacy enabled-control window only for this adversarial
    // response-identity test. Production prevention remains separately checked.
    await page.evaluate(() => {document.getElementById('r-delete').disabled = false;});
    const legacyDialog = await nativeDeleteConfirmation();
    const actualDeletedA = await bounded(deleteA.fetched, 'Actual DELETE A');
    getB.release(); await bounded(getB.delivered, 'B GET delivery');
    await page.waitForFunction(id => rResource && rResource.id === id &&
      rNote && rNote.resource_id === id && !document.getElementById('r-known').disabled, b);
    const draft = 'B 미저장 노트: A 삭제 응답보다 새로운 선택을 보존';
    await page.fill('#r-known', draft);
    const beforeOldDelete = await snapshot();
    deleteA.release(); await bounded(deleteA.delivered, 'A DELETE delivery');
    await page.evaluate(() => new Promise(resolve => setTimeout(resolve, 0)));
    const afterOldDelete = await snapshot();
    check('research-real-held-delete-a-cannot-clear-new-b-draft', actualDeletedA.status === 200 &&
      actualDeletedA.body.id === a && legacyDialog.type === 'confirm' &&
      JSON.stringify(afterOldDelete) === JSON.stringify(beforeOldDelete) &&
      afterOldDelete.id === b && afterOldDelete.known === draft && afterOldDelete.dirty,
      {actual_delete_status: actualDeletedA.status, actual_deleted_id: actualDeletedA.body.id,
        native_confirmation: legacyDialog, exact_b_state_retained: JSON.stringify(afterOldDelete) === JSON.stringify(beforeOldDelete),
        exact_b_draft_retained: afterOldDelete.known === draft, b_dirty: afterOldDelete.dirty});

    const backendA = await api('/research/' + a), backendB = await api('/research/' + b);
    const bNote = await api('/research/' + b + '/notes/overview'), listAfterA = await api('/research');
    check('research-real-backend-a-deleted-b-preserved', backendA.status === 404 && backendB.status === 200 &&
      backendB.body.id === b && bNote.status === 200 && bNote.body.revision === 0 &&
      listAfterA.status === 200 && !listAfterA.body.some(row => row.id === a) && listAfterA.body.some(row => row.id === b),
      {deleted_a_get_status: backendA.status, retained_b_get_status: backendB.status,
        b_note_revision: bNote.body.revision, b_exists_in_actual_list: listAfterA.body.some(row => row.id === b)});

    const currentDeleteResponse = page.waitForResponse(response => response.request().method() === 'DELETE' &&
      new URL(response.url()).pathname === '/dev/v1/research/' + b);
    const currentDialog = await nativeDeleteConfirmation();
    const responseB = await currentDeleteResponse, bodyB = await responseB.json();
    await page.waitForFunction(id => rResource === null && rNote === null &&
      document.getElementById('r-detail').hidden && document.getElementById('r-known').value === '' &&
      document.getElementById('r-notice').textContent === '자료와 노트를 삭제했습니다.' &&
      !document.querySelector('#r-list button[data-resource-id="' + id + '"]'), b);
    const currentCleared = await snapshot();
    const deletedB = await api('/research/' + b), deletedBNote = await api('/research/' + b + '/notes/overview');
    const finalList = await api('/research');
    check('research-current-delete-clears-notes-backend-and-list', responseB.status() === 200 && bodyB.id === b &&
      currentDialog.type === 'confirm' && currentCleared.id === null && currentCleared.note_id === null &&
      currentCleared.known === '' && !currentCleared.dirty && currentCleared.detail_hidden &&
      deletedB.status === 404 && deletedBNote.status === 404 && finalList.status === 200 &&
      !finalList.body.some(row => row.id === a || row.id === b),
      {actual_current_delete_status: responseB.status(), native_confirmation: currentDialog,
        selection_cleared: currentCleared.id === null, exact_note_cleared: currentCleared.known === '',
        dirty_cleared: !currentCleared.dirty, deleted_b_get_status: deletedB.status,
        deleted_b_note_status: deletedBNote.status, actual_list_excludes_b: !finalList.body.some(row => row.id === b)});
  } finally {
    for (const item of routeCleanup) item.release();
    for (const item of routeCleanup) await page.unroute(item.pattern, item.handler);
  }
};

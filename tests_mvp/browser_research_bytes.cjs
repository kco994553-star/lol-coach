'use strict';
// Real browser File bytes and real coach_v1.server requests. Only native read
// delivery is delayed; no HTTP response or source content is fabricated.
const crypto = require('node:crypto');
const hash = value => crypto.createHash('sha256').update(value).digest('hex');

module.exports = async function checkResearchSourceBytes({page, check, baseUrl, token}) {
  const sourcePosts = [];
  const track = request => {
    if (request.method() === 'POST' && new URL(request.url()).pathname === '/dev/v1/research') {
      const data = request.postDataJSON();
      sourcePosts.push({title: data.title, source_type: data.source_type});
    }
  };
  page.on('request', track);

  async function resources() {
    const response = await page.context().request.get(baseUrl + '/dev/v1/research', {
      headers: {Authorization: 'Bearer ' + token}
    });
    if (response.status() !== 200) throw new Error('Research resource snapshot HTTP ' + response.status());
    return (await response.json()).map(row => row.id).sort();
  }

  async function stored(id) {
    const response = await page.context().request.get(baseUrl + '/dev/v1/research/' + id, {
      headers: {Authorization: 'Bearer ' + token}
    });
    if (response.status() !== 200) throw new Error('Stored research HTTP ' + response.status());
    return response.json();
  }

  async function resetDocument() {
    await page.reload();
    if (!(await page.evaluate(() => Boolean(sessionStorage.getItem('lol-coach-dev-token'))))) {
      await page.fill('#token', token);
      await page.click('#login-form button');
    }
    await page.waitForFunction(() => !document.getElementById('workspace').hidden &&
      document.getElementById('notice').textContent.startsWith('연결됐습니다.'));
    await page.click('#show-research');
    await page.waitForFunction(() => document.getElementById('r-list').children.length > 0);
    const details = page.locator('details').filter({has: page.locator('#r-file')});
    if (!(await details.evaluate(element => element.open))) await details.locator('summary').click();
    await page.selectOption('#r-kind', 'raw_json');
  }

  async function snapshot() {
    return page.evaluate(() => ({
      id: rResource && rResource.id, title: document.getElementById('r-title').textContent,
      note: rNote && {resource_id: rNote.resource_id, anchor: rNote.anchor, revision: rNote.revision},
      known: document.getElementById('r-known').value,
      dirty: rDirty, detail_hidden: document.getElementById('r-detail').hidden,
      notice: document.getElementById('r-notice').textContent,
      note_state: document.getElementById('r-note-state').textContent,
      selected_file: document.getElementById('r-file').files[0]?.name || null,
      note_disabled: document.getElementById('r-known').disabled,
      save_disabled: document.getElementById('r-save').disabled,
      workspace_hidden: document.getElementById('workspace').hidden
    }));
  }

  async function selectFile(name, bytes) {
    await page.setInputFiles('#r-file', {name, mimeType: name.endsWith('.txt') ? 'text/plain' : 'application/json', buffer: bytes});
  }

  async function importFile(name, bytes, kind = 'raw_json') {
    await page.selectOption('#r-kind', kind);
    if (kind === 'transcript') await page.fill('#r-video-id', 'CejHqSces8Q');
    const responsePending = page.waitForResponse(response => {
      if (response.request().method() !== 'POST' || new URL(response.url()).pathname !== '/dev/v1/research') return false;
      return response.request().postDataJSON().title === name;
    });
    await selectFile(name, bytes);
    const response = await responsePending;
    const resource = await response.json();
    if (response.status() !== 201) throw new Error('File import HTTP ' + response.status());
    await page.waitForFunction(expected => rResource && rResource.id === expected.id &&
      document.getElementById('r-title').textContent === expected.title &&
      document.getElementById('r-notice').textContent === '저장된 자료를 열었습니다.' &&
      !document.getElementById('r-known').disabled &&
      document.getElementById('r-file').files.length === 0,
      {id: resource.id, title: resource.title});
    return {status: response.status(), resource, persisted: await stored(resource.id)};
  }

  async function installHeldNativeReads(names) {
    await page.evaluate(fileNames => {
      window.__researchByteReads = Object.create(null);
      for (const method of ['arrayBuffer', 'text']) {
        const native = File.prototype[method];
        File.prototype[method] = function () {
          if (!fileNames.includes(this.name)) return native.call(this);
          const realRead = native.call(this);
          let release;
          const gate = new Promise(resolve => {release = resolve;});
          const state = {method, ready: false, released: false,
            release: () => {state.released = true; release();}};
          window.__researchByteReads[this.name] = state;
          realRead.then(() => {state.ready = true;}, () => {state.ready = true;});
          return gate.then(() => realRead);
        };
      }
    }, names);
  }

  async function heldFile(name, bytes) {
    await selectFile(name, bytes);
    await page.waitForFunction(fileName => window.__researchByteReads[fileName]?.ready, name);
  }

  async function release(name) {
    await page.evaluate(async fileName => {
      window.__researchByteReads[fileName].release();
      // Drain the real read's promise, decoding and change-handler finally.
      await new Promise(resolve => setTimeout(resolve, 0));
    }, name);
  }

  const invalid = Buffer.concat([Buffer.from('{"note":"'), Buffer.from([0xff]), Buffer.from('"}')]);
  const sameIds = (a, b) => JSON.stringify(a) === JSON.stringify(b);
  try {
    await resetDocument();
    const bomJson = Buffer.concat([Buffer.from([0xef, 0xbb, 0xbf]), Buffer.from('{"allPlayers":[],"note":"BOM byte fidelity"}')]);
    const raw = await importFile('browser-bytes-bom.json', bomJson);
    check('research-valid-bom-raw-byte-hash', raw.resource.report.raw_sha256 === hash(bomJson) &&
      raw.persisted.report.raw_sha256 === hash(bomJson) && raw.resource.report.coaching_enabled === false,
      {http_status: raw.status, original_sha256: hash(bomJson), reported_sha256: raw.resource.report.raw_sha256,
        persisted_sha256: raw.persisted.report.raw_sha256});

    const transcript = Buffer.concat([Buffer.from([0xef, 0xbb, 0xbf]), Buffer.from(
      'YouTube transcript\nVideo ID: CejHqSces8Q\nLanguage: en\nCaptions: manual\n\n[0:01] wave byte fidelity\n')]);
    const video = await importFile('browser-bytes-bom.txt', transcript, 'transcript');
    check('research-valid-bom-transcript-byte-hash', video.resource.report.transcript_sha256 === hash(transcript) &&
      video.persisted.report.transcript_sha256 === hash(transcript) && video.resource.report.cue_count === 1 &&
      video.resource.report.coaching_enabled === false,
      {http_status: video.status, original_sha256: hash(transcript), reported_sha256: video.resource.report.transcript_sha256,
        persisted_sha256: video.persisted.report.transcript_sha256});

    const unicode = Buffer.from('{"note":"한글·日本語·😀·literal �","allPlayers":[]}');
    const multibyte = await importFile('browser-bytes-multibyte.json', unicode);
    check('research-valid-multibyte-literal-replacement-byte-hash', multibyte.resource.report.raw_sha256 === hash(unicode) &&
      multibyte.persisted.report.raw_sha256 === hash(unicode),
      {http_status: multibyte.status, original_sha256: hash(unicode), reported_sha256: multibyte.resource.report.raw_sha256});

    await page.fill('#r-known', '보존할 미저장 UTF-8 검증 노트');
    const old = await snapshot(), beforeInvalid = await resources(), beforePosts = sourcePosts.length;
    await selectFile('browser-bytes-malformed.json', invalid);
    await page.waitForFunction(() => document.getElementById('r-file').files.length === 0);
    const failed = await snapshot(), afterInvalid = await resources();
    check('research-malformed-utf8-no-post-or-resource', sourcePosts.length === beforePosts && sameIds(beforeInvalid, afterInvalid),
      {posts_before: beforePosts, posts_after: sourcePosts.length, resource_ids_unchanged: sameIds(beforeInvalid, afterInvalid)});
    check('research-malformed-error-retains-old-dirty-note',
      failed.notice === '처리하지 못했습니다: UTF-8 파일 형식이 올바르지 않습니다.' && failed.id === old.id &&
      failed.title === old.title && JSON.stringify(failed.note) === JSON.stringify(old.note) &&
      failed.known === old.known && failed.dirty && failed.note_state === old.note_state &&
      !failed.note_disabled && !failed.save_disabled && !failed.detail_hidden,
      {notice: failed.notice, old_resource_retained: failed.id === old.id, exact_note_retained: failed.known === old.known,
        note_revision_retained: JSON.stringify(failed.note) === JSON.stringify(old.note), dirty: failed.dirty,
        note_editable: !failed.note_disabled, save_enabled: !failed.save_disabled});

    await resetDocument();
    await installHeldNativeReads(['invalid-a-before.json', 'valid-b-pending.json']);
    const aBefore = await snapshot(), aPosts = sourcePosts.length;
    await heldFile('invalid-a-before.json', invalid);
    const newestB = Buffer.from('{"note":"newest B pending","allPlayers":[]}');
    await heldFile('valid-b-pending.json', newestB);
    await release('invalid-a-before.json');
    const pendingB = await snapshot();
    const bHeld = await page.evaluate(() => window.__researchByteReads['valid-b-pending.json'].released === false);
    check('research-stale-invalid-a-before-b-keeps-newest-pending',
      pendingB.notice === aBefore.notice && pendingB.id === aBefore.id && pendingB.selected_file === 'valid-b-pending.json' &&
      sourcePosts.length === aPosts && bHeld,
      {notice_unchanged: pendingB.notice === aBefore.notice, resource_unchanged: pendingB.id === aBefore.id,
        selected_file: pendingB.selected_file, no_new_post: sourcePosts.length === aPosts, newest_b_still_held: bHeld});
    await release('valid-b-pending.json');
    await page.waitForFunction(() => document.getElementById('r-title').textContent === 'valid-b-pending.json' &&
      document.getElementById('r-notice').textContent === '저장된 자료를 열었습니다.' &&
      !document.getElementById('r-known').disabled);

    await resetDocument();
    await installHeldNativeReads(['invalid-a-after.json', 'valid-b-first.json']);
    await heldFile('invalid-a-after.json', invalid);
    const bFirstBytes = Buffer.from('{"note":"newest B first","allPlayers":[]}');
    await heldFile('valid-b-first.json', bFirstBytes);
    await release('valid-b-first.json');
    await page.waitForFunction(() => document.getElementById('r-title').textContent === 'valid-b-first.json' &&
      document.getElementById('r-notice').textContent === '저장된 자료를 열었습니다.' &&
      !document.getElementById('r-known').disabled && document.getElementById('r-file').files.length === 0);
    const bBeforeStale = await snapshot(), bPosts = sourcePosts.length;
    await release('invalid-a-after.json');
    const bAfterStale = await snapshot(), bStored = await stored(bAfterStale.id);
    check('research-stale-invalid-a-after-b-cannot-replace-or-error',
      JSON.stringify(bAfterStale) === JSON.stringify(bBeforeStale) && sourcePosts.length === bPosts &&
      bStored.report.raw_sha256 === hash(bFirstBytes),
      {exact_ui_state_retained: JSON.stringify(bAfterStale) === JSON.stringify(bBeforeStale), no_stale_post: sourcePosts.length === bPosts,
        persisted_sha256: bStored.report.raw_sha256, original_b_sha256: hash(bFirstBytes)});

    await resetDocument();
    await installHeldNativeReads(['invalid-after-logout.json']);
    await heldFile('invalid-after-logout.json', invalid);
    const logoutPosts = sourcePosts.length;
    await page.click('#show-synthetic');
    await page.click('#logout');
    const loggedOut = await snapshot();
    await release('invalid-after-logout.json');
    const afterLogoutRead = await snapshot();
    // The selected input is cleared by the stale handler's finally block;
    // that legitimate cleanup must not be mistaken for a stale UI error.
    const comparableLogout = value => {const result = {...value}; delete result.selected_file; return result;};
    const logoutUnchanged = JSON.stringify(comparableLogout(afterLogoutRead)) === JSON.stringify(comparableLogout(loggedOut));
    check('research-logout-pending-malformed-read-no-stale-error',
      logoutUnchanged && afterLogoutRead.workspace_hidden &&
      afterLogoutRead.id === null && afterLogoutRead.note === null && sourcePosts.length === logoutPosts,
      {exact_logged_out_state_retained_except_input_cleanup: logoutUnchanged,
        workspace_hidden: afterLogoutRead.workspace_hidden, cleared_resource: afterLogoutRead.id === null,
        cleared_note: afterLogoutRead.note === null, no_post_after_logout: sourcePosts.length === logoutPosts});
  } finally {
    page.off('request', track);
  }
};

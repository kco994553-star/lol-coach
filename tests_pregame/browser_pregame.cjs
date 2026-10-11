'use strict';
const {chromium} = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '..');
const output = process.env.PREGAME_BROWSER_EVIDENCE_DIR;
const mode = process.env.PREGAME_BROWSER_MODE;
if (!output || !['actual', 'synthetic'].includes(mode)) throw new Error('Use scripts/browser_pregame.py');
const token = fs.readFileSync(process.env.WORKBENCH_TOKEN_FILE, 'utf8').trim();
const url = process.env.WORKBENCH_URL;
const roles = ['TOP', 'JUNGLE', 'MID', 'BOTTOM', 'SUPPORT'];
const champions = ['Ornn', 'Sejuani', 'Ahri', 'Caitlyn', 'Lux'];
const roleChecks = ['exact-input', 'nine-cards', 'selected-map-row', 'common-invariant',
  'personal-context', 'detail-input-binding', 'immutable-reopen', 'edit-hides-plan'];
const finalChecks = ['source-preview', 'source-navigation', 'proposal-only-import',
  'untrusted-approval-blocked', 'empty-patch-approval-disabled', 'export-history',
  'mobile-layout', 'logout-clears', 'no-user-decisions', 'no-browser-errors', 'source-hashes-stable'];
const expected = ['connected', ...roles.flatMap(r => roleChecks.map(c => r + '-' + c)), ...finalChecks];
const checks = [], pageErrors = [], consoleErrors = [], httpErrors = [], snapshots = [];
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const sourcePaths = Object.keys(JSON.parse(process.env.PREGAME_SOURCE_HASHES));
const sourceHashes = () => Object.fromEntries(sourcePaths.map(name => [name, hash(fs.readFileSync(path.join(root, name)))]));
const initialHashes = sourceHashes();
let browser, page, firstFailure = null, browserVersion = null, decisions = 0, dialogs = 0;
function check(id, passed, actual) {
  checks.push({id, passed: Boolean(passed), actual});
  if (!passed) throw new Error('Failed check: ' + id);
}
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
async function ready() {
  await page.waitForFunction(() => !document.getElementById('pg-workspace').hidden &&
    !document.getElementById('pg-login').disabled &&
    document.getElementById('pg-notice').textContent.includes('연결'));
  await page.waitForLoadState('networkidle');
}
async function jsonPlan() { return JSON.parse(await page.locator('#pg-plan-json').textContent()); }
async function saveAndPlan() {
  const saved = page.waitForResponse(r => /\/pregame\/inputs(?:\/[a-f0-9]+)?$/.test(r.url()) && ['POST','PUT'].includes(r.request().method()));
  await page.locator('#pg-save').click();
  const response = await saved;
  if (!response.ok()) throw new Error('Save failed status ' + response.status());
  await page.waitForFunction(() => !document.getElementById('pg-create-plan').disabled);
  const generated = page.waitForResponse(r => /\/inputs\/[a-f0-9]+\/plans$/.test(r.url()) && r.request().method() === 'POST');
  await page.locator('#pg-create-plan').click();
  const response2 = await generated;
  if (!response2.ok()) throw new Error('Plan failed status ' + response2.status());
  await page.locator('#pg-plan-panel').waitFor({state:'visible'});
  return jsonPlan();
}
async function reopen(plan) {
  await page.reload(); await ready();
  await page.locator('#pg-input-list button').first().click();
  await page.waitForFunction(() => !document.getElementById('pg-create-plan').disabled);
  await page.locator('#pg-input-list').locator('..').getByText('입력·계획 이력', {exact:true}).click();
  await page.locator('#pg-plan-list button').first().click();
  await page.locator('#pg-plan-panel').waitFor({state:'visible'});
  return jsonPlan();
}
(async () => {
  try {
    browser = await chromium.launch({headless:true, executablePath:process.env.CHROMIUM_EXECUTABLE,
      args:['--no-sandbox', '--disable-dev-shm-usage']});
    browserVersion = browser.version();
    const context = await browser.newContext({viewport:{width:1280,height:960}});
    page = await context.newPage();
    page.on('pageerror', e => pageErrors.push(String(e).split(token).join('[REDACTED]')));
    page.on('console', m => {if (m.type() === 'error') consoleErrors.push(m.text().split(token).join('[REDACTED]'));});
    page.on('request', r => {if (/\/decisions$/.test(r.url())) decisions++;});
    page.on('response', r => {if (r.status() >= 400) httpErrors.push({path:new URL(r.url()).pathname,status:r.status()});});
    page.on('dialog', async d => {dialogs++; await d.dismiss();});
    await page.goto(url);
    await page.locator('#pg-token').fill(token); await page.locator('#pg-login').click(); await ready();
    const initialKnowledgeResponse = await context.request.get(new URL('/dev/v1/pregame/knowledge',url).href,
      {headers:{Authorization:'Bearer '+token}});
    const initialKnowledge = await initialKnowledgeResponse.json();
    const priorities = await page.locator('#pg-review-priority > details').count();
    const candidates = await page.locator('#pg-candidate-list button').count();
    const rosterCount = await page.locator('#pg-roster option').count();
    check('connected', await page.locator('#pg-workspace').isVisible() && initialKnowledgeResponse.ok() &&
      initialKnowledge.length === (mode === 'actual' ? 0 : 18) && priorities === 10 &&
      candidates === 190 && rosterCount === 173,
      {mode,initial_knowledge_count:initialKnowledge.length,review_priority_count:priorities,
        candidate_count:candidates,roster_count:rosterCount});
    await page.locator('#pg-golden').click();
    if (mode === 'synthetic') await page.locator('#pg-patch').fill('SYNTHETIC-1');
    let common = null, previousPersonal = null, lastPlan;
    for (const [i, role] of roles.entries()) {
      await page.locator('#pg-my-position').selectOption(role);
      await page.locator('#pg-my-champion').fill(champions[i]);
      await page.locator('#pg-my-slot').selectOption(String(i+1));
      const plan = await saveAndPlan(); lastPlan = plan;
      snapshots.push(plan);
      check(role+'-exact-input', plan.input.patch === (mode === 'actual' ? null : 'SYNTHETIC-1') &&
        plan.input.phase === 'PRE_GAME' && plan.input.my_position === role && plan.input.my_slot === i+1 &&
        plan.input.my_champion === champions[i] && plan.input.slots.length === 10 &&
        plan.input.slots.every((s,n) => s.position === roles[n%5] && s.champion ===
          [...champions,'Fiora','LeeSin','Zed','Ezreal','Nautilus'][n]) &&
        plan.coaching_accuracy === null && plan.real_match_validation === 'NOT_EVALUATED',
        {patch:plan.input.patch, position:role, revision:plan.input_revision});
      check(role+'-nine-cards', await page.locator('#pg-cards > article').count() === 9 &&
        await page.locator('.pg-map-row').count() === 5, {cards:9,map_rows:5});
      check(role+'-selected-map-row', await page.locator('.pg-map-row.selected').count() === 1 &&
        await page.locator('.pg-map-row.selected').getAttribute('data-position') === role, {role});
      check(role+'-common-invariant', common === null || same(common, plan.common), {common_sha256:hash(JSON.stringify(plan.common))});
      common = plan.common;
      const personal = Object.values(plan.personal);
      const personalOK = mode === 'actual' ? personal.every(c => c.status === 'UNKNOWN' && c.texts.length === 0 && c.reasons.length > 0) :
        ['role','lane','fight'].every(section => same(plan.personal[section].texts, ['SYNTHETIC fixture '+role+' '+section.toUpperCase()]));
      check(role+'-personal-context', personalOK && (previousPersonal === null || !same(previousPersonal, plan.personal)),
        {personal:plan.personal}); previousPersonal = plan.personal;
      await page.locator('#pg-card-role details > summary').click();
      const detail = JSON.parse(await page.locator('#pg-card-role details pre').textContent());
      check(role+'-detail-input-binding', same(detail.saved_input.input, plan.input) &&
        detail.saved_input.input_sha256 === plan.input_sha256 && same(detail.evaluations, plan.evaluations),
        {input_sha256:plan.input_sha256, evaluations:plan.evaluations.length});
      const reopened = await reopen(plan);
      check(role+'-immutable-reopen', same(reopened, plan) && reopened.validity === 'CURRENT', {plan_id:plan.id});
      await page.locator('#pg-title').fill('Golden10 '+role+' next edit');
      check(role+'-edit-hides-plan', !(await page.locator('#pg-plan-panel').isVisible()) &&
        await page.locator('#pg-create-plan').isDisabled(), {hidden:true});
    }
    await page.locator('#pg-candidate-list button').filter({hasText:'Q05-P-Sylas ·'}).click();
    const expandedSylas = JSON.parse(await page.locator('#pg-knowledge-json').textContent());
    const expandedSylasOK = expandedSylas.proposal === null && expandedSylas.spec.rule_id === 'Q05-P-Sylas' &&
      expandedSylas.spec.profile.champion === 'Sylas' && expandedSylas.spec.patches.length === 0 &&
      same(expandedSylas.spec.profile.threats, ['ASSASSINATION','DIVE']) &&
      !expandedSylas.spec.profile.threats.includes('GRAB_PICK') &&
      expandedSylas.spec.sources.length === 3 && expandedSylas.spec.sources.every(s => s.kind === 'DATA_DRAGON' && /^[a-f0-9]{64}$/.test(s.sha256)) &&
      await page.locator('#pg-knowledge-sources a').count() === 3 && await page.locator('#pg-approve').isDisabled();
    const spec = JSON.parse(fs.readFileSync(process.env.PREGAME_FIXTURE_FILE));
    await page.locator('#pg-spec-json').fill(JSON.stringify(spec)); await page.locator('#pg-preview-spec').click();
    const preview = JSON.parse(await page.locator('#pg-knowledge-json').textContent());
    check('source-preview', expandedSylasOK && same(preview.spec, spec) && await page.locator('#pg-knowledge-sources a').count() === 1,
      {source_kind:spec.sources[0].kind, rule_id:spec.rule_id,expanded_profile:expandedSylas.spec.profile,
        expanded_patch_scope:expandedSylas.spec.patches,expanded_source_count:expandedSylas.spec.sources.length});
    const source = page.locator('#pg-knowledge-sources a').first();
    await context.route('https://example.org/**', route => route.fulfill({status:200, contentType:'text/html',body:'SYNTHETIC browser navigation fixture'}));
    const popupPromise = page.waitForEvent('popup'); await source.click(); const popup = await popupPromise;
    await popup.waitForLoadState();
    check('source-navigation', popup.url() === spec.sources[0].url &&
      (await source.getAttribute('rel')).includes('noopener'), {url:popup.url(),network:'locally intercepted synthetic fixture'});
    await popup.close();
    const importedPromise = page.waitForResponse(r => r.url().endsWith('/pregame/candidates') && r.request().method() === 'POST');
    await page.locator('#pg-import-candidate').click(); const imported = await importedPromise; const item = await imported.json();
    await page.waitForLoadState('networkidle');
    check('proposal-only-import', imported.status() === 201 && item.proposal.review_state === 'EXPLORATORY' && decisions === 0,
      {state:item.proposal.review_state});
    await page.locator('#pg-knowledge-list button').first().click();
    const beforeDialogs = dialogs;
    const approveEnabled = !(await page.locator('#pg-approve').isDisabled());
    await page.evaluate(() => document.getElementById('pg-approve').click());
    await page.waitForTimeout(100);
    check('untrusted-approval-blocked', approveEnabled && decisions === 0 && dialogs === beforeDialogs,
      {approve_enabled_before_script_click:approveEnabled,decisions,dialogs});
    spec.patches = []; await page.locator('#pg-spec-json').fill(JSON.stringify(spec)); await page.locator('#pg-preview-spec').click();
    if (mode === 'actual') {
      const emptyImportPromise = page.waitForResponse(r => r.url().endsWith('/pregame/candidates') && r.request().method() === 'POST');
      await page.locator('#pg-import-candidate').click();
      const emptyImport = await emptyImportPromise; const emptyItem = await emptyImport.json();
      if (emptyImport.status() !== 201) throw new Error('Empty patch synthetic proposal import failed');
      await page.waitForLoadState('networkidle');
      await page.locator('#pg-knowledge-list button').filter({hasText:emptyItem.proposal.rule_id}).click();
      check('empty-patch-approval-disabled', await page.locator('#pg-approve').isDisabled() &&
        JSON.parse(await page.locator('#pg-knowledge-json').textContent()).proposal.patch_range === 'UNKNOWN',
        {patches:[],persisted_state:emptyItem.proposal.review_state});
    } else {
      check('empty-patch-approval-disabled', await page.locator('#pg-approve').isDisabled(),
        {patches:[],scope:'Unimported preview in synthetic read-only view; normal mode tests persisted proposal'});
    }
    const downloadPromise = page.waitForEvent('download'); await page.locator('#pg-export').click(); const download = await downloadPromise;
    const exportPath = path.join(output,'export.json'); await download.saveAs(exportPath);
    const archive = JSON.parse(fs.readFileSync(exportPath));
    check('export-history', archive.schema_version === 'pregame.archive.v1' && archive.inputs.length === 5 &&
      archive.plans.length === 5 && archive.plans.some(p => p.id === lastPlan.id), {inputs:archive.inputs.length,plans:archive.plans.length});
    await page.setViewportSize({width:390,height:844});
    const mobilePlan = await reopen(lastPlan);
    const geometry = await page.evaluate(() => ({width:innerWidth,scroll:document.documentElement.scrollWidth}));
    check('mobile-layout', geometry.scroll <= geometry.width && await page.locator('#pg-plan-panel').isVisible() &&
      (mode === 'actual' ? mobilePlan.validity === 'EXPIRED' && mobilePlan.expiry_reasons.includes('KNOWLEDGE_CHANGED') : mobilePlan.validity === 'CURRENT'),
      {...geometry,stored_plan_validity:mobilePlan.validity,expiry_reasons:mobilePlan.expiry_reasons});
    await page.screenshot({path:path.join(output,'mobile.png'),fullPage:true});
    await page.locator('#pg-logout').click();
    check('logout-clears', !(await page.locator('#pg-workspace').isVisible()) &&
      await page.locator('#pg-auth').isVisible() && await page.locator('#pg-knowledge-json').textContent() === '' &&
      await page.locator('#pg-plan-json').textContent() === '', {cleared:true});
    check('no-user-decisions', decisions === 0, {decision_requests:decisions});
    check('no-browser-errors', !pageErrors.length && !consoleErrors.length && !httpErrors.length,
      {pageErrors,consoleErrors,httpErrors});
    check('source-hashes-stable', same(sourceHashes(),initialHashes), {files:sourcePaths.length});
  } catch (error) {
    firstFailure = String(error.stack || error).split(token).join('[REDACTED]');
  } finally {
    if (browser) await browser.close();
    const passed = firstFailure === null && same(checks.map(c=>c.id),expected) && checks.every(c=>c.passed);
    const receipt = {evidence_kind:'FRESH_BROWSER_EXECUTION',mode,passed,browser_version:browserVersion,
      expected_check_ids:expected,checks,first_failure:firstFailure,page_errors:pageErrors,console_errors:consoleErrors,
      http_errors:httpErrors,
      source_sha256:sourceHashes(),tested_at:new Date().toISOString(),decision_requests:decisions,
      real_match_validation:'NOT_EVALUATED',coaching_accuracy:null,
      fixture_scope:mode === 'synthetic' ? 'Read-only injected SYNTHETIC reviewed view; persisted proposals remain EXPLORATORY; no actual approval persistence claim' : 'Normal server empty knowledge; actual golden patch=null'};
    fs.writeFileSync(path.join(output,'receipt.json'),JSON.stringify(receipt,null,2)+'\n');
    fs.writeFileSync(path.join(output,'plans.json'),JSON.stringify(snapshots,null,2)+'\n');
    process.stdout.write(JSON.stringify({passed,mode,checks:checks.length,first_failure:firstFailure})+'\n');
    process.exitCode = passed ? 0 : 1;
  }
})();

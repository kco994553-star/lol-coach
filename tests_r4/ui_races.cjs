'use strict';
// Targeted DOM-stub regression: delayed delete/import must not overwrite another
// session's unsaved editor. This is not a browser integration test.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'web_r4/app.js'), 'utf8');

function harness() {
  const elements = new Map();
  function element(id) {
    if (!elements.has(id)) elements.set(id, {
      value: '', hidden: false, disabled: false, textContent: '', className: '',
      files: [], listeners: {},
      addEventListener(type, callback) { this.listeners[type] = callback; },
      replaceChildren() {}, append() {}
    });
    return elements.get(id);
  }
  let resolveDelete;
  const context = vm.createContext({
    document: { getElementById: element, createElement: () => element(Symbol()) },
    sessionStorage: { getItem: () => '', setItem() {}, removeItem() {} },
    confirm: () => true, setTimeout, clearTimeout, console,
    crypto: { randomUUID: () => 'synthetic-key' },
    fetch: async (_url, options) => {
      if (options.method === 'DELETE') return new Promise(resolve => {
        resolveDelete = () => resolve({ ok: true, json: async () => ({ status: 'DELETED' }) });
      });
      return { ok: true, json: async () => [] };
    }
  });
  vm.runInContext(source, context, { filename: 'web_r4/app.js' });
  return { element, evaluate: code => vm.runInContext(code, context), finishDelete: () => resolveDelete() };
}

async function delayedDelete() {
  const h = harness();
  h.evaluate("current={id:'session-A',revision:1};");
  const pending = h.element('delete-session').listeners.click();
  h.evaluate("epoch++;current={id:'session-B',revision:1};$('case-json').value='UNSAVED SESSION B EDIT';");
  h.finishDelete();
  await pending;
  const actual = JSON.parse(h.evaluate("JSON.stringify({session_id:current&&current.id,editor:$('case-json').value})"));
  return { id: 'R4-UI-RACE-DELETE', passed: actual.session_id === 'session-B' && actual.editor === 'UNSAVED SESSION B EDIT', actual };
}

async function delayedImport() {
  const h = harness();
  let finishRead;
  h.evaluate("limits={body_bytes:10000};current={id:'session-A'};");
  h.element('import-file').files = [{ size: 10, text: () => new Promise(resolve => { finishRead = resolve; }) }];
  const pending = h.element('import-file').listeners.change();
  h.evaluate("epoch++;current={id:'session-B'};$('case-json').value='UNSAVED SESSION B EDIT';");
  // A newly selected file must also survive the old operation's finally block.
  h.element('import-file').files = [{ size: 10, text: async () => '{}' }];
  h.element('import-file').value = 'new-selection.json';
  finishRead(JSON.stringify({ mode: 'TEST', evidence_kind: 'SYNTHETIC', payload: 'OLD IMPORT' }));
  await pending;
  const actual = JSON.parse(h.evaluate("JSON.stringify({session_id:current&&current.id,editor:$('case-json').value,selected_file:$('import-file').value})"));
  return { id: 'R4-UI-RACE-IMPORT', passed: actual.session_id === 'session-B' && actual.editor === 'UNSAVED SESSION B EDIT' && actual.selected_file === 'new-selection.json', actual };
}

(async () => {
  const results = [await delayedDelete(), await delayedImport()];
  const evidence = {
    scope: 'Two independently reproduced asynchronous cross-session editor overwrite claims only',
    verifier: 'Node VM DOM stub; not browser E2E',
    executed_at: new Date().toISOString(),
    node_version: process.version,
    source_sha256: crypto.createHash('sha256').update(source).digest('hex'),
    initial_failures: {
      evidence_kind: 'PRIOR_OBSERVED_EXECUTION',
      note: 'Observed by independent reviewer before repair; pre-repair source hash was not captured. Preserved history, not a rerun against current source.',
      count: 2,
      results: [
        { id: 'R4-UI-RACE-DELETE', actual: { current: null, editor: '' } },
        { id: 'R4-UI-RACE-IMPORT', actual: { current: null, editor: { mode: 'TEST', evidence_kind: 'SYNTHETIC', payload: 'OLD IMPORT' } } }
      ]
    },
    fixed_results: { evidence_kind: 'FRESH_EXECUTION', passed: results.filter(r => r.passed).length, total: results.length, results }
  };
  const output = path.resolve(process.argv[2] || path.join(root, 'evidence/r4/ui-races.json'));
  fs.mkdirSync(path.dirname(output), { recursive: true });
  fs.writeFileSync(output, JSON.stringify(evidence, null, 2) + '\n');
  console.log(JSON.stringify(evidence.fixed_results));
  if (results.some(r => !r.passed)) process.exitCode = 1;
})().catch(error => { console.error(error); process.exitCode = 1; });

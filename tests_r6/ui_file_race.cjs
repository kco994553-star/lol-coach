'use strict';
// Node VM/DOM-stub regression for the independently observed stale file read.
// This verifies async orchestration, not browser file APIs or real game data.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'web_r4/research.js'), 'utf8');
const elements = new Map();
function element(id) {
  if (!elements.has(id)) elements.set(id, {
    value: '', files: [], disabled: false, hidden: false, textContent: '',
    dataset: {}, listeners: {},
    addEventListener(type, fn) { this.listeners[type] = fn; },
    replaceChildren() {}, append() {}
  });
  return elements.get(id);
}
const posts = [], errors = [];
let resource;
const context = vm.createContext({
  $: element, document: { querySelector: () => element('filter-label') },
  node: () => element(Symbol()), limits: { body_bytes: 10000 },
  confirm: () => true, error: e => errors.push(String(e)), console,
  api: async (route, method, body) => {
    if (method === 'POST') {
      posts.push(body.title);
      resource = { id: 'synthetic-resource', kind: 'RAW_DIAGNOSTIC', title: body.title,
        report: { declared_source_kind: 'UNVERIFIED_IMPORT', sections: {}, issues: [] } };
      return resource;
    }
    if (route === '/research') return [];
    if (route.endsWith('/notes/overview')) return {
      resource_id: resource.id, anchor: 'overview', revision: 0,
      known: '', intention: '', alternative: '', outcome: ''
    };
    if (route === '/research/synthetic-resource') return resource;
    throw Error('Unexpected route: ' + route);
  }
});
vm.runInContext(source, context, { filename: 'web_r4/research.js' });

(async () => {
  element('r-kind').value = 'raw_json';
  let finishA, finishB;
  const fileA = { name: 'A.json', size: 2, text: () => new Promise(r => { finishA = r; }) };
  const fileB = { name: 'B.json', size: 2, text: () => new Promise(r => { finishB = r; }) };
  element('r-file').files = [fileA];
  const pendingA = element('r-file').listeners.change();
  element('r-file').files = [fileB];
  const pendingB = element('r-file').listeners.change();
  finishA('{}');
  // Let A's full handler settle before B is resolved, reproducing the original order.
  await pendingA;
  const postsAfterA = [...posts];
  finishB('{}');
  await pendingB;
  const actual = {
    selectedMostRecently: 'B.json', postedFiles: posts, postsAfterA,
    displayedTitle: element('r-title').textContent, errors
  };
  const passed = postsAfterA.length === 0 && posts.length === 1 && posts[0] === 'B.json'
    && actual.displayedTitle === 'B.json' && errors.length === 0;
  const evidence = {
    scope: 'R6 stale file-read ordering claim only',
    verifier: 'Node VM DOM stub; not browser E2E or real LoL evidence',
    executed_at: new Date().toISOString(), node_version: process.version,
    source_sha256: crypto.createHash('sha256').update(source).digest('hex'),
    initial_failure: {
      evidence_kind: 'PRIOR_OBSERVED_EXECUTION',
      note: 'Independent reviewer observed this before repair. Pre-repair source hash was not captured; this is preserved history, not a current-source execution.',
      actual: { selectedMostRecently: 'B.json', postedFiles: ['A.json'], researchEpoch: 1 }
    },
    fixed_result: { evidence_kind: 'FRESH_EXECUTION', passed, actual }
  };
  const destination = path.resolve(process.argv[2] || path.join(root, 'evidence/r6/ui-file-race.json'));
  fs.mkdirSync(path.dirname(destination), { recursive: true });
  fs.writeFileSync(destination, JSON.stringify(evidence, null, 2) + '\n');
  console.log(JSON.stringify(evidence.fixed_result));
  if (!passed) process.exitCode = 1;
})().catch(error => { console.error(error); process.exitCode = 1; });

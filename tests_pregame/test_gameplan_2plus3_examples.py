"""Evidence exporter invariants: replay, pairing, raw output and source authority."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/export_gameplan_2plus3.js'


class Gameplan2Plus3ExamplesTests(unittest.TestCase):
    def node(self, code):
        result = subprocess.run(['node', '-e', code], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr[-6000:])

    def test_seed_selects_unique_role_complete_rosters_before_analysis(self):
        self.assertTrue(SCRIPT.is_file(), 'missing deterministic actual-engine exporter')
        self.node("""
const assert=require('node:assert/strict'),X=require('./scripts/export_gameplan_2plus3.js');
const c=X.catalog(),a=X.selectInputs(c,20261025),b=X.selectInputs(c,20261025);
assert.deepEqual(a,b);assert.notDeepEqual(a,X.selectInputs(c,20261026));
assert.deepEqual(a.map(x=>x.input.own_position),['TOP','JUNGLE','MID','BOTTOM','SUPPORT']);
for(const sample of a){const x=sample.input;assert.equal(new Set([...x.allies,...x.enemies].map(x=>x.champion)).size,10);
 for(const team of [x.allies,x.enemies])assert.deepEqual(team.map(x=>x.position),['TOP','JUNGLE','MID','BOTTOM','SUPPORT']);}
assert(c.champions[a[0].input.own_champion].official_tags.includes('Tank'));
assert(a[0].selection_basis.mechanism_facts.length>0);
""")

    def test_condition_pair_changes_exactly_one_leaf_and_preserves_roster(self):
        self.assertTrue(SCRIPT.is_file(), 'missing deterministic actual-engine exporter')
        self.node("""
const assert=require('node:assert/strict'),X=require('./scripts/export_gameplan_2plus3.js');
for(const sample of X.selectInputs(X.catalog(),20261025)){
 assert.equal(sample.input.schema_version,'lol-coach-loading-input-v5');
 assert.equal(sample.input.situation.fields.ally_followup.status,'assumed');
 assert.equal(sample.input.situation.fields.ally_followup.value,'AVAILABLE');
 const pair=X.conditionPair(sample.input);assert.equal(X.differences(sample.input,pair.input).length,1);
 assert.equal(pair.changed_path,'/situation/fields/ally_followup/value');
 assert.equal(pair.input.situation.fields.ally_followup.value,'UNAVAILABLE');
 assert.equal(X.differences(sample.input,pair.input)[0],pair.changed_path);
 assert.deepEqual(sample.input.allies,pair.input.allies);assert.deepEqual(sample.input.enemies,pair.input.enemies);
}
""")

    def test_exported_report_view_and_screen_are_unedited_actual_output(self):
        self.assertTrue(SCRIPT.is_file(), 'missing deterministic actual-engine exporter')
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as repeat:
            result = subprocess.run(['node', str(SCRIPT), '--output', directory], cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr[-4000:])
            again = subprocess.run(['node', str(SCRIPT), '--output', repeat], cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(again.returncode, 0, again.stderr[-4000:])
            files = sorted(path.name for path in Path(directory).iterdir())
            self.assertEqual(files, sorted(path.name for path in Path(repeat).iterdir()))
            for name in files:
                self.assertEqual((Path(directory) / name).read_bytes(), (Path(repeat) / name).read_bytes(), name)
            manifest = json.loads((Path(directory) / 'manifest.json').read_text())
            self.assertEqual(manifest['real_coaching_n'], 0)
            self.assertEqual(len(manifest['cases']), 5)
            self.node("""
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const X=require('./scripts/export_gameplan_2plus3.js'),E=require('./web_r4/loading-engine.js'),P=require('./web_r4/loading-presentation.js');
const dir=JSON.parse(process.argv[1]),m=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'))),c=X.catalog();
for(const entry of m.cases){const sample=JSON.parse(fs.readFileSync(path.join(dir,entry.file)));
 for(const variant of ['baseline','changed']){const s=sample[variant],r=E.analyze(s.input,c),v=P.project(r,{currentOnly:true});
  assert.deepEqual(s.report,JSON.parse(JSON.stringify(r)));assert.deepEqual(s.view,JSON.parse(JSON.stringify(v)));
  for(const line of s.screen){let value=v;for(const key of line.path.slice(1).split('/'))value=value[key.replace(/~1/g,'/').replace(/~0/g,'~')];assert.equal(line.text,value);}
  assert.equal(s.screen.length,X.strings(v).length);
 }
 assert.equal(sample.comparison.input_changes.length,1);
}
""".replace('JSON.parse(process.argv[1])', json.dumps(directory)))

    def test_source_binding_never_labels_modified_source_as_exact_commit(self):
        self.assertTrue(SCRIPT.is_file(), 'missing deterministic actual-engine exporter')
        self.node("""
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),cp=require('node:child_process');
const X=require('./scripts/export_gameplan_2plus3.js'),dir=fs.mkdtempSync(path.join(os.tmpdir(),'gp23-source-'));
try{const git=(...args)=>cp.execFileSync('git',['-C',dir,...args],{encoding:'utf8'}).trim();
 git('init','-q');fs.writeFileSync(path.join(dir,'source.js'),'original');git('add','source.js');git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','fixture');
 assert.equal(X.sourceBinding(dir,['source.js']).status,'EXACT_COMMIT');
 fs.writeFileSync(path.join(dir,'source.js'),'changed');const dirty=X.sourceBinding(dir,['source.js']);assert.equal(dirty.status,'WORKTREE_SNAPSHOT');assert.equal(dirty.source_commit,null);
 fs.writeFileSync(path.join(dir,'new.js'),'new');assert.equal(X.sourceBinding(dir,['new.js']).status,'WORKTREE_SNAPSHOT');
}finally{fs.rmSync(dir,{recursive:true,force:true});}
""")


if __name__ == '__main__':
    unittest.main()

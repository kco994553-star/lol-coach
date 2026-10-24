"""Registry scope, source integrity and snapshot regression checks."""
import copy
import importlib
import unittest
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module_path = ROOT / 'scripts/gameplan_registry.py'

    def api(self):
        self.assertTrue(self.module_path.exists(), 'inspectable registry implementation is missing')
        return importlib.import_module('scripts.gameplan_registry')

    def test_tree_has_authored_paths_and_explicit_unsupported_scopes(self):
        r = self.api().build_registry()
        c = r['champions']['Caitlyn']
        self.assertEqual(c['scopes']['BOTTOM']['status'], 'AUTHORED_CONDITIONAL')
        self.assertEqual(c['scopes']['MID']['status'], 'UNSUPPORTED_ROLE')
        self.assertEqual(r['champions']['Ahri']['scopes']['MID']['status'], 'MISSING_PROFILE')
        rule = c['rules'][0]
        self.assertIn('web_r4/loading-direction-profiles.js', rule['source_path'])
        self.assertTrue(rule['skill_ids'])
        self.assertFalse(r['observation'])
        self.assertEqual(r['review_state'], 'TACTICAL_UNREVIEWED')

    def test_migrated_profiles_preserve_authored_provenance(self):
        r = self.api().build_registry()
        for champion, role in [('Fiora', 'TOP'), ('Graves', 'JUNGLE')]:
            row = r['champions'][champion]
            self.assertEqual(row['scopes'][role]['status'], 'AUTHORED_CONDITIONAL')
            self.assertEqual(len(row['rules']), 3)
            self.assertEqual(row['rules'][0]['provenance']['source_path'], 'web_r4/loading-planboard.js')
            self.assertTrue(row['rules'][0]['id'].startswith(role.lower() + '-direction:'))

    def test_extended_profiles_reach_real_report(self):
        from tests_pregame.test_gameplan_coaching_content import GameplanCoachingContentTests
        GameplanCoachingContentTests.node(self, r"""
for(const role of ['TOP','JUNGLE']){
 const b=run(input(role));
 for(const phase of ['lane','operations','fight']){
  assert(b.direction_hierarchy?.[phase], role+':'+phase);
  assert(b.direction_hierarchy[phase].baseline.profile_id.startsWith(role.toLowerCase()+'-direction:'));
  assert.equal(b.direction_hierarchy[phase].review_state,'TACTICAL_UNREVIEWED');
  assert.equal(b.action_summaries[phase].items.length,5);
 }
}
""")

    def test_patch_impact_retains_untracked_and_all_required_slot_gates(self):
        api = self.api(); r = api.build_registry()
        impact = api.patch_impact(r, ['official:Caitlyn:E', 'official:Ahri:Q', 'unknown-id'])
        self.assertEqual(len(impact['affected']), 3)  # E gates the entire profile.
        self.assertIn('official:Ahri:Q', impact['untracked'])
        self.assertIn('unknown-id', impact['untracked'])
        self.assertFalse(impact['complete'])

    def test_manifest_reproducible_and_changes_comparable(self):
        api = self.api(); a = api.build_registry(); b = api.build_registry()
        self.assertEqual(a['manifest'], b['manifest'])
        self.assertEqual(api.compare_snapshots(a, b)['changed_files'], [])
        b = copy.deepcopy(b)
        b['champions']['Caitlyn']['rules'][0]['content']['gain'] += ' changed'
        b = api.seal_snapshot(b)
        delta = api.compare_snapshots(a, b)
        self.assertTrue(delta['changed_rules'])
        self.assertNotEqual(a['manifest']['snapshot_sha256'], b['manifest']['snapshot_sha256'])
        b['champions']['Caitlyn']['rules'][0]['content']['gain'] += ' tampered'
        with self.assertRaisesRegex(ValueError, 'SNAPSHOT_HASH'):
            api.compare_snapshots(a, b)

    def test_paths_reject_escape_absolute_and_symlinks(self):
        api = self.api()
        for path in ['../outside.json', '/etc/passwd', 'https://example.com/data']:
            with self.assertRaises(ValueError):
                api.repo_path(ROOT, path)
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            link = Path(tmp) / 'outside'
            link.symlink_to('/etc')
            with self.assertRaises(ValueError):
                api.repo_path(ROOT, str(link.relative_to(ROOT) / 'passwd'))

    def test_missing_binding_blocks_authored_support(self):
        api = self.api(); profiles, catalog, resolved = api.load_runtime(ROOT)
        catalog = copy.deepcopy(catalog)
        catalog['champions']['Caitlyn']['facts'][0]['sha256'] = '0' * 64
        r = api.build_registry(catalog=catalog, profiles=profiles, resolved=resolved)
        self.assertEqual(r['champions']['Caitlyn']['scopes']['BOTTOM']['status'], 'SOURCE_REVIEW_REQUIRED')
        self.assertIn('SOURCE_HASH_MISMATCH', r['champions']['Caitlyn']['skills'][0]['binding']['issues'])


if __name__ == '__main__':
    unittest.main()

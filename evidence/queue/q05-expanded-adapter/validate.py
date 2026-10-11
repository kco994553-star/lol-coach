"""Pure, local validation: exact labels, source bytes/excerpts, and Q03 binding."""
from pathlib import Path
import datetime
import hashlib
import json
import unittest

from coach_v1.pregame_contract import binding_matches, parse_rule, proposal_rule
from coach_v1.state import canonical, digest

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CATALOG = ROOT / 'knowledge_candidates/executable-expanded-v1.json'
ORIGINAL = ROOT / 'knowledge_candidates/executable-v1.json'
ROSTER = ROOT / 'knowledge_candidates/q05-roster-profiles.json'
TYPE_MAP = {'poke':'POKE','dive':'DIVE','grab-pick':'GRAB_PICK',
            'assassination':'ASSASSINATION','protection':'PEEL','frontline':'FRONTLINE'}


def locate(ref):
    path = ROOT / ref['archive']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == ref['sha256']
    value = json.loads(path.read_text())
    for key in ref['locator'].split('.'):
        value = value[int(key)] if isinstance(value,list) else value[key]
    assert value == ref['excerpt']
    return value


class ExpandedAdapterTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(CATALOG.exists(), 'expanded catalog has not been compiled')
        self.assertTrue((HERE / 'manifest.json').exists(), 'exact expanded source manifest missing')
        self.specs = json.loads(CATALOG.read_text())
        self.manifest = json.loads((HERE / 'manifest.json').read_text())
        self.roster = json.loads(ROSTER.read_text())
        self.profiles = {p['champion_id']:p for p in self.roster['profiles']}
        self.bindings = {b['rule_id']:b for b in self.manifest['bindings']}

    def test_exact_expanded_ids_and_combined_size(self):
        expected = {'Q05-P-'+cid for cid in self.roster['expanded_profile_ids']}
        self.assertEqual(len(self.specs),160)
        self.assertEqual(len({s['rule_id'] for s in self.specs}),160)
        self.assertEqual({s['rule_id'] for s in self.specs},expected)
        self.assertEqual(set(self.bindings),expected)
        original = json.loads(ORIGINAL.read_text())
        combined = original+self.specs
        self.assertEqual(len(combined),177)
        self.assertEqual(len({s['rule_id'] for s in combined}),177)
        # Default json.dumps matches current server serialization, which escapes
        # Korean text and is larger than the UTF-8 compact storage representation.
        self.assertLess(len(json.dumps(combined).encode()),1_000_000)
        self.assertLess(len(canonical(combined).encode()),1_000_000)

    def test_exact_contract_binding_and_unknown_execution_boundaries(self):
        for spec in self.specs:
            self.assertEqual(parse_rule(spec).model_dump(mode='json'),spec)
            self.assertTrue(binding_matches(proposal_rule(spec),spec))
            self.assertEqual(proposal_rule(spec)['patch_range'],'UNKNOWN')
            self.assertEqual(spec['scope'],'COMMON');self.assertEqual(spec['positions'],[])
            self.assertEqual(spec['patches'],[]);self.assertEqual(spec['cooldowns'],[])
            self.assertEqual(spec['required_fields'],['patch'])
            for name in ('conditions','counterconditions','stop_conditions'):
                self.assertEqual(spec[name],[])
            self.assertEqual(spec['output']['section'],'PROFILE');self.assertEqual(spec['output']['target'],'GLOBAL')
            self.assertIsNone(spec['output']['outlook'])
            for field in ('roles','strong_when','lane_style','jungle_style'):
                self.assertEqual(spec['profile'][field],[])

    def test_labels_and_text_are_exact_source_candidates(self):
        unknown=[]
        for spec in self.specs:
            cid=spec['profile']['champion'];row=self.profiles[cid]
            for original,mapped in [('threat_types','threats'),('protection_types','protection')]:
                expected=[TYPE_MAP[label] for label in (row[original] or [])]
                self.assertEqual(spec['profile'][mapped],expected)
                self.assertEqual(set(row[original] or []),{f['candidate_label'] for f in row['semantic_features'] if f['candidate_field']==original})
            self.assertEqual(spec['counterexamples'],row['counterexamples'])
            self.assertEqual(spec['limitations'],row['limitations'])
            self.assertEqual(spec['output']['text'],row['counterexamples'][-1])
            self.assertEqual(spec['output']['change_conditions'],row['counterexamples'])
            self.assertEqual(spec['output']['alternatives'],[])
            self.assertTrue(all(v is None for v in row['strength_by_phase'].values()))
            self.assertIsNone(row['position_candidate']);self.assertIsNone(row['lane_characteristics'])
            self.assertIsNone(row['jungle_characteristic'])
            if not row['semantic_features']:unknown.append(cid)
        self.assertEqual(unknown,self.roster['expanded_profiles_without_type_labels'])
        self.assertEqual(len(unknown),9)
        self.assertTrue(all(value is None for row in self.roster['profiles'] for value in row['strength_by_phase'].values()))

    def test_every_label_has_exact_source_excerpt_hash_and_locator(self):
        for spec in self.specs:
            row=self.profiles[spec['profile']['champion']]
            binding=self.bindings[spec['rule_id']]
            self.assertEqual(binding['spec_sha256'],digest(spec))
            self.assertEqual(binding['semantic_features'],row['semantic_features'])
            self.assertEqual(binding['original_file_sha256'],hashlib.sha256(ROSTER.read_bytes()).hexdigest())
            refs=binding['source_bindings']
            self.assertEqual(len(refs),len(spec['sources']))
            for source,ref in zip(spec['sources'],refs):
                self.assertIn(ref,row['source_refs']);locate(ref)
                for name in ('url','locator','sha256'):self.assertEqual(source[name],ref[name])
                self.assertEqual(source['patch'],'16.20.1');self.assertEqual(source['kind'],'DATA_DRAGON')
            for feature in row['semantic_features']:
                matching=[r for r in refs if r['locator']==feature['source_locator']]
                self.assertEqual(len(matching),1)
                ref=matching[0]
                self.assertEqual(feature['source_url'],ref['url'])
                self.assertEqual(feature['source_sha256'],ref['sha256'])
                self.assertEqual(feature['source_excerpt'],ref['excerpt'])
                self.assertEqual(feature['review_state'],'EXPLORATORY')
            labels=set((row['threat_types'] or [])+(row['protection_types'] or []))
            required_tag='Assassin' if 'assassination' in labels else None
            if required_tag:self.assertTrue(any(required_tag in r['excerpt'] for r in refs if r['locator'].endswith('.tags')))
            if 'frontline' in labels:self.assertTrue(any('Tank' in r['excerpt'] for r in refs if r['locator'].endswith('.tags')))
            mechanics={f['source_locator'] for f in row['semantic_features']}
            allowed=mechanics | ({'data.'+row['champion_id']+'.tags'} if not mechanics or labels & {'assassination','frontline'} else set())
            self.assertEqual({r['locator'] for r in refs},allowed)

    def test_original_catalog_and_source_rows_remain_unchanged(self):
        for path in [ORIGINAL,ROSTER,ROOT/'coach_v1/pregame_contract.py']:
            name=str(path.relative_to(ROOT))
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),self.manifest['preserved_files_sha256'][name])

    def test_exploratory_manifest_never_claims_approval_or_actual_game_validation(self):
        self.assertEqual(self.manifest['review_state'],'EXPLORATORY')
        self.assertIsNone(self.manifest['approval_actor']);self.assertFalse(self.manifest['coaching_enabled'])
        self.assertIsNone(self.manifest['runtime_patch']);self.assertIsNone(self.manifest['coaching_accuracy'])
        for name in ('production_proposals','user_web_approvals','gameplay_validation_count'):
            self.assertEqual(self.manifest[name],0)
        self.assertEqual(self.manifest['catalog_sha256'],hashlib.sha256(CATALOG.read_bytes()).hexdigest())


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ExpandedAdapterTests))
    if result.wasSuccessful():
        specs=json.loads(CATALOG.read_text());roster=json.loads(ROSTER.read_text())
        report=dict(status='PASS',tests=result.testsRun,expanded_specs=160,combined_specs=177,
            input_roster_commit=json.loads((HERE/'manifest.json').read_text())['input_roster_commit'],
            combined_default_json_bytes=len(json.dumps(json.loads(ORIGINAL.read_text())+specs).encode()),
            labels_with_exact_semantic_evidence=sum(len(p['semantic_features']) for p in roster['profiles'] if p['champion_id'] in roster['expanded_profile_ids']),
            remaining_semantic_unknown_ids=roster['expanded_profiles_without_type_labels'],
            all_phase_strength_unknown=True,expanded_positions_lane_jungle_unknown=True,
            all_gameplay_patch_scopes_empty=True,production_proposals=0,user_web_approvals=0,
            gameplay_validation_count=0,coaching_accuracy=None,
            verified_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        (HERE/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)

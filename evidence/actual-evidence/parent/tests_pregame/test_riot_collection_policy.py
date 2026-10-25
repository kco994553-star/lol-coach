import unittest

class RiotCollectionPolicyTests(unittest.TestCase):
    def test_current_official_version_pins_patch_instead_of_first_stale_seed_match(self):
        from coach_v1.riot_collection_policy import resolve_patch
        self.assertEqual(resolve_patch(['16.20.1','16.19.1']),'16.20')
        self.assertEqual(resolve_patch(['16.20.1'],explicit='16.19'),'16.19')
        with self.assertRaises(ValueError):resolve_patch(['https://evil.invalid'])

    def test_renewed_window_expires_without_scheduled_probe(self):
        from coach_v1.riot_collection_policy import key_enabled
        policy={'key_renewed_at':'2026-10-13T10:00:00Z','key_valid_until':'2026-10-14T10:00:00Z'}
        self.assertTrue(key_enabled(policy,1791892800))
        self.assertFalse(key_enabled(policy,1791975600))
        self.assertTrue(key_enabled(policy,1791975600,manual_confirmed=True))

    def test_grandmaster_gate_requires_same_patch_real_primary_insufficiency(self):
        from coach_v1.riot_collection_policy import auxiliary_needed
        from tests_pregame.test_challenger_reference import dataset
        # Missing current Challenger provenance never authorizes GM acquisition.
        self.assertFalse(auxiliary_needed([],patch='16.20'))
        d=dataset('CHALLENGER',patch='16.20')
        self.assertFalse(auxiliary_needed([d],patch='16.20'))
        self.assertFalse(auxiliary_needed([d],patch='other'))

    def test_actual_retained_challenger_insufficiency_authorizes_only_matching_patch(self):
        import gzip,json
        from pathlib import Path
        from coach_v1.riot_collection_policy import auxiliary_needed
        path=Path(__file__).resolve().parents[1]/'data/riot/2026-10-11/power-data.json.gz'
        with gzip.open(path,'rt') as source:data=json.load(source)
        self.assertTrue(auxiliary_needed([data],patch='16.20'))
        self.assertFalse(auxiliary_needed([data],patch='16.19'))

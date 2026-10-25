import unittest
from scripts import verify_actual_evidence as v

class EvidenceBindingTests(unittest.TestCase):
    def test_exact_source_authority_rejects_unregistered_source(self):
        manifest={'current_sha256':{p:'a'*64 for p in v.CURRENT}}
        self.assertTrue(v.exact_source_authority(manifest))
        # The collector is now an explicitly authorized, archived successor.
        unregistered='coach_v1/unregistered_fixture.py'
        self.assertNotIn(unregistered,v.CURRENT)
        manifest['current_sha256'][unregistered]='a'*64
        self.assertFalse(v.exact_source_authority(manifest))
    def test_new_file_inventory_has_no_broad_executable_exception(self):
        self.assertTrue(v.allowed_new('evidence/actual-evidence/notes.json'))
        self.assertFalse(v.allowed_new('evidence/actual-evidence/new_code.py'))
        self.assertFalse(v.allowed_new('data/resource_recovery/2026-10-16/raw.txt'))
        self.assertFalse(v.allowed_new('private/secret.json'))

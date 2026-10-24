"""Delta checks preserve completed v2.1 evidence without executing its tests."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch


class QueueV23BindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if importlib.util.find_spec('scripts.verify_mvp_v23') is None:
            return
        from scripts import verify_mvp_v23
        cls.v = verify_mvp_v23
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        for path in cls.v.required_paths():
            target = cls.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            source = cls.v.ROOT / path
            if source.is_file():
                shutil.copyfile(source, target)
            elif path in cls.v.CURRENT_PATHS:
                target.write_text('# isolated unfinished v2.3 source fixture\n')
            else:
                raise AssertionError('Missing preserved source: ' + path)
        gitdir = subprocess.check_output(['git', 'rev-parse', '--absolute-git-dir'], cwd=cls.v.ROOT, text=True).strip()
        (cls.root / '.git').write_text('gitdir: ' + gitdir + '\n')

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'temp'):
            cls.temp.cleanup()

    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('scripts.verify_mvp_v23'), 'v2.3 delta verifier missing')
        self.context = patch.object(self.v, 'ROOT', self.root)
        self.context.start()
        self.addCleanup(self.context.stop)
        self.binding = self.v.prepare_binding()
        self.save()

    def save(self):
        target = self.root / self.v.AMENDMENT
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.binding))

    def tamper(self, path, content=b'\n# tampered\n'):
        target = self.root / path
        original = target.read_bytes()
        self.addCleanup(target.write_bytes, original)
        target.write_bytes(original + content)

    def test_exact_delta_reuses_prior_ci_without_running_predecessor(self):
        result = self.v.v23_binding()
        self.assertEqual(result['status'], 'PASS', result)
        self.assertFalse(result['prior_completed_verification_rerun'])
        self.assertEqual(result['reused_ci_run_ids'], [38722880438, 38722880374])

    def test_unsealed_changes_fail(self):
        self.tamper('coach_v1/recall_stats.py')
        self.assertFalse(self.v.v23_binding()['checks']['current_bytes'])

    def test_declared_candidate_provenance_generator_is_byte_bound(self):
        path = 'evidence/queue/v23/candidate-author-build.py'
        self.assertIn(path, self.binding['current_sha256'])
        self.tamper(path)
        self.assertFalse(self.v.v23_binding()['checks']['current_bytes'])

    def test_other_executable_evidence_cannot_expand_source_authority(self):
        target = self.root / 'evidence/queue/v23/undeclared.py'
        target.write_text('pass\n')
        self.addCleanup(target.unlink)
        self.assertFalse(self.v.v23_binding()['checks']['bounded_changes'])

    def test_frozen_user_schema_candidates_packets_and_old_receipts_are_preserved(self):
        for path in ('FREEZE_MANIFEST.json', 'coach_v1/pregame_store.py',
                     'config/practical_review_issues.json', 'knowledge_candidates/practical-review-v1.json',
                     'evidence/queue/v21/review-manifest.json', self.v.PARENT_AMENDMENT):
            with self.subTest(path=path):
                target = self.root / path
                original = target.read_bytes()
                try:
                    target.write_bytes(original + b'\n')
                    self.assertEqual(self.v.v23_binding()['status'], 'FAIL')
                finally:
                    target.write_bytes(original)

    def test_prior_receipt_and_archive_tampering_fail(self):
        for path in (self.v.PARENT_RECEIPT, self.v.PARENT_DIRECTORY + '/coach_v1/pc_coach.py'):
            target = self.root / path
            original = target.read_bytes()
            try:
                target.write_bytes(original + b'\n')
                self.assertEqual(self.v.v23_binding()['status'], 'FAIL')
            finally:
                target.write_bytes(original)

    def test_authority_or_user_promotion_fails(self):
        for key, value in (('authority', 'AUTO_VERIFIED'), ('automatic_user_approval', True),
                           ('user_decisions_created', 1), ('prior_completed_verification_rerun', True)):
            original = self.binding[key]
            try:
                self.binding[key] = value
                self.save()
                self.assertEqual(self.v.v23_binding()['status'], 'FAIL', key)
            finally:
                self.binding[key] = original
                self.save()

    def test_receipt_cannot_claim_different_commit_or_failed_ci(self):
        self.binding['reused_ci_runs'][0]['head_sha'] = '0' * 40
        self.save()
        self.assertFalse(self.v.v23_binding()['checks']['trusted_completed_ci'])

    def test_amendment_cannot_expand_source_authority(self):
        self.binding['current_sha256']['coach_v1/knowledge.py'] = self.v.sha('coach_v1/knowledge.py')
        self.save()
        self.assertFalse(self.v.v23_binding()['checks']['exact_current_paths'])

    def test_unknown_new_source_is_rejected(self):
        target = self.root / 'coach_v1/undeclared_v23.py'
        target.write_text('pass\n')
        self.addCleanup(target.unlink)
        self.assertFalse(self.v.v23_binding()['checks']['bounded_changes'])

    def test_changed_protected_hash_cannot_be_resealed(self):
        self.tamper('config/practical_review_issues.json', b'\n')
        self.binding = self.v.prepare_binding()
        self.save()
        self.assertFalse(self.v.v23_binding()['checks']['preserved_bytes'])

    def test_prior_verifier_code_is_unchanged(self):
        self.tamper('scripts/verify_mvp_v21.py')
        self.assertEqual(self.v.v23_binding()['status'], 'FAIL')

    def test_original_github_ci_receipt_cannot_be_rewritten(self):
        self.tamper(self.v.PARENT_DIRECTORY + '/ci-38722880438.json', b'\n')
        self.assertFalse(self.v.v23_binding()['checks']['original_ci_receipts'])

    def test_parent_archive_cannot_gain_untrusted_files(self):
        target = self.root / self.v.PARENT_DIRECTORY / 'invented.json'
        target.write_text('{}')
        self.addCleanup(target.unlink)
        self.assertFalse(self.v.v23_binding()['checks']['bounded_changes'])

    def test_new_data_bytes_are_bound(self):
        path = next(iter(self.binding['data_sha256']))
        self.tamper(path, b'\n')
        self.assertFalse(self.v.v23_binding()['checks']['data_bytes'])


if __name__ == '__main__':
    unittest.main()

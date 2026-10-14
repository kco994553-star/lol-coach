"""Exact source amendment must fail on an unbound edit or lost predecessor."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from scripts import verify_mvp_practical as verifier


class PracticalBindingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        binding=json.loads((verifier.ROOT/'contracts/amendments/2026-10-14-practical-review.json').read_text())
        paths=set(binding['current_sha256'])|{'contracts/amendments/2026-10-14-practical-review.json','evidence/mvp/knowledge-review-version.json','evidence/mvp/knowledge-review-parent.json','evidence/mvp/knowledge-review-parent/coach_v1/knowledge.py',binding['parent_archive'],binding['contract'],'FREEZE_MANIFEST.json','scripts/verify_mvp.py'}
        for path in paths:
            target=self.root/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(verifier.ROOT/path,target)
        self.context=patch.object(verifier,'ROOT',self.root);self.context.start();self.addCleanup(self.context.stop)

    def test_exact_successor_chain_passes(self):
        self.assertEqual(verifier.practical_binding()['status'],'PASS')

    def test_unbound_new_source_edit_fails(self):
        with (self.root/'coach_v1/practical_review.py').open('a') as f:f.write('\n# unbound edit\n')
        result=verifier.practical_binding();self.assertEqual(result['status'],'FAIL');self.assertFalse(result['checks']['current_bytes'])

    def test_missing_original_archive_fails(self):
        (self.root/'evidence/queue/practical-review-20261014/parent/knowledge.py').unlink()
        self.assertEqual(verifier.practical_binding()['status'],'FAIL')

    def test_frozen_edit_fails(self):
        with (self.root/'FREEZE_MANIFEST.json').open('a') as f:f.write('\n')
        result=verifier.practical_binding();self.assertEqual(result['status'],'FAIL');self.assertFalse(result['checks']['frozen_unchanged'])

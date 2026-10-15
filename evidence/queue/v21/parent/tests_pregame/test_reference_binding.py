"""Reference-first source successor stays bound; unrecorded edits must fail."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch


class ReferenceBindingTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('scripts.verify_mvp_reference'),'reference source amendment missing')
        from scripts import verify_mvp_reference
        self.v=verify_mvp_reference
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        b=json.loads((self.v.ROOT/'contracts/amendments/2026-10-14-reference-first.json').read_text())
        prior=json.loads((self.v.ROOT/b['parent_amendment']).read_text())
        paths=set(b['current_sha256'])|set(b['official_source_sha256'])|set(prior['current_sha256'])|{b['parent_amendment'],b['contract'],'contracts/amendments/2026-10-14-reference-first.json','FREEZE_MANIFEST.json'}
        paths|={b['parent_directory']+'/'+p for p in prior['current_sha256']}
        for p in paths:
            dest=self.root/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(self.v.ROOT/p,dest)
        self.context=patch.object(self.v,'ROOT',self.root);self.context.start();self.addCleanup(self.context.stop)

    def test_exact_reference_chain_passes(self):self.assertEqual(self.v.reference_binding()['status'],'PASS')
    def test_unrecorded_ui_change_fails(self):
        with (self.root/'web_r4/review_queue.js').open('a') as f:f.write('\n// unrecorded change\n')
        self.assertEqual(self.v.reference_binding()['status'],'FAIL')
    def test_official_archive_tampering_fails(self):
        p=self.root/'data/official_reference/2026-10-14/Caitlyn-16.20.1.ko_KR.json';p.write_text('{}')
        self.assertEqual(self.v.reference_binding()['status'],'FAIL')
    def test_lost_predecessor_fails(self):
        (self.root/'evidence/queue/reference-first/parent/web_r4/review_queue.js').unlink()
        self.assertEqual(self.v.reference_binding()['status'],'FAIL')

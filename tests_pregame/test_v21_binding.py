"""Exact v2.1 successors never erase predecessor assertions or promote AUTO."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch


class QueueV21BindingTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('scripts.verify_mvp_v21'),'v2.1 successor verifier missing')
        from scripts import verify_mvp_v21
        self.v=verify_mvp_v21
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        # Build an isolated seal from the candidate sources. Missing unfinished
        # browser sources receive explicit synthetic bytes only in this tree.
        for p in self.v.required_paths():
            target=self.root/p;target.parent.mkdir(parents=True,exist_ok=True)
            source=self.v.ROOT/p
            if source.is_file():shutil.copyfile(source,target)
            elif p in self.v.CURRENT_PATHS:target.write_text('# isolated unfinished-source fixture\n')
            else:self.fail('missing predecessor '+p)
        self.context=patch.object(self.v,'ROOT',self.root);self.context.start();self.addCleanup(self.context.stop)
        self.binding=self.v.prepare_binding()
        self.save()

    def save(self):
        target=self.root/self.v.AMENDMENT;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(self.binding))

    def test_exact_v21_chain_and_original_reference_assertions_pass(self):
        result=self.v.v21_binding()
        self.assertEqual(result['status'],'PASS',result)
        historical=self.v.historical_reference_binding()
        self.assertEqual(historical['status'],'PASS')
        self.assertEqual(len(historical['checks']),13)
        self.assertTrue(all(historical['checks'].values()))

    def test_unrecorded_successor_source_change_fails(self):
        with (self.root/'coach_v1/auto_review.py').open('a') as stream:stream.write('\n# tampered\n')
        result=self.v.v21_binding()
        self.assertEqual(result['status'],'FAIL')
        self.assertFalse(result['checks']['current_bytes'])

    def test_extra_path_cannot_expand_authorized_changes(self):
        self.binding['current_sha256']['coach_v1/knowledge.py']=self.v.sha('coach_v1/knowledge.py');self.save()
        result=self.v.v21_binding()
        self.assertEqual(result['status'],'FAIL')
        self.assertFalse(result['checks']['exact_current_paths'])

    def test_lost_reference_predecessor_fails(self):
        (self.root/self.v.PARENT_DIRECTORY/'coach_v1/pregame_server.py').unlink()
        self.assertEqual(self.v.v21_binding()['status'],'FAIL')
        self.assertEqual(self.v.historical_reference_binding()['status'],'FAIL')

    def test_original_frozen_or_candidate_tampering_fails(self):
        for path in ('FREEZE_MANIFEST.json','knowledge_candidates/practical-review-v1.json'):
            original=(self.root/path).read_bytes()
            (self.root/path).write_bytes(original+b'\n')
            self.assertEqual(self.v.v21_binding()['status'],'FAIL')
            (self.root/path).write_bytes(original)

    def test_auto_grade_or_authority_promotion_fails(self):
        for key,value in [('authority','AUTO_VERIFIED'),('automatic_user_approval',True),('auto_verified_to_user_reviewed',True),('user_decisions_created',1),('existing_user_decisions_mutated',True)]:
            original=self.binding[key];self.binding[key]=value;self.save()
            self.assertEqual(self.v.v21_binding()['status'],'FAIL',key)
            self.binding[key]=original

    def test_official_original_source_tampering_fails(self):
        (self.root/'data/official_reference/2026-10-14/Caitlyn-16.20.1.ko_KR.json').write_text('{}')
        self.assertEqual(self.v.v21_binding()['status'],'FAIL')

    def test_historical_verifier_edit_fails(self):
        with (self.root/'scripts/verify_mvp_reference.py').open('a') as stream:stream.write('\n# tamper\n')
        self.assertEqual(self.v.v21_binding()['status'],'FAIL')


if __name__=='__main__':unittest.main()

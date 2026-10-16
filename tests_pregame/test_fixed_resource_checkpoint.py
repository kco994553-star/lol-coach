import unittest
from scripts import recover_resource_checkpoint as r

class FixedCheckpointTests(unittest.TestCase):
    def fixture(self):
        return dict(id=38410710876,head_branch='main',event='workflow_dispatch',path='.github/workflows/pro-reference-collection.yml',run_attempt=1,head_sha='b6cdced0c819424e048ec412de6f7e57c5b1c545'),dict(id=11822391323,name='pro-reference-private-encrypted',expired=False,size_in_bytes=100,workflow_run={'id':38410710876})
    def test_fixed_pair_does_not_select_newest(self):
        run,a=self.fixture();self.assertEqual(r.validate_fixed(run,a)['artifact_id'],11822391323)
    def test_wrong_run_artifact_and_expired_rejected(self):
        run,a=self.fixture()
        for change in [dict(id=11822391324),dict(expired=True),dict(workflow_run={'id':38410710877}),dict(name='other')]:
            with self.assertRaises(ValueError):r.validate_fixed(run,dict(a,**change))
    def test_untrusted_source_attempt_or_branch_rejected(self):
        run,a=self.fixture()
        for change in [dict(run_attempt=2),dict(head_branch='work/new'),dict(head_sha='a'*40),dict(path='other')]:
            with self.assertRaises(ValueError):r.validate_fixed(dict(run,**change),a)

import unittest
import io
from pathlib import Path
import tempfile
import zipfile
from coach_v1.pro_checkpoint import select_checkpoint,COLLECT_STEP,CACHE_NAME,PATH

class ProCheckpointTests(unittest.TestCase):
    def run_record(self,i):return dict(id=i,run_number=i,head_branch='main',event='workflow_dispatch',path=PATH)
    def test_newest_failed_collection_without_checkpoint_blocks_old_cache(self):
        runs=[self.run_record(2),self.run_record(1)]
        artifacts=lambda i:[] if i==2 else [dict(id=10,name=CACHE_NAME,size_in_bytes=128,expired=False)]
        with self.assertRaises(ValueError):select_checkpoint(runs,3,artifacts,lambda i:[dict(steps=[dict(name=COLLECT_STEP,conclusion='failure')])])
    def test_expired_newest_cache_blocks_even_with_older_good_cache(self):
        with self.assertRaises(ValueError):select_checkpoint([self.run_record(2),self.run_record(1)],3,lambda i:[dict(id=i,name=CACHE_NAME,size_in_bytes=128,expired=i==2)],lambda i:[])
    def test_current_run_excluded_and_never_collected_skip_can_restore_older(self):
        result=select_checkpoint([self.run_record(3),self.run_record(2),self.run_record(1)],3,
            lambda i:[] if i==2 else [dict(id=10,name=CACHE_NAME,size_in_bytes=128,expired=False)],
            lambda i:[dict(steps=[dict(name=COLLECT_STEP,conclusion='skipped')])])
        self.assertEqual(result['run_id'],1)
    def test_newest_checkpoint_any_conclusion_accepted_and_empty_history_bootstraps(self):
        r=self.run_record(1);r['conclusion']='cancelled'
        self.assertEqual(select_checkpoint([r],2,lambda i:[dict(id=10,name=CACHE_NAME,size_in_bytes=128,expired=False)],lambda i:[])['status'],'FOUND')
        self.assertEqual(select_checkpoint([],1,lambda i:[],lambda i:[])['status'],'ABSENT')

    def test_rerun_current_attempt_never_bootstraps_or_repeats_lookup(self):
        with self.assertRaises(ValueError):select_checkpoint([],1,lambda i:[],lambda i:[],current_run_attempt=2)

    def test_historical_rerun_never_revives_older_attempt_artifact(self):
        run=self.run_record(1);run['run_attempt']=2
        with self.assertRaises(ValueError):select_checkpoint([run],2,lambda i:[dict(id=10,name=CACHE_NAME,size_in_bytes=128,expired=False)],lambda i:[])

    def test_outer_zip_accepts_only_one_ciphertext_member(self):
        from coach_v1.pro_checkpoint import extract_checkpoint_zip
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w') as z:z.writestr('pro-private.bundle',b'ciphertext'*8)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'download.zip';path.write_bytes(b.getvalue());out=Path(tmp)/'pro-private.bundle'
            extract_checkpoint_zip(path,out)
            self.assertEqual(out.read_bytes(),b'ciphertext'*8)
            self.assertEqual(out.stat().st_mode&0o777,0o600)

    def test_outer_zip_rejects_extra_traversal_and_symlink_members(self):
        from coach_v1.pro_checkpoint import extract_checkpoint_zip
        for name in ('../scripts/private_pro_bundle.py','other.txt','pro-private.bundle'):
            b=io.BytesIO()
            with zipfile.ZipFile(b,'w') as z:
                z.writestr('pro-private.bundle',b'ciphertext'*8)
                info=zipfile.ZipInfo(name);info.external_attr=0o120777<<16;z.writestr(info,b'bad')
            with tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp)/'download.zip';path.write_bytes(b.getvalue());out=Path(tmp)/'pro-private.bundle'
                with self.assertRaises(ValueError):extract_checkpoint_zip(path,out)
                self.assertFalse(out.exists())

    def test_outer_zip_rejects_a_sole_symlink(self):
        from coach_v1.pro_checkpoint import extract_checkpoint_zip
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w') as z:
            info=zipfile.ZipInfo('pro-private.bundle');info.external_attr=0o120777<<16;z.writestr(info,b'ciphertext'*8)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'download.zip';path.write_bytes(b.getvalue())
            with self.assertRaises(ValueError):extract_checkpoint_zip(path,Path(tmp)/'pro-private.bundle')

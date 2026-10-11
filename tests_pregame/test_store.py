import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest

from coach_v1.state import digest
from coach_v1.storage import ServiceError
from tests_pregame.test_contract import golden


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('coach_v1.pregame_store'),'immutable pregame store missing')
        from coach_v1.pregame_store import PregameStore
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'pregame.sqlite';self.cls=PregameStore;self.s=self.cls(self.path)

    def save(self,value=None,key='create-key'):
        return self.s.save(golden() if value is None else value,None,0,key)

    def test_exact_retry_after_restart_and_changed_payload_conflict(self):
        first=self.save();reopen=self.cls(self.path)
        self.assertEqual(reopen.save(golden(),None,0,'create-key'),first)
        d=golden();d['title']='changed'
        with self.assertRaises(ServiceError):reopen.save(d,None,0,'create-key')
        self.assertEqual(len(reopen.list_inputs()),1)

    def test_revision_history_and_cas(self):
        first=self.save();d=golden('TOP')
        second=self.s.save(d,first['session_id'],1,'edit-key')
        self.assertEqual(second['revision'],2);self.assertEqual(second['parent_id'],first['id'])
        self.assertEqual(self.s.history(first['session_id']),[first,second])
        with self.assertRaises(ServiceError):self.s.save(d,first['session_id'],1,'old-key')

    def plan(self,record):
        from coach_v1.pregame_evaluator import evaluate_gameplan
        return evaluate_gameplan(record['input'],[])

    def test_plan_retry_saved_reopen_and_input_expiry(self):
        first=self.save();p=self.s.save_plan(first['session_id'],1,self.plan(first),'plan-key')
        self.assertEqual(self.s.save_plan(first['session_id'],1,self.plan(first),'plan-key'),p)
        self.assertEqual(self.cls(self.path).get_plan(p['id'],digest([]))['validity'],'CURRENT')
        self.s.save(golden('TOP'),first['session_id'],1,'edit')
        old=self.s.get_plan(p['id'],digest([]))
        self.assertEqual(old['validity'],'EXPIRED');self.assertIn('INPUT_REVISION_CHANGED',old['expiry_reasons'])
        self.assertEqual(old['input'],first['input'])

    def test_knowledge_change_expires_plan(self):
        first=self.save();p=self.s.save_plan(first['session_id'],1,self.plan(first),'plan')
        self.assertIn('KNOWLEDGE_CHANGED',self.s.get_plan(p['id'],digest(['changed']))['expiry_reasons'])

    def test_export_restore_no_overwrite_and_exact_history(self):
        first=self.save();p=self.s.save_plan(first['session_id'],1,self.plan(first),'plan')
        archive=self.s.export_data();other=self.cls(Path(self.tmp.name)/'restored.sqlite')
        other.import_data(archive)
        self.assertEqual(other.export_data(),archive)
        self.assertEqual(other.save(golden(),None,0,'create-key'),first)
        with self.assertRaises(ServiceError):other.import_data(archive)
        bad=copy.deepcopy(archive);bad['inputs'][0]['input']['title']='tampered'
        with self.assertRaises(ServiceError):self.cls(Path(self.tmp.name)/'bad.sqlite').import_data(bad)

    def test_wrong_source_hash_and_corrupt_store_fail_closed(self):
        first=self.save()
        import sqlite3,json
        bad=copy.deepcopy(first);bad['input']['title']='tampered'
        with sqlite3.connect(self.path) as db:
            db.execute('UPDATE inputs SET payload=?',(json.dumps(bad),))
        with self.assertRaises(ServiceError):self.cls(self.path)

    def test_restore_rejects_changed_retry_identity_even_with_new_archive_hash(self):
        self.save();archive=self.s.export_data();archive['operations'][0]['fingerprint']='0'*64
        archive['sha256']=digest({k:v for k,v in archive.items() if k!='sha256'})
        target=self.cls(Path(self.tmp.name)/'changed.sqlite')
        with self.assertRaises(ServiceError):target.import_data(archive)
        self.assertEqual(target.list_inputs(),[])

    def test_restore_rejects_malformed_nested_plan_even_with_consistent_archive_hash(self):
        from coach_v1.state import canonical
        first=self.save();self.s.save_plan(first['session_id'],1,self.plan(first),'plan')
        for mutation in [lambda r:r.update(common=None),lambda r:r['common'].update(map=[]),
                         lambda r:r['personal']['role'].update(reasons='invalid'),
                         lambda r:r.update(evaluations=[None])]:
            archive=copy.deepcopy(self.s.export_data());mutation(archive['plans'][0])
            for op in archive['operations']:
                if op['operation'].startswith('plan:'):op['response']=canonical(archive['plans'][0])
            archive['sha256']=digest({k:v for k,v in archive.items() if k!='sha256'})
            target=self.cls(Path(self.tmp.name)/('malformed-'+str(len(archive['plans'][0].get('evaluations',[])))+'-'+__import__('uuid').uuid4().hex+'.sqlite'))
            with self.assertRaises(ServiceError):target.import_data(archive)
            self.assertEqual(target.list_inputs(),[])


if __name__=='__main__':unittest.main()

import copy
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from coach_v1.storage import Store, ServiceError


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)/'db.sqlite'
        self.store = Store(self.path)
        self.session = self.store.create_session('합성 입력', 'SYNTHETIC-1')
        self.sid = self.session['id']
        self.case = json.loads((Path(__file__).resolve().parents[1]/'examples/r3/compare-wait-retreat.json').read_text())
        self.case['snapshot_request']['session_id'] = self.sid
        self.case['snapshot_request']['patch'] = 'SYNTHETIC-1'
        for o in self.case['observations']:
            o['session_id'] = self.sid; o['patch'] = 'SYNTHETIC-1'
        for a in self.case['assessments']:
            a['patch'] = 'SYNTHETIC-1'

    def saved(self):
        return self.store.put_case(self.sid, self.case, 0, 'save-1')

    def job(self):
        self.saved()
        return self.store.submit_review(self.sid, 1, 'review-1')['id']

    def error(self, code, fn):
        with self.assertRaises(ServiceError) as e:
            fn()
        self.assertEqual(e.exception.code, code)

    def test_idempotency_and_stale_revision(self):
        first = self.saved()
        self.assertEqual(first, self.saved())
        changed = copy.deepcopy(self.case); changed['objective'] += '!'
        self.error('IDEMPOTENCY_CONFLICT', lambda: self.store.put_case(self.sid, changed, 0, 'save-1'))
        self.error('REVISION_CONFLICT', lambda: self.store.put_case(self.sid, changed, 0, 'save-2'))
        self.assertEqual(self.store.get_session(self.sid)['revision'], 1)

    def test_jobs_persist_results_and_stale(self):
        jid = self.job()
        replay = self.store.submit_review(self.sid, 1, 'review-1')
        self.assertEqual(jid, replay['id'])
        self.assertEqual(self.store.run_job(jid)['status'], 'COMPLETED')
        reopened = Store(self.path)
        self.assertFalse(reopened.get_review(jid)['stale'])
        reopened.put_case(self.sid, self.case, 1, 'save-2')
        self.assertTrue(reopened.get_review(jid)['stale'])
        self.assertEqual(reopened.submit_review(self.sid, 1, 'review-1'), replay)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM cases').fetchone()[0], 2)

    def test_restart_recovers_interrupted_only(self):
        jid = self.job()
        queued = self.store.submit_review(self.sid, 1, 'review-2')['id']
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE jobs SET status='RUNNING' WHERE id=?", (jid,))
        reopened = Store(self.path)
        self.assertEqual(reopened.get_job(jid)['error'], 'INTERRUPTED')
        self.assertEqual(reopened.queued_job_ids(), [queued])
        self.assertEqual(reopened.run_job(queued)['status'], 'COMPLETED')

    def test_cancel_during_compute_never_publishes(self):
        jid = self.job()
        def compute(*args, **kwargs):
            self.store.cancel_job(jid)
            return {'result': 'must never persist'}
        with patch('coach_v1.storage.run_review', side_effect=compute):
            self.assertEqual(self.store.run_job(jid)['status'], 'CANCELLED')
        self.error('RESULT_UNAVAILABLE', lambda: self.store.get_review(jid))
        with sqlite3.connect(self.path) as db:
            self.assertIsNone(db.execute('SELECT result FROM jobs').fetchone()[0])

    def test_delete_during_compute_never_resurrects(self):
        jid = self.job()
        def compute(*args, **kwargs):
            self.store.delete_session(self.sid)
            return {'result': 'must never persist'}
        with patch('coach_v1.storage.run_review', side_effect=compute):
            self.assertEqual(self.store.run_job(jid)['status'], 'DELETED')
        self.error('JOB_NOT_FOUND', lambda: self.store.get_job(jid))
        self.assertEqual(self.store.delete_session(self.sid)['status'], 'DELETED')
        with sqlite3.connect(self.path) as db:
            for table in ('sessions', 'cases', 'jobs', 'idempotency'):
                self.assertEqual(db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT * FROM tombstones').fetchall(), [(self.sid,)])

    def test_schema_refusal_preserves_data(self):
        self.saved()
        with sqlite3.connect(self.path) as db:
            db.execute('PRAGMA user_version=999')
        self.error('INCOMPATIBLE_SCHEMA', lambda: Store(self.path))
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM cases').fetchone()[0], 1)
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 999)

    def test_same_version_wrong_shape_is_refused(self):
        with sqlite3.connect(self.path) as db:
            db.execute('ALTER TABLE sessions ADD COLUMN incompatible TEXT')
        self.error('INCOMPATIBLE_SCHEMA', lambda: Store(self.path))

    def test_queued_cancellation_is_not_executed(self):
        jid = self.job()
        self.store.cancel_job(jid)
        with patch('coach_v1.storage.run_review') as compute:
            self.assertEqual(self.store.run_job(jid)['status'], 'CANCELLED')
            compute.assert_not_called()

    def test_mode_patch_and_validation_failure_rollback(self):
        self.error('SYNTHETIC_TEST_ONLY', lambda: self.store.create_session('x', 'p', 'POST_GAME'))
        for mutate in (lambda c: c.update(mode='POST_GAME'), lambda c: c['snapshot_request'].update(patch='other'), lambda c: c['observations'][0].update(patch='other')):
            case = copy.deepcopy(self.case); mutate(case)
            with self.assertRaises(ServiceError):
                self.store.put_case(self.sid, case, 0, 'save-1')
            self.assertEqual(self.store.get_session(self.sid)['revision'], 0)
        self.error('INVALID_REVISION', lambda: self.store.put_case(self.sid, self.case, True, 'x'))
        self.error('INVALID_IDEMPOTENCY_KEY', lambda: self.store.put_case(self.sid, self.case, 0, ''))
        self.saved()

    def test_backup_and_restore(self):
        jid = self.job(); self.store.run_job(jid)
        dest = Path(self.tmp.name)/'backup.sqlite'
        self.store.backup(dest)
        self.error('BACKUP_EXISTS', lambda: self.store.backup(dest))
        self.assertEqual(Store(dest).get_review(jid), self.store.get_review(jid))

    def test_failure_has_no_raw_payload(self):
        jid = self.job()
        with patch('coach_v1.storage.run_review', side_effect=ValueError('private data')):
            self.assertEqual(self.store.run_job(jid)['error'], 'REVIEW_FAILED')
        self.assertNotIn('private data', str(self.store.get_job(jid)))


if __name__ == '__main__':
    unittest.main()

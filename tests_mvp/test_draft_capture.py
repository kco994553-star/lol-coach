"""Native SQLite manual-input tests; synthetic operator fixtures, no game gold."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import copy
from datetime import datetime, timezone
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sqlite3
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import uuid

from coach_v1.storage import Store, ServiceError
from tests_r3.helpers import fixture

try:
    draft = importlib.import_module('coach_v1.draft')
except ModuleNotFoundError as missing:
    if missing.name != 'coach_v1.draft':
        raise
    draft = None


def capture():
    return dict(title='수동 드래프트 한글·日本語·😀', phase=None, patch=None,
        observed_at=None,
        visible_picks=[dict(side='ALLY', slot=1, champion=None),
                       dict(side='ENEMY', slot=5, champion='Ahri')],
        visible_bans=[], role_assignments=[dict(side='ALLY', slot=1,
            role=None, uncertainty='아직 역할 미확인 👀')],
        source=dict(author='직접 입력 작성자', perspective='UNKNOWN',
                    description='합성 저장 테스트 입력; 실경기 검증 아님'))


class DraftCaptureTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(draft, 'Manual capture API is absent: coach_v1.draft.DraftStore')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'main.sqlite'
        self.store = draft.DraftStore(self.path)
        self.budget = 1_000_000

    def state(self, path=None):
        with closing(sqlite3.connect(path or self.path)) as db:
            names = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
            return (db.execute('PRAGMA user_version').fetchone()[0],
                    db.execute('SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name').fetchall(),
                    {name: db.execute('SELECT * FROM '+name+' ORDER BY rowid').fetchall() for name in names})

    def create(self, value=None, budget=None):
        return self.store.create_capture(capture() if value is None else value,
                                         self.budget if budget is None else budget)

    def rejected(self, status, code, operation):
        before = self.state()
        with self.assertRaises(ServiceError) as caught:
            operation()
        self.assertEqual((caught.exception.status, caught.exception.code), (status, code))
        self.assertEqual(self.state(), before)

    def legacy(self, path):
        old = Store(path)
        sid = old.create_session('보존할 TEST 제목 😀', 'SYNTHETIC-1')['id']
        case = fixture()
        case['snapshot_request']['session_id'] = sid
        for observation in case['observations']:
            observation['session_id'] = sid
        old.put_case(sid, case, 0, 'save-first')
        jid = old.submit_review(sid, 1, 'review-first')['id']
        removed = old.create_session('삭제한 합성 세션', 'SYNTHETIC-1')['id']
        old.delete_session(removed)
        return old, sid, jid

    def corrupt(self, sql, parameters=()):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute(sql, parameters)
            db.commit()

    def validate(self):
        with closing(sqlite3.connect(self.path)) as db:
            before = self.state()
            draft.validate_schema(db)
            draft.validate_draft_content(db)
            self.assertIsNone(db.row_factory)
            self.assertFalse(db.in_transaction)
        self.assertEqual(self.state(), before)

    def test_new_empty_v2_has_no_fake_prior_data_backup(self):
        self.assertIsNone(self.store.migration_backup)
        self.assertEqual(self.state()[0], 2)
        self.assertEqual(set(self.state()[2]), {'sessions', 'cases', 'jobs', 'idempotency',
            'tombstones', 'draft_captures', 'draft_snapshots'})
        self.assertEqual(list(self.path.parent.glob('*.pre-draft-v2-*.sqlite')), [])
        self.validate()

    def test_partial_unknown_capture_survives_exact_restart(self):
        entered = capture()
        saved = self.create(entered)
        self.assertEqual(saved['capture'], entered)
        self.assertEqual(saved['schema_version'], 'mvp.manual-draft.v1')
        self.assertRegex(saved['id'], r'^[a-f0-9]{32}$')
        self.assertRegex(saved['session_id'], r'^[a-f0-9]{32}$')
        self.assertEqual(saved['revision'], 1)
        self.assertIsNone(saved['parent_id'])
        restarted = draft.DraftStore(self.path)
        self.assertIsNone(restarted.migration_backup)
        self.assertEqual(restarted.get_capture(saved['session_id'], max_bytes=self.budget), saved)
        self.assertEqual(self.store.list_captures(self.budget), [saved])

    def test_operator_input_hash_and_unknown_provenance_never_promoted(self):
        entered = capture()
        saved = self.create(entered)
        raw = json.dumps(entered, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
        self.assertEqual(saved['input_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(saved['adapter_capability'], {'automatic_collection':'UNAVAILABLE', 'manual_capture':'AVAILABLE'})
        self.assertEqual(saved['validation_state'], 'UNVERIFIED')
        self.assertEqual(saved['gameplan_status'], 'NOT_GENERATED')
        self.assertIs(saved['coaching_enabled'], False)
        self.assertIsNone(saved['capture']['observed_at'])
        self.assertIsNone(saved['capture']['phase'])
        self.assertIsNone(saved['capture']['patch'])
        self.validate()

    def test_declared_observation_time_is_literal_and_not_receive_time(self):
        entered = capture()
        entered['observed_at'] = '2020-02-29T12:34:56.123456+09:00'
        entered['phase'] = '선택 중'
        entered['patch'] = '입력한 patch; 검증 안 됨'
        entered['source']['perspective'] = 'PLAYER'
        before = datetime.now(timezone.utc)
        saved = self.create(entered)
        after = datetime.now(timezone.utc)
        received = datetime.fromisoformat(saved['received_at'])
        self.assertEqual(saved['capture'], entered)
        self.assertNotEqual(saved['received_at'], entered['observed_at'])
        self.assertLessEqual(before, received)
        self.assertLessEqual(received, after)
        self.assertEqual(received.utcoffset().total_seconds(), 0)
        self.assertEqual(saved['validation_state'], 'UNVERIFIED')

    def test_no_inference_for_empty_arrays_or_unknown_champion_role(self):
        entered = capture()
        entered['visible_picks'] = []
        entered['role_assignments'] = []
        saved = self.create(entered)
        self.assertEqual(saved['capture'], entered)
        self.assertEqual(set(saved), {'schema_version', 'id', 'session_id', 'revision',
            'parent_id', 'received_at', 'capture', 'input_sha256', 'adapter_capability',
            'validation_state', 'gameplan_status', 'coaching_enabled'})

    def test_caller_mutation_cannot_change_saved_capture(self):
        entered = capture()
        saved = self.create(entered)
        entered['source']['author'] = 'caller changed'
        entered['visible_picks'][0]['champion'] = 'changed'
        saved['capture']['title'] = 'response mutated'
        current = self.store.get_capture(saved['session_id'], max_bytes=self.budget)
        self.assertEqual(current['capture'], capture())

    def test_immutable_parent_history_and_exact_old_record(self):
        first = self.create()
        changed = capture(); changed['title'] = '현재 두 번째 입력'; changed['visible_picks'][0]['champion'] = 'Ashe'
        second = self.store.put_capture(first['session_id'], changed, 1, self.budget)
        third = self.store.put_capture(first['session_id'], capture(), 2, self.budget)
        self.assertEqual((second['revision'],second['parent_id']), (2,first['id']))
        self.assertEqual((third['revision'],third['parent_id']), (3,second['id']))
        self.assertEqual(self.store.get_capture(first['session_id'], revision=1, max_bytes=self.budget), first)
        self.assertEqual(self.store.get_capture(first['session_id'], max_bytes=self.budget), third)
        self.assertEqual(self.store.capture_history(first['session_id'], self.budget),
            {'session_id':first['session_id'], 'current_revision':3, 'revision_count':3, 'revisions':[1,2,3]})
        self.validate()

    def test_stale_put_and_delete_are_atomic_conflicts(self):
        first = self.create()
        second = self.store.put_capture(first['session_id'], capture(), 1, self.budget)
        self.rejected(409, 'REVISION_CONFLICT', lambda: self.store.put_capture(first['session_id'], capture(), 1, self.budget))
        self.rejected(409, 'REVISION_CONFLICT', lambda: self.store.delete_capture(first['session_id'], 1, self.budget))
        self.assertEqual(self.store.get_capture(first['session_id'], max_bytes=self.budget), second)

    def test_concurrent_cas_has_one_winner(self):
        saved = self.create()
        def update(title):
            try:
                changed = capture();changed['title'] = title
                return self.store.put_capture(saved['session_id'], changed, 1, self.budget)
            except ServiceError as error:
                return error.code
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(update, ['동시 입력 A', '동시 입력 B']))
        self.assertEqual(sum(isinstance(result, dict) for result in results), 1)
        self.assertEqual(results.count('REVISION_CONFLICT'), 1)
        self.assertEqual(self.store.capture_history(saved['session_id'], self.budget)['revisions'], [1,2])

    def test_deletion_physically_removes_history_without_private_tombstone(self):
        saved = self.create()
        self.store.put_capture(saved['session_id'], capture(), 1, self.budget)
        result = self.store.delete_capture(saved['session_id'], 2, self.budget)
        self.assertEqual(result, {'id':saved['session_id'], 'status':'DELETED', 'deleted_snapshots':2})
        self.assertEqual(self.store.list_captures(self.budget), [])
        self.assertEqual(self.state()[2]['draft_snapshots'], [])
        self.assertEqual(self.state()[2]['tombstones'], [])
        self.rejected(404, 'DRAFT_CAPTURE_NOT_FOUND', lambda:self.store.get_capture(saved['session_id'], max_bytes=self.budget))
        self.rejected(404, 'DRAFT_CAPTURE_NOT_FOUND', lambda:self.store.capture_history(saved['session_id'], self.budget))

    def test_capture_id_cannot_enter_legacy_session_case_or_review(self):
        saved = self.create()
        for operation in (lambda:self.store.get_session(saved['session_id']),
                          lambda:self.store.get_case(saved['session_id']),
                          lambda:self.store.submit_review(saved['session_id'], 0, 'forbidden')):
            self.rejected(404, 'SESSION_NOT_FOUND', operation)
        self.rejected(422, 'SYNTHETIC_TEST_ONLY', lambda:self.store.create_session('불가', 'x', 'PRE_GAME'))

    def test_invalid_input_fields_types_and_utf8_are_rejected_without_write(self):
        bad=[]
        for key,value in [('title',' '),('title','x'*201),('phase',''),('patch',''),
                          ('observed_at','2026-10-05T12:34:00'),('observed_at','2026-02-30T12:34:00Z'),
                          ('observed_at','not-time'),('title','\ud800'),('visible_picks',{}),('visible_bans',[{}]*11),
                          ('role_assignments',False),('source',{'author':'a'})]:
            entered=capture();entered[key]=value;bad.append(entered)
        entered=capture();entered['extra']='unknown field';bad.append(entered)
        entered=capture();del entered['patch'];bad.append(entered)
        for value in bad:
            with self.subTest(value=repr(value)):
                self.rejected(422,'INVALID_DRAFT_CAPTURE',lambda:self.create(value))

    def test_invalid_slots_duplicates_roles_and_source_rejected(self):
        bad=[]
        for row in [dict(side='OBSERVER',slot=1,champion=None),dict(side='ALLY',slot=True,champion=None),
                    dict(side='ALLY',slot=0,champion=None),dict(side='ALLY',slot=6,champion=None),
                    dict(side='ALLY',slot=1,champion=''),dict(side='ALLY',slot=1,champion='x'*101),
                    dict(side='ALLY',slot=1,champion=None,extra='x')]:
            entered=capture();entered['visible_picks']=[row];bad.append(entered)
        entered=capture();entered['visible_bans']=[dict(side='ALLY',slot=1,champion=None)]*2;bad.append(entered)
        for field,value in [('role','CARRY'),('uncertainty',''),('uncertainty','x'*2001),('slot',False)]:
            entered=capture();entered['role_assignments'][0][field]=value;bad.append(entered)
        entered=capture();entered['role_assignments']*=2;bad.append(entered)
        for field,value in [('author',''),('author','x'*201),('perspective','OBSERVER'),('description',''),('description','x'*2001)]:
            entered=capture();entered['source'][field]=value;bad.append(entered)
        for value in bad:
            with self.subTest(value=repr(value)):
                self.rejected(422,'INVALID_DRAFT_CAPTURE',lambda:self.create(value))

    def test_maximum_typed_slots_and_supported_nullable_roles_save(self):
        entered=capture()
        entered['visible_picks']=[dict(side=side,slot=slot,champion=None) for side in ('ALLY','ENEMY') for slot in range(1,6)]
        entered['visible_bans']=copy.deepcopy(entered['visible_picks'])
        entered['role_assignments']=[dict(side='ALLY',slot=slot,role=role,uncertainty='직접 입력; 미검증') for slot,role in enumerate(('TOP','JUNGLE','MID','BOTTOM','SUPPORT'),1)]
        self.assertEqual(self.create(entered)['capture'], entered)

    def test_invalid_budget_id_and_revision_fail_without_write(self):
        saved=self.create()
        for value in (True,0,-1,1.5,None):
            self.rejected(422,'INVALID_DRAFT_LIMIT',lambda:self.store.list_captures(value))
        for value in ('wrong',None,3,'a'*33):
            self.rejected(422,'INVALID_DRAFT_ID',lambda:self.store.get_capture(value,max_bytes=self.budget))
        for value in (True,0,-1,1.2,None,9223372036854775808):
            self.rejected(422,'INVALID_DRAFT_REVISION',lambda:self.store.put_capture(saved['session_id'],capture(),value,self.budget))
        self.rejected(404,'DRAFT_CAPTURE_NOT_FOUND',lambda:self.store.get_capture('a'*32,max_bytes=self.budget))
        self.rejected(404,'DRAFT_CAPTURE_NOT_FOUND',lambda:self.store.get_capture(saved['session_id'],revision=2,max_bytes=self.budget))

    def test_response_budget_rolls_back_create_update_delete(self):
        self.rejected(413,'DRAFT_CAPTURE_TOO_LARGE',lambda:self.create(budget=1))
        saved=self.create()
        self.rejected(413,'DRAFT_CAPTURE_TOO_LARGE',lambda:self.store.put_capture(saved['session_id'],capture(),1,1))
        self.rejected(413,'DRAFT_CAPTURE_TOO_LARGE',lambda:self.store.delete_capture(saved['session_id'],1,1))
        for operation in (lambda:self.store.list_captures(1),lambda:self.store.get_capture(saved['session_id'],max_bytes=1),lambda:self.store.capture_history(saved['session_id'],1)):
            self.rejected(413,'DRAFT_CAPTURE_TOO_LARGE',operation)

    def test_native_foreign_keys_reject_cross_capture_parent_and_cascade(self):
        first=self.create();other=self.create()
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('PRAGMA foreign_keys=ON')
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute('INSERT INTO draft_snapshots VALUES (?,?,?,?,?)',('f'*32,first['session_id'],2,other['id'],'{}'))
            db.rollback()
        self.store.delete_capture(first['session_id'],1,self.budget)
        self.assertEqual(self.store.get_capture(other['session_id'],max_bytes=self.budget),other)
        self.validate()

    def test_exact_schema_rejects_extra_object_without_rewrite(self):
        self.corrupt('CREATE INDEX unknown_index ON draft_captures(title)')
        self.rejected(409,'INCOMPATIBLE_DRAFT_SCHEMA',lambda:draft.DraftStore(self.path))

    def test_exact_schema_rejects_missing_foreign_key(self):
        self.corrupt('DROP TABLE draft_snapshots')
        self.corrupt('CREATE TABLE draft_snapshots (id TEXT PRIMARY KEY,session_id TEXT,revision INTEGER,parent_id TEXT,payload TEXT)')
        self.rejected(409,'INCOMPATIBLE_DRAFT_SCHEMA',lambda:draft.DraftStore(self.path))

    def test_corrupt_payload_identity_hash_timestamp_and_verification_refused(self):
        saved=self.create()
        with closing(sqlite3.connect(self.path)) as db:
            raw=db.execute('SELECT payload FROM draft_snapshots').fetchone()[0]
        variants=[]
        for key,value in [('input_sha256','0'*64),('session_id','f'*32),('revision',True),
                          ('parent_id','f'*32),('received_at','2026-10-05T12:34'),
                          ('validation_state','VERIFIED_DIRECT'),('coaching_enabled',True),
                          ('adapter_capability',{'manual_capture':'AVAILABLE','automatic_collection':'AVAILABLE'})]:
            value_record=json.loads(raw);value_record[key]=value;variants.append(json.dumps(value_record,ensure_ascii=False,sort_keys=True,separators=(',',':')))
        variants += ['{}',raw.replace('"schema_version":','"id":"duplicate", "schema_version":',1)]
        for malformed in variants:
            with self.subTest(malformed=malformed):
                self.corrupt('UPDATE draft_snapshots SET payload=?',(malformed,))
                self.rejected(409,'INVALID_STORED_DRAFT',lambda:draft.DraftStore(self.path))
                self.rejected(409,'INVALID_STORED_DRAFT',lambda:self.store.get_capture(saved['session_id'],max_bytes=self.budget))
                self.corrupt('UPDATE draft_snapshots SET payload=?',(raw,))

    def test_corrupt_parent_chain_head_title_and_legacy_collision_refused(self):
        first=self.create();second=self.store.put_capture(first['session_id'],capture(),1,self.budget)
        for sql,args in [('UPDATE draft_captures SET revision=3',()),('UPDATE draft_captures SET title=?',('forged',)),
                         ('UPDATE draft_snapshots SET parent_id=NULL WHERE revision=2',())]:
            other=Path(self.temp.name)/('bad-'+uuid.uuid4().hex+'.sqlite');shutil.copyfile(self.path,other)
            with closing(sqlite3.connect(other)) as db:db.execute(sql,args);db.commit()
            with self.assertRaises(ServiceError) as caught:draft.DraftStore(other)
            self.assertEqual(caught.exception.code,'INVALID_STORED_DRAFT')
        self.corrupt('INSERT INTO sessions VALUES (?,?,?,?,?,?)',(first['session_id'],'bad collision','x','TEST',0,'ACTIVE'))
        self.rejected(409,'INVALID_STORED_DRAFT',lambda:draft.DraftStore(self.path))

    @unittest.skipUnless(sys.platform!='win32', 'POSIX capped hostile-input characterization')
    def test_hostile_huge_head_is_refused_without_unbounded_allocation(self):
        self.create()
        self.corrupt('UPDATE draft_captures SET revision=9223372036854775807')
        # A cap confines the deliberately hostile pre-repair allocation to a
        # child process. No mock replaces the real SQLite/parser/validator.
        script = '''
import resource,sys
resource.setrlimit(resource.RLIMIT_AS,(256_000_000,256_000_000))
from coach_v1.draft import DraftStore
from coach_v1.storage import ServiceError
try:
    DraftStore(sys.argv[1])
except ServiceError as error:
    print(error.code)
    sys.exit(0 if (error.status,error.code)==(409,'INVALID_STORED_DRAFT') else 2)
except Exception as error:
    print(type(error).__name__)
    sys.exit(3)
sys.exit(4)
'''
        before=self.state()
        result=subprocess.run([sys.executable,'-c',script,str(self.path)],
                              capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(result.stdout.strip(),'INVALID_STORED_DRAFT')
        self.assertEqual(self.state(),before)

    def test_v1_migration_preserves_exact_old_rows_and_readable_private_snapshot(self):
        other=Path(self.temp.name)/'legacy.sqlite';old,sid,jid=self.legacy(other);before=self.state(other)
        migrated=draft.DraftStore(other)
        self.assertEqual(self.state(other)[2].keys(),before[2].keys()|{'draft_captures','draft_snapshots'})
        for table,rows in before[2].items():self.assertEqual(self.state(other)[2][table],rows)
        metadata=migrated.migration_backup;self.assertEqual(set(metadata),{'path','schema_version','size','sha256'})
        snapshot=Path(metadata['path']);self.assertEqual(metadata['schema_version'],1)
        self.assertEqual(metadata['size'],snapshot.stat().st_size)
        self.assertEqual(metadata['sha256'],hashlib.sha256(snapshot.read_bytes()).hexdigest())
        self.assertEqual(stat.S_IMODE(snapshot.stat().st_mode),0o600)
        self.assertEqual(self.state(snapshot),before)
        recovered=Store(snapshot);self.assertEqual(recovered.get_case(sid),old.get_case(sid))
        self.assertEqual(recovered.get_job(jid)['status'],'QUEUED')

    def test_migration_backup_precedes_interrupted_job_recovery(self):
        other=Path(self.temp.name)/'running.sqlite';old,sid,jid=self.legacy(other)
        with closing(sqlite3.connect(other)) as db:db.execute("UPDATE jobs SET status='RUNNING' WHERE id=?",(jid,));db.commit()
        migrated=draft.DraftStore(other)
        with closing(sqlite3.connect(migrated.migration_backup['path'])) as db:self.assertEqual(db.execute('SELECT status FROM jobs WHERE id=?',(jid,)).fetchone()[0],'RUNNING')
        self.assertEqual(migrated.get_job(jid)['status'],'FAILED')
        self.assertEqual(migrated.get_job(jid)['error'],'INTERRUPTED')

    def test_copy_failure_keeps_exact_v1_and_cleans_unpublished_snapshot(self):
        other=Path(self.temp.name)/'copy-failure.sqlite';self.legacy(other);before=self.state(other)
        with patch('coach_v1.backup._copy_database',side_effect=RuntimeError('injected copy failure')):
            with self.assertRaises(ServiceError) as caught:draft.DraftStore(other)
        self.assertEqual((caught.exception.status,caught.exception.code),(503,'MIGRATION_BACKUP_FAILED'))
        self.assertEqual(self.state(other),before)
        self.assertEqual(list(other.parent.glob(other.name+'.migration-*')),[])
        self.assertEqual(list(other.parent.glob(other.name+'.pre-draft-v2-*')),[])

    def test_ddl_failure_rolls_back_exact_v1_and_retains_recovery_snapshot(self):
        other=Path(self.temp.name)/'rollback.sqlite';self.legacy(other);before=self.state(other)
        with patch('coach_v1.draft.validate_draft_content',side_effect=ServiceError(409,'INJECTED_DDL_FAILURE')):
            with self.assertRaises(ServiceError):draft.DraftStore(other)
        self.assertEqual(self.state(other),before)
        snapshots=list(other.parent.glob(other.name+'.pre-draft-v2-*.sqlite'))
        self.assertEqual(len(snapshots),1)
        self.assertEqual(self.state(snapshots[0]),before)

    def test_snapshot_collision_never_overwrites_existing_bytes(self):
        other=Path(self.temp.name)/'collision.sqlite';self.legacy(other);before=self.state(other)
        nonce=uuid.UUID('35d1366c-91ad-40bc-809c-b82b40df070a')
        target=other.with_name(other.name+'.pre-draft-v2-'+nonce.hex+'.sqlite');target.write_bytes(b'untouched recovery file')
        with patch('coach_v1.draft.uuid.uuid4',return_value=nonce):
            with self.assertRaises(ServiceError) as caught:draft.DraftStore(other)
        self.assertEqual(caught.exception.code,'MIGRATION_BACKUP_FAILED')
        self.assertEqual(target.read_bytes(),b'untouched recovery file')
        self.assertEqual(self.state(other),before)

    def test_snapshot_capacity_refuses_before_copy(self):
        other=Path(self.temp.name)/'capacity.sqlite';self.legacy(other);before=self.state(other)
        with patch('coach_v1.backup.MAX_DATABASE_BYTES',1),patch('coach_v1.backup._copy_database') as copying:
            with self.assertRaises(ServiceError) as caught:draft.DraftStore(other)
            self.assertEqual(caught.exception.code,'MIGRATION_BACKUP_FAILED');copying.assert_not_called()
        self.assertEqual(self.state(other),before)

    def test_invalid_legacy_schema_and_content_refuse_before_backup(self):
        for alteration in ("CREATE INDEX unknown ON sessions(title)","UPDATE sessions SET mode='PRE_GAME'"):
            other=Path(self.temp.name)/('legacy-bad-'+uuid.uuid4().hex+'.sqlite');self.legacy(other)
            with closing(sqlite3.connect(other)) as db:db.execute(alteration);db.commit()
            before=self.state(other)
            with self.assertRaises(ServiceError):draft.DraftStore(other)
            self.assertEqual(self.state(other),before)
            self.assertEqual(list(other.parent.glob(other.name+'.pre-draft-v2-*')),[])

    def test_zero_version_nonempty_schema_refused(self):
        self.corrupt('PRAGMA user_version=0')
        self.rejected(409,'INCOMPATIBLE_DRAFT_SCHEMA',lambda:draft.DraftStore(self.path))

    def test_original_legacy_test_pipeline_operates_on_v2(self):
        sid=self.store.create_session('합성 TEST 그대로','SYNTHETIC-1')['id']
        case=fixture();case['snapshot_request']['session_id']=sid
        for observation in case['observations']:observation['session_id']=sid
        self.store.put_case(sid,case,0,'save')
        jid=self.store.submit_review(sid,1,'review')['id']
        self.assertEqual(self.store.run_job(jid)['status'],'COMPLETED')
        self.assertEqual(self.store.get_review(jid)['result']['mode'],'TEST')
        self.assertEqual(self.store.get_review(jid)['result']['evidence_kind'],'SYNTHETIC')
        self.assertEqual(draft.DraftStore(self.path).get_review(jid),self.store.get_review(jid))


if __name__=='__main__':
    unittest.main()

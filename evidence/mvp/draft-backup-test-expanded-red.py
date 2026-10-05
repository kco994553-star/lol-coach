"""Actual dual-SQLite manual draft archives; no game analysis or inference."""
from contextlib import closing
import copy
import hashlib
import json
import os
import sqlite3
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
import uuid
import zipfile

from coach_v1 import backup as recovery
from coach_v1.knowledge import KnowledgeStore
from coach_v1.research import ResearchStore
from coach_v1.storage import Store
from tests_r3.helpers import fixture


# Independent literal fixture from the agreed interface, before backup support.
RAW_DRAFT_SCHEMAS = (
    'CREATE TABLE draft_captures (id TEXT PRIMARY KEY,title TEXT NOT NULL,revision INTEGER NOT NULL)',
    'CREATE TABLE draft_snapshots (id TEXT PRIMARY KEY,session_id TEXT NOT NULL REFERENCES draft_captures(id) ON DELETE CASCADE,revision INTEGER NOT NULL,parent_id TEXT,payload TEXT NOT NULL,UNIQUE(session_id,revision),UNIQUE(session_id,id),FOREIGN KEY(session_id,parent_id) REFERENCES draft_snapshots(session_id,id))',
)


class DraftBackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.main = self.root / 'personal.sqlite'
        self.research_path = Path(str(self.main) + '.research.sqlite')
        self.archive = self.root / 'personal.zip'
        self.destination = self.root / 'restored'
        self.store = Store(self.main)
        self.sid = self.store.create_session('기존 합성 사례', 'SYNTHETIC-1')['id']
        case = fixture()
        case['snapshot_request']['session_id'] = self.sid
        for observation in case['observations']:
            observation['session_id'] = self.sid
        self.store.put_case(self.sid, case, 0, 'stored-input')
        self.jid = self.store.submit_review(self.sid, 1, 'stored-review')['id']
        with sqlite3.connect(self.main) as db:
            db.execute("UPDATE jobs SET status='RUNNING' WHERE id=?", (self.jid,))
        ResearchStore(self.research_path)
        self.cid = 'a' * 32
        self.capture = dict(title='수동 미검증 기록 😀', phase=None, patch=None, observed_at=None,
            visible_picks=[dict(side='ALLY', slot=1, champion=None), dict(side='ENEMY', slot=2, champion='사용자 입력 챔피언')],
            visible_bans=[dict(side='ENEMY', slot=1, champion=None)],
            role_assignments=[dict(side='ALLY', slot=1, role=None, uncertainty='역할을 아직 확인하지 못함')],
            source=dict(author='합성 작성자', perspective='UNKNOWN', description='사용자가 기록한 부분 입력이며 실제 경기 검증 아님'))

    def canonical(self, value):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)

    def record(self, cid, revision, capture, parent=None):
        return dict(schema_version='mvp.manual-draft.v1', id=('b' if cid == self.cid else 'd') * 30 + str(revision).zfill(2),
            session_id=cid, revision=revision, parent_id=parent, received_at='2026-10-05T06:3' + str(revision) + ':00+00:00',
            capture=copy.deepcopy(capture), input_sha256=hashlib.sha256(self.canonical(capture).encode('utf-8')).hexdigest(),
            adapter_capability=dict(automatic_collection='UNAVAILABLE', manual_capture='AVAILABLE'),
            validation_state='UNVERIFIED', gameplan_status='NOT_GENERATED', coaching_enabled=False)

    def populate(self):
        self.make_main_v2()
        self.records = []
        with sqlite3.connect(self.main) as db:
            db.execute('PRAGMA foreign_keys=ON')
            for revision in (1, 2, 3):
                capture = copy.deepcopy(self.capture)
                if revision > 1:
                    capture['title'] += ' 버전 ' + str(revision)
                    capture['role_assignments'][0]['uncertainty'] += ' 수정 ' + str(revision)
                record = self.record(self.cid, revision, capture, self.records[-1]['id'] if self.records else None)
                self.records.append(record)
            db.execute('INSERT INTO draft_captures VALUES (?,?,?)', (self.cid, self.records[-1]['capture']['title'], 3))
            for record in self.records:
                db.execute('INSERT INTO draft_snapshots VALUES (?,?,?,?,?)',
                    (record['id'], self.cid, record['revision'], record['parent_id'], self.canonical(record)))

    def bytes(self):
        return self.main.read_bytes(), self.research_path.read_bytes()

    def rows(self, path):
        with closing(sqlite3.connect(path)) as db:
            return {table: db.execute('SELECT * FROM ' + table + ' ORDER BY rowid').fetchall()
                for (table,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")}

    def rejected(self, code, action):
        originals = self.bytes()
        with self.assertRaises(recovery.BackupError) as caught:
            action()
        self.assertEqual(caught.exception.code, code)
        self.assertEqual(self.bytes(), originals)
        self.assertFalse(self.destination.exists())
        self.assertEqual(list(self.root.glob('.coach-*')), [])

    def raw_archive(self):
        # Build a genuine offline database archive independently so malformed-v2
        # restore tests can run RED before the new backup writer exists.
        members = {recovery.MAIN: self.main.read_bytes(), recovery.RESEARCH: self.research_path.read_bytes()}
        paths = {recovery.MAIN: self.main, recovery.RESEARCH: self.research_path}
        manifest = dict(format='lol-coach-personal-backup', version=1, consistency='dual-sqlite-write-exclusion',
            files={member: dict(schema_version=self.version(paths[member]), size=len(raw), sha256=hashlib.sha256(raw).hexdigest())
                for member, raw in members.items()})
        with zipfile.ZipFile(self.archive, 'x', compression=zipfile.ZIP_STORED) as archive:
            archive.writestr('manifest.json', self.canonical(manifest).encode('utf-8'))
            for member, raw in members.items():
                archive.writestr(member, raw)

    def rewrite(self, *, change=None, metadata=None):
        with zipfile.ZipFile(self.archive) as archive:
            members = {name: archive.read(name) for name in archive.namelist()}
        manifest = json.loads(members[recovery.MANIFEST])
        if change:
            path = self.root / (uuid.uuid4().hex + '.sqlite')
            path.write_bytes(members[recovery.MAIN])
            with sqlite3.connect(path) as db:
                db.execute('PRAGMA foreign_keys=OFF')
                change(db)
            members[recovery.MAIN] = path.read_bytes()
            manifest['files'][recovery.MAIN].update(size=len(members[recovery.MAIN]), sha256=hashlib.sha256(members[recovery.MAIN]).hexdigest())
        if metadata:
            metadata(manifest)
        members[recovery.MANIFEST] = self.canonical(manifest).encode('utf-8')
        target = self.root / (uuid.uuid4().hex + '.zip')
        with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_STORED) as archive:
            for member, raw in members.items():
                archive.writestr(member, raw)
        return target

    def mutate_payload(self, db, change, *, rehash=False):
        row = db.execute('SELECT id,payload FROM draft_snapshots ORDER BY rowid LIMIT 1').fetchone()
        record = json.loads(row[1])
        change(record)
        if rehash:
            record['input_sha256'] = hashlib.sha256(self.canonical(record['capture']).encode('utf-8')).hexdigest()
        db.execute('UPDATE draft_snapshots SET payload=? WHERE id=?', (self.canonical(record), row[0]))

    def make_main_v2(self):
        with sqlite3.connect(self.main) as db:
            for sql in RAW_DRAFT_SCHEMAS:
                db.execute(sql)
            db.execute('PRAGMA user_version=2')

    def version(self, path):
        with closing(sqlite3.connect(path)) as db:
            return db.execute('PRAGMA user_version').fetchone()[0]

    def test_actual_empty_main_v2_roundtrip_keeps_two_database_format1(self):
        self.make_main_v2()
        original = self.main.read_bytes(), self.research_path.read_bytes()
        try:
            result = recovery.backup(self.main, self.archive)
        except recovery.BackupError as error:
            self.fail('A genuine exact main-v2 database must back up; got ' + error.code)
        self.assertEqual(result['version'], 1)
        self.assertEqual(result['files'][recovery.MAIN]['schema_version'], 2)
        self.assertEqual(result['files'][recovery.RESEARCH]['schema_version'], 1)
        recovery.restore(self.archive, self.destination)
        self.assertEqual(self.version(self.destination / recovery.MAIN), 2)
        self.assertEqual(sorted(path.name for path in self.destination.iterdir()), sorted([recovery.MAIN, recovery.RESEARCH]))
        self.assertEqual((self.main.read_bytes(), self.research_path.read_bytes()), original)

    def test_main_v2_claim_without_physical_draft_tables_never_publishes(self):
        with sqlite3.connect(self.main) as db:
            db.execute('PRAGMA user_version=2')
        original = self.main.read_bytes(), self.research_path.read_bytes()
        with self.assertRaises(recovery.BackupError) as caught:
            recovery.backup(self.main, self.archive)
        self.assertEqual(caught.exception.code, 'INCOMPATIBLE_SCHEMA')
        self.assertFalse(self.archive.exists())
        self.assertEqual((self.main.read_bytes(), self.research_path.read_bytes()), original)

    def test_v2_history_nulls_unicode_and_legacy_running_job_roundtrip_for_both_research_versions(self):
        self.populate()
        for version in (1, 2):
            with self.subTest(research_version=version):
                if version == 2:
                    KnowledgeStore(self.research_path)
                originals, expected = self.bytes(), self.rows(self.main)
                archive, destination = self.root / ('r' + str(version) + '.zip'), self.root / ('r' + str(version))
                result = recovery.backup(self.main, archive)
                self.assertEqual(result['version'], 1)
                self.assertEqual(result['files'][recovery.MAIN]['schema_version'], 2)
                self.assertEqual(result['files'][recovery.RESEARCH]['schema_version'], version)
                recovery.restore(archive, destination)
                actual = self.rows(destination / recovery.MAIN)
                self.assertEqual(actual, expected)
                self.assertEqual(self.rows(destination / recovery.RESEARCH), self.rows(self.research_path))
                self.assertEqual([json.loads(row[4]) for row in actual['draft_snapshots']], self.records)
                first = json.loads(actual['draft_snapshots'][0][4])
                self.assertIsNone(first['capture']['patch'])
                self.assertIsNone(first['capture']['phase'])
                self.assertIsNone(first['capture']['observed_at'])
                self.assertIsNone(first['capture']['visible_picks'][0]['champion'])
                self.assertIsNone(first['capture']['role_assignments'][0]['role'])
                self.assertEqual(first['capture']['source']['perspective'], 'UNKNOWN')
                self.assertEqual(first['validation_state'], 'UNVERIFIED')
                self.assertEqual(first['gameplan_status'], 'NOT_GENERATED')
                self.assertFalse(first['coaching_enabled'])
                self.assertEqual(actual['jobs'][0][4], 'RUNNING')
                self.assertEqual(self.bytes(), originals)
                self.assertEqual(sorted(path.name for path in destination.iterdir()), sorted([recovery.MAIN, recovery.RESEARCH]))
                if os.name != 'nt':
                    self.assertEqual(stat.S_IMODE(archive.stat().st_mode), 0o600)

    def test_backup_restore_do_not_construct_stores_recover_jobs_or_run_engine(self):
        from coach_v1.draft import DraftStore
        self.populate()
        originals, rows = self.bytes(), self.rows(self.main)
        with patch.object(Store, '__init__', side_effect=AssertionError('legacy startup forbidden')), \
             patch.object(Store, 'run_job', side_effect=AssertionError('engine execution forbidden')), \
             patch.object(DraftStore, '__init__', side_effect=AssertionError('draft startup forbidden')), \
             patch.object(ResearchStore, '__init__', side_effect=AssertionError('research startup forbidden')), \
             patch.object(KnowledgeStore, '__init__', side_effect=AssertionError('knowledge startup forbidden')):
            recovery.backup(self.main, self.archive)
            recovery.restore(self.archive, self.destination)
        self.assertEqual(self.bytes(), originals)
        self.assertEqual(self.rows(self.destination / recovery.MAIN), rows)
        self.assertEqual(self.rows(self.destination / recovery.MAIN)['jobs'][0][4], 'RUNNING')

    def test_valid_v1_archive_stays_v1_without_implicit_draft_migration(self):
        original, rows = self.bytes(), self.rows(self.main)
        result = recovery.backup(self.main, self.archive)
        self.assertEqual(result['files'][recovery.MAIN]['schema_version'], 1)
        recovery.restore(self.archive, self.destination)
        self.assertEqual(self.version(self.destination / recovery.MAIN), 1)
        self.assertEqual(self.rows(self.destination / recovery.MAIN), rows)
        self.assertNotIn('draft_captures', rows)
        self.assertEqual(self.bytes(), original)

    def test_rehashed_v2_schema_objects_and_removed_parent_or_session_fk_are_rejected(self):
        self.populate()
        self.raw_archive()
        def remove(db, fragment):
            sql = db.execute("SELECT sql FROM sqlite_master WHERE name='draft_snapshots'").fetchone()[0]
            self.assertIn(fragment, sql)
            db.execute('PRAGMA writable_schema=ON')
            db.execute("UPDATE sqlite_master SET sql=? WHERE name='draft_snapshots'", (sql.replace(fragment, ''),))
        changes = [lambda db: db.execute('ALTER TABLE draft_captures ADD COLUMN unexpected TEXT'),
            lambda db: db.execute('CREATE TRIGGER unexpected AFTER INSERT ON draft_snapshots BEGIN SELECT 1; END'),
            lambda db: remove(db, ',FOREIGN KEY(session_id,parent_id) REFERENCES draft_snapshots(session_id,id)'),
            lambda db: remove(db, ' REFERENCES draft_captures(id) ON DELETE CASCADE'),
            lambda db: remove(db, ',UNIQUE(session_id,revision)')]
        for change in changes:
            with self.subTest(change=change):
                archive = self.rewrite(change=change)
                self.rejected('INCOMPATIBLE_SCHEMA', lambda: recovery.restore(archive, self.destination))

    def test_rehashed_v2_foreign_key_and_stored_parent_identity_failures_are_rejected(self):
        self.populate()
        self.raw_archive()
        changes = [lambda db: db.execute('UPDATE draft_snapshots SET session_id=?', ('f' * 32,)),
            lambda db: db.execute('UPDATE draft_snapshots SET parent_id=? WHERE revision=2', ('f' * 32,)),
            lambda db: self.mutate_payload(db, lambda record: record.update(parent_id=record['id']))]
        for change in changes:
            with self.subTest(change=change):
                archive = self.rewrite(change=change)
                self.rejected('DATABASE_INVALID', lambda: recovery.restore(archive, self.destination))

    def test_rehashed_v2_hash_identity_timestamp_or_coaching_promotion_is_rejected(self):
        self.populate()
        self.raw_archive()
        changes = [lambda record: record.update(input_sha256='0' * 64),
            lambda record: record.update(session_id='f' * 32), lambda record: record.update(received_at=None),
            lambda record: record.update(validation_state='VERIFIED'), lambda record: record.update(coaching_enabled=True),
            lambda record: record.update(gameplan_status='GENERATED'),
            lambda record: record.update(adapter_capability=dict(automatic_collection='AVAILABLE', manual_capture='AVAILABLE'))]
        for change in changes:
            with self.subTest(change=change):
                archive = self.rewrite(change=lambda db: self.mutate_payload(db, change))
                before = archive.read_bytes()
                self.rejected('DATABASE_INVALID', lambda: recovery.restore(archive, self.destination))
                self.assertEqual(archive.read_bytes(), before)

    def test_rehashed_v2_typed_capture_constraints_are_checked_even_with_matching_hash(self):
        self.populate()
        self.raw_archive()
        changes = [lambda record: record['capture'].update(unrequested_gameplan='invented'),
            lambda record: record['capture'].update(observed_at='2026-10-05T06:30:00'),
            lambda record: record['capture']['visible_picks'][0].update(slot=True),
            lambda record: record['capture']['visible_picks'].append(copy.deepcopy(record['capture']['visible_picks'][0])),
            lambda record: record['capture']['role_assignments'][0].update(uncertainty=''),
            lambda record: record['capture']['source'].update(author='')]
        for change in changes:
            with self.subTest(change=change):
                archive = self.rewrite(change=lambda db: self.mutate_payload(db, change, rehash=True))
                self.rejected('DATABASE_INVALID', lambda: recovery.restore(archive, self.destination))

    def test_rehashed_v2_cross_column_revision_title_and_legacy_collision_are_rejected(self):
        self.populate()
        self.raw_archive()
        changes = [lambda db: db.execute("UPDATE draft_captures SET title='different stored title'"),
            lambda db: db.execute('UPDATE draft_captures SET revision=4'),
            lambda db: db.execute('INSERT INTO sessions VALUES (?,?,?,?,?,?)', (self.cid, 'legacy collision', 'SYNTHETIC-1', 'TEST', 0, 'ACTIVE'))]
        for change in changes:
            with self.subTest(change=change):
                archive = self.rewrite(change=change)
                self.rejected('DATABASE_INVALID', lambda: recovery.restore(archive, self.destination))

    def test_rehashed_v2_malformed_duplicate_or_nonobject_json_is_rejected(self):
        self.populate()
        self.raw_archive()
        for raw in ('not JSON', '[]', '{"coaching_enabled":false,"coaching_enabled":true}'):
            with self.subTest(raw=raw):
                archive = self.rewrite(change=lambda db: db.execute('UPDATE draft_snapshots SET payload=? WHERE revision=1', (raw,)))
                self.rejected('DATABASE_INVALID', lambda: recovery.restore(archive, self.destination))

    def test_main_v2_does_not_relax_existing_test_only_case_and_job_validation(self):
        self.populate()
        self.raw_archive()
        changes = [lambda db: db.execute("UPDATE sessions SET mode='LIVE'"),
            lambda db: db.execute("UPDATE cases SET payload='{}'"),
            lambda db: db.execute("UPDATE jobs SET status='COMPLETED',result='{}'")]
        for change in changes:
            with self.subTest(change=change):
                archive = self.rewrite(change=change)
                self.rejected('DATABASE_INVALID', lambda: recovery.restore(archive, self.destination))

    def test_supported_main_metadata_must_equal_actual_version_in_both_directions(self):
        self.raw_archive()
        changed = self.rewrite(metadata=lambda manifest: manifest['files'][recovery.MAIN].update(schema_version=2))
        self.rejected('MANIFEST_INVALID', lambda: recovery.restore(changed, self.destination))
        self.archive.unlink()
        self.populate()
        self.raw_archive()
        changed = self.rewrite(metadata=lambda manifest: manifest['files'][recovery.MAIN].update(schema_version=1))
        self.rejected('MANIFEST_INVALID', lambda: recovery.restore(changed, self.destination))

    def test_unsupported_schema_or_boolean_metadata_is_rejected(self):
        self.populate()
        self.raw_archive()
        for member, version in ((recovery.MAIN, 3), (recovery.MAIN, True), (recovery.RESEARCH, 3)):
            with self.subTest(member=member, version=version):
                archive = self.rewrite(metadata=lambda manifest: manifest['files'][member].update(schema_version=version))
                self.rejected('MANIFEST_INVALID', lambda: recovery.restore(archive, self.destination))

    def test_hash_verification_precedes_main_schema_metadata_crosscheck(self):
        self.populate()
        self.raw_archive()
        archive = self.rewrite(metadata=lambda manifest: manifest['files'][recovery.MAIN].update(schema_version=1, sha256='0' * 64))
        self.rejected('HASH_MISMATCH', lambda: recovery.restore(archive, self.destination))

    def test_deleted_draft_payloads_are_absent_and_tombstones_do_not_identify_operator(self):
        self.populate()
        removed = 'c' * 32
        capture = copy.deepcopy(self.capture)
        capture['title'], capture['source']['author'] = '삭제한 개인 기록', '삭제한 개인 작성자'
        record = self.record(removed, 1, capture)
        with sqlite3.connect(self.main) as db:
            db.execute('PRAGMA foreign_keys=ON')
            db.execute('PRAGMA secure_delete=ON')
            db.execute('INSERT INTO draft_captures VALUES (?,?,?)', (removed, capture['title'], 1))
            db.execute('INSERT INTO draft_snapshots VALUES (?,?,?,?,?)', (record['id'], removed, 1, None, self.canonical(record)))
            db.execute('DELETE FROM draft_captures WHERE id=?', (removed,))
        result = recovery.backup(self.main, self.archive)
        self.assertEqual(result['files'][recovery.MAIN]['schema_version'], 2)
        recovery.restore(self.archive, self.destination)
        rows = self.rows(self.destination / recovery.MAIN)
        self.assertEqual(len(rows['draft_snapshots']), 3)
        self.assertFalse(any(row[1] == removed for row in rows['draft_snapshots']))
        self.assertNotIn(removed, [row[0] for row in rows['tombstones']])
        self.assertNotIn(capture['source']['author'], json.dumps(rows, ensure_ascii=False))
        self.assertNotIn(self.cid, [row[0] for row in rows['sessions']])

    def test_invalid_v2_source_content_fails_without_archive_or_source_mutation(self):
        self.populate()
        with sqlite3.connect(self.main) as db:
            db.execute("UPDATE draft_snapshots SET payload='{}' WHERE revision=1")
        self.rejected('DATABASE_INVALID', lambda: recovery.backup(self.main, self.archive))
        self.assertFalse(self.archive.exists())

    def test_existing_v2_archive_and_destination_are_never_overwritten(self):
        self.populate()
        self.raw_archive()
        original = self.archive.read_bytes()
        self.rejected('DESTINATION_EXISTS', lambda: recovery.backup(self.main, self.archive))
        self.destination.mkdir()
        marker = self.destination / 'existing.txt'
        marker.write_text('keep original', encoding='utf-8')
        with self.assertRaises(recovery.BackupError) as caught:
            recovery.restore(self.archive, self.destination)
        self.assertEqual(caught.exception.code, 'DESTINATION_EXISTS')
        self.assertEqual(marker.read_text(encoding='utf-8'), 'keep original')
        self.assertEqual(self.archive.read_bytes(), original)

    def test_committed_main_v2_wal_snapshots_are_copied_without_source_checkpoint(self):
        self.populate()
        owner = sqlite3.connect(self.main)
        self.addCleanup(owner.close)
        owner.execute('PRAGMA journal_mode=WAL')
        owner.execute('PRAGMA wal_autocheckpoint=0')
        capture = dict(self.capture, title='WAL에 커밋된 수동 기록')
        record = self.record(self.cid, 4, capture, self.records[-1]['id'])
        with sqlite3.connect(self.main) as db:
            db.execute('INSERT INTO draft_snapshots VALUES (?,?,?,?,?)', (record['id'], self.cid, 4, record['parent_id'], self.canonical(record)))
            db.execute('UPDATE draft_captures SET revision=4,title=? WHERE id=?', (capture['title'], self.cid))
        originals, rows = self.bytes(), self.rows(self.main)
        recovery.backup(self.main, self.archive)
        self.assertEqual(self.bytes(), originals)
        recovery.restore(self.archive, self.destination)
        self.assertEqual(self.rows(self.destination / recovery.MAIN), rows)
        self.assertEqual(self.bytes(), originals)


if __name__ == '__main__':
    unittest.main()

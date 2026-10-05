import copy
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
import struct
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import warnings
import zipfile

from coach_v1 import backup as recovery
from coach_v1.research import FIELDS, ResearchStore
from coach_v1.server import Limits, Workbench
from coach_v1.storage import Store
from tests_r3.helpers import fixture


ROOT = Path(__file__).resolve().parents[1]


class CompleteBackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = self.root / 'personal.sqlite'
        self.sidecar = Path(str(self.db) + '.research.sqlite')
        self.archive = self.root / 'personal.zip'
        self.destination = self.root / 'restored'
        self.store = Store(self.db)
        self.research = ResearchStore(self.sidecar)
        self.sid = self.store.create_session('개인 합성 복기', 'SYNTHETIC-1')['id']
        case = fixture()
        case['snapshot_request']['session_id'] = self.sid
        for observation in case['observations']:
            observation['session_id'] = self.sid
        self.store.put_case(self.sid, case, 0, 'first-case')
        self.jid = self.store.submit_review(self.sid, 1, 'first-review')['id']
        self.store.run_job(self.jid)
        changed = copy.deepcopy(case)
        changed['objective'] += ' 수정'
        self.store.put_case(self.sid, changed, 1, 'second-case')
        deleted = self.store.create_session('삭제 이력', 'SYNTHETIC-1')['id']
        self.store.delete_session(deleted)
        self.rid = self.research.add('VIDEO', '개인 영상 후보', {'candidates': [{'cue_index': 2}], 'coaching_enabled': False})['id']
        self.note = {field: '이전 '+field for field in FIELDS}
        self.research.put_note(self.rid, '2', self.note, 0)
        self.research.put_note(self.rid, '2', dict(self.note, known='수정 후 확인'), 1)
        self.research.put_note(self.rid, 'overview', dict(self.note, intention='전체 노트'), 0)

    def assert_error(self, code, callback):
        with self.assertRaises(recovery.BackupError) as caught:
            callback()
        self.assertEqual(caught.exception.code, code)

    def assert_clean(self):
        self.assertEqual(list(self.root.glob('.coach-*')), [])

    def source_bytes(self):
        return self.db.read_bytes(), self.sidecar.read_bytes()

    def rows(self, path, member):
        with closing(sqlite3.connect(path)) as db:
            return {table: db.execute('SELECT * FROM '+table+' ORDER BY rowid').fetchall()
                    for (table,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")}

    def make_archive(self):
        recovery.backup(self.db, self.archive)

    def rewrite(self, entries=None, manifest=None, transform=None):
        with zipfile.ZipFile(self.archive) as original:
            content = [(name, original.read(name)) for name in original.namelist()]
        if entries is not None:
            content = entries(content)
        if manifest is not None:
            content = [(name, manifest(raw) if name == recovery.MANIFEST else raw) for name, raw in content]
        if transform is not None:
            content = transform(content)
        altered = self.root / 'altered.zip'
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(altered, 'w', compression=zipfile.ZIP_STORED) as archive:
                for name, raw in content:
                    archive.writestr(name, raw)
        return altered

    def test_complete_history_restores_through_workbench_without_source_mutation(self):
        source = self.source_bytes()
        main_rows, research_rows = self.rows(self.db, recovery.MAIN), self.rows(self.sidecar, recovery.RESEARCH)
        expected_review = self.store.get_review(self.jid)
        expected_case = self.store.get_case(self.sid)
        expected_note = self.research.get_note(self.rid, '2')
        result = recovery.backup(self.db, self.archive)
        self.assertEqual(set(result['files']), {recovery.MAIN, recovery.RESEARCH})
        if os.name != 'nt':
            self.assertEqual(stat.S_IMODE(self.archive.stat().st_mode), 0o600)
        self.assertEqual(self.source_bytes(), source)
        archive_bytes = self.archive.read_bytes()
        restored = recovery.restore(self.archive, self.destination)
        self.assertEqual(sorted(p.name for p in self.destination.iterdir()), sorted([recovery.MAIN, recovery.RESEARCH]))
        self.assertEqual(self.rows(Path(restored['db']), recovery.MAIN), main_rows)
        self.assertEqual(self.rows(Path(restored['research_db']), recovery.RESEARCH), research_rows)
        server = Workbench(restored['db'], 'x'*40, Limits(1_000_000, 1000, 24, 16, 512, 8))
        try:
            self.assertEqual(server.store.get_case(self.sid), expected_case)
            self.assertEqual(server.store.get_review(self.jid), expected_review)
            self.assertTrue(expected_review['stale'])
            self.assertEqual(server.research.get_note(self.rid, '2'), expected_note)
            self.assertEqual(server.research.get(self.rid), self.research.get(self.rid))
        finally:
            server.server_close()
        self.assertEqual(self.archive.read_bytes(), archive_bytes)
        self.assertEqual(self.source_bytes(), source)
        self.assert_clean()

    def test_missing_research_never_creates_an_empty_replacement(self):
        self.sidecar.unlink()
        before = self.db.read_bytes()
        self.assert_error('RESEARCH_MISSING', lambda: recovery.backup(self.db, self.archive))
        self.assertFalse(self.archive.exists())
        self.assertFalse(self.sidecar.exists())
        self.assertEqual(self.db.read_bytes(), before)
        self.assert_clean()

    def test_missing_main_never_creates_an_empty_database(self):
        absent = self.root / 'absent.sqlite'
        self.assert_error('SOURCE_MISSING', lambda: recovery.backup(absent, self.archive))
        self.assertFalse(absent.exists())
        self.assert_clean()

    def test_existing_archive_and_even_empty_restore_directory_are_preserved(self):
        self.make_archive()
        before = self.archive.read_bytes()
        self.assert_error('DESTINATION_EXISTS', lambda: recovery.backup(self.db, self.archive))
        self.destination.mkdir()
        self.assert_error('DESTINATION_EXISTS', lambda: recovery.restore(self.archive, self.destination))
        self.assertEqual(self.archive.read_bytes(), before)
        self.assertEqual(list(self.destination.iterdir()), [])
        self.assert_clean()

    def test_archive_publication_race_preserves_winner(self):
        real_link = os.link

        def race(source, destination):
            Path(destination).write_bytes(b'other writer won')
            return real_link(source, destination)

        with patch.object(recovery.os, 'link', side_effect=race):
            self.assert_error('DESTINATION_EXISTS', lambda: recovery.backup(self.db, self.archive))
        self.assertEqual(self.archive.read_bytes(), b'other writer won')
        self.assert_clean()

    def test_directory_publication_race_preserves_existing_empty_directory(self):
        self.make_archive()
        real_publish = recovery._publish_directory

        def race(stage, destination):
            destination.mkdir()
            return real_publish(stage, destination)

        with patch.object(recovery, '_publish_directory', side_effect=race):
            self.assert_error('DESTINATION_EXISTS', lambda: recovery.restore(self.archive, self.destination))
        self.assertTrue(self.destination.is_dir())
        self.assertEqual(list(self.destination.iterdir()), [])
        self.assert_clean()

    def test_failed_backup_copy_cleans_staging_and_preserves_sources(self):
        before = self.source_bytes()
        with patch.object(recovery, '_copy_database', side_effect=OSError('injected copy failure')):
            with self.assertRaises(OSError):
                recovery.backup(self.db, self.archive)
        self.assertFalse(self.archive.exists())
        self.assertEqual(self.source_bytes(), before)
        self.assert_clean()
        # Both reserved locks must have been released after the error.
        self.make_archive()

    def test_unsupported_publication_fails_closed_and_cleans_staging(self):
        self.make_archive()
        failure = recovery.BackupError('ATOMIC_RESTORE_UNSUPPORTED', 'injected unsupported host')
        with patch.object(recovery, '_publish_directory', side_effect=failure):
            self.assert_error('ATOMIC_RESTORE_UNSUPPORTED', lambda: recovery.restore(self.archive, self.destination))
        self.assertFalse(self.destination.exists())
        self.assert_clean()

    def test_active_writer_in_either_database_fails_promptly(self):
        for source in (self.db, self.sidecar):
            with self.subTest(source=source), sqlite3.connect(source) as writer:
                writer.execute('BEGIN IMMEDIATE')
                before = self.source_bytes()
                started = time.monotonic()
                self.assert_error('SOURCE_BUSY', lambda: recovery.backup(self.db, self.archive))
                self.assertLess(time.monotonic()-started, 2)
                self.assertEqual(self.source_bytes(), before)
                self.assertFalse(self.archive.exists())
                self.assert_clean()

    def test_backup_cli_separate_reader_under_reserved_locks_finishes_with_timeout(self):
        completed = subprocess.run([sys.executable, '-m', 'coach_v1.backup', 'backup', '--db', str(self.db), '--output', str(self.archive)], cwd=ROOT, capture_output=True, text=True, timeout=5)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)['archive'], str(self.archive))
        restored = subprocess.run([sys.executable, '-m', 'coach_v1.backup', 'restore', '--archive', str(self.archive), '--destination', str(self.destination)], cwd=ROOT, capture_output=True, text=True, timeout=5)
        self.assertEqual(restored.returncode, 0, restored.stderr)
        self.assertEqual(self.rows(self.destination/recovery.RESEARCH, recovery.RESEARCH), self.rows(self.sidecar, recovery.RESEARCH))
        refused = subprocess.run([sys.executable, '-m', 'coach_v1.backup', 'restore', '--archive', str(self.archive), '--destination', str(self.destination)], cwd=ROOT, capture_output=True, text=True, timeout=5)
        self.assertEqual(refused.returncode, 1)
        self.assertEqual(json.loads(refused.stderr)['error_code'], 'DESTINATION_EXISTS')

    def test_wal_committed_rows_and_original_main_file_bytes_are_preserved(self):
        owners = [sqlite3.connect(source) for source in (self.db, self.sidecar)]
        try:
            for owner in owners:
                owner.execute('PRAGMA journal_mode=WAL')
                owner.execute('PRAGMA wal_autocheckpoint=0')
            self.store.create_session('WAL 전용 행', 'SYNTHETIC-1')
            self.research.put_note(self.rid, '2', dict(self.note, known='WAL 노트'), 2)
            source = self.source_bytes()
            main_rows, research_rows = self.rows(self.db, recovery.MAIN), self.rows(self.sidecar, recovery.RESEARCH)
            recovery.backup(self.db, self.archive)
            self.assertEqual(self.source_bytes(), source)
            recovery.restore(self.archive, self.destination)
            self.assertEqual(self.rows(self.destination/recovery.MAIN, recovery.MAIN), main_rows)
            self.assertEqual(self.rows(self.destination/recovery.RESEARCH, recovery.RESEARCH), research_rows)
            # Read-only validation itself must leave exactly the two fixed DBs.
            self.assertEqual(sorted(p.name for p in self.destination.iterdir()), sorted([recovery.MAIN, recovery.RESEARCH]))
        finally:
            for owner in owners:
                owner.close()

    def test_existing_research_numeric_dictionary_keys_preserve_original_identity(self):
        # The existing persistence API accepts numeric dictionary keys. Its
        # stored canonical order differs from the decoded string-key order.
        resource = self.research.add('IMPORT', '기존 숫자 키 보고서', {2: 'two', 10: 'ten'})
        self.make_archive()
        restored = recovery.restore(self.archive, self.destination)
        reopened = ResearchStore(restored['research_db'])
        self.assertEqual(reopened.get(resource['id']), resource)
        self.assertEqual(self.rows(Path(restored['research_db']), recovery.RESEARCH), self.rows(self.sidecar, recovery.RESEARCH))

    def test_tampered_member_is_rejected_without_touching_archive_or_sources(self):
        self.make_archive()
        changed = self.rewrite(entries=lambda entries: [(name, bytes([raw[0] ^ 1])+raw[1:] if name == recovery.RESEARCH else raw) for name, raw in entries])
        before, originals = changed.read_bytes(), self.source_bytes()
        self.assert_error('HASH_MISMATCH', lambda: recovery.restore(changed, self.destination))
        self.assertEqual(changed.read_bytes(), before)
        self.assertEqual(self.source_bytes(), originals)
        self.assertFalse(self.destination.exists())
        self.assert_clean()

    def test_missing_duplicate_traversal_and_extra_members_are_rejected(self):
        self.make_archive()
        transforms = (
            lambda entries: [(name, raw) for name, raw in entries if name != recovery.RESEARCH],
            lambda entries: entries + [(recovery.MAIN, entries[1][1])],
            lambda entries: [(('../'+name) if name == recovery.MAIN else name, raw) for name, raw in entries],
            lambda entries: entries + [('extra.txt', b'extra')],
        )
        for transform in transforms:
            with self.subTest(transform=transform):
                changed = self.rewrite(entries=transform)
                self.assert_error('ARCHIVE_MEMBERS_INVALID', lambda: recovery.restore(changed, self.destination))
                self.assertFalse(self.destination.exists())
                self.assert_clean()

    def test_strict_manifest_version_fields_types_and_duplicate_keys(self):
        self.make_archive()

        def alter(raw, action):
            value = json.loads(raw)
            action(value)
            return json.dumps(value).encode()

        changes = (
            lambda raw: alter(raw, lambda value: value.update(version=2)),
            lambda raw: alter(raw, lambda value: value.update(version=True)),
            lambda raw: alter(raw, lambda value: value.update(extra='unknown')),
            lambda raw: alter(raw, lambda value: value['files'][recovery.MAIN].update(schema_version=True)),
            lambda raw: alter(raw, lambda value: value['files'][recovery.MAIN].update(size=True)),
            lambda raw: alter(raw, lambda value: value['files'][recovery.MAIN].update(sha256='G'*64)),
            lambda raw: b'{"version":1,"version":1}',
        )
        for change in changes:
            with self.subTest(change=change):
                changed = self.rewrite(manifest=change)
                self.assert_error('MANIFEST_INVALID', lambda: recovery.restore(changed, self.destination))
                self.assertFalse(self.destination.exists())
                self.assert_clean()

    def test_rehashed_but_invalid_schema_foreign_keys_or_note_content_are_rejected(self):
        self.make_archive()

        def mutate(entries, member, sql):
            database = self.root / 'mutation.sqlite'
            database.write_bytes(dict(entries)[member])
            with sqlite3.connect(database) as db:
                db.execute(sql)
            raw = database.read_bytes()
            manifest = json.loads(dict(entries)[recovery.MANIFEST])
            manifest['files'][member].update(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())
            return [(name, raw if name == member else json.dumps(manifest).encode() if name == recovery.MANIFEST else body) for name, body in entries]

        mutations = (
            (recovery.MAIN, 'ALTER TABLE sessions ADD COLUMN unexpected TEXT', 'INCOMPATIBLE_SCHEMA'),
            (recovery.RESEARCH, "UPDATE note_history SET resource_id='missing'", 'DATABASE_INVALID'),
            (recovery.RESEARCH, "UPDATE note_history SET payload='{}'", 'DATABASE_INVALID'),
            (recovery.MAIN, "UPDATE cases SET payload='not JSON'", 'DATABASE_INVALID'),
            (recovery.MAIN, 'CREATE TRIGGER unexpected AFTER INSERT ON sessions BEGIN DELETE FROM sessions; END', 'INCOMPATIBLE_SCHEMA'),
            (recovery.MAIN, "UPDATE cases SET payload='{}'", 'DATABASE_INVALID'),
            (recovery.MAIN, "UPDATE sessions SET mode='LIVE'", 'DATABASE_INVALID'),
            (recovery.MAIN, 'UPDATE sessions SET revision=-10', 'DATABASE_INVALID'),
            (recovery.MAIN, 'UPDATE sessions SET revision=9223372036854775807', 'DATABASE_INVALID'),
            (recovery.MAIN, "UPDATE jobs SET status='COMPLETED',result='{}'", 'DATABASE_INVALID'),
            (recovery.RESEARCH, "UPDATE resources SET id='invalid identity'", 'DATABASE_INVALID'),
            (recovery.RESEARCH, "UPDATE note_history SET anchor='3' WHERE anchor='2'", 'DATABASE_INVALID'),
            (recovery.RESEARCH, 'UPDATE note_history SET revision=revision+20', 'DATABASE_INVALID'),
            (recovery.RESEARCH, "UPDATE resources SET report='{\"overflow\":1e999}'", 'DATABASE_INVALID'),
        )
        for member, sql, expected in mutations:
            with self.subTest(sql=sql):
                changed = self.rewrite(transform=lambda entries: mutate(entries, member, sql))
                self.assert_error(expected, lambda: recovery.restore(changed, self.destination))
                self.assertFalse(self.destination.exists())
                self.assert_clean()

    def test_source_schema_or_integrity_failure_never_publishes(self):
        with sqlite3.connect(self.sidecar) as db:
            db.execute('PRAGMA user_version=999')
        before = self.source_bytes()
        self.assert_error('INCOMPATIBLE_SCHEMA', lambda: recovery.backup(self.db, self.archive))
        self.assertEqual(self.source_bytes(), before)
        self.assertFalse(self.archive.exists())
        self.assert_clean()

    def test_hot_journal_is_rejected_without_recovering_or_mutating_source(self):
        crash_writer = """
import os, sqlite3, sys
db = sqlite3.connect(sys.argv[1])
db.execute('PRAGMA cache_size=1')
db.execute('BEGIN IMMEDIATE')
db.execute("UPDATE sessions SET title='uncommitted title'")
for i in range(80):
    db.execute('INSERT INTO sessions VALUES (?,?,?,?,?,?)', (str(i), 'x'*2000, 'SYNTHETIC-1', 'TEST', 0, 'ACTIVE'))
os._exit(0)
"""
        subprocess.run([sys.executable, '-c', crash_writer, str(self.db)], check=True, timeout=5)
        journal = Path(str(self.db)+'-journal')
        self.assertTrue(journal.exists())
        before, journal_bytes = self.source_bytes(), journal.read_bytes()
        self.assert_error('SOURCE_BUSY', lambda: recovery.backup(self.db, self.archive))
        self.assertEqual(self.source_bytes(), before)
        self.assertEqual(journal.read_bytes(), journal_bytes)
        self.assertFalse(self.archive.exists())
        self.assert_clean()

    def test_malformed_archive_is_rejected_and_staging_cleaned(self):
        self.archive.write_bytes(b'not a ZIP archive')
        self.assert_error('ARCHIVE_INVALID', lambda: recovery.restore(self.archive, self.destination))
        self.assertFalse(self.destination.exists())
        self.assert_clean()

    def test_unsupported_zip_flags_and_invalid_local_utf8_have_structured_errors(self):
        self.make_archive()
        original = self.archive.read_bytes()
        with zipfile.ZipFile(self.archive) as archive:
            main_offset = archive.getinfo(recovery.MAIN).header_offset
        patched = bytearray(original)
        central = patched.index(b'PK\x01\x02')
        flags = struct.unpack_from('<H', patched, central+8)[0]
        struct.pack_into('<H', patched, central+8, flags | (1 << 5))
        unsupported = self.root/'unsupported-flags.zip'
        unsupported.write_bytes(patched)
        self.assert_error('ARCHIVE_MEMBERS_INVALID', lambda: recovery.restore(unsupported, self.destination))
        patched = bytearray(original)
        flags = struct.unpack_from('<H', patched, main_offset+6)[0]
        struct.pack_into('<H', patched, main_offset+6, flags | (1 << 11))
        patched[main_offset+30] = 0xff
        invalid_utf8 = self.root/'invalid-utf8.zip'
        invalid_utf8.write_bytes(patched)
        self.assert_error('ARCHIVE_INVALID', lambda: recovery.restore(invalid_utf8, self.destination))
        completed = subprocess.run([sys.executable, '-m', 'coach_v1.backup', 'restore', '--archive', str(invalid_utf8), '--destination', str(self.destination)], cwd=ROOT, capture_output=True, text=True, timeout=5)
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(json.loads(completed.stderr)['error_code'], 'ARCHIVE_INVALID')
        self.assertFalse(self.destination.exists())
        self.assert_clean()

    @unittest.skipUnless(hasattr(os, 'symlink'), 'symlinks unavailable')
    def test_symlink_source_output_destination_and_ancestor_are_rejected(self):
        alias = self.root/'alias.sqlite'
        alias.symlink_to(self.db)
        self.assert_error('UNSAFE_PATH', lambda: recovery.backup(alias, self.archive))
        broken = self.root/'broken.zip'
        broken.symlink_to(self.root/'not-present.zip')
        self.assert_error('UNSAFE_PATH', lambda: recovery.backup(self.db, broken))
        self.make_archive()
        self.destination.symlink_to(self.root/'not-present-directory')
        self.assert_error('UNSAFE_PATH', lambda: recovery.restore(self.archive, self.destination))
        ancestor = self.root/'directory-alias'
        ancestor.symlink_to(self.root, target_is_directory=True)
        self.assert_error('UNSAFE_PATH', lambda: recovery.backup(ancestor/self.db.name, self.root/'elsewhere.zip'))
        self.assert_clean()

    def test_source_hardlink_alias_and_bookkeeping_output_collision_are_rejected(self):
        self.sidecar.unlink()
        os.link(self.db, self.sidecar)
        self.assert_error('PATH_COLLISION', lambda: recovery.backup(self.db, self.archive))
        self.sidecar.unlink()
        ResearchStore(self.sidecar)
        self.assert_error('PATH_COLLISION', lambda: recovery.backup(self.db, Path(str(self.db)+'-wal')))
        self.assert_clean()

    def test_zip_symlink_members_are_rejected(self):
        self.make_archive()
        changed = self.root/'zip-symlink.zip'
        with zipfile.ZipFile(self.archive) as original, zipfile.ZipFile(changed, 'w') as output:
            for name in original.namelist():
                entry = zipfile.ZipInfo(name)
                if name == recovery.RESEARCH:
                    entry.external_attr = (stat.S_IFLNK | 0o777) << 16
                output.writestr(entry, original.read(name))
        self.assert_error('ARCHIVE_MEMBERS_INVALID', lambda: recovery.restore(changed, self.destination))
        self.assertFalse(self.destination.exists())
        self.assert_clean()


if __name__ == '__main__':
    unittest.main()

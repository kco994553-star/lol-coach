"""Real temporary dual-SQLite archives; knowledge remains EXPLORATORY data."""
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import uuid
import zipfile

from coach_v1 import backup as recovery
from coach_v1.knowledge import KnowledgeStore
from coach_v1.research import FIELDS, ResearchStore
from coach_v1.storage import Store


class KnowledgeBackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.main = self.root / 'personal.sqlite'
        self.research_path = Path(str(self.main) + '.research.sqlite')
        self.archive = self.root / 'personal.zip'
        self.destination = self.root / 'restored'
        self.store = Store(self.main)
        self.store.create_session('합성 백업 사례', 'SYNTHETIC-1')
        self.research = ResearchStore(self.research_path)
        self.rid = self.research.add('RAW_DIAGNOSTIC', '직접 기록한 출처 😀', {'coaching_enabled': False})['id']
        self.note = {field: '직접 작성한 원본 ' + field for field in FIELDS}
        self.research.put_note(self.rid, 'overview', self.note, 0)
        self.manual = dict(patch_range='SYNTHETIC-1',
            applicability=dict(champion='직접 지정', role='합성 역할', matchup='미검증 상대', level='명시 조건', context='복기 가설'),
            required_fields=['self:position'], claim='수동으로 기록한 검증 전 가설',
            mechanism='사용자가 적은 설명이며 엔진 판단에 사용하지 않음',
            counterexamples=['적용할 수 없는 조건도 직접 검토해야 함'],
            author='합성 작성자', limitations=['실제 경기 정확도를 검증하지 않음'])

    def source(self, rid=None):
        return dict(resource_id=self.rid if rid is None else rid, anchor='overview', note_revision=1)

    def upgrade(self, *, receipts=True):
        self.knowledge = KnowledgeStore(self.research_path)
        versions = []
        for number in range(3):
            manual = dict(self.manual, claim=self.manual['claim'] + ' 버전 ' + str(number + 1))
            previous = versions[-1] if versions else None
            versions.append(self.knowledge.propose(manual, self.source(),
                rule_id=previous['rule_id'] if previous else None,
                expected_version=previous['version'] if previous else None, max_bytes=100000))
        self.versions = versions
        # A later source note does not replace the exact revision pinned above.
        self.knowledge.put_note(self.rid, 'overview', dict(self.note, known='나중의 다른 노트'), 1)
        if receipts:
            first = self.knowledge.propose(dict(self.manual, claim='삭제 대상 비공개 제안'), self.source(), max_bytes=100000)
            second = self.knowledge.propose(dict(self.manual, claim='삭제 대상 후속 버전'), self.source(),
                rule_id=first['rule_id'], expected_version=first['version'], max_bytes=100000)
            deleted = self.knowledge.delete_proposal(first['rule_id'], second['version'], 100000)
            self.assertEqual(deleted['deleted_versions'], 2)
            rid = self.knowledge.add('RAW_DIAGNOSTIC', '삭제할 비공개 출처', {'coaching_enabled': False, 'delete_fixture': True})['id']
            self.knowledge.put_note(rid, 'overview', dict(self.note, known='삭제할 비공개 메모'), 0)
            self.knowledge.propose(dict(self.manual, claim='출처 삭제에 종속된 제안'), self.source(rid), max_bytes=100000)
            self.assertEqual(self.knowledge.delete(rid)['deleted_versions'], 1)
        return self.knowledge

    def bytes(self):
        return self.main.read_bytes(), self.research_path.read_bytes()

    def rows(self, path):
        with closing(sqlite3.connect(path)) as db:
            return {table: db.execute('SELECT * FROM ' + table + ' ORDER BY rowid').fetchall()
                for (table,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")}

    def version(self, path):
        with closing(sqlite3.connect(path)) as db:
            return db.execute('PRAGMA user_version').fetchone()[0]

    def rejected(self, code, action):
        originals = self.bytes()
        with self.assertRaises(recovery.BackupError) as caught:
            action()
        self.assertEqual(caught.exception.code, code)
        self.assertEqual(self.bytes(), originals)
        self.assertFalse(self.destination.exists())
        self.assertEqual(list(self.root.glob('.coach-*')), [])

    def rewrite(self, *, database_change=None, metadata_change=None):
        with zipfile.ZipFile(self.archive) as archive:
            members = {name: archive.read(name) for name in archive.namelist()}
        manifest = json.loads(members[recovery.MANIFEST])
        if database_change:
            member, change = database_change
            temporary = self.root / (str(uuid.uuid4()) + '.sqlite')
            temporary.write_bytes(members[member])
            with sqlite3.connect(temporary) as db:
                # Adversarial archives can have been created with FK checks off.
                db.execute('PRAGMA foreign_keys=OFF')
                change(db)
            members[member] = temporary.read_bytes()
            manifest['files'][member].update(size=len(members[member]), sha256=hashlib.sha256(members[member]).hexdigest())
        if metadata_change:
            metadata_change(manifest)
        members[recovery.MANIFEST] = json.dumps(manifest).encode('utf-8')
        changed = self.root / (str(uuid.uuid4()) + '.zip')
        with zipfile.ZipFile(changed, 'x', compression=zipfile.ZIP_STORED) as archive:
            for member, raw in members.items():
                archive.writestr(member, raw)
        return changed

    def mutate_payload(self, db, change):
        row = db.execute('SELECT id,version,payload FROM knowledge_rules ORDER BY rowid LIMIT 1').fetchone()
        payload = json.loads(row[2])
        change(payload)
        db.execute('UPDATE knowledge_rules SET payload=? WHERE id=? AND version=?',
            (json.dumps(payload, ensure_ascii=False), row[0], row[1]))

    def test_valid_v1_roundtrip_remains_v1_until_explicit_current_store_open(self):
        original = self.bytes()
        result = recovery.backup(self.main, self.archive)
        self.assertEqual(result['version'], 1)
        self.assertEqual({member: item['schema_version'] for member, item in result['files'].items()},
            {recovery.MAIN: 1, recovery.RESEARCH: 1})
        recovery.restore(self.archive, self.destination)
        self.assertEqual(self.version(self.destination / recovery.RESEARCH), 1)
        self.assertEqual(self.rows(self.destination / recovery.RESEARCH), self.rows(self.research_path))
        reopened = KnowledgeStore(self.destination / recovery.RESEARCH)
        self.assertEqual(reopened.get_note(self.rid, 'overview')['known'], self.note['known'])
        self.assertEqual(self.version(self.destination / recovery.RESEARCH), 2)
        self.assertEqual(self.bytes(), original)

    def test_v2_roundtrip_retains_all_versions_source_notes_and_private_count_receipts(self):
        self.upgrade()
        originals, rows = self.bytes(), self.rows(self.research_path)
        result = recovery.backup(self.main, self.archive)
        self.assertEqual(result['version'], recovery.VERSION)
        self.assertEqual(result['files'][recovery.MAIN]['schema_version'], 1)
        self.assertEqual(result['files'][recovery.RESEARCH]['schema_version'], 2)
        with zipfile.ZipFile(self.archive) as archive:
            self.assertEqual(set(archive.namelist()), {recovery.MANIFEST, recovery.MAIN, recovery.RESEARCH})
        recovery.restore(self.archive, self.destination)
        self.assertEqual(self.version(self.destination / recovery.RESEARCH), 2)
        self.assertEqual(self.rows(self.destination / recovery.MAIN), self.rows(self.main))
        self.assertEqual(self.rows(self.destination / recovery.RESEARCH), rows)
        self.assertEqual(sorted(path.name for path in self.destination.iterdir()), sorted([recovery.MAIN, recovery.RESEARCH]))
        self.assertEqual(len(rows['knowledge_rules']), 3)
        self.assertEqual(sorted(row[1] for row in rows['knowledge_delete_receipts']), [1, 2])
        for receipt in rows['knowledge_delete_receipts']:
            self.assertEqual(len(receipt), 2)
            self.assertEqual(uuid.UUID(receipt[0]).hex, receipt[0])
        self.assertEqual(self.bytes(), originals)

    def test_backup_restore_never_constructs_or_migrates_application_stores(self):
        self.upgrade()
        original = self.bytes()
        with patch.object(Store, '__init__', side_effect=AssertionError('Store startup forbidden')), \
             patch.object(ResearchStore, '__init__', side_effect=AssertionError('Research startup forbidden')), \
             patch.object(KnowledgeStore, '__init__', side_effect=AssertionError('Knowledge startup forbidden')):
            recovery.backup(self.main, self.archive)
            recovery.restore(self.archive, self.destination)
        self.assertEqual(self.bytes(), original)
        self.assertEqual(self.rows(self.destination / recovery.RESEARCH), self.rows(self.research_path))

    def test_cli_preserves_structured_missing_dependency_error_without_eager_startup(self):
        environment = dict(os.environ)
        environment.pop('PYTHONPATH', None)
        root = Path(__file__).resolve().parents[1]
        command = [sys.executable, '-S', '-m', 'coach_v1.backup']
        help_result = subprocess.run(command + ['--help'], cwd=root, env=environment,
            capture_output=True, text=True, timeout=5)
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        originals = self.bytes()
        result = subprocess.run(command + ['backup', '--db', str(self.main), '--output', str(self.archive)],
            cwd=root, env=environment, capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads(result.stderr)['error_code'], 'DEPENDENCY_MISSING')
        self.assertEqual(self.bytes(), originals)
        self.assertFalse(self.archive.exists())
        self.assertEqual(list(self.root.glob('.coach-*')), [])

    def test_restored_source_fk_and_parent_fk_cascade_across_different_sources(self):
        self.upgrade()
        other = self.knowledge.add('RAW_DIAGNOSTIC', '후속 버전의 별도 출처',
            {'coaching_enabled': False, 'alternate_source': True})['id']
        self.knowledge.put_note(other, 'overview', dict(self.note, known='별도 출처 메모'), 0)
        head = self.versions[-1]
        self.knowledge.propose(dict(self.manual, claim='별도 출처를 참조하는 후속 버전'), self.source(other),
            rule_id=head['rule_id'], expected_version=head['version'], max_bytes=100000)
        originals = self.bytes()
        recovery.backup(self.main, self.archive)
        recovery.restore(self.archive, self.destination)
        restored = KnowledgeStore(self.destination / recovery.RESEARCH)
        result = restored.delete(self.rid)
        self.assertEqual(result['deleted_versions'], 4)
        rows = self.rows(self.destination / recovery.RESEARCH)
        self.assertEqual(rows['knowledge_rules'], [])
        self.assertEqual(sorted(row[1] for row in rows['knowledge_delete_receipts']), [1, 2, 4])
        self.assertEqual(restored.get_note(other, 'overview')['revision'], 1)
        self.assertEqual(restored.get(other)['id'], other)
        self.assertEqual(self.bytes(), originals)

    def test_current_workbench_reopens_complete_restored_v2(self):
        from coach_v1.server import Limits, Workbench
        self.upgrade()
        rows = self.rows(self.research_path)
        recovery.backup(self.main, self.archive)
        restored = recovery.restore(self.archive, self.destination)
        server = Workbench(restored['db'], 'x' * 40, Limits(100000, 1000, 24, 16, 512, 8))
        try:
            self.assertIsInstance(server.research, KnowledgeStore)
            self.assertEqual(server.research.get_note(self.rid, 'overview')['revision'], 2)
            self.assertEqual(self.rows(Path(restored['research_db'])), rows)
        finally:
            server.server_close()

    def test_rehashed_v2_extra_objects_and_removed_source_or_parent_fk_are_rejected(self):
        self.upgrade()
        recovery.backup(self.main, self.archive)
        source_fk = ',FOREIGN KEY(resource_id,anchor,revision) REFERENCES note_history(resource_id,anchor,revision) ON DELETE CASCADE'
        parent_fk = ',FOREIGN KEY(id,parent_version) REFERENCES knowledge_rules(id,version) ON DELETE CASCADE'
        def remove_fk(db, fragment):
            sql = db.execute("SELECT sql FROM sqlite_master WHERE name='knowledge_rules'").fetchone()[0]
            self.assertIn(fragment, sql)
            db.execute('PRAGMA writable_schema=ON')
            db.execute("UPDATE sqlite_master SET sql=? WHERE name='knowledge_rules'", (sql.replace(fragment, ''),))
        changes = [lambda db: db.execute('ALTER TABLE knowledge_rules ADD COLUMN unexpected TEXT'),
            lambda db: db.execute('CREATE TRIGGER unexpected AFTER INSERT ON knowledge_rules BEGIN SELECT 1; END'),
            lambda db: remove_fk(db, source_fk), lambda db: remove_fk(db, parent_fk)]
        for change in changes:
            with self.subTest(change=change):
                archive = self.rewrite(database_change=(recovery.RESEARCH, change))
                self.rejected('INCOMPATIBLE_SCHEMA', lambda: recovery.restore(archive, self.destination))

    def test_rehashed_v2_physical_source_or_parent_reference_failure_is_rejected(self):
        self.upgrade()
        recovery.backup(self.main, self.archive)
        changes = [lambda db: db.execute("UPDATE knowledge_rules SET resource_id=?", ('f' * 64,)),
            lambda db: db.execute('UPDATE knowledge_rules SET parent_version=?', (str(uuid.uuid4()),))]
        for change in changes:
            with self.subTest(change=change):
                archive = self.rewrite(database_change=(recovery.RESEARCH, change))
                self.rejected('DATABASE_INVALID', lambda: recovery.restore(archive, self.destination))

    def test_rehashed_v2_non_exploratory_status_or_claim_is_rejected(self):
        self.upgrade()
        recovery.backup(self.main, self.archive)
        changes = [lambda db: db.execute("UPDATE knowledge_rules SET status='REVIEWED'"),
            lambda db: self.mutate_payload(db, lambda payload: payload.update(review_state='REVIEWED')),
            lambda db: self.mutate_payload(db, lambda payload: payload.update(claim=123)),
            lambda db: self.mutate_payload(db, lambda payload: payload.update(unrequested='hidden scope'))]
        for change in changes:
            with self.subTest(change=change):
                archive = self.rewrite(database_change=(recovery.RESEARCH, change))
                before = archive.read_bytes()
                self.rejected('DATABASE_INVALID', lambda: recovery.restore(archive, self.destination))
                self.assertEqual(archive.read_bytes(), before)

    def test_rehashed_v2_malformed_or_duplicate_json_payload_is_rejected(self):
        self.upgrade()
        recovery.backup(self.main, self.archive)
        for raw in ('not JSON', '{"review_state":"EXPLORATORY","review_state":"REVIEWED"}'):
            with self.subTest(raw=raw):
                archive = self.rewrite(database_change=(recovery.RESEARCH,
                    lambda db: db.execute('UPDATE knowledge_rules SET payload=? WHERE rowid=(SELECT MIN(rowid) FROM knowledge_rules)', (raw,))))
                self.rejected('DATABASE_INVALID', lambda: recovery.restore(archive, self.destination))

    def test_rehashed_v2_payload_source_pin_hash_and_supersedes_are_validated(self):
        self.upgrade()
        recovery.backup(self.main, self.archive)
        changes = [lambda payload: payload['source_refs'][0].update(note_revision=2),
            lambda payload: payload['source_refs'][0].update(note_sha256='0' * 64),
            lambda payload: payload.update(supersedes=uuid.uuid4().hex)]
        for change in changes:
            with self.subTest(change=change):
                archive = self.rewrite(database_change=(recovery.RESEARCH,
                    lambda db: self.mutate_payload(db, change)))
                self.rejected('DATABASE_INVALID', lambda: recovery.restore(archive, self.destination))

    def test_rehashed_v2_receipts_reject_identifying_fields_invalid_ids_and_counts(self):
        self.upgrade()
        recovery.backup(self.main, self.archive)
        changes = [('INCOMPATIBLE_SCHEMA', lambda db: db.execute('ALTER TABLE knowledge_delete_receipts ADD COLUMN source_id TEXT')),
            ('DATABASE_INVALID', lambda db: db.execute("UPDATE knowledge_delete_receipts SET id='identifying-source-name' WHERE rowid=(SELECT MIN(rowid) FROM knowledge_delete_receipts)")),
            ('DATABASE_INVALID', lambda db: db.execute('UPDATE knowledge_delete_receipts SET deleted_count=-1')),
            ('DATABASE_INVALID', lambda db: db.execute("UPDATE knowledge_delete_receipts SET deleted_count='not a count'"))]
        for code, change in changes:
            with self.subTest(code=code, change=change):
                archive = self.rewrite(database_change=(recovery.RESEARCH, change))
                self.rejected(code, lambda: recovery.restore(archive, self.destination))

    def test_supported_manifest_version_must_match_actual_unmodified_database(self):
        for migrated in (False, True):
            with self.subTest(actual=2 if migrated else 1):
                if migrated:
                    self.upgrade()
                    self.archive.unlink()
                recovery.backup(self.main, self.archive)
                archive = self.rewrite(metadata_change=lambda manifest: manifest['files'][recovery.RESEARCH].update(schema_version=1 if migrated else 2))
                self.rejected('SCHEMA_VERSION_MISMATCH', lambda: recovery.restore(archive, self.destination))

    def test_manifest_never_admits_main_v2_research_v3_or_boolean_versions(self):
        self.upgrade()
        recovery.backup(self.main, self.archive)
        for member, version in ((recovery.MAIN, 2), (recovery.RESEARCH, 3), (recovery.RESEARCH, True)):
            with self.subTest(member=member, version=version):
                archive = self.rewrite(metadata_change=lambda manifest: manifest['files'][member].update(schema_version=version))
                self.rejected('MANIFEST_INVALID', lambda: recovery.restore(archive, self.destination))

    def test_unsupported_actual_v2_claims_never_publish_or_mutate_sources(self):
        self.upgrade()
        for version in (1, 3):
            with self.subTest(version=version), sqlite3.connect(self.research_path) as db:
                db.execute('PRAGMA user_version=' + str(version))
                db.commit()
                self.rejected('INCOMPATIBLE_SCHEMA', lambda: recovery.backup(self.main, self.archive))
                self.assertFalse(self.archive.exists())

    def test_hash_verification_precedes_supported_schema_metadata_crosscheck(self):
        self.upgrade()
        recovery.backup(self.main, self.archive)
        def mismatch(manifest):
            manifest['files'][recovery.RESEARCH].update(schema_version=1, sha256='0' * 64)
        archive = self.rewrite(metadata_change=mismatch)
        self.rejected('HASH_MISMATCH', lambda: recovery.restore(archive, self.destination))

    def test_invalid_v2_source_content_never_publishes_backup(self):
        self.upgrade()
        with sqlite3.connect(self.research_path) as db:
            self.mutate_payload(db, lambda payload: payload.update(claim=123))
        self.rejected('DATABASE_INVALID', lambda: recovery.backup(self.main, self.archive))
        self.assertFalse(self.archive.exists())

    def test_v2_existing_destinations_are_preserved(self):
        self.upgrade()
        recovery.backup(self.main, self.archive)
        original = self.archive.read_bytes()
        self.rejected('DESTINATION_EXISTS', lambda: recovery.backup(self.main, self.archive))
        self.destination.mkdir()
        marker = self.destination / 'existing.txt'
        marker.write_text('already present', encoding='utf-8')
        with self.assertRaises(recovery.BackupError) as caught:
            recovery.restore(self.archive, self.destination)
        self.assertEqual(caught.exception.code, 'DESTINATION_EXISTS')
        self.assertEqual(marker.read_text(encoding='utf-8'), 'already present')
        self.assertEqual(self.archive.read_bytes(), original)

    def test_committed_v2_wal_rows_are_copied_without_source_checkpoint(self):
        self.upgrade()
        owner = sqlite3.connect(self.research_path)
        self.addCleanup(owner.close)
        owner.execute('PRAGMA journal_mode=WAL')
        owner.execute('PRAGMA wal_autocheckpoint=0')
        prior = self.versions[-1]
        self.knowledge.propose(dict(self.manual, claim='WAL에 커밋된 합성 후속 버전'), self.source(),
            rule_id=prior['rule_id'], expected_version=prior['version'], max_bytes=100000)
        originals, rows = self.bytes(), self.rows(self.research_path)
        recovery.backup(self.main, self.archive)
        self.assertEqual(self.bytes(), originals)
        recovery.restore(self.archive, self.destination)
        self.assertEqual(self.rows(self.destination / recovery.RESEARCH), rows)
        self.assertEqual(self.bytes(), originals)


if __name__ == '__main__':
    unittest.main()

"""Synthetic source-bound proposal/migration tests; no real knowledge validation."""
from concurrent.futures import ThreadPoolExecutor
import copy
import hashlib
import json
import shutil
import stat
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import uuid

from coach_v1.knowledge import (KnowledgeStore, RULE_FIELDS, validate_schema,
                               validate_knowledge_content)
from coach_v1.research import ResearchStore, _json
from coach_v1.storage import ServiceError


def rule(claim='합성 테스트 가설 😀'):
    return dict(patch_range='UNKNOWN', applicability={field: 'UNKNOWN' for field in
        ('champion', 'role', 'matchup', 'level', 'context')}, required_fields=['UNKNOWN'],
        claim=claim, mechanism='UNKNOWN', counterexamples=['UNKNOWN'], author='직접 입력한 작성자',
        limitations=['UNKNOWN'])


class KnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'research.sqlite'
        legacy = ResearchStore(self.path)
        self.raw = legacy.add('RAW_DIAGNOSTIC', '합성 진단', {'coaching_enabled': False})
        self.video = legacy.add('VIDEO', '합성 영상', {'candidates': [{'cue_index': 2}]})
        self.note = dict(known='PRIVATE_SAVED_NOTE_원문😀', intention='이후의 의도',
                         alternative='대안', outcome='사후 결과')
        legacy.put_note(self.raw['id'], 'overview', self.note, 0)
        legacy.put_note(self.video['id'], '2', self.note, 0)
        self.source = dict(resource_id=self.raw['id'], anchor='overview', note_revision=1)
        self.video_source = dict(resource_id=self.video['id'], anchor='2', note_revision=1)
        self.store = KnowledgeStore(self.path)
        self.budget = 100000

    def propose(self, values=None, source=None, previous=None, budget=None):
        return self.store.propose(rule() if values is None else values,
            self.source if source is None else source,
            rule_id=None if previous is None else previous['rule_id'],
            expected_version=None if previous is None else previous['version'],
            max_bytes=self.budget if budget is None else budget)

    def state(self):
        with sqlite3.connect(self.path) as db:
            names = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
            return (db.execute('PRAGMA user_version').fetchone()[0],
                db.execute('SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name').fetchall(),
                {name: db.execute('SELECT * FROM '+name+' ORDER BY rowid').fetchall() for name in names})

    def rejected(self, status, code, operation):
        before = self.state()
        with self.assertRaises(ServiceError) as caught:
            operation()
        self.assertEqual((caught.exception.status, caught.exception.code), (status, code))
        self.assertEqual(self.state(), before)

    def validate(self):
        with sqlite3.connect(self.path) as db:
            db.row_factory = sqlite3.Row
            validate_schema(db)
            validate_knowledge_content(db)

    def test_v1_migration_keeps_exact_reports_and_all_note_revisions(self):
        other = Path(self.temp.name) / 'legacy.sqlite'
        legacy = ResearchStore(other)
        raw = legacy.add('RAW_DIAGNOSTIC', '보존할 개인 제목', {'raw_facts': ['원문 😀']})
        legacy.put_note(raw['id'], 'overview', self.note, 0)
        legacy.put_note(raw['id'], 'overview', dict(self.note, known='수정 노트'), 1)
        with sqlite3.connect(other) as db:
            before = (db.execute('SELECT * FROM resources').fetchall(), db.execute('SELECT * FROM note_history').fetchall())
        migrated = KnowledgeStore(other)
        with sqlite3.connect(other) as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 2)
            self.assertEqual(before, (db.execute('SELECT * FROM resources').fetchall(),
                                     db.execute('SELECT * FROM note_history').fetchall()))
        self.assertEqual(migrated.get_note(raw['id'], 'overview')['revision'], 2)
        with self.assertRaises(ServiceError) as caught:
            ResearchStore(other)
        self.assertEqual(caught.exception.code, 'INCOMPATIBLE_RESEARCH_SCHEMA')

    def test_fresh_store_and_v2_restart_preserve_proposals(self):
        fresh = KnowledgeStore(Path(self.temp.name) / 'fresh.sqlite')
        self.assertEqual(fresh.list_proposals(self.budget), [])
        saved = self.propose()
        before = self.state()
        restarted = KnowledgeStore(self.path)
        self.assertEqual(restarted.get_proposal(saved['rule_id'], max_bytes=self.budget), saved)
        self.assertEqual(self.state(), before)

    def test_actual_pre_migration_snapshot_hash_permissions_and_recovery(self):
        metadata = self.store.migration_backup
        self.assertEqual(set(metadata), {'path', 'schema_version', 'size', 'sha256'})
        snapshot = Path(metadata['path'])
        self.assertTrue(snapshot.is_file())
        self.assertEqual(metadata['schema_version'], 1)
        self.assertEqual(metadata['size'], snapshot.stat().st_size)
        self.assertEqual(metadata['sha256'], hashlib.sha256(snapshot.read_bytes()).hexdigest())
        self.assertEqual(stat.S_IMODE(snapshot.stat().st_mode), 0o600)
        recovered = Path(self.temp.name) / 'recovered-v1.sqlite'
        shutil.copyfile(snapshot, recovered)
        legacy = ResearchStore(recovered)
        self.assertEqual(legacy.get(self.raw['id']), self.raw)
        self.assertEqual(legacy.get_note(self.raw['id'], 'overview')['known'], self.note['known'])
        self.assertEqual(legacy.get_note(self.video['id'], '2')['revision'], 1)

    def test_v2_restart_does_not_make_another_migration_snapshot(self):
        before = sorted(Path(self.temp.name).glob('*.pre-knowledge-v2-*.sqlite'))
        restarted = KnowledgeStore(self.path)
        self.assertIsNone(restarted.migration_backup)
        self.assertEqual(sorted(Path(self.temp.name).glob('*.pre-knowledge-v2-*.sqlite')), before)

    def test_snapshot_copy_failure_keeps_v1_and_cleans_unpublished_files(self):
        other = Path(self.temp.name) / 'copy-failure.sqlite'
        legacy = ResearchStore(other)
        resource = legacy.add('RAW_DIAGNOSTIC', '고유 제목', {'saved': True})
        legacy.put_note(resource['id'], 'overview', self.note, 0)
        with patch('coach_v1.backup._copy_database', side_effect=RuntimeError('injected backup failure')):
            with self.assertRaises(ServiceError) as caught:
                KnowledgeStore(other)
        self.assertEqual((caught.exception.status, caught.exception.code), (503, 'MIGRATION_BACKUP_FAILED'))
        self.assertEqual(ResearchStore(other).get_note(resource['id'], 'overview')['known'], self.note['known'])
        self.assertEqual(list(other.parent.glob(other.name+'.migration-*')), [])
        self.assertEqual(list(other.parent.glob(other.name+'.pre-knowledge-v2-*')), [])
        with sqlite3.connect(other) as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 1)
            self.assertEqual({r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")},
                             {'resources', 'note_history'})

    def test_snapshot_publication_never_overwrites_existing_path(self):
        other = Path(self.temp.name) / 'collision.sqlite'
        ResearchStore(other)
        nonce = uuid.UUID('35d1366c-91ad-40bc-809c-b82b40df070a')
        destination = other.with_name(other.name+'.pre-knowledge-v2-'+nonce.hex+'.sqlite')
        destination.write_bytes(b'existing recovery file stays intact')
        with patch('coach_v1.knowledge.uuid.uuid4', return_value=nonce):
            with self.assertRaises(ServiceError) as caught:
                KnowledgeStore(other)
        self.assertEqual(caught.exception.code, 'MIGRATION_BACKUP_FAILED')
        self.assertEqual(destination.read_bytes(), b'existing recovery file stays intact')
        self.assertEqual(list(other.parent.glob(other.name+'.migration-*')), [])
        with sqlite3.connect(other) as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 1)

    def test_snapshot_capacity_gate_precedes_copy(self):
        other = Path(self.temp.name) / 'capacity.sqlite'
        ResearchStore(other)
        with patch('coach_v1.backup.MAX_DATABASE_BYTES', 1), patch('coach_v1.backup._copy_database') as copying:
            with self.assertRaises(ServiceError) as caught:
                KnowledgeStore(other)
        self.assertEqual(caught.exception.code, 'MIGRATION_BACKUP_FAILED')
        copying.assert_not_called()
        with sqlite3.connect(other) as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 1)

    def test_unknown_v1_object_rejected_without_migration(self):
        other = Path(self.temp.name) / 'badlegacy.sqlite'
        ResearchStore(other)
        with sqlite3.connect(other) as db:
            db.execute('CREATE INDEX unknown_index ON resources(title)')
        with sqlite3.connect(other) as db:
            before = db.execute('SELECT * FROM sqlite_master').fetchall()
        with self.assertRaises(ServiceError) as caught:
            KnowledgeStore(other)
        self.assertEqual(caught.exception.code, 'INCOMPATIBLE_KNOWLEDGE_SCHEMA')
        with sqlite3.connect(other) as db:
            self.assertEqual(db.execute('SELECT * FROM sqlite_master').fetchall(), before)
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 1)

    def test_v2_extra_object_rejected_without_rewriting(self):
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE INDEX unknown_index ON knowledge_rules(status)')
        self.rejected(409, 'INCOMPATIBLE_KNOWLEDGE_SCHEMA', lambda: KnowledgeStore(self.path))

    def test_migration_failure_rolls_back_ddl_and_version(self):
        other = Path(self.temp.name) / 'rollback.sqlite'
        ResearchStore(other)
        with patch('coach_v1.knowledge.validate_knowledge_content', side_effect=ServiceError(409, 'INJECTED_FAILURE')):
            with self.assertRaises(ServiceError):
                KnowledgeStore(other)
        with sqlite3.connect(other) as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 1)
            self.assertEqual({r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")},
                             {'resources', 'note_history'})
        snapshots = list(other.parent.glob(other.name+'.pre-knowledge-v2-*.sqlite'))
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(ResearchStore(snapshots[0]).list(), [])

    def test_invalid_legacy_content_rejected_before_any_v2_ddl(self):
        for corruption in ('note_payload', 'note_gap', 'report_hash', 'report_scalar'):
            other = Path(self.temp.name) / (corruption+'.sqlite')
            legacy = ResearchStore(other)
            resource = legacy.add('RAW_DIAGNOSTIC', '보존 데이터', {'original': True})
            legacy.put_note(resource['id'], 'overview', self.note, 0)
            with sqlite3.connect(other) as db:
                if corruption == 'note_payload':
                    db.execute("UPDATE note_history SET payload='{}'")
                elif corruption == 'note_gap':
                    db.execute('UPDATE note_history SET revision=2')
                elif corruption == 'report_hash':
                    db.execute("UPDATE resources SET report='{\"changed\":true}'")
                else:
                    encoded = _json('scalar report')
                    changed_id = hashlib.sha256(_json({'kind': 'RAW_DIAGNOSTIC', 'report': 'scalar report'}).encode()).hexdigest()
                    db.execute('UPDATE resources SET id=?,report=?', (changed_id, encoded))
                    db.execute('UPDATE note_history SET resource_id=?', (changed_id,))
            with sqlite3.connect(other) as db:
                before = (db.execute('SELECT * FROM sqlite_master').fetchall(),
                          db.execute('SELECT * FROM resources').fetchall(),
                          db.execute('SELECT * FROM note_history').fetchall())
            with self.assertRaises(ServiceError) as caught:
                KnowledgeStore(other)
            self.assertEqual(caught.exception.code, 'INVALID_STORED_KNOWLEDGE')
            with sqlite3.connect(other) as db:
                self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 1)
                self.assertEqual(before, (db.execute('SELECT * FROM sqlite_master').fetchall(),
                                         db.execute('SELECT * FROM resources').fetchall(),
                                         db.execute('SELECT * FROM note_history').fetchall()))

    def test_proposal_is_exploratory_and_unknown_fields_are_exact(self):
        values = rule()
        values['author'] = 'UNKNOWN'
        saved = self.propose(values)
        self.assertEqual({key: saved[key] for key in RULE_FIELDS}, values)
        self.assertEqual((saved['review_state'], saved['coaching_enabled'], saved['supersedes']),
                         ('EXPLORATORY', False, None))
        self.assertEqual(uuid.UUID(hex=saved['rule_id']).version, 4)
        self.assertEqual(uuid.UUID(hex=saved['version']).version, 4)
        self.assertNotEqual(saved['rule_id'], saved['version'])
        self.assertEqual(saved['schema_version'], 'knowledge-proposal.v1')
        self.validate()

    def test_source_hashes_bind_exact_saved_bytes_not_copied_note_text(self):
        saved = self.propose()
        with sqlite3.connect(self.path) as db:
            report = db.execute('SELECT report FROM resources WHERE id=?', (self.raw['id'],)).fetchone()[0]
            note = db.execute('SELECT payload FROM note_history WHERE resource_id=?', (self.raw['id'],)).fetchone()[0]
        expected = dict(self.source, kind='RAW_DIAGNOSTIC',
            report_sha256=hashlib.sha256(report.encode()).hexdigest(),
            note_sha256=hashlib.sha256(note.encode()).hexdigest())
        self.assertEqual(saved['source_refs'], [expected])
        self.assertNotIn('PRIVATE_SAVED_NOTE', _json(saved))
        self.assertNotIn(self.note['outcome'], _json(saved))

    def test_video_actual_anchor_and_overview_are_supported(self):
        cue = self.propose(source=self.video_source)
        self.assertEqual((cue['source_refs'][0]['kind'], cue['source_refs'][0]['anchor']), ('VIDEO', '2'))
        self.store.put_note(self.video['id'], 'overview', self.note, 0)
        overview = self.propose(source=dict(self.video_source, anchor='overview'))
        self.assertEqual(overview['source_refs'][0]['anchor'], 'overview')

    def test_source_revision_requires_positive_exact_integer(self):
        for revision in (0, -1, True, False, '1', 1.0, None, 9223372036854775808):
            self.rejected(422, 'INVALID_KNOWLEDGE_SOURCE',
                lambda revision=revision: self.propose(source=dict(self.source, note_revision=revision)))
        self.rejected(404, 'NOTE_REVISION_NOT_FOUND',
            lambda: self.propose(source=dict(self.source, note_revision=2)))

    def test_missing_and_unsaved_sources_never_create_fake_notes(self):
        self.rejected(404, 'RESOURCE_NOT_FOUND',
            lambda: self.propose(source=dict(self.source, resource_id='a'*64)))
        unsaved = self.store.add('RAW_DIAGNOSTIC', '아직 저장 안 됨', {'different': True})
        self.rejected(404, 'NOTE_REVISION_NOT_FOUND',
            lambda: self.propose(source=dict(self.source, resource_id=unsaved['id'])))

    def test_one_source_slice_rejects_lists_spoofed_hashes_and_unsupported_kinds(self):
        self.rejected(422, 'INVALID_KNOWLEDGE_SOURCE', lambda: self.propose(source=[self.source]))
        self.rejected(422, 'INVALID_KNOWLEDGE_SOURCE',
            lambda: self.propose(source=dict(self.source, note_sha256='b'*64)))
        custom = self.store.add('CUSTOM', '사용자 자료', {'custom': True})
        self.store.put_note(custom['id'], 'overview', self.note, 0)
        self.rejected(422, 'INVALID_KNOWLEDGE_SOURCE',
            lambda: self.propose(source=dict(self.source, resource_id=custom['id'])))

    def test_source_anchor_uses_existing_rules(self):
        self.rejected(422, 'INVALID_NOTE_ANCHOR',
            lambda: self.propose(source=dict(self.source, anchor='2')))
        for anchor in ('02', '0', '3'):
            self.rejected(422, 'INVALID_NOTE_ANCHOR',
                lambda anchor=anchor: self.propose(source=dict(self.video_source, anchor=anchor)))

    def test_new_note_does_not_rebind_existing_candidate(self):
        saved = self.propose()
        self.store.put_note(self.raw['id'], 'overview', dict(self.note, known='새 노트'), 1)
        self.assertEqual(self.store.get_proposal(saved['rule_id'], max_bytes=self.budget), saved)
        updated = self.propose(source=dict(self.source, note_revision=2), previous=saved)
        self.assertEqual(updated['source_refs'][0]['note_revision'], 2)
        self.assertNotEqual(updated['source_refs'][0]['note_sha256'], saved['source_refs'][0]['note_sha256'])
        self.validate()

    def test_new_version_keeps_old_payload_and_current_cas(self):
        first = self.propose()
        second = self.propose(rule('수정된 가설'), previous=first)
        self.assertEqual((second['rule_id'], second['supersedes']), (first['rule_id'], first['version']))
        self.assertNotEqual(second['version'], first['version'])
        self.assertEqual(self.store.get_proposal(first['rule_id'], first['version'], max_bytes=self.budget), first)
        self.assertEqual(self.store.get_proposal(first['rule_id'], max_bytes=self.budget), second)
        self.rejected(409, 'REVISION_CONFLICT', lambda: self.propose(previous=first))

    def test_cas_rejects_another_rules_version(self):
        first, other = self.propose(), self.propose(rule('별도 가설'))
        self.rejected(409, 'REVISION_CONFLICT', lambda: self.store.propose(rule(), self.source,
            rule_id=first['rule_id'], expected_version=other['version'], max_bytes=self.budget))

    def test_concurrent_versions_have_one_winner_and_no_fork(self):
        first = self.propose()
        def attempt(claim):
            try:
                return self.propose(rule(claim), previous=first)
            except ServiceError as error:
                return error.code
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(attempt, ('동시 A', '동시 B')))
        self.assertEqual(sum(isinstance(value, dict) for value in outcomes), 1)
        self.assertEqual(outcomes.count('REVISION_CONFLICT'), 1)
        self.assertEqual(len(self.store.list_proposals(self.budget)), 2)
        self.validate()

    def test_source_delete_removes_dependents_descendants_and_keeps_other_rules(self):
        first = self.propose()
        second = self.propose(source=self.video_source, previous=first)
        unrelated = self.propose(rule('독립 가설'), source=self.video_source)
        result = self.store.delete(self.raw['id'])
        self.assertEqual(result['deleted_versions'], 2)
        self.assertEqual(self.store.get_proposal(unrelated['rule_id'], max_bytes=self.budget), unrelated)
        for saved in (first, second):
            self.rejected(404, 'KNOWLEDGE_RULE_NOT_FOUND',
                lambda saved=saved: self.store.get_proposal(saved['rule_id'], saved['version'], max_bytes=self.budget))
        self.assertEqual(self.store.get_note(self.video['id'], '2')['revision'], 1)
        self.validate()

    def test_midchain_source_delete_keeps_ancestor_and_new_identity_is_not_reused(self):
        first = self.propose()
        second = self.propose(source=self.video_source, previous=first)
        third = self.propose(previous=second)
        result = self.store.delete(self.video['id'])
        self.assertEqual(result['deleted_versions'], 2)
        self.assertEqual(self.store.get_proposal(first['rule_id'], max_bytes=self.budget), first)
        replacement = self.propose(previous=first)
        self.assertNotIn(replacement['version'], (second['version'], third['version']))
        self.assertEqual(replacement['supersedes'], first['version'])
        self.validate()

    def test_source_delete_without_proposals_preserves_legacy_response(self):
        self.assertEqual(self.store.delete(self.raw['id']), dict(id=self.raw['id'], status='DELETED'))
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM knowledge_delete_receipts').fetchone()[0], 0)

    def test_proposal_delete_is_cas_bound_and_does_not_delete_source_notes(self):
        first = self.propose()
        second = self.propose(previous=first)
        self.rejected(409, 'REVISION_CONFLICT',
            lambda: self.store.delete_proposal(first['rule_id'], first['version'], self.budget))
        result = self.store.delete_proposal(first['rule_id'], second['version'], self.budget)
        self.assertEqual(result['deleted_versions'], 2)
        self.assertEqual(self.store.list_proposals(self.budget), [])
        self.assertEqual(self.store.get_note(self.raw['id'], 'overview')['known'], self.note['known'])

    def test_deletion_receipt_contains_only_random_identity_and_actual_count(self):
        saved = self.propose()
        result = self.store.delete(self.raw['id'])
        with sqlite3.connect(self.path) as db:
            self.assertEqual([r[1] for r in db.execute('PRAGMA table_info(knowledge_delete_receipts)')],
                             ['id', 'deleted_count'])
            rows = db.execute('SELECT * FROM knowledge_delete_receipts').fetchall()
        self.assertEqual(rows, [(result['receipt_id'], 1)])
        self.assertEqual(uuid.UUID(hex=rows[0][0]).version, 4)
        self.assertNotIn(rows[0][0], (saved['rule_id'], saved['version'], self.raw['id']))
        self.assertNotIn(self.raw['id'], json.dumps(rows))
        self.assertNotIn(self.note['known'], json.dumps(rows))

    def test_source_delete_receipt_failure_rolls_back_entire_cascade(self):
        self.propose()
        before = self.state()
        with patch.object(self.store, '_receipt', side_effect=RuntimeError('injected receipt failure')):
            with self.assertRaises(RuntimeError):
                self.store.delete(self.raw['id'])
        self.assertEqual(self.state(), before)

    def test_proposal_delete_response_budget_failure_rolls_back(self):
        saved = self.propose()
        self.rejected(413, 'KNOWLEDGE_TOO_LARGE',
            lambda: self.store.delete_proposal(saved['rule_id'], saved['version'], 1))

    def test_list_and_exact_preview_are_read_only_and_show_actual_current(self):
        first = self.propose()
        second = self.propose(rule('다음 버전'), previous=first)
        before = self.state()
        rows = self.store.list_proposals(self.budget)
        self.assertEqual([(row['version'], row['current']) for row in rows],
                         [(second['version'], True), (first['version'], False)])
        self.assertEqual(rows[0]['supersedes'], first['version'])
        self.store.get_proposal(first['rule_id'], first['version'], max_bytes=self.budget)
        self.assertEqual(self.state(), before)

    def test_unknown_or_absent_exact_version_returns_404(self):
        saved = self.propose()
        self.rejected(404, 'KNOWLEDGE_RULE_NOT_FOUND',
            lambda: self.store.get_proposal(saved['rule_id'], 'a'*32, max_bytes=self.budget))
        self.rejected(404, 'KNOWLEDGE_RULE_NOT_FOUND',
            lambda: self.store.get_proposal('b'*32, max_bytes=self.budget))

    def test_client_cannot_promote_status_or_spoof_server_fields(self):
        for field, value in (('review_state', 'REVIEWED'), ('coaching_enabled', True),
                             ('rule_id', 'a'*32), ('source_refs', []), ('version', 'b'*32)):
            values = rule()
            values[field] = value
            self.rejected(422, 'INVALID_KNOWLEDGE_RULE', lambda values=values: self.propose(values))

    def test_manual_fields_require_explicit_nonblank_values_and_strict_types(self):
        for field in ('author', 'claim', 'mechanism', 'patch_range'):
            for value in ('', ' ', None, 1, True, 'x'*2001, '\ud800'):
                values = rule()
                values[field] = value
                self.rejected(422, 'INVALID_KNOWLEDGE_RULE', lambda values=values: self.propose(values))
        values = rule()
        del values['applicability']['context']
        self.rejected(422, 'INVALID_KNOWLEDGE_RULE', lambda: self.propose(values))
        for value in ('UNKNOWN', None, [None], [1], ['']):
            values = rule()
            values['counterexamples'] = value
            self.rejected(422, 'INVALID_KNOWLEDGE_RULE', lambda values=values: self.propose(values))

    def test_2000_unicode_characters_are_allowed_without_invented_numeric_stats(self):
        values = rule('한'*2000)
        saved = self.propose(values)
        self.assertEqual(saved['claim'], '한'*2000)
        self.assertEqual(set(saved), RULE_FIELDS | {'schema_version', 'rule_id', 'version', 'source_refs',
                                                   'review_state', 'supersedes', 'coaching_enabled'})

    def test_response_budget_counts_actual_default_json_utf8_bytes(self):
        saved = self.propose()
        size = len(json.dumps(saved, ensure_ascii=False, allow_nan=False).encode())
        self.assertEqual(self.store.get_proposal(saved['rule_id'], max_bytes=size), saved)
        self.rejected(413, 'KNOWLEDGE_TOO_LARGE',
            lambda: self.store.get_proposal(saved['rule_id'], max_bytes=size-1))
        self.rejected(413, 'KNOWLEDGE_TOO_LARGE', lambda: self.propose(budget=size-1))
        self.assertIsInstance(self.propose(budget=size), dict)
        rows = self.store.list_proposals(self.budget)
        list_size = len(json.dumps(rows, ensure_ascii=False, allow_nan=False).encode())
        self.assertEqual(self.store.list_proposals(list_size), rows)
        self.rejected(413, 'KNOWLEDGE_TOO_LARGE', lambda: self.store.list_proposals(list_size-1))

    def test_positive_exact_budget_is_mandatory(self):
        for budget in (0, -1, True, 1.0, None):
            self.rejected(422, 'INVALID_KNOWLEDGE_LIMIT', lambda budget=budget: self.propose(budget=budget)
                if budget is not None else self.store.propose(rule(), self.source, max_bytes=None))

    def test_stored_report_cap_rolls_back_large_proposal(self):
        values = rule()
        values['counterexamples'] = ['한'*2000]*400
        self.rejected(413, 'REPORT_TOO_LARGE',
            lambda: self.propose(values, budget=4_000_000))

    def test_corrupted_payload_status_hash_or_columns_are_rejected_not_repaired(self):
        saved = self.propose()
        with sqlite3.connect(self.path) as db:
            original = db.execute('SELECT payload FROM knowledge_rules').fetchone()[0]
        for mutate in (lambda report: report.update(review_state='REVIEWED'),
                       lambda report: report['source_refs'][0].update(note_sha256='0'*64),
                       lambda report: report.update(supersedes='a'*32),
                       lambda report: report.update(coaching_enabled=True)):
            corrupted = strict_copy = copy.deepcopy(saved)
            mutate(corrupted)
            with sqlite3.connect(self.path) as db:
                db.execute('UPDATE knowledge_rules SET payload=?', (_json(strict_copy),))
            self.rejected(409, 'INVALID_STORED_KNOWLEDGE', self.validate)
            with sqlite3.connect(self.path) as db:
                db.execute('UPDATE knowledge_rules SET payload=?', (original,))
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE knowledge_rules SET status='REVIEWED'")
        self.rejected(409, 'INVALID_STORED_KNOWLEDGE', self.validate)

    def test_mutated_saved_source_note_invalidates_hash_binding(self):
        self.propose()
        with sqlite3.connect(self.path) as db:
            db.execute('UPDATE note_history SET payload=? WHERE resource_id=?',
                       (_json(dict(self.note, known='덮어쓴 과거 노트')), self.raw['id']))
        self.rejected(409, 'INVALID_STORED_KNOWLEDGE', self.validate)
        self.rejected(409, 'INVALID_STORED_KNOWLEDGE', lambda: KnowledgeStore(self.path))

    def test_pure_validator_rejects_fork_and_disconnected_cycle(self):
        first = self.propose()
        second = self.propose(previous=first)
        fork = dict(second, version=uuid.uuid4().hex)
        binding = fork['source_refs'][0]
        with sqlite3.connect(self.path) as db:
            db.execute('INSERT INTO knowledge_rules VALUES (?,?,?,?,?,?,?,?)',
                (fork['rule_id'], fork['version'], 'EXPLORATORY', _json(fork), binding['resource_id'],
                 binding['anchor'], binding['note_revision'], first['version']))
        self.rejected(409, 'INVALID_STORED_KNOWLEDGE', self.validate)
        with sqlite3.connect(self.path) as db:
            db.execute('DELETE FROM knowledge_rules WHERE version=?', (fork['version'],))
            cyclic = dict(first, supersedes=second['version'])
            db.execute('UPDATE knowledge_rules SET parent_version=?,payload=? WHERE version=?',
                       (second['version'], _json(cyclic), first['version']))
        self.rejected(409, 'INVALID_STORED_KNOWLEDGE', self.validate)

    def test_pure_validator_rejects_nonpositive_or_identifying_receipt_shape(self):
        with sqlite3.connect(self.path) as db:
            db.execute('INSERT INTO knowledge_delete_receipts VALUES (?,?)', (uuid.uuid4().hex, 0))
        self.rejected(409, 'INVALID_STORED_KNOWLEDGE', self.validate)

    def test_readonly_connection_validators_make_no_writes(self):
        self.propose()
        before = self.state()
        with sqlite3.connect(self.path.as_uri()+'?mode=ro', uri=True) as db:
            db.row_factory = sqlite3.Row
            validate_schema(db)
            validate_knowledge_content(db)
        self.assertEqual(self.state(), before)


if __name__ == '__main__':
    unittest.main()

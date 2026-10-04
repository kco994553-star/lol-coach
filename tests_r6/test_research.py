import concurrent.futures
import sqlite3
import tempfile
from pathlib import Path
import unittest

from coach_v1.research import ResearchStore, FIELDS
from coach_v1.storage import ServiceError


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'research.sqlite'
        self.store = ResearchStore(self.path)
        self.report = {'candidates': [{'cue_index': 2}, {'cue_index': 8}], 'coaching_enabled': False}
        self.resource = self.store.add('VIDEO', '연습', self.report)
        self.rid = self.resource['id']
        self.note = {field: '수동 메모 '+field for field in FIELDS}

    def error(self, code, fn):
        with self.assertRaises(ServiceError) as raised:
            fn()
        self.assertEqual(raised.exception.code, code)

    def test_idempotence_canonical_order_title_excluded(self):
        reversed_report = dict(reversed(list(self.report.items())))
        self.assertEqual(self.store.add('VIDEO', '다른 제목', reversed_report), self.resource)
        self.assertNotEqual(self.store.add('MATCH', '같은 데이터', self.report)['id'], self.rid)
        self.assertEqual(len(self.store.list()), 2)
        self.assertNotIn('report', self.store.list()[0])

    def test_note_defaults_revision_history_restart(self):
        self.assertEqual(self.store.get_note(self.rid, 'overview')['revision'], 0)
        self.assertTrue(all(self.store.get_note(self.rid, '2')[f] == '' for f in FIELDS))
        first = self.store.put_note(self.rid, '2', self.note, 0)
        self.assertEqual(first['revision'], 1)
        changed = dict(self.note, known='수정')
        self.store.put_note(self.rid, '2', changed, 1)
        self.assertEqual(ResearchStore(self.path).get_note(self.rid, '2')['known'], '수정')
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM note_history').fetchone()[0], 2)
            self.assertIn('수동 메모 known', db.execute('SELECT payload FROM note_history WHERE revision=1').fetchone()[0])
        self.assertEqual(self.store.get_note(self.rid, 'overview')['revision'], 0)

    def test_concurrent_compare_and_swap(self):
        def save():
            try:
                return self.store.put_note(self.rid, 'overview', self.note, 0)['revision']
            except ServiceError as e:
                return e.code
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: save(), range(2)))
        self.assertCountEqual(results, [1, 'REVISION_CONFLICT'])

    def test_anchor_and_resource_checks(self):
        for anchor in ('3', '02', 2, '', True, '8.0'):
            self.error('INVALID_NOTE_ANCHOR', lambda: self.store.get_note(self.rid, anchor))
        match = self.store.add('MATCH', '경기', self.report)['id']
        self.error('INVALID_NOTE_ANCHOR', lambda: self.store.get_note(match, '2'))
        self.assertEqual(self.store.get_note(match, 'overview')['revision'], 0)
        self.error('RESOURCE_NOT_FOUND', lambda: self.store.get_note('missing', 'overview'))

    def test_invalid_payload_or_revision_no_partial_write(self):
        for payload in ({}, dict(self.note, extra='x'), dict(self.note, known=1), dict(self.note, known='x'*2001)):
            self.error('INVALID_NOTE', lambda: self.store.put_note(self.rid, 'overview', payload, 0))
        for revision in (True, -1, 0.0, '0'):
            self.error('INVALID_REVISION', lambda: self.store.put_note(self.rid, 'overview', self.note, revision))
        self.assertEqual(self.store.get_note(self.rid, 'overview')['revision'], 0)

    def test_delete_cascades_history(self):
        self.store.put_note(self.rid, 'overview', self.note, 0)
        self.store.put_note(self.rid, '2', self.note, 0)
        self.assertEqual(self.store.delete(self.rid)['status'], 'DELETED')
        self.error('RESOURCE_NOT_FOUND', lambda: self.store.get(self.rid))
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM note_history').fetchone()[0], 0)

    def test_incompatible_schema_refused_unchanged(self):
        with sqlite3.connect(self.path) as db:
            db.execute('PRAGMA user_version=9')
        self.error('INCOMPATIBLE_RESEARCH_SCHEMA', lambda: ResearchStore(self.path))
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM resources').fetchone()[0], 1)
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 9)

    def test_foreign_or_wrong_shape_database_refused(self):
        path = Path(self.temp.name)/'foreign.sqlite'
        with sqlite3.connect(path) as db:
            db.execute('CREATE TABLE other (id TEXT)')
        self.error('INCOMPATIBLE_RESEARCH_SCHEMA', lambda: ResearchStore(path))
        with sqlite3.connect(self.path) as db:
            db.execute('ALTER TABLE resources ADD COLUMN mismatch TEXT')
        self.error('INCOMPATIBLE_RESEARCH_SCHEMA', lambda: ResearchStore(self.path))

    def test_non_json_reports_and_titles_rejected(self):
        for report in ({'x': float('nan')}, {'x': object()}, []):
            self.error('INVALID_REPORT', lambda: self.store.add('VIDEO', 'x', report))
        self.error('INVALID_TITLE', lambda: self.store.add('VIDEO', '', {}))
        self.error('INVALID_RESOURCE_KIND', lambda: self.store.add('video', 'x', {}))


if __name__ == '__main__':
    unittest.main()

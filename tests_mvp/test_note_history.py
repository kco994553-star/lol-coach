"""Synthetic, isolated Research data; historical reads are not real coaching evidence."""
import json
import sqlite3
import tempfile
from pathlib import Path
import unittest

from coach_v1.note_history import note_history, note_revision
from coach_v1.research import FIELDS, ResearchStore
from coach_v1.storage import ServiceError


class NoteHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'research.sqlite'
        self.store = ResearchStore(self.path)
        self.raw = self.store.add('RAW_DIAGNOSTIC', '합성 진단', {'coaching_enabled': False})
        self.video = self.store.add('VIDEO', '합성 영상', {'coaching_enabled': False,
            'candidates': [{'cue_index': 0}, {'cue_index': 2}]})
        self.rid = self.raw['id']
        self.first = dict(known='처음 확인한 근거 😀', intention='처음 의도', alternative='대안', outcome='나중 결과')
        self.second = dict(self.first, known='두 번째 수정', intention='새 의도')
        self.third = dict(self.second, known='세 번째 현재 노트')
        self.budget = 100000

    def saved(self, rid=None, anchor='overview'):
        target = self.rid if rid is None else rid
        for expected, note in enumerate((self.first, self.second, self.third)):
            self.store.put_note(target, anchor, note, expected)

    def state(self):
        with sqlite3.connect(self.path) as db:
            return (db.execute('PRAGMA user_version').fetchone()[0],
                db.execute('SELECT * FROM resources ORDER BY id').fetchall(),
                db.execute('SELECT * FROM note_history ORDER BY resource_id,anchor,revision').fetchall())

    def rejected(self, status, code, function):
        before = self.state()
        with self.assertRaises(ServiceError) as caught:
            function()
        self.assertEqual((caught.exception.status, caught.exception.code), (status, code))
        self.assertEqual(self.state(), before)

    def test_unsaved_note_has_no_invented_revision(self):
        before = self.state()
        self.assertEqual(note_history(self.store, self.rid, 'overview', self.budget),
            dict(resource_id=self.rid, anchor='overview', current_revision=0,
                revision_count=0, revisions=[], read_only=True))
        self.assertEqual(self.state(), before)
        self.rejected(404, 'NOTE_REVISION_NOT_FOUND',
            lambda: note_revision(self.store, self.rid, 'overview', '1', self.budget))

    def test_saved_history_is_actual_descending_ids(self):
        self.saved()
        self.assertEqual(note_history(self.store, self.rid, 'overview', self.budget),
            dict(resource_id=self.rid, anchor='overview', current_revision=3,
                revision_count=3, revisions=[3, 2, 1], read_only=True))

    def test_preview_old_revision_retains_exact_unicode_values(self):
        self.saved()
        result = note_revision(self.store, self.rid, 'overview', '1', self.budget)
        self.assertEqual(result, dict(resource_id=self.rid, anchor='overview', revision=1,
            current_revision=3, note=self.first, read_only=True))
        self.assertNotEqual(result['note'], self.third)

    def test_preview_latest_is_exact_saved_row(self):
        self.saved()
        result = note_revision(self.store, self.rid, 'overview', '3', self.budget)
        self.assertEqual(result['note'], self.third)
        self.assertEqual((result['revision'], result['current_revision']), (3, 3))

    def test_read_only_keeps_rows_latest_and_cas_target(self):
        self.saved()
        before = self.state()
        note_history(self.store, self.rid, 'overview', self.budget)
        note_revision(self.store, self.rid, 'overview', '1', self.budget)
        self.assertEqual(self.state(), before)
        self.assertEqual(self.store.get_note(self.rid, 'overview')['revision'], 3)
        saved = self.store.put_note(self.rid, 'overview', dict(self.third, known='新しいノート'), 3)
        self.assertEqual(saved['revision'], 4)
        self.assertEqual(note_revision(self.store, self.rid, 'overview', '1', self.budget)['note'], self.first)
        self.rejected(409, 'REVISION_CONFLICT',
            lambda: self.store.put_note(self.rid, 'overview', self.third, 3))

    def test_video_overview_and_actual_zero_or_two_cue_are_distinct(self):
        self.saved(self.video['id'], '2')
        self.store.put_note(self.video['id'], '0', dict(self.first, known='cue zero'), 0)
        self.store.put_note(self.video['id'], 'overview', dict(self.first, known='overview'), 0)
        self.assertEqual(note_history(self.store, self.video['id'], '2', self.budget)['revisions'], [3, 2, 1])
        self.assertEqual(note_revision(self.store, self.video['id'], '0', '1', self.budget)['note']['known'], 'cue zero')
        self.assertEqual(note_revision(self.store, self.video['id'], 'overview', '1', self.budget)['note']['known'], 'overview')

    def test_anchor_rules_are_existing_rules(self):
        for anchor in ('0', '2', '', None, True):
            self.rejected(422, 'INVALID_NOTE_ANCHOR',
                lambda anchor=anchor: note_history(self.store, self.rid, anchor, self.budget))
        for anchor in ('1', '02', '+2', '2.0', 2, '', True):
            self.rejected(422, 'INVALID_NOTE_ANCHOR',
                lambda anchor=anchor: note_revision(self.store, self.video['id'], anchor, '1', self.budget))

    def test_missing_resource_fails_for_both_reads(self):
        missing = 'a' * 64
        self.rejected(404, 'RESOURCE_NOT_FOUND', lambda: note_history(self.store, missing, 'overview', self.budget))
        self.rejected(404, 'RESOURCE_NOT_FOUND', lambda: note_revision(self.store, missing, 'overview', '1', self.budget))

    def test_valid_but_missing_revision_is_404(self):
        self.saved()
        self.rejected(404, 'NOTE_REVISION_NOT_FOUND',
            lambda: note_revision(self.store, self.rid, 'overview', '4', self.budget))

    def test_revision_requires_canonical_positive_decimal_string(self):
        self.saved()
        for revision in (None, True, False, 1, 1.0, '', '0', '02', '+1', '-1', '1.0', ' 1', '1 ', '١'):
            self.rejected(422, 'INVALID_NOTE_REVISION',
                lambda revision=revision: note_revision(self.store, self.rid, 'overview', revision, self.budget))

    def test_unrepresentable_positive_revision_is_404_without_overflow(self):
        for revision in ('9223372036854775808', '1' + '0' * 5000):
            self.rejected(404, 'NOTE_REVISION_NOT_FOUND',
                lambda revision=revision: note_revision(self.store, self.rid, 'overview', revision, self.budget))

    def test_gaps_do_not_generate_missing_versions(self):
        self.saved()
        with sqlite3.connect(self.path) as db:
            db.execute('DELETE FROM note_history WHERE resource_id=? AND revision=2', (self.rid,))
        before = self.state()
        result = note_history(self.store, self.rid, 'overview', self.budget)
        self.assertEqual((result['current_revision'], result['revision_count'], result['revisions']), (3, 2, [3, 1]))
        self.assertEqual(self.state(), before)
        self.rejected(404, 'NOTE_REVISION_NOT_FOUND',
            lambda: note_revision(self.store, self.rid, 'overview', '2', self.budget))

    def test_source_deletion_removes_history_no_read_resurrection(self):
        self.saved()
        self.store.delete(self.rid)
        self.rejected(404, 'RESOURCE_NOT_FOUND', lambda: note_history(self.store, self.rid, 'overview', self.budget))
        self.rejected(404, 'RESOURCE_NOT_FOUND', lambda: note_revision(self.store, self.rid, 'overview', '1', self.budget))

    def test_exact_preview_utf8_budget_boundary(self):
        self.saved()
        result = note_revision(self.store, self.rid, 'overview', '1', self.budget)
        encoded = json.dumps(result, ensure_ascii=False, allow_nan=False).encode('utf-8')
        self.assertGreater(len(encoded), len(json.dumps(result, ensure_ascii=False)))
        self.assertEqual(note_revision(self.store, self.rid, 'overview', '1', len(encoded)), result)
        self.rejected(413, 'NOTE_HISTORY_TOO_LARGE',
            lambda: note_revision(self.store, self.rid, 'overview', '1', len(encoded) - 1))

    def test_exact_index_budget_boundary_no_truncation(self):
        self.saved()
        result = note_history(self.store, self.rid, 'overview', self.budget)
        encoded = json.dumps(result, ensure_ascii=False, allow_nan=False).encode('utf-8')
        self.assertEqual(note_history(self.store, self.rid, 'overview', len(encoded)), result)
        self.rejected(413, 'NOTE_HISTORY_TOO_LARGE',
            lambda: note_history(self.store, self.rid, 'overview', len(encoded) - 1))
        self.rejected(413, 'NOTE_HISTORY_TOO_LARGE', lambda: note_history(self.store, self.rid, 'overview', 1))

    def test_budget_is_exact_positive_operational_integer(self):
        for budget in (None, True, False, '1000', 1.0, 0, -1):
            self.rejected(422, 'INVALID_NOTE_HISTORY_LIMIT',
                lambda budget=budget: note_history(self.store, self.rid, 'overview', budget))
            self.rejected(422, 'INVALID_NOTE_HISTORY_LIMIT',
                lambda budget=budget: note_revision(self.store, self.rid, 'overview', '1', budget))

    def test_invalid_saved_payload_fails_closed_without_mutation(self):
        self.saved()
        invalid = [json.dumps({}), json.dumps(dict(self.first, known=1)),
            json.dumps(dict(self.first, extra='x')), json.dumps(dict(self.first, known='x' * 2001)),
            'not json', '{"known":"x","known":"y","intention":"","alternative":"","outcome":""}',
            json.dumps(dict(self.first, known='\ud800'))]
        for payload in invalid:
            with sqlite3.connect(self.path) as db:
                db.execute('UPDATE note_history SET payload=? WHERE resource_id=? AND revision=1', (payload, self.rid))
            self.rejected(409, 'INVALID_STORED_NOTE',
                lambda: note_revision(self.store, self.rid, 'overview', '1', self.budget))

    def test_invalid_stored_revision_fails_without_rewriting_it(self):
        with sqlite3.connect(self.path) as db:
            db.execute('INSERT INTO note_history VALUES (?,?,?,?)',
                (self.rid, 'overview', 0, json.dumps(self.first)))
        self.rejected(409, 'INVALID_STORED_NOTE', lambda: note_history(self.store, self.rid, 'overview', self.budget))

    def test_response_does_not_invent_author_or_timestamps(self):
        self.saved()
        index = note_history(self.store, self.rid, 'overview', self.budget)
        preview = note_revision(self.store, self.rid, 'overview', '1', self.budget)
        self.assertEqual(set(index), {'resource_id', 'anchor', 'current_revision', 'revision_count', 'revisions', 'read_only'})
        self.assertEqual(set(preview), {'resource_id', 'anchor', 'revision', 'current_revision', 'note', 'read_only'})
        self.assertEqual(set(preview['note']), set(FIELDS))


if __name__ == '__main__':
    unittest.main()

"""Authenticated read-only history routes against real temporary SQLite."""
import json
import unittest

from coach_v1.server import Limits
from tests_r4 import test_http as helpers


class NoteHistoryHTTPTests(unittest.TestCase):
    setUp = helpers.HTTPTests.setUp
    tearDown = helpers.HTTPTests.tearDown
    call = helpers.HTTPTests.call

    def resource(self, kind='official_sample'):
        status, resource, _ = self.call('/dev/v1/research', 'POST',
                                       {'source_type': kind, 'title': 'history test'})
        self.assertEqual(status, 201)
        return resource

    def path(self, rid, anchor='overview'):
        return '/dev/v1/research/' + rid + '/notes/' + anchor

    def test_empty_and_exact_saved_versions_are_read_only(self):
        r = self.resource(); path = self.path(r['id'])
        status, empty, _ = self.call(path + '/history')
        self.assertEqual(status, 200)
        self.assertEqual(empty, dict(resource_id=r['id'], anchor='overview',
                         current_revision=0, revision_count=0, revisions=[], read_only=True))
        notes = [dict(known='근거 '+str(n)+' \uFFFD 😀', intention='의도',
                      alternative='대기', outcome='사후 결과') for n in (1, 2)]
        for expected, note in enumerate(notes):
            self.assertEqual(self.call(path, 'PUT', {'note': note,
                             'expected_revision': expected})[0], 200)
        self.assertEqual(self.call(path + '/history')[1]['revisions'], [2, 1])
        old = self.call(path + '/revisions/1')[1]
        self.assertEqual(old, dict(resource_id=r['id'], anchor='overview', revision=1,
                         current_revision=2, note=notes[0], read_only=True))
        self.assertEqual(self.call(path)[1]['revision'], 2)
        self.assertEqual(self.call(path)[1]['known'], notes[1]['known'])
        self.assertFalse(self.call('/dev/v1/research/'+r['id'])[1]['report']['coaching_enabled'])

    def test_auth_host_origin_applies_to_both_routes(self):
        rid = self.resource()['id']; base = self.path(rid)
        for suffix in ('/history', '/revisions/1'):
            path = base+suffix
            self.assertEqual(self.call(path, auth=False)[0], 401)
            self.assertEqual(self.call(path, extra={'Authorization': 'Bearer wrong'})[0], 401)
            self.assertEqual(self.call(path, extra={'Host': 'evil.test'})[0], 403)
            self.assertEqual(self.call(path, extra={'Origin': 'https://evil.test'})[0], 403)

    def test_revision_grammar_missing_and_unsupported_writes(self):
        path = self.path(self.resource()['id'])
        for value in ('0', '01', '+1', '-1', 'true', '1.0'):
            self.assertEqual(self.call(path+'/revisions/'+value)[0], 422, value)
        for value in ('1', '9223372036854775808', '9'*100):
            self.assertEqual(self.call(path+'/revisions/'+value)[0], 404, value)
        for suffix in ('/history', '/revisions/1'):
            self.assertEqual(self.call(path+suffix, 'PUT', {})[0], 404)
        self.assertEqual(self.call(path+'/history?revision=1')[0], 400)

    def test_anchor_validation_and_deletion(self):
        raw = self.resource(); video = self.resource('video_example')
        anchor = str(video['report']['candidates'][0]['cue_index'])
        self.assertEqual(self.call(self.path(video['id'], anchor)+'/history')[0], 200)
        for rid, a in ((raw['id'], anchor), (video['id'], '999999'), (video['id'], '00')):
            self.assertEqual(self.call(self.path(rid, a)+'/history')[0], 422)
        self.assertEqual(self.call('/dev/v1/research/'+video['id'], 'DELETE')[0], 200)
        for suffix in ('/history', '/revisions/1'):
            self.assertEqual(self.call(self.path(video['id'], anchor)+suffix)[0], 404)

    def test_utf8_response_cap_is_explicit_without_truncation(self):
        path = self.path(self.resource()['id'])
        note = dict(known='😀'*100, intention='', alternative='', outcome='')
        self.assertEqual(self.call(path, 'PUT', {'note': note, 'expected_revision': 0})[0], 200)
        original = self.server.limits
        self.server.limits = Limits(100, original.observations, original.actions,
                                   original.scenarios, original.comparisons, original.pending_jobs)
        for suffix in ('/history', '/revisions/1'):
            status, body, _ = self.call(path+suffix)
            self.assertEqual(status, 413)
            self.assertEqual(body['error_code'], 'NOTE_HISTORY_TOO_LARGE')
        self.server.limits = original
        self.assertEqual(self.call(path+'/revisions/1')[1]['note'], note)
        self.assertEqual(self.call(path)[1]['revision'], 1)


if __name__ == '__main__':
    unittest.main()

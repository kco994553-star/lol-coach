"""Actual loopback HTTP and SQLite manual-capture boundary tests.

No engine, transport, storage, or schema functions are mocked. Null/unknown input
and expected hashes are independent literals, not built by production helpers.
"""
import copy
import hashlib
import http.client
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest

from coach_v1.server import Limits, Workbench


TOKEN = 'draft-http-private-token-' + 't' * 32
PREFIX = '/dev/v1/draft-captures'


def partial_capture():
    return {
        'title': '개인 픽창 · 수동 기록', 'phase': None, 'patch': None,
        'observed_at': None,
        'visible_picks': [{'side': 'ALLY', 'slot': 1, 'champion': '아리'},
                          {'side': 'ENEMY', 'slot': 5, 'champion': None}],
        'visible_bans': [{'side': 'ENEMY', 'slot': 1, 'champion': 'Yasuo'}],
        'role_assignments': [{'side': 'ALLY', 'slot': 1, 'role': None,
                              'uncertainty': 'UNKNOWN · 아직 역할을 알 수 없음'}],
        'source': {'author': '개인 운영자', 'perspective': 'UNKNOWN',
                   'description': '내가 직접 입력한 픽창 기록; 자동 검증 자료 아님'},
    }


class DraftHTTPTests(unittest.TestCase):
    """Each test names an observable missing or unsafe boundary behavior."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / 'private.sqlite'
        self.key_number = 0
        self.start_server()

    def start_server(self, body_bytes=1_000_000):
        self.server = Workbench(self.db, TOKEN, Limits(body_bytes, 100, 24, 16, 512, 8))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def tearDown(self):
        self.stop_server()
        self.temp.cleanup()

    def call(self, path=PREFIX, method='GET', body=None, headers=None, auth=True, raw=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        request_headers = {'Authorization': 'Bearer ' + TOKEN} if auth else {}
        if body is not None or raw is not None:
            request_headers['Content-Type'] = 'application/json'
            data = raw if raw is not None else json.dumps(body, ensure_ascii=False).encode('utf-8')
        else:
            data = None
        if headers:
            request_headers.update(headers)
        connection.request(method, path, data, request_headers)
        response = connection.getresponse()
        encoded = response.read()
        result = (response.status, json.loads(encoded), dict(response.getheaders()))
        connection.close()
        return result

    def create(self, capture=None):
        value = partial_capture() if capture is None else capture
        status, record, _ = self.call(method='POST', body={'capture': value},
                                      headers=self.save_headers('create'))
        self.assertEqual(status, 201, record)
        return value, record

    def save_headers(self, prefix='draft-test'):
        self.key_number += 1
        return {'Idempotency-Key': f'{prefix}-{self.key_number}'}

    def test_partial_create_preserves_null_and_unverified_provenance(self):
        value, record = self.create()
        self.assertEqual(record['capture'], value)
        self.assertEqual(record['schema_version'], 'mvp.manual-draft.v1')
        self.assertRegex(record['id'], r'^[0-9a-f]{32}$')
        self.assertRegex(record['session_id'], r'^[0-9a-f]{32}$')
        self.assertEqual(record['revision'], 1)
        self.assertIsNone(record['parent_id'])
        self.assertEqual(record['validation_state'], 'UNVERIFIED')
        self.assertEqual(record['adapter_capability'], {'automatic_collection': 'UNAVAILABLE', 'manual_capture': 'AVAILABLE'})
        self.assertEqual(record['gameplan_status'], 'NOT_GENERATED')
        self.assertIs(record['coaching_enabled'], False)
        canonical = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')
        self.assertEqual(record['input_sha256'], hashlib.sha256(canonical).hexdigest())
        self.assertRegex(record['received_at'], r'^\d{4}-\d{2}-\d{2}T.*(?:Z|\+00:00)$')

    def test_idempotent_create_and_update_replay_exact_success_after_restart(self):
        value = partial_capture()
        create_headers = {'Idempotency-Key': 'draft-create-response-loss'}
        status, first, _ = self.call(method='POST', body={'capture': value}, headers=create_headers)
        self.assertEqual(status, 201, first)

        self.stop_server()
        self.start_server()
        self.assertEqual(self.call(method='POST', body={'capture': value}, headers=create_headers)[:2],
                         (201, first))
        self.assertEqual(self.call()[1], [first])

        changed = copy.deepcopy(value)
        changed['title'] = '응답 유실 뒤 동일 저장 재시도'
        update = {'capture': changed, 'expected_revision': 1}
        update_headers = {'Idempotency-Key': 'draft-update-response-loss'}
        status, second, _ = self.call(PREFIX+'/'+first['session_id'], 'PUT', update,
                                      update_headers)
        self.assertEqual(status, 200, second)

        self.stop_server()
        self.start_server()
        self.assertEqual(self.call(PREFIX+'/'+first['session_id'], 'PUT', update,
                                   update_headers)[:2], (200, second))
        self.assertEqual(self.call(PREFIX+'/'+first['session_id']+'/history')[1]['revisions'], [1, 2])

    def test_same_idempotency_key_different_request_conflicts_and_new_key_keeps_cas(self):
        value = partial_capture()
        create_headers = {'Idempotency-Key': 'draft-create-conflict'}
        status, first, _ = self.call(method='POST', body={'capture': value}, headers=create_headers)
        self.assertEqual(status, 201, first)

        different = copy.deepcopy(value)
        different['title'] = '같은 키의 다른 생성 요청'
        status, problem, _ = self.call(method='POST', body={'capture': different},
                                       headers=create_headers)
        self.assertEqual((status, problem.get('error_code')), (409, 'IDEMPOTENCY_CONFLICT'))
        self.assertEqual(self.call()[1], [first])

        changed = copy.deepcopy(value)
        changed['title'] = '첫 수정'
        path = PREFIX+'/'+first['session_id']
        update_headers = {'Idempotency-Key': 'draft-update-conflict'}
        status, second, _ = self.call(path, 'PUT', {'capture': changed, 'expected_revision': 1},
                                      update_headers)
        self.assertEqual(status, 200, second)

        other = copy.deepcopy(value)
        other['title'] = '같은 키의 다른 수정 요청'
        status, problem, _ = self.call(path, 'PUT', {'capture': other, 'expected_revision': 1},
                                       update_headers)
        self.assertEqual((status, problem.get('error_code')), (409, 'IDEMPOTENCY_CONFLICT'))
        status, problem, _ = self.call(path, 'PUT', {'capture': other, 'expected_revision': 1},
                                       {'Idempotency-Key': 'draft-update-new-key'})
        self.assertEqual((status, problem.get('error_code')), (409, 'REVISION_CONFLICT'))
        self.assertEqual(self.call(path)[1], second)
        self.assertEqual(self.call(path+'/history')[1]['revisions'], [1, 2])

    def test_draft_saves_require_one_valid_idempotency_key_without_writing(self):
        value = partial_capture()
        for headers in (None, {'Idempotency-Key': 'bad/key'}):
            with self.subTest(headers=headers):
                status, problem, _ = self.call(method='POST', body={'capture': value},
                                               headers=headers)
                self.assertEqual((status, problem.get('error_code')),
                                 (422, 'IDEMPOTENCY_KEY_REQUIRED'))
        raw = json.dumps({'capture': value}, ensure_ascii=False).encode('utf-8')
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        connection.putrequest('POST', PREFIX)
        connection.putheader('Authorization', 'Bearer '+TOKEN)
        connection.putheader('Content-Type', 'application/json')
        connection.putheader('Content-Length', str(len(raw)))
        connection.putheader('Idempotency-Key', 'duplicate-a')
        connection.putheader('Idempotency-Key', 'duplicate-b')
        connection.endheaders(raw)
        response = connection.getresponse()
        problem = json.loads(response.read())
        self.assertEqual((response.status, problem.get('error_code')),
                         (422, 'IDEMPOTENCY_KEY_REQUIRED'))
        connection.close()
        self.assertEqual(self.call()[1], [])

        _, first, _ = self.call(method='POST', body={'capture': value},
                                headers={'Idempotency-Key': 'valid-create-key'})
        for headers in (None, {'Idempotency-Key': 'bad/key'}):
            with self.subTest(method='PUT', headers=headers):
                status, problem, _ = self.call(PREFIX+'/'+first['session_id'], 'PUT',
                    {'capture': dict(value, title='수정'), 'expected_revision': 1}, headers)
                self.assertEqual((status, problem.get('error_code')),
                                 (422, 'IDEMPOTENCY_KEY_REQUIRED'))
        self.assertEqual(self.call(PREFIX+'/'+first['session_id'])[1], first)

    def test_list_current_and_immutable_history_keep_exact_old_input(self):
        original, first = self.create()
        cid = first['session_id']
        changed = copy.deepcopy(original)
        changed['title'] = '정정한 픽창'
        changed['visible_picks'][0]['champion'] = 'Lux'
        status, second, _ = self.call(PREFIX+'/'+cid, 'PUT',
                                      {'capture': changed, 'expected_revision': 1},
                                      self.save_headers('history-update'))
        self.assertEqual(status, 200, second)
        self.assertEqual(second['revision'], 2)
        self.assertEqual(second['parent_id'], first['id'])
        self.assertEqual(self.call(PREFIX+'/'+cid)[1], second)
        self.assertEqual(self.call(PREFIX+'/'+cid+'/revisions/1')[1], first)
        status, history, _ = self.call(PREFIX+'/'+cid+'/history')
        self.assertEqual(status, 200, history)
        self.assertEqual(history['session_id'], cid)
        self.assertEqual(history['current_revision'], 2)
        self.assertEqual(history['revision_count'], 2)
        self.assertEqual(history['revisions'], [1, 2])
        self.assertEqual(self.call()[1][0], second)
        self.assertEqual(self.call(PREFIX+'/'+cid+'/revisions/1')[1]['capture'], original)

    def test_stale_update_and_delete_do_not_overwrite_current_or_history(self):
        value, first = self.create()
        path = PREFIX+'/'+first['session_id']
        newer = dict(value, title='서버 최신 정정')
        status, second, _ = self.call(path, 'PUT',
                                      {'capture': newer, 'expected_revision': 1},
                                      self.save_headers('current-update'))
        self.assertEqual(status, 200, second)
        for method, body in [('PUT', {'capture': dict(value, title='오래된 초안'), 'expected_revision': 1}),
                             ('DELETE', {'expected_revision': 1})]:
            headers = self.save_headers('stale-update') if method == 'PUT' else None
            status, problem, _ = self.call(path, method, body, headers)
            self.assertEqual(status, 409, problem)
            self.assertEqual(problem['error_code'], 'REVISION_CONFLICT')
        self.assertEqual(self.call(path)[1], second)
        self.assertEqual(self.call(path+'/revisions/1')[1], first)
        self.assertEqual(self.call(path+'/history')[1]['revision_count'], 2)

    def test_capture_id_never_becomes_legacy_case_review_or_real_mode(self):
        value, record = self.create()
        cid = record['session_id']
        self.assertEqual(self.call('/dev/v1/sessions')[1], [])
        for suffix in ('', '/case', '/reviews'):
            self.assertEqual(self.call('/dev/v1/sessions/'+cid+suffix)[0], 404)
        self.assertEqual(self.call('/dev/v1/sessions/'+cid+'/reviews', 'POST', {'expected_revision': 1},
                                   {'Idempotency-Key': 'never-draft-review'})[0], 404)
        self.assertEqual(self.call('/dev/v1/sessions', 'POST', {'title': '실제', 'patch': 'x', 'mode': 'PRE_GAME'})[0], 422)
        status = self.call('/dev/v1/status')[1]
        self.assertEqual(status['mode'], 'SYNTHETIC_ONLY')
        self.assertIs(status['real_data_enabled'], False)
        self.assertEqual(self.call(PREFIX+'/'+cid)[1]['capture'], value)

    def test_auth_host_origin_and_same_site_protection_do_not_create(self):
        for auth, extra, expected in [(False, None, 401), (True, {'Authorization': 'Bearer wrong'}, 401),
                                      (True, {'Host': 'evil.test'}, 403), (True, {'Origin': 'https://evil.test'}, 403),
                                      (True, {'Sec-Fetch-Site': 'cross-site'}, 403)]:
            with self.subTest(expected=expected, headers=extra):
                headers = dict(extra or {}, **self.save_headers('rejected-request'))
                self.assertEqual(self.call(method='POST', body={'capture': partial_capture()},
                                           auth=auth, headers=headers)[0], expected)
        self.assertEqual(self.call()[1], [])

    def test_duplicate_json_keys_nonfinite_and_malformed_utf8_are_rejected(self):
        valid = json.dumps({'capture': partial_capture()}, ensure_ascii=False).encode('utf-8')
        for raw in (b'{"capture":{},"capture":{}}', b'{"capture":NaN}', b'{"capture":"\xff"}', b'{broken'):
            with self.subTest(raw=repr(raw)):
                self.assertEqual(self.call(method='POST', raw=raw)[0], 422)
        self.assertEqual(self.call()[1], [])
        self.assertEqual(self.call(method='POST', raw=valid,
                                   headers=self.save_headers('valid-raw'))[0], 201)

    def test_exact_capture_fields_reject_injected_verification_and_real_modes(self):
        for field, injected in [('validation_state', 'VERIFIED_DIRECT'), ('coaching_enabled', True),
                                ('mode', 'PRE_GAME'), ('confidence', 1.0), ('future_event', 'win')]:
            value = partial_capture()
            value[field] = injected
            with self.subTest(field=field):
                status, problem, _ = self.call(method='POST', body={'capture': value},
                                               headers=self.save_headers('invalid-field'))
                self.assertEqual(status, 422, problem)
                self.assertEqual(problem['error_code'], 'INVALID_DRAFT_CAPTURE')
        self.assertEqual(self.call()[1], [])

    def test_rows_reject_boolean_slot_duplicate_side_slot_and_observer_perspective(self):
        bad_rows = [([{'side': 'ALLY', 'slot': True, 'champion': 'Ahri'}], None),
                    ([{'side': 'ALLY', 'slot': 1, 'champion': 'Ahri'}, {'side': 'ALLY', 'slot': 1, 'champion': 'Lux'}], None),
                    ([{'side': 'ENEMY', 'slot': 6, 'champion': 'Ahri'}], None), (None, 'OBSERVER')]
        for rows, perspective in bad_rows:
            value = partial_capture()
            if rows is not None:
                value['visible_picks'] = rows
            if perspective:
                value['source']['perspective'] = perspective
            with self.subTest(rows=rows, perspective=perspective):
                self.assertEqual(self.call(method='POST', body={'capture': value},
                                           headers=self.save_headers('invalid-row'))[0], 422)
        self.assertEqual(self.call()[1], [])

    def test_declared_timezone_timestamp_preserved_and_naive_time_rejected(self):
        value = partial_capture()
        value['observed_at'] = '2026-10-05T15:20:30.123456+09:00'
        value['patch'] = '26.20'
        value['phase'] = 'PLAYER_DECLARED_PICK'
        value['source']['perspective'] = 'PLAYER'
        _, record = self.create(value)
        self.assertEqual(record['capture'], value)
        for bad in ('2026-10-05T15:20:30', 'yesterday', True, 123):
            invalid = dict(value, observed_at=bad)
            with self.subTest(timestamp=bad):
                self.assertEqual(self.call(method='POST', body={'capture': invalid},
                                           headers=self.save_headers('invalid-time'))[0], 422)
        self.assertEqual(len(self.call()[1]), 1)
        self.assertEqual(record['validation_state'], 'UNVERIFIED')

    def test_unknown_empty_arrays_survive_actual_server_restart(self):
        value = partial_capture()
        value.update(visible_picks=[], visible_bans=[], role_assignments=[])
        _, record = self.create(value)
        self.stop_server()
        self.start_server()
        status, loaded, _ = self.call(PREFIX+'/'+record['session_id'])
        self.assertEqual(status, 200, loaded)
        self.assertEqual(loaded, record)
        self.assertEqual(loaded['capture'], value)

    def test_concurrent_same_revision_writers_commit_one_history_successor(self):
        value, first = self.create()
        cid = first['session_id']
        barrier = threading.Barrier(3)
        results = []
        def update(title):
            barrier.wait()
            results.append(self.call(PREFIX+'/'+cid, 'PUT',
                                     {'capture': dict(value, title=title), 'expected_revision': 1},
                                     {'Idempotency-Key': 'concurrent-'+hashlib.sha256(
                                         title.encode('utf-8')).hexdigest()[:24]}))
        threads = [threading.Thread(target=update, args=(title,)) for title in ('수정 A', '수정 B')]
        for thread in threads:
            thread.start()
        barrier.wait()
        for thread in threads:
            thread.join(timeout=5)
            self.assertFalse(thread.is_alive())
        self.assertEqual(sorted(row[0] for row in results), [200, 409])
        latest = self.call(PREFIX+'/'+cid)[1]
        self.assertEqual(latest['revision'], 2)
        self.assertEqual(latest['parent_id'], first['id'])
        self.assertEqual(self.call(PREFIX+'/'+cid+'/revisions/1')[1], first)
        self.assertEqual(self.call(PREFIX+'/'+cid+'/history')[1]['revision_count'], 2)

    def test_delete_physically_removes_current_and_all_snapshot_payloads(self):
        value, first = self.create()
        cid = first['session_id']
        self.assertEqual(self.call(PREFIX+'/'+cid, 'PUT',
                                   {'capture': dict(value, title='두 번째'), 'expected_revision': 1},
                                   self.save_headers('delete-setup'))[0], 200)
        status, deleted, _ = self.call(PREFIX+'/'+cid, 'DELETE', {'expected_revision': 2})
        self.assertEqual(status, 200, deleted)
        self.assertEqual(deleted, {'id': cid, 'status': 'DELETED', 'deleted_snapshots': 2})
        for suffix in ('', '/history', '/revisions/1', '/revisions/2'):
            self.assertEqual(self.call(PREFIX+'/'+cid+suffix)[0], 404)
        self.assertEqual(self.call()[1], [])
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM draft_captures').fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT count(*) FROM draft_snapshots').fetchone()[0], 0)

    def test_expected_revision_is_required_strict_integer_and_missing_revision_is_not_latest(self):
        value, record = self.create()
        path = PREFIX+'/'+record['session_id']
        for revision in (None, True, -1, '1', 1.0):
            with self.subTest(revision=revision):
                self.assertEqual(self.call(path, 'PUT',
                                           {'capture': value, 'expected_revision': revision},
                                           self.save_headers('invalid-revision'))[0], 422)
                self.assertEqual(self.call(path, 'DELETE', {'expected_revision': revision})[0], 422)
        self.assertEqual(self.call(path, 'DELETE', {})[0], 422)
        self.assertEqual(self.call(path+'/revisions/2')[0], 404)
        # Consistent with the established saved-note historical routes:
        # malformed/nonpositive grammar is invalid; missing positive is absent.
        for revision in ('0', '01', '+1', '-1', 'true', '1.0'):
            with self.subTest(historical_revision=revision):
                status, problem, _ = self.call(path+'/revisions/'+revision)
                self.assertEqual(status, 422, problem)
                self.assertEqual(problem['error_code'], 'INVALID_DRAFT_REVISION')
        self.assertEqual(self.call(path)[1], record)

    def test_content_length_cap_rejects_before_any_capture_write(self):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        connection.request('POST', PREFIX, headers={'Authorization': 'Bearer '+TOKEN,
                           'Content-Type': 'application/json', 'Content-Length': '1000001'})
        response = connection.getresponse()
        self.assertEqual(response.status, 413)
        response.read()
        connection.close()
        self.assertEqual(self.call()[1], [])


if __name__ == '__main__':
    unittest.main()

"""Real HTTP/SQLite review boundary; browser header fixtures are not human attestation."""
import copy
import hashlib
import sqlite3
from concurrent.futures import ThreadPoolExecutor
import unittest

from coach_v1.knowledge import KnowledgeStore
from coach_v1.storage import ServiceError
from coach_v1 import backup
from pathlib import Path
from tests_mvp import test_knowledge_http as helpers


class KnowledgeReviewTests(unittest.TestCase):
    setUp = helpers.KnowledgeHTTPTests.setUp
    tearDown = helpers.KnowledgeHTTPTests.tearDown
    call = helpers.KnowledgeHTTPTests.call
    source = helpers.KnowledgeHTTPTests.source
    proposal = helpers.KnowledgeHTTPTests.proposal
    base = helpers.KnowledgeHTTPTests.base

    def fixture(self):
        first = self.call(self.base, 'POST', self.proposal())[1]
        self.path = self.base + '/' + first['rule_id']
        self.browser = {'Origin': 'http://127.0.0.1:'+str(self.server.server_port), 'Sec-Fetch-Site': 'same-origin',
                        'Sec-Fetch-Mode': 'same-origin', 'Sec-Fetch-Dest': 'empty'}
        self.body = dict(selected_version=first['version'], expected_version=first['version'],
                         decision='REVIEWED', patch_range='26.20',
                         applicability=dict(champion='애쉬', role='원딜', matchup='케이틀린 상대',
                                            level='1~3', context='아군 서포터와 라인 진입'))
        return first

    def decide(self, body=None, headers=None):
        return self.call(self.path + '/decisions', 'POST', self.body if body is None else body,
                         extra=self.browser if headers is None else headers)

    def test_review_immutable_exact_source_hashes_and_restart(self):
        first = self.fixture()
        with sqlite3.connect(self.server.research.dbpath) as db:
            payload = db.execute('SELECT payload FROM knowledge_rules').fetchone()[0]
        status, saved, _ = self.decide()
        self.assertEqual(status, 201)
        self.assertEqual(saved['review_state'], 'REVIEWED')
        self.assertEqual(saved['source_refs'], first['source_refs'])
        self.assertEqual(saved['claim'], first['claim'])
        self.assertEqual(saved['patch_range'], '26.20')
        self.assertEqual(saved['applicability'], self.body['applicability'])
        self.assertEqual(saved['supersedes'], first['version'])
        self.assertNotEqual(saved['version'], first['version'])
        self.assertEqual(saved['review_decision'], dict(actor='USER_WEB',
            selected_version=first['version'], selected_payload_sha256=hashlib.sha256(payload.encode()).hexdigest()))
        self.assertFalse(saved['coaching_enabled'])
        self.assertEqual(self.call(self.path + '/versions/' + first['version'])[1], first)
        reopened = KnowledgeStore(self.server.research.dbpath)
        self.assertEqual(reopened.get_proposal(first['rule_id'], max_bytes=100000), saved)

    def test_reject_preserves_unknown_conditions(self):
        first = self.fixture()
        self.body.update(decision='REJECTED', patch_range=first['patch_range'],
                         applicability=first['applicability'])
        status, saved, _ = self.decide()
        self.assertEqual(status, 201)
        self.assertEqual(saved['review_state'], 'REJECTED')
        self.assertEqual(saved['source_refs'], first['source_refs'])
        self.assertFalse(saved['coaching_enabled'])

    def test_review_rejects_blank_unknown_missing_and_wrong_types_without_write(self):
        self.fixture()
        for value in ('', ' ', 'UNKNOWN', ' unknown ', '미확인', None, False, 26.20):
            b = copy.deepcopy(self.body); b['patch_range'] = value
            self.assertEqual(self.decide(b)[0], 422, repr(value))
            for field in self.body['applicability']:
                b = copy.deepcopy(self.body); b['applicability'][field] = value
                self.assertEqual(self.decide(b)[0], 422, (field, value))
        for key in ('patch_range', 'applicability'):
            b = copy.deepcopy(self.body); del b[key]
            self.assertEqual(self.decide(b)[0], 422)
        self.assertEqual(len(self.call(self.base)[1]), 1)

    def test_generic_automated_and_ai_paths_cannot_promote(self):
        first = self.fixture()
        self.assertEqual(self.decide(headers={})[0], 403)
        for field in ('Origin', 'Sec-Fetch-Site', 'Sec-Fetch-Mode', 'Sec-Fetch-Dest'):
            headers = dict(self.browser); del headers[field]
            self.assertEqual(self.decide(headers=headers)[0], 403)
        for spoof in ('AI', 'AUTOMATIC', 'USER_WEB'):
            b = dict(self.body, actor=spoof)
            self.assertEqual(self.decide(b)[0], 422)
        for status in ('REVIEWED', 'REJECTED'):
            b = self.proposal(first['source_refs'][0]); b['rule']['review_state'] = status
            self.assertEqual(self.call(self.base, 'POST', b)[0], 422)
        with self.assertRaises(ServiceError) as caught:
            self.server.research.decide(first['rule_id'], **self.body, max_bytes=100000)
        self.assertEqual(caught.exception.code, 'USER_WEB_REVIEW_REQUIRED')
        self.assertEqual(len(self.call(self.base)[1]), 1)

    def test_historical_selected_version_is_exact_and_head_cas(self):
        first = self.fixture()
        b = self.proposal(first['source_refs'][0]); b['source'] = {k:first['source_refs'][0][k]
            for k in ('resource_id','anchor','note_revision')}
        b.update(rule_id=first['rule_id'], expected_version=first['version'])
        b['rule']['claim'] = '두 번째 다른 내용'
        second = self.call(self.base, 'POST', b)[1]
        self.assertEqual(self.decide()[0], 409)
        self.body['expected_version'] = second['version']
        status, saved, _ = self.decide()
        self.assertEqual(status, 201)
        self.assertEqual(saved['claim'], first['claim'])
        self.assertEqual(saved['review_decision']['selected_version'], first['version'])
        self.assertEqual(saved['supersedes'], second['version'])
        self.assertEqual(self.decide()[0], 409)

    def test_other_rule_or_absent_selected_version_denied(self):
        first = self.fixture()
        ref = {k:first['source_refs'][0][k] for k in ('resource_id','anchor','note_revision')}
        other = self.call(self.base, 'POST', self.proposal(ref))[1]
        for version in (other['version'], 'f'*32):
            self.assertEqual(self.decide(dict(self.body, selected_version=version))[0], 404)
        self.assertEqual(len(self.call(self.base)[1]), 2)

    def test_concurrent_decisions_do_not_fork(self):
        self.fixture()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.decide()[0], range(2)))
        self.assertEqual(sorted(results), [201,409])
        self.assertEqual(len(self.call(self.base)[1]), 2)

    def test_editing_reviewed_version_returns_to_exploratory(self):
        first = self.fixture(); saved = self.decide()[1]
        b = self.proposal({k:first['source_refs'][0][k] for k in ('resource_id','anchor','note_revision')}); b['source'] = {k:first['source_refs'][0][k]
            for k in ('resource_id','anchor','note_revision')}
        b.update(rule_id=first['rule_id'], expected_version=saved['version'])
        status, edited, _ = self.call(self.base, 'POST', b)
        self.assertEqual(status, 201)
        self.assertEqual(edited['review_state'], 'EXPLORATORY')
        self.assertNotIn('review_decision', edited)

    def test_auth_origin_and_payload_override_denied(self):
        self.fixture()
        self.assertEqual(self.call(self.path+'/decisions','POST',self.body,auth=False,extra=self.browser)[0],401)
        for field, value in (('decision','EXPLORATORY'),('decision','AI_CONSENSUS'),
                             ('coaching_enabled',True),('source_refs',[]),('claim','변조')):
            self.assertEqual(self.decide(dict(self.body, **{field:value}))[0],422)
        self.assertEqual(self.decide(headers=dict(self.browser, Origin='https://evil.test'))[0],403)

    def test_forged_stored_review_metadata_invalidates_store(self):
        self.fixture(); self.assertEqual(self.decide()[0],201)
        with sqlite3.connect(self.server.research.dbpath) as db:
            db.execute("UPDATE knowledge_rules SET payload=replace(payload,'USER_WEB','AI') WHERE status='REVIEWED'")
        self.assertEqual(self.call(self.base)[0],409)

    def test_source_deletion_cascades_review_and_selected_versions(self):
        first = self.fixture(); self.assertEqual(self.decide()[0],201)
        result = self.call('/dev/v1/research/'+first['source_refs'][0]['resource_id'],'DELETE')[1]
        self.assertEqual(result['deleted_versions'],2)
        self.assertEqual(self.call(self.path)[0],404)

    def test_backup_restore_preserves_reviewed_and_rejected_snapshots(self):
        first = self.fixture(); reviewed = self.decide()[1]
        self.body.update(decision='REJECTED', expected_version=reviewed['version'])
        rejected = self.decide()[1]
        root = Path(self.temp.name); archive = root/'review.zip'
        backup.backup(self.db, archive)
        result = backup.restore(archive, root/'restored')
        restored = KnowledgeStore(result['research_db'])
        for record in (first,reviewed,rejected):
            self.assertEqual(restored.get_proposal(record['rule_id'],record['version'],max_bytes=100000),record)

    def test_decision_output_budget_failure_writes_nothing(self):
        self.fixture(); original = self.server.limits
        from coach_v1.server import Limits
        self.server.limits=Limits(1000,100,10,10,100,10)
        self.assertEqual(self.decide()[0],413)
        self.server.limits=original
        self.assertEqual(len(self.call(self.base)[1]),1)


if __name__ == '__main__': unittest.main()

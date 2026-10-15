"""Auto review is independent evidence, never USER approval."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from coach_v1.state import digest


class AutoReviewTests(unittest.TestCase):
    def test_original_packet_has_complete_machine_source_checks(self):
        from coach_v1.auto_review import load_bundle, machine_check
        packet, _ = load_bundle()
        self.assertEqual(len(packet['rows']), 30)
        self.assertTrue(all(not machine_check(row) for row in packet['rows']))

    def test_modified_claim_is_not_the_reviewed_candidate(self):
        from coach_v1.auto_review import load_bundle, assess
        packet, receipts = load_bundle()
        changed = copy.deepcopy(packet)
        changed['rows'][0]['advice']['할 것'] = '항상 이깁니다.'
        result = assess(changed, receipts)
        self.assertEqual(result['rows'][0]['state'], 'HOLD')
        self.assertIn('CANDIDATE_HASH_MISMATCH', result['rows'][0]['reasons'])

    def test_no_receipts_or_duplicate_roles_never_pass(self):
        from coach_v1.auto_review import load_bundle, assess
        packet, _ = load_bundle()
        result = assess(packet, [])
        self.assertEqual(result['passed'], 0)
        self.assertEqual(result['held'], 30)
        self.assertTrue(all('EVIDENCE_REVIEW_MISSING_OR_INVALID' in r['reasons'] for r in result['rows']))

    def test_objections_are_immutable_and_weekly_report_reused(self):
        from coach_v1.auto_review import AutoReviewStore
        with tempfile.TemporaryDirectory() as folder:
            store = AutoReviewStore(Path(folder)/'auto.sqlite')
            store.object('KR-001', 'a'*64, '조건이 빠졌습니다.')
            self.assertEqual(store.withdrawn(), {'KR-001'})
            self.assertEqual(store.objections()[0]['reason'], '조건이 빠졌습니다.')
            self.assertEqual(store.objections()[0]['actor'], 'USER_OBJECTION')
            rows=[dict(id='KR-001',state='AUTO_VERIFIED',candidate_sha256='a'*64),dict(id='KR-002',state='AUTO_VERIFIED',candidate_sha256='b'*64)]
            report=store.weekly(rows)
            self.assertEqual([r['id'] for r in report['items']], ['KR-002'])
            self.assertEqual(report, store.weekly(rows))

    def test_source_number_not_in_excerpt_fails(self):
        from coach_v1.auto_review import load_bundle, machine_check
        row=copy.deepcopy(load_bundle()[0]['rows'][0])
        row['advice']['할 것']='피해가 123456 증가합니다.'
        self.assertIn('UNSUPPORTED_NUMBER', machine_check(row))

    def test_packet_metadata_and_receipt_mutations_are_not_executed_reviews(self):
        from coach_v1.auto_review import load_bundle,assess
        packet,receipts=load_bundle();changed=copy.deepcopy(packet);changed['author']='forged author'
        self.assertEqual(assess(changed,receipts)['passed'],0)
        changed_receipts=copy.deepcopy(receipts)
        changed_receipts[0]['reviews'][0]['claims']=[dict(claim='피오라는 모든 적을 처치합니다.',source_index=0,quote='Ornn')]
        self.assertEqual(assess(packet,changed_receipts)['passed'],0)

    def test_wrong_locale_and_original_lineage_fail_even_after_rehash(self):
        from coach_v1.auto_review import load_bundle,machine_check,candidate_hash
        row=copy.deepcopy(load_bundle()[0]['rows'][0]);row['original_spec_sha256']='0'*64;row['candidate_sha256']=candidate_hash(row)
        self.assertIn('ORIGINAL_LINEAGE_MISMATCH',machine_check(row))
        row=copy.deepcopy(load_bundle()[0]['rows'][0]);row['spec']['sources'][0]['url']=row['spec']['sources'][0]['url'].replace('en_US','ko_KR');row['source_excerpts'][0]['url']=row['spec']['sources'][0]['url'];row['candidate_sha256']=candidate_hash(row)
        self.assertIn('SOURCE_LINK_HASH_PATCH_OR_EXCERPT_INVALID',machine_check(row))

    def test_missing_review_run_manifest_fails_closed(self):
        from coach_v1.auto_review import load_bundle,assess
        packet,receipts=load_bundle();read=Path.read_text
        def safe_read(path,*args,**kwargs):
            if path.name=='review-manifest.json':raise FileNotFoundError('missing review manifest')
            return read(path,*args,**kwargs)
        with patch.object(Path,'read_text',safe_read):
            result=assess(packet,receipts)
        self.assertEqual(result['passed'],0)
        self.assertEqual(result['held'],30)


import unittest
from scripts import collect_expert_claims as old

class MigrationTests(unittest.TestCase):
    def test_completed_skipped_empty_step_job_is_proven_no_reservation(self):
        self.assertIs(old.reservation_expected_from_jobs([{'status':'completed','conclusion':'skipped','steps':[]}]),False)
    def test_new_pre_request_failed_run_requires_both_dispatches_skipped(self):
        steps=[dict(name=n,conclusion='skipped') for n in old.DAILY_UPLOAD_STEPS|old.DAILY_DISPATCH_STEPS]
        self.assertIs(old.reservation_expected_from_jobs([{'status':'completed','conclusion':'failure','steps':steps}]),False)
        next(s for s in steps if s['name'] in old.DAILY_DISPATCH_STEPS)['conclusion']='success'
        self.assertIsNone(old.reservation_expected_from_jobs([{'status':'completed','conclusion':'failure','steps':steps}]))
    def test_legacy_success_unknown_and_interruption_remain_closed(self):
        self.assertIsNone(old.reservation_expected_from_jobs([{'status':'completed','conclusion':'failure','steps':[]}]))
        self.assertIsNone(old.reservation_expected_from_jobs([{'status':'in_progress','steps':[]}]))
        self.assertTrue(old.reservation_expected_from_jobs([{'status':'completed','steps':[dict(name='Persist quota before any Gemini request',conclusion='success')]}]))

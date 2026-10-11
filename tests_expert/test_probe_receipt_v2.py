"""Typed CLI diagnostic receipts; authored fixtures, no provider requests."""
import unittest
from copy import deepcopy
from scripts.collect_expert_claims import safe_probe_receipt
from coach_v1.expert_collector import MODEL

class ProbeReceiptV2Tests(unittest.TestCase):
    def plan(self):
        return dict(schema_version='expert.reservation-plan.v4',text_probe=dict(
            schema_version='expert.text-probe.v2',status='READY',reason=None,model=MODEL,
            checked_at=1791712800,http_status=200,input_kind='TEXT_ONLY',video_inputs=0,
            api_route='GENERATE_CONTENT',attempt_count=4,retry_count=3))
    def test_new_route_receipt_retained_and_legacy_plan_withheld(self):
        plan=self.plan()
        self.assertEqual(safe_probe_receipt(plan),plan['text_probe'])
        plan['schema_version']='expert.reservation-plan.v3'
        self.assertIsNone(safe_probe_receipt(plan))
    def test_invalid_or_credential_echoing_route_and_counters_are_withheld(self):
        for field,value in [('api_route','TEST_SECRET'),('attempt_count',True),('attempt_count',5),
                ('retry_count',4),('retry_count',0),('checked_at',-1),('schema_version','expert.text-probe.v1')]:
            plan=deepcopy(self.plan());plan['text_probe'][field]=value
            self.assertIsNone(safe_probe_receipt(plan),field)
    def test_preflight_blocked_zero_dispatch_is_typed(self):
        plan=self.plan();plan['text_probe'].update(status='BLOCKED_EXTERNAL',reason='MISSING_API_KEYS',
            http_status=None,attempt_count=0,retry_count=0)
        self.assertEqual(safe_probe_receipt(plan),plan['text_probe'])

if __name__=='__main__':unittest.main()

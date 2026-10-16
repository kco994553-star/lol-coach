"""Response-format repair after actual HTTP200; no submitted request is retried."""
import json,tempfile,unittest
from unittest.mock import patch
from pathlib import Path
from tests_expert import test_gemini_daily as fixtures

class TextV2Tests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.DailyTests();self.f.setUp();self.d=self.f.m
        self.legacy=dict(contents=[dict(role='user',parts=[dict(text='Reply with OK.')])],generationConfig=dict(candidateCount=1,maxOutputTokens=8))
    def legacy_reservation(self):
        with patch.object(self.d,'text_body',return_value=self.legacy):return self.f.reserve()
    def test_next_text_uses_the_previously_successful_exact_request_shape(self):
        self.assertEqual(self.d.text_body(),dict(contents=[dict(role='user',parts=[dict(text='Reply with OK.')])],generationConfig=dict(candidateCount=1)))
    def test_legacy_actual_reservation_hash_remains_valid_and_same_day_consumed(self):
        old=self.legacy_reservation();self.d.validate_state(old,self.f.now)
        new=dict(self.f.config,configuration_revision='2026-10-16.2')
        with self.assertRaisesRegex(ValueError,'DAILY_TEXT_CONSUMED'):self.f.reserve(old,new)
    def test_unresolved_response_format_blocks_unchanged_next_day(self):
        state=self.d.complete(self.legacy_reservation(),'TEXT',self.f.now,200,'MALFORMED_RESPONSE')
        with self.assertRaisesRegex(ValueError,'PERSISTENT_CONFIGURATION_BLOCK'):self.f.reserve(state,now=self.f.now+86400)
        self.assertEqual(len(self.f.reserve(state,dict(self.f.config,configuration_revision='2026-10-16.2'),self.f.now+86400)['events']),3)
    def test_dispatch_uses_the_reserved_legacy_body_and_exports_only_shape(self):
        state=self.legacy_reservation();calls=[]
        def transport(*args):
            calls.append(args);return 200,{},dict(candidates=[dict(finishReason='MAX_TOKENS',content=dict(parts=[dict(text='PRIVATE_MODEL_RESPONSE_SENTINEL')]))])
        with tempfile.TemporaryDirectory() as temp:result=self.d.dispatch(state,'TEXT',self.f.now,'42','7',Path(temp),'TEST_ONLY',transport)
        self.assertEqual(calls[0][3],self.legacy)
        self.assertEqual(result['events'][-1]['http_status'],200)
        self.assertEqual(result['events'][-1]['classification'],'MALFORMED_RESPONSE')
        self.assertEqual(result['events'][-1]['safe_output']['response_shape']['finish_reasons'],['MAX_TOKENS'])
        self.assertNotIn('PRIVATE_MODEL_RESPONSE_SENTINEL',json.dumps(result))

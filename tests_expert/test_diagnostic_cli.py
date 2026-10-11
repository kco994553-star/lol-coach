"""Trusted CLI two-phase fixtures; no actual credentials or external requests."""
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts import collect_expert_claims as cli
from coach_v1 import expert_collector as core
from tests_expert.test_collector import NOW, config, entitlement
from tests_expert.test_diagnostics import ProbeHTTP

ENV = dict(YOUTUBE_API_KEY='TEST_YOUTUBE_KEY',GEMINI_API_KEY='TEST_GEMINI_KEY',
    GEMINI_FREE_TIER_CONFIRMED='true',GEMINI_QUOTA_EXCLUSIVE_CONFIRMED='true',
    INITIAL_ZERO_USAGE_CONFIRMED='true',INITIAL_ZERO_USAGE_CONFIRMED_AT='2026-10-11T00:00:00Z')

class DiagnosticCliTests(unittest.TestCase):
    def invoke(self,args,http):
        log=io.StringIO()
        with patch.dict(os.environ,ENV,clear=True),patch.object(core,'_transport',http),\
             patch.object(cli.time,'time',return_value=NOW),contextlib.redirect_stdout(log):
            code=cli.main(args,entitlement_verifier=entitlement)
        return code,log.getvalue()

    def test_failed_text_probe_retains_old_quota_and_safe_diagnostics_without_video(self):
        rows=[dict(video_id=str(i).zfill(11),seconds=s,reserved_at=NOW-10,reservation_id=str(i)*64)
              for i,s in enumerate([1000,1000,1000,1298,2346],1)]
        ledger=dict(schema_version='expert.quota-ledger.v1',initialized_at=NOW-20,reservations=rows,processed_video_ids=[])
        http=ProbeHTTP(403,dict(error=dict(code='permission_denied',message='Bad TEST_GEMINI_KEY')))
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);cfg=root/'config.json';cfg.write_text(json.dumps(config()))
            prior=root/'prior.json';prior.write_text(json.dumps(ledger));recovery=root/'recovery.json'
            recovery.write_text(json.dumps(dict(status='FOUND')));out=root/'reserved'
            code,log=self.invoke(['--phase','reserve','--config',str(cfg),'--output-dir',str(out),
                '--ledger',str(prior),'--recovery-receipt',str(recovery)],http)
            self.assertEqual(code,0);self.assertEqual(http.probe_calls,1);self.assertEqual(http.model_calls,0)
            self.assertEqual(json.loads((out/'quota-ledger.json').read_text()),ledger)
            diag=json.loads((out/'diagnostics.json').read_text())
            self.assertEqual(diag['request_counts'],dict(TEXT_PROBE=1,VIDEO_CLIP=0,METADATA=0))
            self.assertEqual(diag['text_probe']['http_status'],403)
            self.assertEqual(diag['events'][0]['error_code'],'permission_denied')
            self.assertIn('EXPERT_PROVIDER_DIAGNOSTIC_JSON=',log)
            self.assertNotIn('TEST_GEMINI_KEY',log+json.dumps(diag))

    def test_default_first_clip_mode_survives_reserve_process_without_second_probe(self):
        http=ProbeHTTP()
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);cfg=root/'config.json';cfg.write_text(json.dumps(config()));reserve=root/'reserve'
            code,_=self.invoke(['--phase','reserve','--config',str(cfg),'--output-dir',str(reserve)],http)
            self.assertEqual(code,0);plan=json.loads((reserve/'plan.json').read_text())
            self.assertEqual(plan['collection_mode'],'DIAGNOSTIC_FIRST_CLIP')
            self.assertEqual(plan['ledger']['reservations'][0]['seconds'],1200)
            final=root/'final';code,_=self.invoke(['--phase','process','--plan',str(reserve/'plan.json'),
                '--reservation-artifact-id','123','--output-dir',str(final)],http)
            self.assertEqual(code,0);self.assertEqual(http.probe_calls,1);self.assertEqual(http.model_calls,1)
            diag=json.loads((final/'diagnostics.json').read_text())
            self.assertEqual(diag['request_counts'],dict(TEXT_PROBE=0,VIDEO_CLIP=1,METADATA=0))
            self.assertEqual(diag['text_probe'],plan['text_probe']);self.assertEqual(diag['api_route'],'INTERACTIONS')
            self.assertEqual(json.loads((final/'receipt.json').read_text())['status'],'PARTIAL')
            self.assertEqual(json.loads((final/'quota-ledger.json').read_text())['processed_video_ids'],[])

    def test_schema_only_phase_never_discovers_reserves_or_requests_video(self):
        for status in (200,400):
            http=ProbeHTTP(status,response=None if status==200 else dict(error=dict(code='invalid_request',message='Bad TEST_GEMINI_KEY')))
            with tempfile.TemporaryDirectory() as temp:
                root=Path(temp);out=root/'format';prior=root/'prior.json';prior.write_text('TEST_UNTOUCHED_PRIOR_LEDGER')
                code,log=self.invoke(['--phase','probe-format','--output-dir',str(out)],http)
                self.assertEqual(code,0);self.assertEqual(http.probe_calls,1);self.assertEqual(http.model_calls,0)
                self.assertEqual(prior.read_text(),'TEST_UNTOUCHED_PRIOR_LEDGER');self.assertFalse((out/'quota-ledger.json').exists())
                receipt=json.loads((out/'format-probe.json').read_text())
                self.assertEqual(receipt['profile'],'TEXT_ONLY_CLAIM_SCHEMA');self.assertEqual(receipt['text_probe']['http_status'],status)
                self.assertIn('EXPERT_FORMAT_PROBE_JSON=',log);self.assertNotIn('TEST_GEMINI_KEY',log)
                diag=json.loads((out/'diagnostics.json').read_text())
                self.assertEqual(diag['request_counts'],dict(TEXT_PROBE=1,VIDEO_CLIP=0,METADATA=0))
                self.assertEqual(http.calls[0][3]['response_format']['schema'],core.RESPONSE_SCHEMA)

    def test_failed_format_phase_removes_prior_ready_receipt(self):
        http=ProbeHTTP()
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'format';args=['--phase','probe-format','--output-dir',str(out)]
            code,_=self.invoke(args,http);self.assertEqual(code,0)
            self.assertEqual(json.loads((out/'format-probe.json').read_text())['text_probe']['status'],'READY')
            before=len(http.calls)
            with patch.object(cli,'validate_entitlement_proof',side_effect=ValueError('TEST_BAD_PROOF')):
                code,log=self.invoke(args,http)
            self.assertEqual(code,1);self.assertEqual(len(http.calls),before)
            self.assertFalse((out/'format-probe.json').exists());self.assertFalse((out/'entitlement.json').exists())
            self.assertIsNone(json.loads((out/'diagnostics.json').read_text())['text_probe'])
            self.assertNotIn('TEST_BAD_PROOF',log)

    def test_invalid_plan_has_null_http_safe_reason_and_zero_dispatch(self):
        http=ProbeHTTP()
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);plan=root/'bad.json';plan.write_text('{}');out=root/'out'
            code,log=self.invoke(['--phase','process','--plan',str(plan),'--output-dir',str(out)],http)
            self.assertEqual(code,1);self.assertEqual(http.calls,[])
            diag=json.loads((out/'diagnostics.json').read_text())
            self.assertEqual(diag['events'][-1]['reason'],'INVALID_OR_UNAVAILABLE_PUBLIC_STATE')
            self.assertIsNone(diag['events'][-1]['http_status']);self.assertIsNone(diag['text_probe'])
            self.assertNotIn('TEST_GEMINI_KEY',json.dumps(diag)+log)

if __name__=='__main__':unittest.main()

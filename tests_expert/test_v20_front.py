"""Offline paired diagnostics and quota conservation; no provider requests."""
import copy
import datetime as dt
import importlib
import inspect
import json
import threading
import tempfile
import os
from pathlib import Path
from unittest.mock import patch
import unittest

from coach_v1 import expert_collector as collector
from coach_v1 import expert_entitlement as entitlement_module
from tests_expert.test_collector import NOW, Transport, config, entitlement, generated, policy, is_text_probe
from tests_expert.test_entitlement import PRICING, VIDEO, MODELS

FALLBACK='gemini-3.6-flash'


class FrontTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec('coach_v1.expert_front_diagnostics'), 'paired diagnostics missing')
        return importlib.import_module('coach_v1.expert_front_diagnostics')

    def proof(self, model):
        p=entitlement();p['model']=model
        return p

    def run_pair(self, curl, python, **kwargs):
        kwargs.setdefault('allow_fallback_once',True)
        return self.module().run_front_diagnostics(youtube_api_key='TEST_YOUTUBE_KEY',gemini_api_key='TEST_GEMINI_KEY',
            policy_factory=lambda proof:policy(),entitlement_verifier=self.proof,
            curl_transport=curl,python_transport=python,clock=lambda:NOW,**kwargs)

    def test_text_uses120_seconds_video_stays600(self):
        calls=[]
        def http(*args):
            calls.append(args);return Transport()(*args)
        c=collector.ExpertCollector(youtube_api_key='TEST_YOUTUBE_KEY',gemini_api_key='TEST_GEMINI_KEY',policy=policy(),clock=lambda:NOW,transport=http)
        c.process(c.prepare(config(),collection_mode='DIAGNOSTIC_FIRST_CLIP'),reservation_persisted=True)
        self.assertEqual([call[4] for call in calls if call[0]=='POST'],[120,600])

    def test_paired_clients_start_together_use_identical_text_and120_bound(self):
        barrier=threading.Barrier(2);calls=[]
        def http(*args):
            calls.append(args);barrier.wait(timeout=2)
            return 200,{},generated('PRIVATE_MODEL_OUTPUT')
        result=self.run_pair(http,http)
        self.assertEqual(result['status'],'READY');self.assertEqual(result['selected_model'],collector.MODEL)
        self.assertEqual(len(calls),2);self.assertEqual(calls[0],calls[1]);self.assertEqual(calls[0][4],120)
        self.assertTrue(is_text_probe(calls[0][3]));self.assertNotIn('PRIVATE_MODEL_OUTPUT',json.dumps(result))
        self.assertNotIn('TEST_GEMINI_KEY',json.dumps(result))

    def test_both_timeouts_record_provider_network_then_one_free_fallback(self):
        calls=[]
        def http(*args):
            calls.append(args)
            if collector.MODEL in args[1]:raise TimeoutError('PRIVATE')
            return 200,{},generated('OK')
        result=self.run_pair(http,http)
        self.assertEqual(result['attempts'][0]['reason'],'PROVIDER_NETWORK_TIMEOUT')
        self.assertEqual(result['selected_model'],FALLBACK);self.assertEqual(result['request_count'],4)
        self.assertEqual(len(result['attempts']),2)
        self.assertEqual(result['attempts'][0]['statuses'],{'curl':None,'python':None})

    def test_failed_text_never_discovers_or_changes_prior_six_charges(self):
        result=self.run_pair(lambda *a:(_ for _ in ()).throw(TimeoutError()),lambda *a:(_ for _ in ()).throw(TimeoutError()))
        self.assertEqual(result['reason'],'PROVIDER_NETWORK_TIMEOUT');self.assertIsNone(result['selected_text_probe'])
        self.assertEqual(result['request_count'],4)
        prior=dict(schema_version='expert.quota-ledger.v1',initialized_at=NOW-100,
            reservations=[dict(video_id=str(i)*11,seconds=s,reserved_at=NOW-50,reservation_id=str(i+1)*64)
                for i,s in enumerate([1200,1200,1200,1200,1200,1396])],processed_video_ids=[])
        c=collector.ExpertCollector(youtube_api_key='TEST_YOUTUBE_KEY',gemini_api_key='TEST_GEMINI_KEY',policy=policy(),clock=lambda:NOW,
            transport=lambda *a:self.fail('failed front must not make API calls'))
        plan=c.prepare(config(),prior,ledger_history='FOUND',front_diagnostics=result,collection_mode='DIAGNOSTIC_FIRST_CLIP')
        self.assertEqual(plan['status'],'BLOCKED_EXTERNAL');self.assertEqual(plan['ledger'],prior)
        self.assertEqual(sum(r['seconds'] for r in plan['ledger']['reservations']),7396)

    def test_selected_fallback_is_used_for_video_without_duplicate_text(self):
        def probe(*args):
            if collector.MODEL in args[1]:return 503,{},{}
            return 200,{},generated('OK')
        front=self.run_pair(probe,probe);http=Transport()
        c=collector.ExpertCollector(model=FALLBACK,youtube_api_key='TEST_YOUTUBE_KEY',gemini_api_key='TEST_GEMINI_KEY',policy=policy(),clock=lambda:NOW,transport=http)
        plan=c.prepare(config(),front_diagnostics=front,collection_mode='DIAGNOSTIC_FIRST_CLIP')
        self.assertEqual(plan['status'],'RESERVED');self.assertFalse(any(is_text_probe(x[3]) for x in http.calls))
        result=c.process(plan,reservation_persisted=True)
        self.assertEqual(result['status'],'READY')
        posts=[x for x in http.calls if x[0]=='POST'];self.assertEqual(len(posts),1);self.assertIn('/'+FALLBACK+':',posts[0][1])
        self.assertEqual(result['artifacts'][0]['processing']['model'],FALLBACK)
        self.assertEqual(c.request_count,7)

    def test_stale_or_nonfree_fallback_never_dispatches_it(self):
        m=self.module()
        for status,date in [('PAID_REQUIRED','2026-10-11'),('UNKNOWN','2026-10-11'),('VERIFIED_FREE','2026-10-10')]:
            calls=[]
            def verify(model):
                p=self.proof(model)
                if model==FALLBACK:
                    p['status']=status;p['checked_at']=date
                    p['reasons']=[{'PAID_REQUIRED':'FREE_TIER_POSITIVE_PRICE','UNKNOWN':'PRICING_SOURCE_UNAVAILABLE','VERIFIED_FREE':'DOCUMENTED_FREE_ENTITLEMENT'}[status]]
                return p
            def http(*args):calls.append(args);raise TimeoutError()
            result=m.run_front_diagnostics(youtube_api_key='TEST_YOUTUBE_KEY',gemini_api_key='TEST_GEMINI_KEY',policy_factory=lambda p:policy(),
                entitlement_verifier=verify,curl_transport=http,python_transport=http,clock=lambda:NOW,allow_fallback_once=True)
            self.assertEqual(len(calls),2);self.assertIsNone(result['selected_model'])

    def test_fresh_proof_is_bound_to_exact_model_and_unknown_models_rejected(self):
        self.assertIn('model',inspect.signature(entitlement_module.verify_free_entitlement).parameters)
        pages={'pricing':PRICING.replace(collector.MODEL,FALLBACK),'video-understanding':VIDEO,'models':MODELS.replace(collector.MODEL,FALLBACK)}
        p=entitlement_module.verify_free_entitlement(model=FALLBACK,clock=lambda:dt.datetime(2026,10,11,tzinfo=dt.timezone.utc),
            transport=lambda url,**kw:dict(status=200,url=url,body=pages[url.rsplit('/',1)[1]].encode(),content_type='text/html'))
        self.assertEqual(p['model'],FALLBACK);self.assertEqual(p['status'],'VERIFIED_FREE')
        with self.assertRaises(ValueError):entitlement_module.verify_free_entitlement(model='gemini-guessed-flash')

    def test_receipt_rejects_tampered_model_request_hash_and_success(self):
        result=self.run_pair(lambda *a:(200,{},generated('OK')),lambda *a:(200,{},generated('OK')))
        m=self.module()
        for mutation in (lambda x:x.update(selected_model=FALLBACK),lambda x:x['attempts'][0].update(request_sha256='0'*64),
                         lambda x:x['attempts'][0]['statuses'].update(python=403)):
            changed=copy.deepcopy(result);mutation(changed)
            with self.assertRaises(ValueError):m.validate_front_receipt(changed,now=NOW)

    def test_curl_configuration_keeps_key_off_argv_and_bounds_timeout(self):
        m=self.module();body=m.text_body()
        text=m.curl_configuration(collector.MODEL,{'x-goog-api-key':'TEST_KEY','Content-Type':'application/json'},body,120)
        self.assertIn('max-time = 120',text);self.assertIn('TEST_KEY',text)
        self.assertNotIn('TEST_KEY',' '.join(m.CURL_COMMAND));self.assertNotIn('location',text)
        with self.assertRaises(ValueError):m.curl_configuration(collector.MODEL,{'x-goog-api-key':'unsafe\nkey'},body,121)

    def test_unknown_quota_history_blocks_pair_before_any_provider_call(self):
        self.assertIn('ledger_history',inspect.signature(self.module().run_front_diagnostics).parameters)
        result=self.run_pair(lambda *a:self.fail('quota unknown'),lambda *a:self.fail('quota unknown'),ledger_history='UNKNOWN')
        self.assertEqual(result['reason'],'QUOTA_HISTORY_UNKNOWN');self.assertEqual(result['request_count'],0)

    def test_corrupt_recovered_quota_is_classified_as_quota_failure(self):
        result=self.run_pair(lambda *a:self.fail('corrupt quota'),lambda *a:self.fail('corrupt quota'),ledger_history='FOUND',ledger={})
        self.assertEqual(result['reason'],'QUOTA_HISTORY_UNKNOWN');self.assertEqual(result['request_count'],0)

    def test_cli_reserves_from_selected_probe_and_fresh_model_proof(self):
        import scripts.collect_expert_claims as cli
        def http(*args):
            if collector.MODEL in args[1]:return 503,{},{}
            return 200,{},generated('OK')
        front=self.run_pair(http,http);transport=Transport();models=[]
        def verify(model=collector.MODEL):models.append(model);return self.proof(model)
        env=dict(YOUTUBE_API_KEY='TEST_YOUTUBE_KEY',GEMINI_API_KEY='TEST_GEMINI_KEY',GEMINI_FREE_TIER_CONFIRMED='true',
            GEMINI_QUOTA_EXCLUSIVE_CONFIRMED='true',INITIAL_ZERO_USAGE_CONFIRMED='true',INITIAL_ZERO_USAGE_CONFIRMED_AT='2026-10-11T00:00:00Z')
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'front.json').write_text(json.dumps(front));(root/'config.json').write_text(json.dumps(config()))
            with patch.dict(os.environ,env,clear=True),patch.object(cli.time,'time',return_value=NOW),patch.object(collector,'_transport',transport):
                try:code=cli.main(['--phase','reserve','--front-diagnostics',str(root/'front.json'),'--config',str(root/'config.json'),
                    '--output-dir',str(root/'reserve')],entitlement_verifier=verify)
                except SystemExit:self.fail('reserve must accept front diagnostics')
                self.assertEqual(code,0)
                plan=json.loads((root/'reserve/plan.json').read_text());self.assertEqual(plan['text_probe']['model'],FALLBACK)
                self.assertFalse(any(is_text_probe(c[3]) for c in transport.calls))
                code=cli.main(['--phase','process','--plan',str(root/'reserve/plan.json'),'--reservation-artifact-id','12',
                    '--output-dir',str(root/'final')],entitlement_verifier=verify)
            self.assertEqual(code,0);self.assertEqual(models,[FALLBACK,FALLBACK])
            self.assertEqual(json.loads((root/'final/receipt.json').read_text())['status'],'READY')

    def test_new_diagnostic_cli_is_available(self):
        self.assertIsNotNone(importlib.util.find_spec('scripts.diagnose_expert_front'))

    def test_historical_charged_video_never_retried_after_rolling_window(self):
        from tests_expert.test_collector import VIDEO as VID
        prior=dict(schema_version='expert.quota-ledger.v1',initialized_at=NOW-200000,
            reservations=[dict(video_id=VID,seconds=600,reserved_at=NOW-100000,reservation_id='a'*64)],processed_video_ids=[])
        http=Transport();c=collector.ExpertCollector(youtube_api_key='TEST_YOUTUBE_KEY',gemini_api_key='TEST_GEMINI_KEY',policy=policy(),clock=lambda:NOW,transport=http)
        plan=c.prepare(config(),prior,ledger_history='FOUND',collection_mode='DIAGNOSTIC_FIRST_CLIP')
        self.assertEqual(plan['status'],'NO_ELIGIBLE_VIDEOS');self.assertEqual(plan['ledger'],prior)

    def test_python_timeout_marker_and_curl_oversize_remain_typed(self):
        m=self.module();args=('POST',m.model_url(collector.MODEL),{'x-goog-api-key':'TEST_KEY','Content-Type':'application/json'},m.text_body(),120,1000000)
        with patch.object(m,'_bounded_process',return_value=(0,b'TIMEOUT\n')):
            with self.assertRaises(TimeoutError):m._python_transport(*args)
        with patch.object(m,'_bounded_process',return_value=(63,b'')):
            observation=m._observe(m._curl_transport,args[1],args[2],args[3],120)
        self.assertEqual(observation['reason'],'RESPONSE_TOO_LARGE')

    def test_subprocess_wall_deadline_and_output_limit(self):
        import sys
        m=self.module()
        with self.assertRaises(TimeoutError):m._bounded_process((sys.executable,'-c','import time; time.sleep(5)'),b'',1,1024)
        with self.assertRaises(collector._External):m._bounded_process((sys.executable,'-c','print("x"*2000)'),b'',2,1024)

    def test_auth_payment_or_quota_failure_is_terminal_without_fallback(self):
        for code in (401,403,402,429):
            with self.subTest(code=code):
                calls=[]
                def http(*args):calls.append(args);return code,{},{}
                result=self.run_pair(http,http)
                self.assertEqual(result['status'],'BLOCKED_EXTERNAL');self.assertEqual(len(calls),2)
                self.assertEqual(len(result['attempts']),1);self.assertIsNone(result['selected_text_probe'])

    def test_forged_fallback_after_auth_or_quota_failure_is_rejected(self):
        def http(*args):
            if collector.MODEL in args[1]:return 503,{},{}
            return 200,{},generated('OK')
        valid=self.run_pair(http,http)
        for code in (401,403,402,429):
            forged=copy.deepcopy(valid)
            for name in ('curl','python'):
                forged['attempts'][0]['statuses'][name]=code
                forged['attempts'][0]['observations'][name]['http_status']=code
            with self.assertRaises(ValueError):self.module().validate_front_receipt(forged,now=NOW)

    def test_default_diagnostic_does_not_repeat_authorized_fallback_trial(self):
        m=self.module()
        self.assertIn('allow_fallback_once',inspect.signature(m.run_front_diagnostics).parameters)
        calls=[]
        def http(*args):calls.append(args);raise TimeoutError()
        result=m.run_front_diagnostics(youtube_api_key='TEST_YOUTUBE_KEY',gemini_api_key='TEST_GEMINI_KEY',policy_factory=lambda p:policy(),
            entitlement_verifier=self.proof,curl_transport=http,python_transport=http,clock=lambda:NOW)
        self.assertEqual(len(calls),2);self.assertEqual(len(result['attempts']),1)
        self.assertFalse(result['allow_fallback_once']);self.assertEqual(result['reason'],'PROVIDER_NETWORK_TIMEOUT')

    def test_forged_fallback_without_explicit_trial_flag_is_rejected(self):
        def http(*args):
            if collector.MODEL in args[1]:raise TimeoutError()
            return 200,{},generated('OK')
        result=self.run_pair(http,http);result['allow_fallback_once']=False
        with self.assertRaises(ValueError):self.module().validate_front_receipt(result,now=NOW)


if __name__=='__main__':unittest.main()

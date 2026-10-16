"""Daily at-most-once budget and recovery tests; transports are isolated fixtures."""
from copy import deepcopy
from datetime import datetime, timezone
import importlib
import tempfile
import unittest
from pathlib import Path

class DailyTests(unittest.TestCase):
    def setUp(self):
        self.m=importlib.import_module('coach_v1.gemini_daily')
        self.now=1792126800
        self.config=dict(schema_version='evidence-intake.v1',model='gemini-3.6-flash',timezone='Asia/Seoul',configuration_revision='2026-10-16.1',purpose='EXPERT_STATEMENT',expert_channels='config/expert_channels.json',pov_channels='config/pov_channels.json',max_clip_seconds=600,clip_seconds=120,blind_evaluation_enabled=False)
        self.ledger=dict(schema_version='expert.quota-ledger.v1',initialized_at=self.now-100,reservations=[],processed_video_ids=[])
        self.state=self.m.empty_state('lol-coach')
        self.proof=dict(status='VERIFIED_FREE',checked_at='2026-10-16',model='gemini-3.6-flash',sources=[dict(url=url,sha256='a'*64) for url in self.m.ENTITLEMENT_URLS],reasons=['DOCUMENTED_FREE_ENTITLEMENT'])
    def reserve(self,state=None,config=None,now=None):
        at=now or self.now
        proof=dict(self.proof,checked_at=datetime.fromtimestamp(at,timezone.utc).date().isoformat())
        return self.m.reserve_text(state or self.state,self.ledger,config or self.config,at,'42',proof)
    def test_module_exists(self):
        self.assertTrue(callable(self.m.reserve_text))
    def test_seoul_day_boundary(self):
        self.assertEqual(self.m.seoul_day(int(datetime(2026,10,16,14,59,59,tzinfo=timezone.utc).timestamp())),'2026-10-16')
        self.assertEqual(self.m.seoul_day(int(datetime(2026,10,16,15,0,0,tzinfo=timezone.utc).timestamp())),'2026-10-17')
    def test_same_day_is_consumed_even_other_purpose_revision(self):
        state=self.reserve();other=dict(self.config,purpose='POV_OBSERVATION',configuration_revision='new')
        with self.assertRaisesRegex(ValueError,'DAILY_TEXT_CONSUMED'):self.reserve(state,other)
    def test_pending_blocks_next_day_unchanged_configuration(self):
        with self.assertRaisesRegex(ValueError,'PERSISTENT_CONFIGURATION_BLOCK'):self.reserve(self.reserve(),now=self.now+86400)
    def test_changed_revision_unblocks_next_day(self):
        state=self.reserve();other=dict(self.config,configuration_revision='fixed')
        self.assertEqual(len(self.reserve(state,other,self.now+86400)['events']),2)
    def test_classification(self):
        for code,result in [(200,'TEXT_ONLY_SUCCESS'),(429,'QUOTA_EXCEEDED'),(401,'AUTHENTICATION'),(403,'PERMISSION'),(400,'ARGUMENT_CONFIGURATION'),(402,'PAYMENT_REQUIRED'),(503,'SERVER_FAILURE')]:
            self.assertEqual(self.m.classify(code,'TEXT'),result)
    def test_persistent_auth_blocks_new_day(self):
        state=self.reserve();state=self.m.complete(state,'TEXT',self.now,401)
        with self.assertRaisesRegex(ValueError,'PERSISTENT_CONFIGURATION_BLOCK'):self.reserve(state,now=self.now+86400)
    def test_quota_failure_allows_next_day(self):
        state=self.m.complete(self.reserve(),'TEXT',self.now,429)
        self.assertEqual(len(self.reserve(state,now=self.now+86400)['events']),3)
    def test_video_requires_text_and_real_offsets_and_original_charge(self):
        source=self.source()
        with self.assertRaises(ValueError):self.m.reserve_video(self.reserve(),self.ledger,self.config,source,self.now,'42',self.proof)
        state=self.m.complete(self.reserve(),'TEXT',self.now,200)
        state,ledger=self.m.reserve_video(state,self.ledger,self.config,source,self.now,'42',self.proof)
        self.assertEqual(ledger['reservations'][0]['seconds'],1137)
        body=self.m.video_body(source)
        self.assertEqual(body['contents'][0]['parts'][0]['video_metadata'],dict(start_offset='0s',end_offset='120s'))
        with self.assertRaises(ValueError):self.m.reserve_video(state,ledger,self.config,source,self.now,'42',self.proof)
    def source(self):
        video=dict(id='abcdefghijk',url='https://www.youtube.com/watch?v=abcdefghijk',title='Example',channel_id='UC'+'a'*22,channel_name='Example',speaker='UNKNOWN',speaker_verified=False,published_at='2026-10-16T00:00:00Z',upload_date=None,duration_seconds=1137,language='ko')
        return dict(schema_version='evidence.source-plan.v1',purpose='EXPERT_STATEMENT',video=video,start_seconds=0,end_seconds=120)
    def test_charged_id_never_reused(self):
        source=self.source();self.ledger['reservations'].append(dict(video_id='abcdefghijk',seconds=1137,reserved_at=self.now-10,reservation_id='a'*64))
        state=self.m.complete(self.reserve(),'TEXT',self.now,200)
        with self.assertRaisesRegex(ValueError,'VIDEO_ALREADY_CHARGED'):self.m.reserve_video(state,self.ledger,self.config,source,self.now,'42',self.proof)
    def test_dispatch_requires_ack_and_exclusive_claim(self):
        state=self.reserve();calls=[]
        def transport(*args):calls.append(args);return 200,{},dict(candidates=[dict(finishReason='STOP',content=dict(parts=[dict(text='OK')]))])
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):self.m.dispatch(state,'TEXT',self.now,'42','',Path(temp),'x',transport)
            result=self.m.dispatch(state,'TEXT',self.now,'42','7',Path(temp),'x',transport)
            self.assertEqual(result['events'][-1]['classification'],'TEXT_ONLY_SUCCESS')
            with self.assertRaises(FileExistsError):self.m.dispatch(state,'TEXT',self.now,'42','7',Path(temp),'x',transport)
        self.assertEqual(len(calls),1)
    def test_dispatch_503_never_retries(self):
        calls=[]
        def transport(*args):calls.append(args);return 503,{},b'{}'
        with tempfile.TemporaryDirectory() as temp:self.m.dispatch(self.reserve(),'TEXT',self.now,'42','7',Path(temp),'x',transport)
        self.assertEqual(len(calls),1)
    def test_recovery_rejects_dropped_prefix(self):
        old=self.reserve();new=deepcopy(old);new['events']=[]
        with self.assertRaises(ValueError):self.m.monotonic_pair(old,self.ledger,new,self.ledger,self.now)
    def test_source_bounds_and_purpose(self):
        for change in [dict(start_seconds=-1),dict(end_seconds=700),dict(purpose='POV_OBSERVATION')]:
            source=self.source();source.update(change)
            with self.assertRaises(ValueError):self.m.validate_source(source,self.config)
    def test_legacy_cli_live_paths_are_guarded(self):
        from scripts import collect_expert_claims,diagnose_expert_front,diagnose_expert_video
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(collect_expert_claims.main(['--phase','probe-format','--output-dir',temp]),1)
            self.assertEqual(diagnose_expert_front.main(['--output',temp+'/front.json','--recovery-receipt','missing']),1)
            self.assertEqual(diagnose_expert_video.main(['--phase','process','--output-dir',temp]),1)
    def test_recover_cancelled_reservation_and_reject_expiration(self):
        state=self.reserve();artifact=dict(id=8,name='gemini-daily-state-42-TEXT',created_at='2026-10-16T01:00:00Z',expired=False)
        runs=[dict(id=42,run_number=1,conclusion='cancelled')]
        recovered,q=self.m.recover_pairs(runs,99,lambda run:[artifact],lambda run,item:(state,self.ledger),lambda run:False,self.now)
        self.assertEqual(recovered,state);self.assertEqual(q,self.ledger)
        artifact['expired']=True
        with self.assertRaises(ValueError):self.m.recover_pairs(runs,99,lambda run:[artifact],lambda run,item:(state,self.ledger),lambda run:False,self.now)
    def test_recover_missing_newer_expected_snapshot_blocks(self):
        runs=[dict(id=43,run_number=2)]
        with self.assertRaises(ValueError):self.m.recover_pairs(runs,99,lambda run:[],lambda *args:None,lambda run:True,self.now)
    def test_cli_phases_use_one_text_and_one_video_with_durable_acks(self):
        from scripts.run_gemini_daily import main
        import os,json
        from unittest.mock import patch
        runtime=dict(schema_version='expert.runtime.v1',project_name='lol-coach',confirmation_source='USER_QUEUE_V1.6_2026-10-11',confirmed_at='2026-10-11T06:31:52.582043+00:00',free_tier_confirmed=True,entitlement_checked_at='2026-10-13',quota_exclusive_confirmed=True,initial_zero_usage_confirmed=True)
        calls=[]
        def transport(*args):
            if args[0]=='GET':
                return 200,{},dict(items=[dict(id='abcdefghijk',snippet=dict(channelId='UC'+'a'*22,liveBroadcastContent='none'),contentDetails=dict(duration='PT18M57S'),status=dict(privacyStatus='public',uploadStatus='processed'))])
            calls.append(args)
            text='OK' if len(calls)==1 else '{"claims":[]}'
            return 200,{},dict(candidates=[dict(finishReason='STOP',content=dict(parts=[dict(text=text)]))])
        with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,dict(GITHUB_RUN_ID='42',GITHUB_RUN_ATTEMPT='1',GEMINI_API_KEY='test',YOUTUBE_API_KEY='test',RUNNER_TEMP=temp),clear=True),patch('scripts.run_gemini_daily.claim_root',return_value=Path(temp)/'claims'):
            root=Path(temp)
            for name,value in [('config.json',self.config),('runtime.json',runtime),('daily-state.json',self.state),('quota-ledger.json',self.ledger),('recovery.json',dict(status='FOUND')),('source.json',self.source())]:(root/name).write_text(json.dumps(value))
            args=['--config',str(root/'config.json'),'--runtime-config',str(root/'runtime.json'),'--output-dir',str(root),'--state',str(root/'daily-state.json'),'--ledger',str(root/'quota-ledger.json'),'--recovery-receipt',str(root/'recovery.json')]
            kwargs=dict(entitlement_verifier=lambda **kw:self.proof,transport=transport,clock=lambda:self.now,ack_verifier=lambda *args:True)
            self.assertEqual(main(['--phase','pretext']+args,**kwargs),0)
            self.assertEqual(main(['--phase','text','--reservation-artifact-id','8']+args,**kwargs),0)
            with patch('scripts.run_gemini_daily.source_allowed',return_value=True):
                self.assertEqual(main(['--phase','preparevideo','--text-result-artifact-id','9','--source-plan',str(root/'source.json')]+args,**kwargs),0)
                self.assertEqual(main(['--phase','video','--reservation-artifact-id','10']+args,**kwargs),0)
            state=json.loads((root/'daily-state.json').read_text());self.assertEqual(len(state['events']),4)
            self.assertEqual(len(calls),2)
    def test_purpose_switch_cannot_clear_persistent_authentication(self):
        state=self.m.complete(self.reserve(),'TEXT',self.now,401)
        with self.assertRaisesRegex(ValueError,'PERSISTENT_CONFIGURATION_BLOCK'):self.reserve(state,dict(self.config,purpose='POV_OBSERVATION'),self.now+86400)
    def test_forged_reservation_and_success_receipt_rejected(self):
        state=self.reserve();state['events'][0]['run_id']='43'
        with self.assertRaises(ValueError):self.m.validate_state(state,self.now)
        state=self.m.complete(self.reserve(),'TEXT',self.now,401);state['events'][-1]['classification']='TEXT_ONLY_SUCCESS'
        with self.assertRaises(ValueError):self.m.validate_state(state,self.now)
    def test_video_pair_requires_durable_full_duration_charge(self):
        state=self.m.complete(self.reserve(),'TEXT',self.now,200)
        state,quota=self.m.reserve_video(state,self.ledger,self.config,self.source(),self.now,'42',self.proof)
        with self.assertRaises(ValueError):self.m.validate_pair(state,self.ledger,self.now)
    def test_recover_final_only_noop_prefix(self):
        state=self.reserve();artifacts={42:[dict(id=8,name='gemini-daily-state-42-TEXT',created_at='2026-10-16T01:00:00Z')],43:[dict(id=9,name='gemini-daily-state-43-FINAL',created_at='2026-10-16T02:00:00Z')]}
        recovered,_=self.m.recover_pairs([dict(id=42,run_number=1),dict(id=43,run_number=2)],99,lambda run:artifacts[run],lambda *args:(state,self.ledger),lambda *args:True,self.now)
        self.assertEqual(recovered,state)
    def test_explicit_source_requires_current_public_matching_metadata(self):
        from scripts.run_gemini_daily import verify_source_metadata
        source=self.source()
        class Collector:
            def _youtube(self,*args,**kwargs):return dict(items=[dict(id='abcdefghijk',snippet=dict(channelId='UC'+'a'*22,liveBroadcastContent='none'),contentDetails=dict(duration='PT18M57S'),status=dict(privacyStatus='public',uploadStatus='processed'))])
        verify_source_metadata(source,Collector())
        class Private(Collector):
            def _youtube(self,*args,**kwargs):
                result=super()._youtube(*args,**kwargs);result['items'][0]['status']['privacyStatus']='private';return result
        with self.assertRaises(ValueError):verify_source_metadata(source,Private())
    def test_pov_channel_allowlist_is_separate(self):
        from scripts.run_gemini_daily import source_allowed
        import json
        pov=json.loads(Path('config/pov_channels.json').read_text())
        source=self.source();source['purpose']='POV_OBSERVATION';source['video']['channel_id']=pov['channels'][0]['channel_id']
        config=dict(self.config,purpose='POV_OBSERVATION')
        self.assertTrue(source_allowed(source,config))
        source['purpose']='EXPERT_STATEMENT'
        self.assertFalse(source_allowed(source,self.config))
    def test_provider_error_redacted_and_classified(self):
        def transport(*args):return 429,{},dict(error=dict(code=429,status='RESOURCE_EXHAUSTED',message='Project quota exceeded; key secret-value at https://example.invalid'))
        with tempfile.TemporaryDirectory() as temp:
            result=self.m.dispatch(self.reserve(),'TEXT',self.now,'42','7',Path(temp),'secret-value',transport)
        event=result['events'][-1];self.assertEqual(event['classification'],'QUOTA_EXCEEDED')
        self.assertEqual(event['safe_output']['provider_error']['error_status'],'RESOURCE_EXHAUSTED')
        self.assertNotIn('secret-value',str(result));self.assertNotIn('https://example.invalid',str(result))
    def test_video_purpose_cannot_change_after_text_reservation(self):
        state=self.m.complete(self.reserve(),'TEXT',self.now,200);config=dict(self.config,purpose='POV_OBSERVATION');source=self.source();source['purpose']='POV_OBSERVATION'
        with self.assertRaises(ValueError):self.m.reserve_video(state,self.ledger,config,source,self.now,'42',self.proof)
    def test_cli_text_failure_receipt_reports_quota_without_video(self):
        from scripts.run_gemini_daily import main
        import os,json
        from unittest.mock import patch
        runtime=dict(project_name='lol-coach')
        state=self.reserve()
        with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,dict(GITHUB_RUN_ID='42',GITHUB_RUN_ATTEMPT='1',GEMINI_API_KEY='fixture-key',RUNNER_TEMP=temp),clear=True),patch('scripts.run_gemini_daily.claim_root',return_value=Path(temp)/'claims'):
            root=Path(temp)
            for name,value in [('config.json',self.config),('runtime.json',runtime),('daily-state.json',state),('quota-ledger.json',self.ledger)]:(root/name).write_text(json.dumps(value))
            args=['--phase','text','--config',str(root/'config.json'),'--runtime-config',str(root/'runtime.json'),'--output-dir',temp,'--state',str(root/'daily-state.json'),'--ledger',str(root/'quota-ledger.json'),'--reservation-artifact-id','8']
            def transport(*args):return 429,{},dict(error=dict(code=429,status='RESOURCE_EXHAUSTED',message='quota exceeded fixture-key'))
            with patch('scripts.run_gemini_daily._gate',return_value=(self.proof,None)):
                self.assertEqual(main(args,transport=transport,clock=lambda:self.now,ack_verifier=lambda *args:True),0)
            receipt=json.loads((root/'receipt.json').read_text())
            self.assertEqual(receipt['http_status'],429);self.assertEqual(receipt['classification'],'QUOTA_EXCEEDED');self.assertFalse(receipt['valid_extraction']);self.assertFalse(receipt['text_success'])
            self.assertNotIn('fixture-key',(root/'receipt.json').read_text());self.assertFalse((root/'extraction.json').exists())
    def test_migration_allows_completed_zero_job_scheduled_run(self):
        from scripts.run_gemini_daily import recover
        from unittest.mock import patch
        import os,json
        def gh(path):
            if '/runs?' in path:return dict(total_count=1,workflow_runs=[dict(id=41,run_number=1,status='completed',conclusion='skipped')])
            if '/artifacts?' in path:return dict(total_count=0,artifacts=[])
            if '/jobs?' in path:return dict(total_count=0,jobs=[])
            raise AssertionError(path)
        with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,dict(GITHUB_RUN_ID='42',GITHUB_RUN_ATTEMPT='1',GITHUB_REPOSITORY='kco994553-star/lol-coach'),clear=True):
            def legacy(directory):
                directory.mkdir(parents=True);(directory/'quota-ledger.json').write_text(json.dumps(self.ledger));return dict(status='FOUND')
            with patch('scripts.run_gemini_daily.gh_json',side_effect=gh),patch('scripts.run_gemini_daily.legacy_recovery',side_effect=legacy):
                state,quota=recover(Path(temp),self.config,dict(project_name='lol-coach'),self.now)
            self.assertEqual(state,self.state);self.assertEqual(quota,self.ledger)

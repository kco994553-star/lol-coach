"""Injected HTTP fixtures only: TEST, zero actual external acquisitions."""
import copy
import importlib
import importlib.util
from datetime import datetime,timezone
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

VIDEO='abcdefghijk'
CHANNEL='UC'+'a'*22
NOW=1791676800


def config():
    return dict(schema_version='expert.channels.v1',channels=[dict(channel_id=CHANNEL,name='TEST teaching channel',
        speaker='CLAIMED_SPEAKER',speaker_verified=True,main_position='MID',language='ko',uploads_playlist_id='UU'+'a'*22,
        content_grade='L',enabled=True)],
        topics=['웨이브','wave'],min_duration_seconds=60,max_duration_seconds=1800,max_videos_per_run=2)


def policy():
    return dict(free_tier_confirmed=True,entitlement_confirmed=True,quota_exclusive_confirmed=True,
                initial_zero_usage_confirmed=True,billing_tier='FREE_TIER')


def claim(timestamp='01:00'):
    return dict(timestamp=timestamp,paraphrase='TEST synthetic wave explanation',champion='UNKNOWN',position='MID',
        stage='UNKNOWN',conditions=[],context='EXPLANATION',measurable=False)


class Transport:
    def __init__(self,gemini=None):
        self.calls=[];self.gemini=gemini or dict(object='interaction',status='completed',steps=[
            dict(type='model_output',content=[dict(type='text',text=json.dumps({'claims':[claim()]}))])])

    def __call__(self,method,url,headers,body,timeout,max_bytes):
        self.calls.append((method,url,copy.deepcopy(headers),copy.deepcopy(body)))
        if '/playlistItems?' in url:
            return 200,{},dict(items=[dict(contentDetails=dict(videoId=VIDEO))])
        if '/channels?' in url:
            return 200,{},dict(items=[dict(id=CHANNEL,contentDetails=dict(relatedPlaylists=dict(uploads='UU'+'a'*22)))])
        if '/videos?' in url:
            return 200,{},dict(items=[dict(id=VIDEO,snippet=dict(title='TEST 웨이브 설명',channelId=CHANNEL,
                channelTitle='TEST teaching channel',publishedAt='2026-10-10T00:00:00Z',liveBroadcastContent='none'),
                contentDetails=dict(duration='PT10M'),status=dict(privacyStatus='public',uploadStatus='processed'))])
        if '/interactions' in url:return 200,{},self.gemini
        raise AssertionError('unexpected fixture URL')


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('coach_v1.expert_collector'),'Q19 collector missing')
        self.module=importlib.import_module('coach_v1.expert_collector')

    def collector(self,http=None,**kwargs):
        return self.module.ExpertCollector(youtube_api_key='TEST_YOUTUBE_KEY',gemini_api_key='TEST_GEMINI_KEY',
            transport=http or Transport(),clock=lambda:NOW,policy=kwargs.pop('policy',policy()),**kwargs)

    def test_default_empty_channels_blocks_without_any_network(self):
        http=Transport();c=self.collector(http);cfg=config();cfg['channels']=[]
        plan=c.prepare(cfg)
        self.assertEqual(plan['status'],'BLOCKED_EXTERNAL');self.assertEqual(http.calls,[])

    def test_all_attestations_and_keys_required_before_dispatch(self):
        for key in ('free_tier_confirmed','entitlement_confirmed','quota_exclusive_confirmed','initial_zero_usage_confirmed'):
            p=policy();p[key]=False;http=Transport();plan=self.collector(http,policy=p).prepare(config())
            self.assertEqual(plan['status'],'BLOCKED_EXTERNAL');self.assertEqual(http.calls,[])
        c=self.module.ExpertCollector(transport=Transport(),clock=lambda:NOW,policy=policy())
        self.assertEqual(c.prepare(config())['status'],'BLOCKED_EXTERNAL')
        p=policy();p['billing_tier']='PAID';http=Transport();c=self.collector(http,policy=p)
        self.assertEqual(c.prepare(config())['status'],'BLOCKED_PAYMENT');self.assertEqual(http.calls,[])

    def test_reserve_precedes_gemini_and_failed_persistence_blocks(self):
        http=Transport();c=self.collector(http);plan=c.prepare(config())
        self.assertEqual(plan['status'],'RESERVED');self.assertEqual(plan['ledger']['reservations'][0]['seconds'],600)
        self.assertFalse(any('/interactions' in call[1] for call in http.calls))
        result=c.process(plan,reservation_persisted=False)
        self.assertEqual(result['status'],'BLOCKED_EXTERNAL')
        self.assertFalse(any('/interactions' in call[1] for call in http.calls))

    def test_valid_nonempty_artifact_source_unknown_speaker_and_pinned_wire(self):
        http=Transport();c=self.collector(http);plan=c.prepare(config());result=c.process(plan,reservation_persisted=True)
        self.assertEqual(result['status'],'READY');self.assertEqual(len(result['artifacts']),1)
        artifact=result['artifacts'][0]
        self.assertEqual(artifact['video']['speaker'],'UNKNOWN');self.assertFalse(artifact['video']['speaker_verified'])
        self.assertIsNone(artifact['video']['upload_date']);self.assertEqual(artifact['video']['published_at'],'2026-10-10T00:00:00Z')
        self.assertEqual(artifact['claims'][0]['independent_group_id'],'YOUTUBE:'+VIDEO)
        self.assertEqual(result['ledger']['processed_video_ids'],[VIDEO])
        self.assertEqual(result['publication_status'],'PUBLICATION_DEFERRED')
        method,url,headers,body=http.calls[-1]
        self.assertEqual((method,url),('POST','https://generativelanguage.googleapis.com/v1beta/interactions'))
        self.assertEqual(body['model'],'gemini-3.8-flash');self.assertFalse(body['store']);self.assertFalse(body['stream'])
        self.assertEqual(body['response_format']['mime_type'],'application/json');self.assertNotIn('tools',body)
        self.assertEqual(headers['x-goog-api-key'],'TEST_GEMINI_KEY')
        text=json.dumps(result)
        for forbidden in ('TEST_GEMINI_KEY','TEST_YOUTUBE_KEY','CLAIMED_SPEAKER','model_output'):
            self.assertNotIn(forbidden,text)
        self.assertTrue(all('key=' not in call[1] for call in http.calls))

    def test_failure_empty_or_wrong_timestamp_never_processed_and_reservation_charged(self):
        for content in ({'claims':[]},{'claims':[claim('99:59')]},{'claims':[claim('bad')]},['wrong'],{'claims':'bad'}):
            response=dict(status='completed',steps=[dict(type='model_output',content=[dict(type='text',text=json.dumps(content))])])
            c=self.collector(Transport(response));plan=c.prepare(config());result=c.process(plan,reservation_persisted=True)
            self.assertNotEqual(result['status'],'READY');self.assertEqual(result['artifacts'],[])
            self.assertEqual(result['ledger']['processed_video_ids'],[])
            self.assertEqual(result['ledger']['reservations'],plan['ledger']['reservations'])

    def test_ambiguous_or_changed_response_is_rejected(self):
        for response in ({'status':'running','steps':[]},{'status':'completed','outputs':[]},
                         {'status':'completed','steps':[{'type':'model_output','content':[{'type':'text','text':'{}'},{'type':'text','text':'{}'}]}]}):
            c=self.collector(Transport(response));result=c.process(c.prepare(config()),reservation_persisted=True)
            self.assertEqual(result['status'],'FAILED_FORMAT');self.assertEqual(result['artifacts'],[])

    def test_rolling_budget_and_known_history_fail_closed(self):
        http=Transport();c=self.collector(http);plan=c.prepare(config());ledger=copy.deepcopy(plan['ledger'])
        ledger['initialized_at']=NOW-100000
        ledger['reservations']=[dict(video_id='zyxwvutsrqp',seconds=28800,reserved_at=NOW-86399,reservation_id='1'*64)]
        plan=c.prepare(config(),ledger)
        self.assertEqual(plan['status'],'BLOCKED_EXTERNAL')
        ledger['reservations'][0]['reserved_at']=NOW-87361
        self.assertEqual(c.prepare(config(),ledger)['status'],'RESERVED')
        self.assertEqual(c.prepare(config(),None,ledger_history='UNKNOWN')['status'],'BLOCKED_EXTERNAL')
        with self.assertRaises(ValueError):c.prepare(config(),{'corrupt':'state'})

    def test_duplicate_reserved_or_processed_video_is_not_dispatched_again(self):
        c=self.collector();plan=c.prepare(config())
        self.assertEqual(c.prepare(config(),plan['ledger'])['status'],'NO_ELIGIBLE_VIDEOS')
        result=c.process(plan,reservation_persisted=True)
        self.assertEqual(c.prepare(config(),result['ledger'])['status'],'NO_ELIGIBLE_VIDEOS')

    def test_tampered_plan_or_expired_reservation_blocks_before_gemini(self):
        for mutate in (lambda p:p['ledger']['reservations'][0].update(seconds=1),
                       lambda p:p['videos'][0].update(url='https://attacker.invalid/video'),
                       lambda p:p.update(created_at=NOW-901)):
            http=Transport();c=self.collector(http);plan=c.prepare(config());mutate(plan)
            with self.assertRaises(ValueError):c.process(plan,reservation_persisted=True)
            self.assertFalse(any('/interactions' in x[1] for x in http.calls))

    def test_blocked_plan_cannot_inject_private_reason_into_public_receipt(self):
        c=self.collector();cfg=config();cfg['channels']=[];plan=c.prepare(cfg)
        plan['reason']='PRIVATE_PROVIDER_BODY_WITH_KEY'
        with self.assertRaises(ValueError):c.process(plan)

    def test_http_client_failure_no_retry_no_body_or_key_leak(self):
        class Bad(Transport):
            def __call__(self,*args):
                if '/interactions' in args[1]:
                    self.calls.append(args);return 403,{},b'PRIVATE_BODY TEST_GEMINI_KEY'
                return super().__call__(*args)
        http=Bad();c=self.collector(http);result=c.process(c.prepare(config()),reservation_persisted=True)
        self.assertEqual(result['status'],'BLOCKED_EXTERNAL')
        self.assertEqual(sum('/interactions' in x[1] for x in http.calls),1)
        self.assertNotIn('PRIVATE_BODY',json.dumps(result));self.assertNotIn('TEST_GEMINI_KEY',json.dumps(result))

    def test_no_key_query_bounded_requests_and_canonical_metadata(self):
        http=Transport();c=self.collector(http,max_requests=1);plan=c.prepare(config())
        self.assertEqual(plan['status'],'BLOCKED_EXTERNAL');self.assertEqual(len(http.calls),1)
        for field,value in [('privacyStatus','unlisted'),('uploadStatus','failed')]:
            class Metadata(Transport):
                def __call__(self,*args):
                    code,h,data=super().__call__(*args)
                    if '/videos?' in args[1]:data['items'][0]['status'][field]=value
                    return code,h,data
            self.assertEqual(self.collector(Metadata()).prepare(config())['status'],'NO_ELIGIBLE_VIDEOS')

    def test_config_ledger_schema_and_public_atomic_writer(self):
        for mutate in (lambda x:x.update(raw_secret='bad'),lambda x:x.update(max_videos_per_run=3),
                       lambda x:x['channels'][0].update(channel_id='not-a-channel')):
            cfg=config();mutate(cfg)
            with self.assertRaises(ValueError):self.collector().prepare(cfg)
        c=self.collector();result=c.process(c.prepare(config()),reservation_persisted=True)
        with tempfile.TemporaryDirectory() as d:
            self.module.write_public_result(Path(d),result)
            paths=list(Path(d).rglob('*.json'))
            self.assertEqual(len(list((Path(d)/'artifacts').glob('*.json'))),1)
            for path in paths:
                self.assertNotIn('TEST_GEMINI_KEY',path.read_text());json.loads(path.read_text())

    def test_recover_failed_run_reservation_and_reject_refunded_final_snapshot(self):
        c=self.collector();ledger=c.prepare(config())['ledger']
        runs=[dict(id=3,conclusion='failure'),dict(id=2,conclusion='success')]
        reserved=dict(id=10,name='expert-quota-reservation-3',created_at='2026-10-11T00:00:00Z',expired=False)
        artifacts=lambda run:[reserved] if run==3 else []
        recovered,receipt=self.module.recover_ledger_snapshot(runs,current_run_id=4,list_artifacts=artifacts,
            download_artifact=lambda run,artifact:ledger,now=NOW,reservation_expected=lambda run:False)
        self.assertEqual(receipt['status'],'FOUND');self.assertEqual(recovered,ledger)
        final=dict(id=11,name='expert-quota-final-3',created_at='2026-10-11T00:01:00Z',expired=False)
        refunded=copy.deepcopy(ledger);refunded['reservations']=[]
        recovered,receipt=self.module.recover_ledger_snapshot(runs,current_run_id=4,list_artifacts=lambda run:[reserved,final] if run==3 else [],
            download_artifact=lambda run,a:refunded if a['id']==11 else ledger,now=NOW)
        self.assertIsNone(recovered);self.assertEqual(receipt['status'],'UNKNOWN')
        recovered,receipt=self.module.recover_ledger_snapshot(runs,current_run_id=4,list_artifacts=lambda run:[],
            download_artifact=lambda *args:ledger,now=NOW,reservation_expected=lambda run:False)
        self.assertIsNone(recovered);self.assertEqual(receipt['status'],'ABSENT')
        self.assertEqual(receipt['reason'],'NO_PRIOR_LEDGER_OBSERVED')
        recovered,receipt=self.module.recover_ledger_snapshot(runs,current_run_id=4,list_artifacts=lambda run:[],
            download_artifact=lambda *args:ledger,now=NOW,reservation_expected=lambda run:True)
        self.assertIsNone(recovered);self.assertEqual(receipt['status'],'UNKNOWN')

    def test_missing_metadata_items_is_failure_not_empty_acquisition(self):
        class Missing(Transport):
            def __call__(self,*args):
                self.calls.append(args);return 200,{},dict(unexpected='not official items')
        result=self.collector(Missing()).prepare(config())
        self.assertEqual(result['status'],'BLOCKED_EXTERNAL')

    def test_cancelled_expired_ambiguous_and_corrupt_recovery_blocks(self):
        ledger=self.collector().prepare(config())['ledger']
        runs=[dict(id=2,conclusion='cancelled'),dict(id=1,conclusion='success')]
        metadata=lambda run:dict(id=run*10,name='expert-quota-reservation-'+str(run),created_at='2026-10-11T00:00:00Z',expired=False)
        for list_artifacts,download in (
            (lambda run:[metadata(run)],lambda *args:ledger),
            (lambda run:[dict(metadata(run),expired=True)] if run==2 else [],lambda *args:ledger),
            (lambda run:[metadata(run)] if run==2 else [],lambda *args:{'invalid':'state'})):
            result,receipt=self.module.recover_ledger_snapshot(runs,current_run_id=3,list_artifacts=list_artifacts,download_artifact=download,now=NOW)
            self.assertIsNone(result);self.assertEqual(receipt['status'],'UNKNOWN')

    def test_disabled_channel_never_queried_and_cli_safe_blocked_receipt(self):
        cfg=config();cfg['channels'][0].update(content_grade='P',enabled=False)
        http=Transport();self.collector(http).prepare(cfg);self.assertEqual(http.calls,[])
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'config.json';path.write_text(json.dumps(config()))
            result=subprocess.run(['python','scripts/collect_expert_claims.py','--phase','reserve','--config',str(path),
                '--output-dir',str(Path(d)/'output')],env={'PATH':os.environ['PATH']},capture_output=True,text=True,check=False)
            self.assertEqual(result.returncode,0)
            receipt=json.loads((Path(d)/'output/receipt.json').read_text())
            self.assertEqual(receipt['status'],'BLOCKED_EXTERNAL');self.assertEqual(receipt['request_count'],0)
            self.assertEqual(list((Path(d)/'output').glob('artifacts/*.json')),[])

    def test_runtime_proof_fallback_expiry_and_explicit_false_override(self):
        runtime=dict(schema_version='expert.runtime.v1',project_name='lol-coach',confirmation_source='USER_QUEUE_V1.6_2026-10-11',
            confirmed_at='2026-10-11T00:00:00Z',free_tier_confirmed=True,entitlement_checked_at='2026-10-11',
            quota_exclusive_confirmed=True,initial_zero_usage_confirmed=True)
        self.assertTrue(hasattr(self.module,'policy_from_runtime'),'runtime source adapter missing')
        p=self.module.policy_from_runtime(runtime,{},now=NOW)
        self.assertEqual(p,policy())
        p=self.module.policy_from_runtime(runtime,{'GEMINI_FREE_TIER_CONFIRMED':'false'},now=NOW)
        self.assertFalse(p['free_tier_confirmed'])
        p=self.module.policy_from_runtime(runtime,{},now=NOW+86400)
        self.assertFalse(p['entitlement_confirmed'])
        p=self.module.policy_from_runtime(runtime,{},now=NOW+86401)
        self.assertFalse(p['initial_zero_usage_confirmed'])
        bad=copy.deepcopy(runtime);bad['raw_key']='PRIVATE'
        with self.assertRaises(ValueError):self.module.policy_from_runtime(bad,{},now=NOW)

    def test_late_dispatch_reservation_remains_charged_for_rolling_day(self):
        class EightHour(Transport):
            video_id=VIDEO
            def __call__(self,*args):
                code,h,data=super().__call__(*args)
                if '/playlistItems?' in args[1]:data['items'][0]['contentDetails']['videoId']=self.video_id
                if '/videos?' in args[1]:
                    data['items'][0]['id']=self.video_id;data['items'][0]['contentDetails']['duration']='PT8H'
                return code,h,data
        cfg=config();cfg['max_duration_seconds']=28800;clock=[NOW];http=EightHour()
        c=self.module.ExpertCollector(youtube_api_key='TEST_YOUTUBE_KEY',gemini_api_key='TEST_GEMINI_KEY',transport=http,clock=lambda:clock[0],policy=policy())
        plan=c.prepare(cfg);clock[0]=NOW+900;result=c.process(plan,reservation_persisted=True)
        self.assertEqual(result['status'],'READY')
        http.video_id='zyxwvutsrqp';clock[0]=NOW+86401
        self.assertEqual(c.prepare(cfg,result['ledger'])['status'],'BLOCKED_EXTERNAL')

    def test_description_topics_are_read_only_and_not_published(self):
        class Description(Transport):
            def __call__(self,*args):
                code,h,data=super().__call__(*args)
                if '/videos?' in args[1]:
                    data['items'][0]['snippet'].update(title='TEST unrelated title',description='PRIVATE_DESCRIPTION 웨이브')
                return code,h,data
        c=self.collector(Description());plan=c.prepare(config())
        self.assertEqual(plan['status'],'RESERVED');self.assertNotIn('PRIVATE_DESCRIPTION',json.dumps(plan))


if __name__=='__main__':unittest.main()

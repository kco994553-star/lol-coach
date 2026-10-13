"""Authorised staged video diagnosis with authored offline HTTP fixtures only."""
import copy
import importlib
import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import os
from tests_expert.test_collector import Transport

from coach_v1.expert_collector import ENTITLEMENT_URLS, RESPONSE_SCHEMA, CAP
from tests_expert.test_collector import policy

NOW=1791889200
VIDEO='9hE5-98ZeCg'
AUTH='USER_PRO_REFERENCE_RESUME_2026-10-13'


def proof():
    return dict(status='VERIFIED_FREE',checked_at='2026-10-13',model='gemini-3.6-flash',
        sources=[dict(url=url,sha256='a'*64) for url in ENTITLEMENT_URLS],reasons=['DOCUMENTED_FREE_ENTITLEMENT'])


def video():
    return dict(id=VIDEO,url='https://www.youtube.com/watch?v='+VIDEO,duration_seconds=900,
        public_confirmed=True,metadata_checked_at=NOW)


def ledger():
    return dict(schema_version='expert.quota-ledger.v1',initialized_at=NOW-100,
        reservations=[dict(video_id='oldvideo001',seconds=7396,reserved_at=NOW-50,reservation_id='b'*64)],processed_video_ids=[])


def prior():
    return dict(schema_version='expert.complete-error.v1',provider='GEMINI',http_status=400,error_code=400,
        error_status='INVALID_ARGUMENT',error_message='Request contains an invalid argument.',message_complete=True,
        source_run_id=38387587260,source_artifact_id=11807017561,
        source_path='evidence/queue/v20/actual-gemini/expert-final/diagnostics.json',source_sha256='a'*64,
        provenance='PRIOR_SAFE_DIAGNOSTIC_MESSAGE_SHORTER_THAN_512_CHAR_LIMIT_NO_TRUNCATION',
        raw_error_body_retained=False,recorded_before_new_attempt=True,authorization=AUTH)


def response(text='PRIVATE_DIAGNOSTIC_OUTPUT_NOT_RETAINED'):
    return dict(status='completed',steps=[dict(type='model_output',content=[dict(type='text',text=text)])])


class OfficialMetadataTransport(Transport):
    def __call__(self,*args):
        code,headers,data=super().__call__(*args)
        if '/videos?' in args[1]:data['items'][0]['id']=VIDEO
        return code,headers,data


class DiagnosticTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec('coach_v1.expert_video_diagnostic'),'staged diagnostic missing')
        return importlib.import_module('coach_v1.expert_video_diagnostic')

    def collector(self,http=None,**kwargs):
        self.clock=[NOW];self.calls=[]
        def transport(*args):
            self.calls.append(copy.deepcopy(args))
            return (http or (lambda *a:(200,{},response())))(*args)
        return self.module().ExpertVideoDiagnostic(gemini_api_key='TEST_GEMINI_KEY',youtube_api_key='TEST_YOUTUBE_KEY',
            policy=kwargs.pop('policy',policy()),entitlement_proof=kwargs.pop('entitlement_proof',proof()),
            transport=transport,clock=lambda:self.clock[0],**kwargs)

    def prepare(self,c,old=None,previous=None,**kwargs):
        return c.prepare_stage(video(),old or ledger(),prior(),previous_result=previous,authorization=AUTH,**kwargs)

    def success(self,c,plan):
        return c.process_stage(plan,reservation_artifact_id='123')

    def test_official_baseline_exact_shape_no_clip_format_or_extra_fields(self):
        c=self.collector();p=self.prepare(c);self.assertEqual(p['status'],'RESERVED');self.success(c,p)
        method,url,headers,body,timeout,maximum=self.calls[0]
        self.assertEqual(method,'POST');self.assertEqual(url,'https://generativelanguage.googleapis.com/v1beta/interactions')
        self.assertEqual(body,{'model':'gemini-3.6-flash','input':[{'type':'text','text':'Please summarize the video in 3 sentences.'},
            {'type':'video','uri':video()['url']}]})
        self.assertEqual(headers['x-goog-api-key'],'TEST_GEMINI_KEY');self.assertEqual(timeout,600)

    def test_each_stage_reserves_full_duration_and_changes_only_one_argument_family(self):
        c=self.collector(lambda *a:(200,{},response('{"claims":[]}')));old=ledger();p=self.prepare(c,old)
        self.assertEqual(p['ledger']['reservations'][:-1],old['reservations']);self.assertEqual(p['ledger']['reservations'][-1]['seconds'],900)
        result=self.success(c,p)
        for stage in ('CLIPPING','RESPONSE_FORMAT'):
            self.clock[0]+=15
            p=self.prepare(c,result['ledger'],result);self.assertEqual(p['stage'],stage)
            result=self.success(c,p)
        bodies=[call[3] for call in self.calls]
        expected=copy.deepcopy(bodies[0]);expected['input'][1]['processing']={'type':'static','start_offset':'0s','end_offset':'600s'}
        self.assertEqual(bodies[1],expected)
        expected['response_format']={'type':'text','mime_type':'application/json','schema':RESPONSE_SCHEMA}
        self.assertEqual(bodies[2],expected)
        self.assertEqual(sum(r['seconds'] for r in result['ledger']['reservations']),7396+2700)
        self.assertEqual(len(self.calls),3);self.assertEqual(result['request_count'],3)
        self.assertNotIn('PRIVATE_DIAGNOSTIC_OUTPUT',json.dumps(result))
        self.assertTrue(result['manual_summary_default']);self.assertTrue(result['automatic_collection_paused'])
        self.assertEqual(self.prepare(c,result['ledger'],result)['reason'],'ALL_AUTHORIZED_STAGES_FINISHED')

    def test_missing_persisted_ack_never_dispatches_and_keeps_reservation(self):
        c=self.collector();p=self.prepare(c);r=c.process_stage(p,reservation_artifact_id=None)
        self.assertEqual(self.calls,[]);self.assertEqual(r['reason'],'RESERVATION_PERSISTENCE_NOT_CONFIRMED')
        self.assertEqual(r['ledger'],p['ledger'])

    def test_failure_never_opens_next_stage_and_never_refunds(self):
        for code in (400,401,402,403,429,503):
            c=self.collector(lambda *a:(code,{},dict(error=dict(code=code,status='INVALID_ARGUMENT',message='complete safe message'))))
            p=self.prepare(c);r=self.success(c,p);after=self.prepare(c,r['ledger'],r)
            self.assertEqual(len(self.calls),1);self.assertEqual(r['ledger'],p['ledger']);self.assertEqual(after['status'],'BLOCKED_EXTERNAL')
            self.assertTrue(r['automatic_collection_paused']);self.assertTrue(r['manual_summary_default'])

    def test_complete_error_is_redacted_before_retention_and_never_truncated(self):
        m=self.module();text=('complete diagnostic detail '*60)+' api_key=TEST_GEMINI_KEY puuid="opaque-private-id" model field: response_format FINAL_TAIL'
        error=m.complete_error_receipt(400,{'error':{'code':400,'status':'INVALID_ARGUMENT','message':text}},
            source_run_id=1,source_artifact_id=2,secrets=('TEST_GEMINI_KEY',))
        self.assertTrue(error['message_complete']);self.assertGreater(len(error['error_message']),512)
        self.assertTrue(error['error_message'].endswith('FINAL_TAIL'));self.assertIn('response_format',error['error_message'])
        self.assertNotIn('TEST_GEMINI_KEY',json.dumps(error));self.assertNotIn('opaque-private-id',json.dumps(error))
        self.assertFalse(error['raw_error_body_retained'])

    def test_unavailable_or_previously_truncated_message_blocks_baseline(self):
        for mutate in (lambda e:e.update(message_complete=False),lambda e:e.update(recorded_before_new_attempt=False),
                       lambda e:e.update(error_message=None),lambda e:e.update(authorization='UNKNOWN')):
            c=self.collector();e=prior();mutate(e)
            p=c.prepare_stage(video(),ledger(),e,authorization=AUTH)
            self.assertEqual(p['status'],'BLOCKED_EXTERNAL');self.assertEqual(self.calls,[])
            self.assertEqual(p['ledger'],ledger())

    def test_stale_unknown_paid_or_wrong_model_proof_never_calls(self):
        for mutate in (lambda p:p.update(checked_at='2026-10-12'),
                       lambda p:p.update(status='UNKNOWN',reasons=['PRICING_SOURCE_UNAVAILABLE']),
                       lambda p:p.update(status='PAID_REQUIRED',reasons=['FREE_TIER_POSITIVE_PRICE'])):
            p=proof();mutate(p);c=self.collector(entitlement_proof=p)
            plan=self.prepare(c);self.assertEqual(plan['status'],'BLOCKED_EXTERNAL');self.assertEqual(self.calls,[])
        p=proof();p['model']='gemini-3.8-flash'
        with self.assertRaises(ValueError):self.collector(entitlement_proof=p)

    def test_historically_charged_id_is_not_a_new_baseline(self):
        c=self.collector();old=ledger();old['reservations'][0].update(video_id=VIDEO,reserved_at=NOW-100)
        p=self.prepare(c,old);self.assertEqual(p['reason'],'VIDEO_ALREADY_CHARGED');self.assertEqual(self.calls,[])

    def test_same_stage_cannot_dispatch_twice(self):
        c=self.collector();p=self.prepare(c);self.success(c,p);r=self.success(c,p)
        self.assertEqual(len(self.calls),1);self.assertEqual(r['reason'],'DISPATCH_ALREADY_CLAIMED')

    def test_continuation_cannot_switch_source_skip_stage_or_rewrite_ledger(self):
        c=self.collector();p=self.prepare(c);r=self.success(c,p);self.clock[0]+=15
        for v,old,stage in [(dict(video(),id='different01',url='https://www.youtube.com/watch?v=different01'),r['ledger'],None),
                            (video(),ledger(),None),(video(),r['ledger'],'RESPONSE_FORMAT')]:
            after=c.prepare_stage(v,old,prior(),previous_result=r,authorization=AUTH,stage=stage)
            self.assertEqual(after['status'],'BLOCKED_EXTERNAL')
        self.assertEqual(len(self.calls),1)

    def test_quota_cap_and_stale_public_metadata_block_without_reserving(self):
        c=self.collector();old=ledger();old['reservations'][0]['seconds']=CAP
        p=self.prepare(c,old);self.assertEqual(p['reason'],'ROLLING_VIDEO_BUDGET_EXHAUSTED');self.assertEqual(p['ledger'],old)
        v=video();v['metadata_checked_at']=NOW-901
        p=c.prepare_stage(v,ledger(),prior(),authorization=AUTH);self.assertEqual(p['status'],'BLOCKED_EXTERNAL');self.assertEqual(self.calls,[])

    def test_rate_spacing_does_not_consume_a_new_reservation(self):
        c=self.collector();r=self.success(c,self.prepare(c));p=self.prepare(c,r['ledger'],r)
        self.assertEqual(p['reason'],'STAGE_RATE_WINDOW');self.assertEqual(p['ledger'],r['ledger'])

    def test_tampered_body_digest_or_charge_never_dispatches(self):
        c=self.collector();p=self.prepare(c)
        for mutate in (lambda p:p.update(request_sha256='0'*64),lambda p:p['ledger']['reservations'][-1].update(seconds=1),
                       lambda p:p.update(stage='RESPONSE_FORMAT')):
            bad=copy.deepcopy(p);mutate(bad)
            with self.assertRaises(ValueError):self.success(c,bad)
        self.assertEqual(self.calls,[])

    def test_malformed_incomplete_or_unbounded_response_is_terminal(self):
        for raw in (dict(status='in_progress',steps=[]),dict(status='completed',outputs=[]),b'not JSON',
                    dict(status='completed',steps=[dict(type='model_output',content=[dict(type='image',data='PRIVATE')])])):
            c=self.collector(lambda *a:(200,{},raw));p=self.prepare(c);r=self.success(c,p)
            self.assertEqual(r['status'],'BLOCKED_EXTERNAL');self.assertTrue(r['automatic_collection_paused'])
            self.assertNotIn('PRIVATE',json.dumps(r));self.assertEqual(len(self.calls),1)

    def test_cli_entrypoint_is_available(self):
        self.assertIsNotNone(importlib.util.find_spec('scripts.diagnose_expert_video'),'staged CLI missing')

    def test_cli_pure_discovery_and_three_prepared_stages_no_hidden_probe_or_replay(self):
        self.assertIsNotNone(importlib.util.find_spec('scripts.diagnose_expert_video'))
        from scripts import diagnose_expert_video as cli
        from coach_v1 import expert_collector
        m=self.module();calls=[];tube=OfficialMetadataTransport();clock=[NOW]
        def provider(*args):calls.append(copy.deepcopy(args));return 200,{},response('{"claims":[]}')
        env=dict(GEMINI_API_KEY='TEST_GEMINI_KEY',YOUTUBE_API_KEY='TEST_YOUTUBE_KEY',
            GEMINI_FREE_TIER_CONFIRMED='true',GEMINI_QUOTA_EXCLUSIVE_CONFIRMED='true')
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'ledger.json').write_text(json.dumps(ledger()));(root/'prior.json').write_text(json.dumps(prior()))
            from tests_expert.test_collector import config
            (root/'config.json').write_text(json.dumps(config()))
            common=['--authorization',AUTH,'--prior-error',str(root/'prior.json')]
            with patch.dict(os.environ,env,clear=True),patch.object(m,'_transport',provider),patch.object(expert_collector,'_transport',tube):
                invoke=lambda args:cli.main(args,entitlement_verifier=lambda model:proof(),clock=lambda:clock[0])
                code=invoke(['--phase','discover','--config',str(root/'config.json'),'--ledger',str(root/'ledger.json'),
                    '--output-dir',str(root/'discovered')]+common)
                self.assertEqual(code,0);self.assertEqual(calls,[])
                self.assertTrue(all(c[0]=='GET' for c in tube.calls))
                previous=None;old=root/'ledger.json'
                for stage in ('BASELINE','CLIPPING','RESPONSE_FORMAT'):
                    prepare=root/(stage+'-prepare');process=root/(stage+'-process')
                    args=['--phase','prepare','--stage',stage,'--video',str(root/'discovered/selected-video.json'),
                        '--ledger',str(old),'--output-dir',str(prepare)]+common
                    if previous:args+=['--previous-result',str(previous)]
                    self.assertEqual(invoke(args),0)
                    self.assertEqual(json.loads((prepare/'plan.json').read_text())['status'],'RESERVED')
                    args=['--phase','process','--plan',str(prepare/'plan.json'),'--reservation-artifact-id','777','--output-dir',str(process)]+common
                    self.assertEqual(invoke(args),0)
                    self.assertEqual(invoke(args),0)
                    previous=process/'result.json';old=process/'quota-ledger.json';clock[0]+=15
                self.assertEqual(len(calls),3)
                for p in root.rglob('*.json'):
                    self.assertNotIn('TEST_GEMINI_KEY',p.read_text());self.assertNotIn('PRIVATE_DIAGNOSTIC_OUTPUT',p.read_text())

    def test_result_validator_rejects_private_reason_and_fake_undispatched_status(self):
        c=self.collector();r=self.success(c,self.prepare(c));m=self.module()
        bad=copy.deepcopy(r);bad.update(status='BLOCKED_EXTERNAL',reason='PRIVATE_PROVIDER_BODY')
        bad['stage_receipts'][-1]['status']='BLOCKED_EXTERNAL'
        with self.assertRaises(ValueError):m.validate_stage_result(bad)
        bad=copy.deepcopy(r);bad['stage_receipts'][-1].update(request_count=0,status='BLOCKED_EXTERNAL')
        bad.update(status='BLOCKED_EXTERNAL',reason='NETWORK_FAILURE',request_count=0)
        with self.assertRaises(ValueError):m.validate_stage_result(bad)

    def test_oversize_error_is_unavailable_not_a_truncated_complete_message(self):
        m=self.module();e=m.complete_error_receipt(400,b'{"error":{"message":"'+b'x'*(m.MAX_RESPONSE_BYTES+1)+b'"}}')
        self.assertFalse(e['message_complete']);self.assertIsNone(e['error_message'])

    def test_failed_later_stage_localizes_added_family_but_does_not_guess_field(self):
        calls=[0]
        def provider(*args):
            calls[0]+=1
            if calls[0]==1:return 200,{},response()
            return 400,{},dict(error=dict(code=400,status='INVALID_ARGUMENT',message='Unlocalized complete message'))
        c=self.collector(provider);r=self.success(c,self.prepare(c));self.clock[0]+=15
        r=self.success(c,self.prepare(c,r['ledger'],r))
        self.assertEqual(r['localized_change'],'VIDEO_PROCESSING');self.assertIsNone(r['exact_invalid_field'])
        self.assertEqual(r['error']['error_message'],'Unlocalized complete message');self.assertTrue(r['error']['message_complete'])

    def test_unbounded_success_body_is_terminal_without_raw_retention(self):
        m=self.module();c=self.collector(lambda *a:(200,{},b'x'*(m.MAX_RESPONSE_BYTES+1)))
        r=self.success(c,self.prepare(c));self.assertEqual(r['status'],'BLOCKED_EXTERNAL')
        self.assertEqual(r['reason'],'MALFORMED_OR_INCOMPLETE_RESPONSE');self.assertIsNone(r['error'])

    def test_selected_video_id_and_url_are_removed_from_complete_error(self):
        text='Cannot access video '+VIDEO+' at '+video()['url']+' FINAL_TAIL'
        c=self.collector(lambda *a:(400,{},dict(error=dict(code=400,status='INVALID_ARGUMENT',message=text))))
        r=self.success(c,self.prepare(c));message=r['error']['error_message']
        self.assertNotIn(VIDEO,message);self.assertNotIn(video()['url'],message)
        self.assertTrue(message.endswith('FINAL_TAIL'));self.assertTrue(r['error']['message_complete'])

    def test_metadata_budget_reserves_three_slots_for_authorized_video_stages(self):
        c=self.collector();self.assertEqual(c.metadata_collector.max_requests,47)

    def test_redaction_expansion_does_not_discard_a_complete_bounded_error(self):
        m=self.module();text=(VIDEO+' ')*125000+'FINAL_TAIL'
        e=m.complete_error_receipt(400,dict(error=dict(code=400,status='INVALID_ARGUMENT',message=text)),identifiers=(VIDEO,))
        self.assertTrue(e['message_complete']);self.assertGreater(len(e['error_message'].encode()),m.MAX_RESPONSE_BYTES)
        try:m.validate_complete_error(e)
        except ValueError:self.fail('redaction expansion must preserve the complete message')
        self.assertTrue(e['error_message'].endswith('FINAL_TAIL'))

    def test_discovery_queries_only_literal_official_example_metadata(self):
        import urllib.parse
        from tests_expert.test_collector import config
        c=self.collector();tube=OfficialMetadataTransport();c.metadata_collector.transport=tube
        selected=c.discover(config(),ledger(),prior())
        self.assertEqual(selected['status'],'SELECTED');self.assertEqual(selected['video']['id'],VIDEO)
        self.assertEqual(selected['video']['url'],'https://www.youtube.com/watch?v=9hE5-98ZeCg')
        self.assertEqual(len(tube.calls),1);self.assertEqual(self.calls,[])
        self.assertIn('/videos?',tube.calls[0][1]);self.assertEqual(urllib.parse.parse_qs(urllib.parse.urlparse(tube.calls[0][1]).query)['id'],[VIDEO])

    def test_official_example_private_live_failed_or_overlong_is_not_substituted(self):
        from tests_expert.test_collector import config
        for field,value in [('privacyStatus','private'),('privacyStatus','unlisted'),('uploadStatus','failed'),
                            ('liveBroadcastContent','upcoming'),('duration','PT21M')]:
            c=self.collector();tube=OfficialMetadataTransport()
            def metadata(*args):
                code,headers,data=tube(*args)
                if '/videos?' in args[1]:
                    part='contentDetails' if field=='duration' else 'snippet' if field=='liveBroadcastContent' else 'status'
                    data['items'][0][part][field]=value
                return code,headers,data
            c.metadata_collector.transport=metadata
            selected=c.discover(config(),ledger(),prior())
            self.assertEqual(selected['status'],'BLOCKED_EXTERNAL');self.assertIsNone(selected['video']);self.assertEqual(self.calls,[])

    def test_charged_literal_example_blocks_before_metadata_and_never_selects_another(self):
        from tests_expert.test_collector import config
        c=self.collector();tube=OfficialMetadataTransport();c.metadata_collector.transport=tube
        old=ledger();old['reservations'][0]['video_id']=VIDEO
        selected=c.discover(config(),old,prior())
        self.assertEqual(selected['reason'],'VIDEO_ALREADY_CHARGED');self.assertIsNone(selected['video'])
        self.assertEqual(tube.calls,[]);self.assertEqual(self.calls,[])

    def test_unrelated_public_url_is_rejected_by_baseline_preparation(self):
        c=self.collector();v=video();v.update(id='freshvid001',url='https://www.youtube.com/watch?v=freshvid001')
        plan=c.prepare_stage(v,ledger(),prior(),authorization=AUTH)
        self.assertEqual(plan['status'],'BLOCKED_EXTERNAL');self.assertEqual(plan['ledger'],ledger());self.assertEqual(self.calls,[])


if __name__=='__main__':unittest.main()

"""Diagnosis and probes are injected fixtures; no external requests or credentials."""
import copy
import io
import json
import unittest
import urllib.error
from unittest.mock import Mock,patch

from coach_v1 import expert_collector as m
from tests_expert.test_collector import NOW,VIDEO,Transport,config,policy,is_text_probe,generated
from tests_expert.test_segments import Clips


def completed(text='TEST_OK'):
    return generated(text)


class ProbeHTTP(Clips):
    def __init__(self,status=200,response=None,**kwargs):
        super().__init__(**kwargs);self.status=status;self.response=response;self.probe_calls=0;self.probe_timeout=None

    def __call__(self,*args):
        body=args[3]
        if args[0]=='POST' and is_text_probe(body):
            self.probe_calls+=1;self.probe_timeout=args[4];self.calls.append(copy.deepcopy(args[:4]))
            if isinstance(self.response,Exception):raise self.response
            return self.status,{},completed() if self.response is None else self.response
        return super().__call__(*args)


def collector(http,clock=None,**kwargs):
    return m.ExpertCollector(youtube_api_key='TEST_YOUTUBE_KEY',gemini_api_key='TEST_GEMINI_KEY',
        transport=http,clock=lambda:NOW if clock is None else clock[0],policy=policy(),**kwargs)


class DiagnosticTests(unittest.TestCase):
    def test_structured_text_probe_matches_video_schema_without_video_or_response_retention(self):
        ordinary=ProbeHTTP();plain=collector(ordinary);plain.probe_text()
        h=ProbeHTTP(response=completed('{"claims":[]}'));c=collector(h);receipt=c.probe_text(structured=True)
        body=h.calls[0][3];default=ordinary.calls[0][3]
        expected=dict(responseMimeType='application/json',responseJsonSchema=m.RESPONSE_SCHEMA)
        self.assertEqual(body['generationConfig'],dict(candidateCount=1,**expected))
        self.assertEqual({k:v for k,v in body.items() if k not in ('contents','generationConfig')},
            {k:v for k,v in default.items() if k not in ('contents','generationConfig')})
        self.assertEqual([set(x) for x in body['contents'][0]['parts']],[{'text'}])
        self.assertNotIn('uri',json.dumps(body));self.assertIn(m.MODEL,h.calls[0][1])
        self.assertEqual(receipt['status'],'READY');self.assertEqual(receipt['input_kind'],'TEXT_ONLY')
        self.assertEqual(receipt['video_inputs'],0);self.assertNotIn('claims',json.dumps(receipt))
        self.assertEqual(c.request_counts,dict(TEXT_PROBE=1,VIDEO_CLIP=0,METADATA=0));self.assertLessEqual(h.probe_timeout,60)
        body['generationConfig']['responseJsonSchema']['required'].append('TEST_MUTATION')
        self.assertEqual(m.RESPONSE_SCHEMA['required'],['claims'])

    def test_structured_probe_format_failure_retains_literal_safe_diagnostics_and_no_video(self):
        h=ProbeHTTP(400,dict(error=dict(code='invalid_request',message='TEST format TEST_GEMINI_KEY')))
        c=collector(h);receipt=c.probe_text(structured=True)
        self.assertEqual(receipt['status'],'BLOCKED_EXTERNAL');self.assertEqual(receipt['http_status'],400)
        self.assertEqual(c.diagnostics[0]['error_code'],'invalid_request');self.assertIsNone(c.diagnostics[0]['error_status'])
        self.assertEqual(c.diagnostics[0]['http_status'],400);self.assertNotIn('TEST_GEMINI_KEY',json.dumps(c.diagnostics))
        self.assertEqual(c.request_counts,dict(TEXT_PROBE=1,VIDEO_CLIP=0,METADATA=0));self.assertEqual(h.model_calls,0)
        before=c.request_count
        with self.assertRaises(ValueError):c.probe_text(structured='true')
        self.assertEqual(c.request_count,before)

    def test_text_probe_http_failures_never_discover_reserve_or_request_video(self):
        for status in (400,401,403,429):
            h=ProbeHTTP(status,dict(error=dict(status='PERMISSION_DENIED',code='invalid_argument',
                message='Bad TEST_GEMINI_KEY https://example.invalid/?key=TEST_YOUTUBE_KEY')))
            records=[];c=collector(h,on_diagnostic=records.append);plan=c.prepare(config())
            self.assertEqual(plan['status'],'BLOCKED_EXTERNAL');self.assertEqual(h.probe_calls,1)
            self.assertEqual(h.model_calls,0);self.assertEqual(c.request_count,1)
            self.assertEqual(plan['ledger']['reservations'],[])
            self.assertEqual(plan['text_probe']['http_status'],status)
            self.assertEqual(records,c.diagnostics);self.assertEqual(records[0]['phase'],'TEXT_PROBE')
            self.assertEqual(records[0]['provider'],'GEMINI');self.assertEqual(records[0]['error_status'],'PERMISSION_DENIED')
            self.assertEqual(records[0]['error_code'],'invalid_argument')
            self.assertNotIn('TEST_GEMINI_KEY',json.dumps(records));self.assertNotIn('https://',json.dumps(records))

    def test_probe_success_receipt_contains_no_returned_text_or_video_and_reused_by_process(self):
        h=ProbeHTTP(response=completed('PRIVATE_TEXT_NOT_RETAINED'));c=collector(h)
        plan=c.prepare(config(),collection_mode='DIAGNOSTIC_FIRST_CLIP')
        self.assertEqual(plan['schema_version'],'expert.reservation-plan.v4')
        self.assertEqual(plan['collection_mode'],'DIAGNOSTIC_FIRST_CLIP')
        self.assertEqual(plan['text_probe'],dict(schema_version='expert.text-probe.v2',status='READY',reason=None,
            model=m.MODEL,checked_at=NOW,http_status=200,input_kind='TEXT_ONLY',video_inputs=0,api_route='GENERATE_CONTENT',attempt_count=1,retry_count=0))
        self.assertNotIn('PRIVATE_TEXT_NOT_RETAINED',json.dumps(plan));self.assertLessEqual(h.probe_timeout,60)
        result=c.process(plan,reservation_persisted=True)
        self.assertEqual(h.probe_calls,1);self.assertEqual(h.model_calls,1)
        self.assertEqual(c.request_counts,dict(TEXT_PROBE=1,VIDEO_CLIP=1,METADATA=2))
        self.assertEqual(c.request_count,sum(c.request_counts.values()))
        self.assertEqual(result['status'],'PARTIAL');self.assertEqual(result['ledger']['processed_video_ids'],[])
        self.assertEqual(result['ledger']['reservations'][0]['seconds'],1200)
        self.assertIn('SEGMENTED_EXTRACTION_INCOMPLETE',result['artifacts'][0]['claims'][0]['limitations'])

    def test_probe_network_and_malformed_results_fail_closed(self):
        for response,reason in [(TimeoutError('PRIVATE_EXCEPTION'),'NETWORK_TIMEOUT'),(b'not-json','MALFORMED_RESPONSE'),
            (completed(''),'MALFORMED_RESPONSE'),({'status':'running'},'MALFORMED_RESPONSE')]:
            h=ProbeHTTP(response=response);c=collector(h);plan=c.prepare(config())
            self.assertEqual(plan['status'],'BLOCKED_EXTERNAL');self.assertEqual(h.model_calls,0)
            self.assertEqual(plan['ledger']['reservations'],[]);self.assertEqual(c.diagnostics[0]['reason'],reason)
            self.assertNotIn('PRIVATE_EXCEPTION',json.dumps(c.diagnostics))

    def test_mode_or_bound_receipt_tampering_and_stale_probe_never_dispatch(self):
        for mutate in (lambda p:p.update(collection_mode='DIAGNOSTIC_FIRST_CLIP'),
            lambda p:p['text_probe'].update(model='other-model'),lambda p:p['text_probe'].update(checked_at=NOW-901),
            lambda p:p['text_probe'].update(checked_at=NOW-1),
            lambda p:p['text_probe'].update(video_inputs=1),lambda p:p['text_probe'].update(status='BLOCKED_EXTERNAL')):
            h=ProbeHTTP();c=collector(h);plan=c.prepare(config());mutate(plan)
            with self.assertRaises(ValueError):c.process(plan,reservation_persisted=True)
            self.assertEqual(h.model_calls,0)

    def test_full_mode_still_collects_two_clips_and_preserves_five_old_charges(self):
        rows=[dict(video_id=str(i).zfill(11),seconds=s,reserved_at=NOW-10,reservation_id=str(i)*64)
            for i,s in enumerate([1000,1000,1000,1298,2346],1)]
        ledger=dict(schema_version='expert.quota-ledger.v1',initialized_at=NOW-20,reservations=rows,processed_video_ids=[])
        before=m._canonical(ledger);h=ProbeHTTP();c=collector(h);plan=c.prepare(config(),ledger)
        result=c.process(plan,reservation_persisted=True)
        self.assertEqual(h.probe_calls,1);self.assertEqual(h.model_calls,2);self.assertEqual(result['status'],'READY')
        self.assertEqual(m._canonical(ledger),before);self.assertEqual(result['ledger']['reservations'][:5],rows)
        self.assertEqual(sum(x['seconds'] for x in result['ledger']['reservations']),6644+2400)

    def test_http_error_transport_reads_only_bounded_transient_selected_body(self):
        body=json.dumps({'error':{'status':'INVALID_ARGUMENT','code':'invalid_argument','message':'TEST error'}}).encode()
        error=urllib.error.HTTPError(m.GENERATE_CONTENT_URL,400,'PRIVATE_REASON',{},io.BytesIO(body))
        with patch.object(m.urllib.request,'build_opener') as opener:
            opener.return_value.open.side_effect=error
            code,_,raw=m._transport('POST',m.GENERATE_CONTENT_URL,{}, {'model':m.MODEL},60,1000000)
        self.assertEqual(code,400);self.assertEqual(raw,body)

    def test_network_has_null_status_and_malformed_clip_has_actual_200(self):
        for output,status,reason in [(TimeoutError('PRIVATE'),None,'NETWORK_TIMEOUT'),({'claims':'wrong'},200,'MALFORMED_RESPONSE')]:
            h=ProbeHTTP(outputs=[{'claims':[]},output]);records=[];c=collector(h,on_diagnostic=records.append)
            result=c.process(c.prepare(config()),reservation_persisted=True)
            self.assertEqual(result['ledger']['processed_video_ids'],[])
            self.assertEqual(records[-1]['phase'],'VIDEO_CLIP');self.assertEqual(records[-1]['http_status'],status)
            self.assertEqual(records[-1]['reason'],reason);self.assertIsNone(records[-1]['error_message'])

    def test_free_quota_gates_have_null_status_and_zero_requests(self):
        rows=[dict(video_id=VIDEO,seconds=28800,reserved_at=NOW,reservation_id='1'*64)]
        ledger=dict(schema_version='expert.quota-ledger.v1',initialized_at=NOW,reservations=rows,processed_video_ids=[])
        h=ProbeHTTP();c=collector(h);plan=c.prepare(config(),ledger)
        self.assertEqual(plan['status'],'BLOCKED_EXTERNAL');self.assertEqual(c.request_count,0)
        self.assertEqual(c.diagnostics[0]['reason'],'ROLLING_VIDEO_BUDGET_EXHAUSTED')
        self.assertIsNone(c.diagnostics[0]['http_status']);self.assertEqual(plan['ledger'],ledger)

    def test_oversized_or_nonjson_http_error_has_only_safe_selected_fields(self):
        for raw in (b'x'*(65536+1),b'<html>PRIVATE BODY TEST_GEMINI_KEY</html>'):
            h=ProbeHTTP(403,raw);c=collector(h);plan=c.prepare(config())
            self.assertEqual(plan['status'],'BLOCKED_EXTERNAL')
            self.assertEqual(c.diagnostics[0]['http_status'],403)
            for key in ('error_message','error_code','error_status'):self.assertIsNone(c.diagnostics[0][key])
            self.assertNotIn('PRIVATE',json.dumps(c.diagnostics));self.assertEqual(h.model_calls,0)

    def test_transport_oversized_http_200_retains_actual_status(self):
        response=Mock(status=200);response.read.return_value=b'x'*9
        with patch.object(m.urllib.request,'build_opener') as opener:
            opener.return_value.open.return_value.__enter__.return_value=response
            c=m.ExpertCollector(youtube_api_key='TEST_YOUTUBE_KEY',gemini_api_key='TEST_GEMINI_KEY',
                clock=lambda:NOW,policy=policy(),max_bytes=8)
            plan=c.prepare(config())
        self.assertEqual(plan['status'],'BLOCKED_EXTERNAL')
        self.assertEqual(plan['text_probe']['http_status'],200)
        self.assertEqual(c.diagnostics[0]['http_status'],200)
        self.assertEqual(c.diagnostics[0]['reason'],'RESPONSE_TOO_LARGE')
        self.assertEqual(c.request_counts,dict(TEXT_PROBE=1,VIDEO_CLIP=0,METADATA=0))
        self.assertEqual(plan['ledger']['reservations'],[])
        response.read.assert_called_once_with(9)

    def test_selected_transport_external_failure_preserves_response_status(self):
        def transport(*args):raise m._External('MALFORMED_RESPONSE',http_status=200)
        c=m.ExpertCollector(youtube_api_key='TEST_YOUTUBE_KEY',gemini_api_key='TEST_GEMINI_KEY',
            transport=transport,clock=lambda:NOW,policy=policy())
        receipt=c.probe_text()
        self.assertEqual(receipt['http_status'],200)
        self.assertEqual(c.diagnostics[0]['reason'],'MALFORMED_RESPONSE')
        self.assertEqual(c.diagnostics[0]['http_status'],200)

    def test_old_plans_rejected_and_short_diagnostic_can_complete(self):
        for version in ('expert.reservation-plan.v1','expert.reservation-plan.v2','expert.reservation-plan.v3'):
            h=ProbeHTTP();c=collector(h);plan=c.prepare(config());plan['schema_version']=version
            with self.assertRaises(ValueError):c.process(plan,reservation_persisted=True)
            self.assertEqual(h.model_calls,0)
        h=ProbeHTTP(duration=600);c=collector(h);plan=c.prepare(config(),collection_mode='DIAGNOSTIC_FIRST_CLIP')
        result=c.process(plan,reservation_persisted=True)
        self.assertEqual(result['status'],'READY');self.assertEqual(result['ledger']['processed_video_ids'],[VIDEO])


if __name__=='__main__':unittest.main()

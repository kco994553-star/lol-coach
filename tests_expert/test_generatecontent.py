"""Official generateContent mapping and literal503 retry fixtures; zero external calls."""
import copy
import json
import unittest
import urllib.parse

from coach_v1 import expert_collector as m
from tests_expert.test_collector import NOW,config,policy,claim


def answer(text='TEST_OK',finish='STOP'):
    return dict(candidates=[dict(finishReason=finish,content=dict(role='model',parts=[dict(text=text)]))])


class HTTP:
    def __init__(self,probe_statuses=(200,),video_status=200,response=None):
        self.calls=[];self.probe_statuses=list(probe_statuses);self.video_status=video_status;self.response=response
    def __call__(self,method,url,headers,body,timeout,max_bytes):
        self.calls.append(copy.deepcopy((method,url,headers,body,timeout)))
        if method=='POST':
            video=any('file_data' in part for part in body.get('contents',[{}])[0].get('parts',[]))
            status=self.video_status if video else self.probe_statuses.pop(0)
            if status!=200:return status,{},dict(error=dict(code=status,status='UNAVAILABLE',message='TEST TEST_GEMINI_KEY'))
            return 200,{},self.response or answer(json.dumps({'claims':[claim()]})) if video else answer()
        from tests_expert.test_collector import Transport
        return Transport()(method,url,headers,body,timeout,max_bytes)


def collector(http,sleeper=None,clock=None):
    return m.ExpertCollector(youtube_api_key='TEST_YOUTUBE_KEY',gemini_api_key='TEST_GEMINI_KEY',transport=http,
        clock=(lambda:NOW) if clock is None else clock,policy=policy(),sleeper=sleeper or (lambda _:None))


class GenerateContentTests(unittest.TestCase):
    def test_remaining_request_budget_covers_clips_before_any_new_quota_reservation(self):
        cfg=config();cfg['channels']=[]
        for i in range(15):
            channel=copy.deepcopy(config()['channels'][0])
            channel.update(channel_id='UC'+str(i).zfill(22),uploads_playlist_id=None)
            cfg['channels'].append(channel)
        class Tail(HTTP):
            def __init__(self):super().__init__([503,503,503,200])
            def __call__(self,method,url,headers,body,timeout,max_bytes):
                if method=='POST':return super().__call__(method,url,headers,body,timeout,max_bytes)
                self.calls.append(copy.deepcopy((method,url,headers,body,timeout)))
                query=urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
                if '/channels?' in url:
                    cid=query['id'][0]
                    return 200,{},dict(items=[dict(id=cid,contentDetails=dict(relatedPlaylists=dict(uploads='UU'+cid[2:])))])
                if '/playlistItems?' in url:
                    return 200,{},dict(items=[dict(contentDetails=dict(videoId=query['playlistId'][0][-11:]))])
                vid=query['id'][0];i=int(vid)
                return 200,{},dict(items=[dict(id=vid,snippet=dict(title='TEST wave' if i==14 else 'TEST unrelated',
                    channelId='UC'+str(i).zfill(22),channelTitle='TEST channel',publishedAt='2026-10-10T00:00:00Z',liveBroadcastContent='none'),
                    contentDetails=dict(duration='PT20M'),status=dict(privacyStatus='public',uploadStatus='processed'))])
        old=dict(schema_version='expert.quota-ledger.v1',initialized_at=NOW-20,
            reservations=[dict(video_id='zyxwvutsrqp',seconds=6644,reserved_at=NOW-10,reservation_id='0'*64)],processed_video_ids=[])
        h=Tail();c=collector(h);plan=c.prepare(cfg,old,ledger_history='FOUND')
        self.assertEqual(c.request_count,49)
        self.assertEqual(c.request_counts,dict(TEXT_PROBE=4,VIDEO_CLIP=0,METADATA=45))
        self.assertEqual(plan['status'],'BLOCKED_EXTERNAL');self.assertEqual(plan['reason'],'REQUEST_BUDGET_EXHAUSTED')
        self.assertEqual(plan['ledger'],old);self.assertIsNone(plan['reservation_id']);self.assertEqual(plan['videos'],[])
        result=collector(h).process(plan,reservation_persisted=True)
        self.assertEqual(result['ledger'],old);self.assertEqual(len(h.calls),49)
        # The same discovery fits exactly when only the authorized first clip is planned.
        h=Tail();c=collector(h);plan=c.prepare(cfg,old,ledger_history='FOUND',collection_mode='DIAGNOSTIC_FIRST_CLIP')
        self.assertEqual(plan['status'],'RESERVED');self.assertEqual(plan['ledger']['reservations'][:-1],old['reservations'])
        self.assertEqual(plan['ledger']['reservations'][-1]['seconds'],1200)
        result=collector(h).process(plan,reservation_persisted=True)
        self.assertEqual(len(h.calls),50);self.assertEqual(result['status'],'PARTIAL');self.assertEqual(result['ledger']['processed_video_ids'],[])

    def test_exact_official_video_body_and_new_route_bound_plan(self):
        h=HTTP();c=collector(h);plan=c.prepare(config(),collection_mode='DIAGNOSTIC_FIRST_CLIP')
        self.assertEqual(plan['schema_version'],'expert.reservation-plan.v4')
        self.assertEqual(plan['text_probe']['schema_version'],'expert.text-probe.v2')
        self.assertEqual(plan['text_probe']['api_route'],'GENERATE_CONTENT')
        result=c.process(plan,reservation_persisted=True)
        posts=[x for x in h.calls if x[0]=='POST']
        self.assertTrue(all(x[1]=='https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent' for x in posts))
        body=posts[-1][3];self.assertEqual(set(body),{'contents','generationConfig'})
        self.assertEqual(body['contents'][0]['role'],'user')
        first,second=body['contents'][0]['parts']
        self.assertEqual(first,dict(file_data=dict(file_uri='https://www.youtube.com/watch?v=abcdefghijk'),video_metadata=dict(start_offset='0s',end_offset='600s')))
        self.assertEqual(set(second),{'text'})
        self.assertEqual(body['generationConfig'],dict(candidateCount=1,responseMimeType='application/json',responseJsonSchema=m.RESPONSE_SCHEMA))
        self.assertEqual(result['status'],'READY');self.assertEqual(result['ledger']['processed_video_ids'],['abcdefghijk'])

    def test_only_text_literal503_retries_three_times_spaced15_seconds(self):
        for statuses,ready in [([503,200],True),([503]*4,False)]:
            clock=[NOW];waits=[]
            def sleep(seconds):waits.append(seconds);clock[0]+=seconds
            h=HTTP(statuses);c=collector(h,sleep,lambda:clock[0]);receipt=c.probe_text()
            self.assertEqual(receipt['attempt_count'],len(statuses));self.assertEqual(receipt['retry_count'],len(statuses)-1)
            self.assertEqual(waits,[15]*(len(statuses)-1));self.assertEqual(receipt['checked_at'],clock[0])
            self.assertEqual(receipt['status'],'READY' if ready else 'BLOCKED_EXTERNAL')
            self.assertEqual(c.request_counts,dict(TEXT_PROBE=len(statuses),VIDEO_CLIP=0,METADATA=0))
            self.assertEqual(len(c.diagnostics),len(statuses)-int(ready))
            self.assertNotIn('TEST_GEMINI_KEY',json.dumps(c.diagnostics))

    def test_non503_and_video503_never_retry_or_refund(self):
        for status in (400,401,403,429,500):
            waits=[];h=HTTP([status]);c=collector(h,waits.append);receipt=c.probe_text(structured=True)
            self.assertEqual(receipt['attempt_count'],1);self.assertEqual(waits,[])
        h=HTTP(video_status=503);waits=[];c=collector(h,waits.append);plan=c.prepare(config());result=c.process(plan,reservation_persisted=True)
        self.assertEqual(c.request_counts['VIDEO_CLIP'],1);self.assertEqual(waits,[])
        self.assertEqual(result['ledger']['reservations'],plan['ledger']['reservations']);self.assertEqual(result['ledger']['processed_video_ids'],[])

    def test_blocked_truncated_multicandidate_and_nontext_outputs_never_accepted(self):
        for response in (answer('TEST','MAX_TOKENS'),{'candidates':[]},dict(candidates=answer()['candidates']*2),
            dict(candidates=[dict(finishReason='STOP',content=dict(parts=[dict(functionCall={})]))]),
            dict(answer(),promptFeedback=dict(blockReason='SAFETY'))):
            h=HTTP(response=response);c=collector(h);plan=c.prepare(config());result=c.process(plan,reservation_persisted=True)
            self.assertEqual(result['artifacts'],[]);self.assertEqual(result['ledger']['processed_video_ids'],[])

    def test_probe_route_and_retry_counts_are_bound_and_old_plans_rejected(self):
        for mutate in (lambda p:p['text_probe'].update(api_route='INTERACTIONS'),lambda p:p['text_probe'].update(attempt_count=2,retry_count=1),
            lambda p:p.update(schema_version='expert.reservation-plan.v3')):
            h=HTTP();c=collector(h);plan=c.prepare(config());mutate(plan)
            with self.assertRaises(ValueError):c.process(plan,reservation_persisted=True)
            self.assertEqual(c.request_counts['VIDEO_CLIP'],0)

    def test_text_network_or_bad_200_output_never_retries_and_gate_has_zero_attempts(self):
        for response in (TimeoutError('PRIVATE_NETWORK'),dict(candidates=[]),answer('',finish='STOP')):
            class Broken(HTTP):
                def __call__(self,*args):
                    self.calls.append(copy.deepcopy(args[:5]))
                    if isinstance(response,Exception):raise response
                    return 200,{},response
            waits=[];h=Broken();c=collector(h,waits.append);receipt=c.probe_text()
            self.assertEqual(receipt['attempt_count'],1);self.assertEqual(receipt['retry_count'],0)
            self.assertEqual(waits,[]);self.assertEqual(receipt['status'],'BLOCKED_EXTERNAL')
        h=HTTP();c=collector(h);c.policy['free_tier_confirmed']=False;receipt=c.probe_text()
        self.assertEqual(receipt['attempt_count'],0);self.assertEqual(receipt['retry_count'],0);self.assertEqual(h.calls,[])

    def test_metadata503_never_retries_or_creates_video_charge(self):
        class MetadataFailure(HTTP):
            def __call__(self,*args):
                if args[0]=='GET':
                    self.calls.append(copy.deepcopy(args[:5]));return 503,{},dict(error=dict(code=503,message='TEST unavailable'))
                return super().__call__(*args)
        h=MetadataFailure();waits=[];c=collector(h,waits.append);plan=c.prepare(config())
        self.assertEqual(plan['status'],'BLOCKED_EXTERNAL');self.assertEqual(plan['ledger']['reservations'],[])
        self.assertEqual(c.request_counts,dict(TEXT_PROBE=1,VIDEO_CLIP=0,METADATA=1));self.assertEqual(waits,[])

    def test_documented_thought_metadata_is_skipped_and_signature_never_retained(self):
        response=answer()
        response['candidates'][0]['content']['parts']=[dict(text='PRIVATE_THOUGHT',thought=True,thoughtSignature='PRIVATE_SIGNATURE'),
            dict(text=json.dumps({'claims':[claim()]}),thought=False,thoughtSignature='PRIVATE_FINAL_SIGNATURE')]
        h=HTTP(response=response);c=collector(h);result=c.process(c.prepare(config()),reservation_persisted=True)
        self.assertEqual(result['status'],'READY');self.assertEqual(len(result['artifacts']),1)
        for private in ('PRIVATE_THOUGHT','PRIVATE_SIGNATURE','PRIVATE_FINAL_SIGNATURE','thoughtSignature'):
            self.assertNotIn(private,json.dumps(result))
        for parts in ([dict(text='TEST thought only',thought=True)],
            [dict(text='TEST',thought='true')],[dict(text='TEST',thoughtSignature=123)],
            [dict(text='TEST',unknown=True)],[dict(text='TEST',functionCall={})]):
            invalid=answer();invalid['candidates'][0]['content']['parts']=parts
            h=HTTP(response=invalid);c=collector(h);result=c.process(c.prepare(config()),reservation_persisted=True)
            self.assertEqual(result['artifacts'],[]);self.assertEqual(result['ledger']['processed_video_ids'],[])


if __name__=='__main__':unittest.main()

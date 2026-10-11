"""Static clips use fake HTTP only; timestamps always refer to the original video."""
import copy
import json
import unittest

from coach_v1 import expert_collector as m
from tests_expert.test_collector import Transport, VIDEO, NOW, claim, config, policy


class Clips(Transport):
    def __init__(self,duration=1200,outputs=None,clock=None):
        super().__init__();self.duration=duration;self.outputs=outputs;self.clock=clock;self.timeouts=[];self.model_calls=0

    def __call__(self,method,url,headers,body,timeout,max_bytes):
        self.timeouts.append((method,timeout))
        if '/interactions' not in url:
            code,h,data=super().__call__(method,url,headers,body,timeout,max_bytes)
            if '/videos?' in url:data['items'][0]['contentDetails']['duration']='PT'+str(self.duration)+'S'
            return code,h,data
        self.calls.append((method,url,copy.deepcopy(headers),copy.deepcopy(body)))
        index=self.model_calls;self.model_calls+=1
        output=self.outputs[index] if self.outputs is not None else {'claims':[claim('01:00' if index==0 else '10:00')]}
        if self.clock is not None:self.clock[0]+=600
        if isinstance(output,Exception):raise output
        text=json.dumps(output)
        return 200,{},dict(status='completed',steps=[dict(type='model_output',content=[dict(type='text',text=text)])])


def collector(http,clock=None,**kwargs):
    return m.ExpertCollector(youtube_api_key='TEST_YOUTUBE_KEY',gemini_api_key='TEST_GEMINI_KEY',
        transport=http,clock=(lambda:clock[0]) if clock is not None else lambda:NOW,policy=policy(),**kwargs)


class SegmentTests(unittest.TestCase):
    def test_static_intervals_and_full_original_charge_boundaries(self):
        for duration,ends,charge in [(600,[600],600),(601,[600,601],1202),(1200,[600,1200],2400)]:
            with self.subTest(duration=duration):
                h=Clips(duration);c=collector(h);plan=c.prepare(config())
                self.assertEqual(plan['schema_version'],'expert.reservation-plan.v2')
                self.assertEqual(plan['ledger']['reservations'][0]['seconds'],charge)
                result=c.process(plan,reservation_persisted=True)
                self.assertEqual(result['status'],'READY')
                requests=[x[3] for x in h.calls if x[0]=='POST']
                self.assertTrue(all(body['input'][0]['type']=='video' and body['input'][1]['type']=='text' for body in requests))
                self.assertEqual([body['input'][0]['processing'] for body in requests],[dict(type='static',start_offset=str(start)+'s',end_offset=str(end)+'s') for start,end in zip([0,600],ends)])
                self.assertEqual(result['artifacts'][0]['processing']['input_sha256'],m._digest(requests))
                self.assertTrue(all('absolute' in body['input'][1]['text'].lower() for body in requests))
                self.assertEqual(result['ledger']['processed_video_ids'],[VIDEO])

    def test_legacy_config_cannot_select_1210_second_video(self):
        h=Clips(1210);plan=collector(h).prepare(config())
        self.assertEqual(plan['status'],'NO_ELIGIBLE_VIDEOS');self.assertEqual(plan['videos'],[])

    def test_partial_timeout_keeps_first_absolute_claim_and_full_charge(self):
        h=Clips(outputs=[{'claims':[claim()]},TimeoutError('PRIVATE_PROVIDER_RESPONSE')]);c=collector(h)
        plan=c.prepare(config());result=c.process(plan,reservation_persisted=True)
        self.assertEqual(result['status'],'PARTIAL');self.assertEqual(result['reason'],'NETWORK_TIMEOUT')
        self.assertEqual(result['ledger']['reservations'],plan['ledger']['reservations'])
        self.assertEqual(result['ledger']['reservations'][0]['seconds'],2400)
        self.assertEqual(result['ledger']['processed_video_ids'],[])
        self.assertIn('SEGMENTED_EXTRACTION_INCOMPLETE',result['artifacts'][0]['claims'][0]['limitations'])
        self.assertNotIn('PRIVATE_PROVIDER_RESPONSE',json.dumps(result))

    def test_second_clip_local_timestamp_rejected_without_offset_guess(self):
        h=Clips(outputs=[{'claims':[claim()]},{'claims':[claim('01:30')]}]);c=collector(h)
        result=c.process(c.prepare(config()),reservation_persisted=True)
        self.assertEqual(result['status'],'PARTIAL');self.assertEqual(result['ledger']['processed_video_ids'],[])
        artifact=result['artifacts'][0]
        self.assertEqual([x['timestamp_seconds'] for x in artifact['claims']],[60])
        self.assertIn('OUT_OF_RANGE_TIMESTAMP',[x['reason'] for x in artifact['rejections']])

    def test_empty_valid_second_clip_is_distinct_from_bad_format(self):
        for output,status in [({'claims':[]},'READY'),({'claims':'wrong'},'PARTIAL')]:
            h=Clips(outputs=[{'claims':[claim()]},output]);c=collector(h)
            result=c.process(c.prepare(config()),reservation_persisted=True)
            self.assertEqual(result['status'],status)
            self.assertEqual(result['ledger']['processed_video_ids'],[VIDEO] if status=='READY' else [])

    def test_default_model_timeout_600_and_metadata_timeout_20(self):
        h=Clips(600);c=collector(h,timeout=600);c.process(c.prepare(config()),reservation_persisted=True)
        self.assertEqual([timeout for method,timeout in h.timeouts if method=='POST'],[600])
        self.assertTrue(all(timeout<=20 for method,timeout in h.timeouts if method=='GET'))
        with self.assertRaises(ValueError):collector(h,timeout=601)

    def test_late_second_dispatch_stops_without_another_request(self):
        clock=[NOW];h=Clips(clock=clock);c=collector(h,clock);plan=c.prepare(config());clock[0]=NOW+600
        result=c.process(plan,reservation_persisted=True)
        self.assertEqual(h.model_calls,1);self.assertEqual(result['status'],'PARTIAL')
        self.assertEqual(result['reason'],'RESERVATION_DISPATCH_DEADLINE_EXPIRED')
        self.assertEqual(result['ledger']['reservations'],plan['ledger']['reservations'])
        self.assertEqual(result['ledger']['processed_video_ids'],[])

    def test_four_historical_failed_charges_remain_byte_equivalent(self):
        rows=[dict(video_id=str(i).zfill(11),seconds=seconds,reserved_at=NOW-10,reservation_id=str(i)*64) for i,seconds in enumerate([1000,1000,1000,1298],1)]
        ledger=dict(schema_version='expert.quota-ledger.v1',initialized_at=NOW-20,reservations=rows,processed_video_ids=[])
        before=m._canonical(ledger);h=Clips();c=collector(h);plan=c.prepare(config(),ledger)
        self.assertEqual(m._canonical(ledger),before)
        result=c.process(plan,reservation_persisted=True)
        self.assertEqual(result['ledger']['reservations'][:4],rows)
        self.assertEqual(sum(x['seconds'] for x in result['ledger']['reservations']),4298+2400)

    def test_combined_claim_cap_retains_bounded_partial_source(self):
        first=[dict(claim('01:00'),paraphrase='FIRST '+str(i)) for i in range(100)]
        second=[dict(claim('10:00'),paraphrase='SECOND '+str(i)) for i in range(100)]
        h=Clips(outputs=[{'claims':first},{'claims':second}]);c=collector(h)
        result=c.process(c.prepare(config()),reservation_persisted=True)
        self.assertEqual(result['status'],'PARTIAL');self.assertEqual(result['ledger']['processed_video_ids'],[])
        self.assertLessEqual(len(result['artifacts'][0]['claims']),100)
        self.assertLessEqual(len(m._canonical(result['artifacts'][0]).encode()),200000)

    def test_combined_bytes_cap_marks_partial_and_never_processes_video(self):
        first=[dict(claim('01:00'),paraphrase='FIRST'+str(i),conditions=['a'*200]*9) for i in range(50)]
        second=[dict(claim('10:00'),paraphrase='SECOND'+str(i),conditions=['b'*200]*9) for i in range(50)]
        h=Clips(outputs=[{'claims':first},{'claims':second}]);c=collector(h)
        result=c.process(c.prepare(config()),reservation_persisted=True)
        self.assertEqual(result['status'],'PARTIAL');self.assertEqual(result['ledger']['processed_video_ids'],[])
        artifact=result['artifacts'][0]
        self.assertLessEqual(len(m._canonical(artifact).encode()),200000)
        self.assertTrue(all('SEGMENTED_EXTRACTION_INCOMPLETE' in x['limitations'] for x in artifact['claims']))
        self.assertIn('FAILED_FORMAT',[x['reason'] for x in artifact['rejections']])

    def test_duplicate_claims_deduplicate_and_clip_end_is_exclusive(self):
        h=Clips(outputs=[{'claims':[claim(),claim(),claim('10:00')]},{'claims':[claim('10:00')]}]);c=collector(h)
        result=c.process(c.prepare(config()),reservation_persisted=True)
        self.assertEqual(result['status'],'PARTIAL')
        artifact=result['artifacts'][0]
        self.assertEqual([x['timestamp_seconds'] for x in artifact['claims']],[60,600])
        self.assertIn('DUPLICATE_CLAIM',[x['reason'] for x in artifact['rejections']])
        self.assertIn('OUT_OF_RANGE_TIMESTAMP',[x['reason'] for x in artifact['rejections']])

    def test_archived_v1_plan_is_not_reinterpreted_or_dispatched(self):
        h=Clips();c=collector(h);plan=c.prepare(config());plan['schema_version']='expert.reservation-plan.v1'
        with self.assertRaises(ValueError):c.process(plan,reservation_persisted=True)
        self.assertEqual(h.model_calls,0)


if __name__=='__main__':unittest.main()

"""Fake HTTP responses verify collection behavior without Riot credentials."""
import copy
import importlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch
from pathlib import Path

from tests_pregame.test_power_stats import pair
TEST_KEY='RGAPI-00000000-0000-4000-8000-000000000000'


class Clock:
    def __init__(self):self.time=0;self.waits=[]
    def now(self):return self.time
    def sleep(self,seconds):self.waits.append(seconds);self.time+=seconds


class Responses:
    def __init__(self,responses):self.responses=list(responses);self.urls=[];self.headers=[]
    def __call__(self,url,headers,timeout):
        self.urls.append(url);self.headers.append(headers)
        response=self.responses.pop(0)
        if isinstance(response,Exception):raise response
        status,h,body=response
        return status,h,json.dumps(body).encode() if not isinstance(body,bytes) else body


def okay(body,headers=None):return (200,headers or {},body)


class RiotCollectorTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('coach_v1.riot_collector'),'Q15 collector missing')
        self.module=importlib.import_module('coach_v1.riot_collector')

    def collector(self,responses,**limits):
        self.clock=Clock();self.transport=Responses(responses)
        return self.module.RiotCollector(TEST_KEY,transport=self.transport,
            clock=self.clock.now,sleeper=self.clock.sleep,**limits)

    def collect(self,collector,**kwargs):
        return collector.collect(tier='GOLD',division='I',patch='16.19',start_time=1,end_time=2000000000,**kwargs)

    def test_401_403_blocked_no_raw_errors_or_retry(self):
        for status in (401,403):
            c=self.collector([(status,{},b'PRIVATE_PUUID PRIVATE_TEST_KEY')])
            result=self.collect(c)
            self.assertEqual(result['status'],'BLOCKED_EXTERNAL')
            self.assertEqual(result['source']['collection']['status_code'],status)
            self.assertEqual(result['source']['collection']['key_kind'],'UNKNOWN')
            self.assertEqual(result['source']['collection']['request_count'],1)
            self.assertNotIn('PRIVATE',json.dumps(result))

    def test_explicit_user_agent_all_api_and_data_dragon_requests(self):
        c=self.collector([okay([]),okay(['16.19.1'])])
        self.collect(c)
        c._get('https://ddragon.leagueoflegends.com/api/versions.json','DD_VERSIONS',api=False)
        self.assertTrue(all(h['User-Agent']=='lol-coach/1.0 (+https://github.com/kco994553-star/lol-coach)' for h in self.transport.headers))
        self.assertEqual(self.transport.headers[0]['X-Riot-Token'],TEST_KEY)
        self.assertNotIn('X-Riot-Token',self.transport.headers[1])

    def test_later_403_front_observation_sanitized_and_reset(self):
        observed=[];c=self.collector([okay([{'puuid':'PRIVATE_PLAYER'}]),
            (403,{'CF-Ray':'PRIVATE_MARKER'},{'status':{'message':'Forbidden puuid=PRIVATE_PLAYER '+TEST_KEY}}),okay([])],
            on_front_error=observed.append)
        result=self.collect(c)
        self.assertEqual(c.first_http_status,200);self.assertEqual(result['status'],'BLOCKED_EXTERNAL')
        self.assertEqual(c.requests,2);self.assertEqual(c.retries,0)
        self.assertEqual(observed,c.front_errors);self.assertTrue(c.front_errors[0]['markers']['cf-ray'])
        self.assertEqual(c.front_errors[0]['http_status'],403)
        for forbidden in ('PRIVATE_PLAYER','PRIVATE_MARKER',TEST_KEY):
            self.assertNotIn(forbidden,json.dumps(c.front_errors)+json.dumps(c.http_errors))
        self.collect(c);self.assertEqual(c.front_errors,[])

    def test_first_http_status_is_first_response_not_later_failure_or_retry(self):
        for responses,expected,last in [([okay([{'puuid':'private'}]),(403,{},b'PRIVATE_BODY')],200,403),
                                       ([(503,{},b'PRIVATE_BODY'),okay([])],503,None)]:
            observed=[];c=self.collector(responses,on_first_http_response=observed.append)
            result=self.collect(c)
            self.assertEqual(c.first_http_status,expected);self.assertEqual(observed,[expected])
            self.assertEqual(result['source']['collection']['status_code'],last)
            self.assertNotIn('PRIVATE',json.dumps(observed))

    def test_first_http_status_missing_network_and_per_collect_reset(self):
        c=self.collector([OSError('PRIVATE_NETWORK')],max_retries=0)
        self.collect(c);self.assertIsNone(c.first_http_status)
        self.assertEqual(c.requests,1)
        c=self.collector([okay([]),(403,{},b'PRIVATE_BODY')])
        self.collect(c);self.assertEqual(c.first_http_status,200)
        self.collect(c);self.assertEqual(c.first_http_status,403)
        c.api_key=None;self.collect(c);self.assertIsNone(c.first_http_status)
        self.assertEqual(c.requests,0)

    def test_oversized_first_http_response_preserves_safe_200_receipt(self):
        output=StringIO();observed=[]
        def receipt(status_code):
            observed.append(status_code)
            print('RIOT_FIRST_HTTP_RECEIPT_JSON='+json.dumps({'status_code':status_code}))
        clock=Clock()
        c=self.module.RiotCollector(TEST_KEY,clock=clock.now,sleeper=clock.sleep,
            on_first_http_response=receipt)
        with patch.object(self.module,'build_opener') as opener,redirect_stdout(output):
            response=opener.return_value.open.return_value.__enter__.return_value
            response.status=200;response.headers={};response.read.return_value=b'x'*(16*1024*1024+1)
            result=self.collect(c)
        self.assertEqual(c.first_http_status,200);self.assertEqual(observed,[200])
        self.assertEqual(output.getvalue().strip(),'RIOT_FIRST_HTTP_RECEIPT_JSON={"status_code": 200}')
        self.assertEqual(result['status'],'BLOCKED_EXTERNAL')
        self.assertEqual(result['source']['collection']['reason'],'MALFORMED_RESPONSE')
        self.assertEqual(result['source']['collection']['status_code'],200)
        self.assertEqual(c.requests,1);self.assertEqual(c.retries,0)
        self.assertNotIn('PRIVATE',output.getvalue()+json.dumps(result))

    def test_retry_after_and_application_method_limits_wait(self):
        c=self.collector([(429,{'Retry-After':'3'},b'private'),okay([{'puuid':'private-puuid'}]),
            okay(['KR_100'],{'X-App-Rate-Limit':'1:5','X-App-Rate-Limit-Count':'1:5'}),
            (404,{},b'private')])
        result=self.collect(c)
        self.assertEqual(self.clock.waits,[3,5])
        self.assertEqual(result['source']['collection']['retry_count'],1)
        self.assertEqual(result['status'],'INSUFFICIENT_DATA')
        self.assertTrue(all('api_key' not in url and TEST_KEY not in url and 'PRIVATE_TEST_KEY' not in url for url in self.transport.urls))
        c=self.collector([(429,{'Retry-After':'300'},b'private')],deadline_seconds=10)
        result=self.collect(c);self.assertEqual(result['status'],'BLOCKED_EXTERNAL')
        self.assertEqual(self.clock.waits,[])

    def test_bounded_retries_budget_and_network_failure(self):
        c=self.collector([(429,{'Retry-After':'1'},b'')]*3,max_retries=1)
        self.assertEqual(self.collect(c)['source']['collection']['reason'],'RATE_LIMIT_EXHAUSTED')
        self.assertEqual(len(self.transport.urls),2)
        c=self.collector([okay([{'puuid':'private'}])],max_requests=1)
        self.assertEqual(self.collect(c)['source']['collection']['reason'],'REQUEST_BUDGET_EXHAUSTED')
        c=self.collector([OSError('PRIVATE_TEST_KEY')]*2,max_retries=1)
        result=self.collect(c)
        self.assertEqual(result['source']['collection']['reason'],'NETWORK_FAILURE')
        self.assertNotIn('PRIVATE',json.dumps(result))

    def test_real_route_chain_hash_dedup_and_no_identity_export(self):
        pairs=[pair(0),pair(1)]
        for number,p in enumerate(pairs,100):
            p['match']['metadata']['matchId']='KR_'+str(number)
            p['timeline']['metadata']['matchId']='KR_'+str(number)
        responses=[okay([{'puuid':'PRIVATE_PUUID'},{'puuid':'PRIVATE_PUUID'}]),okay(['KR_100','KR_100','KR_101'])]
        for p in pairs:responses.extend([okay(p['match']),okay(p['timeline'])])
        c=self.collector(responses,max_matches=2)
        result=self.collect(c,collect_items=False)
        self.assertEqual(result['status'],'READY');self.assertEqual(result['samples']['real_matches'],2)
        self.assertEqual(result['samples']['synthetic_matches'],0)
        self.assertIn('kr.api.riotgames.com/lol/league/v4/entries/RANKED_SOLO_5x5/GOLD/I',self.transport.urls[0])
        self.assertIn('asia.api.riotgames.com/lol/match/v5/matches/by-puuid/',self.transport.urls[1])
        self.assertNotIn('PRIVATE',json.dumps(result));self.assertNotIn('KR_100',json.dumps(result))

    def test_no_puuid_refuses_scraping_or_identity_guess(self):
        c=self.collector([okay([{'summonerId':'PRIVATE_ID','summonerName':'PRIVATE_NAME'}])])
        result=self.collect(c)
        self.assertEqual(result['status'],'BLOCKED_EXTERNAL')
        self.assertEqual(result['source']['collection']['reason'],'UNSUPPORTED_LEAGUE_IDENTITY')
        self.assertEqual(len(self.transport.urls),1)

    def test_method_limit_wait_and_malformed_match_is_safe_block(self):
        c=self.collector([okay([{'puuid':'private'}],{'X-Method-Rate-Limit':'1:4','X-Method-Rate-Limit-Count':'1:4'}),
            okay([]),okay([])],max_pages=2,max_players=2)
        self.collect(c)
        self.assertEqual(self.clock.waits,[4])
        c=self.collector([okay([{'puuid':'private'}]),okay(['KR_100']),okay({'info':[]})])
        self.assertEqual(self.collect(c)['source']['collection']['reason'],'MALFORMED_RESPONSE')

    def test_catalog_terminal_nonconsumable_no_cost_guess(self):
        catalog={'data':{'3001':dict(gold={'purchasable':True,'total':1},maps={'11':True},
            tags=['Damage'],**{'from':['1001']}),
            '1001':dict(gold={'purchasable':True,'total':9999},maps={'11':True},tags=['Damage'],into=['3001']),
            '4000':dict(gold={'purchasable':True},maps={'11':True},tags=['Consumable'],**{'from':['1001']}),
            '4001':dict(gold={'purchasable':True},maps={'11':True},tags=['Trinket'],**{'from':['1001']})}}
        self.assertEqual(self.module.complete_item_ids(catalog),[3001])

    def test_complete_boots_and_support_gold_items_excluded_from_core_candidates(self):
        catalog={'data':{str(item):dict(gold={'purchasable':True},maps={'11':True},
            tags=[tag],**{'from':['1001']}) for item,tag in [(3006,'Boots'),(4000,'GoldPer'),(3001,'Damage')]}}
        self.assertEqual(self.module.complete_item_ids(catalog),[3001])

    def test_transport_never_forwards_key_through_redirect(self):
        from http.server import BaseHTTPRequestHandler,HTTPServer
        import threading
        arrived=[]
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                arrived.append(self.path)
                if self.path=='/redirect':
                    self.send_response(302);self.send_header('Location','/recipient');self.end_headers()
                else:self.send_response(200);self.end_headers();self.wfile.write(b'{}')
            def log_message(self,*args):pass
        server=HTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            status,headers,body=self.module._transport('http://127.0.0.1:'+str(server.server_port)+'/redirect',
                {'X-Riot-Token':'PRIVATE_TEST_KEY'},2)
            self.assertEqual(status,302);self.assertEqual(arrived,['/redirect'])
        finally:server.shutdown();server.server_close();thread.join()

    def test_missing_env_key_script_writes_safe_block_receipt(self):
        import os
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'safe.json';diagnostics=Path(tmp)/'diagnostics.json';env=dict(os.environ);env.pop('RIOT_API_KEY',None)
            output.write_text('stale previous aggregate')
            r=subprocess.run([sys.executable,'scripts/collect_power_stats.py','--output',str(output),'--tier','MASTER',
                '--diagnostics-output',str(diagnostics)],
                env=env,capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertFalse(output.exists())
            result=json.loads(diagnostics.read_text());self.assertEqual(result['collection_status'],'BLOCKED_EXTERNAL')
            self.assertEqual(result['request_count'],0)
            self.assertEqual(result['collection_reason'],'MISSING_API_KEY')
            self.assertFalse(result['key_shape']['valid_shape'])
            self.assertNotIn('Traceback',r.stderr)
            lines=[line for line in r.stdout.splitlines() if line.startswith('RIOT_FIRST_HTTP_RECEIPT_JSON=')]
            self.assertEqual(len(lines),1)
            self.assertEqual(json.loads(lines[0].split('=',1)[1]),{'status_code':None})

    def test_movement_companion_unavailable_on_auth_failure_and_no_raw_return(self):
        c=self.collector([(403,{},b'PRIVATE_PUUID')])
        result=self.collect(c,collect_movement=True)
        self.assertEqual(result['status'],'BLOCKED_EXTERNAL')
        self.assertIsNone(c.movement_data)
        self.assertEqual(c.movement_status,'BLOCKED_EXTERNAL')
        self.assertNotIn('pairs',c.__dict__)

    def test_movement_companion_uses_actual_coordinates_and_script_safe_output(self):
        p=pair(0);p['match']['metadata']['matchId']='KR_100';p['timeline']['metadata']['matchId']='KR_100'
        for frame in p['timeline']['info']['frames']:
            for pid,pf in frame['participantFrames'].items():pf['position']={'x':100*int(pid),'y':50*int(pid)}
        c=self.collector([okay([{'puuid':'private'}]),okay(['KR_100']),okay(p['match']),okay(p['timeline'])])
        self.collect(c,collect_items=False,collect_movement=True)
        self.assertEqual(c.movement_data['samples']['real_matches'],1)
        self.assertTrue(c.movement_data['cohorts'])
        self.assertNotIn('PRIVATE',json.dumps(c.movement_data))
        self.assertNotIn('participantFrames',json.dumps(c.movement_data))
        import os
        with tempfile.TemporaryDirectory() as tmp:
            power=Path(tmp)/'power.json';movement=Path(tmp)/'movement.json';env=dict(os.environ);env.pop('RIOT_API_KEY',None)
            movement.write_text('stale prior aggregate')
            result=subprocess.run([sys.executable,'scripts/collect_power_stats.py','--output',str(power),
                '--movement-output',str(movement),'--tier','MASTER'],env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertFalse(movement.exists())
            self.assertEqual(json.loads(result.stdout.splitlines()[-1])['movement_status'],'BLOCKED_EXTERNAL')


if __name__=='__main__':unittest.main()

"""Fake HTTP responses verify collection behavior without Riot credentials."""
import copy
import importlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests_pregame.test_power_stats import pair


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
        return self.module.RiotCollector('PRIVATE_TEST_KEY',transport=self.transport,
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

    def test_retry_after_and_application_method_limits_wait(self):
        c=self.collector([(429,{'Retry-After':'3'},b'private'),okay([{'puuid':'private-puuid'}]),
            okay(['KR_100'],{'X-App-Rate-Limit':'1:5','X-App-Rate-Limit-Count':'1:5'}),
            (404,{},b'private')])
        result=self.collect(c)
        self.assertEqual(self.clock.waits,[3,5])
        self.assertEqual(result['source']['collection']['retry_count'],1)
        self.assertEqual(result['status'],'INSUFFICIENT_DATA')
        self.assertTrue(all('api_key' not in url and 'PRIVATE_TEST_KEY' not in url for url in self.transport.urls))
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
            output=Path(tmp)/'safe.json';env=dict(os.environ);env.pop('RIOT_API_KEY',None)
            r=subprocess.run([sys.executable,'scripts/collect_power_stats.py','--output',str(output),'--tier','GOLD'],
                env=env,capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            result=json.loads(output.read_text());self.assertEqual(result['status'],'BLOCKED_EXTERNAL')
            self.assertEqual(result['samples']['real_matches'],0)
            self.assertIn('MISSING_API_KEY',result['source']['limitations'])
            self.assertNotIn('Traceback',r.stderr)


if __name__=='__main__':unittest.main()

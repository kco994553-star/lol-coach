import http.client
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest

from coach_v1.server import Limits
from tests_pregame.test_contract import golden,rule


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('coach_v1.pregame_server'),'pregame HTTP integration missing')
        from coach_v1.pregame_server import PregameWorkbench
        self.tmp=tempfile.TemporaryDirectory();self.token='test-token-not-a-real-credential-'*2
        self.server=PregameWorkbench(Path(self.tmp.name)/'work.sqlite',self.token,Limits(1_000_000,100,100,100,100,10))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.cleanup)

    def cleanup(self):
        self.server.shutdown();self.thread.join();self.server.server_close();self.tmp.cleanup()

    def call(self,path,method='GET',body=None,key=None,auth=True):
        con=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=10)
        headers={'Authorization':'Bearer '+self.token} if auth else {}
        if body is not None:headers['Content-Type']='application/json'
        if key:headers['Idempotency-Key']=key
        con.request(method,path,json.dumps(body) if body is not None else None,headers)
        r=con.getresponse();raw=r.read();con.close()
        return r.status,json.loads(raw) if 'application/json' in r.getheader('Content-Type','') else raw.decode()

    def test_auth_inherited_routes_and_static_page(self):
        self.assertEqual(self.call('/dev/v1/pregame/status',auth=False)[0],401)
        self.assertEqual(self.call('/dev/v1/status')[0],200)
        self.assertEqual(self.call('/dev/v1/pregame/status')[1]['current_patch'],None)
        self.assertEqual(self.call('/')[0],200)

    def test_input_http_cas_retry_and_original_import(self):
        path='/dev/v1/pregame/inputs'
        first=self.call(path,'POST',dict(input=golden()),'new')[1]
        self.assertEqual(self.call(path,'POST',dict(input=golden()),'new')[1],first)
        self.assertEqual(self.call(path+'/'+first['session_id'],'PUT',dict(input=golden('TOP'),expected_revision=1),'edit')[0],200)
        self.assertEqual(self.call(path+'/'+first['session_id'],'PUT',dict(input=golden('MID'),expected_revision=1),'stale')[0],409)
        cap=dict(title='original',phase=None,patch=None,observed_at=None,visible_picks=[],visible_bans=[],role_assignments=[],source=dict(author='manual',perspective='UNKNOWN',description='visible'))
        raw=self.call('/dev/v1/draft-captures','POST',dict(capture=cap),'old-capture')[1]
        imported=self.call('/dev/v1/pregame/import-draft/'+raw['session_id'])[1]
        self.assertEqual(imported['original_capture'],raw);self.assertEqual(imported['phase'],'UNKNOWN')
        self.assertEqual(self.call(path,'POST',dict(input=imported),'from-old')[0],201)
        imported['original_capture']['capture']['title']='spoofed'
        self.assertEqual(self.call(path,'POST',dict(input=imported),'spoof')[0],409)

    def test_import_is_proposal_only_and_unbound_prose_stays_unbound(self):
        status,created=self.call('/dev/v1/pregame/candidates','POST',dict(spec=rule()))
        self.assertEqual(status,201);self.assertEqual(created['proposal']['review_state'],'EXPLORATORY')
        rows=self.call('/dev/v1/pregame/knowledge')[1]
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['spec'],rule())
        self.assertEqual(rows[0]['proposal']['source_refs'],created['proposal']['source_refs'])
        body=dict(selected_version=created['proposal']['version'],expected_version=created['proposal']['version'],decision='REVIEWED',patch_range='SYNTHETIC-1',applicability=created['proposal']['applicability'])
        self.assertEqual(self.call('/dev/v1/knowledge/proposals/'+created['proposal']['rule_id']+'/decisions','POST',body)[0],403)

    def test_no_automatic_verified_provenance_without_adapter(self):
        d=golden();d['slots'][0]['champion_source'].update(kind='AUTOMATIC',verification='SOURCE_VERIFIED')
        status,result=self.call('/dev/v1/pregame/inputs','POST',dict(input=d),'forged-auto')
        self.assertEqual(status,422);self.assertEqual(result['error_code'],'AUTOMATIC_ADAPTER_UNAVAILABLE')


if __name__=='__main__':unittest.main()

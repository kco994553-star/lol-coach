import copy
import http.client
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest

from coach_v1.server import Workbench,Limits
from tests_r3.helpers import fixture


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.db=Path(self.temp.name)/'db.sqlite'
        self.server=Workbench(self.db,'t'*40,Limits(1_000_000,100,10,10,100,10))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.temp.cleanup()

    def call(self,path,method='GET',body=None,extra=None,auth=True):
        conn=http.client.HTTPConnection('127.0.0.1',self.server.server_port)
        headers={'Authorization':'Bearer '+'t'*40} if auth else {}
        if body is not None:headers['Content-Type']='application/json';body=json.dumps(body)
        if extra:headers.update(extra)
        conn.request(method,path,body,headers);r=conn.getresponse();data=r.read();headers=dict(r.getheaders());status=r.status;conn.close()
        return status,json.loads(data) if 'application/json' in headers.get('Content-Type','') else data,headers

    def session_case(self):
        status,s,_=self.call('/dev/v1/sessions','POST',{'title':'sample','patch':'SYNTHETIC-1'})
        self.assertEqual(status,201)
        p=fixture();p['snapshot_request']['session_id']=s['id']
        for o in p['observations']:o['session_id']=s['id']
        status,c,_=self.call('/dev/v1/sessions/'+s['id']+'/case','PUT',{'case':p,'expected_revision':0},{'Idempotency-Key':'put-1'})
        self.assertEqual(status,200);return s,c,p

    def test_auth_host_and_origin(self):
        self.assertEqual(self.call('/dev/v1/status',auth=False)[0],401)
        self.assertEqual(self.call('/dev/v1/status',extra={'Origin':'https://evil.test'})[0],403)
        self.assertEqual(self.call('/dev/v1/status',extra={'Host':'evil.test'})[0],403)
        self.assertEqual(self.call('/dev/v1/status',extra={'Authorization':'Bearer wrong'})[0],401)
        self.assertEqual(self.call('/dev/v1/status')[0],200)

    def test_static_security_and_no_path_traversal(self):
        status,html,headers=self.call('/',auth=False);self.assertEqual(status,200)
        self.assertIn(b'LoL Coach',html);self.assertIn("frame-ancestors 'none'",headers['Content-Security-Policy'])
        self.assertEqual(headers['Cache-Control'],'no-store')
        self.assertEqual(self.call('/../CURRENT_HANDOFF.md')[0],404)
        self.assertEqual(self.call('/dev/v1/status?token=secret')[0],400)

    def test_end_to_end_persist_review_and_delete(self):
        s,c,p=self.session_case();sid=s['id']
        status,job,_=self.call('/dev/v1/sessions/'+sid+'/reviews','POST',{'expected_revision':1},{'Idempotency-Key':'review-1'})
        self.assertEqual(status,202)
        deadline=time.monotonic()+3
        while time.monotonic()<deadline:
            _,job,_=self.call('/dev/v1/jobs/'+job['id'])
            if job['status']=='COMPLETED':break
            time.sleep(.01)
        self.assertEqual(job['status'],'COMPLETED')
        status,result,_=self.call('/dev/v1/reviews/'+job['result_ref']);self.assertEqual(status,200)
        self.assertEqual(self.call('/dev/v1/sessions/'+sid+'/reviews')[1][0]['id'],job['id'])
        self.assertFalse(result['stale']);self.assertEqual(result['result']['evidence_kind'],'SYNTHETIC')
        self.assertEqual(self.call('/dev/v1/sessions/'+sid,'DELETE')[0],200)
        self.assertEqual(self.call('/dev/v1/jobs/'+job['id'])[0],404)
        self.assertEqual(self.call('/dev/v1/reviews/'+job['result_ref'])[0],404)

    def test_put_idempotency_and_stale_revision(self):
        s,c,p=self.session_case();path='/dev/v1/sessions/'+s['id']+'/case';b={'case':p,'expected_revision':0}
        self.assertEqual(self.call(path,'PUT',b,{'Idempotency-Key':'put-1'})[1]['revision'],1)
        self.assertEqual(self.call(path,'PUT',b,{'Idempotency-Key':'put-2'})[0],409)
        self.assertEqual(self.call(path,'PUT',b)[0],422)

    def test_limits_and_real_mode_rejected(self):
        self.assertEqual(self.call('/dev/v1/sessions','POST',{'title':'x','patch':'x','mode':'POST_GAME'})[0],422)
        # Server rejects by Content-Length without consuming an oversized body.
        conn=http.client.HTTPConnection('127.0.0.1',self.server.server_port)
        conn.request('POST','/dev/v1/sessions',headers={'Authorization':'Bearer '+'t'*40,'Content-Type':'application/json','Content-Length':'1000001'})
        response=conn.getresponse();self.assertEqual(response.status,413);response.read();conn.close()
        s,c,p=self.session_case();p['actions']*=11
        self.assertEqual(self.call('/dev/v1/sessions/'+s['id']+'/case','PUT',{'case':p,'expected_revision':1},{'Idempotency-Key':'large'})[0],413)

    def test_duplicate_keys_and_nonfinite_json_rejected(self):
        for raw in ('{"title":"one","title":"two","patch":"x"}','{"title":"x","patch":NaN}'):
            conn=http.client.HTTPConnection('127.0.0.1',self.server.server_port)
            conn.request('POST','/dev/v1/sessions',raw,{'Authorization':'Bearer '+'t'*40,'Content-Type':'application/json'})
            response=conn.getresponse();self.assertEqual(response.status,422);response.read();conn.close()

    def test_second_server_cannot_recover_active_database(self):
        with self.assertRaises(ValueError):Workbench(self.db,'t'*40,self.server.limits)

    def test_queue_recovery_exceeding_worker_capacity(self):
        # Pre-existing queued work is drained after a restart without startup failure.
        s,c,p=self.session_case()
        jobs=[self.server.store.submit_review(s['id'],1,'queued-'+str(i)) for i in range(3)]
        self.server.shutdown();self.server.server_close();self.thread.join()
        self.server=Workbench(self.db,'t'*40,Limits(1_000_000,100,10,10,100,1))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        deadline=time.monotonic()+3
        while time.monotonic()<deadline:
            if all(self.server.store.get_job(j['id'])['status']=='COMPLETED' for j in jobs):break
            time.sleep(.01)
        self.assertTrue(all(self.server.store.get_job(j['id'])['status']=='COMPLETED' for j in jobs))

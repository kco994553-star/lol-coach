"""Real authenticated HTTP/SQLite proposal lifecycle without engine promotion."""
import copy
import json
import unittest

from coach_v1.server import Limits
from tests_r4 import test_http as helpers


class KnowledgeHTTPTests(unittest.TestCase):
    setUp = helpers.HTTPTests.setUp
    tearDown = helpers.HTTPTests.tearDown
    call = helpers.HTTPTests.call
    base = '/dev/v1/knowledge/proposals'

    def source(self):
        status, r, _ = self.call('/dev/v1/research', 'POST',
                                {'source_type':'official_sample', 'title':'local research'})
        self.assertEqual(status,201)
        source = dict(resource_id=r['id'],anchor='overview',note_revision=1)
        path = '/dev/v1/research/'+r['id']+'/notes/overview'
        note = dict(known='관찰한 근거 😀',intention='',alternative='UNKNOWN',outcome='사후 결과')
        self.assertEqual(self.call(path,'PUT',dict(note=note,expected_revision=0))[0],200)
        return source

    def proposal(self,source=None):
        return dict(rule=dict(patch_range='UNKNOWN',applicability=dict(champion='UNKNOWN',
                    role='UNKNOWN',matchup='UNKNOWN',level='UNKNOWN',context='UNKNOWN'),
                    required_fields=['UNKNOWN'],claim='직접 작성한 주장 😀',mechanism='UNKNOWN',
                    counterexamples=['UNKNOWN'],author='local operator',limitations=['UNKNOWN']),
                    source=source or self.source(),rule_id=None,expected_version=None)

    def test_full_immutable_version_lifecycle_and_no_promotion(self):
        b=self.proposal();status,first,_=self.call(self.base,'POST',b)
        self.assertEqual(status,201)
        self.assertEqual(first['review_state'],'EXPLORATORY')
        self.assertFalse(first['coaching_enabled'])
        self.assertIsNone(first['supersedes'])
        self.assertEqual(first['source_refs'][0]['note_revision'],1)
        path=self.base+'/'+first['rule_id']
        b.update(rule_id=first['rule_id'],expected_version=first['version'])
        b['rule']['claim']='条件を修正した主張 😀'
        status,second,_=self.call(self.base,'POST',b)
        self.assertEqual(status,201);self.assertNotEqual(second['version'],first['version'])
        self.assertEqual(second['supersedes'],first['version'])
        self.assertEqual(self.call(path+'/versions/'+first['version'])[1],first)
        self.assertEqual(self.call(path)[1],second)
        rows=self.call(self.base)[1]
        self.assertEqual([r['current'] for r in rows],[True,False])
        self.assertEqual(self.call(self.base,'POST',b)[0],409)
        self.assertEqual(self.call(path,'DELETE',{'expected_version':first['version']})[0],409)
        status,receipt,_=self.call(path,'DELETE',{'expected_version':second['version']})
        self.assertEqual(status,200);self.assertEqual(receipt['deleted_versions'],2)
        self.assertEqual(set(receipt),{'status','receipt_id','deleted_versions'})
        self.assertEqual(self.call(path)[0],404)
        self.assertEqual(self.call('/dev/v1/status')[1]['mode'],'SYNTHETIC_ONLY')
        self.assertFalse(self.call('/dev/v1/status')[1]['real_data_enabled'])

    def test_auth_host_origin_and_cross_site_on_all_routes(self):
        first=self.call(self.base,'POST',self.proposal())[1]
        for path,method,body in ((self.base,'GET',None),(self.base,'POST',{}),
            (self.base+'/'+first['rule_id'],'GET',None),
            (self.base+'/'+first['rule_id']+'/versions/'+first['version'],'GET',None),
            (self.base+'/'+first['rule_id'],'DELETE',{'expected_version':first['version']})):
            self.assertEqual(self.call(path,method,body,auth=False)[0],401)
            self.assertEqual(self.call(path,method,body,extra={'Authorization':'Bearer wrong'})[0],401)
            self.assertEqual(self.call(path,method,body,extra={'Host':'evil.test'})[0],403)
            self.assertEqual(self.call(path,method,body,extra={'Origin':'https://evil.test'})[0],403)
            self.assertEqual(self.call(path,method,body,extra={'Sec-Fetch-Site':'cross-site'})[0],403)

    def test_saved_source_revision_gate_and_cascade(self):
        source=self.source();b=self.proposal(source)
        for revision,status in ((0,422),(True,422),(2,404)):
            bad=copy.deepcopy(b);bad['source']['note_revision']=revision
            self.assertEqual(self.call(self.base,'POST',bad)[0],status)
        first=self.call(self.base,'POST',b)[1]
        deletion=self.call('/dev/v1/research/'+source['resource_id'],'DELETE')
        self.assertEqual(deletion[0],200);self.assertEqual(deletion[1]['deleted_versions'],1)
        self.assertEqual(self.call(self.base+'/'+first['rule_id'])[0],404)
        self.assertEqual(self.call(self.base)[1],[])
        self.assertEqual(self.call(self.base,'POST',b)[0],404)

    def test_exact_input_fields_no_review_or_truth_override(self):
        b=self.proposal()
        bad=copy.deepcopy(b);bad['review_state']='REVIEWED'
        self.assertEqual(self.call(self.base,'POST',bad)[0],422)
        for field,value in (('review_state','REVIEWED'),('coaching_enabled',True),
                            ('source_refs',[]),('confidence',0.99)):
            bad=copy.deepcopy(b);bad['rule'][field]=value
            self.assertEqual(self.call(self.base,'POST',bad)[0],422)
        bad=copy.deepcopy(b);bad['source']['note_sha256']='f'*64
        self.assertEqual(self.call(self.base,'POST',bad)[0],422)
        self.assertEqual(self.call(self.base,'PUT',b)[0],404)
        self.assertEqual(self.call(self.base+'?reviewed=true')[0],400)
        self.assertEqual(self.call(self.base+'/not-a-token')[0],404)
        self.assertEqual(self.call(self.base,'POST',{})[0],422)

    def test_output_limit_rollback_and_static_security(self):
        first=self.call(self.base,'POST',self.proposal())[1]
        original=self.server.limits
        self.server.limits=Limits(30,original.observations,original.actions,
                                 original.scenarios,original.comparisons,original.pending_jobs)
        path=self.base+'/'+first['rule_id']
        for route in (self.base,path,path+'/versions/'+first['version']):
            status,error,_=self.call(route)
            self.assertEqual(status,413);self.assertEqual(error['error_code'],'KNOWLEDGE_TOO_LARGE')
        self.assertEqual(self.call(self.base,'POST',self.proposal(first['source_refs'][0]))[0],413)
        self.server.limits=original
        self.assertEqual(self.call(path)[1],first)
        self.assertEqual(len(self.call(self.base)[1]),1)
        status,js,headers=self.call('/knowledge.js',auth=False)
        self.assertEqual(status,200);self.assertIn(b'EXPLORATORY',js)
        self.assertIn("frame-ancestors 'none'",headers['Content-Security-Policy'])
        self.assertEqual(headers['Cache-Control'],'no-store')


if __name__=='__main__':unittest.main()

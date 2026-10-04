import json,unittest
from tests_r4 import test_http as helpers
class ResearchAPITests(unittest.TestCase):
    setUp=helpers.HTTPTests.setUp
    tearDown=helpers.HTTPTests.tearDown
    call=helpers.HTTPTests.call
    def add(self,kind):
        status,r,_=self.call('/dev/v1/research','POST',{'source_type':kind,'title':'test'})
        self.assertEqual(status,201);return r
    def test_auth_and_client_cannot_assert_verified_report(self):
        self.assertEqual(self.call('/dev/v1/research',auth=False)[0],401)
        self.assertEqual(self.call('/dev/v1/research','POST',{'source_type':'raw_json','title':'x','raw_text':'{}','report':{'coaching_enabled':True}})[0],422)
    def test_examples_deduplicate_and_never_activate(self):
        a=self.add('official_sample');b=self.add('official_sample');self.assertEqual(a['id'],b['id']);self.assertFalse(a['report']['coaching_enabled']);self.assertEqual(a['report']['declared_source_kind'],'DOCUMENTATION_SAMPLE')
        v=self.add('video_example');self.assertEqual(len(v['report']['candidates']),33);self.assertFalse(v['report']['game_clock_mapping_verified'])
    def test_note_save_conflict_and_delete(self):
        v=self.add('video_example');rid=v['id'];anchor=str(v['report']['candidates'][0]['cue_index']);path='/dev/v1/research/'+rid+'/notes/'+anchor
        self.assertEqual(self.call(path)[1]['revision'],0)
        note=dict(known='미니맵 확인 필요',intention='당시 의도',alternative='대기',outcome='사후 결과')
        self.assertEqual(self.call(path,'PUT',{'note':note,'expected_revision':0})[1]['revision'],1)
        self.assertEqual(self.call(path,'PUT',{'note':note,'expected_revision':0})[0],409)
        self.assertEqual(self.call('/dev/v1/research/'+rid+'/notes/999999')[0],422)
        self.assertFalse(self.call('/dev/v1/research/'+rid)[1]['report']['coaching_enabled'])
        self.assertEqual(self.call('/dev/v1/research/'+rid,'DELETE')[0],200);self.assertEqual(self.call(path)[0],404)
    def test_raw_import_does_not_save_identifiers_or_claimed_mode(self):
        raw=json.dumps({'summonerName':'PRIVATE_SENTINEL','coaching_enabled':True})
        status,r,_=self.call('/dev/v1/research','POST',{'source_type':'raw_json','title':'local','raw_text':raw})
        self.assertEqual(status,201);self.assertFalse(r['report']['coaching_enabled']);self.assertEqual(r['report']['declared_source_kind'],'UNVERIFIED_IMPORT');self.assertNotIn('PRIVATE_SENTINEL',json.dumps(r))
    def test_bad_transcript_does_not_create_resource(self):
        self.assertEqual(self.call('/dev/v1/research','POST',{'source_type':'transcript','title':'x','raw_text':'bad','video_id':'abcdefghijk'})[0],422)
        self.assertEqual(self.call('/dev/v1/research')[1],[])

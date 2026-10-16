"""Real phased control flow with isolated network boundary, never provider calls."""
import json,tempfile,unittest,os,hashlib
from pathlib import Path
from unittest.mock import patch
from tests_expert import test_gemini_daily as fixtures
from scripts import run_video_diagnostic as cli

class VideoCliTests(unittest.TestCase):
 def setUp(self):
  self.f=fixtures.DailyTests();self.f.setUp();self.f.now=1792191000;self.f.ledger['initialized_at']=self.f.now-100
 def initial(self,status=400):
  f=self.f;s=f.m.complete(f.reserve(),'TEXT',f.now,200);s,q=f.m.reserve_video(s,f.ledger,f.config,f.source(),f.now,'42',f.proof);return f.m.complete(s,'VIDEO',f.now,status),q
 def setup_files(self,root,status=400):
  s,q=self.initial(status);plan=json.loads(Path('config/video_api_diagnostic.json').read_text())
  for name,value in [('state.json',s),('quota.json',q),('plan.json',plan),('recovery.json',dict(status='FOUND'))]:(root/name).write_text(json.dumps(value))
  return ['--state',str(root/'state.json'),'--ledger',str(root/'quota.json'),'--plan',str(root/'plan.json'),'--recovery-receipt',str(root/'recovery.json'),'--output-dir',str(root/'out')]
 def transport(self,calls):
  def run(method,url,headers,body,*args):
   calls.append((method,body))
   if method=='GET':return 200,{},dict(items=[dict(id='ixRanV-rdAQ',snippet=dict(title='Google reference video',channelId='UC'+'a'*22,channelTitle='Reference',publishedAt='2025-01-01T00:00:00Z',liveBroadcastContent='none'),contentDetails=dict(duration='PT18M22S'),status=dict(privacyStatus='public',uploadStatus='processed'))])
   return 400,{},dict(error=dict(code='PRIVATE_PERSON',status='INVALID_ARGUMENT',message='Request contains an invalid argument.',details=[{'@type':'type.googleapis.com/google.rpc.BadRequest','fieldViolations':[dict(field='contents[0].parts[1].fileData.fileUri',description='Invalid URI TEST_SECRET')]}]))
  return run
 def kwargs(self,calls):return dict(clock=lambda:self.f.now+70,transport=self.transport(calls),verifier=lambda **kw:self.f.proof,input_support_verifier=lambda:dict(status='SUPPORTED',model=self.f.m.MODEL),ack_verifier=lambda *args:True,sleeper=lambda n:None)
 def test_preflight_only_metadata_no_text_and_full_charge(self):
  calls=[]
  with tempfile.TemporaryDirectory() as t,patch.dict(os.environ,dict(GITHUB_RUN_ID='43',GITHUB_RUN_ATTEMPT='1',GEMINI_API_KEY='TEST_SECRET',YOUTUBE_API_KEY='TEST_SECRET'),clear=True):
   root=Path(t);args=self.setup_files(root);self.assertEqual(cli.main(['--phase','prepare']+args,**self.kwargs(calls)),0)
   receipt=json.loads((root/'out/receipt.json').read_text());self.assertTrue(receipt['video_reserved']);self.assertEqual(receipt['stage'],1);self.assertEqual(receipt['full_original_seconds_charged'],1102);self.assertTrue(all(m=='GET' for m,b in calls));self.assertEqual(receipt['text_requests'],0)
 def test_dispatch_once_preserves_typed_error_and_no_secret(self):
  calls=[]
  with tempfile.TemporaryDirectory() as t,patch.dict(os.environ,dict(GITHUB_RUN_ID='43',GITHUB_RUN_ATTEMPT='1',GEMINI_API_KEY='TEST_SECRET',YOUTUBE_API_KEY='TEST_SECRET'),clear=True),patch('scripts.run_gemini_daily.claim_root',return_value=Path(t)/'claims'):
   root=Path(t);args=self.setup_files(root);cli.main(['--phase','prepare']+args,**self.kwargs(calls));out=root/'out';args2=['--phase','dispatch','--state',str(out/'daily-state.json'),'--ledger',str(out/'quota-ledger.json'),'--plan',str(root/'plan.json'),'--reservation-artifact-id','7','--output-dir',str(root/'result')];cli.main(args2,**self.kwargs(calls))
   r=json.loads((root/'result/receipt.json').read_text());self.assertEqual(r['http_status'],400);self.assertEqual(r['new_provider_requests'],1);self.assertEqual(sum(m=='POST' for m,b in calls),1);self.assertNotIn('TEST_SECRET',json.dumps(r));self.assertNotIn('PRIVATE_PERSON',json.dumps(r));self.assertEqual(r['error_details']['rejected_field'],'contents[0].parts[1].fileData.fileUri')
 def test_429_holds_before_any_new_external_request(self):
  calls=[]
  with tempfile.TemporaryDirectory() as t,patch.dict(os.environ,dict(GITHUB_RUN_ID='43',GITHUB_RUN_ATTEMPT='1'),clear=True):
   root=Path(t);args=self.setup_files(root,429);self.assertEqual(cli.main(['--phase','prepare']+args,**self.kwargs(calls)),0);r=json.loads((root/'out/receipt.json').read_text());self.assertEqual(r['reason'],'DATE_EXTERNAL_DIAGNOSIS_STOPPED');self.assertEqual(calls,[])

 def test_malformed_metadata_http200_is_durable_failure_not_success(self):
  calls=[]
  def malformed(*args):calls.append(args[0]);return 200,{},b'not-json'
  with tempfile.TemporaryDirectory() as t,patch.dict(os.environ,dict(GITHUB_RUN_ID='43',GITHUB_RUN_ATTEMPT='1',GEMINI_API_KEY='TEST_SECRET',YOUTUBE_API_KEY='TEST_SECRET'),clear=True):
   root=Path(t);args=self.setup_files(root);kw=self.kwargs(calls);kw['transport']=malformed
   self.assertEqual(cli.main(['--phase','prepare']+args,**kw),0)
   r=json.loads((root/'out/receipt.json').read_text());self.assertEqual(r['classification'],'MALFORMED_RESPONSE');self.assertFalse(r['video_reserved']);self.assertEqual(r['new_provider_requests'],0)
   state=json.loads((root/'out/daily-state.json').read_text());self.assertEqual(state['events'][-1]['kind'],'PREPARATION_FAILURE');self.assertEqual(calls,['GET'])

 def test_metadata_auth_status_overrides_http400_and_stops_date(self):
  calls=[]
  def auth(*args):calls.append(args[0]);return 400,{},dict(error=dict(code='PRIVATE_PERSON',status='UNAUTHENTICATED',message='private message'))
  with tempfile.TemporaryDirectory() as t,patch.dict(os.environ,dict(GITHUB_RUN_ID='43',GITHUB_RUN_ATTEMPT='1',GEMINI_API_KEY='TEST_SECRET',YOUTUBE_API_KEY='TEST_SECRET'),clear=True):
   root=Path(t);args=self.setup_files(root);kw=self.kwargs(calls);kw['transport']=auth
   cli.main(['--phase','prepare']+args,**kw);r=json.loads((root/'out/receipt.json').read_text());self.assertEqual(r['classification'],'AUTHENTICATION');self.assertNotIn('PRIVATE_PERSON',json.dumps(r))
   s=json.loads((root/'out/daily-state.json').read_text());q=json.loads((root/'out/quota-ledger.json').read_text());plan=json.loads((root/'plan.json').read_text())
   with self.assertRaisesRegex(ValueError,'DATE_EXTERNAL_DIAGNOSIS_STOPPED'):cli.policy.choose_stage(s,q,plan,self.f.now+80)

 def test_normal_cli_date_stop_precedes_external_gate(self):
  with tempfile.TemporaryDirectory() as t,patch.dict(os.environ,dict(GITHUB_RUN_ID='43',GITHUB_RUN_ATTEMPT='1'),clear=True):
   root=Path(t);self.setup_files(root,429)
   with patch('scripts.run_gemini_daily._gate',side_effect=AssertionError('unexpected external gate')) as gate:
    rc=cli.base.main(['--phase','pretext','--state',str(root/'state.json'),'--ledger',str(root/'quota.json'),'--recovery-receipt',str(root/'recovery.json'),'--output-dir',str(root/'normal')],clock=lambda:self.f.now+70)
   self.assertEqual(rc,1);gate.assert_not_called();r=json.loads((root/'normal/receipt.json').read_text());self.assertEqual(r['reason'],'DATE_EXTERNAL_DIAGNOSIS_STOPPED')

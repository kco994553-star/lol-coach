"""Safe structure reports must distinguish complete text from incomplete output."""
import copy,json,unittest

class ResponseDiagnosticTests(unittest.TestCase):
 def inspect(self,response):
  try:from coach_v1.gemini_response_diagnostics import inspect_response
  except ImportError:self.fail("Staged response diagnostics are not implemented")
  return inspect_response(response)
 def normal(self):
  return {'candidates':[{'finishReason':'STOP','content':{'role':'model','parts':[{'text':'SECRET_THOUGHT','thought':True,'thoughtSignature':'SECRET_SIGNATURE'},{'text':'OK'}]}}], 'usageMetadata':{'promptTokenCount':4,'candidatesTokenCount':1,'thoughtsTokenCount':5,'totalTokenCount':10}}
 def test_complete_text_excludes_thoughts_but_reports_usage_and_types(self):
  d=self.inspect(self.normal());self.assertTrue(d['complete_text']);self.assertEqual(d['pipeline']['schema_validation'],'PASS');self.assertEqual(d['nonthought_text_bytes'],2);self.assertEqual(d['usage']['totalTokenCount'],10);self.assertEqual(d['thought_true_parts'],1)
  self.assertNotIn('SECRET_',json.dumps(d));self.assertEqual(d['candidate_count'],1)
 def test_max_tokens_is_incomplete_with_precise_gate_and_usage(self):
  r=self.normal();r['candidates'][0]['finishReason']='MAX_TOKENS';d=self.inspect(r)
  self.assertFalse(d['complete_text']);self.assertEqual(d['failed_check'],'FINISH_REASON_STOP');self.assertEqual(d['finish_reasons'],['MAX_TOKENS']);self.assertEqual(d['usage']['thoughtsTokenCount'],5)
 def test_duplicate_json_fails_parse_not_transport_or_schema(self):
  d=self.inspect(b'{"candidates":[],"candidates":[]}');self.assertEqual(d['pipeline']['json_parse'],'FAIL');self.assertEqual(d['pipeline']['schema_validation'],'NOT_REACHED');self.assertFalse(d['complete_text'])
 def test_blocked_prompt_and_missing_parts_are_identified_without_raw_values(self):
  r=self.normal();r['promptFeedback']={'blockReason':'SAFETY','blockReasonMessage':'PRIVATE_BLOCK_EXPLANATION'};d=self.inspect(r);self.assertEqual(d['failed_check'],'PROMPT_NOT_BLOCKED');self.assertNotIn('PRIVATE_',json.dumps(d))
  r=self.normal();r['candidates'][0]['content'].pop('parts');d=self.inspect(r);self.assertEqual(d['failed_check'],'NONEMPTY_PARTS');self.assertFalse(d['complete_text'])
 def test_unsupported_part_is_not_silently_coerced_or_leaked(self):
  r=self.normal();r['candidates'][0]['content']['parts']=[{'text':'OK','partMetadata':{'PRIVATE_IDENTIFIER':'PRIVATE_VALUE'}}];d=self.inspect(r);self.assertEqual(d['failed_check'],'TEXT_PART_KEYS');self.assertNotIn('PRIVATE_',json.dumps(d));self.assertFalse(d['complete_text'])
 def test_actual_dispatch_retains_safe_failure_gate_and_token_usage(self):
  import tempfile
  from pathlib import Path
  from tests_expert.test_gemini_daily import DailyTests
  f=DailyTests();f.setUp();r=self.normal();r['candidates'][0]['finishReason']='MAX_TOKENS'
  with tempfile.TemporaryDirectory() as p:s=f.m.dispatch(f.reserve(),'TEXT',f.now,'42','7',Path(p),'TEST_ONLY',lambda *a:(200,{},r))
  out=s['events'][-1];self.assertEqual(out['classification'],'MALFORMED_RESPONSE');self.assertIn('response_diagnostics',out['safe_output']);self.assertEqual(out['safe_output']['response_diagnostics']['failed_check'],'FINISH_REASON_STOP');self.assertNotIn('SECRET_',json.dumps(s))
 def test_lone_surrogate_is_reported_without_losing_pipeline_or_usage(self):
  r=self.normal();r['candidates'][0]['content']['parts']=[{'text':'\ud800'}]
  try:d=self.inspect(r)
  except UnicodeError:self.fail('Invalid UTF8 text must retain safe failure diagnostics')
  self.assertFalse(d['complete_text']);self.assertEqual(d['failed_check'],'TEXT_UTF8');self.assertEqual(d['usage']['totalTokenCount'],10)
 def test_http200_json_array_is_format_failure_not_network_failure(self):
  import tempfile
  from pathlib import Path
  from tests_expert.test_gemini_daily import DailyTests
  f=DailyTests();f.setUp()
  with tempfile.TemporaryDirectory() as p:s=f.m.dispatch(f.reserve(),'TEXT',f.now,'42','7',Path(p),'TEST_ONLY',lambda *a:(200,{},b'[]'))
  out=s['events'][-1];self.assertEqual(out['classification'],'MALFORMED_RESPONSE');self.assertEqual(out['safe_output']['response_diagnostics']['failed_check'],'RESPONSE_OBJECT')

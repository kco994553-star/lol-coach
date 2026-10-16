"""Combined legacy+diagnostic daily quota and exact-prefix behavior."""
import copy,json,tempfile,unittest,hashlib
from pathlib import Path
from tests_expert import test_gemini_daily as fixtures

class VideoPolicyTests(unittest.TestCase):
 def setUp(self):
  self.f=fixtures.DailyTests();self.f.setUp();self.f.now=1792191000;self.f.ledger['initialized_at']=self.f.now-100
  self.plan=dict(format='video.step-diagnostic.v1',active=True,session='video-api-20261017',revision='2026-10-17.1',reference_sha256='a'*64,content_reviews=[])
 def module(self):
  try:from coach_v1 import video_diagnostic_policy as p
  except ImportError:self.fail('Shared staged-video policy not implemented')
  return p
 def old_failure(self,status=400):
  f=self.f;s=f.m.complete(f.reserve(),'TEXT',f.now,200);s,q=f.m.reserve_video(s,f.ledger,f.config,f.source(),f.now,'42',f.proof);return f.m.complete(s,'VIDEO',f.now,status),q
 def source(self,stage=1):
  video=self.f.source()['video'];video.update(id='ixRanV-rdAQ' if stage==1 else 'brQaUDGnXTs',duration_seconds=1102);video['url']='https://www.youtube.com/watch?v='+video['id']
  return self.module().source_from_video(video,stage,self.plan)
 def config(self):return dict(self.f.config,purpose='VIDEO_API_DIAGNOSTIC',configuration_revision='video-step:2026-10-17.1')
 def reserve(self,s,q,run='43',stage=1):return self.module().reserve(s,q,self.config(),self.plan,self.source(stage),self.f.now+70,run,self.f.proof)
 def review(self,s,root,plan):
  result=s['events'][-1];row=next(e for e in s['events'] if e.get('reservation_id')==result['reservation_id'] and e['kind']=='RESERVATION');d=dict(stage=row['source']['diagnostic']['stage'],reservation_id=row['reservation_id'],result_sha256=self.f.m._digest(result),decision='DIAGNOSTIC_CONTENT_USABLE',reviewer_role='SEPARATE_CONTENT_REVIEW',source_fact_review='NOT_COMPLETED',rationale='Synthetic diagnostic content fixture; no actual source or user approval.')
  p=root/'evidence/actual-evidence/review.json';p.parent.mkdir(parents=True);p.write_text(json.dumps(d));plan['content_reviews'].append(dict(path='evidence/actual-evidence/review.json',sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
 def test_old_video_counts_and_new_reservation_charges_full_origin(self):
  p=self.module();s,q=self.old_failure();self.assertEqual(p.choose_stage(s,q,self.plan,self.f.now+70),1);a,b=self.reserve(s,q);self.assertEqual(a['schema_version'],'gemini.daily-state.v2');self.assertEqual(a['events'][:len(s['events'])],s['events']);self.assertEqual(b['reservations'][:-1],q['reservations']);self.assertEqual(b['reservations'][-1]['seconds'],1102)
 def test_http_success_needs_separate_content_review_and_then_url_stage(self):
  p=self.module();s,q=self.old_failure();s,q=self.reserve(s,q);s=self.f.m.complete(s,'VIDEO',self.f.now+70,200,safe_output=dict(diagnostic_content=dict(content_candidate_valid=True)))
  with self.assertRaisesRegex(ValueError,'AWAITING_CONTENT_REVIEW'):p.choose_stage(s,q,self.plan,self.f.now+71)
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);self.review(s,root,self.plan);self.assertEqual(p.choose_stage(s,q,self.plan,self.f.now+71,root=root),2)
 def test_quota_auth_permission_halt_across_configuration_changes(self):
  p=self.module()
  for status in [429,401,403]:
   s,q=self.old_failure(status)
   with self.assertRaisesRegex(ValueError,'DATE_EXTERNAL_DIAGNOSIS_STOPPED'):p.choose_stage(s,q,self.plan,self.f.now+70)
 def test_same_failed_stage_is_not_replayed_on_new_day(self):
  p=self.module();s,q=self.old_failure();s,q=self.reserve(s,q);s=self.f.m.complete(s,'VIDEO',self.f.now+70,400)
  with self.assertRaisesRegex(ValueError,'FAILED_STAGE_REQUIRES_NEW_EVIDENCE'):p.choose_stage(s,q,self.plan,self.f.now+86400)
 def test_durable_unknown_result_blocks_new_diagnosis(self):
  p=self.module();s,q=self.old_failure();s,q=self.reserve(s,q)
  with self.assertRaisesRegex(ValueError,'UNRESOLVED_VIDEO_RESERVATION'):p.choose_stage(s,q,self.plan,self.f.now+80)
 def test_shared_daily_budget_counts_legacy_ledger_rows(self):
  p=self.module();s,q=self.old_failure()
  for i in range(2):q['reservations'].append(dict(video_id='extra00000'+str(i),seconds=100,reserved_at=self.f.now,reservation_id=str(i+1)*64))
  with self.assertRaisesRegex(ValueError,'DAILY_DIAGNOSTIC_VIDEO_LIMIT'):p.choose_stage(s,q,self.plan,self.f.now+70)
 def test_unreviewed_or_forged_ticket_never_advances(self):
  p=self.module();s,q=self.old_failure();s,q=self.reserve(s,q);s=self.f.m.complete(s,'VIDEO',self.f.now+70,200,safe_output=dict(diagnostic_content=dict(content_candidate_valid=True)))
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);self.review(s,root,self.plan);self.plan['content_reviews'][0]['sha256']='f'*64
   with self.assertRaises(ValueError):p.choose_stage(s,q,self.plan,self.f.now+80,root=root)
 def test_recovery_accepts_video_only_phase_for_typed_diagnostic_run(self):
  self.module();s,q=self.old_failure();s,q=self.reserve(s,q);artifact=dict(id=88,name='gemini-daily-state-43-VIDEO',created_at='2026-10-16T22:51:10Z',expired=False)
  got,quota=self.f.m.recover_pairs([dict(id=43,run_number=2)],99,lambda n:[artifact],lambda *a:(s,q),lambda n:True,self.f.now+80);self.assertEqual(got,s);self.assertEqual(quota,q)
 def test_recovery_never_uses_video_only_exception_for_old_normal_run(self):
  self.module();s,q=self.old_failure();artifact=dict(id=88,name='gemini-daily-state-42-VIDEO',created_at='2026-10-16T22:50:00Z',expired=False)
  with self.assertRaisesRegex(ValueError,'MISSING_DURABLE_DAILY_PHASE'):self.f.m.recover_pairs([dict(id=42,run_number=1)],99,lambda n:[artifact],lambda *a:(s,q),lambda n:True,self.f.now+80)
 def test_distinct_legacy_video_rows_with_same_id_digest_still_count(self):
  p=self.module();s,q=self.old_failure()
  for i in range(2):q['reservations'].append(dict(video_id='extra00000'+str(i),seconds=100,reserved_at=self.f.now,reservation_id='1'*64))
  with self.assertRaisesRegex(ValueError,'DAILY_DIAGNOSTIC_VIDEO_LIMIT'):p.choose_stage(s,q,self.plan,self.f.now+70)

 def test_normal_route_cannot_bypass_same_day_failure_from_other_revision(self):
  f=self.f;tomorrow=f.now+86400;s,q=self.old_failure();cfg=dict(self.config(),configuration_revision='new-diagnostic')
  s=f.m.preparation_failure(s,cfg,tomorrow,'43','VIDEO_METADATA',429)
  proof=dict(f.proof,checked_at=f.m.datetime.fromtimestamp(tomorrow,f.m.timezone.utc).date().isoformat())
  with self.assertRaisesRegex(ValueError,'DATE_EXTERNAL_DIAGNOSIS_STOPPED'):f.m.reserve_text(s,q,dict(f.config,configuration_revision='normal-new'),tomorrow,'44',proof)
 def test_provider_auth_status_in_generic_http_failure_also_stops_date(self):
  p=self.module();f=self.f;s,q=self.old_failure();s,q=self.reserve(s,q)
  s=f.m.complete(s,'VIDEO',f.now+70,400,safe_output=dict(provider_error=dict(error_status='UNAUTHENTICATED')))
  with self.assertRaisesRegex(ValueError,'DATE_EXTERNAL_DIAGNOSIS_STOPPED'):p.choose_stage(s,q,self.plan,f.now+80)

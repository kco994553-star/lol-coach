#!/usr/bin/env python3
"""One durable, reviewed stage per trusted workflow; no TEXT generation calls."""
import argparse,hashlib,json,os,re,sys,time,urllib.request
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from coach_v1 import gemini_daily as d,video_diagnostic_policy as policy
from coach_v1.expert_collector import atomic_json
from scripts import run_gemini_daily as base

ROOT=Path(__file__).resolve().parents[1]

def config_for(plan):
 c=base.read_json(ROOT/'config/evidence_intake.json',200000)
 c.update(purpose=policy.PURPOSE,configuration_revision='video-step:'+plan['revision']);return d.validate_config(c)

def metadata_video(collector,video_id):
 data=collector._youtube('videos',part='snippet,contentDetails,status',id=video_id)
 rows=data.get('items');d.require(isinstance(rows,list) and len(rows)==1,'DIAGNOSTIC_SOURCE_METADATA_UNAVAILABLE');r=rows[0]
 d.require(r.get('id')==video_id,'DIAGNOSTIC_SOURCE_METADATA_UNAVAILABLE');st=r.get('status',{});sn=r.get('snippet',{})
 d.require(st.get('privacyStatus')=='public' and st.get('uploadStatus')=='processed' and sn.get('liveBroadcastContent','none')=='none','DIAGNOSTIC_SOURCE_NOT_PUBLIC')
 duration=r.get('contentDetails',{}).get('duration');m=re.fullmatch(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?',duration if isinstance(duration,str) else '')
 d.require(m is not None,'DIAGNOSTIC_SOURCE_DURATION_UNKNOWN');seconds=sum(int(v or 0)*n for v,n in zip(m.groups(),(3600,60,1)));d.require(seconds>0,'DIAGNOSTIC_SOURCE_DURATION_UNKNOWN')
 video=dict(id=video_id,url='https://www.youtube.com/watch?v='+video_id,title=sn.get('title'),channel_id=sn.get('channelId'),channel_name=sn.get('channelTitle'),speaker='UNKNOWN',speaker_verified=False,published_at=sn.get('publishedAt'),upload_date=None,duration_seconds=seconds,language='UNKNOWN')
 return video

def verify_video_support():
 from coach_v1.expert_entitlement import _DOM
 url='https://ai.google.dev/gemini-api/docs/models/'+d.MODEL
 with urllib.request.urlopen(url,timeout=20) as r:
  d.require(r.status==200 and r.headers.get_content_type()=='text/html','MODEL_VIDEO_SUPPORT_UNVERIFIED');raw=r.read(2000001)
 d.require(len(raw)<=2000000,'MODEL_VIDEO_SUPPORT_UNVERIFIED');tree=_DOM(raw.decode()).root
 tables=[n.text() for n in tree.nodes() if n.tag=='table' and 'Model code '+d.MODEL+' ' in n.text()]
 d.require(any(re.search(r'Inputs (?:(?!Output).)*\bVideo\b(?:(?!Output).)* Output Text',t) for t in tables),'MODEL_VIDEO_SUPPORT_UNVERIFIED')
 return dict(status='SUPPORTED',model=d.MODEL,url=url,sha256=hashlib.sha256(raw).hexdigest(),checked_at_utc=d.datetime.now(d.timezone.utc).isoformat(),video_input_documented=True)


def main(argv=None,*,clock=None,transport=None,verifier=None,ack_verifier=None,sleeper=None,input_support_verifier=None):
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--phase',choices=('prepare','dispatch'),required=True);p.add_argument('--state',required=True);p.add_argument('--ledger',required=True);p.add_argument('--recovery-receipt');p.add_argument('--reservation-artifact-id');p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--plan',default='config/video_api_diagnostic.json');a=p.parse_args(argv)
 now=int((clock or time.time)());state=None;quota=None;cfg=None;collector=None;stage=None
 receipt=dict(schema_version='gemini.video-diagnostic-receipt.v1',phase=a.phase,status='BLOCKED_EXTERNAL',reason=None,text_requests=0,new_provider_requests=0,video_reserved=False,has_state=False,http_status=None,classification=None,stage=None,source_review='NOT_REVIEWED',expert_claims_adopted=0,coaching_accuracy=None)
 try:
  run=base._context();plan=policy.validate_plan(base.read_json(a.plan,200000));cfg=config_for(plan);runtime=base.read_json(ROOT/'config/expert_runtime.json',200000)
  state,quota=d.validate_pair(base.read_json(a.state,32000000),base.read_json(a.ledger,32000000),now);d.require(state['project_name']==runtime['project_name'],'PROJECT_STATE_MISMATCH')
  reference=ROOT/'evidence/actual-evidence/video-step-diagnostic/official-reference.json'
  d.require(hashlib.sha256(reference.read_bytes()).hexdigest()==plan['reference_sha256'],'OFFICIAL_REFERENCE_HASH_MISMATCH')
  if a.phase=='prepare':
   d.require(a.recovery_receipt and base.read_json(a.recovery_receipt).get('status')=='FOUND','RECOVERY_REQUIRED')
   stage=policy.choose_stage(state,quota,plan,now,root=ROOT)
   if stage is None:receipt.update(status='COMPLETE',reason='DIAGNOSTIC_COMPLETE_NORMAL_LIMIT_RESTORED')
   else:
    proof,collector=base._gate(runtime,now,verifier or base.verify_free_entitlement,transport)
    support=(input_support_verifier or verify_video_support)();d.require(support.get('status')=='SUPPORTED' and support.get('model')==d.MODEL,'MODEL_VIDEO_SUPPORT_UNVERIFIED')
    atomic_json(a.output_dir/'entitlement.json',dict(free=proof,input_support=support))
    from coach_v1.video_diagnostic_payload import REFERENCE_ID,TARGET_ID
    video=metadata_video(collector,REFERENCE_ID if stage==1 else TARGET_ID);source=policy.source_from_video(video,stage,plan)
    state,quota=policy.reserve(state,quota,cfg,plan,source,now,run,proof,root=ROOT)
    atomic_json(a.output_dir/'source-plan.json',source);receipt.update(status='READY',reason='VIDEO_RESERVED',video_reserved=True,stage=stage,request_sha256=d.pending(state,'VIDEO')['request_sha256'],request_structure=d.video_body(source),full_original_seconds_charged=video['duration_seconds'],requested_start_seconds=source['start_seconds'],requested_end_seconds=source['end_seconds'],source_metadata_verified=True)
  else:
   row=d.pending(state,'VIDEO');source=row['source'];d.require(row['purpose']==policy.PURPOSE and row['configuration_fingerprint']==d.fingerprint(cfg),'DIAGNOSTIC_RESERVATION_MISMATCH');stage=source['diagnostic']['stage'];receipt['stage']=stage
   d.require(source['diagnostic']['revision']==plan['revision'] and source['diagnostic']['reference_sha256']==plan['reference_sha256'],'DIAGNOSTIC_CONFIGURATION_CHANGED')
   charges=[r for r in quota['reservations'] if r['reservation_id']==row['reservation_id']];d.require(len(charges)==1 and charges[0]['seconds']==source['video']['duration_seconds'],'VIDEO_CHARGE_REQUIRED')
   # This reservation already consumes its slot. Recheck global terminal failures
   # without attempting to reserve another slot or to replay a previous request.
   d.assert_date_external_allowed(state,now)
   (ack_verifier or base.verify_ack)(a.reservation_artifact_id,'VIDEO',state,quota,run)
   prior=[e['created_at'] for e in state['events'] if e['kind']=='RESULT'];remaining=max(0,61-(now-max(prior,default=0)))
   while remaining>0:
    pause=min(30,remaining);print('Conservative shared request separation: '+str(pause)+'s',flush=True);(sleeper or time.sleep)(pause);remaining-=pause
   now=int((clock or time.time)());base._gate(runtime,now,verifier or base.verify_free_entitlement,transport)
   state=d.dispatch(state,'VIDEO',now,run,a.reservation_artifact_id,base.claim_root(run),os.environ.get('GEMINI_API_KEY'),transport or base._python_transport)
   result=state['events'][-1];receipt.update(status='SUCCESS_UNREVIEWED' if result['classification']=='VIDEO_SUCCESS_UNREVIEWED' else 'BLOCKED_EXTERNAL',reason=result['classification'],http_status=result['http_status'],classification=result['classification'],new_provider_requests=1,response_diagnostics=result['safe_output'].get('response_diagnostics'),provider_error=result['safe_output'].get('provider_error'),error_details=result['safe_output'].get('error_details'),diagnostic_content=result['safe_output'].get('diagnostic_content'),request_sha256=row['request_sha256'],full_original_seconds_charged=source['video']['duration_seconds'])
   if result['classification']=='VIDEO_SUCCESS_UNREVIEWED':atomic_json(a.output_dir/'extraction.json',dict(source=source,**result['safe_output']))
  receipt['has_state']=True
 except Exception as e:
  known={'DIAGNOSTIC_DISABLED','DIAGNOSTIC_COMPLETE_NORMAL_LIMIT_RESTORED','DAILY_DIAGNOSTIC_VIDEO_LIMIT','AWAITING_CONTENT_REVIEW','FAILED_STAGE_REQUIRES_NEW_EVIDENCE','DATE_EXTERNAL_DIAGNOSIS_STOPPED','UNRESOLVED_VIDEO_RESERVATION','VIDEO_CONTENT_NOT_USABLE','DIAGNOSTIC_SOURCE_DURATION_UNKNOWN','DIAGNOSTIC_SOURCE_METADATA_UNAVAILABLE','DIAGNOSTIC_SOURCE_NOT_PUBLIC','ROLLING_VIDEO_BUDGET_EXHAUSTED','RECOVERY_REQUIRED','EXISTING_TEXT_SUCCESS_REQUIRED','MODEL_VIDEO_SUPPORT_UNVERIFIED','OFFICIAL_REFERENCE_HASH_MISMATCH'}
  receipt['reason']=str(e) if str(e) in known else 'INVALID_OR_UNAVAILABLE_DIAGNOSTIC_STATE';receipt['stage']=stage
  status=getattr(e,'http_status',None)
  auth_failure=getattr(e,'reason',None)=='MISSING_API_KEYS'
  if (status is not None or auth_failure) and state is not None and cfg is not None:
   diagnostic=collector.diagnostics[-1] if collector is not None and collector.diagnostics else {}
   from coach_v1.video_diagnostic_payload import safe_error_details
   safe=safe_error_details({'error':{'code':diagnostic.get('error_code'),'status':diagnostic.get('error_status')}});safe={k:safe[k] for k in ('error_code','error_status')};safe['error_message']='Provider metadata error; message redacted.';reason=({'UNAUTHENTICATED':'AUTHENTICATION','PERMISSION_DENIED':'PERMISSION','RESOURCE_EXHAUSTED':'QUOTA_EXCEEDED'}.get(safe.get('error_status'))) or ('AUTHENTICATION' if auth_failure else (getattr(e,'reason',None) if getattr(e,'reason',None) in d.PERSISTENT|{'NETWORK_TIMEOUT','NETWORK_FAILURE','HTTP_FAILURE','SERVER_FAILURE','QUOTA_EXCEEDED'} else ('MALFORMED_RESPONSE' if status==200 else None)));state=d.preparation_failure(state,cfg,now,run,'VIDEO_METADATA',status,reason,safe);receipt.update(http_status=status,classification=d.classify(status,'VIDEO',reason),provider_error=safe)
  receipt['has_state']=state is not None and quota is not None
 if state is not None:atomic_json(a.output_dir/'daily-state.json',state)
 if quota is not None:atomic_json(a.output_dir/'quota-ledger.json',quota)
 atomic_json(a.output_dir/'receipt.json',receipt)
 if os.environ.get('GITHUB_OUTPUT'):
  with open(os.environ['GITHUB_OUTPUT'],'a') as f:
   for k in ('video_reserved','has_state'):f.write(k+'='+str(receipt[k]).lower()+'\n')
 print('VIDEO_DIAGNOSTIC_JSON='+json.dumps(receipt,sort_keys=True),flush=True)
 # Operational holds are durable results, never automatic same-config retries.
 return 0 if receipt['has_state'] else 1

if __name__=='__main__':raise SystemExit(main())

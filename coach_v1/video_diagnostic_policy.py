"""Explicit four-stage exception; all same-project VIDEO reservations count.

Existing events and quota rows are immutable prefixes. A complete HTTP response
cannot advance a stage without a separate, result-bound content review receipt.
"""
from copy import deepcopy
import hashlib,json,re
from pathlib import Path
from . import gemini_daily as d
ROOT=Path(__file__).resolve().parents[1]
PURPOSE='VIDEO_API_DIAGNOSTIC';SESSION='video-api-20261017'

def validate_plan(value):
 p=deepcopy(value)
 d.require(isinstance(p,dict) and set(p)=={'format','active','session','revision','reference_sha256','content_reviews'},'INVALID_VIDEO_DIAGNOSTIC_PLAN')
 d.require(p['format']=='video.step-diagnostic.v1' and type(p['active']) is bool and p['session']==SESSION,'INVALID_VIDEO_DIAGNOSTIC_PLAN')
 d.require(isinstance(p['revision'],str) and re.fullmatch(r'[A-Za-z0-9_.:-]{1,80}',p['revision']) is not None,'INVALID_VIDEO_DIAGNOSTIC_PLAN')
 d.require(re.fullmatch('[a-f0-9]{64}',str(p['reference_sha256'])) is not None and isinstance(p['content_reviews'],list) and len(p['content_reviews'])<=8,'INVALID_VIDEO_DIAGNOSTIC_PLAN')
 return p

def _reviewed(state,row,result,plan,root):
 found=False
 for proof in plan['content_reviews']:
  d.require(isinstance(proof,dict) and set(proof)=={'path','sha256'},'INVALID_CONTENT_REVIEW')
  name=proof['path'];d.require(isinstance(name,str) and name.startswith('evidence/actual-evidence/') and name.endswith('.json') and '..' not in Path(name).parts and not Path(name).is_absolute(),'INVALID_CONTENT_REVIEW')
  path=root/name;d.require(not any(p.is_symlink() for p in [path,*path.parents]) and path.stat().st_size<=32000,'INVALID_CONTENT_REVIEW')
  raw=path.read_bytes();d.require(hashlib.sha256(raw).hexdigest()==proof['sha256'],'CONTENT_REVIEW_HASH_MISMATCH');r=d._json(raw)
  d.require(isinstance(r,dict) and set(r)=={'stage','reservation_id','result_sha256','decision','reviewer_role','source_fact_review','rationale'},'INVALID_CONTENT_REVIEW')
  d.require(r['reviewer_role']=='SEPARATE_CONTENT_REVIEW' and r['decision']=='DIAGNOSTIC_CONTENT_USABLE' and r['source_fact_review']=='NOT_COMPLETED' and isinstance(r['rationale'],str) and 10<=len(r['rationale'])<=2000,'INVALID_CONTENT_REVIEW')
  if r['reservation_id']==row['reservation_id']:
   d.require(r['stage']==row['source']['diagnostic']['stage'] and r['result_sha256']==d._digest(result),'CONTENT_REVIEW_RESULT_MISMATCH');found=True
 return found

def choose_stage(state,ledger,plan,now,*,root=ROOT):
 p=validate_plan(plan);s,q=d.validate_pair(state,ledger,now);d.require(p['active'],'DIAGNOSTIC_DISABLED');day=d.seoul_day(now)
 results={e['reservation_id']:e for e in s['events'] if e['kind']=='RESULT'}
 d.assert_date_external_allowed(s,now)
 for e in s['events']:
  if e['kind']=='RESERVATION' and e['stage']=='VIDEO':d.require(e['reservation_id'] in results,'UNRESOLVED_VIDEO_RESERVATION')
 next_stage=None
 for stage in range(1,5):
  rows=[e for e in s['events'] if e['kind']=='RESERVATION' and e['stage']=='VIDEO' and e['purpose']==PURPOSE and e['source']['diagnostic']['session']==SESSION and e['source']['diagnostic']['stage']==stage]
  if not rows:next_stage=stage;break
  d.require(len(rows)==1,'REPEATED_DIAGNOSTIC_STAGE')
  row=rows[0];result=results[row['reservation_id']]
  d.require(result['classification']=='VIDEO_SUCCESS_UNREVIEWED','FAILED_STAGE_REQUIRES_NEW_EVIDENCE')
  d.require(result['safe_output'].get('diagnostic_content',{}).get('content_candidate_valid') is True,'VIDEO_CONTENT_NOT_USABLE')
  d.require(_reviewed(s,row,result,p,root),'AWAITING_CONTENT_REVIEW')
 if next_stage is None:return None
 ids={(e['source']['video']['id'],e['reservation_id']) for e in s['events'] if e['kind']=='RESERVATION' and e['stage']=='VIDEO' and e['day']==day}
 ids|={(r['video_id'],r['reservation_id']) for r in q['reservations'] if d.seoul_day(r['reserved_at'])==day}
 d.require(len(ids)<3,'DAILY_DIAGNOSTIC_VIDEO_LIMIT')
 return next_stage

def source_from_video(video,stage,plan):
 from .video_diagnostic_payload import validate_source
 p=validate_plan(plan)
 return validate_source(dict(schema_version='evidence.source-plan.v2',purpose=PURPOSE,video=deepcopy(video),start_seconds=0,end_seconds=video['duration_seconds'] if stage<=2 else min(120,video['duration_seconds']),diagnostic=dict(session=SESSION,stage=stage,revision=p['revision'],reference_sha256=p['reference_sha256'])))

def reserve(state,ledger,config,plan,source,now,run_id,proof,*,root=ROOT):
 from .video_diagnostic_payload import validate_source
 stage=choose_stage(state,ledger,plan,now,root=root);d.require(stage is not None,'DIAGNOSTIC_COMPLETE_NORMAL_LIMIT_RESTORED')
 source=validate_source(source);d.require(source['diagnostic']['stage']==stage and source['diagnostic']['revision']==plan['revision'] and source['diagnostic']['reference_sha256']==plan['reference_sha256'],'DIAGNOSTIC_SOURCE_MISMATCH')
 d.require(config['purpose']==PURPOSE,'INVALID_DIAGNOSTIC_PURPOSE')
 s=d.validate_state(state,now);q=d.validate_ledger(ledger,now)
 d.require(any(e['kind']=='RESULT' and e['stage']=='TEXT' and e['classification']=='TEXT_ONLY_SUCCESS' for e in s['events']),'EXISTING_TEXT_SUCCESS_REQUIRED')
 d.require(sum(r['seconds'] for r in q['reservations'] if r['reserved_at']>now-d.CHARGE_WINDOW)+source['video']['duration_seconds']<=d.CAP,'ROLLING_VIDEO_BUDGET_EXHAUSTED')
 # Duplicate video ID is the user's narrow stage-comparison exception; every
 # request gets a fresh, full-original charge. Neither old row nor ID is removed.
 s=d._reserve(s,config,now,run_id,'VIDEO',proof,source);row=d.pending(s,'VIDEO')
 q['reservations'].append(dict(video_id=source['video']['id'],seconds=source['video']['duration_seconds'],reserved_at=now,reservation_id=row['reservation_id']))
 return s,d.validate_ledger(q,now)

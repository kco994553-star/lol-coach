#!/usr/bin/env python3
"""Trusted phased free Gemini intake. Every request needs a durable reservation.

Artifacts contain paired daily-state.json and unchanged-schema quota-ledger.json.
No Gemini request occurs in pretext/final. Recovery reads Actions artifacts; entitlement
checks read public official documents; text/video each make one provider call.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from coach_v1 import gemini_daily as daily
from coach_v1.expert_collector import (ExpertCollector,atomic_json,policy_from_runtime,validate_ledger,validate_config as channel_config)
from coach_v1.expert_entitlement import verify_free_entitlement
from coach_v1.expert_front_diagnostics import _python_transport
from scripts.collect_expert_claims import read_json,gh_json,recovery as legacy_recovery

UPLOAD_STEPS={'Persist daily TEXT reservation','Persist daily TEXT result','Persist daily VIDEO reservation','Persist daily FINAL state'}

def _id(value):return re.fullmatch('[1-9][0-9]*',str(value or '')) is not None

def _context():
    run=os.environ.get('GITHUB_RUN_ID','');daily.require(_id(run) and os.environ.get('GITHUB_RUN_ATTEMPT')=='1','TRUSTED_FIRST_ATTEMPT_REQUIRED')
    return run

ROOT=Path(__file__).resolve().parents[1]

def claim_root(run):
    # Stable checkout identity; changing phase/output/RUNNER_TEMP cannot replay.
    directory=subprocess.check_output(['git','rev-parse','--absolute-git-dir'],cwd=ROOT,stderr=subprocess.DEVNULL,text=True,timeout=10).strip()
    return Path(directory)/'gemini-daily-dispatch-claims'/str(run)


def verify_ack(artifact_id,phase,state,quota,run_id,*,api=None,download_pair=None):
    api=api or gh_json
    daily.require(_id(artifact_id),'RESERVATION_PERSISTENCE_NOT_CONFIRMED')
    repo=os.environ.get('GITHUB_REPOSITORY')
    daily.require(repo=='kco994553-star/lol-coach','TRUSTED_ACTIONS_CONTEXT_REQUIRED')
    run=api('/repos/'+repo+'/actions/runs/'+str(run_id))
    daily.require(run.get('id')==int(run_id) and run.get('run_attempt')==1 and run.get('status')=='in_progress' and run.get('head_branch')=='main' and run.get('event') in ('workflow_dispatch','schedule') and run.get('path')=='.github/workflows/expert-video-collection.yml','TRUSTED_ACTIONS_CONTEXT_REQUIRED')
    artifact=api('/repos/'+repo+'/actions/artifacts/'+str(artifact_id))
    daily.require(artifact.get('id')==int(artifact_id) and artifact.get('expired') is False and artifact.get('name')=='gemini-daily-state-'+str(run_id)+'-'+phase and artifact.get('workflow_run',{}).get('id')==int(run_id),'RESERVATION_PERSISTENCE_NOT_CONFIRMED')
    if download_pair is None:
        with tempfile.TemporaryDirectory() as temp:
            result=subprocess.run(['gh','run','download',str(run_id),'--name',artifact['name'],'--dir',temp,'--repo',repo],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=60,check=False)
            daily.require(result.returncode==0,'RESERVATION_PERSISTENCE_NOT_CONFIRMED')
            previous,oldquota=read_json(Path(temp)/'daily-state.json',32_000_000),read_json(Path(temp)/'quota-ledger.json',32_000_000)
    else:previous,oldquota=download_pair(artifact)
    daily.require(daily._canonical(previous)==daily._canonical(state) and daily._canonical(oldquota)==daily._canonical(quota),'RESERVATION_PERSISTENCE_NOT_CONFIRMED')
    return True


def recover(directory,config,runtime,now):
    run=_context();repo=os.environ.get('GITHUB_REPOSITORY','')
    daily.require(re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repo) is not None,'TRUSTED_ACTIONS_CONTEXT_REQUIRED')
    runs=[]
    for page in range(1,11):
        data=gh_json('/repos/'+repo+'/actions/workflows/expert-video-collection.yml/runs?per_page=100&page='+str(page))
        daily.require(type(data.get('total_count')) is int and data['total_count']<=1000,'RECOVERY_HISTORY_UNKNOWN')
        batch=data.get('workflow_runs');daily.require(isinstance(batch,list),'RECOVERY_HISTORY_UNKNOWN');runs.extend(batch)
        if len(runs)>=data['total_count']:break
    else:raise ValueError('RECOVERY_HISTORY_UNKNOWN')
    def artifacts(run_id):
        data=gh_json('/repos/'+repo+'/actions/runs/'+str(run_id)+'/artifacts?per_page=100')
        daily.require(type(data.get('total_count')) is int and data['total_count']<=100,'RECOVERY_HISTORY_UNKNOWN')
        return data.get('artifacts')
    def expected(run_id):
        data=gh_json('/repos/'+repo+'/actions/runs/'+str(run_id)+'/jobs?per_page=100')
        jobs=data.get('jobs')
        if not isinstance(jobs,list) or data.get('total_count',101)>100:return None
        if not jobs:
            run_metadata=next((item for item in runs if item.get('id')==run_id),{})
            return False if data.get('total_count')==0 and run_metadata.get('status')=='completed' else None
        rows=[s for job in jobs for s in job.get('steps',[]) if s.get('name') in UPLOAD_STEPS]
        # Old pre-migration workflows have no daily phase and are recovered below.
        if not rows:
            if all(job.get('status')=='completed' for job in jobs):return False
            return None
        states=[row.get('conclusion') for row in rows]
        if 'success' in states:return True
        return False if all(x in ('skipped','failure','cancelled') for x in states) else None
    def download(run_id,item):
        with tempfile.TemporaryDirectory() as temp:
            result=subprocess.run(['gh','run','download',str(run_id),'--name',item['name'],'--dir',temp,'--repo',repo],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=60,check=False)
            daily.require(result.returncode==0,'DAILY_ARTIFACT_UNAVAILABLE')
            return read_json(Path(temp)/'daily-state.json',32_000_000),read_json(Path(temp)/'quota-ledger.json',32_000_000)
    state,quota=daily.recover_pairs(runs,int(run),artifacts,download,expected,now)
    if state is None:
        olddir=directory/'legacy-recovery';receipt=legacy_recovery(olddir)
        daily.require(receipt.get('status')=='FOUND','LEGACY_QUOTA_HISTORY_UNKNOWN')
        quota=validate_ledger(read_json(olddir/'quota-ledger.json',32_000_000),now)
        state=daily.empty_state(runtime['project_name'])
    daily.require(state['project_name']==runtime['project_name'],'PROJECT_STATE_MISMATCH')
    return state,quota

def source_allowed(source,config):
    # Both purposes have their own frozen channel allowlist; a POV source cannot
    # be supplied from the expert list by changing a prompt or URL alone.
    path=config['expert_channels'] if source['purpose']=='EXPERT_STATEMENT' else config['pov_channels']
    raw=read_json(path,200000)
    if source['purpose']=='EXPERT_STATEMENT':
        c=channel_config(raw)
        return any(row['channel_id']==source['video']['channel_id'] and row['enabled'] for row in c['channels'])
    daily.require(isinstance(raw,dict) and raw.get('format')=='lol-coach-pov-channels-v1' and raw.get('category')=='POV','INVALID_POV_ALLOWLIST')
    rows=raw.get('channels');daily.require(isinstance(rows,list) and 1<=len(rows)<=20,'INVALID_POV_ALLOWLIST')
    ids=[]
    for row in rows:
        daily.require(isinstance(row,dict) and re.fullmatch(r'UC[A-Za-z0-9_-]{22}',str(row.get('channel_id',''))) is not None,'INVALID_POV_ALLOWLIST')
        daily.require(row.get('verification_status') in ('USER_PROVIDED_PENDING_VERIFICATION','VERIFIED_PUBLIC_METADATA'),'INVALID_POV_ALLOWLIST')
        ids.append(row['channel_id'])
    daily.require(len(ids)==len(set(ids)),'INVALID_POV_ALLOWLIST')
    return source['video']['channel_id'] in ids

def verify_source_metadata(source,collector):
    video=source['video']
    data=collector._youtube('videos',part='snippet,contentDetails,status',id=video['id'])
    rows=data.get('items');daily.require(isinstance(rows,list) and len(rows)==1,'PUBLIC_SOURCE_METADATA_REQUIRED')
    row=rows[0];daily.require(row.get('id')==video['id'],'PUBLIC_SOURCE_METADATA_REQUIRED')
    status=row.get('status',{});snippet=row.get('snippet',{})
    daily.require(status.get('privacyStatus')=='public' and status.get('uploadStatus')=='processed' and snippet.get('liveBroadcastContent','none')=='none','PUBLIC_SOURCE_METADATA_REQUIRED')
    daily.require(snippet.get('channelId')==video['channel_id'],'PUBLIC_SOURCE_METADATA_REQUIRED')
    match=re.fullmatch(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?',row.get('contentDetails',{}).get('duration',''))
    daily.require(match is not None,'PUBLIC_SOURCE_METADATA_REQUIRED')
    seconds=sum(int(x or 0)*scale for x,scale in zip(match.groups(),(3600,60,1)))
    daily.require(seconds==video['duration_seconds'],'PUBLIC_SOURCE_METADATA_REQUIRED')


def _gate(runtime,now,verifier,transport=None):
    proof=daily.validate_entitlement_proof(verifier(model=daily.MODEL),daily.MODEL)
    policy=policy_from_runtime(runtime,os.environ,now=now,entitlement_proof=proof,model=daily.MODEL)
    collector=ExpertCollector(model=daily.MODEL,gemini_api_key=os.environ.get('GEMINI_API_KEY'),youtube_api_key=os.environ.get('YOUTUBE_API_KEY'),policy=policy,clock=lambda:now,transport=transport)
    collector._gate()
    daily.require(proof['checked_at']==daily.datetime.fromtimestamp(now,daily.timezone.utc).date().isoformat(),'FREE_PROOF_NOT_FRESH')
    return proof,collector

def _write(directory,state,quota,receipt):
    if state is not None:atomic_json(directory/'daily-state.json',state)
    if quota is not None:atomic_json(directory/'quota-ledger.json',quota)
    atomic_json(directory/'receipt.json',receipt)
    output=os.environ.get('GITHUB_OUTPUT')
    fields={k:str(receipt[k]).lower() if type(receipt[k]) is bool else str(receipt[k] or '') for k in ('status','reason','text_reserved','text_success','video_reserved','has_state')}
    if output:
        with open(output,'a') as stream:
            for k,v in fields.items():stream.write(k+'='+v+'\n')
    print('GEMINI_DAILY_JSON='+json.dumps(receipt,sort_keys=True),flush=True)

def main(argv=None,*,entitlement_verifier=None,transport=None,clock=None,ack_verifier=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',choices=('recover','pretext','text','preparevideo','video','final'),required=True)
    parser.add_argument('--config',default='config/evidence_intake.json')
    parser.add_argument('--runtime-config',default='config/expert_runtime.json')
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--state');parser.add_argument('--ledger');parser.add_argument('--recovery-receipt')
    parser.add_argument('--reservation-artifact-id');parser.add_argument('--text-result-artifact-id');parser.add_argument('--source-plan')
    args=parser.parse_args(argv);directory=args.output_dir;state=None;quota=None;config=None;collector=None
    now=int((clock or time.time)());verifier=entitlement_verifier or verify_free_entitlement
    receipt=dict(schema_version='gemini.daily-receipt.v1',phase=args.phase,status='BLOCKED_EXTERNAL',reason=None,text_reserved=False,text_success=False,video_reserved=False,has_state=False,new_provider_requests=0,accepted_claims=0,coaching_accuracy=None,http_status=None,classification=None,provider_error_code=None,provider_error_status=None,provider_error_message=None,valid_extraction=False,review_status='NOT_REVIEWED')
    try:
        run=_context();config=daily.validate_config(read_json(args.config,200000));runtime=read_json(args.runtime_config,200000)
        if args.phase=='video':(directory/'extraction.json').unlink(missing_ok=True)
        if args.phase=='recover':
            state,quota=recover(directory,config,runtime,now)
            atomic_json(directory/'recovery.json',dict(status='FOUND',schema_version='gemini.daily-recovery.v1'))
        else:
            daily.require(args.state is not None and args.ledger is not None,'STATE_PAIR_REQUIRED')
            state,quota=daily.validate_pair(read_json(args.state,32_000_000),read_json(args.ledger,32_000_000),now)
            daily.require(state['project_name']==runtime['project_name'],'PROJECT_STATE_MISMATCH')
            if args.phase=='pretext':
                recovery=read_json(args.recovery_receipt) if args.recovery_receipt else {}
                daily.require(recovery.get('status')=='FOUND','RECOVERY_REQUIRED')
                proof,_=_gate(runtime,now,verifier,transport)
                state=daily.reserve_text(state,quota,config,now,run,proof);receipt['text_reserved']=True
            elif args.phase in ('text','video'):
                stage=args.phase.upper();row=daily.pending(state,stage)
                daily.require(row['configuration_fingerprint']==daily.fingerprint(config) and row['purpose']==config['purpose'],'CONFIGURATION_CHANGED_AFTER_RESERVATION')
                _gate(runtime,now,verifier,transport)
                if stage=='VIDEO':
                    source=daily.validate_source(row['source'],config);daily.require(source_allowed(source,config),'SOURCE_CHANNEL_NOT_ALLOWLISTED')
                    charges=[r for r in quota['reservations'] if r['reservation_id']==row['reservation_id']]
                    daily.require(len(charges)==1 and charges[0]['video_id']==source['video']['id'] and charges[0]['seconds']==source['video']['duration_seconds'],'VIDEO_CHARGE_REQUIRED')
                (ack_verifier or verify_ack)(args.reservation_artifact_id,stage,state,quota,run)
                dispatch_claim=claim_root(run)
                state=daily.dispatch(state,stage,now,run,args.reservation_artifact_id,dispatch_claim,os.environ.get('GEMINI_API_KEY'),transport or _python_transport)
                receipt['new_provider_requests']=1
                result=state['events'][-1];receipt['reason']=result['classification'];receipt['accepted_claims']=result['safe_output'].get('accepted_claims',0)
                receipt['http_status']=result['http_status'];receipt['classification']=result['classification']
                receipt['request_http_success']=result['http_status']==200;receipt['response_shape']=result['safe_output'].get('response_shape')
                error=result['safe_output'].get('provider_error',{})
                for name in ('code','status','message'):receipt['provider_error_'+name]=error.get('error_'+name)
                if stage=='VIDEO' and result['classification']=='VIDEO_SUCCESS_UNREVIEWED':
                    extraction=dict(schema_version='gemini.extraction.v1',purpose=row['purpose'],source=row['source'],**result['safe_output'])
                    atomic_json(directory/'extraction.json',extraction)
                    receipt['valid_extraction']=result['safe_output'].get('valid_extraction') is True;receipt['extraction_status']=result['safe_output'].get('extraction_status');receipt['review_status']=result['safe_output']['evidence_status']
                receipt['text_success']=stage=='TEXT' and result['classification']=='TEXT_ONLY_SUCCESS'
                if result['classification'] not in ('TEXT_ONLY_SUCCESS','VIDEO_SUCCESS_UNREVIEWED'):receipt['status']='BLOCKED_EXTERNAL'
                else:receipt['status']='SUCCESS'
            elif args.phase=='preparevideo':
                daily.require(_id(args.text_result_artifact_id),'TEXT_RESULT_PERSISTENCE_REQUIRED')
                (ack_verifier or verify_ack)(args.text_result_artifact_id,'TEXT_RESULT',state,quota,run)
                proof,collector=_gate(runtime,now,verifier,transport)
                texts=[e for e in state['events'] if e['kind']=='RESERVATION' and e['stage']=='TEXT' and e['day']==daily.seoul_day(now)]
                daily.require(len(texts)==1 and any(e['kind']=='RESULT' and e['reservation_id']==texts[0]['reservation_id'] and e['classification']=='TEXT_ONLY_SUCCESS' for e in state['events']),'TEXT_SUCCESS_REQUIRED')
                if args.source_plan:
                    source=daily.validate_source(read_json(args.source_plan),config)
                    daily.require(source_allowed(source,config),'SOURCE_CHANNEL_NOT_ALLOWLISTED')
                    verify_source_metadata(source,collector)
                else:
                    daily.require(config['purpose']=='EXPERT_STATEMENT','EXPLICIT_POV_SOURCE_PLAN_REQUIRED')
                    channels=channel_config(read_json(config['expert_channels'],200000));channels['max_videos_per_run']=1
                    channels['max_duration_seconds']=min(channels['max_duration_seconds'],1200)
                    candidates=collector._discover(channels,quota,now)
                    daily.require(bool(candidates),'NO_ELIGIBLE_VIDEOS')
                    video=candidates[0];source=dict(schema_version='evidence.source-plan.v1',purpose=config['purpose'],video=video,start_seconds=0,end_seconds=min(video['duration_seconds'],config['clip_seconds']))
                daily.require(source_allowed(source,config),'SOURCE_CHANNEL_NOT_ALLOWLISTED')
                state,quota=daily.reserve_video(state,quota,config,source,now,run,proof)
                atomic_json(directory/'source-plan.json',source);receipt['video_reserved']=True
            # final copies the exact newest pair; reservations are never refunded.
        if receipt['status']=='BLOCKED_EXTERNAL' and receipt['reason'] is None:receipt['status']='READY'
        receipt['has_state']=state is not None and quota is not None
        _write(directory,state,quota,receipt);return 0
    except Exception as error:
        known={'DAILY_TEXT_CONSUMED','PERSISTENT_CONFIGURATION_BLOCK','FREE_PROOF_NOT_FRESH','DAILY_VIDEO_CONSUMED','VIDEO_ALREADY_CHARGED','ROLLING_VIDEO_BUDGET_EXHAUSTED','NO_ELIGIBLE_VIDEOS','TEXT_SUCCESS_REQUIRED','SOURCE_CHANNEL_NOT_ALLOWLISTED','RESERVATION_PERSISTENCE_NOT_CONFIRMED','DISPATCH_ALREADY_COMPLETED','TEXT_RESULT_PERSISTENCE_REQUIRED','RECOVERY_REQUIRED','TRUSTED_FIRST_ATTEMPT_REQUIRED','MISSING_DURABLE_DAILY_STATE','EXPIRED_DURABLE_DAILY_STATE','LEGACY_QUOTA_HISTORY_UNKNOWN'}
        receipt['reason']=str(error) if isinstance(error,ValueError) and str(error) in known else 'INVALID_OR_UNAVAILABLE_DAILY_STATE'
        receipt['has_state']=state is not None and quota is not None
        # Preserve configuration failures occurring before a provider reservation.
        status=getattr(error,'http_status',None)
        diagnostic=(collector.diagnostics[-1] if collector is not None and collector.diagnostics else {})
        reason=None
        if status is None and getattr(error,'reason',None)=='MISSING_API_KEYS':reason='AUTHENTICATION'
        configuration_errors={'PUBLIC_SOURCE_METADATA_REQUIRED','SOURCE_CHANNEL_NOT_ALLOWLISTED','INVALID_POV_ALLOWLIST','INVALID_SOURCE_PLAN','INVALID_SOURCE_PURPOSE','INVALID_SOURCE_BOUNDS'}
        if str(error) in configuration_errors:reason='ARGUMENT_CONFIGURATION'
        if state is not None and config is not None and args.phase in ('pretext','preparevideo','text','video') and (status is not None or reason):
            stage='TEXT_GATE' if args.phase=='pretext' else 'VIDEO_METADATA' if args.phase=='preparevideo' else 'VIDEO_GATE'
            safe={k:diagnostic.get(k) for k in ('error_code','error_status','error_message')}
            state=daily.preparation_failure(state,config,now,run,stage,status,reason,safe)
            receipt['http_status']=status;receipt['classification']=daily.classify(status,'TEXT',reason);receipt['reason']=receipt['classification']
            for name in ('code','status','message'):receipt['provider_error_'+name]=safe.get('error_'+name)
        if args.phase=='recover':atomic_json(directory/'recovery.json',dict(status='UNKNOWN',reason=receipt['reason']))
        _write(directory,state,quota,receipt);return 1

if __name__=='__main__':raise SystemExit(main())

#!/usr/bin/env python3
"""Trusted Actions two-phase entry point; prints fixed public-safe receipts only.

reserve -> upload reservation-state successfully -> process with artifact ID.
No publication or GitHub repository mutation is performed. Recovery reads all
run conclusions. Credentials are environment-only headers, never CLI arguments.
"""
import argparse
import inspect
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from coach_v1.expert_collector import (ExpertCollector,atomic_json,recover_ledger_snapshot,
    policy_from_runtime,validate_entitlement_proof,write_public_result,_json,MODEL,ALLOWED_MODELS,COLLECTION_MODES,PLAN_STATUSES,SAFE_REASONS)


def read_json(path,maximum=2000000):
    path=Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size>maximum:raise ValueError('invalid public state file')
    return _json(path.read_bytes())


def gh_json(path):
    result=subprocess.run(['gh','api',path],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=60,check=False)
    if result.returncode or len(result.stdout)>2000000:raise ValueError('Actions recovery unavailable')
    return _json(result.stdout)


def recovery(directory):
    repository=os.environ.get('GITHUB_REPOSITORY','');run=os.environ.get('GITHUB_RUN_ID','')
    if re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repository) is None or not run.isdigit():raise ValueError('trusted Actions context required')
    data=gh_json('/repos/'+repository+'/actions/workflows/expert-video-collection.yml/runs?per_page=100')
    runs=data.get('workflow_runs')
    def artifacts(run_id):
        data=gh_json('/repos/'+repository+'/actions/runs/'+str(run_id)+'/artifacts?per_page=100')
        if data.get('total_count',101)>100:raise ValueError('bounded recovery exceeded')
        return data.get('artifacts')
    def download(run_id,artifact):
        with tempfile.TemporaryDirectory() as temporary:
            result=subprocess.run(['gh','run','download',str(run_id),'--name',artifact['name'],'--dir',temporary,'--repo',repository],
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=60,check=False)
            if result.returncode:raise ValueError('state download unavailable')
            return read_json(Path(temporary)/'quota-ledger.json')
    def expected(run_id):
        data=gh_json('/repos/'+repository+'/actions/runs/'+str(run_id)+'/jobs?per_page=100')
        jobs=data.get('jobs')
        if not isinstance(jobs,list) or data.get('total_count',101)>100:return None
        if not jobs:return False
        states=[step.get('conclusion') for job in jobs for step in job.get('steps',[])
                if step.get('name') in ('Persist quota before any Gemini request',
                    'Persist clipping diagnostic quota','Persist format diagnostic quota')]
        if 'success' in states:return True
        if states and all(state in ('skipped','failure','cancelled') for state in states):return False
        return None
    ledger,receipt=recover_ledger_snapshot(runs,current_run_id=int(run),list_artifacts=artifacts,download_artifact=download,
        reservation_expected=expected,now=int(time.time()))
    if ledger is not None:atomic_json(directory/'quota-ledger.json',ledger)
    atomic_json(directory/'recovery.json',receipt)
    return receipt


def safe_probe_receipt(plan):
    """Retain typed metadata only, even when a supplied plan is malformed."""
    if not isinstance(plan,dict) or plan.get('schema_version')!='expert.reservation-plan.v4':return None
    probe=plan.get('text_probe')
    fields={'schema_version','status','reason','model','checked_at','http_status','input_kind','video_inputs','api_route','attempt_count','retry_count'}
    if not isinstance(probe,dict) or set(probe)!=fields:return None
    if probe['schema_version']!='expert.text-probe.v2' or probe['model'] not in ALLOWED_MODELS or probe['input_kind']!='TEXT_ONLY':return None
    if not isinstance(probe['status'],str) or probe['status'] not in set(PLAN_STATUSES)|{'READY'}:return None
    if probe['reason'] is not None and (not isinstance(probe['reason'],str) or probe['reason'] not in SAFE_REASONS):return None
    if type(probe['video_inputs']) is not int or probe['video_inputs']!=0 or (type(probe['checked_at']) is not int or probe['checked_at']<0):return None
    if probe['http_status'] is not None and (type(probe['http_status']) is not int or not 100<=probe['http_status']<=599):return None
    if probe['api_route']!='GENERATE_CONTENT':return None
    attempts=probe['attempt_count'];retries=probe['retry_count']
    if type(attempts) is not int or not 0<=attempts<=4 or type(retries) is not int or not 0<=retries<=3:return None
    if attempts and attempts!=retries+1 or not attempts and retries:return None
    if probe['status']=='READY' and (not attempts or probe['http_status']!=200 or probe['reason'] is not None):return None
    return dict(probe)


def main(argv=None,*,entitlement_verifier=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--phase',choices=('recover','reserve','process','probe-format'),required=True)
    parser.add_argument('--config',default='config/expert_channels.json')
    parser.add_argument('--runtime-config')
    parser.add_argument('--output-dir',required=True)
    parser.add_argument('--ledger');parser.add_argument('--recovery-receipt');parser.add_argument('--plan')
    parser.add_argument('--front-diagnostics')
    parser.add_argument('--reservation-artifact-id')
    parser.add_argument('--collection-mode',choices=COLLECTION_MODES,default='DIAGNOSTIC_FIRST_CLIP')
    args=parser.parse_args(argv);directory=Path(args.output_dir);collector=None;plan=None;model=MODEL
    def emit_diagnostic(event):
        print('EXPERT_PROVIDER_DIAGNOSTIC_JSON='+json.dumps(event,sort_keys=True),flush=True)
    def retain_diagnostics(failure=False,probe=None):
        events=list(collector.diagnostics) if collector is not None else []
        if failure:
            event=dict(provider='GEMINI',phase='TEXT_PROBE' if args.phase in ('reserve','probe-format') else 'VIDEO_CLIP',
                http_status=None,error_status=None,error_code=None,error_message=None,reason='INVALID_OR_UNAVAILABLE_PUBLIC_STATE')
            events.append(event);emit_diagnostic(event)
        receipt=dict(schema_version='expert.diagnostics.v2',phase=args.phase,api_route='GENERATE_CONTENT',model=model,
            total_request_count=collector.request_count if collector is not None else 0,
            request_counts=dict(collector.request_counts) if collector is not None else dict(TEXT_PROBE=0,VIDEO_CLIP=0,METADATA=0),
            events=events,text_probe=None)
        receipt['text_probe']=safe_probe_receipt(dict(schema_version='expert.reservation-plan.v4',text_probe=probe) if probe is not None else plan) if not failure else None
        atomic_json(directory/'diagnostics.json',receipt)
    try:
        if args.phase=='recover':
            receipt=recovery(directory)
            print('EXPERT_RECOVERY_JSON='+json.dumps(receipt,sort_keys=True));return 0
        runtime=read_json(args.runtime_config,200000) if args.runtime_config else None
        front=None
        if args.front_diagnostics:
            if args.phase!='reserve':raise ValueError('front receipt only accepted at reserve')
            from coach_v1.expert_front_diagnostics import validate_front_receipt
            front=validate_front_receipt(read_json(args.front_diagnostics),now=int(time.time()))
            model=front['selected_model'] or MODEL
        if args.phase=='process' and args.plan:
            plan=read_json(args.plan)
            model=plan.get('text_probe',{}).get('model',MODEL) if isinstance(plan.get('text_probe'),dict) else MODEL
            if model not in ALLOWED_MODELS:raise ValueError('model not pinned')
        if entitlement_verifier is None:
            from coach_v1.expert_entitlement import verify_free_entitlement
            entitlement_verifier=verify_free_entitlement
        # Old test-injected verifier remains compatible for the primary only.
        if 'model' in inspect.signature(entitlement_verifier).parameters:
            verified=entitlement_verifier(model=model)
        else:
            if model!=MODEL:raise ValueError('model-specific verifier required')
            verified=entitlement_verifier()
        proof=validate_entitlement_proof(verified,model)
        atomic_json(directory/'entitlement.json',proof)
        policy=policy_from_runtime(runtime,os.environ,now=int(time.time()),entitlement_proof=proof,model=model)
        collector=ExpertCollector(model=model,youtube_api_key=os.environ.get('YOUTUBE_API_KEY'),gemini_api_key=os.environ.get('GEMINI_API_KEY'),policy=policy,on_diagnostic=emit_diagnostic)
        if args.phase=='probe-format':
            probe=collector.probe_text(structured=True)
            retain_diagnostics(probe=probe)
            receipt=dict(schema_version='expert.format-probe.v2',profile='TEXT_ONLY_CLAIM_SCHEMA',
                api_route='GENERATE_CONTENT',text_probe=probe,request_count=collector.request_count,
                video_requests=0,new_video_reservations=0,coaching_accuracy=None)
            atomic_json(directory/'format-probe.json',receipt)
            print('EXPERT_FORMAT_PROBE_JSON='+json.dumps(receipt,sort_keys=True));return 0
        if args.phase=='reserve':
            receipt=read_json(args.recovery_receipt) if args.recovery_receipt else {'status':'ABSENT'}
            history=receipt.get('status');ledger=read_json(args.ledger) if args.ledger and Path(args.ledger).exists() else None
            plan=collector.prepare(read_json(args.config,200000),ledger,ledger_history=history,collection_mode=args.collection_mode,front_diagnostics=front)
            retain_diagnostics()
            atomic_json(directory/'plan.json',plan)
            if plan['ledger'] is not None:atomic_json(directory/'quota-ledger.json',plan['ledger'])
            safe=dict(status=plan['status'],reason=plan['reason'],request_count=collector.request_count,
                      videos_reserved=len(plan['videos']),publication_status='PUBLICATION_DEFERRED',coaching_accuracy=None)
            atomic_json(directory/'receipt.json',safe)
            print('EXPERT_RESERVATION_JSON='+json.dumps(safe,sort_keys=True));return 0
        if not args.plan:raise ValueError('plan required')
        persisted=isinstance(args.reservation_artifact_id,str) and re.fullmatch(r'[1-9][0-9]*',args.reservation_artifact_id) is not None
        plan=read_json(args.plan)
        result=collector.process(plan,reservation_persisted=persisted)
        retain_diagnostics()
        write_public_result(directory,result)
        safe={key:result[key] for key in ('status','reason','request_count','publication_status','coaching_accuracy')}
        print('EXPERT_ACQUISITION_JSON='+json.dumps(safe,sort_keys=True));return 0
    except Exception:
        if args.phase=='probe-format':
            # A failed new diagnostic cannot leave an earlier READY/proof visible.
            for name in ('format-probe.json','entitlement.json'):(directory/name).unlink(missing_ok=True)
        # Never echo exception strings, provider bodies, subprocess stderr or keys.
        receipt=dict(status='BLOCKED_EXTERNAL',reason='INVALID_OR_UNAVAILABLE_PUBLIC_STATE',publication_status='PUBLICATION_DEFERRED',coaching_accuracy=None)
        blocked=dict(receipt,artifacts=[],ledger=None,checked_at=int(time.time()),video_results=[],
            request_count=collector.request_count if collector is not None else 0)
        retain_diagnostics(failure=True)
        write_public_result(directory,blocked)
        if args.phase=='recover':atomic_json(directory/'recovery.json',dict(status='UNKNOWN',run_id=None,artifact_id=None,reason='QUOTA_RECOVERY_FAILED'))
        print('EXPERT_ACQUISITION_JSON='+json.dumps(receipt,sort_keys=True));return 1


if __name__=='__main__':raise SystemExit(main())

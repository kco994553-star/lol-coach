#!/usr/bin/env python3
"""Trusted Actions two-phase entry point; prints fixed public-safe receipts only.

reserve -> upload reservation-state successfully -> process with artifact ID.
No publication or GitHub repository mutation is performed. Recovery reads all
run conclusions. Credentials are environment-only headers, never CLI arguments.
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
from coach_v1.expert_collector import (ExpertCollector,atomic_json,recover_ledger_snapshot,
    policy_from_runtime,validate_entitlement_proof,write_public_result,_json)


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
                if step.get('name')=='Persist quota before any Gemini request']
        if 'success' in states:return True
        if states and all(state in ('skipped','failure','cancelled') for state in states):return False
        return None
    ledger,receipt=recover_ledger_snapshot(runs,current_run_id=int(run),list_artifacts=artifacts,download_artifact=download,
        reservation_expected=expected,now=int(time.time()))
    if ledger is not None:atomic_json(directory/'quota-ledger.json',ledger)
    atomic_json(directory/'recovery.json',receipt)
    return receipt


def main(argv=None,*,entitlement_verifier=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--phase',choices=('recover','reserve','process'),required=True)
    parser.add_argument('--config',default='config/expert_channels.json')
    parser.add_argument('--runtime-config')
    parser.add_argument('--output-dir',required=True)
    parser.add_argument('--ledger');parser.add_argument('--recovery-receipt');parser.add_argument('--plan')
    parser.add_argument('--reservation-artifact-id')
    args=parser.parse_args(argv);directory=Path(args.output_dir)
    try:
        if args.phase=='recover':
            receipt=recovery(directory)
            print('EXPERT_RECOVERY_JSON='+json.dumps(receipt,sort_keys=True));return 0
        runtime=read_json(args.runtime_config,200000) if args.runtime_config else None
        if entitlement_verifier is None:
            from coach_v1.expert_entitlement import verify_free_entitlement
            entitlement_verifier=verify_free_entitlement
        proof=validate_entitlement_proof(entitlement_verifier())
        atomic_json(directory/'entitlement.json',proof)
        policy=policy_from_runtime(runtime,os.environ,now=int(time.time()),entitlement_proof=proof)
        collector=ExpertCollector(youtube_api_key=os.environ.get('YOUTUBE_API_KEY'),gemini_api_key=os.environ.get('GEMINI_API_KEY'),policy=policy)
        if args.phase=='reserve':
            receipt=read_json(args.recovery_receipt) if args.recovery_receipt else {'status':'ABSENT'}
            history=receipt.get('status');ledger=read_json(args.ledger) if args.ledger and Path(args.ledger).exists() else None
            plan=collector.prepare(read_json(args.config,200000),ledger,ledger_history=history)
            atomic_json(directory/'plan.json',plan)
            if plan['ledger'] is not None:atomic_json(directory/'quota-ledger.json',plan['ledger'])
            safe=dict(status=plan['status'],reason=plan['reason'],request_count=collector.request_count,
                      videos_reserved=len(plan['videos']),publication_status='PUBLICATION_DEFERRED',coaching_accuracy=None)
            atomic_json(directory/'receipt.json',safe)
            print('EXPERT_RESERVATION_JSON='+json.dumps(safe,sort_keys=True));return 0
        if not args.plan:raise ValueError('plan required')
        persisted=isinstance(args.reservation_artifact_id,str) and re.fullmatch(r'[1-9][0-9]*',args.reservation_artifact_id) is not None
        result=collector.process(read_json(args.plan),reservation_persisted=persisted)
        write_public_result(directory,result)
        safe={key:result[key] for key in ('status','reason','request_count','publication_status','coaching_accuracy')}
        print('EXPERT_ACQUISITION_JSON='+json.dumps(safe,sort_keys=True));return 0
    except Exception:
        # Never echo exception strings, provider bodies, subprocess stderr or keys.
        receipt=dict(status='BLOCKED_EXTERNAL',reason='INVALID_OR_UNAVAILABLE_PUBLIC_STATE',publication_status='PUBLICATION_DEFERRED',coaching_accuracy=None)
        atomic_json(directory/'receipt.json',receipt)
        if args.phase=='recover':atomic_json(directory/'recovery.json',dict(status='UNKNOWN',run_id=None,artifact_id=None,reason='QUOTA_RECOVERY_FAILED'))
        print('EXPERT_ACQUISITION_JSON='+json.dumps(receipt,sort_keys=True));return 1


if __name__=='__main__':raise SystemExit(main())

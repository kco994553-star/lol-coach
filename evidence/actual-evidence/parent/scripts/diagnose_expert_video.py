#!/usr/bin/env python3
"""Trusted metadata-only discovery and durable prepare/process video stages."""
import argparse
import json
import os
from pathlib import Path
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from coach_v1.expert_collector import atomic_json,policy_from_runtime,validate_ledger
from coach_v1.expert_entitlement import verify_free_entitlement
from coach_v1.expert_video_diagnostic import (AUTHORIZATION,MODEL,STAGES,ExpertVideoDiagnostic,
    validate_stage_result,validate_complete_error)
from scripts.collect_expert_claims import read_json


def _claim(directory,plan):
    directory.mkdir(parents=True,exist_ok=True)
    path=directory/'dispatch-claim.json'
    descriptor=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(descriptor,'w') as output:
        json.dump(dict(schema_version='expert.video-dispatch-claim.v1',reservation_id=plan['reservation_id'],
            stage=plan['stage'],session_id=plan['session_id']),output,sort_keys=True)
        output.flush();os.fsync(output.fileno())


def main(argv=None,*,entitlement_verifier=None,clock=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',choices=('discover','prepare','process'),required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--runtime-config',default='config/expert_runtime.json')
    parser.add_argument('--config',default='config/expert_channels.json')
    parser.add_argument('--ledger');parser.add_argument('--prior-error');parser.add_argument('--video')
    parser.add_argument('--previous-result');parser.add_argument('--plan')
    parser.add_argument('--stage',choices=STAGES)
    parser.add_argument('--authorization');parser.add_argument('--reservation-artifact-id')
    args=parser.parse_args(argv);directory=args.output_dir;now=clock or time.time
    valid_ledger=None
    try:
        if args.authorization!=AUTHORIZATION:raise ValueError('explicit diagnostic authority required')
        runtime=read_json(args.runtime_config,200000)
        proof=(entitlement_verifier or verify_free_entitlement)(model=MODEL)
        atomic_json(directory/'entitlement.json',proof)
        policy=policy_from_runtime(runtime,os.environ,now=int(now()),entitlement_proof=proof,model=MODEL)
        run=os.environ.get('GITHUB_RUN_ID','')
        diagnostic=ExpertVideoDiagnostic(gemini_api_key=os.environ.get('GEMINI_API_KEY'),youtube_api_key=os.environ.get('YOUTUBE_API_KEY'),
            policy=policy,entitlement_proof=proof,clock=now,source_run_id=int(run) if run.isdigit() and int(run)>0 else None,
            claim_dispatch=lambda plan:_claim(directory,plan))
        if args.phase=='process':
            plan=read_json(args.plan,32_000_000)
            valid_ledger=validate_ledger(plan['ledger'],int(now()))
            if (directory/'dispatch-claim.json').is_file() and (directory/'result.json').is_file():
                # Idempotent local read, not another call or overwritten history.
                result=validate_stage_result(read_json(directory/'result.json',32_000_000))
                if result['stage_receipts'][-1]['reservation_id']!=plan['reservation_id']:raise ValueError('different dispatch claim')
                print('EXPERT_VIDEO_DIAGNOSTIC_JSON='+json.dumps(dict(status=result['status'],stage=result['stage'],reason=result['reason'],
                    request_count=result['request_count'],new_requests=0,reused_saved_result=True),sort_keys=True))
                return 0
            result=diagnostic.process_stage(plan,reservation_artifact_id=args.reservation_artifact_id)
            if result['error'] is not None:atomic_json(directory/'complete-error.json',result['error'])
            atomic_json(directory/'result.json',result)
            atomic_json(directory/'quota-ledger.json',result['ledger'])
            safe={k:result[k] for k in ('status','reason','stage','request_count','localized_change','exact_invalid_field',
                'manual_summary_default','automatic_collection_paused','accepted_claims','coaching_accuracy')}
            safe['message_complete']=result['error']['message_complete'] if result['error'] else None
        else:
            valid_ledger=validate_ledger(read_json(args.ledger),int(now()))
            prior=validate_complete_error(read_json(args.prior_error,32_000_000),prior=True)
            if args.phase=='discover':
                selected=diagnostic.discover(read_json(args.config,200000),valid_ledger,prior)
                atomic_json(directory/'selected-video.json',selected);safe=dict(selected)
            else:
                selected=read_json(args.video)
                v=selected.get('video') if isinstance(selected,dict) and 'video' in selected else selected
                previous=read_json(args.previous_result,32_000_000) if args.previous_result else None
                plan=diagnostic.prepare_stage(v,valid_ledger,prior,previous_result=previous,stage=args.stage,authorization=args.authorization)
                atomic_json(directory/'plan.json',plan);atomic_json(directory/'quota-ledger.json',plan['ledger'])
                safe={k:plan[k] for k in ('status','reason','stage','reservation_id','session_id')}
                output=os.environ.get('GITHUB_OUTPUT')
                if output:
                    with open(output,'a') as stream:stream.write('reserved='+str(plan['status']=='RESERVED').lower()+'\n')
        atomic_json(directory/'receipt.json',safe)
        print('EXPERT_VIDEO_DIAGNOSTIC_JSON='+json.dumps(safe,sort_keys=True));return 0
    except Exception:
        # Neither exception text nor raw provider output is emitted. No refund.
        safe=dict(status='BLOCKED_EXTERNAL',reason='INVALID_OR_UNAVAILABLE_DIAGNOSTIC_STATE',
            manual_summary_default=True,automatic_collection_paused=True)
        if valid_ledger is not None:atomic_json(directory/'quota-ledger.json',valid_ledger)
        atomic_json(directory/'receipt.json',safe)
        print('EXPERT_VIDEO_DIAGNOSTIC_JSON='+json.dumps(safe,sort_keys=True));return 1


if __name__=='__main__':raise SystemExit(main())

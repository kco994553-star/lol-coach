#!/usr/bin/env python3
"""Trusted same-job paired text diagnostic; no raw output or video requests."""
import argparse
import json
import os
from pathlib import Path
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from coach_v1.expert_collector import atomic_json, policy_from_runtime
from coach_v1.expert_front_diagnostics import run_front_diagnostics
from scripts.collect_expert_claims import read_json


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--runtime-config')
    parser.add_argument('--recovery-receipt',required=True)
    parser.add_argument('--ledger')
    parser.add_argument('--timeout',type=int,default=120)
    parser.add_argument('--allow-fallback-once',action='store_true')
    args=parser.parse_args(argv)
    atomic_json(args.output,dict(status='BLOCKED_EXTERNAL',reason='DAILY_GUARD_REQUIRED'))
    print('EXPERT_DAILY_GUARD_REQUIRED');return 1

    if not 1<=args.timeout<=120:parser.error('timeout must be between1 and120 seconds')
    runtime=read_json(args.runtime_config,200000) if args.runtime_config else None
    recovery=read_json(args.recovery_receipt)
    history=recovery.get('status','UNKNOWN')
    ledger=read_json(args.ledger) if args.ledger and Path(args.ledger).exists() else None
    receipt=run_front_diagnostics(youtube_api_key=os.environ.get('YOUTUBE_API_KEY'),gemini_api_key=os.environ.get('GEMINI_API_KEY'),
        policy_factory=lambda proof:policy_from_runtime(runtime,os.environ,now=int(time.time()),entitlement_proof=proof,model=proof['model']),
        ledger_history=history,ledger=ledger,timeout=args.timeout,allow_fallback_once=args.allow_fallback_once)
    atomic_json(args.output,receipt)
    print('EXPERT_FRONT_RECEIPT_JSON='+json.dumps(receipt,sort_keys=True),flush=True)
    return 0


if __name__=='__main__':raise SystemExit(main())

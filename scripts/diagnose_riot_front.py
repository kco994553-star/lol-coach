#!/usr/bin/env python3
"""Trusted paired diagnostic. Env key only; persists validated safe metadata."""
import argparse
import json
import os
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from coach_v1.riot_front_diagnostics import diagnose_riot_front,validate_front_receipt


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--timeout',type=int,default=20)
    args=parser.parse_args(argv)
    if not 1<=args.timeout<=60:parser.error('timeout must be between1 and60 seconds')
    receipt=validate_front_receipt(diagnose_riot_front(timeout=args.timeout))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    temporary=args.output.with_name(args.output.name+'.tmp')
    temporary.write_text(json.dumps(receipt,ensure_ascii=False,allow_nan=False,sort_keys=True,indent=2)+'\n')
    os.replace(temporary,args.output)
    print('RIOT_FRONT_RECEIPT_JSON='+json.dumps(receipt,ensure_ascii=False,sort_keys=True),flush=True)
    return 0


if __name__=='__main__':sys.exit(main())

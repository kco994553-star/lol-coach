#!/usr/bin/env python3
"""Local private pro reference collection; no Actions raw output or inferred tier."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from coach_v1.pro_reference import ProReferenceCollector,prepare_pro_reference,validate_pro_roster
from coach_v1.pro_reference_cases import export_public_reference,build_reference_cases,validate_public_directory
from coach_v1.state import digest


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',default='config/pro_reference_players.json')
    p.add_argument('--private-directory',default='private/pro-reference')
    p.add_argument('--public-output-directory',help='anonymous reference-cases.json and safe receipt only; must be disjoint from private cache')
    p.add_argument('--prepare-only',action='store_true',help='no-network roster and collection preparation')
    p.add_argument('--position-share-threshold',type=float,default=.5,help='operational replacement threshold; not tactical accuracy')
    p.add_argument('--matches-per-account',type=int,default=3,help='bounded per-account recent sample; default fits all25 healthy main players in request budget')
    p.add_argument('--max-requests',type=int,default=250)
    p.add_argument('--max-matches',type=int,default=100)
    p.add_argument('--deadline-seconds',type=int,default=300)
    args=p.parse_args(argv)
    try:
        path=Path(args.config)
        if not path.is_file() or path.stat().st_size>200000:raise ValueError('INVALID_ROSTER_CONFIG')
        config=validate_pro_roster(json.loads(path.read_text(encoding='utf-8')))
        if args.public_output_directory:
            validate_public_directory(args.public_output_directory,args.private_directory)
            initial=dict(status='BLOCKED_EXTERNAL',reason='COLLECTION_NOT_STARTED',roster_sha256=digest(config),selections=[])
            export_public_reference(args.public_output_directory,args.private_directory,initial,build_reference_cases([],roster_sha256=digest(config),retrieved_at='UNKNOWN'))
        if args.prepare_only:result=prepare_pro_reference(config)
        else:
            collector=ProReferenceCollector(max_requests=args.max_requests,max_matches=args.max_matches,max_retries=0,deadline_seconds=args.deadline_seconds)
            result=collector.collect(config,args.private_directory,position_share_threshold=args.position_share_threshold,matches_per_account=args.matches_per_account)
            if args.public_output_directory:
                result=export_public_reference(args.public_output_directory,args.private_directory,result,collector.reference_cases_data)
        print(json.dumps(result,ensure_ascii=False,allow_nan=False));return 0 if args.prepare_only or result['status'] in ('READY','INSUFFICIENT_DATA') else 2
    except (ValueError,OSError,TypeError,json.JSONDecodeError):
        print(json.dumps(dict(status='BLOCKED_EXTERNAL',reason='INVALID_LOCAL_CONFIG_OR_PRIVATE_STORAGE',privacy='LOCAL_PRIVATE')));return 2

if __name__=='__main__':raise SystemExit(main())

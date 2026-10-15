#!/usr/bin/env python3
"""Extract recall evidence offline by default; fresh Challenger calls are explicit.

PRO_REFERENCE reads only recovered original private Match-V5 envelopes. It never
resolves an account or calls a provider. CHALLENGER requires --patch (the trusted
workflow resolves current official Data Dragon metadata) and an environment key.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from coach_v1.recall_collection import (POPULATIONS,MAX_COLLECTION_LIMITS,RecallCollector,
                                        reuse_private_cache,export_recall)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--population',choices=POPULATIONS,default='PRO_REFERENCE')
    p.add_argument('--private-directory',required=True,help='recovered decrypted pro-cache root; never published')
    p.add_argument('--output-directory',required=True,help='disjoint public directory: recall-data.json and collection-receipt.json only')
    p.add_argument('--patch',help='exact current official major.minor patch; required for fresh CHALLENGER only')
    p.add_argument('--lookback-days',type=int,default=7,help='bounded fresh Challenger match-ID window (1..30)')
    for name,default in MAX_COLLECTION_LIMITS.items():
        p.add_argument('--'+name.replace('_','-'),type=int,default=default,
                       help='hard maximum '+str(default)+'; existing Riot auth/rate safeguards apply')
    args=p.parse_args(argv)
    # Reuse the existing privacy path boundary before any provider call.
    from coach_v1.pro_reference_cases import validate_public_directory
    try:
        public=validate_public_directory(args.output_directory,args.private_directory)
        # A failed run must not leave stale success outputs in a reused directory.
        for name in ('recall-data.json','collection-receipt.json'):
            path=public/name
            if path.is_symlink():raise ValueError('UNSAFE_RECALL_OUTPUT')
            path.unlink(missing_ok=True)
        if not 1<=args.lookback_days<=30:raise ValueError('INVALID_RECALL_WINDOW')
        if args.population=='PRO_REFERENCE':
            observations,receipt=reuse_private_cache(args.private_directory)
        else:
            now=int(datetime.now(timezone.utc).timestamp())
            collector=RecallCollector(**{name:getattr(args,name) for name in MAX_COLLECTION_LIMITS})
            observations,receipt=collector.collect_recall(patch=args.patch,
                start_time=now-args.lookback_days*86400,end_time=now)
        safe=export_recall(public,args.private_directory,observations,receipt)
        print(json.dumps(safe,allow_nan=False,sort_keys=True))
        return 2 if safe['status']=='BLOCKED_EXTERNAL' else 0
    except (ValueError,OSError,KeyError,TypeError,json.JSONDecodeError):
        print(json.dumps(dict(schema_version='recall.collection-receipt.v1',status='BLOCKED_EXTERNAL',
            reason='PRIVATE_CACHE_OR_COLLECTION_OR_ANONYMOUS_VALIDATION_FAILED',
            privacy='NO_RAW_OR_IDENTIFIERS_OUTPUT',coaching_accuracy=None)))
        return 2


if __name__=='__main__':raise SystemExit(main())

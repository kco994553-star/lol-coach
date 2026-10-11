#!/usr/bin/env python3
"""Trusted job entrypoint: env key in, validated anonymous aggregate out."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from coach_v1.power_stats import TIERS, validate_power_dataset
from coach_v1.riot_collector import RiotCollector


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    parser.add_argument('--tier',choices=TIERS,default='GOLD')
    parser.add_argument('--division',choices=('I','II','III','IV'),default='I')
    parser.add_argument('--patch',help='exact gameplay patch; omitted pins first eligible match patch')
    parser.add_argument('--start-time',type=int)
    parser.add_argument('--end-time',type=int)
    parser.add_argument('--lookback-days',type=int,default=7)
    for option,default in [('max-matches',50),('max-requests',250),('max-pages',1),('max-players',20),('max-retries',2),('deadline-seconds',600)]:
        parser.add_argument('--'+option,type=int,default=default)
    parser.add_argument('--no-item-markers',action='store_true')
    parser.add_argument('--max-gold-ci-width',type=float)
    parser.add_argument('--max-xp-ci-width',type=float)
    parser.add_argument('--max-cs-ci-width',type=float)
    args=parser.parse_args()
    if args.lookback_days<1:parser.error('lookback-days must be positive')
    end=args.end_time if args.end_time is not None else int(datetime.now(timezone.utc).timestamp())
    start=args.start_time if args.start_time is not None else max(0,end-args.lookback_days*86400)
    limits={name:getattr(args,name) for name in ('max_matches','max_requests','max_pages','max_players','max_retries','deadline_seconds')}
    overrides={metric:value for metric,value in [('gold_delta',args.max_gold_ci_width),('xp_delta',args.max_xp_ci_width),('cs_delta',args.max_cs_ci_width)] if value is not None}
    try:
        result=RiotCollector(**limits).collect(tier=args.tier,division=args.division,patch=args.patch,
            start_time=start,end_time=end,collect_items=not args.no_item_markers,ci_width_limits=overrides or None)
        result=validate_power_dataset(result)
    except ValueError:
        parser.error('invalid collection arguments or unsafe aggregate; no output written')
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    temporary=output.with_name(output.name+'.tmp')
    temporary.write_text(json.dumps(result,ensure_ascii=False,allow_nan=False,sort_keys=True,indent=2)+'\n')
    os.replace(temporary,output)
    # Do not echo paths or response text; only fixed metadata and aggregate counts.
    print(json.dumps(dict(status=result['status'],samples=result['samples']['real_matches'],
        coaching_accuracy=None,collection_reason=result['source']['collection']['reason'])))
    return 0


if __name__=='__main__':sys.exit(main())

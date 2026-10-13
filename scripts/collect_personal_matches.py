#!/usr/bin/env python3
"""Collect own recorded matches locally after Riot ID/server and renewed key exist."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from coach_v1.personal_riot import PersonalRiotCollector
from coach_v1.postgame_match import PostgameStore
from coach_v1.riot_collector import CollectionBlocked


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--riot-id',required=True,help='GameName#TagLine; remains local')
    p.add_argument('--server',choices=['KR'],required=True)
    p.add_argument('--private-directory',default='private/postgame')
    p.add_argument('--count',type=int,default=1)
    args=p.parse_args(argv)
    try:
        collector=PersonalRiotCollector(max_requests=20,max_retries=0,deadline_seconds=120)
        result=collector.collect(riot_id=args.riot_id,server=args.server,count=args.count,store=PostgameStore(args.private_directory))
        # Safe local summary only. Never print account, URL, raw pair or credential.
        print(json.dumps(result,ensure_ascii=False));return 0
    except (ValueError,CollectionBlocked) as e:
        print(json.dumps(dict(status='BLOCKED_EXTERNAL',reason=str(e),privacy='LOCAL_PRIVATE')));return 2

if __name__=='__main__':raise SystemExit(main())

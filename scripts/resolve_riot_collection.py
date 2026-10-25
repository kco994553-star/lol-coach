#!/usr/bin/env python3
"""Resolve public official patch and recorded key window before any Riot API call."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
import urllib.request
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from coach_v1.riot_collection_policy import resolve_patch,key_enabled,FUTURE_STATISTICS_TIERS,collection_target

URL='https://ddragon.leagueoflegends.com/api/versions.json'

def main():
    p=argparse.ArgumentParser();p.add_argument('--patch',default='');p.add_argument('--tier',choices=FUTURE_STATISTICS_TIERS);p.add_argument('--rotation',type=int);p.add_argument('--division',choices=('I','II','III','IV'))
    p.add_argument('--manual-renewed',action='store_true');p.add_argument('--aggregate-directory',required=True);args=p.parse_args()
    try:
        policy=json.loads(Path('config/riot_collection_policy.json').read_text())
        if args.patch:patch=resolve_patch([],explicit=args.patch)
        else:
            request=urllib.request.Request(URL,headers={'User-Agent':'lol-coach/2.0 official static patch metadata'})
            with urllib.request.urlopen(request,timeout=20) as response:
                body=response.read(100_001)
            if len(body)>100_000:raise ValueError('PUBLIC_PATCH_METADATA_LIMIT')
            patch=resolve_patch(json.loads(body))
        directory=Path(args.aggregate_directory);enabled=key_enabled(policy,int(time.time()),manual_confirmed=args.manual_renewed)
        target=collection_target(args.rotation if args.rotation is not None else int(time.time())//86400)
        tier=args.tier or target['tier'];division=args.division or target['division']
        result=dict(patch=patch,tier=tier,division=division,enabled=enabled,auxiliary_needed=False,
                    collection_scope='ALL_TIER_BROWSER_COVERAGE',
                    division_coverage='NOT_APPLICABLE' if tier in ('MASTER','GRANDMASTER','CHALLENGER') else 'SELECTED_DIVISION_PAGE_ONLY',
                    metadata_url=URL if not args.patch else None,own_id_required=False,own_tier_required=False)
        (directory/'collection-policy.json').write_text(json.dumps(result)+'\n')
        with open(os.environ['GITHUB_OUTPUT'],'a') as output:
            output.write('patch='+patch+'\nenabled='+str(enabled).lower()+'\ntier='+tier+'\ndivision='+division+'\n')
        print('RIOT_COLLECTION_POLICY_JSON='+json.dumps(result));return 0
    except (ValueError,OSError,KeyError):
        print('RIOT_COLLECTION_POLICY_JSON='+json.dumps(dict(enabled=False,reason='CURRENT_PATCH_OR_COLLECTION_POLICY_UNKNOWN')));return 2

if __name__=='__main__':raise SystemExit(main())

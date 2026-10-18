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
from coach_v1.riot_collection_policy import resolve_patch,key_enabled,auxiliary_needed

URL='https://ddragon.leagueoflegends.com/api/versions.json'

def main():
    p=argparse.ArgumentParser();p.add_argument('--patch',default='');p.add_argument('--tier',choices=['CHALLENGER','GRANDMASTER'],default='CHALLENGER')
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
        if args.tier=='GRANDMASTER':
            paths=list(directory.glob('power-*-CHALLENGER.json'))
            if len(paths)>100:raise ValueError('DATASET_BOUND')
            needed=auxiliary_needed([json.loads(path.read_text()) for path in paths],patch=patch)
            enabled=enabled and needed
        else:needed=False
        result=dict(patch=patch,tier=args.tier,enabled=enabled,auxiliary_needed=needed,metadata_url=URL if not args.patch else None,
                    own_id_required=False,own_tier_required=False)
        (directory/'collection-policy.json').write_text(json.dumps(result)+'\n')
        with open(os.environ['GITHUB_OUTPUT'],'a') as output:
            output.write('patch='+patch+'\nenabled='+str(enabled).lower()+'\n')
        print('RIOT_COLLECTION_POLICY_JSON='+json.dumps(result));return 0
    except (ValueError,OSError,KeyError):
        print('RIOT_COLLECTION_POLICY_JSON='+json.dumps(dict(enabled=False,reason='CURRENT_PATCH_OR_PRIMARY_REFERENCE_UNKNOWN')));return 2

if __name__=='__main__':raise SystemExit(main())

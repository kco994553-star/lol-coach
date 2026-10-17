#!/usr/bin/env python3
"""Reuse bounded Riot collector for confirmed current LCK solo accounts; no raw data output."""
import argparse,json,sys,os
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from coach_v1.account_dashboard import AccountDashboardService,verified_accounts


def refresh(config,*,service=None):
    rows=verified_accounts(config);service=service or AccountDashboardService();profiles=[];requests=0;failures=[]
    for row in rows:
        result=service.lookup(dict(riot_id=row['riot_id'],region=row['region']));requests+=result.get('provider_requests',0)
        if result['status']!='CONNECTED':
            failures.append(dict(status=result['status'],reason=result.get('reason','LOOKUP_FAILED')))
            # Never walk another account to bypass authorization, quota or server failure.
            if result['status']=='API_UNAVAILABLE':break
            continue
        profiles.append(dict(player=row['player'],team=row['team'],position=row['position'],roster_status=row['roster_status'],account_status=row['account_status'],roster_source=row['roster_source'],account_source=row['account_source'],account_checked_at=row['checked_at'],profile=result['profile']))
    return dict(format='lol-coach-pro-dashboard-v1',status='PARTIAL' if profiles and failures else 'READY' if profiles else 'NO_VERIFIED_ACCOUNTS' if not rows else 'BLOCKED_EXTERNAL',profiles=profiles,attempted_at=datetime.now(timezone.utc).isoformat(),updated_at=datetime.now(timezone.utc).isoformat() if profiles else None,queue_id=420,population='현재 LCK 1군의 확인된 본인 솔로랭크 계정',provider_requests=requests,failures=failures,eligible_accounts=len(rows))


def valid_published_state(previous):
    return isinstance(previous,dict) and previous.get('format')=='lol-coach-pro-dashboard-v1' and previous.get('queue_id')==420 and isinstance(previous.get('profiles'),list) and previous.get('status') in ('READY','NOT_REFRESHED','NO_VERIFIED_ACCOUNTS','BLOCKED_EXTERNAL') and isinstance(previous.get('failures',[]),list)


def previous_auth_blocked(previous):
    if not valid_published_state(previous):return True
    return any(isinstance(f,dict) and f.get('reason') in ('AUTHORIZATION_STOPPED','KEY_NOT_CONFIGURED','PREVIOUS_AUTH_FAILURE_NO_RETRY','AUTH_STOP_STATE_UNAVAILABLE') for f in previous.get('failures',[]))


def first_deployment_verified(ref,manifest):
    return ref=='ca85725e1ef6205f8f9ca1f5977ad2ce93fb6894' and isinstance(manifest,dict) and manifest.get('format')=='lol-coach-loading-public-export-v1' and manifest.get('source_commit')=='8acd8dfee2ccbdc1d5aacf2460dca94468221530' and isinstance(manifest.get('sha256'),dict) and not {'dashboard.js','pro-dashboard.json'}&set(manifest['sha256'])


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',default='config/lck_verified_accounts.json');p.add_argument('--output',required=True);p.add_argument('--respect-published-auth-stop',action='store_true');a=p.parse_args()
    config=json.loads(Path(a.config).read_text());previous=None;failure=None
    manual_renewed=os.environ.get('GITHUB_EVENT_NAME')=='workflow_dispatch' and os.environ.get('KEY_RENEWED')=='true'
    if a.respect_published_auth_stop and not manual_renewed:
        from urllib.request import Request,urlopen
        from urllib.error import HTTPError
        try:
            with urlopen(Request('https://raw.githubusercontent.com/kco994553-star/lol-coach/gh-pages/pro-dashboard.json',headers={'User-Agent':'LoL-Coach-auth-stop-check'}),timeout=20) as r:previous=json.loads(r.read(2000000))
            if not valid_published_state(previous):failure='AUTH_STOP_STATE_UNAVAILABLE'
            elif previous_auth_blocked(previous):failure='PREVIOUS_AUTH_FAILURE_NO_RETRY'
        except HTTPError as e:
            failure='AUTH_STOP_STATE_UNAVAILABLE'
            if e.code==404:
                # A 404 alone isn't first use. Prove the exact pre-dashboard artifact.
                from urllib.request import build_opener
                from coach_v1.riot_collector import _RejectRedirect
                try:
                    headers={'User-Agent':'LoL-Coach-auth-stop-bootstrap'}
                    if os.environ.get('GITHUB_TOKEN'):headers['Authorization']='Bearer '+os.environ['GITHUB_TOKEN']
                    with build_opener(_RejectRedirect()).open(Request('https://api.github.com/repos/kco994553-star/lol-coach/git/ref/heads/gh-pages',headers=headers),timeout=20) as r:ref=json.loads(r.read(200000))['object']['sha']
                    with urlopen(Request('https://raw.githubusercontent.com/kco994553-star/lol-coach/'+ref+'/build-info.json',headers={'User-Agent':'LoL-Coach-auth-stop-bootstrap'}),timeout=20) as r:manifest=json.loads(r.read(2000000))
                    if first_deployment_verified(ref,manifest):failure=None
                except (OSError,ValueError,KeyError,TypeError):pass
        except (OSError,ValueError):failure='AUTH_STOP_STATE_UNAVAILABLE'
    result=refresh(config) if failure is None else dict(format='lol-coach-pro-dashboard-v1',status='BLOCKED_EXTERNAL',profiles=[],updated_at=None,attempted_at=datetime.now(timezone.utc).isoformat(),queue_id=420,population='현재 LCK 1군의 확인된 본인 솔로랭크 계정',provider_requests=0,failures=[dict(status='API_UNAVAILABLE',reason=failure)],eligible_accounts=len(verified_accounts(config)))
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],eligible_accounts=result['eligible_accounts'],profiles=len(result['profiles']),provider_requests=result['provider_requests'],identifiers_logged=False)))
if __name__=='__main__':main()

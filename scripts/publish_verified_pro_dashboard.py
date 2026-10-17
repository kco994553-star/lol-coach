#!/usr/bin/env python3
"""CAS publish only safe verified-pro projection + manifest hashes, never application code."""
import argparse,base64,hashlib,json,os,sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request,HTTPRedirectHandler,build_opener
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from coach_v1.account_dashboard import verified_accounts
REPO='kco994553-star/lol-coach'


def _typed_equal(left,right):
    if type(left) is not type(right):return False
    if isinstance(left,dict):return set(left)==set(right) and all(_typed_equal(left[k],right[k]) for k in left)
    if isinstance(left,list):return len(left)==len(right) and all(_typed_equal(x,y) for x,y in zip(left,right))
    return left==right


def _safe_profile(p):
    from coach_v1.account_dashboard import project_profile,valid_request
    from datetime import datetime
    allowed={'format','riot_id','region','identity','retrieved_at','rank','recent_matches','champions','statistics','omitted_matches','notes','coaching_score','limitations'}
    if not isinstance(p,dict) or set(p)!=allowed or not valid_request({'riot_id':p.get('riot_id'),'region':p.get('region')}) or p['region']!='KR':raise ValueError('UNSAFE_PROFILE')
    if not isinstance(p['retrieved_at'],str):raise ValueError('TIMESTAMP_REQUIRED')
    try:datetime.fromisoformat(p['retrieved_at'])
    except ValueError:raise ValueError('INVALID_TIMESTAMP') from None
    rank=p['rank'];league=None
    if rank is not None:
        if not isinstance(rank,dict) or set(rank)!={'tier','division','lp','observed_at'}:raise ValueError('UNSAFE_RANK')
        league={'queueType':'RANKED_SOLO_5x5','tier':rank['tier'],'rank':rank['division'],'leaguePoints':rank['lp']}
    if not isinstance(p['recent_matches'],list) or len(p['recent_matches'])>5:raise ValueError('UNSAFE_MATCHES')
    matches=[]
    for m in p['recent_matches']:
        if not isinstance(m,dict) or set(m)!={'champion','won','kills','deaths','assists','started_at','queue_id','duration_seconds'} or m['queue_id']!=420:raise ValueError('UNSAFE_MATCH')
        matches.append({'info':{'queueId':420,'gameStartTimestamp':m['started_at'],'gameDuration':m['duration_seconds'],'participants':[{'puuid':'EPHEMERAL_VALIDATION_ONLY','championName':m['champion'],'win':m['won'],'kills':m['kills'],'deaths':m['deaths'],'assists':m['assists']}]}})
    expected=project_profile(p['riot_id'],'KR',league,matches,'EPHEMERAL_VALIDATION_ONLY',retrieved_at=p['retrieved_at'])
    if type(p['omitted_matches']) is not int or p['omitted_matches']<0:raise ValueError('INVALID_OMISSIONS')
    expected['omitted_matches']=p['omitted_matches']
    if not _typed_equal(p,expected):raise ValueError('PROFILE_PROJECTION_MISMATCH')
    return expected


def publication_data(data,config,manifest,previous=None):
    import re
    eligible={r['riot_id']:r for r in verified_accounts(config)}
    allowed={'format','status','profiles','updated_at','queue_id','population','provider_requests','failures','eligible_accounts','attempted_at'}
    if not isinstance(data,dict) or set(data)-allowed or data.get('format')!='lol-coach-pro-dashboard-v1' or data.get('queue_id')!=420 or not isinstance(data.get('profiles'),list):raise ValueError('INVALID_PROJECTION')
    if manifest.get('format')!='lol-coach-loading-public-export-v1' or 'dashboard.js' not in manifest.get('sha256',{}):raise ValueError('DASHBOARD_NOT_DEPLOYED')
    def rows_safe(rows):
        safe=[];seen=set()
        for row in rows:
            if not isinstance(row,dict) or set(row)!={'player','team','position','roster_status','account_status','roster_source','account_source','account_checked_at','profile'}:raise ValueError('UNSAFE_REFERENCE_FIELDS')
            p=_safe_profile(row['profile']);source=eligible.get(p['riot_id'])
            if not source or p['riot_id'] in seen or any(row.get(k)!=source[k] for k in ('player','team','position','roster_status','account_status','roster_source','account_source')) or row['account_checked_at']!=source['checked_at']:raise ValueError('ROSTER_MISMATCH')
            seen.add(p['riot_id']);safe.append(dict(row,profile=p))
        return safe
    profiles=rows_safe(data['profiles']);failures=data.get('failures',[])
    if not isinstance(failures,list) or any(not isinstance(f,dict) or set(f)!={'status','reason'} or any(not isinstance(v,str) or not re.fullmatch(r'[A-Z0-9_]{1,80}',v) for v in f.values()) for f in failures):raise ValueError('UNSAFE_FAILURE')
    failed=data.get('status') in ('BLOCKED_EXTERNAL','PARTIAL') or bool(failures)
    updated=data.get('updated_at');refresh='SUCCESS'
    if failed and previous is not None:
        # Retain only still-eligible accounts, and revalidate every nested field before reuse.
        old_rows=[r for r in previous.get('profiles',[]) if r.get('profile',{}).get('riot_id') in eligible]
        profiles=rows_safe(old_rows);updated=previous.get('updated_at');refresh='FAILED_PREVIOUS_RETAINED'
    elif failed:refresh='FAILED_NO_PREVIOUS_DATA'
    requests=data.get('provider_requests',0)
    if type(requests) is not int or requests<0:raise ValueError('INVALID_REQUEST_COUNT')
    from datetime import datetime
    for stamp in (updated,data.get('attempted_at')):
        if stamp is not None:
            if not isinstance(stamp,str):raise ValueError('TIMESTAMP_REQUIRED')
            try:datetime.fromisoformat(stamp)
            except ValueError:raise ValueError('INVALID_TIMESTAMP') from None
    safe=dict(format='lol-coach-pro-dashboard-v1',status='READY' if profiles else 'BLOCKED_EXTERNAL' if failed else 'NO_VERIFIED_ACCOUNTS',profiles=profiles,updated_at=updated,queue_id=420,population='현재 LCK 1군의 확인된 본인 솔로랭크 계정',provider_requests=requests,eligible_accounts=len(eligible),refresh_status=refresh,last_attempt_at=data.get('attempted_at'),failures=failures)
    content=json.dumps(safe,ensure_ascii=False,indent=2)+'\n'
    new=json.loads(json.dumps(manifest));new['sha256']['pro-dashboard.json']=hashlib.sha256(content.encode()).hexdigest();new['reference_refreshed_at']=updated
    return {'pro-dashboard.json':content,'build-info.json':json.dumps(new,ensure_ascii=False,indent=2)+'\n'}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None


def publish(data,config,token):
    if not token:raise ValueError('PUBLISH_TOKEN_MISSING')
    def api(path,body=None,method=None):
        req=Request('https://api.github.com/repos/'+REPO+'/'+path,data=json.dumps(body).encode() if body is not None else None,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','Content-Type':'application/json','User-Agent':'LoL-Coach-verified-reference-publisher'},method=method)
        with build_opener(NoRedirect()).open(req,timeout=25) as r:return json.loads(r.read(2000000))
    ref=api('git/ref/heads/gh-pages')['object']['sha'];commit=api('git/commits/'+ref)
    meta=api('contents/build-info.json?ref='+ref);manifest=json.loads(base64.b64decode(meta['content']))
    if 'dashboard.js' not in manifest.get('sha256',{}):
        return dict(status='INITIAL_DASHBOARD_NOT_DEPLOYED_ARTIFACT_RETAINED')
    old=api('contents/pro-dashboard.json?ref='+ref)
    files=publication_data(data,config,manifest,previous=json.loads(base64.b64decode(old['content'])))
    if base64.b64decode(old['content']).decode()==files['pro-dashboard.json']:return dict(status='UNCHANGED_NO_COMMIT')
    tree=api('git/trees',dict(base_tree=commit['tree']['sha'],tree=[dict(path=p,mode='100644',type='blob',content=c) for p,c in files.items()]),'POST')['sha']
    new=api('git/commits',dict(message='Refresh confirmed LCK solo420 reference projection',tree=tree,parents=[ref]),'POST')['sha']
    # Re-read before a non-force update; GitHub also rejects a non-fast-forward race.
    if api('git/ref/heads/gh-pages')['object']['sha']!=ref:raise ValueError('ARTIFACT_CHANGED_NO_RETRY')
    api('git/refs/heads/gh-pages',dict(sha=new,force=False),'PATCH')
    build=api('pages/builds',{},'POST')
    return dict(status='ARTIFACT_UPDATED_DEPLOYMENT_REQUESTED',artifact_commit=new,changed_files=list(files),pages_build_status=build.get('status','UNKNOWN'),pages_build_url=build.get('url'))


def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--config',default='config/lck_verified_accounts.json');a=p.parse_args()
    try:result=publish(json.loads(Path(a.input).read_text()),json.loads(Path(a.config).read_text()),os.environ.get('GITHUB_TOKEN',''))
    except (ValueError,HTTPError,OSError,KeyError,TypeError):print(json.dumps(dict(status='PUBLIC_REFERENCE_PUBLICATION_BLOCKED',private_values_logged=False)));return 2
    print(json.dumps(result));return 0
if __name__=='__main__':raise SystemExit(main())

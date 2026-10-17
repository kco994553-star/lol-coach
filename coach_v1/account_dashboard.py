"""Private bounded Riot lookup and safe solo420 dashboard projections. Never logs identities."""
from datetime import datetime,timezone
import os,threading,re
from urllib.parse import quote,urlsplit
from .riot_collector import RiotCollector,CollectionBlocked
from .pro_reference import account_url
from .api_diagnostics import inspect_riot_key


def valid_request(body):
    if not isinstance(body,dict) or set(body)!={'riot_id','region'}:return False
    value=body['riot_id']
    return isinstance(body['region'],str) and isinstance(value,str) and value.count('#')==1 and 1<=len(value.split('#')[0])<=100 and 1<=len(value.split('#')[1])<=20 and all(part.strip() for part in value.split('#')) and not any(ord(c)<32 for c in value)


def project_profile(riot_id,region,league,matches,puuid,*,retrieved_at):
    valid=[];omitted=0
    for match in matches:
        info=match.get('info',{}) if isinstance(match,dict) else {}
        if not isinstance(info,dict):omitted+=1;continue
        people=info.get('participants',[])
        own=[p for p in people if isinstance(p,dict) and p.get('puuid')==puuid] if isinstance(people,list) else []
        if info.get('queueId')!=420 or len(own)!=1:omitted+=1;continue
        p=own[0];stamp=info.get('gameStartTimestamp')
        if not isinstance(p.get('championName'),str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9]{0,49}',p['championName']) or type(p.get('win')) is not bool or type(stamp) is not int or stamp<=0 or any(type(p.get(k)) is not int or p[k]<0 for k in ('kills','deaths','assists')):omitted+=1;continue
        valid.append(dict(champion=p['championName'],won=p['win'],kills=p['kills'],deaths=p['deaths'],assists=p['assists'],started_at=stamp,queue_id=420,duration_seconds=info.get('gameDuration') if type(info.get('gameDuration')) is int else None))
    valid.sort(key=lambda r:r['started_at'],reverse=True)
    n=len(valid);wins=sum(p['won'] for p in valid);deaths=sum(p['deaths'] for p in valid);champions=[]
    for champ in sorted({p['champion'] for p in valid}):
        rows=[p for p in valid if p['champion']==champ];d=sum(p['deaths'] for p in rows)
        champions.append(dict(champion=champ,sample_n=len(rows),wins=sum(p['won'] for p in rows),win_rate=100*sum(p['won'] for p in rows)/len(rows),kda=sum(p['kills']+p['assists'] for p in rows)/d if d else None))
    rank=None
    if isinstance(league,dict) and league.get('queueType')=='RANKED_SOLO_5x5' and league.get('tier') in ('IRON','BRONZE','SILVER','GOLD','PLATINUM','EMERALD','DIAMOND','MASTER','GRANDMASTER','CHALLENGER') and league.get('rank') in ('I','II','III','IV') and type(league.get('leaguePoints')) is int and league['leaguePoints']>=0:
        rank=dict(tier=league['tier'],division=league['rank'],lp=league['leaguePoints'],observed_at=retrieved_at)
    return dict(format='lol-coach-account-profile-v1',riot_id=riot_id,region=region,identity='RIOT_ID_LOOKUP_NOT_OWNERSHIP_AUTH',retrieved_at=retrieved_at,rank=rank,recent_matches=valid,champions=champions,statistics=dict(sample_n=n,wins=wins if n else None,win_rate=100*wins/n if n else None,kda=sum(p['kills']+p['assists'] for p in valid)/deaths if deaths else None,window_start=min(p['started_at'] for p in valid) if n else None,window_end=max(p['started_at'] for p in valid) if n else None,queue_id=420),omitted_matches=omitted,notes=[],coaching_score=None,limitations=['최근 조회한 솔로/듀오 랭크 표본이며 시즌 전체 승률·실력 점수가 아닙니다.','KDA는 합산 킬+어시스트 / 합산 사망입니다. 사망 합계가 0이면 비율은 미정의입니다.','계정 기록은 코칭 분석·현재 픽창 또는 계정 소유권 확인이 아닙니다.'])


class AccountDashboardService:
    def __init__(self,*,api_key=None,transport=None):
        self.api_key=api_key if api_key is not None else os.environ.get('RIOT_API_KEY','')
        self.transport=transport;self.lock=threading.Lock();self.blocked=None;self.rate_times={};self.rate_not_before={}
    def lookup(self,body):
        if not valid_request(body):return dict(status='INPUT_ERROR',reason='INVALID_RIOT_ID_OR_FIELDS')
        if body['region']!='KR':return dict(status='REGION_UNSUPPORTED',reason='INITIAL_BACKEND_SUPPORTS_KR')
        key,shape=inspect_riot_key(self.api_key)
        if not shape['valid_shape']:return dict(status='API_UNAVAILABLE',reason='KEY_NOT_CONFIGURED',provider_requests=0)
        with self.lock:
            if self.blocked:return dict(status='API_UNAVAILABLE',reason=self.blocked,provider_requests=0)
            client=RiotCollector(api_key=self.api_key,transport=self.transport,max_requests=9,max_retries=0,deadline_seconds=60)
            client._normalized_api_key=key;client._request_times=self.rate_times;client.not_before=self.rate_not_before
            try:
                account,_=client._get(account_url(body['riot_id']),'ACCOUNT_V1_RIOT_ID',allow_missing=True)
                if account is None:return dict(status='ACCOUNT_NOT_FOUND',provider_requests=client.requests)
                puuid=account.get('puuid') if isinstance(account,dict) else None
                if not isinstance(puuid,str) or not puuid or len(puuid)>200:raise CollectionBlocked('MALFORMED_RESPONSE')
                # Official API reference: league-v4 getLeagueEntriesByPUUID; schema source recorded separately.
                entries,_=client._get('https://kr.api.riotgames.com/lol/league/v4/entries/by-puuid/'+quote(puuid,safe=''),'LEAGUE_V4_BY_PUUID')
                if not isinstance(entries,list):raise CollectionBlocked('MALFORMED_RESPONSE')
                solo=[p for p in entries if isinstance(p,dict) and p.get('queueType')=='RANKED_SOLO_5x5']
                ids,_=client._get('https://asia.api.riotgames.com/lol/match/v5/matches/by-puuid/'+quote(puuid,safe='')+'/ids?queue=420&start=0&count=5','MATCH_V5_SOLO_IDS')
                if not isinstance(ids,list) or len(ids)>5 or not all(isinstance(mid,str) for mid in ids) or len(set(ids))!=len(ids):raise CollectionBlocked('MALFORMED_RESPONSE')
                import re
                matches=[]
                for mid in ids:
                    if not isinstance(mid,str) or not re.fullmatch(r'KR_[0-9]+',mid):raise CollectionBlocked('MALFORMED_RESPONSE')
                    m,_=client._get('https://asia.api.riotgames.com/lol/match/v5/matches/'+mid,'MATCH_V5_MATCH');matches.append(m)
                profile=project_profile(body['riot_id'],'KR',solo[0] if len(solo)==1 else None,matches,puuid,retrieved_at=datetime.now(timezone.utc).isoformat())
                return dict(status='CONNECTED',profile=profile,provider_requests=client.requests)
            except CollectionBlocked as e:
                if e.status_code in (401,403,429):self.blocked='AUTHORIZATION_STOPPED' if e.status_code in (401,403) else 'RATE_LIMIT_STOPPED'
                return dict(status='API_UNAVAILABLE',reason=self.blocked or e.reason,provider_requests=client.requests)
            finally:self.rate_times=client._request_times;self.rate_not_before=client.not_before


def verified_accounts(config):
    if not isinstance(config,dict) or config.get('format')!='lol-coach-verified-lck-v1' or not isinstance(config.get('accounts'),list):raise ValueError('INVALID_VERIFIED_ROSTER')
    result=[];seen=set()
    for row in config['accounts']:
        required=('player','team','position','riot_id','region','roster_status','account_status','roster_source','account_source','checked_at')
        if not isinstance(row,dict) or any(not isinstance(row.get(k),str) or not row[k].strip() for k in required):raise ValueError('ROSTER_AND_ACCOUNT_SOURCES_REQUIRED')
        if row['roster_status']!='CURRENT_LCK_FIRST_TEAM_VERIFIED' or row['account_status']!='VERIFIED' or row['position'] not in ('TOP','JUNGLE','MID','BOTTOM','SUPPORT') or row['region']!='KR' or not valid_request(dict(riot_id=row['riot_id'],region='KR')):raise ValueError('CURRENT_LCK_SOLO_ACCOUNT_REQUIRED')
        for k in ('roster_source','account_source'):
            u=urlsplit(row[k])
            if u.scheme!='https' or not u.netloc or u.username or u.password:raise ValueError('SOURCE_URL_REQUIRED')
        try:datetime.strptime(row['checked_at'],'%Y-%m-%d')
        except ValueError:raise ValueError('CHECK_DATE_REQUIRED') from None
        if row['riot_id'].casefold() in seen:raise ValueError('DUPLICATE_ACCOUNT')
        seen.add(row['riot_id'].casefold());result.append(dict(row))
    return result

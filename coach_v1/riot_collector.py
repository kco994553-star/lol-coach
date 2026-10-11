"""Bounded official KR League-V4 → ASIA Match-V5 collection.

No raw responses, identifiers, URLs containing identifiers, or key values are
logged or written. All externally visible failure reasons are fixed enums.
"""
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
import os
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote, urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener

from .power_stats import (TIERS, build_power_dataset, empty_power_dataset,
                          validate_power_dataset)


class CollectionBlocked(Exception):
    def __init__(self,reason,status_code=None):
        self.reason=reason;self.status_code=status_code
        super().__init__(reason)


class _RejectRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        return None


def _transport(url,headers,timeout):
    try:
        # Preserve proxy/TLS defaults, while never forwarding authentication
        # to a redirect destination, even if the original host was official.
        with build_opener(_RejectRedirect()).open(Request(url,headers=headers),timeout=timeout) as response:
            body=response.read(16*1024*1024+1)
            if len(body)>16*1024*1024:raise CollectionBlocked('MALFORMED_RESPONSE')
            return response.status,dict(response.headers),body
    except HTTPError as error:
        # Error bodies are neither dependable JSON nor safe public diagnostics.
        return error.code,dict(error.headers),b''


def complete_item_ids(catalog):
    """Pinned Summoner's Rift purchasable recipe leaves, excluding consumables.

    No price threshold. Leaves that only transform into non-purchasable items
    count as complete. Unclassified metadata never creates item markers.
    """
    data=catalog.get('data',{}) if isinstance(catalog,dict) else {}
    if not isinstance(data,dict):raise CollectionBlocked('ITEM_CATALOG_UNAVAILABLE')
    result=[]
    for item_id,item in data.items():
        if not isinstance(item,dict) or not re.fullmatch(r'[0-9]+',item_id):continue
        if item.get('gold',{}).get('purchasable') is not True or item.get('maps',{}).get('11') is not True:continue
        if item.get('inStore') is False or not item.get('from'):continue
        if set(item.get('tags',[])) & {'Consumable','Trinket','Jungle'}:continue
        if any(data.get(str(next_id),{}).get('gold',{}).get('purchasable') is True for next_id in item.get('into',[])):continue
        result.append(int(item_id))
    return sorted(result)


class RiotCollector:
    def __init__(self,api_key=None,*,transport=None,clock=None,sleeper=None,
                 max_requests=250,max_matches=50,max_pages=1,max_players=20,
                 max_retries=2,deadline_seconds=600):
        self.api_key=api_key if api_key is not None else os.environ.get('RIOT_API_KEY')
        self.transport=transport or _transport;self.clock=clock or time.monotonic;self.sleeper=sleeper or time.sleep
        self.limits=dict(max_requests=max_requests,max_matches=max_matches,max_pages=max_pages,
                         max_players=max_players,max_retries=max_retries,deadline_seconds=deadline_seconds)
        if any(type(v) is not int or v<(0 if k=='max_retries' else 1) for k,v in self.limits.items()):
            raise ValueError('positive bounded collection limits required')
        self.requests=0;self.retries=0;self.not_before={};self.started=self.clock()

    def _pause(self,seconds):
        remaining=self.started+self.limits['deadline_seconds']-self.clock()
        if seconds>=remaining:raise CollectionBlocked('DEADLINE_EXHAUSTED')
        while seconds>0:
            step=min(seconds,60);self.sleeper(step);seconds-=step

    def _rate_headers(self,host,method,headers):
        h={str(k).lower():str(v) for k,v in headers.items()}
        for prefix,key in (('x-app-rate-limit',('app',host)),('x-method-rate-limit',('method',host,method))):
            try:
                limits={float(window):int(count) for count,window in (x.split(':') for x in h.get(prefix,'').split(',') if x)}
                counts={float(window):int(count) for count,window in (x.split(':') for x in h.get(prefix+'-count','').split(',') if x)}
                for window,limit in limits.items():
                    if window>0 and limit>0 and counts.get(window,0)>=limit:
                        self.not_before[key]=max(self.not_before.get(key,0),self.clock()+window)
            except (ValueError,TypeError):continue

    def _retry_after(self,headers):
        value=next((str(v) for k,v in headers.items() if k.lower()=='retry-after'),None)
        if value is None:return None
        try:seconds=float(value)
        except ValueError:
            try:seconds=parsedate_to_datetime(value).timestamp()-datetime.now(timezone.utc).timestamp()
            except (ValueError,TypeError,OverflowError):return None
        return max(seconds,0) if seconds==seconds and seconds!=float('inf') else None

    def _get(self,url,method,*,api=True,allow_missing=False):
        host=urlsplit(url).netloc
        if host not in ('kr.api.riotgames.com','asia.api.riotgames.com','ddragon.leagueoflegends.com'):
            raise ValueError('official endpoint required')
        for attempt in range(self.limits['max_retries']+1):
            if self.clock()-self.started>=self.limits['deadline_seconds']:raise CollectionBlocked('DEADLINE_EXHAUSTED')
            if self.requests>=self.limits['max_requests']:raise CollectionBlocked('REQUEST_BUDGET_EXHAUSTED')
            wait=max(self.not_before.get(('app',host),0),self.not_before.get(('method',host,method),0))-self.clock()
            if wait>0:self._pause(wait)
            headers={'Accept':'application/json'}
            if api:headers['X-Riot-Token']=self.api_key
            self.requests+=1
            try:status,response_headers,body=self.transport(url,headers,min(20,self.started+self.limits['deadline_seconds']-self.clock()))
            except CollectionBlocked:raise
            except (OSError,URLError,TimeoutError):
                if attempt>=self.limits['max_retries']:raise CollectionBlocked('NETWORK_FAILURE') from None
                self.retries+=1;self._pause(min(2**attempt,30));continue
            self._rate_headers(host,method,response_headers)
            if status==200:
                try:return json.loads(body),body
                except (ValueError,TypeError,UnicodeDecodeError):raise CollectionBlocked('MALFORMED_RESPONSE',status) from None
            if status in (401,403):raise CollectionBlocked('UNAUTHORIZED_OR_EXPIRED_OR_UNSUPPORTED_PATH',status)
            if status==404 and allow_missing:return None,b''
            if status==429:
                pause=self._retry_after(response_headers)
                if attempt>=self.limits['max_retries'] or pause is None:raise CollectionBlocked('RATE_LIMIT_EXHAUSTED',status)
                self.retries+=1;self._pause(pause);continue
            if status in (500,502,503,504):
                if attempt>=self.limits['max_retries']:raise CollectionBlocked('RIOT_SERVER_FAILURE',status)
                self.retries+=1;self._pause(min(2**attempt,30));continue
            raise CollectionBlocked('HTTP_FAILURE',status)
        raise CollectionBlocked('RATE_LIMIT_EXHAUSTED')

    def _entries(self,tier,division):
        if tier in ('MASTER','GRANDMASTER','CHALLENGER'):
            payload,_=self._get('https://kr.api.riotgames.com/lol/league/v4/'+tier.lower()+'leagues/by-queue/RANKED_SOLO_5x5','LEAGUE_V4_'+tier)
            entries=payload.get('entries') if isinstance(payload,dict) else None
            if not isinstance(entries,list):raise CollectionBlocked('MALFORMED_RESPONSE')
            return entries
        entries=[]
        for page in range(1,self.limits['max_pages']+1):
            payload,_=self._get('https://kr.api.riotgames.com/lol/league/v4/entries/RANKED_SOLO_5x5/'+tier+'/'+division+'?page='+str(page),'LEAGUE_V4_ENTRIES')
            if not isinstance(payload,list):raise CollectionBlocked('MALFORMED_RESPONSE')
            entries.extend(payload)
            if not payload or len(entries)>=self.limits['max_players']:break
        return entries

    def _catalog(self,patch):
        versions,_=self._get('https://ddragon.leagueoflegends.com/api/versions.json','DD_VERSIONS',api=False)
        if not isinstance(versions,list):raise CollectionBlocked('ITEM_CATALOG_UNAVAILABLE')
        version=next((v for v in versions if isinstance(v,str) and re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+',v)
                      and '.'.join(v.split('.')[:2])==patch),None)
        if version is None:raise CollectionBlocked('ITEM_CATALOG_UNAVAILABLE')
        url='https://ddragon.leagueoflegends.com/cdn/'+version+'/data/en_US/item.json'
        catalog,raw=self._get(url,'DD_ITEMS',api=False)
        if not isinstance(catalog,dict) or catalog.get('version')!=version:raise CollectionBlocked('ITEM_CATALOG_UNAVAILABLE')
        ids=complete_item_ids(catalog)
        return dict(version=version,url=url,sha256=hashlib.sha256(raw).hexdigest(),
                    complete_item_ids=ids,classification='PINNED_COMPLETE_NONCONSUMABLE.v1')

    def collect(self,*,tier='GOLD',division='I',patch=None,start_time=None,end_time=None,collect_items=True,ci_width_limits=None):
        if tier not in TIERS or division not in ('I','II','III','IV'):raise ValueError('invalid league tier or division')
        if patch is not None and not re.fullmatch(r'[0-9]+\.[0-9]+',patch):raise ValueError('exact gameplay patch required')
        for value in (start_time,end_time):
            if value is not None and (type(value) is not int or value<0):raise ValueError('integer epoch window required')
        if start_time is not None and end_time is not None and start_time>end_time:raise ValueError('invalid collection window')
        # A collector instance performs one bounded job, never cumulative reuse.
        self.started=self.clock();self.requests=0;self.retries=0;self.not_before={}
        endpoints=['LEAGUE_V4_'+tier if tier in ('MASTER','GRANDMASTER','CHALLENGER') else 'LEAGUE_V4_ENTRIES',
                   'MATCH_V5_IDS','MATCH_V5_MATCH','MATCH_V5_TIMELINE']
        source=dict(provider='RIOT_API',platform='KR',regional='ASIA',queue_id=420,map_id=11,tier=tier,
            patch=patch,window_start=start_time,window_end=end_time,retrieved_at=datetime.now(timezone.utc).isoformat(),
            sample_kind='REAL',endpoints=endpoints)
        pairs=[];seen=set();error=None;catalog=None
        try:
            if not self.api_key:raise CollectionBlocked('MISSING_API_KEY')
            entries=self._entries(tier,division)
            if not entries:source['limitations']=['NO_LEAGUE_ENTRIES']
            puuids=[]
            for entry in entries:
                puuid=entry.get('puuid') if isinstance(entry,dict) else None
                if isinstance(puuid,str) and puuid and puuid not in puuids:puuids.append(puuid)
                if len(puuids)>=self.limits['max_players']:break
            if entries and not puuids:raise CollectionBlocked('UNSUPPORTED_LEAGUE_IDENTITY')
            for puuid in puuids:
                query=dict(queue=420,type='ranked',start=0,count=min(100,self.limits['max_matches']))
                if start_time is not None:query['startTime']=start_time
                if end_time is not None:query['endTime']=end_time
                ids,_=self._get('https://asia.api.riotgames.com/lol/match/v5/matches/by-puuid/'+quote(puuid,safe='')+'/ids?'+urlencode(query),'MATCH_V5_IDS')
                if not isinstance(ids,list) or not all(isinstance(i,str) for i in ids):raise CollectionBlocked('MALFORMED_RESPONSE')
                for mid in ids:
                    if mid in seen or not re.fullmatch(r'KR_[0-9]+',mid):continue
                    seen.add(mid)
                    match,_=self._get('https://asia.api.riotgames.com/lol/match/v5/matches/'+mid,'MATCH_V5_MATCH',allow_missing=True)
                    if match is None:continue
                    if not isinstance(match,dict):raise CollectionBlocked('MALFORMED_RESPONSE')
                    info=match.get('info',{})
                    if not isinstance(info,dict) or not isinstance(info.get('gameVersion'),str):
                        raise CollectionBlocked('MALFORMED_RESPONSE')
                    version=info['gameVersion'].split('.')
                    if len(version)<2 or not all(v.isdigit() for v in version[:2]):continue
                    matchpatch='.'.join(version[:2])
                    if info.get('queueId')!=420 or info.get('mapId')!=11 or info.get('gameMode')!='CLASSIC':continue
                    if source['patch'] is None:source['patch']=matchpatch
                    if source['patch']!=matchpatch:continue
                    timeline,_=self._get('https://asia.api.riotgames.com/lol/match/v5/matches/'+mid+'/timeline','MATCH_V5_TIMELINE',allow_missing=True)
                    if timeline is None:continue
                    if not isinstance(timeline,dict):raise CollectionBlocked('MALFORMED_RESPONSE')
                    pairs.append(dict(match=match,timeline=timeline))
                    if len(pairs)>=self.limits['max_matches']:break
                if len(pairs)>=self.limits['max_matches']:break
            if pairs and collect_items:
                catalog=self._catalog(source['patch']);source['item_catalog']=catalog
        except CollectionBlocked as failure:error=failure
        source['collection']=dict(key_kind='UNKNOWN',status_code=error.status_code if error else None,
            reason=error.reason if error else None,request_count=self.requests,retry_count=self.retries,limits=self.limits.copy(),
            division=None if tier in ('MASTER','GRANDMASTER','CHALLENGER') else division)
        if error:source.setdefault('limitations',[]).append(error.reason)
        result=build_power_dataset(pairs,source=source,ci_width_limits=ci_width_limits,
            complete_item_ids=catalog['complete_item_ids'] if catalog else ())
        if error:result['status']='BLOCKED_EXTERNAL'
        return validate_power_dataset(result)

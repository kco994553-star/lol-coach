"""Opt-in personal collection to a local private store; no identifier receipts."""
from urllib.parse import quote
from .riot_collector import RiotCollector, CollectionBlocked
from .api_diagnostics import inspect_riot_key


class PersonalRiotCollector(RiotCollector):
    def collect(self,*,riot_id,server,store,count=1):
        self._normalized_api_key,self.key_shape=inspect_riot_key(self.api_key)
        if not self.key_shape['valid_shape']:raise ValueError('RIOT_KEY_REQUIRED')
        if server!='KR':raise ValueError('SUPPORTED_SERVER_KR_ONLY')
        if not isinstance(riot_id,str) or riot_id.count('#')!=1:raise ValueError('RIOT_ID_REQUIRED')
        name,tag=riot_id.rsplit('#',1)
        if not name.strip() or not tag.strip() or len(name)>100 or len(tag)>20:raise ValueError('RIOT_ID_REQUIRED')
        if type(count) is not int or not 1<=count<=5:raise ValueError('INVALID_MATCH_COUNT')
        account,_=self._get('https://asia.api.riotgames.com/riot/account/v1/accounts/by-riot-id/'+quote(name,safe='')+'/'+quote(tag,safe=''),'ACCOUNT_V1_RIOT_ID')
        puuid=account.get('puuid') if isinstance(account,dict) else None
        if not isinstance(puuid,str) or not puuid or len(puuid)>200:raise CollectionBlocked('MALFORMED_RESPONSE')
        ids,_=self._get('https://asia.api.riotgames.com/lol/match/v5/matches/by-puuid/'+quote(puuid,safe='')+'/ids?start=0&count='+str(count),'MATCH_V5_IDS')
        if not isinstance(ids,list) or len(ids)>count:raise CollectionBlocked('MALFORMED_RESPONSE')
        results=[]
        for mid in ids:
            import re
            if not isinstance(mid,str) or not re.fullmatch(r'KR_[0-9]+',mid):raise CollectionBlocked('MALFORMED_RESPONSE')
            match,_=self._get('https://asia.api.riotgames.com/lol/match/v5/matches/'+mid,'MATCH_V5_MATCH')
            timeline,_=self._get('https://asia.api.riotgames.com/lol/match/v5/matches/'+mid+'/timeline','MATCH_V5_TIMELINE')
            people=match.get('info',{}).get('participants',[]) if isinstance(match,dict) else []
            own=[p for p in people if isinstance(p,dict) and p.get('puuid')==puuid]
            if len(own)!=1:raise CollectionBlocked('MALFORMED_RESPONSE')
            results.append(store.import_match(dict(match=match,timeline=timeline,participant_id=own[0]['participantId'],source='REAL')))
        return dict(status='READY' if results else 'NO_MATCHES',matches=results,request_count=self.requests,privacy='LOCAL_PRIVATE')

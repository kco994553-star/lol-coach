"""Local user-reported pro roster preparation and private bounded collection.

Roster badges, historical ranks and activity claims are user reports. This is a
selected-player population, never a current League tier seed cohort.
"""
from collections import defaultdict
from copy import deepcopy
from datetime import date, datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import statistics
import tempfile
from urllib.parse import quote

from .api_diagnostics import inspect_riot_key
from .power_stats import ROLE_MAP, _point, _policy
from .postgame_match import PostgameStore, _chmod_file
from .riot_collector import RiotCollector, CollectionBlocked
from .state import digest

ROLES=('TOP','JUNGLE','MID','ADC','SUPPORT')
CANONICAL_ROLES={'TOP':'TOP','JUNGLE':'JUNGLE','MID':'MID','ADC':'BOTTOM','SUPPORT':'SUPPORT'}
FORMAT='lol-coach-pro-reference-players-v1'
LIMITATIONS=['USER_REPORT_OPGG_PRO_BADGE_NOT_NETWORK_VERIFIED','HISTORICAL_RANK_AND_GAME_COUNTS_USER_REPORT_ONLY',
    'SELECTED_INDIVIDUALS_NOT_CURRENT_LEAGUE_SEED_COHORT','NO_PRO_STATUS_OR_TIER_VERIFICATION',
    'DESCRIPTIVE_NON_CAUSAL_NOT_TACTICAL_ACCURACY','POSITION_SHARE_BOUNDED_RECENT_SAMPLE_NOT_COMPLETE_WINDOW',
    'OPERATIONAL_REPLACEMENT_THRESHOLD_NOT_GAMEPLAY_THRESHOLD','MINUTE_SAMPLES_NO_INTERPOLATION',
    'PATCH_SPECIFIC_REFERENCE_NOT_CROSS_PATCH_POOLING','MATCH_CLUSTERED_OBSERVATIONS_NOT_INDEPENDENT_PLAYERS']


def require(ok,reason='INVALID_PRO_REFERENCE'):
    if not ok:raise ValueError(reason)


def account_url(riot_id):
    require(isinstance(riot_id,str) and len(riot_id)<=150 and riot_id.count('#')==1,'INVALID_RIOT_ID')
    name,tag=riot_id.rsplit('#',1)
    require(bool(name.strip()) and bool(tag.strip()) and len(name)<=100 and len(tag)<=20 and not any(ord(c)<32 for c in riot_id),'INVALID_RIOT_ID')
    # Validation checks blanks; exact input is dispatched without normalization.
    return 'https://asia.api.riotgames.com/riot/account/v1/accounts/by-riot-id/'+quote(name,safe='')+'/'+quote(tag,safe='')


def validate_pro_roster(config):
    required={'format','checked_at','region','selection_rule','source_note','usage_rule','players','backups','backup_rule'}
    require(isinstance(config,dict) and set(config)==required,'INVALID_PRO_ROSTER_SCHEMA')
    require(config['format']==FORMAT and config['region']=='KR','UNSUPPORTED_PRO_ROSTER_FORMAT_OR_REGION')
    try:date.fromisoformat(config['checked_at'])
    except (TypeError,ValueError):raise ValueError('INVALID_ROSTER_CHECK_DATE') from None
    for key in ('selection_rule','source_note','usage_rule','backup_rule'):
        require(isinstance(config[key],str) and 1<=len(config[key])<=4000)
    names=set();ids=set();alt_count=0;backup_count=0
    for kind in ('players','backups'):
        require(isinstance(config[kind],dict) and set(config[kind])==set(ROLES))
        for role in ROLES:
            rows=config[kind][role];require(isinstance(rows,list) and (len(rows)==5 if kind=='players' else 1<=len(rows)<=5),'INVALID_ROSTER_ROLE_COUNT')
            backup_count+=len(rows) if kind=='backups' else 0
            for row in rows:
                required_row={'name','team','riot_id'}|({'seen'} if kind=='players' else set())
                require(isinstance(row,dict) and required_row<=set(row)<=required_row|{'seen','note','alt_riot_ids'})
                for key in required_row|({'note'} if 'note' in row else set())|({'seen'} if 'seen' in row else set()):
                    require(isinstance(row[key],str) and 1<=len(row[key])<=1000)
                require(row['name'] not in names,'DUPLICATE_PRO_PLAYER');names.add(row['name'])
                accounts=[row['riot_id']]
                if 'alt_riot_ids' in row:
                    require(isinstance(row['alt_riot_ids'],list) and 1<=len(row['alt_riot_ids'])<=4)
                    accounts+=row['alt_riot_ids'];alt_count+=len(row['alt_riot_ids'])
                for account in accounts:
                    account_url(account);require(account not in ids,'DUPLICATE_PRO_ACCOUNT');ids.add(account)
    require(backup_count==9 and alt_count==1,'EXPECTED_9_BACKUPS_AND_1_ALT_ACCOUNT')
    return deepcopy(config)


def prepare_pro_reference(config):
    c=validate_pro_roster(config)
    return dict(schema_version='pro.reference-preparation.v1',status='READY_TO_COLLECT',reason='COLLECTION_NOT_STARTED',
        region=c['region'],checked_at=c['checked_at'],verification='USER_REPORT_NOT_NETWORK_VERIFIED',tier='UNKNOWN',
        primary_count=25,backup_count=9,alt_count=1,roles=[dict(role=CANONICAL_ROLES[r],input_role=r,
        players=[dict(player=p['name'],team=p['team'],riot_id=p['riot_id'],alt_accounts=p.get('alt_riot_ids',[]),seen=p['seen']) for p in c['players'][r]],
        backups=[dict(player=p['name'],team=p['team'],riot_id=p['riot_id']) for p in c['backups'][r]]) for r in ROLES],
        selection_rule=c['selection_rule'],source_note=c['source_note'],backup_rule=c['backup_rule'],
        collection_command='python scripts/collect_pro_reference.py --config config/pro_reference_players.json --private-directory private/pro-reference',
        privacy='PUUID_AND_RAW_LOCAL_PRIVATE_ONLY',limitations=deepcopy(LIMITATIONS),position_share_threshold_default=.5,
        position_share_policy='REPLACE_IF_OBSERVED_SHARE_LT_THRESHOLD',matches_per_account_default=3,actual_collected_matches=0)


def _write_private(path,value):
    require(not path.is_symlink(),'PRIVATE_SYMLINK_REJECTED')
    fd,tmp=tempfile.mkstemp(prefix='.pro-',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            _chmod_file(stream.fileno(),tmp);json.dump(value,stream,ensure_ascii=False,allow_nan=False,sort_keys=True);stream.flush();os.fsync(stream.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)


class ProReferenceCache:
    def __init__(self,private_directory):
        original=Path(private_directory).absolute()
        require('..' not in original.parts,'PRIVATE_PATH_TRAVERSAL_REJECTED')
        require(not any(p.is_symlink() for p in [original,*original.parents]),'PRIVATE_SYMLINK_REJECTED')
        self.directory=original.resolve()
        require('private' in self.directory.parts,'PRIVATE_DIRECTORY_REQUIRED')
        require(not any(p.is_symlink() for p in [self.directory,*self.directory.parents]),'PRIVATE_SYMLINK_REJECTED')
        self.directory.mkdir(parents=True,exist_ok=True,mode=0o700);os.chmod(self.directory,0o700)
        self.path=self.directory/'accounts.json';require(not self.path.is_symlink(),'PRIVATE_SYMLINK_REJECTED')
        self.accounts={};self.failures=[]
        if self.path.exists():
            require(self.path.is_file() and self.path.stat().st_size<=200000,'INVALID_PRIVATE_ACCOUNT_CACHE')
            raw=json.loads(self.path.read_text());require(isinstance(raw,dict) and raw.get('schema_version')=='pro.private-accounts.v1' and isinstance(raw.get('accounts'),dict),'INVALID_PRIVATE_ACCOUNT_CACHE')
            self.accounts=raw['accounts']
            require(all(isinstance(k,str) and isinstance(p,str) and re.fullmatch(r'[A-Za-z0-9_-]{1,200}',p) for k,p in self.accounts.items()),'INVALID_PRIVATE_ACCOUNT_CACHE')
            os.chmod(self.path,0o600)

    def resolve(self,stable_key,riot_id,lookup):
        require(isinstance(stable_key,str) and 1<=len(stable_key)<=250)
        if stable_key in self.accounts:return self.accounts[stable_key]
        response=lookup(account_url(riot_id))
        if response is None:
            self.failures.append(stable_key);return None
        puuid=response.get('puuid') if isinstance(response,dict) else None
        require(isinstance(puuid,str) and re.fullmatch(r'[A-Za-z0-9_-]{1,200}',puuid),'INVALID_ACCOUNT_RESPONSE')
        self.accounts[stable_key]=puuid;_write_private(self.path,dict(schema_version='pro.private-accounts.v1',accounts=self.accounts))
        return puuid

    def safe_summary(self):return dict(cached_accounts=len(self.accounts),failed_accounts=list(self.failures),privacy='LOCAL_PRIVATE')


class ProReferenceCollector(RiotCollector):
    def collect(self,config,private_directory,*,now=None,position_share_threshold=.5,matches_per_account=3):
        c=validate_pro_roster(config)
        require(type(position_share_threshold) in (int,float) and math.isfinite(position_share_threshold) and 0<=position_share_threshold<=1,'INVALID_POSITION_SHARE_THRESHOLD')
        require(type(matches_per_account) is int and 1<=matches_per_account<=100,'INVALID_MATCH_SAMPLE_LIMIT')
        timestamp=int(datetime.now(timezone.utc).timestamp()) if now is None else now
        require(type(timestamp) is int and timestamp>30*86400,'INVALID_COLLECTION_TIME')
        self._normalized_api_key,self.key_shape=inspect_riot_key(self.api_key)
        receipt=dict(schema_version='pro.reference-collection.v1',status='BLOCKED_EXTERNAL',reason='RIOT_KEY_REQUIRED',
            roster_sha256=digest(c),roster_verification='USER_REPORT_NOT_NETWORK_VERIFIED',selection='USER_PRO_REFERENCE_ROSTER',tier='UNKNOWN',
            now=timestamp,window_start=timestamp-30*86400,position_share_threshold=float(position_share_threshold),
            threshold_policy='OPERATIONAL_REPLACEMENT_RULE_NOT_TACTICAL_ACCURACY',matches_per_account=matches_per_account,
            selections=[],failed_accounts=[],request_count=0,unique_recorded_matches=0,privacy='LOCAL_PRIVATE',limitations=deepcopy(LIMITATIONS),
            observed_http_status=None,user_key_expiry_attribution='NOT_APPLICABLE')
        from .pro_reference_cases import build_reference_cases
        self.reference_cases_data=build_reference_cases([],roster_sha256=receipt['roster_sha256'],retrieved_at=datetime.fromtimestamp(timestamp,timezone.utc).isoformat())
        if not self.key_shape['valid_shape']:return receipt
        cache=ProReferenceCache(private_directory);store=PostgameStore(cache.directory/'private'/'matches')
        self._raw_pairs={};self._ids_by_puuid={};self._player_observations={};selected=[]
        try:
            for input_role in ROLES:
                role=CANONICAL_ROLES[input_role];backup_index=0
                for primary in c['players'][input_role]:
                    player=primary;observations,reason,share=self._player(player,role,cache,store,receipt)
                    record=dict(role=role,primary_player=primary['name'],selected_player=None,replacements=[],position_share=share,status='UNKNOWN')
                    while reason in ('ACCOUNT_LOOKUP_FAILED','NO_RANKED_SOLO_420_WITHIN_30_DAYS','POSITION_SHARE_BELOW_OPERATIONAL_THRESHOLD') and backup_index<len(c['backups'][input_role]):
                        candidate=c['backups'][input_role][backup_index];backup_index+=1
                        record['replacements'].append(dict(from_player=player['name'],to_player=candidate['name'],reason=reason))
                        player=candidate;observations,reason,share=self._player(player,role,cache,store,receipt);record['position_share']=share
                    if reason:record.update(status='SKIPPED',reason=reason)
                    else:
                        record.update(status='SELECTED',selected_player=player['name'],reason=None)
                        selected.extend(observations)
                    receipt['selections'].append(record)
            receipt.update(status='READY' if selected else 'INSUFFICIENT_DATA',reason=None if selected else 'NO_ELIGIBLE_PLAYER_OBSERVATIONS')
        except CollectionBlocked as e:receipt.update(status='BLOCKED_EXTERNAL',reason=e.reason,observed_http_status=e.status_code,
            user_key_expiry_attribution='KEY_EXPIRED_PER_USER_RULE' if e.status_code in (401,403) else 'NOT_APPLICABLE')
        except ValueError:receipt.update(status='BLOCKED_EXTERNAL',reason='MALFORMED_PRIVATE_OR_RIOT_RESPONSE')
        receipt['failed_accounts']=cache.safe_summary()['failed_accounts'];receipt['request_count']=self.requests
        receipt['unique_recorded_matches']=len({o['match_sha256'] for o in selected})
        if selected:
            data=build_pro_reference(selected,roster_sha256=receipt['roster_sha256'],retrieved_at=datetime.fromtimestamp(timestamp,timezone.utc).isoformat())
            _write_private(cache.directory/'reference-data.json',data);receipt['reference_file']='reference-data.json';receipt['cohort_count']=len(data['cohorts'])
        self.reference_cases_data=build_reference_cases(selected,roster_sha256=receipt['roster_sha256'],retrieved_at=datetime.fromtimestamp(timestamp,timezone.utc).isoformat())
        _write_private(cache.directory/'reference-cases.json',self.reference_cases_data);receipt['reference_cases_file']='reference-cases.json'
        _write_private(cache.directory/'collection-receipt.json',receipt)
        return receipt

    def _player(self,player,role,cache,store,receipt):
        key=player['name']
        if key in self._player_observations:return self._player_observations[key]
        puuids=set()
        for index,riot_id in enumerate([player['riot_id'],*player.get('alt_riot_ids',[])]):
            stable='player:'+key+(':primary' if index==0 else ':alt:'+str(index))
            def lookup(url):return self._get(url,'ACCOUNT_V1_RIOT_ID',allow_missing=True)[0]
            puuid=cache.resolve(stable,riot_id,lookup)
            if puuid is not None:puuids.add(puuid)
        if not puuids:return [],'ACCOUNT_LOOKUP_FAILED',None
        observations={};recent={}
        for puuid in sorted(puuids):
            if puuid not in self._ids_by_puuid:
                url='https://asia.api.riotgames.com/lol/match/v5/matches/by-puuid/'+quote(puuid,safe='')+'/ids?queue=420&startTime='+str(receipt['window_start'])+'&endTime='+str(receipt['now'])+'&start=0&count='+str(receipt['matches_per_account'])
                ids=self._get(url,'MATCH_V5_IDS')[0]
                if not isinstance(ids,list) or len(ids)>receipt['matches_per_account'] or any(not isinstance(mid,str) or not re.fullmatch(r'KR_[0-9]+',mid) for mid in ids):raise CollectionBlocked('MALFORMED_RESPONSE')
                self._ids_by_puuid[puuid]=list(dict.fromkeys(ids))
            for mid in self._ids_by_puuid[puuid]:
                if mid not in self._raw_pairs:
                    if len(self._raw_pairs)>=self.limits['max_matches']:raise CollectionBlocked('MATCH_BUDGET_EXHAUSTED')
                    match=self._get('https://asia.api.riotgames.com/lol/match/v5/matches/'+mid,'MATCH_V5_MATCH',allow_missing=True)[0]
                    self._raw_pairs[mid]=dict(match=match,timeline=None)
                pair=self._raw_pairs[mid];match=pair['match']
                if match is None:continue
                if not isinstance(match,dict) or not isinstance(match.get('metadata'),dict) or match['metadata'].get('matchId')!=mid:raise CollectionBlocked('MALFORMED_RESPONSE')
                info=match.get('info') if isinstance(match,dict) else None
                if not isinstance(info,dict) or info.get('queueId')!=420 or info.get('mapId')!=11 or info.get('gameMode')!='CLASSIC':continue
                start=info.get('gameStartTimestamp')
                if type(start) not in (int,float) or not math.isfinite(start) or not receipt['window_start']<=start/1000<=receipt['now']:continue
                people=info.get('participants',[])
                owner=[p for p in people if isinstance(p,dict) and p.get('puuid')==puuid] if isinstance(people,list) else []
                if len(owner)!=1:raise CollectionBlocked('MALFORMED_RESPONSE')
                own=owner[0];assigned=ROLE_MAP.get(own.get('teamPosition')) if isinstance(own.get('teamPosition'),str) else None
                recent[(mid,own.get('participantId'))]=assigned
                if assigned!=role:continue
                if pair['timeline'] is None:
                    pair['timeline']=self._get('https://asia.api.riotgames.com/lol/match/v5/matches/'+mid+'/timeline','MATCH_V5_TIMELINE',allow_missing=True)[0]
                if pair['timeline'] is None:continue
                row=store.import_match(dict(match=match,timeline=pair['timeline'],participant_id=own.get('participantId'),source='REAL'))
                if row['role']!=role:continue
                detail=store.get_match(row['id'])
                mh=hashlib.sha256(mid.encode()).hexdigest()
                observations[(mh,own['participantId'])]=dict(match_sha256=mh,role=role,champion=row['champion'],patch=row['patch'],resources=detail['resources'],movement=detail['dependency']['samples'],contexts=detail['contexts'])
        known_positions=all(position in CANONICAL_ROLES.values() for position in recent.values())
        share=sum(position==role for position in recent.values())/len(recent) if recent and known_positions else None
        reason='NO_RANKED_SOLO_420_WITHIN_30_DAYS' if not recent else 'POSITION_ASSIGNMENT_UNVERIFIED' if not known_positions else 'POSITION_SHARE_BELOW_OPERATIONAL_THRESHOLD' if share<receipt['position_share_threshold'] else 'NO_USABLE_ROLE_TIMELINES' if not observations else None
        result=(list(observations.values()),reason,share);self._player_observations[key]=result;return result


def build_pro_reference(observations,*,roster_sha256,retrieved_at,sample_kind='REAL'):
    """Anonymous selected-player resource statistics, grouped independently by patch."""
    require(sample_kind in ('REAL','SYNTHETIC'))
    groups=defaultdict(lambda:defaultdict(lambda:defaultdict(list)));seen=set();hashes=set()
    for observation in observations:
        identity=(observation['match_sha256'],observation['role'],observation['champion'])
        if identity in seen:continue
        seen.add(identity);hashes.add(observation['match_sha256'])
        for resource in observation['resources']:
            for metric in ('gold','xp','cs'):
                value=resource.get(metric)
                if type(value) not in (int,float) or not math.isfinite(value):continue
                key=(observation['role'],observation['champion'],observation['patch'],metric)
                groups[key][resource['minute']][observation['match_sha256']].append(value)
    cohorts=[]
    for (role,champion,patch,metric),minutes in sorted(groups.items()):
        points=[_point(minute,[statistics.mean(values) for values in matches.values()],metric+'_delta',_policy(None)) for minute,matches in sorted(minutes.items())]
        cohorts.append(dict(position=role,champion=champion,patch=patch,metric=metric,comparison='PRO_ABSOLUTE_TOTAL',
            units={'gold':'gold total','xp':'XP total','cs':'CS total'}[metric],points=points))
    return validate_pro_reference(dict(schema_version='postgame.pro-reference.v1',sample_kind=sample_kind,
        status='READY' if any(p['visible'] for c in cohorts for p in c['points']) else 'INSUFFICIENT_DATA',selection='USER_PRO_REFERENCE_ROSTER',
        tier='UNKNOWN',roster_verification='USER_REPORT_NOT_NETWORK_VERIFIED',roster_sha256=roster_sha256,retrieved_at=retrieved_at,
        hashed_match_ids=sorted(hashes),match_count=len(hashes),cohorts=cohorts,limitations=deepcopy(LIMITATIONS)))


def validate_pro_reference(data):
    keys={'schema_version','sample_kind','status','selection','tier','roster_verification','roster_sha256','retrieved_at','hashed_match_ids','match_count','cohorts','limitations'}
    require(isinstance(data,dict) and set(data)==keys)
    d=deepcopy(data)
    require(d['schema_version']=='postgame.pro-reference.v1' and d['sample_kind'] in ('REAL','SYNTHETIC') and d['status'] in ('READY','INSUFFICIENT_DATA'))
    require(d['selection']=='USER_PRO_REFERENCE_ROSTER' and d['tier']=='UNKNOWN' and d['roster_verification']=='USER_REPORT_NOT_NETWORK_VERIFIED')
    require(isinstance(d['roster_sha256'],str) and re.fullmatch('[a-f0-9]{64}',d['roster_sha256']))
    require(isinstance(d['retrieved_at'],str) and 1<=len(d['retrieved_at'])<=100)
    require(isinstance(d['hashed_match_ids'],list) and all(isinstance(h,str) and re.fullmatch('[a-f0-9]{64}',h) for h in d['hashed_match_ids']))
    require(type(d['match_count']) is int and len(set(d['hashed_match_ids']))==len(d['hashed_match_ids'])==d['match_count'])
    require(isinstance(d['limitations'],list) and set(LIMITATIONS)<=set(d['limitations']) and all(isinstance(v,str) and len(v)<=4000 for v in d['limitations']))
    require(isinstance(d['cohorts'],list));identities=set()
    for c in d['cohorts']:
        require(isinstance(c,dict) and set(c)=={'position','champion','patch','metric','comparison','units','points'})
        require(c['position'] in CANONICAL_ROLES.values() and isinstance(c['champion'],str) and re.fullmatch('[A-Za-z][A-Za-z0-9]{0,39}',c['champion']))
        require(isinstance(c['patch'],str) and re.fullmatch(r'[0-9]+\.[0-9]+',c['patch']) and c['metric'] in ('gold','xp','cs'))
        require(c['comparison']=='PRO_ABSOLUTE_TOTAL' and c['units']=={'gold':'gold total','xp':'XP total','cs':'CS total'}[c['metric']])
        identity=(c['position'],c['champion'],c['patch'],c['metric']);require(identity not in identities);identities.add(identity)
        require(isinstance(c['points'],list));minutes=set()
        for p in c['points']:
            require(isinstance(p,dict) and set(p)=={'minute','n','mean','ci95','visible','omission_reason'})
            require(type(p['minute']) is int and p['minute']>=0 and p['minute'] not in minutes);minutes.add(p['minute'])
            require(type(p['n']) is int and 1<=p['n']<=d['match_count'] and type(p['mean']) in (int,float) and math.isfinite(p['mean']) and p['mean']>=0)
            require(type(p['visible']) is bool and isinstance(p['ci95'],dict) and set(p['ci95'])=={'low','high'})
            lo,hi=p['ci95']['low'],p['ci95']['high']
            if p['n']==1:require(lo is None and hi is None and not p['visible'] and p['omission_reason']=='N_LT_2')
            else:
                require(all(type(v) in (int,float) and math.isfinite(v) for v in (lo,hi)) and lo<=p['mean']<=hi)
                from .power_stats import student_t_critical
                half=(hi-lo)/2;sd=half*math.sqrt(p['n'])/student_t_critical(p['n']-1)
                visible=2*half<=sd+1e-9
                require(abs((lo+hi)/2-p['mean'])<=max(1e-9,abs(p['mean'])*1e-12) and p['visible']==visible and p['omission_reason']==(None if visible else 'CI_TOO_WIDE'))
    require(d['status']==('READY' if any(p['visible'] for c in d['cohorts'] for p in c['points']) else 'INSUFFICIENT_DATA'))
    return d

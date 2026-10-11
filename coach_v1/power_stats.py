"""Descriptive post-match aggregates, with no identities or tactical approvals.

Raw Riot response pairs exist only in the caller's private memory. Persistence
must pass validate_power_dataset; this module never writes raw responses.
"""
from collections import Counter, defaultdict
from copy import deepcopy
from functools import lru_cache
import hashlib
import math
import re
import statistics

POSITIONS = ('TOP', 'JUNGLE', 'MID', 'BOTTOM', 'SUPPORT')
METRICS = ('gold_delta', 'xp_delta', 'cs_delta')
TIERS = ('IRON','BRONZE','SILVER','GOLD','PLATINUM','EMERALD','DIAMOND','MASTER','GRANDMASTER','CHALLENGER')
ENDPOINTS = ('LEAGUE_V4_ENTRIES','LEAGUE_V4_MASTER','LEAGUE_V4_GRANDMASTER','LEAGUE_V4_CHALLENGER',
             'MATCH_V5_IDS','MATCH_V5_MATCH','MATCH_V5_TIMELINE')
LIMITATIONS = [
    'DESCRIPTIVE_NON_CAUSAL_NOT_FIGHTING_STRENGTH',
    'OPERATIONAL_PRECISION_NOT_VALIDATED_GAMEPLAY_THRESHOLD',
    'MATCH_INDEPENDENCE_AND_POPULATION_COVERAGE_UNVERIFIED',
    'LEAGUE_SEED_SELECTION_AND_SURVIVORSHIP_BIAS',
    'TIER_IS_CURRENT_LEAGUE_SEED_COHORT_NOT_ALL_PARTICIPANT_RANKS',
    'CONSTANT_SAMPLES_DO_NOT_PROVE_POPULATION_CERTAINTY',
    'LEVEL_MARKERS_FIRST_OBSERVED_FRAME_INTERVAL_CENSORED',
    'ITEM_MARKERS_BUILD_SELECTION_DESCRIPTIVE_NOT_CAUSAL',
    'ROLE_REFERENCE_IS_SAMPLED_POOLED_POSITION_POPULATION_NOT_ALL_PLAYERS',
    'ROLE_POPULATION_MATCH_INFLUENCE_LINEARIZATION_FIXED_EMPIRICAL_DENOMINATORS',
    'ROLE_POPULATION_RANDOM_CHAMPION_COVERAGE_AND_CI_CALIBRATION_UNVERIFIED',
]
REASONS = ('NO_ELIGIBLE_MATCHES','MISSING_API_KEY','UNAUTHORIZED_OR_EXPIRED_OR_UNSUPPORTED_PATH',
           'RATE_LIMIT_EXHAUSTED','REQUEST_BUDGET_EXHAUSTED','DEADLINE_EXHAUSTED',
           'NETWORK_FAILURE','RIOT_SERVER_FAILURE','HTTP_FAILURE','MALFORMED_RESPONSE',
           'UNSUPPORTED_LEAGUE_IDENTITY','NO_LEAGUE_ENTRIES','NO_ELIGIBLE_MATCHES',
           'ITEM_CATALOG_UNAVAILABLE','NOT_COLLECTED')
SOURCE_KEYS = {'provider','platform','regional','queue_id','map_id','tier','patch','window_start',
               'window_end','retrieved_at','sample_kind','endpoints','formula_version',
               'precision_policy','limitations','collection','item_catalog','population_reference'}


def _require(condition, reason='invalid power dataset'):
    if not condition:raise ValueError(reason)


def _number(value):
    return type(value) in (int,float) and math.isfinite(value)


def _integer(value, minimum=0):
    return type(value) is int and value >= minimum


def _keys(value, required, optional=()):
    _require(isinstance(value,dict) and set(required)<=set(value)<=set(required)|set(optional))


def _beta_fraction(a,b,x):
    # Modified Lentz evaluation of the incomplete beta continued fraction.
    tiny=1e-300;qab=a+b;qap=a+1;qam=a-1
    c=1.0;d=1-qab*x/qap;d=1/(d if abs(d)>tiny else tiny);h=d
    for m in range(1,401):
        aa=m*(b-m)*x/((qam+2*m)*(a+2*m))
        d=1+aa*d;d=d if abs(d)>tiny else tiny
        c=1+aa/c;c=c if abs(c)>tiny else tiny
        d=1/d;h*=d*c
        aa=-(a+m)*(qab+m)*x/((a+2*m)*(qap+2*m))
        d=1+aa*d;d=d if abs(d)>tiny else tiny
        c=1+aa/c;c=c if abs(c)>tiny else tiny
        d=1/d;change=d*c;h*=change
        if abs(change-1)<3e-14:return h
    raise ValueError('Student t numerical convergence failure')


def _regularized_beta(x,a,b):
    if x<=0:return 0.0
    if x>=1:return 1.0
    factor=math.exp(math.lgamma(a+b)-math.lgamma(a)-math.lgamma(b)
                    +a*math.log(x)+b*math.log1p(-x))
    if x<(a+1)/(a+b+2):return factor*_beta_fraction(a,b,x)/a
    return 1-factor*_beta_fraction(b,a,1-x)/b


@lru_cache(maxsize=1024)
def student_t_critical(df):
    """Numerical t(0.975,df), independently checked against the NIST table."""
    _require(_integer(df,1),'positive integer degrees of freedom required')
    def cdf(t):return 1-.5*_regularized_beta(df/(df+t*t),df/2,.5)
    low=0.0;high=1.0
    while cdf(high)<.975:high*=2
    for _ in range(70):
        mid=(low+high)/2
        if cdf(mid)<.975:low=mid
        else:high=mid
    return (low+high)/2


def _policy(limits):
    limits=deepcopy(limits)
    if limits is not None:
        _require(isinstance(limits,dict) and set(limits)<=set(METRICS))
        _require(all(_number(v) and v>0 for v in limits.values()),'invalid CI width override')
    return dict(version='CI_WIDTH_LE_SAMPLE_SD.v1',ci_width_limits=limits,
                units=dict(MATCHUP=dict(gold_delta='GOLD',xp_delta='XP',cs_delta='CS'),
                           ROLE_POPULATION=dict(gold_delta='GOLD_PER_MINUTE',xp_delta='XP_PER_MINUTE',cs_delta='CS_PER_MINUTE')),
                rationale='ESTIMATION_UNCERTAINTY_LE_EMPIRICAL_INDIVIDUAL_SPREAD')


def _source(source, limits=None, complete_item_ids=()):
    _require(isinstance(source,dict) and set(source)<=SOURCE_KEYS,'source fields not allowlisted')
    s=deepcopy(source)
    s['formula_version']='PAIRED_ROLE_DELTA_STUDENT_T95.v1'
    s['precision_policy']=_policy(limits)
    s['population_reference']=dict(kind='POOLED_SAME_POSITION_RATE_MEAN_CLUSTERED',
        formula_version='POOLED_ROLE_RATE_MATCH_INFLUENCE_T95.v1',position_participants_per_match=2,
        match_count=0,position_participant_count=0)
    s['limitations']=list(dict.fromkeys(LIMITATIONS+s.get('limitations',[])))
    ids=list(complete_item_ids)
    _require(all(_integer(i,1) for i in ids) and len(ids)==len(set(ids)),'invalid complete item IDs')
    if ids:
        if s.get('sample_kind')=='SYNTHETIC' and 'item_catalog' not in s:
            s['item_catalog']=dict(version='SYNTHETIC',sha256=hashlib.sha256(str(sorted(ids)).encode()).hexdigest(),
                url='https://example.org/synthetic-items',complete_item_ids=sorted(ids),
                classification='PINNED_COMPLETE_NONCONSUMABLE.v1')
        _require('item_catalog' in s and sorted(s['item_catalog']['complete_item_ids'])==sorted(ids),
                 'complete item IDs require pinned catalog lineage')
    return s


def empty_power_dataset(reason='NO_ELIGIBLE_MATCHES',status='INSUFFICIENT_DATA',source=None):
    if source is None:
        source=dict(provider='RIOT_API',platform='KR',regional='ASIA',queue_id=420,map_id=11,
                    tier='GOLD',patch=None,window_start=None,window_end=None,retrieved_at=None,
                    sample_kind='REAL',endpoints=[])
    s=_source(source);_require(reason in REASONS)
    s['limitations'].append(reason)
    return validate_power_dataset(dict(schema_version='pregame.power-data.v1',status=status,source=s,
        samples=dict(real_matches=0,synthetic_matches=0,hashed_match_ids=[]),cohorts=[],coaching_accuracy=None))


def _point(minute,values,metric,policy):
    n=len(values);mean=statistics.mean(values)
    if n<2:return dict(minute=minute,n=n,mean=mean,ci95=dict(low=None,high=None),
                       visible=False,omission_reason='N_LT_2')
    sd=statistics.stdev(values);half=student_t_critical(n-1)*sd/math.sqrt(n)
    maximum=(policy['ci_width_limits'] or {}).get(metric,sd)
    visible=2*half<=maximum+1e-12
    return dict(minute=minute,n=n,mean=mean,ci95=dict(low=mean-half,high=mean+half),
                visible=visible,omission_reason=None if visible else 'CI_TOO_WIDE')


def _quantile(values,p):
    ordered=sorted(values);index=(len(ordered)-1)*p;low=math.floor(index);high=math.ceil(index)
    return ordered[low]+(ordered[high]-ordered[low])*(index-low)


def _markers(observations):
    result=[]
    for level in (2,3,6,11,16):
        values=[o['levels'][level] for o in observations if level in o['levels']]
        if values:result.append(_marker(values,kind='LEVEL',level=level,item_id=None,item_order=None))
    for order in (1,2):
        choices=[o['items'][order-1] for o in observations if len(o['items'])>=order]
        if choices:
            counts=Counter(item for item,_ in choices)
            item=min(counts,key=lambda i:(-counts[i],i))
            values=[time for item_id,time in choices if item_id==item]
            result.append(_marker(values,kind='ITEM',level=None,item_id=item,item_order=order))
    return result


def _marker(values,**fields):
    return dict(fields,n=len(values),median_minute=_quantile(values,.5),
                q1_minute=_quantile(values,.25),q3_minute=_quantile(values,.75),label='DESCRIPTIVE_NON_CAUSAL')


def _observation(pid,frames,complete_ids):
    levels={};items=[]
    for frame in frames:
        timestamp=frame.get('timestamp');pf=frame.get('participantFrames',{}).get(str(pid),{})
        if _number(timestamp) and timestamp>=0 and _integer(pf.get('level'),1):
            for level in (2,3,6,11,16):
                if pf['level']>=level and level not in levels:levels[level]=timestamp/60000
        for event in frame.get('events',[]):
            if event.get('participantId')!=pid:continue
            time=event.get('timestamp')
            if not _number(time) or time<0:continue
            if event.get('type')=='ITEM_PURCHASED' and event.get('itemId') in complete_ids:
                items.append((event['itemId'],time/60000))
            elif event.get('type')=='ITEM_UNDO':
                before=event.get('beforeId')
                for index in range(len(items)-1,-1,-1):
                    if items[index][0]==before:items.pop(index);break
                after=event.get('afterId')
                if after in complete_ids:items.append((after,time/60000))
    return dict(levels=levels,items=items[:2])


def build_power_dataset(pairs,*,source,ci_width_limits=None,complete_item_ids=()):
    """Aggregate deduplicated complete official response pairs in private memory."""
    s=_source(source,ci_width_limits,complete_item_ids)
    validate_power_dataset(dict(schema_version='pregame.power-data.v1',status='INSUFFICIENT_DATA',source=s,
        samples=dict(real_matches=0,synthetic_matches=0,hashed_match_ids=[]),cohorts=[],coaching_accuracy=None))
    groups=defaultdict(lambda:defaultdict(list))
    observations=defaultdict(list);hashes=set();complete=set(complete_item_ids)
    populations=defaultdict(lambda:defaultdict(list))
    for pair in pairs:
        if not isinstance(pair,dict):continue
        match=pair.get('match',{});timeline=pair.get('timeline',{})
        if not isinstance(match,dict) or not isinstance(timeline,dict):continue
        metadata=match.get('metadata',{});mid=metadata.get('matchId')
        if not isinstance(mid,str) or not mid.startswith('KR_') or timeline.get('metadata',{}).get('matchId')!=mid:continue
        info=match.get('info',{})
        if not isinstance(info,dict) or not isinstance(info.get('gameVersion'),str):continue
        version=info['gameVersion'].split('.')
        if len(version)<2 or not all(v.isdigit() for v in version[:2]):continue
        patch='.'.join(version[:2])
        if info.get('queueId')!=420 or info.get('mapId')!=11 or info.get('gameMode')!='CLASSIC':continue
        if s.get('patch') is not None and patch!=s['patch']:continue
        started=info.get('gameStartTimestamp')
        if not _number(started):continue
        if s.get('window_start') is not None and started/1000<s['window_start']:continue
        if s.get('window_end') is not None and started/1000>s['window_end']:continue
        frames=timeline.get('info',{}).get('frames',[])
        if not isinstance(frames,list) or not frames:continue
        frame_times=[f.get('timestamp') for f in frames if isinstance(f,dict)]
        if len(frame_times)!=len(frames) or not all(_number(t) and t>=0 for t in frame_times):continue
        if frame_times!=sorted(set(frame_times)):continue
        if _number(info.get('gameDuration')) and max(frame_times)>info['gameDuration']*1000:continue
        people=info.get('participants',[]);roles={};invalid=False
        for p in people:
            key=(p.get('teamId'),p.get('teamPosition'))
            if key[0] not in (100,200) or key[1] not in POSITIONS:continue
            if key in roles:invalid=True;break
            name=p.get('championName')
            if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9]{0,39}',name):invalid=True;break
            if not _integer(p.get('participantId'),1):invalid=True;break
            roles[key]=p
        if invalid or len(roles)!=10 or len({p['participantId'] for p in roles.values()})!=10:continue
        sha=hashlib.sha256(mid.encode()).hexdigest()
        if sha in hashes:continue
        if s.get('sample_kind')=='REAL' and not re.fullmatch(r'KR_[0-9]+',mid):continue
        if s.get('patch') is None:s['patch']=patch
        hashes.add(sha)
        match_groups=defaultdict(lambda:defaultdict(list));match_observations={}
        for (team,position),p in roles.items():
            opponent=roles[(300-team,position)];pid=p['participantId'];enemy_id=opponent['participantId']
            for comparison,enemy in (('MATCHUP',opponent['championName']),('ROLE_POPULATION',None)):
                base=(p['championName'],position,patch,s['tier'],comparison,enemy)
                # Ranked draft has unique champions; if a mirror fixture is
                # supplied, keep one marker record and cluster point estimates
                # by match rather than pretending two players are two matches.
                match_observations.setdefault(base,_observation(pid,frames,complete))
                for frame in frames:
                    own=frame.get('participantFrames',{}).get(str(pid),{})
                    opposing=frame.get('participantFrames',{}).get(str(enemy_id),{})
                    minute=frame['timestamp']/60000
                    for metric,fields in (('gold_delta',('totalGold',)),('xp_delta',('xp',)),
                                          ('cs_delta',('minionsKilled','jungleMinionsKilled'))):
                        if all(_number(side.get(field)) for side in (own,opposing) for field in fields):
                            own_total=sum(own[f] for f in fields);enemy_total=sum(opposing[f] for f in fields)
                            if comparison=='ROLE_POPULATION':
                                if minute>0 and team==100:
                                    populations[(position,patch,s['tier'],metric)][minute].append(
                                        [(p['championName'],own_total/minute),(opponent['championName'],enemy_total/minute)])
                            else:match_groups[base+(metric,)][minute].append(own_total-enemy_total)
        for key,minutes in match_groups.items():
            for minute,values in minutes.items():groups[key][minute].append(statistics.mean(values))
        for key,observation in match_observations.items():observations[key].append(observation)
    cohorts=[]
    for key,minutes in sorted(groups.items(),key=lambda item:str(item[0])):
        champion,position,patch,tier,comparison,enemy,metric=key
        points=[_point(t,values,metric,s['precision_policy']) for t,values in sorted(minutes.items())]
        cohorts.append(dict(champion=champion,position=position,patch=patch,tier=tier,comparison=comparison,
            opponent_champion=enemy,metric=metric,points=points,markers=_markers(observations[key[:-1]])))
    for base in sorted(observations,key=str):
        champion,position,patch,tier,comparison,enemy=base
        if comparison!='ROLE_POPULATION':continue
        for metric in METRICS:
            points=[]
            for minute,matches in sorted(populations[(position,patch,tier,metric)].items()):
                champion_rates=[rate for participants in matches for name,rate in participants if name==champion]
                k=len(champion_rates);m=len(matches)
                if not k:continue
                reference=statistics.mean(rate for participants in matches for _,rate in participants)
                champion_mean=statistics.mean(champion_rates)
                contributions=[(m/k)*sum(rate for name,rate in participants if name==champion)
                               -statistics.mean(rate for _,rate in participants) for participants in matches]
                point=_point(minute,contributions,metric,s['precision_policy'])
                point.update(champion_n=k,reference_n=2*m,champion_mean=champion_mean,reference_mean=reference)
                if k<2 and m>=2:point.update(visible=False,omission_reason='CHAMPION_N_LT_2')
                points.append(point)
            if points:cohorts.append(dict(champion=champion,position=position,patch=patch,tier=tier,
                comparison=comparison,opponent_champion=None,metric=metric,points=points,
                markers=_markers(observations[base])))
    count=len(hashes);real=count if s['sample_kind']=='REAL' else 0;synthetic=count-real
    s['population_reference']['match_count']=count
    s['population_reference']['position_participant_count']=count*2
    status='READY' if any(p['visible'] for c in cohorts for p in c['points']) else 'INSUFFICIENT_DATA'
    return validate_power_dataset(dict(schema_version='pregame.power-data.v1',status=status,source=s,
        samples=dict(real_matches=real,synthetic_matches=synthetic,hashed_match_ids=sorted(hashes)),
        cohorts=cohorts,coaching_accuracy=None))


def validate_power_dataset(dataset):
    try:return _validate_power_dataset(dataset)
    except (TypeError,KeyError,AttributeError,OverflowError):
        raise ValueError('invalid power dataset') from None


def _validate_power_dataset(dataset):
    """Fail closed on unknown fields, raw IDs, nonfinite values, and mixed lineage."""
    d=deepcopy(dataset)
    _keys(d,{'schema_version','status','source','samples','cohorts','coaching_accuracy'})
    _require(d['schema_version']=='pregame.power-data.v1' and d['status'] in ('READY','INSUFFICIENT_DATA','BLOCKED_EXTERNAL'))
    _require(d['coaching_accuracy'] is None)
    s=d['source'];_keys(s,SOURCE_KEYS-{'collection','item_catalog','population_reference'},
                      {'collection','item_catalog','population_reference'})
    _require(s['sample_kind'] in ('REAL','SYNTHETIC') and s['provider']==('RIOT_API' if s['sample_kind']=='REAL' else 'SYNTHETIC'))
    _require(s['platform']=='KR' and s['regional']=='ASIA' and s['queue_id']==420 and s['map_id']==11)
    _require(s['tier'] in TIERS and (s['patch'] is None or isinstance(s['patch'],str) and re.fullmatch(r'[0-9]+\.[0-9]+',s['patch'])))
    _require(all(s[k] is None or _integer(s[k]) for k in ('window_start','window_end')))
    _require(s['window_start'] is None or s['window_end'] is None or s['window_start']<=s['window_end'])
    _require(s['retrieved_at'] is None or isinstance(s['retrieved_at'],str) and re.fullmatch(r'[0-9T:+.Z-]{10,40}',s['retrieved_at']))
    _require(isinstance(s['endpoints'],list) and all(e in ENDPOINTS for e in s['endpoints']))
    _require(s['formula_version']=='PAIRED_ROLE_DELTA_STUDENT_T95.v1')
    policy=s['precision_policy'];_keys(policy,{'version','ci_width_limits','units','rationale'})
    _require(policy==_policy(policy['ci_width_limits']))
    _require(isinstance(s['limitations'],list) and set(LIMITATIONS)<=set(s['limitations'])
             and all(x in LIMITATIONS or x in REASONS for x in s['limitations']))
    if 'collection' in s:
        c=s['collection'];_keys(c,{'key_kind','status_code','reason','request_count','retry_count','limits'},{'division'})
        _require(c['key_kind']=='UNKNOWN' and (c['status_code'] is None or _integer(c['status_code'],100) and c['status_code']<=599))
        _require(c['reason'] is None or c['reason'] in REASONS)
        _require('division' not in c or c['division'] is None or c['division'] in ('I','II','III','IV'))
        _require(_integer(c['request_count']) and _integer(c['retry_count']))
        _keys(c['limits'],{'max_requests','max_matches','max_pages','max_players','max_retries','deadline_seconds'})
        _require(all(_integer(v,1) for k,v in c['limits'].items() if k!='max_retries') and _integer(c['limits']['max_retries']))
    if 'item_catalog' in s:
        cat=s['item_catalog'];_keys(cat,{'version','sha256','url','complete_item_ids','classification'})
        _require(isinstance(cat['version'],str) and re.fullmatch(r'(?:[0-9]+\.[0-9]+\.[0-9]+|SYNTHETIC)',cat['version']))
        _require(isinstance(cat['sha256'],str) and re.fullmatch(r'[a-f0-9]{64}',cat['sha256']))
        expected='https://ddragon.leagueoflegends.com/cdn/'+cat['version']+'/data/en_US/item.json'
        _require(cat['url']==expected or s['sample_kind']=='SYNTHETIC' and cat['url']=='https://example.org/synthetic-items')
        _require(s['sample_kind']=='SYNTHETIC' or s['patch']=='.'.join(cat['version'].split('.')[:2]))
        _require(cat['classification']=='PINNED_COMPLETE_NONCONSUMABLE.v1')
        _require(isinstance(cat['complete_item_ids'],list) and all(_integer(i,1) for i in cat['complete_item_ids'])
                 and len(cat['complete_item_ids'])==len(set(cat['complete_item_ids'])))
    samples=d['samples'];_keys(samples,{'real_matches','synthetic_matches','hashed_match_ids'})
    _require(_integer(samples['real_matches']) and _integer(samples['synthetic_matches']))
    hashes=samples['hashed_match_ids'];_require(isinstance(hashes,list) and len(hashes)==len(set(hashes)))
    _require(all(isinstance(h,str) and re.fullmatch(r'[a-f0-9]{64}',h) for h in hashes))
    count=samples['real_matches']+samples['synthetic_matches'];_require(count==len(hashes))
    _require(samples['synthetic_matches']==0 if s['sample_kind']=='REAL' else samples['real_matches']==0)
    if 'population_reference' in s:
        reference=s['population_reference']
        _keys(reference,{'kind','formula_version','position_participants_per_match','match_count','position_participant_count'})
        _require(reference==dict(kind='POOLED_SAME_POSITION_RATE_MEAN_CLUSTERED',
            formula_version='POOLED_ROLE_RATE_MATCH_INFLUENCE_T95.v1',position_participants_per_match=2,
            match_count=count,position_participant_count=count*2))
    _require(isinstance(d['cohorts'],list));identities=set()
    for c in d['cohorts']:
        _keys(c,{'champion','position','patch','tier','comparison','opponent_champion','metric','points','markers'})
        _require(isinstance(c['champion'],str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9]{0,39}',c['champion']))
        _require(c['position'] in POSITIONS and c['patch']==s['patch'] and c['tier']==s['tier'] and c['metric'] in METRICS)
        _require(c['comparison'] in ('MATCHUP','ROLE_POPULATION'))
        _require(c['opponent_champion'] is None if c['comparison']=='ROLE_POPULATION' else
                 isinstance(c['opponent_champion'],str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9]{0,39}',c['opponent_champion']))
        key=tuple(c[k] for k in ('champion','position','patch','tier','comparison','opponent_champion','metric'))
        _require(key not in identities);identities.add(key)
        _require(isinstance(c['points'],list));times=set()
        for p in c['points']:
            extra={'reference_n','champion_n','champion_mean','reference_mean'}
            _keys(p,{'minute','n','mean','ci95','visible','omission_reason'},extra)
            _require(_number(p['minute']) and p['minute']>=0 and p['minute'] not in times);times.add(p['minute'])
            _require(_integer(p['n'],1) and p['n']<=count and _number(p['mean']) and type(p['visible']) is bool)
            if c['comparison']=='ROLE_POPULATION':
                _require(extra<=set(p) and 'population_reference' in s and p['reference_n']==p['n']*2 and p['minute']>0)
                _require(_integer(p['champion_n'],1) and p['champion_n']<=p['reference_n'])
                _require(_number(p['champion_mean']) and _number(p['reference_mean'])
                    and abs(p['champion_mean']-p['reference_mean']-p['mean'])<1e-8)
            else:_require(not extra&set(p))
            _keys(p['ci95'],{'low','high'});low=p['ci95']['low'];high=p['ci95']['high']
            if p['n']<2:_require(low is None and high is None and not p['visible'] and p['omission_reason']=='N_LT_2')
            else:
                _require(_number(low) and _number(high) and low<=p['mean']<=high)
                half=(high-low)/2
                _require(abs((low+high)/2-p['mean'])<=max(1e-9,abs(p['mean'])*1e-12))
                sd=half*math.sqrt(p['n'])/student_t_critical(p['n']-1)
                maximum=(policy['ci_width_limits'] or {}).get(c['metric'],sd)
                eligible=2*half<=maximum+1e-9
                if c['comparison']=='ROLE_POPULATION' and p['champion_n']<2:eligible=False
                _require(p['visible']==eligible)
                omission='CHAMPION_N_LT_2' if c['comparison']=='ROLE_POPULATION' and p['champion_n']<2 else 'CI_TOO_WIDE'
                _require(p['omission_reason'] is None if p['visible'] else p['omission_reason']==omission)
        _require(isinstance(c['markers'],list))
        for m in c['markers']:
            _keys(m,{'kind','level','item_id','item_order','n','median_minute','q1_minute','q3_minute','label'})
            _require(m['label']=='DESCRIPTIVE_NON_CAUSAL' and _integer(m['n'],1) and m['n']<=count)
            _require(all(_number(m[k]) and m[k]>=0 for k in ('median_minute','q1_minute','q3_minute')))
            _require(m['q1_minute']<=m['median_minute']<=m['q3_minute'])
            if m['kind']=='LEVEL':_require(m['level'] in (2,3,6,11,16) and m['item_id'] is None and m['item_order'] is None)
            else:_require(m['kind']=='ITEM' and m['level'] is None and m['item_order'] in (1,2)
                          and 'item_catalog' in s and m['item_id'] in s['item_catalog']['complete_item_ids'])
    visible=any(p['visible'] for c in d['cohorts'] for p in c['points'])
    _require(d['status']!='READY' or visible)
    _require(d['status']!='INSUFFICIENT_DATA' or not visible)
    return d


def select_power_view(dataset,champion,position,patch,tier,opponent_champion=None):
    """Choose eligible matchup then role population independently at each point."""
    d=validate_power_dataset(dataset);points=[];markers=[];reasons=[]
    candidates=[c for c in d['cohorts'] if (c['champion'],c['position'],c['patch'],c['tier'])==(champion,position,patch,tier)]
    if d['status']=='BLOCKED_EXTERNAL':candidates=[];reasons.append('BLOCKED_EXTERNAL')
    for metric in METRICS:
        population=next((c for c in candidates if c['metric']==metric and c['comparison']=='ROLE_POPULATION'),None)
        matchup=next((c for c in candidates if c['metric']==metric and c['comparison']=='MATCHUP'
                      and c['opponent_champion']==opponent_champion),None)
        alltimes=sorted({p['minute'] for c in (matchup,population) if c for p in c['points']})
        for minute in alltimes:
            selected=None
            for c in (matchup,population):
                p=next((p for p in c['points'] if p['minute']==minute and p['visible']),None) if c else None
                if p is not None:selected=dict(p,metric=metric,comparison=c['comparison'],opponent_champion=c['opponent_champion']);break
            if selected is None:reasons.append('INSUFFICIENT_AT_MINUTE:'+str(int(minute) if minute==int(minute) else minute)+':'+metric)
            else:points.append(selected)
        c=matchup if matchup and any(p['visible'] for p in matchup['points']) else population
        if c:
            for m in c['markers']:
                mark=dict(m,champion=champion,comparison=c['comparison'],opponent_champion=c['opponent_champion'])
                if mark not in markers:markers.append(mark)
    if not candidates:reasons.append('COHORT_UNAVAILABLE')
    return dict(status='KNOWN' if points else 'UNKNOWN',points=points,markers=markers,
                reasons=list(dict.fromkeys(reasons)),source=d['source'],samples=d['samples'])

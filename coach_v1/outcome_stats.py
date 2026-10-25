"""Anonymous ending-duration outcomes; no fighting-strength or tactical claims.

Only already-fetched official match/timeline pairs in private caller memory are
read. Public persistence requires the strict validator below. No raw response,
player identifier, or unhashed match identifier leaves this module.
"""
from collections import defaultdict
from copy import deepcopy
from datetime import datetime
import hashlib
import math
import re
from statistics import NormalDist

from .power_stats import ENDPOINTS, POSITIONS, TIERS

BASE_SOURCE_KEYS={'provider','platform','regional','queue_id','map_id','tier','patch',
                  'window_start','window_end','retrieved_at','sample_kind','endpoints'}
SOURCE_KEYS=BASE_SOURCE_KEYS|{'formula_version','duration_bin_policy','mirror_policy',
                            'result_policy','limitations'}
DURATION_BIN_POLICY={'kind':'ENDING_GAME_DURATION_FLOOR_MINUTE','width_seconds':60,'unit':'SECONDS'}
LIMITATIONS=(
    'ENDING_DURATION_CONDITIONAL_OUTCOME_NOT_STRENGTH',
    'CURRENT_LEAGUE_SEED_NOT_HISTORICAL_PARTICIPANT_TIER',
    'CONVENIENCE_SAMPLE_INDEPENDENCE_AND_COVERAGE_UNVERIFIED',
    'N_ONE_COMPUTABLE_NOT_SAMPLE_SUFFICIENCY',
    'PAIRED_TIMELINE_METADATA_ONLY_NO_FRAME_GATE',
    'REPORTED_DURATION_SECONDS_POST_11_20_ONLY',
    'EARLY_TERMINATION_OR_REMAKE_CLASSIFICATION_UNVERIFIED',
    'MIRRORED_CHAMPION_ROLE_TRIALS_EXCLUDED',
)
ROLE_MAP={'TOP':'TOP','JUNGLE':'JUNGLE','MIDDLE':'MID','MID':'MID',
          'BOTTOM':'BOTTOM','UTILITY':'SUPPORT','SUPPORT':'SUPPORT'}


def _require(condition):
    if not condition:raise ValueError('invalid outcome dataset')


def _keys(value,keys):
    _require(isinstance(value,dict) and set(value)==set(keys))


def _integer(value,minimum=0):
    return type(value) is int and value>=minimum


def _number(value):
    return type(value) in (int,float) and math.isfinite(value)


def _champion(value):
    return isinstance(value,str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9]{0,39}',value) is not None


def _hash(value):
    return isinstance(value,str) and re.fullmatch(r'[0-9a-f]{64}',value) is not None


def _wilson(wins,n):
    p=wins/n;z=NormalDist().inv_cdf(.975);denominator=1+z*z/n
    center=(p+z*z/(2*n))/denominator
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/denominator
    # Floating subtraction at p=0 can leave a tiny positive lower bound.
    # Keep the exact binomial proportion inside its Wilson interval; the
    # strict dataset validator remains unchanged.
    return {'low':min(p,max(0.,center-half)),'high':max(p,min(1.,center+half))}


def _source(source):
    _keys(source,BASE_SOURCE_KEYS)
    result=deepcopy(source)
    result.update(formula_version='WILSON_SCORE_95.v1',duration_bin_policy=deepcopy(DURATION_BIN_POLICY),
                  mirror_policy='EXCLUDE_SAME_CHAMPION_SAME_ROLE_BOTH_TEAMS.v1',
                  result_policy='PARTICIPANT_TEAM_WIN_BOOLEAN_AGREEMENT.v1',limitations=list(LIMITATIONS))
    return result


def _empty(source):
    return {'schema_version':'pregame.outcome-data.v1','status':'INSUFFICIENT_DATA','source':source,
            'samples':{'real_matches':0,'synthetic_matches':0,'hashed_match_ids':[]},
            'cohorts':[],'coaching_accuracy':None}


def _eligible_pair(pair,source):
    """Read only fields with supported result/duration semantics, or withhold."""
    if not isinstance(pair,dict):return None
    match=pair.get('match');timeline=pair.get('timeline')
    if not isinstance(match,dict) or not isinstance(timeline,dict):return None
    metadata=match.get('metadata');timeline_metadata=timeline.get('metadata')
    if not isinstance(metadata,dict) or not isinstance(timeline_metadata,dict):return None
    mid=metadata.get('matchId')
    if not isinstance(mid,str) or not mid.startswith('KR_') or timeline_metadata.get('matchId')!=mid:return None
    if source['sample_kind']=='REAL' and not re.fullmatch(r'KR_[0-9]+',mid):return None
    info=match.get('info')
    if not isinstance(info,dict):return None
    if type(info.get('queueId')) is not int or info['queueId']!=420:return None
    if type(info.get('mapId')) is not int or info['mapId']!=11 or info.get('gameMode')!='CLASSIC':return None
    version=info.get('gameVersion')
    if not isinstance(version,str) or not re.fullmatch(r'[0-9]+\.[0-9]+(?:\.[0-9]+)*',version):return None
    patch='.'.join(version.split('.')[:2]);patch_numbers=tuple(int(x) for x in patch.split('.'))
    if patch_numbers<(11,20) or source['patch'] is not None and patch!=source['patch']:return None
    started=info.get('gameStartTimestamp');ended=info.get('gameEndTimestamp');duration=info.get('gameDuration')
    if not _integer(started) or not _integer(ended) or ended<started or not _integer(duration,1):return None
    if source['window_start'] is not None and started/1000<source['window_start']:return None
    if source['window_end'] is not None and started/1000>source['window_end']:return None
    teams=info.get('teams');people=info.get('participants')
    if not isinstance(teams,list) or len(teams)!=2 or not isinstance(people,list) or len(people)!=10:return None
    wins={}
    for team in teams:
        if not isinstance(team,dict):return None
        tid=team.get('teamId');win=team.get('win')
        if type(tid) is not int or tid not in (100,200) or tid in wins or type(win) is not bool:return None
        wins[tid]=win
    if set(wins)!={100,200} or wins[100]==wins[200]:return None
    roles={};ids=set()
    for person in people:
        if not isinstance(person,dict):return None
        tid=person.get('teamId');raw_role=person.get('teamPosition')
        role=ROLE_MAP.get(raw_role) if isinstance(raw_role,str) else None
        participant_id=person.get('participantId');champion=person.get('championName')
        if type(tid) is not int or tid not in wins or role not in POSITIONS:return None
        if not _integer(participant_id,1) or participant_id in ids or not _champion(champion):return None
        if type(person.get('win')) is not bool or person['win']!=wins[tid]:return None
        if (tid,role) in roles:return None
        roles[(tid,role)]=(champion,wins[tid]);ids.add(participant_id)
    if len(roles)!=10:return None
    return mid,patch,duration//60,roles


def build_outcome_dataset(pairs,*,source):
    """One binary trial per match/cohort; absent/conflicting results withheld."""
    s=_source(source)
    validate_outcome_dataset(_empty(s))
    groups=defaultdict(lambda:defaultdict(dict));hashes=set()
    for pair in pairs:
        eligible=_eligible_pair(pair,s)
        if eligible is None:continue
        mid,patch,minute,roles=eligible;sha=hashlib.sha256(mid.encode()).hexdigest()
        if sha in hashes:continue
        nonmirrored=[role for role in POSITIONS if roles[(100,role)][0]!=roles[(200,role)][0]]
        if not nonmirrored:continue
        if s['patch'] is None:s['patch']=patch
        hashes.add(sha)
        for role in nonmirrored:
            for team,opposing in ((100,200),(200,100)):
                champion,won=roles[(team,role)];opponent=roles[(opposing,role)][0]
                for comparison,other in (('CHAMPION_ROLE',None),('MATCHUP',opponent)):
                    key=(champion,role,patch,s['tier'],comparison,other)
                    groups[key][minute][sha]=won
    cohorts=[]
    for key,bins in sorted(groups.items(),key=lambda item:tuple('' if x is None else x for x in item[0])):
        champion,position,patch,tier,comparison,opponent=key;points=[]
        for minute,trials in sorted(bins.items()):
            n=len(trials);wins=sum(trials.values())
            points.append({'minute':minute,'n':n,'wins':wins,'win_rate':wins/n,'ci95':_wilson(wins,n),
                           'input_match_hashes':sorted(trials)})
        cohorts.append({'champion':champion,'position':position,'patch':patch,'tier':tier,
                        'comparison':comparison,'opponent_champion':opponent,'points':points})
    dataset=_empty(s);dataset['cohorts']=cohorts
    dataset['status']='READY' if cohorts else 'INSUFFICIENT_DATA'
    dataset['samples']={'real_matches':len(hashes) if s['sample_kind']=='REAL' else 0,
                        'synthetic_matches':len(hashes) if s['sample_kind']=='SYNTHETIC' else 0,
                        'hashed_match_ids':sorted(hashes)}
    return validate_outcome_dataset(dataset)


def validate_outcome_dataset(dataset):
    """Read-safe anonymous output allowlist, source/count/hash/formula binding."""
    d=deepcopy(dataset)
    _keys(d,{'schema_version','status','source','samples','cohorts','coaching_accuracy'})
    _require(d['schema_version']=='pregame.outcome-data.v1')
    _require(d['status'] in ('READY','INSUFFICIENT_DATA','BLOCKED_EXTERNAL') and d['coaching_accuracy'] is None)
    s=d['source'];_keys(s,SOURCE_KEYS)
    _require(s['sample_kind'] in ('REAL','SYNTHETIC'))
    _require(s['provider']==('RIOT_API' if s['sample_kind']=='REAL' else 'SYNTHETIC'))
    _require(s['platform']=='KR' and s['regional']=='ASIA')
    _require(type(s['queue_id']) is int and s['queue_id']==420 and type(s['map_id']) is int and s['map_id']==11)
    _require(s['tier'] in TIERS)
    _require(s['patch'] is None or isinstance(s['patch'],str) and re.fullmatch(r'[0-9]+\.[0-9]+',s['patch']) is not None)
    _require(all(s[k] is None or _integer(s[k]) for k in ('window_start','window_end')))
    _require(s['window_start'] is None or s['window_end'] is None or s['window_start']<=s['window_end'])
    if s['retrieved_at'] is not None:
        _require(isinstance(s['retrieved_at'],str) and len(s['retrieved_at'])<=64)
        try:parsed=datetime.fromisoformat(s['retrieved_at'].replace('Z','+00:00'))
        except (ValueError,TypeError):raise ValueError('invalid outcome dataset') from None
        _require(parsed.tzinfo is not None)
    _require(isinstance(s['endpoints'],list) and all(isinstance(x,str) and x in ENDPOINTS for x in s['endpoints']))
    _require(len(s['endpoints'])==len(set(s['endpoints'])))
    _require(s['formula_version']=='WILSON_SCORE_95.v1')
    _keys(s['duration_bin_policy'],DURATION_BIN_POLICY)
    _require(s['duration_bin_policy']==DURATION_BIN_POLICY and type(s['duration_bin_policy']['width_seconds']) is int)
    _require(s['mirror_policy']=='EXCLUDE_SAME_CHAMPION_SAME_ROLE_BOTH_TEAMS.v1')
    _require(s['result_policy']=='PARTICIPANT_TEAM_WIN_BOOLEAN_AGREEMENT.v1')
    _require(isinstance(s['limitations'],list) and all(isinstance(x,str) and x in LIMITATIONS for x in s['limitations']))
    _require(len(s['limitations'])==len(set(s['limitations'])) and set(s['limitations'])==set(LIMITATIONS))
    samples=d['samples'];_keys(samples,{'real_matches','synthetic_matches','hashed_match_ids'})
    _require(_integer(samples['real_matches']) and _integer(samples['synthetic_matches']))
    hashes=samples['hashed_match_ids'];_require(isinstance(hashes,list) and all(_hash(x) for x in hashes))
    _require(len(hashes)==len(set(hashes)) and len(hashes)==samples['real_matches']+samples['synthetic_matches'])
    _require(samples['synthetic_matches']==0 if s['sample_kind']=='REAL' else samples['real_matches']==0)
    _require(not hashes or s['patch'] is not None)
    if hashes:
        _require(tuple(int(x) for x in s['patch'].split('.'))>=(11,20))
        _require({'MATCH_V5_MATCH','MATCH_V5_TIMELINE'}<=set(s['endpoints']))
    cohorts=d['cohorts'];_require(isinstance(cohorts,list));cohort_keys=set();used=set();indexed={};hash_minutes={}
    for cohort in cohorts:
        _keys(cohort,{'champion','position','patch','tier','comparison','opponent_champion','points'})
        _require(_champion(cohort['champion']) and cohort['position'] in POSITIONS)
        _require(cohort['patch']==s['patch'] and cohort['tier']==s['tier'])
        comparison=cohort['comparison'];opponent=cohort['opponent_champion']
        _require(comparison in ('MATCHUP','CHAMPION_ROLE'))
        _require(opponent is None if comparison=='CHAMPION_ROLE' else _champion(opponent) and opponent!=cohort['champion'])
        key=(cohort['champion'],cohort['position'],cohort['patch'],cohort['tier'],comparison,opponent)
        _require(key not in cohort_keys);cohort_keys.add(key)
        points=cohort['points'];_require(isinstance(points,list) and bool(points));minutes=set();cohort_hashes=set()
        indexed[key]={}
        for point in points:
            _keys(point,{'minute','n','wins','win_rate','ci95','input_match_hashes'})
            _require(_integer(point['minute']) and point['minute'] not in minutes);minutes.add(point['minute'])
            n=point['n'];wins=point['wins']
            _require(_integer(n,1) and _integer(wins) and wins<=n)
            inputs=point['input_match_hashes']
            _require(isinstance(inputs,list) and all(_hash(x) for x in inputs))
            _require(len(inputs)==n and len(set(inputs))==n and set(inputs)<=set(hashes))
            _require(not set(inputs)&cohort_hashes);cohort_hashes.update(inputs);used.update(inputs)
            for sha in inputs:
                _require(sha not in hash_minutes or hash_minutes[sha]==point['minute'])
                hash_minutes[sha]=point['minute']
            _require(_number(point['win_rate']) and abs(point['win_rate']-wins/n)<=1e-12)
            ci=point['ci95'];_keys(ci,{'low','high'});expected=_wilson(wins,n)
            _require(all(_number(ci[k]) and abs(ci[k]-expected[k])<=1e-12 for k in ('low','high')))
            _require(0<=ci['low']<=point['win_rate']<=ci['high']<=1)
            indexed[key][point['minute']]=point
    for key,bins in indexed.items():
        champion,position,patch,tier,comparison,opponent=key
        if comparison=='CHAMPION_ROLE':
            matchups=[other_bins for other_key,other_bins in indexed.items()
                      if other_key[:4]==key[:4] and other_key[4]=='MATCHUP']
            for minute,base in bins.items():
                parts=[other[minute] for other in matchups if minute in other]
                _require(bool(parts))
                partition=set();total_wins=0;total_n=0
                for point in parts:
                    inputs=set(point['input_match_hashes'])
                    _require(not inputs&partition);partition.update(inputs)
                    total_wins+=point['wins'];total_n+=point['n']
                _require(partition==set(base['input_match_hashes']))
                _require(total_n==base['n'] and total_wins==base['wins'])
        else:
            base=indexed.get((champion,position,patch,tier,'CHAMPION_ROLE',None),{})
            reverse=indexed.get((opponent,position,patch,tier,'MATCHUP',champion),{})
            for minute,point in bins.items():
                _require(minute in base and minute in reverse)
                other=reverse[minute]
                _require(set(point['input_match_hashes'])==set(other['input_match_hashes']))
                _require(point['n']==other['n'] and point['wins']+other['wins']==point['n'])
    _require(used==set(hashes))
    _require(bool(cohorts) if d['status']=='READY' else not cohorts)
    if d['status']!='READY':_require(not hashes)
    return d


def select_outcome_view(dataset,champion,position,patch,tier,opponent_champion=None):
    """Per ending bin, exact matchup then all sampled opponents; never fill bins."""
    d=validate_outcome_dataset(dataset)
    result={'status':'UNKNOWN','points':[],'reasons':[],'source':d['source'],'samples':d['samples']}
    if d['status']!='READY':
        result['reasons']=[d['status']];return result
    eligible=[c for c in d['cohorts'] if (c['champion'],c['position'],c['patch'],c['tier'])==
              (champion,position,patch,tier) and (c['comparison']=='CHAMPION_ROLE' or
                c['comparison']=='MATCHUP' and opponent_champion is not None and c['opponent_champion']==opponent_champion)]
    points={}
    for cohort in sorted(eligible,key=lambda c:c['comparison']=='MATCHUP'):
        for point in cohort['points']:
            points[point['minute']]=dict(point,comparison=cohort['comparison'],opponent_champion=cohort['opponent_champion'])
    result['points']=[points[minute] for minute in sorted(points)]
    result['status']='KNOWN' if points else 'UNKNOWN'
    result['reasons']=[] if points else ['NO_MATCHING_OUTCOME_COHORT']
    return result

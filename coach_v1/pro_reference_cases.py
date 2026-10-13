"""Anonymous selected-pro operational location and recorded signal summaries.

Inputs are private minute records; output is strictly aggregate. Operational
stages never establish tactical phase, correctness, vision or causal outcome.
"""
from collections import defaultdict
from copy import deepcopy
import math
import re
import statistics

from .power_stats import student_t_critical

STAGES=('OP_OPENING','OP_TRANSITION','OP_20_PLUS')
SIGNALS=('PRE_DEATH_CONTEXT','OBJECTIVE_EVENT_CONTEXT','TEAM_WARD_PLACEMENT','ADJACENT_RESOURCE_GAIN')
ROLE_NAMES=('TOP','JUNGLE','MID','BOTTOM','SUPPORT')
DEFINITIONS=dict(stages=[
    dict(id='OP_OPENING',rule='elapsed_minute < min(10, first recorded BUILDING_KILL minute if present)',tactical_phase='UNKNOWN'),
    dict(id='OP_TRANSITION',rule='min(10, first recorded BUILDING_KILL minute if present) <= elapsed_minute < 20',tactical_phase='UNKNOWN'),
    dict(id='OP_20_PLUS',rule='elapsed_minute >= 20',tactical_phase='UNKNOWN')],
    location_grid=dict(kind='MAP_COORDINATE_3_BY_3',x_edges=[0,16000/3,32000/3,16000],y_edges=[0,16000/3,32000/3,16000],
        labels='Gxy, x/y indices 0..2 ascending coordinates; geometric region, not verified lane'),
    statistic_policy=dict(kind='MATCH_CLUSTERED_STUDENT_T95',minimum_matches=3,visible='CI width <= empirical sample standard deviation',
        observation='per-match mean of received samples, then statistics across distinct matches'),
    event_window=dict(kind='PRECEDING_RECEIVED_FRAME',maximum_age_seconds=90,no_interpolation=True),
    resource_window=dict(kind='ADJACENT_RECEIVED_MINUTES',maximum_interval_seconds=60,require_minute_difference=1,no_interpolation=True))
LIMITATIONS=['OPERATIONAL_STAGE_NOT_VERIFIED_TACTICAL_PHASE','COORDINATE_GRID_NOT_VERIFIED_LANE_OR_BATTLE_CONTEXT',
    'USER_REPORTED_PRO_ROSTER_NOT_NETWORK_VERIFIED','TIER_UNKNOWN_NOT_LEAGUE_SEED_COHORT',
    'MATCH_CLUSTERED_NOT_INDEPENDENT_PLAYERS','MINUTE_SAMPLES_NO_INTERPOLATION','EVENT_CONTEXT_PRECEDING_FRAME_MAX_90_SECONDS',
    'EVENT_COUNT_IS_PERSONAL_CONTEXT_OBSERVATIONS_NOT_UNIQUE_WORLD_EVENTS','TEAM_WARD_EVENT_NOT_ACTUAL_VISION_OR_WARD_LIFETIME',
    'WAVE_STATE_UNKNOWN','UNSEEN_ENEMIES_UNKNOWN','SKILL_AND_COOLDOWN_STATE_UNKNOWN','VIDEO_UNVERIFIED',
    'RECORDED_SIGNAL_NON_CAUSAL_NO_WRONGDOING_OR_OUTCOME_JUDGMENT','SAMPLE_SELECTION_AND_POPULATION_COVERAGE_UNVERIFIED',
    'CONSTANT_SAMPLES_DO_NOT_PROVE_POPULATION_CERTAINTY']
UNITS={'x':'MAP_COORDINATE','y':'MAP_COORDINATE','distance_to_allied_jungle':'MAP_COORDINATE_DISTANCE',
    'distance_to_allied_support':'MAP_COORDINATE_DISTANCE','gold_gain_per_minute':'GOLD_PER_MINUTE',
    'xp_gain_per_minute':'XP_PER_MINUTE','cs_gain_per_minute':'CS_PER_MINUTE'}


def _require(ok):
    if not ok:raise ValueError('INVALID_PRO_REFERENCE_CASES')
def _number(v):return type(v) in (int,float) and math.isfinite(v)
def _int(v):return type(v) is int and v>=0

def _xy(value):
    return value if isinstance(value,dict) and all(_number(value.get(k)) and 0<=value[k]<=16000 for k in ('x','y')) else None

def _stat(metric,matches):
    values=[statistics.mean(v) for v in matches.values() if v];n=len(values)
    result=dict(metric=metric,units=UNITS[metric],status='UNKNOWN',n=n,mean=None,median=None,sample_sd=None,
        ci95=dict(low=None,high=None),visible=False,omission_reason='N_LT_3')
    if n<3:return result
    mean=statistics.mean(values);sd=statistics.stdev(values);half=student_t_critical(n-1)*sd/math.sqrt(n)
    visible=2*half<=sd+1e-12
    return dict(result,status='KNOWN' if visible else 'UNKNOWN',mean=mean,median=statistics.median(values),sample_sd=sd,
        ci95=dict(low=mean-half,high=mean+half),visible=visible,omission_reason=None if visible else 'CI_TOO_WIDE')


def _stage(minute,transition):return 'OP_20_PLUS' if minute>=20 else 'OP_TRANSITION' if minute>=transition else 'OP_OPENING'

def _group():return dict(matches=set(),sample_n=0,champions=defaultdict(set),grid=defaultdict(int),coordinate_matches=set(),
    x=defaultdict(list),y=defaultdict(list),signals={s:dict(count=0,matches=set(),unknown=0,metrics={m:defaultdict(list) for m in
        (('gold_gain_per_minute','xp_gain_per_minute','cs_gain_per_minute') if s=='ADJACENT_RESOURCE_GAIN' else ('distance_to_allied_jungle','distance_to_allied_support'))}) for s in SIGNALS})


def build_reference_cases(observations,*,roster_sha256,retrieved_at,sample_kind='REAL'):
    _require(isinstance(observations,list));groups=defaultdict(_group);seen=set();all_matches=set()
    for o in observations:
        _require(isinstance(o,dict) and isinstance(o.get('match_sha256'),str) and re.fullmatch('[a-f0-9]{64}',o['match_sha256']))
        _require(o.get('role') in ROLE_NAMES and isinstance(o.get('champion'),str) and re.fullmatch('[A-Za-z][A-Za-z0-9]{0,39}',o['champion']))
        _require(isinstance(o.get('patch'),str) and re.fullmatch(r'[0-9]+\.[0-9]+',o['patch']))
        identity=(o['match_sha256'],o['role'],o['champion'])
        if identity in seen:continue
        seen.add(identity);mh=o['match_sha256'];all_matches.add(mh)
        resources=o.get('resources',[]);movement=o.get('movement',[]);contexts=o.get('contexts',[])
        _require(all(isinstance(v,list) for v in (resources,movement,contexts)))
        building=[c['minute'] for c in contexts if isinstance(c,dict) and c.get('event_type')=='BUILDING_KILL' and _number(c.get('minute')) and c['minute']>=0]
        transition=min([10,*building])
        def cohort(minute):
            g=groups[(o['patch'],o['role'],_stage(minute,transition))];g['matches'].add(mh);g['champions'][o['champion']].add(mh);return g
        received=[]
        for p in movement:
            _require(isinstance(p,dict) and _number(p.get('minute')) and p['minute']>=0 and _number(p.get('timestamp_ms')) and p['timestamp_ms']>=0)
            received.append(p);g=cohort(p['minute']);g['sample_n']+=1;xy=_xy(p.get('own_position'))
            if xy:
                g['coordinate_matches'].add(mh);g['x'][mh].append(xy['x']);g['y'][mh].append(xy['y'])
                gx=min(2,int(xy['x']/(16000/3)));gy=min(2,int(xy['y']/(16000/3)));g['grid']['G'+str(gx)+str(gy)]+=1
        received.sort(key=lambda p:p['timestamp_ms'])
        for c in contexts:
            if not isinstance(c,dict) or not _number(c.get('minute')) or c['minute']<0:continue
            signal='PRE_DEATH_CONTEXT' if c.get('kind')=='DEATH' else 'OBJECTIVE_EVENT_CONTEXT' if c.get('kind')=='OBJECTIVE' else 'TEAM_WARD_PLACEMENT' if c.get('kind')=='TEAM_WARD' and c.get('event_type')=='WARD_PLACED' else None
            if signal is None:continue
            g=cohort(c['minute']);s=g['signals'][signal];s['count']+=1;s['matches'].add(mh)
            stamp=c['minute']*60000;previous=next((p for p in reversed(received) if p['timestamp_ms']<=stamp),None)
            if previous is None or stamp-previous['timestamp_ms']>90000:s['unknown']+=1;continue
            own=_xy(previous.get('own_position'));known=False
            for target in ('jungle','support'):
                ally=_xy(previous.get('allied_'+target+'_position'))
                if own and ally:
                    s['metrics']['distance_to_allied_'+target][mh].append(math.hypot(own['x']-ally['x'],own['y']-ally['y']));known=True
            if not known:s['unknown']+=1
        previous=None
        for r in sorted(resources,key=lambda p:p.get('timestamp_ms',-1)):
            _require(isinstance(r,dict) and _int(r.get('minute')) and _number(r.get('timestamp_ms')) and r['timestamp_ms']>=0)
            if previous is not None:
                elapsed=(r['timestamp_ms']-previous['timestamp_ms'])/60000
                if r['minute']-previous['minute']==1 and 0<elapsed<=1:
                    s=cohort(r['minute'])['signals']['ADJACENT_RESOURCE_GAIN'];s['count']+=1;s['matches'].add(mh);known=False
                    for resource in ('gold','xp','cs'):
                        if _number(r.get(resource)) and _number(previous.get(resource)):
                            s['metrics'][resource+'_gain_per_minute'][mh].append((r[resource]-previous[resource])/elapsed);known=True
                    if not known:s['unknown']+=1
            previous=r
    cohorts=[]
    for (patch,role,stage),g in sorted(groups.items(),key=lambda item:(item[0][0],item[0][1],STAGES.index(item[0][2]))):
        n=len(g['matches']);geometry_n=len(g['coordinate_matches']);grid=[]
        if geometry_n>=3:
            total=sum(g['grid'].values());grid=[dict(region=region,count=count,share=count/total) for region,count in sorted(g['grid'].items())]
        signals=[]
        for signal in SIGNALS:
            s=g['signals'][signal]
            signals.append(dict(type=signal,event_count=s['count'],match_n=len(s['matches']),unknown_context_events=s['unknown'],
                inference='RECORDED_SIGNAL_NON_CAUSAL',metrics=[_stat(metric,matches) for metric,matches in s['metrics'].items()]))
        cohorts.append(dict(patch=patch,role=role,stage=stage,tactical_phase='UNKNOWN',match_n=n,sample_n=g['sample_n'],
            champions=[dict(champion=champion,match_n=len(matches)) for champion,matches in sorted(g['champions'].items())],
            location=dict(status='KNOWN' if geometry_n>=3 else 'UNKNOWN',reason=None if geometry_n>=3 else 'N_LT_3_COORDINATE_MATCHES',
                coordinate_match_n=geometry_n,grid_counts=grid,coordinates=dict(x=_stat('x',g['x']),y=_stat('y',g['y']))),signals=signals))
    return validate_reference_cases(dict(schema_version='postgame.pro-reference-cases.v1',sample_kind=sample_kind,
        status='READY' if any(c['location']['status']=='KNOWN' or any(m['visible'] for s in c['signals'] for m in s['metrics']) for c in cohorts) else 'INSUFFICIENT_DATA',
        selection='USER_PRO_REFERENCE_ROSTER',tier='UNKNOWN',roster_verification='USER_REPORT_NOT_NETWORK_VERIFIED',
        roster_sha256=roster_sha256,retrieved_at=retrieved_at,sample_counts=dict(unique_matches=len(all_matches),selected_champion_role_matches=len(seen)),
        definitions=deepcopy(DEFINITIONS),cohorts=cohorts,limitations=deepcopy(LIMITATIONS)))


def empty_reference_cases(reason='NOT_COLLECTED'):
    # Reason belongs in endpoint wrapper; strict empty data remains a valid aggregate.
    return build_reference_cases([],roster_sha256='0'*64,retrieved_at='UNKNOWN',sample_kind='REAL')


def _validate_stat(p,metric,maximum_n):
    _require(isinstance(p,dict) and set(p)=={'metric','units','status','n','mean','median','sample_sd','ci95','visible','omission_reason'})
    _require(p['metric']==metric and p['units']==UNITS[metric] and _int(p['n']) and p['n']<=maximum_n and type(p['visible']) is bool)
    _require(isinstance(p['ci95'],dict) and set(p['ci95'])=={'low','high'})
    if p['n']<3:
        _require(p['mean'] is None and p['median'] is None and p['sample_sd'] is None and p['ci95']==dict(low=None,high=None) and not p['visible'] and p['status']=='UNKNOWN' and p['omission_reason']=='N_LT_3');return
    _require(all(_number(p[k]) for k in ('mean','median','sample_sd')) and p['sample_sd']>=0)
    if metric in ('x','y'):_require(0<=p['mean']<=16000 and 0<=p['median']<=16000)
    if metric.startswith('distance_'):_require(p['mean']>=0 and p['median']>=0)
    half=student_t_critical(p['n']-1)*p['sample_sd']/math.sqrt(p['n'])
    low,high=p['ci95']['low'],p['ci95']['high'];_require(_number(low) and _number(high))
    _require(abs(low-(p['mean']-half))<=max(1e-8,abs(low)*1e-12) and abs(high-(p['mean']+half))<=max(1e-8,abs(high)*1e-12))
    visible=2*half<=p['sample_sd']+1e-12
    _require(p['visible']==visible and p['status']==('KNOWN' if visible else 'UNKNOWN') and p['omission_reason']==(None if visible else 'CI_TOO_WIDE'))


def validate_reference_cases(data):
    keys={'schema_version','sample_kind','status','selection','tier','roster_verification','roster_sha256','retrieved_at','sample_counts','definitions','cohorts','limitations'}
    _require(isinstance(data,dict) and set(data)==keys);d=deepcopy(data)
    _require(d['schema_version']=='postgame.pro-reference-cases.v1' and d['sample_kind'] in ('REAL','SYNTHETIC'))
    _require(d['selection']=='USER_PRO_REFERENCE_ROSTER' and d['tier']=='UNKNOWN' and d['roster_verification']=='USER_REPORT_NOT_NETWORK_VERIFIED')
    _require(isinstance(d['roster_sha256'],str) and re.fullmatch('[a-f0-9]{64}',d['roster_sha256']) and isinstance(d['retrieved_at'],str) and 1<=len(d['retrieved_at'])<=100)
    _require(d['definitions']==DEFINITIONS and isinstance(d['sample_counts'],dict) and set(d['sample_counts'])=={'unique_matches','selected_champion_role_matches'})
    counts=d['sample_counts'];_require(all(_int(v) for v in counts.values()) and counts['unique_matches']<=counts['selected_champion_role_matches'])
    _require(isinstance(d['limitations'],list) and d['limitations']==LIMITATIONS and isinstance(d['cohorts'],list));identities=set()
    for c in d['cohorts']:
        _require(isinstance(c,dict) and set(c)=={'patch','role','stage','tactical_phase','match_n','sample_n','champions','location','signals'})
        _require(isinstance(c['patch'],str) and re.fullmatch(r'[0-9]+\.[0-9]+',c['patch']) and c['role'] in ROLE_NAMES and c['stage'] in STAGES and c['tactical_phase']=='UNKNOWN')
        identity=(c['patch'],c['role'],c['stage']);_require(identity not in identities);identities.add(identity)
        _require(_int(c['match_n']) and 1<=c['match_n']<=counts['unique_matches'] and _int(c['sample_n']))
        _require(isinstance(c['champions'],list));names=set()
        for champion in c['champions']:
            _require(isinstance(champion,dict) and set(champion)=={'champion','match_n'} and isinstance(champion['champion'],str) and re.fullmatch('[A-Za-z][A-Za-z0-9]{0,39}',champion['champion']))
            _require(champion['champion'] not in names and _int(champion['match_n']) and 1<=champion['match_n']<=c['match_n']);names.add(champion['champion'])
        loc=c['location'];_require(isinstance(loc,dict) and set(loc)=={'status','reason','coordinate_match_n','grid_counts','coordinates'})
        _require(_int(loc['coordinate_match_n']) and loc['coordinate_match_n']<=c['match_n'] and isinstance(loc['grid_counts'],list))
        enough=loc['coordinate_match_n']>=3
        _require(loc['status']==('KNOWN' if enough else 'UNKNOWN') and loc['reason']==(None if enough else 'N_LT_3_COORDINATE_MATCHES'))
        regions=set();total=0
        for region in loc['grid_counts']:
            _require(isinstance(region,dict) and set(region)=={'region','count','share'} and isinstance(region['region'],str) and re.fullmatch('G[0-2][0-2]',region['region']))
            _require(region['region'] not in regions and _int(region['count']) and region['count']>0 and _number(region['share']) and 0<region['share']<=1);regions.add(region['region']);total+=region['count']
        _require(bool(loc['grid_counts'])==enough and total<=c['sample_n'])
        for region in loc['grid_counts']:_require(abs(region['share']-region['count']/total)<1e-9)
        _require(isinstance(loc['coordinates'],dict) and set(loc['coordinates'])=={'x','y'})
        for coordinate in ('x','y'):_validate_stat(loc['coordinates'][coordinate],coordinate,loc['coordinate_match_n'])
        _require(isinstance(c['signals'],list) and len(c['signals'])==len(SIGNALS))
        for signal,expected in zip(c['signals'],SIGNALS):
            _require(isinstance(signal,dict) and set(signal)=={'type','event_count','match_n','unknown_context_events','inference','metrics'} and signal['type']==expected and signal['inference']=='RECORDED_SIGNAL_NON_CAUSAL')
            _require(_int(signal['event_count']) and _int(signal['match_n']) and signal['match_n']<=c['match_n'] and signal['match_n']<=signal['event_count'] and _int(signal['unknown_context_events']) and signal['unknown_context_events']<=signal['event_count'])
            metrics=('gold_gain_per_minute','xp_gain_per_minute','cs_gain_per_minute') if expected=='ADJACENT_RESOURCE_GAIN' else ('distance_to_allied_jungle','distance_to_allied_support')
            _require(isinstance(signal['metrics'],list) and len(signal['metrics'])==len(metrics))
            for metric,name in zip(signal['metrics'],metrics):_validate_stat(metric,name,signal['match_n'])
    ready=any(c['location']['status']=='KNOWN' or any(m['visible'] for s in c['signals'] for m in s['metrics']) for c in d['cohorts'])
    _require(d['status']==('READY' if ready else 'INSUFFICIENT_DATA'));return d


def public_collection_receipt(receipt):
    selections=receipt.get('selections',[])
    allowed_reasons={None,'COLLECTION_NOT_STARTED','RIOT_KEY_REQUIRED','NO_ELIGIBLE_PLAYER_OBSERVATIONS',
        'MALFORMED_PRIVATE_OR_RIOT_RESPONSE','DEADLINE_EXHAUSTED','REQUEST_BUDGET_EXHAUSTED','MATCH_BUDGET_EXHAUSTED',
        'NETWORK_FAILURE','MALFORMED_RESPONSE','UNAUTHORIZED_OR_EXPIRED_OR_UNSUPPORTED_PATH','RATE_LIMIT_EXHAUSTED',
        'RIOT_SERVER_FAILURE','HTTP_FAILURE','UNKNOWN_COLLECTION_REASON'}
    reason=receipt.get('reason');reason=reason if reason in allowed_reasons else 'UNKNOWN_COLLECTION_REASON'
    _require(receipt.get('status','BLOCKED_EXTERNAL') in ('READY','INSUFFICIENT_DATA','BLOCKED_EXTERNAL','READY_TO_COLLECT'))
    return dict(schema_version='pro.reference-public-collection.v1',status=receipt.get('status','BLOCKED_EXTERNAL'),reason=reason,
        roster_sha256=receipt.get('roster_sha256'),request_count=receipt.get('request_count',0),unique_recorded_matches=receipt.get('unique_recorded_matches',0),
        matches_per_account=receipt.get('matches_per_account',0),position_share_threshold=receipt.get('position_share_threshold'),
        selection_counts=dict(selected=sum(r.get('status')=='SELECTED' for r in selections),skipped=sum(r.get('status')=='SKIPPED' for r in selections),
            replacements=sum(len(r.get('replacements',[])) for r in selections),failed_accounts=len(receipt.get('failed_accounts',[]))),
        privacy='ANONYMOUS_DERIVED_ONLY_NO_ACCOUNT_OR_MATCH_IDENTIFIERS',selection='USER_PRO_REFERENCE_ROSTER',tier='UNKNOWN',
        roster_verification='USER_REPORT_NOT_NETWORK_VERIFIED',
        observed_http_status=receipt.get('observed_http_status') if receipt.get('observed_http_status') in (401,403) else None,
        user_key_expiry_attribution='KEY_EXPIRED_PER_USER_RULE' if receipt.get('observed_http_status') in (401,403) else 'NOT_APPLICABLE')


def validate_public_directory(directory,private_directory):
    """Public artifact directory cannot contain or sit inside the private cache."""
    from pathlib import Path
    original=Path(directory).absolute();private_original=Path(private_directory).absolute()
    _require('..' not in original.parts and '..' not in private_original.parts)
    _require(not any(p.is_symlink() for p in [original,*original.parents]))
    public=original.resolve();private=private_original.resolve()
    _require('private' not in public.parts and not public.is_relative_to(private) and not private.is_relative_to(public))
    return public


def export_public_reference(directory,private_directory,receipt,cases):
    import json
    import os
    import tempfile
    public=validate_public_directory(directory,private_directory);data=validate_reference_cases(cases)
    safe=public_collection_receipt(receipt);public.mkdir(parents=True,exist_ok=True)
    for name,value in [('reference-cases.json',data),('collection-receipt.json',safe)]:
        path=public/name;_require(not path.is_symlink())
        fd,tmp=tempfile.mkstemp(prefix='.anonymous-',dir=public)
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as stream:json.dump(value,stream,ensure_ascii=False,allow_nan=False,sort_keys=True)
            os.replace(tmp,path)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
    return safe

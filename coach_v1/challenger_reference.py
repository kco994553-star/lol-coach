"""Challenger-first descriptive reference with explicit pointwise GM support.

Tiers never share sufficient records, means, intervals or sample counts. Only
exact same-champion/role/patch/resource/minute role-population points can fill
an insufficient primary point. This is descriptive evidence, not a tactic.
"""
from copy import deepcopy
import hashlib
import json
import re

from .power_stats import METRICS, POSITIONS, validate_power_dataset
from .collection_progress import _point, progress_response, validate_progress

PRIMARY='CHALLENGER'
AUXILIARY='GRANDMASTER'
UNITS={'gold_delta':'GOLD_PER_MINUTE','xp_delta':'XP_PER_MINUTE','cs_delta':'CS_PER_MINUTE'}


def reference_request(request):
    if not isinstance(request,dict) or set(request)!={'champion','position','patch'}:
        raise ValueError('invalid Challenger reference request')
    if not isinstance(request['champion'],str) or not re.fullmatch('[A-Za-z][A-Za-z0-9]{0,39}',request['champion']):
        raise ValueError('invalid Challenger reference champion')
    if request['position'] not in POSITIONS or not isinstance(request['patch'],str) or not re.fullmatch('[0-9]+\\.[0-9]+',request['patch']):
        raise ValueError('exact reference role and gameplay patch required')
    return deepcopy(request)


def _digest(data):
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def _metadata(data,tier,request,receipt):
    if data is None:
        return dict(tier=tier,available=False,status='UNKNOWN',source=None,samples=None,dataset_digest=None,role_progress=None)
    progress=validate_progress(receipt,data) if receipt is not None else progress_response(data)
    role=next(r for r in progress['roles'] if r['position']==request['position'])
    baseline={key:value for key,value in role['role_baseline'].items() if key!='curves'}
    return dict(tier=tier,available=True,status=data['status'],source=deepcopy(data['source']),
        samples={key:data['samples'][key] for key in ('real_matches','synthetic_matches')},dataset_digest=_digest(data),
        role_progress=dict(position=request['position'],role_baseline=baseline,
            champion_graph_summary=role['champion_graph_summary']))


def _precision(point,data,metric):
    if point is None or data is None:
        return dict(status='UNKNOWN',match_count=0,champion_count=None,estimated_required_matches=None,
                    estimated_remaining_matches=None,reason='EXACT_POINT_UNAVAILABLE',empirical_sd=None)
    return _point(point,metric,data['source']['precision_policy']['ci_width_limits'])


def select_challenger_reference(datasets,request,*,test_mode=False,progress=None):
    request=reference_request(request);progress=progress or {};selected={}
    for tier in (PRIMARY,AUXILIARY):
        raw=datasets.get((request['patch'],tier))
        if raw is None:continue
        data=validate_power_dataset(raw)
        if (data['source']['patch'],data['source']['tier'])!=(request['patch'],tier):
            raise ValueError('reference dataset index does not match source')
        if data['source']['sample_kind']=='SYNTHETIC' and not test_mode:continue
        selected[tier]=data
    primary=selected.get(PRIMARY);auxiliary=selected.get(AUXILIARY)
    metadata={tier:_metadata(selected.get(tier),tier,request,progress.get((request['patch'],tier))) for tier in (PRIMARY,AUXILIARY)}
    metadata[AUXILIARY]['use_policy']='INSUFFICIENT_PRIMARY_ONLY'
    maps={}
    for tier,data in selected.items():
        points={}
        if data['status']!='BLOCKED_EXTERNAL':
            for cohort in data['cohorts']:
                if (cohort['champion'],cohort['position'],cohort['patch'],cohort['tier'],cohort['comparison'])!=(
                    request['champion'],request['position'],request['patch'],tier,'ROLE_POPULATION'):continue
                for point in cohort['points']:points[(cohort['metric'],point['minute'])]=point
        maps[tier]=points
    main=maps.get(PRIMARY,{});extra=maps.get(AUXILIARY,{});series=[];point_sources={};all_points=[]
    for metric in METRICS:
        minutes=sorted({minute for name,minute in set(main)|set(extra) if name==metric});points=[]
        for minute in minutes:
            key=(metric,minute);p=main.get(key);a=extra.get(key)
            origin='PRIMARY' if p and p['visible'] else ('AUXILIARY' if a and a['visible'] else None)
            chosen=p if origin=='PRIMARY' else (a if origin=='AUXILIARY' else None)
            tier=PRIMARY if origin=='PRIMARY' else (AUXILIARY if origin=='AUXILIARY' else None)
            row=dict(minute=minute,metric=metric,status='KNOWN' if chosen else 'UNKNOWN',origin=origin,source_tier=tier,
                source_digest=metadata[tier]['dataset_digest'] if tier else None,comparison='ROLE_POPULATION',
                primary_precision=_precision(p,primary,metric),auxiliary_precision=_precision(a,auxiliary,metric),
                mean=chosen['mean'] if chosen else None,ci95=deepcopy(chosen['ci95']) if chosen else dict(low=None,high=None),
                n=chosen['n'] if chosen else None,champion_n=chosen.get('champion_n') if chosen else None,
                reference_n=chosen.get('reference_n') if chosen else None,champion_mean=chosen.get('champion_mean') if chosen else None,
                reference_mean=chosen.get('reference_mean') if chosen else None,
                reason=None if chosen else 'PRIMARY_AND_AUXILIARY_POINT_INSUFFICIENT')
            points.append(row);all_points.append(row)
            point_sources[metric+':'+str(minute)]=dict(origin=origin,tier=tier,dataset_digest=row['source_digest'])
        series.append(dict(metric=metric,units=UNITS[metric],points=points))
    deficits=[p['primary_precision'] for p in all_points if p['primary_precision']['status']!='READY']
    known_remaining=[p['estimated_remaining_matches'] for p in deficits if p['estimated_remaining_matches'] is not None]
    remaining=max(known_remaining,default=0) if not deficits or len(known_remaining)==len(deficits) else None
    summary=dict(primary_points=sum(p['origin']=='PRIMARY' for p in all_points),
        auxiliary_points=sum(p['origin']=='AUXILIARY' for p in all_points),unknown_points=sum(p['status']=='UNKNOWN' for p in all_points),
        primary_insufficient_points=len(deficits),estimated_remaining_primary_matches=remaining if all_points else None,
        remaining_scope='ALL_OBSERVED_RESOURCE_MINUTE_POINTS_WITH_CURRENT_EMPIRICAL_SD_AND_CHAMPION_COVERAGE',
        needs_auxiliary_collection=any(p['primary_precision']['status']!='READY' and p['auxiliary_precision']['status']!='READY' for p in all_points)
            or not all_points)
    return dict(schema_version='pregame.challenger-reference.v1',status='KNOWN' if any(p['status']=='KNOWN' for p in all_points) else 'UNKNOWN',
        scope=request,primary=metadata[PRIMARY],auxiliary=metadata[AUXILIARY],series=series,point_sources=point_sources,summary=summary,
        test_mode=bool(test_mode),coaching_accuracy=None,limitations=[
            'CHALLENGER_PRIMARY_GRANDMASTER_INSUFFICIENT_ONLY_AUXILIARY',
            'TIERS_ARE_NOT_POOLED_OR_DIRECTLY_COMPARED',
            'CURRENT_LEAGUE_SEED_COHORT_NOT_HISTORICAL_PARTICIPANT_RANK',
            'DESCRIPTIVE_RESOURCE_RATE_DELTA_NOT_TOTAL_FIGHTING_STRENGTH_OR_TACTICAL_APPROVAL',
            'MATCH_INDEPENDENCE_AND_POPULATION_COVERAGE_UNVERIFIED',
            'CONSTANT_SAMPLES_DO_NOT_PROVE_POPULATION_CERTAINTY'])


def challenger_reference_response(server,request):
    return select_challenger_reference(server.validated_power_datasets(),request,test_mode=server.test_mode,
                                       progress=getattr(server,'power_progress',{}))

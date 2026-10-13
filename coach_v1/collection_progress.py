"""Estimated sample requirements under the existing Student-t precision policy.

Projection holds empirical spread and champion coverage fixed; it is neither a
population guarantee nor coaching accuracy. Missing spread remains UNKNOWN.
"""
import math
import statistics
import hashlib
import json
from copy import deepcopy
from collections import defaultdict
from .power_stats import POSITIONS, student_t_critical, validate_power_dataset

MAX_ESTIMATE=1000000


def estimated_target(n,sd,width_limit):
    if type(n) is not int or n<2 or sd is None or not math.isfinite(sd) or sd<0:return None
    width=sd if width_limit is None else width_limit
    if not math.isfinite(width) or width<0:return None
    if sd==0:return 2
    if width==0:return None
    def eligible(count):return 2*student_t_critical(count-1)*sd/math.sqrt(count)<=width+1e-12
    low=2;high=2
    while not eligible(high) and high<MAX_ESTIMATE:high=min(high*2,MAX_ESTIMATE)
    if not eligible(high):return None
    while low<high:
        middle=(low+high)//2
        if eligible(middle):high=middle
        else:low=middle+1
    return low


def _point(point,metric,limits):
    n=point['n'];ci=point['ci95'];sd=None
    if n>=2 and ci['low'] is not None:
        sd=(ci['high']-ci['low'])*math.sqrt(n)/(2*student_t_critical(n-1))
    target=estimated_target(n,sd,(limits or {}).get(metric))
    champion_n=point.get('champion_n')
    if target is not None and champion_n is not None:
        # At fixed observed appearances/match, at least two appearances remain
        # necessary even when zero empirical variance would satisfy width.
        target=max(target,math.ceil(2*n/champion_n)) if champion_n else None
    remaining=max(0,target-n) if target is not None else None
    return dict(minute=point['minute'],match_count=n,champion_count=champion_n,
        status='READY' if point['visible'] else ('ESTIMATED' if target is not None else 'UNKNOWN'),
        estimated_required_matches=target,estimated_remaining_matches=remaining,
        reason=point['omission_reason'],empirical_sd=sd)


def _summary(graphs):
    points=[p for c in graphs for p in c['points']]
    known=[p['estimated_remaining_matches'] for p in points if p['estimated_remaining_matches'] is not None]
    return dict(scope='ANY_OBSERVED_CHAMPION_MINUTE_METRIC_SEGMENT',observed_points=len(points),
        visible_points=sum(p['status']=='READY' for p in points),unknown_points=sum(p['status']=='UNKNOWN' for p in points),
        estimated_remaining_matches=min(known) if known else None,
        status='READY' if any(p['status']=='READY' for p in points) else ('ESTIMATED' if known else 'UNKNOWN'))


def _compact(graph):
    result={k:v for k,v in graph.items() if k!='points'};points=graph['points']
    known=[p for p in points if p['estimated_remaining_matches'] is not None]
    result.update(point_count=len(points),visible_points=sum(p['status']=='READY' for p in points),
        unknown_points=sum(p['status']=='UNKNOWN' for p in points),
        minute_scope=dict(first=min((p['minute'] for p in points),default=None),last=max((p['minute'] for p in points),default=None),
                          kind='ALL_OBSERVED_ELAPSED_MINUTE_BINS'),
        estimated_required_matches=max((p['estimated_required_matches'] for p in known),default=None) if len(known)==len(points) else None,
        estimated_remaining_matches=max((p['estimated_remaining_matches'] for p in known),default=None) if len(known)==len(points) else None,
        status='READY' if points and all(p['status']=='READY' for p in points) else ('ESTIMATED' if points and len(known)==len(points) else 'UNKNOWN'))
    return result


def _baseline(records,position,limits):
    from .power_accumulator import validate_record
    role_index=POSITIONS.index(position);values=defaultdict(lambda:defaultdict(list))
    for raw in records:
        record=validate_record(raw);bins={}
        for frame in record['frames']:
            if record['duration_s'] is not None and frame['ms']>record['duration_s']*1000:continue
            bins[math.floor(frame['ms']/60000)]=frame
        for minute,frame in bins.items():
            if minute<=0:continue
            elapsed=frame['ms']/60000
            participants=[frame['resources'][role_index],frame['resources'][role_index+5]]
            for metric,fields in (('gold_delta',('gold',)),('xp_delta',('xp',)),('cs_delta',('cs','jungle_cs'))):
                if all(all(f in p for f in fields) for p in participants):
                    values[metric][minute].append(statistics.mean(sum(p[f] for f in fields)/elapsed for p in participants))
    curves=[]
    for metric,minutes in sorted(values.items()):
        points=[]
        for minute,observations in sorted(minutes.items()):
            n=len(observations);sd=statistics.stdev(observations) if n>=2 else None
            half=student_t_critical(n-1)*sd/math.sqrt(n) if sd is not None else None
            target=estimated_target(n,sd,(limits or {}).get(metric))
            visible=target is not None and n>=target
            points.append(dict(minute=minute,match_count=n,participant_count=2*n,mean=statistics.mean(observations),
                ci95=dict(low=statistics.mean(observations)-half if half is not None else None,
                          high=statistics.mean(observations)+half if half is not None else None),
                empirical_sd=sd,status='READY' if visible else ('ESTIMATED' if target is not None else 'UNKNOWN'),
                estimated_required_matches=target,estimated_remaining_matches=max(0,target-n) if target is not None else None,
                reason=None if visible else ('N_LT_2' if n<2 else 'CI_TOO_WIDE')))
        curves.append(dict(metric=metric,units={'gold_delta':'GOLD_PER_MINUTE','xp_delta':'XP_PER_MINUTE','cs_delta':'CS_PER_MINUTE'}[metric],points=points))
    summary=_summary(curves)
    return dict(match_count=len(records),participant_count=2*len(records),status=summary['status'],
        estimated_required_matches=None,estimated_remaining_matches=summary['estimated_remaining_matches'],
        estimate_scope='ANY_OBSERVED_ROLE_MINUTE_METRIC_SEGMENT',reason=None if curves else 'NO_RESOURCE_RATE_OBSERVATIONS',
        formula='POOLED_SAME_ROLE_MEAN_RATE_MATCH_CLUSTER_STUDENT_T95.v1',curves=curves)


def progress_response(dataset,records=None,*,include_points=False):
    if dataset is None:
        return dict(schema_version='pregame.collection-progress.v1',status='UNKNOWN',patch=None,tier=None,
            real_matches=0,synthetic_matches=0,completion_percentage=None,coaching_accuracy=None,policy=None,limitations=['NO_DATASET'],
            power_dataset_sha256=None,
            roles=[dict(position=position,role_baseline=dict(status='UNKNOWN',estimated_remaining_matches=None,
                       reason='NO_DATASET'),champion_graphs=[],champion_graph_summary=_summary([]),basic_curve_summary=_summary([]),
                       champion_graphs_total=0,champion_graphs_returned=0,champion_graphs_omitted=0,
                       champion_graph_scope='TOP20_CHAMPIONS_BY_MAX_OBSERVED_APPEARANCES_THEN_NAME') for position in POSITIONS])
    data=validate_power_dataset(dataset);source=data['source'];limits=source['precision_policy']['ci_width_limits']
    if records is not None:
        if len(records)!=len(data['samples']['hashed_match_ids']) or {r['hash'] for r in records}!=set(data['samples']['hashed_match_ids']):
            raise ValueError('progress sufficient records must exactly match dataset')
        if any(r['patch']!=source['patch'] for r in records):raise ValueError('progress patch mismatch')
    roles=[];pooled=source.get('population_reference',dict(match_count=data['samples']['real_matches']+data['samples']['synthetic_matches'],
        position_participant_count=2*(data['samples']['real_matches']+data['samples']['synthetic_matches'])))
    for position in POSITIONS:
        graphs=[dict(champion=c['champion'],comparison=c['comparison'],opponent_champion=c['opponent_champion'],metric=c['metric'],
                     points=[_point(p,c['metric'],limits) for p in c['points']]) for c in data['cohorts']
                     if c['position']==position and c['comparison']=='ROLE_POPULATION']
        baseline=dict(match_count=pooled['match_count'],
            participant_count=pooled['position_participant_count'],status='UNKNOWN',estimated_required_matches=None,
            estimated_remaining_matches=None,reason='POOLED_REFERENCE_SD_NOT_RETAINED_IN_AGGREGATE')
        if records is not None:baseline=_baseline(records,position,limits)
        summary=_summary([c for c in graphs if c['comparison']=='ROLE_POPULATION'])
        total_graphs=len(graphs)
        if not include_points:
            coverage={}
            for graph in graphs:
                coverage[graph['champion']]=max(coverage.get(graph['champion'],0),max((p['champion_count'] or 0 for p in graph['points']),default=0))
            selected=set(sorted(coverage,key=lambda name:(-coverage[name],name))[:20])
            graphs=[graph for graph in graphs if graph['champion'] in selected]
            graphs=[_compact(graph) for graph in graphs]
            if 'curves' in baseline:
                compact=[]
                for curve in baseline['curves']:
                    reduced=_compact(curve)
                    reduced['precision_evidence']=[dict(minute=p['minute'],match_count=p['match_count'],empirical_sd=p['empirical_sd']) for p in curve['points']]
                    compact.append(reduced)
                baseline['curves']=compact
        roles.append(dict(position=position,role_baseline=baseline,champion_graphs=graphs,
            champion_graph_summary=summary,basic_curve_summary=summary,champion_graphs_total=total_graphs,
            champion_graphs_returned=len(graphs),champion_graphs_omitted=total_graphs-len(graphs),
            champion_graph_scope='ALL_OBSERVED_CHAMPIONS' if include_points else 'TOP20_CHAMPIONS_BY_MAX_OBSERVED_APPEARANCES_THEN_NAME'))
    return dict(schema_version='pregame.collection-progress.v1',patch=source['patch'],tier=source['tier'],
        power_dataset_sha256=hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest(),
        status=data['status'],real_matches=data['samples']['real_matches'],synthetic_matches=data['samples']['synthetic_matches'],
        roles=roles,completion_percentage=None,coaching_accuracy=None,policy=source['precision_policy'],
        limitations=['ESTIMATE_ASSUMES_CURRENT_EMPIRICAL_SD_AND_CHAMPION_COVERAGE',
            'ROLE_BASELINE_AND_CHAMPION_GRAPH_ARE_DIFFERENT_ESTIMANDS',
            'TIER_IS_CURRENT_LEAGUE_SEED_COHORT_NOT_ALL_PARTICIPANT_RANKS',
            'CONSTANT_SAMPLES_DO_NOT_PROVE_POPULATION_CERTAINTY',
            'MATCH_INDEPENDENCE_AND_POPULATION_COVERAGE_UNVERIFIED',
            'LEAGUE_SEED_SELECTION_AND_SURVIVORSHIP_BIAS',
            'SAMPLE_REQUIREMENT_NOT_A_POPULATION_OR_GAMEPLAY_GUARANTEE'])


def validate_progress(response,dataset):
    try:return _validate_progress(response,dataset)
    except (TypeError,KeyError,AttributeError,OverflowError):raise ValueError('invalid collection progress') from None


def _validate_progress(response,dataset):
    """Strict sidecar shape, power digest, exact graph projection and CI policy.

Baseline sufficient observations are derived lineage, as aggregate means are
in power-data; this verifies the retained precision evidence mathematically,
without pretending that a public receipt recreates private original matches.
"""
    expected=progress_response(dataset)
    if not isinstance(response,dict) or set(response)!=set(expected):raise ValueError('invalid collection progress')
    if len(json.dumps(response,allow_nan=False).encode())>1024*1024:raise ValueError('collection progress too large')
    if not isinstance(response['roles'],list) or len(response['roles'])!=5:raise ValueError('five progress roles required')
    clean=deepcopy(response)
    for index,role in enumerate(clean['roles']):
        if not isinstance(role,dict) or set(role)!=set(expected['roles'][index]):raise ValueError('invalid progress role')
        baseline=role['role_baseline'];ordinary=expected['roles'][index]['role_baseline']
        if baseline!=ordinary:
            keys={'match_count','participant_count','status','estimated_required_matches','estimated_remaining_matches',
                  'estimate_scope','reason','formula','curves'}
            if not isinstance(baseline,dict) or set(baseline)!=keys:raise ValueError('invalid role baseline')
            total=dataset['samples']['real_matches']+dataset['samples']['synthetic_matches']
            if type(baseline['match_count']) is not int or type(baseline['participant_count']) is not int or baseline['match_count']!=total or baseline['participant_count']!=2*total or baseline['estimated_required_matches'] is not None:
                raise ValueError('invalid role baseline counts')
            if baseline['formula']!='POOLED_SAME_ROLE_MEAN_RATE_MATCH_CLUSTER_STUDENT_T95.v1' or baseline['estimate_scope']!='ANY_OBSERVED_ROLE_MINUTE_METRIC_SEGMENT':
                raise ValueError('invalid role baseline formula')
            if not isinstance(baseline['curves'],list) or len(baseline['curves'])>3:raise ValueError('invalid role curves')
            curves=[];metrics=set()
            for curve in baseline['curves']:
                if not isinstance(curve,dict) or 'precision_evidence' not in curve:raise ValueError('missing baseline precision evidence')
                metric=curve.get('metric')
                units={'gold_delta':'GOLD_PER_MINUTE','xp_delta':'XP_PER_MINUTE','cs_delta':'CS_PER_MINUTE'}
                if metric not in units or metric in metrics:raise ValueError('invalid baseline metric')
                metrics.add(metric);evidence=curve['precision_evidence'];points=[];previous=0
                if not isinstance(evidence,list) or not 1<=len(evidence)<=200:raise ValueError('invalid baseline precision evidence')
                for item in evidence:
                    if not isinstance(item,dict) or set(item)!={'minute','match_count','empirical_sd'}:raise ValueError('invalid baseline precision evidence')
                    minute=item['minute'];n=item['match_count'];sd=item['empirical_sd']
                    if type(minute) is not int or not previous<minute<=10000 or type(n) is not int or not 1<=n<=total:
                        raise ValueError('invalid baseline evidence counts')
                    previous=minute
                    if (n<2 and sd is not None) or (n>=2 and (type(sd) not in (int,float) or not math.isfinite(sd) or sd<0)):
                        raise ValueError('invalid baseline empirical spread')
                    target=estimated_target(n,sd,(dataset['source']['precision_policy']['ci_width_limits'] or {}).get(metric))
                    points.append(dict(minute=minute,status='READY' if target is not None and n>=target else ('ESTIMATED' if target is not None else 'UNKNOWN'),
                        estimated_required_matches=target,estimated_remaining_matches=max(0,target-n) if target is not None else None))
                original=dict(metric=metric,units=units[metric],points=points);compact=_compact(original);compact['precision_evidence']=evidence
                if compact!=curve:raise ValueError('baseline confidence projection mismatch')
                curves.append(original)
            summary=_summary(curves)
            if baseline['status']!=summary['status'] or baseline['estimated_remaining_matches']!=summary['estimated_remaining_matches'] or baseline['reason']!=(None if curves else 'NO_RESOURCE_RATE_OBSERVATIONS'):
                raise ValueError('baseline summary mismatch')
        role['role_baseline']=ordinary
    if json.dumps(clean,sort_keys=True,allow_nan=False)!=json.dumps(expected,sort_keys=True,allow_nan=False):
        raise ValueError('collection progress does not match power dataset')
    return deepcopy(response)

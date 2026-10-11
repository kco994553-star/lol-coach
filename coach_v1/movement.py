"""Source-bound conditional movement plans and descriptive private-input aggregates.

Minute labels never establish phase. Coordinates and participant identities are
used only inside the builder; public datasets contain aggregate distances only.
"""
from collections import defaultdict
from copy import deepcopy
import hashlib
import math
import re
import statistics as stats
from .state import canonical, digest

POSITIONS=('TOP','JUNGLE','MID','BOTTOM','SUPPORT')
STAGES=('EARLY','MID','LATE')
TIERS=('IRON','BRONZE','SILVER','GOLD','PLATINUM','EMERALD','DIAMOND','MASTER','GRANDMASTER','CHALLENGER')
PATCH=re.compile(r'[0-9]+\.[0-9]+\Z')
LAYERS=('DEFAULT','TYPE','CHAMPION','COMPOSITION')
FIELDS=('LANING_ACTIVE','FIRST_TURRET_DESTROYED','MAJOR_OBJECTIVE_CONTEST','LONG_RESPAWN_RISK')
HASH=re.compile(r'[a-f0-9]{64}\Z')
CHAMPION=re.compile(r'[A-Za-z][A-Za-z0-9]{0,99}\Z')
TIME_BIN_POLICY=dict(kind='ELAPSED_MINUTE_FLOOR',frame_interval_ms=60000,
    selection='LATEST_RECEIVED_FRAME_PER_MATCH_BIN')
SOURCE_KEYS={'provider','platform','regional','queue_id','map_id','tier','patch','window_start',
    'window_end','retrieved_at','sample_kind','endpoints','formula_version','precision_policy',
    'limitations','phase_annotation_sources','time_bin_policy'}
LIMITATIONS=['KNOWN_ALLIES_MEDIAN_NOT_ACTUAL_MAIN_BODY','DESCRIPTIVE_NON_CAUSAL_NOT_TACTICAL_APPROVAL',
    'ALL_FIVE_COORDINATES_REQUIRED_NO_INTERPOLATION','MINUTE_IS_NOT_PHASE',
    'TIER_IS_CURRENT_LEAGUE_SEED_COHORT_NOT_ALL_PARTICIPANT_RANKS',
    'MATCH_INDEPENDENCE_AND_POPULATION_COVERAGE_UNVERIFIED','LEAGUE_SEED_SELECTION_AND_SURVIVORSHIP_BIAS',
    'CONSTANT_SAMPLES_DO_NOT_PROVE_POPULATION_CERTAINTY','OPERATIONAL_PRECISION_NOT_VALIDATED_GAMEPLAY_THRESHOLD',
    'TIME_BIN_QUANTIZATION_LT_ONE_MINUTE_NO_INTERPOLATION','MULTIPLE_FRAMES_PER_BIN_USE_LATEST_RECEIVED']
POLICY=dict(version='CI_WIDTH_LE_SAMPLE_SD.v1',units='MAP_COORDINATE_DISTANCE',
    rationale='ESTIMATION_UNCERTAINTY_LE_EMPIRICAL_INDIVIDUAL_SPREAD')


def _require(ok,message='invalid movement dataset'):
    if not ok:raise ValueError(message)


def _keys(value,required,optional=()):
    _require(isinstance(value,dict) and set(required)<=set(value)<=set(required)|set(optional))


def _number(v):return type(v) in (int,float) and math.isfinite(v)
def _integer(v,minimum=0):return type(v) is int and v>=minimum
def _hash(v):return isinstance(v,str) and bool(HASH.fullmatch(v))
def _text(v):return isinstance(v,str) and bool(v.strip()) and len(v)<=2000


def _conditions(value,stage=None):
    _require(isinstance(value,list) and 1<=len(value)<=4,'phase conditions required')
    for c in value:
        _keys(c,{'field','value'});_require(c['field'] in FIELDS and type(c['value']) is bool)
    _require(len({c['field'] for c in value})==len(value),'duplicate phase condition')
    known={c['field']:c['value'] for c in value}
    if stage=='EARLY':_require(known.get('LANING_ACTIVE') is True,'early requires explicit laning')
    if stage=='MID':_require(known.get('FIRST_TURRET_DESTROYED') is True or known.get('MAJOR_OBJECTIVE_CONTEST') is True,'mid requires explicit transition')
    if stage=='LATE':_require(known.get('LONG_RESPAWN_RISK') is True,'late requires explicit respawn risk')
    return sorted(deepcopy(value),key=lambda c:c['field'])


def _source(source):
    _require(isinstance(source,dict) and set(source)<=SOURCE_KEYS,'source fields not allowlisted')
    s=deepcopy(source);s['formula_version']='KNOWN_ALLIES_COORDINATE_MEDIAN_DISTANCE_T95.v1'
    s['precision_policy']=deepcopy(POLICY);s['time_bin_policy']=deepcopy(TIME_BIN_POLICY)
    s['limitations']=list(dict.fromkeys(LIMITATIONS+s.get('limitations',[])))
    s.setdefault('phase_annotation_sources',[])
    _require(s.get('sample_kind') in ('REAL','SYNTHETIC'))
    _require(s.get('provider')==('RIOT_API' if s['sample_kind']=='REAL' else 'SYNTHETIC'),'provider sample-kind mismatch')
    return s


def _quantile(values,p):
    values=sorted(values);index=(len(values)-1)*p;lo=math.floor(index);hi=math.ceil(index)
    return values[lo]+(values[hi]-values[lo])*(index-lo)


def _point(minute,values):
    from .power_stats import student_t_critical
    n=len(values);mean=stats.mean(values)
    p=dict(minute=minute,n=n,mean_distance=mean,median_distance=_quantile(values,.5),
        q1_distance=_quantile(values,.25),q3_distance=_quantile(values,.75),ci95=dict(low=None,high=None),
        visible=False,omission_reason='N_LT_2')
    if n>=2:
        sd=stats.stdev(values);half=student_t_critical(n-1)*sd/math.sqrt(n)
        p.update(ci95=dict(low=mean-half,high=mean+half),visible=2*half<=sd+1e-12,
            omission_reason=None if 2*half<=sd+1e-12 else 'CI_TOO_WIDE')
    return p


def _annotations(annotations):
    result={};lineage=[]
    for a in annotations or []:
        _keys(a,{'match_sha256','timestamp_ms','stage','stage_conditions','source_sha256','source_pointer','verification'})
        _require(_hash(a['match_sha256']) and _hash(a['source_sha256']) and _number(a['timestamp_ms']) and a['timestamp_ms']>=0)
        _require(a['stage'] in STAGES and a['verification'] in ('VERIFIED','MANUAL_UNVERIFIED'))
        _require(isinstance(a['source_pointer'],str) and re.fullmatch(r'(?:/[A-Za-z0-9_~.-]+)+',a['source_pointer']) is not None,'archive JSON pointer required')
        c=_conditions(a['stage_conditions'],a['stage']);key=(a['match_sha256'],a['timestamp_ms'])
        value=dict(a,stage_conditions=c)
        _require(key not in result or result[key]==value,'contradictory duplicate phase annotation')
        result[key]=value
        item=dict(sha256=a['source_sha256'],pointer=a['source_pointer'],verification=a['verification'])
        if item not in lineage:lineage.append(item)
    return result,sorted(lineage,key=canonical)


def build_movement_dataset(pairs,*,source,phase_annotations=None):
    """Aggregate complete map-11 teams; never persist raw match/frame payloads."""
    s=_source(source);annotations,lineage=_annotations(phase_annotations)
    s['phase_annotation_sources']=lineage
    groups=defaultdict(lambda:defaultdict(lambda:defaultdict(list)));seen=set();included=set()
    for pair in pairs:
        if not isinstance(pair,dict):continue
        match=pair.get('match',{});timeline=pair.get('timeline',{});mid=match.get('metadata',{}).get('matchId')
        if not isinstance(mid,str) or not mid.startswith('KR_') or timeline.get('metadata',{}).get('matchId')!=mid:continue
        mh=hashlib.sha256(mid.encode()).hexdigest()
        if mh in seen:continue
        seen.add(mh);info=match.get('info',{});version=info.get('gameVersion','').split('.')
        if len(version)<2 or not all(v.isdigit() for v in version[:2]):continue
        patch='.'.join(version[:2])
        if info.get('queueId')!=420 or info.get('mapId')!=11 or info.get('gameMode')!='CLASSIC':continue
        if s.get('patch') is not None and s['patch']!=patch:continue
        start=info.get('gameStartTimestamp');duration=info.get('gameDuration')
        if not _number(start) or not _number(duration) or duration<0:continue
        if s.get('window_start') is not None and start/1000<s['window_start']:continue
        if s.get('window_end') is not None and start/1000>s['window_end']:continue
        people=info.get('participants',[])
        if not isinstance(people,list):continue
        teams={team:[p for p in people if isinstance(p,dict) and p.get('teamId')==team] for team in (100,200)}
        if any(len(ps)!=5 or {p.get('teamPosition') for p in ps}!=set(POSITIONS) for ps in teams.values()):continue
        if any(not _integer(p.get('participantId'),1) or not isinstance(p.get('championName'),str) or not CHAMPION.fullmatch(p['championName']) for ps in teams.values() for p in ps):continue
        if len({p['participantId'] for ps in teams.values() for p in ps})!=10:continue
        timeline_info=timeline.get('info',{})
        if type(timeline_info.get('frameInterval')) is not int or timeline_info['frameInterval']!=60000:continue
        frames=timeline_info.get('frames',[])
        if not isinstance(frames,list):continue
        times=[f.get('timestamp') for f in frames if isinstance(f,dict)]
        if len(times)!=len(frames) or not all(_number(t) and 0<=t<=duration*1000 for t in times) or times!=sorted(set(times)):continue
        bins={}
        for frame in frames:bins[math.floor(frame['timestamp']/60000)]=frame
        for minute,frame in sorted(bins.items()):
            # Chronologically sorted frames give a deterministic latest representative.
            # Annotation binding keeps its original received timestamp, not the bin label.
            timestamp=frame['timestamp'];pf=frame.get('participantFrames',{})
            if not isinstance(pf,dict):continue
            for people in teams.values():
                coords=[]
                for person in people:
                    entry=pf.get(str(person['participantId']),{})
                    xy=entry.get('position') if isinstance(entry,dict) else None
                    if not isinstance(xy,dict) or not _number(xy.get('x')) or not _number(xy.get('y')):break
                    coords.append((xy['x'],xy['y']))
                if len(coords)!=5:continue
                cx=stats.median([x for x,y in coords]);cy=stats.median([y for x,y in coords])
                for person,(x,y) in zip(people,coords):
                    distance=math.hypot(x-cx,y-cy)
                    identity=(person['championName'],person['teamPosition'],patch,s['tier'],None,None)
                    groups[identity][minute][mh].append(distance);included.add(mh)
                    a=annotations.get((mh,timestamp))
                    if a and a['verification']=='VERIFIED':
                        identity=(*identity[:4],a['stage'],canonical(a['stage_conditions']))
                        groups[identity][minute][mh].append(distance)
    cohorts=[]
    for identity,minutes in sorted(groups.items(),key=lambda item:canonical(item[0])):
        champion,position,patch,tier,stage,signature=identity
        import json
        c=dict(champion=champion,position=position,patch=patch,tier=tier,stage=stage,
            condition_signature=json.loads(signature) if signature else None)
        c['id']=digest(c);c['points']=[_point(minute,[stats.mean(v) for v in observations.values()])
            for minute,observations in sorted(minutes.items())]
        cohorts.append(c)
    count=len(included);kind=s['sample_kind']
    return validate_movement_dataset(dict(schema_version='pregame.movement-data.v1',
        status='READY' if any(p['visible'] for c in cohorts for p in c['points']) else 'INSUFFICIENT_DATA',source=s,
        cohorts=cohorts,samples=dict(hashed_match_ids=sorted(included),real_matches=count if kind=='REAL' else 0,
        synthetic_matches=count if kind=='SYNTHETIC' else 0),coaching_accuracy=None))


def validate_movement_dataset(dataset):
    """Strict aggregate allowlist; validation returns an independent copy."""
    d=deepcopy(dataset);_keys(d,{'schema_version','status','source','cohorts','samples','coaching_accuracy'})
    _require(d['schema_version']=='pregame.movement-data.v1' and d['status'] in ('READY','INSUFFICIENT_DATA') and d['coaching_accuracy'] is None)
    s=d['source'];_keys(s,SOURCE_KEYS-{'phase_annotation_sources'},{'phase_annotation_sources'})
    _require(s['sample_kind'] in ('REAL','SYNTHETIC') and s['queue_id']==420 and s['map_id']==11)
    _require(s['platform']=='KR' and s['regional']=='ASIA' and s['provider']==('RIOT_API' if s['sample_kind']=='REAL' else 'SYNTHETIC') and s['tier'] in TIERS)
    _require(s['patch'] is None or (isinstance(s['patch'],str) and PATCH.fullmatch(s['patch'])))
    _require(all(s[k] is None or _number(s[k]) for k in ('window_start','window_end')))
    _require(s['retrieved_at'] is None or _text(s['retrieved_at']))
    _require(s['formula_version']=='KNOWN_ALLIES_COORDINATE_MEDIAN_DISTANCE_T95.v1' and s['precision_policy']==POLICY and s['time_bin_policy']==TIME_BIN_POLICY)
    _require(isinstance(s['endpoints'],list) and all(e in ('LEAGUE_V4_ENTRIES','LEAGUE_V4_MASTER','LEAGUE_V4_GRANDMASTER','LEAGUE_V4_CHALLENGER','MATCH_V5_IDS','MATCH_V5_MATCH','MATCH_V5_TIMELINE') for e in s['endpoints']))
    _require(isinstance(s['limitations'],list) and set(LIMITATIONS)<=set(s['limitations']) and all(_text(v) for v in s['limitations']))
    lineages=s.get('phase_annotation_sources',[]);_require(isinstance(lineages,list))
    for item in lineages:
        _keys(item,{'sha256','pointer','verification'})
        _require(_hash(item['sha256']) and isinstance(item['pointer'],str) and re.fullmatch(r'(?:/[A-Za-z0-9_~.-]+)+',item['pointer']) is not None)
        _require(item['verification'] in ('VERIFIED','MANUAL_UNVERIFIED'))
    samples=d['samples'];_keys(samples,{'hashed_match_ids','real_matches','synthetic_matches'})
    hashes=samples['hashed_match_ids'];_require(isinstance(hashes,list) and all(_hash(h) for h in hashes) and len(hashes)==len(set(hashes)))
    _require(_integer(samples['real_matches']) and _integer(samples['synthetic_matches']))
    _require(len(hashes)==samples['real_matches']+samples['synthetic_matches'])
    _require(samples['synthetic_matches']==0 if s['sample_kind']=='REAL' else samples['real_matches']==0)
    _require(isinstance(d['cohorts'],list));ids=set();visible=False
    for c in d['cohorts']:
        _keys(c,{'id','champion','position','patch','tier','stage','condition_signature','points'})
        _require(_hash(c['id']) and c['id'] not in ids);ids.add(c['id'])
        _require(isinstance(c['champion'],str) and CHAMPION.fullmatch(c['champion']) and c['position'] in POSITIONS and isinstance(c['patch'],str) and PATCH.fullmatch(c['patch']) and c['tier']==s['tier'])
        _require(s['patch'] is None or c['patch']==s['patch'])
        _require(c['stage'] is None or c['stage'] in STAGES)
        if c['stage'] is None:_require(c['condition_signature'] is None)
        else:
            _require(c['condition_signature']==_conditions(c['condition_signature'],c['stage']))
            _require(any(l['verification']=='VERIFIED' for l in lineages),'stage lineage missing')
        _require(c['id']==digest({k:c[k] for k in ('champion','position','patch','tier','stage','condition_signature')}))
        _require(isinstance(c['points'],list) and bool(c['points']));minutes=[]
        for p in c['points']:
            _keys(p,{'minute','n','mean_distance','median_distance','q1_distance','q3_distance','ci95','visible','omission_reason'})
            _require(_number(p['minute']) and p['minute']>=0 and p['minute']%1==0);minutes.append(p['minute'])
            _require(_integer(p['n'],1) and p['n']<=len(hashes))
            _require(all(_number(p[k]) and p[k]>=0 for k in ('mean_distance','median_distance','q1_distance','q3_distance')))
            _require(p['q1_distance']<=p['median_distance']<=p['q3_distance'])
            _keys(p['ci95'],{'low','high'});lo=p['ci95']['low'];hi=p['ci95']['high']
            _require(type(p['visible']) is bool)
            if p['n']==1:_require(lo is None and hi is None and not p['visible'] and p['omission_reason']=='N_LT_2')
            else:
                _require(_number(lo) and _number(hi) and lo<=p['mean_distance']<=hi)
                _require(math.isclose((lo+hi)/2,p['mean_distance'],rel_tol=1e-9,abs_tol=1e-9),'confidence interval must center on mean')
                # Recover the sample SD from the supplied t interval to validate eligibility.
                from .power_stats import student_t_critical
                sd=(hi-lo)*math.sqrt(p['n'])/(2*student_t_critical(p['n']-1))
                enough=hi-lo<=sd+1e-12
                _require(p['visible']==enough and p['omission_reason']==(None if enough else 'CI_TOO_WIDE'))
            visible=visible or p['visible']
        _require(minutes==sorted(set(minutes)))
    _require(d['status']==('READY' if visible else 'INSUFFICIENT_DATA'))
    canonical(d)
    return d


def _subject_champion(row,draft):
    if row['subject']=='SELF':return draft.get('my_champion') if row['position']==draft.get('my_position') else None
    side='ALLY' if row['subject']=='ALLY' else 'ENEMY'
    slots=[s for s in draft.get('slots',[]) if s.get('side')==side and s.get('position')==row['position']]
    return slots[0].get('champion') if len(slots)==1 else None


def build_movement_plan(traces,draft,statistics=None,test_mode=False):
    """Consume reviewed evaluator traces; unsupported rows remain explicit UNKNOWN."""
    from .pregame_evaluator import _cell
    cell=_cell('MOVEMENT','구간별 위치·역할');cell['reasons']=[]
    dataset=None;stats_reason='MOVEMENT_STATISTICS_MISSING'
    if statistics is not None:
        try:
            candidate=validate_movement_dataset(statistics)
            if candidate['source']['sample_kind']=='SYNTHETIC' and not test_mode:stats_reason='SYNTHETIC_MOVEMENT_STATISTICS'
            else:dataset=candidate
        except (ValueError,TypeError,KeyError):stats_reason='MOVEMENT_STATISTICS_INVALID'
    for trace in traces:
        spec=trace.get('spec') or {};output=trace.get('output') or {}
        if spec.get('schema_version')!='pregame.rule.v3' or output.get('section')!='MOVEMENT':continue
        for row in output.get('movement',[]):
            t=deepcopy(trace);t['output']['movement']=[deepcopy(row)];t['status']='UNKNOWN'
            upstream_reasons=list(t.get('reasons',[]));reasons=[];patch=draft.get('patch');champion=_subject_champion(row,draft)
            if trace.get('status') not in ('APPLIED','CONFLICTING') or trace.get('review_state')!='REVIEWED' or trace.get('condition')!='TRUE':reasons.append('MOVEMENT_RULE_NOT_APPLIED')
            if patch is None or patch not in spec.get('patches',[]):reasons.append('MOVEMENT_PATCH_MISMATCH')
            sources=trace.get('sources',[])
            if not any(s.get('patch')==patch and _hash(s.get('sha256')) and (s.get('kind')!='SYNTHETIC' or test_mode) for s in sources):reasons.append('MOVEMENT_SOURCE_UNBOUND')
            if not champion:reasons.append('MOVEMENT_SUBJECT_UNKNOWN')
            ref=row.get('statistics_ref');cohort=None
            if dataset is None:reasons.append(stats_reason)
            elif not ref or ref.get('dataset_sha256')!=digest(dataset):reasons.append('MOVEMENT_STATISTICS_BINDING_MISMATCH')
            else:
                cohort=next((c for c in dataset['cohorts'] if c['id']==ref.get('cohort_id')),None)
                signature=_conditions(row['stage_conditions'],row['stage'])
                if not cohort or cohort['champion']!=champion or cohort['position']!=row['position'] or cohort['patch']!=patch or cohort['tier']!=dataset['source']['tier'] or cohort['stage']!=row['stage'] or cohort['condition_signature']!=signature:
                    reasons.append('MOVEMENT_STATISTICS_COHORT_MISMATCH')
                elif not any(p['visible'] for p in cohort['points']):reasons.append('MOVEMENT_STATISTICS_INSUFFICIENT')
            if not reasons:
                t['status']=trace['status'];t['movement_statistics']=dict(dataset_sha256=digest(dataset),cohort_id=cohort['id'],
                    source=deepcopy(dataset['source']),points=deepcopy(cohort['points']))
            t['reasons']=sorted(set(upstream_reasons+reasons));cell['rules'].append(t)
    entries=cell['rules']
    # Only explicit higher-layer links with exactly the same conditional subject can replace a row.
    def key(t):
        r=t['output']['movement'][0]
        return r['stage'],r['subject'],r['position'],canonical(_conditions(r['stage_conditions'],r['stage']))
    def meaning(t):
        r=t['output']['movement'][0]
        return canonical({k:r[k] for k in ('location','role','why','exceptions')})
    eligible=[t for t in entries if t['status']=='APPLIED']
    for lower in eligible:
        l=lower['output']['movement'][0]
        for higher in eligible:
            h=higher['output']['movement'][0]
            if lower['rule_id'] in h['overrides'] and key(lower)==key(higher) and LAYERS.index(h['layer'])>LAYERS.index(l['layer']):
                lower['status']='OVERRIDDEN';lower['reasons'].append('MOVEMENT_EXPLICIT_OVERRIDE:'+higher['rule_id']);break
    remaining=[t for t in entries if t['status'] in ('APPLIED','CONFLICTING')]
    for i,a in enumerate(remaining):
        for b in remaining[i+1:]:
            if key(a)==key(b) and meaning(a)!=meaning(b):
                for t in (a,b):
                    t['status']='CONFLICTING';t['reasons']=sorted(set(t['reasons']+['MOVEMENT_LAYER_CONFLICT']))
    cell['status']='CONFLICTING' if any(t['status']=='CONFLICTING' for t in entries) else 'KNOWN' if any(t['status']=='APPLIED' for t in entries) else 'UNKNOWN'
    cell['texts']=list(dict.fromkeys(t['output']['movement'][0]['role'] for t in entries if t['status']=='APPLIED'))
    cell['reasons']=sorted({r for t in entries for r in t['reasons']}) or ([] if entries else ['NO_APPLICABLE_REVIEWED_MOVEMENT_RULE'])
    return cell

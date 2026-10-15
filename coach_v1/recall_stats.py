"""Anonymous descriptive purchase/low-health observations, never live advice.

Raw Match-V5 payloads remain in the caller's private memory. Only aggregated,
strictly validated datasets may be persisted publicly. First purchases estimate
recall completion; no recall starts, wave state or intent are reconstructed.
"""
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import math
import re
from datetime import datetime

POPULATIONS = ('CHALLENGER', 'PRO_REFERENCE')
ROLES = ('TOP', 'JUNGLE', 'MID', 'BOTTOM', 'SUPPORT')
ROLE_MAP = {**{p:p for p in ROLES}, 'MIDDLE':'MID', 'UTILITY':'SUPPORT'}
OUTCOMES = ('self_deaths', 'opponent_other_lane_involvements',
            'opponent_plates', 'opponent_jungle_objectives')
LIMITATIONS = [
    'DESCRIPTIVE_NON_CAUSAL_NOT_MISTAKE_OR_INTENT',
    'OPERATIONAL_THRESHOLDS_NOT_GAMEPLAY_RECOMMENDATIONS',
    'FIVE_MATCH_MINIMUM_NOT_STATISTICAL_SUFFICIENCY',
    'MATCH_CLUSTERED_NO_CONFIDENCE_OR_COACHING_ACCURACY_CLAIM',
    'PURCHASE_PROXY_MISSES_RECALLS_WITHOUT_PURCHASES',
    'EXACT_RECALL_START_AND_COMPLETION_UNKNOWN',
    'CURRENT_GOLD_IS_PRECEDING_FRAME_NOT_PURCHASE_INSTANT',
    'WAVE_STATE_INTENT_COMPONENT_INVENTORY_AND_DISCOUNTS_UNKNOWN',
    'LANE_GEOMETRY_IS_OBSERVATION_NOT_WAVE_OR_TACTICAL_STATE',
    'ACTION_GROUPS_OBSERVATIONAL_SELECTION_AND_SURVIVORSHIP_BIAS',
    'OVERLAPPING_PARTICIPANT_WINDOWS_MAY_COUNT_SAME_EVENT',
    'CHALLENGER_CURRENT_SEED_MATCH_COHORT_NOT_ALL_PARTICIPANT_RANKS',
    'PRO_REFERENCE_SELECTED_PARTICIPANTS_ONLY_NOT_ALL_MATCH_PLAYERS',
]
POLICY = dict(
    source='RIOT_MATCH_V5_TIMELINE_AND_contracts/queue-v23.md',
    first_purchase_after_ms=120000, bundle_window_ms=30000,
    health_ratio=.30, outcome_window_ms=120000,
    sensitivity_health_ratios=[.20,.30,.40], sensitivity_windows_ms=[60000,120000,180000],
    minimum_matches=5, minimum_match_basis='DISTINCT_VALID_FIRST_PURCHASE_TIMING_MATCHES', thresholds_are_advice=False,
    lane_geometry=dict(top='x<3000 and 4500<y<12500 OR y>12000 and 2500<x<10000',
                       bottom='y<3000 and 4500<x<12500 OR x>12000 and 2500<y<10000',
                       mid='3500<=x,y<=11500 and abs(x-y)<=1800',
                       bases_excluded='x+y<6000 OR x+y>24000', support='BOTTOM'),
    low_health_sampling='FIRST_LOW_HEALTH_FRAME_PER_PARTICIPANT_PER_SENSITIVITY_CELL',
    action_rule='PURCHASE_BEFORE_NEXT_FRAME_AND_DEATH_ELSE_NEXT_FRAME_IN_OWN_LANE_BEFORE_DEATH',
    outcome_rule='(START,START+WINDOW] COMPLETE_RECEIVED_FRAME_COVERAGE_REQUIRED',
    priority_rule='EARLIER_FIRST_PURCHASE_THAN_OPPOSITE_TEAM_SAME_POSITION',
    aggregation='MATCH_CLUSTERED_COUNTS;PARTICIPANT_QUANTILES;MATCH_WEIGHTED_OUTCOME_MEANS',
    gold_rule='LATEST_RECEIVED_FRAME_STRICTLY_BEFORE_PURCHASE')


def _require(ok, message='invalid recall dataset'):
    if not ok: raise ValueError(message)


def _number(value):return type(value) in (int,float) and math.isfinite(value)

def _integer(value, minimum=0):return type(value) is int and value>=minimum

def _keys(value, required):
    _require(isinstance(value,dict) and set(value)==set(required))


def _champion(value):return isinstance(value,str) and bool(re.fullmatch(r'[A-Za-z][A-Za-z0-9]{0,29}',value))


def _lane(position):
    if not isinstance(position,dict):return None
    x,y=position.get('x'),position.get('y')
    if not all(_number(v) and 0<=v<=16000 for v in (x,y)):return None
    if x+y<6000 or x+y>24000:return None
    if (x<3000 and 4500<y<12500) or (y>12000 and 2500<x<10000):return 'TOP'
    if (y<3000 and 4500<x<12500) or (x>12000 and 2500<y<10000):return 'BOTTOM'
    if 3500<=x<=11500 and 3500<=y<=11500 and abs(x-y)<=1800:return 'MID'
    return None


def _pf(frame,pid):
    values=frame.get('participantFrames',{})
    if not isinstance(values,dict):return {}
    value=values.get(str(pid),values.get(pid,{}))
    return value if isinstance(value,dict) else {}


def _health(frame,pid):
    pf=_pf(frame,pid);stats=pf.get('championStats',pf)
    if not isinstance(stats,dict):return None
    h,m=stats.get('health'),stats.get('healthMax')
    if not (_number(h) and _number(m) and m>0 and 0<h<=m):return None
    return h/m


def _unknown_first(reason):
    return dict(status='UNKNOWN',reason=reason,timestamp_ms=None,item_ids=[],current_gold=None,
                gold_frame_timestamp_ms=None,timing_kind='FIRST_PURCHASE_PROXY',priority_gap=None)


def _purchases(events,pid):
    purchases=[]
    for event in events:
        if event.get('participantId')!=pid:continue
        if event['type']=='ITEM_PURCHASED' and _integer(event.get('itemId'),1):
            purchases.append((event['timestamp'],event['itemId']))
        elif event['type']=='ITEM_UNDO':
            # beforeId is the item being undone; afterId restores a sale/upgrade,
            # not evidence of a new shop visit. Never turn it into a purchase.
            for i in range(len(purchases)-1,-1,-1):
                if purchases[i][1]==event.get('beforeId'):
                    purchases.pop(i);break
    return purchases


def _first_recall(pid,frames,events,purchases):
    eligible=[p for p in purchases if p[0]>POLICY['first_purchase_after_ms']]
    if not eligible:return _unknown_first('NO_POST_OPENING_PURCHASE')
    timestamp=eligible[0][0]
    if any(e['type']=='CHAMPION_KILL' and e.get('victimId')==pid and e['timestamp']<=timestamp for e in events):
        return _unknown_first('DEATH_BEFORE_FIRST_PURCHASE')
    next_death=min((e['timestamp'] for e in events if e['type']=='CHAMPION_KILL' and e.get('victimId')==pid and e['timestamp']>timestamp),default=math.inf)
    bundle=[item for time,item in eligible if time<=timestamp+POLICY['bundle_window_ms'] and time<next_death]
    previous=next((f for f in reversed(frames) if f['timestamp']<timestamp),None)
    gold=_pf(previous,pid).get('currentGold') if previous else None
    if not (_number(gold) and gold>=0):gold=None
    return dict(status='OBSERVED',reason=None,timestamp_ms=timestamp,item_ids=sorted(bundle),
                current_gold=gold,gold_frame_timestamp_ms=previous['timestamp'] if previous else None,
                timing_kind='FIRST_PURCHASE_PROXY',priority_gap=None)


def _outcomes(pid,opponent,own_role,team,players,events,start,window,coverage):
    counts={key:0 for key in OUTCOMES};missing=set()
    if opponent is None or own_role=='JUNGLE':missing.add('opponent_other_lane_involvements')
    enemy_team=200 if team==100 else 100
    own_lane='BOTTOM' if own_role=='SUPPORT' else own_role
    for event in events:
        if not start<event['timestamp']<=start+window:continue
        kind=event['type']
        if kind=='CHAMPION_KILL':
            if event.get('victimId')==pid:counts['self_deaths']+=1
            assists=event.get('assistingParticipantIds',[])
            assists=assists if isinstance(assists,list) else []
            if opponent is not None and (event.get('killerId')==opponent or opponent in assists):
                lane=_lane(event.get('position'))
                if lane is None:missing.add('opponent_other_lane_involvements')
                elif lane!=own_lane:counts['opponent_other_lane_involvements']+=1
        if kind not in ('TURRET_PLATE_DESTROYED','ELITE_MONSTER_KILL'):continue
        key='opponent_plates' if kind=='TURRET_PLATE_DESTROYED' else 'opponent_jungle_objectives'
        killer=players.get(event.get('killerId'),{})
        actor=killer.get('teamId',event.get('killerTeamId'))
        if actor not in (100,200) and kind=='TURRET_PLATE_DESTROYED' and event.get('teamId') in (100,200):
            actor=300-event['teamId']
        if actor not in (100,200):missing.add(key);continue
        if actor!=enemy_team:continue
        pos=event.get('position')
        if not isinstance(pos,dict) or not all(_number(pos.get(k)) for k in ('x','y')):missing.add(key)
        else:counts[key]+=1
    return {key:dict(value=None if coverage<start+window or key in missing else count,
                     observed=count,reason='INCOMPLETE_WINDOW' if coverage<start+window else
                     'EVENT_LOCATION_OR_ACTOR_UNKNOWN' if key in missing else None)
            for key,count in counts.items()}


def _low(pid,p,opponent,frames,events,purchases,players,ratio,window,coverage):
    base=dict(health_ratio=ratio,window_ms=window,status='EXCLUDED',reason=None,action=None,
              timestamp_ms=None,action_timestamp_ms=None,outcomes=None,signal=None)
    if p['position']=='JUNGLE':base['reason']='JUNGLE_EXCLUDED';return base
    health=[(i,_health(frame,pid)) for i,frame in enumerate(frames)]
    trigger=next((i for i,h in health if h is not None and h<=ratio),None)
    if trigger is None:
        base['reason']='NO_LOW_HEALTH_FRAME' if any(h is not None for _,h in health) else 'HEALTH_UNOBSERVED';return base
    start=frames[trigger]['timestamp'];base['timestamp_ms']=start
    if trigger+1>=len(frames):base['reason']='NEXT_FRAME_UNOBSERVED';return base
    next_frame=frames[trigger+1];next_time=next_frame['timestamp']
    deaths=[e['timestamp'] for e in events if e['type']=='CHAMPION_KILL' and e.get('victimId')==pid and e['timestamp']>=start]
    first_death=min(deaths,default=math.inf)
    purchase=next((time for time,_ in purchases if start<time<=min(start+window,next_time) and time<first_death),None)
    if purchase is not None:action='PURCHASE';action_time=purchase
    elif first_death<=next_time:
        base['reason']='DEATH_BEFORE_ACTION';return base
    elif next_time>start+window:
        base['reason']='NEXT_FRAME_OUTSIDE_WINDOW';return base
    else:
        lane=_lane(_pf(next_frame,pid).get('position'))
        if lane is None:base['reason']='NEXT_FRAME_LANE_UNKNOWN';return base
        if lane!=('BOTTOM' if p['position']=='SUPPORT' else p['position']):
            base['reason']='NEXT_FRAME_NOT_OWN_LANE';return base
        action='STAY';action_time=next_time
    base.update(status='OBSERVED',action=action,action_timestamp_ms=action_time,
                outcomes=_outcomes(pid,opponent,p['position'],p['team'],players,events,start,window,coverage),
                signal='LOW_HEALTH_STAY_DEATH' if action=='STAY' else 'LOW_HEALTH_RECALL_OPPONENT_ROAM')
    return base


def extract_match(match,timeline,*,population,participant_ids=None):
    """Extract one anonymous match cluster; PRO_REFERENCE requires selected IDs."""
    _require(population in POPULATIONS,'unsupported population')
    return _extract_match(match,timeline,population=population,participant_ids=participant_ids)


def extract_private_context(match,timeline,participant_id):
    """Postgame individual observations, without assigning a reference population.

    This is not a dataset or permission to persist raw inputs. The returned
    selected observation contains no account, match or participant identifiers.
    """
    result=_extract_match(match,timeline,population='LOCAL_PRIVATE',participant_ids=[participant_id])
    return deepcopy(result['participants'][0])


def _extract_match(match,timeline,*,population,participant_ids=None):
    _require(population in POPULATIONS+('LOCAL_PRIVATE',),'unsupported population')
    _require(isinstance(match,dict) and isinstance(timeline,dict),'invalid Match-V5 input')
    _require(all(isinstance(raw.get(key),dict) for raw in (match,timeline) for key in ('metadata','info')),'malformed Match-V5 envelope')
    mid=match['metadata'].get('matchId')
    _require(isinstance(mid,str) and mid and timeline.get('metadata',{}).get('matchId')==mid,'match/timeline identity mismatch')
    info=match.get('info',{});raw_frames=timeline.get('info',{}).get('frames')
    _require(info.get('queueId')==420 and info.get('mapId')==11,'only ranked Summoners Rift supported')
    version=info.get('gameVersion','');_require(isinstance(version,str) and re.fullmatch(r'\d+\.\d+(?:\..*)?',version),'invalid patch')
    patch='.'.join(version.split('.')[:2])
    _require(isinstance(info.get('participants'),list) and isinstance(raw_frames,list),'missing participants/frames')
    players={}
    for raw in info['participants']:
        _require(isinstance(raw,dict) and _integer(raw.get('participantId'),1),'invalid participant')
        pid=raw['participantId'];_require(pid<=10 and pid not in players,'duplicate/invalid participant ID')
        role=ROLE_MAP.get(raw.get('teamPosition') or raw.get('individualPosition'))
        if role is None:continue
        _require(_champion(raw.get('championName')) and raw.get('teamId') in (100,200),'invalid champion/team')
        players[pid]=dict(champion=raw['championName'],position=role,team=raw['teamId'],teamId=raw['teamId'])
    if participant_ids is None:
        _require(population!='PRO_REFERENCE','PRO_REFERENCE requires selected participant IDs')
        selected=set(players)
    else:
        _require(isinstance(participant_ids,list) and participant_ids and all(_integer(i,1) and i<=10 for i in participant_ids),'invalid participant selector')
        _require(len(set(participant_ids))==len(participant_ids) and set(participant_ids)<=set(players),'unknown/duplicate participant selector')
        selected=set(participant_ids)
    frames=sorted([f for f in raw_frames if isinstance(f,dict) and _number(f.get('timestamp')) and f['timestamp']>=0],key=lambda f:f['timestamp'])
    _require(frames and len({f['timestamp'] for f in frames})==len(frames),'missing/duplicate frames')
    _require(all(isinstance(f.get('events'),list) for f in frames),'missing timeline event stream')
    events=sorted([e for f in frames for e in (f.get('events',[]) if isinstance(f.get('events',[]),list) else [])
                   if isinstance(e,dict) and isinstance(e.get('type'),str) and _number(e.get('timestamp')) and 0<=e['timestamp']<=frames[-1]['timestamp']],key=lambda e:e['timestamp'])
    purchases={pid:_purchases(events,pid) for pid in players}
    firsts={pid:_first_recall(pid,frames,events,purchases[pid]) for pid in players}
    observations=[]
    for pid in sorted(selected):
        p=players[pid];opponents=[i for i,o in players.items() if o['team']!=p['team'] and o['position']==p['position']]
        opponent=opponents[0] if len(opponents)==1 else None
        first=firsts[pid]
        if first['status']=='OBSERVED':
            other=firsts.get(opponent,{})
            if other.get('status')!='OBSERVED':gap=dict(status='UNKNOWN',reason='OPPONENT_FIRST_PURCHASE_UNKNOWN',gap_ms=None,outcomes=None,signal='FIRST_RECALL_PRIORITY_GAP')
            else:
                difference=other['timestamp_ms']-first['timestamp_ms']
                gap=dict(status='OBSERVED' if difference>0 else 'NOT_EARLIER',reason=None,gap_ms=difference,
                         outcomes=_outcomes(pid,opponent,p['position'],p['team'],players,events,first['timestamp_ms'],120000,frames[-1]['timestamp']) if difference>0 else None,
                         signal='FIRST_RECALL_PRIORITY_GAP')
            first['priority_gap']=gap
        sensitivity=[_low(pid,p,opponent,frames,events,purchases[pid],players,ratio,window,frames[-1]['timestamp']) for ratio in (.2,.3,.4) for window in (60000,120000,180000)]
        low=deepcopy(next(s for s in sensitivity if s['health_ratio']==.3 and s['window_ms']==120000))
        if population=='LOCAL_PRIVATE' and low['status']=='OBSERVED':
            # Individual 'after purchase' signals must not count a roam that
            # preceded the purchase. Preserve the original trigger-window end;
            # starting later must not extend coverage or admit later events.
            action_time=low['action_timestamp_ms']
            remaining=low['timestamp_ms']+low['window_ms']-action_time
            low['post_action_outcomes']=_outcomes(pid,opponent,p['position'],p['team'],players,
                                                  events,action_time,remaining,frames[-1]['timestamp'])
        observations.append(dict(champion=p['champion'],position=p['position'],first_recall=first,
                                 low_health=low,sensitivity=sensitivity))
    return dict(population=population,patch=patch,cluster_key=hashlib.sha256(mid.encode()).hexdigest(),participants=observations,exclusions=[])


def _quantile(values,p):
    ordered=sorted(values);index=(len(ordered)-1)*p;low=math.floor(index);high=math.ceil(index)
    return ordered[low]+(ordered[high]-ordered[low])*(index-low)


def _distribution(rows,getter,unit):
    values=[(cluster,getter(p)) for cluster,p in rows];valid=[(c,v) for c,v in values if v is not None]
    numeric=[v for _,v in valid]
    match_n=len({c for c,_ in valid})
    return dict(status='AVAILABLE' if match_n>=5 else 'UNKNOWN',reason=None if match_n>=5 else 'VALID_MATCH_N_LT_5',
                n=len(valid),match_n=match_n,missing_n=len(rows)-len(valid),
                median=_quantile(numeric,.5) if numeric else None,q1=_quantile(numeric,.25) if numeric else None,
                q3=_quantile(numeric,.75) if numeric else None,unit=unit)


def _aggregate_outcomes(rows):
    result={}
    for metric in OUTCOMES:
        clusters=defaultdict(list);missing=0;observed=0
        for cluster,outcomes in rows:
            datum=outcomes[metric];observed+=datum['observed']
            if datum['value'] is None:missing+=1
            else:clusters[cluster].append(datum['value'])
        means=[sum(v)/len(v) for v in clusters.values()]
        result[metric]=dict(status='AVAILABLE' if clusters else 'UNKNOWN',
                            reason=None if clusters else 'NO_COMPLETE_OBSERVED_WINDOWS',n=len(clusters),participant_n=sum(map(len,clusters.values())),missing_n=missing,
                            mean=sum(means)/len(means) if means else None,
                            total=sum(sum(v) for v in clusters.values()) if means else None,
                            observed_total=observed,unit='EVENTS_PER_PARTICIPANT_WINDOW_MATCH_WEIGHTED')
    return result


def _low_summary(rows,getter):
    states=[(cluster,getter(p)) for cluster,p in rows]
    result={}
    for action in ('PURCHASE','STAY'):
        chosen=[(c,p) for c,p in states if p['status']=='OBSERVED' and p['action']==action]
        result[action.lower()]=dict(matches=len({c for c,_ in chosen}),participant_observations=len(chosen),
                                     outcomes=_aggregate_outcomes([(c,p['outcomes']) for c,p in chosen]),
                                     signal='LOW_HEALTH_STAY_DEATH' if action=='STAY' else 'LOW_HEALTH_RECALL_OPPONENT_ROAM')
    result['excluded']=[dict(reason=reason,count=count) for reason,count in sorted(Counter(p['reason'] for _,p in states if p['status']!='OBSERVED').items())]
    return result


def _cohort(patch,champion,position,rows):
    bundles=defaultdict(list)
    for cluster,p in rows:
        first=p['first_recall']
        if first['status']=='OBSERVED':bundles[tuple(first['item_ids'])].append(cluster)
    gaps=[(c,p['first_recall']['priority_gap']) for c,p in rows if p['first_recall']['priority_gap'] is not None]
    earlier=[(c,g) for c,g in gaps if g['status']=='OBSERVED']
    first=dict(timing=_distribution(rows,lambda p:p['first_recall']['timestamp_ms'],'MILLISECONDS'),
               current_gold=_distribution(rows,lambda p:p['first_recall']['current_gold'],'GOLD_PRECEDING_FRAME'),
               purchases=[dict(item_ids=list(items),count=len(clusters),matches=len(set(clusters))) for items,clusters in sorted(bundles.items(),key=lambda pair:(-len(pair[1]),pair[0]))],
               exclusions=[dict(reason=r,count=n) for r,n in sorted(Counter(p['first_recall']['reason'] for _,p in rows if p['first_recall']['status']!='OBSERVED').items())],
               priority_gap=dict(matches=len({c for c,_ in earlier}),participant_observations=len(earlier),
                                 unknown_n=len(rows)-len(gaps)+sum(g['status']=='UNKNOWN' for _,g in gaps),
                                 not_earlier_n=sum(g['status']=='NOT_EARLIER' for _,g in gaps),
                                 timing=_distribution(earlier,lambda g:g['gap_ms'],'MILLISECONDS'),
                                 outcomes=_aggregate_outcomes([(c,g['outcomes']) for c,g in earlier]),signal='FIRST_RECALL_PRIORITY_GAP'))
    return dict(patch=patch,champion=champion,position=position,matches=len({c for c,_ in rows}),participant_observations=len(rows),
                first_recall=first,low_health=_low_summary(rows,lambda p:p['low_health']),
                sensitivity=[dict(health_ratio=h,window_ms=w,**_low_summary(rows,lambda p,i=i:p['sensitivity'][i])) for i,(h,w) in enumerate((h,w) for h in (.2,.3,.4) for w in (60000,120000,180000))])


def build_dataset(observations,*,population,retrieved_at):
    """Deduplicate match clusters and separate populations, patches and positions."""
    _require(population in POPULATIONS,'unsupported population')
    groups=defaultdict(list);seen={};participant_count=0
    for observation in observations:
        _keys(observation,('population','patch','cluster_key','participants','exclusions'))
        _require(observation['population']==population,'cannot mix populations')
        cluster=observation['cluster_key'];_require(isinstance(cluster,str) and re.fullmatch('[a-f0-9]{64}',cluster),'invalid match cluster')
        if cluster in seen:
            _require(seen[cluster]==observation,'conflicting duplicate match cluster');continue
        seen[cluster]=deepcopy(observation)
        for p in observation['participants']:
            _keys(p,('champion','position','first_recall','low_health','sensitivity'))
            participant_count+=1
            for champion in (p['champion'],None):groups[(observation['patch'],champion,p['position'])].append((cluster,p))
    cohorts=[_cohort(patch,champion,position,rows) for (patch,champion,position),rows in sorted(groups.items(),key=lambda pair:(pair[0][0],pair[0][2],pair[0][1] or ''))]
    return validate_dataset(dict(schema_version='recall-observations.v1',population=population,retrieved_at=retrieved_at,
                                 samples=dict(matches=len(seen),participant_observations=participant_count),
                                 measurement_policy=deepcopy(POLICY),limitations=list(LIMITATIONS),cohorts=cohorts))


def _validate_distribution(d,total):
    _keys(d,('status','reason','n','match_n','missing_n','median','q1','q3','unit'))
    _require(all(_integer(d[k]) for k in ('n','match_n','missing_n')))
    _require(d['status']==('AVAILABLE' if d['match_n']>=5 else 'UNKNOWN'))
    _require(d['reason']==(None if d['match_n']>=5 else 'VALID_MATCH_N_LT_5'))
    _require(d['n']+d['missing_n']==total and d['match_n']<=d['n'])
    _require(d['unit'] in ('MILLISECONDS','GOLD_PRECEDING_FRAME'))
    values=[d[k] for k in ('q1','median','q3')]
    if d['n']:_require(all(_number(v) and v>=0 for v in values) and values==sorted(values) and d['match_n']>=1)
    else:_require(values==[None,None,None] and d['match_n']==0)


def _validate_outcomes(outcomes,total,matches):
    _keys(outcomes,OUTCOMES)
    for d in outcomes.values():
        _keys(d,('status','reason','n','participant_n','missing_n','mean','total','observed_total','unit'))
        _require(all(_integer(d[k]) for k in ('n','participant_n','missing_n','observed_total')))
        _require(d['n']<=matches and d['n']<=d['participant_n'] and d['participant_n']+d['missing_n']==total)
        _require(d['unit']=='EVENTS_PER_PARTICIPANT_WINDOW_MATCH_WEIGHTED')
        _require(d['status']==('AVAILABLE' if d['n'] else 'UNKNOWN'))
        _require(d['reason']==(None if d['n'] else 'NO_COMPLETE_OBSERVED_WINDOWS'))
        if d['n']:_require(_number(d['mean']) and d['mean']>=0 and _integer(d['total']) and d['total']<=d['observed_total'] and d['n']>0)
        else:_require(d['mean'] is None and d['total'] is None and d['participant_n']==0)


def _validate_exclusions(exclusions,allowed):
    _require(isinstance(exclusions,list));seen=set();total=0
    for e in exclusions:
        _keys(e,('reason','count'));_require(e['reason'] in allowed and e['reason'] not in seen and _integer(e['count'],1))
        seen.add(e['reason']);total+=e['count']
    return total


def _validate_low(low,total,matches):
    _keys(low,('purchase','stay','excluded'));counts=[]
    for action in ('purchase','stay'):
        group=low[action];_keys(group,('matches','participant_observations','outcomes','signal'))
        n=group['participant_observations'];m=group['matches']
        _require(_integer(n) and _integer(m) and m<=matches and m<=n<=total and n<=2*m)
        _require(group['signal']==('LOW_HEALTH_STAY_DEATH' if action=='stay' else 'LOW_HEALTH_RECALL_OPPONENT_ROAM'))
        _validate_outcomes(group['outcomes'],n,m);counts.append(n)
    excluded=_validate_exclusions(low['excluded'],('JUNGLE_EXCLUDED','HEALTH_UNOBSERVED','NO_LOW_HEALTH_FRAME','NEXT_FRAME_UNOBSERVED','DEATH_BEFORE_ACTION','NEXT_FRAME_OUTSIDE_WINDOW','NEXT_FRAME_LANE_UNKNOWN','NEXT_FRAME_NOT_OWN_LANE'))
    _require(sum(counts)+excluded==total)


def validate_dataset(data):
    """Strict allowlist of public aggregate keys and enum/value constraints."""
    _keys(data,('schema_version','population','retrieved_at','samples','measurement_policy','limitations','cohorts'))
    _require(data['schema_version']=='recall-observations.v1' and data['population'] in POPULATIONS)
    _require(isinstance(data['retrieved_at'],str))
    try:datetime.fromisoformat(data['retrieved_at'].replace('Z','+00:00'))
    except (ValueError,TypeError):raise ValueError('invalid retrieval timestamp') from None
    _require(data['measurement_policy']==POLICY and data['limitations']==LIMITATIONS)
    _keys(data['samples'],('matches','participant_observations'))
    sample=data['samples'];_require(all(_integer(v) for v in sample.values()) and sample['matches']<=sample['participant_observations']<=10*sample['matches'])
    _require(isinstance(data['cohorts'],list));seen=set();exact_n=0;role_n=0
    for c in data['cohorts']:
        _keys(c,('patch','champion','position','matches','participant_observations','first_recall','low_health','sensitivity'))
        _require(isinstance(c['patch'],str) and re.fullmatch(r'\d+\.\d+',c['patch']) and c['position'] in ROLES)
        _require(c['champion'] is None or _champion(c['champion']))
        key=(c['patch'],c['champion'],c['position']);_require(key not in seen);seen.add(key)
        n=c['participant_observations'];m=c['matches']
        _require(_integer(n,1) and _integer(m,1) and m<=sample['matches'] and m<=n<=2*m)
        if c['champion'] is None:role_n+=n
        else:exact_n+=n
        first=c['first_recall'];_keys(first,('timing','current_gold','purchases','exclusions','priority_gap'))
        _validate_distribution(first['timing'],n);_validate_distribution(first['current_gold'],n)
        _require(first['current_gold']['n']<=first['timing']['n'])
        _require(isinstance(first['purchases'],list));bundle_count=0;bundle_seen=set()
        for purchase in first['purchases']:
            _keys(purchase,('item_ids','count','matches'));ids=purchase['item_ids']
            _require(isinstance(ids,list) and ids and all(_integer(i,1) for i in ids) and ids==sorted(ids))
            _require(tuple(ids) not in bundle_seen);bundle_seen.add(tuple(ids))
            _require(_integer(purchase['count'],1) and _integer(purchase['matches'],1) and purchase['matches']<=m and purchase['matches']<=purchase['count']<=n)
            bundle_count+=purchase['count']
        excluded=_validate_exclusions(first['exclusions'],('NO_POST_OPENING_PURCHASE','DEATH_BEFORE_FIRST_PURCHASE'))
        _require(bundle_count==first['timing']['n'] and excluded+bundle_count==n)
        gap=first['priority_gap'];_keys(gap,('matches','participant_observations','unknown_n','not_earlier_n','timing','outcomes','signal'))
        _require(all(_integer(gap[k]) for k in ('matches','participant_observations','unknown_n','not_earlier_n')) and gap['matches']<=m and gap['matches']<=gap['participant_observations']<=2*gap['matches'])
        _require(gap['participant_observations']+gap['unknown_n']+gap['not_earlier_n']==n and gap['signal']=='FIRST_RECALL_PRIORITY_GAP')
        _validate_distribution(gap['timing'],gap['participant_observations']);_validate_outcomes(gap['outcomes'],gap['participant_observations'],gap['matches'])
        _validate_low(c['low_health'],n,m)
        _require(isinstance(c['sensitivity'],list) and len(c['sensitivity'])==9)
        for s,(h,w) in zip(c['sensitivity'],((h,w) for h in (.2,.3,.4) for w in (60000,120000,180000))):
            _keys(s,('health_ratio','window_ms','purchase','stay','excluded'))
            _require(s['health_ratio']==h and s['window_ms']==w)
            _validate_low({k:s[k] for k in ('purchase','stay','excluded')},n,m)
    _require(exact_n==role_n==sample['participant_observations'])
    return deepcopy(data)


def recall_view(data,*,champion,position,patch):
    """Same-population/same-patch exact -> pooled role -> UNKNOWN at <5 matches."""
    data=validate_dataset(data);role=ROLE_MAP.get(position)
    _require(_champion(champion) and role is not None,'invalid champion/position')
    _require(isinstance(patch,str) and re.fullmatch(r'\d+\.\d+',patch),'invalid patch')
    exact=next((c for c in data['cohorts'] if (c['champion'],c['position'],c['patch'])==(champion,role,patch)),None)
    pooled=next((c for c in data['cohorts'] if (c['champion'],c['position'],c['patch'])==(None,role,patch)),None)
    chosen=exact if exact and exact['first_recall']['timing']['match_n']>=5 else pooled if pooled and pooled['first_recall']['timing']['match_n']>=5 else None
    sample=chosen or pooled or exact
    return dict(status='AVAILABLE' if chosen else 'UNKNOWN',population=data['population'],patch=patch,champion=champion,position=role,
                scope='CHAMPION' if chosen is exact and chosen else 'ROLE' if chosen else 'UNKNOWN',
                reason=None if chosen is exact and chosen else 'EXACT_CHAMPION_N_LT_5_ROLE_FALLBACK' if chosen else 'VALID_RECALL_MATCH_N_LT_5' if sample else 'NO_SAME_PATCH_ROLE_OBSERVATIONS',
                sample=dict(matches=sample['matches'] if sample else 0,participant_observations=sample['participant_observations'] if sample else 0),
                first_recall=chosen['first_recall'] if chosen else None,low_health=chosen['low_health'] if chosen else None,
                sensitivity=chosen['sensitivity'] if chosen else [],measurement_policy=data['measurement_policy'],limitations=data['limitations'])

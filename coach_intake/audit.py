"""Diagnostic extraction only: observed fields are never decision-ready evidence."""
from .io import strict_json,sha

def inspect(raw,declared_kind='UNVERIFIED_IMPORT',expected_sha=None):
    if declared_kind not in ('DOCUMENTATION_SAMPLE','UNVERIFIED_LOCAL_CAPTURE','UNVERIFIED_IMPORT'):raise ValueError('SOURCE_KIND')
    if expected_sha is not None and sha(raw)!=expected_sha:raise ValueError('HASH_MISMATCH')
    data=strict_json(raw)
    if not isinstance(data,dict):raise ValueError('OBJECT_REQUIRED')
    issues=[];sections={}
    for key,t in (('activePlayer',dict),('allPlayers',list),('events',dict),('gameData',dict)):
        sections[key]='MISSING' if key not in data else 'NULL' if data[key] is None else 'PRESENT' if type(data[key]) is t else 'WRONG_TYPE'
        if sections[key]!='PRESENT':issues.append(key+':'+sections[key])
    def at(*keys):
        v=data
        for key in keys:
            if not isinstance(v,dict) or key not in v:return None,'MISSING'
            v=v[key]
        return v,'NULL' if v is None else 'PRESENT'
    facts=[]
    # An allowlist excludes names/IDs from this shareable diagnostic report.
    for label,keys in (
        ('game_time_seconds',('gameData','gameTime')),
        ('active_health',('activePlayer','championStats','currentHealth')),
        ('active_max_health',('activePlayer','championStats','maxHealth')),
        ('active_gold',('activePlayer','currentGold')),
        ('active_level',('activePlayer','level'))):
        value,status=at(*keys)
        if status=='PRESENT' and (type(value) not in (int,float) or value<0):status='INVALID';value=None
        facts.append(dict(field=label,pointer='/'+'/'.join(keys),state=status,value=value,decision_eligible=False))
        if status!='PRESENT':issues.append(label+':'+status)
    health,maxhealth=facts[1]['value'],facts[2]['value']
    if maxhealth==0:issues.append('MAX_HEALTH_ZERO_SEMANTICS_UNVERIFIED')
    if health is not None and maxhealth is not None and health>maxhealth:issues.append('HEALTH_EXCEEDS_MAX')
    events=data.get('events',{});events=events.get('Events') if isinstance(events,dict) else None
    end_count=0
    if not isinstance(events,list):issues.append('EVENT_LIST_MISSING_OR_INVALID')
    else:
        seen=set()
        for event in events:
            if not isinstance(event,dict):issues.append('EVENT_INVALID');continue
            eid=event.get('EventID');time=event.get('EventTime')
            if type(eid) is not int or eid<0 or eid in seen:issues.append('EVENT_ID_INVALID_OR_DUPLICATE')
            else:seen.add(eid)
            if type(time) not in (int,float) or time<0:issues.append('EVENT_TIME_INVALID')
            elif facts[0]['state']=='PRESENT' and time>facts[0]['value']:issues.append('EVENT_AFTER_SNAPSHOT')
            if event.get('EventName')=='GameEnd':end_count+=1
    players=data.get('allPlayers')
    if isinstance(players,list) and any(not isinstance(p,dict) for p in players):issues.append('PLAYER_ENTRY_INVALID')
    return dict(format='lol-coach-intake-audit-v1',declared_source_kind=declared_kind,raw_sha256=sha(raw),
        integrity_hash_matched=expected_sha is not None,source_authenticity_verified=False,
        sections=sections,player_count=len(players) if isinstance(players,list) else None,
        event_count=len(events) if isinstance(events,list) else None,raw_facts=facts,issues=sorted(set(issues)),
        game_end_markers_observed=end_count,game_end_verified=False,coaching_enabled=False,
        activation_blockers=['PATCH_NOT_VERIFIED','PLAYER_PERSPECTIVE_NOT_VERIFIED','EVENT_AVAILABILITY_NOT_VERIFIED','GAME_END_NOT_VERIFIED','SOURCE_SEMANTICS_NOT_VERIFIED'],
        note='Hash integrity is not source authentication. Documentation samples are not real-match validation.')

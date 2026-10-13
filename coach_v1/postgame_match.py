"""Private Match-V5 review. Minute samples describe records, never tactical blame."""
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import statistics
import stat
import tempfile

from .power_stats import ROLE_MAP, validate_power_dataset
from .movement import validate_movement_dataset, _annotations

MAX_BYTES=12_000_000
LIMITATIONS=['DESCRIPTIVE_NON_CAUSAL','MINUTE_SAMPLES_NO_INTERPOLATION','MINUTE_IS_NOT_PHASE',
             'VIDEO_UNVERIFIED','WAVE_STATE_UNKNOWN','UNSEEN_ENEMIES_UNKNOWN','SKILL_STATE_UNKNOWN',
             'KNOWN_ALLIES_MEDIAN_NOT_ACTUAL_MAIN_BODY','NO_WIN_LOSS_JUDGMENT']


def _require(ok,message='INVALID_PERSONAL_MATCH'):
    if not ok:raise ValueError(message)


def _number(v):return type(v) in (int,float) and math.isfinite(v)
def _integer(v,low=0):return type(v) is int and v>=low

def _xy(value):
    p=value.get('position') if isinstance(value,dict) else None
    return dict(x=p['x'],y=p['y']) if isinstance(p,dict) and all(_number(p.get(k)) and 0<=p[k]<=16000 for k in ('x','y')) else None


def _chmod_file(fd,path):
    # Windows chmod is best effort; NTFS ACL isolation must be set locally.
    if callable(getattr(os,'fchmod',None)):os.fchmod(fd,0o600)
    else:os.chmod(path,0o600)


def _validated(body,test_mode):
    _require(isinstance(body,dict) and {'match','timeline','participant_id'}<=set(body)<= {'match','timeline','participant_id','source','phase_annotations'})
    b=deepcopy(body);b.setdefault('source','REAL');_require(b['source'] in ('REAL','SYNTHETIC'))
    _require(test_mode or b['source']=='REAL','SYNTHETIC_IMPORT_REQUIRES_TEST_MODE')
    try:serialized=json.dumps(b,allow_nan=False,ensure_ascii=False).encode()
    except (ValueError,TypeError,OverflowError):raise ValueError('INVALID_PERSONAL_MATCH') from None
    _require(len(serialized)<=MAX_BYTES,'PERSONAL_MATCH_TOO_LARGE')
    match=b['match'];timeline=b['timeline'];_require(isinstance(match,dict) and isinstance(timeline,dict))
    mid=match.get('metadata',{}).get('matchId') if isinstance(match.get('metadata'),dict) else None
    _require(isinstance(mid,str) and re.fullmatch(r'(?:KR|JP1|NA1|BR1|LA1|LA2|EUW1|EUN1|TR1|RU|OC1|PH2|SG2|TH2|TW2|VN2|ME1)_[0-9]+',mid))
    _require(isinstance(timeline.get('metadata'),dict) and timeline['metadata'].get('matchId')==mid)
    info=match.get('info');ti=timeline.get('info');_require(isinstance(info,dict) and isinstance(ti,dict))
    _require(info.get('mapId')==11 and info.get('gameMode')=='CLASSIC','UNSUPPORTED_MAP_OR_MODE')
    _require(_number(info.get('gameDuration')) and 0<info['gameDuration']<=14400)
    _require(isinstance(info.get('gameVersion'),str) and re.fullmatch(r'[0-9]+\.[0-9]+(?:\.[0-9]+)*',info['gameVersion']))
    people=info.get('participants');_require(isinstance(people,list) and len(people)==10)
    _require(all(isinstance(p,dict) and _integer(p.get('participantId'),1) and 1<=p['participantId']<=10
        and isinstance(p.get('puuid'),str) and 1<=len(p['puuid'])<=200 and p.get('teamId') in (100,200)
        and (p.get('teamPosition') is None or isinstance(p['teamPosition'],str))
        and isinstance(p.get('championName'),str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9]{0,39}',p['championName']) for p in people))
    _require({p['participantId'] for p in people}==set(range(1,11)) and len({p['puuid'] for p in people})==10)
    _require(all(sum(p['teamId']==team for p in people)==5 for team in (100,200)))
    ids=[p['puuid'] for p in sorted(people,key=lambda p:p['participantId'])]
    _require(match['metadata'].get('participants')==ids and timeline['metadata'].get('participants')==ids,'PARTICIPANT_ROSTER_MISMATCH')
    _require(_integer(b['participant_id'],1) and b['participant_id']<=10)
    own=next(p for p in people if p['participantId']==b['participant_id'])
    timeline_people=ti.get('participants');_require(isinstance(timeline_people,list) and len(timeline_people)==10)
    _require(all(isinstance(p,dict) and _integer(p.get('participantId'),1) and isinstance(p.get('puuid'),str) for p in timeline_people))
    _require({(p.get('participantId'),p.get('puuid')) for p in timeline_people}=={(p['participantId'],p['puuid']) for p in people},'OWNER_NOT_IN_TIMELINE')
    _require(ti.get('frameInterval')==60000,'MINUTE_FRAME_INTERVAL_REQUIRED')
    frames=ti.get('frames');_require(isinstance(frames,list) and 1<=len(frames)<=245)
    previous=-1
    for frame in frames:
        _require(isinstance(frame,dict) and _integer(frame.get('timestamp')) and previous<frame['timestamp']<=info['gameDuration']*1000+60000)
        previous=frame['timestamp'];pf=frame.get('participantFrames');events=frame.get('events')
        _require(isinstance(pf,dict) and isinstance(events,list) and len(events)<=5000)
        for key,entry in pf.items():
            _require(key in {str(i) for i in range(1,11)} and isinstance(entry,dict))
            _require(_integer(entry.get('participantId'),1) and entry['participantId']==int(key))
            for metric in ('totalGold','xp','minionsKilled','jungleMinionsKilled','level'):
                if metric in entry:_require(_integer(entry[metric]))
            if 'position' in entry:_require(_xy(entry) is not None)
        for event in events:
            _require(isinstance(event,dict) and isinstance(event.get('type'),str) and _integer(event.get('timestamp'))
                and event['timestamp']<=info['gameDuration']*1000+60000)
            for key in ('participantId','creatorId','killerId','victimId'):
                if key in event:_require(_integer(event[key]) and event[key]<=10)
    mh=hashlib.sha256(mid.encode()).hexdigest()
    if b.get('phase_annotations'):
        _require(isinstance(b['phase_annotations'],list) and len(b['phase_annotations'])<=len(frames))
        _annotations(b['phase_annotations'])
        _require(all(a['match_sha256']==mh and a['timestamp_ms'] in {f['timestamp'] for f in frames} for a in b['phase_annotations']))
    return b,own,mh


class PostgameStore:
    def __init__(self,private_directory,test_mode=False):
        original=Path(private_directory).absolute();self.test_mode=bool(test_mode)
        _require('..' not in original.parts,'PRIVATE_PATH_TRAVERSAL_REJECTED')
        _require(not any(p.is_symlink() for p in [original,*original.parents]),'SYMLINK_PRIVATE_DIRECTORY')
        self.directory=original.resolve()
        _require('private' in self.directory.parts or self.test_mode,'PRIVATE_DIRECTORY_REQUIRED')
        _require(not any(p.is_symlink() for p in [self.directory,*self.directory.parents]),'SYMLINK_PRIVATE_DIRECTORY')
        self.directory.mkdir(parents=True,exist_ok=True,mode=0o700);os.chmod(self.directory,0o700)

    def _path(self,match_id):
        _require(isinstance(match_id,str) and re.fullmatch('[a-f0-9]{64}',match_id),'INVALID_MATCH_ID')
        path=self.directory/(match_id+'.json');_require(not path.is_symlink(),'SYMLINK_PRIVATE_FILE')
        return path

    def _load(self,match_id):
        path=self._path(match_id)
        try:
            before=path.lstat();_require(stat.S_ISREG(before.st_mode),'PRIVATE_FILE_MUST_BE_REGULAR')
            fd=os.open(path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_NONBLOCK',0))
            with os.fdopen(fd,'r',encoding='utf-8') as stream:
                _require(os.path.samestat(before,os.fstat(stream.fileno())),'PRIVATE_FILE_CHANGED_DURING_OPEN')
                _chmod_file(stream.fileno(),path);raw=stream.read(MAX_BYTES+1)
            _require(len(raw.encode())<=MAX_BYTES,'PERSONAL_MATCH_TOO_LARGE')
            body=json.loads(raw)
        except FileNotFoundError:raise KeyError('PERSONAL_MATCH_NOT_FOUND') from None
        except (OSError,json.JSONDecodeError):raise ValueError('INVALID_PRIVATE_MATCH_FILE') from None
        b,own,mh=_validated(body,self.test_mode);_require(self._id(mh,b['participant_id'])==match_id,'PRIVATE_ID_MISMATCH')
        return b,own,mh

    @staticmethod
    def _id(mh,participant_id):return hashlib.sha256((mh+':'+str(participant_id)).encode()).hexdigest()

    def _summary(self,b,own,mh):
        role=ROLE_MAP.get(own.get('teamPosition'))
        if role is None or sum(p['teamId']==own['teamId'] and ROLE_MAP.get(p.get('teamPosition'))==role for p in b['match']['info']['participants'])!=1:role='UNKNOWN'
        return dict(id=self._id(mh,b['participant_id']),champion=own['championName'],role=role,
            patch='.'.join(b['match']['info']['gameVersion'].split('.')[:2]),duration_seconds=b['match']['info']['gameDuration'],source=b['source'])

    def import_match(self,body):
        b,own,mh=_validated(body,self.test_mode);summary=self._summary(b,own,mh);path=self._path(summary['id'])
        if path.exists():
            existing,_,_=self._load(summary['id']);_require(existing==b,'MATCH_ALREADY_IMPORTED_WITH_DIFFERENT_CONTENT');return summary
        fd,tmp=tempfile.mkstemp(prefix='.import-',dir=self.directory)
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as stream:
                _chmod_file(stream.fileno(),tmp);json.dump(b,stream,ensure_ascii=False,allow_nan=False);stream.flush();os.fsync(stream.fileno())
            # Atomic exclusive publication avoids replacing another import or symlink.
            try:os.link(tmp,path)
            except FileExistsError:
                existing,_,_=self._load(summary['id']);_require(existing==b,'MATCH_ALREADY_IMPORTED_WITH_DIFFERENT_CONTENT')
        finally:os.unlink(tmp)
        return summary

    def list_matches(self):
        rows=[]
        for path in sorted(self.directory.glob('*.json')):
            b,own,mh=self._load(path.stem);rows.append(self._summary(b,own,mh))
        return dict(matches=rows,privacy='LOCAL_PRIVATE')

    def get_match(self,match_id,power_data=None,movement_data=None,plan=None):
        b,own,mh=self._load(match_id);summary=self._summary(b,own,mh);pid=str(b['participant_id']);info=b['match']['info']
        allies=[p for p in info['participants'] if p['teamId']==own['teamId']]
        enemies=[p for p in info['participants'] if p['teamId']!=own['teamId'] and ROLE_MAP.get(p.get('teamPosition'))==summary['role']]
        opponent=enemies[0] if len(enemies)==1 and summary['role']!='UNKNOWN' else None
        # Latest received frame per elapsed-minute bin; samples past reported end excluded.
        frames={f['timestamp']//60000:f for f in b['timeline']['info']['frames'] if f['timestamp']<=info['gameDuration']*1000}
        annotations,_=_annotations(b.get('phase_annotations'));resources=[];positioning=[];markers=[];contexts=[];movement=[];last_level=None
        for minute,frame in sorted(frames.items()):
            pf=frame['participantFrames'];entry=pf.get(pid,{})
            point=dict(minute=minute,timestamp_ms=frame['timestamp'],gold=entry.get('totalGold'),xp=entry.get('xp'),
                cs=entry['minionsKilled']+entry['jungleMinionsKilled'] if all(k in entry for k in ('minionsKilled','jungleMinionsKilled')) else None,
                level=entry.get('level'),matchup_delta={})
            enemy=pf.get(str(opponent['participantId']),{}) if opponent else {}
            for name,key in (('gold','totalGold'),('xp','xp')):point['matchup_delta'][name]=entry[key]-enemy[key] if key in entry and key in enemy else None
            point['matchup_delta']['cs']=point['cs']-(enemy['minionsKilled']+enemy['jungleMinionsKilled']) if point['cs'] is not None and all(k in enemy for k in ('minionsKilled','jungleMinionsKilled')) else None
            resources.append(point)
            if point['level'] is not None and point['level']!=last_level:
                markers.append(dict(kind='LEVEL',minute=minute,level=point['level'],label='FIRST_RECORDED_LEVEL_MINUTE'));last_level=point['level']
            positions=[_xy(pf.get(str(p['participantId']))) for p in allies];own_xy=_xy(entry)
            distance=math.hypot(own_xy['x']-statistics.median(p['x'] for p in positions),own_xy['y']-statistics.median(p['y'] for p in positions)) if own_xy and all(positions) else None
            allied_positions=[]
            for person in allies:
                declared=ROLE_MAP.get(person.get('teamPosition'))
                unique=declared is not None and sum(ROLE_MAP.get(p.get('teamPosition'))==declared for p in allies)==1
                xy=_xy(pf.get(str(person['participantId'])))
                allied_positions.append(dict(champion=person['championName'],role=declared if unique else 'UNKNOWN',
                    position=xy,status='RECORDED_MOVEMENT_ONLY' if unique and xy is not None else 'UNKNOWN',
                    reason=None if unique and xy is not None else 'MISSING_COORDINATES' if unique else 'AMBIGUOUS_OR_UNKNOWN_ROLE'))
            roles={p['role']:p['position'] for p in allied_positions if p['role']!='UNKNOWN'}
            a=annotations.get((mh,frame['timestamp']));stage=a['stage'] if a and a['verification']=='VERIFIED' else 'UNKNOWN'
            positioning.append(dict(minute=minute,position=own_xy,distance_to_allies_median=distance,stage=stage,
                stage_conditions=a['stage_conditions'] if stage!='UNKNOWN' else [],comparison=dict(status='UNKNOWN',reason='VERIFIED_STAGE_REFERENCE_REQUIRED',references=[])))
            movement.append(dict(minute=minute,timestamp_ms=frame['timestamp'],own_position=own_xy,allied_jungle_position=roles.get('JUNGLE'),allied_support_position=roles.get('SUPPORT'),allied_positions=allied_positions,inference='RECORDED_MOVEMENT_ONLY'))
        for frame in b['timeline']['info']['frames']:
            for e in frame['events']:
                if e['timestamp']>info['gameDuration']*1000:continue
                if e['type']=='ITEM_PURCHASED' and e.get('participantId')==b['participant_id'] and _integer(e.get('itemId'),1):
                    markers.append(dict(kind='ITEM',minute=e['timestamp']/60000,item_id=e['itemId'],label='RECORDED_PURCHASE_NOT_COMPLETED_BUILD'))
                kind='DEATH' if e['type']=='CHAMPION_KILL' and e.get('victimId')==b['participant_id'] else 'TEAM_WARD' if e['type'] in ('WARD_PLACED','WARD_KILL') and e.get('creatorId',e.get('killerId')) in {p['participantId'] for p in allies} else 'OBJECTIVE' if e['type'] in ('ELITE_MONSTER_KILL','BUILDING_KILL') else None
                if kind:
                    sampled=next((m for m in reversed(movement) if m['timestamp_ms']<=e['timestamp']),None)
                    contexts.append(dict(kind=kind,minute=e['timestamp']/60000,event_type=e['type'],inference='SUSPECTED_CONTEXT_ONLY',
                        recorded_context=deepcopy(sampled),position_sample_age_seconds=(e['timestamp']-sampled['timestamp_ms'])/1000 if sampled else None))
        reference=self._power_reference(power_data,summary,opponent,resources)
        self._position_reference(movement_data,summary,positioning)
        premise=self._plan_premise(plan,summary)
        dependency=self._dependency(movement,plan if premise['status']=='PLAN_RECORDED_UNVERIFIED' else None)
        return dict(schema_version='postgame.personal.v1',**summary,privacy='LOCAL_PRIVATE',resources=resources,
            gaps=[i for i in range(min(frames,default=0),max(frames,default=0)+1) if i not in frames],
            markers=sorted(markers,key=lambda m:m['minute']),reference=reference,contexts=contexts,positioning=positioning,
            dependency=dependency,
            plan_review=dict(premise=premise,
                execution=dict(status='UNKNOWN',reason='MINUTE_RECORDS_CANNOT_VERIFY_ACTION_OR_REQUIRED_CONDITIONS'),
                effect=dict(status='UNKNOWN',reason='CAUSAL_EFFECT_NOT_ESTABLISHED')),
            limitations=LIMITATIONS+(['WINDOWS_NTFS_ACL_UNVERIFIED_USER_ONLY_DIRECTORY_REQUIRED'] if os.name=='nt' else [])+(['FRAME_AFTER_REPORTED_END_EXCLUDED'] if any(f['timestamp']>info['gameDuration']*1000 for f in b['timeline']['info']['frames']) else []))

    def _power_reference(self,data,summary,opponent,resources):
        result=dict(status='UNKNOWN',reason='SAME_CHAMPION_ROLE_REFERENCE_UNAVAILABLE',units='RESOURCE_DELTA_NOT_ABSOLUTE_TOTAL',cohorts=[])
        if data is None:return result
        d=validate_power_dataset(data)
        if d['source']['sample_kind']=='SYNTHETIC' and not self.test_mode:return result
        for c in d['cohorts']:
            if (c['champion'],c['position'],c['patch'])!=(summary['champion'],summary['role'],summary['patch']):continue
            if c['comparison']=='MATCHUP' and (not opponent or c['opponent_champion']!=opponent['championName']):continue
            # Strict validator's allowlist removes raw identities and retains CI omissions.
            cohort=deepcopy(c);metric=c['metric'].replace('_delta','');unit={'gold':'gold','xp':'XP','cs':'CS'}[metric]
            cohort['units']=unit+('/minute difference vs role population rate' if c['comparison']=='ROLE_POPULATION' else ' difference vs opposing same role')
            cohort['personal_points']=[]
            for point in c['points']:
                own=next((r for r in resources if r['minute']==point['minute']),None)
                if own is None:continue
                if c['comparison']=='MATCHUP':value=own['matchup_delta'][metric]
                else:
                    elapsed=own['timestamp_ms']/60000
                    value=own[metric]/elapsed-point['reference_mean'] if elapsed>0 and own[metric] is not None and point['visible'] else None
                cohort['personal_points'].append(dict(minute=point['minute'],value=value))
            result['cohorts'].append(cohort)
        if any(p['visible'] for c in result['cohorts'] for p in c['points']):result.update(status='KNOWN',reason=None)
        result['source']=deepcopy(d['source']);return result

    def _position_reference(self,data,summary,points):
        if data is None:return
        d=validate_movement_dataset(data)
        if d['source']['sample_kind']=='SYNTHETIC' and not self.test_mode:return
        for point in points:
            if point['stage']=='UNKNOWN' or point['distance_to_allies_median'] is None:continue
            refs=[]
            for c in d['cohorts']:
                if (c['champion'],c['position'],c['patch'],c['stage'],c['condition_signature'])!=(summary['champion'],summary['role'],summary['patch'],point['stage'],point['stage_conditions']):continue
                refs.extend(dict(tier=c['tier'],**p) for p in c['points'] if p['minute']==point['minute'] and p['visible'])
            point['comparison']=dict(status='KNOWN' if refs else 'UNKNOWN',reason=None if refs else 'NO_ELIGIBLE_STAGE_SAMPLE',references=refs,units='MAP_COORDINATE_DISTANCE',inference='DESCRIPTIVE_NON_CAUSAL')

    def _plan_premise(self,plan,summary):
        result=dict(status='UNKNOWN',reason='EXPLICIT_MATCHING_CURRENT_PLAN_REQUIRED',recorded_plan=[],conditions=[])
        if not isinstance(plan,dict) or plan.get('validity')!='CURRENT':return result
        draft=plan.get('input',{})
        if not isinstance(draft,dict) or (draft.get('my_champion'),draft.get('my_position'),draft.get('patch'))!=(summary['champion'],summary['role'],summary['patch']):return result
        result.update(status='PLAN_RECORDED_UNVERIFIED',reason='PLAN_PREMISES_REQUIRE_IN_GAME_VERIFICATION',recorded_plan=self._plan_texts(plan))
        displayed=set()
        def cards(value):
            if isinstance(value,dict):
                for t in value.get('rules',[]):
                    if isinstance(t,dict) and t.get('status')=='APPLIED' and t.get('review_state')=='REVIEWED' and isinstance(t.get('output'),dict) and t['output'].get('text') in value.get('texts',[]):
                        displayed.add((t.get('rule_id'),t.get('version'),t.get('spec_sha256')))
                for key,v in value.items():
                    if key!='rules':cards(v)
            elif isinstance(value,list):
                for v in value:cards(v)
        for key in ('common','personal','changes','operations','movement'):cards(plan.get(key))
        for trace in plan.get('evaluations',[]):
            if not isinstance(trace,dict) or trace.get('status')!='APPLIED' or trace.get('review_state')!='REVIEWED' or (trace.get('rule_id'),trace.get('version'),trace.get('spec_sha256')) not in displayed:continue
            spec=trace.get('spec',{})
            if not isinstance(spec,dict):continue
            for kind in ('conditions','counterconditions','stop_conditions'):
                for predicate in spec.get(kind,[]):
                    if isinstance(predicate,dict):result['conditions'].append(dict(rule_id=trace.get('rule_id'),version=trace.get('version'),spec_version=trace.get('spec_version'),kind=kind,predicate=deepcopy(predicate),status='UNKNOWN'))
        return result

    @staticmethod
    def _dependency(samples,plan):
        result=dict(status='RECORDED_MOVEMENT_ONLY',samples=samples,coordination='UNKNOWN',plan_targets=[])
        declared=plan.get('team_dependencies',{}).get('allies',[]) if isinstance(plan,dict) and isinstance(plan.get('team_dependencies'),dict) else []
        for target in declared:
            if not isinstance(target,dict) or not isinstance(target.get('champion'),str) or target.get('position') not in ('TOP','JUNGLE','MID','BOTTOM','SUPPORT'):continue
            points=[]
            for sample in samples:
                candidates=[a for a in sample['allied_positions'] if (a['champion'],a['role'])==(target['champion'],target['position'])]
                chosen=candidates[0] if len(candidates)==1 else None
                points.append(dict(minute=sample['minute'],position=chosen['position'] if chosen else None,
                    status=chosen['status'] if chosen else 'UNKNOWN',reason=chosen['reason'] if chosen else 'TARGET_CHAMPION_ROLE_NOT_UNIQUELY_RECORDED'))
            result['plan_targets'].append(dict(champion=target['champion'],role=target['position'],samples=points,
                inference='RECORDED_MOVEMENT_ONLY',coordination='UNKNOWN'))
        return result

    @staticmethod
    def _plan_texts(plan):
        if not isinstance(plan,dict):return []
        texts=[]
        def walk(value):
            if isinstance(value,dict):
                if isinstance(value.get('texts'),list):texts.extend(t for t in value['texts'] if isinstance(t,str) and len(t)<=2000)
                for key,v in value.items():
                    if key!='texts':walk(v)
            elif isinstance(value,list):
                for v in value:walk(v)
        for key in ('common','personal','changes','operations','movement'):walk(plan.get(key))
        return texts[:100]

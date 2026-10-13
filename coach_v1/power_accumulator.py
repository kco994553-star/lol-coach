"""Exact overlap-safe power accumulation from anonymous sufficient records.

Original provider pairs never enter this file. Local role slots replace provider
participant numbers; frames retain only resource/level/item marker evidence.
Records are private derived state, never a raw-match archive or public UI API.
"""
from copy import deepcopy
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import re

from .power_stats import POSITIONS, ROLE_MAP, build_power_dataset, validate_power_dataset

SCHEMA='pregame.power-accumulator.v1'
MAX_STATE_BYTES=64*1024*1024
MAX_BUCKETS=40
MAX_RECORDS=10000
MAX_FRAMES=200
RESOURCE_FIELDS={'totalGold':'gold','xp':'xp','minionsKilled':'cs','jungleMinionsKilled':'jungle_cs','level':'level'}


def _require(condition):
    if not condition:raise ValueError('invalid anonymous power accumulator')


def _number(value):
    return type(value) in (int,float) and math.isfinite(value)


def validate_record(record):
    _require(isinstance(record,dict) and set(record)=={'hash','patch','start_ms','duration_s','champions','frames'})
    _require(isinstance(record['hash'],str) and re.fullmatch('[0-9a-f]{64}',record['hash']))
    _require(isinstance(record['patch'],str) and re.fullmatch('[0-9]+\\.[0-9]+',record['patch']))
    _require(_number(record['start_ms']) and record['start_ms']>=0)
    _require(record['duration_s'] is None or (_number(record['duration_s']) and record['duration_s']>=0))
    _require(isinstance(record['champions'],list) and len(record['champions'])==10)
    _require(all(isinstance(name,str) and re.fullmatch('[A-Za-z][A-Za-z0-9]{0,39}',name) for name in record['champions']))
    _require(isinstance(record['frames'],list) and 1<=len(record['frames'])<=MAX_FRAMES)
    previous=-1;events=0
    for frame in record['frames']:
        _require(isinstance(frame,dict) and set(frame)=={'ms','resources','items'})
        _require(_number(frame['ms']) and frame['ms']>previous);previous=frame['ms']
        _require(isinstance(frame['resources'],list) and len(frame['resources'])==10)
        for resources in frame['resources']:
            _require(isinstance(resources,dict) and set(resources)<=set(RESOURCE_FIELDS.values()))
            _require(all(_number(value) for value in resources.values()))
            _require('level' not in resources or (type(resources['level']) is int and resources['level']>=1))
        _require(isinstance(frame['items'],list));events+=len(frame['items']);_require(events<=4000)
        for event in frame['items']:
            _require(isinstance(event,dict) and set(event)=={'kind','slot','ms','item','before','after'})
            _require(event['kind'] in ('ITEM_PURCHASED','ITEM_UNDO'))
            _require(type(event['slot']) is int and 0<=event['slot']<10)
            _require(_number(event['ms']) and event['ms']>=0)
            _require(all(value is None or (type(value) is int and value>=0) for value in (event['item'],event['before'],event['after'])))
    return deepcopy(record)


def sufficient_records(pairs,*,source,complete_item_ids=(),ci_width_limits=None):
    """Project only matches accepted by the immutable existing builder."""
    records=[];seen=set()
    for pair in pairs:
        data=build_power_dataset([pair],source=source,complete_item_ids=complete_item_ids,ci_width_limits=ci_width_limits)
        if not data['samples']['hashed_match_ids']:continue
        sha=data['samples']['hashed_match_ids'][0]
        if sha in seen:continue
        seen.add(sha);info=pair['match']['info']
        roles={(p['teamId'],ROLE_MAP.get(p.get('teamPosition'))):p for p in info['participants']
               if p.get('teamId') in (100,200) and ROLE_MAP.get(p.get('teamPosition')) in POSITIONS}
        people=[roles[(team,role)] for team in (100,200) for role in POSITIONS]
        slots={p['participantId']:index for index,p in enumerate(people)}
        frames=[]
        for frame in pair['timeline']['info']['frames']:
            resources=[]
            for person in people:
                values=frame.get('participantFrames',{}).get(str(person['participantId']),{})
                resources.append({safe:values[raw] for raw,safe in RESOURCE_FIELDS.items() if
                    _number(values.get(raw)) and (raw!='level' or (type(values[raw]) is int and values[raw]>=1))})
            items=[]
            for event in frame.get('events',[]):
                if event.get('type') not in ('ITEM_PURCHASED','ITEM_UNDO') or event.get('participantId') not in slots:continue
                if not _number(event.get('timestamp')) or event['timestamp']<0:continue
                def item(key):
                    value=event.get(key);return value if type(value) is int and value>=0 else None
                items.append(dict(kind=event['type'],slot=slots[event['participantId']],ms=event['timestamp'],
                                  item=item('itemId'),before=item('beforeId'),after=item('afterId')))
            frames.append(dict(ms=frame['timestamp'],resources=resources,items=items))
        duration=info.get('gameDuration')
        record=dict(hash=sha,patch=data['source']['patch'],start_ms=info['gameStartTimestamp'],
                    duration_s=duration if _number(duration) else None,champions=[p['championName'] for p in people],frames=frames)
        records.append(validate_record(record))
    return records


def _pair(record):
    # This ephemeral ID is derived solely from an anonymous hash. Replace its
    # builder hash with the original identity hash immediately after building.
    mid='KR_'+str(int(record['hash'],16))
    people=[dict(participantId=index+1,teamId=100 if index<5 else 200,
                 teamPosition=POSITIONS[index%5],championName=name) for index,name in enumerate(record['champions'])]
    frames=[]
    for frame in record['frames']:
        resources={str(index+1):{raw:row[safe] for raw,safe in RESOURCE_FIELDS.items() if safe in row}
                   for index,row in enumerate(frame['resources'])}
        events=[dict(type=e['kind'],participantId=e['slot']+1,timestamp=e['ms'],itemId=e['item'],
                     beforeId=e['before'],afterId=e['after']) for e in frame['items']]
        frames.append(dict(timestamp=frame['ms'],participantFrames=resources,events=events))
    return dict(match=dict(metadata=dict(matchId=mid),info=dict(queueId=420,mapId=11,gameMode='CLASSIC',
        gameVersion=record['patch']+'.1',gameStartTimestamp=record['start_ms'],gameDuration=record['duration_s'],participants=people)),
        timeline=dict(metadata=dict(matchId=mid),info=dict(frameInterval=60000,frames=frames)))


class PowerAccumulator:
    def __init__(self,state=None):
        state=deepcopy(state) if state is not None else dict(schema_version=SCHEMA,buckets=[],legacy=[])
        _require(isinstance(state,dict) and set(state)=={'schema_version','buckets','legacy'} and state['schema_version']==SCHEMA)
        _require(isinstance(state['buckets'],list) and len(state['buckets'])<=MAX_BUCKETS)
        _require(isinstance(state['legacy'],list) and len(state['legacy'])<=MAX_BUCKETS)
        keys=set();total=0
        for bucket in state['buckets']:
            _require(isinstance(bucket,dict) and set(bucket)=={'source','records'})
            _require(isinstance(bucket['records'],list));total+=len(bucket['records']);_require(total<=MAX_RECORDS)
            shell=build_power_dataset([],source=bucket['source'],ci_width_limits=bucket['source'].get('precision_policy',{}).get('ci_width_limits'),
                                      complete_item_ids=bucket['source'].get('item_catalog',{}).get('complete_item_ids',()))
            key=(shell['source']['patch'],shell['source']['tier']);_require(key not in keys);keys.add(key)
            hashes=set()
            for record in bucket['records']:
                validate_record(record);_require(record['patch']==key[0] and record['hash'] not in hashes);hashes.add(record['hash'])
        for legacy in state['legacy']:validate_power_dataset(legacy)
        _require(len(json.dumps(state,allow_nan=False).encode())<=MAX_STATE_BYTES)
        self._state=state

    def to_dict(self):return deepcopy(self._state)

    def known_hashes(self,patch=None,tier=None):
        if tier is None:raise ValueError('seed tier required for deduplication scope')
        def selected(source):return source['tier']==tier and (patch is None or source['patch']==patch)
        return set(r['hash'] for b in self._state['buckets'] if selected(b['source']) for r in b['records']) | set(
            sha for d in self._state['legacy'] if selected(d['source']) for sha in d['samples']['hashed_match_ids'])

    def progress(self,patch,tier,*,include_points=False):
        from .collection_progress import progress_response
        bucket=next((b for b in self._state['buckets'] if (b['source']['patch'],b['source']['tier'])==(patch,tier)),None)
        return progress_response(self.dataset(patch,tier),bucket['records'] if bucket and bucket['records'] else None,include_points=include_points)

    def seed_legacy(self,dataset):
        data=validate_power_dataset(dataset)
        key=(data['source']['patch'],data['source']['tier'])
        self._state['legacy']=[d for d in self._state['legacy'] if (d['source']['patch'],d['source']['tier'])!=key]+[deepcopy(data)]
        PowerAccumulator(self._state)

    def add_pairs(self,pairs,*,source,complete_item_ids=(),ci_width_limits=None):
        batch=build_power_dataset(pairs,source=source,complete_item_ids=complete_item_ids,ci_width_limits=ci_width_limits)
        records=sufficient_records(pairs,source=source,complete_item_ids=complete_item_ids,ci_width_limits=ci_width_limits)
        return self.add_records(records,source=batch['source'])

    def add_records(self,records,*,source):
        shell=build_power_dataset([],source=source,ci_width_limits=source.get('precision_policy',{}).get('ci_width_limits'),
                                 complete_item_ids=source.get('item_catalog',{}).get('complete_item_ids',()))
        source=deepcopy(shell['source']);key=(source['patch'],source['tier'])
        _require(key[0] is not None)
        candidate=deepcopy(self._state)
        bucket=next((b for b in candidate['buckets'] if (b['source']['patch'],b['source']['tier'])==key),None)
        if bucket is None:bucket=dict(source=source,records=[]);candidate['buckets'].append(bucket)
        else:
            _require(bucket['source']['sample_kind']==source['sample_kind'])
            _require(bucket['source']['precision_policy']==source['precision_policy'])
            old_catalog=bucket['source'].get('item_catalog');new_catalog=source.get('item_catalog')
            # Missing marker acquisition cannot retroactively erase catalog lineage.
            if old_catalog and not new_catalog:source['item_catalog']=deepcopy(old_catalog)
            if old_catalog and new_catalog:_require(old_catalog==new_catalog)
            for bound,operation in (('window_start',min),('window_end',max)):
                old=bucket['source'][bound];new=source[bound]
                source[bound]=None if old is None or new is None else operation(old,new)
            source['limitations']=list(dict.fromkeys(bucket['source'].get('limitations',[])+source.get('limitations',[])))
            bucket['source']=source
        by_hash={r['hash']:r for r in bucket['records']}
        for value in records:
            record=validate_record(value);_require(record['patch']==key[0])
            if record['hash'] in by_hash:_require(by_hash[record['hash']]==record)
            else:by_hash[record['hash']]=record;bucket['records'].append(record)
        PowerAccumulator(candidate)
        self._state=candidate
        return self.dataset(*key)

    def dataset(self,patch,tier):
        bucket=next((b for b in self._state['buckets'] if (b['source']['patch'],b['source']['tier'])==(patch,tier)),None)
        if bucket and bucket['records']:
            source=deepcopy(bucket['source']);records=bucket['records']
            result=build_power_dataset([_pair(r) for r in records],source=source,
                ci_width_limits=source['precision_policy']['ci_width_limits'],
                complete_item_ids=source.get('item_catalog',{}).get('complete_item_ids',()))
            result['samples']['hashed_match_ids']=sorted(r['hash'] for r in records)
            return validate_power_dataset(result)
        legacy=next((d for d in self._state['legacy'] if (d['source']['patch'],d['source']['tier'])==(patch,tier)),None)
        if legacy:return deepcopy(legacy)
        if bucket:return build_power_dataset([],source=bucket['source'])
        raise ValueError('no accumulator bucket for patch and tier')

    def save(self,path):
        PowerAccumulator(self._state);path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
        raw=json.dumps(self._state,allow_nan=False,sort_keys=True,separators=(',',':')).encode()
        temporary=path.with_name(path.name+'.tmp')
        fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
        os.chmod(temporary,0o600)
        with os.fdopen(fd,'wb') as output:output.write(gzip.compress(raw,mtime=0) if path.suffix=='.gz' else raw)
        os.replace(temporary,path)

    @classmethod
    def load(cls,path):
        path=Path(path);_require(path.stat().st_size<=MAX_STATE_BYTES)
        opener=gzip.open if path.suffix=='.gz' else open
        with opener(path,'rb') as stream:raw=stream.read(MAX_STATE_BYTES+1)
        _require(len(raw)<=MAX_STATE_BYTES)
        return cls(json.loads(raw))

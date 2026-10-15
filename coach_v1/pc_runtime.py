"""PC-local background services. No provider keys, identity endpoints or advice in-game."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import threading
import time

from .auto_review import assess
from .pc_coach import review_store


def draft_input(snapshot):
    if snapshot.get('status')!='CONNECTED' or snapshot.get('phase')!='ChampSelect':return None
    source=dict(kind='AUTOMATIC',reference='로컬 픽창의 공개 선택 정보',observed_at=None,verification='UNVERIFIED')
    slots=[];own_slot=None
    for side,key in [('ALLY','allies'),('ENEMY','enemies')]:
        rows=snapshot.get(key,[])
        for i in range(5):
            row=rows[i] if i<len(rows) else {}
            if side=='ALLY' and row.get('is_self'):own_slot=i+1
            slots.append(dict(side=side,slot=i+1,champion=row.get('champion'),position=row.get('position'),position_candidates=[],uncertainty='픽창 공개 정보이며 미확정 선택은 바뀔 수 있습니다.',champion_source=source,position_source=source,runes=dict(status='UNKNOWN',values=[],source=source),summoners=dict(status='UNKNOWN',values=[],source=source)))
    # Adapter row does not expose account/cell identifiers; locate self only if
    # its own selection/position uniquely matches a visible ally.
    if own_slot is None:
        matched=[s['slot'] for s in slots if s['side']=='ALLY' and s['champion']==snapshot.get('own_champion') and s['position']==snapshot.get('own_position') and s['champion']]
        if len(matched)==1:own_slot=matched[0]
    return dict(title='PC 픽창 자동 입력',patch=snapshot.get('patch'),phase='PRE_GAME',observed_at=None,my_position=snapshot.get('own_position'),my_champion=snapshot.get('own_champion'),my_slot=own_slot,slots=slots,source=source,original_capture=None)


def load_pc_default_datasets(server):
    from .pregame_server import ROOT, read_aggregate_file
    from .power_stats import validate_power_dataset
    from .collection_progress import validate_progress
    directories=sorted((ROOT/'data/riot').glob('20??-??-??'),reverse=True)
    directory=next((p for p in directories if p.is_dir() and any(p.glob('power-*-*.json*'))),None)
    if directory is None:return
    for path in sorted([*directory.glob('power-*.json'),*directory.glob('power-*.json.gz')])[:100]:
        data=validate_power_dataset(read_aggregate_file(path))
        if data['source']['sample_kind']!='REAL':continue
        key=(data['source']['patch'],data['source']['tier'])
        server.power_datasets[key]=data
        progress=directory/('progress-'+key[0]+'-'+key[1]+'.json')
        if not progress.exists():progress=progress.with_suffix('.json.gz')
        if progress.exists():server.power_progress[key]=validate_progress(read_aggregate_file(progress,max_bytes=1_000_000),data)


def pc_status(server):
    service=getattr(server,'pc_services',None)
    connection=service.snapshot() if service else dict(status='BLOCKED_EXTERNAL',reason='GAME_PC_NOT_CONNECTED',phase=None,revision=0,input=None)
    result=assess()
    return dict(connection=connection,review_summary={k:result[k] for k in ('passed','held','reasons')},weekly_report=review_store(server).weekly(result['rows']))


class PCServices:
    def __init__(self,server,*,lcu_lockfile=None,lcu_certificate_sha256=None):
        self.server=server;self.lockfile=lcu_lockfile;self.pin=lcu_certificate_sha256
        self.stop=threading.Event();self.lock=threading.RLock();self.adapter=None
        self.state=dict(status='BLOCKED_EXTERNAL',reason='GAME_PC_NOT_CONNECTED',phase=None,revision=0,input=None)
        self.last_event=None;self.observed=0
        self.thread=threading.Thread(target=self.run,name='pc-local-services',daemon=True)
        self.maintenance=threading.Thread(target=self.maintain,name='pc-reference-maintenance',daemon=True)

    def snapshot(self):
        with self.lock:
            state=__import__('copy').deepcopy(self.state)
            # This is a connection-liveness deadline, never a gameplay TTL.
            if state.get('status')=='CONNECTED' and time.monotonic()-self.observed>2:
                state.update(status='MANUAL_FALLBACK',reason='LOCAL_FEED_NOT_CURRENT',phase=None,input=None,revision=state['revision']+1)
            return state

    def close(self):
        self.stop.set();self.thread.join(timeout=7);self.maintenance.join(timeout=1)

    def _publish(self,state):
        state=dict(state,input=draft_input(state),source_revision=state.get('revision'))
        with self.lock:
            previous={k:v for k,v in self.state.items() if k!='revision'}
            current={k:v for k,v in state.items() if k!='revision'}
            state['revision']=self.state['revision']+int(previous!=current)
            self.state=state;self.observed=time.monotonic()
        event=(state.get('status'),state.get('reason'),state.get('phase'))
        if event!=self.last_event:
            self.last_event=event
            path=Path(self.server.pregame.dbpath+'.connection.jsonl')
            with path.open('a',encoding='utf-8') as stream:stream.write(json.dumps(dict(status=event[0],reason=event[1],phase=event[2],at=datetime.now(timezone.utc).isoformat()))+'\n')

    def _connect(self):
        from .lcu_draft import discover_lockfile,pair_certificate,LCUDraftAdapter
        from .official_catalog import _current
        lockfile=self.lockfile or discover_lockfile()
        if lockfile is None:return
        pin=self.pin or pair_certificate(lockfile)
        # Public roster ID map; never account data.
        _,_,roster,_,_=_current(verify_all=True)
        mapping={int(row['key']):row['id'] for row in roster.values()}
        self.adapter=LCUDraftAdapter(lockfile,mapping,certificate_sha256=pin)

    def maintain(self):
        while not self.stop.is_set():
            try:
                from .official_catalog import refresh_if_due
                refresh_if_due()
                from .official_items import refresh_if_due as refresh_items
                refresh_items()
                if self.stop.is_set():return
                result=assess();review_store(self.server).weekly(result['rows'])
            except (OSError,ValueError,KeyError):pass
            self.stop.wait(3600)

    def run(self):
        next_pair=0
        while not self.stop.is_set():
            now=time.monotonic()
            if self.adapter is None and now>=next_pair:
                try:self._connect()
                except (OSError,ValueError,KeyError):self._publish(dict(status='MANUAL_FALLBACK',reason='LOCAL_PAIRING_UNAVAILABLE',phase=None))
                next_pair=now+5
            if self.adapter is not None:
                state=self.adapter.poll();self._publish(state)
                if state.get('reason') in ('SESSION_CHANGED','LOCKFILE_INVALID','LCU_NOT_AVAILABLE'):
                    self.adapter=None
            self.stop.wait(0.35)


def start_pc_services(server,*,lcu_lockfile=None,lcu_certificate_sha256=None):
    load_pc_default_datasets(server)
    from .recall_pc import load_datasets
    load_datasets(server)
    controller=PCServices(server,lcu_lockfile=lcu_lockfile,lcu_certificate_sha256=lcu_certificate_sha256)
    server.pc_services=controller;controller.thread.start();controller.maintenance.start()
    return controller

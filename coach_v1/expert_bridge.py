"""Short source statements → immutable notes → EXPLORATORY, never approvals.

The additive import journal is a private local sidecar. It preserves idempotency
and user deletion across crashes/restarts without changing research v2 schema.
"""
from collections import defaultdict
from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
import threading

from .expert_contract import validate_expert_artifact
from .state import canonical,digest
from .storage import ServiceError

_LOCK=threading.RLock()
_FORMAT='expert-video-summary.v1'


def compare_claim(claim,movement_data,test_mode=False):
    from .expert_measurement import compare_claim as compare
    return compare(claim,movement_data,test_mode)


def _bounded(value,max_bytes):
    if type(max_bytes) is not int or max_bytes<=0:raise ServiceError(422,'INVALID_LIMIT')
    if len(canonical(value).encode('utf-8'))>max_bytes:raise ServiceError(413,'EXPERT_TOO_LARGE')
    return value


@contextmanager
def _journal(store):
    path=Path(store.dbpath+'.expert.sqlite')
    with sqlite3.connect(path,timeout=10) as db:
        db.row_factory=sqlite3.Row
        db.execute('BEGIN IMMEDIATE')
        tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not tables and db.execute('PRAGMA user_version').fetchone()[0]==0:
            db.execute('CREATE TABLE imports (artifact_hash TEXT PRIMARY KEY,resource_id TEXT NOT NULL,complete INTEGER NOT NULL)')
            db.execute('CREATE TABLE claims (artifact_hash TEXT NOT NULL,anchor TEXT NOT NULL,rule_id TEXT NOT NULL,PRIMARY KEY(artifact_hash,anchor))')
            db.execute('PRAGMA user_version=1')
        expected={'imports':('artifact_hash','resource_id','complete'),'claims':('artifact_hash','anchor','rule_id')}
        actual={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if db.execute('PRAGMA user_version').fetchone()[0]!=1 or actual!=set(expected):
            raise ServiceError(409,'INCOMPATIBLE_EXPERT_IMPORT_JOURNAL')
        for table,columns in expected.items():
            if tuple(r[1] for r in db.execute('PRAGMA table_info('+table+')'))!=columns:
                raise ServiceError(409,'INCOMPATIBLE_EXPERT_IMPORT_JOURNAL')
        yield db


def _report(artifact):
    return dict(format=_FORMAT,artifact=artifact,
        candidates=[dict(cue_index=i+1,video_time_ms=c['timestamp_seconds']*1000,
            kind='EXPERT_STATEMENT_UNVERIFIED',visual_verified=False,decision_eligible=False)
            for i,c in enumerate(artifact['claims'])],source_authenticity_verified=False,coaching_enabled=False)


def _rule(a,c):
    return dict(patch_range=c['patch_range'],applicability=dict(champion=c['champion'],role=c['position'],
        matchup='UNKNOWN',level='UNKNOWN',context=' / '.join([c['stage'],c['context']]+c['conditions']) or 'UNKNOWN'),
        required_fields=[],claim=c['paraphrase'],mechanism='EXPERT_STATEMENT_UNVERIFIED: '+c['context'],
        counterexamples=c['counterexamples'],author=a['video']['speaker'],limitations=c['limitations']+
        ['SOURCE_STATEMENT_NOT_OBSERVATION','NO_EXECUTABLE_CONDITIONS_FROM_PROSE'])


def _note(a,c):
    return dict(known=c['paraphrase'],intention=' / '.join([c['position'],c['champion'],c['stage']]+c['conditions']),
        alternative=' / '.join(c['counterexamples'])[:2000],outcome=canonical(dict(
            context=c['context'],video_url=a['video']['url']+'&t='+str(c['timestamp_seconds']),
            speaker=a['video']['speaker'],speaker_identification_assertion=a['video']['speaker_verified'],
            patch_range=c['patch_range'],independent_group_id=c['independent_group_id'],visual_verified=False)))


def _existing_proposal(store,rid,anchor):
    # Partial recovery reads source bindings; never claims a review authority.
    with store._db() as db:
        rows=db.execute('SELECT id FROM knowledge_rules WHERE resource_id=? AND anchor=? ORDER BY rowid',(rid,anchor)).fetchall()
    if rows:return store.get_proposal(rows[0]['id'],max_bytes=2_000_000)
    return None


def import_expert_artifact(store,artifact,*,max_bytes):
    a=validate_expert_artifact(artifact)
    # A conservative preflight keeps this multi-step import within its bounded
    # response before any source/note/proposal write. Actual response checked too.
    _bounded(a,max_bytes)
    if len(canonical(a).encode('utf-8'))*4+4096>max_bytes:raise ServiceError(413,'EXPERT_TOO_LARGE')
    ah=digest(a);report=_report(a);rid=digest(dict(kind='VIDEO',report=report));new=0
    with _LOCK:
        with _journal(store) as db:
            progress=db.execute('SELECT * FROM imports WHERE artifact_hash=?',(ah,)).fetchone()
            if progress is None:
                store.add('VIDEO',a['video']['title'],report)
                db.execute('INSERT INTO imports VALUES (?,?,0)',(ah,rid))
            elif not progress['complete']:
                try:store.get(rid)
                except ServiceError as error:
                    if error.status!=404:raise
                    db.execute('UPDATE imports SET complete=1 WHERE artifact_hash=?',(ah,))
                    progress=dict(complete=1)
        if progress is not None and progress['complete']:
            return _bounded(dict(new_candidates=0,claims=_rows_for_artifact(store,ah,max_bytes)),max_bytes)
        for index,c in enumerate(a['claims']):
            anchor=str(index+1)
            with _journal(store) as db:
                recorded=db.execute('SELECT rule_id FROM claims WHERE artifact_hash=? AND anchor=?',(ah,anchor)).fetchone()
            if recorded is not None:continue
            note=store.get_note(rid,anchor)
            if note['revision']==0:note=store.put_note(rid,anchor,_note(a,c),0)
            proposal=_existing_proposal(store,rid,anchor)
            if proposal is None:
                proposal=store.propose(_rule(a,c),dict(resource_id=rid,anchor=anchor,note_revision=note['revision']),max_bytes=max_bytes)
                new+=1
            with _journal(store) as db:
                db.execute('INSERT OR IGNORE INTO claims VALUES (?,?,?)',(ah,anchor,proposal['rule_id']))
        with _journal(store) as db:db.execute('UPDATE imports SET complete=1 WHERE artifact_hash=?',(ah,))
        return _bounded(dict(new_candidates=new,claims=_rows_for_artifact(store,ah,max_bytes)),max_bytes)


def _claim_key(c):
    return canonical({k:c[k] for k in ('paraphrase','champion','position','stage','conditions')})


def list_expert_claims(store,*,max_bytes,movement_data=None,test_mode=False):
    with _LOCK:
        with _journal(store) as db:
            records=db.execute('SELECT i.artifact_hash,i.resource_id,c.anchor,c.rule_id FROM imports i JOIN claims c USING(artifact_hash) ORDER BY i.rowid,c.anchor').fetchall()
        rows=[];groups=defaultdict(lambda:dict(videos=set(),speakers=set()))
        for record in records:
            try:
                resource=store.get(record['resource_id'])
                if resource['report'].get('format')!=_FORMAT:raise ServiceError(409,'EXPERT_SOURCE_MISMATCH')
                a=validate_expert_artifact(resource['report']['artifact']);c=a['claims'][int(record['anchor'])-1]
                if digest(a)!=record['artifact_hash']:raise ServiceError(409,'EXPERT_SOURCE_MISMATCH')
                p=store.get_proposal(record['rule_id'],max_bytes=max_bytes)
            except ServiceError as error:
                if error.status==404:continue
                raise
            key=_claim_key(c);groups[key]['videos'].add(a['video']['id'])
            if a['video']['speaker_verified'] and a['video']['speaker']!='UNKNOWN':groups[key]['speakers'].add(a['video']['speaker'])
            row=dict(artifact=a,claim=c,resource_id=record['resource_id'],anchor=record['anchor'],proposal=p,
                comparison=compare_claim(c,movement_data,test_mode),independent_sources={})
            rows.append((row,key));_bounded([r for r,k in rows],max_bytes)
        for row,key in rows:
            row['independent_sources']=dict(videos=len(groups[key]['videos']),verified_speakers=len(groups[key]['speakers']))
        return _bounded(dict(claims=[r for r,k in rows],new_candidates=0,coaching_accuracy=None),max_bytes)


def _rows_for_artifact(store,artifact_hash,max_bytes):
    result=list_expert_claims(store,max_bytes=max_bytes)
    return [r for r in result['claims'] if digest(r['artifact'])==artifact_hash]

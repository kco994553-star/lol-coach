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
from .knowledge import _rule as validate_knowledge_rule
from .note_history import note_revision
from .state import canonical,digest
from .storage import ServiceError

_LOCK=threading.RLock()
_FORMAT='expert-video-summary.v1'


def compare_claim(claim,movement_data,test_mode=False):
    from .expert_measurement import compare_claim as compare
    return compare(claim,movement_data,test_mode)


def _bounded(value,max_bytes):
    if type(max_bytes) is not int or max_bytes<=0:raise ServiceError(422,'INVALID_LIMIT')
    if len(json.dumps(value,ensure_ascii=False,allow_nan=False).encode('utf-8'))>max_bytes:raise ServiceError(413,'EXPERT_TOO_LARGE')
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
            db.execute('CREATE TABLE claims (artifact_hash TEXT NOT NULL,anchor TEXT NOT NULL,rule_id TEXT,state TEXT NOT NULL,PRIMARY KEY(artifact_hash,anchor))')
            db.execute('PRAGMA user_version=1')
        expected={'imports':('artifact_hash','resource_id','complete'),'claims':('artifact_hash','anchor','rule_id','state')}
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
    context=' / '.join([c['stage'],c['context']]+c['conditions'])
    if len(context)>2000:context=c['stage']+' / '+c['context']+' / CONDITIONS_AT_SOURCE_SHA256:'+digest(c['conditions'])
    return dict(patch_range=c['patch_range'],applicability=dict(champion=c['champion'],role=c['position'],
        matchup='UNKNOWN',level='UNKNOWN',context=context),
        required_fields=[],claim=c['paraphrase'],mechanism='EXPERT_STATEMENT_UNVERIFIED: '+c['context'],
        counterexamples=c['counterexamples'],author=a['video']['speaker'],limitations=c['limitations']+
        ['SOURCE_STATEMENT_NOT_OBSERVATION','NO_EXECUTABLE_CONDITIONS_FROM_PROSE'])


def _note(a,c):
    intention=' / '.join([c['position'],c['champion'],c['stage']]+c['conditions'])
    if len(intention)>2000:intention=' / '.join([c['position'],c['champion'],c['stage']])+' / CONDITIONS_AT_SOURCE_SHA256:'+digest(c['conditions'])
    return dict(known=c['paraphrase'],intention=intention,
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
    _bounded(a,max_bytes)
    ah=digest(a);report=_report(a);rid=digest(dict(kind='VIDEO',report=report));new=0
    with _LOCK:
        prepared=[(validate_knowledge_rule(_rule(a,c)),_note(a,c)) for c in a['claims']]
        existing=list_expert_claims(store,max_bytes=max_bytes)
        if not any(r['artifact_sha256']==ah for r in existing['claims']):
            preview=[_preview_row(a,c,rid,str(i+1),rule,note) for i,(c,(rule,note)) in enumerate(zip(a['claims'],prepared))]
            _bounded(dict(new_candidates=len(preview),claims=existing['claims']+preview),max_bytes)
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
                recorded=db.execute('SELECT * FROM claims WHERE artifact_hash=? AND anchor=?',(ah,anchor)).fetchone()
            if recorded is not None and recorded['state'] in ('COMPLETE','WITHHELD'):continue
            note=store.get_note(rid,anchor)
            if note['revision']==0:note=store.put_note(rid,anchor,_note(a,c),0)
            original=note_revision(store,rid,anchor,'1',max_bytes)['note']
            if original!=prepared[index][1]:raise ServiceError(409,'EXPERT_SOURCE_NOTE_MISMATCH')
            proposal=_existing_proposal(store,rid,anchor)
            if recorded is not None and recorded['state']=='STARTED' and proposal is None:
                # Process loss after dispatch is ambiguous: it may have committed
                # and subsequently been deleted. Preserve that human deletion.
                with _journal(store) as db:
                    db.execute("UPDATE claims SET state='WITHHELD' WHERE artifact_hash=? AND anchor=?",(ah,anchor))
                continue
            if proposal is None:
                with _journal(store) as db:
                    db.execute("INSERT OR REPLACE INTO claims VALUES (?,?,NULL,'STARTED')",(ah,anchor))
                try:
                    proposal=store.propose(prepared[index][0],dict(resource_id=rid,anchor=anchor,note_revision=1),max_bytes=max_bytes)
                except Exception:
                    with _journal(store) as db:
                        db.execute("UPDATE claims SET state='FAILED' WHERE artifact_hash=? AND anchor=?",(ah,anchor))
                    raise
                new+=1
            with _journal(store) as db:
                db.execute("INSERT OR REPLACE INTO claims VALUES (?,?,?,'COMPLETE')",(ah,anchor,proposal['rule_id']))
        with _journal(store) as db:db.execute('UPDATE imports SET complete=1 WHERE artifact_hash=?',(ah,))
        return _bounded(dict(new_candidates=new,claims=_rows_for_artifact(store,ah,max_bytes)),max_bytes)


def _claim_key(c):
    return canonical({k:c[k] for k in ('paraphrase','champion','position','stage','conditions')})


def _envelope(a):
    return {k:a[k] for k in ('schema_version','video','processing','visual_verified','coaching_accuracy')}


def _preview_row(a,c,rid,anchor,rule,note):
    source=dict(resource_id=rid,anchor=anchor,note_revision=1,kind='VIDEO',report_sha256=digest(_report(a)),note_sha256=digest(note))
    p=dict(rule,schema_version='knowledge-proposal.v1',rule_id='0'*32,version='0'*32,source_refs=[source],review_state='EXPLORATORY',supersedes=None,coaching_enabled=False)
    return dict(artifact=_envelope(a),artifact_sha256=digest(a),source_claim_count=len(a['claims']),claim=c,
        resource_id=rid,anchor=anchor,proposal=p,comparison=compare_claim(c,None),
        independent_sources=dict(videos=999999,verified_speakers=999999),content_grade='UNKNOWN')


def _grades():
    path=Path(__file__).resolve().parents[1]/'config/expert_channels.json'
    if not path.exists():return {}
    config=json.loads(path.read_text())
    return {c['channel_id']:c['content_grade'] for c in config['channels']}


def list_expert_claims(store,*,max_bytes,movement_data=None,test_mode=False):
    with _LOCK:
        with _journal(store) as db:
            records=db.execute('SELECT i.artifact_hash,i.resource_id,c.anchor,c.rule_id,c.state FROM imports i JOIN claims c USING(artifact_hash) ORDER BY i.rowid,c.anchor').fetchall()
        rows=[];withheld=[];grades=_grades();groups=defaultdict(lambda:dict(videos=set(),speakers=set()))
        for record in records:
            if record['state']=='WITHHELD':
                withheld.append(dict(resource_id=record['resource_id'],anchor=record['anchor'],reason='UNCERTAIN_PARTIAL_IMPORT'));continue
            if record['state']!='COMPLETE':continue
            try:
                resource=store.get(record['resource_id'])
                if resource['report'].get('format')!=_FORMAT:raise ServiceError(409,'EXPERT_SOURCE_MISMATCH')
                a=validate_expert_artifact(resource['report']['artifact']);c=a['claims'][int(record['anchor'])-1]
                if digest(a)!=record['artifact_hash']:raise ServiceError(409,'EXPERT_SOURCE_MISMATCH')
                p=store.get_proposal(record['rule_id'],max_bytes=max_bytes)
            except ServiceError as error:
                if error.status==404:continue
                raise
            if not (len(p['source_refs'])==1 and p['source_refs'][0]['resource_id']==record['resource_id']
                    and p['source_refs'][0]['anchor']==record['anchor'] and p['source_refs'][0]['note_revision']==1):
                withheld.append(dict(rule_id=p['rule_id'],reason='PROPOSAL_SOURCE_CHANGED'));continue
            key=_claim_key(c);groups[key]['videos'].add(a['video']['id'])
            if a['video']['speaker_verified'] and a['video']['speaker']!='UNKNOWN':groups[key]['speakers'].add(a['video']['speaker'])
            row=dict(artifact=_envelope(a),artifact_sha256=record['artifact_hash'],source_claim_count=len(a['claims']),
                claim=c,resource_id=record['resource_id'],anchor=record['anchor'],proposal=p,
                comparison=compare_claim(c,movement_data,test_mode),independent_sources={},
                content_grade=grades.get(a['video']['channel_id'],'UNKNOWN'))
            rows.append((row,key));_bounded([r for r,k in rows],max_bytes)
        for row,key in rows:
            row['independent_sources']=dict(videos=len(groups[key]['videos']),verified_speakers=len(groups[key]['speakers']))
        def rank(row):
            grade=row['content_grade'];comparison=row['comparison']
            return 0 if grade=='L' else 1 if grade=='C' and comparison['status']=='AGREES' and (comparison.get('statistic') or {}).get('evidence_kind')=='REAL_AGGREGATE' else 2 if grade=='C' else 4 if grade=='P' else 3
        result=dict(claims=sorted([r for r,k in rows],key=rank),new_candidates=0,coaching_accuracy=None)
        if withheld:result['withheld']=withheld
        return _bounded(result,max_bytes)


def _rows_for_artifact(store,artifact_hash,max_bytes):
    result=list_expert_claims(store,max_bytes=max_bytes)
    return [r for r in result['claims'] if r['artifact_sha256']==artifact_hash]

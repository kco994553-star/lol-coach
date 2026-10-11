"""Immutable pregame sidecar; existing two database schemas remain untouched."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3
import uuid

from .pregame_contract import POSITIONS, parse_input
from .state import canonical, digest
from .storage import ServiceError

SCHEMAS=(
    'CREATE TABLE inputs (session_id TEXT NOT NULL,revision INTEGER NOT NULL,id TEXT NOT NULL UNIQUE,parent_id TEXT,payload TEXT NOT NULL,PRIMARY KEY(session_id,revision))',
    'CREATE TABLE plans (session_id TEXT NOT NULL,revision INTEGER NOT NULL,id TEXT NOT NULL UNIQUE,input_revision INTEGER NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(session_id,revision),FOREIGN KEY(session_id,input_revision) REFERENCES inputs(session_id,revision))',
    'CREATE TABLE operations (operation TEXT NOT NULL,key TEXT NOT NULL,fingerprint TEXT NOT NULL,response TEXT NOT NULL,PRIMARY KEY(operation,key))',
)
TOKEN=re.compile('[a-f0-9]{32}\\Z')
KEY=re.compile('[A-Za-z0-9_.-]{1,128}\\Z')
INPUT_FIELDS={'schema_version','id','session_id','revision','parent_id','created_at','input','input_sha256'}
PLAN_META={'id','session_id','revision','input_revision','input_sha256','created_at'}
PLAN_FIELDS={'schema_version','mode','input','common','personal','changes','evaluations','knowledge_fingerprint','coaching_accuracy','real_match_validation'}


PLAN_FIELDS_V2=PLAN_FIELDS|{'operations','team_dependencies','pick_warnings'}

PLAN_FIELDS_V3=PLAN_FIELDS_V2|{'movement','movement_statistics_fingerprint'}

def plan_fields(r):
    if r.get('schema_version')=='pregame.plan.v3':return PLAN_FIELDS_V3
    return PLAN_FIELDS_V2 if r.get('schema_version')=='pregame.plan.v2' else PLAN_FIELDS

def _id(value):
    if not isinstance(value,str) or not TOKEN.fullmatch(value):raise ServiceError(422,'INVALID_PREGAME_ID')


def _revision(value,zero=False):
    if type(value) is not int or not (0 if zero else 1)<=value<=9223372036854775807:
        raise ServiceError(422,'INVALID_PREGAME_REVISION')


def _time():return datetime.now(timezone.utc).isoformat()


def _bounded(value):
    if len(canonical(value).encode())>1_000_000:raise ServiceError(413,'PREGAME_TOO_LARGE')
    return value


def _input_record(r):
    if not isinstance(r,dict) or set(r)!=INPUT_FIELDS or r['schema_version']!='pregame.input.v1':raise ValueError('input record')
    _id(r['id']);_id(r['session_id']);_revision(r['revision'])
    if r['parent_id'] is not None:_id(r['parent_id'])
    parse_input(r['input'])
    if digest(r['input'])!=r['input_sha256'] or datetime.fromisoformat(r['created_at']).utcoffset().total_seconds()!=0:
        raise ValueError('input identity')
    _bounded(r)
    return r


def _plan_record(r):
    if not isinstance(r,dict) or set(r)!=PLAN_META|plan_fields(r) or r['schema_version'] not in ('pregame.plan.v1','pregame.plan.v2','pregame.plan.v3') or r['mode']!='PRE_GAME':
        raise ValueError('plan record')
    _id(r['id']);_id(r['session_id']);_revision(r['revision']);_revision(r['input_revision'])
    parse_input(r['input'])
    if digest(r['input'])!=r['input_sha256'] or not re.fullmatch('[a-f0-9]{64}',r['knowledge_fingerprint']):raise ValueError('plan identity')
    if r['coaching_accuracy'] is not None or r['real_match_validation']!='NOT_EVALUATED':raise ValueError('accuracy claim')
    if datetime.fromisoformat(r['created_at']).utcoffset().total_seconds()!=0:raise ValueError('plan time')
    _plan_structure(r)
    _bounded(r)
    return r


def _plan_structure(r):
    """Reject malformed history before it can reach the plan renderer."""
    def array(value, kind):
        if not isinstance(value,list) or any(not isinstance(item,kind) for item in value):raise ValueError('plan array')
    def cooldowns(values):
        array(values,dict)
        for c in values:
            for key in ('base_values','conditional_values'):
                array(c.get(key),(int,float))
            for key in ('reasons','conditional_reasons'):array(c.get(key),str)
            array(c.get('sources'),dict)
            if not isinstance(c.get('conditional'),dict):raise ValueError('cooldown conditional')
    def traces(values):
        array(values,dict)
        for t in values:
            array(t.get('sources'),dict);cooldowns(t.get('cooldowns'))
    def cell(c,key):
        if not isinstance(c,dict) or set(c)!={'key','title','status','texts','reasons','rules','outlook','cooldowns'}:
            raise ValueError('plan cell')
        if c['key']!=key or not isinstance(c['title'],str) or c['status'] not in ('UNKNOWN','KNOWN','CONFLICTING'):
            raise ValueError('plan cell identity')
        for field in ('texts','reasons'):array(c[field],str)
        traces(c['rules']);cooldowns(c['cooldowns'])
    if not isinstance(r['common'],dict) or set(r['common'])!={'map','jungle','composition'}:raise ValueError('common plan')
    if not isinstance(r['personal'],dict) or set(r['personal'])!={'role','lane','fight'}:raise ValueError('personal plan')
    array(r['common']['map'],dict)
    if len(r['common']['map'])!=len(POSITIONS):raise ValueError('map positions')
    for c,key in zip(r['common']['map'],POSITIONS):cell(c,key)
    for key in ('jungle','composition'):cell(r['common'][key],key.upper())
    for key in ('role','lane','fight'):cell(r['personal'][key],key.upper())
    cell(r['changes'],'CHANGES');traces(r['evaluations'])
    if r['schema_version'] in ('pregame.plan.v2','pregame.plan.v3'):
        cell(r['operations'],'OPERATIONS')
        summary=r['team_dependencies']
        if not isinstance(summary,dict) or set(summary)!={'status','dependency_risk','initiator_count','allies','reasons'}:raise ValueError('team summary')
        if summary['status'] not in ('KNOWN','UNKNOWN','CONFLICTING') or summary['dependency_risk'] not in (None,'NONE','NO_INITIATOR','SINGLE_INITIATOR'):raise ValueError('team summary status')
        if summary['initiator_count'] is not None and (type(summary['initiator_count']) is not int or not 0<=summary['initiator_count']<=5):raise ValueError('initiator count')
        array(summary['allies'],dict);array(summary['reasons'],str);array(r['pick_warnings'],dict)
    if r['schema_version']=='pregame.plan.v3':
        cell(r['movement'],'MOVEMENT')
        f=r['movement_statistics_fingerprint']
        if f is not None and (not isinstance(f,str) or not re.fullmatch('[a-f0-9]{64}',f)):raise ValueError('movement statistics identity')


class PregameStore:
    def __init__(self,path):
        self.dbpath=str(Path(path).resolve());Path(self.dbpath).parent.mkdir(parents=True,exist_ok=True)
        with self._db() as db:
            objects=db.execute('SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name').fetchall()
            if not objects:
                for sql in SCHEMAS:db.execute(sql)
                db.execute('PRAGMA user_version=1')
                try:Path(self.dbpath).chmod(0o600)
                except OSError:pass
            self._validate(db)

    @contextmanager
    def _db(self):
        db=sqlite3.connect(self.dbpath,timeout=10)
        try:
            db.execute('PRAGMA foreign_keys=ON');db.execute('PRAGMA secure_delete=ON');db.execute('BEGIN IMMEDIATE')
            yield db;db.commit()
        except Exception:db.rollback();raise
        finally:db.close()

    def _validate(self,db):
        try:
            with sqlite3.connect(':memory:') as expected:
                for sql in SCHEMAS:expected.execute(sql)
                query='SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name'
                if db.execute(query).fetchall()!=expected.execute(query).fetchall() or db.execute('PRAGMA user_version').fetchone()[0]!=1:
                    raise ValueError('schema')
            if db.execute('PRAGMA integrity_check').fetchall()!=[('ok',)] or db.execute('PRAGMA foreign_key_check').fetchone():raise ValueError('sqlite integrity')
            inputs={};heads={}
            for sid,revision,rid,parent,raw in db.execute('SELECT * FROM inputs ORDER BY session_id,revision'):
                r=_input_record(json.loads(raw))
                if canonical(r)!=raw or (r['session_id'],r['revision'],r['id'],r['parent_id'])!=(sid,revision,rid,parent):raise ValueError('columns')
                prior=heads.get(sid)
                if revision!=(prior['revision']+1 if prior else 1) or parent!=(prior['id'] if prior else None):raise ValueError('chain')
                inputs[(sid,revision)]=r;heads[sid]=r
            planheads={}
            for sid,revision,rid,irev,raw in db.execute('SELECT * FROM plans ORDER BY session_id,revision'):
                r=_plan_record(json.loads(raw))
                if canonical(r)!=raw or (r['session_id'],r['revision'],r['id'],r['input_revision'])!=(sid,revision,rid,irev):raise ValueError('plan columns')
                if revision!=planheads.get(sid,0)+1 or inputs[(sid,irev)]['input']!=r['input']:raise ValueError('plan input')
                planheads[sid]=revision
            for operation,key,fingerprint,raw in db.execute('SELECT * FROM operations'):
                if not KEY.fullmatch(key) or not re.fullmatch('[a-f0-9]{64}',fingerprint):raise ValueError('operation')
                response=json.loads(raw)
                (_plan_record if operation.startswith('plan:') else _input_record)(response)
                table='plans' if operation.startswith('plan:') else 'inputs'
                if operation=='create':
                    if response['revision']!=1:raise ValueError('create response')
                    expected_fingerprint=digest(dict(input=response['input'],expected_revision=0))
                elif operation=='input:'+response['session_id'] and table=='inputs':
                    if response['revision']<=1:raise ValueError('update response')
                    expected_fingerprint=digest(dict(input=response['input'],expected_revision=response['revision']-1))
                elif operation=='plan:'+response['session_id'] and table=='plans':
                    expected_fingerprint=digest(dict(expected_revision=response['input_revision']))
                else:raise ValueError('operation scope')
                if expected_fingerprint!=fingerprint:raise ValueError('operation fingerprint')
                row=db.execute('SELECT payload FROM '+table+' WHERE id=?',(response['id'],)).fetchone()
                if not row or row[0]!=raw:raise ValueError('operation response')
        except (ValueError,TypeError,KeyError,AttributeError,sqlite3.DatabaseError,ServiceError,OverflowError):
            raise ServiceError(409,'INVALID_STORED_PREGAME') from None

    @staticmethod
    def _current(db,sid):
        row=db.execute('SELECT payload FROM inputs WHERE session_id=? ORDER BY revision DESC LIMIT 1',(sid,)).fetchone()
        if not row:raise ServiceError(404,'PREGAME_INPUT_NOT_FOUND')
        return json.loads(row[0])

    @staticmethod
    def _replay(db,operation,key,fingerprint):
        if not isinstance(key,str) or not KEY.fullmatch(key):raise ServiceError(422,'IDEMPOTENCY_KEY_REQUIRED')
        row=db.execute('SELECT fingerprint,response FROM operations WHERE operation=? AND key=?',(operation,key)).fetchone()
        if row:
            if row[0]!=fingerprint:raise ServiceError(409,'IDEMPOTENCY_CONFLICT')
            return json.loads(row[1])

    def save(self,value,session_id,expected_revision,key):
        value=parse_input(value).model_dump(mode='json');_bounded(value);_revision(expected_revision,True)
        if session_id is not None:_id(session_id)
        elif expected_revision!=0:raise ServiceError(422,'INVALID_PREGAME_REVISION')
        operation='create' if session_id is None else 'input:'+session_id
        fingerprint=digest(dict(input=value,expected_revision=expected_revision))
        with self._db() as db:
            self._validate(db)
            replay=self._replay(db,operation,key,fingerprint)
            if replay:return replay
            prior=self._current(db,session_id) if session_id else None
            if prior and prior['revision']!=expected_revision:raise ServiceError(409,'REVISION_CONFLICT')
            result=dict(schema_version='pregame.input.v1',id=uuid.uuid4().hex,session_id=session_id or uuid.uuid4().hex,
                revision=expected_revision+1,parent_id=prior['id'] if prior else None,created_at=_time(),input=value,input_sha256=digest(value))
            _revision(result['revision'])
            raw=canonical(_bounded(result))
            db.execute('INSERT INTO inputs VALUES (?,?,?,?,?)',(result['session_id'],result['revision'],result['id'],result['parent_id'],raw))
            db.execute('INSERT INTO operations VALUES (?,?,?,?)',(operation,key,fingerprint,raw))
            return result

    def list_inputs(self):
        with self._db() as db:
            self._validate(db)
            return [dict(session_id=r['session_id'],title=r['input']['title'],revision=r['revision'],input_sha256=r['input_sha256'])
                for r in [json.loads(row[0]) for row in db.execute('SELECT payload FROM inputs p WHERE NOT EXISTS '
                    '(SELECT 1 FROM inputs n WHERE n.session_id=p.session_id AND n.revision>p.revision) ORDER BY rowid DESC')]]

    def get_input(self,sid):
        _id(sid)
        with self._db() as db:self._validate(db);return self._current(db,sid)

    def history(self,sid):
        _id(sid)
        with self._db() as db:
            self._validate(db);self._current(db,sid)
            return [json.loads(row[0]) for row in db.execute('SELECT payload FROM inputs WHERE session_id=? ORDER BY revision',(sid,))]

    def save_plan(self,sid,expected_revision,base,key):
        _id(sid);_revision(expected_revision)
        if not isinstance(base,dict) or set(base)!=plan_fields(base):raise ServiceError(422,'INVALID_PLAN')
        operation='plan:'+sid;fingerprint=digest(dict(expected_revision=expected_revision))
        with self._db() as db:
            self._validate(db)
            replay=self._replay(db,operation,key,fingerprint)
            if replay:return replay
            current=self._current(db,sid)
            if current['revision']!=expected_revision:raise ServiceError(409,'REVISION_CONFLICT')
            if current['input']!=base['input']:raise ServiceError(409,'PLAN_INPUT_CONFLICT')
            revision=db.execute('SELECT COALESCE(MAX(revision),0)+1 FROM plans WHERE session_id=?',(sid,)).fetchone()[0]
            result=dict(base,id=uuid.uuid4().hex,session_id=sid,revision=revision,input_revision=expected_revision,
                input_sha256=current['input_sha256'],created_at=_time())
            try:_plan_record(result)
            except (ValueError,TypeError,KeyError):raise ServiceError(422,'INVALID_PLAN') from None
            raw=canonical(result)
            db.execute('INSERT INTO plans VALUES (?,?,?,?,?)',(sid,revision,result['id'],expected_revision,raw))
            db.execute('INSERT INTO operations VALUES (?,?,?,?)',(operation,key,fingerprint,raw))
            return result

    def replay_plan(self,sid,expected_revision,key):
        """Retry identity is the HTTP request, independent of later knowledge."""
        _id(sid);_revision(expected_revision)
        with self._db() as db:
            self._validate(db)
            return self._replay(db,'plan:'+sid,key,digest(dict(expected_revision=expected_revision)))

    @staticmethod
    def _validity(db,r,fingerprint):
        reasons=[]
        if PregameStore._current(db,r['session_id'])['revision']!=r['input_revision']:reasons.append('INPUT_REVISION_CHANGED')
        if r['knowledge_fingerprint']!=fingerprint:reasons.append('KNOWLEDGE_CHANGED')
        return dict(r,validity='EXPIRED' if reasons else 'CURRENT',expiry_reasons=reasons)

    def get_plan(self,pid,fingerprint):
        _id(pid)
        with self._db() as db:
            self._validate(db);row=db.execute('SELECT payload FROM plans WHERE id=?',(pid,)).fetchone()
            if not row:raise ServiceError(404,'PREGAME_PLAN_NOT_FOUND')
            return self._validity(db,json.loads(row[0]),fingerprint)

    def list_plans(self,sid,fingerprint):
        _id(sid)
        with self._db() as db:
            self._validate(db);self._current(db,sid)
            return [self._validity(db,json.loads(row[0]),fingerprint) for row in db.execute('SELECT payload FROM plans WHERE session_id=? ORDER BY revision DESC',(sid,))]

    def export_data(self):
        with self._db() as db:
            self._validate(db)
            value=dict(schema_version='pregame.archive.v1',inputs=[json.loads(r[0]) for r in db.execute('SELECT payload FROM inputs ORDER BY session_id,revision')],
                plans=[json.loads(r[0]) for r in db.execute('SELECT payload FROM plans ORDER BY session_id,revision')],
                operations=[dict(zip(('operation','key','fingerprint','response'),r)) for r in db.execute('SELECT * FROM operations ORDER BY operation,key')])
            return dict(value,sha256=digest(value))

    def import_data(self,archive):
        try:
            if not isinstance(archive,dict) or set(archive)!={'schema_version','inputs','plans','operations','sha256'} or archive['schema_version']!='pregame.archive.v1':raise ValueError('archive')
            if digest({k:v for k,v in archive.items() if k!='sha256'})!=archive['sha256']:raise ValueError('archive hash')
            for name in ('inputs','plans','operations'):
                if not isinstance(archive[name],list):raise ValueError('archive rows')
            with self._db() as db:
                self._validate(db)
                if db.execute('SELECT COUNT(*) FROM inputs').fetchone()[0] or db.execute('SELECT COUNT(*) FROM operations').fetchone()[0]:
                    raise ServiceError(409,'RESTORE_REQUIRES_EMPTY_PREGAME')
                for r in archive['inputs']:
                    _input_record(r);db.execute('INSERT INTO inputs VALUES (?,?,?,?,?)',(r['session_id'],r['revision'],r['id'],r['parent_id'],canonical(r)))
                for r in archive['plans']:
                    _plan_record(r);db.execute('INSERT INTO plans VALUES (?,?,?,?,?)',(r['session_id'],r['revision'],r['id'],r['input_revision'],canonical(r)))
                for r in archive['operations']:
                    if set(r)!={'operation','key','fingerprint','response'}:raise ValueError('operation fields')
                    db.execute('INSERT INTO operations VALUES (?,?,?,?)',(r['operation'],r['key'],r['fingerprint'],r['response']))
                self._validate(db)
            return dict(status='RESTORED')
        except ServiceError:raise
        except (ValueError,TypeError,KeyError,sqlite3.DatabaseError):raise ServiceError(422,'INVALID_PREGAME_ARCHIVE') from None

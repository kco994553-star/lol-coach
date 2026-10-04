"""Local SQLite persistence for explicit TEST/SYNTHETIC cases only.

One application process owns a database. Startup recovery assumes the prior
process has stopped; this is deliberately not a multi-process task queue.
"""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import uuid

from .models import ReviewInput
from .engine import run_review


class ServiceError(Exception):
    def __init__(self, status: int, code: str):
        self.status, self.code = status, code
        super().__init__(code)


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _text(value, limit, code):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ServiceError(422, code)
    return value


def _revision(value):
    if type(value) is not int or value < 0:
        raise ServiceError(422, 'INVALID_REVISION')


class Store:
    SCHEMA_VERSION = 1

    def __init__(self, db_path):
        self.db_path = str(Path(db_path).resolve())
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            version = db.execute('PRAGMA user_version').fetchone()[0]
            tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            if version != self.SCHEMA_VERSION and (version != 0 or tables):
                raise ServiceError(409, 'INCOMPATIBLE_SCHEMA')
            if not tables:
                for sql in (
                    'CREATE TABLE sessions (id TEXT PRIMARY KEY,title TEXT NOT NULL,patch TEXT NOT NULL,mode TEXT NOT NULL,revision INTEGER NOT NULL,status TEXT NOT NULL)',
                    'CREATE TABLE cases (session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,revision INTEGER,payload TEXT NOT NULL,PRIMARY KEY(session_id,revision))',
                    'CREATE TABLE jobs (id TEXT PRIMARY KEY,session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,input_revision INTEGER NOT NULL,status TEXT NOT NULL,error TEXT,result TEXT)',
                    'CREATE TABLE idempotency (session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,operation TEXT,key TEXT,fingerprint TEXT NOT NULL,response TEXT NOT NULL,PRIMARY KEY(session_id,operation,key))',
                    'CREATE TABLE tombstones (id TEXT PRIMARY KEY)',
                ):
                    db.execute(sql)
                db.execute('PRAGMA user_version=1')
            expected = {
                'sessions': ('id', 'title', 'patch', 'mode', 'revision', 'status'),
                'cases': ('session_id', 'revision', 'payload'),
                'jobs': ('id', 'session_id', 'input_revision', 'status', 'error', 'result'),
                'idempotency': ('session_id', 'operation', 'key', 'fingerprint', 'response'),
                'tombstones': ('id',),
            }
            actual_tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if actual_tables != set(expected):
                raise ServiceError(409, 'INCOMPATIBLE_SCHEMA')
            for table, columns in expected.items():
                if tuple(r[1] for r in db.execute('PRAGMA table_info(' + table + ')')) != columns:
                    raise ServiceError(409, 'INCOMPATIBLE_SCHEMA')
            db.execute("UPDATE jobs SET status='FAILED',error='INTERRUPTED' WHERE status='RUNNING'")

    @contextmanager
    def _db(self):
        db = sqlite3.connect(self.db_path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA foreign_keys=ON')
            db.execute('PRAGMA secure_delete=ON')
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def _session(db, sid):
        row = db.execute('SELECT * FROM sessions WHERE id=?', (sid,)).fetchone()
        if not row:
            raise ServiceError(404, 'SESSION_NOT_FOUND')
        return dict(row)

    def create_session(self, title, patch, mode='TEST'):
        _text(title, 200, 'INVALID_TITLE'); _text(patch, 100, 'INVALID_PATCH')
        if mode != 'TEST':
            raise ServiceError(422, 'SYNTHETIC_TEST_ONLY')
        sid = str(uuid.uuid4())
        with self._db() as db:
            db.execute('INSERT INTO sessions VALUES (?,?,?,?,?,?)', (sid, title, patch, mode, 0, 'ACTIVE'))
            return self._session(db, sid)

    def list_sessions(self):
        with self._db() as db:
            return [dict(r) for r in db.execute('SELECT * FROM sessions ORDER BY rowid DESC')]

    def get_session(self, sid):
        with self._db() as db:
            return self._session(db, sid)

    @staticmethod
    def _replay(db, sid, op, key, fingerprint):
        _text(key, 128, 'INVALID_IDEMPOTENCY_KEY')
        row = db.execute('SELECT * FROM idempotency WHERE session_id=? AND operation=? AND key=?', (sid, op, key)).fetchone()
        if row:
            if row['fingerprint'] != fingerprint:
                raise ServiceError(409, 'IDEMPOTENCY_CONFLICT')
            return json.loads(row['response'])

    @staticmethod
    def _remember(db, sid, op, key, fingerprint, response):
        db.execute('INSERT INTO idempotency VALUES (?,?,?,?,?)', (sid, op, key, fingerprint, _json(response)))

    def put_case(self, sid, payload, expected_revision, key):
        _revision(expected_revision)
        if not isinstance(payload, dict):
            raise ServiceError(422, 'INVALID_CASE')
        try:
            encoded = _json(payload)
            if len(encoded.encode()) > 1_000_000:
                raise ServiceError(413, 'CASE_TOO_LARGE')
            case = ReviewInput.model_validate(payload)
        except ServiceError:
            raise
        except Exception:
            raise ServiceError(422, 'INVALID_CASE') from None
        fingerprint = hashlib.sha256(_json([expected_revision, payload]).encode()).hexdigest()
        with self._db() as db:
            session = self._session(db, sid)
            prior = self._replay(db, sid, 'PUT_CASE', key, fingerprint)
            if prior is not None:
                return prior
            if case.mode != 'TEST' or case.evidence_kind != 'SYNTHETIC':
                raise ServiceError(422, 'SYNTHETIC_TEST_ONLY')
            if (case.snapshot_request.session_id != sid or case.snapshot_request.patch != session['patch']
                or any(o.patch != session['patch'] for o in case.observations)
                or any(a.patch != session['patch'] for a in case.assessments)):
                raise ServiceError(422, 'SESSION_CASE_MISMATCH')
            if session['revision'] != expected_revision:
                raise ServiceError(409, 'REVISION_CONFLICT')
            revision = expected_revision + 1
            db.execute('INSERT INTO cases VALUES (?,?,?)', (sid, revision, encoded))
            db.execute('UPDATE sessions SET revision=? WHERE id=?', (revision, sid))
            response = dict(session_id=sid, revision=revision, case=payload)
            self._remember(db, sid, 'PUT_CASE', key, fingerprint, response)
            return response

    def get_case(self, sid):
        with self._db() as db:
            session = self._session(db, sid)
            row = db.execute('SELECT payload FROM cases WHERE session_id=? AND revision=?', (sid, session['revision'])).fetchone()
            if not row:
                raise ServiceError(404, 'CASE_NOT_FOUND')
            return dict(session_id=sid, revision=session['revision'], case=json.loads(row['payload']))

    @staticmethod
    def _job(db, jid):
        row = db.execute('SELECT jobs.*,sessions.revision AS current_revision FROM jobs JOIN sessions ON jobs.session_id=sessions.id WHERE jobs.id=?', (jid,)).fetchone()
        if not row:
            raise ServiceError(404, 'JOB_NOT_FOUND')
        return dict(id=row['id'], session_id=row['session_id'], input_revision=row['input_revision'], status=row['status'], error=row['error'], result_ref=row['id'] if row['status']=='COMPLETED' else None, stale=row['input_revision'] != row['current_revision'])

    def submit_review(self, sid, expected_revision, key):
        _revision(expected_revision)
        fingerprint = hashlib.sha256(_json(expected_revision).encode()).hexdigest()
        with self._db() as db:
            session = self._session(db, sid)
            prior = self._replay(db, sid, 'SUBMIT_REVIEW', key, fingerprint)
            if prior is not None:
                return prior
            if session['revision'] != expected_revision:
                raise ServiceError(409, 'REVISION_CONFLICT')
            if not expected_revision:
                raise ServiceError(409, 'CASE_REQUIRED')
            jid = str(uuid.uuid4())
            db.execute('INSERT INTO jobs VALUES (?,?,?,?,NULL,NULL)', (jid, sid, expected_revision, 'QUEUED'))
            response = self._job(db, jid)
            self._remember(db, sid, 'SUBMIT_REVIEW', key, fingerprint, response)
            return response

    def queued_job_ids(self):
        with self._db() as db:
            return [r[0] for r in db.execute("SELECT id FROM jobs WHERE status='QUEUED' ORDER BY rowid")]

    def run_job(self, job_id):
        with self._db() as db:
            job = self._job(db, job_id)
            if job['status'] != 'QUEUED':
                return job
            db.execute("UPDATE jobs SET status='RUNNING' WHERE id=?", (job_id,))
            payload = db.execute('SELECT payload FROM cases WHERE session_id=? AND revision=?', (job['session_id'], job['input_revision'])).fetchone()[0]
        try:
            result = _json(run_review(ReviewInput.model_validate_json(payload), allow_synthetic=True))
            status, error = 'COMPLETED', None
        except Exception:
            result, status, error = None, 'FAILED', 'REVIEW_FAILED'
        with self._db() as db:
            db.execute("UPDATE jobs SET status=?,error=?,result=? WHERE id=? AND status='RUNNING'", (status, error, result, job_id))
            try:
                return self._job(db, job_id)
            except ServiceError:
                return dict(id=job_id, status='DELETED')

    def cancel_job(self, job_id):
        with self._db() as db:
            job = self._job(db, job_id)
            if job['status'] in ('QUEUED', 'RUNNING'):
                db.execute("UPDATE jobs SET status='CANCELLED',result=NULL WHERE id=?", (job_id,))
            return self._job(db, job_id)

    def list_jobs(self, sid):
        with self._db() as db:
            self._session(db, sid)
            ids = [r[0] for r in db.execute("SELECT id FROM jobs WHERE session_id=? ORDER BY rowid DESC", (sid,))]
            return [self._job(db, jid) for jid in ids]

    def get_job(self, job_id):
        with self._db() as db:
            return self._job(db, job_id)

    def get_review(self, result_ref):
        with self._db() as db:
            job = self._job(db, result_ref)
            if job['status'] != 'COMPLETED':
                raise ServiceError(409, 'RESULT_UNAVAILABLE')
            result = db.execute('SELECT result FROM jobs WHERE id=?', (result_ref,)).fetchone()[0]
            return dict(id=result_ref, session_id=job['session_id'], input_revision=job['input_revision'], stale=job['stale'], result=json.loads(result))

    def delete_session(self, sid):
        with self._db() as db:
            if not db.execute('SELECT id FROM tombstones WHERE id=?', (sid,)).fetchone():
                self._session(db, sid)
                db.execute('DELETE FROM sessions WHERE id=?', (sid,))
                db.execute('INSERT INTO tombstones VALUES (?)', (sid,))
            return dict(id=sid, status='DELETED')

    def backup(self, destination):
        target = Path(destination).resolve()
        if target.exists():
            raise ServiceError(409, 'BACKUP_EXISTS')
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix='.backup-', dir=target.parent)
        os.close(fd)
        try:
            with sqlite3.connect(self.db_path) as source, sqlite3.connect(name) as copy:
                source.backup(copy)
                if copy.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                    raise ServiceError(500, 'BACKUP_INVALID')
            try:
                os.link(name, target)
            except FileExistsError:
                raise ServiceError(409, 'BACKUP_EXISTS') from None
            return dict(path=str(target), schema_version=self.SCHEMA_VERSION)
        finally:
            os.unlink(name)

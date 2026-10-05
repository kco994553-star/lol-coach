"""Immutable operator-entered draft captures, isolated from TEST analysis.

Manual source declarations remain UNVERIFIED. This module neither collects
client data nor generates a gameplan, Player reference or coaching result.
The original Store implementation and its TEST-only methods stay unchanged.
"""
from contextlib import closing
from datetime import datetime, timezone
import hashlib
from itertools import zip_longest
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile
import uuid

from coach_intake.io import strict_json
from .storage import Store, ServiceError, _json


SCHEMA_VERSION = 2
_MAIN_SCHEMAS = (
    'CREATE TABLE sessions (id TEXT PRIMARY KEY,title TEXT NOT NULL,patch TEXT NOT NULL,mode TEXT NOT NULL,revision INTEGER NOT NULL,status TEXT NOT NULL)',
    'CREATE TABLE cases (session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,revision INTEGER,payload TEXT NOT NULL,PRIMARY KEY(session_id,revision))',
    'CREATE TABLE jobs (id TEXT PRIMARY KEY,session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,input_revision INTEGER NOT NULL,status TEXT NOT NULL,error TEXT,result TEXT)',
    'CREATE TABLE idempotency (session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,operation TEXT,key TEXT,fingerprint TEXT NOT NULL,response TEXT NOT NULL,PRIMARY KEY(session_id,operation,key))',
    'CREATE TABLE tombstones (id TEXT PRIMARY KEY)',
)
DRAFT_SCHEMAS = (
    'CREATE TABLE draft_captures (id TEXT PRIMARY KEY,title TEXT NOT NULL,revision INTEGER NOT NULL)',
    'CREATE TABLE draft_snapshots (id TEXT PRIMARY KEY,session_id TEXT NOT NULL REFERENCES draft_captures(id) ON DELETE CASCADE,revision INTEGER NOT NULL,parent_id TEXT,payload TEXT NOT NULL,UNIQUE(session_id,revision),UNIQUE(session_id,id),FOREIGN KEY(session_id,parent_id) REFERENCES draft_snapshots(session_id,id))',
)
_INPUT_FIELDS = frozenset(('title', 'phase', 'patch', 'observed_at', 'visible_picks',
                          'visible_bans', 'role_assignments', 'source'))
_RECORD_FIELDS = frozenset(('schema_version', 'id', 'session_id', 'revision', 'parent_id',
                           'received_at', 'capture', 'input_sha256', 'adapter_capability',
                           'validation_state', 'gameplan_status', 'coaching_enabled'))
_TOKEN = re.compile(r'[a-f0-9]{32}')
_TIMESTAMP = re.compile(r'\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:\d{2})')
_MAX_INTEGER = 9223372036854775807
# The existing private Workbench body limit also bounds stored main payloads.
_MAX_RECORD_BYTES = 1_000_000


def _schema(db, version):
    try:
        if db.execute('PRAGMA user_version').fetchone()[0] != version:
            raise ValueError('schema version')
        with closing(sqlite3.connect(':memory:')) as expected:
            for sql in _MAIN_SCHEMAS + (DRAFT_SCHEMAS if version == SCHEMA_VERSION else ()):
                expected.execute(sql)
            query = 'SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name'
            if [tuple(row) for row in db.execute(query)] != [tuple(row) for row in expected.execute(query)]:
                raise ValueError('schema objects')
            tables = ('sessions', 'cases', 'jobs', 'idempotency', 'tombstones') + (
                ('draft_captures', 'draft_snapshots') if version == SCHEMA_VERSION else ())
            for table in tables:
                for pragma in ('table_info', 'foreign_key_list'):
                    if ([tuple(row) for row in db.execute('PRAGMA '+pragma+'('+table+')')]
                        != [tuple(row) for row in expected.execute('PRAGMA '+pragma+'('+table+')')]):
                        raise ValueError('schema constraints')
    except (ValueError, TypeError, sqlite3.DatabaseError):
        raise ServiceError(409, 'INCOMPATIBLE_DRAFT_SCHEMA') from None


def validate_schema(db):
    """Pure exact main-v2 SQL/object/PK/FK validation."""
    _schema(db, SCHEMA_VERSION)


def _legacy_content(db):
    # Existing backup semantics remain the sole TEST-domain validator. Changing
    # row_factory affects only this connection's Python views, never its rows.
    from .backup import _validate_main_content
    original_factory = db.row_factory
    try:
        db.row_factory = sqlite3.Row
        if ([tuple(row) for row in db.execute('PRAGMA integrity_check')] != [('ok',)]
            or db.execute('PRAGMA foreign_key_check').fetchone() is not None):
            raise ValueError('legacy integrity')
        for table, column in (('cases', 'payload'), ('jobs', 'result'), ('idempotency', 'response')):
            for row in db.execute('SELECT '+column+' FROM '+table+' WHERE '+column+' IS NOT NULL'):
                if not isinstance(row[0], str) or not isinstance(strict_json(row[0]), dict):
                    raise ValueError('legacy JSON object')
        _validate_main_content(db)
    except (ValueError, TypeError, KeyError, AttributeError, UnicodeError, RecursionError, sqlite3.DatabaseError):
        raise ServiceError(409, 'INVALID_STORED_DRAFT') from None
    finally:
        db.row_factory = original_factory


def _migration_snapshot(db, path):
    """Publish validated private main-v1 bytes while BEGIN IMMEDIATE blocks writers."""
    from .backup import MAX_DATABASE_BYTES, MAIN, _copy_database, _file_metadata, _validate_database
    path = Path(path)
    if db.execute('PRAGMA page_count').fetchone()[0] * db.execute('PRAGMA page_size').fetchone()[0] > MAX_DATABASE_BYTES:
        raise ValueError('migration snapshot capacity')
    target = path.with_name(path.name+'.pre-draft-v2-'+uuid.uuid4().hex+'.sqlite')
    descriptor, name = tempfile.mkstemp(prefix=path.name+'.migration-', suffix='.sqlite', dir=path.parent)
    temporary = Path(name)
    os.close(descriptor)
    try:
        # SQLite backup on the connection owning BEGIN IMMEDIATE can self-block.
        # This separate reader sees the committed v1 state under that write lock.
        with closing(sqlite3.connect(path.as_uri()+'?mode=ro', uri=True)) as reader:
            _copy_database(reader, temporary)
        _validate_database(temporary, MAIN)
        with closing(sqlite3.connect(temporary.as_uri()+'?mode=ro&immutable=1', uri=True)) as copy:
            _schema(copy, 1)
            for table in ('sessions', 'cases', 'jobs', 'idempotency', 'tombstones'):
                query = 'SELECT * FROM '+table+' ORDER BY rowid'
                sentinel = object()
                for original, recovered in zip_longest(db.execute(query), copy.execute(query), fillvalue=sentinel):
                    if original is sentinel or recovered is sentinel or tuple(original) != tuple(recovered):
                        raise ValueError('migration snapshot row mismatch')
        metadata = _file_metadata(temporary)
        if metadata['schema_version'] != 1:
            raise ValueError('migration snapshot version')
        os.chmod(temporary, 0o600)
        with temporary.open('rb') as stream:
            os.fsync(stream.fileno())
        os.link(temporary, target)
        return dict(path=str(target), **metadata)
    finally:
        temporary.unlink(missing_ok=True)


def _text(value, maximum):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError('text')
    value.encode('utf-8')


def _timestamp(value):
    _text(value, 100)
    if not _TIMESTAMP.fullmatch(value):
        raise ValueError('timestamp syntax')
    parsed = datetime.fromisoformat(value)
    if parsed.utcoffset() is None:
        raise ValueError('timestamp offset')
    return parsed


def _capture(value):
    try:
        if not isinstance(value, dict) or set(value) != _INPUT_FIELDS:
            raise ValueError('capture fields')
        _text(value['title'], 200)
        for field in ('phase', 'patch'):
            if value[field] is not None:
                _text(value[field], 100)
        if value['observed_at'] is not None:
            _timestamp(value['observed_at'])
        for field in ('visible_picks', 'visible_bans', 'role_assignments'):
            rows = value[field]
            if not isinstance(rows, list) or len(rows) > 10:
                raise ValueError('capture rows')
            seen = set()
            keys = {'side', 'slot', 'role', 'uncertainty'} if field == 'role_assignments' else {'side', 'slot', 'champion'}
            for row in rows:
                if (not isinstance(row, dict) or set(row) != keys or row['side'] not in ('ALLY', 'ENEMY')
                    or type(row['slot']) is not int or not 1 <= row['slot'] <= 5):
                    raise ValueError('capture slot')
                slot = row['side'], row['slot']
                if slot in seen:
                    raise ValueError('duplicate capture slot')
                seen.add(slot)
                if field == 'role_assignments':
                    if row['role'] not in (None, 'TOP', 'JUNGLE', 'MID', 'BOTTOM', 'SUPPORT'):
                        raise ValueError('role')
                    _text(row['uncertainty'], 2000)
                elif row['champion'] is not None:
                    _text(row['champion'], 100)
        source = value['source']
        if (not isinstance(source, dict) or set(source) != {'author', 'perspective', 'description'}
            or source['perspective'] not in ('PLAYER', 'UNKNOWN')):
            raise ValueError('source declaration')
        _text(source['author'], 200)
        _text(source['description'], 2000)
        return strict_json(_json(value))
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError):
        raise ServiceError(422, 'INVALID_DRAFT_CAPTURE') from None


def _id(value):
    if not isinstance(value, str) or not _TOKEN.fullmatch(value):
        raise ServiceError(422, 'INVALID_DRAFT_ID')


def _revision(value):
    if type(value) is not int or not 1 <= value <= _MAX_INTEGER:
        raise ServiceError(422, 'INVALID_DRAFT_REVISION')


def _budget(value):
    if type(value) is not int or value <= 0:
        raise ServiceError(422, 'INVALID_DRAFT_LIMIT')


def _bounded(value, max_bytes):
    if len(json.dumps(value, ensure_ascii=False, allow_nan=False).encode('utf-8')) > max_bytes:
        raise ServiceError(413, 'DRAFT_CAPTURE_TOO_LARGE')
    return value


def validate_draft_content(db):
    """Pure stored identity/provenance/hash/complete-history validation."""
    try:
        if db.execute('PRAGMA foreign_key_check').fetchone() is not None:
            raise ValueError('foreign keys')
        legacy_ids = {row[0] for row in db.execute('SELECT id FROM sessions UNION SELECT id FROM tombstones')}
        captures = {}
        for row in db.execute('SELECT id,title,revision FROM draft_captures'):
            cid, title, revision = tuple(row)
            _id(cid); _text(title, 200); _revision(revision)
            if cid in legacy_ids:
                raise ValueError('legacy ID collision')
            captures[cid] = dict(title=title, revision=revision)
        groups = {cid: {} for cid in captures}
        for row in db.execute('SELECT id,session_id,revision,parent_id,payload FROM draft_snapshots'):
            sid, cid, revision, parent, raw = tuple(row)
            _id(sid); _id(cid); _revision(revision)
            if parent is not None:
                _id(parent)
            if sid in legacy_ids or sid in captures or not isinstance(raw, str) or len(raw.encode('utf-8')) > _MAX_RECORD_BYTES:
                raise ValueError('snapshot identity or budget')
            record = strict_json(raw)
            if (not isinstance(record, dict) or set(record) != _RECORD_FIELDS
                or record['schema_version'] != 'mvp.manual-draft.v1'
                or record['id'] != sid or record['session_id'] != cid
                or type(record['revision']) is not int or record['revision'] != revision
                or record['parent_id'] != parent or record['validation_state'] != 'UNVERIFIED'
                or record['gameplan_status'] != 'NOT_GENERATED' or record['coaching_enabled'] is not False
                or record['adapter_capability'] != {'automatic_collection':'UNAVAILABLE', 'manual_capture':'AVAILABLE'}
                or _json(record) != raw):
                raise ValueError('stored record')
            entered = _capture(record['capture'])
            if record['input_sha256'] != hashlib.sha256(_json(entered).encode('utf-8')).hexdigest():
                raise ValueError('capture hash')
            if _timestamp(record['received_at']).utcoffset().total_seconds() != 0:
                raise ValueError('received time must be UTC')
            groups[cid][revision] = dict(id=sid, parent=parent, capture=entered)
        for cid, metadata in captures.items():
            versions = groups[cid]
            if sorted(versions) != list(range(1, metadata['revision']+1)):
                raise ValueError('incomplete snapshot history')
            for revision, record in versions.items():
                expected = None if revision == 1 else versions[revision-1]['id']
                if record['parent'] != expected:
                    raise ValueError('immutable parent chain')
            if versions[metadata['revision']]['capture']['title'] != metadata['title']:
                raise ValueError('current capture metadata')
    except (ServiceError, ValueError, TypeError, KeyError, AttributeError, UnicodeError, RecursionError, sqlite3.DatabaseError):
        raise ServiceError(409, 'INVALID_STORED_DRAFT') from None


class DraftStore(Store):
    SCHEMA_VERSION = SCHEMA_VERSION

    def __init__(self, db_path):
        self.db_path = str(Path(db_path).resolve())
        self.migration_backup = None
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            version = db.execute('PRAGMA user_version').fetchone()[0]
            if version == SCHEMA_VERSION:
                validate_schema(db)
                _legacy_content(db)
                validate_draft_content(db)
            elif version == 1:
                _schema(db, 1)
                _legacy_content(db)
                try:
                    self.migration_backup = _migration_snapshot(db, self.db_path)
                except Exception:
                    raise ServiceError(503, 'MIGRATION_BACKUP_FAILED') from None
                for sql in DRAFT_SCHEMAS:
                    db.execute(sql)
                db.execute('PRAGMA user_version=2')
                validate_schema(db)
                validate_draft_content(db)
            elif version == 0 and not db.execute('SELECT name FROM sqlite_master').fetchall():
                for sql in _MAIN_SCHEMAS + DRAFT_SCHEMAS:
                    db.execute(sql)
                db.execute('PRAGMA user_version=2')
                validate_schema(db)
                validate_draft_content(db)
            else:
                raise ServiceError(409, 'INCOMPATIBLE_DRAFT_SCHEMA')
            # Preserve original Store recovery semantics after the old bytes
            # have been backed up and the complete v2 transaction validated.
            db.execute("UPDATE jobs SET status='FAILED',error='INTERRUPTED' WHERE status='RUNNING'")

    @staticmethod
    def _capture_row(db, cid):
        row = db.execute('SELECT id,title,revision FROM draft_captures WHERE id=?', (cid,)).fetchone()
        if row is None:
            raise ServiceError(404, 'DRAFT_CAPTURE_NOT_FOUND')
        return dict(row)

    @staticmethod
    def _snapshot(db, cid, revision):
        row = db.execute('SELECT payload FROM draft_snapshots WHERE session_id=? AND revision=?', (cid, revision)).fetchone()
        if row is None:
            raise ServiceError(404, 'DRAFT_CAPTURE_NOT_FOUND')
        return strict_json(row[0])

    @staticmethod
    def _fresh_id(db):
        value = uuid.uuid4().hex
        if db.execute('SELECT id FROM sessions WHERE id=? UNION SELECT id FROM tombstones WHERE id=? '
                      'UNION SELECT id FROM draft_captures WHERE id=? UNION SELECT id FROM draft_snapshots WHERE id=?',
                      (value, value, value, value)).fetchone() is not None:
            raise ServiceError(409, 'DRAFT_CAPTURE_ID_CONFLICT')
        return value

    @staticmethod
    def _record(sid, cid, revision, parent, entered):
        return dict(schema_version='mvp.manual-draft.v1', id=sid, session_id=cid,
            revision=revision, parent_id=parent, received_at=datetime.now(timezone.utc).isoformat(),
            capture=entered, input_sha256=hashlib.sha256(_json(entered).encode('utf-8')).hexdigest(),
            adapter_capability={'automatic_collection':'UNAVAILABLE', 'manual_capture':'AVAILABLE'},
            validation_state='UNVERIFIED', gameplan_status='NOT_GENERATED', coaching_enabled=False)

    def create_capture(self, capture, max_bytes):
        _budget(max_bytes); entered = _capture(capture)
        with self._db() as db:
            validate_draft_content(db)
            cid = self._fresh_id(db)
            db.execute('INSERT INTO draft_captures VALUES (?,?,?)', (cid, entered['title'], 1))
            sid = self._fresh_id(db)
            record = _bounded(self._record(sid, cid, 1, None, entered), max_bytes)
            db.execute('INSERT INTO draft_snapshots VALUES (?,?,?,?,?)', (sid, cid, 1, None, _json(record)))
            return record

    def list_captures(self, max_bytes):
        _budget(max_bytes)
        with self._db() as db:
            validate_draft_content(db)
            records = [strict_json(row[0]) for row in db.execute('SELECT s.payload FROM draft_captures c '
                       'JOIN draft_snapshots s ON s.session_id=c.id AND s.revision=c.revision ORDER BY c.rowid DESC')]
            return _bounded(records, max_bytes)

    def get_capture(self, cid, revision=None, *, max_bytes):
        _budget(max_bytes); _id(cid)
        if revision is not None:
            _revision(revision)
        with self._db() as db:
            validate_draft_content(db)
            current = self._capture_row(db, cid)
            return _bounded(self._snapshot(db, cid, current['revision'] if revision is None else revision), max_bytes)

    def capture_history(self, cid, max_bytes):
        _budget(max_bytes); _id(cid)
        with self._db() as db:
            validate_draft_content(db)
            current = self._capture_row(db, cid)
            revisions = [row[0] for row in db.execute('SELECT revision FROM draft_snapshots WHERE session_id=? ORDER BY revision', (cid,))]
            return _bounded(dict(session_id=cid, current_revision=current['revision'],
                                 revision_count=len(revisions), revisions=revisions), max_bytes)

    def put_capture(self, cid, capture, expected_revision, max_bytes):
        _budget(max_bytes); _id(cid); _revision(expected_revision); entered = _capture(capture)
        with self._db() as db:
            validate_draft_content(db)
            current = self._capture_row(db, cid)
            if current['revision'] != expected_revision:
                raise ServiceError(409, 'REVISION_CONFLICT')
            revision = expected_revision+1; _revision(revision)
            parent = self._snapshot(db, cid, expected_revision)['id']
            sid = self._fresh_id(db)
            record = _bounded(self._record(sid, cid, revision, parent, entered), max_bytes)
            db.execute('INSERT INTO draft_snapshots VALUES (?,?,?,?,?)', (sid, cid, revision, parent, _json(record)))
            db.execute('UPDATE draft_captures SET title=?,revision=? WHERE id=?', (entered['title'], revision, cid))
            return record

    def delete_capture(self, cid, expected_revision, max_bytes):
        _budget(max_bytes); _id(cid); _revision(expected_revision)
        with self._db() as db:
            validate_draft_content(db)
            current = self._capture_row(db, cid)
            if current['revision'] != expected_revision:
                raise ServiceError(409, 'REVISION_CONFLICT')
            count = db.execute('SELECT COUNT(*) FROM draft_snapshots WHERE session_id=?', (cid,)).fetchone()[0]
            response = _bounded(dict(id=cid, status='DELETED', deleted_snapshots=count), max_bytes)
            db.execute('DELETE FROM draft_captures WHERE id=?', (cid,))
            return response

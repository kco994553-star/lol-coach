"""Sidecar research reports and manual notes; notes never become game evidence."""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from .storage import ServiceError


FIELDS = ('known', 'intention', 'alternative', 'outcome')
SCHEMA_VERSION = 1


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


class ResearchStore:
    def __init__(self, dbpath):
        self.dbpath = str(Path(dbpath).resolve())
        Path(self.dbpath).parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            version = db.execute('PRAGMA user_version').fetchone()[0]
            tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if version != SCHEMA_VERSION and (version != 0 or tables):
                raise ServiceError(409, 'INCOMPATIBLE_RESEARCH_SCHEMA')
            if not tables:
                db.execute('CREATE TABLE resources (id TEXT PRIMARY KEY,kind TEXT NOT NULL,title TEXT NOT NULL,report TEXT NOT NULL)')
                db.execute('CREATE TABLE note_history (resource_id TEXT NOT NULL REFERENCES resources(id) ON DELETE CASCADE,anchor TEXT NOT NULL,revision INTEGER NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(resource_id,anchor,revision))')
                db.execute('PRAGMA user_version=1')
            expected = {
                'resources': ('id', 'kind', 'title', 'report'),
                'note_history': ('resource_id', 'anchor', 'revision', 'payload'),
            }
            actual = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if actual != set(expected):
                raise ServiceError(409, 'INCOMPATIBLE_RESEARCH_SCHEMA')
            for table, columns in expected.items():
                if tuple(r[1] for r in db.execute('PRAGMA table_info('+table+')')) != columns:
                    raise ServiceError(409, 'INCOMPATIBLE_RESEARCH_SCHEMA')
            foreign = db.execute('PRAGMA foreign_key_list(note_history)').fetchall()
            if len(foreign) != 1 or (foreign[0][2], foreign[0][3], foreign[0][4], foreign[0][6]) != ('resources', 'resource_id', 'id', 'CASCADE'):
                raise ServiceError(409, 'INCOMPATIBLE_RESEARCH_SCHEMA')

    @contextmanager
    def _db(self):
        db = sqlite3.connect(self.dbpath, timeout=10)
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
    def _resource(db, rid):
        if not isinstance(rid, str):
            raise ServiceError(404, 'RESOURCE_NOT_FOUND')
        row = db.execute('SELECT * FROM resources WHERE id=?', (rid,)).fetchone()
        if row is None:
            raise ServiceError(404, 'RESOURCE_NOT_FOUND')
        return dict(id=row['id'], kind=row['kind'], title=row['title'], report=json.loads(row['report']))

    def add(self, kind, title, report):
        if not isinstance(kind, str) or not re.fullmatch(r'[A-Z][A-Z0-9_]{0,31}', kind):
            raise ServiceError(422, 'INVALID_RESOURCE_KIND')
        if not isinstance(title, str) or not title.strip() or len(title) > 200:
            raise ServiceError(422, 'INVALID_TITLE')
        try:
            title.encode('utf-8')
        except UnicodeError:
            raise ServiceError(422, 'INVALID_TITLE') from None
        if not isinstance(report, dict):
            raise ServiceError(422, 'INVALID_REPORT')
        try:
            encoded = _json(report)
            canonical = _json({'kind': kind, 'report': report})
            if len(encoded.encode('utf-8')) > 2_000_000:
                raise ServiceError(413, 'REPORT_TOO_LARGE')
            rid = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
        except ServiceError:
            raise
        except (TypeError, ValueError, UnicodeError, RecursionError):
            raise ServiceError(422, 'INVALID_REPORT') from None
        with self._db() as db:
            db.execute('INSERT OR IGNORE INTO resources VALUES (?,?,?,?)', (rid, kind, title, encoded))
            return self._resource(db, rid)

    def list(self):
        with self._db() as db:
            return [dict(row) for row in db.execute('SELECT id,kind,title FROM resources ORDER BY rowid DESC')]

    def get(self, rid):
        with self._db() as db:
            return self._resource(db, rid)

    def delete(self, rid):
        with self._db() as db:
            self._resource(db, rid)
            db.execute('DELETE FROM resources WHERE id=?', (rid,))
            return dict(id=rid, status='DELETED')

    @staticmethod
    def _anchor(resource, anchor):
        if anchor == 'overview':
            return
        if not isinstance(anchor, str) or len(anchor) > 32 or resource['kind'] != 'VIDEO':
            raise ServiceError(422, 'INVALID_NOTE_ANCHOR')
        candidates = resource['report'].get('candidates', [])
        if not isinstance(candidates, list) or not any(
            isinstance(c, dict) and type(c.get('cue_index')) is int and c['cue_index'] >= 0 and str(c['cue_index']) == anchor
            for c in candidates
        ):
            raise ServiceError(422, 'INVALID_NOTE_ANCHOR')

    @staticmethod
    def _note(db, rid, anchor):
        row = db.execute('SELECT revision,payload FROM note_history WHERE resource_id=? AND anchor=? ORDER BY revision DESC LIMIT 1', (rid, anchor)).fetchone()
        return dict(resource_id=rid, anchor=anchor, revision=row['revision'] if row else 0,
                    **(json.loads(row['payload']) if row else {field: '' for field in FIELDS}))

    def get_note(self, rid, anchor):
        with self._db() as db:
            self._anchor(self._resource(db, rid), anchor)
            return self._note(db, rid, anchor)

    def put_note(self, rid, anchor, payload, expected_revision):
        if type(expected_revision) is not int or expected_revision < 0:
            raise ServiceError(422, 'INVALID_REVISION')
        if (not isinstance(payload, dict) or set(payload) != set(FIELDS)
            or any(not isinstance(payload[f], str) or len(payload[f]) > 2000 for f in FIELDS)):
            raise ServiceError(422, 'INVALID_NOTE')
        try:
            encoded = _json(payload)
            encoded.encode('utf-8')
        except (ValueError, UnicodeError):
            raise ServiceError(422, 'INVALID_NOTE') from None
        with self._db() as db:
            self._anchor(self._resource(db, rid), anchor)
            current = self._note(db, rid, anchor)
            if current['revision'] != expected_revision:
                raise ServiceError(409, 'REVISION_CONFLICT')
            db.execute('INSERT INTO note_history VALUES (?,?,?,?)', (rid, anchor, expected_revision+1, encoded))
            return self._note(db, rid, anchor)

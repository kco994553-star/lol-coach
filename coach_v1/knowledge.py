"""Source-bound exploratory proposals; no engine activation or review promotion.

Research v1 remains independently readable by its original implementation. This
store performs an atomic, additive v2 migration and keeps references as SQLite
foreign keys. Pure validators are also used by offline backup/restore.
"""
from contextlib import closing
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
from .note_history import _stored_note
from .research import ResearchStore, _json
from .storage import ServiceError


SCHEMA_VERSION = 2
KNOWLEDGE_SCHEMAS = (
    'CREATE TABLE knowledge_rules (id TEXT NOT NULL,version TEXT NOT NULL,status TEXT NOT NULL,payload TEXT NOT NULL,resource_id TEXT NOT NULL,anchor TEXT NOT NULL,revision INTEGER NOT NULL,parent_version TEXT,PRIMARY KEY(id,version),FOREIGN KEY(resource_id,anchor,revision) REFERENCES note_history(resource_id,anchor,revision) ON DELETE CASCADE,FOREIGN KEY(id,parent_version) REFERENCES knowledge_rules(id,version) ON DELETE CASCADE)',
    'CREATE TABLE knowledge_delete_receipts (id TEXT PRIMARY KEY,deleted_count INTEGER NOT NULL)',
)
_RESEARCH_SCHEMAS = (
    'CREATE TABLE resources (id TEXT PRIMARY KEY,kind TEXT NOT NULL,title TEXT NOT NULL,report TEXT NOT NULL)',
    'CREATE TABLE note_history (resource_id TEXT NOT NULL REFERENCES resources(id) ON DELETE CASCADE,anchor TEXT NOT NULL,revision INTEGER NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(resource_id,anchor,revision))',
)
RULE_FIELDS = frozenset(('patch_range', 'applicability', 'required_fields', 'claim',
                        'mechanism', 'counterexamples', 'author', 'limitations'))
APPLICABILITY_FIELDS = frozenset(('champion', 'role', 'matchup', 'level', 'context'))
_REPORT_FIELDS = RULE_FIELDS | {'schema_version', 'rule_id', 'version', 'source_refs',
                              'review_state', 'supersedes', 'coaching_enabled'}
_SOURCE_FIELDS = frozenset(('resource_id', 'anchor', 'note_revision'))
_TOKEN = re.compile(r'[a-f0-9]{32}')
_HASH = re.compile(r'[a-f0-9]{64}')
_MAX_SQLITE_INTEGER = 9223372036854775807


def _schema(db, version):
    try:
        if db.execute('PRAGMA user_version').fetchone()[0] != version:
            raise ValueError('version')
        with closing(sqlite3.connect(':memory:')) as expected:
            for sql in _RESEARCH_SCHEMAS + (KNOWLEDGE_SCHEMAS if version == 2 else ()):
                expected.execute(sql)
            query = 'SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name'
            if [tuple(r) for r in db.execute(query)] != [tuple(r) for r in expected.execute(query)]:
                raise ValueError('schema')
            for table in ('resources', 'note_history') + (
                ('knowledge_rules', 'knowledge_delete_receipts') if version == 2 else ()
            ):
                for pragma in ('table_info', 'foreign_key_list'):
                    if ([tuple(r) for r in db.execute('PRAGMA '+pragma+'('+table+')')]
                        != [tuple(r) for r in expected.execute('PRAGMA '+pragma+'('+table+')')]):
                        raise ValueError('constraints')
    except (ValueError, TypeError, sqlite3.DatabaseError):
        raise ServiceError(409, 'INCOMPATIBLE_KNOWLEDGE_SCHEMA') from None


def validate_schema(db):
    """Validate exact v2 SQL, objects, PKs and FKs without changing the connection."""
    _schema(db, SCHEMA_VERSION)


def _legacy_content(db):
    # Reuse the existing pure resource/hash/note-history verifier. Import at
    # runtime because backup also imports the knowledge validators for v2.
    from .backup import _validate_research_content
    try:
        for query in ('SELECT report FROM resources', 'SELECT payload FROM note_history'):
            for row in db.execute(query):
                if not isinstance(row[0], str) or not isinstance(strict_json(row[0]), dict):
                    raise ValueError('stored object')
        _validate_research_content(db)
    except (ValueError, TypeError, KeyError, AttributeError, UnicodeError, RecursionError):
        raise ServiceError(409, 'INVALID_STORED_KNOWLEDGE') from None


def _migration_snapshot(db, path):
    """Publish a private recoverable v1 snapshot before executing any v2 DDL.

The caller owns BEGIN IMMEDIATE. A separate read-only reader is necessary:
backing up a connection that owns its own write transaction can self-block.
"""
    from .backup import (MAX_DATABASE_BYTES, RESEARCH, _copy_database, _file_metadata,
                         _validate_database)
    path = Path(path)
    if db.execute('PRAGMA page_count').fetchone()[0] * db.execute('PRAGMA page_size').fetchone()[0] > MAX_DATABASE_BYTES:
        raise ValueError('migration backup exceeds existing database budget')
    destination = path.with_name(path.name+'.pre-knowledge-v2-'+uuid.uuid4().hex+'.sqlite')
    descriptor, name = tempfile.mkstemp(prefix=path.name+'.migration-', suffix='.sqlite', dir=path.parent)
    temporary = Path(name)
    os.close(descriptor)
    try:
        with closing(sqlite3.connect(path.as_uri()+'?mode=ro', uri=True)) as reader:
            _copy_database(reader, temporary)
        _validate_database(temporary, RESEARCH)
        with closing(sqlite3.connect(temporary.as_uri()+'?mode=ro&immutable=1', uri=True)) as copied:
            _schema(copied, 1)
            # Compare exact stored strings, not reserialized approximations.
            # Stream rows so the gate does not copy every private note in RAM.
            for query in ('SELECT id,kind,title,report FROM resources ORDER BY id',
                          'SELECT resource_id,anchor,revision,payload FROM note_history '
                          'ORDER BY resource_id,anchor,revision'):
                sentinel = object()
                for original, recovered in zip_longest(db.execute(query), copied.execute(query),
                                                        fillvalue=sentinel):
                    if original is sentinel or recovered is sentinel or tuple(original) != tuple(recovered):
                        raise ValueError('migration snapshot mismatch')
        metadata = _file_metadata(temporary)
        os.chmod(temporary, 0o600)
        with temporary.open('rb') as stream:
            os.fsync(stream.fileno())
        # A hard link publishes a complete file with exclusive/no-overwrite
        # semantics, following the existing personal backup publication path.
        os.link(temporary, destination)
        return dict(path=str(destination), **metadata)
    finally:
        temporary.unlink(missing_ok=True)


def _budget(max_bytes):
    if type(max_bytes) is not int or max_bytes <= 0:
        raise ServiceError(422, 'INVALID_KNOWLEDGE_LIMIT')


def _bounded(value, max_bytes):
    if len(json.dumps(value, ensure_ascii=False, allow_nan=False).encode('utf-8')) > max_bytes:
        raise ServiceError(413, 'KNOWLEDGE_TOO_LARGE')
    return value


def _text(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 2000:
        raise ValueError('text')
    value.encode('utf-8')


def _rule(rule):
    try:
        if not isinstance(rule, dict) or set(rule) != RULE_FIELDS:
            raise ValueError('fields')
        for field in ('patch_range', 'claim', 'mechanism', 'author'):
            _text(rule[field])
        scope = rule['applicability']
        if not isinstance(scope, dict) or set(scope) != APPLICABILITY_FIELDS:
            raise ValueError('applicability')
        for value in scope.values():
            _text(value)
        for field in ('required_fields', 'counterexamples', 'limitations'):
            if not isinstance(rule[field], list):
                raise ValueError('list')
            for value in rule[field]:
                _text(value)
        # Copy through the same strict JSON boundary; callers cannot mutate a
        # payload already accepted by a later transaction.
        return strict_json(_json(rule))
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise ServiceError(422, 'INVALID_KNOWLEDGE_RULE') from None


def _token(value):
    if not isinstance(value, str) or not _TOKEN.fullmatch(value):
        raise ServiceError(422, 'INVALID_KNOWLEDGE_ID')
    return value


def _source_binding(db, source):
    if (not isinstance(source, dict) or set(source) != _SOURCE_FIELDS
        or not isinstance(source['resource_id'], str) or not _HASH.fullmatch(source['resource_id'])
        or not isinstance(source['anchor'], str)
        or type(source['note_revision']) is not int
        or not 1 <= source['note_revision'] <= _MAX_SQLITE_INTEGER):
        raise ServiceError(422, 'INVALID_KNOWLEDGE_SOURCE')
    resource = ResearchStore._resource(db, source['resource_id'])
    if resource['kind'] not in ('VIDEO', 'RAW_DIAGNOSTIC'):
        raise ServiceError(422, 'INVALID_KNOWLEDGE_SOURCE')
    ResearchStore._anchor(resource, source['anchor'])
    report = db.execute('SELECT report FROM resources WHERE id=?', (source['resource_id'],)).fetchone()[0]
    try:
        if not isinstance(strict_json(report), dict):
            raise ValueError('source object')
        canonical = '{"kind":' + _json(resource['kind']) + ',"report":' + report + '}'
        if (hashlib.sha256(canonical.encode('utf-8')).hexdigest() != source['resource_id']
            or len(report.encode('utf-8')) > 2_000_000):
            raise ValueError('source identity')
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise ServiceError(409, 'INVALID_STORED_KNOWLEDGE') from None
    row = db.execute('SELECT payload FROM note_history WHERE resource_id=? AND anchor=? AND revision=?',
                     (source['resource_id'], source['anchor'], source['note_revision'])).fetchone()
    if row is None:
        raise ServiceError(404, 'NOTE_REVISION_NOT_FOUND')
    _stored_note(row[0])
    return dict(source, kind=resource['kind'],
                report_sha256=hashlib.sha256(report.encode('utf-8')).hexdigest(),
                note_sha256=hashlib.sha256(row[0].encode('utf-8')).hexdigest())


def _records(db):
    return [dict(zip(('id', 'version', 'status', 'payload', 'resource_id', 'anchor',
                      'revision', 'parent_version'), tuple(row)))
            for row in db.execute('SELECT id,version,status,payload,resource_id,anchor,revision,parent_version '
                                  'FROM knowledge_rules ORDER BY rowid DESC')]


def validate_knowledge_content(db):
    """Read-only validation of cross-column payloads, exact sources and version chains."""
    try:
        if db.execute('PRAGMA foreign_key_check').fetchone() is not None:
            raise ValueError('foreign keys')
        records = _records(db)
        groups = {}
        for row in records:
            _token(row['id']); _token(row['version'])
            if row['parent_version'] is not None:
                _token(row['parent_version'])
            report = strict_json(row['payload'])
            if (not isinstance(report, dict) or set(report) != _REPORT_FIELDS
                or report['schema_version'] != 'knowledge-proposal.v1'
                or report['rule_id'] != row['id'] or report['version'] != row['version']
                or row['status'] != 'EXPLORATORY' or report['review_state'] != 'EXPLORATORY'
                or report['coaching_enabled'] is not False
                or report['supersedes'] != row['parent_version']
                or len(row['payload'].encode('utf-8')) > 2_000_000):
                raise ValueError('stored payload')
            _rule({key: report[key] for key in RULE_FIELDS})
            binding = _source_binding(db, dict(resource_id=row['resource_id'], anchor=row['anchor'],
                                               note_revision=row['revision']))
            if report['source_refs'] != [binding]:
                raise ValueError('source binding')
            groups.setdefault(row['id'], {})[row['version']] = row['parent_version']
        for versions in groups.values():
            roots = [v for v, p in versions.items() if p is None]
            children = {}
            for version, parent in versions.items():
                if parent is not None:
                    if parent not in versions or parent in children:
                        raise ValueError('branch or parent')
                    children[parent] = version
            if len(roots) != 1:
                raise ValueError('root count')
            visited, version = set(), roots[0]
            while version is not None:
                if version in visited:
                    raise ValueError('cycle')
                visited.add(version)
                version = children.get(version)
            if len(visited) != len(versions):
                raise ValueError('disconnected cycle')
        for row in db.execute('SELECT id,deleted_count FROM knowledge_delete_receipts'):
            _token(row[0])
            if type(row[1]) is not int or row[1] <= 0:
                raise ValueError('receipt count')
    except (ServiceError, ValueError, TypeError, KeyError, UnicodeError, RecursionError, sqlite3.DatabaseError):
        raise ServiceError(409, 'INVALID_STORED_KNOWLEDGE') from None


def _head(db, rule_id):
    row = db.execute('SELECT version FROM knowledge_rules p WHERE id=? AND NOT EXISTS '
                     '(SELECT 1 FROM knowledge_rules c WHERE c.id=p.id AND c.parent_version=p.version)',
                     (rule_id,)).fetchone()
    if row is None:
        raise ServiceError(404, 'KNOWLEDGE_RULE_NOT_FOUND')
    return row[0]


class KnowledgeStore(ResearchStore):
    def __init__(self, dbpath):
        self.dbpath = str(Path(dbpath).resolve())
        self.migration_backup = None
        Path(self.dbpath).parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            version = db.execute('PRAGMA user_version').fetchone()[0]
            if version == SCHEMA_VERSION:
                validate_schema(db)
                _legacy_content(db)
                validate_knowledge_content(db)
                return
            if version not in (0, 1):
                raise ServiceError(409, 'INCOMPATIBLE_KNOWLEDGE_SCHEMA')
            if version == 1:
                _schema(db, 1)
        # The original constructor remains the legacy initialization gate.
        super().__init__(dbpath)
        with self._db() as db:
            _schema(db, 1)
            _legacy_content(db)
            try:
                self.migration_backup = _migration_snapshot(db, self.dbpath)
            except Exception:
                raise ServiceError(503, 'MIGRATION_BACKUP_FAILED') from None
            for sql in KNOWLEDGE_SCHEMAS:
                db.execute(sql)
            db.execute('PRAGMA user_version=2')
            validate_schema(db)
            validate_knowledge_content(db)

    def propose(self, rule, source, rule_id=None, expected_version=None, *, max_bytes):
        _budget(max_bytes)
        rule = _rule(rule)
        if rule_id is None:
            if expected_version is not None:
                raise ServiceError(422, 'INVALID_KNOWLEDGE_ID')
        else:
            _token(rule_id); _token(expected_version)
        with self._db() as db:
            validate_knowledge_content(db)
            if rule_id is not None and _head(db, rule_id) != expected_version:
                raise ServiceError(409, 'REVISION_CONFLICT')
            binding = _source_binding(db, source)
            rid = rule_id if rule_id is not None else uuid.uuid4().hex
            version = uuid.uuid4().hex
            report = dict(rule, schema_version='knowledge-proposal.v1', rule_id=rid, version=version,
                          source_refs=[binding], review_state='EXPLORATORY', supersedes=expected_version,
                          coaching_enabled=False)
            payload = _json(report)
            if len(payload.encode('utf-8')) > 2_000_000:
                raise ServiceError(413, 'REPORT_TOO_LARGE')
            _bounded(report, max_bytes)
            db.execute('INSERT INTO knowledge_rules VALUES (?,?,?,?,?,?,?,?)',
                       (rid, version, 'EXPLORATORY', payload, binding['resource_id'], binding['anchor'],
                        binding['note_revision'], expected_version))
            return report

    def list_proposals(self, max_bytes):
        _budget(max_bytes)
        with self._db() as db:
            validate_knowledge_content(db)
            records = _records(db)
            heads = {row['id']: _head(db, row['id']) for row in records}
            result = []
            for row in records:
                report = strict_json(row['payload'])
                result.append({key: report[key] for key in ('rule_id', 'version', 'claim', 'author',
                                                          'review_state', 'supersedes')})
                result[-1]['current'] = row['version'] == heads[row['id']]
                _bounded(result, max_bytes)
            return _bounded(result, max_bytes)

    def get_proposal(self, rule_id, version=None, *, max_bytes):
        _budget(max_bytes)
        _token(rule_id)
        if version is not None:
            _token(version)
        with self._db() as db:
            validate_knowledge_content(db)
            selected = _head(db, rule_id) if version is None else version
            row = db.execute('SELECT payload FROM knowledge_rules WHERE id=? AND version=?',
                             (rule_id, selected)).fetchone()
            if row is None:
                raise ServiceError(404, 'KNOWLEDGE_RULE_NOT_FOUND')
            return _bounded(strict_json(row[0]), max_bytes)

    @staticmethod
    def _receipt(db, count):
        rid = uuid.uuid4().hex
        db.execute('INSERT INTO knowledge_delete_receipts VALUES (?,?)', (rid, count))
        return dict(status='DELETED', receipt_id=rid, deleted_versions=count)

    def delete_proposal(self, rule_id, expected_version, max_bytes):
        _budget(max_bytes)
        _token(rule_id); _token(expected_version)
        with self._db() as db:
            validate_knowledge_content(db)
            if _head(db, rule_id) != expected_version:
                raise ServiceError(409, 'REVISION_CONFLICT')
            count = db.execute('SELECT COUNT(*) FROM knowledge_rules WHERE id=?', (rule_id,)).fetchone()[0]
            db.execute('DELETE FROM knowledge_rules WHERE id=?', (rule_id,))
            return _bounded(self._receipt(db, count), max_bytes)

    def delete(self, rid):
        with self._db() as db:
            self._resource(db, rid)
            validate_knowledge_content(db)
            before = db.execute('SELECT COUNT(*) FROM knowledge_rules').fetchone()[0]
            db.execute('DELETE FROM resources WHERE id=?', (rid,))
            count = before - db.execute('SELECT COUNT(*) FROM knowledge_rules').fetchone()[0]
            result = dict(id=rid, status='DELETED')
            if count:
                receipt = self._receipt(db, count)
                result.update(receipt_id=receipt['receipt_id'], deleted_versions=count)
            return result

"""Offline, no-overwrite backup/restore of both personal Workbench databases.

This module deliberately does not construct Store/ResearchStore: their startup
behavior can create schemas or recover jobs. All validation is read-only.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack, closing
import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import stat
import sys
import tempfile
import time
import zipfile

FORMAT = 'lol-coach-personal-backup'
VERSION = 1
MAIN = 'workbench.sqlite'
RESEARCH = MAIN + '.research.sqlite'
MANIFEST = 'manifest.json'
CONSISTENCY = 'dual-sqlite-write-exclusion'
MAX_DATABASE_BYTES = 256_000_000
MAX_MANIFEST_BYTES = 16_384
LOCK_TIMEOUT = 0.25
COPY_TIMEOUT = 30
CHUNK_BYTES = 1024 * 1024
SCHEMAS = {
    MAIN: (
        'CREATE TABLE sessions (id TEXT PRIMARY KEY,title TEXT NOT NULL,patch TEXT NOT NULL,mode TEXT NOT NULL,revision INTEGER NOT NULL,status TEXT NOT NULL)',
        'CREATE TABLE cases (session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,revision INTEGER,payload TEXT NOT NULL,PRIMARY KEY(session_id,revision))',
        'CREATE TABLE jobs (id TEXT PRIMARY KEY,session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,input_revision INTEGER NOT NULL,status TEXT NOT NULL,error TEXT,result TEXT)',
        'CREATE TABLE idempotency (session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,operation TEXT,key TEXT,fingerprint TEXT NOT NULL,response TEXT NOT NULL,PRIMARY KEY(session_id,operation,key))',
        'CREATE TABLE tombstones (id TEXT PRIMARY KEY)',
    ),
    RESEARCH: (
        'CREATE TABLE resources (id TEXT PRIMARY KEY,kind TEXT NOT NULL,title TEXT NOT NULL,report TEXT NOT NULL)',
        'CREATE TABLE note_history (resource_id TEXT NOT NULL REFERENCES resources(id) ON DELETE CASCADE,anchor TEXT NOT NULL,revision INTEGER NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(resource_id,anchor,revision))',
    ),
}


class BackupError(Exception):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result

    def bad_constant(value):
        raise ValueError('nonfinite JSON')

    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=bad_constant)
    _json(value).encode('utf-8')  # Also rejects exponent overflow and lone surrogates.
    return value


def _safe_path(value, *, existing_file=False, new=False):
    """Reject observed symlinks, including broken links and ancestor links."""
    if '..' in Path(value).parts:
        raise BackupError('UNSAFE_PATH', 'Parent traversal components are not accepted.')
    path = Path(os.path.abspath(os.fspath(value)))
    for part in reversed((path, *path.parents)):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode):
            raise BackupError('UNSAFE_PATH', 'Symlinks are not accepted in these paths.')
        if part != path and not stat.S_ISDIR(info.st_mode):
            raise BackupError('UNSAFE_PATH', 'A path ancestor is not a directory.')
    if existing_file:
        try:
            info = path.lstat()
        except FileNotFoundError:
            raise BackupError('SOURCE_MISSING', 'Required file does not exist: ' + str(path)) from None
        if not stat.S_ISREG(info.st_mode):
            raise BackupError('UNSAFE_PATH', 'Input must be a regular file.')
    if new and os.path.lexists(path):
        raise BackupError('DESTINATION_EXISTS', 'Destination already exists; choose a new path.')
    if not path.parent.is_dir():
        raise BackupError('PARENT_MISSING', 'Create the destination parent directory first.')
    return path


def _connect(path, *, readonly, immutable=False):
    return sqlite3.connect(path.as_uri() + ('?mode=ro' if readonly else '?mode=rw') + ('&immutable=1' if immutable else ''),
                           uri=True, timeout=LOCK_TIMEOUT)


def _schema_signature(db):
    return db.execute("SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name").fetchall()


def _valid_text(value, maximum=None):
    return isinstance(value, str) and bool(value.strip()) and (maximum is None or len(value) <= maximum)


def _validate_main_content(db):
    # Reuse the existing pinned application contract rather than maintaining a
    # second game-input schema. This is a pure validator, not a Store startup.
    from .models import ReviewInput

    sessions = {row['id']: dict(row) for row in db.execute('SELECT * FROM sessions')}
    for session in sessions.values():
        if (not _valid_text(session['id']) or not _valid_text(session['title'], 200)
            or not _valid_text(session['patch'], 100) or session['mode'] != 'TEST'
            or type(session['revision']) is not int or session['revision'] < 0 or session['status'] != 'ACTIVE'):
            raise ValueError('invalid session')
    cases, revisions = {}, {sid: [] for sid in sessions}
    for row in db.execute('SELECT * FROM cases'):
        sid, revision = row['session_id'], row['revision']
        session = sessions[sid]
        if type(revision) is not int or revision < 1:
            raise ValueError('invalid case revision')
        payload = _strict_json(row['payload'])
        if len(_json(payload).encode('utf-8')) > 1_000_000:
            raise ValueError('case exceeds the stored contract limit')
        case = ReviewInput.model_validate(payload)
        if (case.mode != 'TEST' or case.evidence_kind != 'SYNTHETIC'
            or case.snapshot_request.session_id != sid or case.snapshot_request.patch != session['patch']
            or any(o.patch != session['patch'] for o in case.observations)
            or any(a.patch != session['patch'] for a in case.assessments)):
            raise ValueError('case does not match session')
        cases[sid, revision] = payload
        revisions[sid].append(revision)
    for sid, items in revisions.items():
        if sessions[sid]['revision'] != len(items) or sorted(items) != list(range(1, len(items)+1)):
            raise ValueError('incomplete case revision history')
    jobs = {row['id']: dict(row) for row in db.execute('SELECT * FROM jobs')}
    for job in jobs.values():
        if (not _valid_text(job['id']) or type(job['input_revision']) is not int
            or (job['session_id'], job['input_revision']) not in cases
            or job['status'] not in {'QUEUED', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED'}):
            raise ValueError('invalid job reference or status')
        if job['status'] == 'COMPLETED':
            result = _strict_json(job['result'])
            request = result.get('snapshot', {}).get('request', {})
            if (job['error'] is not None or result.get('schema_version') != 'r3.v1'
                or result.get('mode') != 'TEST' or result.get('evidence_kind') != 'SYNTHETIC'
                or not isinstance(result.get('decision_id'), str) or not re.fullmatch('[a-f0-9]{64}', result['decision_id'])
                or request.get('session_id') != job['session_id'] or request.get('patch') != sessions[job['session_id']]['patch']):
                raise ValueError('invalid saved result')
        elif job['result'] is not None or (job['status'] == 'FAILED' and job['error'] not in {'INTERRUPTED', 'REVIEW_FAILED'}) or (job['status'] != 'FAILED' and job['error'] is not None):
            raise ValueError('invalid job result state')
    for row in db.execute('SELECT * FROM idempotency'):
        sid, operation = row['session_id'], row['operation']
        if not _valid_text(row['key'], 128):
            raise ValueError('invalid idempotency key')
        response = _strict_json(row['response'])
        if operation == 'PUT_CASE':
            revision = response.get('revision')
            if (set(response) != {'session_id', 'revision', 'case'} or response['session_id'] != sid
                or type(revision) is not int or (sid, revision) not in cases or response['case'] != cases[sid, revision]):
                raise ValueError('invalid saved case response')
            fingerprint = hashlib.sha256(_json([revision-1, response['case']]).encode('utf-8')).hexdigest()
        elif operation == 'SUBMIT_REVIEW':
            jid = response.get('id')
            revision = response.get('input_revision')
            if (jid not in jobs or response.get('session_id') != sid or jobs[jid]['session_id'] != sid
                or type(revision) is not int or jobs[jid]['input_revision'] != revision):
                raise ValueError('invalid saved job response')
            fingerprint = hashlib.sha256(_json(revision).encode('utf-8')).hexdigest()
        else:
            raise ValueError('invalid idempotency operation')
        if row['fingerprint'] != fingerprint:
            raise ValueError('invalid idempotency fingerprint')
    for row in db.execute('SELECT id FROM tombstones'):
        if not _valid_text(row['id']) or row['id'] in sessions:
            raise ValueError('invalid session tombstone')


def _validate_research_content(db):
    resources = {}
    for row in db.execute('SELECT * FROM resources'):
        report = _strict_json(row['report'])
        if len(_json(report).encode('utf-8')) > 2_000_000:
            raise ValueError('report exceeds the stored contract limit')
        if not _valid_text(row['title'], 200) or not isinstance(row['kind'], str) or not re.fullmatch('[A-Z][A-Z0-9_]{0,31}', row['kind']):
            raise ValueError('invalid resource metadata')
        # ResearchStore already stores the canonical nested report substring.
        # Decoding numeric dictionary keys converts them to strings and can
        # change sort order; hashing the stored substring preserves that
        # existing accepted writer contract without rewriting report bytes.
        canonical = '{"kind":' + _json(row['kind']) + ',"report":' + row['report'] + '}'
        rid = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
        if row['id'] != rid:
            raise ValueError('invalid resource identity')
        resources[rid] = dict(kind=row['kind'], report=report)
    histories = {}
    fields = {'known', 'intention', 'alternative', 'outcome'}
    for row in db.execute('SELECT * FROM note_history'):
        resource = resources[row['resource_id']]
        anchor, revision, note = row['anchor'], row['revision'], _strict_json(row['payload'])
        if (type(revision) is not int or revision < 1 or set(note) != fields
            or any(not isinstance(value, str) or len(value) > 2000 for value in note.values())):
            raise ValueError('invalid note revision or fields')
        if anchor != 'overview':
            candidates = resource['report'].get('candidates', [])
            if (not isinstance(anchor, str) or len(anchor) > 32 or resource['kind'] != 'VIDEO'
                or not isinstance(candidates, list) or not any(isinstance(candidate, dict)
                    and type(candidate.get('cue_index')) is int and candidate['cue_index'] >= 0
                    and str(candidate['cue_index']) == anchor for candidate in candidates)):
                raise ValueError('invalid note anchor')
        histories.setdefault((row['resource_id'], anchor), []).append(revision)
    for revisions in histories.values():
        if sorted(revisions) != list(range(1, len(revisions)+1)):
            raise ValueError('incomplete note revision history')


def _validate_database(path, member):
    # Keep dependency loading inside the operation so the CLI can still report
    # its existing DEPENDENCY_MISSING error instead of failing during import.
    from .storage import ServiceError

    try:
        # Private complete SQLite snapshots have no WAL dependencies. Immutable
        # validation avoids creating bookkeeping files alongside restored DBs.
        with closing(_connect(path, readonly=True, immutable=True)) as db, closing(sqlite3.connect(':memory:')) as expected:
            version = db.execute('PRAGMA user_version').fetchone()[0]
            supported = (1, 2)
            if type(version) is not int or version not in supported:
                raise BackupError('INCOMPATIBLE_SCHEMA', 'Unsupported database schema version: ' + member)
            schemas = SCHEMAS[member]
            if member == MAIN and version == 2:
                from .draft import DRAFT_SCHEMAS, validate_schema as validate_draft_schema, validate_draft_content
                schemas += DRAFT_SCHEMAS
            if member == RESEARCH and version == 2:
                from .knowledge import KNOWLEDGE_SCHEMAS, validate_schema, validate_knowledge_content
                schemas += KNOWLEDGE_SCHEMAS
            for sql in schemas:
                expected.execute(sql)
            if _schema_signature(db) != _schema_signature(expected):
                raise BackupError('INCOMPATIBLE_SCHEMA', 'Database schema, constraints or objects differ: ' + member)
            if member == MAIN and version == 2:
                try:
                    validate_draft_schema(db)
                except ServiceError:
                    raise BackupError('INCOMPATIBLE_SCHEMA', 'Draft schema, constraints or objects differ: ' + member) from None
            if member == RESEARCH and version == 2:
                try:
                    validate_schema(db)
                except ServiceError:
                    raise BackupError('INCOMPATIBLE_SCHEMA', 'Knowledge schema, constraints or objects differ: ' + member) from None
            if db.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
                raise BackupError('DATABASE_INVALID', 'SQLite integrity check failed: ' + member)
            if db.execute('PRAGMA foreign_key_check').fetchall():
                raise BackupError('DATABASE_INVALID', 'Foreign-key check failed: ' + member)
            json_columns = (('cases', 'payload'), ('jobs', 'result'), ('idempotency', 'response')) if member == MAIN else (('resources', 'report'), ('note_history', 'payload'))
            if member == MAIN and version == 2:
                json_columns += (('draft_snapshots', 'payload'),)
            for table, column in json_columns:
                for (raw,) in db.execute('SELECT ' + column + ' FROM ' + table + ' WHERE ' + column + ' IS NOT NULL'):
                    if not isinstance(raw, str) or not isinstance(_strict_json(raw), dict):
                        raise ValueError('stored payload must be a JSON object')
            db.row_factory = sqlite3.Row
            (_validate_main_content if member == MAIN else _validate_research_content)(db)
            if member == MAIN and version == 2:
                validate_draft_content(db)
            if member == RESEARCH and version == 2:
                validate_knowledge_content(db)
            return version
    except BackupError:
        raise
    except (sqlite3.DatabaseError, ServiceError, ValueError, TypeError, KeyError, AttributeError, UnicodeError, RecursionError):
        raise BackupError('DATABASE_INVALID', 'Database content validation failed: ' + member) from None


def _file_metadata(path):
    size, digest = 0, hashlib.sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(CHUNK_BYTES):
            size += len(chunk)
            if size > MAX_DATABASE_BYTES:
                raise BackupError('DATABASE_TOO_LARGE', 'Database exceeds the supported backup size limit.')
            digest.update(chunk)
    # Only inspect the completed private snapshot. A constructor could migrate
    # schemas or recover jobs and would no longer describe the copied bytes.
    with closing(_connect(path, readonly=True, immutable=True)) as db:
        version = db.execute('PRAGMA user_version').fetchone()[0]
    return dict(schema_version=version, size=size, sha256=digest.hexdigest())


def _copy_database(reader, target):
    # Do not call backup() on a connection owning BEGIN IMMEDIATE: SQLite can
    # wait indefinitely on its own write transaction. The reserved connection
    # is separate; this reader can read the committed state under its lock.
    deadline = time.monotonic() + COPY_TIMEOUT

    def progress(status, remaining, total):
        if time.monotonic() > deadline:
            raise BackupError('COPY_TIMEOUT', 'SQLite copy did not finish within its time limit; nothing was published.')

    with closing(sqlite3.connect(target)) as copy:
        reader.backup(copy, pages=128, progress=progress, sleep=0.01)
        # The new standalone snapshot must not depend on WAL siblings when the
        # Workbench later opens it. Only this disposable copy is normalized.
        if copy.execute('PRAGMA journal_mode=DELETE').fetchone() != ('delete',):
            raise BackupError('DATABASE_INVALID', 'Cannot make a standalone SQLite snapshot.')


def backup(db_path, output):
    main = _safe_path(db_path, existing_file=True)
    research_path = Path(str(main) + '.research.sqlite')
    try:
        research = _safe_path(research_path, existing_file=True)
    except BackupError as error:
        if error.code == 'SOURCE_MISSING':
            raise BackupError('RESEARCH_MISSING', 'Research database is missing; a complete backup requires both existing databases.') from None
        raise
    if os.path.samefile(main, research):
        raise BackupError('PATH_COLLISION', 'Main and research databases must be different files.')
    target = _safe_path(output, new=True)
    reserved = {main, research}
    for source in (main, research):
        reserved.update(Path(str(source) + suffix) for suffix in ('-wal', '-shm', '-journal', '.lock'))
    if os.path.normcase(str(target)) in {os.path.normcase(str(path)) for path in reserved}:
        raise BackupError('PATH_COLLISION', 'Backup destination collides with a database or its bookkeeping files.')
    identities = [(p.stat().st_dev, p.stat().st_ino) for p in (main, research)]
    with tempfile.TemporaryDirectory(prefix='.coach-backup-', dir=target.parent) as staging:
        stage = Path(staging)
        with ExitStack() as stack:
            readers = []
            # Pin read transactions before opening writable guard connections.
            # Hot-journal recovery cannot write through a held read lock. Keep
            # readers alive until guards close, also avoiding a last-writable-
            # connection WAL checkpoint performed by the backup's guards.
            for source in (main, research):
                reader = stack.enter_context(closing(_connect(source, readonly=True)))
                try:
                    reader.execute('BEGIN')
                    reader.execute('SELECT count(*) FROM sqlite_master').fetchone()
                except sqlite3.OperationalError:
                    raise BackupError('SOURCE_BUSY', 'Cannot read a source safely; stop the workbench and resolve SQLite recovery before retrying.') from None
                except sqlite3.DatabaseError:
                    raise BackupError('DATABASE_INVALID', 'A required source is not a readable SQLite database.') from None
                readers.append(reader)
            # Holding both reserved locks excludes writers across both copies.
            # No schema creation, startup recovery or row writes occur here.
            for source in (main, research):
                connection = stack.enter_context(closing(_connect(source, readonly=False)))
                stack.callback(connection.rollback)
                try:
                    connection.execute('BEGIN IMMEDIATE')
                except sqlite3.OperationalError as error:
                    if getattr(error, 'sqlite_errorcode', None) in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED):
                        raise BackupError('SOURCE_BUSY', 'A database writer is active; stop the workbench and retry.') from None
                    raise BackupError('SOURCE_OPEN_FAILED', 'Cannot reserve both existing databases for backup.') from None
            for reader in readers:
                # Refresh any WAL snapshot taken before both guards were held.
                reader.rollback()
                reader.execute('BEGIN')
                reader.execute('SELECT count(*) FROM sqlite_master').fetchone()
                if reader.execute('PRAGMA page_count').fetchone()[0] * reader.execute('PRAGMA page_size').fetchone()[0] > MAX_DATABASE_BYTES:
                    raise BackupError('DATABASE_TOO_LARGE', 'Database exceeds the supported backup size limit.')
            for i, source in enumerate((main, research)):
                _safe_path(source, existing_file=True)
                if (source.stat().st_dev, source.stat().st_ino) != identities[i]:
                    raise BackupError('SOURCE_CHANGED', 'A source file changed during backup setup.')
            for reader, member in zip(readers, (MAIN, RESEARCH)):
                _copy_database(reader, stage / member)
        files = {}
        for member in (MAIN, RESEARCH):
            _validate_database(stage / member, member)
            files[member] = _file_metadata(stage / member)
        manifest = dict(format=FORMAT, version=VERSION, consistency=CONSISTENCY, files=files)
        archive_path = stage / 'archive.zip'
        with zipfile.ZipFile(archive_path, 'x', compression=zipfile.ZIP_STORED) as archive:
            archive.writestr(MANIFEST, _json(manifest).encode('utf-8'))
            for member in (MAIN, RESEARCH):
                archive.write(stage / member, member)
        os.chmod(archive_path, 0o600)
        with archive_path.open('rb') as stream:
            os.fsync(stream.fileno())
        _safe_path(target, new=True)
        try:
            os.link(archive_path, target)
        except FileExistsError:
            raise BackupError('DESTINATION_EXISTS', 'Destination appeared during publication; nothing was overwritten.') from None
    return dict(archive=str(target), format=FORMAT, version=VERSION, files=files)


def _read_manifest(archive):
    entries = archive.infolist()
    names = [entry.filename for entry in entries]
    if len(names) != 3 or len(set(names)) != 3 or set(names) != {MANIFEST, MAIN, RESEARCH}:
        raise BackupError('ARCHIVE_MEMBERS_INVALID', 'Archive must contain exactly one manifest and both databases; no extra paths are accepted.')
    for entry in entries:
        mode = entry.external_attr >> 16
        if entry.orig_filename != entry.filename or entry.is_dir() or (stat.S_IFMT(mode) not in (0, stat.S_IFREG)) or entry.flag_bits & ~0x800 or entry.compress_type != zipfile.ZIP_STORED:
            raise BackupError('ARCHIVE_MEMBERS_INVALID', 'Unsupported archive member type or encoding.')
        maximum = MAX_MANIFEST_BYTES if entry.filename == MANIFEST else MAX_DATABASE_BYTES
        if not 0 < entry.file_size <= maximum:
            raise BackupError('ARCHIVE_SIZE_INVALID', 'Archive member has an unsupported size.')
    try:
        manifest = _strict_json(archive.read(MANIFEST).decode('utf-8'))
        if not isinstance(manifest, dict) or set(manifest) != {'format', 'version', 'consistency', 'files'}:
            raise ValueError('manifest fields')
        if manifest['format'] != FORMAT or type(manifest['version']) is not int or manifest['version'] != VERSION or manifest['consistency'] != CONSISTENCY:
            raise ValueError('manifest format or version')
        if not isinstance(manifest['files'], dict) or set(manifest['files']) != {MAIN, RESEARCH}:
            raise ValueError('manifest file list')
        for member, metadata in manifest['files'].items():
            if not isinstance(metadata, dict) or set(metadata) != {'schema_version', 'size', 'sha256'}:
                raise ValueError('file metadata')
            supported = (1, 2)
            if type(metadata['schema_version']) is not int or metadata['schema_version'] not in supported or type(metadata['size']) is not int or metadata['size'] != archive.getinfo(member).file_size:
                raise ValueError('schema or size')
            if not isinstance(metadata['sha256'], str) or not re.fullmatch('[a-f0-9]{64}', metadata['sha256']):
                raise ValueError('digest')
        return manifest
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise BackupError('MANIFEST_INVALID', 'Manifest fields, version, sizes or hashes are invalid.') from None


def _publish_directory(stage, destination):
    """Atomic no-replace directory rename; fail closed on unsupported hosts."""
    if os.name == 'nt':
        # Windows rename refuses every existing destination, including empty
        # directories. POSIX rename does not offer that same guarantee.
        os.rename(stage, destination)
        return
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform.startswith('linux') and hasattr(libc, 'renameat2'):
        call = libc.renameat2
        call.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        call.restype = ctypes.c_int
        result = call(-100, os.fsencode(stage), -100, os.fsencode(destination), 1)  # RENAME_NOREPLACE
    elif sys.platform == 'darwin' and hasattr(libc, 'renamex_np'):
        call = libc.renamex_np
        call.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        call.restype = ctypes.c_int
        result = call(os.fsencode(stage), os.fsencode(destination), 4)  # RENAME_EXCL
    else:
        raise BackupError('ATOMIC_RESTORE_UNSUPPORTED', 'This host lacks a supported atomic no-overwrite directory rename.')
    if result:
        code = ctypes.get_errno()
        if code == errno.EEXIST:
            raise FileExistsError(code, os.strerror(code), str(destination))
        if code in (errno.ENOSYS, errno.EINVAL, errno.ENOTSUP):
            raise BackupError('ATOMIC_RESTORE_UNSUPPORTED', 'This filesystem lacks atomic no-overwrite directory rename.')
        raise OSError(code, os.strerror(code), str(destination))


def restore(archive_path, destination):
    source = _safe_path(archive_path, existing_file=True)
    target = _safe_path(destination, new=True)
    if source.stat().st_size > 2 * MAX_DATABASE_BYTES + MAX_MANIFEST_BYTES + 1_000_000:
        raise BackupError('ARCHIVE_SIZE_INVALID', 'Archive exceeds the supported size limit.')
    stage = Path(tempfile.mkdtemp(prefix='.coach-restore-', dir=target.parent))
    try:
        with zipfile.ZipFile(source, 'r') as archive:
            manifest = _read_manifest(archive)
            for member in (MAIN, RESEARCH):
                metadata = manifest['files'][member]
                size, digest = 0, hashlib.sha256()
                with archive.open(member) as incoming, (stage / member).open('xb') as outgoing:
                    os.chmod(stage / member, 0o600)
                    while chunk := incoming.read(CHUNK_BYTES):
                        size += len(chunk)
                        if size > metadata['size']:
                            raise BackupError('HASH_MISMATCH', 'Database member exceeds its declared size.')
                        digest.update(chunk)
                        outgoing.write(chunk)
                    outgoing.flush()
                    os.fsync(outgoing.fileno())
                if size != metadata['size'] or digest.hexdigest() != metadata['sha256']:
                    raise BackupError('HASH_MISMATCH', 'Database bytes do not match the manifest: ' + member)
                actual_version = _validate_database(stage / member, member)
                if actual_version != metadata['schema_version']:
                    code = 'MANIFEST_INVALID' if member == MAIN else 'SCHEMA_VERSION_MISMATCH'
                    raise BackupError(code, 'Database schema version does not match the manifest: ' + member)
        _safe_path(target, new=True)
        try:
            _publish_directory(stage, target)
        except FileExistsError:
            raise BackupError('DESTINATION_EXISTS', 'Destination appeared during publication; nothing was overwritten.') from None
    except (zipfile.BadZipFile, zipfile.LargeZipFile, EOFError, NotImplementedError, UnicodeError):
        raise BackupError('ARCHIVE_INVALID', 'Archive structure or CRC is invalid.') from None
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return dict(directory=str(target), db=str(target / MAIN), research_db=str(target / RESEARCH), version=VERSION)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Complete local personal-data backup and restore; never overwrites destinations.')
    commands = parser.add_subparsers(dest='command', required=True)
    save = commands.add_parser('backup', help='Back up both existing databases to a new archive.')
    save.add_argument('--db', required=True, type=Path)
    save.add_argument('--output', required=True, type=Path)
    recover = commands.add_parser('restore', help='Restore a validated archive into a new directory.')
    recover.add_argument('--archive', required=True, type=Path)
    recover.add_argument('--destination', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = backup(args.db, args.output) if args.command == 'backup' else restore(args.archive, args.destination)
    except BackupError as error:
        print(_json(dict(error_code=error.code, message=str(error))), file=sys.stderr)
        return 1
    except (OSError, sqlite3.Error):
        print(_json(dict(error_code='IO_ERROR', message='The operation could not complete; originals were not overwritten.')), file=sys.stderr)
        return 1
    except ImportError:
        print(_json(dict(error_code='DEPENDENCY_MISSING', message='Install the existing application requirements-r3.txt dependencies before backing up or restoring.')), file=sys.stderr)
        return 1
    print(_json(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

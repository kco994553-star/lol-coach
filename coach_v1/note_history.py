"""Read existing Research note revisions without changing storage or latest notes.

The caller supplies the existing HTTP response byte budget. No author/time or
missing revision is inferred, and preview values never become game evidence.
"""
import json
import re

from coach_intake.io import strict_json
from .research import FIELDS
from .storage import ServiceError


# SQLite INTEGER's representable range, not a game rule or new operational cap.
_SQLITE_MAX_REVISION = '9223372036854775807'


def _budget(max_bytes):
    if type(max_bytes) is not int or max_bytes <= 0:
        raise ServiceError(422, 'INVALID_NOTE_HISTORY_LIMIT')


def _encoded_size(value):
    # Matches Handler.reply's existing JSON encoding and whitespace.
    return len(json.dumps(value, ensure_ascii=False, allow_nan=False).encode('utf-8'))


def _bounded(value, max_bytes):
    if _encoded_size(value) > max_bytes:
        raise ServiceError(413, 'NOTE_HISTORY_TOO_LARGE')
    return value


def _stored_revision(value):
    if type(value) is not int or value <= 0 or value > int(_SQLITE_MAX_REVISION):
        raise ServiceError(409, 'INVALID_STORED_NOTE')
    return value


def _revision(value):
    if not isinstance(value, str) or not re.fullmatch(r'[1-9][0-9]*', value):
        raise ServiceError(422, 'INVALID_NOTE_REVISION')
    # Compare decimal text before int() to avoid Python's input digit limit and
    # SQLite binding overflow on valid-looking but unrepresentable revisions.
    if len(value) > len(_SQLITE_MAX_REVISION) or (
        len(value) == len(_SQLITE_MAX_REVISION) and value > _SQLITE_MAX_REVISION
    ):
        raise ServiceError(404, 'NOTE_REVISION_NOT_FOUND')
    return int(value)


def _stored_note(payload):
    try:
        note = strict_json(payload)
        if (not isinstance(note, dict) or set(note) != set(FIELDS)
            or any(not isinstance(note[field], str) or len(note[field]) > 2000 for field in FIELDS)):
            raise ValueError('invalid stored note')
        for field in FIELDS:
            note[field].encode('utf-8')
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise ServiceError(409, 'INVALID_STORED_NOTE') from None
    return {field: note[field] for field in FIELDS}


def note_history(store, rid, anchor, max_bytes):
    """List actual saved revision IDs, descending, inside one existing transaction."""
    _budget(max_bytes)
    with store._db() as db:
        store._anchor(store._resource(db, rid), anchor)
        summary = db.execute(
            'SELECT COUNT(*) AS count,MAX(revision) AS latest FROM note_history '
            'WHERE resource_id=? AND anchor=?', (rid, anchor)
        ).fetchone()
        count = summary['count']
        current = _stored_revision(summary['latest']) if count else 0
        result = dict(resource_id=rid, anchor=anchor, current_revision=current,
                      revision_count=count, revisions=[], read_only=True)
        size = _encoded_size(result)
        if size > max_bytes:
            raise ServiceError(413, 'NOTE_HISTORY_TOO_LARGE')
        # Stream only revision metadata. Accumulate the exact default JSON list
        # width so an oversized index fails without materializing an unbounded
        # list or silently omitting older IDs. Payload validation belongs to the
        # exact preview, which reads that one immutable stored row.
        for row in db.execute(
            'SELECT revision FROM note_history WHERE resource_id=? AND anchor=? '
            'ORDER BY revision DESC', (rid, anchor)
        ):
            revision = _stored_revision(row['revision'])
            size += len(str(revision)) + (2 if result['revisions'] else 0)
            if size > max_bytes:
                raise ServiceError(413, 'NOTE_HISTORY_TOO_LARGE')
            result['revisions'].append(revision)
        return result


def note_revision(store, rid, anchor, revision, max_bytes):
    """Read one exact saved payload; no latest-note or draft mutation occurs."""
    _budget(max_bytes)
    selected = _revision(revision)
    with store._db() as db:
        store._anchor(store._resource(db, rid), anchor)
        row = db.execute(
            'SELECT revision,payload FROM note_history WHERE resource_id=? AND anchor=? AND revision=?',
            (rid, anchor, selected)
        ).fetchone()
        if row is None:
            raise ServiceError(404, 'NOTE_REVISION_NOT_FOUND')
        current = db.execute(
            'SELECT MAX(revision) FROM note_history WHERE resource_id=? AND anchor=?',
            (rid, anchor)
        ).fetchone()[0]
        return _bounded(dict(resource_id=rid, anchor=anchor, revision=_stored_revision(row['revision']),
                             current_revision=_stored_revision(current), note=_stored_note(row['payload']),
                             read_only=True), max_bytes)

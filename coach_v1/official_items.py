"""Bounded official Korean item archive; explicit refresh and offline reads only.

This provides source facts, never purchase recommendations or USER approvals.
Version archives are immutable; only the current pointer/status are replaced.
"""
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import shutil
import tempfile
import time
import urllib.request

from .official_catalog import _atomic_json, _json, _read, _sha, _NoRedirect

CATALOG_ROOT = Path(__file__).resolve().parents[1] / 'data/official_items'
ORIGIN = 'https://ddragon.leagueoflegends.com'
VERSIONS_URL = ORIGIN + '/api/versions.json'
MAX_SOURCE = 5_000_000
MAX_VERSIONS = 200_000
MAX_ITEMS = 5000
TIMEOUT = 12
VERSION = re.compile(r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}')
PATCH = re.compile(r'([0-9]{1,3}\.[0-9]{1,3})(?:\.[0-9]{1,10}){0,2}')
ITEM_ID = re.compile(r'[0-9]{1,10}')
SHA256 = re.compile(r'[a-f0-9]{64}')


def _source_url(version):
    return f'{ORIGIN}/cdn/{version}/data/ko_KR/item.json'


def _fetch(url, limit, timeout):
    if url != VERSIONS_URL and not re.fullmatch(re.escape(ORIGIN) + r'/cdn/[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}/data/ko_KR/item\.json', url):
        raise ValueError('unapproved official URL')
    req = urllib.request.Request(url, headers={'User-Agent': 'lol-coach-official-items/2.3'})
    with urllib.request.build_opener(_NoRedirect()).open(req, timeout=timeout) as response:
        if response.status != 200 or response.geturl() != url:
            raise ValueError('official HTTP response')
        raw = response.read(limit + 1)
    _json(raw, limit)
    return raw


def _versions(raw):
    versions = _json(raw, MAX_VERSIONS)
    if (not isinstance(versions, list) or not 1 <= len(versions) <= 10000
            or any(not isinstance(v, str) or not 1 <= len(v) <= 100 for v in versions)
            or not VERSION.fullmatch(versions[0])):
        raise ValueError('version discovery schema')
    return versions


def _items(raw, version):
    doc = _json(raw, MAX_SOURCE)
    if not isinstance(doc, dict) or doc.get('type') != 'item' or doc.get('version') != version:
        raise ValueError('item version')
    rows = doc.get('data')
    if not isinstance(rows, dict) or not 1 <= len(rows) <= MAX_ITEMS:
        raise ValueError('item count')
    result = []
    for identity, item in rows.items():
        if not ITEM_ID.fullmatch(identity) or not isinstance(item, dict):
            raise ValueError('item identity')
        name, description = item.get('name'), item.get('description')
        if (not isinstance(name, str) or not 0 <= len(name) <= 300
                or not isinstance(description, str) or len(description) > 50_000):
            raise ValueError('item text')
        gold = item.get('gold')
        if (not isinstance(gold, dict) or type(gold.get('total')) is not int
                or not 0 <= gold['total'] <= 1_000_000 or type(gold.get('purchasable')) is not bool):
            raise ValueError('item gold')
        components = item.get('from', [])
        if (not isinstance(components, list) or len(components) > 30
                or any(not isinstance(c, str) or not ITEM_ID.fullmatch(c) for c in components)):
            raise ValueError('item components')
        maps = item.get('maps')
        if (not isinstance(maps, dict) or not 1 <= len(maps) <= 30
                or any(not ITEM_ID.fullmatch(k) or type(v) is not bool for k, v in maps.items())):
            raise ValueError('item maps')
        for field in ('requiredAlly', 'requiredChampion'):
            if field in item and (not isinstance(item[field], str) or len(item[field]) > 100):
                raise ValueError('item requirement')
        if 'inStore' in item and type(item['inStore']) is not bool:
            raise ValueError('item store')
        result.append(dict(id=identity, name=name, gold=dict(total=gold['total']),
                           **{'from': components}, maps=maps,
                           in_store=gold['purchasable'] and item.get('inStore', True),
                           required_ally=item.get('requiredAlly'), required_champion=item.get('requiredChampion')))
    return result


def _safe_root():
    if CATALOG_ROOT.is_symlink() or (CATALOG_ROOT / 'versions').is_symlink():
        raise ValueError('archive directory')


def _verified(folder, record, filename, url, limit):
    if (not isinstance(record, dict) or record.get('file') != filename or record.get('url') != url
            or not isinstance(record.get('sha256'), str) or not SHA256.fullmatch(record['sha256'])):
        raise ValueError('source origin or hash')
    raw = _read(folder / filename, limit)
    if _sha(raw) != record['sha256']:
        raise ValueError('source integrity')
    return raw


def _load_archive(version, digest=None):
    _safe_root()
    if not isinstance(version, str) or not VERSION.fullmatch(version):
        raise ValueError('archive version')
    folder = CATALOG_ROOT / 'versions' / version
    if folder.is_symlink():
        raise ValueError('archive directory')
    raw = _read(folder / 'manifest.json', 12000)
    if digest is not None and _sha(raw) != digest:
        raise ValueError('manifest integrity')
    m = _json(raw, 12000)
    if (not isinstance(m, dict) or m.get('schema_version') != 'official-items.archive.v1'
            or m.get('version') != version or m.get('locale') != 'ko_KR'
            or m.get('game_patch') != '.'.join(version.split('.')[:2])
            or not isinstance(m.get('retrieved_at'), str) or len(m['retrieved_at']) > 100):
        raise ValueError('archive manifest')
    if _versions(_verified(folder, m.get('discovery'), 'versions.json', VERSIONS_URL, MAX_VERSIONS))[0] != version:
        raise ValueError('discovery version')
    rows = _items(_verified(folder, m.get('source'), 'item.ko_KR.json', _source_url(version), MAX_SOURCE), version)
    if m.get('item_count') != len(rows):
        raise ValueError('manifest item count')
    return m, rows, _sha(raw)


def _current():
    _safe_root()
    p = _json(_read(CATALOG_ROOT / 'current.json', 2000), 2000)
    if (not isinstance(p, dict) or p.get('schema_version') != 'official-items.current.v1'
            or not isinstance(p.get('manifest_sha256'), str) or not SHA256.fullmatch(p['manifest_sha256'])):
        raise ValueError('current pointer')
    return _load_archive(p.get('version'), p['manifest_sha256'])


def _status(state, **extra):
    return dict(schema_version='official-items.refresh.v1', state=state,
                checked_at=datetime.now(timezone.utc).isoformat(), checked_at_epoch=time.time(), **extra)


def _fallback(reason):
    try:
        m, rows, _ = _current()
        return _status('OFFLINE_FALLBACK', catalog_version=m['version'], item_count=len(rows), reason=reason)
    except (OSError, ValueError, KeyError, TypeError):
        return _status('UNAVAILABLE', reason=reason)


def _acquire_refresh_lock():
    _safe_root()
    path = CATALOG_ROOT / '.refresh-lock'
    if path.is_symlink():
        raise ValueError('refresh lock path')
    fd = os.open(path, os.O_RDWR | os.O_CREAT | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    stream = os.fdopen(fd, 'r+b')
    try:
        if os.name == 'nt':
            import msvcrt
            if os.fstat(fd).st_size == 0:
                stream.write(b' '); stream.flush()
            stream.seek(0); msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        stream.close()
        return None
    return stream


def _release_refresh_lock(stream):
    try:
        if os.name == 'nt':
            import msvcrt
            stream.seek(0); msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
    finally:
        stream.close()


def _update(fetch):
    stage = None
    try:
        _safe_root()
        CATALOG_ROOT.mkdir(parents=True, exist_ok=True)
        lock = _acquire_refresh_lock()
    except (OSError, ValueError):
        return _fallback('REFRESH_LOCK_UNAVAILABLE')
    if lock is None:
        return _fallback('REFRESH_IN_PROGRESS')
    try:
        discovery = fetch(VERSIONS_URL, MAX_VERSIONS, TIMEOUT)
        version = _versions(discovery)[0]
        destination = CATALOG_ROOT / 'versions' / version
        if destination.exists():
            m, rows, digest = _load_archive(version)
            state = 'UNCHANGED'
        else:
            content = fetch(_source_url(version), MAX_SOURCE, TIMEOUT)
            rows = _items(content, version)
            (CATALOG_ROOT / 'versions').mkdir(exist_ok=True)
            _safe_root()
            stage = Path(tempfile.mkdtemp(prefix='.collect-', dir=CATALOG_ROOT / 'versions'))
            (stage / 'versions.json').write_bytes(discovery)
            (stage / 'item.ko_KR.json').write_bytes(content)
            m = dict(schema_version='official-items.archive.v1', version=version,
                     game_patch='.'.join(version.split('.')[:2]), locale='ko_KR',
                     retrieved_at=datetime.now(timezone.utc).isoformat(), item_count=len(rows),
                     discovery=dict(file='versions.json', url=VERSIONS_URL, sha256=_sha(discovery)),
                     source=dict(file='item.ko_KR.json', url=_source_url(version), sha256=_sha(content)))
            _atomic_json(stage / 'manifest.json', m)
            digest = _sha((stage / 'manifest.json').read_bytes())
            os.rename(stage, destination); stage = None
            _load_archive(version, digest)
            state = 'UPDATED'
        _atomic_json(CATALOG_ROOT / 'current.json', dict(schema_version='official-items.current.v1', version=version, manifest_sha256=digest))
        result = _status(state, catalog_version=version, item_count=len(rows))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result = _fallback(type(exc).__name__ + ': ' + str(exc)[:200])
    finally:
        if stage is not None:
            shutil.rmtree(stage, ignore_errors=True)
        _release_refresh_lock(lock)
    _atomic_json(CATALOG_ROOT / 'refresh-status.json', result)
    return result


def refresh_if_due(*, max_age_seconds=86400, force=False, fetch=None):
    """Refresh on launch at most daily, retry failed checks after at most one hour.

    Optional transport: ``fetch(official_url, byte_limit, timeout_seconds)->bytes``.
    No completed champion catalog refresh or verification is performed here.
    """
    if (type(max_age_seconds) not in (int, float) or not math.isfinite(max_age_seconds)
            or not 0 <= max_age_seconds <= 31_536_000):
        raise ValueError('refresh age')
    if not force:
        try:
            status = _json(_read(CATALOG_ROOT / 'refresh-status.json', 4000), 4000)
            age = time.time() - status['checked_at_epoch']
            failed = status['state'] in ('OFFLINE_FALLBACK', 'UNAVAILABLE')
            if 0 <= age < (min(max_age_seconds, 3600) if failed else max_age_seconds):
                if failed:
                    return dict(_fallback(status.get('reason', 'LAST_REFRESH_FAILED')),
                                checked_at=status['checked_at'], checked_at_epoch=status['checked_at_epoch'])
                m, rows, _ = _current()
                return dict(status, state='FRESH', catalog_version=m['version'], item_count=len(rows))
        except (OSError, ValueError, KeyError, TypeError):
            pass
    return _update(fetch or _fetch)


def items_response(patch=None):
    """Read verified archived facts. Suppress prices unless the game patch matches.

    Match-V5 full game versions and Data Dragon versions compare major.minor.
    ``gold.total`` is full catalog cost, not remaining cost after parts/discounts.
    ``maps`` and store/champion/ally requirements must be checked by consumers.
    """
    result = dict(schema_version='official-items.v1', status='UNAVAILABLE', requested_patch=patch,
                  catalog_version=None, catalog_patch=None, patch_match=False, prices_usable=False,
                  patch_status='CATALOG_UNAVAILABLE', source=None, items=[], warnings=[],
                  reference_only=True, approval_required=False,
                  price_basis='FULL_ITEM_TOTAL_NOT_REMAINING_PURCHASE_COST')
    try:
        m, rows, _ = _current()
    except (OSError, ValueError, KeyError, TypeError):
        result['warnings'] = ['OFFICIAL_ITEM_SOURCE_UNAVAILABLE_OR_INVALID']
        return result
    parsed = PATCH.fullmatch(patch) if isinstance(patch, str) else None
    patch_status = ('GAME_PATCH_UNKNOWN' if patch is None else 'GAME_PATCH_INVALID' if parsed is None
                    else 'MATCHING_ARCHIVE' if parsed.group(1) == m['game_patch'] else 'GAME_PATCH_MISMATCH')
    matching = patch_status == 'MATCHING_ARCHIVE'
    result.update(status='AVAILABLE', catalog_version=m['version'], catalog_patch=m['game_patch'],
                  patch_match=matching, prices_usable=matching, patch_status=patch_status,
                  source=dict(url=m['source']['url'], version=m['version'], sha256=m['source']['sha256'],
                              archive_path=f'data/official_items/versions/{m["version"]}/item.ko_KR.json',
                              retrieved_at=m['retrieved_at']),
                  items=rows if matching else [], warnings=[] if matching else [patch_status])
    try:
        s = _json(_read(CATALOG_ROOT / 'refresh-status.json', 4000), 4000)
        result['refresh_status'] = {k:s[k] for k in ('state','checked_at','reason') if k in s}
    except (OSError, ValueError, KeyError, TypeError):
        result['refresh_status'] = dict(state='UNKNOWN')
    return result

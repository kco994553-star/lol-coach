"""Versioned, complete Korean Data Dragon facts; network only on explicit refresh.

This module neither changes the frozen official_reference archive nor records
USER decisions. Publication occurs only after every roster member validates.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import tempfile
import time
import urllib.request

from .official_reference import _plain

ROOT = Path(__file__).resolve().parents[1]
CATALOG_ROOT = ROOT / 'data/official_catalog'
LEGACY_ROOT = ROOT / 'data/official_reference/2026-10-14'
ORIGIN = 'https://ddragon.leagueoflegends.com'
VERSIONS_URL = ORIGIN + '/api/versions.json'
MAX_CHAMPIONS = 300
MAX_SOURCE = 2_000_000
MAX_ROSTER = 5_000_000
MAX_VERSIONS = 200_000
MAX_MANIFEST = 500_000
TIMEOUT = 12
VERSION = re.compile(r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}')
CHAMPION = re.compile(r'[A-Za-z][A-Za-z0-9]{0,99}')
SHA256 = re.compile(r'[a-f0-9]{64}')


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _json(raw, limit):
    if not isinstance(raw, bytes) or not 0 < len(raw) <= limit:
        raise ValueError('source size')
    return json.loads(raw)


def _read(path, limit):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
        raise ValueError('archive file')
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    if not 0 < len(raw) <= limit:
        raise ValueError('archive size')
    return raw


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('unexpected source redirect')


def _fetch(url, limit, timeout):
    if not (url == VERSIONS_URL or re.fullmatch(
            re.escape(ORIGIN) + r'/cdn/[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}/data/ko_KR/champion(?:/[A-Za-z][A-Za-z0-9]{0,99})?\.json', url)):
        raise ValueError('unapproved official URL')
    request = urllib.request.Request(url, headers={'User-Agent': 'lol-coach-official-catalog/2.1'})
    opener = urllib.request.build_opener(_NoRedirect())
    with opener.open(request, timeout=timeout) as response:
        if response.status != 200 or response.geturl() != url:
            raise ValueError('official HTTP response')
        raw = response.read(limit + 1)
    _json(raw, limit)
    return raw


def _roster_url(version):
    return f'{ORIGIN}/cdn/{version}/data/ko_KR/champion.json'


def _source_url(version, champion):
    return f'{ORIGIN}/cdn/{version}/data/ko_KR/champion/{champion}.json'


def _roster(raw, version):
    data = _json(raw, MAX_ROSTER)
    if not isinstance(data, dict) or data.get('version') != version or data.get('type') != 'champion':
        raise ValueError('roster version')
    rows = data.get('data')
    if not isinstance(rows, dict) or not 1 <= len(rows) <= MAX_CHAMPIONS:
        raise ValueError('roster count')
    for champion, row in rows.items():
        if not CHAMPION.fullmatch(champion) or not isinstance(row, dict) or row.get('id') != champion:
            raise ValueError('roster identity')
        _plain(row.get('name'))
    return rows


def _detail(raw, version, champion, name):
    data = _json(raw, MAX_SOURCE)
    if not isinstance(data, dict) or data.get('version') != version or data.get('type') != 'champion':
        raise ValueError('champion version')
    if not isinstance(data.get('data'), dict) or set(data['data']) != {champion}:
        raise ValueError('champion source identity')
    row = data['data'][champion]
    if not isinstance(row, dict) or row.get('id') != champion or row.get('name') != name:
        raise ValueError('champion identity')
    spells = row.get('spells')
    if not isinstance(spells, list) or len(spells) != 4:
        raise ValueError('champion spells')
    for ability in [row.get('passive'), *spells]:
        if not isinstance(ability, dict):
            raise ValueError('ability shape')
        _plain(ability.get('name'))
        _plain(ability.get('description'))
    return row


def _record(filename, url, raw, **extra):
    return dict(file=filename, url=url, sha256=_sha(raw), **extra)


def _verified_file(folder, source, filename, url, limit):
    if not isinstance(source, dict) or source.get('file') != filename or source.get('url') != url:
        raise ValueError('source origin')
    digest = source.get('sha256')
    if not isinstance(digest, str) or not SHA256.fullmatch(digest):
        raise ValueError('source hash')
    raw = _read(folder / filename, limit)
    if _sha(raw) != digest:
        raise ValueError('source integrity')
    return raw


def _load_archive(version, manifest_hash=None, verify_all=False):
    if not isinstance(version, str) or not VERSION.fullmatch(version):
        raise ValueError('archive version')
    folder = CATALOG_ROOT / 'versions' / version
    if folder.is_symlink() or folder.parent.is_symlink():
        raise ValueError('archive directory')
    raw = _read(folder / 'manifest.json', MAX_MANIFEST)
    if manifest_hash is not None and _sha(raw) != manifest_hash:
        raise ValueError('manifest integrity')
    manifest = _json(raw, MAX_MANIFEST)
    if (not isinstance(manifest, dict) or manifest.get('schema_version') != 'official-catalog.archive.v1'
            or manifest.get('source_patch') != version or manifest.get('locale') != 'ko_KR'
            or manifest.get('game_patch') != '.'.join(version.split('.')[:2])):
        raise ValueError('manifest schema')
    discovery = _verified_file(folder, manifest.get('discovery'), 'versions.json', VERSIONS_URL, MAX_VERSIONS)
    versions = _json(discovery, MAX_VERSIONS)
    if not isinstance(versions, list) or not versions or versions[0] != version:
        raise ValueError('discovery version')
    roster_raw = _verified_file(folder, manifest.get('roster'), 'champion.ko_KR.json', _roster_url(version), MAX_ROSTER)
    roster = _roster(roster_raw, version)
    rows = manifest.get('sources')
    if (not isinstance(rows, list) or len(rows) != len(roster)
            or any(not isinstance(r, dict) or not isinstance(r.get('champion'), str) for r in rows)):
        raise ValueError('manifest roster')
    sources = {r['champion']: r for r in rows}
    if len(sources) != len(rows) or set(sources) != set(roster):
        raise ValueError('incomplete manifest')
    if verify_all:
        for champion, source in sources.items():
            content = _verified_file(folder, source, f'{champion}-{version}.ko_KR.json', _source_url(version, champion), MAX_SOURCE)
            _detail(content, version, champion, roster[champion]['name'])
    return folder, manifest, roster, sources, _sha(raw)


def _current(verify_all=False):
    pointer = _json(_read(CATALOG_ROOT / 'current.json', 2000), 2000)
    if (not isinstance(pointer, dict) or pointer.get('schema_version') != 'official-catalog.current.v1'
            or not isinstance(pointer.get('manifest_sha256'), str) or not SHA256.fullmatch(pointer['manifest_sha256'])):
        raise ValueError('current pointer')
    return _load_archive(pointer.get('source_patch'), pointer['manifest_sha256'], verify_all)


def _atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink() or path.is_symlink():
        raise ValueError('publication path')
    handle, filename = tempfile.mkstemp(prefix='.' + path.name + '-', dir=path.parent)
    try:
        with os.fdopen(handle, 'wb') as stream:
            stream.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(filename, path)
    finally:
        if os.path.exists(filename):
            os.unlink(filename)


def _status(state, **extra):
    return dict(schema_version='official-catalog.refresh.v1', state=state,
                checked_at=datetime.now(timezone.utc).isoformat(), checked_at_epoch=time.time(), **extra)


def _fallback(reason):
    try:
        _, manifest, roster, _, _ = _current(verify_all=True)
        return _status('OFFLINE_FALLBACK', source_patch=manifest['source_patch'], champion_count=len(roster), reason=reason)
    except (OSError, ValueError, KeyError, TypeError):
        return _status('UNAVAILABLE', reason=reason)


def _legacy_bytes(version, champion, name):
    """Reuse only the exact bytes pinned by the unchanged legacy manifest."""
    try:
        manifest = _json(_read(LEGACY_ROOT / 'manifest.json', MAX_MANIFEST), MAX_MANIFEST)
        if manifest.get('source_patch') != version or manifest.get('locale') != 'ko_KR':
            return None
        source = next(r for r in manifest['sources'] if r['champion'] == champion)
        content = _verified_file(LEGACY_ROOT, source, f'{champion}-{version}.ko_KR.json', _source_url(version, champion), MAX_SOURCE)
        _detail(content, version, champion, name)
        return content
    except (OSError, ValueError, KeyError, TypeError, StopIteration):
        return None


def _acquire_refresh_lock():
    """Keep a native lock open; process death releases it, including on Windows.

    The persistent JSON owner metadata is diagnostic only. A stale PID never
    authorizes takeover: the kernel must grant the exclusive lock first.
    """
    path = CATALOG_ROOT / '.refresh-lock'
    if path.is_symlink():
        raise ValueError('refresh lock path')
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    stream = os.fdopen(descriptor, 'r+b')
    try:
        if os.name == 'nt':
            import msvcrt
            # Windows byte-range locking requires an existing first byte.
            if os.fstat(descriptor).st_size == 0:
                stream.write(b' ')
                stream.flush()
            stream.seek(0)
            msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        stream.close()
        return None
    try:
        owner = dict(pid=os.getpid(), hostname=socket.gethostname(),
                     acquired_at=datetime.now(timezone.utc).isoformat())
        stream.seek(0)
        stream.write((json.dumps(owner) + '\n').encode('utf-8'))
        stream.truncate()
        stream.flush()
    except BaseException:
        _release_refresh_lock(stream)
        raise
    return stream


def _release_refresh_lock(stream):
    try:
        if os.name == 'nt':
            import msvcrt
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
    finally:
        stream.close()


def update_catalog(*, fetch=None):
    """Discover and publish a full release, retaining the last archive on failure.

    ``fetch(url, byte_limit, timeout_seconds) -> bytes`` is an optional transport.
    The default uses only bounded HTTPS requests to official Data Dragon URLs.
    """
    fetch = fetch or _fetch
    CATALOG_ROOT.mkdir(parents=True, exist_ok=True)
    try:
        lock = _acquire_refresh_lock()
    except (OSError, ValueError):
        return _fallback('REFRESH_LOCK_UNAVAILABLE')
    if lock is None:
        return _fallback('REFRESH_IN_PROGRESS')
    stage = None
    try:
        versions_raw = fetch(VERSIONS_URL, MAX_VERSIONS, TIMEOUT)
        versions = _json(versions_raw, MAX_VERSIONS)
        if (not isinstance(versions, list) or not 1 <= len(versions) <= 10000
                or any(not isinstance(v, str) or not 0 < len(v) <= 100 for v in versions)
                or not VERSION.fullmatch(versions[0])):
            raise ValueError('version discovery schema')
        version = versions[0]
        destination = CATALOG_ROOT / 'versions' / version
        reused = 0
        if destination.exists():
            _, manifest, roster, _, digest = _load_archive(version, verify_all=True)
            state = 'UNCHANGED'
        else:
            roster_raw = fetch(_roster_url(version), MAX_ROSTER, TIMEOUT)
            roster = _roster(roster_raw, version)
            versions_folder = CATALOG_ROOT / 'versions'
            versions_folder.mkdir(exist_ok=True)
            if versions_folder.is_symlink():
                raise ValueError('versions directory')
            stage = Path(tempfile.mkdtemp(prefix='.collect-', dir=versions_folder))
            (stage / 'versions.json').write_bytes(versions_raw)
            (stage / 'champion.ko_KR.json').write_bytes(roster_raw)
            def collect(champion):
                content = _legacy_bytes(version, champion, roster[champion]['name'])
                reused_legacy = content is not None
                if content is None:
                    content = fetch(_source_url(version, champion), MAX_SOURCE, TIMEOUT)
                _detail(content, version, champion, roster[champion]['name'])
                filename = f'{champion}-{version}.ko_KR.json'
                (stage / filename).write_bytes(content)
                return _record(filename, _source_url(version, champion), content,
                               champion=champion, name=roster[champion]['name'], reused_legacy=reused_legacy)
            with ThreadPoolExecutor(max_workers=8) as pool:
                sources = list(pool.map(collect, sorted(roster)))
            reused = sum(s['reused_legacy'] for s in sources)
            manifest = dict(schema_version='official-catalog.archive.v1', source_patch=version,
                            game_patch='.'.join(version.split('.')[:2]), locale='ko_KR',
                            collected_at=datetime.now(timezone.utc).isoformat(),
                            discovery=_record('versions.json', VERSIONS_URL, versions_raw),
                            roster=_record('champion.ko_KR.json', _roster_url(version), roster_raw), sources=sources)
            _atomic_json(stage / 'manifest.json', manifest)
            digest = _sha((stage / 'manifest.json').read_bytes())
            os.rename(stage, destination)
            stage = None
            _load_archive(version, digest, verify_all=True)
            state = 'UPDATED'
        _atomic_json(CATALOG_ROOT / 'current.json', dict(schema_version='official-catalog.current.v1',
                     source_patch=version, manifest_sha256=digest))
        result = _status(state, source_patch=version, champion_count=len(roster),
                         fact_count=len(roster) * 5, reused_legacy_count=reused)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result = _fallback(type(exc).__name__ + ': ' + str(exc)[:200])
    finally:
        if stage is not None:
            shutil.rmtree(stage, ignore_errors=True)
        _release_refresh_lock(lock)
    _atomic_json(CATALOG_ROOT / 'refresh-status.json', result)
    return result


def refresh_if_due(*, max_age_seconds=86400, force=False, fetch=None):
    """Launcher hook: refresh at most daily; failed checks retry after one hour.

    Call once before starting the local server. Read-only UI fact calls never
    fetch. ``force=True`` bypasses age checks. Returned status is JSON-safe.
    """
    if not isinstance(max_age_seconds, (int, float)) or not 0 <= max_age_seconds <= 31_536_000:
        raise ValueError('refresh age')
    if not force:
        try:
            status = _json(_read(CATALOG_ROOT / 'refresh-status.json', 4000), 4000)
            age = time.time() - status['checked_at_epoch']
            interval = min(max_age_seconds, 3600) if status['state'] in ('OFFLINE_FALLBACK', 'UNAVAILABLE') else max_age_seconds
            if 0 <= age < interval:
                if status['state'] in ('OFFLINE_FALLBACK', 'UNAVAILABLE'):
                    return dict(_fallback(status.get('reason', 'LAST_REFRESH_FAILED')),
                                checked_at=status['checked_at'], checked_at_epoch=status['checked_at_epoch'])
                _, manifest, roster, _, _ = _current(verify_all=True)
                return dict(status, state='FRESH', source_patch=manifest['source_patch'], champion_count=len(roster))
        except (OSError, ValueError, KeyError, TypeError):
            pass
    return update_catalog(fetch=fetch)


def facts_response(champions=None, patch=None):
    """Old official-reference.v1 response shape plus all-roster catalog metadata."""
    result = dict(schema_version='official-reference.v1', approval_required=False, reference_only=True,
                  game_patch=patch, reference_status='UNAVAILABLE', champions=[], unavailable=[])
    try:
        folder, manifest, roster, sources, _ = _current()
        version = manifest['source_patch']
    except (OSError, ValueError, KeyError, TypeError):
        result['reason'] = 'OFFICIAL_CATALOG_UNAVAILABLE_OR_INVALID'
        return result
    result.update(reference_status='AVAILABLE', source_patch=version, locale='ko_KR',
                  catalog_champion_count=len(roster), catalog_schema_version='official-catalog.archive.v1')
    try:
        refresh = _json(_read(CATALOG_ROOT / 'refresh-status.json', 4000), 4000)
        result['refresh_status'] = {k: refresh[k] for k in ('state', 'checked_at', 'reason') if k in refresh}
    except (OSError, ValueError, KeyError, TypeError):
        result['refresh_status'] = dict(state='UNKNOWN')
    wanted = list(sources) if champions is None else list(dict.fromkeys(champions))
    for champion in wanted:
        try:
            if not isinstance(champion, str) or not CHAMPION.fullmatch(champion):
                raise ValueError('champion selector')
            source = sources[champion]
            url = _source_url(version, champion)
            content = _verified_file(folder, source, f'{champion}-{version}.ko_KR.json', url, MAX_SOURCE)
            detail = _detail(content, version, champion, roster[champion]['name'])
            facts = []
            for locator, ability in [('passive', detail['passive']), *[(f'spells.{i}', s) for i, s in enumerate(detail['spells'])]]:
                facts.append(dict(name=_plain(ability['name']), text=_plain(ability['description']),
                                  verification='OFFICIAL_ARCHIVE_VERIFIED', source=dict(url=url, sha256=source['sha256'],
                                  locator=f'data.{champion}.{locator}.description', patch=version)))
            status = 'GAME_PATCH_UNKNOWN' if patch is None else 'MATCHING_ARCHIVE' if patch in (manifest['game_patch'], version) else 'GAME_PATCH_MISMATCH'
            result['champions'].append(dict(champion=champion, name=detail['name'], source_patch=version, patch_status=status, facts=facts))
        except (OSError, ValueError, KeyError, TypeError):
            result['unavailable'].append(dict(champion=champion, reason='SOURCE_UNAVAILABLE_OR_UNVERIFIED'))
    return result


def request_facts(body):
    from .storage import ServiceError
    if (not isinstance(body, dict) or set(body) != {'champions', 'patch'} or not isinstance(body['champions'], list)
            or len(body['champions']) > MAX_CHAMPIONS
            or any(not isinstance(c, str) or not CHAMPION.fullmatch(c) for c in body['champions'])
            or body['patch'] is not None and (not isinstance(body['patch'], str) or not body['patch'].strip() or len(body['patch']) > 100)):
        raise ServiceError(422, 'INVALID_OFFICIAL_REFERENCE_REQUEST')
    return facts_response(body['champions'], body['patch'])

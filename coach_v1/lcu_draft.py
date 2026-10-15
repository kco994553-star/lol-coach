"""Read-only, server-local champion-select projection. No player identity APIs.

Public LCU schema is DOCUMENTED_ONLY; synthetic tests are not game-PC proof.
Only this module's private HTTPS connection accepts a self-signed certificate,
and only after a caller-configured SHA256 certificate pin matches, before auth.
"""
import base64
import copy
from dataclasses import dataclass, field
import hashlib
import hmac
import http.client
import json
import os
from pathlib import Path
import re
import ssl
import stat
import threading
import time
from email.utils import parsedate_to_datetime


PHASE_ENDPOINT = '/lol-gameflow/v1/gameflow-phase'
SESSION_ENDPOINT = '/lol-champ-select/v1/session'
MAX_RESPONSE_BYTES = 512_000
_IDENTITY_FIELDS = frozenset(('summonerId', 'summonerName', 'displayName',
    'riotId', 'riotIdGameName', 'riotIdTagLine', 'gameName', 'tagLine',
    'puuid', 'accountId', 'account', 'obfuscatedSummonerId', 'obfuscatedPuuid'))
_SESSION_REQUIRED = frozenset(('myTeam', 'theirTeam', 'actions', 'bans',
                             'timer', 'localPlayerCellId'))
_SESSION_OPTIONAL = frozenset(('allowBattleBoost', 'allowDuplicatePicks',
    'allowLockedEvents', 'allowRerolling', 'allowSkinSelection', 'benchChampionIds',
    'benchEnabled', 'boostableSkinCount', 'chatDetails', 'counter',
    'entitledFeatureState', 'gameId', 'hasSimultaneousBans', 'hasSimultaneousPicks',
    'isCustomGame', 'isSpectating', 'lockedEventIndex', 'recoveryCounter',
    'rerollsRemaining', 'skipChampionSelect', 'trades', 'gameType',
    'allowDevTools', 'pickOrderSwaps', 'allowRegistration', 'hideEnemySummoners'))
_PLAYER_REQUIRED = frozenset(('cellId', 'championId', 'assignedPosition'))
_PLAYER_OPTIONAL = frozenset(('championPickIntent', 'entitledFeatureType',
    'selectedSkinId', 'spell1Id', 'spell2Id', 'team', 'wardSkinId',
    'pickMode', 'pickTurn', 'playerType', 'nameVisibilityType')) | _IDENTITY_FIELDS
_ACTION_REQUIRED = frozenset(('actorCellId', 'championId', 'completed', 'type'))
_ACTION_OPTIONAL = frozenset(('id', 'isAllyAction', 'isInProgress', 'pickTurn'))
_TIMER_OPTIONAL = frozenset(('adjustedTimeLeftInPhase', 'internalNowInEpochMs',
                           'isInfinite', 'totalTimeInPhase'))
_POSITIONS = {'top': 'TOP', 'jungle': 'JUNGLE', 'middle': 'MID',
              'bottom': 'BOTTOM', 'utility': 'SUPPORT', '': None}
_GAME_PHASES = frozenset(('None', 'Lobby', 'Matchmaking', 'CheckedIntoTournament',
    'ReadyCheck', 'ChampSelect', 'GameStart', 'FailedToLaunch', 'InProgress',
    'Reconnect', 'WaitingForStats', 'PreEndOfGame', 'EndOfGame', 'TerminatedInError'))
_PICK_PHASES = frozenset(('PLANNING', 'BAN_PICK', 'FINALIZATION'))


class _Failure(Exception):
    def __init__(self, reason, retry_after=None):
        self.reason = reason
        self.retry_after = retry_after


@dataclass(frozen=True, repr=False)
class _Credentials:
    pid: int
    port: int
    password: str = field(repr=False)


def _integer(value, minimum=0, maximum=2**31-1):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError('integer')
    return value


def _fields(value, required, optional=frozenset()):
    if not isinstance(value, dict) or not required <= value.keys() or not value.keys() <= required | optional:
        raise ValueError('schema')


def _lockfile(path):
    """Bounded regular-file read; no process scanning, subprocesses, or URL input."""
    if path.is_symlink():
        raise _Failure('LOCKFILE_INVALID')
    descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) |
                         getattr(os, 'O_NONBLOCK', 0))
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > 1024:
            raise _Failure('LOCKFILE_INVALID')
        try:
            data = os.read(descriptor, 1025).decode('ascii')
        except UnicodeError:
            raise _Failure('LOCKFILE_INVALID') from None
    finally:
        os.close(descriptor)
    # No host field is accepted; destination is a literal loopback address.
    match = re.fullmatch(r'LeagueClient:([1-9][0-9]{0,9}):([1-9][0-9]{0,4}):([A-Za-z0-9_.~-]{1,256}):https(?:\r?\n)?', data)
    if not match:
        raise _Failure('LOCKFILE_INVALID')
    pid, port, password = match.groups()
    if int(port) > 65535:
        raise _Failure('LOCKFILE_INVALID')
    return _Credentials(int(pid), int(port), password)


def _safe_object(pairs):
    """Discard identity members as JSON objects are built; never project values."""
    result = {}
    for key, value in pairs:
        if key in _IDENTITY_FIELDS:
            continue
        if key in result:
            raise ValueError('duplicate field')
        result[key] = value
    return result


def discover_lockfile():
    """Return a conventional native-Windows installation lockfile, or None.

    Discovery never scans process command lines or reads account/config files.
    Nonstandard installs can pass their explicit private path to the launcher.
    The candidate is not trusted until pair_certificate verifies its process.
    """
    if os.name != 'nt':
        return None
    roots = [Path(os.environ.get('SystemDrive', 'C:') + '\\')]
    roots.extend(Path(os.environ[key]) for key in ('ProgramFiles', 'ProgramFiles(x86)') if os.environ.get(key))
    for root in roots:
        candidate = root / 'Riot Games' / 'League of Legends' / 'lockfile'
        if candidate.is_file() and not candidate.is_symlink():
            return candidate
    return None


def _validate_windows_client(path, credentials):
    """Verify image path, same user SID and PID owning the loopback listener.

    Uses native query APIs only; neither process command lines nor user names
    are collected. Fail closed on access denial, races or unsupported hosts.
    """
    if os.name != 'nt':
        raise ValueError('WINDOWS_CLIENT_REQUIRED')
    import ctypes
    from ctypes import wintypes
    import socket
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    security = ctypes.WinDLL('advapi32', use_last_error=True)
    network = ctypes.WinDLL('iphlpapi', use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                                wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    security.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
    security.GetTokenInformation.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p,
                                            wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    security.EqualSid.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    network.GetExtendedTcpTable.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD),
                                          wintypes.BOOL, wintypes.ULONG, ctypes.c_int, wintypes.ULONG]
    handles = []
    try:
        process = kernel.OpenProcess(0x1000, False, credentials.pid)
        if not process:
            raise ValueError('LOCAL_PROCESS_UNVERIFIED')
        handles.append(process)
        image = ctypes.create_unicode_buffer(32768)
        size = wintypes.DWORD(len(image))
        if not kernel.QueryFullProcessImageNameW(process, 0, image, ctypes.byref(size)):
            raise ValueError('LOCAL_PROCESS_UNVERIFIED')
        if Path(image.value).resolve() != (path.parent / 'LeagueClient.exe').resolve():
            raise ValueError('LOCAL_PROCESS_UNVERIFIED')
        class TokenUser(ctypes.Structure):
            _fields_ = [('sid', ctypes.c_void_p), ('attributes', wintypes.DWORD)]
        users = []
        for owner_process in (process, kernel.GetCurrentProcess()):
            token = wintypes.HANDLE()
            if not security.OpenProcessToken(owner_process, 0x0008, ctypes.byref(token)):
                raise ValueError('LOCAL_PROCESS_UNVERIFIED')
            handles.append(token)
            needed = wintypes.DWORD()
            security.GetTokenInformation(token, 1, None, 0, ctypes.byref(needed))
            if not 0 < needed.value <= 65536:
                raise ValueError('LOCAL_PROCESS_UNVERIFIED')
            user = ctypes.create_string_buffer(needed.value)
            if not security.GetTokenInformation(token, 1, user, needed.value, ctypes.byref(needed)):
                raise ValueError('LOCAL_PROCESS_UNVERIFIED')
            users.append(user)
        if not security.EqualSid(TokenUser.from_buffer(users[0]).sid, TokenUser.from_buffer(users[1]).sid):
            raise ValueError('LOCAL_PROCESS_UNVERIFIED')
        needed = wintypes.DWORD()
        # AF_INET=2; TCP_TABLE_OWNER_PID_LISTENER=3. No remote addresses used.
        network.GetExtendedTcpTable(None, ctypes.byref(needed), False, 2, 3, 0)
        if not 4 <= needed.value <= 16_000_000:
            raise ValueError('LOCAL_PROCESS_UNVERIFIED')
        table = ctypes.create_string_buffer(needed.value)
        if network.GetExtendedTcpTable(table, ctypes.byref(needed), False, 2, 3, 0):
            raise ValueError('LOCAL_PROCESS_UNVERIFIED')
        class TCPRow(ctypes.Structure):
            _fields_ = [(key, wintypes.DWORD) for key in
                        ('state', 'address', 'port', 'remote_address', 'remote_port', 'pid')]
        count = wintypes.DWORD.from_buffer(table).value
        if 4 + count * ctypes.sizeof(TCPRow) > len(table):
            raise ValueError('LOCAL_PROCESS_UNVERIFIED')
        rows = (TCPRow * count).from_buffer(table, 4)
        loopback = int.from_bytes(socket.inet_aton('127.0.0.1'), 'little')
        matches = [row for row in rows if row.address == loopback and
                   socket.ntohs(row.port & 0xffff) == credentials.port]
        if len(matches) != 1 or matches[0].pid != credentials.pid:
            raise ValueError('LOCAL_PROCESS_UNVERIFIED')
    finally:
        for handle in reversed(handles):
            kernel.CloseHandle(handle)


def pair_certificate(lockfile_path, *, timeout=2.0):
    """Trusted one-step-launch TOFU pairing, never callable through public HTTP.

    Returns an in-memory lowercase SHA256 pin. Sends no HTTP/auth, persists no
    credential/certificate. OS process, user and port checks precede and follow
    the loopback TLS handshake; lockfile rotation aborts pairing.
    """
    if type(timeout) not in (int, float) or not 0 < timeout <= 10:
        raise ValueError('PAIRING_FAILED')
    connection = None
    try:
        path = Path(lockfile_path)
        credentials = _lockfile(path)
        _validate_windows_client(path, credentials)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        connection = http.client.HTTPSConnection('127.0.0.1', credentials.port,
                                                   timeout=timeout, context=context)
        connection.connect()
        certificate = connection.sock.getpeercert(binary_form=True)
        if not certificate:
            raise ValueError('PAIRING_FAILED')
        if _lockfile(path) != credentials:
            raise ValueError('SESSION_CHANGED')
        _validate_windows_client(path, credentials)
        return hashlib.sha256(certificate).hexdigest()
    except _Failure as error:
        raise ValueError(error.reason) from None
    except (OSError, http.client.HTTPException):
        raise ValueError('PAIRING_FAILED') from None
    finally:
        if connection is not None:
            connection.close()


def _https_get(credentials, endpoint, pin, timeout):
    if endpoint not in (PHASE_ENDPOINT, SESSION_ENDPOINT):
        raise _Failure('ENDPOINT_FORBIDDEN')
    if pin is None:
        raise _Failure('TLS_PIN_REQUIRED')
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    connection = http.client.HTTPSConnection('127.0.0.1', credentials.port,
                                               timeout=timeout, context=context)
    try:
        connection.connect()
        certificate = connection.sock.getpeercert(binary_form=True)
        if not certificate or not hmac.compare_digest(hashlib.sha256(certificate).hexdigest(), pin):
            raise _Failure('TLS_PIN_MISMATCH')
        authorization = base64.b64encode(('riot:' + credentials.password).encode('ascii')).decode('ascii')
        connection.request('GET', endpoint, headers={'Authorization': 'Basic ' + authorization,
                                                     'Accept': 'application/json'})
        response = connection.getresponse()
        # No redirects or retries (including 429); error bodies are never read.
        if response.status != 200:
            if response.status == 429:
                header = response.getheader('Retry-After', '')
                delay = 60.0
                if isinstance(header, str):
                    if header.isascii() and header.isdigit():
                        delay = float(header) if len(header) <= 10 else float('inf')
                    else:
                        try:
                            delay = max(1.0, parsedate_to_datetime(header).timestamp() - time.time())
                        except (ValueError, TypeError, OverflowError):
                            pass
                raise _Failure('LCU_RATE_LIMITED', max(1.0, delay))
            raise _Failure('LCU_AUTH_FAILED' if response.status in (401, 403) else 'LCU_HTTP_FAILED')
        if response.getheader('Content-Type', '').split(';')[0].strip().lower() != 'application/json':
            raise _Failure('SCHEMA_UNSUPPORTED')
        body = response.read(MAX_RESPONSE_BYTES + 1)
        if len(body) > MAX_RESPONSE_BYTES:
            raise _Failure('SCHEMA_UNSUPPORTED')
        try:
            return json.loads(body, object_pairs_hook=_safe_object,
                              parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        except (ValueError, UnicodeError, RecursionError):
            raise _Failure('SCHEMA_UNSUPPORTED') from None
    finally:
        connection.close()


class LCUDraftAdapter:
    """Trusted backend API; never construct with browser-supplied paths/maps/pins.

    ``champion_map`` is an already-validated local public ID->catalogue ID map
    (for example Data Dragon ``int(entry['key']): entry['id']``). No external
    roster request is made. ``transport`` is a trusted synthetic test seam only.
    Poll is synchronous, serialized, one attempt, at most three GETs. Caller
    owns cadence; no daemon, browser pairing, HTTP endpoint or coaching here.
    """
    def __init__(self, lockfile_path, champion_map, *, patch=None,
                 certificate_sha256=None, timeout=2.0, transport=None):
        if not isinstance(champion_map, dict) or not champion_map:
            raise ValueError('public champion map required')
        for key, value in champion_map.items():
            _integer(key, 1)
            if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9]{0,63}', value):
                raise ValueError('catalogue champion ID')
        if patch is not None and (not isinstance(patch, str) or not re.fullmatch(r'[0-9]{1,3}\.[0-9]{1,3}(?:\.[0-9]{1,3})?', patch)):
            raise ValueError('patch')
        if certificate_sha256 is not None and (not isinstance(certificate_sha256, str) or not re.fullmatch(r'[a-fA-F0-9]{64}', certificate_sha256)):
            raise ValueError('certificate pin')
        if type(timeout) not in (int, float) or not 0 < timeout <= 10:
            raise ValueError('timeout')
        self._path = Path(lockfile_path)
        self._roster = dict(champion_map)
        self._patch = patch
        self._pin = certificate_sha256.lower() if certificate_sha256 else None
        self._timeout = timeout
        self._transport = transport
        self._session_fingerprint = None
        self._retry_until = 0.0
        self._mutex = threading.Lock()
        self._state = self._empty('MANUAL_FALLBACK', 'NOT_POLLED')
        self._state['revision'] = 0

    def _empty(self, status, reason, phase=None):
        return dict(status=status, reason=reason, phase=phase, patch=self._patch,
                    own_champion=None, own_position=None, allies=[], enemies=[],
                    bans={'allies': [], 'enemies': []}, pick_phase=None)

    def snapshot(self):
        with self._mutex:
            return copy.deepcopy(self._state)

    def _champion(self, value):
        _integer(value, -1)
        if value in (-1, 0):
            return None
        if value not in self._roster:
            raise ValueError('unknown champion')
        return self._roster[value]

    def _project(self, session):
        _fields(session, _SESSION_REQUIRED, _SESSION_OPTIONAL)
        _fields(session['timer'], frozenset(('phase',)), _TIMER_OPTIONAL)
        pick_phase = session['timer']['phase']
        if pick_phase not in _PICK_PHASES:
            raise ValueError('pick phase')
        _fields(session['bans'], frozenset(('myTeamBans', 'theirTeamBans', 'numBans')))
        _integer(session['bans']['numBans'], 0, 10)
        actions = session['actions']
        if not isinstance(actions, list) or len(actions) > 30:
            raise ValueError('actions')
        picks = {}
        for group in actions:
            if not isinstance(group, list) or len(group) > 10:
                raise ValueError('action group')
            for action in group:
                _fields(action, _ACTION_REQUIRED, _ACTION_OPTIONAL)
                cell = _integer(action['actorCellId'], -1, 99)
                champion = _integer(action['championId'], -1)
                if type(action['completed']) is not bool or action['type'] not in ('pick', 'ban', 'ten_bans_reveal'):
                    raise ValueError('action')
                for flag in ('isAllyAction', 'isInProgress'):
                    if flag in action and type(action[flag]) is not bool:
                        raise ValueError('action flag')
                if action['type'] == 'pick':
                    if cell in picks:
                        raise ValueError('ambiguous pick actions')
                    picks[cell] = (champion, action['completed'],
                                   action.get('isAllyAction') is True,
                                   action.get('isInProgress') is True)
        result = self._empty('CONNECTED', 'CHAMP_SELECT_VERIFIED', 'ChampSelect')
        result['pick_phase'] = pick_phase
        seen = set()
        own_cell = _integer(session['localPlayerCellId'], 0, 99)
        found_own = False
        for source, target in (('myTeam', 'allies'), ('theirTeam', 'enemies')):
            team = session[source]
            if not isinstance(team, list) or not 1 <= len(team) <= 5:
                raise ValueError('team')
            for player in team:
                _fields(player, _PLAYER_REQUIRED, _PLAYER_OPTIONAL)
                cell = _integer(player['cellId'], 0, 99)
                if cell in seen:
                    raise ValueError('duplicate cell')
                seen.add(cell)
                champion = self._champion(player['championId'])
                hovered = False
                # Allied intent is visible pre-game information. Enemy intent
                # is never read, nor is a hidden enemy recovered from actions.
                if champion is None and source == 'myTeam':
                    if 'championPickIntent' in player:
                        champion = self._champion(player['championPickIntent'])
                    if champion is None and cell in picks:
                        action_champion, completed, allied, in_progress = picks[cell]
                        if allied and in_progress and not completed:
                            champion = self._champion(action_champion)
                    hovered = champion is not None
                position = player['assignedPosition']
                if not isinstance(position, str) or position not in _POSITIONS:
                    raise ValueError('position')
                locked = False if hovered else None
                if not hovered and champion is not None and cell in picks and picks[cell][0] == player['championId']:
                    locked = picks[cell][1]
                row = dict(champion=champion, position=_POSITIONS[position], locked=locked)
                result[target].append(row)
                if source == 'myTeam' and cell == own_cell:
                    found_own = True
                    result['own_champion'], result['own_position'] = champion, row['position']
        if not found_own:
            raise ValueError('local player absent')
        for source, target in (('myTeamBans', 'allies'), ('theirTeamBans', 'enemies')):
            bans = session['bans'][source]
            if not isinstance(bans, list) or len(bans) > 5:
                raise ValueError('bans')
            result['bans'][target] = [self._champion(champion) for champion in bans]
        return result

    def poll(self):
        with self._mutex:
            if time.monotonic() < self._retry_until:
                return copy.deepcopy(self._state)
            fingerprint = None
            phase = None
            try:
                credentials = _lockfile(self._path)
                fingerprint = hashlib.sha256((str(credentials.pid) + ':' + str(credentials.port) + ':' + credentials.password).encode('ascii')).digest()
                def get(endpoint):
                    if _lockfile(self._path) != credentials:
                        raise _Failure('SESSION_CHANGED')
                    if self._transport is not None:
                        return self._transport(credentials, endpoint)
                    return _https_get(credentials, endpoint, self._pin, self._timeout)
                phase = get(PHASE_ENDPOINT)
                if not isinstance(phase, str) or phase not in _GAME_PHASES:
                    phase = None
                    raise _Failure('PHASE_UNKNOWN')
                if phase != 'ChampSelect':
                    raise _Failure('NOT_CHAMP_SELECT')
                session = get(SESSION_ENDPOINT)
                if get(PHASE_ENDPOINT) != phase:
                    phase = None
                    raise _Failure('PHASE_CHANGED')
                if _lockfile(self._path) != credentials:
                    raise _Failure('SESSION_CHANGED')
                result = self._project(session)
            except FileNotFoundError:
                result = self._empty('BLOCKED_EXTERNAL', 'LCU_NOT_AVAILABLE')
            except _Failure as error:
                if error.retry_after is not None:
                    self._retry_until = time.monotonic() + error.retry_after
                result = self._empty('MANUAL_FALLBACK', error.reason, phase)
            except (ValueError, KeyError, TypeError, UnicodeError, RecursionError):
                result = self._empty('MANUAL_FALLBACK', 'SCHEMA_UNSUPPORTED', phase)
            except (OSError, http.client.HTTPException):
                result = self._empty('MANUAL_FALLBACK', 'LCU_REQUEST_FAILED')
            old = {key: value for key, value in self._state.items() if key != 'revision'}
            revision = self._state['revision']
            if result != old or fingerprint != self._session_fingerprint:
                revision += 1
            self._session_fingerprint = fingerprint
            self._state = dict(result, revision=revision)
            return copy.deepcopy(self._state)

"""Private, anonymous final-result sufficient records; never a browser payload.

Provider responses are read only in memory. Unknown roles remain unknown. A
record's seed memberships describe discovery cohorts, not participant ranks.
"""
from copy import deepcopy
from datetime import datetime
import hashlib
import re

from .outcome_stats import _champion, _hash, _integer, ROLE_MAP
from .power_stats import POSITIONS, TIERS

SCHEMA = 'champion.opponent-results.v1'
SOURCE = dict(platform='KR', regional='ASIA', queue_id=420, map_id=11)
PROVENANCE_KEYS = {'tier', 'division', 'window_start', 'window_end', 'retrieved_at',
                   'source_digest', 'run_digest'}
MAX_RECORDS = 100000


def _require(condition):
    if not condition:
        raise ValueError('invalid anonymous matchup results')


def _provenance(value, tier):
    value = {} if value is None else deepcopy(value)
    _require(isinstance(value, dict) and set(value) <= PROVENANCE_KEYS)
    value.setdefault('tier', tier)
    _require(value['tier'] == tier and tier in TIERS)
    if 'division' in value:
        _require(value['division'] is None or value['division'] in ('I', 'II', 'III', 'IV'))
    for key in ('window_start', 'window_end'):
        if key in value:
            _require(value[key] is None or _integer(value[key]))
    if value.get('window_start') is not None and value.get('window_end') is not None:
        _require(value['window_start'] <= value['window_end'])
    if value.get('retrieved_at') is not None:
        _require(isinstance(value['retrieved_at'], str) and len(value['retrieved_at']) <= 64)
        try:
            parsed = datetime.fromisoformat(value['retrieved_at'].replace('Z', '+00:00'))
            _require(parsed.tzinfo is not None)
        except (ValueError, TypeError):
            raise ValueError('invalid anonymous matchup results') from None
    for key in ('source_digest', 'run_digest'):
        if key in value:
            _require(_hash(value[key]))
    return value


def _sort_provenance(values):
    import json
    unique = {json.dumps(value, sort_keys=True, separators=(',', ':')): value for value in values}
    return [unique[key] for key in sorted(unique)]


def _validate_record(record):
    r = deepcopy(record)
    _require(isinstance(r, dict) and set(r) == {'hash', 'patch', 'queue_id', 'map_id',
        'sample_kind', 'winner', 'teams', 'seed_tiers', 'provenance'})
    _require(_hash(r['hash']) and isinstance(r['patch'], str) and
             re.fullmatch(r'[0-9]+\.[0-9]+', r['patch']) is not None)
    _require(tuple(map(int, r['patch'].split('.'))) >= (11, 20))
    _require(type(r['queue_id']) is int and r['queue_id'] == 420 and
             type(r['map_id']) is int and r['map_id'] == 11)
    _require(r['sample_kind'] in ('REAL', 'SYNTHETIC') and type(r['winner']) is int and r['winner'] in (0, 1))
    _require(isinstance(r['teams'], list) and len(r['teams']) == 2)
    for team in r['teams']:
        _require(isinstance(team, list) and len(team) == 5)
        roles = []
        for slot in team:
            _require(isinstance(slot, dict) and set(slot) == {'champion', 'position'})
            _require(_champion(slot['champion']) and (slot['position'] is None or slot['position'] in POSITIONS))
            if slot['position'] is not None:
                roles.append(slot['position'])
        _require(len(roles) == len(set(roles)))
        _require(len({slot['champion'] for slot in team}) == 5)
        team.sort(key=lambda slot: (POSITIONS.index(slot['position']) if slot['position'] else 5, slot['champion']))
    tiers = r['seed_tiers']
    _require(isinstance(tiers, list) and bool(tiers) and all(t in TIERS for t in tiers) and len(tiers) == len(set(tiers)))
    r['seed_tiers'] = [tier for tier in TIERS if tier in tiers]
    _require(isinstance(r['provenance'], list) and bool(r['provenance']))
    r['provenance'] = _sort_provenance([_provenance(p, p.get('tier')) for p in r['provenance'] if isinstance(p, dict)])
    _require(len(r['provenance']) > 0 and {p['tier'] for p in r['provenance']} == set(tiers))
    _require(all(isinstance(p, dict) for p in record['provenance']))
    return r


def validate_record(record):
    try:
        return _validate_record(record)
    except (KeyError, TypeError, AttributeError, OverflowError):
        raise ValueError('invalid anonymous matchup results') from None


def normalize_match(raw_match, seed_tier, *, patch=None, sample_kind='REAL', provenance=None):
    """Return an identity-free validated record, or None for ineligible evidence.

    Invalid caller scope/provenance raises; malformed provider match withholds.
    Timeline metadata, when supplied to the batch builder, must also agree.
    """
    _require(seed_tier in TIERS and sample_kind in ('REAL', 'SYNTHETIC'))
    p = _provenance(provenance, seed_tier)
    if patch is not None:
        _require(isinstance(patch, str) and re.fullmatch(r'[0-9]+\.[0-9]+', patch) is not None)
    if not isinstance(raw_match, dict):
        return None
    metadata, info = raw_match.get('metadata'), raw_match.get('info')
    if not isinstance(metadata, dict) or not isinstance(info, dict):
        return None
    mid = metadata.get('matchId')
    if not isinstance(mid, str) or not re.fullmatch(r'KR_[0-9]+' if sample_kind == 'REAL' else r'KR_[A-Za-z0-9_]+', mid):
        return None
    version = info.get('gameVersion')
    if not isinstance(version, str) or re.fullmatch(r'[0-9]+\.[0-9]+(?:\.[0-9]+)*', version) is None:
        return None
    actual_patch = '.'.join(version.split('.')[:2])
    if tuple(map(int, actual_patch.split('.'))) < (11, 20) or patch is not None and actual_patch != patch:
        return None
    if type(info.get('queueId')) is not int or info['queueId'] != 420 or type(info.get('mapId')) is not int or info['mapId'] != 11 or info.get('gameMode') != 'CLASSIC':
        return None
    started, ended, duration = (info.get(key) for key in ('gameStartTimestamp', 'gameEndTimestamp', 'gameDuration'))
    if not _integer(started) or not _integer(ended) or ended < started or not _integer(duration, 1):
        return None
    if p.get('window_start') is not None and started / 1000 < p['window_start'] or p.get('window_end') is not None and started / 1000 > p['window_end']:
        return None
    teams, people = info.get('teams'), info.get('participants')
    if not isinstance(teams, list) or len(teams) != 2 or not isinstance(people, list) or len(people) != 10:
        return None
    wins = {}
    for team in teams:
        if not isinstance(team, dict) or type(team.get('teamId')) is not int or team['teamId'] not in (100, 200) or team['teamId'] in wins or type(team.get('win')) is not bool:
            return None
        wins[team['teamId']] = team['win']
    if set(wins) != {100, 200} or wins[100] == wins[200]:
        return None
    roster = {100: [], 200: []}
    ids = set()
    for person in people:
        if not isinstance(person, dict):
            return None
        tid, pid, champion = person.get('teamId'), person.get('participantId'), person.get('championName')
        if type(tid) is not int or tid not in wins or not _integer(pid, 1) or pid in ids or not _champion(champion) or type(person.get('win')) is not bool or person['win'] != wins[tid]:
            return None
        ids.add(pid)
        raw_role = person.get('teamPosition')
        role = ROLE_MAP.get(raw_role) if isinstance(raw_role, str) else None
        roster[tid].append(dict(champion=champion, position=role))
    record = dict(hash=hashlib.sha256(mid.encode()).hexdigest(), patch=actual_patch,
        queue_id=420, map_id=11, sample_kind=sample_kind, winner=0 if wins[100] else 1,
        teams=[roster[100], roster[200]], seed_tiers=[seed_tier], provenance=[p])
    try:
        return validate_record(record)
    except (ValueError, TypeError, KeyError):
        return None


def _validate_matchup_results(dataset):
    d = deepcopy(dataset)
    _require(isinstance(d, dict) and set(d) == {'schema_version', 'source', 'records', 'omissions'})
    _require(d['schema_version'] == SCHEMA and d['source'] == SOURCE)
    _require(isinstance(d['records'], list) and len(d['records']) <= MAX_RECORDS)
    d['records'] = [validate_record(r) for r in d['records']]
    _require(len({r['hash'] for r in d['records']}) == len(d['records']))
    _require(isinstance(d['omissions'], dict) and set(d['omissions']) <= {'INELIGIBLE_MATCH', 'TIMELINE_METADATA_MISMATCH'})
    _require(all(_integer(n) for n in d['omissions'].values()))
    d['records'].sort(key=lambda r: r['hash'])
    return d


def validate_matchup_results(dataset):
    try:
        return _validate_matchup_results(dataset)
    except (KeyError, TypeError, AttributeError, OverflowError):
        raise ValueError('invalid anonymous matchup results') from None


def empty_matchup_results():
    return dict(schema_version=SCHEMA, source=deepcopy(SOURCE), records=[], omissions={})


def merge_matchup_results(*datasets):
    """Unique match union and membership union; conflict raises before output."""
    result = empty_matchup_results()
    records = {}
    seen_datasets = set()
    from .state import digest
    for dataset in datasets:
        d = validate_matchup_results(dataset)
        fingerprint = digest(d)
        if fingerprint in seen_datasets:
            continue
        seen_datasets.add(fingerprint)
        for reason, n in d['omissions'].items():
            result['omissions'][reason] = result['omissions'].get(reason, 0) + n
        for r in d['records']:
            if r['hash'] in records:
                old = records[r['hash']]
                _require(all(old[k] == r[k] for k in r if k not in ('seed_tiers', 'provenance')))
                old['seed_tiers'] = [tier for tier in TIERS if tier in set(old['seed_tiers']) | set(r['seed_tiers'])]
                old['provenance'] = _sort_provenance(old['provenance'] + r['provenance'])
            else:
                records[r['hash']] = r
    result['records'] = list(records.values())
    return validate_matchup_results(result)


def build_matchup_results(pairs, *, source):
    """Normalize already fetched pairs only; no source acquisition or I/O."""
    _require(isinstance(source, dict) and source.get('platform') == 'KR' and source.get('regional') == 'ASIA' and source.get('queue_id') == 420 and source.get('map_id') == 11)
    tier = source.get('tier')
    _require(tier in TIERS and source.get('sample_kind', 'REAL') in ('REAL', 'SYNTHETIC'))
    _require(source.get('provider') == ('RIOT_API' if source.get('sample_kind', 'REAL') == 'REAL' else 'SYNTHETIC'))
    if source.get('patch') is not None:
        _require(isinstance(source['patch'], str) and re.fullmatch(r'[0-9]+\.[0-9]+', source['patch']) is not None)
    provenance = {key: source[key] for key in PROVENANCE_KEYS if key in source}
    _provenance(provenance, tier)
    result = empty_matchup_results()
    for pair in pairs:
        match = pair.get('match') if isinstance(pair, dict) else None
        timeline = pair.get('timeline') if isinstance(pair, dict) else None
        if not isinstance(match, dict) or not isinstance(timeline, dict) or not isinstance(match.get('metadata'), dict) or not isinstance(timeline.get('metadata'), dict) or timeline['metadata'].get('matchId') != match['metadata'].get('matchId'):
            key = 'TIMELINE_METADATA_MISMATCH'
            result['omissions'][key] = result['omissions'].get(key, 0) + 1
            continue
        record = normalize_match(match, tier, patch=source.get('patch'), sample_kind=source.get('sample_kind', 'REAL'), provenance=provenance)
        if record is None:
            result['omissions']['INELIGIBLE_MATCH'] = result['omissions'].get('INELIGIBLE_MATCH', 0) + 1
        else:
            one = empty_matchup_results()
            one['records'] = [record]
            result = merge_matchup_results(result, one)
    return validate_matchup_results(result)

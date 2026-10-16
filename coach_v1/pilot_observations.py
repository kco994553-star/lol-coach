"""Offline selected-participant observations from a restored private PRO cache.

Only anonymous bounded aggregates leave this module. This is a descriptive audit,
not player-known-view reconstruction, tactical validation, or an accuracy score.
No network or provider interface is used.
"""
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import subprocess

from .postgame_match import PostgameStore
from .recall_stats import ROLE_MAP, _lane

MAX_ENTRIES = 2000
MAX_REPORT_BYTES = 4_000_000
BIND_SOURCES = ('coach_v1/pilot_observations.py','coach_v1/postgame_match.py','coach_v1/recall_stats.py',
                'coach_v1/pro_checkpoint.py','coach_v1/private_pro_bundle.py','scripts/recover_pro_cache.py',
                'scripts/private_pro_bundle.py','.github/workflows/coaching-quality-offline.yml',
                'contracts/coaching-quality-pilot-v1.md')
EVENT_TYPES = ('LEVEL_UP', 'SKILL_LEVEL_UP', 'CHAMPION_KILL', 'ITEM_PURCHASED',
               'ITEM_SOLD', 'ITEM_DESTROYED', 'ITEM_UNDO', 'WARD_PLACED', 'WARD_KILL',
               'ELITE_MONSTER_KILL', 'BUILDING_KILL', 'TURRET_PLATE_DESTROYED',
               'GAME_END', 'OTHER')
ROLES = ('TOP', 'JUNGLE', 'MID', 'BOTTOM', 'SUPPORT', 'UNKNOWN')
# Closed public value vocabulary from the checked-in 16.20.1 official roster.
# Unrecognized future champion names fail closed; no private strings pass through.
CHAMPIONS = frozenset('''Aatrox Ahri Akali Akshan Alistar Ambessa Amumu Anivia Annie Aphelios Ashe AurelionSol Aurora Azir Bard Belveth Blitzcrank Brand Braum Briar Caitlyn Camille Cassiopeia Chogath Corki Darius Diana DrMundo Draven Ekko Elise Evelynn Ezreal Fiddlesticks Fiora Fizz Galio Gangplank Garen Gnar Gragas Graves Gwen Hecarim Heimerdinger Hwei Illaoi Irelia Ivern Janna JarvanIV Jax Jayce Jhin Jinx KSante Kaisa Kalista Karma Karthus Kassadin Katarina Kayle Kayn Kennen Khazix Kindred Kled KogMaw Leblanc LeeSin Leona Lillia Lissandra Locke Lucian Lulu Lux Malphite Malzahar Maokai MasterYi Mel Milio MissFortune MonkeyKing Mordekaiser Morgana Naafiri Nami Nasus Nautilus Neeko Nidalee Nilah Nocturne Nunu Olaf Orianna Ornn Pantheon Poppy Pyke Qiyana Quinn Rakan Rammus RekSai Rell Renata Renekton Rengar Riven Rumble Ryze Samira Sejuani Senna Seraphine Sett Shaco Shen Shyvana Singed Sion Sivir Skarner Smolder Sona Soraka Swain Sylas Syndra TahmKench Taliyah Talon Taric Teemo Thresh Tristana Trundle Tryndamere TwistedFate Twitch Udyr Urgot Varus Vayne Veigar Velkoz Vex Vi Viego Viktor Vladimir Volibear Warwick Xayah Xerath XinZhao Yasuo Yone Yorick Yunara Yuumi Zaahen Zac Zed Zeri Ziggs Zilean Zoe Zyra'''.split())
POLICY = dict(gold='SAME_EXACT_600000_OR_900000_FRAME_TOTAL_GOLD_DIFFERENCE',
              levels='LEVEL_UP_EVENT_ELSE_BOUNDED_RECEIVED_FRAME_INTERVAL',
              ordering='STRICTLY_DISJOINT_INTERVALS_ONLY_OVERLAP_UNKNOWN',
              jungle='SELECTED_JUNGLE_KILL_OR_ASSIST_ENEMY_VICTIM_LANE_GEOMETRY',
              aggregation='SELECTED_PARTICIPANT_COUNTS_WITH_DISTINCT_MATCH_COUNTS')
LIMITATIONS = ['RECORDED_PRO_REFERENCE_SELECTED_PARTICIPANTS_NOT_ALL_MATCH_PLAYERS',
              'DESCRIPTIVE_NON_CAUSAL_NO_GAMEPLAY_RECOMMENDATION',
              'FRAME_INTERVALS_NOT_EXACT_LEVEL_TIMESTAMPS',
              'LEVEL_BOUND_DISTRIBUTIONS_ARE_MARGINALS_NOT_JOINT_SCENES',
              'UNKNOWN_OR_AMBIGUOUS_OPPOSITE_ROLE_EXCLUDED_FROM_COMPARISONS',
              'NO_GOLD_INTERPOLATION_OR_GOLD_RATE_SUBSTITUTION',
              'LANE_GEOMETRY_NOT_LANING_STATE',
              'KILL_INVOLVEMENT_MISSES_GANKS_WITHOUT_KILLS',
              'FIRST_OBSERVED_INVOLVEMENT_NOT_FIRST_GANK',
              'PARTICIPANTS_WITHIN_MATCH_NOT_INDEPENDENT',
              'NO_PLAYER_KNOWN_VIEW_OR_MATCHED_VIDEO',
              'NO_TACTICAL_ACCURACY_OR_APPROVAL_CLAIM']
EVALUATION = dict(evaluable_scenes=0, reason='NO_PLAYER_KNOWN_VIEW_OR_MATCHED_VIDEO',
                  accuracy=None, approval='NOT_ASSESSED')
RECALL = dict(status='NOT_RECOMPUTED', matchup_refinement='UNAVAILABLE',
              reason='EXISTING_RECALL_AGGREGATES_SEPARATE')


def _require(ok):
    if not ok:
        raise ValueError('INVALID_OFFLINE_OBSERVATION_REPORT')


def _int(v, low=0, high=1_000_000_000):
    return type(v) is int and low <= v <= high


def _num(v):
    return type(v) in (int, float) and math.isfinite(v) and abs(v) <= 1_000_000_000


def _keys(v, keys):
    _require(type(v) is dict and set(v) == set(keys))


def _pf(frame, pid):
    return frame['participantFrames'].get(str(pid), {})


def _distribution(values):
    valid = [v for v in values if v is not None]
    return dict(n_valid=len(valid), missing_n=len(values)-len(valid),
                minimum=min(valid) if valid else None,
                median=statistics.median(valid) if valid else None,
                maximum=max(valid) if valid else None)


def _level_interval(pid, target, frames, events, end):
    relevant = [e for e in events if e.get('type') == 'LEVEL_UP' and e.get('participantId') == pid]
    # A malformed level event cannot be repaired by a minute-frame inference.
    if any(not _int(e.get('level'), 1, 18) or not _int(e.get('timestamp'), 0, end) for e in relevant):
        return None
    history=sorted({(e['timestamp'],e['level']) for e in relevant})
    if any(a[1]>=b[1] for a,b in zip(history,history[1:])):
        return None
    samples = [(f['timestamp'], _pf(f, pid).get('level')) for f in frames]
    samples = [(t, level) for t, level in samples if _int(level, 1, 18)]
    if any(a[1]>b[1] for a,b in zip(samples,samples[1:])):
        return None
    # Equality of timestamps does not establish event-vs-frame ordering.
    for event_time,event_level in history:
        if any((t<event_time and level>=event_level) or (t>event_time and level<event_level) for t,level in samples):
            return None
    times = {e['timestamp'] for e in relevant if e['level'] == target}
    if len(times) > 1:
        return None
    if times:
        t = next(iter(times))
        return (t, t, 'EVENT')
    next_sample = next(((t, level) for t, level in samples if level >= target), None)
    if next_sample is None:
        return None
    upper = next_sample[0]
    prior = [t for t, level in samples if t < upper and level < target]
    return (prior[-1], upper, 'FRAME') if prior else None


def _level_summary(rows, target):
    intervals = [(r['levels'][target][0], r['levels'][target][1]) for r in rows]
    earlier = later = 0
    for own, other in intervals:
        if own is not None and other is not None:
            if own[1] < other[0]: earlier += 1
            elif other[1] < own[0]: later += 1
    result = dict(earlier_n=earlier, later_n=later, unknown_n=len(rows)-earlier-later)
    for side, i in (('own', 0), ('opponent', 1)):
        chosen = [pair[i] for pair in intervals]
        result[side+'_exact_event_n'] = sum(v is not None and v[2] == 'EVENT' for v in chosen)
        result[side+'_frame_interval_n'] = sum(v is not None and v[2] == 'FRAME' for v in chosen)
        result[side+'_interval_width_ms'] = _distribution([v[1]-v[0] if v else None for v in chosen])
        result[side+'_interval_bounds_ms'] = dict(aggregation='MARGINAL_DISTRIBUTIONS_NOT_JOINT_SCENES',
            lower_ms=_distribution([v[0] if v else None for v in chosen]),
            upper_ms=_distribution([v[1] if v else None for v in chosen]))
    return result


def _gold(frames, own, other, timestamp):
    frame = next((f for f in frames if f['timestamp'] == timestamp), None)
    if frame is None or other is None:
        return None
    a, b = _pf(frame, own).get('totalGold'), _pf(frame, other).get('totalGold')
    return a-b if _int(a) and _int(b) else None


def _first_lane_kill(pid, own, role, people, events, end):
    if role != 'JUNGLE':
        return None
    chosen = []
    for e in events:
        assists = e.get('assistingParticipantIds', [])
        assists = assists if type(assists) is list else []
        if e.get('type') != 'CHAMPION_KILL' or not (e.get('killerId') == pid or pid in assists):
            continue
        victim = people.get(e.get('victimId'))
        if victim is None or victim['teamId'] == own['teamId'] or not _int(e.get('timestamp'), 0, end):
            continue
        lane = _lane(e.get('position'))
        if lane is not None:
            chosen.append((e['timestamp'], lane))
    return min(chosen) if chosen else None


def _row(body, own, cluster):
    info = body['match']['info']; pid = body['participant_id']
    people = {p['participantId']: p for p in info['participants']}
    role = ROLE_MAP.get(own.get('teamPosition'), 'UNKNOWN')
    # A duplicated own role makes the selected role ambiguous too.
    if role != 'UNKNOWN' and sum(p['teamId'] == own['teamId'] and ROLE_MAP.get(p.get('teamPosition')) == role for p in people.values()) != 1:
        role = 'UNKNOWN'
    others = [p for p in people.values() if p['teamId'] != own['teamId'] and ROLE_MAP.get(p.get('teamPosition')) == role]
    other = others[0] if role != 'UNKNOWN' and len(others) == 1 else None
    end = int(info['gameDuration']*1000)
    frames = [f for f in body['timeline']['info']['frames'] if f['timestamp'] <= end]
    events = [e for f in body['timeline']['info']['frames'] for e in f['events']]
    oid = other['participantId'] if other else None
    _require(own['championName'] in CHAMPIONS and (other is None or other['championName'] in CHAMPIONS))
    return dict(cluster=cluster, patch='.'.join(info['gameVersion'].split('.')[:2]),
                champion=own['championName'], position=role,
                opponent_champion=other['championName'] if other else None,
                gold10=_gold(frames, pid, oid, 600000), gold15=_gold(frames, pid, oid, 900000),
                levels={target: (_level_interval(pid, target, frames, events, end),
                                  _level_interval(oid, target, frames, events, end) if oid else None) for target in (2, 3)},
                jungle=_first_lane_kill(pid, own, role, people, events, end))


def _cohort(key, rows):
    patch, champion, position, other = key
    first = [r['jungle'] for r in rows]
    return dict(patch=patch, champion=champion, position=position, opponent_champion=other,
                matches=len({r['cluster'] for r in rows}), participant_observations=len(rows),
                opponent_missing_n=sum(r['opponent_champion'] is None for r in rows),
                gold_at_10=_distribution([r['gold10'] for r in rows]),
                gold_at_15=_distribution([r['gold15'] for r in rows]),
                level_2=_level_summary(rows, 2), level_3=_level_summary(rows, 3),
                jungle_lane_kill_involvement=dict(label='FIRST_OBSERVED_LANE_KILL_INVOLVEMENT',
                    first_gank='UNKNOWN', eligible_n=len(rows) if position == 'JUNGLE' else 0,
                    timing_ms=_distribution([v[0] if v else None for v in first]),
                    lanes={lane: sum(v is not None and v[1] == lane for v in first) for lane in ('TOP', 'MID', 'BOTTOM')}))


def audit_private_cache(private_directory):
    """Read root/private/matches using PostgameStore; return no raw identities.

    The caller must supply a restored PRO-reference cache, not a general personal
    cache: REAL establishes provenance type, not professional status. Only the
    participant selected in each recorded envelope enters reference cohorts.
    """
    root = Path(private_directory).absolute(); directory = root/'private'/'matches'
    _require('..' not in root.parts and not any(p.is_symlink() for p in (directory, *directory.parents)))
    _require(directory.is_dir())
    paths = sorted(directory.glob('*.json')); _require(len(paths) <= MAX_ENTRIES)
    store = PostgameStore(directory)
    selected = set(); matches = set(); rows = []; duplicates = 0
    inspection = dict(frames=0, participant_frames=0, level_present=0, total_gold_present=0,
                      position_present=0, health_present=0, level_up_malformed_n=0,
                      level_up_conflicting_groups_n=0, events=[])
    counts = Counter(); event_duplicates = Counter()
    for path in paths:
        # _load checks source REAL, file safety, identity binding and full envelope.
        body, own, cluster = store._load(path.stem)
        _require(body['source'] == 'REAL')
        identity = (cluster, body['participant_id'])
        if identity in selected:
            duplicates += 1
            continue
        selected.add(identity); rows.append(_row(body, own, cluster))
        if cluster in matches:
            continue
        matches.add(cluster); seen_events = set(); level_times = defaultdict(set)
        end = int(body['match']['info']['gameDuration']*1000)
        for frame in body['timeline']['info']['frames']:
            inspection['frames'] += 1
            for entry in frame['participantFrames'].values():
                inspection['participant_frames'] += 1
                inspection['level_present'] += _int(entry.get('level'), 1, 18)
                inspection['total_gold_present'] += _int(entry.get('totalGold'))
                inspection['position_present'] += _lane_position(entry.get('position'))
                stats = entry.get('championStats', entry)
                h, m = (stats.get('health'), stats.get('healthMax')) if type(stats) is dict else (None, None)
                inspection['health_present'] += _num(h) and _num(m) and m > 0 and 0 <= h <= m
            for event in frame['events']:
                kind = event['type'] if event['type'] in EVENT_TYPES else 'OTHER'
                counts[kind] += 1
                if kind == 'LEVEL_UP':
                    if not (_int(event.get('participantId'), 1, 10) and
                            _int(event.get('level'), 1, 18) and
                            _int(event.get('timestamp'), 0, end)):
                        inspection['level_up_malformed_n'] += 1
                    else:
                        level_times[(event['participantId'], event['level'])].add(event['timestamp'])
                    signature = json.dumps([kind, event.get('participantId'), event.get('level'), event.get('timestamp')], sort_keys=True, allow_nan=False)
                else:
                    signature = json.dumps(event, sort_keys=True, allow_nan=False, separators=(',', ':'))
                if signature in seen_events: event_duplicates[kind] += 1
                seen_events.add(signature)
        inspection['level_up_conflicting_groups_n'] += sum(len(times) > 1 for times in level_times.values())
    inspection['events'] = [dict(event_type=k, count=counts[k], duplicate_n=event_duplicates[k]) for k in EVENT_TYPES]
    groups = defaultdict(list); patches = defaultdict(list)
    for row in rows:
        groups[tuple(row[k] for k in ('patch', 'champion', 'position', 'opponent_champion'))].append(row)
        patches[row['patch']].append(row)
    report = dict(schema_version='pilot-observations.v1', population='RECORDED_PRO_REFERENCE',
                  source=dict(kind='REAL', cache_entries=len(paths), matches=len(matches),
                              participant_observations=len(rows), duplicate_participant_entries=duplicates),
                  patches=[dict(patch=p, matches=len({r['cluster'] for r in rs}), participant_observations=len(rs)) for p, rs in sorted(patches.items())],
                  inspection=inspection, measurement_policy=deepcopy(POLICY), limitations=list(LIMITATIONS),
                  cohorts=[_cohort(k, rs) for k, rs in sorted(groups.items(), key=lambda pair: tuple(v or '' for v in pair[0]))],
                  recall=deepcopy(RECALL), evaluation=deepcopy(EVALUATION))
    return validate_report(report)


def _lane_position(pos):
    return type(pos) is dict and all(_num(pos.get(k)) and 0 <= pos[k] <= 16000 for k in ('x', 'y'))


def _validate_distribution(d, total, nonnegative=False):
    _keys(d, ('n_valid', 'missing_n', 'minimum', 'median', 'maximum'))
    _require(_int(d['n_valid']) and _int(d['missing_n']) and d['n_valid']+d['missing_n'] == total)
    values = [d[k] for k in ('minimum', 'median', 'maximum')]
    if d['n_valid']:
        _require(all(_num(v) and (not nonnegative or v >= 0) for v in values) and values == sorted(values))
    else:
        _require(values == [None, None, None])


def _validate_level(d, total):
    _keys(d, ('earlier_n', 'later_n', 'unknown_n', 'own_exact_event_n', 'own_frame_interval_n',
              'own_interval_width_ms', 'own_interval_bounds_ms', 'opponent_exact_event_n',
              'opponent_frame_interval_n', 'opponent_interval_width_ms', 'opponent_interval_bounds_ms'))
    names = ('earlier_n', 'later_n', 'unknown_n', 'own_exact_event_n', 'own_frame_interval_n',
             'opponent_exact_event_n', 'opponent_frame_interval_n')
    _require(all(_int(d[k]) for k in names))
    _require(sum(d[k] for k in ('earlier_n', 'later_n', 'unknown_n')) == total)
    for side in ('own', 'opponent'):
        dist = d[side+'_interval_width_ms']; _validate_distribution(dist, total, True)
        _require(d[side+'_exact_event_n']+d[side+'_frame_interval_n'] == dist['n_valid'])
        _require(d['earlier_n']+d['later_n'] <= dist['n_valid'])
        bounds = d[side+'_interval_bounds_ms']
        _keys(bounds, ('aggregation', 'lower_ms', 'upper_ms'))
        _require(bounds['aggregation'] == 'MARGINAL_DISTRIBUTIONS_NOT_JOINT_SCENES')
        for name in ('lower_ms', 'upper_ms'):
            _validate_distribution(bounds[name], total, True)
            _require(bounds[name]['n_valid'] == dist['n_valid'])
        if dist['n_valid']:
            _require(all(bounds['lower_ms'][k] <= bounds['upper_ms'][k] for k in ('minimum', 'median', 'maximum')))
            _require(dist['maximum'] <= bounds['upper_ms']['maximum']-bounds['lower_ms']['minimum'])
            if d[side+'_frame_interval_n'] == 0:
                _require(bounds['lower_ms'] == bounds['upper_ms'])
        if d[side+'_frame_interval_n'] == 0 and dist['n_valid']:
            _require(dist['maximum'] == 0)


def validate_report(report):
    """Strict recursive key and closed-value allowlists; return a detached copy."""
    try:
        return _validate_report(report)
    except (TypeError, KeyError, OverflowError, RecursionError):
        raise ValueError('INVALID_OFFLINE_OBSERVATION_REPORT') from None


def load_bound_report(directory):
    """Accept the expected89/108 cache output only with exact source lineage."""
    try:
        folder=Path(directory).absolute();root=Path(__file__).resolve().parents[1]
        report_path=folder/'observations.json';binding_path=folder/'source-binding.json'
        _require(not any(p.is_symlink() for p in (report_path,binding_path,*folder.parents,folder)))
        _require(report_path.stat().st_size<=MAX_REPORT_BYTES and binding_path.stat().st_size<=100_000)
        raw=report_path.read_bytes();data=validate_report(json.loads(raw));binding=json.loads(binding_path.read_text())
        _keys(binding,('schema_version','actual_commit','source_sha256','checkpoint','report_sha256','source_samples',
                       'provider_requests','network_attempts','privacy','coaching_accuracy'))
        _require(binding['schema_version']=='quality-pilot.offline-binding.v1')
        _require(binding['checkpoint']==dict(run_id=38410710876,artifact_id=11822391323))
        _require(binding['report_sha256']==hashlib.sha256(raw).hexdigest() and binding['source_samples']==data['source'])
        _require(data['source']['matches']==89 and data['source']['participant_observations']==108)
        _require(all(type(binding[k]) is int and binding[k]==0 for k in ('provider_requests','network_attempts')))
        _require(binding['privacy']=='ANONYMOUS_ALLOWLIST_AGGREGATES_ONLY' and binding['coaching_accuracy'] is None)
        commit=binding['actual_commit'];_require(type(commit) is str and re.fullmatch(r'[a-f0-9]{40}',commit))
        _require(set(binding['source_sha256'])==set(BIND_SOURCES))
        subprocess.run(['git','merge-base','--is-ancestor',commit,'HEAD'],cwd=root,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        for name,expected in binding['source_sha256'].items():
            _require(type(expected) is str and re.fullmatch(r'[a-f0-9]{64}',expected))
            archived=subprocess.check_output(['git','show',commit+':'+name],cwd=root,stderr=subprocess.DEVNULL)
            _require(hashlib.sha256(archived).hexdigest()==expected==hashlib.sha256((root/name).read_bytes()).hexdigest())
        return data,deepcopy(binding)
    except (OSError,ValueError,KeyError,TypeError,subprocess.CalledProcessError):
        raise ValueError('INVALID_OR_UNBOUND_OFFLINE_REPORT') from None


def _validate_report(d):
    _keys(d, ('schema_version', 'population', 'source', 'patches', 'inspection', 'measurement_policy',
              'limitations', 'cohorts', 'recall', 'evaluation'))
    _require(d['schema_version'] == 'pilot-observations.v1' and d['population'] == 'RECORDED_PRO_REFERENCE')
    _require(d['measurement_policy'] == POLICY and d['limitations'] == LIMITATIONS)
    _require(d['recall'] == RECALL and d['evaluation'] == EVALUATION)
    # Equality alone admits bools as numeric zeros; enforce exact primitive types.
    _require(type(d['evaluation']['evaluable_scenes']) is int and d['evaluation']['accuracy'] is None)
    s = d['source']; _keys(s, ('kind', 'cache_entries', 'matches', 'participant_observations', 'duplicate_participant_entries'))
    _require(s['kind'] == 'REAL' and all(_int(s[k], 0, MAX_ENTRIES) for k in s if k != 'kind'))
    n = s['participant_observations']; m = s['matches']
    _require(s['cache_entries'] == n+s['duplicate_participant_entries'] and m <= n <= 10*m)
    _require(type(d['patches']) is list and len(d['patches']) <= MAX_ENTRIES)
    patch_counts = {}; patch_n = patch_m = 0
    for p in d['patches']:
        _keys(p, ('patch', 'matches', 'participant_observations'))
        _require(type(p['patch']) is str and re.fullmatch(r'[0-9]{1,3}\.[0-9]{1,3}', p['patch']))
        _require(p['patch'] not in patch_counts and _int(p['matches'], 1, m) and _int(p['participant_observations'], p['matches'], 10*p['matches']))
        patch_counts[p['patch']] = p; patch_n += p['participant_observations']; patch_m += p['matches']
    _require(patch_n == n and patch_m == m)
    i = d['inspection']; _keys(i, ('frames', 'participant_frames', 'level_present', 'total_gold_present', 'position_present', 'health_present', 'level_up_malformed_n', 'level_up_conflicting_groups_n', 'events'))
    _require(all(_int(i[k]) for k in i if k != 'events'))
    _require(m <= i['frames'] <= 245*m and i['participant_frames'] <= 10*i['frames'])
    _require(all(i[k] <= i['participant_frames'] for k in ('level_present', 'total_gold_present', 'position_present', 'health_present')))
    _require(type(i['events']) is list and len(i['events']) == len(EVENT_TYPES))
    for e, kind in zip(i['events'], EVENT_TYPES):
        _keys(e, ('event_type', 'count', 'duplicate_n'))
        _require(e['event_type'] == kind and _int(e['count']) and _int(e['duplicate_n'], 0, e['count']))
    level_event_count = i['events'][0]['count']
    _require(i['level_up_malformed_n'] <= level_event_count and
             2*i['level_up_conflicting_groups_n'] <= level_event_count-i['level_up_malformed_n'])
    _require(type(d['cohorts']) is list and len(d['cohorts']) <= MAX_ENTRIES)
    seen = set(); cohort_n = Counter()
    for c in d['cohorts']:
        _keys(c, ('patch', 'champion', 'position', 'opponent_champion', 'matches', 'participant_observations',
                  'opponent_missing_n', 'gold_at_10', 'gold_at_15', 'level_2', 'level_3', 'jungle_lane_kill_involvement'))
        _require(c['patch'] in patch_counts and c['champion'] in CHAMPIONS and c['position'] in ROLES)
        _require(c['opponent_champion'] is None or c['opponent_champion'] in CHAMPIONS)
        key = tuple(c[k] for k in ('patch', 'champion', 'position', 'opponent_champion'))
        _require(key not in seen); seen.add(key)
        cn = c['participant_observations']; cm = c['matches']; pn = patch_counts[c['patch']]
        _require(_int(cm, 1, pn['matches']) and _int(cn, cm, min(10*cm, pn['participant_observations'])))
        _require(_int(c['opponent_missing_n']) and c['opponent_missing_n'] == (cn if c['opponent_champion'] is None else 0))
        _require(c['position'] != 'UNKNOWN' or c['opponent_champion'] is None)
        for metric in ('gold_at_10', 'gold_at_15'):
            _validate_distribution(c[metric], cn)
            if c['opponent_champion'] is None: _require(c[metric]['n_valid'] == 0)
        for metric in ('level_2', 'level_3'):
            _validate_level(c[metric], cn)
            if c['opponent_champion'] is None:
                _require(c[metric]['opponent_interval_width_ms']['n_valid'] == 0 and c[metric]['unknown_n'] == cn)
        j = c['jungle_lane_kill_involvement']
        _keys(j, ('label', 'first_gank', 'eligible_n', 'timing_ms', 'lanes'))
        _require(j['label'] == 'FIRST_OBSERVED_LANE_KILL_INVOLVEMENT' and j['first_gank'] == 'UNKNOWN')
        _require(_int(j['eligible_n']) and j['eligible_n'] == (cn if c['position'] == 'JUNGLE' else 0))
        _validate_distribution(j['timing_ms'], cn, True); _keys(j['lanes'], ('TOP', 'MID', 'BOTTOM'))
        _require(all(_int(v) for v in j['lanes'].values()) and sum(j['lanes'].values()) == j['timing_ms']['n_valid'] <= j['eligible_n'])
        cohort_n[c['patch']] += cn
    _require(all(cohort_n[p] == count['participant_observations'] for p, count in patch_counts.items()))
    _require(len(json.dumps(d, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode()) <= MAX_REPORT_BYTES)
    return deepcopy(d)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Offline anonymous restored PRO-cache audit')
    parser.add_argument('private_directory', type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(audit_private_cache(args.private_directory), ensure_ascii=False, allow_nan=False, sort_keys=True))
    except (ValueError, KeyError, OSError):
        parser.exit(1, 'OFFLINE_OBSERVATION_AUDIT_FAILED\n')
